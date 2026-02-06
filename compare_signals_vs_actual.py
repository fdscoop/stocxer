#!/usr/bin/env python3
"""
Compare ML Signal Predictions vs Actual NIFTY Performance
Analyzes today's signals from database and compares with actual market movement
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

print("=" * 70)
print("📊 ML SIGNAL ACCURACY ANALYSIS")
print("=" * 70)
print(f"⏰ Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
print()

# Connect to Supabase
print("Step 1: Connecting to database...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Connected to Supabase")
print()

# Get today's date range (IST)
today = datetime.now().date()
today_start = datetime.combine(today, datetime.min.time())
today_end = datetime.combine(today, datetime.max.time())

print(f"📅 Analyzing signals for: {today.strftime('%Y-%m-%d')}")
print()

# Query signals from database
print("Step 2: Fetching today's option scanner results from database...")
try:
    # Query the option_scanner_results table
    response = supabase.table("option_scanner_results").select("*").gte("created_at", today_start.isoformat()).lte("created_at", today_end.isoformat()).order("created_at", desc=False).execute()
    
    signals = response.data
    print(f"✅ Found {len(signals)} option scanner results for today")
    print()
    
    if not signals:
        print("⚠️  No results found for today")
        print("   Checking recent results from past 7 days...")
        
        week_ago = today_start - timedelta(days=7)
        response = supabase.table("option_scanner_results").select("*").gte("created_at", week_ago.isoformat()).order("created_at", desc=False).limit(20).execute()
        
        signals = response.data
        print(f"✅ Found {len(signals)} results in past 7 days")
        print()
    
    # Get actual NIFTY data
    print("Step 3: Fetching actual NIFTY price data...")
    from src.api.fyers_client import fyers_client
    
    # Get current quote
    quote_response = fyers_client.get_quotes(["NSE:NIFTY50-INDEX"])
    
    if quote_response and quote_response.get("d"):
        nifty_data = quote_response["d"][0]["v"]
        current_price = nifty_data.get("lp", 0)  # Last price
        open_price = nifty_data.get("open_price", 0)
        high_price = nifty_data.get("high_price", 0)
        low_price = nifty_data.get("low_price", 0)
        prev_close = nifty_data.get("prev_close_price", 0)
        
        # Calculate actual movement
        if prev_close > 0:
            actual_change_pct = ((current_price - prev_close) / prev_close) * 100
            actual_points = current_price - prev_close
        else:
            actual_change_pct = 0
            actual_points = 0
        
        print("✅ NIFTY Actual Performance Today:")
        print(f"   Previous Close: {prev_close:,.2f}")
        print(f"   Open: {open_price:,.2f}")
        print(f"   High: {high_price:,.2f}")
        print(f"   Low: {low_price:,.2f}")
        print(f"   Current/Close: {current_price:,.2f}")
        print(f"   Change: {actual_points:+.2f} ({actual_change_pct:+.2f}%)")
        
        # Determine actual direction
        if actual_change_pct > 0.1:
            actual_direction = "BULLISH"
        elif actual_change_pct < -0.1:
            actual_direction = "BEARISH"
        else:
            actual_direction = "NEUTRAL"
        
        print(f"   Direction: {actual_direction}")
        print()
        
        # Analyze each signal
        print("=" * 70)
        print("📈 SIGNAL vs ACTUAL COMPARISON")
        print("=" * 70)
        print()
        
        correct_predictions = 0
        total_predictions = 0
        
        for idx, signal in enumerate(signals, 1):
            signal_time = datetime.fromisoformat(signal["created_at"].replace("Z", "+00:00"))
            
            # Extract prediction data from option_scanner_results
            index_name = signal.get("index", "N/A")
            signal_type = signal.get("signal", "N/A")
            action = signal.get("action", "N/A")
            confidence = signal.get("confidence", 0)
            htf_direction = signal.get("htf_direction", "neutral")
            option_type = signal.get("option_type", "N/A")
            strike = signal.get("strike", 0)
            entry_price = signal.get("entry_price", 0)
            target_1 = signal.get("target_1", 0)
            target_2 = signal.get("target_2", 0)
            stop_loss = signal.get("stop_loss", 0)
            spot_price = signal.get("spot_price", 0)
            
            # Filter for NIFTY only
            if index_name != "NIFTY":
                continue
            
            # Determine predicted direction from signal
            predicted_direction = "NEUTRAL"
            if "BULLISH" in signal_type.upper() or htf_direction == "bullish" or option_type == "CE":
                predicted_direction = "BULLISH"
            elif "BEARISH" in signal_type.upper() or htf_direction == "bearish" or option_type == "PE":
                predicted_direction = "BEARISH"
            elif action == "WAIT" or "NEUTRAL" in signal_type.upper():
                predicted_direction = "NEUTRAL"
            
            # Check if prediction was correct
            prediction_correct = False
            if predicted_direction == actual_direction:
                prediction_correct = True
                correct_predictions += 1
            elif predicted_direction == "NEUTRAL" and abs(actual_change_pct) < 0.2:
                prediction_correct = True
                correct_predictions += 1
            
            total_predictions += 1
            
            # Display comparison
            print(f"Signal #{total_predictions} - {signal_time.strftime('%H:%M:%S')}")
            print(f"  Signal Type: {signal_type}")
            print(f"  Action: {action}")
            print(f"  Predicted Direction: {predicted_direction} (HTF: {htf_direction})")
            print(f"  Actual Direction: {actual_direction} ({actual_change_pct:+.2f}%, {actual_points:+.0f} pts)")
            print(f"  Confidence: {confidence:.1f}%")
            print(f"  Result: {'✅ CORRECT' if prediction_correct else '❌ INCORRECT'}")
            print()
            
            # Option analysis
            print(f"  Option Recommended: {option_type} {strike:.0f}")
            print(f"  Entry: ₹{entry_price:.2f} | Target 1: ₹{target_1:.2f} | Target 2: ₹{target_2:.2f} | SL: ₹{stop_loss:.2f}")
            
            # Check if option would have been profitable
            option_profitable = False
            if option_type == "CE" and actual_direction == "BULLISH":
                option_profitable = True
                print(f"  Option Result: ✅ Would likely be profitable (market moved up {abs(actual_change_pct):.2f}%)")
            elif option_type == "PE" and actual_direction == "BEARISH":
                option_profitable = True
                print(f"  Option Result: ✅ Would likely be profitable (market moved down {abs(actual_change_pct):.2f}%)")
            elif option_type == "CE" and actual_direction == "BEARISH":
                print(f"  Option Result: ❌ Would likely be unprofitable (bought CE but market fell)")
            elif option_type == "PE" and actual_direction == "BULLISH":
                print(f"  Option Result: ❌ Would likely be unprofitable (bought PE but market rose)")
            else:
                print(f"  Option Result: ⚠️  Neutral/Unclear (market moved {actual_change_pct:+.2f}%)")
            
            print()

        
        # Summary
        print("=" * 70)
        print("📊 ACCURACY SUMMARY")
        print("=" * 70)
        
        if total_predictions > 0:
            accuracy = (correct_predictions / total_predictions) * 100
            print(f"Total Signals Analyzed: {total_predictions}")
            print(f"Correct Predictions: {correct_predictions}")
            print(f"Incorrect Predictions: {total_predictions - correct_predictions}")
            print(f"Accuracy Rate: {accuracy:.1f}%")
            print()
            
            if accuracy >= 70:
                print("✅ EXCELLENT: Model predictions are highly accurate!")
            elif accuracy >= 50:
                print("✅ GOOD: Model predictions are reasonably accurate")
            else:
                print("⚠️  NEEDS IMPROVEMENT: Model accuracy could be better")
        else:
            print("No predictions to analyze")
        
        print()
        
    else:
        print("❌ Failed to fetch NIFTY price data")
        print("   Cannot compare with actual performance")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 70)
print("✅ Analysis Complete")
print("=" * 70)
