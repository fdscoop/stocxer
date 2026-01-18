# TradeWise Deployment Guide

## Architecture

**Frontend (Vercel):**
- Serves static HTML/CSS/JS files
- Ultra-fast CDN delivery
- ~2MB deployment size
- Free hosting

**Backend (Railway):**
- Full Python FastAPI application
- All ML libraries included
- Database connections
- Fyers API integration
- Supabase authentication

## Deployment Steps

### 1. Deploy Backend to Railway

Railway is already configured with `railway.json` and `Procfile`.

```bash
# Railway will automatically:
1. Install all dependencies from requirements.txt (including ML libraries)
2. Run database migrations
3. Start the FastAPI server
4. Expose it at: https://your-app.railway.app
```

**Railway Environment Variables:**
- `FYERS_CLIENT_ID`
- `FYERS_SECRET_KEY`
- `FYERS_REDIRECT_URI` (set to Railway URL)
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `POSTGRES_*` (if using Railway Postgres)
- `REDIS_*` (if using Railway Redis)

### 2. Deploy Frontend to Vercel

Vercel is now configured to serve ONLY static files - no Python backend.

```bash
# Vercel will:
1. Serve files from /static folder
2. Deploy to CDN
3. Provide HTTPS automatically
```

**Vercel Environment Variables:**
Set this in Vercel Dashboard:
- `RAILWAY_API_URL` = `https://your-app.railway.app`

Or inject it in the build:
```bash
# In Vercel build settings, add:
echo "window.RAILWAY_API_URL = '$RAILWAY_API_URL';" > static/env.js
```

### 3. Update Frontend to Use Railway Backend

Option A: Set environment variable in Vercel
- Add `RAILWAY_API_URL` in Vercel dashboard

Option B: Update config.js manually
```javascript
// In static/config.js, replace:
API_URL: 'https://your-actual-railway-app.railway.app'
```

### 4. Update CORS in Railway Backend

In Railway's `main.py`, update CORS origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-app.vercel.app",
        "http://localhost:8000",  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## File Structure

```
TradeWise/
├── static/              # Frontend (deployed to Vercel)
│   ├── index.html       # Main dashboard
│   ├── login.html       # Authentication
│   ├── screener.html    # Stock screener
│   ├── check_ml.html    # ML predictions
│   └── config.js        # API configuration
│
├── main.py              # Backend API (deployed to Railway)
├── requirements.txt     # All dependencies (ML included for Railway)
├── vercel.json          # Vercel config (static files only)
├── railway.json         # Railway config (full backend)
└── Procfile             # Railway start command
```

## Deployment Sizes

**Vercel (Frontend Only):**
- HTML/CSS/JS: ~2MB
- No Python, no dependencies
- Lightning fast CDN delivery

**Railway (Full Backend):**
- Python + all dependencies: ~500MB
- ML libraries included
- Full API capabilities
- No size limits on Railway

## Local Development

```bash
# Run full stack locally
python main.py  # Backend on :8000

# Or develop frontend only
cd static
python -m http.server 3000  # Serve static files
# Edit config.js to point to Railway backend
```

## Benefits of This Setup

✅ **Vercel (Frontend):**
- Free hosting
- Global CDN
- Automatic HTTPS
- Zero configuration
- Instant deployments

✅ **Railway (Backend):**
- Full ML capabilities
- No size limits
- Database support
- Background jobs
- Easy scaling

✅ **Separation of Concerns:**
- Frontend updates don't require backend rebuild
- Backend can use heavy ML libraries
- Better security (API keys only on backend)
- Independent scaling

## Testing

**Frontend (Vercel):**
```bash
curl https://your-app.vercel.app/
# Should return index.html
```

**Backend (Railway):**
```bash
curl https://your-app.railway.app/health
# Should return: {"status":"online"}
```

**Integration:**
```bash
# Login from Vercel frontend should call Railway backend
# Check browser DevTools Network tab
```

## Troubleshooting

**CORS Errors:**
- Add Vercel domain to Railway CORS origins
- Check browser console for specific error

**API Not Found:**
- Verify `RAILWAY_API_URL` is set correctly
- Check config.js has correct Railway URL

**Authentication Issues:**
- Ensure Supabase redirect URLs include both:
  - `https://your-app.vercel.app/*`
  - `https://your-app.railway.app/*`

## Cost

- **Vercel:** FREE (Hobby plan)
- **Railway:** ~$5/month (with usage)
- **Total:** ~$5/month for full-stack deployment

## Next Steps

1. Deploy backend to Railway ✓
2. Get Railway URL
3. Update `static/config.js` with Railway URL
4. Deploy frontend to Vercel ✓
5. Test login and API calls
6. Update Supabase redirect URLs
