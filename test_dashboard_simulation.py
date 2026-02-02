#!/usr/bin/env python3
"""
Test option scanner as user scans from dashboard
Simulates the exact API call the frontend makes
"""

import asyncio
import json
from datetime import datetime

async def test_dashboard_scan():
    """Test option scanner like the dashboard does"""
    
    print("=" * 60)
    print("🎯 TESTING OPTION SCANNER - Dashboard Simulation")
    print("=" * 60)
    
    # Import after setting up path
    import sys
    sys.path.insert(0, '/Users/bineshbalan/TradeWise')
    
    from src.api.fyers_client import fyers_client
    from src.analytics.index_options import IndexOptionsAnalyzer, get_index_analyzer
    from supabase import create_client
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize Fyers with stored token
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
    result = supabase.table('fyers_tokens').select('*').order('updated_at', desc=True).limit(1).execute()
    
    if result.data:
        token_data = result.data[0]
        fyers_client.access_token = token_data['access_token']
        fyers_client._initialize_client()
        print(f"✅ Fyers initialized with token (expires: {token_data.get('expires_at', 'unknown')})")
    else:
        print("❌ No Fyers token found!")
        return
    
    # Test all indices like user would from dashboard
    indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
    
    for index in indices:
        print(f"\n{'='*50}")
        print(f"📊 Scanning {index}...")
        print(f"{'='*50}")
        
        try:
            analyzer = get_index_analyzer(fyers_client)
            
            # This is what the dashboard calls
            analysis = analyzer.analyze_option_chain(index, 'weekly')
            
            if analysis:
                print(f"\n✅ {index} Scan Results:")
                print(f"   📈 Spot Price: ₹{analysis.spot_price:,.2f}")
                print(f"   📊 Futures Price: ₹{analysis.future_price:,.2f}")
                print(f"   📉 Basis: {analysis.basis:.2f} ({analysis.basis_pct:.2f}%)")
                print(f"   📊 PCR (OI): {analysis.pcr_oi:.2f}")
                print(f"   📊 PCR (Volume): {analysis.pcr_volume:.2f}")
                print(f"   🎯 Max Pain: {analysis.max_pain}")
                print(f"   💰 ATM Strike: {analysis.atm_strike}")
                print(f"   📊 ATM IV: {analysis.atm_iv:.1f}%")
                print(f"   📅 Expiry: {analysis.expiry_date} ({analysis.days_to_expiry} days)")
                print(f"   📊 Strikes Analyzed: {len(analysis.strikes)}")
                
                # Support/Resistance levels
                if analysis.support_levels:
                    print(f"   🟢 Support Levels: {', '.join([str(int(s)) for s in analysis.support_levels[:3]])}")
                if analysis.resistance_levels:
                    print(f"   🔴 Resistance Levels: {', '.join([str(int(r)) for r in analysis.resistance_levels[:3]])}")
                
                # Top strikes by OI
                if analysis.strikes:
                    sorted_calls = sorted([s for s in analysis.strikes if s.call_oi > 0], 
                                         key=lambda x: x.call_oi, reverse=True)[:3]
                    sorted_puts = sorted([s for s in analysis.strikes if s.put_oi > 0], 
                                        key=lambda x: x.put_oi, reverse=True)[:3]
                    
                    print(f"\n   📊 Top Call OI Strikes:")
                    for s in sorted_calls:
                        print(f"      {int(s.strike)}: OI={s.call_oi:,}, Vol={s.call_volume:,}")
                    
                    print(f"\n   📊 Top Put OI Strikes:")
                    for s in sorted_puts:
                        print(f"      {int(s.strike)}: OI={s.put_oi:,}, Vol={s.put_volume:,}")
                
                # Test saving to database (like dashboard does)
                print(f"\n   💾 Simulating save to database...")
                scan_result = {
                    'user_id': '4f1d1b44-7459-43fa-8aec-f9b9a0605c4b',
                    'index': index,
                    'spot_price': analysis.spot_price,
                    'futures_price': analysis.future_price,
                    'pcr_oi': analysis.pcr_oi,
                    'pcr_volume': analysis.pcr_volume,
                    'max_pain': analysis.max_pain,
                    'atm_iv': analysis.atm_iv,
                    'expiry_date': analysis.expiry_date,
                    'scanned_at': datetime.now().isoformat(),
                    'total_call_oi': analysis.total_call_oi,
                    'total_put_oi': analysis.total_put_oi,
                }
                
                # Save to option_scan_results table
                try:
                    save_result = supabase.table('option_scan_results').insert(scan_result).execute()
                    print(f"   ✅ Saved to database! ID: {save_result.data[0].get('id', 'unknown') if save_result.data else 'none'}")
                except Exception as e:
                    print(f"   ⚠️ Database save error: {e}")
                    
            else:
                print(f"❌ {index}: No analysis result returned")
                
        except Exception as e:
            import traceback
            print(f"❌ {index} Error: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Dashboard scan simulation complete!")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(test_dashboard_scan())
