#!/usr/bin/env python3
"""
Check latest option scanner result to see if new ICT logic is working
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get most recent result
response = supabase.table("option_scanner_results").select("*").order("created_at", desc=True).limit(1).execute()

if response.data:
    result = response.data[0]
    print("=" * 70)
    print("LATEST OPTION SCANNER RESULT")
    print("=" * 70)
    print(f"Created: {result['created_at']}")
    print(f"Index: {result['index']}")
    print(f"Signal: {result['signal']}")
    print(f"Action: {result['action']}")
    print(f"HTF Direction: {result['htf_direction']}")
    print(f"Option Type: {result['option_type']}")
    print(f"Strike: {result['strike']}")
    print(f"Confidence: {result['confidence']}%")
    print()
    
    # Check if it matches market direction
    spot = result['spot_price']
    print(f"Spot Price: {spot:.2f}")
    print()
    
    # Show full signal data if available
    if result.get('full_signal_data'):
        signal_data = result['full_signal_data']
        print("HTF Analysis:")
        htf = signal_data.get('htf_analysis', {})
        print(f"  Direction: {htf.get('direction', 'N/A')}")
        print(f"  Strength: {htf.get('strength', 0)}")
        print()
else:
    print("No results found")
