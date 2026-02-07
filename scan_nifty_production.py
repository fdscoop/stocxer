#!/usr/bin/env python3
"""
NIFTY Scan using Production API
Authenticates with Supabase and scans NIFTY via production backend
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
API_URL = os.getenv("TRADEWISE_API_URL", "https://stocxer-484044910258.europe-west1.run.app")
EMAIL = os.getenv("TEST_USER_EMAIL")
PASSWORD = os.getenv("TEST_USER_PASSWORD")

print("=" * 70)
print("🚀 NIFTY SCAN - Production API")
print("=" * 70)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"API URL: {API_URL}")
print()

# Step 1: Login
print("=" * 70)
print("🔐 STEP 1: Authentication")
print("=" * 70)
print(f"Email: {EMAIL}")

try:
    response = requests.post(
        f"{API_URL}/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        user = data.get("user", {})
        
        print(f"✅ Login successful!")
        print(f"   User ID: {user.get('id', 'N/A')}")
        print(f"   Email: {user.get('email', 'N/A')}")
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
        
except Exception as e:
    print(f"❌ Login error: {e}")
    exit(1)

# Step 2: Scan NIFTY
print()
print("=" * 70)
print("📊 STEP 2: Scanning NIFTY (All 50 Constituent Stocks)")
print("=" * 70)
print("🔍 Analyzing...")
print("   - Fetching live market data")
print("   - Scanning all 50 constituent stocks")
print("   - Calculating probabilities and signals")
print("   - Generating options recommendations")
print()

try:
    start_time = datetime.now()
    
    response = requests.get(
        f"{API_URL}/index/probability/NIFTY",
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "include_ml": True,
            "include_stocks": True,
            "include_sectors": True
        },
        timeout=120
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    if response.status_code == 200:
        result = response.json()
        
        print("=" * 70)
        print("✅ SCAN COMPLETE!")
        print("=" * 70)
        print(f"⏱️  Analysis time: {elapsed:.2f} seconds")
        print()
        
        # Index Prediction
        prediction = result.get("prediction", {})
        print("=" * 70)
        print("📈 INDEX PREDICTION")
        print("=" * 70)
        print(f"Current Level: {result.get('current_level', 0):,.2f}")
        print(f"Expected Direction: {prediction.get('expected_direction', 'N/A')}")
        print(f"Expected Move: {prediction.get('expected_move_pct', 0):+.3f}%")
        print(f"Expected Points: {prediction.get('expected_points', 0):+.2f}")
        print(f"Confidence: {prediction.get('confidence', 0):.1f}%")
        print()
        
        # Expected Range
        exp_range = prediction.get("expected_range", {})
        print(f"Expected Range:")
        print(f"  📈 High: {exp_range.get('high', 0):,.2f} (+{exp_range.get('points_up', 0):.0f} pts)")
        print(f"  📉 Low:  {exp_range.get('low', 0):,.2f} (-{exp_range.get('points_down', 0):.0f} pts)")
        print()
        
        # Probability Distribution
        print(f"Probability Distribution:")
        print(f"  📈 Bullish:  {prediction.get('probability_up', 0):.1%}")
        print(f"  📉 Bearish:  {prediction.get('probability_down', 0):.1%}")
        print(f"  ➡️  Neutral:  {prediction.get('probability_neutral', 0):.1%}")
        print()
        
        # Stock Summary
        summary = result.get("stock_summary", {})
        print("=" * 70)
        print("📊 STOCK SUMMARY")
        print("=" * 70)
        print(f"Total Stocks Analyzed: {summary.get('total_analyzed', 0)}")
        print(f"  🟢 Bullish: {summary.get('bullish', 0)} ({summary.get('bullish_pct', 0):.0f}%)")
        print(f"  🔴 Bearish: {summary.get('bearish', 0)} ({summary.get('bearish_pct', 0):.0f}%)")
        print(f"  ⚪ Neutral: {summary.get('neutral', 0)}")
        print()
        
        # Market Regime
        regime = result.get("regime", {})
        print("=" * 70)
        print("🌡️  MARKET REGIME")
        print("=" * 70)
        print(f"Type: {regime.get('type', 'N/A')}")
        print(f"ADX: {regime.get('adx', 0):.1f}")
        print(f"Volatility: {regime.get('volatility_level', 'N/A')}")
        print(f"Trend Strength: {regime.get('trend_strength', 0):.1f}%")
        print()
        
        # Top Bullish Contributors
        bullish = result.get("top_bullish_contributors", [])
        if bullish:
            print("=" * 70)
            print("🚀 TOP 5 BULLISH CONTRIBUTORS")
            print("=" * 70)
            for i, stock in enumerate(bullish[:5], 1):
                print(f"{i}. {stock.get('symbol', 'N/A'):12} | "
                      f"Weight: {stock.get('weight_pct', 0):5.2f}% | "
                      f"Move: {stock.get('expected_move', 0):+.2f}% | "
                      f"Prob: {stock.get('probability', 0):.0%} | "
                      f"Conf: {stock.get('confidence', 0):.0f}%")
            print()
        
        # Top Bearish Contributors
        bearish = result.get("top_bearish_contributors", [])
        if bearish:
            print("=" * 70)
            print("📉 TOP 5 BEARISH CONTRIBUTORS")
            print("=" * 70)
            for i, stock in enumerate(bearish[:5], 1):
                print(f"{i}. {stock.get('symbol', 'N/A'):12} | "
                      f"Weight: {stock.get('weight_pct', 0):5.2f}% | "
                      f"Move: {stock.get('expected_move', 0):+.2f}% | "
                      f"Prob: {stock.get('probability', 0):.0%} | "
                      f"Conf: {stock.get('confidence', 0):.0f}%")
            print()
        
        # Options Recommendation
        option_rec = result.get("option_recommendation", {})
        if option_rec:
            print("=" * 70)
            print("💡 OPTIONS RECOMMENDATION")
            print("=" * 70)
            print(f"Bias: {option_rec.get('bias', 'N/A')}")
            print(f"Recommended: {option_rec.get('recommended_option', 'N/A')}")
            print(f"ATM Strike: {option_rec.get('atm_strike', 0)}")
            print(f"Target Strike: {option_rec.get('target_strike', 0)}")
            print()
            
            strikes = option_rec.get("suggested_strikes", {})
            print(f"Suggested Strikes:")
            print(f"  🔥 Aggressive:   {strikes.get('aggressive', 0)}")
            print(f"  ⚖️  Moderate:     {strikes.get('moderate', 0)}")
            print(f"  🛡️  Conservative: {strikes.get('conservative', 0)}")
            print()
            
            print(f"Expected Target: {option_rec.get('expected_target', 0):,.2f}")
            print(f"Stop Loss: {option_rec.get('stop_loss_level', 0):,.2f}")
            print(f"Points to Target: {option_rec.get('points_to_target', 0):.0f}")
            print(f"Risk/Reward: {option_rec.get('risk_reward', 'N/A')}")
            print()
        
        # Sector Analysis
        sectors = result.get("sector_analysis", {})
        if sectors:
            print("=" * 70)
            print(f"🏢 SECTOR ANALYSIS ({len(sectors)} sectors)")
            print("=" * 70)
            for sector_name, sector_data in list(sectors.items())[:5]:
                signal = sector_data.get("signal", "N/A")
                conf = sector_data.get("confidence", 0)
                move = sector_data.get("expected_move", 0)
                print(f"{sector_name:25} | Signal: {signal:12} | Conf: {conf:5.1f}% | Move: {move:+7.2f}%")
            if len(sectors) > 5:
                print(f"... and {len(sectors) - 5} more sectors")
            print()
        
        # Final Summary
        print("=" * 70)
        print("✅ SCAN COMPLETE - All Data Collected Successfully")
        print("=" * 70)
        print()
        print("📋 Summary:")
        print(f"  • Scanned {summary.get('total_analyzed', 0)} constituent stocks")
        print(f"  • Generated {prediction.get('expected_direction', 'N/A')} prediction with {prediction.get('confidence', 0):.0f}% confidence")
        print(f"  • Recommended {option_rec.get('recommended_option', 'N/A')} options")
        print(f"  • Analyzed {len(sectors)} sectors")
        print(f"  • Analysis completed in {elapsed:.2f} seconds")
        print()
        
        # Save to file
        with open("nifty_scan_result_live.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"💾 Full result saved to: nifty_scan_result_live.json")
        print()
        
    else:
        print(f"❌ Scan failed: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        exit(1)
        
except Exception as e:
    print(f"❌ Scan error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
