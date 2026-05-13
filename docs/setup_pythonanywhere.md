# PythonAnywhere Setup Guide

PythonAnywhere is an alternative to GitHub Actions for running the AI engine. It runs the script on a schedule from a persistent cloud Linux environment.

---

## Account Requirements

| Plan | Scheduled tasks | Minimum interval |
|------|----------------|-----------------|
| Free (Beginner) | 1 task | Once daily only |
| Hacker ($5/mo) | Unlimited | Every hour minimum |
| Web Dev ($12/mo) | Unlimited | Every hour minimum |

> **Limitation**: PythonAnywhere free accounts cannot run tasks every 5 minutes. The minimum interval for paid accounts is also 1 hour via the standard scheduler.
>
> **Workaround for 5-minute intervals on paid accounts**: Use an "Always-on task" that runs a Python loop with `time.sleep(300)`.

---

## Option A — Hourly Scheduled Task (Free/Paid)

This runs the engine once per hour instead of every 5 minutes.

### Step 1: Upload Your Code

1. Go to [pythonanywhere.com](https://www.pythonanywhere.com) and log in
2. Open a **Bash console**
3. Clone your repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/xauusd-signal.git
   cd xauusd-signal/ai_engine
   ```

### Step 2: Create a Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Set Environment Variables

```bash
# Create a .env file (NOT committed to git)
cat > .env << 'EOF'
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
MARKET_DATA_API_KEY=your-alpha-vantage-key
NEWS_API_KEY=your-newsapi-key
EOF
```

### Step 4: Test Manually

```bash
cd ~/xauusd-signal/ai_engine
source venv/bin/activate
python main.py
```

You should see the engine run and exit with `Run completed in X.XX seconds`.

### Step 5: Create Scheduled Task

1. Go to **Dashboard → Tasks**
2. Click **Add a new scheduled task**
3. Set the command:
   ```
   /home/YOUR_USERNAME/xauusd-signal/ai_engine/venv/bin/python /home/YOUR_USERNAME/xauusd-signal/ai_engine/main.py
   ```
4. Set the interval to **Hourly** (or daily on free plan)
5. Click **Create**

---

## Option B — Always-On Task (Paid Plans Only)

This achieves true 5-minute intervals using a persistent loop.

### Create `ai_engine/loop_runner.py`

```python
"""
Persistent loop runner for PythonAnywhere Always-On tasks.
Runs main.py every 5 minutes indefinitely.
"""
import time
import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("loop")

SCRIPT = Path(__file__).parent / "main.py"
INTERVAL = 300  # 5 minutes

while True:
    logger.info("--- Cycle start ---")
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            timeout=240,
            check=False,
        )
        if result.returncode != 0:
            logger.warning("main.py exited with code %d", result.returncode)
    except subprocess.TimeoutExpired:
        logger.error("main.py timed out after 240 seconds")
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)

    logger.info("Sleeping %d seconds…", INTERVAL)
    time.sleep(INTERVAL)
```

### Add as Always-On Task

1. Go to **Dashboard → Tasks → Always-on tasks**
2. Click **Add a new always-on task**
3. Command:
   ```
   /home/YOUR_USERNAME/xauusd-signal/ai_engine/venv/bin/python /home/YOUR_USERNAME/xauusd-signal/ai_engine/loop_runner.py
   ```

---

## Updating the Code

```bash
cd ~/xauusd-signal
git pull origin main
```

If you changed `requirements.txt`:
```bash
source ai_engine/venv/bin/activate
pip install -r ai_engine/requirements.txt
```

Then restart your scheduled/always-on task from the PythonAnywhere dashboard.

---

## Recommendation

For true 5-minute cycles, **GitHub Actions is the better choice** (free for public repos, no server management). Use PythonAnywhere if you need a dedicated persistent environment or prefer not to use GitHub Actions.
