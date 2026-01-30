-- Create option_scanner_results table to store full actionable signals
-- This stores the complete JSON response from /signals/{symbol}/actionable endpoint

CREATE TABLE IF NOT EXISTS public.option_scanner_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Basic identification
    index TEXT NOT NULL,  -- NIFTY, BANKNIFTY, etc
    symbol TEXT NOT NULL,  -- NSE:NIFTY50-INDEX
    
    -- Signal information
    signal TEXT NOT NULL,  -- ICT_BULLISH_REVERSAL, ICT_BEARISH_CONTINUATION, etc
    action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL', 'WAIT', 'AVOID')),
    confidence DECIMAL(5, 2) NOT NULL,
    confidence_level TEXT,  -- HIGH, MEDIUM, LOW, AVOID
    
    -- Option details
    strike DECIMAL(10, 2) NOT NULL,
    option_type TEXT NOT NULL CHECK (option_type IN ('CE', 'PE')),
    trading_symbol TEXT NOT NULL,  -- NSE:NIFTY2620325450CE
    expiry_date DATE NOT NULL,
    days_to_expiry INTEGER NOT NULL,
    
    -- Pricing
    entry_price DECIMAL(10, 2) NOT NULL,
    ltp DECIMAL(10, 2),
    iv_used DECIMAL(5, 2),
    
    -- Targets and risk
    target_1 DECIMAL(10, 2),
    target_2 DECIMAL(10, 2),
    stop_loss DECIMAL(10, 2),
    risk_per_lot DECIMAL(10, 2),
    reward_1_per_lot DECIMAL(10, 2),
    reward_2_per_lot DECIMAL(10, 2),
    risk_reward_ratio_1 TEXT,
    risk_reward_ratio_2 TEXT,
    
    -- Greeks
    delta DECIMAL(8, 4),
    gamma DECIMAL(8, 4),
    theta DECIMAL(8, 4),
    vega DECIMAL(8, 4),
    
    -- Index data
    spot_price DECIMAL(10, 2),
    future_price DECIMAL(10, 2),
    basis DECIMAL(10, 2),
    vix DECIMAL(5, 2),
    pcr_oi DECIMAL(5, 2),
    pcr_volume DECIMAL(5, 2),
    
    -- Analysis results
    htf_direction TEXT,  -- bullish, bearish, neutral
    htf_strength DECIMAL(5, 2),
    ltf_found BOOLEAN DEFAULT FALSE,
    ltf_entry_type TEXT,
    
    -- Full JSON data (for complete signal with all nested objects)
    full_signal_data JSONB NOT NULL,
    
    -- Metadata
    is_reversal_play BOOLEAN DEFAULT FALSE,
    trading_mode TEXT,  -- INTRADAY, SWING, etc
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_option_scanner_user_id ON public.option_scanner_results(user_id);
CREATE INDEX IF NOT EXISTS idx_option_scanner_index ON public.option_scanner_results(index);
CREATE INDEX IF NOT EXISTS idx_option_scanner_timestamp ON public.option_scanner_results(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_option_scanner_action ON public.option_scanner_results(action);
CREATE INDEX IF NOT EXISTS idx_option_scanner_confidence ON public.option_scanner_results(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_option_scanner_expiry ON public.option_scanner_results(expiry_date);
CREATE INDEX IF NOT EXISTS idx_option_scanner_user_timestamp ON public.option_scanner_results(user_id, timestamp DESC);

-- Enable Row Level Security
ALTER TABLE public.option_scanner_results ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only access their own option scanner results
CREATE POLICY "Users can view own option scanner results" ON public.option_scanner_results
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own option scanner results" ON public.option_scanner_results
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own option scanner results" ON public.option_scanner_results
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own option scanner results" ON public.option_scanner_results
    FOR DELETE USING (auth.uid() = user_id);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_option_scanner_results_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_option_scanner_results_updated_at
    BEFORE UPDATE ON public.option_scanner_results
    FOR EACH ROW
    EXECUTE FUNCTION update_option_scanner_results_updated_at();

-- Verify table creation
SELECT 
    'option_scanner_results table created successfully' AS status,
    COUNT(*) AS initial_row_count
FROM public.option_scanner_results;
