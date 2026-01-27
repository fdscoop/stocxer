# Session Management - Daily 7 AM IST Reset

## Overview
Stocxer AI now uses a **daily session reset** model instead of short inactivity timeouts. Users stay logged in all day and only need to re-login once per day at 7 AM IST.

## Key Features

### ✅ Long Session Duration
- **No more frequent re-logins** due to inactivity
- Sessions persist for 24+ hours
- Automatic token refresh enabled via Supabase
- Local storage persistence enabled

### ✅ Daily 7 AM IST Reset
- Sessions automatically expire at **7:00 AM IST** each day
- Users are logged out and redirected to landing page
- Clean slate each morning for fresh market analysis
- Aligns with Indian market pre-opening time (9:15 AM)

## How It Works

### 1. Login Process
```typescript
// When user logs in:
- Store auth token in localStorage
- Record current timestamp in IST
- Enable persistent session in Supabase client
```

### 2. Session Check on Page Load
```typescript
// Every time app loads:
- Check if current time is after today's 7 AM IST
- If last login was before 7 AM AND now is after 7 AM:
  → Logout and redirect to login page
- Otherwise:
  → Continue with active session
```

### 3. Token Refresh
```typescript
// Supabase automatically:
- Refreshes JWT tokens before expiry
- Maintains session across browser tabs
- Persists session across browser restarts
```

## Implementation Details

### Files Modified
1. **`frontend/lib/supabase.ts`**
   - Configure Supabase client with persistence options
   - Add `checkDailySessionReset()` function
   - Add `updateLastLoginTime()` function

2. **`frontend/app/page.tsx`**
   - Check session on mount
   - Auto-logout if past 7 AM reset time

3. **`frontend/app/login/page.tsx`**
   - Record login timestamp on successful login

### Configuration
```typescript
// Supabase client config
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,          // Keep session across reloads
    autoRefreshToken: true,        // Auto-refresh before expiry
    detectSessionInUrl: true,      // Handle OAuth callbacks
    storage: window.localStorage,  // Store in localStorage
    storageKey: 'stocxer-auth-token',
  },
})
```

### Session Reset Logic
```typescript
// Check if session should reset
export function checkDailySessionReset(): boolean {
  const lastLogin = localStorage.getItem('stocxer-last-login-date')
  const now = new Date()
  const istTime = new Date(now.getTime() + 5.5 * 60 * 60 * 1000) // UTC+5:30
  
  const today7AM = new Date(istTime)
  today7AM.setHours(7, 0, 0, 0)
  
  // If last login < 7 AM AND now >= 7 AM → logout
  if (lastLoginDate < today7AM && istTime >= today7AM) {
    return true // Time to logout
  }
  
  return false
}
```

## User Experience

### Before (❌ Old Behavior)
- Session expires after ~5-10 minutes of inactivity
- Frequent "Session expired" messages
- User has to re-login multiple times per day
- Frustrating workflow interruption

### After (✅ New Behavior)
- Login once in the morning
- Stay logged in entire day
- Only re-login at 7 AM IST daily
- Smooth, uninterrupted workflow

## Why 7 AM IST?

1. **Pre-market timing**: Indian stock market pre-opening is 9:00-9:15 AM IST
2. **Fresh analysis**: Daily reset ensures users get fresh probability calculations
3. **Database cleanup**: Aligns with backend data refresh schedules
4. **User habit**: Most traders start their day before market opens

## Testing

### Test Session Persistence
1. Login to app
2. Wait 30 minutes (previous timeout period)
3. ✅ Session should remain active
4. Use app normally - no re-login required

### Test Daily Reset
1. Login before 7 AM IST
2. Wait until after 7 AM IST
3. Refresh/navigate to app
4. ✅ Should auto-logout and redirect to login

### Test Across Browser Restarts
1. Login to app
2. Close browser completely
3. Reopen browser and navigate to app
4. ✅ Should still be logged in (if before 7 AM)

## Troubleshooting

### Session still expiring quickly?
- Clear browser cache and localStorage
- Ensure `.env.local` has correct Supabase keys
- Check browser console for auth errors

### Not logging out at 7 AM?
- Verify system timezone is correct
- Check localStorage for `stocxer-last-login-date`
- Browser must be active (refresh page) for check to run

### Token refresh failing?
- Verify Supabase project settings
- Check JWT expiration settings in Supabase dashboard
- Ensure `NEXT_PUBLIC_SUPABASE_ANON_KEY` is valid

## Backend Compatibility

This change is **frontend-only** and fully compatible with existing backend:
- Backend JWT tokens remain unchanged
- API authentication flow unchanged
- Supabase auth system handles token refresh
- No backend modifications required

## Future Enhancements

Potential improvements:
- [ ] Configurable reset time per user
- [ ] Weekend/holiday skip (no trading days)
- [ ] Background token refresh (service worker)
- [ ] Multi-device session sync
- [ ] Session activity analytics

---

**Status**: ✅ Deployed  
**Commit**: 7f3b661  
**Date**: January 27, 2026
