# News & Sentiment Analysis System - Complete Overview

## ✅ Current Implementation Status

Your TradeWise application has a **fully functional news fetching and sentiment analysis system**. Here's the complete breakdown:

---

## 1️⃣ News Fetching Schedule (Every 15 Minutes - 24/7)

### Backend Implementation
**File**: `main.py` (Lines 165-190) + `src/services/news_service.py`

```
✅ YES - Fetches every 15 minutes, 24 hours a day, 7 days a week
```

**How it works:**

1. **Scheduler Configuration** (main.py:291-312)
   - Uses APScheduler with `IntervalTrigger(minutes=15)`
   - Runs continuously in background **24/7**
   - **Updated**: Now fetches anytime, not just during market hours
   - Gets you latest global news, market developments, policy changes at any time

2. **API Rate Limit Management**
   - **Limit**: 100 requests/day from Marketaux API
   - **Fetch frequency**: Every 15 minutes = 96 requests/day
   - **Articles per request**: 3 articles (free tier)
   - **Total**: ~288 articles/day possible
   - **Safety**: 96 < 100, so you never exceed daily limit

3. **Automatic News Fetch Process**
   ```
   1. Backend starts at app startup → `await fetch_market_news()`
   2. Scheduler triggers every 15 minutes
   3. During market hours only (8 AM - 6 PM IST) to save API quota
   4. During non-market hours: scheduler sleeps to preserve daily limit
   ```

4. **What Gets Fetched** (src/services/news_service.py:487-530)
   - **General Indian market news**: Keywords like "nifty", "sensex", "bse"
   - **Specific keywords rotating**: "nifty sensex market", "rbi sebi india stock", "fii dii investment india"
   - **Countries**: India (primary), US (for global market impact)
   - **Storage**: All articles stored in Supabase `news_articles` table

**Database Storage**:
```sql
Table: news_articles
Columns:
- article_uuid (unique identifier)
- title
- description
- source (Reuters, Economic Times, etc.)
- url
- published_at (timestamp)
- sentiment (positive, negative, neutral)
- sentiment_score (-1 to +1)
- relevance_score (0 to 1)
- impact_level (high, medium, low)
- affected_indices (NIFTY, BANKNIFTY, FINNIFTY)
- affected_sectors (banking, it, pharma, auto, etc.)
- keywords (extracted from article)
- created_at
```

---

## 2️⃣ Sentiment Analysis from Database

### ✅ YES - Performs sentiment analysis on stored news

**Implementation Files**:
- `src/analytics/news_sentiment.py` (Main sentiment analyzer)
- `src/services/news_service.py` (Database sentiment aggregation)

### How Sentiment Analysis Works:

1. **Per-Article Sentiment** (news_service.py:144-213)
   - **Method**: Keyword-based sentiment scoring
   - **Scope**: Analyzes article title, description, and keywords
   - **Score Range**: -1.0 (bearish) to +1.0 (bullish)
   - **Keywords tracked**:
     ```
     Bullish: "surge", "rally", "growth", "bull", "buy", "positive", "gain"
     Bearish: "fall", "crash", "decline", "bear", "sell", "negative", "loss"
     ```
   - **Sentiment classification**: positive | negative | neutral

2. **Market Sentiment Aggregation** (news_sentiment.py:380-450)
   - **Time Windows**: 15min, 1hr, 4hr, 1day
   - **Calculation**:
     ```
     Market Sentiment = Weighted average of article sentiments
     Weight = relevance_score × impact_level × article_freshness
     ```
   - **Output**: Overall market sentiment with aggregate sentiment_score

3. **Cached Sentiment** (news_service.py:600-650)
   - Caches sentiment analysis results
   - Updates every 15 minutes with new news
   - Retrieved via `/api/sentiment` endpoint

### Sentiment Analysis Endpoints:

```
GET /api/sentiment?time_window=1hr
Response:
{
  "sentiment": "bullish" | "bearish" | "neutral",
  "sentiment_score": 0.35,
  "high_impact_articles": [...],
  "last_updated": "2024-01-25T10:30:00Z"
}
```

---

## 3️⃣ Dashboard News Display

### ✅ YES - News displays on dashboard for users to read

**Frontend Implementation**: `frontend/app/page.tsx` (Lines 1592-1700)

### Dashboard News Section Features:

#### Display Format:
```
📰 Market News (Last 6 Hours)
├─ Article 1 Title
│  ├─ Source: Reuters | Published: Jan 25, 10:30 AM
│  ├─ Affected Indices: NIFTY, BANKNIFTY
│  ├─ Sentiment Badge: 📈 (positive) | 📉 (negative) | ➖ (neutral)
│  └─ Impact Badge: HIGH | MEDIUM | LOW
│
├─ Article 2 Title
│  ...
└─ [View all N articles] button
```

#### Features:
1. **Real-time updates**: Fetches news on page load
2. **Refresh button**: Users can manually refresh news
3. **Sentiment visualization**: 
   - 📈 Green badge for positive sentiment
   - 📉 Red badge for negative sentiment
   - ➖ Gray badge for neutral sentiment
4. **Impact level indicators**: Color-coded badges (orange=high, yellow=medium)
5. **Clickable articles**: Click to open full article in new tab
6. **Time display**: Shows when article was published (India timezone)
7. **Affected indices**: Shows which indices the news impacts
8. **Limit display**: Shows 5 most recent articles, with "View all X articles" option

#### Data Flow:
```
Frontend (dashboard) 
  ↓ GET /api/news?hours=6&limit=10
Backend (main.py:730-776)
  ↓ Queries news_articles table from Supabase
  ↓ Filters by: last 6 hours, max 10 articles
  ↓ Includes sentiment_score, impact_level, affected_indices
Frontend displays in card grid
```

---

## 4️⃣ Sentiment Integration with Trading Signals

### ✅ YES - Sentiment score adjusts trading signal confidence

**Implementation**: `main.py:4415-4450` (Stock Screener) + `main.py:5030-5050` (Options Scanner)

### How Sentiment Affects Signals:

When a trading signal is generated, the backend automatically:

1. **Fetches market sentiment** from cached news analysis
2. **Checks alignment**: Does signal direction match sentiment?
3. **Adjusts confidence** based on alignment/conflict:

```
IF Signal Action == "BUY" AND Sentiment == "BULLISH"
  ✅ Confidence BOOST: +5% to +10%
  Label: "sentiment_support": true

IF Signal Action == "BUY" AND Sentiment == "BEARISH"
  ⚠️ Confidence REDUCTION: -5%
  Label: "sentiment_conflict": true

IF Signal Action == "SELL" AND Sentiment == "BEARISH"
  ✅ Confidence BOOST: +5% to +10%

IF Signal Action == "SELL" AND Sentiment == "BULLISH"
  ⚠️ Confidence REDUCTION: -5%
```

**Result**: Trading signals are more reliable when aligned with market sentiment

---

## 5️⃣ Database Schema

### news_articles Table (Supabase)

```sql
CREATE TABLE news_articles (
    id UUID PRIMARY KEY,
    article_uuid TEXT UNIQUE,
    title TEXT,
    description TEXT,
    snippet TEXT,
    source TEXT,
    source_domain TEXT,
    url TEXT,
    image_url TEXT,
    published_at TIMESTAMPTZ,
    
    -- Sentiment Analysis
    sentiment VARCHAR(20),  -- positive, negative, neutral
    sentiment_score DECIMAL(3,2),  -- -1.0 to 1.0
    relevance_score DECIMAL(3,2),  -- 0.0 to 1.0
    impact_level VARCHAR(20),  -- high, medium, low
    
    -- Classification
    affected_indices TEXT[],  -- ['NIFTY', 'BANKNIFTY']
    affected_sectors TEXT[],  -- ['banking', 'it', 'pharma']
    keywords TEXT[],
    
    -- Metadata
    language VARCHAR(5),
    countries TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 6️⃣ API Endpoints for News & Sentiment

### News Endpoints:

```
1. GET /api/news
   Query Params:
   - hours: 1-24 (default: 4)
   - limit: max articles (default: 20)
   - indices: comma-separated (NIFTY,BANKNIFTY)
   - sectors: comma-separated (banking,it,pharma)
   
   Response:
   {
     "success": true,
     "count": 5,
     "articles": [
       {
         "id": "uuid",
         "title": "NIFTY surges 2% on FII inflows",
         "source": "Reuters",
         "published_at": "2024-01-25T10:30:00Z",
         "sentiment": "positive",
         "sentiment_score": 0.65,
         "impact_level": "high",
         "affected_indices": ["NIFTY", "BANKNIFTY"],
         "url": "https://..."
       }
     ]
   }

2. GET /api/sentiment
   Query Params:
   - time_window: 15min, 1hr, 4hr, 1day (default: 1hr)
   
   Response:
   {
     "sentiment": "bullish",
     "sentiment_score": 0.45,
     "time_window": "1hr",
     "articles_analyzed": 12,
     "last_updated": "2024-01-25T10:30:00Z"
   }
```

---

## 7️⃣ Current Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       EVERY 15 MINUTES                           │
│                    (During 8 AM - 6 PM IST)                      │
└──────────────────────────┬──────────────────────────────────────┘
                          │
                          ▼
           ┌──────────────────────────┐
           │  fetch_market_news()     │
           │  (Background Task)       │
           └────────────┬─────────────┘
                        │
          ┌─────────────┴──────────────┐
          │                            │
          ▼                            ▼
    ┌──────────────┐          ┌──────────────┐
    │ Marketaux    │          │ Marketaux    │
    │ API Call 1   │          │ API Call 2   │
    │ "nifty news" │          │ "rbi sebi"   │
    └─────┬────────┘          └─────┬────────┘
          │                         │
          └─────────────┬───────────┘
                        │
                        ▼
        ┌───────────────────────────┐
        │ Sentiment Analysis        │
        │ Per Article Scoring       │
        │ Keyword-based (-1 to +1)  │
        └────────────┬──────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Store in Supabase DB       │
        │ news_articles table        │
        │ (with sentiment scores)    │
        └────────────┬───────────────┘
                     │
        ┌────────────┴───────────────┐
        │                            │
        ▼                            ▼
   ┌─────────────┐            ┌──────────────┐
   │ Frontend    │            │ Trading      │
   │ Dashboard   │            │ Signals      │
   │ Shows News  │            │ Adjusted by  │
   │ + Sentiment │            │ Sentiment    │
   └─────────────┘            └──────────────┘

USER VIEW: 📰 Market News card with articles + sentiment badges
```

---

## 8️⃣ Code Examples

### Fetching News on Frontend:
```typescript
// frontend/app/page.tsx (Line 379)
const fetchNews = async () => {
  setLoadingNews(true)
  const response = await fetch(`${apiUrl}/api/news?hours=6&limit=10`)
  if (response.ok) {
    const data = await response.json()
    setNews(data.articles || [])  // Display on dashboard
  }
  setLoadingNews(false)
}
```

### Getting Market Sentiment:
```python
# main.py (Line 779)
@app.get("/api/sentiment")
async def get_market_sentiment(time_window: str = Query("1hr")):
    sentiment = news_analyzer.analyze_market_sentiment()
    return {
        "sentiment": sentiment.sentiment,
        "sentiment_score": sentiment.sentiment_score,
        ...
    }
```

### Adjusting Signal by Sentiment:
```python
# main.py (Line 4422)
sentiment_data = await news_analyzer.get_sentiment_for_signal(symbol="NIFTY")
if sentiment_data and sentiment_data.get("sentiment_score", 0) != 0:
    for signal in signals:
        if signal.action == "BUY" and sentiment_overall == "bullish":
            signal.confidence += abs(sentiment_score) * 10  # +10% boost
```

---

## 9️⃣ Configuration & Limits

### Marketaux API Limits:
```
- 100 API requests per day (FREE TIER)
- 3 articles per request
- Maximum: ~288 articles per day
- Cost: $0 (free tier)
- Fetch frequency: Every 15 minutes (96 requests/day) ✅
```

### Market Hours:
```
✅ Now fetching 24/7: No market hours restriction
   - Midnight to midnight: Continuously fetching every 15 minutes
   - Rationale: Get news from global markets, policy announcements, 
     pre-market developments, earnings after hours, etc.
   - Safety: 96 requests/day (every 15 min) < 100 requests/day limit
```

---

## 🔟 Summary: What's Working ✅

| Feature | Status | Details |
|---------|--------|---------|
| **News Fetching** | ✅ | Every 15 min, 96x daily, 8 AM - 6 PM IST |
| **API Rate Limits** | ✅ | 100/day available, 96/day used (safe) |
| **Sentiment Analysis** | ✅ | Keyword-based, -1.0 to +1.0 scoring |
| **Database Storage** | ✅ | Supabase `news_articles` with full metadata |
| **Dashboard Display** | ✅ | Shows 5 articles with sentiment badges |
| **Sentiment Integration** | ✅ | Boosts/reduces signal confidence ±10% |
| **Caching** | ✅ | Sentiment cached, updated every 15 min |
| **Error Handling** | ✅ | Falls back if API fails, logs all errors |

---

## 🔧 How to Verify It's Running

### Check Backend Logs:
```bash
# Look for these log messages:
grep -i "📰" /path/to/backend/logs.txt

# Expected output:
"📰 Starting scheduled news fetch from Marketaux..."
"✅ News fetch complete: 5 articles stored"
"📰 News fetch scheduler configured - will fetch every 15 minutes"
```

### Test API Endpoints:
```bash
# Get recent news
curl "http://localhost:8000/api/news?hours=6&limit=5"

# Get market sentiment
curl "http://localhost:8000/api/sentiment?time_window=1hr"
```

### Check Dashboard:
1. Open http://localhost:3000
2. Login
3. Scroll to "📰 Market News" section
4. Should see articles with green/red/gray sentiment badges

---

## 🚀 How to Enhance Further

If you want to improve the news system:

1. **Add Real-time News Streaming**: Replace 15-min interval with WebSocket feed
2. **Add Sector-Specific Sentiment**: Separate FMCG sentiment from Banking sentiment
3. **Add Insider/Analyst Signals**: Include analyst ratings from news sources
4. **Machine Learning Sentiment**: Replace keyword-based with NLP/transformer models
5. **Add RSS Feeds**: Integrate BSE/NSE official RSS feeds for official announcements
6. **Add Telegram/Slack Alerts**: Notify users of high-impact news automatically

---

**Last Updated**: January 25, 2024
**System Status**: ✅ Fully Functional
