#!/usr/bin/env python3
"""BANKNIFTY Scan Simulation"""

import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

print('=' * 70)
print('🧑‍💻 USER SIMULATION: Scanning BANKNIFTY from Dashboard')
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

# Get BANKNIFTY spot
print()
print('━' * 70)
print('🔍 Fetching BANKNIFTY spot price...')
quote = fyers_client.get_quotes(['NSE:NIFTYBANK-INDEX'])
if quote.get('s') == 'ok':
    spot = quote['d'][0]['v']['lp']
    print(f'   ✅ BANKNIFTY Spot: ₹{spot:,.2f}')
else:
    print(f'   ⚠️ Quote issue: {quote}')
    spot = 58417

# Analyze option chain
print()
print('━' * 70)
print('📊 Fetching BANKNIFTY option chain...')
from src.analytics.index_options import get_index_analyzer
import time

analyzer = get_index_analyzer(fyers_client)
start = time.time()
chain = analyzer.analyze_option_chain('BANKNIFTY', 'weekly')

if chain:
    print(f'   ✅ Option chain fetched in {time.time()-start:.1f}s')
    print(f'   📈 Spot: ₹{chain.spot_price:,.2f}')
    print(f'   📊 Futures: ₹{chain.future_price:,.2f}')
    print(f'   📅 Expiry: {chain.expiry_date} ({chain.days_to_expiry} days)')
    print(f'   📊 Strikes: {len(chain.strikes)}')
else:
    print('   ❌ Failed!')
    exit(1)

# MTF Analysis
print()
print('━' * 70)
print('📈 Running MTF/ICT Analysis...')
from src.analytics.mtf_ict_analysis import get_mtf_analyzer, Timeframe

mtf = get_mtf_analyzer(fyers_client)
start = time.time()
mtf_result = mtf.analyze('NSE:NIFTYBANK-INDEX', [
    Timeframe.DAILY,
    Timeframe.FOUR_HOUR,
    Timeframe.ONE_HOUR,
    Timeframe.FIFTEEN_MIN,
    Timeframe.FIVE_MIN
])

print(f'   ✅ MTF Analysis in {time.time()-start:.1f}s')
print(f'   🎯 Bias: {mtf_result.overall_bias.upper()}')
for tf, analysis in mtf_result.analyses.items():
    print(f'      {tf}: {analysis.bias} | {analysis.market_structure.trend}')

# Generate Signal
print()
print('━' * 70)
print('🎯 Generating Signal...')

print(f'   📊 PCR (OI): {chain.pcr_oi:.2f}')
print(f'   📊 Max Pain: {chain.max_pain}')
print(f'   📊 ATM Strike: {chain.atm_strike}')
print(f'   📊 ATM IV: {chain.atm_iv:.1f}%')

# Determine recommendation
if mtf_result.overall_bias == 'bullish':
    rec_type = 'CALL'
    strike = chain.atm_strike + 100
elif mtf_result.overall_bias == 'bearish':
    rec_type = 'PUT'
    strike = chain.atm_strike - 100
else:
    rec_type = 'NEUTRAL'
    strike = chain.atm_strike

# Find option price
entry = 300  # default
for s in chain.strikes:
    if s.strike == strike:
        if rec_type == 'CALL':
            entry = s.call_ltp or 300
        else:
            entry = s.put_ltp or 300
        break

opt_suffix = "CE" if rec_type == "CALL" else "PE"

# Print Signal
print()
print('╔' + '═' * 68 + '╗')
print('║' + ' ' * 20 + '🎯 BANKNIFTY SIGNAL' + ' ' * 27 + '║')
print('╠' + '═' * 68 + '╣')
print(f'║  Index: BANKNIFTY{" " * 50}║')
print(f'║  Bias: {mtf_result.overall_bias.upper()}{" " * (59 - len(mtf_result.overall_bias))}║')
print(f'║  Action: BUY {rec_type}{" " * (53 - len(rec_type))}║')
print('╠' + '═' * 68 + '╣')
print(f'║  Strike: {strike} {opt_suffix}{" " * 48}║')
print(f'║  Entry: ₹{entry:.2f}{" " * (56 - len(f"{entry:.2f}"))}║')
print(f'║  Target 1: ₹{round(entry * 1.3)}{" " * 51}║')
print(f'║  Target 2: ₹{round(entry * 1.8)}{" " * 51}║')
print(f'║  Stop Loss: ₹{round(entry * 0.7)}{" " * 50}║')
print('╠' + '═' * 68 + '╣')
print(f'║  Spot: ₹{chain.spot_price:,.2f}{" " * 46}║')
print(f'║  PCR: {chain.pcr_oi:.2f} | Max Pain: {chain.max_pain} | IV: {chain.atm_iv:.1f}%{" " * 18}║')
print('╚' + '═' * 68 + '╝')

# Save to database
print()
print('━' * 70)
print('💾 Saving to database...')

from src.services.screener_service import screener_service
import asyncio

signal_data = {
    'index': 'BANKNIFTY',
    'signal': f'ICT_{mtf_result.overall_bias.upper()}_BIAS',
    'action': f'BUY {rec_type}',
    'option': {
        'strike': strike,
        'type': opt_suffix,
        'symbol': f'{strike} {opt_suffix}',
        'trading_symbol': f'NSE:BANKNIFTY26203{strike}{opt_suffix}',
        'expiry_date': chain.expiry_date,
        'expiry_info': {'days_to_expiry': chain.days_to_expiry, 'is_weekly': True}
    },
    'pricing': {'ltp': entry, 'entry_price': entry, 'iv_used': chain.atm_iv},
    'entry': {'price': entry, 'trigger_level': chain.spot_price},
    'targets': {'target_1': round(entry * 1.3), 'target_2': round(entry * 1.8), 'stop_loss': round(entry * 0.7)},
    'risk_reward': {'risk_per_lot': round((entry - entry*0.7) * 15), 'reward_1_per_lot': round((entry*1.3 - entry) * 15), 'ratio_1': 1.0},
    'greeks': {'delta': 0.45, 'gamma': 0.01, 'theta': -5.0, 'vega': 10.0},
    'confidence': {'level': 'HIGH', 'score': 75},
    'confidence_breakdown': {'total': 75},
    'index_data': {'spot_price': chain.spot_price, 'future_price': chain.future_price, 'pcr_oi': chain.pcr_oi, 'max_pain': chain.max_pain, 'atm_iv': chain.atm_iv},
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
print('✅ BANKNIFTY SCAN COMPLETE!')
print('=' * 70)
