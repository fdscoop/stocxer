#!/usr/bin/env python3
"""
Check user credits directly
"""
import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

from config.supabase_config import get_supabase_admin_client

supabase = get_supabase_admin_client()

# Get user by email
print("🔍 Finding user...")
users = supabase.table('users').select('id,email').execute()
for user in users.data:
    if 'bineshch' in user['email']:
        print(f"Found: {user['email']} (ID: {user['id']})")
        
        # Get their credits
        credits = supabase.table('user_credits').select('*').eq('user_id', user['id']).execute()
        if credits.data:
            print(f"✅ Credits: {credits.data[0]['balance']}")
        else:
            print(f"⚠️ No credits record found")
        break
else:
    print("User not found")
