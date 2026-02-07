#!/usr/bin/env python3
"""
Test NIFTY scan as user would from frontend - testing both expiries
"""
import requests
import json
import sys

API_URL = "http://localhost:8000"

def test_scan(expiry_type, description):
    print("\n" + "=" * 70)
    print(f"🧪 TEST: {description}")
    print(f"   Expiry Type: {expiry_type}")
    print("=" * 70)
    
    try:
        # Call actionable signal endpoint (as frontend does)
        url = f"{API_URL}/signals/NIFTY/actionable?expiry={expiry_type}"
        print(f"\n📡 Calling: {url}")
        
        response = requests.get(url, timeout=120)
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text[:500])
            return
        
        data = response.json()
        
        # Extract key info
        print("\n📊 RESULTS:")
        print(f"   Signal: {data.get('signal', 'N/A')}")
        print(f"   Action: {data.get('action', 'N/A')}")
        print(f"   Is Expiry Day: {data.get('is_expiry_day', 'N/A')}")
        
        opt = data.get('option', {})
        print(f"\n📅 EXPIRY INFO:")
        print(f"   Expiry Date: {opt.get('expiry_date', 'N/A')}")
        expiry_info = opt.get('expiry_info', {})
        print(f"   Days to Expiry: {expiry_info.get('days_to_expiry', 'N/A')}")
        print(f"   Is Weekly: {expiry_info.get('is_weekly', 'N/A')}")
        
        print(f"\n📈 OPTION:")
        print(f"   Type: {opt.get('type', 'N/A')}")
        print(f"   Strike: {opt.get('strike', 'N/A')}")
        print(f"   Symbol: {opt.get('trading_symbol', 'N/A')}")
        
        pricing = data.get('pricing', {})
        print(f"\n💰 PRICING:")
        print(f"   LTP: ₹{pricing.get('ltp', 'N/A')}")
        print(f"   Entry Price: ₹{pricing.get('entry_price', 'N/A')}")
        
        # HTF Analysis
        htf = data.get('htf_analysis', {})
        print(f"\n📊 HTF ANALYSIS:")
        print(f"   Direction: {htf.get('direction', 'N/A')}")
        print(f"   Strength: {htf.get('strength', 'N/A')}")
        
        # Confidence
        conf = data.get('confidence', {})
        print(f"\n🎯 CONFIDENCE:")
        print(f"   Score: {conf.get('score', 'N/A')}")
        print(f"   Level: {conf.get('level', 'N/A')}")
        
        # Warnings (IMPORTANT!)
        warnings = data.get('warnings', [])
        if warnings:
            print(f"\n⚠️ WARNINGS ({len(warnings)}):")
            for w in warnings:
                print(f"   🔸 {w}")
        else:
            print("\n✅ No warnings")
            
        # Trading mode
        tm = data.get('trading_mode', {})
        print(f"\n📌 TRADING MODE:")
        print(f"   Mode: {tm.get('mode', 'N/A')}")
        print(f"   DTE: {tm.get('dte', 'N/A')}")
        print(f"   Description: {tm.get('description', 'N/A')}")
        
        return data
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (120s)")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("\n" + "🔷" * 35)
    print("   NIFTY OPTIONS SCAN - USER FLOW TEST")
    print("   Testing expiry selection behavior")
    print("🔷" * 35)
    
    # Test 1: Weekly expiry (should be expiry day with warnings)
    result1 = test_scan("weekly", "WEEKLY EXPIRY (Feb 3 - Should be Expiry Day)")
    
    # Wait a bit to avoid rate limiting
    import time
    print("\n⏳ Waiting 5 seconds before next test...")
    time.sleep(5)
    
    # Test 2: Next weekly expiry (should NOT be expiry day)
    result2 = test_scan("next_weekly", "NEXT WEEKLY EXPIRY (Feb 10 - Should be 8 DTE)")
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    
    if result1:
        dte1 = result1.get('option', {}).get('expiry_info', {}).get('days_to_expiry', 'N/A')
        is_exp1 = result1.get('is_expiry_day', 'N/A')
        warn1 = len(result1.get('warnings', []))
        print(f"Weekly:      DTE={dte1}, Is Expiry Day={is_exp1}, Warnings={warn1}")
    
    if result2:
        dte2 = result2.get('option', {}).get('expiry_info', {}).get('days_to_expiry', 'N/A')
        is_exp2 = result2.get('is_expiry_day', 'N/A')
        warn2 = len(result2.get('warnings', []))
        print(f"Next Weekly: DTE={dte2}, Is Expiry Day={is_exp2}, Warnings={warn2}")
    
    print("\n✅ Test complete!")
