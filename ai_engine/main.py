"""
XAUUSD AI Trading Signal Engine — main entry point.

Run manually:  python main.py
Run via cron:  every 5 minutes via GitHub Actions or PythonAnywhere.
"""

from __future__ import annotations

import logging
import sys
import traceback
from datetime import datetime, timezone

# ── Bootstrap logging before importing local modules ─────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")

import config                           # noqa: E402
import market_data as md                # noqa: E402
import indicators                       # noqa: E402
import news_filter                      # noqa: E402
import signal_engine                    # noqa: E402
import risk_manager                     # noqa: E402
import supabase_client as db            # noqa: E402


def run() -> None:
    start_ts = datetime.now(timezone.utc)
    logger.info("═" * 60)
    logger.info("AI Engine run started at %s", start_ts.isoformat())
    logger.info("Symbol: %s | Mode: %s", config.SYMBOL, config.ENGINE_MODE)

    # ── 1. Fetch market data ─────────────────────────────────────────────────
    logger.info("Step 1/5 — Fetching market data…")
    df = md.fetch_ohlcv(config.SYMBOL, config.CANDLES_NEEDED)
    logger.info("Received %d candles. Latest close: %.4f", len(df), df["close"].iloc[-1])

    # ── 2. Compute indicators ────────────────────────────────────────────────
    logger.info("Step 2/5 — Computing indicators…")
    df = indicators.compute_all(df)

    # ── 3. News filter ───────────────────────────────────────────────────────
    logger.info("Step 3/5 — Checking news impact…")
    news_impact = news_filter.get_news_impact()
    logger.info("News impact: %s", news_impact)

    # ── 4. Generate signal ───────────────────────────────────────────────────
    logger.info("Step 4/5 — Generating signal…")
    signal = signal_engine.generate_signal(df, news_impact)
    logger.info(
        "Signal: %s | Confidence: %d%% | Trend: %s",
        signal["signal"], signal["confidence"], signal["trend"],
    )

    # ── 5. Validate and push to Supabase ─────────────────────────────────────
    logger.info("Step 5/5 — Pushing signal to Supabase…")
    if not risk_manager.validate_signal_payload(signal):
        logger.error("Signal payload failed validation — aborting insert")
        db.log_to_db("ERROR", "Signal payload validation failed", {"signal": signal})
        sys.exit(1)

    record = db.insert_signal(signal)
    if record:
        logger.info("Signal saved. DB id: %s", record.get("id"))
        db.log_to_db("INFO", "Signal generated successfully", {
            "signal":     signal["signal"],
            "confidence": signal["confidence"],
            "id":         record.get("id"),
        })
    else:
        logger.error("Failed to save signal to Supabase")
        db.log_to_db("ERROR", "Failed to insert signal", {"signal": signal})
        sys.exit(1)

    elapsed = (datetime.now(timezone.utc) - start_ts).total_seconds()
    logger.info("Run completed in %.2f seconds", elapsed)
    logger.info("═" * 60)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception:
        logger.critical("Unhandled exception:\n%s", traceback.format_exc())
        sys.exit(1)
