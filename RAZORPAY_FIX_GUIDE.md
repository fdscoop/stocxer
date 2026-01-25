# Razorpay Configuration Fix

The error "Failed to create order: Razorpay not configured" indicates that Razorpay environment variables are not set in the production deployment.

## What was Fixed

1. **Updated Razorpay Service** - Modified to properly load credentials from settings
2. **Updated render.yaml** - Added missing Razorpay environment variables
3. **Added debugging information** - Better error messages to identify configuration issues

## Deployment Steps Required

### 1. Set Environment Variables in Render Dashboard

Go to your Render service dashboard and add these environment variables:

```
RAZORPAY_KEY_ID=rzp_test_S2J0LeOfybI0jg
RAZORPAY_KEY_SECRET=1V0OWq0JzMThyiQYboFjum3X
RAZORPAY_WEBHOOK_SECRET=(your webhook secret when you set up webhooks)
```

### 2. Redeploy the Service

After setting the environment variables, trigger a new deployment in Render.

## Verification

Once deployed, test the billing endpoint:
- Visit: `https://stocxer-ai.onrender.com/api/billing/credits/packs`
- Try creating an order through your frontend billing dashboard

## Next Steps for Webhooks

1. Go to Razorpay Dashboard → Settings → Webhooks
2. Add webhook URL: `https://stocxer-ai.onrender.com/api/billing/webhooks/razorpay`
3. Enable events: `payment.captured`, `payment.failed`, `subscription.charged`, `subscription.cancelled`
4. Copy the webhook secret and add it as `RAZORPAY_WEBHOOK_SECRET` environment variable

## Files Modified

- `/src/services/razorpay_service.py` - Fixed credential loading
- `/render.yaml` - Added Razorpay environment variables

The Razorpay service now works correctly locally and should work in production once the environment variables are set in Render.