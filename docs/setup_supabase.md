# Supabase Setup Guide

## 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click **New Project**
3. Choose a name (e.g., `xauusd-signal`) and set a strong database password
4. Select the region closest to you
5. Wait ~2 minutes for the project to provision

---

## 2. Run the Database Schema

1. In your project sidebar, go to **SQL Editor**
2. Click **New Query**
3. Open `database/supabase_schema.sql` from this project
4. Paste the entire contents into the editor
5. Click **Run** (or press `Ctrl+Enter`)
6. You should see: `Success. No rows returned`

---

## 3. Collect Your API Keys

Navigate to **Project Settings → API**:

| Key | Where used |
|-----|-----------|
| **Project URL** | Both frontend and AI engine |
| **anon / public key** | Frontend `js/config.js` only |
| **service_role / secret key** | AI engine `.env` and GitHub Secrets only |

> **Security rule**: Never put the `service_role` key in frontend code or commit it to git.

---

## 4. Configure the Frontend

Open `frontend/js/config.js` and replace:

```js
url:     "https://YOUR_PROJECT_ID.supabase.co",
anonKey: "YOUR_SUPABASE_ANON_KEY",
```

---

## 5. Verify Realtime Is Enabled

1. Go to **Database → Replication**
2. Confirm `signals` table is listed under **Source**
3. If not, run in SQL Editor:
   ```sql
   ALTER PUBLICATION supabase_realtime ADD TABLE public.signals;
   ```

---

## 6. Verify Row Level Security

Run this in SQL Editor to confirm RLS is active:

```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';
```

All four tables should show `rowsecurity = true`.

---

## 7. Test the Connection

In your browser console (on `dashboard.html`), you should see:

```
[realtime] signals channel status: SUBSCRIBED
```

If you see `CHANNEL_ERROR`, check that your anon key in `config.js` is correct.
