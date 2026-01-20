#!/usr/bin/env python3
"""Test RLS policies after setup"""

from supabase import create_client
from config.settings import settings

def test_rls_policies():
    print("🔧 Testing RLS Policies...")
    
    # Test with anon key (normal app access)
    print("\n1. Testing with anon key (normal app access)...")
    try:
        anon_supabase = create_client(settings.supabase_url, settings.supabase_key)
        response = anon_supabase.table('fyers_tokens').select('*').execute()
        print(f"   ✅ Anon key can access tokens: {len(response.data) if response.data else 0} tokens found")
        
        if response.data:
            for i, token in enumerate(response.data):
                print(f"   Token {i+1}: expires {token.get('expires_at', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Anon key access failed: {e}")
    
    # Test with service role key
    print("\n2. Testing with service role key...")
    try:
        service_supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        response = service_supabase.table('fyers_tokens').select('*').execute()
        print(f"   ✅ Service role can access tokens: {len(response.data) if response.data else 0} tokens found")
    except Exception as e:
        print(f"   ❌ Service role access failed: {e}")
    
    print("\n🚀 RLS Policies Test Complete!")

if __name__ == "__main__":
    test_rls_policies()