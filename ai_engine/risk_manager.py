"""
Risk management: compute entry, stop loss, take profit and validate R:R ratio.
"""

from __future__ import annotations

import logging
import pandas as pd

import config

logger = logging.getLogger(__name__)


def compute_levels(
    df: pd.DataFrame,
    direction: str,  # "BUY" or "SELL"
) -> dict[str, float] | None:
    """
    Returns {entry, stop_loss, take_profit, risk_reward} or None if R:R invalid.

    Stop-loss  : ATR × ATR_SL_MULTIPLIER from entry
    Take-profit: ATR × ATR_TP_MULTIPLIER from entry
    """
    latest = df.iloc[-1]
    entry = float(latest["close"])
    atr   = float(latest["atr"]) if "atr" in df.columns else 1.0

    sl_distance = atr * config.ATR_SL_MULTIPLIER
    tp_distance = atr * config.ATR_TP_MULTIPLIER

    if direction == "BUY":
        stop_loss   = entry - sl_distance
        take_profit = entry + tp_distance
    else:  # SELL
        stop_loss   = entry + sl_distance
        take_profit = entry - tp_distance

    # Sanity check — prices must be positive
    if stop_loss <= 0 or take_profit <= 0:
        logger.warning("Invalid price levels: entry=%.4f sl=%.4f tp=%.4f", entry, stop_loss, take_profit)
        return None

    risk        = abs(entry - stop_loss)
    reward      = abs(take_profit - entry)
    risk_reward = round(reward / risk, 2) if risk > 0 else 0.0

    if risk_reward < config.MIN_RISK_REWARD:
        logger.info(
            "R:R %.2f below minimum %.2f — rejecting signal",
            risk_reward, config.MIN_RISK_REWARD,
        )
        return None

    return {
        "entry":       round(entry, 4),
        "stop_loss":   round(stop_loss, 4),
        "take_profit": round(take_profit, 4),
        "risk_reward": risk_reward,
    }


def validate_signal_payload(payload: dict) -> bool:
    """
    Final validation before sending to Supabase.
    Returns True if the payload looks safe to store.
    """
    required_fields = ["symbol", "mode", "signal", "confidence", "entry",
                       "stop_loss", "take_profit", "risk_reward",
                       "trend", "volatility", "news_impact", "reasons"]

    for field in required_fields:
        if field not in payload:
            logger.error("Missing field in signal payload: %s", field)
            return False

    if payload["signal"] not in ("BUY", "SELL", "WAIT"):
        logger.error("Invalid signal value: %s", payload["signal"])
        return False

    if not isinstance(payload["confidence"], int) or not (0 <= payload["confidence"] <= 100):
        logger.error("Invalid confidence: %s", payload["confidence"])
        return False

    if payload["signal"] != "WAIT":
        for price_field in ("entry", "stop_loss", "take_profit"):
            val = payload.get(price_field)
            if val is None or val <= 0:
                logger.error("Invalid price in field %s: %s", price_field, val)
                return False

    return True
