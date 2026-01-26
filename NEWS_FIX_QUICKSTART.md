# 🚀 QUICK START: Fix News Fetching Every Hour

## TL;DR - 3 Steps to Fix

### 1. Deploy to Render (2 minutes)

```bash
git add .
git commit -m "Fix hourly news fetch with external cron"
git push origin main
```

Wait for Render to deploy (~5 minutes). Check: https://stocxer-ai.onrender.com/health

### 2. Set Up Cron Job (3 minutes)

**Go to**: [https://cron-job.org/en/members/jobs/](https://cron-job.org/en/members/jobs/)

**Click**: "Create cronjob"

**Fill in**:
- Title: `TradeWise News`
- URL: `https://stocxer-ai.onrender.com/fetch-news`
- Schedule: `Every 1 hour(s)` or `0 * * * *`
- Method: `GET`

**Click**: "Create cronjob"

### 3. Test (1 minute)

```bash
# Test manually
curl https://stocxer-ai.onrender.com/fetch-news

# Should return:
# {"success":true,"articles_stored":3,"timestamp":"...","message":"..."}
```

## ✅ Done!

News will be fetched automatically every hour. No more manual intervention needed.

## Verify After 1 Hour

```bash
# Check latest news in Supabase
```

Or run:
```bash
python test_news_scheduler.py
```

---

**Questions?** Read [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) for full details.
