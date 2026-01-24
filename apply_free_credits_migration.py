#!/usr/bin/env python3
"""
Apply 100 Free Credits Migration
Gives all new and existing users 100 free credits
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def main():
    """Apply migration to give users 100 free credits"""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    print("🚀 Starting 100 Free Credits Migration...")
    print("=" * 60)
    
    try:
        # Step 1: Update default value (handled by SQL migration)
        print("\n✓ Step 1: Default value will be set to 100 in SQL migration")
        
        # Step 2: Get all users with zero balance
        print("\n📊 Step 2: Checking existing users...")
        response = supabase.table('user_credits').select('*').eq('balance', 0).execute()
        users_to_update = response.data if response.data else []
        
        print(f"   Found {len(users_to_update)} users with 0 balance")
        
        if users_to_update:
            print("\n💰 Step 3: Updating user balances...")
            updated_count = 0
            
            for user in users_to_update:
                user_id = user['user_id']
                
                # Update balance
                supabase.table('user_credits').update({
                    'balance': 100,
                    'lifetime_purchased': float(user.get('lifetime_purchased', 0)) + 100,
                    'updated_at': datetime.now().isoformat()
                }).eq('user_id', user_id).execute()
                
                # Record bonus transaction
                supabase.table('credit_transactions').insert({
                    'user_id': user_id,
                    'transaction_type': 'bonus',
                    'amount': 100,
                    'balance_before': 0,
                    'balance_after': 100,
                    'description': 'Welcome bonus: 100 free credits'
                }).execute()
                
                updated_count += 1
                print(f"   ✓ Updated user {updated_count}/{len(users_to_update)}")
            
            print(f"\n✅ Successfully updated {updated_count} users with 100 free credits")
        else:
            print("\n✓ No users need updating")
        
        # Step 4: Verify the changes
        print("\n🔍 Step 4: Verifying changes...")
        
        # Check user_credits
        credits_response = supabase.table('user_credits').select('user_id, balance, lifetime_purchased').execute()
        if credits_response.data:
            print(f"   ✓ Found {len(credits_response.data)} user_credits records")
            zero_balance_count = sum(1 for u in credits_response.data if float(u['balance']) == 0)
            if zero_balance_count > 0:
                print(f"   ⚠️  Warning: {zero_balance_count} users still have 0 balance")
            else:
                print("   ✓ All users have non-zero balance")
        
        # Check bonus transactions
        bonus_response = supabase.table('credit_transactions')\
            .select('user_id')\
            .eq('transaction_type', 'bonus')\
            .eq('description', 'Welcome bonus: 100 free credits')\
            .execute()
        
        if bonus_response.data:
            print(f"   ✓ Found {len(bonus_response.data)} welcome bonus transactions")
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("\n📝 Summary:")
        print(f"   - Updated {len(users_to_update)} existing users")
        print(f"   - New users will automatically get 100 free credits")
        print(f"   - Total bonus transactions: {len(bonus_response.data) if bonus_response.data else 0}")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
