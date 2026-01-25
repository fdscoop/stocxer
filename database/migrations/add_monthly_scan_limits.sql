-- ============================================
-- ADD MONTHLY SCAN LIMITS TO PLAN_LIMITS
-- ============================================
-- This migration adds monthly quota tracking for subscription plans
-- Free trial: No monthly limit (PAYG based on credits)
-- Medium: 30,000 scans/month
-- Pro: 150,000 scans/month

-- Add monthly_scan_limit column to plan_limits table
ALTER TABLE public.plan_limits
ADD COLUMN IF NOT EXISTS monthly_scan_limit INTEGER; -- NULL = unlimited (free plan)

COMMENT ON COLUMN public.plan_limits.monthly_scan_limit IS 'Monthly scan quota for subscription plans. NULL = unlimited (free/PAYG). Used to track usage_logs and enforce limits.';

-- Update plan limits with monthly quotas
UPDATE public.plan_limits
SET monthly_scan_limit = NULL
WHERE plan_type = 'free';

UPDATE public.plan_limits
SET monthly_scan_limit = 30000
WHERE plan_type = 'medium';

UPDATE public.plan_limits
SET monthly_scan_limit = 150000
WHERE plan_type = 'pro';

-- Verify the changes
SELECT plan_type, monthly_scan_limit, daily_option_scans, daily_stock_scans
FROM public.plan_limits
ORDER BY plan_type;
