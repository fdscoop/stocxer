#!/usr/bin/env python3
"""
Quick check of option_scanner_results structure
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get one recent result to see structure
response = supabase.table("option_scanner_results").select("*").limit(1).order("created_at", desc=True).execute()

if response.data:
    print("Sample option_scanner_results record:")
    print(json.dumps(response.data[0], indent=2))
else:
    print("No data found")
