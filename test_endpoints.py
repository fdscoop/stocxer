"""Test all endpoints"""
import requests

# Login and test
login_data = {'email': 'bineshch@gmail.com', 'password': 'Tra@2026'}
login_response = requests.post('http://localhost:8000/api/auth/login', json=login_data)
token = login_response.json().get('access_token')

headers = {'Authorization': f'Bearer {token}'}

# Test screener
print('Testing /screener/latest...')
r = requests.get('http://localhost:8000/screener/latest?index=NIFTY', headers=headers)
print(f'  Status: {r.status_code}')
if r.ok:
    print(f'  Response status: {r.json().get("status")}')
else:
    print(f'  Error: {r.text[:200]}')

# Test billing
print('\nTesting /api/billing/status...')
r = requests.get('http://localhost:8000/api/billing/status', headers=headers)
print(f'  Status: {r.status_code}')
if r.ok:
    print(f'  Credits: {r.json().get("credits_balance")}')
else:
    print(f'  Error: {r.text[:200]}')

# Test AI chat
print('\nTesting /api/ai/chat...')
r = requests.post('http://localhost:8000/api/ai/chat', 
    headers=headers, 
    json={'query': 'what is the current signal?'})
print(f'  Status: {r.status_code}')
if r.ok:
    print(f'  Response: {r.json().get("response", "")[:100]}...')
else:
    print(f'  Error: {r.text[:200]}')
