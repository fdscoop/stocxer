"""
Test Option-Aware ICT Signal System with Authentication
Logs in and tests the new endpoint
"""

import requests
import json
from datetime import datetime

# Configuration
import os
BASE_URL = "http://127.0.0.1:8000"
EMAIL = os.getenv("TEST_USER_EMAIL", "test@example.com")
PASSWORD = os.getenv("TEST_USER_PASSWORD", "test_password")

def test_option_aware_signal():
    """Test the option-aware signal endpoint with authentication"""
    
    print("=" * 80)
    print("🧪 TESTING OPTION-AWARE ICT SIGNAL SYSTEM WITH AUTH")
    print("=" * 80)
    print()
    
    # Step 1: Login
    print("Step 1: Logging in...")
    print("-" * 80)
    
    try:
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EMAIL,
                "password": PASSWORD
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return
        
        login_data = login_response.json()
        access_token = login_data.get("access_token")
        
        if not access_token:
            print(f"❌ No access token in response")
            print(f"   Response: {json.dumps(login_data, indent=2)}")
            return
        
        print(f"✅ Logged in successfully")
        print(f"   User: {login_data.get('user', {}).get('email', 'Unknown')}")
        print()
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: Test option-aware signal endpoint
    print("Step 2: Testing option-aware signal endpoint...")
    print("-" * 80)
    
    # Test with NIFTY
    index = "NIFTY"
    
    try:
        signal_response = requests.get(
            f"{BASE_URL}/api/signals/{index}/option-aware",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        print(f"   Status Code: {signal_response.status_code}")
        print()
        
        if signal_response.status_code == 400:
            # Market might be closed
            error_data = signal_response.json()
            print(f"⚠️  {error_data.get('detail', 'Bad request')}")
            print()
            print("Note: This is expected if market is closed.")
            print("The endpoint requires market hours: 9:15 AM - 3:30 PM IST (Mon-Fri)")
            return
        
        if signal_response.status_code != 200:
            print(f"❌ Request failed: {signal_response.status_code}")
            print(f"   Response: {signal_response.text}")
            return
        
        signal_data = signal_response.json()
        
        # Display results
        print("=" * 80)
        print("📊 SIGNAL GENERATED")
        print("=" * 80)
        print()
        
        print(f"Index: {signal_data.get('index', 'N/A')}")
        print(f"Spot Price: ₹{signal_data.get('spot_price', 0):,.2f}")
        print(f"Status: {signal_data.get('status', 'N/A')}")
        print()
        
        signal = signal_data.get('signal', {})
        
        if signal.get('signal') == 'WAIT':
            print("⏸️  WAIT Signal")
            print(f"   Reason: {signal.get('reasoning', ['No setup'])[0]}")
        else:
            print(f"🎯 Action: {signal.get('action', 'N/A')}")
            print(f"📈 Confidence: {signal.get('confidence', {}).get('score', 0)}% ({signal.get('confidence', {}).get('level', 'N/A')})")
            print(f"🏆 Tier: {signal.get('tier', 'N/A')} - {signal.get('setup_type', 'N/A')}")
            print()
            
            # Option details
            if 'option' in signal:
                option = signal['option']
                print("📍 Option Details:")
                print(f"   Strike: {option.get('strike', 'N/A')} {option.get('type', 'N/A')}")
                print(f"   Symbol: {option.get('symbol', 'N/A')}")
                print(f"   Entry: ₹{option.get('entry_price', 0):.2f}")
                print(f"   Delta: {option.get('delta', 0):.3f}")
                print(f"   Volume: {option.get('volume', 0):,}")
                print(f"   OI: {option.get('oi', 0):,}")
                print()
            
            # Targets
            if 'targets' in signal:
                targets = signal['targets']
                print("🎯 Targets & Stop Loss:")
                print(f"   Target 1: ₹{targets.get('target_1_price', 0):.2f} (+{targets.get('target_1_points', 0):.1f} pts)")
                print(f"   Target 2: ₹{targets.get('target_2_price', 0):.2f} (+{targets.get('target_2_points', 0):.1f} pts)")
                print(f"   Stop Loss: ₹{targets.get('stop_loss_price', 0):.2f} (-{targets.get('stop_loss_points', 0):.1f} pts)")
                print()
            
            # Risk/Reward
            if 'risk_reward' in signal:
                rr = signal['risk_reward']
                print("💰 Risk/Reward Per Lot:")
                print(f"   Risk: ₹{rr.get('risk_per_lot', 0):,.2f}")
                print(f"   Reward 1: ₹{rr.get('reward_1_per_lot', 0):,.2f} ({rr.get('ratio_1', 'N/A')})")
                print(f"   Reward 2: ₹{rr.get('reward_2_per_lot', 0):,.2f} ({rr.get('ratio_2', 'N/A')})")
                print(f"   Lot Size: {signal.get('lot_size', 'N/A')}")
                print()
            
            # Index context
            if 'index_context' in signal:
                ctx = signal['index_context']
                print("📊 Index Context:")
                print(f"   Spot: ₹{ctx.get('spot_price', 0):,.2f}")
                print(f"   Expected Move: {ctx.get('expected_move', 0)} points")
                print(f"   Delta Factor: {ctx.get('delta_factor', 0):.3f}")
                print()
        
        print("=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print()
        
        # Show full JSON for reference
        print("Full JSON Response:")
        print(json.dumps(signal_data, indent=2))
        
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print()
    print("🚀 Starting Authenticated Test")
    print(f"   Server: {BASE_URL}")
    print(f"   User: {EMAIL}")
    print()
    
    test_option_aware_signal()
