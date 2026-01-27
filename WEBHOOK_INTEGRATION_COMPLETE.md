# 🔗 Webhook Integration Guide : Complete Implementation

## ✅ What's Implemented

I've implemented a comprehensive webhook integration that automatically updates all your database tables when payments are captured. Here's what's been built:

### 🎯 Webhook Endpoint: `/api/billing/webhooks/razorpay`

**Supported Events:**
- `payment.captured` - Automatically adds credits or activates subscriptions
- `payment.failed` - Logs failures for support/retry
- `subscription.charged` - Extends subscription period for renewals  
- `subscription.cancelled` - Updates subscription status

### 🗄️ Database Tables Updated

Based on your SQL schema, the webhook automatically updates:

1. **`user_credits`** - Updates credit balance
2. **`credit_transactions`** - Records all credit movements
3. **`user_subscriptions`** - Manages subscription lifecycle
4. **`payment_history`** - Tracks all payment records (if you add this table)

### 🔄 Complete Payment Flow

#### Credit Purchase Flow:
1. User initiates purchase → `POST /api/billing/credits/create-order`
2. Razorpay processes payment → Webhook fires `payment.captured`
3. Webhook automatically:
   - Adds credits to `user_credits.balance`
   - Creates record in `credit_transactions` 
   - Updates `user_credits.lifetime_purchased`

#### Subscription Flow:
1. User upgrades → `POST /api/billing/subscription/create-order`
2. Razorpay processes payment → Webhook fires `payment.captured`
3. Webhook automatically:
   - Creates/updates record in `user_subscriptions`
   - Sets subscription active with proper dates
   - Links Razorpay payment ID

## 🚀 Setup Instructions

### 1. Razorpay Dashboard Configuration

Go to [Razorpay Dashboard → Settings → Webhooks](https://dashboard.razorpay.com/app/webhooks)

**Add Webhook URL:**
```
https://stocxer-ai.onrender.com/api/billing/webhooks/razorpay
```

**Enable These Events:**
- ✅ `payment.captured`
- ✅ `payment.failed`  
- ✅ `subscription.charged`
- ✅ `subscription.cancelled`

**Get Webhook Secret:**
- Copy the webhook secret from dashboard
- Add to Render environment variables as `RAZORPAY_WEBHOOK_SECRET`

### 2. Environment Variables

In your Render dashboard, ensure these are set:
```env
RAZORPAY_KEY_ID=rzp_test_S2J0LeOfybI0jg
RAZORPAY_KEY_SECRET=1V0OWq0JzMThyiQYboFjum3X
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret_here
```

### 3. Deploy and Test

1. **Deploy** your app with the new webhook code
2. **Test** with Razorpay test cards:
   - Success: `4111 1111 1111 1111`
   - Failure: `4000 0000 0000 0002`

## 🔍 How It Works

### Payment Captured Event
```python
# When payment.captured webhook fires:
async def handle_payment_captured(webhook_data):
    # 1. Extract payment details
    payment_id = webhook_data['payload']['payment']['entity']['id']
    order_id = webhook_data['payload']['payment']['entity']['order_id']
    amount = webhook_data['payload']['payment']['entity']['amount']
    
    # 2. Fetch order to get user_id from notes
    order_data = razorpay_service.fetch_order(order_id)
    user_id = order_data['notes']['user_id']
    order_type = order_data['notes']['order_type']  # 'credit' or 'subscription'
    
    # 3. Update appropriate tables
    if order_type == 'credit':
        # Add credits to user_credits table
        # Create credit_transactions record
    elif order_type == 'subscription':
        # Create/update user_subscriptions table
        # Set subscription active
```

### Database Updates

**For Credit Purchases:**
```sql
-- Updates user_credits table
UPDATE user_credits 
SET balance = balance + credits_amount,
    lifetime_purchased = lifetime_purchased + credits_amount
WHERE user_id = ?;

-- Inserts into credit_transactions
INSERT INTO credit_transactions (
    user_id, transaction_type, amount, 
    razorpay_payment_id, description
) VALUES (?, 'purchase', ?, ?, ?);
```

**For Subscriptions:**
```sql
-- Upserts user_subscriptions table
INSERT INTO user_subscriptions (
    user_id, plan_type, status, 
    razorpay_subscription_id, current_period_start, current_period_end
) VALUES (?, ?, 'active', ?, NOW(), NOW() + INTERVAL 1 MONTH)
ON CONFLICT (user_id) DO UPDATE SET
    plan_type = EXCLUDED.plan_type,
    status = EXCLUDED.status;
```

## 📊 Monitoring & Logs

The webhook provides detailed logging:
```
📨 Webhook received: payment.captured
💰 Processing payment: pay_abc123 for ₹100
✅ Added 120 credits to user 12345678...
```

**Check logs in Render:**
- Go to your service → Logs tab
- Look for webhook events and processing results

## 🛡️ Security Features

1. **Signature Verification** - Validates webhook authenticity
2. **Duplicate Prevention** - Uses payment_id to prevent double processing
3. **Error Handling** - Graceful failure with detailed error logs
4. **Idempotency** - Safe to replay webhooks

## 🧪 Testing

### Test Credit Purchase:
```bash
# Test with curl (after payment completion)
curl -X POST https://stocxer-ai.onrender.com/api/billing/webhooks/razorpay \
  -H "Content-Type: application/json" \
  -H "X-Razorpay-Signature: test_signature" \
  -d '{
    "event": "payment.captured",
    "payload": {
      "payment": {
        "entity": {
          "id": "pay_test123",
          "order_id": "order_test123", 
          "amount": 10000,
          "status": "captured"
        }
      }
    }
  }'
```

### Verify Database Updates:
```sql
-- Check credits were added
SELECT * FROM user_credits WHERE user_id = 'your_user_id';

-- Check transaction was recorded  
SELECT * FROM credit_transactions WHERE razorpay_payment_id = 'pay_test123';
```

## 🎉 Benefits

✅ **Automatic Processing** - No manual intervention needed  
✅ **Real-time Updates** - Credits/subscriptions activate immediately  
✅ **Audit Trail** - Complete transaction history  
✅ **Failure Handling** - Failed payments logged for follow-up  
✅ **Scalable** - Handles high volume automatically  
✅ **Reliable** - Webhook retries ensure delivery

## 🚨 Troubleshooting

**Webhook not firing?**
- Check Razorpay webhook URL is correct
- Verify webhook secret in environment variables
- Check Render logs for incoming requests

**Payments not processing?**
- Verify signature verification passes
- Check user_id exists in order notes
- Ensure Supabase connection is working

**Database not updating?**
- Check Supabase service key permissions
- Verify table schemas match expectations
- Look for SQL errors in logs

## 📈 Next Steps

1. **Monitor** webhook success rates in Razorpay dashboard
2. **Set up alerts** for failed webhooks
3. **Add analytics** to track conversion rates
4. **Implement refund handling** for customer support

Your webhook integration is now production-ready! 🎉