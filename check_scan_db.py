#!/usr/bin/env python3
"""Check recent scan results in database to verify index field is being saved correctly."""

import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL", "https://cxbcpmouqkajlxzmbomu.supabase.co")
key = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN4YmNwbW91cWthamx4em1ib211Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NjA3NjMsImV4cCI6MjA4NDMzNjc2M30.oBozxBnSKARn-3xkRy8ceNU3wpxXh8MBReGtmtsBpEw")

supabase = create_client(url, key)

print("=" * 60)
print("CHECKING RECENT SCAN RESULTS IN DATABASE")
print("=" * 60)
print()

# Fetch recent scan results
response = supabase.table("option_scanner_results").select(
    "id, created_at, trading_symbol, index, action, expiry, probability"
).order("created_at", desc=True).limit(20).execute()

if response.data:
    print(f"Found {len(response.data)} recent scan results:\n")
    
    for i, r in enumerate(response.data[:15], 1):
        symbol = r.get('trading_symbol', 'N/A')
        index_val = r.get('index', 'NOT SET')
        expiry = r.get('expiry', 'N/A')
        action = r.get('action', 'N/A')
        created = r.get('created_at', 'N/A')[:19] if r.get('created_at') else 'N/A'
        
        print(f"{i}. {symbol}")
        print(f"   Index: {index_val if index_val else 'NULL'} | Expiry: {expiry} | Action: {action}")
        print(f"   Created: {created}")
        print()
        
    # Summary
    print("=" * 60)
    print("INDEX FIELD SUMMARY:")
    indices_found = {}
    null_count = 0
    for r in response.data:
        idx = r.get('index')
        if idx:
            indices_found[idx] = indices_found.get(idx, 0) + 1
        else:
            null_count += 1
    
    for idx, count in indices_found.items():
        print(f"  - {idx}: {count} records")
    if null_count:
        print(f"  - NULL/NOT SET: {null_count} records")
    print("=" * 60)
else:
    print("No scan results found in database")
