"""
Central configuration for the AI trading signal engine.
All secrets are loaded from environment variables — never hardcoded.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

# ── Market data ───────────────────────────────────────────────────────────────
MARKET_DATA_API_KEY: str = os.getenv("MARKET_DATA_API_KEY", "")
NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")

SYMBOL: str = "XAUUSD"
TIMEFRAME: str = "5min"          # used by Alpha Vantage / Twelve Data
CANDLES_NEEDED: int = 250        # minimum history for EMA-200

# ── Signal engine thresholds ──────────────────────────────────────────────────
ENGINE_MODE: str = "SCALPING"    # SCALPING | SWING | POSITION
MIN_CONFIDENCE: int = 60         # signals below this → WAIT
MIN_RISK_REWARD: float = 2.0     # minimum acceptable R:R ratio

# ── ATR-based risk parameters ─────────────────────────────────────────────────
ATR_SL_MULTIPLIER: float = 1.5   # stop loss = entry ± (ATR × multiplier)
ATR_TP_MULTIPLIER: float = 3.0   # take profit = entry ± (ATR × multiplier)

# ── Indicator periods ─────────────────────────────────────────────────────────
EMA_FAST: int = 20
EMA_MID: int = 50
EMA_SLOW: int = 200
RSI_PERIOD: int = 14
MACD_FAST: int = 12
MACD_SLOW: int = 26
MACD_SIGNAL: int = 9
ATR_PERIOD: int = 14
BB_PERIOD: int = 20
BB_STD: float = 2.0

# ── News filter ───────────────────────────────────────────────────────────────
NEWS_FILTER_ENABLED: bool = True
HIGH_IMPACT_CURRENCIES: list[str] = ["USD", "XAU"]
NEWS_BLOCK_MINUTES_BEFORE: int = 30   # block trading N minutes before event
NEWS_BLOCK_MINUTES_AFTER: int = 15    # block trading N minutes after event

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_TO_SUPABASE: bool = True
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
