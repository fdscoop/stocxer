#!/usr/bin/env python3
"""Update Fyers token in database with fresh access token"""
import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

import os
from dotenv import load_dotenv
load_dotenv('/Users/bineshbalan/TradeWise/.env')

from supabase import create_client
from datetime import datetime, timedelta
from src.api.fyers_client import fyers_client

# The auth code from Fyers callback
auth_code = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOiI1MjNQMkIzTUQ1IiwidXVpZCI6ImU5ODI4YTNiNzMwODRmYmFiNjg5ZjgyOTYwNjhiYTlkIiwiaXBBZGRyIjoiIiwibm9uY2UiOiIiLCJzY29wZSI6IiIsImRpc3BsYXlfbmFtZSI6IlhCMDYzODQiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmNTZkMmFiZGNhZGY1MTg2MTczNGE1MWViNmUzODJiMDMyMzRkMTI1MmQ5YjkzOGU1ODRkYWIxOSIsImlzRGRwaUVuYWJsZWQiOiJZIiwiaXNNdGZFbmFibGVkIjoiWSIsImF1ZCI6IltcImQ6MVwiLFwiZDoyXCIsXCJ4OjBcIixcIng6MVwiLFwieDoyXCJdIiwiZXhwIjoxNzcwMDI1MjM2LCJpYXQiOjE3Njk5OTUyMzYsImlzcyI6ImFwaS5sb2dpbi5meWVycy5pbiIsIm5iZiI6MTc2OTk5NTIzNiwic3ViIjoiYXV0aF9jb2RlIn0.W-LQwQO64RZD6o1qGPdsPiuz392DrsG30rQu-tzSvOE"

print("Exchanging auth code for access token...")
success = fyers_client.set_access_token(auth_code)

if not success:
    print("Failed to exchange auth code - it may have expired")
    print("Using existing token from previous successful exchange...")
    # The access token we got from the previous successful exchange
    fyers_client.access_token = "523P2B3MD5-100:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImNsaWVudF9pZCI6IjUyM1AyQjNNRDUtMTAwIiwiZXhwIjoxNzcwMDc5NjE1LCJpYXQiOjE3Njk5OTMyMTUsImlzcyI6ImFwaS5meWVycy5pbiIsImp0aSI6IjA4MWRjODNiYjQ2MTRmNGJhMTNiOGE2MmU2MWUyMWQ5IiwibmJmIjoxNzY5OTkzMjE1LCJzdWIiOiJhY2Nlc3NfdG9rZW4iLCJ0eXBlIjoiYXBpIiwidXNlcl9uYW1lIjoiWEIwNjM4NCIsInV1aWQiOiJmOTEzMjI3MTFlMGU0OTBhODNjMjYwYmNiN2M2Y2E4NyIsInZlcnNpb24iOjN9.XYkDQ0lDixLjFvZvqvmRAPCL_cNVNLnlc4pXt38m7ro"
    fyers_client._initialize_client()

access_token = fyers_client.access_token
print(f"Access token: {access_token[:50]}...")

# Store in Supabase
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

# Update the existing token
expires_at = datetime.utcnow() + timedelta(hours=24)
result = supabase.table('fyers_tokens').update({
    'access_token': access_token,
    'expires_at': expires_at.isoformat()
}).eq('user_id', '4f1d1b44-7459-43fa-8aec-f9b9a0605c4b').execute()

print(f"Updated token in database")

# Verify token works
try:
    profile = fyers_client.get_profile()
    print(f"Fyers profile: {profile}")
    
    # Test getting a quote
    quote = fyers_client.get_quotes(["NSE:NIFTY50-INDEX"])
    if quote and quote.get("d"):
        spot = quote["d"][0]["v"]["lp"]
        print(f"NIFTY Spot: {spot}")
        print("Token is working!")
except Exception as e:
    print(f"Error: {e}")
