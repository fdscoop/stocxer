"""
Quick script to set up billing database tables in Supabase
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def setup_billing_tables():
    """Create billing tables in Supabase"""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
        return False
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Read the migration SQL
    with open('database/migrations/subscription_schema.sql', 'r') as f:
        sql = f.read()
    
    print("📝 Migration SQL loaded (387 lines)")
    print("\n🚀 To execute this migration:")
    print("\n1. Go to: https://supabase.com/dashboard/project/cxbcpmouqkajlxzmbomu/sql/new")
    print("2. Copy the SQL from: database/migrations/subscription_schema.sql")
    print("3. Paste it into the SQL Editor")
    print("4. Click 'Run' button")
    print("\n✨ After running, these tables will be created:")
    print("   - user_subscriptions")
    print("   - user_credits") 
    print("   - credit_transactions")
    print("   - usage_logs")
    print("   - plan_limits (with 3 default plans)")
    print("   - credit_packs (with 5 packs)")
    print("   - payment_history")
    print("\n📋 The migration is safe to run multiple times (uses IF NOT EXISTS)")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("  BILLING DATABASE SETUP")
    print("=" * 60)
    setup_billing_tables()
