# 100 Free Credits for New Users

## Overview
This update gives all new users **100 free credits** as a welcome bonus when they sign up. This allows them to try out the platform features before deciding to purchase more credits or subscribe.

## What Changed

### 1. Database Schema Updates
- **Default credit balance**: Changed from `0` to `100`
- **Default lifetime_purchased**: Changed from `0` to `100`
- **Welcome bonus**: Automatically recorded in `credit_transactions` table

### 2. Automatic Initialization
New trigger automatically:
- Creates `user_credits` record with 100 credits
- Records welcome bonus transaction
- Happens automatically on user registration

### 3. Backend Service Updates
- `billing_service.py` now initializes credits for existing users without records
- Prevents errors when checking credit balance for new users
- Gracefully handles missing credit records

## Files Modified

### Database
- `database/migrations/subscription_schema.sql` - Updated default values
- `database/migrations/add_100_free_credits.sql` - Complete migration script

### Backend
- `src/services/billing_service.py` - Added `_initialize_user_credits()` function
- Automatically creates credit record with 100 free credits if missing

### Migration Scripts
- `apply_free_credits_migration.py` - Python script to update existing users

## How to Apply

### Method 1: Supabase SQL Editor (Recommended)
1. Go to your Supabase project dashboard
2. Click "SQL Editor" in the left sidebar
3. Create a new query
4. Copy and paste the contents of `database/migrations/add_100_free_credits.sql`
5. Click "Run" to execute the migration

### Method 2: Python Script
```bash
cd /Users/bineshbalan/TradeWise
source venv/bin/activate
python apply_free_credits_migration.py
```

## What Users Get

### New Users (After Migration)
- ✅ 100 free credits automatically on signup
- ✅ Welcome bonus transaction recorded
- ✅ Can immediately start using features

### Existing Users
- ✅ Existing credits unchanged
- ✅ Continue using platform normally
- ✅ Backend handles missing credit records gracefully

## Credit Usage Examples

With 100 free credits, users can perform:
- **~102 option scans** (₹0.98 each)
- **~117 stock scans** (₹0.85 each)
- **~5 bulk scans** (₹17.50 for 25 stocks)
- Or any combination of the above!

## Verification

### Check User Credits
```sql
SELECT user_id, balance, lifetime_purchased, lifetime_spent 
FROM public.user_credits 
LIMIT 10;
```

### Check Welcome Bonus Transactions
```sql
SELECT user_id, amount, description, created_at
FROM public.credit_transactions 
WHERE transaction_type = 'bonus' 
AND description = 'Welcome bonus: 100 free credits'
ORDER BY created_at DESC;
```

### Check Default Values
```sql
SELECT column_name, column_default 
FROM information_schema.columns 
WHERE table_name = 'user_credits' 
AND column_name IN ('balance', 'lifetime_purchased');
```

## Benefits

### For Users
- **No barrier to entry**: Can try features immediately
- **Better onboarding**: Experience platform before committing
- **Fair value**: 100 credits worth of exploration

### For Business
- **Higher conversion**: Users engage before hitting paywall
- **Better retention**: Positive first experience
- **Competitive advantage**: Most competitors don't offer free credits

## Rollback (If Needed)

To revert the changes:
```sql
-- Remove trigger
DROP TRIGGER IF EXISTS trigger_initialize_user_credits ON auth.users;
DROP FUNCTION IF EXISTS public.initialize_user_credits();

-- Reset default values
ALTER TABLE public.user_credits ALTER COLUMN balance SET DEFAULT 0;
ALTER TABLE public.user_credits ALTER COLUMN lifetime_purchased SET DEFAULT 0;
```

⚠️ **Warning**: This won't remove credits already given to users.

## Next Steps

1. ✅ Database schema updated
2. ✅ Backend service updated
3. ✅ Migration script created
4. ⏭️ Apply SQL migration in Supabase
5. ⏭️ Test with new user registration
6. ⏭️ Monitor credit usage analytics
7. ⏭️ Update marketing materials to highlight free credits

## Support

If you encounter issues:
1. Check Supabase logs in the dashboard
2. Verify trigger is active: `SELECT * FROM pg_trigger WHERE tgname = 'trigger_initialize_user_credits';`
3. Check function exists: `SELECT proname FROM pg_proc WHERE proname = 'initialize_user_credits';`

---

**Migration Date**: 23 January 2026  
**Status**: ✅ Ready to Deploy  
**Impact**: All new users, zero impact on existing users
