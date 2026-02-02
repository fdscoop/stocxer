#!/usr/bin/env python3
"""
Test option scanner via API - exactly like Next.js frontend does
This tests the FULL analysis pipeline: MTF/ICT + Options + ML + News
"""

import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

API_URL = "http://localhost:8000"

def get_auth_token():
    """Get a valid Supabase auth token"""
    from supabase import create_client
    
    supabase = create_client(
        os.getenv('SUPABASE_URL'), 
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    
    # Use admin to create a session for testing
    # In production, user would login via frontend
    try:
        # Try to sign in
        auth_response = supabase.auth.sign_in_with_password({
            'email': 'binesh.balan@gmail.com',
            'password': 'Stocxer@123'  # Adjust if needed
        })
        if auth_response.session:
            return auth_response.session.access_token
    except Exception as e:
        print(f"Sign in failed: {e}")
    
    # Fallback: create admin session
    try:
        user = supabase.auth.admin.get_user_by_id('4f1d1b44-7459-43fa-8aec-f9b9a0605c4b')
        # Generate magic link token for testing
        link = supabase.auth.admin.generate_link({
            'type': 'magiclink',
            'email': 'binesh.balan@gmail.com'
        })
        # Extract token from link
        if hasattr(link, 'properties') and link.properties:
            return link.properties.hashed_token
    except Exception as e:
        print(f"Admin token failed: {e}")
    
    return None

def test_full_scan(index: str, expiry: str = "weekly", quick_scan: bool = True):
    """Test option scanner via API endpoint"""
    
    print(f"\n{'='*60}")
    print(f"🎯 FULL API TEST: {index} ({expiry})")
    print(f"   Mode: {'Quick' if quick_scan else 'Full (with 50 stocks)'}")
    print(f"{'='*60}")
    
    token = get_auth_token()
    if not token:
        print("❌ Could not get auth token")
        return
    
    print(f"✅ Got auth token: {token[:30]}...")
    
    # Build URL exactly like frontend does
    url = f"{API_URL}/options/scan"
    params = {
        "index": index,
        "expiry": expiry,
        "min_volume": 1000,
        "min_oi": 10000,
        "strategy": "all",
        "include_probability": True,
        "quick_scan": quick_scan,
        "analysis_mode": "auto"
    }
    
    print(f"\n📡 Calling: {url}")
    print(f"   Params: {params}")
    
    try:
        start_time = datetime.now()
        response = requests.get(
            url,
            params=params,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            timeout=120  # 2 min timeout for full scan
        )
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n⏱️  Response time: {elapsed:.1f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ SCAN SUCCESSFUL!")
            print(f"\n{'─'*50}")
            print(f"📈 MARKET DATA:")
            market = data.get('market_data', {})
            print(f"   Spot Price: ₹{market.get('spot_price', 0):,.2f}")
            print(f"   ATM Strike: {market.get('atm_strike')}")
            print(f"   VIX: {market.get('vix')}")
            print(f"   Expiry: {market.get('expiry_date')} ({market.get('days_to_expiry')} days)")
            
            # MTF/ICT Analysis
            print(f"\n{'─'*50}")
            print(f"🎯 MTF/ICT ANALYSIS:")
            mtf = data.get('mtf_ict_analysis', {})
            if mtf and not mtf.get('error'):
                print(f"   Overall Bias: {mtf.get('overall_bias', 'N/A').upper()}")
                print(f"   Timeframes: {mtf.get('timeframes_analyzed', [])}")
                for tf, details in mtf.get('timeframe_details', {}).items():
                    print(f"      {tf}: {details.get('bias')} - {details.get('trend')}")
                if mtf.get('confluence_zones'):
                    print(f"   Confluence Zones: {[z.get('level') for z in mtf.get('confluence_zones', [])]}")
            else:
                print(f"   ⚠️ Error: {mtf.get('error', 'Not available')}")
            
            # Probability Analysis (only in full mode)
            print(f"\n{'─'*50}")
            print(f"📊 PROBABILITY ANALYSIS:")
            prob = data.get('probability_analysis')
            if prob and not prob.get('error'):
                print(f"   Direction: {prob.get('expected_direction')}")
                print(f"   Probability Up: {prob.get('probability_up', 0):.1%}")
                print(f"   Probability Down: {prob.get('probability_down', 0):.1%}")
                print(f"   Stocks Scanned: {prob.get('stocks_scanned', 0)}/{prob.get('total_stocks', 0)}")
                print(f"   Bullish Stocks: {prob.get('bullish_stocks', 0)} ({prob.get('bullish_pct', 0):.1f}%)")
                print(f"   Bearish Stocks: {prob.get('bearish_stocks', 0)} ({prob.get('bearish_pct', 0):.1f}%)")
                print(f"   Recommended: {prob.get('recommended_option_type')}")
                print(f"   MTF Override: {prob.get('mtf_override', False)}")
            elif quick_scan:
                print(f"   ⚡ Quick scan mode - 50-stock analysis skipped")
            else:
                print(f"   ⚠️ Error: {prob.get('error', 'Not available') if prob else 'N/A'}")
            
            # Market Metrics (PCR, etc)
            print(f"\n{'─'*50}")
            print(f"📉 MARKET METRICS:")
            metrics = data.get('market_metrics', {})
            print(f"   PCR (OI): {metrics.get('pcr_oi', 0):.2f}")
            print(f"   PCR (Volume): {metrics.get('pcr_volume', 0):.2f}")
            print(f"   Max Pain: {metrics.get('max_pain')}")
            print(f"   ATM IV: {metrics.get('atm_iv', 0):.1f}%")
            
            # Opportunities
            print(f"\n{'─'*50}")
            print(f"💰 TOP OPPORTUNITIES:")
            opps = data.get('opportunities', [])[:5]
            for i, opp in enumerate(opps, 1):
                print(f"\n   {i}. {opp.get('type')} {opp.get('strike')}")
                print(f"      LTP: ₹{opp.get('ltp', 0):.2f}")
                print(f"      Score: {opp.get('score', 0):.1f}")
                print(f"      Signal: {opp.get('signal', 'N/A')}")
                entry = opp.get('entry_analysis', {})
                if entry:
                    print(f"      Entry Grade: {entry.get('entry_grade', 'N/A')}")
                    print(f"      Recommendation: {entry.get('entry_recommendation', 'N/A')}")
            
            # News Sentiment
            print(f"\n{'─'*50}")
            print(f"📰 NEWS SENTIMENT:")
            sentiment = data.get('news_sentiment')
            if sentiment:
                print(f"   Overall: {sentiment.get('sentiment', 'N/A')}")
                print(f"   Score: {sentiment.get('sentiment_score', 0):.2f}")
            else:
                print(f"   Not available")
            
            print(f"\n{'='*60}")
            print(f"✅ Full pipeline test completed for {index}")
            print(f"{'='*60}")
            
        else:
            print(f"\n❌ SCAN FAILED:")
            try:
                error = response.json()
                print(f"   Error: {json.dumps(error, indent=2)}")
            except:
                print(f"   Response: {response.text[:500]}")
                
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 120s")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Check backend is running
    try:
        health = requests.get(f"{API_URL}/health", timeout=5)
        if health.status_code != 200:
            print("❌ Backend not running! Start with: python main.py")
            exit(1)
        print("✅ Backend is running")
    except:
        print("❌ Backend not running! Start with: python main.py")
        exit(1)
    
    # Test all indices with quick scan
    for index in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
        test_full_scan(index, 'weekly', quick_scan=True)
