# TradeWise Deployment Guide

## Prerequisites

- Git installed
- GitHub account
- Vercel account (for Vercel deployment)
- Railway account (for Railway deployment)

## Environment Variables

All platforms require these environment variables:

```
FYERS_APP_ID=your_fyers_app_id
FYERS_SECRET_KEY=your_fyers_secret_key
FYERS_REDIRECT_URL=https://your-domain.com/callback
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
LOG_LEVEL=INFO
ENVIRONMENT=production
```

## Deploy to GitHub

1. **Initialize Git (if not already done)**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Add remote repository**
   ```bash
   git remote add origin https://github.com/fdscoop/stocxer.git
   git branch -M main
   ```

3. **Push to GitHub**
   ```bash
   git push -u origin main
   ```

## Deploy to Vercel

### Option 1: Via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository: `fdscoop/stocxer`
4. Configure:
   - **Framework Preset**: Other
   - **Build Command**: `pip install -r requirements.txt`
   - **Output Directory**: Leave empty
5. Add Environment Variables (from list above)
6. Click "Deploy"

### Option 2: Via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# Add environment variables
vercel env add FYERS_APP_ID
vercel env add FYERS_SECRET_KEY
vercel env add FYERS_REDIRECT_URL
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY

# Deploy to production
vercel --prod
```

### Update Vercel Deployment

After adding environment variables, update `FYERS_REDIRECT_URL` to:
```
https://your-vercel-domain.vercel.app/callback
```

## Deploy to Railway

### Option 1: Via Railway Dashboard

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `fdscoop/stocxer`
5. Railway will automatically:
   - Detect Python
   - Install dependencies from `requirements.txt`
   - Use the `Procfile` for start command
6. Add Environment Variables:
   - Go to your project → Variables
   - Add all required environment variables
7. Generate Domain:
   - Go to Settings → Generate Domain
8. Update `FYERS_REDIRECT_URL` with your Railway domain

### Option 2: Via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to project
railway link

# Add environment variables
railway variables set FYERS_APP_ID=your_value
railway variables set FYERS_SECRET_KEY=your_value
railway variables set SUPABASE_URL=your_value
railway variables set SUPABASE_KEY=your_value
railway variables set FYERS_REDIRECT_URL=https://your-app.railway.app/callback

# Deploy
railway up
```

## Post-Deployment Steps

### 1. Update Fyers Redirect URL

In your Fyers API dashboard:
- Add your deployment URL to allowed redirect URLs
- Examples:
  - `https://your-app.vercel.app/callback`
  - `https://your-app.railway.app/callback`

### 2. Update Supabase RLS Policy

Run this SQL in Supabase SQL Editor to allow user registration:

```sql
-- Allow users to insert their own profile
CREATE POLICY "Users can insert own profile" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);
```

### 3. Configure Supabase Auth

In Supabase Dashboard → Authentication → URL Configuration:
- Add your deployment URLs to "Site URL"
- Add to "Redirect URLs"

### 4. Test Deployment

```bash
# Health check
curl https://your-app.vercel.app/health

# API test
curl https://your-app.vercel.app/screener/categories
```

## Continuous Deployment

Both Vercel and Railway support automatic deployments:

- **Push to main branch** → Automatic production deployment
- **Push to other branches** → Preview deployments (Vercel)

## Troubleshooting

### Vercel Issues

1. **Build fails**: Check Python version in `runtime.txt`
2. **Environment variables not working**: Ensure they're added in Vercel dashboard
3. **API routes not working**: Check `vercel.json` configuration

### Railway Issues

1. **Build fails**: Check logs in Railway dashboard
2. **Port binding error**: Railway automatically sets `$PORT` environment variable
3. **Memory issues**: Upgrade to a higher plan if needed

### Common Issues

1. **Fyers callback fails**: 
   - Verify redirect URL matches exactly (including https/http)
   - Check Fyers dashboard for allowed URLs

2. **Supabase connection fails**:
   - Verify SUPABASE_URL and SUPABASE_KEY
   - Check if RLS policies are set correctly

3. **Static files not loading**:
   - Ensure `static/` directory is in repository
   - Check CORS settings

## Monitoring

- **Vercel**: View logs at `https://vercel.com/your-account/project-name`
- **Railway**: View logs in Railway dashboard

## Updating Deployment

```bash
# Make changes
git add .
git commit -m "Update description"
git push origin main
```

Both platforms will automatically deploy your changes.

## Cost Considerations

- **Vercel**: Free tier includes 100GB bandwidth/month
- **Railway**: Free $5 credit/month, then pay-as-you-go
- **GitHub**: Free for public repositories

## Security Notes

1. Never commit `.env` file (already in `.gitignore`)
2. Use environment variables for all secrets
3. Rotate API keys periodically
4. Enable Supabase RLS policies
5. Use HTTPS only in production
