# Option Expiry Dropdown Implementation

## Overview
Added a comprehensive expiry date dropdown for the option scanner in the dashboard. Users can now select from:
- **Weekly**: Nearest expiry (e.g., "29 Jan")
- **Next Weekly**: Second nearest expiry (e.g., "05 Feb")
- **Monthly**: Last occurrence of expiry day in the month (e.g., "27 Feb")
- **All Other Expiries**: Any additional expiries available from the exchange

## What Was Changed

### 1. Backend Updates

#### `/src/analytics/index_options.py`
- **Updated `get_expiry_dates()` method** (Line ~530):
  - Now returns `all_expiries` array with all available expiry dates from Fyers
  - Provides complete list of expiries in addition to weekly/monthly

- **Updated `analyze_option_chain()` method** (Line ~713):
  - Now accepts both keywords (`"weekly"`, `"monthly"`, `"next_weekly"`) AND actual dates (`"YYYY-MM-DD"`)
  - Automatically calculates days to expiry for any provided date
  - Falls back to weekly if invalid format provided

```python
# Now supports:
# - Keywords: "weekly", "monthly", "next_weekly"
# - Dates: "2026-01-29", "2026-02-05", etc.
```

### 2. Frontend Updates

#### `/frontend/app/options/page.tsx`
- **Added state for expiry management**:
  ```typescript
  const [expiryDates, setExpiryDates] = useState<ExpiryData | null>(null)
  const [loadingExpiries, setLoadingExpiries] = useState(false)
  ```

- **Implemented automatic expiry fetching**:
  - Fetches available expiries when index changes
  - Uses `/index/{index}/expiries` API endpoint
  - Displays loading state while fetching

- **Enhanced expiry dropdown**:
  - Shows human-readable dates (e.g., "Weekly - 29 Jan")
  - Displays all available expiries from exchange
  - Filters out duplicates (weekly/monthly already shown)
  - Auto-selects weekly expiry by default

- **Implemented real API integration**:
  - Replaced mock data with actual API calls to `/options/scan`
  - Passes selected expiry (keyword or date) to backend
  - Handles probability analysis from response
  - Graceful fallback to mock data on errors

## API Endpoints Used

### GET `/index/{index}/expiries`
Fetches available expiry dates for an index.

**Response:**
```json
{
  "index": "NIFTY",
  "expiries": {
    "weekly": "2026-01-29",
    "weekly_days": 2,
    "next_weekly": "2026-02-05",
    "next_weekly_days": 9,
    "monthly": "2026-02-26",
    "monthly_days": 30,
    "all_expiries": ["2026-01-29", "2026-02-05", "2026-02-12", "2026-02-19", "2026-02-26"]
  }
}
```

### GET `/options/scan`
Scans options with selected parameters.

**Query Parameters:**
- `index`: Index to scan (NIFTY, BANKNIFTY, etc.)
- `expiry`: Can be "weekly", "monthly", "next_weekly", OR actual date "2026-01-29"
- `min_volume`: Minimum volume filter
- `min_oi`: Minimum Open Interest filter

## User Experience

1. **User selects index** (NIFTY, BANKNIFTY, etc.)
2. **Dropdown automatically loads** available expiries for that index
3. **User sees clear options**:
   - "Weekly - 29 Jan" (nearest)
   - "Next Week - 05 Feb" (second nearest)
   - "Monthly - 27 Feb" (last occurrence in month)
   - "12 Feb 2026" (other available expiries)
4. **User selects preferred expiry** and clicks "Scan Options"
5. **Backend processes** with the exact expiry selected

## Benefits

✅ **Flexibility**: Users can scan any available expiry, not just weekly/monthly
✅ **Clarity**: Shows actual dates instead of vague terms like "weekly"
✅ **Accuracy**: Uses real expiry data from exchange, not calculated dates
✅ **User-Friendly**: Human-readable format (e.g., "29 Jan" instead of "2026-01-29")
✅ **Backwards Compatible**: Still accepts "weekly"/"monthly" keywords

## Technical Details

### Date Handling
- Backend returns dates in `YYYY-MM-DD` format
- Frontend displays in `DD MMM` format for readability
- Full date `DD MMM YYYY` shown for non-weekly/monthly expiries

### State Management
- Expiries fetched automatically on index change
- Loading state prevents premature scans
- Default selection to weekly expiry for convenience

### Error Handling
- Graceful fallback if expiries can't be fetched
- Invalid expiry formats default to weekly
- Mock data fallback for API failures

## Testing

To test the feature:
1. Navigate to `/options` in the dashboard
2. Select different indices and observe expiry options change
3. Select different expiries and run scans
4. Verify actual dates are shown in dropdown
5. Check that both keywords and dates work with backend

## Future Enhancements

Possible improvements:
- Show expiry in options results table
- Add expiry filtering in results
- Show days remaining until expiry
- Add expiry-based sorting
- Visual indicator for near-expiry options
