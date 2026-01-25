# Free Trial & Billing Model - Complete Implementation Guide

## Overview

Your TradeWise platform now has a **hybrid billing model** with three tiers:

1. **Free Trial (₹0)** - Start with 100 credits
2. **Pay As You Go (₹50+)** - Buy credits as needed
3. **Subscription Plans** - Flat monthly fee with unlimited scans

---

## Tier 1: Free Trial / Pay As You Go (PAYG)

### How It Works

**Every new user automatically gets:**
- **100 free credits** on account creation
- No daily scan limits
- Unlimited scans (limited only by credit balance)
- Pricing: ₹0.85 per stock scan, ₹0.98 per option scan
- No expiry on credits

### User Experience

```
Wallet shows:
┌─────────────────────────────────────────┐
│ Current Plan: Free Trial (PAYG)         │
│ ₹0.85 per stock • ₹0.98 per option      │
├─────────────────────────────────────────┤
│ Credits Balance: ₹100.00                │
│ [Buy Credits]                           │
├─────────────────────────────────────────┤
│ Today's Usage: 0 Scans                  │
│ Unlimited (credits based)               │
└─────────────────────────────────────────┘
```

### When Credits Run Out

Once balance < 0:
1. User gets error: "Insufficient credits. Buy more to continue."
2. User can buy credit packs (Starter ₹50, Basic ₹100, Value ₹250, etc.)
3. Credits added immediately after payment
4. User can continue scanning

### Database Structure

```sql
-- User starts with this
INSERT INTO user_credits (user_id, balance)
VALUES ('user123', 100);  -- 100 free credits

-- Transaction logged
INSERT INTO credit_transactions (
    user_id, transaction_type, amount, 
    balance_before, balance_after, description
) VALUES (
    'user123', 'bonus', 100, 0, 100,
    'Welcome bonus: 100 free credits'
);
```

---

## Tier 2: Medium Subscription (₹4,999/month)

### Features
- 30,000 scans/month (approximately 1,000 scans/day)
- Flat ₹4,999/month pricing
- 25 stocks per bulk scan
- Email support

### Daily Limits (if user exceeds monthly quota)
- Daily option scans: 50
- Daily stock scans: 200
- Bulk scans: 10/day (25 stocks each)

### Plan Limits in Database

```sql
plan_type: 'medium'
daily_option_scans: 50
daily_stock_scans: 200
bulk_scan_limit: 25
daily_bulk_scans: 10
```

---

## Tier 3: Pro Subscription (₹9,999/month)

### Features
- **Unlimited** monthly scans
- Unlimited bulk scans (100+ stocks)
- Accuracy tracking
- Historical data access
- Priority support
- Early access to features

### Plan Limits in Database

```sql
plan_type: 'pro'
daily_option_scans: NULL  -- Unlimited
daily_stock_scans: NULL   -- Unlimited
bulk_scan_limit: 100      -- Unlimited
daily_bulk_scans: NULL    -- Unlimited
```

---

## Billing Logic Flow

### For Free Trial / PAYG Users

```
User wants to scan
  ↓
Check active subscription? → NO
  ↓
Check credit balance
  ├─ Balance ≥ cost → Allow scan, deduct credits
  └─ Balance < cost → Deny, show "Buy credits" error
```

### For Subscription Users

```
User wants to scan
  ↓
Check active subscription? → YES
  ↓
Check plan type (medium/pro)
  ├─ pro → Always allow (NULL limits = unlimited)
  └─ medium → Check daily limits
    ├─ Within limit → Allow, log usage
    └─ Over limit → Deny, show "Upgrade" message
```

---

## Key Implementation Details

### 1. User Initialization

When a new user signs up:
- `user_subscriptions` record created with `plan_type: 'free', status: 'active'`
- `user_credits` record created with `balance: 100`
- Welcome bonus transaction logged

### 2. Pricing Configuration

```python
# src/middleware/token_middleware.py
TOKEN_COSTS = {
    ScanType.STOCK_SCAN: Decimal("0.85"),
    ScanType.OPTION_SCAN: Decimal("0.98"),
    ScanType.CHART_SCAN: Decimal("0.50"),
    ScanType.BULK_SCAN: Decimal("5.00")
}
```

### 3. Wallet Display Logic

```typescript
// Shows plan based on subscription status
if (subscription_active && plan_type in ['medium', 'pro']) {
    display: "Medium" or "Pro"
} else {
    display: "Free Trial (Pay As You Go)"
}

// Shows pricing info for PAYG users
if (!subscription_active) {
    display: "₹0.85 per stock • ₹0.98 per option"
}

// Shows usage limits appropriately
if (subscription_active && daily_limit) {
    display: `Limit: ${limit}/day`
} else if (subscription_active) {
    display: "Unlimited"
} else {
    display: "Unlimited (credits based)"
}
```

### 4. Plan Limits Table

After running the migration `fix_free_trial_model.sql`:

```sql
Free tier:
  daily_option_scans: NULL    (Unlimited - PAYG only)
  daily_stock_scans: NULL     (Unlimited - PAYG only)
  bulk_scan_limit: 0          (No bulk in free)
  daily_bulk_scans: 0

Medium tier:
  daily_option_scans: 50
  daily_stock_scans: 200
  bulk_scan_limit: 25
  daily_bulk_scans: 10

Pro tier:
  daily_option_scans: NULL    (Unlimited)
  daily_stock_scans: NULL     (Unlimited)
  bulk_scan_limit: 100        (Unlimited bulk)
  daily_bulk_scans: NULL      (Unlimited)
```

---

## Recent Changes

### 1. Database Migration
**File:** `database/migrations/fix_free_trial_model.sql`
- Updated `plan_limits` for "free" plan to have NULL daily limits
- Updated Medium/Pro plan limits appropriately

### 2. Frontend Updates
**File:** `frontend/components/billing/BillingDashboard.tsx`
- Changed plan display from "free" → "Free Trial (Pay As You Go)"
- Added pricing info for PAYG users (₹0.85/₹0.98)
- Fixed usage limit display to only show daily limits for subscription users
- Added informational banner explaining free trial model

### 3. Existing Backend Logic
**File:** `src/services/billing_service.py`
- Already initializes users with 100 credits ✓
- Already checks credit balance for PAYG users ✓
- Already differentiates subscription vs PAYG billing ✓
- Token deduction working with new pricing (₹0.85/₹0.98) ✓

---

## What "Limit: 3/day" Meant?

The "3/day" limit you were seeing came from the old `plan_limits` configuration which set:
```sql
free plan: daily_option_scans = 3
```

This is now **removed** because:
1. Your model is **credit-based**, not time-limited
2. "Free Trial" = "100 ₹ of free credits to spend"
3. Once credits are used, users buy more (PAYG)
4. No arbitrary daily limits - only credit-based limits

---

## Distinguishing Free Trial from Subscription

### Free Trial (PAYG)
- ✓ 100 free ₹ on signup
- ✓ ₹0.85/stock, ₹0.98/option
- ✓ No daily limits
- ✓ No card required
- ✓ When credits end, must buy more

### Medium Subscription
- ✓ ₹4,999/month
- ✓ 30,000 scans/month
- ✓ Daily limits apply
- ✓ Billed monthly
- ✓ Can't run out (flat fee)

### Pro Subscription
- ✓ ₹9,999/month
- ✓ Unlimited scans
- ✓ No daily limits
- ✓ Billed monthly
- ✓ Premium features

---

## Testing the Implementation

### Test 1: New User Free Trial
```bash
1. Create new account
2. Check wallet: Should show "Free Trial (PAYG)" with ₹100 balance
3. Do a stock scan (costs ₹0.85)
4. Balance should become ₹99.15
```

### Test 2: Credit Exhaustion
```bash
1. Keep scanning until balance < ₹0.85
2. Try to scan → Should get error
3. Buy credits → Should be added immediately
4. Scan again → Should work
```

### Test 3: Subscription Switch
```bash
1. Subscribe to Medium plan
2. Wallet should show "Medium" (not "Free Trial")
3. Should see daily limits (50 options/day, 200 stocks/day)
4. Daily usage should track in `usage_logs` table (not deduct credits)
```

---

## Pricing Summary

| Plan | Price | Stock Scans | Option Scans | Bulk Scans | Expiry |
|------|-------|-------------|--------------|-----------|--------|
| **Free Trial** | ₹0 | ₹0.85 each | ₹0.98 each | Not allowed | Credits don't expire |
| **PAYG** | ₹50+ | ₹0.85 each | ₹0.98 each | Not allowed | Credits don't expire |
| **Medium** | ₹4,999/mo | 50/day | 50/day | 10/day (25 stocks) | 1 month |
| **Pro** | ₹9,999/mo | Unlimited | Unlimited | Unlimited | 1 month |

---

## Next Steps

1. ✅ Apply database migration: `fix_free_trial_model.sql`
2. ✅ Deploy frontend changes
3. ✅ Test with new user account
4. Test subscription upgrade flow
5. Monitor credit transactions for accuracy
6. Consider toast notifications for payment feedback (currently console logging)
