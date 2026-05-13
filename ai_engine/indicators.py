"""
Technical indicator calculations.
All functions accept a pandas DataFrame with OHLCV columns and return
a new DataFrame with the indicator columns appended.
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd

import config

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# EMA
# ─────────────────────────────────────────────────────────────────────────────

def add_ema(df: pd.DataFrame, period: int, col: str = "close") -> pd.DataFrame:
    df[f"ema_{period}"] = df[col].ewm(span=period, adjust=False).mean()
    return df


def add_all_emas(df: pd.DataFrame) -> pd.DataFrame:
    df = add_ema(df, config.EMA_FAST)
    df = add_ema(df, config.EMA_MID)
    df = add_ema(df, config.EMA_SLOW)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# RSI
# ─────────────────────────────────────────────────────────────────────────────

def add_rsi(df: pd.DataFrame, period: int = config.RSI_PERIOD) -> pd.DataFrame:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi"] = df["rsi"].fillna(50)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# MACD
# ─────────────────────────────────────────────────────────────────────────────

def add_macd(
    df: pd.DataFrame,
    fast: int = config.MACD_FAST,
    slow: int = config.MACD_SLOW,
    signal: int = config.MACD_SIGNAL,
) -> pd.DataFrame:
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd_line"]   = ema_fast - ema_slow
    df["macd_signal"] = df["macd_line"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"]   = df["macd_line"] - df["macd_signal"]
    return df


# ─────────────────────────────────────────────────────────────────────────────
# ATR
# ─────────────────────────────────────────────────────────────────────────────

def add_atr(df: pd.DataFrame, period: int = config.ATR_PERIOD) -> pd.DataFrame:
    high_low  = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close  = (df["low"]  - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.ewm(com=period - 1, min_periods=period).mean()
    df["atr"] = df["atr"].fillna(df["atr"].median())
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Bollinger Bands
# ─────────────────────────────────────────────────────────────────────────────

def add_bollinger_bands(
    df: pd.DataFrame,
    period: int = config.BB_PERIOD,
    std_dev: float = config.BB_STD,
) -> pd.DataFrame:
    df["bb_mid"]   = df["close"].rolling(period).mean()
    rolling_std    = df["close"].rolling(period).std()
    df["bb_upper"] = df["bb_mid"] + std_dev * rolling_std
    df["bb_lower"] = df["bb_mid"] - std_dev * rolling_std
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"]
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Smart Money Concepts (simplified detection)
# ─────────────────────────────────────────────────────────────────────────────

def detect_break_of_structure(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """
    Bullish BOS: price closes above the highest high of the last N candles.
    Bearish BOS: price closes below the lowest low of the last N candles.
    """
    df["bos_bull"] = df["close"] > df["high"].shift(1).rolling(lookback).max()
    df["bos_bear"] = df["close"] < df["low"].shift(1).rolling(lookback).min()
    return df


def detect_liquidity_sweep(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """
    Bullish sweep: wick pierces below recent swing low then closes above it.
    Bearish sweep: wick pierces above recent swing high then closes below it.
    """
    recent_high = df["high"].shift(1).rolling(lookback).max()
    recent_low  = df["low"].shift(1).rolling(lookback).min()

    df["liq_sweep_bull"] = (df["low"] < recent_low) & (df["close"] > recent_low)
    df["liq_sweep_bear"] = (df["high"] > recent_high) & (df["close"] < recent_high)
    return df


def detect_fair_value_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Bullish FVG : gap between candle[i-2] high and candle[i] low (price never filled).
    Bearish FVG : gap between candle[i-2] low  and candle[i] high.
    """
    df["fvg_bull"] = df["low"] > df["high"].shift(2)
    df["fvg_bear"] = df["high"] < df["low"].shift(2)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Volatility label
# ─────────────────────────────────────────────────────────────────────────────

def classify_volatility(df: pd.DataFrame) -> str:
    """Return LOW / MEDIUM / HIGH based on latest ATR vs rolling average."""
    if "atr" not in df.columns:
        return "MEDIUM"
    latest_atr = df["atr"].iloc[-1]
    avg_atr    = df["atr"].rolling(50).mean().iloc[-1]
    if pd.isna(avg_atr) or avg_atr == 0:
        return "MEDIUM"
    ratio = latest_atr / avg_atr
    if ratio < 0.8:
        return "LOW"
    if ratio > 1.4:
        return "HIGH"
    return "MEDIUM"


# ─────────────────────────────────────────────────────────────────────────────
# Master function — compute all indicators at once
# ─────────────────────────────────────────────────────────────────────────────

def compute_all(df: pd.DataFrame) -> pd.DataFrame:
    df = add_all_emas(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_atr(df)
    df = add_bollinger_bands(df)
    df = detect_break_of_structure(df)
    df = detect_liquidity_sweep(df)
    df = detect_fair_value_gap(df)
    logger.debug("Indicators computed. Latest close=%.4f", df["close"].iloc[-1])
    return df
