#!/usr/bin/env python3
"""
Test NIFTY scan as a real user would - checking all calculations
Test both nearest expiry (weekly) and next week expiry
"""
import sys
import os
import json
from datetime import datetime
from pytz import timezone as pytz_timezone

sys.path.insert(0, '/Users/bineshbalan/TradeWise')

from dotenv import load_dotenv
load_dotenv('/Users/bineshbalan/TradeWise/.env', override=True)

import requests

IST = pytz_timezone('Asia/Kolkata')

def get_ist_now():
    return datetime.now(IST)

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def verify_calculations(data, expiry_type):
    """Verify all calculations in the scan response"""
    issues = []
    
    market_data = data.get('market_data', {})
    actionable = data.get('actionable_signal', {})
    prob_analysis = data.get('probability_analysis', {})
    
    # Check DTE calculation
    expiry_date_str = market_data.get('expiry_date')
    days_to_expiry = market_data.get('days_to_expiry')
    
    if expiry_date_str and days_to_expiry is not None:
        try:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            today_ist = get_ist_now().date()
            calculated_dte = (expiry_date - today_ist).days
            
            if abs(calculated_dte - days_to_expiry) > 1:
                issues.append(f"❌ DTE mismatch: API says {days_to_expiry}, calculated {calculated_dte}")
            else:
                print(f"   ✅ DTE correct: {days_to_expiry} days (expiry: {expiry_date_str})")
        except Exception as e:
            issues.append(f"❌ Could not verify DTE: {e}")
    
    # Check EXPIRY_DAY_AVOID logic
    signal = actionable.get('signal', '')
    if days_to_expiry is not None:
        if days_to_expiry <= 1 and signal != 'EXPIRY_DAY_AVOID':
            issues.append(f"❌ DTE={days_to_expiry} but signal is not EXPIRY_DAY_AVOID: {signal}")
        elif days_to_expiry > 1 and signal == 'EXPIRY_DAY_AVOID':
            issues.append(f"❌ DTE={days_to_expiry} but got EXPIRY_DAY_AVOID (BUG!)")
        else:
            if signal == 'EXPIRY_DAY_AVOID':
                print(f"   ✅ Correctly returned EXPIRY_DAY_AVOID for DTE={days_to_expiry}")
            else:
                print(f"   ✅ Correctly returned {signal} for DTE={days_to_expiry}")
    
    # Check spot price and ATM strike
    spot_price = market_data.get('spot_price')
    atm_strike = market_data.get('atm_strike')
    
    if spot_price and atm_strike:
        # ATM should be closest strike to spot (typically within 50 points for NIFTY)
        diff = abs(spot_price - atm_strike)
        if diff > 100:
            issues.append(f"❌ ATM strike {atm_strike} too far from spot {spot_price} (diff: {diff})")
        else:
            print(f"   ✅ ATM strike {atm_strike} close to spot {spot_price:.2f} (diff: {diff:.2f})")
    
    # Check PCR OI
    pcr_oi = market_data.get('pcr_oi')
    if pcr_oi:
        if pcr_oi < 0.3 or pcr_oi > 3.0:
            issues.append(f"❌ PCR OI {pcr_oi} seems out of normal range (0.3-3.0)")
        else:
            print(f"   ✅ PCR OI {pcr_oi:.2f} in normal range")
    
    # Check probability analysis
    if prob_analysis:
        prob_up = prob_analysis.get('probability_up', 0)
        prob_down = prob_analysis.get('probability_down', 0)
        
        # Probabilities should sum close to 1 (allowing for neutral)
        if prob_up + prob_down > 1.1:
            issues.append(f"❌ Probabilities don't make sense: up={prob_up}, down={prob_down}")
        else:
            print(f"   ✅ Probability up: {prob_up:.1%}, down: {prob_down:.1%}")
        
        stocks_scanned = prob_analysis.get('stocks_scanned', 0)
        if stocks_scanned > 0:
            print(f"   ✅ Analyzed {stocks_scanned} constituent stocks")
    
    # Check options data
    options = data.get('options', [])
    if options:
        print(f"   ✅ Found {len(options)} options in scan results")
        
        # Check top option
        top_option = options[0]
        if top_option.get('score', 0) < 0 or top_option.get('score', 0) > 200:
            issues.append(f"❌ Top option score {top_option.get('score')} seems wrong")
        else:
            print(f"   ✅ Top option: {top_option.get('strike')} {top_option.get('type')} with score {top_option.get('score'):.1f}")
    
    # Check targets if signal is not AVOID
    if signal != 'EXPIRY_DAY_AVOID' and actionable:
        targets = actionable.get('targets', {})
        entry_price = actionable.get('entry', {}).get('price', 0)
        target_1 = targets.get('target_1', 0)
        stop_loss = targets.get('stop_loss', 0)
        
        if entry_price > 0:
            if target_1 <= entry_price:
                issues.append(f"❌ Target 1 ({target_1}) <= Entry ({entry_price})")
            else:
                print(f"   ✅ Targets valid: Entry ₹{entry_price:.0f} → T1 ₹{target_1:.0f} → SL ₹{stop_loss:.0f}")
    
    return issues

def run_scan(api_url, token, expiry_type, expiry_label):
    """Run a scan and verify results"""
    print_section(f"SCANNING NIFTY - {expiry_label} ({expiry_type})")
    
    url = f"{api_url}/options/scan?index=NIFTY&expiry={expiry_type}&min_volume=1000&min_oi=10000&strategy=all&include_probability=true&quick_scan=true"
    
    print(f"\n📡 Request URL: {url}")
    print(f"⏰ Current IST: {get_ist_now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=120)
        
        if response.ok:
            data = response.json()
            
            print(f"\n📊 SCAN RESULTS:")
            print(f"   Status: {data.get('status')}")
            print(f"   Scan Mode: {data.get('scan_mode')}")
            print(f"   Index: {data.get('index')}")
            
            market_data = data.get('market_data', {})
            print(f"\n📈 MARKET DATA:")
            print(f"   Spot Price: ₹{market_data.get('spot_price', 'N/A')}")
            print(f"   Expiry Date: {market_data.get('expiry_date', 'N/A')}")
            print(f"   Days to Expiry: {market_data.get('days_to_expiry', 'N/A')}")
            print(f"   ATM Strike: {market_data.get('atm_strike', 'N/A')}")
            print(f"   VIX: {market_data.get('vix', 'N/A')}")
            print(f"   PCR OI: {market_data.get('pcr_oi', 'N/A')}")
            
            actionable = data.get('actionable_signal', {})
            if actionable:
                print(f"\n🎯 ACTIONABLE SIGNAL:")
                print(f"   Signal: {actionable.get('signal', 'N/A')}")
                print(f"   Action: {actionable.get('action', 'N/A')}")
                
                option_info = actionable.get('option', {})
                if option_info:
                    print(f"   Option: {option_info.get('strike')} {option_info.get('type')}")
                    print(f"   Expiry: {option_info.get('expiry_date')} ({option_info.get('expiry_info', {}).get('days_to_expiry')} days)")
                
                targets = actionable.get('targets', {})
                if targets and targets.get('target_1'):
                    print(f"   Target 1: ₹{targets.get('target_1')}")
                    print(f"   Target 2: ₹{targets.get('target_2')}")
                    print(f"   Stop Loss: ₹{targets.get('stop_loss')}")
                
                warnings = actionable.get('warnings', [])
                if warnings:
                    print(f"\n⚠️  WARNINGS:")
                    for w in warnings[:3]:
                        print(f"      {w}")
            
            prob = data.get('probability_analysis', {})
            if prob:
                print(f"\n📊 PROBABILITY ANALYSIS:")
                print(f"   Direction: {prob.get('expected_direction', 'N/A')}")
                print(f"   Prob Up: {prob.get('probability_up', 0):.1%}")
                print(f"   Prob Down: {prob.get('probability_down', 0):.1%}")
                print(f"   Stocks Analyzed: {prob.get('stocks_scanned', 0)}/{prob.get('total_stocks', 0)}")
            
            # Verify calculations
            print(f"\n🔍 VERIFICATION:")
            issues = verify_calculations(data, expiry_type)
            
            if issues:
                print(f"\n❌ ISSUES FOUND ({len(issues)}):")
                for issue in issues:
                    print(f"   {issue}")
            else:
                print(f"\n✅ ALL CALCULATIONS VERIFIED - NO ISSUES!")
            
            return data, issues
            
        else:
            print(f"❌ Scan failed: HTTP {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {json.dumps(error, indent=2)[:500]}")
            except:
                print(f"   Response: {response.text[:500]}")
            return None, [f"HTTP {response.status_code}"]
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None, [str(e)]

def main():
    print_section("NIFTY SCAN TEST - USER SIMULATION")
    print(f"Current IST: {get_ist_now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Today: {get_ist_now().strftime('%A, %B %d, %Y')}")
    
    # Authenticate
    email = os.getenv('TEST_USER_EMAIL')
    password = os.getenv('TEST_USER_PASSWORD')
    
    if not email or not password:
        print("❌ TEST_USER_EMAIL and TEST_USER_PASSWORD must be set in .env")
        return
    
    print(f"\n🔐 Authenticating as: {email}")
    
    from config.supabase_config import supabase_admin
    try:
        auth_response = supabase_admin.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        token = auth_response.session.access_token
        print(f"✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Use production API
    api_url = os.getenv('TRADEWISE_API_URL', 'https://stocxer-484044910258.europe-west1.run.app')
    print(f"📡 Using API: {api_url}")
    
    # First, get available expiries
    print_section("FETCHING AVAILABLE EXPIRIES")
    try:
        expiry_response = requests.get(f"{api_url}/index/NIFTY/expiries")
        if expiry_response.ok:
            expiries = expiry_response.json().get('expiries', {})
            print(f"   Weekly: {expiries.get('weekly')} ({expiries.get('weekly_days')} days)")
            print(f"   Next Weekly: {expiries.get('next_weekly')} ({expiries.get('next_weekly_days')} days)")
            print(f"   Monthly: {expiries.get('monthly')} ({expiries.get('monthly_days')} days)")
    except Exception as e:
        print(f"❌ Failed to fetch expiries: {e}")
    
    # Test 1: Weekly (nearest) expiry
    weekly_result, weekly_issues = run_scan(api_url, token, "weekly", "WEEKLY (Nearest)")
    
    # Test 2: Next weekly expiry
    next_weekly_result, next_weekly_issues = run_scan(api_url, token, "next_weekly", "NEXT WEEKLY")
    
    # Summary
    print_section("TEST SUMMARY")
    
    print("\n📋 WEEKLY EXPIRY TEST:")
    if weekly_issues:
        print(f"   ❌ {len(weekly_issues)} issues found")
        for issue in weekly_issues:
            print(f"      - {issue}")
    else:
        print("   ✅ All calculations correct!")
        if weekly_result:
            signal = weekly_result.get('actionable_signal', {}).get('signal', 'N/A')
            dte = weekly_result.get('market_data', {}).get('days_to_expiry', 'N/A')
            print(f"   Signal: {signal} (DTE: {dte})")
    
    print("\n📋 NEXT WEEKLY EXPIRY TEST:")
    if next_weekly_issues:
        print(f"   ❌ {len(next_weekly_issues)} issues found")
        for issue in next_weekly_issues:
            print(f"      - {issue}")
    else:
        print("   ✅ All calculations correct!")
        if next_weekly_result:
            signal = next_weekly_result.get('actionable_signal', {}).get('signal', 'N/A')
            dte = next_weekly_result.get('market_data', {}).get('days_to_expiry', 'N/A')
            print(f"   Signal: {signal} (DTE: {dte})")
    
    # Final verdict
    total_issues = len(weekly_issues) + len(next_weekly_issues)
    if total_issues == 0:
        print("\n" + "🎉" * 20)
        print("  ALL TESTS PASSED - EXPIRY SELECTION WORKING CORRECTLY!")
        print("🎉" * 20)
    else:
        print(f"\n⚠️  {total_issues} total issues need attention")

if __name__ == "__main__":
    main()
