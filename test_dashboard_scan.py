#!/usr/bin/env python3
"""
Test NIFTY Scan as User from Dashboard
This simulates exactly what happens when a user clicks "Scan" on the dashboard
"""

import os
import json
import requests
from dotenv import load_dotenv
from config.supabase_config import supabase_admin

load_dotenv()

def main():
    print("=" * 80)
    print("🔐 STEP 1: USER AUTHENTICATION")
    print("=" * 80)
    
    email = os.getenv('TEST_USER_EMAIL')
    password = os.getenv('TEST_USER_PASSWORD')
    print(f"Email: {email}")
    
    auth_result = supabase_admin.auth.sign_in_with_password({
        'email': email,
        'password': password
    })
    token = auth_result.session.access_token
    user_id = auth_result.user.id
    print(f"✅ Authenticated! User ID: {user_id[:8]}...")
    print(f"✅ Token obtained (first 50 chars): {token[:50]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # =========================================================================
    # STEP 2: OPTIONS SCAN (what dashboard does first)
    # =========================================================================
    print("\n" + "=" * 80)
    print("📊 STEP 2: OPTIONS SCAN (/options/scan)")
    print("=" * 80)
    
    scan_url = "http://localhost:8000/options/scan"
    params = {
        "index": "NIFTY",
        "expiry": "weekly",
        "min_volume": 1000,
        "min_oi": 10000,
        "strategy": "all",
        "include_probability": "true",
        "quick_scan": "false"
    }
    
    print(f"Calling: {scan_url}")
    print(f"Params: {params}")
    
    scan_response = requests.get(scan_url, headers=headers, params=params, timeout=120)
    print(f"\n📬 Response Status: {scan_response.status_code}")
    
    if scan_response.status_code != 200:
        print(f"❌ Scan failed: {scan_response.text[:500]}")
        return
    
    scan_data = scan_response.json()
    print(f"\n📦 Scan Response Keys: {list(scan_data.keys())}")
    
    # Check MTF Analysis
    if 'mtf_analysis' in scan_data:
        mtf = scan_data['mtf_analysis']
        print(f"\n📈 MTF Analysis:")
        print(f"   - Trend: {mtf.get('trend', 'N/A')}")
        print(f"   - Confluence: {mtf.get('confluence', 'N/A')}")
        print(f"   - Strength: {mtf.get('trend_strength', 'N/A')}")
    
    # Check Probability Analysis
    if 'probability_analysis' in scan_data:
        prob = scan_data['probability_analysis']
        print(f"\n🎯 Probability Analysis:")
        print(f"   - Bias: {prob.get('final_bias', 'N/A')}")
        print(f"   - Confidence: {prob.get('confidence_score', 'N/A')}")
        print(f"   - Action: {prob.get('recommended_action', 'N/A')}")
    
    # Check ICT Analysis
    if 'ict_analysis' in scan_data:
        ict = scan_data['ict_analysis']
        print(f"\n🏛️ ICT Analysis:")
        print(f"   - Market Structure: {ict.get('market_structure', {}).get('trend', 'N/A')}")
        print(f"   - Order Blocks: {len(ict.get('order_blocks', []))}")
        print(f"   - Fair Value Gaps: {len(ict.get('fair_value_gaps', []))}")
    
    spot_price = scan_data.get('spot_price', 'N/A')
    print(f"\n💰 Spot Price: {spot_price}")
    print(f"📅 Expiry: {scan_data.get('expiry', 'N/A')}")
    print(f"📊 Total Options: {len(scan_data.get('options', []))}")
    
    # =========================================================================
    # STEP 3: ACTIONABLE SIGNAL (what dashboard does after scan)
    # =========================================================================
    print("\n" + "=" * 80)
    print("🎯 STEP 3: ACTIONABLE SIGNAL (/signals/NIFTY/actionable)")
    print("=" * 80)
    
    signal_url = "http://localhost:8000/signals/NIFTY/actionable"
    signal_params = {"expiry_type": "weekly"}
    
    print(f"Calling: {signal_url}")
    print(f"Params: {signal_params}")
    
    signal_response = requests.get(signal_url, headers=headers, params=signal_params, timeout=120)
    print(f"\n📬 Response Status: {signal_response.status_code}")
    
    if signal_response.status_code != 200:
        print(f"❌ Signal request failed: {signal_response.text[:500]}")
        return
    
    signal_data = signal_response.json()
    print(f"\n📦 Signal Response Keys: {list(signal_data.keys())}")
    
    # Check actionable signal
    if signal_data.get('has_signal'):
        print(f"\n✅ ACTIONABLE SIGNAL FOUND!")
        print(f"   - Direction: {signal_data.get('direction', 'N/A')}")
        print(f"   - Confidence: {signal_data.get('confidence', 'N/A')}")
        print(f"   - Entry: {signal_data.get('entry_price', 'N/A')}")
        print(f"   - Stop Loss: {signal_data.get('stop_loss', 'N/A')}")
        print(f"   - Target 1: {signal_data.get('target_1', 'N/A')}")
        print(f"   - Target 2: {signal_data.get('target_2', 'N/A')}")
        print(f"   - Risk/Reward: {signal_data.get('risk_reward', 'N/A')}")
        
        # Check option recommendation
        if signal_data.get('option_recommendation'):
            opt = signal_data['option_recommendation']
            print(f"\n📝 Option Recommendation:")
            print(f"   - Strike: {opt.get('strike', 'N/A')}")
            print(f"   - Type: {opt.get('option_type', 'N/A')}")
            print(f"   - Premium: {opt.get('premium', 'N/A')}")
            print(f"   - Symbol: {opt.get('symbol', 'N/A')}")
    else:
        print(f"\n⚠️ No actionable signal - Reason: {signal_data.get('reason', 'Unknown')}")
    
    # =========================================================================
    # CHECK ENHANCED ML PREDICTION - THIS IS THE NEW MODULE
    # =========================================================================
    if 'enhanced_ml_prediction' in signal_data:
        ml = signal_data['enhanced_ml_prediction']
        print(f"\n🧠 ENHANCED ML PREDICTION (NEW!):")
        print(f"   - Available Modules: {ml.get('available_modules', {})}")
        
        if ml.get('direction_prediction') and not ml['direction_prediction'].get('error'):
            dp = ml['direction_prediction']
            print(f"\n   📊 Direction Prediction:")
            print(f"      - Direction: {dp.get('direction', 'N/A')}")
            print(f"      - Confidence: {dp.get('confidence', 0):.1%}")
            print(f"      - Trade Signal: {dp.get('trade_signal', 'N/A')}")
            print(f"      - Signal Strength: {dp.get('signal_strength', 'N/A')}")
            probs = dp.get('probabilities', {})
            if probs:
                print(f"      - Probabilities: UP={probs.get('up',0):.1%} | SIDEWAYS={probs.get('sideways',0):.1%} | DOWN={probs.get('down',0):.1%}")
        
        if ml.get('speed_prediction') and not ml['speed_prediction'].get('error'):
            sp = ml['speed_prediction']
            print(f"\n   ⚡ Speed Prediction:")
            print(f"      - Speed: {sp.get('category', 'N/A')}")
            print(f"      - Confidence: {sp.get('confidence', 0):.1%}")
            print(f"      - Expected Move: {sp.get('expected_move_pct', 0):.2f}%")
            print(f"      - Expected Time: {sp.get('expected_time_mins', 0)} mins")
            print(f"      - Options Action: {sp.get('options_action', 'N/A')}")
            if sp.get('reasoning'):
                print(f"      - Reasoning: {sp['reasoning'][0] if sp['reasoning'] else 'N/A'}")
        
        if ml.get('iv_prediction') and not ml['iv_prediction'].get('error'):
            iv = ml['iv_prediction']
            print(f"\n   📈 IV Prediction:")
            print(f"      - IV Direction: {iv.get('direction', 'N/A')}")
            print(f"      - Confidence: {iv.get('confidence', 0):.1%}")
            print(f"      - Current IV: {iv.get('current_iv', 0):.2f}%")
            print(f"      - Predicted IV: {iv.get('predicted_iv', 0):.2f}%")
            print(f"      - Expected Change: {iv.get('expected_iv_change_pct', 0):.2f}%")
            regime = iv.get('regime', {})
            print(f"      - IV Regime: {regime.get('current', 'N/A')} (percentile: {regime.get('percentile', 0):.0f}%)")
        
        if ml.get('theta_scenarios') and not ml['theta_scenarios'].get('error'):
            ts = ml['theta_scenarios']
            greeks = ts.get('greeks', {})
            print(f"\n   📐 Theta Scenarios:")
            print(f"      - Delta: {greeks.get('delta', 0):.4f}")
            print(f"      - Gamma: {greeks.get('gamma', 0):.6f}")
            print(f"      - Theta/Hour: ₹{greeks.get('theta_per_hour', 0):.2f}")
            print(f"      - Vega: {greeks.get('vega', 0):.2f}")
            summary = ts.get('summary', {})
            print(f"      - Optimal Hold: {summary.get('optimal_holding_time_mins', 0)} mins")
            print(f"      - Max Theta Loss: ₹{summary.get('max_theta_loss_today', 0):.2f}")
            recs = ts.get('recommendations', {})
            print(f"      - Urgency: {recs.get('urgency', 'N/A')}")
            print(f"      - Recommendation: {recs.get('hold_recommendation', 'N/A')}")
        
        if ml.get('simulation') and not ml['simulation'].get('error'):
            sim = ml['simulation']
            print(f"\n   🎮 P&L Simulation:")
            grade = sim.get('trade_grade', {})
            print(f"      - Trade Grade: {grade.get('grade', 'N/A')}")
            ev = sim.get('expected_values', {})
            print(f"      - Expected P&L: ₹{ev.get('expected_pnl', 0):.2f} ({ev.get('expected_pnl_pct', 0):.1f}%)")
            print(f"      - Win Probability: {ev.get('win_probability', 0)*100:.0f}%")
            risk = sim.get('risk_metrics', {})
            print(f"      - Max Loss: ₹{risk.get('max_loss', 0):.2f}")
            print(f"      - Max Gain: ₹{risk.get('max_gain', 0):.2f}")
            print(f"      - Risk/Reward: {risk.get('risk_reward_ratio', 0):.2f}:1")
            recs = sim.get('recommendations', {})
            print(f"      - Should Trade: {'YES' if recs.get('should_trade') else 'NO'}")
            print(f"      - Entry Timing: {recs.get('entry_timing', 'N/A')}")
        
        if ml.get('combined_recommendation'):
            cr = ml['combined_recommendation']
            print(f"\n   🎯 Combined ML Recommendation:")
            print(f"      - Action: {cr.get('action', 'N/A')}")
            print(f"      - Confidence: {cr.get('confidence', 0):.0%}")
            kf = cr.get('key_factors', {})
            print(f"      - Direction: {kf.get('direction', 'N/A')} ({kf.get('direction_confidence', 0):.0%})")
            print(f"      - Speed: {kf.get('speed', 'N/A')} ({kf.get('speed_confidence', 0):.0%})")
            print(f"      - IV: {kf.get('iv_direction', 'N/A')}")
            print(f"      - Grade: {kf.get('grade', 'N/A')}")
            if cr.get('reasoning'):
                print(f"      - Reasoning: {cr['reasoning'][0]}")
            if cr.get('warnings'):
                print(f"      - ⚠️ Warning: {cr['warnings'][0]}")
    else:
        print(f"\n⚠️ No enhanced_ml_prediction in response")
    
    # Check probability analysis in signal
    if 'probability_analysis' in signal_data:
        prob = signal_data['probability_analysis']
        print(f"\n🎯 Probability Analysis in Signal:")
        print(f"   - Final Bias: {prob.get('final_bias', 'N/A')}")
        print(f"   - Confidence: {prob.get('confidence_score', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("✅ SCAN FLOW COMPLETE")
    print("=" * 80)
    
    # Save full response for debugging
    with open('scan_debug_output.json', 'w') as f:
        json.dump({
            'scan_data': scan_data,
            'signal_data': signal_data
        }, f, indent=2, default=str)
    print("\n📁 Full response saved to scan_debug_output.json")

if __name__ == "__main__":
    main()
