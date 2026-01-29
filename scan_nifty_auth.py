#!/usr/bin/env python3
"""
Authenticated NIFTY scan through terminal
Logs in with Supabase credentials and gets Fyers token
"""

import requests
import json
from datetime import datetime, timedelta

# API endpoint
BASE_URL = "http://localhost:8000"

# User credentials
EMAIL = "bineshch@gmail.com"
PASSWORD = "Tra@2026"

def login():
    """Login with Supabase and get access token"""
    print("🔐 Logging in...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EMAIL,
                "password": PASSWORD
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get("access_token")
            
            if access_token:
                print(f"✅ Login successful!")
                print(f"   User: {EMAIL}")
                return access_token
            else:
                print(f"❌ Login failed: No access token in response")
                print(f"   Response: {result}")
                return None
        else:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def check_fyers_status(access_token):
    """Check if Fyers token exists"""
    print("\n🔍 Checking Fyers token status...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/fyers/status",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Fyers status: {result.get('status', 'unknown')}")
            return result.get("status") == "active"
        else:
            print(f"⚠️ Could not check Fyers status")
            return False
            
    except Exception as e:
        print(f"⚠️ Fyers status check error: {e}")
        return False

def scan_nifty_authenticated(access_token):
    """Perform authenticated NIFTY scan"""
    print("\n" + "=" * 70)
    print("🚀 SCANNING NIFTY (Authenticated)")
    print("=" * 70)
    
    # Calculate next expiry (Thursday)
    today = datetime.now()
    days_ahead = 3 - today.weekday()  # Thursday is 3
    if days_ahead <= 0:
        days_ahead += 7
    next_expiry = today + timedelta(days=days_ahead)
    expiry_date = next_expiry.strftime("%Y-%m-%d")
    
    print(f"\n📅 Target Expiry: {expiry_date}")
    print(f"🔍 Analyzing NIFTY with constituent stocks...")
    print()
    
    # Make authenticated API request
    try:
        response = requests.get(
            f"{BASE_URL}/index/probability/NIFTY",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "include_ml": True,
                "include_stocks": True,
                "include_sectors": True
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ ANALYSIS COMPLETE")
            print("=" * 70)
            
            # Display prediction
            prediction = result.get("prediction", {})
            print(f"\n📊 INDEX PREDICTION:")
            print(f"   Direction: {prediction.get('direction', 'N/A')}")
            print(f"   Confidence: {prediction.get('confidence', 0):.1%}")
            print(f"   Expected Move: {prediction.get('expected_move_pct', 0):.2f}%")
            
            # Market regime
            regime = result.get("regime", {})
            print(f"\n🌡️ MARKET REGIME:")
            print(f"   Type: {regime.get('type', 'N/A')}")
            print(f"   Volatility: {regime.get('volatility', 'N/A')}")
            print(f"   Trading Strategy: {regime.get('recommended_strategy', 'N/A')}")
            
            # Sector analysis
            sectors = result.get("sectors", [])
            if sectors:
                print(f"\n🏢 TOP SECTORS ({len(sectors)} total):")
                for sector in sectors[:5]:  # Top 5
                    print(f"   {sector.get('sector_name', 'N/A')}: "
                          f"{sector.get('bullish_pct', 0):.0f}% bullish, "
                          f"{sector.get('weight', 0):.1f}% weight")
            
            # Stock signals
            stocks = result.get("stock_signals", [])
            if stocks:
                print(f"\n📈 TOP BULLISH STOCKS:")
                bullish = [s for s in stocks if s.get('signal_strength', 0) > 0][:5]
                for stock in bullish:
                    print(f"   {stock.get('symbol', 'N/A')}: "
                          f"Strength {stock.get('signal_strength', 0):.2f}, "
                          f"Prob {stock.get('probability', 0):.0%}")
                
                print(f"\n📉 TOP BEARISH STOCKS:")
                bearish = [s for s in stocks if s.get('signal_strength', 0) < 0][:5]
                for stock in bearish:
                    print(f"   {stock.get('symbol', 'N/A')}: "
                          f"Strength {stock.get('signal_strength', 0):.2f}, "
                          f"Prob {stock.get('probability', 0):.0%}")
            
            # ML optimization
            ml_opt = result.get("ml_optimization", {})
            if ml_opt and not ml_opt.get("error"):
                print(f"\n🤖 ML OPTIMIZATION:")
                print(f"   Optimized Direction: {ml_opt.get('optimized_direction', 'N/A')}")
                print(f"   Optimized Confidence: {ml_opt.get('optimized_confidence', 0):.1%}")
                print(f"   Improvement: {ml_opt.get('improvement_pct', 0):.1f}%")
            
            # Summary
            summary = result.get("summary", {})
            print(f"\n📋 SUMMARY:")
            print(f"   Total Stocks Analyzed: {summary.get('total_stocks', 0)}")
            print(f"   Bullish: {summary.get('bullish_count', 0)}")
            print(f"   Bearish: {summary.get('bearish_count', 0)}")
            print(f"   Neutral: {summary.get('neutral_count', 0)}")
            
            # Save full result
            with open("nifty_analysis_result.json", "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Full result saved to: nifty_analysis_result.json")
            
            return result
            
        elif response.status_code == 401:
            print("❌ Authentication failed - token may be expired")
            print("   Try logging in again")
        elif response.status_code == 403:
            print("❌ Access forbidden - check Fyers authentication")
        else:
            print(f"❌ Scan failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
        return None
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - scan may take longer")
        print("   Try increasing timeout or check backend logs")
        return None
    except Exception as e:
        print(f"❌ Scan error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("=" * 70)
    print("🎯 AUTHENTICATED NIFTY ANALYSIS")
    print("=" * 70)
    print()
    
    # Step 1: Login
    access_token = login()
    if not access_token:
        print("\n❌ Cannot proceed without authentication")
        return
    
    # Step 2: Check Fyers
    has_fyers = check_fyers_status(access_token)
    if not has_fyers:
        print("\n⚠️ Warning: Fyers token may not be active")
        print("   Scan may use cached/historical data")
    
    # Step 3: Scan NIFTY
    result = scan_nifty_authenticated(access_token)
    
    if result:
        print("\n" + "=" * 70)
        print("✅ SCAN COMPLETED SUCCESSFULLY")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ SCAN FAILED")
        print("=" * 70)

if __name__ == "__main__":
    main()
