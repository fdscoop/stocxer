#!/usr/bin/env python3
"""
Test multiple sequential chats to verify token deduction consistency
"""
import requests
import json

BASE_URL = "http://localhost:8000"
EMAIL = "bineshch@gmail.com"
PASSWORD = "Tra@2026"

# Login
print("🔐 Logging in...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": EMAIL, "password": PASSWORD}
)
token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Get initial balance
print("💰 Getting initial balance...")
balance_response = requests.get(f"{BASE_URL}/api/billing/status", headers=headers)
initial_balance = balance_response.json()['credits_balance']
print(f"   Initial balance: {initial_balance}")

# Test multiple chats
queries = [
    "What is a BUY signal?",
    "Explain a PUT option in simple terms",
    "What makes a stock bullish?",
    "How to manage risk in trading?",
    "What is implied volatility?"
]

print(f"\n📊 Making {len(queries)} sequential chat requests...")
print("=" * 60)

for i, query in enumerate(queries, 1):
    chat_request = {
        "query": query,
        "signal_data": None,
        "scan_data": None,
        "scan_id": None,
        "use_cache": False
    }
    
    response = requests.post(
        f"{BASE_URL}/api/ai/chat",
        headers=headers,
        json=chat_request,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        tokens_remaining = data.get('tokens_remaining', 'N/A')
        print(f"\n{i}. Query: {query}")
        print(f"   Status: ✅ Success")
        print(f"   Tokens Remaining: {tokens_remaining}")
    elif response.status_code == 402:
        print(f"\n{i}. Query: {query}")
        print(f"   Status: ⚠️ Insufficient Tokens")
        print(f"   Message: {response.json().get('detail')}")
        break
    else:
        print(f"\n{i}. Query: {query}")
        print(f"   Status: ❌ Error {response.status_code}")
        break

# Final balance check
print("\n" + "=" * 60)
balance_response = requests.get(f"{BASE_URL}/api/billing/status", headers=headers)
final_balance = balance_response.json()['credits_balance']
total_deducted = initial_balance - final_balance

print(f"\n📈 Summary:")
print(f"   Initial Balance:  {initial_balance}")
print(f"   Final Balance:    {final_balance}")
print(f"   Total Deducted:   {total_deducted}")
print(f"   Expected Deduct:  {len(queries) * 0.20}")
print(f"   Match: {'✅ YES' if abs(total_deducted - len(queries) * 0.20) < 0.01 else '❌ NO'}")
