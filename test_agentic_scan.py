#!/usr/bin/env python3
import requests
import time

# User credentials
user_email = "bineshch@gmail.com"
user_password = "Tra@2026"

login_url = "http://localhost:8000/api/auth/login"
ai_url = "http://localhost:8000/api/ai/chat"

print(f"Logging in as {user_email}...")
login_resp = requests.post(login_url, json={"email": user_email, "password": user_password})

if login_resp.status_code != 200:
    print(f"Login failed: {login_resp.status_code} - {login_resp.text}")
    exit(1)

token = login_resp.json().get('access_token') or login_resp.json().get('token')
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print("Login successful.")

print("\n" + "="*60)
print("TEST: Agentic Scan Trigger (Triggering a fresh scan for BANKNIFTY)")
print("="*60)

# The query should trigger 'scan' type and then internal httpx call to /options/scan
resp = requests.post(ai_url, json={
    "query": "scan banknifty for me",
    "use_cache": False
}, headers=headers, timeout=120)

if resp.status_code == 200:
    result = resp.json()
    print("\nAI Response:")
    print("-" * 40)
    print(result.get('response'))
    print("-" * 40)
    
    # Check if the response matches our requirements
    response_text = result.get('response', '')
    word_count = len(response_text.split())
    has_markdown = "**" in response_text or "##" in response_text
    
    print(f"\nVerification Results:")
    print(f"  - Word Count: {word_count} (Target: <100)")
    print(f"  - No Markdown: {'✅' if not has_markdown else '❌'}")
    
    # Check if it analyzed a signal (implicitly checks if scan worked)
    has_data = any(x in response_text.lower() for x in ["ce", "pe", "rs", "target", "strike"])
    print(f"  - Analyzed Live Signal: {'✅' if has_data else '❌'}")
else:
    print(f"Request failed: {resp.status_code} - {resp.text}")

print("\n" + "="*60)
print("TEST: Verifying Brevity for Simple Question")
print("="*60)

resp = requests.post(ai_url, json={
    "query": "it is risky if i buy now?",
    "use_cache": False
}, headers=headers, timeout=60)

if resp.status_code == 200:
    result = resp.json()
    print("\nAI Response:")
    print("-" * 40)
    print(result.get('response'))
    print("-" * 40)
    
    word_count = len(result.get('response', '').split())
    has_markdown = "**" in result.get('response', '') or "##" in result.get('response', '')
    
    print(f"\nVerification Results:")
    print(f"  - Word Count: {word_count} (Target: <100)")
    print(f"  - No Markdown: {'✅' if not has_markdown else '❌'}")
else:
    print(f"Request failed: {resp.status_code} - {resp.text}")
