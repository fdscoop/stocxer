#!/usr/bin/env python3
"""
Test expiry selection to debug the EXPIRY_DAY_AVOID issue
When user selects "next_weekly", system should NOT return expiry day signal
"""
import sys
import os
from datetime import datetime
from pytz import timezone as pytz_timezone

# Add project root to path
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv('/Users/bineshbalan/TradeWise/.env', override=True)

# Debug: Check if env vars are loaded
print(f"DEBUG: TEST_USER_EMAIL = {os.getenv('TEST_USER_EMAIL')}")

import asyncio
import requests

# IST timezone
IST = pytz_timezone('Asia/Kolkata')

def get_current_ist_time():
    """Get current time in IST"""
    return datetime.now(IST)

async def test_expiry_flow():
    """Test the complete expiry selection flow"""
    
    print("=" * 70)
    print("🧪 EXPIRY SELECTION DEBUG TEST")
    print("=" * 70)
    
    # Current time in IST
    now_ist = get_current_ist_time()
    print(f"\n📅 Current IST Time: {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   Today's Date (IST): {now_ist.date()}")
    print(f"   Day of Week: {now_ist.strftime('%A')}")
    
    # Step 1: Authenticate using env credentials
    print("\n" + "=" * 70)
    print("🔐 Step 1: Authenticating...")
    print("=" * 70)
    
    email = os.getenv('TEST_USER_EMAIL')
    password = os.getenv('TEST_USER_PASSWORD')
    
    if not email or not password:
        print("❌ TEST_USER_EMAIL and TEST_USER_PASSWORD must be set in .env")
        return
    
    # Login to get auth token
    from config.supabase_config import supabase_admin
    try:
        auth_response = supabase_admin.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        token = auth_response.session.access_token
        print(f"✅ Authenticated as: {email}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Step 2: Check available expiries
    print("\n" + "=" * 70)
    print("📅 Step 2: Fetching Available Expiries...")
    print("=" * 70)
    
    api_url = os.getenv('TRADEWISE_API_URL', 'http://localhost:8000')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    expiry_response = requests.get(f"{api_url}/index/NIFTY/expiries")
    if expiry_response.ok:
        expiries = expiry_response.json()
        print(f"\n📋 Available Expiries from Backend:")
        print(f"   Weekly: {expiries.get('expiries', {}).get('weekly')} ({expiries.get('expiries', {}).get('weekly_days')} days)")
        print(f"   Next Weekly: {expiries.get('expiries', {}).get('next_weekly')} ({expiries.get('expiries', {}).get('next_weekly_days')} days)")
        print(f"   Monthly: {expiries.get('expiries', {}).get('monthly')} ({expiries.get('expiries', {}).get('monthly_days')} days)")
        
        if expiries.get('expiries', {}).get('all_expiries'):
            print(f"   All Expiries: {expiries.get('expiries', {}).get('all_expiries')[:5]}...")
    else:
        print(f"❌ Failed to fetch expiries: {expiry_response.status_code}")
        print(expiry_response.text)
    
    # Step 3: Test scanning with WEEKLY expiry
    print("\n" + "=" * 70)
    print("🔍 Step 3: Testing WEEKLY Expiry Scan...")
    print("=" * 70)
    
    weekly_url = f"{api_url}/options/scan?index=NIFTY&expiry=weekly&min_volume=1000&min_oi=10000&strategy=all&include_probability=true&quick_scan=true"
    print(f"   URL: {weekly_url}")
    
    weekly_response = requests.get(weekly_url, headers=headers)
    if weekly_response.ok:
        data = weekly_response.json()
        print(f"\n📊 Weekly Scan Result:")
        print(f"   Status: {data.get('status')}")
        print(f"   Expiry Date: {data.get('market_data', {}).get('expiry_date')}")
        print(f"   Days to Expiry: {data.get('market_data', {}).get('days_to_expiry')}")
        print(f"   Available Keys: {list(data.keys())}")
        
        # Check if EXPIRY_DAY_AVOID was triggered
        actionable = data.get('actionable_signal') or data.get('signal_data') or {}
        signal_type = actionable.get('signal') or actionable.get('action') or 'N/A'
        print(f"   Signal Type: {signal_type}")
        
        if signal_type == 'EXPIRY_DAY_AVOID' or 'EXPIRY_DAY' in str(actionable):
            print(f"   ⚠️ EXPIRY_DAY_AVOID TRIGGERED!")
            print(f"   Full Signal: {actionable}")
        else:
            print(f"   Signal Action: {actionable.get('action', 'N/A')}")
    else:
        print(f"❌ Weekly scan failed: {weekly_response.status_code}")
        try:
            error_data = weekly_response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Response: {weekly_response.text[:500]}")
    
    # Step 4: Test scanning with NEXT_WEEKLY expiry
    print("\n" + "=" * 70)
    print("🔍 Step 4: Testing NEXT_WEEKLY Expiry Scan...")
    print("=" * 70)
    
    next_weekly_url = f"{api_url}/options/scan?index=NIFTY&expiry=next_weekly&min_volume=1000&min_oi=10000&strategy=all&include_probability=true&quick_scan=true"
    print(f"   URL: {next_weekly_url}")
    
    next_weekly_response = requests.get(next_weekly_url, headers=headers)
    if next_weekly_response.ok:
        data = next_weekly_response.json()
        print(f"\n📊 Next Weekly Scan Result:")
        print(f"   Status: {data.get('status')}")
        print(f"   Expiry Date: {data.get('market_data', {}).get('expiry_date')}")
        print(f"   Days to Expiry: {data.get('market_data', {}).get('days_to_expiry')}")
        
        # Check if EXPIRY_DAY_AVOID was triggered incorrectly
        if data.get('actionable_signal', {}).get('signal') == 'EXPIRY_DAY_AVOID':
            print(f"   ❌ BUG! EXPIRY_DAY_AVOID should NOT trigger for next_weekly!")
            print(f"   Signal: {data.get('actionable_signal', {}).get('action')}")
            print(f"   Expiry Info: {data.get('actionable_signal', {}).get('option', {}).get('expiry_info')}")
        else:
            print(f"   ✅ Signal: {data.get('actionable_signal', {}).get('action', 'N/A')}")
    else:
        print(f"❌ Next weekly scan failed: {next_weekly_response.status_code}")
        try:
            error_data = next_weekly_response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Response: {next_weekly_response.text[:500]}")
    
    # Step 5: Test with specific date
    print("\n" + "=" * 70)
    print("🔍 Step 5: Testing with Specific Date (2026-02-10)...")
    print("=" * 70)
    
    specific_url = f"{api_url}/options/scan?index=NIFTY&expiry=2026-02-10&min_volume=1000&min_oi=10000&strategy=all&include_probability=true&quick_scan=true"
    print(f"   URL: {specific_url}")
    
    specific_response = requests.get(specific_url, headers=headers)
    if specific_response.ok:
        data = specific_response.json()
        print(f"\n📊 Specific Date Scan Result:")
        print(f"   Status: {data.get('status')}")
        print(f"   Expiry Date: {data.get('market_data', {}).get('expiry_date')}")
        print(f"   Days to Expiry: {data.get('market_data', {}).get('days_to_expiry')}")
        
        if data.get('actionable_signal', {}).get('signal') == 'EXPIRY_DAY_AVOID':
            print(f"   ❌ BUG! EXPIRY_DAY_AVOID should NOT trigger for Feb 10!")
            print(f"   Signal: {data.get('actionable_signal', {}).get('action')}")
        else:
            print(f"   ✅ Signal: {data.get('actionable_signal', {}).get('action', 'N/A')}")
    else:
        print(f"❌ Specific date scan failed: {specific_response.status_code}")
    
    print("\n" + "=" * 70)
    print("✅ Expiry Selection Debug Test Complete")
    print("=" * 70)
    
    # Step 6: Test the actionable signal endpoint with next_weekly
    print("\n" + "=" * 70)
    print("🔍 Step 6: Testing Actionable Signal with NEXT_WEEKLY...")
    print("=" * 70)
    
    signal_url = f"{api_url}/signals/NSE:NIFTY50-INDEX/actionable?expiry=next_weekly"
    print(f"   URL: {signal_url}")
    
    signal_response = requests.get(signal_url, headers=headers)
    if signal_response.ok:
        data = signal_response.json()
        print(f"\n📊 Actionable Signal (next_weekly):")
        
        # Check the expiry info in the signal
        option_info = data.get('option', {})
        expiry_info = option_info.get('expiry_info', {})
        
        print(f"   Signal: {data.get('signal', data.get('action', 'N/A'))}")
        print(f"   Expiry Date: {option_info.get('expiry_date', 'N/A')}")
        print(f"   Days to Expiry: {expiry_info.get('days_to_expiry', 'N/A')}")
        print(f"   Is Expiry Day: {expiry_info.get('is_expiry_day', 'N/A')}")
        
        if data.get('signal') == 'EXPIRY_DAY_AVOID':
            print(f"   ❌ BUG! EXPIRY_DAY_AVOID should NOT trigger for next_weekly!")
            print(f"   Action: {data.get('action')}")
        else:
            print(f"   ✅ No expiry day block - Signal can be generated")
            print(f"   Strike: {option_info.get('strike', 'N/A')}")
            print(f"   Type: {option_info.get('type', 'N/A')}")
    else:
        print(f"❌ Signal request failed: {signal_response.status_code}")
        try:
            print(f"   Error: {signal_response.json()}")
        except:
            print(f"   Response: {signal_response.text[:500]}")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_expiry_flow())
