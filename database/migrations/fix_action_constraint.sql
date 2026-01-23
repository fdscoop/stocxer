-- Fix action column constraint to support options signals
-- This migration allows action values: 'BUY', 'SELL', 'BUY CALL', 'BUY PUT', 'SELL CALL', 'SELL PUT'

-- Drop existing constraint
ALTER TABLE public.screener_results 
DROP CONSTRAINT IF EXISTS screener_results_action_check;

-- Add updated constraint with options support
ALTER TABLE public.screener_results 
ADD CONSTRAINT screener_results_action_check 
CHECK (action IN ('BUY', 'SELL', 'BUY CALL', 'BUY PUT', 'SELL CALL', 'SELL PUT'));

-- Verify the constraint was added
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'public.screener_results'::regclass 
AND conname = 'screener_results_action_check';
