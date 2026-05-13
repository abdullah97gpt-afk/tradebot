"""
News impact filter.

Checks whether a high-impact economic event is scheduled within the
blocking window around the current time.

Primary source : ForexFactory calendar RSS (no key required).
Fallback source: NewsAPI (requires NEWS_API_KEY).
Offline mode   : returns LOW impact when all fetches fail.
"""

from __future__ import annotations

import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

import config

logger = logging.getLogger(__name__)

_HIGH_KEYWORDS = [
    "non-farm", "nfp", "fed", "fomc", "interest rate", "cpi", "ppi",
    "gdp", "unemployment", "payroll", "inflation", "powell",
    "gold", "xau", "dollar", "dxy",
]


# ─────────────────────────────────────────────────────────────────────────────
# Public interface
# ─────────────────────────────────────────────────────────────────────────────

def get_news_impact() -> str:
    """
    Returns 'HIGH', 'MEDIUM', or 'LOW'.
    HIGH means: do not trade — a major event is within the blocking window.
    """
    if not config.NEWS_FILTER_ENABLED:
        return "LOW"

    try:
        impact = _check_forexfactory_rss()
        logger.info("News impact: %s", impact)
        return impact
    except Exception as exc:
        logger.warning("ForexFactory check failed (%s) — falling back to NewsAPI", exc)

    if config.NEWS_API_KEY:
        try:
            impact = _check_newsapi()
            logger.info("NewsAPI news impact: %s", impact)
            return impact
        except Exception as exc2:
            logger.warning("NewsAPI check failed: %s", exc2)

    logger.info("News filter offline — defaulting to LOW impact")
    return "LOW"


# ─────────────────────────────────────────────────────────────────────────────
# ForexFactory RSS (free, no key)
# ─────────────────────────────────────────────────────────────────────────────

def _check_forexfactory_rss() -> str:
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
    resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    now = datetime.now(timezone.utc)
    block_before = timedelta(minutes=config.NEWS_BLOCK_MINUTES_BEFORE)
    block_after  = timedelta(minutes=config.NEWS_BLOCK_MINUTES_AFTER)

    for event in root.findall(".//event"):
        impact_el = event.find("impact")
        if impact_el is None or impact_el.text not in ("High", "Medium"):
            continue

        currency_el = event.find("country")
        if currency_el is not None and currency_el.text not in config.HIGH_IMPACT_CURRENCIES + ["US", "USD"]:
            continue

        date_el = event.find("date")
        time_el = event.find("time")
        if date_el is None or time_el is None:
            continue

        try:
            event_dt = datetime.strptime(
                f"{date_el.text} {time_el.text}", "%m-%d-%Y %I:%M%p"
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        if (event_dt - block_before) <= now <= (event_dt + block_after):
            if impact_el.text == "High":
                return "HIGH"
            return "MEDIUM"

    return "LOW"


# ─────────────────────────────────────────────────────────────────────────────
# NewsAPI fallback
# ─────────────────────────────────────────────────────────────────────────────

def _check_newsapi() -> str:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "gold XAU Federal Reserve interest rate",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": config.NEWS_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    articles = data.get("articles", [])
    if not articles:
        return "LOW"

    now = datetime.now(timezone.utc)
    for article in articles:
        published_str = article.get("publishedAt", "")
        if not published_str:
            continue
        try:
            pub_dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        except ValueError:
            continue

        age_minutes = (now - pub_dt).total_seconds() / 60
        if age_minutes > 60:
            continue

        title = (article.get("title") or "").lower()
        desc  = (article.get("description") or "").lower()
        text  = title + " " + desc

        for keyword in _HIGH_KEYWORDS:
            if keyword in text:
                return "MEDIUM"  # NewsAPI can't reliably flag HIGH

    return "LOW"
