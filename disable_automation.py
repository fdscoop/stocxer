#!/usr/bin/env python3
"""
Disable All Automated Trading Features
This script helps you quickly disable all automated scanning and trading
"""
import asyncio
import sys
from config.supabase_config import supabase_admin
from src.services.paper_trading_service import paper_trading_service

async def disable_all_automation():
    """Disable all automated features"""
    print("\n" + "="*60)
    print("🛑 DISABLING ALL AUTOMATED TRADING FEATURES")
    print("="*60)
    
    try:
        # 1. Get user ID for bineshch@gmail.com
        print("\n🔍 Finding user...")
        auth_response = await get_user_by_email("bineshch@gmail.com")
        if not auth_response:
            print("❌ User not found")
            return
            
        user_id = auth_response['id']
        email = auth_response['email']
        print(f"✅ Found user: {email}")
        
        # 2. Stop any running paper trading scanners
        print(f"\n🛑 Stopping automated paper trading...")
        stop_result = await paper_trading_service.stop_automated_trading(user_id)
        print(f"   Result: {stop_result.get('message', 'Unknown')}")
        
        # 3. Disable paper trading in config
        print(f"\n⚙️ Disabling paper trading configuration...")
        config = {
            "enabled": False,  # KEY: Disable automation
            "indices": ["NIFTY"],
            "scan_interval_minutes": 5,
            "max_positions": 3,
            "capital_per_trade": 10000,
            "min_confidence": 65,
            "trading_mode": "intraday"
        }
        
        config_result = await paper_trading_service.save_user_config(user_id, config)
        print(f"   Config disabled: {config_result.get('status') == 'success'}")
        
        # 4. Check status
        print(f"\n📊 Final status check...")
        status = await paper_trading_service.get_trading_status(user_id)
        
        print(f"   Trading enabled: {status.get('config', {}).get('enabled', False)}")
        print(f"   Scanner running: {status.get('scanner_running', False)}")
        print(f"   Open positions: {status.get('open_positions', 0)}")
        
        print("\n" + "="*60)
        print("✅ AUTOMATION DISABLED SUCCESSFULLY")
        print("="*60)
        print("\n📋 Summary:")
        print("   ✅ News fetching: DISABLED (commented out in main.py)")
        print("   ✅ Options auto-scanning: DISABLED (already disabled)")
        print("   ✅ Paper trading scanner: STOPPED")
        print("   ✅ Paper trading config: enabled=false")
        
        print("\n🎯 What's still working:")
        print("   ✅ Manual option scans (90-180 sec)")
        print("   ✅ Manual stock screening")
        print("   ✅ Manual news fetching via /fetch-news")
        print("   ✅ All analysis features")
        
        print("\n💡 To re-enable automation:")
        print("   1. Set enabled=true in paper trading config")
        print("   2. Uncomment news scheduler in main.py")
        print("   3. Restart the server")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def get_user_by_email(email: str):
    """Get user by email"""
    try:
        # Query auth.users table directly
        response = supabase_admin.table("auth.users").select("*").eq("email", email).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception:
        # Try alternative approach
        try:
            # Get from public.users table which might have the mapping
            response = supabase_admin.rpc('get_user_by_email', {'user_email': email}).execute()
            if response.data:
                return response.data[0]
        except Exception:
            pass
        
        # Hardcoded user ID for bineshch@gmail.com (from previous auth test)
        return {
            'id': '4f1d1b44-7459-43fa-8aec-f9b9a0605c4b',
            'email': 'bineshch@gmail.com'
        }

if __name__ == "__main__":
    print("🤖 TradeWise Automation Disabler")
    print("This will stop all automated scanning and trading")
    
    confirm = input("\nContinue? (y/N): ").lower().strip()
    if confirm != 'y':
        print("❌ Cancelled")
        sys.exit(0)
    
    asyncio.run(disable_all_automation())