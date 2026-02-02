#!/usr/bin/env python3
"""Exchange Fyers auth code for access token and store in Supabase"""
import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

import os
from dotenv import load_dotenv
load_dotenv('/Users/bineshbalan/TradeWise/.env')

from src.api.fyers_client import fyers_client
from supabase import create_client
from datetime import datetime, timedelta

# The auth code from Fyers callback
auth_code = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOiI1MjNQMkIzTUQ1IiwidXVpZCI6ImY5MTMyMjcxMWUwZTQ5MGE4M2MyNjBiY2I3YzZjYTg3IiwiaXBBZGRyIjoiIiwibm9uY2UiOiIiLCJzY29wZSI6IiIsImRpc3BsYXlfbmFtZSI6IlhCMDYzODQiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJhZWU0ODc2OTI5YmJjNDAxNGRkODM0YTc3MTMwNjJlMDA4ZWY3NDkzYmQ0NmExYjA0MDM3MzU1MCIsImlzRGRwaUVuYWJsZWQiOiJZIiwiaXNNdGZFbmFibGVkIjoiWSIsImF1ZCI6IltcImQ6MVwiLFwiZDoyXCIsXCJ4OjBcIixcIng6MVwiLFwieDoyXCJdIiwiZXhwIjoxNzcwMDIzMjE1LCJpYXQiOjE3Njk5OTMyMTUsImlzcyI6ImFwaS5sb2dpbi5meWVycy5pbiIsIm5iZiI6MTc2OTk5MzIxNSwic3ViIjoiYXV0aF9jb2RlIn0.rI-5WycMErArsdOOLB28pe1qJIPmGXO7KcgAJehxYQA"

print("Exchanging auth code for access token...")

# Exchange auth code for access token
success = fyers_client.set_access_token(auth_code)
if success:
    print(f"Got access token: {fyers_client.access_token[:50]}...")
    
    # Store in Supabase
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    supabase = create_client(url, key)
    
    # Get user ID for bineshch@gmail.com
    user_result = supabase.table('users').select('id, email').eq('email', 'bineshch@gmail.com').execute()
    if user_result.data:
        user_id = user_result.data[0]['id']
        print(f"Found user: {user_result.data[0]['email']} (ID: {user_id})")
        
        # Store/update token
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Check if token exists
        existing = supabase.table('fyers_tokens').select('*').eq('user_id', user_id).execute()
        
        token_data = {
            'user_id': user_id,
            'email': 'bineshch@gmail.com',
            'access_token': fyers_client.access_token,
            'expires_at': expires_at.isoformat()
        }
        
        if existing.data:
            # Update existing
            result = supabase.table('fyers_tokens').update(token_data).eq('user_id', user_id).execute()
            print(f"Updated Fyers token in database")
        else:
            # Insert new
            result = supabase.table('fyers_tokens').insert(token_data).execute()
            print(f"Inserted Fyers token in database")
        
        # Verify token works
        profile = fyers_client.get_profile()
        print(f"Fyers profile: {profile}")
    else:
        print("User bineshch@gmail.com not found in database")
else:
    print("Failed to exchange auth code")
