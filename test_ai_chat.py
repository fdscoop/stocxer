#!/usr/bin/env python3
"""
Test AI Chat endpoint with proper signal data
"""
import requests
import json

print("🔐 Testing AI Chat Endpoint...")
print("="*50)

# Step 1: Login
login_url = "http://localhost:8000/api/auth/login"
login_data = {
    "email": "bineshch@gmail.com",
    "password": "Tra@2026"
}

try:
    print("\n1. Logging in...")
    response = requests.post(login_url, json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token') or data.get('token')
        print(f"   ✅ Login successful")
        print(f"   Token: {token[:20]}...")
        
        # Step 2: Test AI chat with signal data (like frontend sends)
        print("\n2. Testing AI chat with signal data...")
        ai_url = "http://localhost:8000/api/ai/chat"
        ai_data = {
            "query": "Explain this signal in simple terms",
            "signal_data": {
                "action": "WAIT",
                "strike": 25400,
                "type": "CE",
                "entry_price": 161.8,
                "target_1": 226.52,
                "target_2": 291.24,
                "stop_loss": 97.08,
                "confidence": 35,
                "direction": "BEARISH"
            },
            "scan_data": {
                "symbol": "NIFTY",
                "results": {
                    "status": "success",
                    "index": "NIFTY",
                    "expiry": "weekly",
                    "options": [
                        {"strike": 25400, "type": "CE", "ltp": 161.8, "volume": 50000, "oi": 200000}
                    ]
                }
            },
            "use_cache": False
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        ai_response = requests.post(ai_url, json=ai_data, headers=headers, timeout=30)
        
        print(f"   Status: {ai_response.status_code}")
        
        if ai_response.status_code == 200:
            ai_result = ai_response.json()
            print(f"\n   ✅ AI Response:")
            print(f"   {ai_result.get('response', '')}")
            print(f"\n   Cached: {ai_result.get('cached', False)}")
            print(f"   Confidence: {ai_result.get('confidence_score', 0)}")
        else:
            print(f"   ❌ AI Error: {ai_response.text[:300]}")
            
    else:
        print(f"   ❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except requests.exceptions.ConnectionError:
    print("   ❌ Cannot connect to backend. Is it running on port 8000?")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*50)
