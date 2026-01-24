# Hybrid Subscription + PAYG Billing System

## Overview

TradeWise now includes a comprehensive billing system that combines:
- **Pay-As-You-Go (PAYG)** - Buy credits and pay only for what you use
- **Monthly Subscriptions** - Fixed monthly fee with generous limits
- **Free Tier** - Limited daily access at no cost

## Pricing Structure

### Pay-As-You-Go (PAYG)
- **Option Scan**: ₹0.98 per scan
- **Stock Scan**: ₹0.85 per stock
- **Bulk Scan**: ₹5.00 base + ₹0.50 per stock
- **Credits never expire** - Use them whenever you want

### Credit Packs
| Pack | Price | Credits | Bonus | Total |
|------|-------|---------|-------|-------|
| Starter | ₹50 | 50 | 0 | 50 |
| Basic | ₹100 | 100 | 5 | 105 |
| Value | ₹250 | 250 | 15 | 265 |
| Power | ₹500 | 500 | 40 | 540 |
| Premium | ₹1000 | 1000 | 100 | 1100 |

### Monthly Subscriptions

#### Free Plan (₹0)
- 3 option scans/day
- 10 stock scans/day
- No bulk scanning
- Basic dashboard access
- Community support

#### Medium Plan (₹499/month)
- 50 option scans/day
- 200 stock scans/day
- 25 stocks per bulk scan
- 10 bulk scans/day
- Email support
- All analysis features

#### Pro Plan (₹999/month)
- **Unlimited** option scans
- **Unlimited** stock scans
- 100 stocks per bulk scan
- **Unlimited** bulk scans
- Priority support
- Accuracy tracking dashboard
- Historical data access
- Early access to new features

## Architecture

### Database Schema

The billing system adds 7 new tables:

1. **user_subscriptions** - User subscription plans
2. **user_credits** - PAYG credit balance
3. **credit_transactions** - Complete audit trail of credits
4. **usage_logs** - Daily usage tracking for subscriptions
5. **plan_limits** - Configuration of plan limits
6. **credit_packs** - Available credit packs
7. **payment_history** - Payment records

### Backend Components

```
src/
├── models/
│   └── billing_models.py          # Pydantic models for billing
├── services/
│   ├── billing_service.py         # Core billing logic
│   ├── razorpay_service.py        # Payment gateway integration
│   └── billing_middleware.py      # Billing check decorators
└── api/
    └── billing_routes.py           # Billing API endpoints
```

### API Endpoints

#### Billing Status
- `GET /api/billing/status` - Get user's billing status
- `GET /api/billing/dashboard` - Complete dashboard data

#### Credits (PAYG)
- `GET /api/billing/credits/packs` - Available credit packs
- `POST /api/billing/credits/create-order` - Create Razorpay order
- `POST /api/billing/credits/verify-payment` - Verify and add credits
- `GET /api/billing/credits/transactions` - Transaction history

#### Subscriptions
- `GET /api/billing/plans` - All available plans
- `POST /api/billing/subscription/create` - Create subscription
- `POST /api/billing/subscription/cancel` - Cancel subscription

#### Webhooks
- `POST /api/billing/webhooks/razorpay` - Razorpay webhook handler

## Setup Instructions

### 1. Database Migration

Run the billing schema migration in Supabase SQL Editor:

```bash
# Navigate to database migrations
cd database/migrations

# Copy the SQL and run in Supabase SQL Editor
cat subscription_schema.sql
```

Or use the Supabase CLI:
```bash
supabase db push
```

### 2. Install Dependencies

```bash
pip install razorpay>=1.4.1
```

### 3. Configure Razorpay

1. Sign up at [Razorpay](https://razorpay.com/)
2. Get your API keys from the [Dashboard](https://dashboard.razorpay.com/app/keys)
3. Add to `.env`:

```env
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_secret_key
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
```

**Important**: Use test keys (`rzp_test_*`) for development!

### 4. Configure Webhooks

1. Go to Razorpay Dashboard → Settings → Webhooks
2. Add webhook URL: `https://your-domain.com/api/billing/webhooks/razorpay`
3. Enable events:
   - `payment.captured`
   - `payment.failed`
   - `subscription.charged`
   - `subscription.cancelled`
4. Copy the webhook secret to `.env`

### 5. Frontend Integration

The billing dashboard is available at:
```
/billing  # or wherever you mount the BillingDashboard component
```

## Usage Flow

### For Subscription Users

1. User subscribes to Medium or Pro plan
2. Billing service checks daily limits
3. Usage is logged but no charges
4. If limit exceeded, user can:
   - Wait for next day
   - Upgrade plan
   - Use credits for extra scans

### For PAYG Users

1. User buys credit pack
2. Credits added to balance
3. Each scan deducts credits
4. If balance insufficient:
   - Show error message
   - Prompt to buy more credits
   - Or suggest subscription

### Free Tier

1. User on free plan (default)
2. 3 option scans + 10 stock scans/day
3. After limit:
   - Prompt to buy credits
   - Or subscribe to paid plan

## Adding Billing Checks to Endpoints

Use the middleware to protect endpoints:

```python
from src.services.billing_middleware import check_billing_for_scan, deduct_billing_for_scan

@app.get("/api/analyze/options")
async def analyze_options(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    
    # Check if user can perform scan
    await check_billing_for_scan(user_id, 'option_scan', count=1)
    
    # Perform the scan
    result = perform_scan()
    
    # Deduct credits or log usage
    await deduct_billing_for_scan(user_id, 'option_scan', count=1)
    
    return result
```

Or use the decorator:

```python
from src.services.billing_middleware import require_billing_check

@app.get("/api/scan")
@require_billing_check('option_scan')
async def scan_options(authorization: str = Header(None)):
    # Billing automatically checked and deducted
    return perform_scan()
```

## Frontend Components

### BillingDashboard
Shows complete billing information:
- Current plan and credits
- Today's usage
- Available credit packs
- Transaction history

### Updated PricingSection
Shows all pricing options:
- PAYG with per-scan pricing
- Free tier with limits
- Medium and Pro subscriptions

## Testing

### Test Credit Purchase Flow

1. Login as test user
2. Navigate to billing dashboard
3. Click "Buy Credits" on any pack
4. Use Razorpay test cards:
   - Success: `4111 1111 1111 1111`
   - Failure: `4012 0010 3714 1112`
5. Verify credits added to balance

### Test Subscription Limits

1. Subscribe to Free plan (default)
2. Perform 3 option scans
3. 4th scan should be blocked
4. Error message shows upgrade options

### Test PAYG Deduction

1. Buy ₹100 credit pack
2. Perform option scan (₹0.98 deduction)
3. Check transaction log
4. Verify new balance

## Monitoring

### Key Metrics to Track

- Daily revenue (credits + subscriptions)
- Conversion rate (free → paid)
- Credit pack popularity
- Plan distribution
- Average credit balance
- Churn rate

### Database Queries

```sql
-- Daily revenue
SELECT 
    DATE(created_at) as date,
    SUM(amount_inr / 100) as revenue
FROM payment_history
WHERE status = 'captured'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Active subscriptions by plan
SELECT 
    plan_type,
    COUNT(*) as users
FROM user_subscriptions
WHERE status = 'active'
GROUP BY plan_type;

-- Top credit purchasers
SELECT 
    user_id,
    SUM(amount) as total_purchased
FROM credit_transactions
WHERE transaction_type = 'purchase'
GROUP BY user_id
ORDER BY total_purchased DESC
LIMIT 10;
```

## Security Considerations

1. **Always verify signatures** - Razorpay payments and webhooks
2. **Use service role key** - For billing operations
3. **Rate limit** - Billing endpoints to prevent abuse
4. **Audit trail** - All transactions are logged
5. **RLS policies** - Users can only access their own data

## Common Issues

### Credits not added after payment

Check:
1. Payment signature verification
2. Webhook delivery status in Razorpay dashboard
3. `credit_transactions` table for the payment ID
4. Supabase logs for errors

### Subscription limits not enforced

Check:
1. `usage_logs` table for today's date
2. `plan_limits` table has correct values
3. Billing service is being called before scan

### Webhook failures

Check:
1. Webhook secret matches `.env`
2. Endpoint is publicly accessible
3. Razorpay dashboard shows delivery status
4. Server logs for webhook errors

## Future Enhancements

- **Annual subscriptions** with discount
- **Referral credits** for user growth
- **Usage analytics** dashboard
- **Auto-recharge** when balance low
- **Family plans** for teams
- **Volume discounts** for enterprises

## Support

For billing issues:
- Email: support@stocxer.in
- Include transaction ID or order ID
- Check transaction history first

For technical issues:
- Check logs: `/logs/billing.log`
- Run database health check
- Verify Razorpay integration

---

**Last Updated**: January 23, 2026  
**Version**: 1.0.0
