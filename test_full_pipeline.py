#!/usr/bin/env python3
"""
Test FULL option scanner pipeline - exactly what the API endpoint does
This simulates the complete analysis: MTF/ICT + Options + ML + News + Chart
"""

import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

print("=" * 70)
print("🎯 FULL PIPELINE TEST - Same as /options/scan API")
print("=" * 70)

# Initialize Fyers with stored token
from src.api.fyers_client import fyers_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
result = supabase.table('fyers_tokens').select('*').order('updated_at', desc=True).limit(1).execute()

if result.data:
    token_data = result.data[0]
    fyers_client.access_token = token_data['access_token']
    fyers_client._initialize_client()
    print(f"✅ Fyers initialized (expires: {token_data.get('expires_at', 'unknown')[:16]})")
else:
    print("❌ No Fyers token found!")
    exit(1)

def test_full_pipeline(index: str, expiry: str = "weekly", quick_scan: bool = True):
    """Run the complete analysis pipeline"""
    
    print(f"\n{'='*60}")
    print(f"📊 SCANNING {index} - {'Quick' if quick_scan else 'Full'} Mode")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    
    # ==================== STEP 1: MTF/ICT ANALYSIS ====================
    print(f"\n🔍 STEP 1: MTF/ICT Analysis...")
    try:
        from src.analytics.mtf_ict_analysis import MultiTimeframeICTAnalyzer, get_mtf_analyzer, Timeframe
        
        index_symbol_map = {
            "NIFTY": "NSE:NIFTY50-INDEX",
            "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
            "FINNIFTY": "NSE:FINNIFTY-INDEX",
        }
        mtf_symbol = index_symbol_map.get(index.upper())
        
        mtf_analyzer = get_mtf_analyzer(fyers_client)
        
        # Intraday timeframes
        timeframes = [
            Timeframe.DAILY,
            Timeframe.FOUR_HOUR,
            Timeframe.ONE_HOUR,
            Timeframe.FIFTEEN_MIN,
            Timeframe.FIVE_MIN
        ]
        
        mtf_result = mtf_analyzer.analyze(mtf_symbol, timeframes)
        mtf_bias = mtf_result.overall_bias
        
        print(f"   ✅ Overall Bias: {mtf_bias.upper()}")
        for tf_key, tf_analysis in mtf_result.analyses.items():
            print(f"      {tf_key}: {tf_analysis.bias} - {tf_analysis.market_structure.trend}")
        
        if mtf_result.confluence_zones:
            print(f"   📍 Confluence Zones: {[z.get('center', z.get('level')) for z in mtf_result.confluence_zones[:3]]}")
            
    except Exception as e:
        print(f"   ⚠️ MTF Analysis failed: {e}")
        mtf_bias = None
        mtf_result = None
    
    # ==================== STEP 2: PROBABILITY ANALYSIS ====================
    probability_analysis = None
    recommended_option_type = None
    
    if not quick_scan:
        print(f"\n📊 STEP 2: Probability Analysis (50 stocks)...")
        try:
            from src.analytics.index_probability import get_probability_analyzer
            
            prob_analyzer = get_probability_analyzer(fyers_client, analysis_mode="intraday")
            prediction = prob_analyzer.analyze_index(index.upper())
            
            if prediction:
                print(f"   ✅ Direction: {prediction.expected_direction}")
                print(f"   Probability Up: {prediction.prob_up:.1%}")
                print(f"   Probability Down: {prediction.prob_down:.1%}")
                print(f"   Stocks Scanned: {prediction.total_stocks_analyzed}")
                print(f"   Bullish: {prediction.bullish_stocks}, Bearish: {prediction.bearish_stocks}")
                
                probability_analysis = prediction
                
                # Determine recommended option type
                if prediction.expected_direction == "BULLISH":
                    recommended_option_type = "CALL"
                elif prediction.expected_direction == "BEARISH":
                    recommended_option_type = "PUT"
                else:
                    recommended_option_type = "STRADDLE"
                    
        except Exception as e:
            print(f"   ⚠️ Probability Analysis failed: {e}")
    else:
        print(f"\n⚡ STEP 2: SKIPPED (Quick scan mode)")
        # Use MTF bias only
        if mtf_bias:
            if mtf_bias == "bullish":
                recommended_option_type = "CALL"
            elif mtf_bias == "bearish":
                recommended_option_type = "PUT"
            else:
                recommended_option_type = "STRADDLE"
            print(f"   Using MTF bias: {mtf_bias} → {recommended_option_type}")
    
    # ==================== STEP 3: OPTION CHAIN ANALYSIS ====================
    print(f"\n📈 STEP 3: Option Chain Analysis...")
    try:
        from src.analytics.index_options import get_index_analyzer
        
        analyzer = get_index_analyzer(fyers_client)
        chain = analyzer.analyze_option_chain(index.upper(), expiry)
        
        if chain:
            print(f"   ✅ Spot: ₹{chain.spot_price:,.2f}")
            print(f"   Futures: ₹{chain.future_price:,.2f}")
            print(f"   PCR (OI): {chain.pcr_oi:.2f}")
            print(f"   PCR (Volume): {chain.pcr_volume:.2f}")
            print(f"   Max Pain: {chain.max_pain}")
            print(f"   ATM Strike: {chain.atm_strike}")
            print(f"   ATM IV: {chain.atm_iv:.1f}%")
            print(f"   Expiry: {chain.expiry_date} ({chain.days_to_expiry} days)")
            print(f"   Strikes: {len(chain.strikes)}")
            
            # Top OI strikes
            sorted_calls = sorted([s for s in chain.strikes if s.call_oi > 0], 
                                 key=lambda x: x.call_oi, reverse=True)[:3]
            sorted_puts = sorted([s for s in chain.strikes if s.put_oi > 0], 
                                key=lambda x: x.put_oi, reverse=True)[:3]
            
            print(f"\n   📊 Top Call OI: {[int(s.strike) for s in sorted_calls]}")
            print(f"   📊 Top Put OI: {[int(s.strike) for s in sorted_puts]}")
        else:
            print(f"   ❌ No option chain data!")
            return
            
    except Exception as e:
        print(f"   ❌ Option Chain failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ==================== STEP 4: NEWS SENTIMENT ====================
    print(f"\n📰 STEP 4: News Sentiment...")
    try:
        from src.analytics.news_sentiment import news_analyzer
        import asyncio
        
        async def get_sentiment():
            return await news_analyzer.get_sentiment_for_signal(
                symbol=index.upper(),
                signal_type=recommended_option_type
            )
        
        sentiment_data = asyncio.run(get_sentiment())
        
        if sentiment_data:
            print(f"   ✅ Sentiment: {sentiment_data.get('sentiment', 'N/A')}")
            print(f"   Score: {sentiment_data.get('sentiment_score', 0):.2f}")
        else:
            print(f"   ⚠️ No sentiment data")
            
    except Exception as e:
        print(f"   ⚠️ News Sentiment failed: {e}")
    
    # ==================== STEP 5: PROCESS OPTIONS ====================
    print(f"\n💰 STEP 5: Process Options...")
    try:
        # Filter high-volume, high-OI options
        good_calls = [s for s in chain.strikes 
                     if s.call_volume > 1000 and s.call_oi > 10000]
        good_puts = [s for s in chain.strikes 
                    if s.put_volume > 1000 and s.put_oi > 10000]
        
        print(f"   Found {len(good_calls)} CALL opportunities")
        print(f"   Found {len(good_puts)} PUT opportunities")
        
        # Show top opportunities based on recommendation
        if recommended_option_type == "CALL" and good_calls:
            print(f"\n   🎯 Top CALL opportunities (recommended):")
            for s in sorted(good_calls, key=lambda x: x.call_oi, reverse=True)[:3]:
                print(f"      Strike {int(s.strike)}: LTP=₹{s.call_ltp:.2f}, OI={s.call_oi:,}, Vol={s.call_volume:,}")
        elif recommended_option_type == "PUT" and good_puts:
            print(f"\n   🎯 Top PUT opportunities (recommended):")
            for s in sorted(good_puts, key=lambda x: x.put_oi, reverse=True)[:3]:
                print(f"      Strike {int(s.strike)}: LTP=₹{s.put_ltp:.2f}, OI={s.put_oi:,}, Vol={s.put_volume:,}")
                
    except Exception as e:
        print(f"   ⚠️ Process Options failed: {e}")
    
    # ==================== STEP 6: SAVE TO DATABASE ====================
    print(f"\n💾 STEP 6: Save to Database...")
    try:
        scan_result = {
            'user_id': '4f1d1b44-7459-43fa-8aec-f9b9a0605c4b',
            'index': index,
            'spot_price': chain.spot_price,
            'signal': recommended_option_type or 'NEUTRAL',
            'action': f"Consider {recommended_option_type}" if recommended_option_type else "Wait",
            'confidence': 0.7 if mtf_bias else 0.5,
            'confidence_level': 'high' if mtf_bias else 'medium',
            'analysis_data': {
                'mtf_bias': mtf_bias,
                'pcr_oi': chain.pcr_oi,
                'max_pain': chain.max_pain,
                'atm_iv': chain.atm_iv
            }
        }
        
        # Note: Actual save would go to option_scanner_results table
        # For testing, we just print
        print(f"   Would save: {index} - {recommended_option_type} @ ₹{chain.spot_price:,.2f}")
        print(f"   MTF Bias: {mtf_bias}, PCR: {chain.pcr_oi:.2f}")
        
    except Exception as e:
        print(f"   ⚠️ Save failed: {e}")
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n⏱️  Total time: {elapsed:.1f}s")
    
    # ==================== STEP 7: GENERATE ACTIONABLE SIGNAL ====================
    print(f"\n🎯 STEP 7: Generate Actionable Signal...")
    try:
        from src.analytics.signal_generator import generate_actionable_signal
        
        # Build signal data
        signal_data = {
            "index": index,
            "mtf_bias": mtf_bias,
            "chain_data": {
                "spot_price": chain.spot_price,
                "future_price": chain.future_price,
                "atm_strike": chain.atm_strike,
                "pcr_oi": chain.pcr_oi,
                "max_pain": chain.max_pain,
                "atm_iv": chain.atm_iv,
                "days_to_expiry": chain.days_to_expiry,
                "expiry_date": chain.expiry_date
            },
            "recommended_option_type": recommended_option_type
        }
        
        # Generate signal
        signal = generate_actionable_signal(
            symbol=f"NSE:{index}50-INDEX" if index == "NIFTY" else f"NSE:{index}-INDEX",
            chain_data=signal_data["chain_data"],
            mtf_bias=mtf_bias,
            recommended_type=recommended_option_type
        )
        
        if signal:
            print(f"   ✅ Signal Generated!")
            print(f"      Action: {signal.get('action', 'N/A')}")
            print(f"      Option: {signal.get('option', {}).get('strike')} {signal.get('option', {}).get('type')}")
            print(f"      Entry: ₹{signal.get('entry', {}).get('price', 0):.2f}")
            print(f"      Target 1: ₹{signal.get('targets', {}).get('target_1', 0)}")
            print(f"      Stop Loss: ₹{signal.get('targets', {}).get('stop_loss', 0)}")
            print(f"      Confidence: {signal.get('confidence', {}).get('level', 'N/A')}")
        else:
            print(f"   ⚠️ No signal generated")
            
    except ImportError:
        print(f"   ⚠️ Signal generator not available as separate module")
        # Generate simple signal based on analysis
        if recommended_option_type and chain:
            print(f"   📝 Manual Signal Construction:")
            
            strike = chain.atm_strike
            if recommended_option_type == "CALL":
                # OTM call
                strike = chain.atm_strike + 100 if index == "NIFTY" else chain.atm_strike + 500
                strikes_data = [s for s in chain.strikes if s.strike == strike]
                ltp = strikes_data[0].call_ltp if strikes_data else 100
            else:
                # OTM put
                strike = chain.atm_strike - 100 if index == "NIFTY" else chain.atm_strike - 500
                strikes_data = [s for s in chain.strikes if s.strike == strike]
                ltp = strikes_data[0].put_ltp if strikes_data else 100
            
            signal = {
                "action": f"BUY {recommended_option_type}",
                "signal": f"ICT_{mtf_bias.upper()}_BIAS" if mtf_bias else "ICT_NEUTRAL_BIAS",
                "option": {
                    "strike": strike,
                    "type": "CE" if recommended_option_type == "CALL" else "PE"
                },
                "entry": {
                    "price": ltp,
                    "trigger_level": chain.spot_price
                },
                "targets": {
                    "target_1": round(ltp * 1.3),
                    "target_2": round(ltp * 1.8),
                    "stop_loss": round(ltp * 0.75)
                },
                "confidence": {
                    "level": "HIGH" if mtf_bias else "MEDIUM",
                    "score": 75 if mtf_bias else 55
                },
                "index_data": {
                    "spot_price": chain.spot_price,
                    "pcr_oi": chain.pcr_oi,
                    "max_pain": chain.max_pain
                }
            }
            
            print(f"   ✅ Signal: {signal['action']}")
            print(f"      Strike: {signal['option']['strike']} {signal['option']['type']}")
            print(f"      Entry: ₹{signal['entry']['price']:.2f}")
            print(f"      Target 1: ₹{signal['targets']['target_1']}")
            print(f"      Stop Loss: ₹{signal['targets']['stop_loss']}")
            print(f"      Confidence: {signal['confidence']['level']} ({signal['confidence']['score']}%)")
    except Exception as e:
        print(f"   ❌ Signal generation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # ==================== SUMMARY ====================
    print(f"\n{'─'*60}")
    print(f"📋 SUMMARY FOR {index}:")
    print(f"{'─'*60}")
    print(f"   MTF/ICT Bias: {mtf_bias.upper() if mtf_bias else 'N/A'}")
    print(f"   Spot Price: ₹{chain.spot_price:,.2f}")
    print(f"   PCR: {chain.pcr_oi:.2f} ({'Bullish' if chain.pcr_oi < 0.8 else 'Bearish' if chain.pcr_oi > 1.2 else 'Neutral'})")
    print(f"   Max Pain: {chain.max_pain}")
    print(f"   Recommended: {recommended_option_type}")
    print(f"{'─'*60}")

if __name__ == '__main__':
    # Test all indices
    for index in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
        test_full_pipeline(index, 'weekly', quick_scan=True)
    
    print("\n" + "=" * 70)
    print("✅ FULL PIPELINE TEST COMPLETE")
    print("=" * 70)
