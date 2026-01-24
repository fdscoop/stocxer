#!/usr/bin/env python3
"""Check if FYERS token exists in Supabase"""
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.supabase_config import supabase_admin

try:
    print("Checking Supabase for FYERS tokens...")
    response = supabase_admin.table("fyers_tokens").select("*").order("updated_at", desc=True).execute()
    
    if not response.data:
        print("\n❌ NO TOKENS FOUND IN DATABASE")
        print("\nTo fix this:")
        print("1. Open TradeWise app in browser")
        print("2. Go to Settings → Connect Fyers")
        print("3. Complete Fyers authentication")
        print("4. Token will be saved to Supabase")
    else:
        print(f"\n✅ Found {len(response.data)} token(s) in database:\n")
        
        for i, token in enumerate(response.data, 1):
            print(f"Token {i}:")
            print(f"  User ID: {token.get('user_id', 'N/A')}")
            print(f"  Created: {token.get('created_at', 'N/A')}")
            print(f"  Updated: {token.get('updated_at', 'N/A')}")
            
            # Check expiry
            if token.get('expires_at'):
                expires_at = datetime.fromisoformat(token["expires_at"])
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                
                now = datetime.now(timezone.utc)
                
                if expires_at < now:
                    print(f"  Status: ❌ EXPIRED")
                else:
                    time_left = expires_at - now
                    hours_left = time_left.total_seconds() / 3600
                    print(f"  Status: ✅ VALID ({hours_left:.1f} hours remaining)")
            else:
                print(f"  Status: ⚠️  No expiry info")
            
            print()
        
        # Check if any valid token exists
        valid_tokens = [t for t in response.data 
                       if t.get('expires_at') and 
                       datetime.fromisoformat(t['expires_at']).replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)]
        
        if valid_tokens:
            print(f"✅ {len(valid_tokens)} valid token(s) available for MCP server")
        else:
            print("⚠️  All tokens expired. Please re-authenticate via TradeWise app")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
