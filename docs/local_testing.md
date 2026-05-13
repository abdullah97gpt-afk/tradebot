# Local Testing Guide

Run and test the entire platform on your local machine before deploying.

---

## Prerequisites

- Python 3.10 or 3.11
- A Supabase project with the schema applied (see `setup_supabase.md`)
- A browser (Chrome or Firefox recommended)

---

## Step 1: Set Up the AI Engine

```bash
cd ai_engine

# Create and activate virtual environment
python -m venv venv

# Windows PowerShell:
venv\Scripts\Activate.ps1

# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env and fill in your Supabase credentials
```

Open `.env` in any text editor and set:

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

Leave `MARKET_DATA_API_KEY` blank to use synthetic data for testing.

---

## Step 3: Run the AI Engine

```bash
# With virtual environment active:
python main.py
```

Expected output:
```
2026-01-01T12:00:00Z [INFO] main — ════════════════════════════════
2026-01-01T12:00:00Z [INFO] main — AI Engine run started at …
2026-01-01T12:00:00Z [INFO] main — Step 1/5 — Fetching market data…
2026-01-01T12:00:02Z [WARNING] main — MARKET_DATA_API_KEY not set — using synthetic demo data
2026-01-01T12:00:02Z [INFO] main — Received 250 candles. Latest close: 2351.2000
2026-01-01T12:00:02Z [INFO] main — Step 2/5 — Computing indicators…
2026-01-01T12:00:02Z [INFO] main — Step 3/5 — Checking news impact…
2026-01-01T12:00:03Z [INFO] main — News impact: LOW
2026-01-01T12:00:03Z [INFO] main — Step 4/5 — Generating signal…
2026-01-01T12:00:03Z [INFO] main — Signal: BUY | Confidence: 72% | Trend: BULLISH
2026-01-01T12:00:03Z [INFO] main — Step 5/5 — Pushing signal to Supabase…
2026-01-01T12:00:04Z [INFO] main — Signal saved. DB id: abc12345-…
2026-01-01T12:00:04Z [INFO] main — Run completed in 2.14 seconds
```

---

## Step 4: View the Frontend Locally

### Option A — Open directly

Simply open `frontend/dashboard.html` in your browser. Because all JS is loaded from CDN and the Supabase client uses HTTPS, it works without a local server.

### Option B — Local HTTP server (avoids any CORS issues)

```bash
# Python (from project root)
python -m http.server 8080

# Then visit: http://localhost:8080/frontend/dashboard.html
```

Or with Node.js:
```bash
npx serve frontend
```

---

## Step 5: Confirm Real-Time Updates

1. Open `dashboard.html` in your browser
2. In your browser's DevTools Console you should see:
   ```
   [realtime] signals channel status: SUBSCRIBED
   ```
3. Run `python main.py` again in the terminal
4. Within 1–2 seconds, the dashboard should flash and update with the new signal

---

## Step 6: Run the Engine on a Loop (local testing)

```bash
# Windows PowerShell — run every 30 seconds for quick testing
while ($true) { python main.py; Start-Sleep 30 }

# macOS/Linux
while true; do python main.py; sleep 30; done
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: supabase` | Activate venv: `venv\Scripts\Activate.ps1` |
| `KeyError: SUPABASE_URL` | Create `.env` file with your credentials |
| `CHANNEL_ERROR` in browser console | Check anon key in `frontend/js/config.js` |
| Dashboard shows "—" for all values | No signals in DB yet — run `python main.py` |
| `Signal insert returned no data` | Check Supabase service role key and RLS policies |
