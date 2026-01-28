"""Test Fyers token format with and without client_id prefix"""
from fyers_apiv3 import fyersModel
from config.supabase_config import supabase_admin
import tempfile
import os

# Get token from DB
response = supabase_admin.table('fyers_tokens').select('*').order('updated_at', desc=True).limit(1).execute()
token = response.data[0]['access_token'] if response.data else None
client_id = '523P2B3MD5-100'

print(f'Token (first 30 chars): {token[:30]}...')
print(f'Client ID: {client_id}')

# Try with client_id prefix (this is the Fyers v3 API format)
token_with_prefix = f'{client_id}:{token}'
print(f'\nToken with prefix (first 50): {token_with_prefix[:50]}...')

log_path = os.path.join(tempfile.gettempdir(), 'fyers_test')
os.makedirs(log_path, exist_ok=True)

# Test WITHOUT prefix
print('\n--- Testing WITHOUT client_id prefix ---')
fyers1 = fyersModel.FyersModel(client_id=client_id, token=token, log_path=log_path)
result1 = fyers1.quotes({'symbols': 'NSE:NIFTY50-INDEX'})
print(f'Result: code={result1.get("code")}, message={result1.get("message", "OK")}')

# Test WITH prefix
print('\n--- Testing WITH client_id prefix ---')
fyers2 = fyersModel.FyersModel(client_id=client_id, token=token_with_prefix, log_path=log_path)
result2 = fyers2.quotes({'symbols': 'NSE:NIFTY50-INDEX'})
print(f'Result: code={result2.get("code")}, message={result2.get("message", "OK")}')

if result2.get('d'):
    print(f'\n✅ Token WITH prefix works!')
    print(f'Spot data: {result2["d"][0]["v"]}')
elif result1.get('d'):
    print(f'\n✅ Token WITHOUT prefix works!')
    print(f'Spot data: {result1["d"][0]["v"]}')
else:
    print('\n❌ Both formats failed')
