-- ============================================================================
-- PAPER TRADING SYSTEM - DATABASE SCHEMA
-- ============================================================================
-- This schema enables automated paper trading with:
-- - Configuration management
-- - Signal generation and tracking
-- - Position management
-- - Activity logging
-- - Performance analytics
-- ============================================================================

-- 1. Paper Trading Configuration
-- Stores user-specific automated trading settings
CREATE TABLE IF NOT EXISTS paper_trading_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT false,
    indices TEXT[] DEFAULT ARRAY['NIFTY'],  -- ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
    scan_interval_minutes INTEGER DEFAULT 12,
    max_positions INTEGER DEFAULT 3,
    capital_per_trade NUMERIC DEFAULT 10000,
    trading_mode TEXT DEFAULT 'intraday',  -- 'intraday', 'swing'
    start_time TIME DEFAULT '09:15:00',
    end_time TIME DEFAULT '15:15:00',
    auto_exit_time TIME DEFAULT '15:15:00',
    min_confidence NUMERIC DEFAULT 65,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 2. Paper Trading Signals
-- Tracks all generated trading signals
CREATE TABLE IF NOT EXISTS paper_trading_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    scan_id UUID,
    index TEXT NOT NULL,
    signal_type TEXT NOT NULL,  -- 'BUY_CALL', 'BUY_PUT', 'AVOID', 'WAIT'
    option_symbol TEXT NOT NULL,
    strike NUMERIC NOT NULL,
    option_type TEXT NOT NULL,  -- 'CE', 'PE'
    entry_price NUMERIC NOT NULL,
    stop_loss NUMERIC NOT NULL,
    target_1 NUMERIC NOT NULL,
    target_2 NUMERIC NOT NULL,
    confidence NUMERIC NOT NULL,
    trading_mode TEXT NOT NULL,
    dte INTEGER NOT NULL,
    signal_timestamp TIMESTAMPTZ DEFAULT NOW(),
    executed BOOLEAN DEFAULT false,
    execution_timestamp TIMESTAMPTZ,
    status TEXT DEFAULT 'PENDING',  -- 'PENDING', 'EXECUTED', 'REJECTED', 'CANCELLED'
    rejection_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Paper Trading Positions
-- Manages open and closed positions
CREATE TABLE IF NOT EXISTS paper_trading_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    signal_id UUID REFERENCES paper_trading_signals(id) ON DELETE SET NULL,
    index TEXT NOT NULL,
    option_symbol TEXT NOT NULL,
    strike NUMERIC NOT NULL,
    option_type TEXT NOT NULL,  -- 'CE', 'PE'
    quantity INTEGER NOT NULL,
    entry_price NUMERIC NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    exit_price NUMERIC,
    exit_time TIMESTAMPTZ,
    exit_reason TEXT,  -- 'TARGET_1', 'TARGET_2', 'STOP_LOSS', 'EOD_EXIT', 'MANUAL'
    stop_loss NUMERIC NOT NULL,
    target_1 NUMERIC NOT NULL,
    target_2 NUMERIC NOT NULL,
    current_ltp NUMERIC,  -- Last traded price (updated periodically)
    current_pnl NUMERIC,  -- Current unrealized P&L (for open positions)
    status TEXT DEFAULT 'OPEN',  -- 'OPEN', 'CLOSED'
    pnl NUMERIC,  -- Realized P&L (for closed positions)
    pnl_pct NUMERIC,  -- Realized P&L percentage
    order_id TEXT,  -- Fyers order ID (will be rejected for paper trading)
    order_response JSONB,  -- Full order response from Fyers
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Paper Trading Activity Log
-- Comprehensive audit trail of all trading activities
CREATE TABLE IF NOT EXISTS paper_trading_activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    position_id UUID REFERENCES paper_trading_positions(id) ON DELETE SET NULL,
    activity_type TEXT NOT NULL,  
    -- Activity types:
    -- 'SCAN' - Market scan performed
    -- 'SIGNAL_GENERATED' - Trading signal created
    -- 'ORDER_PLACED' - Order submitted to broker
    -- 'ORDER_REJECTED' - Order rejected by broker
    -- 'POSITION_OPENED' - Position created
    -- 'TARGET_CHECK' - Target/SL monitoring check
    -- 'POSITION_CLOSED' - Position closed
    -- 'EOD_EXIT' - End of day auto-exit
    -- 'MANUAL_EXIT' - User manually closed position
    -- 'ERROR' - Error occurred
    details JSONB,  -- Additional context (signal data, error messages, etc.)
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Paper Trading Performance Summary
-- Daily aggregated performance metrics
CREATE TABLE IF NOT EXISTS paper_trading_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    breakeven_trades INTEGER DEFAULT 0,
    win_rate NUMERIC,  -- Percentage of winning trades
    total_pnl NUMERIC DEFAULT 0,  -- Total profit/loss for the day
    avg_win NUMERIC,  -- Average profit per winning trade
    avg_loss NUMERIC,  -- Average loss per losing trade
    max_win NUMERIC,  -- Largest single win
    max_loss NUMERIC,  -- Largest single loss
    max_drawdown NUMERIC,  -- Maximum drawdown during the day
    profit_factor NUMERIC,  -- Gross profit / Gross loss
    avg_trade_duration_minutes INTEGER,  -- Average time in position
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ============================================================================

-- Paper Trading Positions Indexes
CREATE INDEX IF NOT EXISTS idx_paper_positions_user_status 
    ON paper_trading_positions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_paper_positions_user_date 
    ON paper_trading_positions(user_id, entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_paper_positions_signal 
    ON paper_trading_positions(signal_id);

-- Paper Trading Signals Indexes
CREATE INDEX IF NOT EXISTS idx_paper_signals_user_status 
    ON paper_trading_signals(user_id, status);
CREATE INDEX IF NOT EXISTS idx_paper_signals_user_timestamp 
    ON paper_trading_signals(user_id, signal_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_paper_signals_executed 
    ON paper_trading_signals(user_id, executed);

-- Paper Trading Activity Log Indexes
CREATE INDEX IF NOT EXISTS idx_paper_activity_user_timestamp 
    ON paper_trading_activity_log(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_paper_activity_type 
    ON paper_trading_activity_log(activity_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_paper_activity_position 
    ON paper_trading_activity_log(position_id, timestamp DESC);

-- Paper Trading Performance Indexes
CREATE INDEX IF NOT EXISTS idx_paper_performance_user_date 
    ON paper_trading_performance(user_id, date DESC);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE paper_trading_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_trading_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_trading_positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_trading_activity_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_trading_performance ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own paper trading config" ON paper_trading_config;
DROP POLICY IF EXISTS "Users can insert their own paper trading config" ON paper_trading_config;
DROP POLICY IF EXISTS "Users can update their own paper trading config" ON paper_trading_config;
DROP POLICY IF EXISTS "Users can delete their own paper trading config" ON paper_trading_config;
DROP POLICY IF EXISTS "Users can view their own signals" ON paper_trading_signals;
DROP POLICY IF EXISTS "Service role can insert signals" ON paper_trading_signals;
DROP POLICY IF EXISTS "Service role can update signals" ON paper_trading_signals;
DROP POLICY IF EXISTS "Users can view their own positions" ON paper_trading_positions;
DROP POLICY IF EXISTS "Service role can insert positions" ON paper_trading_positions;
DROP POLICY IF EXISTS "Service role can update positions" ON paper_trading_positions;
DROP POLICY IF EXISTS "Users can view their own activity" ON paper_trading_activity_log;
DROP POLICY IF EXISTS "Service role can insert activity" ON paper_trading_activity_log;
DROP POLICY IF EXISTS "Users can view their own performance" ON paper_trading_performance;
DROP POLICY IF EXISTS "Service role can manage performance" ON paper_trading_performance;

-- Paper Trading Config Policies
CREATE POLICY "Users can view their own paper trading config"
    ON paper_trading_config FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own paper trading config"
    ON paper_trading_config FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own paper trading config"
    ON paper_trading_config FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own paper trading config"
    ON paper_trading_config FOR DELETE
    USING (auth.uid() = user_id);

-- Paper Trading Signals Policies
CREATE POLICY "Users can view their own signals"
    ON paper_trading_signals FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert signals"
    ON paper_trading_signals FOR INSERT
    WITH CHECK (true);  -- Service role only

CREATE POLICY "Service role can update signals"
    ON paper_trading_signals FOR UPDATE
    USING (true);  -- Service role only

-- Paper Trading Positions Policies
CREATE POLICY "Users can view their own positions"
    ON paper_trading_positions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert positions"
    ON paper_trading_positions FOR INSERT
    WITH CHECK (true);  -- Service role only

CREATE POLICY "Service role can update positions"
    ON paper_trading_positions FOR UPDATE
    USING (true);  -- Service role only

-- Paper Trading Activity Log Policies
CREATE POLICY "Users can view their own activity"
    ON paper_trading_activity_log FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert activity"
    ON paper_trading_activity_log FOR INSERT
    WITH CHECK (true);  -- Service role only

-- Paper Trading Performance Policies
CREATE POLICY "Users can view their own performance"
    ON paper_trading_performance FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage performance"
    ON paper_trading_performance FOR ALL
    USING (true);  -- Service role only

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to calculate win rate
CREATE OR REPLACE FUNCTION calculate_win_rate(p_winning_trades INTEGER, p_total_trades INTEGER)
RETURNS NUMERIC AS $$
BEGIN
    IF p_total_trades = 0 THEN
        RETURN 0;
    END IF;
    RETURN ROUND((p_winning_trades::NUMERIC / p_total_trades::NUMERIC) * 100, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to calculate profit factor
CREATE OR REPLACE FUNCTION calculate_profit_factor(p_user_id UUID, p_date DATE)
RETURNS NUMERIC AS $$
DECLARE
    v_gross_profit NUMERIC;
    v_gross_loss NUMERIC;
BEGIN
    -- Calculate gross profit (sum of all winning trades)
    SELECT COALESCE(SUM(pnl), 0) INTO v_gross_profit
    FROM paper_trading_positions
    WHERE user_id = p_user_id
    AND DATE(exit_time) = p_date
    AND pnl > 0
    AND status = 'CLOSED';
    
    -- Calculate gross loss (sum of all losing trades, absolute value)
    SELECT COALESCE(ABS(SUM(pnl)), 0) INTO v_gross_loss
    FROM paper_trading_positions
    WHERE user_id = p_user_id
    AND DATE(exit_time) = p_date
    AND pnl < 0
    AND status = 'CLOSED';
    
    -- Calculate profit factor
    IF v_gross_loss = 0 THEN
        RETURN NULL;  -- Undefined if no losses
    END IF;
    
    RETURN ROUND(v_gross_profit / v_gross_loss, 2);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS update_paper_config_updated_at ON paper_trading_config;
DROP TRIGGER IF EXISTS update_paper_positions_updated_at ON paper_trading_positions;
DROP TRIGGER IF EXISTS update_paper_performance_updated_at ON paper_trading_performance;

CREATE TRIGGER update_paper_config_updated_at
    BEFORE UPDATE ON paper_trading_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_paper_positions_updated_at
    BEFORE UPDATE ON paper_trading_positions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_paper_performance_updated_at
    BEFORE UPDATE ON paper_trading_performance
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA (OPTIONAL)
-- ============================================================================

-- No initial data needed - users will create their own configs

-- ============================================================================
-- CLEANUP FUNCTIONS (FOR TESTING)
-- ============================================================================

-- Function to reset paper trading data for a user (useful for testing)
CREATE OR REPLACE FUNCTION reset_paper_trading_data(p_user_id UUID)
RETURNS void AS $$
BEGIN
    DELETE FROM paper_trading_activity_log WHERE user_id = p_user_id;
    DELETE FROM paper_trading_positions WHERE user_id = p_user_id;
    DELETE FROM paper_trading_signals WHERE user_id = p_user_id;
    DELETE FROM paper_trading_performance WHERE user_id = p_user_id;
    DELETE FROM paper_trading_config WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE paper_trading_config IS 'User configuration for automated paper trading';
COMMENT ON TABLE paper_trading_signals IS 'All trading signals generated by the system';
COMMENT ON TABLE paper_trading_positions IS 'Open and closed trading positions';
COMMENT ON TABLE paper_trading_activity_log IS 'Comprehensive audit trail of all trading activities';
COMMENT ON TABLE paper_trading_performance IS 'Daily aggregated performance metrics';

COMMENT ON COLUMN paper_trading_positions.current_ltp IS 'Last traded price - updated every minute for open positions';
COMMENT ON COLUMN paper_trading_positions.current_pnl IS 'Unrealized P&L for open positions';
COMMENT ON COLUMN paper_trading_positions.order_response IS 'Full response from Fyers API (including rejection message)';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
