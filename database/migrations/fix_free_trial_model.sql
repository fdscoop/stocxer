-- ============================================
-- FIX FREE TRIAL BILLING MODEL
-- ============================================
-- This migration updates the billing model to properly implement:
-- 1. Free Trial: 100 credits (no daily limits)
-- 2. Pay As You Go: Buy credits as needed (₹0.85/stock, ₹0.98/option)
-- 3. Medium/Pro: Flat fee subscription with scan limits

-- Update plan_limits for "free" plan
-- Free plan should have NO daily limits - it's PAYG based on credit balance
UPDATE public.plan_limits
SET 
    daily_option_scans = NULL,    -- NULL = unlimited (limited only by credits)
    daily_stock_scans = NULL,     -- NULL = unlimited (limited only by credits)
    bulk_scan_limit = 0,          -- No bulk scan in free tier
    daily_bulk_scans = 0
WHERE plan_type = 'free';

-- Ensure "medium" and "pro" plans have proper limits
-- Medium: 30,000 scans/month without daily limits (tracked monthly only)
UPDATE public.plan_limits
SET 
    daily_option_scans = NULL,    -- NULL = unlimited daily (only monthly limit applies)
    daily_stock_scans = NULL,     -- NULL = unlimited daily (only monthly limit applies)
    bulk_scan_limit = 25,         -- Max 25 stocks per bulk scan
    daily_bulk_scans = NULL,      -- NULL = unlimited daily bulk scans
    has_accuracy_tracking = FALSE,
    has_priority_support = FALSE,
    has_historical_data = FALSE,
    has_early_access = FALSE
WHERE plan_type = 'medium';

-- Pro: 150,000 scans/month without any limits (unlimited everything)
UPDATE public.plan_limits
SET 
    daily_option_scans = NULL,    -- Unlimited daily
    daily_stock_scans = NULL,     -- Unlimited daily
    bulk_scan_limit = NULL,       -- Unlimited bulk scans (100+ stocks)
    daily_bulk_scans = NULL,      -- Unlimited daily bulk scans
    has_accuracy_tracking = TRUE,
    has_priority_support = TRUE,
    has_historical_data = TRUE,
    has_early_access = TRUE
WHERE plan_type = 'pro';

-- Verify the changes
SELECT plan_type, daily_option_scans, daily_stock_scans, bulk_scan_limit, daily_bulk_scans
FROM public.plan_limits
ORDER BY plan_type;
