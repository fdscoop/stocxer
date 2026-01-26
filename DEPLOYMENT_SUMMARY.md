# NEWS FETCH EVERY HOUR - DEPLOYMENT GUIDE

## 🎯 Problem Solved

Your backend was configured to fetch news every 1 hour using APScheduler, but it wasn't working on Render because:
- **Render free tier puts services to sleep after 15 minutes of inactivity**
- When the service sleeps, the scheduler stops
- News was not being fetched and stored in the database

## ✅ Solution Implemented

### 1. **Internal Scheduler (Backup)**
   - APScheduler still runs every 1 hour when the service is awake
   - Fetches news on startup
   - Located in [main.py](main.py#L296-L320)

### 2. **Public Endpoint** (NEW)
   - `/fetch-news` - Can be called by external cron services
   - Returns JSON with number of articles stored
   - Keeps service awake when called
   - Located in [main.py](main.py#L431-L453)

### 3. **Enhanced Health Check** (UPDATED)
   - `/health` - Shows scheduler status and jobs
   - Reports if news service is available
   - Shows next run time for scheduled jobs
   - Located in [main.py](main.py#L407-L429)

## 🚀 Deployment Steps

### Step 1: Deploy to Render

```bash
# Commit and push your changes
git add .
git commit -m "Add hourly news fetch with external cron support"
git push origin main
```

Render will automatically redeploy. Wait for deployment to complete (~5 minutes).

### Step 2: Verify Deployment

```bash
# Check if API is online and endpoint exists
curl https://stocxer-ai.onrender.com/health | json_pp

# Test the fetch-news endpoint
curl https://stocxer-ai.onrender.com/fetch-news | json_pp
```

Expected response:
```json
{
  "success": true,
  "articles_stored": 3,
  "timestamp": "2026-01-26T...",
  "message": "Successfully fetched and stored 3 articles"
}
```

### Step 3: Set Up External Cron (REQUIRED for Free Tier)

#### **Option A: cron-job.org** (Recommended - Free, Simple)

1. Go to [https://cron-job.org](https://cron-job.org)
2. Click "Sign up" (free account)
3. After login, click "Create cronjob"
4. Fill in:
   - **Title**: `TradeWise News Fetcher`
   - **Address (URL)**: `https://stocxer-ai.onrender.com/fetch-news`
   - **Schedule**: 
     - Pattern: Every 1 hour(s)
     - Or use custom: `0 * * * *`
   - **Request method**: GET
   - **Notification**: Email on failure (optional)
5. Click "Create cronjob"

✅ **Done!** News will be fetched every hour automatically.

#### **Option B: GitHub Actions** (Free for Public Repos)

1. Create file `.github/workflows/fetch-news.yml`:

```yaml
name: Fetch Market News Hourly

on:
  schedule:
    - cron: '0 * * * *'  # Every hour at minute 0
  workflow_dispatch:  # Allow manual trigger

jobs:
  fetch-news:
    runs-on: ubuntu-latest
    steps:
      - name: Fetch Market News
        run: |
          RESPONSE=$(curl -s -w "\n%{http_code}" https://stocxer-ai.onrender.com/fetch-news)
          HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
          BODY=$(echo "$RESPONSE" | head -n -1)
          
          echo "HTTP Status: $HTTP_CODE"
          echo "Response: $BODY"
          
          if [ $HTTP_CODE -eq 200 ]; then
            echo "✅ News fetch successful"
          else
            echo "❌ News fetch failed"
            exit 1
          fi
```

2. Commit and push:

```bash
git add .github/workflows/fetch-news.yml
git commit -m "Add GitHub Actions for hourly news fetch"
git push
```

3. Enable workflow:
   - Go to your GitHub repo → Actions tab
   - Find "Fetch Market News Hourly" workflow
   - Click "Enable workflow"
   - Test by clicking "Run workflow"

#### **Option C: EasyCron** (100 Free Jobs/Year)

1. Go to [https://www.easycron.com/](https://www.easycron.com/)
2. Sign up for free account
3. Add new cron job:
   - **URL**: `https://stocxer-ai.onrender.com/fetch-news`
   - **Cron Expression**: `0 * * * *`
   - **HTTP Method**: GET
4. Save

## 📊 Monitoring & Verification

### Check if Cron is Working

**Method 1: Via API**
```bash
# Check recent news
curl https://stocxer-ai.onrender.com/news/sentiment | json_pp

# Check health
curl https://stocxer-ai.onrender.com/health | json_pp
```

**Method 2: Via Supabase Dashboard**
```sql
-- Check latest news
SELECT * FROM market_news 
ORDER BY fetched_at DESC 
LIMIT 10;

-- Check fetch log
SELECT * FROM news_fetch_log 
ORDER BY fetch_time DESC 
LIMIT 10;

-- Count articles per hour
SELECT 
  DATE_TRUNC('hour', fetched_at) as hour,
  COUNT(*) as articles_count
FROM market_news 
WHERE fetched_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

**Method 3: Via Test Script**
```bash
# Run local test to verify database
python test_news_scheduler.py
```

### What to Expect

- **First 24 hours**: ~24 fetch attempts (one per hour)
- **Articles per fetch**: 3-6 articles (depends on API availability)
- **Total articles/day**: ~72-144 articles
- **API requests/day**: ~24 requests (well under 100 limit)

### Troubleshooting

**Problem: No new articles in database**

1. Check cron-job.org execution log (if using cron-job.org)
2. Check GitHub Actions runs (if using GitHub Actions)
3. Manually trigger: `curl https://stocxer-ai.onrender.com/fetch-news`
4. Check Render logs for errors

**Problem: API returns 503**

- MARKETAUX_API_KEY not set in Render environment variables
- Go to Render Dashboard → Environment → Add `MARKETAUX_API_KEY`

**Problem: Duplicate articles**

- This is normal! The system uses `article_uuid` to prevent duplicates
- Database uses `UPSERT` to update existing articles

**Problem: Render service sleeping**

- External cron will wake it up automatically
- Each fetch request keeps service awake for 15 minutes

## 📋 Files Modified

| File | Changes |
|------|---------|
| [main.py](main.py) | ✅ Changed scheduler from 15 min to 1 hour<br>✅ Updated `/health` endpoint<br>✅ Added `/fetch-news` endpoint |
| [test_news_scheduler.py](test_news_scheduler.py) | ✨ NEW - Test script to verify news fetching |
| [NEWS_SCHEDULER_SETUP.md](NEWS_SCHEDULER_SETUP.md) | ✨ NEW - Detailed cron setup guide |
| [setup_news_cron.sh](setup_news_cron.sh) | ✨ NEW - Automated setup script |
| [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) | ✨ NEW - This file |

## 🎓 Quick Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check service status & scheduler |
| `/fetch-news` | GET | Manually trigger news fetch |
| `/news/sentiment` | GET | Get latest sentiment analysis |

### Cron Expressions

| Expression | Meaning |
|------------|---------|
| `0 * * * *` | Every hour at minute 0 |
| `*/30 * * * *` | Every 30 minutes |
| `0 */2 * * *` | Every 2 hours |
| `0 9-17 * * 1-5` | Every hour 9 AM-5 PM, Mon-Fri |

### Rate Limits

- **Marketaux API**: 100 requests/day
- **Current usage**: ~24 requests/day (1 per hour)
- **Remaining**: 76 requests for manual fetches

## ✅ Success Checklist

- [ ] Code changes committed and pushed to GitHub
- [ ] Render deployment successful
- [ ] `/health` endpoint returns scheduler info
- [ ] `/fetch-news` endpoint returns success
- [ ] Cron job configured on cron-job.org or GitHub Actions
- [ ] First hourly fetch completed successfully
- [ ] News visible in Supabase `market_news` table
- [ ] Fetch logs visible in `news_fetch_log` table

## 🎯 Next Steps

1. **Deploy now**: Push changes to Render
2. **Set up cron**: Use cron-job.org (5 minutes)
3. **Wait 1 hour**: Let the first fetch run
4. **Verify**: Check Supabase for new articles
5. **Monitor**: Check daily for the first week

## 📞 Need Help?

Run the automated test:
```bash
python test_news_scheduler.py
```

Check the setup script:
```bash
./setup_news_cron.sh
```

Or manually verify:
```bash
curl https://stocxer-ai.onrender.com/health | json_pp
curl https://stocxer-ai.onrender.com/fetch-news | json_pp
```

---

**Last Updated**: January 26, 2026
**Backend URL**: https://stocxer-ai.onrender.com
**Frontend URL**: https://stocxer.in
