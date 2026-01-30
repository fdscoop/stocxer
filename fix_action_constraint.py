#!/usr/bin/env python3
"""
Fix the screener_results action constraint to include WAIT and AVOID
"""

import os
import sys
from supabase import create_client

def fix_action_constraint():
    """Update the action constraint to include WAIT and AVOID"""
    
    # Get Supabase credentials from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        sys.exit(1)
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        print("🔧 Fixing screener_results action constraint...")
        
        # Drop existing constraint
        drop_sql = """
        ALTER TABLE public.screener_results 
        DROP CONSTRAINT IF EXISTS screener_results_action_check;
        """
        
        # Add updated constraint
        add_sql = """
        ALTER TABLE public.screener_results 
        ADD CONSTRAINT screener_results_action_check 
        CHECK (action IN ('BUY', 'SELL', 'BUY CALL', 'BUY PUT', 'SELL CALL', 'SELL PUT', 'WAIT', 'AVOID'));
        """
        
        # Verify constraint
        verify_sql = """
        SELECT conname, pg_get_constraintdef(oid) 
        FROM pg_constraint 
        WHERE conrelid = 'public.screener_results'::regclass 
        AND conname = 'screener_results_action_check';
        """
        
        # Execute drop
        supabase.postgrest.rpc('exec_sql', {'sql': drop_sql}).execute()
        print("✅ Dropped old constraint")
        
        # Execute add
        supabase.postgrest.rpc('exec_sql', {'sql': add_sql}).execute()
        print("✅ Added new constraint with WAIT and AVOID")
        
        # Execute verify
        result = supabase.postgrest.rpc('exec_sql', {'sql': verify_sql}).execute()
        print(f"✅ Constraint verified: {result.data}")
        
        print("\n✅ Action constraint updated successfully!")
        print("   Allowed actions: BUY, SELL, BUY CALL, BUY PUT, SELL CALL, SELL PUT, WAIT, AVOID")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_action_constraint()
