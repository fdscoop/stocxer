#!/usr/bin/env python3
"""Test Fyers API directly to debug option chain issues"""
import os
import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

from dotenv import load_dotenv
load_dotenv('/Users/bineshbalan/TradeWise/.env')

from fyers_apiv3 import fyersModel
import tempfile

# Get credentials from environment
client_id = os.environ.get('FYERS_CLIENT_ID')
access_token = os.environ.get('FYERS_ACCESS_TOKEN')

print(f"Client ID: {client_id}")
print(f"Access Token present: {bool(access_token)}")

if not access_token:
    print("\n❌ No FYERS_ACCESS_TOKEN in .env!")
    print("The access token might be stored in the database instead.")
    
    # Try to get from Supabase
    from supabase import create_client
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    
    print(f"\nTrying Supabase...")
    supabase = create_client(url, key)
    
    # Check fyers_tokens table
    result = supabase.table('fyers_tokens').select('*').limit(1).execute()
    if result.data:
        token_data = result.data[0]
        access_token = token_data.get('access_token')
        print(f"Found token in DB! Expires: {token_data.get('expires_at')}")
    else:
        print("No tokens found in fyers_tokens table")
        sys.exit(1)

# Initialize Fyers client
log_path = os.path.join(tempfile.gettempdir(), "fyers_logs")
os.makedirs(log_path, exist_ok=True)

fyers = fyersModel.FyersModel(
    client_id=client_id,
    token=access_token,
    log_path=log_path
)

print("\n" + "="*50)
print("TEST 1: Option chain WITHOUT expiry (default/current)")
print("="*50)
data1 = {
    "symbol": "NSE:NIFTY50-INDEX",
    "strikecount": 5
}
response1 = fyers.optionchain(data1)
print(f"Code: {response1.get('code')}")
if response1.get('code') == 200:
    options = response1.get('data', {}).get('optionsChain', [])
    actual_options = [o for o in options if o.get('strike_price', -1) > 0]
    print(f"Options count: {len(actual_options)}")
    if actual_options:
        print(f"Sample: strike={actual_options[0].get('strike_price')}, type={actual_options[0].get('option_type')}")
else:
    print(f"Error: {response1}")

print("\n" + "="*50)
print("TEST 2: Option chain WITH Unix timestamp (Feb 3, 2026)")  
print("="*50)
data2 = {
    "symbol": "NSE:NIFTY50-INDEX",
    "strikecount": 5,
    "timestamp": "1770112800"  # Unix timestamp for Feb 3, 2026
}
response2 = fyers.optionchain(data2)
print(f"Code: {response2.get('code')}")
if response2.get('code') == 200:
    options = response2.get('data', {}).get('optionsChain', [])
    actual_options = [o for o in options if o.get('strike_price', -1) > 0]
    print(f"Options count: {len(actual_options)}")
    if actual_options:
        print(f"Sample: strike={actual_options[0].get('strike_price')}, type={actual_options[0].get('option_type')}, symbol={actual_options[0].get('symbol')}")
else:
    print(f"Error: {response2}")

print("\n" + "="*50)
print("TEST 3: Option chain WITH Unix timestamp (Feb 24, 2026 - monthly)")
print("="*50)
data3 = {
    "symbol": "NSE:NIFTY50-INDEX", 
    "strikecount": 5,
    "timestamp": "1771927200"  # Unix timestamp for Feb 24, 2026
}
response3 = fyers.optionchain(data3)
print(f"Code: {response3.get('code')}")
if response3.get('code') == 200:
    options = response3.get('data', {}).get('optionsChain', [])
    actual_options = [o for o in options if o.get('strike_price', -1) > 0]
    print(f"Options count: {len(actual_options)}")
    if actual_options:
        print(f"Sample: strike={actual_options[0].get('strike_price')}, type={actual_options[0].get('option_type')}, symbol={actual_options[0].get('symbol')}")
else:
    print(f"Error: {response3}")
