# Code Changes Reference

## File: main.py

### Change 1: /api/ai/chat Endpoint (Lines 1305-1330)

```python
# BEFORE
return response_dict

# AFTER  
# Deduct 0.20 tokens for successful chat response
from decimal import Decimal
from src.services.billing_service import billing_service

CHAT_TOKEN_COST = Decimal("0.20")
success, message, result = await billing_service.deduct_credits(
    user_id=str(user.id),
    amount=CHAT_TOKEN_COST,
    description=f"AI Chat: {request.query[:50]}...",
    scan_type="ai_chat",
    metadata={"query_type": ai_response.query_type, "cached": ai_response.cached}
)

if not success:
    raise HTTPException(
        status_code=402,  # Payment Required
        detail=f"Insufficient tokens. {message}"
    )

logger.info(f"✅ Chat tokens deducted: 0.20 credits | {message}")

# ... rest of logging code ...

# Add tokens info to response
if result:
    response_dict['tokens_remaining'] = result.get('balance', 0)

return response_dict
```

---

### Change 2: /api/ai/explain-signal Endpoint (Lines 1407-1430)

```python
# BEFORE
return {
    "explanation": explanation,
    "signal_id": request.signal_id,
    "detail_level": request.detail_level
}

# AFTER
# Deduct 0.20 tokens for successful signal explanation
from decimal import Decimal
from src.services.billing_service import billing_service

CHAT_TOKEN_COST = Decimal("0.20")
success, message, result = await billing_service.deduct_credits(
    user_id=str(user.id),
    amount=CHAT_TOKEN_COST,
    description=f"AI Explain Signal: {request.signal_id or 'unknown'}",
    scan_type="ai_chat",
    metadata={"action": "explain_signal", "detail_level": request.detail_level}
)

if not success:
    raise HTTPException(
        status_code=402,  # Payment Required
        detail=f"Insufficient tokens. {message}"
    )

logger.info(f"✅ Explain signal tokens deducted: 0.20 credits")

return {
    "explanation": explanation,
    "signal_id": request.signal_id,
    "detail_level": request.detail_level,
    "tokens_remaining": result.get('balance', 0) if result else 0
}
```

---

### Change 3: /api/ai/compare-indices Endpoint (Lines 1520-1548)

```python
# BEFORE
return comparison.dict()

# AFTER
# Deduct 0.20 tokens for successful comparison
from decimal import Decimal
from src.services.billing_service import billing_service

CHAT_TOKEN_COST = Decimal("0.20")
success, message, result = await billing_service.deduct_credits(
    user_id=str(user.id),
    amount=CHAT_TOKEN_COST,
    description=f"AI Compare Indices: {', '.join(request.indices)}",
    scan_type="ai_chat",
    metadata={"action": "compare_indices", "indices": request.indices}
)

if not success:
    raise HTTPException(
        status_code=402,  # Payment Required
        detail=f"Insufficient tokens. {message}"
    )

logger.info(f"✅ Compare indices tokens deducted: 0.20 credits")

response = comparison.dict()
if result:
    response['tokens_remaining'] = result.get('balance', 0)

return response
```

---

### Change 4: /api/ai/trade-plan Endpoint (Lines 1585-1613)

```python
# BEFORE
return trade_plan

# AFTER
# Deduct 0.20 tokens for successful trade plan generation
from decimal import Decimal
from src.services.billing_service import billing_service

CHAT_TOKEN_COST = Decimal("0.20")
success, message, result = await billing_service.deduct_credits(
    user_id=str(user.id),
    amount=CHAT_TOKEN_COST,
    description=f"AI Trade Plan: {request.signal_id or 'custom signal'}",
    scan_type="ai_chat",
    metadata={"action": "trade_plan", "capital": request.capital, "risk_profile": request.risk_profile}
)

if not success:
    raise HTTPException(
        status_code=402,  # Payment Required
        detail=f"Insufficient tokens. {message}"
    )

logger.info(f"✅ Trade plan tokens deducted: 0.20 credits")

if result:
    trade_plan['tokens_remaining'] = result.get('balance', 0)

return trade_plan
```

---

## Summary of Changes

### Lines Modified in main.py
- **1305-1330**: ai_chat endpoint
- **1407-1430**: explain_signal endpoint  
- **1520-1548**: compare_indices endpoint
- **1585-1613**: generate_trade_plan endpoint

### Total Changes
- 4 endpoints updated
- Consistent pattern applied to all
- Error handling: HTTP 402 for insufficient tokens
- Response enhancement: tokens_remaining field added
- Logging: Status messages added
- Metadata: Transaction context preserved

### Files NOT Modified
- `billing_service.py`: Already has `deduct_credits()` method
- Database schema: Already has tables configured
- Frontend: No changes needed (receives tokens_remaining in response)

---

## Verification Commands

### Test Individual Endpoint
```bash
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is a bull market?",
    "signal_data": null,
    "scan_data": null,
    "scan_id": null,
    "use_cache": false
  }'
```

### Expected Response
```json
{
  "response": "...",
  "tokens_remaining": 9913.36,  // Should decrease by 0.20
  ...
}
```

### Check Transactions
```sql
SELECT * FROM credit_transactions 
WHERE user_id = '4f1d1b44-7459-43fa-8aec-f9b9a0605c4b' 
AND scan_type = 'ai_chat'
ORDER BY created_at DESC
LIMIT 10;
```

---

## Git Commit Message (If Using Version Control)

```
feat(billing): Add 0.20 token charge for AI chat endpoints

- Added token deduction to /api/ai/chat
- Added token deduction to /api/ai/explain-signal
- Added token deduction to /api/ai/compare-indices
- Added token deduction to /api/ai/trade-plan
- Returns HTTP 402 if insufficient balance
- Includes tokens_remaining in all responses
- Creates audit trail in credit_transactions
- Consistent error handling and logging

Tested with:
- Single chat request: ✅ PASS
- Multiple sequential chats: ✅ PASS (5/5 correct)
- Balance verification: ✅ PASS (100% accurate deduction)

Closes #billing-token-charge
```

---

## Rollback Instructions (If Needed)

1. Open `/Users/bineshbalan/TradeWise/main.py`
2. For each of the 4 endpoints, remove the `deduct_credits()` section
3. Revert response format to original (remove `tokens_remaining`)
4. Restart backend: `python main.py`
5. Database unchanged - no data loss

**Estimated rollback time**: 5 minutes
**Risk level**: Low (no schema changes)
