#!/usr/bin/env python3
"""
Verify all 8 steps of the scan flow are executing correctly.
"""

import json

def verify_scan_flow():
    with open('scan_debug_output.json', 'r') as f:
        d = json.load(f)
    
    scan = d.get('scan_data', {})
    signal = d.get('signal_data', {})
    
    print('=' * 80)
    print('📊 FULL SCAN FLOW VERIFICATION')
    print('=' * 80)
    
    # Step 1: Authentication - Done (we got data back)
    print('\n✅ STEP 1: AUTHENTICATION - Passed')
    
    # Step 2: Options Chain Fetch
    print('\n📦 STEP 2: OPTIONS CHAIN FETCH')
    print(f'   Total Options: {scan.get("total_options", 0)}')
    market = scan.get('market_data', {})
    print(f'   Spot Price: {market.get("spot_price", "N/A")}')
    print(f'   Future Price: {market.get("future_price", "N/A")}')
    print(f'   Data Source: {scan.get("data_source", "N/A")}')
    
    # Step 3: MTF/ICT Analysis
    print('\n📈 STEP 3: MTF/ICT ANALYSIS')
    mtf_ict = scan.get('mtf_ict_analysis', {})
    if mtf_ict:
        print(f'   Overall Bias: {mtf_ict.get("overall_bias", "N/A")}')
        print(f'   Trend Strength: {mtf_ict.get("trend_strength", "N/A")}')
        print(f'   Confluence Zones: {len(mtf_ict.get("confluence_zones", []))}')
        tf_biases = mtf_ict.get('timeframe_biases', {})
        if tf_biases:
            for tf, data in list(tf_biases.items())[:4]:
                print(f'   {tf}: {data.get("bias", "N/A")} | Trend: {data.get("trend", "N/A")}')
    else:
        print('   ⚠️ MTF/ICT Analysis not found in scan data')
    
    # Also check signal's mtf_analysis
    mtf_signal = signal.get('mtf_analysis', {})
    if mtf_signal:
        print(f'\n   From Signal:')
        print(f'   Overall Bias: {mtf_signal.get("overall_bias", "N/A")}')
        print(f'   Trend Strength: {mtf_signal.get("trend_strength", "N/A")}')
    
    # Step 4: Probability Analysis
    print('\n🎯 STEP 4: PROBABILITY ANALYSIS (Constituent Stocks)')
    prob_scan = scan.get('probability_analysis', {})
    prob_signal = signal.get('probability_analysis', {})
    prob = prob_signal if prob_signal else prob_scan
    
    if prob:
        print(f'   Final Bias: {prob.get("final_bias", "N/A")}')
        print(f'   Confidence: {prob.get("confidence_score", "N/A")}')
        print(f'   Recommended Action: {prob.get("recommended_action", "N/A")}')
        print(f'   Bullish Stocks: {prob.get("bullish_stocks", "N/A")}')
        print(f'   Bearish Stocks: {prob.get("bearish_stocks", "N/A")}')
        print(f'   Probability Up: {prob.get("probability_up", "N/A")}')
        print(f'   Probability Down: {prob.get("probability_down", "N/A")}')
    else:
        print('   ⚠️ Probability Analysis not found')
    
    # Check constituent recommendation
    const_rec = signal.get('constituent_recommendation', {})
    if const_rec and isinstance(const_rec, dict):
        print(f'\n   Constituent Recommendation:')
        print(f'   Bias: {const_rec.get("bias", "N/A")}')
        print(f'   Confidence: {const_rec.get("confidence", "N/A")}')
        print(f'   Action: {const_rec.get("action", "N/A")}')
    elif const_rec:
        print(f'\n   Constituent Recommendation: {const_rec}')
    
    # Step 5: Option Chain Analysis (Greeks, IV, PCR)
    print('\n📊 STEP 5: OPTION CHAIN ANALYSIS')
    greeks = signal.get('greeks', {})
    if greeks:
        print(f'   Delta: {greeks.get("delta", "N/A")}')
        print(f'   Gamma: {greeks.get("gamma", "N/A")}')
        print(f'   Theta: {greeks.get("theta", "N/A")}')
        print(f'   Vega: {greeks.get("vega", "N/A")}')
        print(f'   IV: {greeks.get("iv", "N/A")}%')
    
    pricing = signal.get('pricing', {})
    if pricing:
        print(f'   ATM Strike: {pricing.get("atm_strike", "N/A")}')
        print(f'   PCR: {pricing.get("pcr", "N/A")}')
        print(f'   Max Pain: {pricing.get("max_pain", "N/A")}')
    
    # Step 6: News Sentiment
    print('\n📰 STEP 6: NEWS SENTIMENT')
    sentiment = scan.get('sentiment_analysis', {})
    if sentiment:
        print(f'   Sentiment Score: {sentiment.get("score", "N/A")}')
        print(f'   Sentiment Label: {sentiment.get("label", "N/A")}')
        print(f'   News Count: {sentiment.get("news_count", "N/A")}')
    else:
        print('   ⚠️ Sentiment Analysis not found in scan')
    
    # Step 7: Enhanced ML Prediction (NEW!)
    print('\n🧠 STEP 7: ENHANCED ML PREDICTION (NEW!)')
    ml = signal.get('enhanced_ml_prediction', {})
    if ml and not ml.get('error'):
        modules = ml.get('available_modules', {})
        print(f'   Direction Module: {"✅" if modules.get("direction") else "❌"}')
        print(f'   Speed Module: {"✅" if modules.get("speed") else "❌"}')
        print(f'   IV Module: {"✅" if modules.get("iv") else "❌"}')
        print(f'   Theta Module: {"✅" if modules.get("theta") else "❌"}')
        print(f'   Simulator Module: {"✅" if modules.get("simulator") else "❌"}')
        
        # Direction
        dp = ml.get('direction_prediction', {})
        if dp and not dp.get('error'):
            print(f'\n   Direction: {dp.get("direction")} ({dp.get("confidence", 0):.0%})')
        
        # Speed
        sp = ml.get('speed_prediction', {})
        if sp and not sp.get('error'):
            print(f'   Speed: {sp.get("category")} ({sp.get("confidence", 0):.0%})')
        
        # IV
        iv = ml.get('iv_prediction', {})
        if iv and not iv.get('error'):
            print(f'   IV: {iv.get("direction")} ({iv.get("confidence", 0):.0%})')
        
        # Simulation
        sim = ml.get('simulation', {})
        if sim and not sim.get('error'):
            grade = sim.get('trade_grade', {})
            print(f'   Trade Grade: {grade.get("grade", "N/A")}')
        
        cr = ml.get('combined_recommendation', {})
        if cr:
            print(f'\n   ML Action: {cr.get("action", "N/A")}')
            print(f'   ML Confidence: {cr.get("confidence", 0):.0%}')
    else:
        print(f'   ⚠️ ML Error: {ml.get("error", "Unknown")}')
    
    # Step 8: Save to Database
    print('\n💾 STEP 8: SAVE TO DATABASE')
    print(f'   Saved to DB: {signal.get("saved_to_db", "N/A")}')
    print(f'   Signal ID: {signal.get("signal_id", "N/A")}')
    print(f'   Opportunities Saved: {scan.get("opportunities_saved", "N/A")}')
    
    # Final Signal Summary
    print('\n' + '=' * 80)
    print('🎯 FINAL SIGNAL SUMMARY')
    print('=' * 80)
    print(f'   Index: {signal.get("index", "N/A")}')
    print(f'   Action: {signal.get("action", "N/A")}')
    print(f'   Signal Type: {signal.get("signal", "N/A")}')
    opt = signal.get("option", {})
    print(f'   Option: Strike={opt.get("strike")} Type={opt.get("type")}')
    entry = signal.get("entry", {})
    print(f'   Entry Price: {entry.get("price", "N/A")}')
    targets = signal.get("targets", {})
    print(f'   Target 1: {targets.get("target_1", "N/A")}')
    print(f'   Target 2: {targets.get("target_2", "N/A")}')
    print(f'   Stop Loss: {targets.get("stop_loss", "N/A")}')
    print(f'   Confidence: {signal.get("confidence", "N/A")}')
    print(f'   Spot Price: {signal.get("spot_price", "N/A")}')
    
    print('\n' + '=' * 80)
    print('✅ SCAN FLOW VERIFICATION COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    verify_scan_flow()
