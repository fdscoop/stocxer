-- Create option_scan_opportunities table to store all scanned option opportunities
-- This stores the full list of evaluated options from /options/scan endpoint

CREATE TABLE IF NOT EXISTS public.option_scan_opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL,  -- Groups all options from same scan
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Scan context
    index TEXT NOT NULL,  -- NIFTY, BANKNIFTY, etc
    expiry_date DATE NOT NULL,
    scan_mode TEXT,  -- 'quick' or 'full'
    
    -- Option details
    strike DECIMAL(10, 2) NOT NULL,
    option_type TEXT NOT NULL CHECK (option_type IN ('CE', 'PE', 'CALL', 'PUT')),
    trading_symbol TEXT NOT NULL,  -- NSE:NIFTY2620325450CE
    
    -- Pricing
    ltp DECIMAL(10, 2),
    bid DECIMAL(10, 2),
    ask DECIMAL(10, 2),
    
    -- Volume & OI
    volume INTEGER,
    oi INTEGER,
    oi_change INTEGER,
    oi_change_pct DECIMAL(8, 2),
    
    -- Greeks
    iv DECIMAL(8, 2),
    delta DECIMAL(8, 4),
    gamma DECIMAL(8, 4),
    theta DECIMAL(8, 4),
    vega DECIMAL(8, 4),
    
    -- Scoring
    score DECIMAL(8, 2) NOT NULL,  -- Overall score (0-100)
    strategy_match TEXT,  -- bullish, bearish, neutral, etc
    recommendation TEXT,  -- Quick recommendation text
    probability_boost BOOLEAN DEFAULT FALSE,
    sentiment_boost BOOLEAN DEFAULT FALSE,
    sentiment_conflict BOOLEAN DEFAULT FALSE,
    
    -- Entry Analysis (if available)
    entry_grade TEXT,  -- A, B, C, D
    entry_recommendation TEXT,
    limit_order_price DECIMAL(10, 2),
    max_acceptable_price DECIMAL(10, 2),
    wait_for_pullback BOOLEAN,
    pullback_probability DECIMAL(5, 2),
    
    -- Targets (calculated)
    target_1 DECIMAL(10, 2),
    target_2 DECIMAL(10, 2),
    stop_loss DECIMAL(10, 2),
    
    -- Discount Zone
    discount_zone_type TEXT,
    is_in_discount BOOLEAN,
    discount_pct DECIMAL(8, 2),
    
    -- Rank in scan
    rank INTEGER NOT NULL,  -- 1 = best, 2 = second best, etc
    
    -- Market context at scan time
    spot_price DECIMAL(10, 2),
    future_price DECIMAL(10, 2),
    pcr_oi DECIMAL(5, 2),
    vix DECIMAL(5, 2),
    
    -- Is this the selected/recommended option?
    is_recommended BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    scanned_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_scan_opps_user_id ON public.option_scan_opportunities(user_id);
CREATE INDEX IF NOT EXISTS idx_scan_opps_scan_id ON public.option_scan_opportunities(scan_id);
CREATE INDEX IF NOT EXISTS idx_scan_opps_index ON public.option_scan_opportunities(index);
CREATE INDEX IF NOT EXISTS idx_scan_opps_scanned_at ON public.option_scan_opportunities(scanned_at DESC);
CREATE INDEX IF NOT EXISTS idx_scan_opps_score ON public.option_scan_opportunities(score DESC);
CREATE INDEX IF NOT EXISTS idx_scan_opps_user_scan ON public.option_scan_opportunities(user_id, scan_id);
CREATE INDEX IF NOT EXISTS idx_scan_opps_rank ON public.option_scan_opportunities(scan_id, rank);

-- Enable Row Level Security
ALTER TABLE public.option_scan_opportunities ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own scan opportunities" ON public.option_scan_opportunities
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own scan opportunities" ON public.option_scan_opportunities
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own scan opportunities" ON public.option_scan_opportunities
    FOR DELETE USING (auth.uid() = user_id);

-- Comment on table
COMMENT ON TABLE public.option_scan_opportunities IS 'Stores all scanned option opportunities from each scan, allowing users to review alternative options';
COMMENT ON COLUMN public.option_scan_opportunities.scan_id IS 'Groups all options from the same scan session';
COMMENT ON COLUMN public.option_scan_opportunities.rank IS 'Rank within the scan (1 = best score)';
COMMENT ON COLUMN public.option_scan_opportunities.is_recommended IS 'True if this was the final recommended option';
