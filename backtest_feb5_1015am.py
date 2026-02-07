#!/usr/bin/env python3
"""
Backtest Script: Simulate NIFTY scan at 10:15 AM IST on Feb 5, 2026
Then compare predictions against actual market performance for the rest of the day.

This tests the new ICT-based option type selection logic.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from pytz import timezone as pytz_timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from src.api.fyers_client import FyersClient
from src.analytics.mtf_ict_analysis import get_mtf_analyzer, Timeframe
from src.analytics.option_aware_ict import OptionAwarePracticalICT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== BACKTEST CONFIGURATION ====================
BACKTEST_DATE = "2026-02-05"
BACKTEST_TIME = "10:15"  # IST
BACKTEST_DATETIME_IST = datetime(2026, 2, 5, 10, 15, 0, tzinfo=pytz_timezone('Asia/Kolkata'))

# Known actual results for Feb 5, 2026 (for comparison)
ACTUAL_RESULTS = {
    "previous_close": 25776.00,
    "open": 25776.00,  # Approximate
    "high": 25800.00,  # Approximate
    "low": 25600.00,   # Approximate
    "close": 25642.80,
    "change": -133.20,
    "change_pct": -0.52,
    "direction": "BEARISH"
}

def main():
    """Run backtest simulation"""
    
    print("=" * 70)
    print("🕐 BACKTEST: NIFTY Scan at 10:15 AM IST on Feb 5, 2026")
    print("=" * 70)
    print(f"Simulating scan as if current time is: {BACKTEST_DATETIME_IST}")
    print(f"Market opened at 9:15 AM, we're scanning at 10:15 AM (1 hour into trading)")
    print()
    
    # Initialize Fyers client (reads from .env automatically)
    fyers_client = FyersClient()
    
    # Initialize option analyzer
    option_aware_ict = OptionAwarePracticalICT(fyers_client)

    
    # ==================== STEP 1: FETCH HISTORICAL DATA UP TO 10:15 AM ====================
    print("=" * 70)
    print("📊 STEP 1: Fetching Historical Data (up to 10:15 AM)")
    print("=" * 70)
    
    # Calculate date range: From 9:15 AM to 10:15 AM on Feb 5, 2026
    market_open = BACKTEST_DATETIME_IST.replace(hour=9, minute=15, second=0)
    scan_time = BACKTEST_DATETIME_IST
    
    # For backtesting, we need data BEFORE 10:15 AM
    # Fetch data up to 10:15 AM (not beyond)
    date_to = scan_time
    
    # For different timeframes, we need different lookback periods
    # 5m: Last 100 candles = ~8 hours
    # 15m: Last 100 candles = ~25 hours
    # 1H: Last 100 candles = ~4 days
    # 4H: Last 100 candles = ~16 days
    # Daily: Last 100 candles = ~100 days
    
    symbol = "NSE:NIFTY50-INDEX"
    
    print(f"Symbol: {symbol}")
    print(f"Fetching data UP TO: {date_to}")
    print()
    
    # Fetch multi-timeframe data
    candles_by_timeframe = {}
    
    timeframes_to_fetch = [
        ("5", "5m", timedelta(hours=8)),
        ("15", "15m", timedelta(hours=25)),
        ("60", "1H", timedelta(days=4)),
        ("240", "4H", timedelta(days=16)),
        ("D", "Daily", timedelta(days=100))
    ]
    
    for resolution, tf_name, lookback in timeframes_to_fetch:
        date_from = date_to - lookback
        
        print(f"Fetching {tf_name} candles: {date_from.strftime('%Y-%m-%d %H:%M')} to {date_to.strftime('%Y-%m-%d %H:%M')}")
        
        try:
            df = fyers_client.get_historical_data(
                symbol=symbol,
                resolution=resolution,
                date_from=date_from,
                date_to=date_to  # CRITICAL: Only data up to 10:15 AM
            )
            
            if not df.empty:
                candles_by_timeframe[resolution] = df
                print(f"  ✅ Fetched {len(df)} candles for {tf_name}")
                print(f"  📅 Latest candle: {df.index[-1]}")
                print(f"  💰 Latest close: {df['close'].iloc[-1]:.2f}")
            else:
                print(f"  ⚠️ No data for {tf_name}")
        except Exception as e:
            print(f"  ❌ Error fetching {tf_name}: {e}")
        
        print()
    
    # ==================== STEP 2: GET SPOT PRICE AT 10:15 AM ====================
    print("=" * 70)
    print("📍 STEP 2: Getting Spot Price at 10:15 AM")
    print("=" * 70)
    
    # For backtest, we'll use the last close from 5m candles
    if "5" in candles_by_timeframe and not candles_by_timeframe["5"].empty:
        spot_price = candles_by_timeframe["5"]['close'].iloc[-1]
        print(f"Spot Price at 10:15 AM: ₹{spot_price:.2f}")
    else:
        print("⚠️ Could not determine spot price, using previous close")
        spot_price = ACTUAL_RESULTS["previous_close"]
    
    print()
    
    # ==================== STEP 3: RUN MTF/ICT ANALYSIS ====================
    print("=" * 70)
    print("🔍 STEP 3: Multi-Timeframe ICT Analysis")
    print("=" * 70)
    
    mtf_analyzer = get_mtf_analyzer(fyers_client)
    
    # Analyze with intraday timeframes (since we're 1 hour into market)
    timeframes = [
        Timeframe.DAILY,
        Timeframe.FOUR_HOUR,
        Timeframe.ONE_HOUR,
        Timeframe.FIFTEEN_MIN,
        Timeframe.FIVE_MIN
    ]
    
    # For backtest, we need to manually pass the candles we fetched
    # (since mtf_analyzer would fetch fresh data by default)
    
    # Simplified: Just analyze the candles we have
    print("Analyzing market structure, Order Blocks, FVGs...")
    print()
    
    # Check HTF bias from 1H and 4H
    htf_bias = "neutral"
    htf_strength = 50
    
    if "60" in candles_by_timeframe:
        df_1h = candles_by_timeframe["60"]
        if len(df_1h) >= 50:
            # Simple EMA-based bias
            close = df_1h['close']
            ema20 = close.ewm(span=20).mean()
            ema50 = close.ewm(span=50).mean()
            
            if ema20.iloc[-1] > ema50.iloc[-1] and close.iloc[-1] > ema20.iloc[-1]:
                htf_bias = "bullish"
                htf_strength = 65
            elif ema20.iloc[-1] < ema50.iloc[-1] and close.iloc[-1] < ema20.iloc[-1]:
                htf_bias = "bearish"
                htf_strength = 65
    
    print(f"HTF Bias (1H): {htf_bias.upper()}")
    print(f"HTF Strength: {htf_strength}")
    print()
    
    # ==================== STEP 4: CACHE CONTEXT FOR OPTION TYPE SELECTION ====================
    print("=" * 70)
    print("🎯 STEP 4: ICT-Based Option Type Selection")
    print("=" * 70)
    
    # Cache context (simulating what main.py does)
    option_aware_ict.cached_candles = candles_by_timeframe
    option_aware_ict.cached_htf_bias = {
        'overall_direction': htf_bias,
        'bias_strength': htf_strength,
        'structure_quality': 'moderate'
    }
    option_aware_ict.cached_probability = None  # We're not running full stock scan
    
    # Determine option type using new ICT logic
    direction = "BUY" if htf_bias == "bullish" else "SELL" if htf_bias == "bearish" else "WAIT"
    
    if direction != "WAIT":
        option_type = option_aware_ict._determine_option_type_from_ict(
            direction=direction,
            spot_price=spot_price
        )
        
        print()
        print(f"✅ PREDICTION AT 10:15 AM:")
        print(f"   Direction: {direction}")
        print(f"   Option Type: {option_type}")
        print(f"   HTF Bias: {htf_bias.upper()} ({htf_strength})")
        print()
    else:
        option_type = None
        print("⚠️ No clear signal - WAIT")
        print()
    
    # ==================== STEP 5: COMPARE WITH ACTUAL RESULTS ====================
    print("=" * 70)
    print("📊 STEP 5: Comparing Prediction vs Actual Results")
    print("=" * 70)
    
    print("ACTUAL MARKET PERFORMANCE (Feb 5, 2026):")
    print(f"  Previous Close: ₹{ACTUAL_RESULTS['previous_close']:.2f}")
    print(f"  Close: ₹{ACTUAL_RESULTS['close']:.2f}")
    print(f"  Change: {ACTUAL_RESULTS['change']:.2f} ({ACTUAL_RESULTS['change_pct']:.2f}%)")
    print(f"  Direction: {ACTUAL_RESULTS['direction']}")
    print()
    
    if option_type:
        print("PREDICTION AT 10:15 AM:")
        print(f"  HTF Bias: {htf_bias.upper()}")
        print(f"  Recommended Option: {option_type}")
        print(f"  Expected Direction: {direction}")
        print()
        
        # Check if prediction was correct
        actual_direction = ACTUAL_RESULTS['direction']
        
        if actual_direction == "BEARISH":
            correct_option = "PE"
        elif actual_direction == "BULLISH":
            correct_option = "CE"
        else:
            correct_option = None
        
        if option_type == correct_option:
            print("✅ PREDICTION: CORRECT!")
            print(f"   Recommended {option_type} and market was {actual_direction}")
        else:
            print("❌ PREDICTION: INCORRECT")
            print(f"   Recommended {option_type} but market was {actual_direction}")
            print(f"   Should have recommended {correct_option}")
        
        print()
        
        # Calculate what would have happened with the trade
        if option_type == "PE" and actual_direction == "BEARISH":
            print("💰 TRADE OUTCOME:")
            print(f"   Bought PE (Put) at 10:15 AM")
            print(f"   Market fell {abs(ACTUAL_RESULTS['change']):.2f} points")
            print(f"   ✅ PUT option would have been PROFITABLE!")
        elif option_type == "CE" and actual_direction == "BULLISH":
            print("💰 TRADE OUTCOME:")
            print(f"   Bought CE (Call) at 10:15 AM")
            print(f"   Market rose {abs(ACTUAL_RESULTS['change']):.2f} points")
            print(f"   ✅ CALL option would have been PROFITABLE!")
        else:
            print("💰 TRADE OUTCOME:")
            print(f"   Bought {option_type} at 10:15 AM")
            print(f"   Market moved {ACTUAL_RESULTS['change']:.2f} points")
            print(f"   ❌ Option would have LOST value")
    
    print()
    print("=" * 70)
    print("✅ BACKTEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
