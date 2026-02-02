"""
Test and verify all Paper Trading database tables
"""
import asyncio
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()
load_dotenv('frontend/.env.production')

# Initialize Supabase client
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL') or 'https://cxbcpmouqkajlxzmbomu.supabase.co'
SUPABASE_ANON_KEY = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY') or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN4YmNwbW91cWthamx4em1ib211Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NjA3NjMsImV4cCI6MjA4NDMzNjc2M30.oBozxBnSKARn-3xkRy8ceNU3wpxXh8MBReGtmtsBpEw'

print(f"🔐 Connecting to Supabase: {SUPABASE_URL}")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Authenticate user
print("🔑 Authenticating user...")
auth_response = supabase.auth.sign_in_with_password({
    "email": os.getenv("TEST_USER_EMAIL", "test@example.com"),
    "password": os.getenv("TEST_USER_PASSWORD", "test_password")
})

if not auth_response.user:
    print("❌ Authentication failed!")
    exit(1)

print(f"✅ Authenticated as: {auth_response.user.email}")
print(f"   User ID: {auth_response.user.id}")
print(f"   Access Token: {auth_response.session.access_token[:50]}...")

user_id = auth_response.user.id

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_table_data(table_name: str, data: list, limit: int = 10):
    """Print table data in a readable format"""
    print(f"\n📊 {table_name.upper()}")
    print(f"   Total rows: {len(data)}")
    
    if not data:
        print("   ⚠️  No data found")
        return
    
    print(f"   Showing first {min(limit, len(data))} rows:\n")
    
    for i, row in enumerate(data[:limit], 1):
        print(f"   Row {i}:")
        for key, value in row.items():
            if isinstance(value, dict) or isinstance(value, list):
                print(f"      {key}: {json.dumps(value, indent=6)}")
            elif isinstance(value, datetime):
                print(f"      {key}: {value.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"      {key}: {value}")
        print()

async def test_database():
    """Test all paper trading database tables"""
    
    print_header("📊 SCANNING PAPER TRADING DATABASE")
    
    # Test 1: paper_trading_config
    print_header("1️⃣  PAPER TRADING CONFIG")
    config_response = supabase.table('paper_trading_config').select('*').eq('user_id', user_id).execute()
    print_table_data('paper_trading_config', config_response.data)
    
    # Test 2: paper_trading_signals
    print_header("2️⃣  PAPER TRADING SIGNALS")
    signals_response = supabase.table('paper_trading_signals').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(10).execute()
    print_table_data('paper_trading_signals', signals_response.data)
    
    # Test 3: paper_trading_positions
    print_header("3️⃣  PAPER TRADING POSITIONS")
    positions_response = supabase.table('paper_trading_positions').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(10).execute()
    print_table_data('paper_trading_positions', positions_response.data)
    
    # Test 4: paper_trading_activity_log
    print_header("4️⃣  PAPER TRADING ACTIVITY LOG")
    activity_response = supabase.table('paper_trading_activity_log').select('*').eq('user_id', user_id).order('timestamp', desc=True).limit(15).execute()
    print_table_data('paper_trading_activity_log', activity_response.data)
    
    # Test 5: paper_trading_performance
    print_header("5️⃣  PAPER TRADING PERFORMANCE")
    performance_response = supabase.table('paper_trading_performance').select('*').eq('user_id', user_id).order('date', desc=True).execute()
    print_table_data('paper_trading_performance', performance_response.data)
    
    # Summary Statistics
    print_header("📈 SUMMARY STATISTICS")
    
    # Count positions by status
    all_positions = supabase.table('paper_trading_positions').select('status').eq('user_id', user_id).execute()
    open_count = sum(1 for p in all_positions.data if p['status'] == 'OPEN')
    closed_count = sum(1 for p in all_positions.data if p['status'] == 'CLOSED')
    
    print(f"\n   Positions:")
    print(f"      Total: {len(all_positions.data)}")
    print(f"      Open: {open_count}")
    print(f"      Closed: {closed_count}")
    
    # Count signals by status
    all_signals = supabase.table('paper_trading_signals').select('status, signal_type').eq('user_id', user_id).execute()
    executed_signals = sum(1 for s in all_signals.data if s['status'] == 'EXECUTED')
    pending_signals = sum(1 for s in all_signals.data if s['status'] == 'PENDING')
    
    print(f"\n   Signals:")
    print(f"      Total: {len(all_signals.data)}")
    print(f"      Executed: {executed_signals}")
    print(f"      Pending: {pending_signals}")
    
    # Signal types breakdown
    signal_types = {}
    for s in all_signals.data:
        st = s['signal_type']
        signal_types[st] = signal_types.get(st, 0) + 1
    
    print(f"\n   Signal Types:")
    for signal_type, count in signal_types.items():
        print(f"      {signal_type}: {count}")
    
    # Activity types breakdown
    all_activities = supabase.table('paper_trading_activity_log').select('activity_type').eq('user_id', user_id).execute()
    activity_types = {}
    for a in all_activities.data:
        at = a['activity_type']
        activity_types[at] = activity_types.get(at, 0) + 1
    
    print(f"\n   Activities:")
    print(f"      Total: {len(all_activities.data)}")
    for activity_type, count in sorted(activity_types.items(), key=lambda x: x[1], reverse=True):
        print(f"      {activity_type}: {count}")
    
    # Calculate P&L from closed positions
    closed_positions = [p for p in all_positions.data if p['status'] == 'CLOSED']
    if closed_positions:
        total_pnl = sum(float(p.get('pnl', 0) or 0) for p in closed_positions)
        winning = sum(1 for p in closed_positions if float(p.get('pnl', 0) or 0) > 0)
        losing = sum(1 for p in closed_positions if float(p.get('pnl', 0) or 0) < 0)
        
        print(f"\n   P&L (Closed Positions):")
        print(f"      Total P&L: ₹{total_pnl:,.2f}")
        print(f"      Winning Trades: {winning}")
        print(f"      Losing Trades: {losing}")
        if closed_count > 0:
            print(f"      Win Rate: {(winning/closed_count)*100:.1f}%")
    
    print_header("✅ DATABASE SCAN COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_database())
