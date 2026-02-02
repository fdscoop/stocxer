-- Fix action constraint on option_scanner_results table to allow full action names
-- Run this migration to allow 'BUY CALL', 'BUY PUT', 'SELL CALL', 'SELL PUT'

-- Drop existing constraint (if exists)
ALTER TABLE option_scanner_results 
DROP CONSTRAINT IF EXISTS option_scanner_results_action_check;

-- Add updated constraint with all valid actions
ALTER TABLE option_scanner_results 
ADD CONSTRAINT option_scanner_results_action_check 
CHECK (action IN ('BUY', 'SELL', 'BUY CALL', 'BUY PUT', 'SELL CALL', 'SELL PUT', 'WAIT', 'AVOID', '🚨 AVOID - EXPIRY DAY'));

-- Verify the constraint was updated
SELECT 
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint 
WHERE conrelid = 'option_scanner_results'::regclass 
AND conname = 'option_scanner_results_action_check';
