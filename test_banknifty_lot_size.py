"""
Test BANKNIFTY lot size from Fyers
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

# Test BANKNIFTY symbol
symbol = "NSE:BANKNIFTY26FEB60000CE"
print(f"\n🔍 Testing symbol: {symbol}")

try:
    quote = fyers_client.get_quotes([symbol])
    print(f"\n📊 Full quote response:")
    import json
    print(json.dumps(quote, indent=2))
    
    if quote and "d" in quote and len(quote["d"]) > 0:
        symbol_data = quote["d"][0]["v"]
        print(f"\n📊 Symbol data:")
        print(json.dumps(symbol_data, indent=2))
        
        if "lot_size" in symbol_data:
            lot_size = int(symbol_data["lot_size"])
            print(f"\n✅ LOT SIZE FROM FYERS: {lot_size}")
        else:
            print(f"\n❌ No 'lot_size' field in symbol data")
            print(f"Available fields: {list(symbol_data.keys())}")
    else:
        print(f"\n❌ Invalid quote response")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
