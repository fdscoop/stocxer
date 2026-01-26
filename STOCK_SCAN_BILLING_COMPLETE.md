# Stock Scanner Token Validation & Billing - Implementation Complete

## Overview
Implemented comprehensive token validation and billing for the stock screener, matching the functionality already working in options scanning.

## Features Implemented

### 1. **Pre-Scan Cost Calculation**
- New endpoint: `/api/screener/calculate-cost`
- Calculates total cost before scanning
- Shows cost breakdown to user:
  - Number of stocks to scan
  - Cost per stock (₹0.85)
  - Total cost
  - Current wallet balance
  - Subscription status and limits

### 2. **Smart Payment Logic**
Priority-based payment system:

```
1. Check if user has active subscription
   ├─ Yes → Check daily scan limit
   │   ├─ Limit not exhausted → Use subscription (FREE)
   │   └─ Limit exhausted → Use PAYG wallet
   └─ No → Use PAYG wallet
```

### 3. **User Confirmation Flow**
Before scan execution, user sees:

**With Active Subscription:**
```
You are about to scan 20 stocks.

✅ This scan will use your Premium subscription.
📊 Scans remaining today: 45 of 50

Click OK to proceed.
```

**With PAYG (No Subscription):**
```
You are about to scan 20 stocks.

💰 Total cost: ₹17.00 (₹0.85 per stock)
💳 Your wallet balance: ₹50.00

✅ Amount will be deducted from your wallet.

Click OK to proceed with the scan.
```

**Insufficient Balance:**
```
You are about to scan 20 stocks.

💰 Total cost: ₹17.00 (₹0.85 per stock)
💳 Your wallet balance: ₹5.00

❌ Insufficient balance. Please add credits to your wallet or subscribe to a plan.
```

### 4. **Token Deduction**
- Uses `@require_tokens(ScanType.STOCK_SCAN)` decorator
- Dynamically calculates scan count based on:
  - Custom mode: Number of selected stocks
  - Random mode: Limit parameter
- Cost calculation: `₹0.85 × number_of_stocks`
- Deducts from wallet only if subscription unavailable/exhausted

### 5. **Automatic Refund on Failure**
- Uses `@with_refund_on_failure(ScanType.STOCK_SCAN)` decorator
- If scan fails, automatically refunds tokens to wallet
- User doesn't lose credits for failed scans

### 6. **Error Handling**
Enhanced error messages:
- **402 Payment Required**: Clear message about insufficient credits
- **401 Unauthorized**: Session expired or Fyers auth needed
- **500 Server Error**: Technical error with refund guarantee

## Technical Implementation

### Backend Changes

1. **Token Middleware Enhancement** (`src/middleware/token_middleware.py`):
```python
# Dynamic scan count calculation for stock scans
if scan_type == ScanType.STOCK_SCAN:
    # Count selected stocks or use limit
    actual_scan_count = calculate_from_request()
    
# Smart payment logic
if user.has_subscription and subscription_limit_available:
    use_subscription()
else:
    deduct_from_wallet()
```

2. **New Endpoint** (`main.py`):
```python
@app.post("/api/screener/calculate-cost")
async def calculate_scan_cost(...):
    """Pre-calculate scan cost for user confirmation"""
    return {
        "total_cost": 17.00,
        "per_stock_cost": 0.85,
        "stock_count": 20,
        "will_use_subscription": False,
        "wallet_balance": 50.00,
        "sufficient_balance": True
    }
```

3. **Protected Endpoints**:
```python
@app.get("/screener/scan")
@require_tokens(ScanType.STOCK_SCAN)
@with_refund_on_failure(ScanType.STOCK_SCAN)
async def scan_stocks(..., token_validation: dict = None):
    # Scan logic
```

### Frontend Changes

1. **Cost Calculation Before Scan** (`frontend/app/screener/page.tsx`):
```typescript
const runScan = async () => {
    // First calculate cost and get confirmation
    await calculateAndConfirmCost()
}

const calculateAndConfirmCost = async () => {
    const costData = await fetch('/api/screener/calculate-cost', ...)
    
    // Show confirmation dialog with cost breakdown
    if (!confirm(message)) return
    
    // Proceed with scan
    await performScan()
}
```

2. **Enhanced Error Handling**:
```typescript
if (response.status === 402) {
    alert('❌ Payment Required\n\n' + errorMessage)
}
```

## Token Costs

| Scan Type | Cost per Unit | Notes |
|-----------|---------------|-------|
| Stock Scan | ₹0.85 | Per stock analyzed |
| Option Scan | ₹0.98 | Per options chain scan |
| Bulk Scan | ₹5.00 | Up to 50 stocks |

## Testing Scenarios

### Scenario 1: User with Active Subscription
- User: Premium subscriber (50 scans/day)
- Scans used today: 10
- Action: Scan 20 stocks
- **Result**: Uses subscription (FREE), no wallet deduction

### Scenario 2: Subscription Limit Exhausted
- User: Basic subscriber (10 scans/day)
- Scans used today: 10
- Action: Scan 5 stocks
- **Result**: Uses wallet (₹4.25 deducted)

### Scenario 3: PAYG User
- User: No subscription
- Wallet: ₹50.00
- Action: Scan 15 stocks
- **Result**: ₹12.75 deducted from wallet

### Scenario 4: Insufficient Balance
- User: No subscription
- Wallet: ₹5.00
- Action: Scan 20 stocks (₹17.00 required)
- **Result**: Scan blocked, prompted to add credits

### Scenario 5: Scan Failure
- User: PAYG, ₹50.00 wallet
- Action: Scan 10 stocks (₹8.50 deducted)
- **Result**: Scan fails → ₹8.50 refunded automatically

## Database Schema

### Usage Tracking
```sql
-- usage_logs table stores each scan
{
    "user_id": "uuid",
    "scan_type": "stock_scan",
    "amount": 17.00,
    "description": "stock_scan: 20 scan(s)",
    "payment_method": "wallet" | "subscription",
    "scan_count": 20,
    "metadata": {
        "calculated_scan_count": 20,
        "stocks": ["NSE:RELIANCE-EQ", ...]
    },
    "refunded": false,
    "created_at": "timestamp"
}
```

## Benefits

1. **Transparent Pricing**: Users see exact cost before scanning
2. **No Surprise Charges**: Confirmation required before deduction
3. **Fair Refunds**: Automatic refunds if scan fails
4. **Subscription Value**: Clear benefit of having a subscription
5. **Flexible Payment**: Works for both subscribers and PAYG users
6. **Accurate Billing**: Dynamic cost based on actual stocks scanned

## Next Steps

1. **Monitor Usage**: Track scan patterns and costs
2. **Optimize Limits**: Adjust daily limits based on usage
3. **Add Analytics**: Show users their scan history and costs
4. **Bulk Discounts**: Consider tiered pricing for large scans

## Deployment

✅ Code pushed to `main` branch
✅ Render will auto-deploy backend changes
✅ Vercel will auto-deploy frontend changes

Wait 2-3 minutes for deployment to complete, then test on production!
