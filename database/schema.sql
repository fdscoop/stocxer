-- TradeWise Database Schema for Supabase

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Users can only read their own data
CREATE POLICY "Users can view own data" ON public.users
    FOR SELECT USING (auth.uid() = id);

-- Users can insert their own profile during registration
CREATE POLICY "Users can insert own profile" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Users can update their own data
CREATE POLICY "Users can update own data" ON public.users
    FOR UPDATE USING (auth.uid() = id);


-- Fyers authentication tokens table
CREATE TABLE IF NOT EXISTS public.fyers_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type TEXT DEFAULT 'Bearer',
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Enable Row Level Security
ALTER TABLE public.fyers_tokens ENABLE ROW LEVEL SECURITY;

-- Users can only access their own tokens
CREATE POLICY "Users can view own tokens" ON public.fyers_tokens
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own tokens" ON public.fyers_tokens
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own tokens" ON public.fyers_tokens
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own tokens" ON public.fyers_tokens
    FOR DELETE USING (auth.uid() = user_id);


-- Screener results table
CREATE TABLE IF NOT EXISTS public.screener_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    current_price DECIMAL(10, 2) NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL')),
    confidence DECIMAL(5, 2) NOT NULL,
    target_1 DECIMAL(10, 2),
    target_2 DECIMAL(10, 2),
    stop_loss DECIMAL(10, 2),
    rsi DECIMAL(5, 2),
    sma_5 DECIMAL(10, 2),
    sma_15 DECIMAL(10, 2),
    momentum_5d DECIMAL(5, 2),
    volume_surge BOOLEAN DEFAULT FALSE,
    change_pct DECIMAL(5, 2),
    volume BIGINT,
    reasons JSONB,
    scan_params JSONB,
    scanned_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    -- Options trading columns (added for options scanner integration)
    signal_type TEXT DEFAULT 'STOCK',
    strike DECIMAL(10, 2),
    option_type TEXT,
    expiry_date DATE,
    entry_price DECIMAL(10, 2),
    reversal_probability DECIMAL(5, 2)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_screener_user_id ON public.screener_results(user_id);
CREATE INDEX IF NOT EXISTS idx_screener_scan_id ON public.screener_results(scan_id);
CREATE INDEX IF NOT EXISTS idx_screener_symbol ON public.screener_results(symbol);
CREATE INDEX IF NOT EXISTS idx_screener_action ON public.screener_results(action);
CREATE INDEX IF NOT EXISTS idx_screener_scanned_at ON public.screener_results(scanned_at DESC);
CREATE INDEX IF NOT EXISTS idx_screener_signal_type ON public.screener_results(signal_type);
CREATE INDEX IF NOT EXISTS idx_screener_expiry ON public.screener_results(expiry_date);

-- Enable Row Level Security
ALTER TABLE public.screener_results ENABLE ROW LEVEL SECURITY;

-- Users can only access their own screener results
CREATE POLICY "Users can view own results" ON public.screener_results
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own results" ON public.screener_results
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own results" ON public.screener_results
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own results" ON public.screener_results
    FOR DELETE USING (auth.uid() = user_id);


-- Screener scan history table (tracks each scan session)
CREATE TABLE IF NOT EXISTS public.screener_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL UNIQUE,
    stocks_scanned INTEGER NOT NULL,
    total_signals INTEGER NOT NULL,
    buy_signals INTEGER NOT NULL,
    sell_signals INTEGER NOT NULL,
    min_confidence DECIMAL(5, 2) NOT NULL,
    scan_params JSONB,
    scan_time TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_scans_user_id ON public.screener_scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_scan_id ON public.screener_scans(scan_id);
CREATE INDEX IF NOT EXISTS idx_scans_scan_time ON public.screener_scans(scan_time DESC);

-- Enable Row Level Security
ALTER TABLE public.screener_scans ENABLE ROW LEVEL SECURITY;

-- Users can only access their own scan history
CREATE POLICY "Users can view own scans" ON public.screener_scans
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own scans" ON public.screener_scans
    FOR INSERT WITH CHECK (auth.uid() = user_id);


-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fyers_tokens_updated_at BEFORE UPDATE ON public.fyers_tokens
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_screener_results_updated_at BEFORE UPDATE ON public.screener_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- AUTO-CONFIRM USERS (FOR DEVELOPMENT)
-- ============================================
-- This is useful for development to auto-confirm users
-- Remove this in production if you want email confirmation

-- Note: Run this SQL in Supabase SQL Editor to confirm all existing unconfirmed users:
-- UPDATE auth.users SET email_confirmed_at = NOW() WHERE email_confirmed_at IS NULL;
