#!/usr/bin/env python3
"""
Paper Trading Database Setup Script

This script initializes the paper trading system database tables in Supabase.

Usage:
    python setup_paper_trading.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.supabase_config import supabase_admin
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_sql_file(filename: str) -> str:
    """Read SQL file content"""
    sql_path = project_root / "database" / filename
    
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")
    
    with open(sql_path, 'r') as f:
        return f.read()


def execute_sql(sql: str) -> bool:
    """Execute SQL in Supabase"""
    try:
        # Split SQL into individual statements
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        
        logger.info(f"Executing {len(statements)} SQL statements...")
        
        for i, statement in enumerate(statements, 1):
            # Skip comments and empty lines
            if statement.startswith('--') or not statement:
                continue
            
            try:
                # Execute via Supabase RPC (if available)
                # Note: Direct SQL execution requires service role key
                logger.info(f"Statement {i}/{len(statements)}: {statement[:50]}...")
                
                # For Supabase, we need to use their SQL editor or migration system
                # This script will output the SQL to run manually
                
            except Exception as e:
                logger.error(f"Error in statement {i}: {e}")
                logger.error(f"Statement: {statement[:100]}...")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        return False


def verify_tables() -> bool:
    """Verify that tables were created successfully"""
    try:
        tables = [
            'paper_trading_config',
            'paper_trading_signals',
            'paper_trading_positions',
            'paper_trading_activity_log',
            'paper_trading_performance'
        ]
        
        logger.info("Verifying tables...")
        
        for table in tables:
            try:
                result = supabase_admin.table(table).select("*").limit(1).execute()
                logger.info(f"✓ Table '{table}' exists")
            except Exception as e:
                logger.error(f"✗ Table '{table}' not found: {e}")
                return False
        
        logger.info("All tables verified successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying tables: {e}")
        return False


def setup_paper_trading():
    """Main setup function"""
    print("\n" + "=" * 70)
    print("PAPER TRADING SYSTEM - DATABASE SETUP")
    print("=" * 70 + "\n")
    
    # Check if Supabase is configured
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        print("❌ ERROR: Supabase credentials not found!")
        print("\nPlease set the following environment variables:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_SERVICE_ROLE_KEY")
        print("\nYou can find these in your Supabase project settings.")
        return False
    
    print("✓ Supabase credentials found\n")
    
    # Read SQL schema
    print("📄 Reading SQL schema...")
    try:
        sql = read_sql_file("paper_trading_schema.sql")
        print(f"✓ Loaded {len(sql)} characters of SQL\n")
    except FileNotFoundError as e:
        print(f"❌ ERROR: {e}")
        return False
    
    # Inform user about manual SQL execution
    print("⚠️  IMPORTANT: Supabase requires SQL to be executed via SQL Editor")
    print("\nPlease follow these steps:")
    print("\n1. Go to your Supabase project dashboard")
    print("2. Navigate to: SQL Editor")
    print("3. Create a new query")
    print("4. Copy the contents of: database/paper_trading_schema.sql")
    print("5. Paste into the SQL Editor")
    print("6. Click 'Run' to execute")
    print("\nAlternatively, use the Supabase CLI:")
    print("  supabase db push")
    
    # Ask user if they've run the SQL
    print("\n" + "-" * 70)
    response = input("\nHave you executed the SQL schema in Supabase? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n⚠️  Please run the SQL schema first, then run this script again.")
        return False
    
    print("\n" + "-" * 70)
    print("Verifying database setup...\n")
    
    # Verify tables
    if verify_tables():
        print("\n" + "=" * 70)
        print("✅ PAPER TRADING DATABASE SETUP COMPLETE!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Start your FastAPI server: python main.py")
        print("2. Access the paper trading dashboard")
        print("3. Configure your trading settings")
        print("4. Start automated paper trading")
        print("\n⚠️  Remember: Keep your Fyers balance at ₹0 for paper trading")
        print("   Orders will be rejected but positions will be tracked.")
        return True
    else:
        print("\n" + "=" * 70)
        print("❌ SETUP VERIFICATION FAILED")
        print("=" * 70)
        print("\nPlease check:")
        print("1. SQL schema was executed successfully in Supabase")
        print("2. Service role key has proper permissions")
        print("3. No errors in Supabase SQL Editor")
        return False


def create_sample_config():
    """Create a sample configuration for testing"""
    print("\n" + "-" * 70)
    response = input("Create a sample configuration? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        return
    
    # This would require a user ID - skip for now
    print("\n⚠️  Sample configuration requires a user ID from auth.users")
    print("You can create a configuration via the dashboard after logging in.")


if __name__ == "__main__":
    try:
        success = setup_paper_trading()
        
        if success:
            create_sample_config()
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
