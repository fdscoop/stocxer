-- RLS Policy Updates for TradeWise
-- This script updates the Row Level Security policies to allow the application to access tokens

-- First, let's check the current policies
-- Run this in your Supabase SQL editor to see current policies:
-- SELECT * FROM pg_policies WHERE tablename = 'fyers_tokens';

-- Drop existing restrictive policies if they exist
DROP POLICY IF EXISTS "Users can only view their own tokens" ON fyers_tokens;
DROP POLICY IF EXISTS "Users can only insert their own tokens" ON fyers_tokens;
DROP POLICY IF EXISTS "Users can only update their own tokens" ON fyers_tokens;

-- Create new policies that allow the application to access tokens
-- Policy for the application to read any token (for startup token loading)
CREATE POLICY "Application can read tokens for startup" ON fyers_tokens
    FOR SELECT
    USING (true);  -- Allow reading any token

-- Policy for authenticated users to manage their own tokens
CREATE POLICY "Users can manage their own tokens" ON fyers_tokens
    FOR ALL
    USING (auth.uid() = user_id);

-- Policy for service role to have full access (for admin operations)
CREATE POLICY "Service role has full access" ON fyers_tokens
    FOR ALL
    TO service_role
    USING (true);

-- Alternative: More restrictive policy that only allows reading non-expired tokens
-- Uncomment this and comment the above "Application can read tokens" if you prefer:
/*
CREATE POLICY "Application can read valid tokens" ON fyers_tokens
    FOR SELECT
    USING (
        expires_at > now() OR expires_at IS NULL
    );
*/

-- Make sure RLS is enabled on the table
ALTER TABLE fyers_tokens ENABLE ROW LEVEL SECURITY;

-- Verify the policies were created
SELECT 
    policyname, 
    permissive, 
    roles, 
    cmd, 
    qual,
    with_check
FROM pg_policies 
WHERE tablename = 'fyers_tokens'
ORDER BY policyname;