"""
Check what valid BANKNIFTY option symbols exist in Fyers
"""
from src.api.fyers_client import FyersClient
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv('frontend/.env.production')

# Initialize Supabase and authenticate
supabase: Client = create_client(
    'https://cxbcpmouqkajlxzmbomu.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN4YmNwbW91cWthamx4em1ib211Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NjA3NjMsImV4cCI6MjA4NDMzNjc2M30.oBozxBnSKARn-3xkRy8ceNU3wpxXh8MBReGtmtsBpEw'
)

auth_response = supabase.auth.sign_in_with_password({
    "email": "bineshch@gmail.com",
    "password": "Tra@2026"
})

# Get Fyers token
fyers_data = supabase.table('fyers_tokens').select('*').eq('user_id', auth_response.user.id).execute()
access_token = fyers_data.data[0]['access_token']

# Initialize Fyers client
client = FyersClient()
client.access_token = access_token
client._initialize_client()

print("="*80)
print("  🔍 CHECKING VALID BANKNIFTY SYMBOLS")
print("="*80)

# Get BANKNIFTY spot price
print("\n1️⃣  Getting BANKNIFTY spot price...")
try:
    quotes = client.fyers.quotes({"symbols": "NSE:NIFTYBANK-INDEX"})
    if quotes['s'] == 'ok':
        spot = quotes['d'][0]['v']['lp']
        print(f"   BANKNIFTY Spot: ₹{spot:,.2f}")
    else:
        print(f"   Error: {quotes}")
        spot = 60000  # Fallback
except Exception as e:
    print(f"   Error: {e}")
    spot = 60000

# Try different symbol formats for BANKNIFTY
print(f"\n2️⃣  Testing BANKNIFTY option symbol formats...")
print(f"   ATM Strike: {round(spot/100)*100}")

# Format 1: Weekly with BANKNIFTY prefix
test_symbols = [
    "NSE:BANKNIFTY26205CE",  # Old format
    "NSE:BANKNIFTY2620560500CE",  # Weekly format
    "NSE:BANKNIFTY26FEB60500CE",  # Monthly format
    "NSE:NIFTYBANK26205CE",  # Alternative naming
    "NSE:NIFTYBANK2620560500CE",
]

for symbol in test_symbols:
    try:
        result = client.fyers.quotes({"symbols": symbol})
        if result['s'] == 'ok':
            print(f"   ✅ VALID: {symbol}")
            ltp = result['d'][0]['v']['lp']
            print(f"      LTP: ₹{ltp}")
        else:
            print(f"   ❌ INVALID: {symbol} - {result.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"   ❌ ERROR: {symbol} - {e}")

# Get actual option chain to see real symbols
print(f"\n3️⃣  Fetching BANKNIFTY option chain...")
try:
    # Use the option chain endpoint
    import httpx
    import asyncio
    
    async def get_chain():
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(
                "http://localhost:8000/options/chain",
                params={"index": "BANKNIFTY", "expiry": "weekly"}
            )
            return response.json()
    
    chain_data = asyncio.run(get_chain())
    
    if 'strikes' in chain_data and len(chain_data['strikes']) > 0:
        print(f"\n   Sample BANKNIFTY option symbols from chain:")
        for i, strike_data in enumerate(chain_data['strikes'][:5], 1):
            ce_symbol = strike_data.get('ce', {}).get('symbol', 'N/A')
            print(f"      {i}. {ce_symbol}")
    else:
        print(f"   No strikes found in chain data")
        
except Exception as e:
    print(f"   Error fetching chain: {e}")

print("\n" + "="*80)
