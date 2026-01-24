# Razorpay Webhook Setup with Supabase Edge Functions

## Why Use Supabase Edge Functions?

✅ **Better than main app webhooks:**
- Independent of your main server uptime
- Globally distributed (low latency)
- Auto-scales automatically
- Built-in CORS handling
- Simpler deployment

## Setup Steps

### 1. Add Razorpay Keys to Your `.env` File

```bash
# Copy from .env.example and add your actual keys
RAZORPAY_KEY_ID=rzp_test_YOUR_ACTUAL_KEY_ID
RAZORPAY_KEY_SECRET=your_actual_secret_key
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
```

**Get your keys:**
1. Sign up at https://razorpay.com/
2. Go to https://dashboard.razorpay.com/app/keys
3. Use **test mode** keys for development (they start with `rzp_test_`)

### 2. Install Supabase CLI

```bash
# macOS
brew install supabase/tap/supabase

# Or using npm
npm install -g supabase
```

### 3. Login to Supabase

```bash
supabase login
```

### 4. Link Your Project

```bash
# Get your project ref from Supabase dashboard URL
# https://app.supabase.com/project/YOUR-PROJECT-REF

cd /Users/bineshbalan/TradeWise
supabase link --project-ref YOUR-PROJECT-REF
```

### 5. Set Edge Function Secrets

```bash
# Set the webhook secret
supabase secrets set RAZORPAY_WEBHOOK_SECRET=your_webhook_secret_here

# Verify it was set
supabase secrets list
```

### 6. Deploy the Edge Function

```bash
cd /Users/bineshbalan/TradeWise
supabase functions deploy razorpay-webhook
```

After deployment, you'll get a URL like:
```
https://YOUR-PROJECT-REF.supabase.co/functions/v1/razorpay-webhook
```

### 7. Configure Razorpay Webhook

1. Go to Razorpay Dashboard → **Settings** → **Webhooks**
2. Click **"+ Create New Webhook"**
3. Enter the URL:
   ```
   https://YOUR-PROJECT-REF.supabase.co/functions/v1/razorpay-webhook
   ```
4. Select these events:
   - ✅ `payment.captured`
   - ✅ `payment.failed`
   - ✅ `subscription.charged`
   - ✅ `subscription.cancelled`
5. Enter the webhook secret (same as in your Edge Function)
6. Save

### 8. Test the Webhook

```bash
# Test locally
supabase functions serve razorpay-webhook

# Send test event from Razorpay dashboard
# Check the logs in your terminal
```

## How It Works

```
User Buys Credits
     ↓
Razorpay Processes Payment
     ↓
Razorpay Sends Webhook → Supabase Edge Function
     ↓
Edge Function:
  - Verifies signature
  - Adds credits to user_credits table
  - Logs transaction
  - Records payment history
     ↓
User sees updated balance instantly
```

## Webhook Event Flow

### Payment Captured (Credit Purchase)

1. **Verify** signature
2. **Extract** user_id and pack_id from payment notes
3. **Calculate** credits (base + bonus)
4. **Update** user_credits table
5. **Insert** credit_transaction record
6. **Insert** payment_history record

### Payment Failed

1. **Log** failed payment in payment_history
2. **Optional:** Send notification to user

### Subscription Events

- `subscription.charged` → Renew subscription period
- `subscription.cancelled` → Update subscription status

## Testing

### Test with Razorpay Test Cards

**Success:**
- Card: `4111 1111 1111 1111`
- CVV: Any 3 digits
- Expiry: Any future date

**Failure:**
- Card: `4012 0010 3714 1112`

### Check Logs

```bash
# View Edge Function logs
supabase functions logs razorpay-webhook --tail

# Or in Supabase Dashboard
# Project → Edge Functions → razorpay-webhook → Logs
```

### Verify Database

```sql
-- Check if credits were added
SELECT * FROM user_credits WHERE user_id = 'your-user-id';

-- Check transaction log
SELECT * FROM credit_transactions 
WHERE user_id = 'your-user-id' 
ORDER BY created_at DESC 
LIMIT 5;

-- Check payment history
SELECT * FROM payment_history 
WHERE user_id = 'your-user-id' 
ORDER BY created_at DESC 
LIMIT 5;
```

## Security Notes

✅ **Webhook signature verification** - Always validates requests are from Razorpay  
✅ **Service role key** - Used securely in Edge Function environment  
✅ **Environment variables** - Secrets never exposed in code  
✅ **Transaction atomicity** - All DB operations in try-catch blocks  

## Common Issues

### Webhook Not Receiving Events

1. **Check URL** - Make sure it's the correct Edge Function URL
2. **Check secrets** - Run `supabase secrets list`
3. **Check logs** - Look for errors in Edge Function logs
4. **Test signature** - Webhook secret must match exactly

### Credits Not Added

1. **Check user_id** in payment notes
2. **Check pack_id** exists in credit_packs table
3. **View Edge Function logs** for errors
4. **Check RLS policies** on tables

### Deployment Failed

```bash
# Re-deploy with verbose logging
supabase functions deploy razorpay-webhook --debug

# Check project is linked
supabase projects list
```

## Advantages Over Main App Webhook

| Feature | Main App | Edge Function |
|---------|----------|---------------|
| Uptime | Depends on server | 99.9% SLA |
| Scaling | Manual | Auto |
| Latency | Variable | <100ms globally |
| CORS | Manual setup | Built-in |
| Deploy | Full redeploy | Independent |
| Cost | Server cost | Pay per execution |

## Alternative: Keep Main App Webhook

If you prefer to keep the webhook in your main app instead:

1. **Remove** Edge Function
2. **Use** `/api/billing/webhooks/razorpay` endpoint
3. **Configure** Razorpay webhook to your domain:
   ```
   https://your-domain.com/api/billing/webhooks/razorpay
   ```

Both approaches work! Edge Functions are recommended for production.

---

**Need Help?**

- Supabase Docs: https://supabase.com/docs/guides/functions
- Razorpay Webhooks: https://razorpay.com/docs/webhooks/
- Edge Function Logs: Supabase Dashboard → Functions → Logs
