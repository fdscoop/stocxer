#!/usr/bin/env python3
"""
Test saving and retrieving scan opportunities
"""

import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
from src.services.screener_service import screener_service

USER_ID = "4f1d1b44-7459-43fa-8aec-f9b9a0605c4b"

async def test_save_and_retrieve():
    print("=" * 70)
    print("🧪 Testing Scan Opportunities Save & Retrieve")
    print("=" * 70)
    
    # Create test data (simulating /options/scan output)
    import uuid
    scan_id = str(uuid.uuid4())
    
    test_options = [
        {
            "strike": 24800,
            "type": "PE",
            "fyers_symbol": "NSE:NIFTY2620324800PE",
            "ltp": 200.55,
            "bid": 200.00,
            "ask": 201.00,
            "volume": 150000,
            "oi": 2500000,
            "oi_change": 50000,
            "oi_change_pct": 2.0,
            "iv": 15.1,
            "delta": -0.45,
            "gamma": 0.01,
            "theta": -5.0,
            "vega": 10.0,
            "score": 85.5,
            "strategy_match": "bearish",
            "recommendation": "Strong bearish setup",
            "probability_boost": True,
            "sentiment_boost": False,
            "entry_analysis": {
                "entry_grade": "A",
                "entry_recommendation": "Enter on pullback to 195",
                "limit_order_price": 195.0,
                "max_acceptable_price": 205.0,
                "wait_for_pullback": True,
                "pullback_probability": 65.0,
                "option_target_1": 260,
                "option_target_2": 350,
                "option_stop_loss": 140
            },
            "discount_zone": {
                "zone_type": "premium_discount",
                "is_in_discount": True,
                "discount_pct": 5.2
            }
        },
        {
            "strike": 24850,
            "type": "PE",
            "fyers_symbol": "NSE:NIFTY2620324850PE",
            "ltp": 220.30,
            "volume": 120000,
            "oi": 2100000,
            "iv": 14.8,
            "delta": -0.48,
            "score": 78.2,
            "strategy_match": "bearish",
            "recommendation": "ATM put - higher delta"
        },
        {
            "strike": 24750,
            "type": "PE",
            "fyers_symbol": "NSE:NIFTY2620324750PE",
            "ltp": 175.45,
            "volume": 180000,
            "oi": 2800000,
            "iv": 15.5,
            "delta": -0.42,
            "score": 72.8,
            "strategy_match": "bearish",
            "recommendation": "Slightly OTM put"
        },
        {
            "strike": 24900,
            "type": "CE",
            "fyers_symbol": "NSE:NIFTY2620324900CE",
            "ltp": 85.20,
            "volume": 95000,
            "oi": 1800000,
            "iv": 13.2,
            "delta": 0.35,
            "score": 55.0,
            "strategy_match": "bullish",
            "recommendation": "Counter-trend play"
        },
        {
            "strike": 24950,
            "type": "CE",
            "fyers_symbol": "NSE:NIFTY2620324950CE",
            "ltp": 65.50,
            "volume": 85000,
            "oi": 1500000,
            "iv": 12.8,
            "delta": 0.30,
            "score": 48.5,
            "strategy_match": "bullish",
            "recommendation": "OTM call - low cost"
        }
    ]
    
    market_data = {
        "spot_price": 24825.45,
        "future_price": 24791.80,
        "pcr_oi": 0.59,
        "vix": 15.2
    }
    
    print(f"\n📝 Test Data:")
    print(f"   Scan ID: {scan_id[:8]}...")
    print(f"   Options: {len(test_options)}")
    print(f"   Top Option: {test_options[0]['strike']} {test_options[0]['type']} (Score: {test_options[0]['score']})")
    
    # Step 1: Save opportunities
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("💾 Step 1: Saving scan opportunities...")
    
    result = await screener_service.save_scan_opportunities(
        user_id=USER_ID,
        scan_id=scan_id,
        index="NIFTY",
        expiry_date="2026-02-03",
        scan_mode="quick",
        options=test_options,
        market_data=market_data,
        recommended_strike=24800,
        recommended_type="PE",
        max_options=10
    )
    
    if result.get("saved"):
        print(f"   ✅ Saved {result.get('count')} opportunities")
    else:
        print(f"   ❌ Save failed: {result.get('error')}")
        return
    
    # Step 2: Retrieve by scan_id
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔍 Step 2: Retrieving by scan_id...")
    
    opportunities = await screener_service.get_scan_opportunities(
        user_id=USER_ID,
        scan_id=scan_id
    )
    
    print(f"   ✅ Retrieved {len(opportunities)} opportunities")
    
    # Display
    print(f"\n   📊 Retrieved Opportunities:")
    for opp in opportunities:
        recommended = "⭐" if opp.get("is_recommended") else "  "
        print(f"      {recommended} #{opp['rank']}: {opp['strike']} {opp['option_type']} - Score: {opp['score']:.1f} - Grade: {opp.get('entry_grade', 'N/A')}")
    
    # Step 3: Retrieve latest
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔍 Step 3: Retrieving latest scan opportunities...")
    
    latest = await screener_service.get_latest_scan_opportunities(
        user_id=USER_ID,
        index="NIFTY"
    )
    
    print(f"   ✅ Retrieved {len(latest)} from latest scan")
    
    # Step 4: Test API endpoint
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🌐 Step 4: Testing API endpoint...")
    
    import httpx
    from config.supabase_config import supabase
    
    # Get a token
    supabase_client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
    
    async with httpx.AsyncClient() as client:
        # Get auth token (you'd normally get this from login)
        # For test, we'll just check the endpoint exists
        response = await client.get(
            f"http://localhost:8000/options/scan-opportunities/latest",
            headers={"Authorization": "Bearer test_token"}
        )
        
        if response.status_code == 401:
            print(f"   ⚠️ API requires valid auth token (expected)")
        elif response.status_code == 200:
            data = response.json()
            print(f"   ✅ API returned {data.get('count', 0)} opportunities")
        else:
            print(f"   ⚠️ API returned status {response.status_code}")
    
    # Summary
    print(f"\n" + "=" * 70)
    print("✅ TEST COMPLETE!")
    print("=" * 70)
    print(f"\n📋 Summary:")
    print(f"   ✅ Saved {result.get('count')} scan opportunities")
    print(f"   ✅ Retrieved by scan_id: {len(opportunities)}")
    print(f"   ✅ Retrieved latest: {len(latest)}")
    print(f"\n🔗 New API Endpoints:")
    print(f"   GET /options/scan-opportunities/latest - Get most recent scan's options")
    print(f"   GET /options/scan-opportunities/{{scan_id}} - Get options by scan ID")
    print(f"   GET /options/scan-opportunities - Get all recent opportunities")
    print()

if __name__ == "__main__":
    asyncio.run(test_save_and_retrieve())
