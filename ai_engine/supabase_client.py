"""
Supabase client wrapper.

Uses the supabase-py library with the SERVICE ROLE KEY — only used in the
AI engine, never in the frontend.
"""

from __future__ import annotations

import logging
from typing import Any

from supabase import create_client, Client

import config

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
        logger.debug("Supabase client initialised")
    return _client


# ─────────────────────────────────────────────────────────────────────────────
# Signals
# ─────────────────────────────────────────────────────────────────────────────

def insert_signal(payload: dict) -> dict | None:
    """Insert a signal row and return the inserted record."""
    try:
        client = get_client()
        # Remove None values — Supabase rejects nulls in non-nullable numeric cols
        clean = {k: v for k, v in payload.items() if v is not None}
        result = client.table("signals").insert(clean).execute()
        if result.data:
            logger.info("Signal inserted: id=%s signal=%s", result.data[0].get("id"), payload.get("signal"))
            return result.data[0]
        logger.warning("Signal insert returned no data: %s", result)
        return None
    except Exception as exc:
        logger.error("Failed to insert signal: %s", exc)
        return None


def get_latest_signals(limit: int = 50) -> list[dict]:
    try:
        client = get_client()
        result = (
            client.table("signals")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.error("Failed to fetch signals: %s", exc)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Market data
# ─────────────────────────────────────────────────────────────────────────────

def insert_market_data(rows: list[dict]) -> bool:
    """Bulk insert OHLCV rows."""
    if not rows:
        return True
    try:
        client = get_client()
        client.table("market_data").insert(rows).execute()
        logger.debug("Inserted %d market_data rows", len(rows))
        return True
    except Exception as exc:
        logger.error("Failed to insert market_data: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Settings
# ─────────────────────────────────────────────────────────────────────────────

def get_setting(key: str, default: Any = None) -> Any:
    try:
        client = get_client()
        result = client.table("settings").select("value").eq("key", key).single().execute()
        if result.data:
            return result.data["value"]
        return default
    except Exception:
        return default


def upsert_setting(key: str, value: Any) -> bool:
    try:
        client = get_client()
        client.table("settings").upsert({"key": key, "value": value}).execute()
        return True
    except Exception as exc:
        logger.error("Failed to upsert setting %s: %s", key, exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

def log_to_db(level: str, message: str, context: dict | None = None) -> None:
    """Write a log entry to the Supabase logs table (fire-and-forget)."""
    if not config.LOG_TO_SUPABASE:
        return
    try:
        client = get_client()
        client.table("logs").insert({
            "level":   level.upper(),
            "message": message,
            "context": context or {},
        }).execute()
    except Exception as exc:
        logger.debug("DB log write failed: %s", exc)
