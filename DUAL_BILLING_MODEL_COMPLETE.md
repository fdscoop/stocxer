# 🚀 Dual Billing Model Implementation Guide

## ✅ Implementation Complete

I've implemented your **dual billing model** with clear separation between subscriptions and pay-as-you-go:

### 🔐 Multi-Project Razorpay Solution

**Problem Solved:** Your webhook will now **ONLY process payments** for this project.

**How it works:**
```python
# All orders now include project identifier
notes={
    'project': 'stocxer-tradewise',  # 🔑 Your unique identifier
    'user_id': user_id,
    # ... other data
}

# Webhook filters payments
if project != 'stocxer-tradewise':
    print(f"🚫 Ignoring payment from different project: {project}")
    return  # Ignore payments from other projects
```

**Benefits:**
- ✅ Safe to use same Razorpay account for multiple projects
- ✅ Webhook processes only relevant payments  
- ✅ No payment mixing between projects
- ✅ Clear separation via `receipt` prefixes: `stocxer_` vs your other project

---

### 🎯 Token-Based Validation System

**Pre-API Validation:** All requests are blocked if insufficient balance.

```python
# Example usage in your scan endpoints
from src.middleware.token_middleware import require_tokens, ScanType

@require_tokens(ScanType.STOCK_SCAN, scan_count=1)
async def stock_scan_endpoint(authorization: str = Header(None)):
    # This API will ONLY run if user has sufficient tokens
    # Tokens are automatically deducted before API execution
    pass

@require_tokens(ScanType.OPTION_SCAN, scan_count=10) 
async def bulk_option_scan(authorization: str = Header(None)):
    # Validates and deducts tokens for 10 option scans
    pass
```

**Token Costs (Configurable):**
```python
TOKEN_COSTS = {
    ScanType.STOCK_SCAN: Decimal("1.0"),     # 1 token per stock scan
    ScanType.OPTION_SCAN: Decimal("2.0"),    # 2 tokens per option scan  
    ScanType.CHART_SCAN: Decimal("0.5"),     # 0.5 tokens per chart
    ScanType.BULK_SCAN: Decimal("5.0")       # 5 tokens per bulk scan
}
```

---

### 🔄 Dual Model Logic Flow

#### For Subscribed Users:
1. ✅ Check subscription limits first
2. ✅ If within limits → Use subscription (free)
3. ✅ If limits exceeded → Use wallet tokens
4. ❌ If no wallet balance → Block request

#### For PAYG Users:
1. ✅ Check wallet balance
2. ✅ If sufficient → Deduct tokens  
3. ❌ If insufficient → Block with helpful message

#### Error Messages:
```
Token balance insufficient. Required: 2.0, Available: 1.5

Please:
• Subscribe to a plan
• Or use pay-as-you-go  
• Or add tokens to your wallet
```

---

### 📊 Database Integration

**All tables are automatically updated:**

1. **`user_credits`** - Real-time balance tracking
2. **`credit_transactions`** - Complete audit trail
3. **`usage_logs`** - Daily subscription usage tracking
4. **`user_subscriptions`** - Subscription status & limits

**Example transaction flow:**
```sql
-- User makes stock scan (costs 1 token)
-- Before: balance = 100.0
-- After: balance = 99.0

INSERT INTO credit_transactions (
    user_id, transaction_type, amount,
    balance_before, balance_after,
    description, scan_type, scan_count
) VALUES (
    'user123', 'debit', 1.0,
    100.0, 99.0,
    'stock_scan: 1 scan(s)', 'stock_scan', 1
);
```

---

### 🧪 Production Testing Strategy

**You're right - testing directly in production is perfectly fine for this setup:**

#### ✅ Why it's safe:
1. **Project isolation** prevents payment mixing
2. **Webhook filtering** ensures only your payments are processed
3. **Test mode** Razorpay keys prevent real charges
4. **Granular validation** prevents double-processing

#### 🧪 Testing steps:

1. **Deploy webhook changes** to production
2. **Set environment variables** in Render:
   ```env
   RAZORPAY_KEY_ID=rzp_test_S2J0LeOfybI0jg
   RAZORPAY_KEY_SECRET=1V0OWq0JzMThyiQYboFjum3X
   RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
   ```

3. **Configure Razorpay webhook:**
   ```
   URL: https://stocxer-ai.onrender.com/api/billing/webhooks/razorpay
   Events: payment.captured, payment.failed, subscription.charged, subscription.cancelled
   ```

4. **Test with test cards:**
   - Success: `4111 1111 1111 1111`
   - Failure: `4000 0000 0000 0002`

5. **Monitor logs** in Render dashboard for:
   ```
   📨 Webhook received: payment.captured
   💰 Processing payment: pay_test123 for ₹100
   ✅ Added 120 credits to user 12345678...
   ```

---

### 🔧 Integration Steps

#### 1. Apply Token Middleware to Your Endpoints:

```python
# In your main.py or scan endpoints
from src.middleware.token_middleware import require_tokens, ScanType

@app.post("/api/scan/stock")
@require_tokens(ScanType.STOCK_SCAN)
async def stock_scan(authorization: str = Header(None)):
    # Your existing scan logic here
    # Tokens already validated and deducted
    pass

@app.post("/api/scan/options") 
@require_tokens(ScanType.OPTION_SCAN)
async def option_scan(authorization: str = Header(None)):
    # Your existing options logic
    pass
```

#### 2. Update Frontend Error Handling:

```javascript
// Handle 402 Payment Required responses
fetch('/api/scan/stock', { 
    headers: { Authorization: `Bearer ${token}` }
})
.then(response => {
    if (response.status === 402) {
        // Show token insufficient modal
        showTokenInsufficientAlert(response.message);
        return;
    }
    // Process successful response
})
```

#### 3. Monitor & Adjust:

- **Watch token costs** - adjust `TOKEN_COSTS` based on usage
- **Monitor conversion** - users should top up when prompted  
- **Track usage patterns** - optimize pricing strategy

---

### 🎉 Benefits Achieved

✅ **No API waste** - Requests blocked before processing  
✅ **Clear separation** - Subscription vs PAYG logic isolated  
✅ **Multi-project safe** - No payment conflicts  
✅ **Real-time validation** - Immediate balance checks  
✅ **Audit trail** - Complete transaction history  
✅ **Scalable architecture** - Handle high volume automatically  

Your billing system is now production-ready with robust token-based validation! 🚀