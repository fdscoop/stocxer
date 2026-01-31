#!/usr/bin/env python3
"""
Test complete flow: login -> check credits -> chat
"""
import requests
import json

BASE_URL = "http://localhost:8000"
EMAIL = "bineshch@gmail.com"
PASSWORD = "Tra@2026"

print("=" * 60)
print("TEST: Chat with Token Deduction")
print("=" * 60)

# Step 1: Login
print("\n1️⃣  LOGIN")
print("-" * 60)
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": EMAIL, "password": PASSWORD}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(f"Response: {login_response.text}")
    exit(1)

auth_data = login_response.json()
token = auth_data.get("access_token")
user = auth_data.get("user", {})
user_id = user.get("id")

print(f"✅ Login successful")
print(f"   Email: {user.get('email')}")
print(f"   User ID: {user_id}")
print(f"   Token: {token[:30]}...")

# Step 2: Get current balance
print("\n2️⃣  CHECK BALANCE")
print("-" * 60)
headers = {"Authorization": f"Bearer {token}"}

balance_response = requests.get(
    f"{BASE_URL}/api/billing/status",
    headers=headers
)

if balance_response.status_code == 200:
    balance_data = balance_response.json()
    print(f"✅ Got billing status")
    
    # Navigate the response structure
    balance = balance_data
    if isinstance(balance_data, dict):
        if 'credits_balance' in balance_data:
            balance = balance_data['credits_balance']
        elif 'credits' in balance_data:
            balance = balance_data['credits'].get('balance', 0)
        else:
            balance = balance_data
    
    print(f"   Response keys: {list(balance_data.keys())}")
    print(f"   Full response:")
    print(json.dumps(balance_data, indent=2, default=str)[:500])
else:
    print(f"❌ Failed to get balance: {balance_response.status_code}")
    print(f"Response: {balance_response.text}")

# Step 3: Make a chat request
print("\n3️⃣  TEST CHAT (Should deduct 0.20 tokens)")
print("-" * 60)

chat_request = {
    "query": "What is market sentiment today?",
    "signal_data": None,
    "scan_data": None,
    "scan_id": None,
    "use_cache": False
}

chat_response = requests.post(
    f"{BASE_URL}/api/ai/chat",
    headers=headers,
    json=chat_request,
    timeout=30
)

print(f"Status Code: {chat_response.status_code}")

if chat_response.status_code == 200:
    chat_data = chat_response.json()
    print(f"✅ Chat successful")
    print(f"   Response: {chat_data.get('response', '')[:100]}...")
    
    if 'tokens_remaining' in chat_data:
        print(f"   ✅ Tokens remaining: {chat_data['tokens_remaining']}")
    else:
        print(f"   ⚠️ No tokens_remaining in response")
        
elif chat_response.status_code == 402:
    print(f"⚠️  Insufficient tokens")
    print(f"   Message: {chat_response.json().get('detail')}")
else:
    print(f"❌ Chat failed")
    print(f"   Status: {chat_response.status_code}")
    print(f"   Message: {chat_response.text}")
