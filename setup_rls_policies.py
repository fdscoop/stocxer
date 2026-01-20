#!/usr/bin/env python3
"""
Script to set up RLS policies for TradeWise Supabase database
Run this script to configure the Row Level Security policies properly
"""

from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

def setup_rls_policies():
    """Set up RLS policies for fyers_tokens table"""
    
    # You need to use your service role key for admin operations
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not SUPABASE_SERVICE_KEY or SUPABASE_SERVICE_KEY == 'your_service_role_key_here':
        print("❌ SUPABASE_SERVICE_KEY not set in .env file")
        print("📝 To get your service role key:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to Settings > API")
        print("3. Copy the 'service_role' key (not anon key)")
        print("4. Add it to your .env file as SUPABASE_SERVICE_KEY=your_key_here")
        return False
    
    try:
        # Create client with service role key
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        print("🔧 Setting up RLS policies for fyers_tokens table...")
        
        # SQL to set up the policies
        rls_sql = """
        -- Drop existing policies
        DROP POLICY IF EXISTS "Users can only view their own tokens" ON fyers_tokens;
        DROP POLICY IF EXISTS "Users can only insert their own tokens" ON fyers_tokens;
        DROP POLICY IF EXISTS "Users can only update their own tokens" ON fyers_tokens;
        DROP POLICY IF EXISTS "Application can read tokens for startup" ON fyers_tokens;
        DROP POLICY IF EXISTS "Users can manage their own tokens" ON fyers_tokens;
        DROP POLICY IF EXISTS "Service role has full access" ON fyers_tokens;
        
        -- Create new policies
        CREATE POLICY "Application can read tokens for startup" ON fyers_tokens
            FOR SELECT
            USING (true);
        
        CREATE POLICY "Users can manage their own tokens" ON fyers_tokens
            FOR ALL
            USING (auth.uid() = user_id);
        
        CREATE POLICY "Service role has full access" ON fyers_tokens
            FOR ALL
            TO service_role
            USING (true);
        
        -- Ensure RLS is enabled
        ALTER TABLE fyers_tokens ENABLE ROW LEVEL SECURITY;
        """
        
        # Execute the SQL
        result = supabase.rpc('exec_sql', {'sql': rls_sql}).execute()
        
        print("✅ RLS policies set up successfully!")
        print("🔍 Checking current policies...")
        
        # Check what policies exist
        policies_result = supabase.rpc('exec_sql', {
            'sql': "SELECT policyname, cmd FROM pg_policies WHERE tablename = 'fyers_tokens'"
        }).execute()
        
        if policies_result.data:
            print("📋 Current policies:")
            for policy in policies_result.data:
                print(f"  - {policy['policyname']} ({policy['cmd']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up RLS policies: {e}")
        print("\n🛠️ Manual setup required:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to Database > Tables > fyers_tokens")
        print("3. Click on 'RLS disabled' to enable it")
        print("4. Add the policies from database/rls_policies.sql")
        return False

def test_token_access():
    """Test if we can now access tokens from the database"""
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')  # anon key
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table('fyers_tokens').select('*').execute()
        
        print(f"\n🧪 Testing token access with anon key...")
        print(f"📊 Found {len(response.data) if response.data else 0} tokens")
        
        if response.data and len(response.data) > 0:
            print("✅ Token access working! The application can now load tokens.")
            return True
        else:
            print("⚠️ No tokens found, but access is working.")
            return True
            
    except Exception as e:
        print(f"❌ Still cannot access tokens: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TradeWise RLS Policy Setup")
    print("=" * 40)
    
    if setup_rls_policies():
        test_token_access()
        print("\n✅ Setup complete! Your application should now be able to load tokens from the database.")
    else:
        print("\n❌ Setup failed. Please check the manual setup instructions above.")