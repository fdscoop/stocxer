# Tradient News API Integration

## Overview

TradeWise now uses **Tradient API** as the primary news source with **Marketaux** as fallback.

### Why Tradient?

| Feature | Tradient (Primary) | Marketaux (Fallback) |
|---------|-------------------|---------------------|
| Articles per fetch | 50+ | 3 |
| Daily limit | Unlimited | 100 requests |
| Pre-computed sentiment | ✅ Yes | ❌ No |
| NSE/BSE stock codes | ✅ Yes | ❌ No |
| Sector classification | ✅ Yes | ❌ No |
| Market cap info | ✅ Yes | ❌ No |
| Cost | Free | Free (limited) |

### Data Sources

Tradient aggregates news from major financial sources:
- Bloomberg
- Reuters
- CNBC
- Economic Times
- Moneycontrol
- NSE/BSE announcements

## Files Changed

### New Files

1. **`src/services/tradient_news_service.py`** - Main service
   - `TradientNewsService` class
   - Fetches from Tradient API
   - Falls back to Marketaux if Tradient fails
   - Stores in same `market_news` table
   - Updates `market_sentiment_cache`

2. **`test_tradient_news.py`** - Test script
   - Tests API connection
   - Tests storage
   - Tests sentiment cache
   - Tests signal adjustment

### Updated Files

1. **`main.py`**
   - Imports `tradient_news_service` as primary
   - Falls back to old `news_service` if needed
   - Enhanced `/health` endpoint with service status
   - Updated `/fetch-news` endpoint with source info

2. **`src/analytics/news_sentiment.py`**
   - Updated imports to use Tradient service
   - Fallback to Marketaux if Tradient unavailable

## API Endpoints

### Trigger News Fetch
```bash
curl https://stocxer-ai.onrender.com/fetch-news
```

Response:
```json
{
  "success": true,
  "articles_stored": 50,
  "timestamp": "2026-01-26T21:53:23.550234",
  "message": "Successfully fetched and stored 50 articles",
  "source": "tradient",
  "using_fallback": false,
  "service_status": {
    "primary_source": "tradient",
    "fallback_source": "marketaux",
    "using_fallback": false,
    "consecutive_failures": 0,
    "last_fetch_time": "2026-01-26T21:53:23.550234",
    "fallback_available": true
  }
}
```

### Health Check
```bash
curl https://stocxer-ai.onrender.com/health
```

Response includes news service status:
```json
{
  "status": "online",
  "news_service": {
    "available": true,
    "type": "tradient",
    "primary_source": "tradient",
    "fallback_source": "marketaux",
    "using_fallback": false,
    "consecutive_failures": 0
  }
}
```

## Database Schema

Uses existing `market_news` table with enhanced `entities` column:

```json
{
  "stock_name": "TCS Limited",
  "stock_symbol": "TCS",
  "isin_code": "INE467B01029",
  "nse_scrip_code": 11536,
  "bse_scrip_code": 532540,
  "sector_name": "IT - Software",
  "marketcap": "Large Cap",
  "market_cap_value": 1500000
}
```

## Fallback Logic

1. **Primary attempt**: Tradient API
   - If success: Store articles, reset failure counter
   - If failure: Increment failure counter, try fallback

2. **Fallback attempt**: Marketaux API
   - Only triggered if Tradient fails
   - Limited to 100 requests/day
   - Articles converted to compatible format

3. **Scanner/Screener protection**:
   - If both APIs fail, scanners continue with cached sentiment
   - Signals are not blocked, just sentiment adjustment skipped

## Scheduled Fetching

The scheduler runs every **1 hour** (via APScheduler):

```python
scheduler.add_job(
    scheduled_news_fetch,
    IntervalTrigger(hours=1),
    id='news_fetch_job',
    name='Hourly News Fetch'
)
```

### Render Free Tier Issue

Render free tier sleeps services after 15 minutes of inactivity.
Use external cron (cron-job.org or GitHub Actions) to call `/fetch-news` hourly.

## Testing

```bash
# Run test script
python test_tradient_news.py

# Expected output:
# ✅ Tradient API fetch: 50+ articles
# ✅ Database storage: 50 articles
# ✅ Sentiment cache: Updated for all time windows
# ✅ Signal adjustment: Working with sentiment data
```

## Deployment Checklist

1. ✅ Deploy updated code to Render
2. ✅ Verify `/health` shows `type: "tradient"`
3. ✅ Set up external cron for `/fetch-news`
4. ✅ Verify news in database (Supabase `market_news` table)
5. ✅ Test scanner with sentiment integration
