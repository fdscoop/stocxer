"""
Dashboard Scan Test - Simulating Real User Experience
Tests the exact flow when user clicks "🔍 Scan" on dashboard

Flow:
1. Login with user credentials
2. Get Fyers token from Supabase
3. Call /signals/NSE:NIFTY50-INDEX/actionable
4. Display result as dashboard would
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.auth_service import AuthService
from src.models.auth_models import UserLogin
from src.api.fyers_client import FyersClient
import httpx


async def main():
    print("=" * 80)
    print("🔍 DASHBOARD SCAN TEST - Simulating Real User")
    print("=" * 80)
    print()
    
    # Step 1: Login
    print("📝 Step 1: User Login")
    print("-" * 80)
    
    auth_service = AuthService()
    login_data = UserLogin(
        email="bineshch@gmail.com",
        password="Tra@2026"
    )
    
    try:
        token_response = await auth_service.login_user(login_data)
        print(f"✅ Logged in as: {login_data.email}")
        print(f"✅ User ID: {token_response.user.id}")
        print(f"✅ Access Token: {token_response.access_token[:50]}...")
        print()
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return
    
    # Step 2: Get Fyers Token from Supabase
    print("📝 Step 2: Retrieve Fyers Token from Supabase")
    print("-" * 80)
    
    try:
        fyers_token_response = await auth_service.get_fyers_token(token_response.user.id)
        if not fyers_token_response:
            print(f"❌ No Fyers token found in database")
            print(f"   Please authenticate with Fyers first")
            return
        
        fyers_token = fyers_token_response.access_token
        print(f"✅ Fyers token retrieved from database")
        print(f"✅ Token: {fyers_token[:50]}...")
        print()
        
        # Initialize Fyers client
        fyers_client = FyersClient()
        fyers_client.access_token = fyers_token
        fyers_client._initialize_client()
        print(f"✅ Fyers client initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to get Fyers token: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Get current NIFTY price (like dashboard does)
    print("📝 Step 3: Fetch Current NIFTY Price")
    print("-" * 80)
    
    try:
        symbol = "NSE:NIFTY50-INDEX"
        quote = fyers_client.get_quotes([symbol])
        if quote and quote.get('d'):
            spot_price = quote['d'][0]['v']['lp']
            day_change = quote['d'][0]['v']['ch']
            change_pct = quote['d'][0]['v']['chp']
            print(f"✅ NIFTY Spot: ₹{spot_price:,.2f}")
            print(f"   Change: {'+' if day_change > 0 else ''}{day_change:,.2f} ({'+' if change_pct > 0 else ''}{change_pct:.2f}%)")
            print()
        else:
            print(f"⚠️ Could not fetch NIFTY price")
            spot_price = None
    except Exception as e:
        print(f"⚠️ Error fetching spot price: {e}")
        spot_price = None
        print()
    
    # Step 4: Call Signal Generation Endpoint (Main Test!)
    print("📝 Step 4: Generate Trading Signal")
    print("-" * 80)
    print("🔍 Calling: GET /signals/NSE:NIFTY50-INDEX/actionable")
    print()
    
    try:
        # Make API call to signal endpoint
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://localhost:8000/signals/NSE:NIFTY50-INDEX/actionable",
                headers={
                    "Authorization": f"Bearer {fyers_token}"
                }
            )
            
            if response.status_code == 200:
                signal = response.json()
                print("✅ Signal Generated Successfully!")
                print()
                
                # Display signal like dashboard would
                display_signal_as_dashboard(signal, spot_price)
                
            elif response.status_code == 404:
                print(f"⚠️ Endpoint not found - trying direct function call instead")
                print()
                # Fallback: call function directly
                await test_signal_generation_direct(fyers_client)
                
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
    except httpx.ConnectError:
        print(f"⚠️ Server not running on localhost:8000")
        print(f"   Testing with direct function call instead...")
        print()
        await test_signal_generation_direct(fyers_client)
        
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        import traceback
        traceback.print_exc()


async def test_signal_generation_direct(fyers_client):
    """Test signal generation by calling the function directly"""
    print("📝 Direct Function Test")
    print("-" * 80)
    
    try:
        # Import the main file
        from main import _generate_actionable_signal, get_multi_timeframe_analysis
        
        symbol = "NSE:NIFTY50-INDEX"
        
        print("🔄 Fetching multi-timeframe data...")
        mtf_result = await get_multi_timeframe_analysis(symbol)
        
        print(f"✅ Data fetched:")
        for tf, data in mtf_result.items():
            if data is not None and not data.empty:
                print(f"   {tf}: {len(data)} candles")
            else:
                print(f"   {tf}: No data")
        print()
        
        print("🔄 Generating signal...")
        signal = _generate_actionable_signal(
            mtf_result=mtf_result,
            session_info=None,
            chain_data=None,
            historical_prices=mtf_result.get('D'),
            probability_analysis=None
        )
        
        print("✅ Signal Generated!")
        print()
        
        # Display signal
        spot_price = None
        if mtf_result.get('D') is not None and not mtf_result['D'].empty:
            spot_price = mtf_result['D']['close'].iloc[-1]
        
        display_signal_as_dashboard(signal, spot_price)
        
    except Exception as e:
        print(f"❌ Error in direct test: {e}")
        import traceback
        traceback.print_exc()


def display_signal_as_dashboard(signal, spot_price=None):
    """Display signal exactly as dashboard would show it"""
    print("=" * 80)
    print("🎯 LIVE TRADING SIGNAL (Dashboard View)")
    print("=" * 80)
    print()
    
    # Main action
    action = signal.get('action', 'WAIT')
    is_call = 'CALL' in action
    is_put = 'PUT' in action
    
    action_color = "🟢" if is_call else "🔴" if is_put else "🟡"
    print(f"{action_color} ACTION: {action}")
    
    # Strike info
    if signal.get('option'):
        opt = signal['option']
        print(f"   Strike: {opt.get('strike')} {opt.get('type')}")
        print(f"   Symbol: {opt.get('trading_symbol', 'N/A')}")
        
        if opt.get('expiry_date'):
            from datetime import datetime
            expiry = datetime.fromisoformat(opt['expiry_date'].replace('Z', '+00:00'))
            print(f"   Expiry: {expiry.strftime('%b %d, %Y')} ({opt.get('expiry_info', {}).get('days_to_expiry', 'N/A')} days)")
    else:
        print(f"   Reason: {signal.get('reason', 'No setup')}")
    
    print()
    
    # Pricing
    if signal.get('pricing'):
        pricing = signal['pricing']
        print("💰 PRICING:")
        print(f"   Best Price (LTP): ₹{pricing.get('ltp', 'N/A')}")
        print(f"   Max Entry: ₹{pricing.get('entry_price', 'N/A')}")
        print(f"   Source: {pricing.get('price_source', 'N/A')}")
        print()
    elif signal.get('entry'):
        print("💰 ENTRY:")
        print(f"   Price: ₹{signal['entry'].get('price', 'N/A')}")
        print()
    
    # Direction & Probability
    if signal.get('setup_details'):
        setup = signal['setup_details']
        print("📊 DIRECTION & PROBABILITY:")
        print(f"   Direction: {setup.get('reversal_direction', 'N/A')}")
        print(f"   Probability: {setup.get('reversal_probability', 'N/A')}%")
        print()
    
    # Confidence
    if signal.get('confidence'):
        conf = signal['confidence']
        score = conf.get('score', 0)
        level = conf.get('level', 'UNKNOWN')
        
        level_emoji = "🔴" if score < 40 else "🟡" if score < 70 else "🟢"
        print(f"{level_emoji} CONFIDENCE: {score}% ({level})")
        print()
    
    # Targets & Stop Loss
    if signal.get('targets'):
        targets = signal['targets']
        entry_price = signal.get('entry', {}).get('price') or signal.get('pricing', {}).get('entry_price', 0)
        
        print("🎯 TARGETS & STOP LOSS:")
        
        t1 = targets.get('target_1', 0)
        t2 = targets.get('target_2', 0)
        sl = targets.get('stop_loss', 0)
        
        if entry_price and entry_price > 0:
            t1_pct = ((t1 - entry_price) / entry_price) * 100 if t1 else 0
            t2_pct = ((t2 - entry_price) / entry_price) * 100 if t2 else 0
            sl_pct = ((sl - entry_price) / entry_price) * 100 if sl else 0
            
            print(f"   🟢 Target 1: ₹{t1:.2f} ({'+' if t1_pct > 0 else ''}{t1_pct:.1f}%)")
            print(f"   🟢 Target 2: ₹{t2:.2f} ({'+' if t2_pct > 0 else ''}{t2_pct:.1f}%)")
            print(f"   🔴 Stop Loss: ₹{sl:.2f} ({'+' if sl_pct > 0 else ''}{sl_pct:.1f}%)")
            
            # Risk:Reward
            risk = abs(entry_price - sl) if sl else 0
            reward1 = abs(t1 - entry_price) if t1 else 0
            reward2 = abs(t2 - entry_price) if t2 else 0
            
            if risk > 0:
                rr1 = reward1 / risk
                rr2 = reward2 / risk
                print(f"   ⚖️  R:R Ratio: 1:{rr1:.1f} to 1:{rr2:.1f}")
        else:
            print(f"   Target 1: ₹{t1:.2f}")
            print(f"   Target 2: ₹{t2:.2f}")
            print(f"   Stop Loss: ₹{sl:.2f}")
        
        print()
    
    # HTF Analysis (NEW FLOW ONLY)
    if signal.get('htf_analysis'):
        htf = signal['htf_analysis']
        print("📈 HTF ANALYSIS (ICT Top-Down):")
        print(f"   Direction: {htf.get('direction', 'N/A').upper()}")
        print(f"   Strength: {htf.get('strength', 0):.1f}%")
        print(f"   Structure: {htf.get('structure_quality', 'N/A')}")
        print(f"   Zone: {htf.get('premium_discount', 'N/A').upper()}")
        print()
    
    # LTF Entry Model (NEW FLOW ONLY)
    if signal.get('ltf_entry_model'):
        ltf = signal['ltf_entry_model']
        if ltf.get('found'):
            print("⚡ LTF ENTRY MODEL:")
            print(f"   ✅ Found: {ltf.get('entry_type', 'N/A')}")
            print(f"   Timeframe: {ltf.get('timeframe', 'N/A')}")
            print(f"   Zone: {ltf.get('entry_zone', {})}")
            print()
        else:
            print("⚡ LTF ENTRY MODEL: ❌ Not found")
            print()
    
    # Confirmation Stack (NEW FLOW ONLY)
    if signal.get('confirmation_stack'):
        stack = signal['confirmation_stack']
        print("✅ CONFIRMATION STACK:")
        
        if stack.get('ml_prediction'):
            ml = stack['ml_prediction']
            agrees = ml.get('agrees_with_htf', True)
            conflict_emoji = "⚠️ CONFLICT!" if not agrees else "✅"
            print(f"   ML: {ml.get('direction', 'N/A').upper()} ({ml.get('confidence', 0)}%) {conflict_emoji}")
        
        if stack.get('candlestick_patterns'):
            cs = stack['candlestick_patterns']
            print(f"   Patterns: {cs.get('dominant_pattern', 'None')} ({cs.get('pattern_strength', 0):.1f}%)")
        
        if stack.get('futures_sentiment'):
            fut = stack['futures_sentiment']
            print(f"   Futures: {fut.get('sentiment', 'N/A')} (Basis: {fut.get('basis', 0):.2f})")
        
        print()
    
    # Confidence Breakdown (NEW FLOW ONLY)
    if signal.get('confidence_breakdown'):
        breakdown = signal['confidence_breakdown']
        print("📊 CONFIDENCE BREAKDOWN:")
        print(f"   Total: {breakdown.get('total', 0):.1f}/100")
        
        if breakdown.get('components'):
            comps = breakdown['components']
            print(f"   • HTF Structure: {comps.get('ict_htf_structure', 0):.1f}/40")
            print(f"   • LTF Entry: {comps.get('ict_ltf_confirmation', 0):.1f}/25")
            print(f"   • ML Alignment: {comps.get('ml_alignment', 0):.1f}/15")
            print(f"   • Patterns: {comps.get('candlestick_patterns', 0):.1f}/10")
            print(f"   • Futures: {comps.get('futures_basis', 0):.1f}/5")
            print(f"   • Constituents: {comps.get('constituents', 0):.1f}/5")
        
        print()
    
    # Market Context
    if spot_price:
        print(f"📍 NIFTY Spot: ₹{spot_price:,.2f}")
        print()
    
    print("=" * 80)
    
    # Flow indicator
    if signal.get('htf_analysis'):
        print("✨ Signal generated using: NEW ICT TOP-DOWN FLOW ✨")
    else:
        print("⚠️  Signal generated using: OLD ML-FIRST FLOW")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
