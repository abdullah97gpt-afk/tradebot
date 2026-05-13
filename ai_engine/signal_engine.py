"""
Core signal generation engine.

Reads the processed DataFrame (with all indicators) and returns a
structured signal dict ready for Supabase insertion.
"""

from __future__ import annotations

import logging
import pandas as pd

import config
import risk_manager

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Public interface
# ─────────────────────────────────────────────────────────────────────────────

def generate_signal(df: pd.DataFrame, news_impact: str = "LOW") -> dict:
    """
    Analyse the latest bar and return a complete signal dictionary.
    Always returns a dict — worst case it's a WAIT signal.
    """
    if len(df) < config.EMA_SLOW:
        logger.warning("Not enough data (%d candles) to generate signal", len(df))
        return _wait_signal("Insufficient candle history", news_impact)

    # Block trading during high-impact news
    if news_impact == "HIGH":
        logger.info("High-impact news detected — emitting WAIT signal")
        return _wait_signal("High-impact news event in progress", news_impact)

    scores = _score_conditions(df)
    bull_score = scores["bull"]
    bear_score = scores["bear"]
    reasons    = scores["reasons"]

    # ── Determine direction ──────────────────────────────────────────────────
    if bull_score >= 4 and bull_score > bear_score:
        direction = "BUY"
        confidence = _calc_confidence(bull_score, bear_score, max_conditions=8)
    elif bear_score >= 4 and bear_score > bull_score:
        direction = "SELL"
        confidence = _calc_confidence(bear_score, bull_score, max_conditions=8)
    else:
        return _wait_signal("Insufficient signal alignment", news_impact, reasons)

    # ── Confidence gate ──────────────────────────────────────────────────────
    if confidence < config.MIN_CONFIDENCE:
        return _wait_signal(
            f"Confidence {confidence}% below threshold {config.MIN_CONFIDENCE}%",
            news_impact,
            reasons,
        )

    # ── Risk levels ──────────────────────────────────────────────────────────
    levels = risk_manager.compute_levels(df, direction)
    if levels is None:
        return _wait_signal("Risk/reward requirements not met", news_impact, reasons)

    # ── Build signal ─────────────────────────────────────────────────────────
    trend      = _detect_trend(df)
    volatility = _detect_volatility(df)
    signal_reasons = [r for r in reasons if r["side"] == direction]
    reason_texts   = [r["text"] for r in signal_reasons]

    if news_impact == "MEDIUM":
        reason_texts.append("Medium-impact news — trade with caution")

    payload = {
        "symbol":      config.SYMBOL,
        "mode":        config.ENGINE_MODE,
        "signal":      direction,
        "confidence":  confidence,
        "entry":       levels["entry"],
        "stop_loss":   levels["stop_loss"],
        "take_profit": levels["take_profit"],
        "risk_reward": levels["risk_reward"],
        "trend":       trend,
        "volatility":  volatility,
        "news_impact": news_impact,
        "reasons":     reason_texts,
    }

    logger.info(
        "Signal generated: %s | conf=%d%% | entry=%.4f | SL=%.4f | TP=%.4f | R:R=%.2f",
        direction, confidence, levels["entry"], levels["stop_loss"],
        levels["take_profit"], levels["risk_reward"],
    )
    return payload


# ─────────────────────────────────────────────────────────────────────────────
# Scoring conditions
# ─────────────────────────────────────────────────────────────────────────────

def _score_conditions(df: pd.DataFrame) -> dict:
    latest = df.iloc[-1]
    prev   = df.iloc[-2]

    close = latest["close"]
    bull_score = 0
    bear_score = 0
    reasons: list[dict] = []

    # 1. EMA stack alignment
    ema20  = latest.get("ema_20",  close)
    ema50  = latest.get("ema_50",  close)
    ema200 = latest.get("ema_200", close)

    if ema20 > ema50 > ema200:
        bull_score += 2
        reasons.append({"side": "BUY",  "text": "EMA bullish alignment (20 > 50 > 200)"})
    elif ema20 < ema50 < ema200:
        bear_score += 2
        reasons.append({"side": "SELL", "text": "EMA bearish alignment (20 < 50 < 200)"})

    # 2. Price vs EMA-200
    if close > ema200:
        bull_score += 1
        reasons.append({"side": "BUY",  "text": "Price above EMA-200"})
    else:
        bear_score += 1
        reasons.append({"side": "SELL", "text": "Price below EMA-200"})

    # 3. RSI confirmation (not overbought/oversold, trending in direction)
    rsi = latest.get("rsi", 50)
    if 45 < rsi < 70:
        bull_score += 1
        reasons.append({"side": "BUY",  "text": f"RSI bullish zone ({rsi:.1f})"})
    elif 30 < rsi < 55:
        bear_score += 1
        reasons.append({"side": "SELL", "text": f"RSI bearish zone ({rsi:.1f})"})

    # 4. MACD cross / histogram
    macd_hist      = latest.get("macd_hist",   0)
    prev_macd_hist = prev.get("macd_hist",     0)
    if macd_hist > 0 and prev_macd_hist <= 0:
        bull_score += 1
        reasons.append({"side": "BUY",  "text": "MACD bullish crossover"})
    elif macd_hist < 0 and prev_macd_hist >= 0:
        bear_score += 1
        reasons.append({"side": "SELL", "text": "MACD bearish crossover"})
    elif macd_hist > 0:
        bull_score += 1
        reasons.append({"side": "BUY",  "text": "MACD histogram positive"})
    elif macd_hist < 0:
        bear_score += 1
        reasons.append({"side": "SELL", "text": "MACD histogram negative"})

    # 5. Bollinger Band position
    bb_upper = latest.get("bb_upper", close + 1)
    bb_lower = latest.get("bb_lower", close - 1)
    bb_mid   = latest.get("bb_mid",   close)

    if close > bb_mid and close < bb_upper:
        bull_score += 1
        reasons.append({"side": "BUY",  "text": "Price in upper Bollinger Band zone"})
    elif close < bb_mid and close > bb_lower:
        bear_score += 1
        reasons.append({"side": "SELL", "text": "Price in lower Bollinger Band zone"})

    # 6. Smart Money: Break of Structure
    if latest.get("bos_bull", False):
        bull_score += 1
        reasons.append({"side": "BUY",  "text": "Bullish Break of Structure detected"})
    if latest.get("bos_bear", False):
        bear_score += 1
        reasons.append({"side": "SELL", "text": "Bearish Break of Structure detected"})

    # 7. Liquidity Sweep
    if latest.get("liq_sweep_bull", False):
        bull_score += 1
        reasons.append({"side": "BUY",  "text": "Bullish liquidity sweep (stop hunt)"})
    if latest.get("liq_sweep_bear", False):
        bear_score += 1
        reasons.append({"side": "SELL", "text": "Bearish liquidity sweep (stop hunt)"})

    # 8. Fair Value Gap
    if latest.get("fvg_bull", False):
        bull_score += 1
        reasons.append({"side": "BUY",  "text": "Bullish Fair Value Gap present"})
    if latest.get("fvg_bear", False):
        bear_score += 1
        reasons.append({"side": "SELL", "text": "Bearish Fair Value Gap present"})

    return {"bull": bull_score, "bear": bear_score, "reasons": reasons}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _calc_confidence(primary: int, opposing: int, max_conditions: int) -> int:
    """Score → 0-100 confidence integer."""
    net = primary - opposing
    raw = (net / max_conditions) * 100
    return max(0, min(100, int(round(raw + (primary / max_conditions) * 20))))


def _detect_trend(df: pd.DataFrame) -> str:
    latest = df.iloc[-1]
    ema20  = latest.get("ema_20",  latest["close"])
    ema200 = latest.get("ema_200", latest["close"])
    if ema20 > ema200 * 1.001:
        return "BULLISH"
    if ema20 < ema200 * 0.999:
        return "BEARISH"
    return "NEUTRAL"


def _detect_volatility(df: pd.DataFrame) -> str:
    if "atr" not in df.columns:
        return "MEDIUM"
    latest_atr = df["atr"].iloc[-1]
    avg_atr    = df["atr"].rolling(50).mean().iloc[-1]
    if pd.isna(avg_atr) or avg_atr == 0:
        return "MEDIUM"
    ratio = latest_atr / avg_atr
    if ratio > 1.5:
        return "HIGH"
    if ratio < 0.7:
        return "LOW"
    return "MEDIUM"


def _wait_signal(reason: str, news_impact: str = "LOW", existing_reasons: list | None = None) -> dict:
    latest_close = 0.0
    reasons_out = [reason]
    if existing_reasons:
        reasons_out += [r["text"] for r in existing_reasons[:3]]

    return {
        "symbol":      config.SYMBOL,
        "mode":        config.ENGINE_MODE,
        "signal":      "WAIT",
        "confidence":  0,
        "entry":       None,
        "stop_loss":   None,
        "take_profit": None,
        "risk_reward": None,
        "trend":       "NEUTRAL",
        "volatility":  "MEDIUM",
        "news_impact": news_impact,
        "reasons":     reasons_out,
    }
