# 🔧 Fix Database Schema Error - Add Options Columns

## Problem Identified

From your Render logs at `02:58:43`:
```
Save options signal error: Could not find the 'entry_price' column of 'screener_results' in the schema cache
```

**Root Cause**: The `screener_results` table is missing columns needed for options signals.

---

## ✅ Good News: Sentiment Feature Working!

Your sentiment integration IS working in production:
```
02:58:18 - 📰 Retrieved 3 real news articles from database
```

The option scan completed successfully with sentiment-boosted signals! 🎉

---

## 🛠️ Fix Instructions

### Step 1: Run Migration in Supabase

1. Go to your Supabase dashboard: https://cxbcpmouqkajlxzmbomu.supabase.co
2. Navigate to **SQL Editor**
3. Copy and run the migration from: `database/add_options_columns.sql`

**Or run this SQL directly**:

```sql
-- Add options-specific columns
ALTER TABLE public.screener_results
ADD COLUMN IF NOT EXISTS signal_type TEXT DEFAULT 'STOCK',
ADD COLUMN IF NOT EXISTS strike DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS option_type TEXT,
ADD COLUMN IF NOT EXISTS expiry_date DATE,
ADD COLUMN IF NOT EXISTS entry_price DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS reversal_probability DECIMAL(5, 2);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_screener_signal_type ON public.screener_results(signal_type);
CREATE INDEX IF NOT EXISTS idx_screener_expiry ON public.screener_results(expiry_date);
```

### Step 2: Verify the Fix

After running the migration, check in Supabase:
1. Go to **Table Editor** → `screener_results`
2. Verify new columns exist:
   - ✅ `signal_type` (TEXT)
   - ✅ `strike` (DECIMAL)
   - ✅ `option_type` (TEXT)
   - ✅ `expiry_date` (DATE)
   - ✅ `entry_price` (DECIMAL)
   - ✅ `reversal_probability` (DECIMAL)

### Step 3: Restart Render (Optional)

The schema cache might need a refresh:
1. Go to Render dashboard → stocxer-ai service
2. Click **Manual Deploy** → **Clear build cache & deploy**

---

## 📊 What These Columns Do

| Column | Purpose |
|--------|---------|
| `signal_type` | Distinguishes STOCK vs OPTIONS signals |
| `strike` | Option strike price (e.g., 25250) |
| `option_type` | CE (Call) or PE (Put) |
| `expiry_date` | Option expiry date |
| `entry_price` | Recommended entry price |
| `reversal_probability` | Probability % from analysis |

---

## 🎯 Expected Result

After migration, option signals will save successfully:
```
✅ Saved OPTIONS signal for NIFTY: BUY PUT - ID: xxx
```

No more `PGRST204` errors!

---

## 📝 Files Updated

1. ✅ `database/add_options_columns.sql` - Migration script (NEW)
2. ✅ `database/schema.sql` - Updated with options columns
3. ℹ️ Main schema file now includes options support for future deployments

---

## Next Steps After Fix

1. ✅ Run migration in Supabase
2. ✅ Test an option scan from the app
3. ✅ Verify signals save to database
4. ✅ Add `MARKETAUX_API_KEY` to Render environment (if not already done)
