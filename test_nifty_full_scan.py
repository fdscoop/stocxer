#!/usr/bin/env python3
"""
🎯 FULL NIFTY SCAN TEST - Complete data verification for Dashboard scanning
This shows all data collected including options chain (calls/puts)
"""

import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

print("=" * 80)
print("📊 FULL NIFTY SCAN - Complete Data Collection Verification")
print("=" * 80)
print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================
# STEP 1: Initialize Fyers Client
# ============================================================
print("━" * 80)
print("🔌 STEP 1: Initialize Fyers Client")
print("━" * 80)

from supabase import create_client
from src.api.fyers_client import fyers_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

result = supabase.table('fyers_tokens').select('*').order('updated_at', desc=True).limit(1).execute()

if result.data:
    token_data = result.data[0]
    fyers_client.access_token = token_data['access_token']
    fyers_client._initialize_client()
    print(f"   ✅ Fyers connected")
    print(f"   📅 Token expires: {token_data.get('expires_at', 'unknown')[:19]}")
else:
    print("   ❌ No Fyers token!")
    exit(1)

# ============================================================
# STEP 2: Fetch NIFTY Spot Price
# ============================================================
print()
print("━" * 80)
print("💰 STEP 2: Fetch NIFTY Spot Price")
print("━" * 80)

try:
    quote = fyers_client.get_quotes(["NSE:NIFTY50-INDEX"])
    if quote.get('s') == 'ok':
        spot_data = quote['d'][0]['v']
        spot_price = spot_data['lp']
        print(f"   ✅ NIFTY Spot Price: ₹{spot_price:,.2f}")
        print(f"   📈 Open: ₹{spot_data.get('open_price', 'N/A'):,.2f}")
        print(f"   📉 Low: ₹{spot_data.get('low_price', 'N/A'):,.2f}")
        print(f"   📊 High: ₹{spot_data.get('high_price', 'N/A'):,.2f}")
        print(f"   📊 Prev Close: ₹{spot_data.get('prev_close_price', 'N/A'):,.2f}")
    else:
        print(f"   ⚠️ Quote issue: {quote}")
        spot_price = 25650
except Exception as e:
    print(f"   ⚠️ Error: {e}")
    spot_price = 25650

# ============================================================
# STEP 3: Fetch Full Option Chain
# ============================================================
print()
print("━" * 80)
print("📊 STEP 3: Fetch Full Option Chain Data")
print("━" * 80)

from src.analytics.index_options import get_index_analyzer

analyzer = get_index_analyzer(fyers_client)
start_time = time.time()

chain = analyzer.analyze_option_chain("NIFTY", "weekly")
fetch_time = time.time() - start_time

if chain:
    print(f"   ✅ Option chain fetched in {fetch_time:.1f}s")
    print()
    
    # Basic Chain Info
    print("   📋 CHAIN OVERVIEW:")
    print(f"      Spot Price: ₹{chain.spot_price:,.2f}")
    print(f"      Futures Price: ₹{chain.future_price:,.2f}")
    print(f"      Expiry Date: {chain.expiry_date}")
    print(f"      Days to Expiry: {chain.days_to_expiry}")
    print(f"      Total Strikes: {len(chain.strikes)}")
    print()
    
    # PCR & Volatility
    print("   📊 MARKET METRICS:")
    print(f"      ATM Strike: {chain.atm_strike}")
    print(f"      ATM IV: {chain.atm_iv:.2f}%")
    print(f"      PCR (OI): {chain.pcr_oi:.3f} → {'🟢 Bullish' if chain.pcr_oi < 0.8 else '🔴 Bearish' if chain.pcr_oi > 1.2 else '🟡 Neutral'}")
    print(f"      PCR (Volume): {chain.pcr_volume:.3f}")
    print(f"      Max Pain: {chain.max_pain}")
    print()
    
    # Support/Resistance
    print("   📈 OI-BASED LEVELS:")
    print(f"      Support Levels: {chain.support_levels[:5]}")
    print(f"      Resistance Levels: {chain.resistance_levels[:5]}")
    print()
    
    # ============================================================
    # STEP 4: Display Option Chain (Calls & Puts)
    # ============================================================
    print("━" * 80)
    print("📋 STEP 4: OPTIONS CHAIN - CALL & PUT DATA")
    print("━" * 80)
    print()
    
    # Header
    print(f"{'─'*40} CALLS {'─'*28}│{'─'*28} PUTS {'─'*40}")
    print(f"{'Volume':>12} {'OI':>12} {'LTP':>10} {'IV':>8} │{'Strike':^10}│ {'LTP':<10} {'OI':<12} {'Volume':<12} {'IV':<8}")
    print("─" * 120)
    
    # Display strikes around ATM (±10 strikes)
    atm = chain.atm_strike
    strikes_to_show = sorted([s for s in chain.strikes if abs(s.strike - atm) <= 500], key=lambda x: x.strike)
    
    for strike in strikes_to_show:
        call_iv = getattr(strike, 'call_iv', 0) or 0
        put_iv = getattr(strike, 'put_iv', 0) or 0
        
        # Highlight ATM strike
        marker = " ★" if strike.strike == atm else "  "
        
        print(f"{strike.call_volume:>12,} {strike.call_oi:>12,} {strike.call_ltp:>10.2f} {call_iv:>7.1f}% │{strike.strike:^10}│ {strike.put_ltp:<10.2f} {strike.put_oi:<12,} {strike.put_volume:<12,} {put_iv:<7.1f}%{marker}")
    
    print("─" * 120)
    print(f"   ★ = ATM Strike ({atm})")
    print()
    
    # Totals
    total_call_oi = sum(s.call_oi for s in chain.strikes)
    total_put_oi = sum(s.put_oi for s in chain.strikes)
    total_call_vol = sum(s.call_volume for s in chain.strikes)
    total_put_vol = sum(s.put_volume for s in chain.strikes)
    
    print("   📊 CHAIN TOTALS:")
    print(f"      Total Call OI: {total_call_oi:,}")
    print(f"      Total Put OI: {total_put_oi:,}")
    print(f"      Total Call Volume: {total_call_vol:,}")
    print(f"      Total Put Volume: {total_put_vol:,}")
    print()
    
else:
    print("   ❌ Failed to fetch option chain!")
    exit(1)

# ============================================================
# STEP 5: Multi-Timeframe Analysis
# ============================================================
print("━" * 80)
print("📈 STEP 5: Multi-Timeframe (MTF) & ICT Analysis")
print("━" * 80)

from src.analytics.mtf_ict_analysis import get_mtf_analyzer, Timeframe

mtf_analyzer = get_mtf_analyzer(fyers_client)
start_time = time.time()

timeframes = [
    Timeframe.DAILY,
    Timeframe.FOUR_HOUR,
    Timeframe.ONE_HOUR,
    Timeframe.FIFTEEN_MIN,
    Timeframe.FIVE_MIN
]

mtf_result = mtf_analyzer.analyze("NSE:NIFTY50-INDEX", timeframes)
mtf_time = time.time() - start_time

print(f"   ✅ MTF Analysis complete in {mtf_time:.1f}s")
print()
print(f"   🎯 OVERALL BIAS: {mtf_result.overall_bias.upper()}")
print()
print("   📊 TIMEFRAME BREAKDOWN:")
print(f"   {'Timeframe':<15} {'Bias':<12} {'Trend':<15} {'BOS':<10} {'CHoCH':<10}")
print("   " + "─" * 62)

for tf_key, tf_analysis in mtf_result.analyses.items():
    bos = "Yes" if tf_analysis.market_structure.break_of_structure else "No"
    choch = "Yes" if tf_analysis.market_structure.change_of_character else "No"
    print(f"   {tf_key:<15} {tf_analysis.bias:<12} {tf_analysis.market_structure.trend:<15} {bos:<10} {choch:<10}")

print()

# ICT Details
print("   🏛️ ICT ANALYSIS DETAILS:")
for tf_key, tf_analysis in mtf_result.analyses.items():
    if hasattr(tf_analysis, 'order_blocks') and tf_analysis.order_blocks:
        print(f"      {tf_key} Order Blocks: {len(tf_analysis.order_blocks)}")
    if hasattr(tf_analysis, 'fair_value_gaps') and tf_analysis.fair_value_gaps:
        print(f"      {tf_key} FVGs: {len(tf_analysis.fair_value_gaps)}")
print()

# ============================================================
# STEP 6: Signal Generation
# ============================================================
print("━" * 80)
print("🎯 STEP 6: Signal Generation")
print("━" * 80)

mtf_bias = mtf_result.overall_bias

# Determine recommended option
if mtf_bias == "bullish":
    recommended_type = "CALL"
    target_strike = chain.atm_strike + 50
elif mtf_bias == "bearish":
    recommended_type = "PUT"
    target_strike = chain.atm_strike - 50
else:
    # Neutral - use PCR to decide
    if chain.pcr_oi < 0.8:
        recommended_type = "CALL"
        target_strike = chain.atm_strike + 50
    elif chain.pcr_oi > 1.2:
        recommended_type = "PUT"
        target_strike = chain.atm_strike - 50
    else:
        recommended_type = "NEUTRAL"
        target_strike = chain.atm_strike

# Get strike data
strike_data = next((s for s in chain.strikes if s.strike == target_strike), None)
if not strike_data:
    strike_data = next((s for s in chain.strikes if s.strike == chain.atm_strike), None)
    target_strike = chain.atm_strike

if strike_data:
    if recommended_type == "CALL":
        entry_price = strike_data.call_ltp
        oi = strike_data.call_oi
        volume = strike_data.call_volume
        option_suffix = "CE"
    elif recommended_type == "PUT":
        entry_price = strike_data.put_ltp
        oi = strike_data.put_oi
        volume = strike_data.put_volume
        option_suffix = "PE"
    else:
        entry_price = 100
        oi = 0
        volume = 0
        option_suffix = "PE"
else:
    entry_price = 100
    oi = 0
    volume = 0
    option_suffix = "PE"

# Calculate targets (30% target, 30% SL)
target_1 = round(entry_price * 1.30)
target_2 = round(entry_price * 1.80)
stop_loss = round(entry_price * 0.70)

# Confidence
if mtf_bias in ["bullish", "bearish"]:
    confidence = 75
else:
    confidence = 50

# Build symbol
exp_date = datetime.strptime(chain.expiry_date, "%Y-%m-%d")
year_suffix = exp_date.strftime("%y")
month = exp_date.month
month_code = str(month) if month <= 9 else ("O" if month == 10 else "N" if month == 11 else "D")
day = exp_date.strftime("%d")
trading_symbol = f"NSE:NIFTY{year_suffix}{month_code}{day}{target_strike}{option_suffix}"

print()
print("╔" + "═" * 76 + "╗")
print("║" + " " * 28 + "🎯 TRADING SIGNAL" + " " * 31 + "║")
print("╠" + "═" * 76 + "╣")
print(f"║  Index: NIFTY" + " " * 62 + "║")
print(f"║  MTF Bias: {mtf_bias.upper():<64}║")
print(f"║  Recommendation: {'BUY ' + recommended_type if recommended_type != 'NEUTRAL' else 'WAIT':<58}║")
print("╠" + "═" * 76 + "╣")
print(f"║  Strike: {target_strike} {option_suffix}" + " " * 56 + "║")
print(f"║  Symbol: {trading_symbol:<65}║")
print(f"║  Expiry: {chain.expiry_date} ({chain.days_to_expiry} days)" + " " * 47 + "║")
print("╠" + "═" * 76 + "╣")
print(f"║  Entry Price: ₹{entry_price:<61.2f}║")
print(f"║  Target 1 (+30%): ₹{target_1:<56}║")
print(f"║  Target 2 (+80%): ₹{target_2:<56}║")
print(f"║  Stop Loss (-30%): ₹{stop_loss:<55}║")
print("╠" + "═" * 76 + "╣")
print(f"║  Volume: {volume:,}" + " " * (67 - len(f"{volume:,}")) + "║")
print(f"║  Open Interest: {oi:,}" + " " * (60 - len(f"{oi:,}")) + "║")
print(f"║  Confidence: {confidence}%" + " " * 61 + "║")
print("╠" + "═" * 76 + "╣")
print(f"║  Spot: ₹{chain.spot_price:,.2f} | PCR: {chain.pcr_oi:.2f} | Max Pain: {chain.max_pain} | IV: {chain.atm_iv:.1f}%" + " " * 10 + "║")
print("╚" + "═" * 76 + "╝")

# ============================================================
# SUMMARY
# ============================================================
print()
print("=" * 80)
print("✅ FULL SCAN COMPLETE - Data Collection Summary")
print("=" * 80)
print()
print("📋 DATA COLLECTED:")
print(f"   ✅ Spot Price: ₹{chain.spot_price:,.2f}")
print(f"   ✅ Futures Price: ₹{chain.future_price:,.2f}")
print(f"   ✅ Option Chain: {len(chain.strikes)} strikes analyzed")
print(f"   ✅ Calls: {len([s for s in chain.strikes if s.call_ltp > 0])} with valid LTP")
print(f"   ✅ Puts: {len([s for s in chain.strikes if s.put_ltp > 0])} with valid LTP")
print(f"   ✅ PCR (OI): {chain.pcr_oi:.3f}")
print(f"   ✅ PCR (Volume): {chain.pcr_volume:.3f}")
print(f"   ✅ Max Pain: {chain.max_pain}")
print(f"   ✅ ATM IV: {chain.atm_iv:.2f}%")
print(f"   ✅ MTF Analysis: {len(mtf_result.analyses)} timeframes")
print(f"   ✅ Overall Bias: {mtf_result.overall_bias.upper()}")
print(f"   ✅ Signal Generated: {'BUY ' + recommended_type if recommended_type != 'NEUTRAL' else 'WAIT'}")
print()
print("🎯 RECOMMENDED TRADE:")
print(f"   {trading_symbol}")
print(f"   Entry: ₹{entry_price:.2f} | Target: ₹{target_1} | SL: ₹{stop_loss}")
print()
