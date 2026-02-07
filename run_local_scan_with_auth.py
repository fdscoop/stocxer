#!/usr/bin/env python3
"""
Local NIFTY Scan with Fyers Authentication
1. Authenticates with Supabase
2. Retrieves Fyers token from database
3. Sets up local environment
4. Provides instructions to run local server
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment
load_dotenv()

print("=" * 70)
print("🔐 FYERS TOKEN RETRIEVAL FOR LOCAL SCANNING")
print("=" * 70)
print()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for direct DB access
EMAIL = os.getenv("TEST_USER_EMAIL")
PASSWORD = os.getenv("TEST_USER_PASSWORD")

if not all([SUPABASE_URL, SUPABASE_KEY, EMAIL, PASSWORD]):
    print("❌ Missing environment variables in .env file")
    print("   Required: SUPABASE_URL, SUPABASE_SERVICE_KEY, TEST_USER_EMAIL, TEST_USER_PASSWORD")
    sys.exit(1)

print("Step 1: Connecting to Supabase...")
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    sys.exit(1)

print()
print("Step 2: Authenticating user...")
try:
    # Sign in to get user ID
    auth_response = supabase.auth.sign_in_with_password({
        "email": EMAIL,
        "password": PASSWORD
    })
    
    user_id = auth_response.user.id
    print(f"✅ Authenticated as: {EMAIL}")
    print(f"   User ID: {user_id}")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
    sys.exit(1)

print()
print("Step 3: Retrieving Fyers token from database...")
try:
    # Query fyers_tokens table
    response = supabase.table("fyers_tokens").select("*").eq("user_id", user_id).execute()
    
    if response.data and len(response.data) > 0:
        token_data = response.data[0]
        fyers_access_token = token_data.get("access_token")
        
        if fyers_access_token:
            print(f"✅ Fyers token found!")
            print(f"   Token: {fyers_access_token[:20]}...")
            print(f"   Expires: {token_data.get('expires_at', 'N/A')}")
            
            # Update .env file
            print()
            print("Step 4: Updating .env file with Fyers token...")
            
            # Read current .env
            with open(".env", "r") as f:
                lines = f.readlines()
            
            # Update FYERS_ACCESS_TOKEN line
            updated = False
            for i, line in enumerate(lines):
                if line.startswith("FYERS_ACCESS_TOKEN="):
                    lines[i] = f"FYERS_ACCESS_TOKEN={fyers_access_token}\n"
                    updated = True
                    break
            
            # Write back
            with open(".env", "w") as f:
                f.writelines(lines)
            
            print("✅ .env file updated with Fyers token")
            
            print()
            print("=" * 70)
            print("✅ SETUP COMPLETE - Ready for Local Scanning!")
            print("=" * 70)
            print()
            print("📋 Next Steps:")
            print()
            print("1️⃣  Start the local backend server:")
            print("   source .venv/bin/activate")
            print("   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
            print()
            print("2️⃣  In a NEW terminal, run the scan:")
            print("   cd /Users/bineshbalan/TradeWise")
            print("   source .venv/bin/activate")
            print("   python scan_nifty_auth.py")
            print()
            print("   OR run the simple unauthenticated scan:")
            print("   python scan_nifty.py")
            print()
            print("🔍 You'll see detailed logs in the server terminal showing:")
            print("   • All 50 constituent stocks being analyzed")
            print("   • Technical indicator calculations")
            print("   • Probability computations")
            print("   • Signal generation process")
            print("   • Options chain recommendations")
            print()
            
        else:
            print("❌ No access token found in database")
            print()
            print("You need to authenticate with Fyers first:")
            print("1. Go to https://stocxer.in")
            print("2. Login with your credentials")
            print("3. Click 'Authenticate with Fyers'")
            print("4. Complete the Fyers authentication flow")
            print("5. Run this script again")
    else:
        print("❌ No Fyers token record found for this user")
        print()
        print("You need to authenticate with Fyers first:")
        print("1. Go to https://stocxer.in")
        print("2. Login with your credentials")
        print("3. Click 'Authenticate with Fyers'")
        print("4. Complete the Fyers authentication flow")
        print("5. Run this script again")
        
except Exception as e:
    print(f"❌ Database query failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
