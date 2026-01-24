-- ============================================
-- HYBRID SUBSCRIPTION + PAYG BILLING SYSTEM
-- ============================================
-- This migration adds tables for subscription management and PAYG credits
-- Run this in Supabase SQL Editor after the main schema

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. USER SUBSCRIPTIONS TABLE
-- ============================================
-- Tracks active subscription plans (free, medium, pro)
CREATE TABLE IF NOT EXISTS public.user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    plan_type TEXT NOT NULL CHECK (plan_type IN ('free', 'medium', 'pro')),
    status TEXT NOT NULL CHECK (status IN ('active', 'cancelled', 'expired', 'trial')),
    razorpay_subscription_id TEXT,
    razorpay_plan_id TEXT,
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Indexes for subscriptions
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON public.user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_period_end ON public.user_subscriptions(current_period_end);

COMMENT ON TABLE public.user_subscriptions IS 'User subscription plans with Razorpay integration';
COMMENT ON COLUMN public.user_subscriptions.plan_type IS 'Subscription tier: free, medium (₹499/mo), pro (₹999/mo)';
COMMENT ON COLUMN public.user_subscriptions.status IS 'Subscription status: active, cancelled, expired, trial';


-- ============================================
-- 2. USER CREDITS TABLE (PAYG)
-- ============================================
-- Tracks credit balance for pay-as-you-go users
CREATE TABLE IF NOT EXISTS public.user_credits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    balance DECIMAL(10, 2) NOT NULL DEFAULT 100 CHECK (balance >= 0),
    lifetime_purchased DECIMAL(10, 2) DEFAULT 100,
    lifetime_spent DECIMAL(10, 2) DEFAULT 0,
    last_topped_up TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Indexes for credits
CREATE INDEX IF NOT EXISTS idx_credits_user_id ON public.user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_credits_balance ON public.user_credits(balance);

COMMENT ON TABLE public.user_credits IS 'PAYG credit balance - new users start with 100 free credits';
COMMENT ON COLUMN public.user_credits.balance IS 'Current credit balance (new users get 100 free credits)';
COMMENT ON COLUMN public.user_credits.lifetime_purchased IS 'Total credits purchased lifetime (includes 100 welcome bonus)';
COMMENT ON COLUMN public.user_credits.lifetime_spent IS 'Total credits spent lifetime';


-- ============================================
-- 3. CREDIT TRANSACTIONS TABLE
-- ============================================
-- Logs all credit purchases, debits, refunds, and bonuses
CREATE TABLE IF NOT EXISTS public.credit_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('purchase', 'debit', 'refund', 'bonus')),
    amount DECIMAL(10, 2) NOT NULL,
    balance_before DECIMAL(10, 2) NOT NULL,
    balance_after DECIMAL(10, 2) NOT NULL,
    description TEXT,
    razorpay_payment_id TEXT,
    razorpay_order_id TEXT,
    scan_type TEXT, -- 'option_scan', 'stock_scan', 'bulk_scan'
    scan_count INTEGER, -- Number of stocks/options in the scan
    metadata JSONB, -- Additional data (e.g., scan_id, symbol)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for transactions
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON public.credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON public.credit_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_created ON public.credit_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_razorpay ON public.credit_transactions(razorpay_payment_id) WHERE razorpay_payment_id IS NOT NULL;

COMMENT ON TABLE public.credit_transactions IS 'Complete audit log of all credit movements';
COMMENT ON COLUMN public.credit_transactions.transaction_type IS 'purchase: bought credits, debit: used credits, refund: returned credits, bonus: promotional credits';


-- ============================================
-- 4. USAGE LOGS TABLE
-- ============================================
-- Daily usage tracking for subscription users
CREATE TABLE IF NOT EXISTS public.usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    scan_type TEXT NOT NULL CHECK (scan_type IN ('option_scan', 'stock_scan', 'bulk_scan')),
    count INTEGER NOT NULL DEFAULT 1 CHECK (count > 0),
    usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
    metadata JSONB, -- Store scan details if needed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_scan_date UNIQUE(user_id, scan_type, usage_date)
);

-- Indexes for usage logs
CREATE INDEX IF NOT EXISTS idx_usage_user_date ON public.usage_logs(user_id, usage_date DESC);
CREATE INDEX IF NOT EXISTS idx_usage_date ON public.usage_logs(usage_date DESC);
CREATE INDEX IF NOT EXISTS idx_usage_type ON public.usage_logs(scan_type);

COMMENT ON TABLE public.usage_logs IS 'Daily usage tracking for subscription quota management';
COMMENT ON COLUMN public.usage_logs.scan_type IS 'option_scan: index options, stock_scan: individual stocks, bulk_scan: bulk screener';


-- ============================================
-- 5. PLAN LIMITS CONFIGURATION TABLE
-- ============================================
-- Defines limits for each subscription tier
CREATE TABLE IF NOT EXISTS public.plan_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_type TEXT NOT NULL UNIQUE CHECK (plan_type IN ('free', 'medium', 'pro')),
    daily_option_scans INTEGER, -- NULL = unlimited
    daily_stock_scans INTEGER, -- NULL = unlimited
    bulk_scan_limit INTEGER, -- Max stocks per bulk scan
    daily_bulk_scans INTEGER, -- NULL = unlimited
    has_accuracy_tracking BOOLEAN DEFAULT FALSE,
    has_priority_support BOOLEAN DEFAULT FALSE,
    has_historical_data BOOLEAN DEFAULT FALSE,
    has_early_access BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default plan limits
INSERT INTO public.plan_limits (
    plan_type, 
    daily_option_scans, 
    daily_stock_scans, 
    bulk_scan_limit, 
    daily_bulk_scans,
    has_accuracy_tracking,
    has_priority_support,
    has_historical_data,
    has_early_access
) VALUES
    ('free', 3, 10, 0, 0, FALSE, FALSE, FALSE, FALSE),
    ('medium', 50, 200, 25, 10, FALSE, FALSE, FALSE, FALSE),
    ('pro', NULL, NULL, 100, NULL, TRUE, TRUE, TRUE, TRUE)
ON CONFLICT (plan_type) DO UPDATE SET
    daily_option_scans = EXCLUDED.daily_option_scans,
    daily_stock_scans = EXCLUDED.daily_stock_scans,
    bulk_scan_limit = EXCLUDED.bulk_scan_limit,
    daily_bulk_scans = EXCLUDED.daily_bulk_scans,
    has_accuracy_tracking = EXCLUDED.has_accuracy_tracking,
    has_priority_support = EXCLUDED.has_priority_support,
    has_historical_data = EXCLUDED.has_historical_data,
    has_early_access = EXCLUDED.has_early_access,
    updated_at = NOW();

COMMENT ON TABLE public.plan_limits IS 'Configuration of limits for each subscription tier (NULL = unlimited)';


-- ============================================
-- 6. CREDIT PACKS CONFIGURATION TABLE
-- ============================================
-- Defines available credit packs for purchase
CREATE TABLE IF NOT EXISTS public.credit_packs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    amount_inr INTEGER NOT NULL CHECK (amount_inr > 0), -- Amount in INR
    credits DECIMAL(10, 2) NOT NULL CHECK (credits > 0), -- Credits received
    bonus_credits DECIMAL(10, 2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Remove duplicates and add unique constraint
DO $$ 
BEGIN
    -- Step 1: Delete duplicate credit packs (keep only the oldest one)
    DELETE FROM public.credit_packs a
    USING public.credit_packs b
    WHERE a.id > b.id
      AND a.name = b.name;
    
    -- Step 2: Add unique constraint if not exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'credit_packs_name_key'
    ) THEN
        ALTER TABLE public.credit_packs ADD CONSTRAINT credit_packs_name_key UNIQUE (name);
    END IF;
END $$;

-- Insert default credit packs
INSERT INTO public.credit_packs (name, amount_inr, credits, bonus_credits, display_order) VALUES
    ('Starter Pack', 50, 50, 0, 1),
    ('Basic Pack', 100, 100, 5, 2),
    ('Value Pack', 250, 250, 15, 3),
    ('Power Pack', 500, 500, 40, 4),
    ('Premium Pack', 1000, 1000, 100, 5)
ON CONFLICT (name) DO UPDATE SET
    amount_inr = EXCLUDED.amount_inr,
    credits = EXCLUDED.credits,
    bonus_credits = EXCLUDED.bonus_credits,
    display_order = EXCLUDED.display_order,
    updated_at = NOW();

COMMENT ON TABLE public.credit_packs IS 'Available credit packs with bonus credits for larger purchases';


-- ============================================
-- 7. PAYMENT HISTORY TABLE
-- ============================================
-- Tracks all payments (subscriptions and credit purchases)
CREATE TABLE IF NOT EXISTS public.payment_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    payment_type TEXT NOT NULL CHECK (payment_type IN ('subscription', 'credits', 'refund')),
    amount_inr INTEGER NOT NULL, -- Amount in paisa (₹100 = 10000)
    razorpay_payment_id TEXT,
    razorpay_order_id TEXT,
    razorpay_signature TEXT,
    status TEXT NOT NULL CHECK (status IN ('created', 'pending', 'captured', 'failed', 'refunded')),
    payment_method TEXT, -- 'upi', 'card', 'netbanking', 'wallet'
    failure_reason TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for payment history
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON public.payment_history(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON public.payment_history(status);
CREATE INDEX IF NOT EXISTS idx_payments_created ON public.payment_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payments_razorpay ON public.payment_history(razorpay_payment_id) WHERE razorpay_payment_id IS NOT NULL;

COMMENT ON TABLE public.payment_history IS 'Complete payment audit trail for subscriptions and credit purchases';


-- ============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- User Subscriptions RLS
ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own subscription" ON public.user_subscriptions;
CREATE POLICY "Users can view own subscription" ON public.user_subscriptions
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own subscription" ON public.user_subscriptions;
CREATE POLICY "Users can insert own subscription" ON public.user_subscriptions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own subscription" ON public.user_subscriptions;
CREATE POLICY "Users can update own subscription" ON public.user_subscriptions
    FOR UPDATE USING (auth.uid() = user_id);


-- User Credits RLS
ALTER TABLE public.user_credits ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own credits" ON public.user_credits;
CREATE POLICY "Users can view own credits" ON public.user_credits
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own credits" ON public.user_credits;
CREATE POLICY "Users can insert own credits" ON public.user_credits
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own credits" ON public.user_credits;
CREATE POLICY "Users can update own credits" ON public.user_credits
    FOR UPDATE USING (auth.uid() = user_id);


-- Credit Transactions RLS
ALTER TABLE public.credit_transactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own transactions" ON public.credit_transactions;
CREATE POLICY "Users can view own transactions" ON public.credit_transactions
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own transactions" ON public.credit_transactions;
CREATE POLICY "Users can insert own transactions" ON public.credit_transactions
    FOR INSERT WITH CHECK (auth.uid() = user_id);


-- Usage Logs RLS
ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own usage" ON public.usage_logs;
CREATE POLICY "Users can view own usage" ON public.usage_logs
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own usage" ON public.usage_logs;
CREATE POLICY "Users can insert own usage" ON public.usage_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own usage" ON public.usage_logs;
CREATE POLICY "Users can update own usage" ON public.usage_logs
    FOR UPDATE USING (auth.uid() = user_id);


-- Plan Limits (public read)
ALTER TABLE public.plan_limits ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can view plan limits" ON public.plan_limits;
CREATE POLICY "Anyone can view plan limits" ON public.plan_limits
    FOR SELECT TO authenticated USING (TRUE);


-- Credit Packs (public read)
ALTER TABLE public.credit_packs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can view credit packs" ON public.credit_packs;
CREATE POLICY "Anyone can view credit packs" ON public.credit_packs
    FOR SELECT TO authenticated USING (TRUE);


-- Payment History RLS
ALTER TABLE public.payment_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own payments" ON public.payment_history;
CREATE POLICY "Users can view own payments" ON public.payment_history
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own payments" ON public.payment_history;
CREATE POLICY "Users can insert own payments" ON public.payment_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);


-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to automatically create free subscription for new users
CREATE OR REPLACE FUNCTION create_default_subscription()
RETURNS TRIGGER AS $$
BEGIN
    -- Create free subscription
    INSERT INTO public.user_subscriptions (user_id, plan_type, status, current_period_start, current_period_end)
    VALUES (NEW.id, 'free', 'active', NOW(), NOW() + INTERVAL '100 years');
    
    -- Create credits record with 0 balance
    INSERT INTO public.user_credits (user_id, balance)
    VALUES (NEW.id, 0);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create default subscription on user signup
DROP TRIGGER IF EXISTS on_user_created_subscription ON public.users;
CREATE TRIGGER on_user_created_subscription
    AFTER INSERT ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION create_default_subscription();


-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_billing_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON public.user_subscriptions;
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON public.user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_billing_updated_at();

DROP TRIGGER IF EXISTS update_credits_updated_at ON public.user_credits;
CREATE TRIGGER update_credits_updated_at BEFORE UPDATE ON public.user_credits
    FOR EACH ROW EXECUTE FUNCTION update_billing_updated_at();

DROP TRIGGER IF EXISTS update_plan_limits_updated_at ON public.plan_limits;
CREATE TRIGGER update_plan_limits_updated_at BEFORE UPDATE ON public.plan_limits
    FOR EACH ROW EXECUTE FUNCTION update_billing_updated_at();

DROP TRIGGER IF EXISTS update_credit_packs_updated_at ON public.credit_packs;
CREATE TRIGGER update_credit_packs_updated_at BEFORE UPDATE ON public.credit_packs
    FOR EACH ROW EXECUTE FUNCTION update_billing_updated_at();

DROP TRIGGER IF EXISTS update_payment_history_updated_at ON public.payment_history;
CREATE TRIGGER update_payment_history_updated_at BEFORE UPDATE ON public.payment_history
    FOR EACH ROW EXECUTE FUNCTION update_billing_updated_at();


-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Verify all tables were created
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
    AND table_name IN (
        'user_subscriptions', 
        'user_credits', 
        'credit_transactions', 
        'usage_logs', 
        'plan_limits', 
        'credit_packs', 
        'payment_history'
    )
ORDER BY table_name;

-- Check plan limits
SELECT plan_type, daily_option_scans, daily_stock_scans, bulk_scan_limit 
FROM public.plan_limits 
ORDER BY plan_type;

-- Check credit packs
SELECT name, amount_inr, credits, bonus_credits 
FROM public.credit_packs 
WHERE is_active = TRUE 
ORDER BY display_order;
