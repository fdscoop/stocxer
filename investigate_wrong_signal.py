"""
Investigate why the scanner gave wrong PUT signals at 12:30 PM
when market was actually going bullish.

User: bineshch@gmail.com
Issue: PUT recommendations for SENSEX 82000 and NIFTY 25200 when market went to 82600
"""
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

async def investigate():
    print("=" * 80)
    print("INVESTIGATING WRONG SIGNAL ISSUE")
    print("=" * 80)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Find user
    print("\n1. Finding user bineshch@gmail.com...")
    users = supabase.table("profiles").select("*").eq("email", "bineshch@gmail.com").execute()
    
    if not users.data:
        # Try auth.users approach
        print("   User not in profiles, checking auth...")
        # List all users to find
        all_profiles = supabase.table("profiles").select("*").execute()
        print(f"   Found {len(all_profiles.data)} profiles")
        for p in all_profiles.data:
            print(f"   - {p.get('email', 'no-email')}: {p.get('id', 'no-id')[:8]}...")
        return
    
    user = users.data[0]
    user_id = user.get("id")
    print(f"   Found user: {user.get('email')} (ID: {user_id[:8]}...)")
    
    # Check scan_results table
    print("\n2. Checking scan_results table...")
    try:
        scans = supabase.table("scan_results").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(20).execute()
        if scans.data:
            print(f"   Found {len(scans.data)} recent scans")
            for scan in scans.data[:10]:
                created = scan.get("created_at", "")[:19]
                index = scan.get("index", "?")
                direction = scan.get("direction", "?")
                print(f"   - {created}: {index} → {direction}")
        else:
            print("   No scan results found in scan_results table")
    except Exception as e:
        print(f"   scan_results table error: {e}")
    
    # Check option_scans table
    print("\n3. Checking option_scans table...")
    try:
        option_scans = supabase.table("option_scans").select("*").eq("user_id", user_id).order("scanned_at", desc=True).limit(20).execute()
        if option_scans.data:
            print(f"   Found {len(option_scans.data)} option scans")
            for scan in option_scans.data[:10]:
                scanned = scan.get("scanned_at", "")[:19]
                index = scan.get("index_name", "?")
                direction = scan.get("recommended_direction", "?")
                option_type = scan.get("recommended_option_type", "?")
                prob_up = scan.get("probability_up", 0)
                prob_down = scan.get("probability_down", 0)
                print(f"   - {scanned}: {index} → {direction} ({option_type}) P↑:{prob_up:.1%} P↓:{prob_down:.1%}")
        else:
            print("   No option scans found")
    except Exception as e:
        print(f"   option_scans table error: {e}")
    
    # Check user_scans table
    print("\n4. Checking user_scans table...")
    try:
        user_scans = supabase.table("user_scans").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(20).execute()
        if user_scans.data:
            print(f"   Found {len(user_scans.data)} user scans")
            for scan in user_scans.data[:10]:
                created = scan.get("created_at", "")[:19]
                scan_type = scan.get("scan_type", "?")
                data = scan.get("scan_data", {})
                print(f"   - {created}: {scan_type}")
                if isinstance(data, dict):
                    print(f"     Direction: {data.get('recommended_direction', data.get('direction', '?'))}")
        else:
            print("   No user scans found")
    except Exception as e:
        print(f"   user_scans table error: {e}")
    
    # Check credits_usage for scan records
    print("\n5. Checking credits_usage table...")
    try:
        usage = supabase.table("credits_usage").select("*").eq("user_id", user_id).order("used_at", desc=True).limit(20).execute()
        if usage.data:
            print(f"   Found {len(usage.data)} credit usage records")
            for u in usage.data[:10]:
                used = u.get("used_at", "")[:19]
                action = u.get("action", "?")
                credits = u.get("credits_used", 0)
                print(f"   - {used}: {action} ({credits} credits)")
        else:
            print("   No credit usage found")
    except Exception as e:
        print(f"   credits_usage table error: {e}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    print("""
The issue was at 12:30 PM, market was BULLISH but scanner recommended PUT.

ROOT CAUSE ANALYSIS:
1. Scanner uses 60-day DAILY candles for constituent analysis
2. At 12:30 PM, today's bullish momentum wasn't captured
3. Previous day's bearish close influenced the signal
4. No intraday momentum detection (5-min candles) was used

WHAT WE FIXED:
- Added intraday momentum analysis (5-min candles)
- Added 40-point weight for intraday signals
- BUT: This is only for constituent stocks

WHAT'S STILL MISSING:
- MTF/ICT analysis on INDEX itself during intraday
- FVG detection on 5-min/15-min charts
- Liquidity sweep detection
- Order block analysis for intraday

The long-term signal uses MTF/ICT on the INDEX chart:
- Monthly → Weekly → Daily → 4H → 1H → 15min
- FVG, order blocks, liquidity zones

Intraday scanner should do the same but with:
- Daily → 4H → 1H → 15min → 5min timeframes
- Focus on intraday patterns
""")

if __name__ == "__main__":
    asyncio.run(investigate())
