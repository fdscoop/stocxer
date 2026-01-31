#!/usr/bin/env python3
"""
Check and fix user credits directly
"""
import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

from config.supabase_config import get_supabase_admin_client
from datetime import datetime
from decimal import Decimal

supabase = get_supabase_admin_client()

# Get user
print("🔍 Getting user: bineshch@gmail.com")
try:
    users = supabase.table('users').select('id,email').execute()
    user = None
    for u in users.data:
        if u['email'] == 'bineshch@gmail.com':
            user = u
            break
    
    if not user:
        print("❌ User not found in database. Checking auth.users...")
        auth_users = supabase.auth.admin.list_users()
        print(f"Auth users in system: {[u.email for u in auth_users.users][:5]}")
        sys.exit(1)
    
    user_id = user['id']
    print(f"✅ User found: {user['email']} (ID: {user_id})")
    
    # Check if user has credits record
    print(f"\n💰 Checking user_credits table...")
    credits = supabase.table('user_credits').select('*').eq('user_id', user_id).execute()
    
    if credits.data:
        print(f"✅ Credits record exists:")
        print(f"   Balance: {credits.data[0]['balance']}")
        print(f"   Lifetime Purchased: {credits.data[0]['lifetime_purchased']}")
        print(f"   Lifetime Spent: {credits.data[0]['lifetime_spent']}")
    else:
        print(f"⚠️ No credits record - creating one...")
        # Create credits record
        result = supabase.table('user_credits').insert({
            'user_id': user_id,
            'balance': 8000,
            'lifetime_purchased': 8000,
            'lifetime_spent': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }).execute()
        
        print(f"✅ Credits record created with 8000 balance")
        
        # Also insert transaction record
        supabase.table('credit_transactions').insert({
            'user_id': user_id,
            'transaction_type': 'bonus',
            'amount': 8000,
            'balance_before': 0,
            'balance_after': 8000,
            'description': 'Test credits for token charging',
            'created_at': datetime.now().isoformat()
        }).execute()
        
        print(f"✅ Transaction record created")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
