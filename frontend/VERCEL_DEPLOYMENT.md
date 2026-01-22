# Vercel Deployment Configuration

## Environment Variables

Add these environment variables in your Vercel project settings:

### Required Variables

1. **NEXT_PUBLIC_API_URL**
   - Value: `https://stocxer-ai.onrender.com`
   - Description: Backend API URL hosted on Render

2. **NEXT_PUBLIC_SUPABASE_URL**
   - Value: `https://cxbcpmouqkajlxzmbomu.supabase.co`
   - Description: Supabase project URL

3. **NEXT_PUBLIC_SUPABASE_ANON_KEY**
   - Value: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN4YmNwbW91cWthamx4em1ib211Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NjA3NjMsImV4cCI6MjA4NDMzNjc2M30.oBozxBnSKARn-3xkRy8ceNU3wpxXh8MBReGtmtsBpEw`
   - Description: Supabase anonymous/public API key

## Steps to Deploy

1. **Connect to Vercel**
   ```bash
   vercel
   ```

2. **Add Environment Variables**
   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Add all the variables listed above
   - Apply to: Production, Preview, and Development

3. **Deploy**
   ```bash
   vercel --prod
   ```

## Custom Domain

If using custom domain `stocxer.in`:
- Add domain in Vercel dashboard
- Update DNS records as instructed
- SSL will be automatically configured

## Backend URL

The frontend will automatically detect the environment:
- **Localhost**: Uses `http://localhost:8000`
- **Vercel/Production**: Uses `https://stocxer-ai.onrender.com`
- **Custom Domain**: Uses the configured `NEXT_PUBLIC_API_URL`

## Testing

After deployment, test:
1. Login functionality
2. Fyers authentication
3. API calls to backend
4. Data loading

## Troubleshooting

### 401 Unauthorized errors
- Ensure `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- Check that backend is running on Render
- Verify CORS is configured on backend for Vercel domain

### API connection issues
- Check backend logs on Render
- Verify environment variables are applied
- Try clearing browser cache and localStorage
