#!/usr/bin/env python3
"""
Test script to verify token deduction on AI chat responses
"""
import asyncio
import os
import sys
from decimal import Decimal
from datetime import datetime

# Add project to path
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

async def test_token_deduction():
    """Test that tokens are deducted for chat responses"""
    from src.services.auth_service import auth_service
    from src.services.billing_service import billing_service
    from config.supabase_config import get_supabase_admin_client
    
    try:
        supabase = get_supabase_admin_client()
        
        # Get a test user (use your email or create a test)
        print("🔍 Fetching test user...")
        users_response = supabase.table('users').select('*').limit(1).execute()
        
        if not users_response.data:
            print("❌ No users found in database. Please create a user first.")
            return
        
        test_user = users_response.data[0]
        user_id = test_user['id']
        user_email = test_user['email']
        
        print(f"📧 Testing with user: {user_email} (ID: {user_id})")
        
        # Get current balance
        print("\n💰 Getting current balance...")
        balance_response = supabase.table('user_credits').select('*').eq('user_id', user_id).single().execute()
        
        if balance_response.data:
            current_balance = Decimal(str(balance_response.data['balance']))
            print(f"   Current balance: {current_balance} credits")
        else:
            print("   No balance record found. This user needs to have credits initialized.")
            return
        
        # Try to deduct 0.20 credits
        print(f"\n🔄 Attempting to deduct 0.20 credits...")
        success, message, result = await billing_service.deduct_credits(
            user_id=user_id,
            amount=Decimal("0.20"),
            description="Test AI Chat Response",
            scan_type="ai_chat",
            metadata={"test": True, "timestamp": datetime.now().isoformat()}
        )
        
        if success:
            print(f"✅ {message}")
            new_balance = result.get('balance', 0) if result else 0
            print(f"   New balance: {new_balance} credits")
            
            # Verify transaction was recorded
            print(f"\n📋 Verifying transaction was recorded...")
            txn_response = supabase.table('credit_transactions').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=True).limit(1).execute()
            
            if txn_response.data:
                latest_txn = txn_response.data[0]
                print(f"   Transaction Type: {latest_txn['transaction_type']}")
                print(f"   Amount: {latest_txn['amount']} credits")
                print(f"   Description: {latest_txn['description']}")
                print(f"   Balance Before: {latest_txn['balance_before']}")
                print(f"   Balance After: {latest_txn['balance_after']}")
                print(f"   Created At: {latest_txn['created_at']}")
                print(f"\n✅ Token deduction working correctly!")
            else:
                print("   ⚠️ Transaction not found")
        else:
            print(f"❌ {message}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_token_deduction())
