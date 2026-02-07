#!/usr/bin/env python3
"""
Test the enhanced Top-Down ICT Analysis with AMD Detection

This script:
1. Connects to Fyers via Supabase token
2. Runs the new TopDownICTAnalyzer on NIFTY
3. Shows the complete analysis hierarchy
4. Compares with existing scan results
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_section(text):
    print("\n" + "-" * 60)
    print(f"  {text}")
    print("-" * 60)


def main():
    print_header("TOP-DOWN ICT ANALYSIS WITH AMD DETECTION - TEST")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # ========================================================================
    # STEP 1: Connect to Fyers
    # ========================================================================
    print_section("Step 1: Connecting to Fyers")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Get token
    response = supabase.table("fyers_tokens").select("*").order("updated_at", desc=True).limit(1).execute()
    
    if not response.data:
        print("❌ No Fyers token found!")
        return
    
    token_data = response.data[0]
    access_token = token_data["access_token"]
    print(f"✅ Token found for user {token_data.get('user_id', '')[:8]}...")
    
    # Initialize Fyers client
    from src.api.fyers_client import fyers_client
    fyers_client.access_token = access_token
    fyers_client._initialize_client()
    
    # Verify
    try:
        profile = fyers_client.get_profile()
        if profile.get("code") == 200 or profile.get("s") == "ok":
            print(f"✅ Fyers connected: {profile.get('data', {}).get('name', 'User')}")
        else:
            print(f"⚠️ Token may be expired: {profile}")
    except Exception as e:
        print(f"⚠️ Could not verify token: {e}")
    
    # ========================================================================
    # STEP 2: Run Top-Down Analysis
    # ========================================================================
    print_section("Step 2: Running Top-Down ICT Analysis")
    
    from src.analytics.topdown_ict_amd import get_topdown_analyzer
    
    analyzer = get_topdown_analyzer(fyers_client)
    
    symbol = "NSE:NIFTY50-INDEX"
    
    try:
        result = analyzer.analyze(symbol)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ========================================================================
    # STEP 3: Display Results
    # ========================================================================
    print_header("ANALYSIS RESULTS")
    
    # HTF Analysis
    print_section("HTF (Monthly/Weekly) - Bias & Liquidity Zones")
    print(f"   HTF Bias: {result.htf_bias.upper()}")
    print(f"   Key Levels:")
    for level_name, level_value in result.htf_key_levels.items():
        if level_value:
            print(f"      {level_name}: {level_value:.2f}")
    
    print(f"\n   Liquidity Zones ({len(result.htf_liquidity_zones)}):")
    for zone in result.htf_liquidity_zones[:5]:
        distance_pct = abs(zone.level - result.current_price) / result.current_price * 100
        print(f"      {zone.zone_type.upper()}: {zone.level:.2f} ({distance_pct:.1f}% away) - {zone.touches} touches, TF: {zone.timeframe}")
    
    # MTF Analysis
    print_section("MTF (Daily/4H) - Range & Session")
    print(f"   Session: {result.mtf_session}")
    print(f"   Phase: {result.mtf_phase.upper()}")
    print(f"   4H Range:")
    print(f"      High: {result.mtf_range.range_high:.2f}")
    print(f"      Mid:  {result.mtf_range.range_mid:.2f}")
    print(f"      Low:  {result.mtf_range.range_low:.2f}")
    print(f"   Current Position: {result.mtf_range.current_position.upper()}")
    print(f"   Expansion Phase: {'YES' if result.mtf_range.expansion_phase else 'NO'}")
    
    # LTF Analysis + AMD
    print_section("LTF (1H-1min) - AMD Detection & Entry Zones")
    
    print(f"\n   📊 AMD Phases Detected ({len(result.ltf_amd_phases)}):")
    for phase in result.ltf_amd_phases[:5]:
        print(f"      {phase.manipulation_type}: Level={phase.key_level:.2f}, Conf={phase.confidence:.0f}%, Signal={phase.trade_signal}")
        print(f"         Time: {phase.start_time}")
    
    if result.active_manipulation:
        print(f"\n   ⚠️ ACTIVE MANIPULATION:")
        print(f"      Type: {result.active_manipulation.manipulation_type}")
        print(f"      Level: {result.active_manipulation.key_level:.2f}")
        print(f"      Signal: {result.active_manipulation.trade_signal}")
        print(f"      Confidence: {result.active_manipulation.confidence:.0f}%")
    
    print(f"\n   🎯 Entry Zones ({len(result.ltf_entry_zones)}):")
    for ez in result.ltf_entry_zones[:3]:
        print(f"      {ez.entry_type} @ {ez.entry_price:.2f}")
        print(f"         Direction: {ez.direction.upper()}")
        print(f"         Zone: {ez.zone_low:.2f} - {ez.zone_high:.2f}")
        print(f"         SL: {ez.stop_loss:.2f}, T1: {ez.target_1:.2f}, T2: {ez.target_2:.2f}")
        print(f"         Confidence: {ez.confidence:.0f}%")
        print(f"         Trigger: {ez.trigger_condition}")
    
    # Final Signal
    print_section("FINAL SIGNAL")
    print(f"   🎯 Action: {result.recommended_action}")
    print(f"   📊 Confidence: {result.confidence:.1f}%")
    print(f"   📝 Reasoning: {result.reasoning}")
    
    if result.entry_zone:
        print(f"\n   📍 Entry Details:")
        print(f"      Type: {result.entry_zone.entry_type}")
        print(f"      Entry: {result.entry_zone.entry_price:.2f}")
        print(f"      Stop Loss: {result.entry_zone.stop_loss:.2f}")
        print(f"      Target 1: {result.entry_zone.target_1:.2f}")
        print(f"      Target 2: {result.entry_zone.target_2:.2f}")
    
    # ========================================================================
    # STEP 4: Compare with Existing App Scans
    # ========================================================================
    print_header("COMPARISON WITH EXISTING APP SCANS")
    
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    
    try:
        scan_response = supabase.table("option_scanner_results").select("*").gte("created_at", today_start.isoformat()).eq("index", "NIFTY").order("created_at", desc=True).limit(5).execute()
        
        if scan_response.data:
            print(f"\n   Recent App Scans ({len(scan_response.data)} shown):")
            
            for scan in scan_response.data:
                scan_time = scan.get('created_at', '')[:19]
                action = scan.get('action', 'N/A')
                signal = scan.get('signal', 'N/A')
                option_type = scan.get('option_type', 'N/A')
                confidence = scan.get('confidence', 0)
                
                print(f"\n      {scan_time}")
                print(f"         Signal: {signal}")
                print(f"         Action: {action} {option_type}")
                print(f"         Confidence: {confidence}%")
            
            # Compare
            print(f"\n   📊 COMPARISON:")
            
            latest_scan = scan_response.data[0]
            latest_action = latest_scan.get('action', 'WAIT')
            latest_option = latest_scan.get('option_type', 'N/A')
            
            new_action = result.recommended_action
            
            if "CALL" in new_action and latest_option == "CE":
                print(f"      ✅ AGREEMENT: Both suggest CALL")
            elif "PUT" in new_action and latest_option == "PE":
                print(f"      ✅ AGREEMENT: Both suggest PUT")
            elif new_action == "WAIT" and latest_action == "WAIT":
                print(f"      ✅ AGREEMENT: Both suggest WAIT")
            else:
                print(f"      ⚠️ DIFFERENCE DETECTED:")
                print(f"         Old App: {latest_action} {latest_option}")
                print(f"         New AMD: {new_action}")
                
                if result.active_manipulation:
                    print(f"\n      💡 NEW INSIGHT: AMD detected {result.active_manipulation.manipulation_type}")
                    print(f"         This is a COUNTER-TRADE opportunity the old app missed!")
        else:
            print("   No recent scans found for comparison")
            
    except Exception as e:
        print(f"   ⚠️ Could not fetch scans: {e}")
    
    print_header("TEST COMPLETE")


if __name__ == "__main__":
    main()
