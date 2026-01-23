-- ============================================
-- NEWS SENTIMENT TABLE FOR MARKETAUX INTEGRATION
-- ============================================
-- Stores news articles from Marketaux API for sentiment analysis
-- News is fetched every 15 minutes and cached in this table
-- Rate limit: 100 requests/day, 3 articles per request

-- News articles table
CREATE TABLE IF NOT EXISTS public.market_news (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Marketaux article identifiers
    article_uuid TEXT UNIQUE NOT NULL,  -- Unique ID from Marketaux
    
    -- Article content
    title TEXT NOT NULL,
    description TEXT,
    snippet TEXT,
    
    -- Source information
    source TEXT NOT NULL,
    source_domain TEXT,
    url TEXT,
    image_url TEXT,
    
    -- Timing information
    published_at TIMESTAMPTZ NOT NULL,  -- When article was published
    fetched_at TIMESTAMPTZ DEFAULT NOW(),  -- When we fetched it
    
    -- Categorization
    keywords TEXT[],  -- Keywords/tags from API
    entities JSONB,  -- Companies, tickers mentioned
    
    -- Sentiment analysis
    sentiment TEXT CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    sentiment_score DECIMAL(4, 3),  -- -1.000 to 1.000
    relevance_score DECIMAL(4, 3),  -- 0.000 to 1.000 (relevance to Indian market)
    
    -- Market impact assessment
    impact_level TEXT CHECK (impact_level IN ('high', 'medium', 'low')),
    affected_indices TEXT[],  -- ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
    affected_sectors TEXT[],  -- ['banking', 'it', 'pharma', etc.]
    
    -- Metadata
    language TEXT DEFAULT 'en',
    countries TEXT[],  -- Countries mentioned
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_news_published_at ON public.market_news(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_fetched_at ON public.market_news(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_sentiment ON public.market_news(sentiment);
CREATE INDEX IF NOT EXISTS idx_news_impact ON public.market_news(impact_level);
CREATE INDEX IF NOT EXISTS idx_news_article_uuid ON public.market_news(article_uuid);

-- Full-text search index on title and description
CREATE INDEX IF NOT EXISTS idx_news_fulltext ON public.market_news 
    USING GIN (to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, '')));

-- No RLS needed - news is public data that backend fetches
-- Backend uses service role key to insert, clients can read via API


-- ============================================
-- NEWS FETCH LOG TABLE
-- ============================================
-- Track API calls to manage rate limits

CREATE TABLE IF NOT EXISTS public.news_fetch_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fetch_time TIMESTAMPTZ DEFAULT NOW(),
    articles_fetched INTEGER DEFAULT 0,
    api_response_code INTEGER,
    error_message TEXT,
    query_params JSONB,  -- Store the query parameters used
    credits_remaining INTEGER,  -- API credits remaining (if returned by API)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fetch_log_time ON public.news_fetch_log(fetch_time DESC);


-- ============================================
-- NEWS SENTIMENT AGGREGATION TABLE
-- ============================================
-- Pre-computed sentiment aggregations for quick lookups

CREATE TABLE IF NOT EXISTS public.market_sentiment_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Time window
    time_window TEXT NOT NULL,  -- '15min', '1hr', '4hr', '1day'
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    
    -- Aggregated sentiment
    overall_sentiment TEXT CHECK (overall_sentiment IN ('bullish', 'bearish', 'neutral')),
    sentiment_score DECIMAL(4, 3),  -- -1.000 to 1.000
    
    -- Counts
    total_articles INTEGER DEFAULT 0,
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    
    -- Top themes/keywords
    top_keywords JSONB,  -- {"keyword": count, ...}
    key_themes TEXT[],
    
    -- Index-specific sentiment
    nifty_sentiment DECIMAL(4, 3),
    banknifty_sentiment DECIMAL(4, 3),
    
    -- Sector sentiment breakdown
    sector_sentiment JSONB,  -- {"banking": 0.5, "it": -0.2, ...}
    
    -- Trading implications
    market_mood TEXT,
    trading_implication TEXT,
    
    -- Tracking
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(time_window, window_start)
);

CREATE INDEX IF NOT EXISTS idx_sentiment_cache_window ON public.market_sentiment_cache(time_window, window_start DESC);


-- ============================================
-- TRIGGERS
-- ============================================

CREATE TRIGGER update_market_news_updated_at 
    BEFORE UPDATE ON public.market_news
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sentiment_cache_updated_at 
    BEFORE UPDATE ON public.market_sentiment_cache
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- CLEANUP FUNCTION
-- ============================================
-- Delete news older than 7 days to keep the database lean

CREATE OR REPLACE FUNCTION cleanup_old_news()
RETURNS void AS $$
BEGIN
    -- Delete news older than 7 days
    DELETE FROM public.market_news 
    WHERE published_at < NOW() - INTERVAL '7 days';
    
    -- Delete fetch logs older than 30 days
    DELETE FROM public.news_fetch_log 
    WHERE fetch_time < NOW() - INTERVAL '30 days';
    
    -- Delete sentiment cache older than 7 days
    DELETE FROM public.market_sentiment_cache 
    WHERE window_end < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- You can schedule this cleanup using pg_cron or call it periodically from backend
