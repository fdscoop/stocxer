# Option Scanner - Expiry Day Exclusion

## Overview
Modified the option scanner to automatically exclude options expiring **today** (IST timezone) from the available expiry dates. This prevents users from accidentally selecting expiry day options, which are highly risky due to extreme time decay.

## Changes Made

### 1. Updated `src/analytics/index_options.py`

#### Modified `get_expiry_dates()` method:
- **Added IST timezone support**: Uses `pytz` to get the current date in IST (Asia/Kolkata timezone)
- **Filters out today's expiry**: When parsing expiry dates from Fyers API, any expiry matching today's date is excluded
- **Enhanced logging**: Logs when today's expiry is excluded with clear message
- **Updated fallback logic**: Also excludes today's date in the fallback calculation when Fyers API is unavailable

#### Key Code Changes:

**Before:**
```python
def get_expiry_dates(self, index: str) -> Dict[str, str]:
    today = datetime.now()
    # ... fetched all expiries including today
```

**After:**
```python
def get_expiry_dates(self, index: str) -> Dict[str, str]:
    # Use IST timezone for accurate date comparison
    from pytz import timezone as pytz_timezone
    ist = pytz_timezone('Asia/Kolkata')
    today = datetime.now(ist).date()
    
    # ... filters out expiries matching today
    if expiry_date.date() != today:
        expiry_dates.append(expiry_date)
    else:
        logger.info(f"🚫 Excluding today's expiry: {date_str} (expiry day options not recommended)")
```

### 2. Updated `requirements.txt`
- **Added `pytz>=2023.3`**: Explicit dependency for timezone support to ensure it's always available

### 3. Created Test Script
- **Added `test_expiry_exclusion.py`**: Test script to verify the expiry exclusion logic works correctly
- Successfully tested and confirmed today's expiry is excluded

## How It Works

### Before the Change
- If today is an expiry day (e.g., Tuesday), the scanner would include today's expiry in the dropdown
- Users could accidentally select expiring options with extreme time decay
- Risk of poor trade entries on expiry day

### After the Change
1. System checks current date in **IST timezone** (India Standard Time)
2. When fetching expiries from Fyers API, compares each expiry date with today
3. If an expiry matches today's date, it's **excluded** from the list
4. The nearest available expiry becomes the next expiry date (not today)
5. Logs clearly show when today's expiry is excluded

### Example Scenario
**If today is Tuesday, January 30, 2026 (expiry day):**

**Before:**
- Available expiries: Jan 30 (Today), Feb 06, Feb 13, Feb 27
- Risk: User might select Jan 30 expiry

**After:**
- Available expiries: Feb 06, Feb 13, Feb 27
- Safe: Today's expiry is automatically excluded
- Log message: "🚫 Excluding today's expiry: 30-01-2026 (expiry day options not recommended)"

## Benefits

✅ **Safer Trading**: Prevents accidental selection of expiry day options  
✅ **Better Risk Management**: Avoids extreme theta decay on expiry day  
✅ **Timezone Accurate**: Uses IST for accurate date comparison (not server timezone)  
✅ **Clear Logging**: Explicit messages when expiry is excluded  
✅ **Backward Compatible**: Existing code continues to work normally on non-expiry days  
✅ **Fallback Support**: Also works when using calculated expiries instead of API data  

## Testing

### Test Results
```
Current IST Date: 2026-01-29 (Thursday)
Sample Expiry Dates (Before Filtering): 5
Filtered expiries: 4
Excluded: 1
✅ TEST PASSED: Expiry exclusion logic working correctly!
```

### Manual Testing
1. Navigate to `/options` page in the dashboard
2. Select an index (NIFTY, BANKNIFTY, etc.)
3. Check the expiry dropdown
4. **On expiry day**: Today's expiry will not appear in the list
5. **On non-expiry days**: All future expiries are shown normally

## Technical Details

### Date Comparison
- Uses `date()` comparison (not `datetime`) to avoid time component issues
- IST timezone ensures accuracy regardless of server location
- Comparison: `expiry_date.date() != today.date()`

### Timezone Handling
```python
from pytz import timezone as pytz_timezone
ist = pytz_timezone('Asia/Kolkata')
today = datetime.now(ist).date()
```

### Fallback Logic
Even when Fyers API is unavailable and fallback calculations are used:
```python
# Skip to next week if today is Tuesday (expiry day)
days_ahead = (1 - today_datetime.weekday()) % 7
if days_ahead == 0:  # Today is Tuesday
    days_ahead = 7
```

## Files Modified

1. **src/analytics/index_options.py** - Main logic for expiry exclusion
2. **requirements.txt** - Added pytz dependency
3. **test_expiry_exclusion.py** - Test script (new file)

## Impact on Existing Features

- ✅ No breaking changes
- ✅ Existing API endpoints work normally
- ✅ Frontend dropdown automatically reflects the filtered expiries
- ✅ All other scanner functionality remains unchanged

## Deployment Notes

1. **Install new dependency**: `pip install -r requirements.txt` (adds pytz)
2. **No database changes**: No migrations needed
3. **No frontend changes**: Frontend automatically adapts to filtered expiries
4. **Restart required**: Restart the FastAPI server after deployment

## Edge Cases Handled

1. **Only one expiry available and it's today**: Returns empty or moves to next available
2. **Fallback calculation on expiry day**: Skips today and calculates next week
3. **Different timezones**: Uses IST regardless of server timezone
4. **Market holidays**: Still excludes if expiry falls on today (holiday or not)

## Future Enhancements (Optional)

- Add UI indicator showing why certain expiries are hidden
- Show warning message if user tries to scan on expiry day
- Add config option to override expiry day exclusion (for advanced users)
- Track excluded expiries in analytics

---

**Status**: ✅ **IMPLEMENTED & TESTED**  
**Date**: January 29, 2026  
**Impact**: Low-risk, high-value safety feature
