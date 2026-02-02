#!/usr/bin/env python3
"""
Test authenticated NIFTY options scan
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def login_and_scan():
    print("🔐 Logging in...\n")
    
    # Login
    login_data = {
        "email": os.getenv("TEST_USER_EMAIL", "test@example.com"),
        "password": os.getenv("TEST_USER_PASSWORD", "test_password")
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.json())
        return
    
    auth_data = response.json()
    token = auth_data.get('access_token')
    
    if not token:
        print("❌ No token received")
        print(auth_data)
        return
    
    print(f"✅ Login successful!")
    print(f"👤 User: {auth_data.get('user', {}).get('email')}")
    print(f"🎫 Token: {token[:20]}...\n")
    
    # Calculate next expiry
    today = datetime.now()
    days_ahead = 3 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_expiry = today + timedelta(days=days_ahead)
    expiry = next_expiry.strftime('%Y-%m-%d')
    
    # Scan options
    print(f"🔍 Scanning NIFTY options for expiry: {expiry}...\n")
    
    url = f"{BASE_URL}/options/scan"
    params = {
        'index': 'NIFTY',
        'expiry': expiry,
        'min_volume': 1000,
        'min_oi': 10000,
        'strategy': 'all',
        'include_probability': 'true'
    }
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"📡 Request URL: {url}")
    print(f"📊 Parameters: {json.dumps(params, indent=2)}\n")
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        print(f"📈 Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Scan successful!")
            print(f"\n📊 Results Summary:")
            print(f"   Total signals: {len(data.get('signals', []))}")
            print(f"   Index: {data.get('index', 'N/A')}")
            print(f"   Expiry: {data.get('expiry', 'N/A')}")
            print(f"   Strategy: {data.get('strategy', 'N/A')}")
            
            if data.get('signals'):
                print(f"\n🎯 Top 5 Signals:")
                for i, signal in enumerate(data['signals'][:5], 1):
                    print(f"\n   {i}. {signal.get('symbol')}")
                    print(f"      Action: {signal.get('action')}")
                    print(f"      Entry: ₹{signal.get('entry_price', 0):.2f}")
                    print(f"      Target: ₹{signal.get('target_price', 0):.2f}")
                    print(f"      Stop Loss: ₹{signal.get('stop_loss', 0):.2f}")
                    print(f"      Confidence: {signal.get('confidence', 0):.1f}%")
            
            print(f"\n💾 Full response saved to /tmp/scan_result.json")
            with open('/tmp/scan_result.json', 'w') as f:
                json.dump(data, f, indent=2)
        else:
            print(f"❌ Scan failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    login_and_scan()
