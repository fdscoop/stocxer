#!/usr/bin/env python3
"""Test the integrated options scanner with probability analysis"""

import requests
import json
import time
from supabase import create_client
from config.settings import settings

def get_auth_token():
    """Get a valid auth token"""
    supabase = create_client(settings.supabase_url, settings.supabase_key)
    
    email = f'test{int(time.time())}@tradewise.app'
    password = 'test123456'
    
    try:
        response = supabase.auth.sign_up({
            'email': email,
            'password': password
        })
        
        if response.session:
            return response.session.access_token
        else:
            login_resp = supabase.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            return login_resp.session.access_token
    except Exception as e:
        print(f"Auth error: {e}")
        return None

def test_scanner():
    """Test the integrated scanner"""
    print("="*70)
    print("🎯 TESTING INTEGRATED OPTIONS SCANNER")
    print("="*70)
    
    # Get auth token
    print("\n1. Getting auth token...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    print(f"✅ Got token: {token[:30]}...")
    
    # Test BANKNIFTY (14 stocks - faster)
    print("\n2. Testing BANKNIFTY options scan with probability analysis...")
    print("   (This scans all 14 bank stocks + options chain)")
    
    url = "http://localhost:8000/options/scan"
    params = {
        "index": "BANKNIFTY",
        "expiry": "weekly",
        "min_volume": 1000,
        "min_oi": 10000,
        "include_probability": "true"
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=120)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return
        
        data = response.json()
        
        print("\n" + "="*70)
        print("📊 SCAN RESULTS")
        print("="*70)
        print(f"Index: {data.get('index')}")
        print(f"Data Source: {data.get('data_source')}")
        print(f"Scan Time: {data.get('scan_time')}")
        
        # Probability Analysis
        prob = data.get('probability_analysis')
        if prob and not prob.get('error'):
            print("\n" + "="*70)
            print("📈 CONSTITUENT STOCK ANALYSIS")
            print("="*70)
            print(f"  ✅ Stocks Scanned: {prob.get('stocks_scanned')}/{prob.get('total_stocks')}")
            print(f"  📊 Expected Direction: {prob.get('expected_direction')}")
            print(f"  📈 Expected Move: {prob.get('expected_move_pct')}%")
            print(f"  🎯 Confidence: {prob.get('confidence')}%")
            print(f"  🟢 Probability UP: {prob.get('probability_up', 0) * 100:.1f}%")
            print(f"  🔴 Probability DOWN: {prob.get('probability_down', 0) * 100:.1f}%")
            print(f"  📊 Bullish Stocks: {prob.get('bullish_stocks')} ({prob.get('bullish_pct')}%)")
            print(f"  📉 Bearish Stocks: {prob.get('bearish_stocks')} ({prob.get('bearish_pct')}%)")
            print(f"  📈 Market Regime: {prob.get('market_regime')}")
            print(f"\n  ⭐ RECOMMENDED: {data.get('recommended_option_type')} OPTIONS")
            
            # Top stocks
            print("\n  🚀 Top Bullish Stocks:")
            for s in prob.get('top_bullish_stocks', [])[:3]:
                print(f"     • {s['symbol']}: {s['probability']*100:.0f}% ({s['expected_move']:+.1f}%)")
            
            print("\n  📉 Top Bearish Stocks:")
            for s in prob.get('top_bearish_stocks', [])[:3]:
                print(f"     • {s['symbol']}: {s['probability']*100:.0f}% ({s['expected_move']:+.1f}%)")
            
            if prob.get('volume_surge_stocks'):
                print("\n  🔥 Volume Surge Stocks:")
                for s in prob.get('volume_surge_stocks', [])[:3]:
                    print(f"     • {s['symbol']}: {s['volume_ratio']:.1f}x")
        else:
            print("\n⚠️ Probability analysis not available")
            if prob and prob.get('error'):
                print(f"   Error: {prob.get('error')}")
        
        # Options
        print("\n" + "="*70)
        print("🎯 TOP OPTIONS (Score Boosted by Probability Analysis)")
        print("="*70)
        
        for i, opt in enumerate(data.get('options', [])[:10]):
            boost = '⚡' if opt.get('probability_boost') else '  '
            print(f"{boost} {i+1}. {opt['type']} {opt['strike']} - Score: {opt['score']:.0f}, LTP: ₹{opt['ltp']:.2f}, IV: {opt.get('iv', 0):.1f}%")
        
        print(f"\n📊 Total Options Found: {data.get('total_options')}")
        print("\n✅ Integration test completed successfully!")
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (120s)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_scanner()
