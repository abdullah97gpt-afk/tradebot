# XAUUSD AI Signal Platform

Personal-use AI-assisted XAUUSD / Gold trading signal dashboard.

**Signal only — no order execution, no financial advice.**

---

## Architecture

```
GitHub Actions (every 5 min)
        │
        ▼
  ai_engine/main.py
  ├─ market_data.py   ← fetch OHLCV (Alpha Vantage / Twelve Data / synthetic)
  ├─ indicators.py    ← EMA, RSI, MACD, ATR, BB, SMC structures
  ├─ news_filter.py   ← ForexFactory RSS calendar check
  ├─ signal_engine.py ← multi-condition scoring → BUY / SELL / WAIT
  ├─ risk_manager.py  ← ATR-based SL/TP, R:R validation
  └─ supabase_client.py ← insert signal to Supabase
        │
        ▼
   Supabase PostgreSQL
        │  (Realtime)
        ▼
  Cloudflare Pages (frontend/)
  ├─ dashboard.html   ← live signal + chart + history
  └─ index.html       ← landing page
```

---

## Quick Start

### 1. Supabase

1. Create project at [supabase.com](https://supabase.com)
2. Run `database/supabase_schema.sql` in the SQL Editor
3. Copy **URL**, **anon key**, and **service role key**

### 2. Frontend

1. Edit `frontend/js/config.js` — add your Supabase URL and anon key
2. Deploy `frontend/` to Cloudflare Pages (build output dir: `frontend`)

### 3. AI Engine

```bash
cd ai_engine
python -m venv venv && venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
python main.py         # test run
```

### 4. GitHub Actions (production)

1. Push repo to GitHub
2. Add secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
3. Workflow runs automatically every 5 minutes

---

## Docs

| Guide | File |
|-------|------|
| Supabase setup | `docs/setup_supabase.md` |
| Cloudflare Pages deploy | `docs/setup_cloudflare.md` |
| GitHub Actions | `docs/setup_github_actions.md` |
| PythonAnywhere | `docs/setup_pythonanywhere.md` |
| Local testing | `docs/local_testing.md` |

---

## Signal Format

```json
{
  "symbol":      "XAUUSD",
  "mode":        "SCALPING",
  "signal":      "BUY",
  "confidence":  82,
  "entry":       2350.20,
  "stop_loss":   2346.80,
  "take_profit": 2357.00,
  "risk_reward": 2.0,
  "trend":       "BULLISH",
  "volatility":  "MEDIUM",
  "news_impact": "LOW",
  "reasons":     ["EMA bullish alignment (20 > 50 > 200)", "RSI bullish zone (58.3)", "…"]
}
```

---

## Indicators Used

- EMA 20 / 50 / 200 — trend direction and stack alignment
- RSI 14 — momentum confirmation
- MACD (12/26/9) — crossover and histogram
- ATR 14 — volatility and SL/TP sizing
- Bollinger Bands (20, 2σ) — price position in range
- Break of Structure (BOS) — SMC trend shift detection
- Liquidity Sweep — SMC stop-hunt identification
- Fair Value Gap (FVG) — SMC imbalance zones

---

## Disclaimer

This tool is for personal educational use only. It does not execute trades, manage money, or provide financial advice. Past signal performance does not guarantee future results. Trade at your own risk.
