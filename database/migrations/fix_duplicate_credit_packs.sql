-- Fix duplicate credit packs and add unique constraint

-- Step 1: Delete duplicate credit packs (keep only the oldest one)
DELETE FROM public.credit_packs
WHERE id NOT IN (
    SELECT MIN(id)
    FROM public.credit_packs
    GROUP BY name, amount_inr, credits, bonus_credits
);

-- Step 2: Add unique constraint to prevent future duplicates
ALTER TABLE public.credit_packs 
ADD CONSTRAINT credit_packs_name_key UNIQUE (name);

-- Step 3: Verify - should show 5 packs
SELECT name, amount_inr, credits, bonus_credits, display_order
FROM public.credit_packs
WHERE is_active = TRUE
ORDER BY display_order;
