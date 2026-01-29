"""Check user data"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Check users table
print('Looking for bineshch@gmail.com...')
result = supabase.table('users').select('*').execute()
print(f'Found {len(result.data)} users')
for u in result.data:
    email = u.get('email', 'no-email')
    print(f'  - {email}')
    if 'binesh' in email.lower():
        print(f'    ID: {u.get("id")}')
        print(f'    Created: {u.get("created_at")}')

# Check user_credits
print('\nChecking user_credits...')
credits = supabase.table('user_credits').select('*').execute()
for c in credits.data:
    uid = c.get("user_id", "?")
    cr = c.get("credits_remaining", 0)
    print(f'  User: {uid[:8]}... Credits: {cr}')

# Check fyers_tokens  
print('\nChecking fyers_tokens...')
tokens = supabase.table('fyers_tokens').select('user_id,updated_at').execute()
for t in tokens.data:
    uid = t.get("user_id", "?")
    upd = t.get("updated_at", "?")
    print(f'  User: {uid[:8]}... Updated: {upd}')
