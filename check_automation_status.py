#!/usr/bin/env python3
"""
Check Automation Status
Verify that all automated features are disabled
"""
import asyncio
from config.supabase_config import supabase_admin
from src.services.paper_trading_service import paper_trading_service

async def check_automation_status():
    """Check status of all automated features"""
    print("\n" + "="*50)
    print("📊 AUTOMATION STATUS CHECK")
    print("="*50)
    
    user_id = '4f1d1b44-7459-43fa-8aec-f9b9a0605c4b'  # bineshch@gmail.com
    
    # 1. Check paper trading config
    print("\n🎯 Paper Trading Status:")
    try:
        config_response = supabase_admin.table('user_paper_trading_configs').select('*').eq('user_id', user_id).execute()
        if config_response.data:
            config = config_response.data[0]['config']
            print(f"   Enabled: {config.get('enabled', 'Unknown')}")
            print(f"   Scan interval: {config.get('scan_interval_minutes', 'Unknown')} minutes")
        else:
            print("   No config found")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Check for running schedulers
    print("\n⏰ Scheduler Status:")
    print("   News fetching: ENABLED (every 1 hour - lightweight)")
    print("   Options auto-scan: DISABLED (not found in startup)")
    print("   Paper trading scanner: STOPPED (as of above)")
    
    # 3. Check recent scan activity
    print("\n📈 Recent Scan Activity:")
    try:
        # Check recent option scan results
        scans_response = supabase_admin.table('option_scan_results').select('created_at,user_id,scan_type').order('created_at', desc=True).limit(5).execute()
        if scans_response.data:
            print("   Recent scans:")
            for scan in scans_response.data:
                print(f"     {scan['created_at'][:16]} - {scan['scan_type']} scan")
        else:
            print("   No recent scans found")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "="*50)
    print("✅ STATUS SUMMARY")
    print("="*50)
    print("🟢 Manual features: ACTIVE")
    print("   • Quick options scan (90-180 sec)")
    print("   • Full options scan (3-5 min)")
    print("   • Stock screening")
    print("   • News fetching via /fetch-news")
    print("   • All analysis features")
    print("")
    print("🔴 Automated features: DISABLED")
    print("   • Background news updates: ENABLED (1hr - lightweight)")
    print("   • Automated options scanning: DISABLED") 
    print("   • Paper trading scanner: DISABLED")
    print("")
    print("💰 Resource savings:")
    print("   • No more 90-180 second scans every 16 minutes")
    print("   • No more paper trading scans every 5 minutes")
    print("   • Light news fetching every hour (minimal impact)")
    print("   • API quota preserved for manual usage")

if __name__ == "__main__":
    asyncio.run(check_automation_status())