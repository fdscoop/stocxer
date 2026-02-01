#!/usr/bin/env python3
"""
Live Signal Generation Test using Real Fyers Data

This script:
1. Authenticates with Fyers API
2. Fetches LIVE historical data for all timeframes
3. Runs the momentum-enhanced signal generation
4. Shows the actual signal that would be generated

NO DEMO DATA - Only real market data from Fyers API
"""

import sys
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def authenticate_fyers():
    """
    Authenticate with Fyers API and return initialized client
    """
    from src.api.fyers_client import fyers_client
    
    # Check if already authenticated
    if fyers_client.fyers:
        try:
            profile = fyers_client.get_profile()
            if profile.get('s') == 'ok' or profile.get('code') == 200:
                logger.info(f"✅ Already authenticated as: {profile.get('data', {}).get('name', 'Unknown')}")
                return fyers_client
        except Exception as e:
            logger.warning(f"Existing token may be invalid: {e}")
    
    # Check for access token in environment
    access_token = os.getenv('FYERS_ACCESS_TOKEN')
    if access_token and len(access_token) > 50:
        logger.info("🔑 Using access token from environment...")
        fyers_client.access_token = access_token
        fyers_client._initialize_client()
        
        try:
            profile = fyers_client.get_profile()
            if profile.get('s') == 'ok' or profile.get('code') == 200:
                logger.info(f"✅ Authenticated as: {profile.get('data', {}).get('name', 'Unknown')}")
                return fyers_client
        except Exception as e:
            logger.warning(f"Token authentication failed: {e}")
    
    # Need to authenticate manually
    logger.info("\n" + "=" * 60)
    logger.info("🔐 FYERS AUTHENTICATION REQUIRED")
    logger.info("=" * 60)
    
    auth_url = fyers_client.generate_auth_url()
    logger.info(f"\n1. Open this URL in your browser:\n   {auth_url}")
    logger.info("\n2. Login with your Fyers credentials")
    logger.info("3. After login, you'll be redirected to a URL with 'auth_code=' parameter")
    logger.info("4. Copy the auth_code value and paste it below\n")
    
    auth_code = input("Enter auth_code: ").strip()
    
    if not auth_code:
        logger.error("No auth code provided!")
        return None
    
    success = fyers_client.set_access_token(auth_code)
    
    if success:
        logger.info("✅ Authentication successful!")
        # Save the token for future use
        logger.info(f"\n💡 TIP: Save this access token to .env file:")
        logger.info(f"   FYERS_ACCESS_TOKEN={fyers_client.access_token}")
        return fyers_client
    else:
        logger.error("❌ Authentication failed!")
        return None


def fetch_live_candles(fyers_client, symbol: str = "NSE:NIFTY50-INDEX") -> Dict[str, pd.DataFrame]:
    """
    Fetch LIVE historical candles for ALL timeframes needed for top-down analysis
    
    Returns:
        Dict mapping timeframe to DataFrame with OHLCV data
    """
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 FETCHING LIVE DATA FOR {symbol}")
    logger.info("=" * 60)
    
    # Timeframe configuration
    # Key format: timeframe code used in analysis
    # Value: (days_lookback, fyers_resolution)
    timeframes = {
        # HTF (Higher Timeframes)
        'M': (366, 'M'),      # Monthly - 1 year
        'W': (366, 'W'),      # Weekly - 1 year
        'D': (180, 'D'),      # Daily - 6 months
        '240': (100, '240'),  # 4H - 100 days (Fyers max for intraday)
        '4H': (100, '240'),   # Alias for 240
        
        # LTF (Lower Timeframes) - for entry confirmation
        '60': (100, '60'),    # 1H - 100 days
        '1H': (100, '60'),    # Alias for 60
        '15': (100, '15'),    # 15m - 100 days
        '5': (100, '5'),      # 5m - 100 days
        '3': (100, '3'),      # 3m - 100 days
    }
    
    candles = {}
    end_date = datetime.now()
    
    for tf_key, (days_back, resolution) in timeframes.items():
        start_date = end_date - timedelta(days=days_back)
        
        try:
            logger.info(f"   Fetching {tf_key} ({resolution})... ", end="")
            
            df = fyers_client.get_historical_data(
                symbol=symbol,
                resolution=resolution,
                date_from=start_date,
                date_to=end_date
            )
            
            if df is not None and len(df) > 0:
                candles[tf_key] = df
                # Show last candle info
                last_candle = df.iloc[-1]
                logger.info(f"✅ {len(df)} candles (last: {last_candle.name}, close: {last_candle['close']:.2f})")
            else:
                logger.info(f"⚠️ No data")
                
        except Exception as e:
            logger.info(f"❌ Error: {e}")
    
    return candles


def get_live_quote(fyers_client, symbol: str = "NSE:NIFTY50-INDEX") -> float:
    """Get current live price"""
    try:
        quote = fyers_client.get_quotes([symbol])
        if quote.get('s') == 'ok' and quote.get('d'):
            ltp = quote['d'][0].get('v', {}).get('lp', 0)
            logger.info(f"💰 Current {symbol} Price: ₹{ltp:,.2f}")
            return ltp
    except Exception as e:
        logger.warning(f"Could not get live quote: {e}")
    
    return 0


def run_live_signal_generation(candles: Dict[str, pd.DataFrame], current_price: float):
    """
    Run the signal generation with LIVE data
    """
    logger.info("\n" + "=" * 60)
    logger.info("🎯 RUNNING LIVE SIGNAL GENERATION")
    logger.info("=" * 60)
    
    from src.analytics.ict_analysis import analyze_multi_timeframe_ict_topdown
    from src.analytics.confidence_calculator import calculate_trade_confidence
    
    # Run top-down analysis
    logger.info("\n📈 Phase 1: ICT Top-Down Analysis")
    
    topdown_result = analyze_multi_timeframe_ict_topdown(
        candles_by_timeframe=candles,
        current_price=current_price,
        trading_mode="intraday"  # Use intraday for current market conditions
    )
    
    htf_bias = topdown_result['htf_bias']
    ltf_entry = topdown_result['ltf_entry']
    
    # Display HTF Bias
    logger.info(f"\n📊 HTF BIAS RESULT:")
    logger.info(f"   Direction: {htf_bias.overall_direction.upper()}")
    logger.info(f"   Strength: {htf_bias.bias_strength:.1f}/100")
    logger.info(f"   Structure Quality: {htf_bias.structure_quality}")
    logger.info(f"   Premium/Discount: {htf_bias.premium_discount.upper()}")
    logger.info(f"   Key Zones: {len(htf_bias.key_zones)}")
    
    # Display LTF Entry
    logger.info(f"\n🎯 LTF ENTRY MODEL:")
    if ltf_entry:
        logger.info(f"   ✅ ENTRY FOUND!")
        logger.info(f"   Type: {ltf_entry.entry_type}")
        logger.info(f"   Timeframe: {ltf_entry.timeframe}m")
        logger.info(f"   Entry Zone: ₹{ltf_entry.entry_zone[0]:.2f} - ₹{ltf_entry.entry_zone[1]:.2f}")
        logger.info(f"   Trigger Price: ₹{ltf_entry.trigger_price:.2f}")
        logger.info(f"   Momentum Confirmed: {'✅' if ltf_entry.momentum_confirmed else '❌'}")
        logger.info(f"   Alignment Score: {ltf_entry.alignment_score:.0f}%")
        logger.info(f"   Confidence: {ltf_entry.confidence:.2%}")
    else:
        logger.info(f"   ❌ No entry model found")
    
    # Calculate confidence
    htf_bias_dict = {
        'overall_direction': htf_bias.overall_direction,
        'bias_strength': htf_bias.bias_strength,
        'structure_quality': htf_bias.structure_quality,
        'premium_discount': htf_bias.premium_discount
    }
    
    ltf_entry_dict = {
        'entry_type': ltf_entry.entry_type if ltf_entry else 'NO_SETUP',
        'timeframe': ltf_entry.timeframe if ltf_entry else 'N/A',
        'momentum_confirmed': ltf_entry.momentum_confirmed if ltf_entry else False,
        'alignment_score': ltf_entry.alignment_score if ltf_entry else 0
    }
    
    confidence = calculate_trade_confidence(
        htf_bias=htf_bias_dict,
        ltf_entry=ltf_entry_dict
    )
    
    # Determine signal
    logger.info(f"\n📊 CONFIDENCE BREAKDOWN:")
    logger.info(f"   ICT HTF Structure:    {confidence['htf_structure']:.1f}/40")
    logger.info(f"   ICT LTF Confirmation: {confidence['ltf_confirmation']:.1f}/25")
    logger.info(f"   ML Alignment:         {confidence['ml_alignment']:.1f}/15")
    logger.info(f"   Candlestick Patterns: {confidence['candlestick']:.1f}/10")
    logger.info(f"   Futures Basis:        {confidence['futures_basis']:.1f}/5")
    logger.info(f"   Constituents:         {confidence['constituents']:.1f}/5")
    logger.info(f"   {'─' * 50}")
    logger.info(f"   TOTAL CONFIDENCE:     {confidence['total']:.1f}/100 ({confidence['confidence_level']})")
    
    # Determine trade direction
    trade_direction = htf_bias.overall_direction
    momentum_override = False
    
    # Check for momentum override when HTF is neutral
    if trade_direction == 'neutral' and ltf_entry:
        if 'MOMENTUM' in ltf_entry.entry_type or ltf_entry.alignment_score >= 50:
            # Determine direction from entry type
            if 'bullish' in ltf_entry.entry_type.lower():
                trade_direction = 'bullish'
            elif 'bearish' in ltf_entry.entry_type.lower():
                trade_direction = 'bearish'
            else:
                # Infer from entry zone position relative to price
                if ltf_entry.trigger_price < current_price:
                    trade_direction = 'bullish'
                elif ltf_entry.trigger_price > current_price:
                    trade_direction = 'bearish'
            
            if trade_direction != 'neutral':
                momentum_override = True
    
    # Final signal
    logger.info("\n" + "=" * 60)
    logger.info("🚀 FINAL SIGNAL")
    logger.info("=" * 60)
    
    if trade_direction == 'bullish':
        action = "BUY CALL"
        emoji = "📈"
    elif trade_direction == 'bearish':
        action = "BUY PUT"
        emoji = "📉"
    else:
        action = "WAIT"
        emoji = "⏳"
    
    logger.info(f"\n   {emoji} ACTION: {action}")
    logger.info(f"   Direction: {trade_direction.upper()}")
    logger.info(f"   Confidence: {confidence['total']:.1f}% ({confidence['confidence_level']})")
    
    if momentum_override:
        logger.info(f"   ⚡ Momentum Override: ACTIVE (HTF was neutral)")
    
    if trade_direction != 'neutral':
        # Suggest strike
        atm_strike = round(current_price / 50) * 50
        if trade_direction == 'bullish':
            suggested_strike = atm_strike
        else:
            suggested_strike = atm_strike
        
        logger.info(f"\n   📋 SUGGESTED TRADE:")
        logger.info(f"   Strike: {suggested_strike} {'CE' if trade_direction == 'bullish' else 'PE'}")
        logger.info(f"   Current Price: ₹{current_price:,.2f}")
        
        if ltf_entry:
            logger.info(f"   Entry Zone: ₹{ltf_entry.entry_zone[0]:.2f} - ₹{ltf_entry.entry_zone[1]:.2f}")
    else:
        logger.info(f"\n   ⚠️ REASON FOR WAIT:")
        if htf_bias.overall_direction == 'neutral':
            logger.info(f"   • HTF bias is neutral (conflicting timeframes)")
        if not ltf_entry:
            logger.info(f"   • No LTF entry model found")
        if confidence['total'] < 40:
            logger.info(f"   • Confidence too low ({confidence['total']:.1f}% < 40%)")
    
    logger.info("\n" + "=" * 60)
    
    return {
        'action': action,
        'direction': trade_direction,
        'confidence': confidence,
        'htf_bias': htf_bias,
        'ltf_entry': ltf_entry,
        'momentum_override': momentum_override
    }


def main():
    """Main entry point"""
    logger.info("=" * 70)
    logger.info("🔴 LIVE SIGNAL GENERATION TEST")
    logger.info("   Using REAL Fyers data (no demo data)")
    logger.info("=" * 70)
    
    # Step 1: Authenticate
    fyers = authenticate_fyers()
    if not fyers:
        logger.error("Cannot proceed without authentication!")
        return
    
    # Step 2: Get live price
    current_price = get_live_quote(fyers)
    if current_price == 0:
        logger.warning("Could not get live price, using last close from daily candle")
    
    # Step 3: Fetch live candles for all timeframes
    candles = fetch_live_candles(fyers)
    
    if not candles:
        logger.error("❌ No candle data fetched! Check Fyers connection.")
        return
    
    # If we didn't get live price, use last daily close
    if current_price == 0 and 'D' in candles:
        current_price = candles['D']['close'].iloc[-1]
        logger.info(f"💰 Using last daily close as current price: ₹{current_price:,.2f}")
    
    # Step 4: Run signal generation
    result = run_live_signal_generation(candles, current_price)
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📋 TEST COMPLETE")
    logger.info("=" * 70)
    logger.info(f"   Signal: {result['action']}")
    logger.info(f"   Direction: {result['direction'].upper()}")
    logger.info(f"   Confidence: {result['confidence']['total']:.1f}%")
    if result['momentum_override']:
        logger.info(f"   ⚡ Momentum override was used")
    logger.info("")


if __name__ == "__main__":
    main()
