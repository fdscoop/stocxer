# Stock Screener - Custom Stock Selection Feature

## Overview
The stock screener now supports two scanning modes:
1. **Random Scan** - Original functionality to scan a random selection of stocks
2. **Select Stocks** - NEW: Search and select specific stocks/indices to scan

## Features Added

### 1. Stock Search Box
- Type keywords to search through 500+ NSE stocks
- Search by stock name or symbol (e.g., "RELIANCE", "TCS", "HDFC")
- Real-time filtering as you type
- Shows up to 100 matching results

### 2. Multi-Select Functionality
- Click on any stock to add it to your selection
- Visual checkboxes show selected stocks
- Selected stocks appear as badges for easy review
- Click the X on badges to remove stocks

### 3. Quick Select Presets
- **NIFTY 50** - Instantly select all 50 NIFTY index stocks
- **Bank Nifty** - Select all banking sector stocks
- **Clear All** - Remove all selections

### 4. Multiple Index Scanning
You can now scan multiple indices simultaneously by:
- Using the NIFTY 50 preset to scan the entire index
- Using the Bank Nifty preset for banking stocks
- Manually selecting stocks from different sectors
- Combining stocks from multiple indices

## How to Use

### Random Scan Mode (Original)
1. Select "Random Scan" button
2. Choose number of stocks (25, 50, 100, or 200)
3. Set minimum confidence level (60%, 70%, or 80%)
4. Choose action filter (All, BUY Only, or SELL Only)
5. Click "Scan Stocks"

### Custom Stock Selection Mode (NEW)
1. Click "Select Stocks" button
2. Choose a quick preset OR use the search box:
   - Click "NIFTY 50" to select all NIFTY stocks
   - Click "Bank Nifty" to select banking stocks
   - Type in the search box to find specific stocks
3. Click on stocks to add them to your selection
4. Review selected stocks in the badge area
5. Set minimum confidence level and action filter
6. Click "Scan X Stocks" to run the analysis

### Scanning Multiple Indices Example
**To scan both NIFTY and Bank Nifty:**
1. Click "Select Stocks"
2. Click "NIFTY 50" preset (50 stocks selected)
3. The stocks remain selected
4. Search for other stocks or keep current selection
5. Click "Scan 50 Stocks"

**To scan specific stocks across sectors:**
1. Click "Select Stocks"
2. Search "RELIANCE" and select it
3. Search "TCS" and select it
4. Search "HDFCBANK" and select it
5. Continue adding stocks as needed
6. Click "Scan X Stocks"

## Technical Implementation

### Frontend Changes
- **File**: `/frontend/app/screener/page.tsx`
- Added stock selection state management
- Implemented search and filter logic
- Created stock picker UI with checkboxes
- Added quick select presets for common indices

### Backend Changes
- **File**: `/main.py`
- Modified POST endpoint to accept `symbols` parameter
- Updated `scan_stocks()` to handle comma-separated symbol list
- Existing `get_stock_list()` endpoint provides searchable stock data

### API Endpoints Used

#### Get Stock List
```
GET /screener/stocks/list
Response: {
  "status": "success",
  "total": 500,
  "stocks": [
    {
      "symbol": "NSE:RELIANCE-EQ",
      "name": "Reliance Industries Ltd",
      "short_name": "RELIANCE"
    },
    ...
  ]
}
```

#### Scan Stocks (Updated)
```
POST /api/screener/scan
Headers: Authorization: Bearer <token>
Body: {
  "symbols": "NSE:RELIANCE-EQ,NSE:TCS-EQ,NSE:HDFCBANK-EQ", // Optional
  "min_confidence": 70,
  "action": "BUY"
}
```

## Benefits

### For Traders
- **Focused Analysis**: Scan only the stocks you're interested in
- **Index Tracking**: Easily scan entire indices like NIFTY 50
- **Sector Analysis**: Select all stocks from a specific sector
- **Time Saving**: Quick presets for common stock groups
- **Flexibility**: Mix and match stocks from different categories

### Performance
- Scans specific stocks faster than random sampling
- Reduced API calls when scanning fewer stocks
- Better control over scan scope and time

## Rate Limiting
- **Random Mode**: Scans up to 200 stocks with 600ms delay between each
- **Custom Mode**: Scans your selected stocks (no limit on count)
- Each stock takes ~0.6 seconds to analyze
- Example: 50 stocks = ~30 seconds scan time

## UI Components Added
- `Checkbox` component for multi-select
- Stock picker dropdown with search
- Badge display for selected stocks
- Mode toggle buttons
- Quick select preset buttons

## Future Enhancements
Potential improvements:
- Save custom stock lists for reuse
- Add more preset lists (IT stocks, Pharma stocks, etc.)
- Export scan results for selected stocks
- Compare performance across different stock groups
- Historical comparison of index performance

## Testing
To test the new functionality:
1. Start the backend: `python main.py`
2. Start the frontend: `cd frontend && npm run dev`
3. Login to the screener page
4. Try both scan modes
5. Test search functionality
6. Test quick select presets
7. Verify scan results

## Troubleshooting

**Stock list not loading**
- Check API connection
- Verify backend is running
- Check browser console for errors

**Selected stocks not appearing**
- Click the checkbox to select
- Stocks appear as badges below search box

**Scan button disabled**
- Ensure at least one stock is selected in custom mode
- Check that you're logged in and authenticated

## Notes
- Stocks must be in NSE format: `NSE:SYMBOL-EQ`
- Backend automatically formats symbols if needed
- Search is case-insensitive
- Results are saved to your account automatically
