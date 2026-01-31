#!/usr/bin/env python3
import requests
import json

login_url = "http://localhost:8000/api/auth/login"
login_data = {"email": "bineshch@gmail.com", "password": "Tra@2026"}

resp = requests.post(login_url, json=login_data)
token = resp.json().get('access_token') or resp.json().get('token')
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

ai_url = "http://localhost:8000/api/ai/chat"

# Test signal data (same as user's example)
signal_data = {
    "signal": "ICT_NEUTRAL_BIAS",
    "action": "WAIT",
    "option": {
        "strike": 25400,
        "type": "CE",
        "symbol": "25400 CE",
        "trading_symbol": "NSE:NIFTY2620325400CE",
        "expiry_date": "2026-02-03",
        "expiry_info": {
            "days_to_expiry": 3,
            "is_weekly": True
        }
    },
    "pricing": {
        "ltp": 161.8,
        "entry_price": 161.8
    },
    "targets": {
        "target_1": 226.52,
        "target_2": 291.24,
        "stop_loss": 97.08
    },
    "greeks": {
        "delta": 0.4193,
        "gamma": 0.0012,
        "theta": -22.2499,
        "vega": 8.9697
    },
    "confidence": {
        "score": 4.5,
        "level": "AVOID"
    }
}

print("TEST 1: Simple Question (Should be 3-4 sentences)")
print("="*60)
resp = requests.post(ai_url, json={
    "query": "what if i want to buy now and target 5, 10 or 15 points. is that risky?",
    "signal_data": signal_data,
    "use_cache": False
}, headers=headers, timeout=40)

if resp.status_code == 200:
    response = resp.json().get('response')
    print(f"AI Response:\n{response}\n")
    print(f"Length: {len(response)} chars, {len(response.split())} words")
    print(f"Lines: {response.count(chr(10)) + 1}")
    
    # Check if it mentions actual data
    has_data = any([
        "161.8" in response or "161" in response,
        "22" in response and "decay" in response.lower(),
        "4.5" in response or "avoid" in response.lower(),
        "25400" in response
    ])
    print(f"Uses Actual Data: {'YES' if has_data else 'NO'}")
    print(f"Has ** symbols: {'YES (BAD)' if '**' in response else 'NO (GOOD)'}")
else:
    print(f"Error: {resp.status_code}")

print("\n\nTEST 2: Trading Knowledge")
print("="*60)
resp = requests.post(ai_url, json={
    "query": "What's the difference between NIFTY and a NIFTY call option?",
    "use_cache": False
}, headers=headers, timeout=40)

if resp.status_code == 200:
    response = resp.json().get('response')
    print(f"AI Response:\n{response}\n")
    knows_ce = "call" in response.lower() or "ce" in response.lower()
    knows_index = "index" in response.lower() or "cannot trade" in response.lower()
    print(f"Knows CE/Call: {'YES' if knows_ce else 'NO'}")
    print(f"Knows Index vs Option: {'YES' if knows_index else 'NO'}")
else:
    print(f"Error: {resp.status_code}")
