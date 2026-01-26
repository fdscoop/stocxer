# News Fetching with Render Cron Jobs

## Problem

The APScheduler in the FastAPI backend works locally, but on Render's free tier, **services go to sleep after 15 minutes of inactivity**, which stops the scheduler from running.

## Solution

Use **Render Cron Jobs** (or external cron services) to call the `/fetch-news` endpoint every hour.

## Option 1: Render Cron Jobs (Recommended for Paid Plans)

### Update `render.yaml`

Add a cron job service to your `render.yaml`:

```yaml
services:
  # Your existing web service
  - type: web
    name: tradewise
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      # ... your existing env vars ...
    healthCheckPath: /health

  # New cron job for news fetching
  - type: cron
    name: tradewise-news-fetcher
    schedule: "0 * * * *"  # Every hour at minute 0
    buildCommand: pip install -r requirements.txt
    startCommand: curl -X GET https://stocxer-ai.onrender.com/fetch-news
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
```

### Cron Schedule Examples

```bash
"0 * * * *"      # Every hour at minute 0
"*/30 * * * *"   # Every 30 minutes
"0 */2 * * *"    # Every 2 hours
"0 9-17 * * *"   # Every hour from 9 AM to 5 PM
```

## Option 2: EasyCron (Free Tier Compatible)

Since Render cron jobs are only available on paid plans, use a free external cron service like **EasyCron**:

1. Go to [EasyCron.com](https://www.easycron.com/) and sign up (free plan: 100 jobs/year)
2. Create a new cron job:
   - **URL**: `https://stocxer-ai.onrender.com/fetch-news`
   - **Cron Expression**: `0 * * * *` (every hour)
   - **Method**: GET
   - **Time Zone**: Asia/Kolkata (IST)

## Option 3: cron-job.org (Free, No Signup Required)

1. Go to [cron-job.org](https://cron-job.org)
2. Create a free account
3. Add a new cron job:
   - **Title**: TradeWise News Fetcher
   - **URL**: `https://stocxer-ai.onrender.com/fetch-news`
   - **Schedule**: Every hour
   - **Method**: GET

## Option 4: GitHub Actions (Free for Public Repos)

Create `.github/workflows/fetch-news.yml`:

```yaml
name: Fetch Market News

on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:  # Allow manual trigger

jobs:
  fetch-news:
    runs-on: ubuntu-latest
    steps:
      - name: Fetch News
        run: |
          curl -X GET https://stocxer-ai.onrender.com/fetch-news
```

## Verification

### Check Health Status

```bash
curl https://stocxer-ai.onrender.com/health
```

Response will show:
```json
{
  "status": "online",
  "service": "TradeWise API",
  "version": "1.0.0",
  "timestamp": "2026-01-26T...",
  "scheduler": {
    "status": "running",
    "jobs": [
      {
        "id": "news_fetch_job",
        "name": "Fetch Market News from Marketaux",
        "next_run": "2026-01-26T..."
      }
    ]
  },
  "news_service": "available"
}
```

### Manually Trigger News Fetch

```bash
curl https://stocxer-ai.onrender.com/fetch-news
```

Response:
```json
{
  "success": true,
  "articles_stored": 3,
  "timestamp": "2026-01-26T...",
  "message": "Successfully fetched and stored 3 articles"
}
```

### Check Database

Run the test script locally:

```bash
python test_news_scheduler.py
```

Or check in Supabase Dashboard:
```sql
SELECT COUNT(*) FROM market_news;
SELECT * FROM market_news ORDER BY fetched_at DESC LIMIT 5;
SELECT * FROM news_fetch_log ORDER BY fetch_time DESC LIMIT 5;
```

## Rate Limits

- **Marketaux API**: 100 requests/day
- **Fetching every 1 hour**: 24 requests/day
- **Safe margin**: 76 requests remaining for manual fetches

## Keeping Render Awake

The `/fetch-news` endpoint also keeps your Render service awake, preventing it from sleeping. If you're on the free tier, your service will sleep after 15 minutes, but the cron job will wake it up every hour.

## Current Configuration

- **Internal Scheduler**: APScheduler runs every 1 hour (may not work on Render free tier)
- **Startup Fetch**: News is fetched immediately when the app starts
- **External Trigger**: `/fetch-news` endpoint for cron services
- **Health Check**: `/health` shows scheduler status

## Recommendation

**For Production (Render Free Tier):**
1. Use **cron-job.org** or **GitHub Actions** to call `/fetch-news` every hour
2. Keep the internal APScheduler as a backup (works when service is awake)
3. Monitor via `/health` endpoint

**For Production (Render Paid):**
1. Use **Render Cron Jobs** (native integration)
2. Keep internal scheduler disabled to avoid duplicate fetches
3. Monitor via Render dashboard

## Next Steps

1. Choose your preferred cron solution (Option 2 or 3 recommended for free tier)
2. Set up the cron job with the URL: `https://stocxer-ai.onrender.com/fetch-news`
3. Test by checking the `/health` endpoint after an hour
4. Verify news is being stored in Supabase
