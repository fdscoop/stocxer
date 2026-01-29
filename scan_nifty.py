#!/usr/bin/env python3
"""
Quick NIFTY scan through terminal
Tests the local backend API at localhost:8000
"""

import requests
import json
from datetime import datetime, timedelta

# API endpoint
BASE_URL = "http://localhost:8000"

def scan_nifty():
    """Perform a NIFTY scan"""
    print("=" * 70)
    print("🚀 SCANNING NIFTY - Terminal Test")
    print("=" * 70)
    print()
    
    # Calculate next expiry (Thursday)
    today = datetime.now()
    days_ahead = 3 - today.weekday()  # Thursday is 3
    if days_ahead <= 0:
        days_ahead += 7
    next_expiry = today + timedelta(days=days_ahead)
    expiry_date = next_expiry.strftime("%Y-%m-%d")
    
    print(f"📅 Target Expiry: {expiry_date}")
    print(f"🔍 Scanning NIFTY...")
    print()
    
    # Make API request to NIFTY probability analysis endpoint
    try:
        response = requests.get(
            f"{BASE_URL}/index/probability/NIFTY",
            params={
                "include_ml": True,
                "include_stocks": True,
                "include_sectors": True
            },
            timeout=90
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ SCAN COMPLETE")
            print("=" * 70)
            
            # Display signal
            signal = result.get("signal", {})
            print(f"\n📊 SIGNAL: {signal.get('action', 'N/A')}")
            print(f"   Type: {signal.get('signal', 'N/A')}")
            
            # Option details
            option = signal.get("option", {})
            print(f"\n🎯 OPTION:")
            print(f"   Strike: {option.get('strike', 'N/A')}")
            print(f"   Type: {option.get('type', 'N/A')}")
            print(f"   Symbol: {option.get('symbol', 'N/A')}")
            
            # Pricing
            pricing = signal.get("pricing", {})
            print(f"\n💰 PRICING:")
            print(f"   LTP: ₹{pricing.get('ltp', 'N/A')}")
            print(f"   Entry Price: ₹{pricing.get('entry_price', 'N/A')}")
            print(f"   Source: {pricing.get('price_source', 'N/A')}")
            
            # Entry details
            entry = signal.get("entry", {})
            print(f"\n📍 ENTRY:")
            print(f"   Best Entry: ₹{entry.get('best_entry_price', 'N/A')}")
            print(f"   Max Entry: ₹{entry.get('max_entry_price', 'N/A')}")
            print(f"   Timing: {entry.get('timing', 'N/A')}")
            
            # Targets
            targets = signal.get("targets", {})
            print(f"\n🎯 TARGETS:")
            print(f"   Target 1: ₹{targets.get('target_1', 'N/A')}")
            print(f"   Target 2: ₹{targets.get('target_2', 'N/A')}")
            print(f"   Stop Loss: ₹{targets.get('stop_loss', 'N/A')}")
            
            # Confidence
            confidence = signal.get("confidence", {})
            print(f"\n📈 CONFIDENCE:")
            print(f"   Score: {confidence.get('score', 'N/A')}/100")
            print(f"   Level: {confidence.get('level', 'N/A')}")
            
            # Analysis  
            analysis = result.get("analysis", {})
            print(f"\n🔍 ANALYSIS:")
            print(f"   HTF Bias: {analysis.get('overall_bias', 'N/A')}")
            print(f"   Spot Price: ₹{analysis.get('spot_price', 'N/A')}")
            
            # Save full result to file
            with open("nifty_scan_result.json", "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Full result saved to: nifty_scan_result.json")
            
        else:
            print(f"❌ Scan failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend at localhost:8000")
        print("   Make sure the backend server is running:")
        print("   → cd /Users/bineshbalan/TradeWise")
        print("   → python -m uvicorn main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    scan_nifty()
