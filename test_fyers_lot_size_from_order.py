"""
Test if Fyers order API returns lot size in error response
"""
from src.api.fyers_client import fyers_client
from config.supabase_config import supabase_admin

# Authenticate
print("🔐 Authenticating...")
auth_response = supabase_admin.auth.sign_in_with_password({
    "email": "bineshch@gmail.com",
    "password": "Tra@2026"
})
user_id = auth_response.user.id
print(f"✅ Authenticated as: {auth_response.user.email}")

# Get Fyers token
token_response = supabase_admin.table("fyers_tokens")\
    .select("*")\
    .eq("user_id", user_id)\
    .order("updated_at", desc=True)\
    .limit(1)\
    .execute()

if token_response.data:
    fyers_token = token_response.data[0]["access_token"]
    fyers_client.access_token = fyers_token
    fyers_client._initialize_client()
    print(f"✅ Fyers client initialized")

# Try to place an order with quantity 1 (should fail)
symbol = "NSE:BANKNIFTY26FEB60000CE"
print(f"\n🔍 Testing order with symbol: {symbol}")
print(f"📦 Using quantity: 1 (intentionally wrong to see error)")

order_data = {
    "symbol": symbol,
    "qty": 1,
    "type": 2,  # LIMIT
    "side": 1,  # BUY
    "productType": "INTRADAY",
    "limitPrice": 990,
    "stopPrice": 0,
    "disclosedQty": 0,
    "validity": "DAY",
    "offlineOrder": False
}

try:
    print(f"\n📤 Placing order...")
    response = fyers_client.place_order(order_data)
    print(f"\n📊 Full response:")
    import json
    print(json.dumps(response, indent=2))
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Try with quantity 65 (NIFTY lot size)
print(f"\n" + "="*70)
print(f"🔍 Testing order with quantity: 65 (NIFTY lot size)")
order_data["qty"] = 65

try:
    print(f"\n📤 Placing order...")
    response = fyers_client.place_order(order_data)
    print(f"\n📊 Full response:")
    import json
    print(json.dumps(response, indent=2))
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Try with quantity 30 (BANKNIFTY lot size)
print(f"\n" + "="*70)
print(f"🔍 Testing order with quantity: 30 (BANKNIFTY lot size)")
order_data["qty"] = 30

try:
    print(f"\n📤 Placing order...")
    response = fyers_client.place_order(order_data)
    print(f"\n📊 Full response:")
    import json
    print(json.dumps(response, indent=2))
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
