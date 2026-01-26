#!/usr/bin/env python3
"""
Test stock scan billing system
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_stock_scan_billing():
    print("🧪 Testing Stock Scan Billing System\n")
    
    # Login
    print("1️⃣ Logging in...")
    login_data = {
        "email": "bineshch@gmail.com",
        "password": "Tra@2026"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    auth_data = response.json()
    token = auth_data.get('access_token')
    print(f"✅ Logged in as {auth_data.get('user', {}).get('email')}\n")
    
    # Test 1: Calculate cost for 10 stocks
    print("2️⃣ Calculating cost for 10 stocks...")
    cost_data = {
        "limit": 10,
        "min_confidence": 60
    }
    
    response = requests.post(
        f"{BASE_URL}/api/screener/calculate-cost",
        json=cost_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        cost = response.json()
        print(f"✅ Cost calculation successful:")
        print(f"   📊 Stocks: {cost['stock_count']}")
        print(f"   💰 Per stock: ₹{cost['per_stock_cost']}")
        print(f"   💵 Total cost: ₹{cost['total_cost']}")
        print(f"   💳 Wallet balance: ₹{cost['wallet_balance']}")
        print(f"   📦 Has subscription: {cost['has_subscription']}")
        print(f"   🎯 Will use subscription: {cost['will_use_subscription']}")
        print(f"   ✅ Sufficient balance: {cost['sufficient_balance']}")
        print(f"   💳 Payment method: {cost['payment_method']}\n")
    else:
        print(f"❌ Cost calculation failed: {response.status_code}")
        print(f"   Response: {response.text}\n")
    
    # Test 2: Calculate cost for custom stock selection
    print("3️⃣ Calculating cost for 5 custom stocks...")
    cost_data = {
        "symbols": "NSE:RELIANCE-EQ,NSE:TCS-EQ,NSE:INFY-EQ,NSE:HDFCBANK-EQ,NSE:ICICIBANK-EQ",
        "min_confidence": 60
    }
    
    response = requests.post(
        f"{BASE_URL}/api/screener/calculate-cost",
        json=cost_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        cost = response.json()
        print(f"✅ Cost calculation successful:")
        print(f"   📊 Stocks: {cost['stock_count']}")
        print(f"   💵 Total cost: ₹{cost['total_cost']}")
        print(f"   💳 Payment method: {cost['payment_method']}\n")
    else:
        print(f"❌ Cost calculation failed: {response.status_code}\n")
    
    # Test 3: Try actual scan with small limit
    print("4️⃣ Testing actual scan with 3 stocks...")
    scan_data = {
        "limit": 3,
        "min_confidence": 60,
        "randomize": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/screener/scan",
        json=scan_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Scan successful!")
        print(f"   📊 Stocks scanned: {result['stocks_scanned']}")
        print(f"   🎯 Total signals: {result['total_signals']}")
        print(f"   📈 BUY signals: {result['buy_signals']}")
        print(f"   📉 SELL signals: {result['sell_signals']}")
    elif response.status_code == 402:
        error = response.json()
        print(f"⚠️  Payment Required (Expected if no credits)")
        print(f"   Message: {error.get('detail')}")
    elif response.status_code == 401:
        error = response.json()
        print(f"⚠️  Fyers auth required (Expected if not connected)")
        print(f"   Message: {error.get('detail')}")
    else:
        print(f"❌ Scan failed: {response.status_code}")
        print(f"   Response: {response.text}")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    test_stock_scan_billing()
