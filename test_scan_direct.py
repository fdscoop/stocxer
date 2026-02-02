#!/usr/bin/env python3
"""Direct test of option chain scanning with real Fyers data"""
import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

import os
from dotenv import load_dotenv
load_dotenv('/Users/bineshbalan/TradeWise/.env')

from supabase import create_client
from src.api.fyers_client import FyersClient, fyers_client
from src.analytics.index_options import get_index_analyzer, IndexOptionsAnalyzer

# Get Fyers token from database
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

result = supabase.table('fyers_tokens').select('*').limit(1).execute()
if not result.data:
    print("❌ No Fyers token found in database!")
    sys.exit(1)

token_data = result.data[0]
access_token = token_data['access_token']
print(f"✅ Found Fyers token in DB, expires: {token_data.get('expires_at')}")

# Initialize Fyers client with token
fyers_client.access_token = access_token
fyers_client._initialize_client()
print(f"✅ Fyers client initialized: fyers={fyers_client.fyers is not None}")

# Test getting quotes first
print("\n--- Test 1: Get NIFTY Quote ---")
try:
    quote = fyers_client.get_quotes(["NSE:NIFTY50-INDEX"])
    if quote and quote.get("d"):
        spot = quote["d"][0]["v"]["lp"]
        print(f"✅ NIFTY Spot Price: ₹{spot}")
    else:
        print(f"❌ Quote failed: {quote}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test option chain directly
print("\n--- Test 2: Get Option Chain ---")
try:
    chain = fyers_client.get_option_chain("NSE:NIFTY50-INDEX", strike_count=5)
    print(f"Response code: {chain.get('code')}")
    if chain.get('code') == 200:
        options = chain.get('data', {}).get('optionsChain', [])
        actual_options = [o for o in options if o.get('strike_price', -1) > 0]
        print(f"✅ Got {len(actual_options)} option entries")
        if actual_options:
            print(f"Sample: strike={actual_options[0].get('strike_price')}, type={actual_options[0].get('option_type')}")
    else:
        print(f"❌ Failed: {chain}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test full analysis
print("\n--- Test 3: Full Option Chain Analysis ---")
try:
    analyzer = get_index_analyzer(fyers_client)
    print(f"Analyzer created: fyers={analyzer.fyers is not None}, inner={analyzer.fyers.fyers is not None}")
    
    # Get expiry dates to see what timestamp will be used
    expiries = analyzer.get_expiry_dates("NIFTY")
    print(f"Weekly expiry: {expiries.get('weekly')}")
    
    # Convert to timestamp like the code does
    from datetime import datetime
    expiry_date = expiries.get('weekly')
    if expiry_date:
        expiry_date_parsed = datetime.strptime(expiry_date, "%Y-%m-%d")
        fyers_expiry_timestamp = str(int(expiry_date_parsed.timestamp()))
        print(f"Fyers timestamp: {fyers_expiry_timestamp}")
        
        # Test option chain with this timestamp
        print(f"\nTesting option chain WITH timestamp {fyers_expiry_timestamp}...")
        chain_with_ts = fyers_client.get_option_chain("NSE:NIFTY50-INDEX", strike_count=5, expiry_date=fyers_expiry_timestamp)
        print(f"With timestamp - code: {chain_with_ts.get('code')}, message: {chain_with_ts.get('message', 'OK')}")
        if chain_with_ts.get('code') != 200:
            print(f"Full response: {chain_with_ts}")
    
    result = analyzer.analyze_option_chain("NIFTY", "weekly")
    if result:
        print(f"✅ Analysis successful!")
        print(f"   Spot: ₹{result.spot_price}")
        print(f"   Expiry: {result.expiry_date}")
        print(f"   PCR: {result.pcr_oi}")
        print(f"   Max Pain: {result.max_pain}")
    else:
        print("❌ Analysis returned None")
except Exception as e:
    import traceback
    print(f"❌ Exception: {e}")
    traceback.print_exc()
