"""
Fetches XAUUSD OHLCV data.

Primary source  : Alpha Vantage (free tier supports 5-min bars).
Fallback source : Twelve Data (if MARKET_DATA_API_KEY is set and contains ':td').
Offline fallback: synthetic sine-wave data so the engine never crashes during
                  local testing when no API key is configured.
"""

from __future__ import annotations

import time
import math
import random
import logging
import requests
import pandas as pd
from datetime import datetime, timezone

import config

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Public interface
# ─────────────────────────────────────────────────────────────────────────────

def fetch_ohlcv(symbol: str = config.SYMBOL, limit: int = config.CANDLES_NEEDED) -> pd.DataFrame:
    """Return a DataFrame with columns [open, high, low, close, volume] sorted oldest→newest."""

    if not config.MARKET_DATA_API_KEY:
        logger.warning("MARKET_DATA_API_KEY not set — using synthetic demo data")
        return _synthetic_data(limit)

    # Twelve Data prefix: "td:<key>"
    if config.MARKET_DATA_API_KEY.startswith("td:"):
        key = config.MARKET_DATA_API_KEY[3:]
        df = _fetch_twelve_data(symbol, key, limit)
    else:
        df = _fetch_alpha_vantage(symbol, config.MARKET_DATA_API_KEY, limit)

    if df is None or df.empty:
        logger.warning("Primary data source failed — using synthetic demo data")
        return _synthetic_data(limit)

    logger.info("Fetched %d candles for %s", len(df), symbol)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Alpha Vantage
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_alpha_vantage(symbol: str, api_key: str, limit: int) -> pd.DataFrame | None:
    """
    Alpha Vantage FX_INTRADAY — free tier, 25 requests/day.
    Maps XAUUSD → from_symbol=XAU, to_symbol=USD.
    """
    from_sym, to_sym = "XAU", "USD"
    interval = "5min"
    outputsize = "full" if limit > 100 else "compact"

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "FX_INTRADAY",
        "from_symbol": from_sym,
        "to_symbol": to_sym,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.error("Alpha Vantage request failed: %s", exc)
        return None

    key = f"Time Series FX ({interval})"
    if key not in data:
        logger.error("Alpha Vantage unexpected response: %s", list(data.keys()))
        return None

    rows = []
    for ts_str, bar in data[key].items():
        rows.append({
            "timestamp": pd.Timestamp(ts_str, tz="UTC"),
            "open":   float(bar["1. open"]),
            "high":   float(bar["2. high"]),
            "low":    float(bar["3. low"]),
            "close":  float(bar["4. close"]),
            "volume": 0.0,
        })

    df = pd.DataFrame(rows).sort_values("timestamp").set_index("timestamp")
    return df.tail(limit)


# ─────────────────────────────────────────────────────────────────────────────
# Twelve Data
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_twelve_data(symbol: str, api_key: str, limit: int) -> pd.DataFrame | None:
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": "5min",
        "outputsize": min(limit, 5000),
        "apikey": api_key,
        "format": "JSON",
        "order": "ASC",
    }

    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.error("Twelve Data request failed: %s", exc)
        return None

    if data.get("status") == "error" or "values" not in data:
        logger.error("Twelve Data error: %s", data.get("message", data))
        return None

    rows = []
    for bar in data["values"]:
        rows.append({
            "timestamp": pd.Timestamp(bar["datetime"], tz="UTC"),
            "open":   float(bar["open"]),
            "high":   float(bar["high"]),
            "low":    float(bar["low"]),
            "close":  float(bar["close"]),
            "volume": float(bar.get("volume", 0) or 0),
        })

    df = pd.DataFrame(rows).set_index("timestamp")
    return df.tail(limit)


# ─────────────────────────────────────────────────────────────────────────────
# Synthetic fallback (for local testing without API key)
# ─────────────────────────────────────────────────────────────────────────────

def _synthetic_data(limit: int) -> pd.DataFrame:
    """Generates realistic-looking XAUUSD 5-minute candle data for testing."""
    random.seed(42)
    base_price = 2350.0
    rows = []
    t = int(time.time()) - limit * 300  # 5-min steps back

    price = base_price
    for i in range(limit):
        # Smooth random walk with slight mean reversion
        drift = math.sin(i / 50) * 0.3
        change = random.gauss(drift, 1.2)
        price = max(1800.0, min(3000.0, price + change))

        spread = random.uniform(0.3, 1.5)
        high = price + random.uniform(0.5, 2.5)
        low = price - random.uniform(0.5, 2.5)
        open_ = price + random.gauss(0, 0.5)
        close_ = price
        volume = random.uniform(800, 3000)

        rows.append({
            "timestamp": pd.Timestamp(t + i * 300, unit="s", tz="UTC"),
            "open":   round(open_, 4),
            "high":   round(high, 4),
            "low":    round(low, 4),
            "close":  round(close_, 4),
            "volume": round(volume, 2),
        })

    df = pd.DataFrame(rows).set_index("timestamp")
    logger.debug("Generated %d synthetic candles", len(df))
    return df
