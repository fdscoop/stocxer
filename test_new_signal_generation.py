#!/usr/bin/env python3
"""
Test the new ICT top-down signal generation function
Compares OLD flow vs NEW flow side-by-side
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import json
from datetime import datetime, timedelta

# Import authentication
from src.services.auth_service import auth_service
from src.api.fyers_client import FyersClient

# Import signal generation
from main import _generate_actionable_signal, _generate_actionable_signal_topdown

EMAIL = "bineshch@gmail.com"
PASSWORD = "Tra@2026"

async def test_new_signal_flow():
    """
    Test new signal generation with live NIFTY data
    """
    print("=" * 80)
    print("🧪 TESTING NEW ICT TOP-DOWN SIGNAL GENERATION")
    print("=" * 80)
    print()
    
    # Step 1: Login and get Fyers token
    print("🔐 Step 1: Authentication")
    try:
        from src.models.auth_models import UserLogin
        
        login_data = UserLogin(email=EMAIL, password=PASSWORD)
        result = await auth_service.login_user(login_data)
        
        if not result or not result.access_token:
            print(f"❌ Login failed")
            return
        
        user = result.user
        print(f"✅ Logged in as: {user.email}")
        
        # Get Fyers token
        fyers_token = await auth_service.get_fyers_token(user.id)
        if not fyers_token or not fyers_token.access_token:
            print("❌ No Fyers token found!")
            return
        
        print(f"✅ Fyers token found (expires in {(fyers_token.expires_at - datetime.now().replace(tzinfo=fyers_token.expires_at.tzinfo)).total_seconds() / 3600:.1f}h)")
        
        # Create Fyers client
        fyers_client = FyersClient()
        fyers_client.access_token = fyers_token.access_token
        fyers_client._initialize_client()
        
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Step 2: Get NIFTY data
    print("\n📊 Step 2: Fetching NIFTY Market Data")
    
    try:
        # Get spot price
        spot_data = fyers_client.get_quotes(["NSE:NIFTY50-INDEX"])
        if not spot_data or not spot_data.get('d'):
            print("❌ Failed to get NIFTY spot price")
            return
        
        spot_price = spot_data['d'][0]['v']['lp']
        print(f"✅ NIFTY Spot: ₹{spot_price}")
        
        # Get historical data for multiple timeframes (MAXIMUM DATA)
        # Fyers limits: Daily=366 days, Intraday=100 days
        end_date = datetime.now()
        
        timeframes_to_fetch = {
            'M': (366, 'M'),      # Monthly - 366 days (aggregated from daily)
            'W': (366, 'W'),      # Weekly - 366 days (aggregated from daily)
            'D': (366, 'D'),      # Daily - 366 days (maximum allowed)
            '240': (100, '240'),  # 4H - 100 days (intraday max)
            '60': (100, '60'),    # 1H - 100 days (intraday max)
            '15': (100, '15'),    # 15m - 100 days (intraday max)
            '5': (100, '5'),      # 5m - 100 days (intraday max)
            '3': (100, '3')       # 3m - 100 days (intraday max)
        }
        
        historical_data = {}
        print("\n   Fetching historical data:")
        
        for tf_key, (days_back, resolution) in timeframes_to_fetch.items():
            start_date = end_date - timedelta(days=days_back)
            df = fyers_client.get_historical_data(
                symbol="NSE:NIFTY50-INDEX",
                resolution=resolution,
                date_from=start_date,
                date_to=end_date
            )
            
            if df is not None and len(df) > 0:
                historical_data[tf_key] = df
                print(f"   ✅ {tf_key}: {len(df)} candles")
            else:
                print(f"   ⚠️ {tf_key}: No data")
        
        # Get option chain
        expiry_date = end_date + timedelta(days=(3 - end_date.weekday()) % 7)  # Next Thursday
        chain_data = fyers_client.get_option_chain(
            symbol="NIFTY",
            expiry_date=expiry_date.strftime("%Y-%m-%d")
        )
        
        if not chain_data:
            print("❌ Failed to get option chain")
            return
        
        print(f"✅ Option chain: {len(chain_data.get('strikes', []))} strikes")
        
    except Exception as e:
        print(f"❌ Data fetch error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Prepare mock objects for signal generation
    print("\n🔧 Step 3: Preparing Signal Generation Inputs")
    
    # Mock MTF result (simplified)
    class MockMTFResult:
        def __init__(self, price, analyses):
            self.current_price = price
            self.overall_bias = 'neutral'  # Will be overridden by new flow
            self.analyses = analyses
    
    class MockAnalysis:
        def __init__(self, candles):
            self.candles = candles
            self.fair_value_gaps = []
            self.trend = 'neutral'
    
    mtf_analyses = {
        tf: MockAnalysis(df) for tf, df in historical_data.items()
    }
    
    mtf_result = MockMTFResult(spot_price, mtf_analyses)
    
    # Mock session info
    class MockSessionInfo:
        current_session = "market_hours"
    
    session_info = MockSessionInfo()
    
    # Historical prices for ML
    historical_prices = historical_data.get('D')['close'] if 'D' in historical_data else None
    
    print(f"✅ MTF Result: {len(mtf_analyses)} timeframes")
    print(f"✅ Session: {session_info.current_session}")
    print(f"✅ Historical prices: {len(historical_prices) if historical_prices is not None else 0} days")
    
    # Step 4: Test OLD flow
    print("\n" + "=" * 80)
    print("🔄 Step 4: Testing OLD Signal Generation Flow")
    print("=" * 80)
    
    try:
        old_signal = _generate_actionable_signal(
            mtf_result=mtf_result,
            session_info=session_info,
            chain_data=chain_data,
            historical_prices=historical_prices,
            probability_analysis=None
        )
        
        print("\n📊 OLD FLOW RESULT:")
        print(f"   Signal: {old_signal.get('signal')}")
        print(f"   Action: {old_signal.get('action')}")
        print(f"   Strike: {old_signal['option'].get('strike')}")
        print(f"   Type: {old_signal['option'].get('type')}")
        print(f"   Confidence: {old_signal['confidence'].get('score')}/100 ({old_signal['confidence'].get('level')})")
        print(f"   Entry: ₹{old_signal['entry'].get('price')}")
        print(f"   Target 1: ₹{old_signal['targets'].get('target_1')}")
        print(f"   Stop Loss: ₹{old_signal['targets'].get('stop_loss')}")
        
    except Exception as e:
        print(f"❌ OLD flow error: {e}")
        import traceback
        traceback.print_exc()
        old_signal = None
    
    # Step 5: Test NEW flow
    print("\n" + "=" * 80)
    print("🆕 Step 5: Testing NEW ICT Top-Down Signal Generation Flow")
    print("=" * 80)
    
    try:
        new_signal = _generate_actionable_signal_topdown(
            mtf_result=mtf_result,
            session_info=session_info,
            chain_data=chain_data,
            historical_prices=historical_prices,
            probability_analysis=None,
            use_new_flow=True  # Enable new flow
        )
        
        print("\n📊 NEW FLOW RESULT:")
        print(f"   Signal: {new_signal.get('signal')}")
        print(f"   Action: {new_signal.get('action')}")
        print(f"   Strike: {new_signal['option'].get('strike')}")
        print(f"   Type: {new_signal['option'].get('type')}")
        
        # HTF Analysis
        htf = new_signal.get('htf_analysis', {})
        print(f"\n   HTF Analysis:")
        print(f"      Direction: {htf.get('direction')}")
        print(f"      Strength: {htf.get('strength')}/100")
        print(f"      Structure: {htf.get('structure_quality')}")
        print(f"      Premium/Discount: {htf.get('premium_discount')}")
        
        # LTF Entry
        ltf = new_signal.get('ltf_entry_model', {})
        if ltf.get('found'):
            print(f"\n   LTF Entry Model:")
            print(f"      Type: {ltf.get('entry_type')}")
            print(f"      Timeframe: {ltf.get('timeframe')}")
            print(f"      Entry Zone: ₹{ltf.get('entry_zone')[0]:.2f} - ₹{ltf.get('entry_zone')[1]:.2f}")
            print(f"      Confidence: {ltf.get('confidence')}%")
        else:
            print(f"\n   LTF Entry Model: ❌ Not found")
        
        # Confirmation Stack
        conf = new_signal.get('confirmation_stack', {})
        print(f"\n   Confirmation Stack:")
        
        ml = conf.get('ml_prediction', {})
        if ml.get('available', True):
            print(f"      ML: {ml.get('direction')} ({ml.get('confidence')}%) - {'✅' if ml.get('agrees_with_htf') else '⚠️'}")
        
        candles = conf.get('candlestick_patterns', {})
        if candles.get('available', True):
            print(f"      Patterns: {candles.get('confluence_score')}/100 ({candles.get('confidence_level')})")
        
        futures = conf.get('futures_sentiment', {})
        if futures.get('available', True):
            print(f"      Futures: {futures.get('sentiment')} ({futures.get('basis_pct')}%) - {'✅' if futures.get('agrees_with_htf') else '⚠️'}")
        
        # Confidence Breakdown
        cb = new_signal.get('confidence_breakdown', {})
        print(f"\n   Confidence Breakdown:")
        comps = cb.get('components', {})
        print(f"      ICT HTF:      {comps.get('ict_htf_structure')}/40")
        print(f"      ICT LTF:      {comps.get('ict_ltf_confirmation')}/25")
        print(f"      ML Alignment: {comps.get('ml_alignment')}/15")
        print(f"      Patterns:     {comps.get('candlestick_patterns')}/10")
        print(f"      Futures:      {comps.get('futures_basis')}/5")
        print(f"      Constituents: {comps.get('constituents')}/5")
        print(f"      {'─' * 40}")
        print(f"      TOTAL:        {cb.get('total')}/100 ({cb.get('level')})")
        
        print(f"\n   Pricing:")
        print(f"      Entry: ₹{new_signal['entry'].get('price')}")
        print(f"      Target 1: ₹{new_signal['targets'].get('target_1')}")
        print(f"      Target 2: ₹{new_signal['targets'].get('target_2')}")
        print(f"      Stop Loss: ₹{new_signal['targets'].get('stop_loss')}")
        print(f"      Risk/Reward: {new_signal['risk_reward'].get('ratio_1')}")
        
    except Exception as e:
        print(f"❌ NEW flow error: {e}")
        import traceback
        traceback.print_exc()
        new_signal = None
    
    # Step 6: Compare results
    print("\n" + "=" * 80)
    print("📊 Step 6: Comparison (OLD vs NEW)")
    print("=" * 80)
    
    if old_signal and new_signal:
        print(f"\n{'Metric':<25} {'OLD Flow':<30} {'NEW Flow':<30}")
        print("─" * 85)
        print(f"{'Signal Type':<25} {old_signal.get('signal'):<30} {new_signal.get('signal'):<30}")
        print(f"{'Action':<25} {old_signal.get('action'):<30} {new_signal.get('action'):<30}")
        print(f"{'Strike':<25} {old_signal['option'].get('strike'):<30} {new_signal['option'].get('strike'):<30}")
        print(f"{'Option Type':<25} {old_signal['option'].get('type'):<30} {new_signal['option'].get('type'):<30}")
        print(f"{'Confidence':<25} {old_signal['confidence'].get('score'):<30} {new_signal['confidence'].get('score'):<30}")
        print(f"{'Entry Price':<25} ₹{old_signal['entry'].get('price'):<29} ₹{new_signal['entry'].get('price'):<29}")
        
        # Save full results to JSON
        results = {
            'timestamp': datetime.now().isoformat(),
            'spot_price': spot_price,
            'old_flow': old_signal,
            'new_flow': new_signal
        }
        
        with open('signal_comparison_test.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Full comparison saved to: signal_comparison_test.json")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_new_signal_flow())
