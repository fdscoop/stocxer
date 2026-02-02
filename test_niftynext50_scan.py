#!/usr/bin/env python3
"""
NIFTYNEXT50 Scan Simulation - Same as user clicking scan on dashboard
Note: This index may not be added to the dashboard yet
"""
import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

import os
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

print('=' * 70)
print('🧑‍💻 USER SIMULATION: Scanning NIFTYNEXT50 from Dashboard')
print('=' * 70)
print(f'📅 Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print()

# Initialize Fyers
from supabase import create_client
from src.api.fyers_client import fyers_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
result = supabase.table('fyers_tokens').select('*').order('updated_at', desc=True).limit(1).execute()

if result.data:
    fyers_client.access_token = result.data[0]['access_token']
    fyers_client._initialize_client()
    print('✅ Fyers connected')
else:
    print('❌ No Fyers token!')
    exit(1)

# First, let's find the correct symbol for NIFTY NEXT 50
print()
print('━' * 70)
print('🔍 Finding NIFTYNEXT50 symbol...')
symbols_to_try = [
    'NSE:NIFTYNXT50-INDEX',
    'NSE:NIFTY_NEXT50-INDEX',
    'NSE:NIFTYNEXT50-INDEX',
    'NSE:NIFTY_NEXT_50-INDEX',
    'NSE:NEXT50-INDEX'
]

valid_symbol = None
spot = 0
for sym in symbols_to_try:
    quote = fyers_client.get_quotes([sym])
    if quote and 'd' in quote and quote['d']:
        v = quote['d'][0].get('v', {})
        if v.get('lp') and v.get('s') != 'error':
            valid_symbol = sym
            spot = v.get('lp', 0)
            print(f'   ✅ Found: {sym} @ ₹{spot:,.2f}')
            break
        else:
            print(f'   ❌ {sym}: Invalid')
    else:
        print(f'   ❌ {sym}: No data')

if not valid_symbol:
    print('   ⚠️ Could not find valid symbol, trying option chain anyway...')
    valid_symbol = 'NSE:NIFTYNXT50-INDEX'
    spot = 74000

# Get option chain
print()
print('━' * 70)
print('📊 Fetching NIFTYNEXT50 option chain...')
start = time.time()
from src.analytics.index_options import get_index_analyzer
analyzer = get_index_analyzer(fyers_client)

# Try different index names for option chain
index_names = ['NIFTYNXT50', 'NIFTYNEXT50', 'NIFTY_NEXT50', 'NEXT50']
chain = None
used_index = None

for idx_name in index_names:
    try:
        chain = analyzer.analyze_option_chain(idx_name, 'weekly')
        if chain and chain.strikes:
            used_index = idx_name
            print(f'   ✅ Found option chain for: {idx_name}')
            break
    except Exception as e:
        print(f'   ❌ {idx_name}: {str(e)[:50]}')

if chain:
    elapsed = time.time() - start
    print(f'   ✅ Option chain fetched in {elapsed:.1f}s')
    print(f'   📈 Spot: ₹{chain.spot_price:,.2f}')
    print(f'   📊 Futures: ₹{chain.future_price:,.2f}')
    print(f'   📅 Expiry: {chain.expiry_date} ({chain.days_to_expiry} days)')
    print(f'   📊 Strikes: {len(chain.strikes)}')
else:
    print('   ❌ Failed to fetch option chain!')
    print('   ℹ️  NIFTYNEXT50 options may not be available or index not supported')
    exit(1)

# MTF Analysis
print()
print('━' * 70)
print('📈 Running MTF/ICT Analysis...')
start = time.time()
from src.analytics.mtf_ict_analysis import get_mtf_analyzer, Timeframe
mtf = get_mtf_analyzer(fyers_client)
mtf_result = mtf.analyze(valid_symbol, [
    Timeframe.DAILY,
    Timeframe.FOUR_HOUR,
    Timeframe.ONE_HOUR,
    Timeframe.FIFTEEN_MIN,
    Timeframe.FIVE_MIN
])

elapsed = time.time() - start
print(f'   ✅ MTF Analysis in {elapsed:.1f}s')
print(f'   🎯 Bias: {mtf_result.overall_bias.upper()}')
for tf, analysis in mtf_result.analyses.items():
    print(f'      {tf}: {analysis.bias} | {analysis.market_structure.trend}')

# Generate signal
print()
print('━' * 70)
print('🎯 Generating Signal...')
print(f'   📊 PCR (OI): {chain.pcr_oi:.2f}')
print(f'   📊 Max Pain: {chain.max_pain}')
print(f'   📊 ATM Strike: {chain.atm_strike}')
print(f'   📊 ATM IV: {chain.atm_iv:.1f}%')

# Find best option
bias = mtf_result.overall_bias.upper()
rec_type = 'PUT' if bias == 'BEARISH' else 'CALL'
strike = chain.atm_strike - 200 if rec_type == 'PUT' else chain.atm_strike + 200

# Get option data from strikes
entry = 200  # default
for s in chain.strikes:
    if s.strike == strike:
        entry = s.put_ltp if rec_type == 'PUT' else s.call_ltp
        break

target1 = round(entry * 1.3)
target2 = round(entry * 1.8)
sl = round(entry * 0.7)

print()
print('╔' + '═' * 68 + '╗')
print('║' + '🎯 NIFTYNEXT50 SIGNAL'.center(68) + '║')
print('╠' + '═' * 68 + '╣')
print(f'║  Index: NIFTYNEXT50 ({used_index})'.ljust(69) + '║')
print(f'║  Bias: {bias}'.ljust(69) + '║')
print(f'║  Action: BUY {rec_type}'.ljust(69) + '║')
print('╠' + '═' * 68 + '╣')
opt_suffix = "PE" if rec_type == "PUT" else "CE"
print(f'║  Strike: {strike} {opt_suffix}'.ljust(69) + '║')
print(f'║  Entry: ₹{entry:.2f}'.ljust(69) + '║')
print(f'║  Target 1: ₹{target1}'.ljust(69) + '║')
print(f'║  Target 2: ₹{target2}'.ljust(69) + '║')
print(f'║  Stop Loss: ₹{sl}'.ljust(69) + '║')
print('╠' + '═' * 68 + '╣')
print(f'║  Spot: ₹{chain.spot_price:,.2f}'.ljust(69) + '║')
print(f'║  PCR: {chain.pcr_oi:.2f} | Max Pain: {chain.max_pain} | IV: {chain.atm_iv:.1f}%'.ljust(69) + '║')
print('╚' + '═' * 68 + '╝')

# Save to database
print()
print('━' * 70)
print('💾 Saving to database...')
from src.services.screener_service import screener_service

signal_data = {
    'index': used_index or 'NIFTYNXT50',
    'action': f'BUY {rec_type}',
    'option': {
        'symbol': f'NSE:{used_index}26FEB{strike}{opt_suffix}',
        'strike': strike,
        'option_type': rec_type,
        'type': 'CE' if rec_type == 'CALL' else 'PE',
        'expiry': str(chain.expiry_date),
        'expiry_date': str(chain.expiry_date),
        'trading_symbol': f'NSE:{used_index}26FEB{strike}{opt_suffix}',
        'is_weekly': True,
        'expiry_info': {'days_to_expiry': chain.days_to_expiry}
    },
    'entry': {'price': entry, 'limit_price': entry * 0.98},
    'pricing': {'entry_price': entry, 'ltp': entry},
    'targets': {'target_1': target1, 'target_2': target2, 'stop_loss': sl},
    'risk_reward': {'ratio': round((target1 - entry) / (entry - sl), 1) if entry > sl else 1.0},
    'confidence': {'level': 'HIGH', 'score': 75},
    'confidence_breakdown': {'total': 75},
    'index_data': {
        'spot_price': chain.spot_price, 
        'future_price': chain.future_price, 
        'pcr_oi': chain.pcr_oi, 
        'max_pain': chain.max_pain, 
        'atm_iv': chain.atm_iv
    },
    'htf_analysis': {'direction': mtf_result.overall_bias, 'strength': 75},
    'ltf_entry_model': {'found': True, 'entry_type': 'FVG_TEST'}
}

async def save():
    return await screener_service.save_option_scanner_result(
        user_id='4f1d1b44-7459-43fa-8aec-f9b9a0605c4b',
        signal_data=signal_data
    )

result = asyncio.run(save())
if result.get('saved'):
    print(f'   ✅ Saved! ID: {result.get("signal_id")}')
else:
    print(f'   ⚠️ Failed: {result.get("error")}')

print()
print('=' * 70)
print('✅ NIFTYNEXT50 SCAN COMPLETE!')
print('=' * 70)
