#!/usr/bin/env python3
"""Test actionable signals with expiry parameter."""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("TRADEWISE_API_URL", "http://localhost:8000")

# Login
login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
    "email": os.getenv("TEST_USER_EMAIL"),
    "password": os.getenv("TEST_USER_PASSWORD")
})
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("  ACTIONABLE SIGNALS TEST - EXPIRY PARAMETER")
print("=" * 60)
print(f"API: {BASE_URL}")
print()

# Test WEEKLY
print("📅 WEEKLY EXPIRY (DTE=1 - should trigger EXPIRY_DAY_AVOID):")
resp = requests.get(f"{BASE_URL}/signals/NSE:NIFTY50-INDEX/actionable?expiry=weekly", headers=headers)
data = resp.json()
print(f"   DTE: {data.get('days_to_expiry')}")
print(f"   Action: {data.get('action')}")
reason = data.get("reason", "N/A")
print(f"   Reason: {reason[:80] if reason else 'N/A'}")
if data.get('action') == 'EXPIRY_DAY_AVOID':
    print("   ✅ Correctly returned EXPIRY_DAY_AVOID for DTE=1")
else:
    print(f"   ⚠️ Action={data.get('action')} for DTE={data.get('days_to_expiry')}")

print()

# Test NEXT_WEEKLY  
print("📅 NEXT_WEEKLY EXPIRY (DTE=8 - should NOT trigger EXPIRY_DAY_AVOID):")
resp = requests.get(f"{BASE_URL}/signals/NSE:NIFTY50-INDEX/actionable?expiry=next_weekly", headers=headers)
data = resp.json()
dte = data.get("days_to_expiry")
action = data.get("action")
print(f"   DTE: {dte}")
print(f"   Action: {action}")
reason = data.get("reason", "N/A")
print(f"   Reason: {reason[:80] if reason else 'N/A'}")

if dte == 8:
    print("   ✅ DTE correctly calculated as 8 days")
else:
    print(f"   ❌ DTE should be 8, got {dte}")
    
if action != "EXPIRY_DAY_AVOID":
    print("   ✅ Correctly NOT returning EXPIRY_DAY_AVOID for DTE=8")
else:
    print("   ❌ Should NOT return EXPIRY_DAY_AVOID for DTE=8")

print()
print("=" * 60)
