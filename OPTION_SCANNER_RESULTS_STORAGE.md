# Option Scanner Results Storage & Display

## Overview
Complete storage system for actionable option trading signals from `/signals/{symbol}/actionable` endpoint. Stores full JSON signal data in dedicated `option_scanner_results` table with structured fields for easy querying.

## What This Solves

**Problem**: Option scanner signals from `/signals/{symbol}/actionable` were returning rich data but not being properly stored or displayed on dashboard.

**Solution**: 
- ✅ New dedicated table `option_scanner_results` for complete signal storage
- ✅ Automatic saving when authenticated users request signals
- ✅ API endpoints to fetch latest and recent scanner results
- ✅ Dashboard integration ready

---

## Database Schema

### Table: `option_scanner_results`

Stores complete actionable trading signals with structured fields + full JSON.

**Key Fields**:
```sql
- id (UUID)                    -- Unique signal ID
- user_id (UUID)               -- User who requested signal
- index (TEXT)                 -- NIFTY, BANKNIFTY, FINNIFTY
- symbol (TEXT)                -- NSE:NIFTY50-INDEX
- signal (TEXT)                -- ICT_BULLISH_REVERSAL, etc
- action (TEXT)                -- BUY, SELL, WAIT, AVOID
- confidence (DECIMAL)         -- 0-100
- strike (DECIMAL)             -- Option strike price
- option_type (TEXT)           -- CE or PE
- trading_symbol (TEXT)        -- NSE:NIFTY2620325450CE
- expiry_date (DATE)           -- Option expiry
- entry_price (DECIMAL)        -- Recommended entry
- target_1, target_2 (DECIMAL) -- Profit targets
- stop_loss (DECIMAL)          -- Risk management
- delta, gamma, theta, vega    -- Greeks
- spot_price, vix, pcr_oi      -- Market data
- full_signal_data (JSONB)     -- Complete JSON response
- timestamp (TIMESTAMPTZ)      -- Signal generation time
```

**Indexes**:
- `user_id` + `timestamp` (fast user queries)
- `index` (filter by NIFTY/BANKNIFTY)
- `action` (filter BUY/SELL signals)
- `confidence` (sort by quality)

---

## API Endpoints

### 1. **Get Latest Signal** (Dashboard)
```bash
GET /options/scanner-results/latest?index=NIFTY

Headers:
  Authorization: Bearer <token>

Response:
{
  "status": "success",
  "id": "uuid",
  "index": "NIFTY",
  "action": "BUY",
  "strike": 25450,
  "option_type": "CE",
  "entry_price": 141.9,
  "target_1": 198.66,
  "target_2": 255.42,
  "stop_loss": 85.14,
  "confidence": 29.5,
  "confidence_level": "AVOID",
  "full_signal_data": { ... },  // Complete JSON
  "timestamp": "2026-01-30T04:34:16Z"
}
```

### 2. **Get Recent Signals** (History)
```bash
GET /options/scanner-results/recent?hours=24&limit=20&index=NIFTY

Response:
{
  "status": "success",
  "count": 15,
  "time_range_hours": 24,
  "index_filter": "NIFTY",
  "results": [
    { /* signal 1 */ },
    { /* signal 2 */ },
    ...
  ]
}
```

---

## How It Works

### Signal Generation & Storage Flow

```
User Dashboard → Clicks "Scan NIFTY"
    ↓
Frontend → GET /signals/NIFTY/actionable
    ↓
Backend:
  1. MTF ICT Analysis (all timeframes)
  2. Option Chain Analysis
  3. ML Predictions
  4. Constituent Analysis (if not quick_mode)
  5. Generate Actionable Signal
    ↓
  6. Save to option_scanner_results table ✅
    ↓
Frontend:
  - Display signal on dashboard
  - Show strike, entry, targets, risk/reward
  - Store in recent scans
```

### Automatic Saving

When `/signals/{symbol}/actionable` is called with authentication:
```python
# In main.py
if authorization:
    user = await auth_service.get_current_user(token)
    save_result = await screener_service.save_option_scanner_result(
        user_id=str(user.id),
        signal_data=signal  # Complete JSON
    )
```

All signals are automatically saved - no extra API calls needed.

---

## Dashboard Integration

### Current Status
✅ **Backend Ready**: Signals are saved automatically  
✅ **API Endpoints**: Created and ready to use  
⏳ **Frontend**: Needs update to fetch from new endpoints

### To Display on Dashboard

**Option 1: Replace `/screener/latest` with option scanner data**
```typescript
// In frontend/app/page.tsx
const fetchLatestScanResults = async (token: string) => {
  // Change from: GET /screener/latest
  // To: GET /options/scanner-results/latest
  
  const response = await fetch(`${apiUrl}/options/scanner-results/latest?index=${selectedIndex}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  
  const data = await response.json()
  if (data.status === 'success') {
    // Use data.full_signal_data for complete signal
    setTradingSignal(data.full_signal_data)
  }
}
```

**Option 2: Add separate "Option Signals" section**
```typescript
// Show recent option signals in a card
const [optionSignals, setOptionSignals] = useState([])

const fetchRecentOptionSignals = async (token: string) => {
  const response = await fetch(`${apiUrl}/options/scanner-results/recent?hours=24&limit=10`, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  const data = await response.json()
  setOptionSignals(data.results)
}
```

---

## Migration Instructions

### Step 1: Create Table in Supabase
```sql
-- Run in Supabase SQL Editor
-- File: database/migrations/create_option_scanner_results.sql

-- This creates:
-- ✅ option_scanner_results table
-- ✅ Indexes for fast queries
-- ✅ RLS policies for user isolation
-- ✅ Auto-update timestamp trigger
```

### Step 2: Deploy Backend Changes
```bash
# Already included in code - no extra steps
# Signals will auto-save on next deployment
```

### Step 3: Test
```bash
# Test signal generation
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/signals/NIFTY/actionable"

# Check if saved
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/options/scanner-results/latest"
```

---

## Data Example

### Sample Signal Saved
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user-uuid",
  "index": "NIFTY",
  "signal": "ICT_NEUTRAL_BIAS",
  "action": "WAIT",
  "confidence": 29.5,
  "confidence_level": "AVOID",
  "strike": 25450,
  "option_type": "CE",
  "trading_symbol": "NSE:NIFTY2620325450CE",
  "expiry_date": "2026-02-03",
  "days_to_expiry": 4,
  "entry_price": 141.9,
  "ltp": 141.9,
  "target_1": 198.66,
  "target_2": 255.42,
  "stop_loss": 85.14,
  "risk_per_lot": 2838.0,
  "delta": 0.376,
  "gamma": 0.001,
  "theta": -18.9261,
  "vega": 10.0571,
  "spot_price": 25314.1,
  "vix": 13.72,
  "pcr_oi": 0.78,
  "htf_direction": "neutral",
  "htf_strength": 30,
  "is_reversal_play": false,
  "trading_mode": "INTRADAY",
  "timestamp": "2026-01-30T04:34:16Z",
  "full_signal_data": { /* Complete JSON response */ }
}
```

---

## Query Examples

### Get Today's NIFTY Signals
```sql
SELECT 
  action,
  strike,
  option_type,
  entry_price,
  confidence,
  timestamp
FROM option_scanner_results
WHERE user_id = 'your-user-id'
  AND index = 'NIFTY'
  AND DATE(timestamp) = CURRENT_DATE
ORDER BY timestamp DESC;
```

### Get High Confidence BUY Signals (Last 7 Days)
```sql
SELECT *
FROM option_scanner_results
WHERE user_id = 'your-user-id'
  AND action = 'BUY'
  AND confidence >= 70
  AND timestamp >= NOW() - INTERVAL '7 days'
ORDER BY confidence DESC, timestamp DESC;
```

### Get Signals by Strike Range
```sql
SELECT 
  index,
  strike,
  option_type,
  entry_price,
  action,
  confidence
FROM option_scanner_results
WHERE user_id = 'your-user-id'
  AND strike BETWEEN 25000 AND 26000
  AND expiry_date >= CURRENT_DATE
ORDER BY confidence DESC;
```

---

## Benefits

✅ **Complete Data**: Full JSON + structured fields  
✅ **Fast Queries**: Indexed for performance  
✅ **User Isolation**: RLS ensures privacy  
✅ **Historical Analysis**: Track signal performance  
✅ **Dashboard Ready**: Easy to display  
✅ **Backward Compatible**: Old screener_results still works  

---

## Next Steps

1. ✅ **Migration**: Run `create_option_scanner_results.sql` in Supabase
2. ⏳ **Deploy**: Push to production (auto-saves signals)
3. ⏳ **Frontend Update**: Modify dashboard to fetch from new endpoints
4. ⏳ **Testing**: Verify signals appear on dashboard

---

## Files Changed

1. **database/migrations/create_option_scanner_results.sql** - New table schema
2. **src/services/screener_service.py** - Save/fetch methods
3. **main.py** - Updated `/signals/actionable` to save, added new endpoints

---

## Support

**Issue**: Signals not showing on dashboard?
- Check: Did you run the migration SQL?
- Check: Is user authenticated when calling endpoint?
- Check: Frontend pointing to correct API endpoint?

**Issue**: RLS policy blocking inserts?
- Solution: Service uses `supabase_admin` client (bypasses RLS)

**Issue**: Want to test without frontend?
```bash
# Generate and save signal
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/signals/NIFTY/actionable"

# Fetch latest
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/options/scanner-results/latest?index=NIFTY"
```
