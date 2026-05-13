# Cloudflare Pages Deployment Guide

## Overview

Cloudflare Pages hosts the `frontend/` folder as a static site with global CDN distribution — completely free on the Free plan.

---

## Option A — Deploy via GitHub (Recommended)

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/xauusd-signal.git
git push -u origin main
```

### Step 2: Create a Cloudflare Pages Project

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com)
2. Navigate to **Workers & Pages → Pages**
3. Click **Create a project → Connect to Git**
4. Authorize Cloudflare to access your GitHub account
5. Select your `xauusd-signal` repository
6. Click **Begin setup**

### Step 3: Configure Build Settings

| Setting | Value |
|---------|-------|
| **Production branch** | `main` |
| **Framework preset** | None |
| **Build command** | *(leave empty)* |
| **Build output directory** | `frontend` |

Click **Save and Deploy**.

### Step 4: Your Site Is Live

Cloudflare will give you a URL like:  
`https://xauusd-signal.pages.dev`

Every push to `main` automatically redeploys.

---

## Option B — Deploy via Wrangler CLI

```bash
npm install -g wrangler
wrangler login
wrangler pages deploy frontend --project-name xauusd-signal
```

---

## Custom Domain (Optional)

1. In your Pages project, go to **Custom domains**
2. Click **Set up a custom domain**
3. Enter your domain (e.g., `signals.yourdomain.com`)
4. Follow the DNS instructions

---

## Environment Variables

This frontend has **no** server-side environment variables — the Supabase URL and anon key are embedded in `js/config.js`. This is safe because:
- The anon key is public by design
- Row Level Security in Supabase limits what the anon key can read/write
- The service role key is never in frontend code

---

## Notes

- The site is fully static — no build step required
- Lightweight Charts and Tailwind load from CDN
- Supabase JS client loads from CDN via ES module import
