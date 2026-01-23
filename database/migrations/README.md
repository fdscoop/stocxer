# Database Migration: Fix Action Constraint

## 🎯 Purpose
Fix the `screener_results_action_check` constraint to allow options-specific action values.

## 📋 Migration Details
- **File**: `fix_action_constraint.sql`
- **Date**: 2026-01-23
- **Issue**: Database constraint violation when saving options signals

## 🔧 What This Fixes

### Before
```sql
CHECK (action IN ('BUY', 'SELL'))
```
❌ Only allows stock signals

### After
```sql
CHECK (action IN ('BUY', 'SELL', 'BUY CALL', 'BUY PUT', 'SELL CALL', 'SELL PUT'))
```
✅ Allows both stock and options signals

## 🚀 How to Run

### Step 1: Open Supabase SQL Editor
1. Go to: https://cxbcpmouqkajlxzmbomu.supabase.co
2. Navigate to **SQL Editor** (left sidebar)
3. Click **New Query**

### Step 2: Run the Migration
Copy and paste the contents of `fix_action_constraint.sql` into the SQL editor and click **Run**.

Or run this directly:

```sql
-- Drop existing constraint
ALTER TABLE public.screener_results 
DROP CONSTRAINT IF EXISTS screener_results_action_check;

-- Add updated constraint with options support
ALTER TABLE public.screener_results 
ADD CONSTRAINT screener_results_action_check 
CHECK (action IN ('BUY', 'SELL', 'BUY CALL', 'BUY PUT', 'SELL CALL', 'SELL PUT'));
```

### Step 3: Verify Success
You should see:
```
Success. No rows returned
```

### Step 4: Test
Trigger an options scan from your app and verify the signal saves successfully without errors.

## ✅ Expected Result

After migration, options signals will save successfully:
```
✅ Saved OPTIONS signal for NIFTY: BUY PUT - ID: xxx
```

No more constraint violation errors!

## 📝 Files Modified
- ✅ `database/migrations/fix_action_constraint.sql` - Migration script (NEW)
- ✅ `database/schema.sql` - Updated constraint for future deployments
