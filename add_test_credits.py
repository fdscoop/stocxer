#!/usr/bin/env python3
"""
Add test credits to user
"""
import asyncio
import sys
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, '/Users/bineshbalan/TradeWise')

async def add_test_credits():
    """Add 100 test credits to user"""
    from config.supabase_config import get_supabase_admin_client
    
    try:
        supabase = get_supabase_admin_client()
        
        # Get user by email
        print("🔍 Finding user: bineshch@gmail.com...")
        users_response = supabase.table('users').select('*').eq('email', 'bineshch@gmail.com').single().execute()
        
        if not users_response.data:
            print("❌ User not found")
            return
        
        user_id = users_response.data['id']
        print(f"✅ Found user: {user_id}")
        
        # Update or create credits
        print(f"\n💰 Adding 100 credits...")
        supabase.table('user_credits').upsert({
            'user_id': user_id,
            'balance': 100,
            'lifetime_purchased': 100,
            'lifetime_spent': 0,
            'updated_at': datetime.now().isoformat()
        }, on_conflict='user_id').execute()
        
        print(f"✅ Credits added successfully!")
        
        # Record welcome bonus transaction
        supabase.table('credit_transactions').insert({
            'user_id': user_id,
            'transaction_type': 'bonus',
            'amount': 100,
            'balance_before': 0,
            'balance_after': 100,
            'description': 'Test bonus: 100 credits for testing',
            'created_at': datetime.now().isoformat()
        }).execute()
        
        print(f"✅ Transaction recorded")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_test_credits())
