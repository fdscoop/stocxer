# News Sentiment Analysis Integration

## Overview

TradeWise now includes a news sentiment analysis feature powered by the Marketaux API. This feature:

1. **Fetches real-time market news** every 15 minutes during market hours
2. **Stores news in Supabase** for efficient querying
3. **Analyzes sentiment** of news articles using keyword matching + API sentiment scores
4. **Integrates sentiment into trading signals** to boost or reduce confidence

## Setup

### 1. Get Marketaux API Key

1. Go to [https://www.marketaux.com/](https://www.marketaux.com/)
2. Sign up for a free account
3. Get your API key from the dashboard

**Free Tier Limits:**
- 100 requests per day
- 3 articles per request
- Our 15-minute fetch schedule uses ~96 requests/day (safe margin)

### 2. Add API Key to Environment

Add to your `.env` file:

```env
MARKETAUX_API_KEY=C7vaAhOlnlnwHOkUaLBwVtweW84tXBvXh2lMObmP
NEWS_FETCH_INTERVAL_MINUTES=15
NEWS_RETENTION_DAYS=7
```

### 3. Create Database Tables

Run the SQL in Supabase SQL Editor:

```sql
-- Copy contents from database/news_schema.sql
```

This creates:
- `market_news` - Stores news articles
- `news_fetch_log` - Tracks API usage
- `market_sentiment_cache` - Pre-computed sentiment aggregations

### 4. Install Dependencies

```bash
pip install httpx
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

## How It Works

### News Fetching (Every 15 Minutes)

1. Background scheduler triggers `fetch_market_news()` every 15 minutes
2. Fetches news filtered for India (`countries=in`)
3. Parses articles and calculates:
   - **Sentiment** (positive/negative/neutral)
   - **Sentiment score** (-1.0 to 1.0)
   - **Relevance score** (how relevant to Indian market)
   - **Impact level** (high/medium/low)
   - **Affected indices** (NIFTY, BANKNIFTY, FINNIFTY)
   - **Affected sectors** (banking, it, pharma, etc.)
4. Stores in Supabase with upsert (no duplicates)
5. Updates sentiment cache for quick lookups

### Sentiment Integration in Signals

#### Options Scanner
- Bullish sentiment boosts CALL option scores by up to 15%
- Bearish sentiment boosts PUT option scores by up to 15%
- Conflicting sentiment reduces scores by up to 10%

#### Stock Screener
- Bullish sentiment boosts BUY signal confidence by up to 10%
- Bearish sentiment boosts SELL signal confidence by up to 10%
- Conflicting sentiment reduces confidence by up to 5%
- Adds sentiment reason to signal reasons list

## API Endpoints

### GET /api/news
Get recent market news from database.

**Parameters:**
- `hours` (int, default: 4): Hours of news to fetch
- `indices` (string): Comma-separated indices filter
- `sectors` (string): Comma-separated sectors filter
- `limit` (int, default: 20): Max articles

**Response:**
```json
{
    "success": true,
    "count": 10,
    "articles": [
        {
            "title": "Nifty gains 200 points...",
            "sentiment": "positive",
            "sentiment_score": 0.65,
            "published_at": "2026-01-23T10:30:00Z",
            ...
        }
    ]
}
```

### GET /api/sentiment
Get aggregated market sentiment.

**Parameters:**
- `time_window` (string): One of "15min", "1hr", "4hr", "1day"

**Response:**
```json
{
    "success": true,
    "overall_sentiment": "bullish",
    "sentiment_score": 0.42,
    "market_mood": "Optimistic - Cautious Buying",
    "trading_implication": "Buy on dips. Look for quality setups.",
    "key_themes": ["fii", "nifty", "rally"],
    "sector_sentiment": {
        "banking": 0.5,
        "it": 0.3
    }
}
```

### GET /api/sentiment/for-signal
Get sentiment data for signal enhancement.

**Parameters:**
- `symbol` (string): Trading symbol (e.g., "NIFTY")
- `signal_type` (string): "BUY", "SELL", or "HOLD"

**Response:**
```json
{
    "success": true,
    "sentiment": "bullish",
    "sentiment_score": 0.42,
    "confidence_adjustment": 8.4,
    "signal_adjustment": null,
    "market_mood": "Optimistic - Cautious Buying",
    "reason": "Bullish sentiment supports long position.",
    "latest_news": [...]
}
```

### POST /api/news/fetch
Manually trigger news fetch (use sparingly due to rate limits).

### GET /api/news/status
Get news service status and API usage.

**Response:**
```json
{
    "success": true,
    "available": true,
    "requests_today": 45,
    "daily_limit": 100,
    "requests_remaining": 55,
    "total_articles_stored": 150,
    "scheduler_running": true,
    "recent_fetches": [...]
}
```

## Sentiment Analysis Logic

### Bullish Keywords
rally, surge, jump, gain, rise, bullish, buy, strong, growth, profit, beat, exceed, upgrade, positive, optimistic, recovery, expansion, boost, breakout, high, outperform, upside, bull, inflow, accumulation, buying, support, momentum

### Bearish Keywords
fall, drop, decline, crash, bearish, sell, weak, loss, miss, below, downgrade, negative, pessimistic, recession, contraction, cut, selloff, breakdown, low, underperform, downside, bear, outflow, selling, resistance, correction, slump, plunge

### India-Specific Keywords (Relevance)
india, nifty, sensex, bse, nse, rbi, sebi, rupee, inr, mumbai, indian, fii, dii, reliance, tcs, infosys, hdfc, icici, sbi

### High Impact Keywords
rbi, fed, rate, policy, election, budget, gdp, inflation, fii, crash, rally, major, significant, breaking, urgent, sebi, government, regulatory, ban, approval

## Files Created/Modified

### New Files
- `database/news_schema.sql` - Database schema for news tables
- `src/services/news_service.py` - Marketaux API service
- `NEWS_SENTIMENT_GUIDE.md` - This documentation

### Modified Files
- `src/analytics/news_sentiment.py` - Added real data integration
- `main.py` - Added news endpoints and scheduler
- `config/settings.py` - Added API key configuration
- `.env.example` - Added API key example
- `requirements.txt` - Added httpx dependency

## Rate Limit Management

- News is only fetched during market hours (8 AM - 6 PM IST)
- This saves API quota for when it matters most
- ~48 requests during market hours vs ~96 if 24/7
- You can monitor usage via `/api/news/status`

## Troubleshooting

### News service not available
- Check if `MARKETAUX_API_KEY` is set in `.env`
- Verify the API key is valid at marketaux.com

### No news in database
- Check `/api/news/status` for fetch errors
- Verify database tables exist
- Check if you've hit the daily rate limit

### Sentiment not affecting signals
- Ensure news has been fetched recently
- Check if sentiment is neutral (no adjustment)
- Verify relevance score is above threshold (0.1)

## Future Improvements

1. **More news sources** - Add Economic Times, Moneycontrol RSS feeds
2. **Entity-based sentiment** - Track sentiment per company/sector
3. **ML-based sentiment** - Use NLP models for better accuracy
4. **Breaking news alerts** - Real-time notifications for major news
5. **Historical sentiment correlation** - Backtest sentiment vs price moves
