"""
Fix Unconfirmed Users - Auto-confirm all users for development
Run this script to confirm all unconfirmed users in Supabase
"""
from config.supabase_config import supabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_unconfirmed_users():
    """
    Auto-confirm all unconfirmed users
    
    Note: This requires service_role key, not anon key!
    You need to run this SQL in Supabase SQL Editor instead:
    
    UPDATE auth.users 
    SET email_confirmed_at = NOW() 
    WHERE email_confirmed_at IS NULL;
    """
    
    print("\n" + "="*60)
    print("🔧 FIX UNCONFIRMED USERS")
    print("="*60)
    print("\nThis script cannot directly update auth.users table.")
    print("You need to run this SQL command in Supabase SQL Editor:\n")
    print("─" * 60)
    print("UPDATE auth.users")
    print("SET email_confirmed_at = NOW()")
    print("WHERE email_confirmed_at IS NULL;")
    print("─" * 60)
    print("\nSteps:")
    print("1. Go to: https://supabase.com/dashboard/project/cxbcpmouqkajlxzmbomu/sql")
    print("2. Paste the SQL command above")
    print("3. Click 'Run'")
    print("4. All unconfirmed users will now be able to login!")
    print("\n" + "="*60)
    
    # Try to show existing users (if possible)
    try:
        print("\n📊 Checking registered users...")
        users = supabase.table("users").select("email, created_at").execute()
        
        if users.data:
            print(f"\nFound {len(users.data)} registered users:")
            for user in users.data:
                print(f"  - {user['email']} (registered: {user['created_at'][:10]})")
        else:
            print("No users found in public.users table yet.")
            
    except Exception as e:
        logger.error(f"Could not fetch users: {e}")
        print(f"\n⚠️  Could not fetch users: {e}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    fix_unconfirmed_users()
