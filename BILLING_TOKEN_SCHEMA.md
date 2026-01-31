# Database Schema Structure

## Core Tables

### 1. users (extends Supabase auth.users)
```
- id (UUID, PK)
- email (TEXT, UNIQUE)
- full_name (TEXT)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

### 2. user_subscriptions
```
- id (UUID, PK)
- user_id (UUID, FK to auth.users) - UNIQUE
- plan_type (TEXT) - 'free' | 'medium' | 'pro'
- status (TEXT) - 'active' | 'cancelled' | 'expired' | 'trial'
- razorpay_subscription_id (TEXT)
- razorpay_plan_id (TEXT)
- current_period_start (TIMESTAMPTZ)
- current_period_end (TIMESTAMPTZ)
- cancel_at_period_end (BOOLEAN)
- cancelled_at (TIMESTAMPTZ)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

### 3. user_credits (PAYG - Pay As You Go)
```
- id (UUID, PK)
- user_id (UUID, FK to auth.users) - UNIQUE
- balance (DECIMAL) - Current credits (new users: 100 free)
- lifetime_purchased (DECIMAL) - Total purchased lifetime
- lifetime_spent (DECIMAL) - Total spent lifetime
- last_topped_up (TIMESTAMPTZ)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

### 4. credit_transactions (Audit Log)
```
- id (UUID, PK)
- user_id (UUID, FK to auth.users)
- transaction_type (TEXT) - 'purchase' | 'debit' | 'refund' | 'bonus'
- amount (DECIMAL) - Amount of transaction
- balance_before (DECIMAL)
- balance_after (DECIMAL)
- description (TEXT)
- razorpay_payment_id (TEXT)
- razorpay_order_id (TEXT)
- scan_type (TEXT) - 'option_scan' | 'stock_scan' | 'bulk_scan' | 'ai_chat'
- scan_count (INTEGER)
- metadata (JSONB) - Additional data
- created_at (TIMESTAMPTZ)
```

### 5. usage_logs (Daily Usage Tracking)
```
- id (UUID, PK)
- user_id (UUID, FK to auth.users)
- scan_type (TEXT) - 'option_scan' | 'stock_scan' | 'bulk_scan'
- count (INTEGER)
- usage_date (DATE)
- metadata (JSONB)
- created_at (TIMESTAMPTZ)
- UNIQUE(user_id, scan_type, usage_date)
```

### 6. plan_limits (Configuration)
```
- id (UUID, PK)
- plan_type (TEXT, UNIQUE) - 'free' | 'medium' | 'pro'
- daily_option_scans (INTEGER, NULL = unlimited)
- daily_stock_scans (INTEGER, NULL = unlimited)
- bulk_scan_limit (INTEGER)
- daily_bulk_scans (INTEGER, NULL = unlimited)
- has_accuracy_tracking (BOOLEAN)
- has_priority_support (BOOLEAN)
- has_historical_data (BOOLEAN)
- has_early_access (BOOLEAN)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

## Billing Flow

### AI Chat Token Deduction
1. User makes chat request → `/api/ai/chat`
2. Backend verifies user authentication
3. AI service processes request
4. On success: `deduct_credits(user_id, 0.20, "AI Chat", "ai_chat")`
5. System checks: `balance >= 0.20`
6. If sufficient: deduct from `user_credits.balance`, create transaction record
7. If insufficient: return HTTP 402 (Payment Required)

### Transaction Record
```json
{
  "user_id": "uuid",
  "transaction_type": "debit",
  "amount": 0.20,
  "balance_before": 100.00,
  "balance_after": 99.80,
  "description": "AI Chat: What is the current market sentiment...",
  "scan_type": "ai_chat",
  "metadata": {
    "query_type": "general",
    "cached": false,
    "action": "chat"
  }
}
```

## Endpoints Charging 0.20 Credits Each

1. **POST /api/ai/chat** - General chat queries
2. **POST /api/ai/explain-signal** - Signal explanations  
3. **POST /api/ai/compare-indices** - Index comparisons
4. **POST /api/ai/trade-plan** - Trade plan generation

## Current Implementation Status

✅ Token deduction logic implemented in:
- `main.py` - Chat endpoint (line ~1305)
- `main.py` - Explain signal endpoint (line ~1407)
- `main.py` - Compare indices endpoint (line ~1520)
- `main.py` - Trade plan endpoint (line ~1585)

✅ Billing service:
- `src/services/billing_service.py` - `deduct_credits()` method (line 754)

✅ Database tables:
- `user_credits` - Stores balance
- `credit_transactions` - Audit log of all transactions

## Testing

To verify token deduction works:

1. User must have `user_credits` record with `balance >= 0.20`
2. Make API call to any of the 4 endpoints
3. Response includes: `"tokens_remaining": X`
4. Check `credit_transactions` table for new record with `transaction_type: "debit"`
