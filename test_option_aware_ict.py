"""
Test script for Option-Aware ICT Signal Generation
Tests the complete end-to-end flow of the option-aware signal system
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.fyers_client import fyers_client
from src.analytics.option_aware_ict import OptionAwarePracticalICT
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_option_aware_signal():
    """Test the complete option-aware signal generation"""
    
    print("=" * 80)
    print("🧪 TESTING OPTION-AWARE ICT SIGNAL SYSTEM")
    print("=" * 80)
    print()
    
    # Initialize analyzer
    analyzer = OptionAwarePracticalICT(fyers_client)
    
    # Test configuration
    index = "NIFTY"
    fyers_symbol = "NSE:NIFTY50-INDEX"
    
    print(f"📊 Testing with: {index}")
    print()
    
    # Step 1: Fetch candles
    print("Step 1: Fetching candles for multiple timeframes...")
    print("-" * 80)
    
    now = datetime.now()
    date_to = now
    date_from_15m = now - timedelta(days=5)
    date_from_1h = now - timedelta(days=15)
    date_from_4h = now - timedelta(days=60)
    date_from_daily = now - timedelta(days=180)
    
    candles_by_timeframe = {}
    
    try:
        # 15min
        print("  Fetching 15min candles...")
        df_15m = fyers_client.get_historical_data(
            symbol=fyers_symbol,
            resolution="15",
            date_from=date_from_15m,
            date_to=date_to
        )
        if df_15m is not None and not df_15m.empty:
            candles_by_timeframe['15'] = df_15m
            print(f"    ✅ 15min: {len(df_15m)} candles")
        else:
            print(f"    ⚠️ 15min: No data")
        
        # 1H
        print("  Fetching 1H candles...")
        df_1h = fyers_client.get_historical_data(
            symbol=fyers_symbol,
            resolution="60",
            date_from=date_from_1h,
            date_to=date_to
        )
        if df_1h is not None and not df_1h.empty:
            candles_by_timeframe['60'] = df_1h
            print(f"    ✅ 1H: {len(df_1h)} candles")
        else:
            print(f"    ⚠️ 1H: No data")
        
        # 4H
        print("  Fetching 4H candles...")
        df_4h = fyers_client.get_historical_data(
            symbol=fyers_symbol,
            resolution="240",
            date_from=date_from_4h,
            date_to=date_to
        )
        if df_4h is not None and not df_4h.empty:
            candles_by_timeframe['240'] = df_4h
            print(f"    ✅ 4H: {len(df_4h)} candles")
        else:
            print(f"    ⚠️ 4H: No data")
        
        # Daily
        print("  Fetching Daily candles...")
        df_daily = fyers_client.get_historical_data(
            symbol=fyers_symbol,
            resolution="D",
            date_from=date_from_daily,
            date_to=date_to
        )
        if df_daily is not None and not df_daily.empty:
            candles_by_timeframe['D'] = df_daily
            print(f"    ✅ Daily: {len(df_daily)} candles")
        else:
            print(f"    ⚠️ Daily: No data")
        
        print()
        print(f"✅ Fetched {len(candles_by_timeframe)} timeframes successfully")
        print()
        
    except Exception as e:
        print(f"❌ Error fetching candles: {e}")
        return
    
    # Step 2: Get spot price
    print("Step 2: Fetching spot price...")
    print("-" * 80)
    
    try:
        quote_response = fyers_client.get_quotes([fyers_symbol])
        if quote_response.get('s') != 'ok' or not quote_response.get('d'):
            print(f"❌ Could not fetch spot price")
            return
        
        spot_price = quote_response['d'][0]['v']['lp']
        print(f"✅ Spot price: ₹{spot_price:.2f}")
        print()
        
    except Exception as e:
        print(f"❌ Error fetching spot price: {e}")
        return
    
    # Step 3: Generate signal
    print("Step 3: Generating option-aware signal...")
    print("-" * 80)
    
    try:
        signal = await analyzer.generate_option_signal(
            index=index,
            candles_by_timeframe=candles_by_timeframe,
            spot_price=spot_price,
            dte=4  # Assume 4 days to expiry
        )
        
        print()
        print("=" * 80)
        print("📊 SIGNAL GENERATED")
        print("=" * 80)
        print()
        
        # Display signal details
        if signal['signal'] == 'WAIT':
            print("⏸️  WAIT Signal")
            print(f"   Reason: {signal.get('reasoning', ['No setup found'])[0]}")
        else:
            print(f"🎯 Action: {signal['action']}")
            print(f"📈 Confidence: {signal['confidence']['score']}% ({signal['confidence']['level']})")
            print(f"🏆 Tier: {signal['tier']} - {signal['setup_type']}")
            print()
            
            # Option details
            option = signal['option']
            print("📍 Option Details:")
            print(f"   Strike: {option['strike']} {option['type']}")
            print(f"   Symbol: {option['symbol']}")
            print(f"   Entry: ₹{option['entry_price']:.2f}")
            print(f"   Delta: {option['delta']:.3f}")
            print(f"   Volume: {option['volume']:,}")
            print(f"   OI: {option['oi']:,}")
            print()
            
            # Targets
            targets = signal['targets']
            print("🎯 Targets & Stop Loss:")
            print(f"   Target 1: ₹{targets['target_1_price']:.2f} (+{targets['target_1_points']:.1f} pts)")
            print(f"   Target 2: ₹{targets['target_2_price']:.2f} (+{targets['target_2_points']:.1f} pts)")
            print(f"   Stop Loss: ₹{targets['stop_loss_price']:.2f} (-{targets['stop_loss_points']:.1f} pts)")
            print()
            
            # Risk/Reward
            rr = signal['risk_reward']
            print("💰 Risk/Reward Per Lot:")
            print(f"   Risk: ₹{rr['risk_per_lot']:,.2f}")
            print(f"   Reward 1: ₹{rr['reward_1_per_lot']:,.2f} ({rr['ratio_1']})")
            print(f"   Reward 2: ₹{rr['reward_2_per_lot']:,.2f} ({rr['ratio_2']})")
            print(f"   Lot Size: {signal['lot_size']}")
            print()
            
            # Index context
            ctx = signal['index_context']
            print("📊 Index Context:")
            print(f"   Spot: ₹{ctx['spot_price']:.2f}")
            print(f"   Expected Move: {ctx['expected_move']} points")
            print(f"   Delta Factor: {ctx['delta_factor']:.3f}")
            print()
        
        print("=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error generating signal: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    print()
    print("🚀 Starting Option-Aware ICT Signal Test")
    print()
    
    # Check if Fyers client has access token
    if not fyers_client.access_token:
        print("⚠️  WARNING: No Fyers access token found")
        print("   The test will fail without a valid token.")
        print("   Please authenticate first using the main application.")
        print()
    
    try:
        asyncio.run(test_option_aware_signal())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
