#!/usr/bin/env python3
"""
Register test user
"""
import requests

BASE_URL = "http://localhost:8000"
EMAIL = "bineshch@gmail.com"
PASSWORD = "Tra@2026"

print("📝 Registering user...")
response = requests.post(
    f"{BASE_URL}/api/auth/register",
    json={
        "email": EMAIL,
        "password": PASSWORD,
        "full_name": "Test User"
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code in [200, 201]:
    print("\n✅ User registered successfully!")
    data = response.json()
    print(f"   User ID: {data.get('user', {}).get('id')}")
    print(f"   Email: {data.get('user', {}).get('email')}")
