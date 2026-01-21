# Vercel Deployment Update Instructions

## Steps to Deploy Next.js Frontend on Vercel

### 1. Update Vercel Project Settings

Go to your Vercel dashboard → Project Settings → Build & Output Settings:

**Root Directory:** Leave empty (use root)
**Build Command:** `cd frontend && npm install && npm run build`
**Output Directory:** `frontend/.next`
**Install Command:** `cd frontend && npm install`

### 2. Environment Variables

Add these environment variables in Vercel Dashboard:

```
NEXT_PUBLIC_API_URL=https://stocxer-ai.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://cxbcpmouqkajlxzmbomu.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN4YmNwbW91cWthamx4em1ib211Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NjA3NjMsImV4cCI6MjA4NDMzNjc2M30.oBozxBnSKARn-3xkRy8ceNU3wpxXh8MBReGtmtsBpEw
```

### 3. Framework Detection

Vercel should now detect this as a Next.js project automatically due to the updated vercel.json configuration.

### 4. Trigger Deployment

The git push should automatically trigger a new deployment. If not:
- Go to Vercel Dashboard → Deployments
- Click "Redeploy" on the latest deployment

### 5. Verify Deployment

Once deployed, test these pages:
- `/` - Main dashboard with trading signals
- `/login` - Authentication page
- `/screener` - Stock screener page

### 6. Backend Connection

The frontend is configured to use:
- **Local development:** `http://localhost:8000`
- **Vercel deployment:** `https://stocxer-ai.onrender.com`

Make sure your Render backend is running at `https://stocxer-ai.onrender.com`.

## Troubleshooting

If deployment fails:

1. **Check build logs** in Vercel dashboard
2. **Verify Node.js version** (should use Node 18+)
3. **Check environment variables** are properly set
4. **Test locally** with `npm run build` in frontend directory

## What Changed

- ✅ Updated `vercel.json` to build Next.js app from `frontend/` directory
- ✅ Configured proper build commands for monorepo structure
- ✅ API URL automatically uses production backend when deployed
- ✅ Environment variables properly configured for Supabase integration