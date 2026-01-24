-- ============================================
-- ADD 100 FREE CREDITS FOR NEW USERS
-- ============================================
-- This migration:
-- 1. Updates the default balance for user_credits table to 100
-- 2. Updates existing users with 0 balance to 100
-- 3. Creates a trigger to automatically give new users 100 credits
-- 4. Records the bonus in credit_transactions table

-- ============================================
-- 1. UPDATE DEFAULT VALUE IN user_credits TABLE
-- ============================================
ALTER TABLE public.user_credits 
ALTER COLUMN balance SET DEFAULT 100;

COMMENT ON COLUMN public.user_credits.balance IS 'Current credit balance (new users start with 100 free credits)';


-- ============================================
-- 2. UPDATE EXISTING USERS WITH ZERO BALANCE
-- ============================================
-- Give 100 free credits to existing users who have 0 balance
UPDATE public.user_credits
SET 
    balance = 100,
    lifetime_purchased = lifetime_purchased + 100,
    updated_at = NOW()
WHERE balance = 0;

-- Record the bonus credits in transactions table for existing users
INSERT INTO public.credit_transactions (
    user_id,
    transaction_type,
    amount,
    balance_before,
    balance_after,
    description,
    created_at
)
SELECT 
    uc.user_id,
    'bonus'::TEXT,
    100,
    0,
    100,
    'Welcome bonus: 100 free credits'::TEXT,
    NOW()
FROM public.user_credits uc
WHERE uc.balance = 100 
AND NOT EXISTS (
    SELECT 1 FROM public.credit_transactions ct 
    WHERE ct.user_id = uc.user_id 
    AND ct.transaction_type = 'bonus' 
    AND ct.description = 'Welcome bonus: 100 free credits'
);


-- ============================================
-- 3. CREATE FUNCTION TO INITIALIZE NEW USER CREDITS
-- ============================================
CREATE OR REPLACE FUNCTION public.initialize_user_credits()
RETURNS TRIGGER AS $$
BEGIN
    -- Create user_credits record with 100 free credits
    INSERT INTO public.user_credits (
        user_id,
        balance,
        lifetime_purchased,
        created_at,
        updated_at
    ) VALUES (
        NEW.id,
        100,
        100,
        NOW(),
        NOW()
    )
    ON CONFLICT (user_id) DO NOTHING;
    
    -- Record welcome bonus transaction
    INSERT INTO public.credit_transactions (
        user_id,
        transaction_type,
        amount,
        balance_before,
        balance_after,
        description,
        created_at
    ) VALUES (
        NEW.id,
        'bonus',
        100,
        0,
        100,
        'Welcome bonus: 100 free credits',
        NOW()
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.initialize_user_credits IS 'Automatically gives new users 100 free credits on registration';


-- ============================================
-- 4. CREATE TRIGGER FOR NEW USER REGISTRATION
-- ============================================
-- Note: We create this trigger on public.users (not auth.users) since we own that table
DROP TRIGGER IF EXISTS trigger_initialize_user_credits ON public.users;

CREATE TRIGGER trigger_initialize_user_credits
    AFTER INSERT ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.initialize_user_credits();

COMMENT ON TRIGGER trigger_initialize_user_credits ON public.users IS 'Gives new users 100 free credits on signup';


-- ============================================
-- 5. MANUAL INITIALIZATION FOR EXISTING USERS
-- ============================================
-- For existing users who already have a public.users record but no credits
INSERT INTO public.user_credits (
    user_id,
    balance,
    lifetime_purchased,
    created_at,
    updated_at
)
SELECT 
    u.id,
    100,
    100,
    NOW(),
    NOW()
FROM public.users u
WHERE NOT EXISTS (
    SELECT 1 FROM public.user_credits uc WHERE uc.user_id = u.id
)
ON CONFLICT (user_id) DO NOTHING;

-- Record welcome bonus for newly initialized users
INSERT INTO public.credit_transactions (
    user_id,
    transaction_type,
    amount,
    balance_before,
    balance_after,
    description,
    created_at
)
SELECT 
    u.id,
    'bonus',
    100,
    0,
    100,
    'Welcome bonus: 100 free credits',
    NOW()
FROM public.users u
WHERE EXISTS (
    SELECT 1 FROM public.user_credits uc 
    WHERE uc.user_id = u.id 
    AND uc.balance = 100
)
AND NOT EXISTS (
    SELECT 1 FROM public.credit_transactions ct 
    WHERE ct.user_id = u.id 
    AND ct.transaction_type = 'bonus' 
    AND ct.description = 'Welcome bonus: 100 free credits'
);


-- ============================================
-- 6. NOTE ON BACKEND SERVICE
-- ============================================
-- The backend service (billing_service.py) also handles initialization
-- This ensures credits are created even if:
-- - The trigger doesn't fire
-- - Users were created before the trigger existed
-- - There's any issue with the database trigger


-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Run these to verify the migration worked:

-- 1. Check all user credits
-- SELECT user_id, balance, lifetime_purchased FROM public.user_credits;

-- 2. Check welcome bonus transactions
-- SELECT user_id, amount, description FROM public.credit_transactions WHERE transaction_type = 'bonus';

-- 3. Verify trigger exists
-- SELECT tgname, tgenabled FROM pg_trigger WHERE tgname = 'trigger_initialize_user_credits';

-- 4. Check users without credits (should be empty)
-- SELECT u.id, u.email FROM public.users u 
-- WHERE NOT EXISTS (SELECT 1 FROM public.user_credits uc WHERE uc.user_id = u.id);
