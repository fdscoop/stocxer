"""
Check signals and orders for all configured indices
"""
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import json

load_dotenv()
load_dotenv('frontend/.env.production')

# Initialize Supabase client
SUPABASE_URL = 'https://cxbcpmouqkajlxzmbomu.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN4YmNwbW91cWthamx4em1ib211Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NjA3NjMsImV4cCI6MjA4NDMzNjc2M30.oBozxBnSKARn-3xkRy8ceNU3wpxXh8MBReGtmtsBpEw'

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Authenticate
auth_response = supabase.auth.sign_in_with_password({
    "email": "bineshch@gmail.com",
    "password": "Tra@2026"
})
user_id = auth_response.user.id

print("="*80)
print("  📊 SIGNALS & POSITIONS BY INDEX")
print("="*80)

# Get config
config = supabase.table('paper_trading_config').select('*').eq('user_id', user_id).execute()
configured_indices = config.data[0]['indices'] if config.data else []
print(f"\n✅ Configured Indices: {', '.join(configured_indices)}")

# Check signals for each index
print("\n" + "="*80)
print("  1️⃣  SIGNALS BY INDEX")
print("="*80)

all_signals = supabase.table('paper_trading_signals').select('*').eq('user_id', user_id).execute()

signal_by_index = {}
for signal in all_signals.data:
    idx = signal['index']
    if idx not in signal_by_index:
        signal_by_index[idx] = []
    signal_by_index[idx].append(signal)

for idx in configured_indices:
    signals = signal_by_index.get(idx, [])
    print(f"\n📈 {idx}:")
    print(f"   Total Signals: {len(signals)}")
    
    if signals:
        executed = sum(1 for s in signals if s['executed'])
        pending = sum(1 for s in signals if not s['executed'])
        print(f"   Executed: {executed}")
        print(f"   Pending: {pending}")
        
        # Show latest signal
        latest = max(signals, key=lambda s: s['created_at'])
        print(f"\n   Latest Signal:")
        print(f"      Type: {latest['signal_type']}")
        print(f"      Symbol: {latest['option_symbol']}")
        print(f"      Confidence: {latest['confidence']}%")
        print(f"      Status: {latest['status']}")
        if latest['rejection_reason']:
            print(f"      Rejection: {latest['rejection_reason']}")
    else:
        print(f"   ⚠️  No signals generated yet")

# Check positions by index
print("\n" + "="*80)
print("  2️⃣  POSITIONS BY INDEX")
print("="*80)

all_positions = supabase.table('paper_trading_positions').select('*').eq('user_id', user_id).execute()

position_by_index = {}
for pos in all_positions.data:
    idx = pos['index']
    if idx not in position_by_index:
        position_by_index[idx] = []
    position_by_index[idx].append(pos)

for idx in configured_indices:
    positions = position_by_index.get(idx, [])
    print(f"\n📊 {idx}:")
    print(f"   Total Positions: {len(positions)}")
    
    if positions:
        open_pos = sum(1 for p in positions if p['status'] == 'OPEN')
        closed_pos = sum(1 for p in positions if p['status'] == 'CLOSED')
        print(f"   Open: {open_pos}")
        print(f"   Closed: {closed_pos}")
        
        # Show sample positions
        print(f"\n   Sample Positions:")
        for i, pos in enumerate(positions[:3], 1):
            order_id = "N/A"
            if pos.get('order_response'):
                order_id = pos['order_response'].get('id', 'N/A')
            print(f"      {i}. {pos['option_symbol']} | Qty: {pos['quantity']} | Order ID: {order_id}")
    else:
        print(f"   ⚠️  No positions yet")

# Check activity log for scan attempts
print("\n" + "="*80)
print("  3️⃣  SCAN ACTIVITY BY INDEX")
print("="*80)

scan_activities = supabase.table('paper_trading_activity_log').select('*').eq('user_id', user_id).eq('activity_type', 'SCAN').order('timestamp', desc=True).limit(20).execute()

scan_by_index = {}
for activity in scan_activities.data:
    details = activity.get('details', {})
    idx = details.get('index', 'UNKNOWN')
    if idx not in scan_by_index:
        scan_by_index[idx] = []
    scan_by_index[idx].append(activity)

for idx in configured_indices:
    scans = scan_by_index.get(idx, [])
    print(f"\n🔍 {idx}:")
    print(f"   Total Scans: {len(scans)}")
    
    if scans:
        latest_scan = scans[0]
        scan_details = latest_scan.get('details', {})
        print(f"   Last Scan: {latest_scan['timestamp']}")
        print(f"   Signal Generated: {scan_details.get('signal_generated', False)}")
        if 'error' in scan_details:
            print(f"   Error: {scan_details['error']}")
    else:
        print(f"   ⚠️  No scans recorded yet")

print("\n" + "="*80)
print("  ✅ ANALYSIS COMPLETE")
print("="*80)
