-- Fix screener_results action constraint to include WAIT and AVOID
-- Run this in your Supabase SQL Editor

-- Step 1: Drop the existing constraint
ALTER TABLE public.screener_results 
DROP CONSTRAINT IF EXISTS screener_results_action_check;

-- Step 2: Add the updated constraint with WAIT and AVOID
ALTER TABLE public.screener_results 
ADD CONSTRAINT screener_results_action_check 
CHECK (action IN ('BUY', 'SELL', 'BUY CALL', 'BUY PUT', 'SELL CALL', 'SELL PUT', 'WAIT', 'AVOID'));

-- Step 3: Verify the constraint was added correctly
SELECT 
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint 
WHERE conrelid = 'public.screener_results'::regclass 
AND conname = 'screener_results_action_check';
