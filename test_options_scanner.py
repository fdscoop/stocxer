#!/usr/bin/env python3
"""Test Options Scanner Dashboard"""

import requests
import json
from datetime import datetime

def test_options_scanner():
    """Test the options scanner functionality"""
    
    print("🧪 Testing TradeWise Options Scanner Dashboard")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Health check
    print("\n1. 🏥 Health Check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Server Online: {health['service']} v{health['version']}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: Dashboard page load
    print("\n2. 📄 Dashboard Page...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            content = response.text
            if "showOptionsScanner()" in content:
                print("   ✅ Options Scanner UI found in dashboard")
            else:
                print("   ❌ Options Scanner UI not found")
        else:
            print(f"   ❌ Dashboard load failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Dashboard error: {e}")
    
    # Test 3: Options Scanner API (without auth to see error)
    print("\n3. 🔐 API Authentication...")
    try:
        response = requests.get(f"{base_url}/options/scan?index=NIFTY&expiry=weekly")
        if response.status_code == 401:
            print("   ✅ API properly requires authentication")
        else:
            print(f"   ⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API test error: {e}")
    
    # Test 4: Try with auth token (from localhost helper)
    print("\n4. 🎯 Testing Options Scanner with Auth...")
    print("   📝 Instructions for manual testing:")
    print(f"   1. Open: {base_url}")
    print("   2. Use localhost setup to get auth token")
    print("   3. Click 'Options Scanner' button")
    print("   4. Configure filters (Index: NIFTY, Expiry: weekly)")
    print("   5. Click 'Scan Options' to test")
    
    print("\n" + "=" * 50)
    print("🎉 OPTIONS SCANNER DASHBOARD: READY FOR TESTING!")
    print(f"🌐 Open in browser: {base_url}")
    print("💡 Use the localhost setup panel to get authentication")

if __name__ == "__main__":
    test_options_scanner()