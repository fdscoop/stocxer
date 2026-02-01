#!/usr/bin/env python3
"""
Test signal generation as a user would from the dashboard.

This tests the full flow:
1. User authentication via Supabase
2. Loading user's Fyers token
3. Running the options scan endpoint
4. Getting the signal result

Usage:
    python test_dashboard_scan.py
"""

import sys
import os
import asyncio
import logging
import httpx
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# API Configuration
# Use local server for testing, or production
API_BASE_URL = os.getenv('TRADEWISE_API_URL', 'http://localhost:8000')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Test user credentials
TEST_EMAIL = "bineshch@gmail.com"
TEST_PASSWORD = "Tra@2026"


async def login_user(email: str, password: str) -> dict:
    """
    Login user via Supabase and get access token
    """
    from supabase import create_client
    
    logger.info(f"🔐 Logging in as {email}...")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            logger.info(f"✅ Logged in as: {response.user.email}")
            logger.info(f"   User ID: {response.user.id}")
            return {
                "user": response.user,
                "session": response.session,
                "access_token": response.session.access_token
            }
        else:
            logger.error("❌ Login failed - no user returned")
            return None
            
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        return None


async def check_fyers_token(user_id: str) -> dict:
    """
    Check if user has a valid Fyers token stored
    """
    from supabase import create_client
    
    logger.info(f"🔑 Checking Fyers token for user {user_id}...")
    
    # Use service key for database access
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    supabase = create_client(SUPABASE_URL, service_key)
    
    try:
        result = supabase.table('fyers_tokens').select('*').eq('user_id', user_id).execute()
        
        if result.data and len(result.data) > 0:
            token_data = result.data[0]
            logger.info(f"✅ Fyers token found")
            logger.info(f"   Created: {token_data.get('created_at', 'Unknown')}")
            logger.info(f"   Token length: {len(token_data.get('access_token', ''))}")
            return token_data
        else:
            logger.warning("⚠️ No Fyers token found for this user")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error checking Fyers token: {e}")
        return None


async def run_options_scan(access_token: str, index: str = "NIFTY", quick_scan: bool = True) -> dict:
    """
    Run the options scan endpoint as the user would from dashboard
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 Running Options Scan for {index}")
    logger.info(f"   Mode: {'Quick' if quick_scan else 'Full'}")
    logger.info(f"{'='*60}")
    
    # Build the request
    url = f"{API_BASE_URL}/options/scan"
    params = {
        "index": index,
        "expiry": "weekly",
        "min_volume": 1000,
        "min_oi": 10000,
        "strategy": "all",
        "quick_scan": str(quick_scan).lower(),
        "analysis_mode": "intraday"  # Use intraday mode for current market conditions
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"🌐 Calling: {url}")
    logger.info(f"   Params: {params}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            
            logger.info(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.error(f"❌ Scan failed: {response.status_code}")
                logger.error(f"   Response: {response.text[:500]}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"❌ Request error: {e}")
            return {"error": str(e)}


def display_scan_results(results: dict):
    """
    Display the scan results in a user-friendly format
    """
    if "error" in results:
        logger.error(f"❌ Scan Error: {results['error']}")
        return
    
    logger.info(f"\n{'='*70}")
    logger.info("📊 SCAN RESULTS")
    logger.info(f"{'='*70}")
    
    # Signal Data
    signal = results.get("signal_data", {})
    if signal:
        action = signal.get("action", "UNKNOWN")
        direction = signal.get("direction", "unknown")
        
        if action == "BUY CALL":
            emoji = "📈"
        elif action == "BUY PUT":
            emoji = "📉"
        else:
            emoji = "⏳"
        
        logger.info(f"\n{emoji} SIGNAL: {action}")
        logger.info(f"   Direction: {direction.upper() if direction else 'N/A'}")
        
        # Confidence
        confidence = signal.get("confidence", {})
        if isinstance(confidence, dict):
            logger.info(f"\n📊 CONFIDENCE BREAKDOWN:")
            logger.info(f"   Total: {confidence.get('score', confidence.get('total', 0)):.1f}%")
            logger.info(f"   Level: {confidence.get('level', confidence.get('confidence_level', 'N/A'))}")
        else:
            logger.info(f"   Confidence: {confidence}")
        
        # HTF Analysis
        htf = signal.get("htf_analysis", {})
        if htf:
            logger.info(f"\n📈 HTF ANALYSIS:")
            logger.info(f"   Direction: {htf.get('direction', 'N/A').upper()}")
            logger.info(f"   Strength: {htf.get('strength', 0):.1f}/100")
            logger.info(f"   Structure: {htf.get('structure_quality', 'N/A')}")
            logger.info(f"   Premium/Discount: {htf.get('premium_discount', 'N/A').upper()}")
        
        # LTF Entry
        ltf = signal.get("ltf_entry_model", {})
        if ltf and ltf.get("found"):
            logger.info(f"\n🎯 LTF ENTRY MODEL:")
            logger.info(f"   ✅ Entry Found!")
            logger.info(f"   Type: {ltf.get('entry_type', 'N/A')}")
            logger.info(f"   Timeframe: {ltf.get('timeframe', 'N/A')}")
            if ltf.get("entry_zone"):
                logger.info(f"   Entry Zone: ₹{ltf['entry_zone'][0]:.2f} - ₹{ltf['entry_zone'][1]:.2f}")
            logger.info(f"   Momentum: {'✅' if ltf.get('momentum_confirmed') else '❌'}")
            logger.info(f"   Confidence: {ltf.get('confidence', 0):.2%}")
        else:
            logger.info(f"\n🎯 LTF ENTRY MODEL: ❌ Not found")
        
        # Option Recommendation
        option = signal.get("option", {})
        if option:
            logger.info(f"\n💰 RECOMMENDED OPTION:")
            logger.info(f"   Strike: {option.get('strike', 'N/A')} {option.get('type', 'N/A')}")
            logger.info(f"   Symbol: {option.get('trading_symbol', option.get('symbol', 'N/A'))}")
        
        # Entry Details
        entry = signal.get("entry", {})
        if entry:
            logger.info(f"\n📍 ENTRY DETAILS:")
            logger.info(f"   Entry Price: ₹{entry.get('price', 0):.2f}")
            logger.info(f"   Trigger: ₹{entry.get('trigger_level', 0):.2f}")
            logger.info(f"   Timing: {entry.get('timing', 'N/A')}")
        
        # Targets
        targets = signal.get("targets", {})
        if targets:
            logger.info(f"\n🎯 TARGETS & STOP LOSS:")
            logger.info(f"   Target 1: ₹{targets.get('target_1', 0):.2f}")
            logger.info(f"   Target 2: ₹{targets.get('target_2', 0):.2f}")
            logger.info(f"   Stop Loss: ₹{targets.get('stop_loss', 0):.2f}")
    else:
        logger.warning("⚠️ No signal data in response")
    
    # MTF Analysis
    mtf = results.get("mtf_analysis", {})
    if mtf and "error" not in mtf:
        logger.info(f"\n📊 MTF ANALYSIS:")
        logger.info(f"   Overall Bias: {mtf.get('overall_bias', 'N/A').upper()}")
        logger.info(f"   Timeframes: {mtf.get('timeframes_analyzed', [])}")
    
    # Market Status
    market = results.get("market_status", {})
    if market:
        logger.info(f"\n🏦 MARKET STATUS:")
        logger.info(f"   Status: {market.get('status', 'Unknown')}")
        logger.info(f"   Session: {market.get('session', 'Unknown')}")
    
    logger.info(f"\n{'='*70}")


async def test_local_signal_generation():
    """
    Test signal generation directly (without API) for faster debugging
    """
    logger.info("\n" + "=" * 70)
    logger.info("🔬 DIRECT SIGNAL GENERATION TEST (Local)")
    logger.info("=" * 70)
    
    # Import required modules
    from src.api.fyers_client import fyers_client
    from src.analytics.ict_analysis import analyze_multi_timeframe_ict_topdown
    from src.analytics.confidence_calculator import calculate_trade_confidence
    
    # Check if Fyers client is initialized
    if not fyers_client.fyers:
        logger.warning("⚠️ Fyers client not initialized, attempting authentication...")
        
        # Try to load token from database
        login_result = await login_user(TEST_EMAIL, TEST_PASSWORD)
        if login_result:
            fyers_token = await check_fyers_token(login_result["user"].id)
            if fyers_token:
                fyers_client.access_token = fyers_token.get("access_token")
                fyers_client._initialize_client()
                logger.info("✅ Fyers client initialized with stored token")
            else:
                logger.error("❌ No Fyers token available")
                return
        else:
            logger.error("❌ Cannot authenticate user")
            return
    
    # Fetch live data
    symbol = "NSE:NIFTY50-INDEX"
    logger.info(f"\n📊 Fetching LIVE candles for {symbol}...")
    
    candles = {}
    timeframes = {
        'D': (180, 'D'),
        '240': (60, '240'),   # 4H - 60 days (well within 100 day limit)
        '60': (30, '60'),     # 1H - 30 days
        '15': (15, '15'),     # 15m - 15 days
        '5': (7, '5'),        # 5m - 7 days
    }
    
    from datetime import timedelta
    end_date = datetime.now()
    
    for tf_key, (days, resolution) in timeframes.items():
        try:
            start_date = end_date - timedelta(days=days)
            df = fyers_client.get_historical_data(
                symbol=symbol,
                resolution=resolution,
                date_from=start_date,
                date_to=end_date
            )
            if df is not None and len(df) > 0:
                candles[tf_key] = df
                logger.info(f"   {tf_key}: {len(df)} candles")
        except Exception as e:
            logger.warning(f"   {tf_key}: Error - {e}")
    
    if not candles:
        logger.error("❌ No candle data fetched!")
        return
    
    # Get current price
    try:
        quote = fyers_client.get_quotes([symbol])
        current_price = quote['d'][0]['v']['lp'] if quote.get('s') == 'ok' else candles['D']['close'].iloc[-1]
    except:
        current_price = candles['D']['close'].iloc[-1]
    
    logger.info(f"\n💰 Current Price: ₹{current_price:,.2f}")
    
    # Run analysis
    logger.info(f"\n🎯 Running ICT Top-Down Analysis...")
    
    result = analyze_multi_timeframe_ict_topdown(
        candles_by_timeframe=candles,
        current_price=current_price,
        trading_mode="intraday"
    )
    
    htf_bias = result['htf_bias']
    ltf_entry = result['ltf_entry']
    
    # Display results
    logger.info(f"\n📈 HTF BIAS:")
    logger.info(f"   Direction: {htf_bias.overall_direction.upper()}")
    logger.info(f"   Strength: {htf_bias.bias_strength:.1f}/100")
    logger.info(f"   Structure: {htf_bias.structure_quality}")
    
    if ltf_entry:
        logger.info(f"\n🎯 LTF ENTRY FOUND!")
        logger.info(f"   Type: {ltf_entry.entry_type}")
        logger.info(f"   Timeframe: {ltf_entry.timeframe}")
        logger.info(f"   Entry Zone: {ltf_entry.entry_zone[0]:.2f} - {ltf_entry.entry_zone[1]:.2f}")
        logger.info(f"   Momentum: {'✅' if ltf_entry.momentum_confirmed else '❌'}")
    else:
        logger.info(f"\n🎯 LTF ENTRY: ❌ Not found")
    
    # Calculate confidence
    confidence = calculate_trade_confidence(
        htf_bias={
            'overall_direction': htf_bias.overall_direction,
            'bias_strength': htf_bias.bias_strength,
            'structure_quality': htf_bias.structure_quality,
            'premium_discount': htf_bias.premium_discount
        },
        ltf_entry={
            'entry_type': ltf_entry.entry_type if ltf_entry else 'NO_SETUP',
            'timeframe': ltf_entry.timeframe if ltf_entry else 'N/A',
            'momentum_confirmed': ltf_entry.momentum_confirmed if ltf_entry else False,
            'alignment_score': ltf_entry.alignment_score if ltf_entry else 0
        }
    )
    
    logger.info(f"\n📊 CONFIDENCE: {confidence['total']:.1f}% ({confidence['confidence_level']})")
    
    # Determine final signal
    trade_direction = htf_bias.overall_direction
    if trade_direction == 'neutral' and ltf_entry and ('MOMENTUM' in ltf_entry.entry_type or ltf_entry.alignment_score >= 50):
        if ltf_entry.trigger_price < current_price:
            trade_direction = 'bullish'
        else:
            trade_direction = 'bearish'
        logger.info(f"   ⚡ Momentum override: {trade_direction.upper()}")
    
    if trade_direction == 'bullish':
        action = "BUY CALL"
    elif trade_direction == 'bearish':
        action = "BUY PUT"
    else:
        action = "WAIT"
    
    logger.info(f"\n🚀 FINAL SIGNAL: {action}")
    logger.info("=" * 70)


async def main():
    """Main test function"""
    logger.info("=" * 70)
    logger.info("🔬 DASHBOARD SCAN TEST")
    logger.info(f"   Testing as user: {TEST_EMAIL}")
    logger.info(f"   Time: {datetime.now()}")
    logger.info("=" * 70)
    
    # Step 1: Login
    login_result = await login_user(TEST_EMAIL, TEST_PASSWORD)
    
    if not login_result:
        logger.error("❌ Cannot proceed without authentication")
        return
    
    # Step 2: Check Fyers token
    fyers_token = await check_fyers_token(login_result["user"].id)
    
    if not fyers_token:
        logger.warning("\n⚠️ User doesn't have a Fyers token stored!")
        logger.info("   The scan will fail without Fyers authentication.")
        logger.info("   User needs to connect their Fyers account first.")
    
    # Step 3: Test direct signal generation (local, faster)
    await test_local_signal_generation()
    
    # Step 4: Test via API (optional - requires server running)
    # Uncomment to test full API flow:
    # logger.info("\n" + "=" * 70)
    # logger.info("🌐 Testing via API endpoint...")
    # logger.info("=" * 70)
    # results = await run_options_scan(
    #     access_token=login_result["session"].access_token,
    #     index="NIFTY",
    #     quick_scan=True
    # )
    # display_scan_results(results)


if __name__ == "__main__":
    asyncio.run(main())
