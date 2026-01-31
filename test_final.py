#!/usr/bin/env python3
import requests

login_url = "http://localhost:8000/api/auth/login"
login_data = {"email": "bineshch@gmail.com", "password": "Tra@2026"}

resp = requests.post(login_url, json=login_data)
token = resp.json().get('access_token') or resp.json().get('token')
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

ai_url = "http://localhost:8000/api/ai/chat"

# Test with exact signal data from user's example
signal_data = {
    "action": "WAIT",
    "option": {"strike": 25400, "type": "CE", "expiry_info": {"days_to_expiry": 3}},
    "pricing": {"ltp": 161.8},
    "targets": {"target_1": 226.52, "target_2": 291.24, "stop_loss": 97.08},
    "greeks": {"theta": -22.2499},
    "confidence": {"score": 4.5, "level": "AVOID"}
}

print("FINAL TEST: Concise, Data-Driven Response")
print("="*60)
resp = requests.post(ai_url, json={
    "query": "what if i want to buy now and target 5, 10 or 15 points?",
    "signal_data": signal_data,
    "use_cache": False
}, headers=headers, timeout=30)

if resp.status_code == 200:
    response = resp.json().get('response')
    print(f"AI Response:\n{response}\n")
    
    # Metrics
    word_count = len(response.split())
    line_count = response.count('\n') + 1
    has_theta = "-22" in response or "22" in response
    has_strike = "25400" in response
    has_ltp = "161" in response
    has_confidence = "4.5" in response or "avoid" in response.lower()
    has_markdown = "**" in response or "##" in response
    
    print(f"\nMetrics:")
    print(f"  Words: {word_count} (Target: <100 for simple questions)")
    print(f"  Lines: {line_count} (Target: 3-8)")
    print(f"  Cites Theta: {has_theta}")
    print(f"  Cites Strike: {has_strike}")
    print(f"  Cites LTP: {has_ltp}")
    print(f"  Cites Confidence: {has_confidence}")
    print(f"  Has Markdown (**): {has_markdown} {'❌ BAD' if has_markdown else '✅ GOOD'}")
    
    success = word_count < 150 and not has_markdown and (has_theta or has_ltp or has_confidence)
    print(f"\n{'✅ SUCCESS' if success else '❌ NEEDS MORE WORK'}")
else:
    print(f"Error: {resp.status_code}")
