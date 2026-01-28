#!/usr/bin/env python3
"""Test different Fyers option symbol formats"""

from fyers_apiv3 import fyersModel
from datetime import datetime, timedelta
import os

# Use token from environment or hardcode for testing
# Token from previous session - valid until 2026-01-29
token = os.environ.get('FYERS_TOKEN', 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE3Mzc5MzYwODAsImV4cCI6MTczODAxNjI0MCwibmJmIjoxNzM3OTM2MDgwLCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCbnh0WWdMYjdPbmtveDltN09XVnJVZmRKWmhPcTZWQ1dxdGJSVFZnQ2tmUGN1ZnR2c2UzYU93WVRmb3Y1elNsOV92RXdHZmJxUWFMdDcydFB3YVlQVFRMQ2w0Wng2NWd4MU8wbW9YRFVfMVBfd0dxQUo5VXhSVllUeWVoNlVxNTBBVUZoQyIsImRpc3BsYXlfbmFtZSI6IkJJTkVTSCBDSEFLUkFQQU5JIEFEREFNIiwiZnlfaWQiOiJZQjA0MDE3Iiwib21zIjoiSzEiLCJoc21fa2V5IjoiNjc3ZWM5MTQwYmRkOGZmZGI5MjI4NTQzMmVjMDQxN2E5ZTBlYjM2NDY3NmE5ZDM5YTlhYjBlZjkiLCJvbW5lX3VzZXJfdHlwZSI6IkNMSUVOVCJ9.qXA_28qYOFsaWSm1t9MJ9GY3MYaKakqmEvJwxPDGYpE')
print(f'Token: {token[:50]}...')

fyers = fyersModel.FyersModel(client_id='KNFUQHKZJY-100', token=token, log_path='/tmp/')

# Test different symbol formats for options expiring around Jan 30, 2026
# Current weekly expiry should be Jan 30, 2026 (Thursday)
# Next expiry Feb 6, 2026

test_symbols = [
    # Current format (YYMMDD) - Wrong?
    'NSE:NIFTY26013024650PE',
    
    # Monthly format with month name (for monthly expiry)
    'NSE:NIFTY26JAN24650PE',
    
    # Weekly format with month code:
    # For weekly: YY + Month code (1-9 for Jan-Sep, O/N/D for Oct/Nov/Dec) + DD
    'NSE:NIFTY26130024650PE',   # Jan 30 = month code 1 + 30 day
    'NSE:NIFTY2613024650PE',    # Jan 30 = month code 1 + 30 day (no zero)
    
    # Feb 6 expiry test
    'NSE:NIFTY26020624650PE',   # YYMMDD format
    'NSE:NIFTY26FEB24650PE',    # Month name format
    'NSE:NIFTY2620624650PE',    # Month code 2 + 06 day
    
    # Try current month expiry with different strikes
    'NSE:NIFTY26JAN25000CE',
    'NSE:NIFTY26JAN25300PE',
    
    # Also test what option chain returns as symbol
]

for sym in test_symbols:
    print(f'\nTesting: {sym}')
    data = {
        'symbol': sym,
        'resolution': '15',
        'date_format': '1',
        'range_from': int((datetime.now() - timedelta(days=5)).timestamp()),
        'range_to': int(datetime.now().timestamp()),
        'cont_flag': '0'
    }
    result = fyers.history(data=data)
    code = result.get('code', result.get('s', 'N/A'))
    message = result.get('message', result.get('errmsg', 'OK'))
    candles = len(result.get('candles', [])) if code in [200, 'ok'] else 0
    print(f'  Result: code={code}, candles={candles}, message={str(message)[:60]}')

# Also test quotes to see what symbols are valid
print("\n\n=== Testing Quotes API ===")
quote_symbols = [
    'NSE:NIFTY26JAN25000CE',
    'NSE:NIFTY26013025000CE',
    'NSE:NIFTY2613025000CE',
]

for sym in quote_symbols:
    print(f'\nQuote for: {sym}')
    data = {"symbols": sym}
    result = fyers.quotes(data)
    print(f'  Result: {result.get("code", "N/A")} - {str(result.get("message", result.get("d", [])))[:100]}')

# Try to get option chain to see actual symbol format
print("\n\n=== Option Chain Symbol Format ===")
chain_data = {
    "symbol": "NSE:NIFTY-INDEX",
    "strikecount": 3,
    "timestamp": ""
}
chain_result = fyers.optionchain(data=chain_data)
if chain_result.get('code') == 200:
    for opt in chain_result.get('data', {}).get('optionsChain', [])[:5]:
        print(f"  Symbol: {opt.get('symbol')} - Strike: {opt.get('strikePrice')} - Type: {opt.get('option_type')}")
else:
    print(f"  Error: {chain_result}")
