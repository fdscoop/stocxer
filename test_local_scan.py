#!/usr/bin/env python3
"""
Test local NIFTY options scan
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# You need to use your actual auth token from the frontend
# For now, let's just test without auth to see the endpoint response
def test_scan():
    print("🔍 Testing NIFTY options scan locally...\n")
    
    # Calculate next expiry (next Thursday)
    today = datetime.now()
    days_ahead = 3 - today.weekday()  # Thursday is 3
    if days_ahead <= 0:
        days_ahead += 7
    next_expiry = today + timedelta(days=days_ahead)
    expiry = next_expiry.strftime('%Y-%m-%d')
    
    url = f"{BASE_URL}/options/scan"
    params = {
        'index': 'NIFTY',
        'expiry': expiry,
        'min_volume': 1000,
        'min_oi': 10000,
        'strategy': 'all',
        'include_probability': 'true'
    }
    
    print(f"📡 Requesting: {url}")
    print(f"📊 Parameters: {params}\n")
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            if 'access-control' in key.lower() or 'cors' in key.lower():
                print(f"  {key}: {value}")
        print(f"\nResponse Body:")
        
        if response.status_code == 401:
            print("⚠️  Authentication required")
            print("   Response:", response.json())
            print("\n💡 To test with auth, get your JWT token from browser DevTools:")
            print("   1. Open https://www.stocxer.in in browser")
            print("   2. Login and open DevTools (F12)")
            print("   3. Go to Application > Local Storage > token")
            print("   4. Copy the token value and use it in Authorization header")
        else:
            print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_scan()
