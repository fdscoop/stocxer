#!/usr/bin/env python3
"""
Test token deduction with actual API call
"""
import requests
import json
from decimal import Decimal

BASE_URL = "http://localhost:8000"
EMAIL = "bineshch@gmail.com"
PASSWORD = "Tra@2026"

def test_chat_with_token_deduction():
    """Test that tokens are deducted on chat API call"""
    try:
        # Step 1: Login
        print("🔐 Logging in...")
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": EMAIL, "password": PASSWORD}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        auth_data = login_response.json()
        token = auth_data.get("access_token")
        user_id = auth_data.get("user", {}).get("id")
        
        print(f"✅ Logged in successfully")
        print(f"   User ID: {user_id}")
        print(f"   Token: {token[:20]}...")
        
        # Step 2: Get current balance
        print(f"\n💰 Getting current balance...")
        headers = {"Authorization": f"Bearer {token}"}
        
        balance_response = requests.get(
            f"{BASE_URL}/api/billing/status",
            headers=headers
        )
        
        if balance_response.status_code == 200:
            balance_data = balance_response.json()
            current_balance = balance_data.get("credits", {}).get("balance", 0)
            print(f"   Current balance: {current_balance} credits")
        else:
            print(f"   Could not fetch balance")
            return
        
        if current_balance < 0.20:
            print(f"❌ Insufficient balance (need 0.20, have {current_balance})")
            return
        
        # Step 3: Make a chat request
        print(f"\n💬 Sending chat request...")
        chat_request = {
            "query": "What is the current market sentiment for NIFTY?",
            "signal_data": None,
            "scan_data": None,
            "scan_id": None,
            "use_cache": False
        }
        
        chat_response = requests.post(
            f"{BASE_URL}/api/ai/chat",
            headers=headers,
            json=chat_request
        )
        
        print(f"   Response Status: {chat_response.status_code}")
        
        if chat_response.status_code == 200:
            chat_data = chat_response.json()
            print(f"✅ Chat request successful")
            print(f"   Response: {chat_data.get('response', '')[:100]}...")
            
            tokens_remaining = chat_data.get('tokens_remaining')
            if tokens_remaining is not None:
                print(f"   ✅ Tokens remaining: {tokens_remaining}")
                print(f"   ✅ Tokens deducted: {current_balance - tokens_remaining}")
            
        elif chat_response.status_code == 402:
            print(f"⚠️  Insufficient tokens: {chat_response.json().get('detail')}")
        else:
            print(f"❌ Chat failed ({chat_response.status_code}): {chat_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chat_with_token_deduction()
