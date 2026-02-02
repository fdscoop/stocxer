#!/usr/bin/env python3
"""Test option chain scanning with the fixed expiry timestamp lookup"""
import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

import os
from dotenv import load_dotenv
load_dotenv('/Users/bineshbalan/TradeWise/.env')

from supabase import create_client
from src.api.fyers_client import fyers_client
from src.analytics.index_options import IndexOptionsAnalyzer

# Get Fyers token from database
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

result = supabase.table('fyers_tokens').select('*').limit(1).execute()
if not result.data:
    print("No Fyers token found in database!")
    sys.exit(1)

token_data = result.data[0]
access_token = token_data['access_token']
print(f"Found Fyers token in DB, expires: {token_data.get('expires_at')}")

# Initialize Fyers client with token
# Token already has CLIENT_ID prefix from set_access_token
fyers_client.access_token = access_token
print(f"Setting access token: {access_token[:50]}...")
fyers_client._initialize_client()
print(f"Fyers client initialized: fyers={fyers_client.fyers is not None}")

# Test NIFTY quote first
print("\n--- Test 1: Get NIFTY Quote ---")
try:
    quote = fyers_client.get_quotes(["NSE:NIFTY50-INDEX"])
    if quote and quote.get("d"):
        spot = quote["d"][0]["v"]["lp"]
        print(f"NIFTY Spot Price: {spot}")
    else:
        print(f"Quote failed: {quote}")
        sys.exit(1)
except Exception as e:
    print(f"Exception: {e}")
    sys.exit(1)

# Test full option chain analysis with the fixed code
print("\n--- Test 2: Full Option Chain Analysis (NIFTY) ---")
try:
    analyzer = IndexOptionsAnalyzer(fyers_client)
    print(f"Analyzer created: fyers={analyzer.fyers is not None}")
    
    result = analyzer.analyze_option_chain("NIFTY", "weekly")
    
    if result:
        print(f"NIFTY Analysis successful!")
        print(f"   Spot: {result.get('spot_price')}")
        print(f"   Expiry: {result.get('expiry_date')}")
        print(f"   ATM Strike: {result.get('atm_strike')}")
        print(f"   Bias: {result.get('bias')}")
        print(f"   Strikes: {len(result.get('strike_analysis', []))}")
    else:
        print(f"NIFTY Analysis returned None")
except Exception as e:
    print(f"NIFTY Analysis error: {e}")
    import traceback
    traceback.print_exc()

# Test BANKNIFTY
print("\n--- Test 3: Full Option Chain Analysis (BANKNIFTY) ---")
try:
    result2 = analyzer.analyze_option_chain("BANKNIFTY", "weekly")
    
    if result2:
        print(f"BANKNIFTY Analysis successful!")
        print(f"   Spot: {result2.get('spot_price')}")
        print(f"   Expiry: {result2.get('expiry_date')}")
        print(f"   ATM Strike: {result2.get('atm_strike')}")
    else:
        print(f"BANKNIFTY Analysis returned None")
except Exception as e:
    print(f"BANKNIFTY Analysis error: {e}")

# Test FINNIFTY
print("\n--- Test 4: Full Option Chain Analysis (FINNIFTY) ---")
try:
    result3 = analyzer.analyze_option_chain("FINNIFTY", "weekly")
    
    if result3:
        print(f"FINNIFTY Analysis successful!")
        print(f"   Spot: {result3.get('spot_price')}")
        print(f"   Expiry: {result3.get('expiry_date')}")
    else:
        print(f"FINNIFTY Analysis returned None")
except Exception as e:
    print(f"FINNIFTY Analysis error: {e}")

print("\nTest complete!")
