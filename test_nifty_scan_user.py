#!/usr/bin/env python3
"""
Test NIFTY scan as a user from dashboard.
Simulates what happens when user clicks "Scan NIFTY" button.
"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.insert(0, '.')
load_dotenv()

# Get auth token
from config.supabase_config import supabase_admin

print("=" * 70)
print("🔍 Testing NIFTY Scan as User (Dashboard Flow)")
print("=" * 70)

# Authenticate
email = os.getenv('TEST_USER_EMAIL')
password = os.getenv('TEST_USER_PASSWORD')

print(f"\n1️⃣ Authenticating as: {email}")
try:
    auth_response = supabase_admin.auth.sign_in_with_password({
        'email': email,
        'password': password
    })
    token = auth_response.session.access_token
    print("   ✅ Authentication successful")
except Exception as e:
    print(f"   ❌ Authentication failed: {e}")
    sys.exit(1)

# Make scan request
print("\n2️⃣ Scanning NIFTY options (FULL mode with signal generation)...")
url = "http://localhost:8000/options/scan"
params = {
    'index': 'NIFTY',
    'expiry': 'weekly',
    'min_volume': 100,
    'min_oi': 1000,
    'strategy': 'all',
    'include_probability': 'true',
    'quick_scan': 'false'  # Force full scan with signal generation
}
headers = {
    'Authorization': f'Bearer {token}'
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=60)
    response.raise_for_status()
    data = response.json()
    print("   ✅ Scan completed successfully")
except Exception as e:
    print(f"   ❌ Scan failed: {e}")
    sys.exit(1)

# Parse results
print("\n" + "=" * 70)
print("📊 SCAN RESULTS")
print("=" * 70)

print(f"\n📋 Basic Info:")
print(f"   Status: {data.get('status')}")
print(f"   Scan Mode: {data.get('scan_mode')}")
print(f"   Total Options: {data.get('total_options')}")
print(f"   Data Source: {data.get('data_source')}")

# Market data
md = data.get('market_data', {})
print(f"\n📈 Market Data:")
print(f"   Spot Price: ₹{md.get('spot_price', 'N/A')}")
print(f"   Day Change: {md.get('day_change_pct', 0):.2f}%")
print(f"   ATM Strike: {md.get('atm_strike', 'N/A')}")
print(f"   VIX: {md.get('vix', 'N/A')}")

# Probability analysis
pa = data.get('probability_analysis') or {}
print(f"\n🎯 Probability Analysis:")
print(f"   Direction: {pa.get('direction', 'N/A')}")
print(f"   Probability: {(pa.get('probability') or 0)*100:.1f}%")
print(f"   Confidence: {(pa.get('confidence') or 0)*100:.1f}%")

# MTF ICT Analysis
mtf = data.get('mtf_ict_analysis') or {}
print(f"\n📊 MTF ICT Analysis:")
print(f"   Direction: {mtf.get('direction', 'N/A')}")
print(f"   Confidence: {(mtf.get('confidence') or 0)*100:.1f}%")
print(f"   Signal Strength: {mtf.get('signal_strength', 'N/A')}")
print(f"   Trade Recommendation: {mtf.get('trade_recommendation', 'N/A')}")

# Check for actionable signal
print("\n" + "=" * 70)
if 'actionable_signal' in data and data['actionable_signal']:
    sig = data['actionable_signal']
    print("🚀 ACTIONABLE SIGNAL FOUND!")
    print("=" * 70)
    print(f"   Type: {sig.get('type', 'N/A')}")
    print(f"   Strike: {sig.get('strike', 'N/A')}")
    print(f"   Premium: ₹{sig.get('premium', 'N/A')}")
    print(f"   Confidence: {sig.get('confidence', 'N/A')}")
    print(f"   Strategy: {sig.get('strategy', 'N/A')}")
    
    # Check for enhanced ML prediction
    if 'enhanced_ml_prediction' in sig:
        ml = sig['enhanced_ml_prediction']
        print("\n🧠 Enhanced ML Prediction:")
        
        # Direction
        dir_pred = ml.get('direction_prediction', {})
        print(f"   📈 Direction: {dir_pred.get('direction', 'N/A')} ({dir_pred.get('confidence', 0)*100:.0f}% conf)")
        
        # Speed
        speed_pred = ml.get('speed_prediction', {})
        print(f"   ⚡ Speed: {speed_pred.get('category', 'N/A')} ({speed_pred.get('confidence', 0)*100:.0f}% conf)")
        
        # IV
        iv_pred = ml.get('iv_prediction', {})
        print(f"   📊 IV Direction: {iv_pred.get('direction', 'N/A')} ({iv_pred.get('expected_iv_change_pct', 0):+.1f}%)")
        
        # Simulation
        sim = ml.get('simulation', {})
        if sim:
            print(f"\n   💰 Trade Simulation:")
            print(f"      Grade: {sim.get('grade', 'N/A')}")
            print(f"      Win Probability: {sim.get('win_probability', 0)*100:.1f}%")
            print(f"      Expected P&L: {sim.get('expected_pnl_pct', 0):+.1f}%")
            print(f"      Should Trade: {'✅ YES' if sim.get('should_trade') else '❌ NO'}")
            print(f"      Stop Loss: ₹{sim.get('stop_loss', 'N/A')}")
            print(f"      Take Profit: ₹{sim.get('take_profit', 'N/A')}")
        
        # Combined recommendation
        combined = ml.get('combined_recommendation', {})
        if combined:
            print(f"\n   📋 Combined Recommendation:")
            print(f"      Action: {combined.get('action', 'N/A')}")
            print(f"      Confidence: {combined.get('confidence', 0)*100:.0f}%")
            for warning in combined.get('warnings', [])[:3]:
                print(f"      ⚠️ {warning}")
    else:
        print("\n   ⚠️ No enhanced ML prediction in signal")
else:
    print("📭 NO ACTIONABLE SIGNAL")
    print("=" * 70)
    print("   Reason: No strong setup found or market conditions not favorable")
    print("   This can happen when:")
    print("   - Market is closed (weekends/holidays)")
    print("   - No clear directional bias")
    print("   - Volume/OI filters too strict")

# Show top options if available
options = data.get('options', [])
if options:
    print(f"\n📋 Top {min(5, len(options))} Options Found:")
    for i, opt in enumerate(options[:5], 1):
        print(f"   {i}. {opt.get('strike')} {opt.get('option_type')} @ ₹{opt.get('ltp', 'N/A')}")
        print(f"      Volume: {opt.get('volume', 'N/A'):,} | OI: {opt.get('oi', 'N/A'):,}")

print("\n" + "=" * 70)
print("✅ Test completed!")
print("=" * 70)
