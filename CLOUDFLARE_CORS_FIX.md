# Cloudflare CORS Configuration Fix

## Problem
Cloudflare is caching CORS preflight (OPTIONS) responses, causing stale "No Access-Control-Allow-Origin" errors even after backend CORS is fixed.

## Solutions

### Option 1: Purge Cloudflare Cache (Quick Fix)
1. Go to https://dash.cloudflare.com
2. Select your domain
3. Go to **Caching** → **Configuration**
4. Click **Purge Everything**
5. Confirm the purge
6. Wait 30 seconds and test again

### Option 2: Configure Page Rules to Bypass OPTIONS Requests
1. Go to https://dash.cloudflare.com
2. Select your domain
3. Go to **Rules** → **Page Rules**
4. Click **Create Page Rule**
5. URL pattern: `stocxer-ai.onrender.com/*`
6. Settings:
   - **Cache Level**: Bypass
   - Or add: **Bypass Cache on Cookie** (for any cookie)
7. Save and Deploy

### Option 3: Add Transform Rule for OPTIONS Requests (Best)
1. Go to **Rules** → **Transform Rules**
2. Create **Modify Response Header** rule:
   - **When incoming requests match**: `http.request.method eq "OPTIONS"`
   - **Then**: Set Dynamic `Cache-Control` to `no-store, no-cache, must-revalidate, max-age=0`
3. Save

### Option 4: Disable Cloudflare Proxy (Not Recommended)
In your DNS settings, click the orange cloud to make it gray (DNS only).

## Verification
After applying any fix, verify with:
```bash
curl -X OPTIONS -H "Origin: https://www.stocxer.in" \
  -H "Access-Control-Request-Method: GET" \
  -I https://stocxer-ai.onrender.com/options/scan
```

Should show:
- `access-control-allow-origin: https://www.stocxer.in`
- `access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT`

## Why Screener Works But Options Scanner Doesn't
Both endpoints go through Cloudflare, but:
- Screener endpoint may have been accessed after CORS fix (fresh cache)
- Options endpoint has stale cache from before CORS fix
- Cloudflare's edge cache TTL keeps the old response

## Recommended Solution
**Purge cache now** (Option 1), then implement **Transform Rule** (Option 3) to prevent future issues.
