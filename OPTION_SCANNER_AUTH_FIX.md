# ✅ Fixed: Option Scanner Authentication

## Issue Resolution
The option scanner (index.html) was not using the same authentication method as the stock screener (screener.html), causing it to fail when calling Fyers-dependent endpoints.

## Changes Made

### 1. Added Authorization Headers to All API Calls

Updated the following functions in `/Users/bineshbalan/TradeWise/static/index.html`:

#### `loadIndexData()` - Line ~1332
```javascript
const headers = {};
if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
}
const res = await fetch(`${API}/index/overview`, { headers });
```

#### `loadMarketRegime()` - Line ~1413
```javascript
const headers = {};
if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
}
const res = await fetch(`${API}/index/market-regime`, { headers });
```

#### `loadExpiries()` - Line ~1441
```javascript
const headers = {};
if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
}
const res = await fetch(`${API}/index/${currentIndex}/expiries`, { headers });
```

#### `refreshChain()` - Line ~1494
```javascript
const headers = {};
if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
}
const res = await fetch(`${API}/index/${currentIndex}/chain?expiry=${currentExpiry}`, { headers });
```

#### `refreshSignal()` - Line ~1707
```javascript
const headers = {};
if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
}
const res = await fetch(`${API}/index/${currentIndex}/signal`, { headers });
```

### 2. Added Fyers Authentication Check Function

Implemented `checkFyersAuth()` function (similar to screener.html) - Line ~1395:

```javascript
// Check Fyers authentication status
async function checkFyersAuth() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API}/api/fyers/token`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            // No Fyers token - show authentication modal
            console.warn('⚠️ Fyers authentication required for live data');
            showAuthRequired();
        }
    } catch (error) {
        console.error('Auth check error:', error);
    }
}
```

### 3. Added Fyers Auth Check on Page Load

Line ~1036:
```javascript
// Check auth before loading anything
if (!checkAuth()) {
    throw new Error('Not authenticated');
}

// Check Fyers authentication status
if (authToken) {
    checkFyersAuth();
}
```

## How It Works Now

1. **Page Load**:
   - Checks Supabase authentication (user must be logged in)
   - Checks Fyers authentication via `/api/fyers/token` endpoint
   - If no Fyers token, shows authentication modal

2. **API Calls**:
   - All API requests include `Authorization: Bearer <token>` header
   - Backend can verify user identity from Supabase
   - Backend can load user's Fyers token from `fyers_tokens` table

3. **Authentication Flow**:
   - Same as screener.html
   - Uses localStorage to store auth_token
   - Sends token with every API request
   - Backend validates and loads corresponding Fyers token

## Testing

### Test with Valid Auth Token
```bash
# The option scanner now sends Authorization header like screener does
# Test locally at: http://localhost:8000/
# Or via ngrok: https://7ba080a7b86b.ngrok-free.app/
```

### Expected Behavior

**Without Fyers Token**:
- Shows modal: "🔒 Fyers Authentication Required"
- Button to authenticate: "Authenticate Now"
- Clear instructions on how to connect Fyers

**With Fyers Token**:
- Loads live market data
- Shows real-time prices
- Option chain displays correctly
- Signal generation works

## Files Modified

1. `/Users/bineshbalan/TradeWise/static/index.html`
   - Added Authorization headers to 5 API call functions
   - Added `checkFyersAuth()` function
   - Added Fyers auth check on page load

## Server Access

- **Local**: http://localhost:8000/
- **Public**: https://7ba080a7b86b.ngrok-free.app/
- **Screener**: https://7ba080a7b86b.ngrok-free.app/static/screener.html

## Next Steps

1. Login to TradeWise with Supabase credentials
2. Visit option scanner (index.html)
3. If prompted, complete Fyers authentication
4. Both screener and option scanner will work with same Fyers token

---

**Status**: ✅ Fixed - Option scanner now uses proper authentication method
**Date**: 2026-01-19
