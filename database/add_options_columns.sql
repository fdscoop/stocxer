-- ============================================
-- ADD OPTIONS TRADING COLUMNS TO screener_results
-- ============================================
-- This migration adds columns needed for saving options signals
-- Run this in Supabase SQL Editor

-- Add options-specific columns to screener_results table
ALTER TABLE public.screener_results
ADD COLUMN IF NOT EXISTS signal_type TEXT DEFAULT 'STOCK',
ADD COLUMN IF NOT EXISTS strike DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS option_type TEXT,  -- 'CE' or 'PE'
ADD COLUMN IF NOT EXISTS expiry_date DATE,
ADD COLUMN IF NOT EXISTS entry_price DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS reversal_probability DECIMAL(5, 2);

-- Add index for options queries
CREATE INDEX IF NOT EXISTS idx_screener_signal_type ON public.screener_results(signal_type);
CREATE INDEX IF NOT EXISTS idx_screener_expiry ON public.screener_results(expiry_date);

-- Add comment for clarity
COMMENT ON COLUMN public.screener_results.signal_type IS 'Type of signal: STOCK or OPTIONS';
COMMENT ON COLUMN public.screener_results.strike IS 'Option strike price (NULL for stock signals)';
COMMENT ON COLUMN public.screener_results.option_type IS 'Option type: CE (Call) or PE (Put)';
COMMENT ON COLUMN public.screener_results.expiry_date IS 'Option expiry date';
COMMENT ON COLUMN public.screener_results.entry_price IS 'Recommended entry price for option';
COMMENT ON COLUMN public.screener_results.reversal_probability IS 'Probability of reversal (for options signals)';

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'screener_results'
  AND column_name IN ('signal_type', 'strike', 'option_type', 'expiry_date', 'entry_price', 'reversal_probability')
ORDER BY ordinal_position;
