#!/usr/bin/env python3
"""
Direct NIFTY scan without requiring backend server
Uses environment credentials to authenticate with Supabase and Fyers
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 70)
print("🚀 DIRECT NIFTY SCAN - Live Terminal Output")
print("=" * 70)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Import required modules
try:
    from src.api.fyers_client import FyersClient
    from src.analytics.index_probability_analyzer import IndexProbabilityAnalyzer
    from src.analytics.index_constituents import index_manager
    print("✅ Modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMake sure you're in the virtual environment:")
    print("  source .venv/bin/activate")
    sys.exit(1)

print()
print("=" * 70)
print("🔐 STEP 1: Initialize Fyers Client")
print("=" * 70)

# Get Fyers credentials from environment
fyers_client_id = os.getenv("FYERS_CLIENT_ID")
fyers_secret = os.getenv("FYERS_SECRET_KEY")

if not fyers_client_id or not fyers_secret:
    print("❌ Fyers credentials not found in .env file")
    sys.exit(1)

print(f"✅ Client ID: {fyers_client_id}")
print(f"✅ Secret Key: {'*' * 10}")

# Initialize Fyers client
fyers_client = FyersClient()
print("✅ Fyers client initialized")

print()
print("=" * 70)
print("📊 STEP 2: Scan NIFTY Constituent Stocks")
print("=" * 70)

# Get NIFTY constituents
constituents = index_manager.get_constituents("NIFTY")
print(f"✅ Found {len(constituents)} constituent stocks in NIFTY 50")
print()

# Initialize analyzer
analyzer = IndexProbabilityAnalyzer(fyers_client)
print("✅ Probability analyzer initialized")
print()

print("🔍 Starting constituent stock analysis...")
print("   This will scan all 50 stocks with live market data")
print()

# Perform analysis
try:
    start_time = datetime.now()
    prediction = analyzer.analyze_index("NIFTY")
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print()
    print("=" * 70)
    print("✅ SCAN COMPLETE!")
    print("=" * 70)
    print(f"⏱️  Analysis time: {elapsed:.2f} seconds")
    print()
    
    # Display results
    print("=" * 70)
    print("📈 INDEX PREDICTION")
    print("=" * 70)
    print(f"Current Level: {prediction.current_level:,.2f}")
    print(f"Expected Direction: {prediction.expected_direction}")
    print(f"Expected Move: {prediction.expected_move_pct:+.3f}%")
    print(f"Confidence: {prediction.prediction_confidence:.1f}%")
    print()
    print(f"Probability Distribution:")
    print(f"  📈 Bullish: {prediction.prob_up:.1%}")
    print(f"  📉 Bearish: {prediction.prob_down:.1%}")
    print(f"  ➡️  Neutral: {prediction.prob_neutral:.1%}")
    print()
    
    # Stock summary
    print("=" * 70)
    print("📊 STOCK SUMMARY")
    print("=" * 70)
    print(f"Total Stocks Analyzed: {prediction.total_stocks_analyzed}")
    print(f"  🟢 Bullish: {prediction.bullish_stocks} ({prediction.bullish_stocks/prediction.total_stocks_analyzed*100:.0f}%)")
    print(f"  🔴 Bearish: {prediction.bearish_stocks} ({prediction.bearish_stocks/prediction.total_stocks_analyzed*100:.0f}%)")
    print(f"  ⚪ Neutral: {prediction.neutral_stocks} ({prediction.neutral_stocks/prediction.total_stocks_analyzed*100:.0f}%)")
    print()
    
    # Market regime
    print("=" * 70)
    print("🌡️  MARKET REGIME")
    print("=" * 70)
    print(f"Type: {prediction.regime.regime.value}")
    print(f"ADX: {prediction.regime.adx_value:.1f}")
    print(f"Volatility: {prediction.regime.volatility_level}")
    print(f"Trend Strength: {prediction.regime.trend_strength:.1f}%")
    print()
    
    # Top contributors
    print("=" * 70)
    print("🚀 TOP 5 BULLISH CONTRIBUTORS")
    print("=" * 70)
    for i, stock in enumerate(prediction.top_bullish_contributors[:5], 1):
        symbol = stock.symbol.replace("NSE:", "").replace("-EQ", "")
        print(f"{i}. {symbol:12} | Weight: {stock.weight*100:5.2f}% | Move: {stock.expected_move_pct:+.2f}% | Prob: {stock.probability:.0%} | Conf: {stock.confidence_score:.0f}%")
    print()
    
    print("=" * 70)
    print("📉 TOP 5 BEARISH CONTRIBUTORS")
    print("=" * 70)
    for i, stock in enumerate(prediction.top_bearish_contributors[:5], 1):
        symbol = stock.symbol.replace("NSE:", "").replace("-EQ", "")
        print(f"{i}. {symbol:12} | Weight: {stock.weight*100:5.2f}% | Move: {stock.expected_move_pct:+.2f}% | Prob: {stock.probability:.0%} | Conf: {stock.confidence_score:.0f}%")
    print()
    
    # Options recommendation
    print("=" * 70)
    print("💡 OPTIONS RECOMMENDATION")
    print("=" * 70)
    
    current_level = prediction.current_level or 0
    expected_move_pct = prediction.expected_move_pct
    
    # Calculate strikes
    strike_interval = 50  # NIFTY uses 50-point strikes
    atm_strike = round(current_level / strike_interval) * strike_interval
    
    if prediction.expected_direction == "BULLISH":
        print(f"Recommended: CALL (CE) Options")
        print(f"ATM Strike: {atm_strike}")
        print(f"Suggested Strikes:")
        print(f"  🔥 Aggressive: {atm_strike} (ATM)")
        print(f"  ⚖️  Moderate: {atm_strike + strike_interval} (1 OTM)")
        print(f"  🛡️  Conservative: {atm_strike + strike_interval * 2} (2 OTM)")
    elif prediction.expected_direction == "BEARISH":
        print(f"Recommended: PUT (PE) Options")
        print(f"ATM Strike: {atm_strike}")
        print(f"Suggested Strikes:")
        print(f"  🔥 Aggressive: {atm_strike} (ATM)")
        print(f"  ⚖️  Moderate: {atm_strike - strike_interval} (1 OTM)")
        print(f"  🛡️  Conservative: {atm_strike - strike_interval * 2} (2 OTM)")
    else:
        print(f"Recommended: Range-bound strategies (Iron Condor/Strangle)")
        print(f"ATM Strike: {atm_strike}")
    
    print()
    print("=" * 70)
    print("✅ SCAN COMPLETE - All Data Collected Successfully")
    print("=" * 70)
    print()
    print("📋 Summary:")
    print(f"  • Scanned {prediction.total_stocks_analyzed} constituent stocks")
    print(f"  • Generated index prediction with {prediction.prediction_confidence:.0f}% confidence")
    print(f"  • Identified top bullish and bearish movers")
    print(f"  • Provided options recommendations (CE/PE)")
    print(f"  • Analysis completed in {elapsed:.2f} seconds")
    print()
    
except Exception as e:
    print()
    print("=" * 70)
    print("❌ SCAN FAILED")
    print("=" * 70)
    print(f"Error: {e}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
