# TradeWise: Vercel + Railway Deployment - Quick Start

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    TradeWise Stack                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────┐          ┌──────────────────┐     │
│  │     VERCEL       │          │     RAILWAY      │     │
│  │  (Frontend)      │          │     (Backend)    │     │
│  ├──────────────────┤          ├──────────────────┤     │
│  │ • Static Files   │ ◄────────│ • FastAPI        │     │
│  │ • HTML/CSS/JS    │ API      │ • ML Libraries   │     │
│  │ • ~2MB           │ Calls    │ • Database       │     │
│  │ • Free/CDN       │          │ • Fyers API      │     │
│  │ • Instant        │          │ • Supabase Auth  │     │
│  └──────────────────┘          └──────────────────┘     │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Deployment Checklist

### Step 1: Deploy Backend to Railway

Railway is already configured. Just ensure environment variables are set:

```
✅ FYERS_CLIENT_ID
✅ FYERS_SECRET_KEY
✅ FYERS_REDIRECT_URI = https://your-railway-app.railway.app
✅ SUPABASE_URL
✅ SUPABASE_KEY
✅ Other DB/Redis configs if needed
```

**Expected size:** ~500MB (includes all ML libraries)  
**What's deployed:** Full Python backend with everything

---

### Step 2: Deploy Frontend to Vercel

Vercel is now configured for static files ONLY.

**What happens:**
1. Vercel ignores all Python files
2. Only serves /static folder
3. ~2MB total deployment

**Environment Variable:**
Set in Vercel dashboard:
```
RAILWAY_API_URL = https://your-railway-app.railway.app
```

Or update `static/config.js` directly:
```javascript
API_URL: 'https://your-railway-app.railway.app'
```

---

### Step 3: Update Supabase Redirect URLs

Go to: https://supabase.com/dashboard/project/cxbcpmouqkajlxzmbomu/auth/url-configuration

Add these redirect URLs:
```
https://your-vercel-app.vercel.app/*
https://your-railway-app.railway.app/*
http://localhost:8000/*
```

---

## File Changes Made

| File | Change | Purpose |
|------|--------|---------|
| `vercel.json` | Removed Python builds | Serve static files only |
| `.vercelignore` | Exclude backend code | Only deploy /static |
| `static/config.js` | NEW - API config | Point to Railway backend |
| `static/login.html` | Use config.js URL | Dynamic API endpoint |
| `VERCEL_RAILWAY_DEPLOYMENT.md` | Detailed guide | Full deployment docs |

---

## Deployment Sizes

| Component | Before | After |
|-----------|--------|-------|
| **Vercel** | 314MB ❌ | 2MB ✅ |
| **Railway** | N/A | ~500MB |
| **Total** | FAILED | ~502MB ✅ |

**Reduction:** 99.4% on Vercel! 🚀

---

## How Frontend Calls Backend

```javascript
// In browser JavaScript:
const API_BASE = window.RAILWAY_API_URL || window.location.origin;

// Example API call:
fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    body: JSON.stringify({email, password})
})
```

**Local development:** `http://localhost:8000`  
**Vercel → Railway:** `https://your-railway-app.railway.app`

---

## Testing Deployment

**Frontend is live:**
```bash
curl https://your-app.vercel.app/
# Should return index.html
```

**Backend is live:**
```bash
curl https://your-app.railway.app/health
# Should return: {"status":"online"}
```

**Integration test:**
1. Open https://your-app.vercel.app/login
2. Try to login
3. Check browser DevTools → Network tab
4. Should see requests to Railway backend

---

## If Something Goes Wrong

**CORS errors:**
- Update Railway CORS to include Vercel domain

**API not found:**
- Check `static/config.js` has correct Railway URL
- Check `RAILWAY_API_URL` env var in Vercel

**Blank page:**
- Check browser console
- Verify /static files are deployed

---

## Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| **Vercel** | FREE | Hobby plan, static files |
| **Railway** | ~$5/month | With included $5 credit |
| **Supabase** | FREE | Hobby plan |
| **Total** | ~$0-5/month | Very affordable! |

---

## Next Deployment Steps

After you've verified everything works:

1. ✅ Push changes to GitHub
2. ✅ Railway auto-deploys (watch build logs)
3. ✅ Vercel auto-deploys (watch build logs)
4. ✅ Test login: https://your-vercel-app.vercel.app/login
5. ✅ Test screener: https://your-vercel-app.vercel.app/screener

---

## Key Benefits

✅ **Super fast:** Vercel CDN for global delivery  
✅ **Cost-effective:** Free frontend, cheap backend  
✅ **Scalable:** Deploy frontend/backend independently  
✅ **Secure:** API keys only on Railway  
✅ **Reliable:** 99.9% uptime on both  
✅ **Easy:** Auto-deploys on git push  

---

**Commit:** ee05cf6  
**Status:** READY FOR DEPLOYMENT 🚀

For detailed deployment instructions, see: `VERCEL_RAILWAY_DEPLOYMENT.md`
