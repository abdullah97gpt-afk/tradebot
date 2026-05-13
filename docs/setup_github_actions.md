# GitHub Actions Setup Guide

The workflow at `.github/workflows/ai-signal-cron.yml` runs `ai_engine/main.py` every 5 minutes using a GitHub Actions cron schedule.

---

## Step 1: Push the Repo to GitHub

```bash
git add .
git commit -m "Add AI engine and workflow"
git push origin main
```

---

## Step 2: Add Repository Secrets

1. Go to your GitHub repository
2. Navigate to **Settings → Secrets and variables → Actions**
3. Click **New repository secret** for each of the following:

| Secret Name | Value | Required |
|-------------|-------|----------|
| `SUPABASE_URL` | `https://your-project-id.supabase.co` | **Yes** |
| `SUPABASE_SERVICE_ROLE_KEY` | Your service role key from Supabase | **Yes** |
| `MARKET_DATA_API_KEY` | Alpha Vantage or Twelve Data key | No |
| `NEWS_API_KEY` | NewsAPI.org key | No |

---

## Step 3: Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. If prompted, click **I understand my workflows, go ahead and enable them**
3. You should see `AI Signal Engine` in the workflow list

---

## Step 4: Verify the First Run

1. Click the **AI Signal Engine** workflow
2. Click **Run workflow → Run workflow** to trigger it manually
3. Watch the run — you should see:
   ```
   Run completed in X.XX seconds
   ```
4. Open your Supabase dashboard → **Table Editor → signals**
5. You should see a new row

---

## Step 5: Confirm Cron Schedule

After 5–10 minutes the workflow will fire automatically.  
The cron `*/5 * * * *` means: at minute 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55 of every hour.

> **Note**: GitHub Actions cron jobs can be delayed by 1–15 minutes during high load periods. This is normal and expected.

---

## Manual Trigger with Debug Mode

1. Go to **Actions → AI Signal Engine**
2. Click **Run workflow**
3. Set **Enable debug logging** to `true`
4. This will show full DEBUG-level logs including indicator values

---

## Cost

- GitHub Free plan: 2,000 minutes/month
- Each run takes ~15–30 seconds
- 5-minute cron = ~288 runs/day × 0.5 min = ~144 min/day = ~4,320 min/month
- **Exceeds free tier for public repos** — use a **public repository** (free unlimited minutes) or upgrade to GitHub Pro

### Recommendation: Use a public repository

Your secrets are never exposed even in public repos. The signal data is already public (Supabase anon key). This is safe.

---

## Disable the Engine Temporarily

To pause signal generation without deleting the workflow:
1. Go to **Actions → AI Signal Engine**
2. Click the `...` menu → **Disable workflow**
