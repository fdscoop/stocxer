#!/usr/bin/env python3
"""
NIFTY AMD (Accumulation, Manipulation, Distribution) Pattern Analysis

This script analyzes why TradeWise didn't detect the AMD pattern in lower timeframes.

What happened on Feb 6, 2026:
1. App suggested PE (25500, 25450, 25550) in the morning - Bearish bias
2. Market moved within 4H ICT support/resistance range till noon
3. At support zone, on 3rd test (1-3 min chart), price broke below - MANIPULATION
4. Price then reversed and hit first resistance - DISTRIBUTION
5. Returned to support zone, then hit second resistance - ACCUMULATION phase confirmed

Problem: App didn't suggest CALL options at the key support zone where manipulation occurred.

This analysis will:
1. Fetch historical data (1min, 3min, 5min, 15min, 1H, 4H)
2. Fetch all scan results from today
3. Identify the AMD pattern in lower timeframes
4. Explain why the app missed the CALL opportunity
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_subheader(text):
    print("\n" + "-" * 60)
    print(f"  {text}")
    print("-" * 60)


class NiftyAMDAnalyzer:
    """Analyze AMD patterns in NIFTY using multiple timeframes"""
    
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.fyers_client = None
        self.access_token = None
        
    def connect_fyers(self) -> bool:
        """Connect to Fyers using token from Supabase"""
        print("Connecting to Supabase and fetching Fyers token...")
        
        try:
            response = self.supabase.table("fyers_tokens").select("*").order("updated_at", desc=True).limit(1).execute()
            
            if not response.data:
                print("❌ No Fyers token found in database!")
                print("   Please authenticate via TradeWise app first.")
                return False
            
            token_data = response.data[0]
            self.access_token = token_data["access_token"]
            expires_at = token_data.get("expires_at", "unknown")
            user_id = token_data.get("user_id", "unknown")[:8]
            
            print(f"✅ Found Fyers token for user {user_id}...")
            print(f"   Expires: {expires_at}")
            
            # Initialize Fyers client
            from src.api.fyers_client import FyersClient, fyers_client
            fyers_client.access_token = self.access_token
            fyers_client._initialize_client()
            self.fyers_client = fyers_client
            
            # Verify token works
            try:
                profile = self.fyers_client.get_profile()
                if profile.get("code") == 200 or profile.get("s") == "ok":
                    print(f"✅ Fyers connected: {profile.get('data', {}).get('name', 'User')}")
                    return True
                else:
                    print(f"⚠️ Token may be expired: {profile}")
                    return False
            except Exception as e:
                print(f"⚠️ Could not verify token: {e}")
                return True  # Continue anyway
                
        except Exception as e:
            print(f"❌ Error connecting to Fyers: {e}")
            return False
    
    def fetch_historical_data(self, resolution: str, days: int = 5) -> pd.DataFrame:
        """Fetch historical data for NIFTY at given resolution"""
        symbol = "NSE:NIFTY50-INDEX"
        date_to = datetime.now()
        date_from = date_to - timedelta(days=days)
        
        print(f"   Fetching {resolution} data ({days} days)...")
        
        try:
            df = self.fyers_client.get_historical_data(
                symbol=symbol,
                resolution=resolution,
                date_from=date_from,
                date_to=date_to
            )
            
            if df is not None and not df.empty:
                print(f"   ✅ Got {len(df)} candles")
                return df
            else:
                print(f"   ⚠️ No data returned")
                return pd.DataFrame()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return pd.DataFrame()
    
    def fetch_todays_scans(self) -> list:
        """Fetch all option scanner results from today"""
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        print(f"Fetching scans from {today_start.strftime('%Y-%m-%d')}...")
        
        try:
            response = self.supabase.table("option_scanner_results").select("*").gte("created_at", today_start.isoformat()).eq("index", "NIFTY").order("created_at", desc=False).execute()
            
            scans = response.data or []
            print(f"✅ Found {len(scans)} NIFTY scans today")
            return scans
        except Exception as e:
            print(f"❌ Error fetching scans: {e}")
            return []
    
    def identify_support_resistance_zones(self, df: pd.DataFrame, lookback: int = 20) -> dict:
        """Identify key support and resistance zones from the data"""
        if df.empty:
            return {"support": [], "resistance": []}
        
        # Find swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(lookback, len(df) - lookback):
            # Swing High
            if df['high'].iloc[i] == df['high'].iloc[i-lookback:i+lookback+1].max():
                swing_highs.append({
                    'price': df['high'].iloc[i],
                    'time': df.index[i]
                })
            
            # Swing Low  
            if df['low'].iloc[i] == df['low'].iloc[i-lookback:i+lookback+1].min():
                swing_lows.append({
                    'price': df['low'].iloc[i],
                    'time': df.index[i]
                })
        
        return {
            "support": swing_lows[-5:] if swing_lows else [],
            "resistance": swing_highs[-5:] if swing_highs else []
        }
    
    def detect_manipulation_events(self, df_ltf: pd.DataFrame, support_levels: list, resistance_levels: list) -> list:
        """
        Detect manipulation events - when price breaks a level and quickly reverses
        
        AMD Pattern:
        - Accumulation: Smart money accumulates positions
        - Manipulation: False breakout to trap retail traders
        - Distribution: Smart money distributes at better prices
        """
        manipulations = []
        
        if df_ltf.empty or not support_levels:
            return manipulations
        
        # Get support levels as prices
        support_prices = [s['price'] for s in support_levels]
        
        for i in range(3, len(df_ltf) - 1):
            current_low = df_ltf['low'].iloc[i]
            prev_closes = df_ltf['close'].iloc[i-3:i]
            next_closes = df_ltf['close'].iloc[i:i+2] if i+2 <= len(df_ltf) else df_ltf['close'].iloc[i:]
            
            # Check for support break and reversal (manipulation)
            for support in support_prices:
                # Price broke below support
                if current_low < support * 0.998:  # 0.2% break
                    # But previous candles were above
                    if all(c >= support * 0.998 for c in prev_closes):
                        # And next candles are back above
                        if len(next_closes) > 0 and all(c >= support * 0.998 for c in next_closes):
                            manipulations.append({
                                'type': 'BEAR_TRAP',
                                'time': df_ltf.index[i],
                                'level': support,
                                'low_hit': current_low,
                                'recovery': float(next_closes.iloc[-1]) if len(next_closes) > 0 else None,
                                'signal': 'BUY CALL - False breakdown reversal'
                            })
        
        return manipulations
    
    def analyze_scan_accuracy(self, scans: list, manipulations: list) -> dict:
        """Analyze if scans detected the manipulation events"""
        analysis = {
            'total_scans': len(scans),
            'pe_recommendations': 0,
            'ce_recommendations': 0,
            'wait_recommendations': 0,
            'manipulation_detected': False,
            'missed_opportunities': []
        }
        
        for scan in scans:
            action = scan.get('action', 'WAIT')
            option_type = scan.get('option_type', '')
            scan_time = scan.get('created_at', '')
            
            if option_type == 'PE' or 'PUT' in action:
                analysis['pe_recommendations'] += 1
            elif option_type == 'CE' or 'CALL' in action:
                analysis['ce_recommendations'] += 1
            else:
                analysis['wait_recommendations'] += 1
        
        # Check if any manipulation event could have been captured
        for manip in manipulations:
            was_detected = False
            for scan in scans:
                scan_time = datetime.fromisoformat(scan.get('created_at', '').replace('Z', '+00:00'))
                manip_time = manip['time']
                
                # Check if scan was within 30 minutes of manipulation
                if isinstance(manip_time, pd.Timestamp):
                    manip_time = manip_time.to_pydatetime()
                
                # Make both timezone-aware for comparison
                if scan_time.tzinfo is None:
                    scan_time = scan_time.replace(tzinfo=timezone.utc)
                if manip_time.tzinfo is None:
                    manip_time = manip_time.replace(tzinfo=timezone.utc)
                
                time_diff = abs((scan_time - manip_time).total_seconds())
                
                if time_diff < 1800:  # 30 minutes
                    if scan.get('option_type') == 'CE' or 'CALL' in scan.get('action', ''):
                        was_detected = True
                        analysis['manipulation_detected'] = True
            
            if not was_detected:
                analysis['missed_opportunities'].append({
                    'time': str(manip['time']),
                    'type': manip['type'],
                    'suggested_action': manip['signal'],
                    'level': manip['level']
                })
        
        return analysis
    
    def run_analysis(self):
        """Run the complete AMD pattern analysis"""
        print_header("NIFTY AMD PATTERN ANALYSIS")
        print(f"⏰ Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        
        # Step 1: Connect to Fyers
        print_subheader("Step 1: Connecting to Fyers")
        if not self.connect_fyers():
            print("❌ Cannot proceed without Fyers connection")
            return
        
        # Step 2: Fetch historical data for multiple timeframes
        print_subheader("Step 2: Fetching Multi-Timeframe Historical Data")
        
        data = {}
        
        # Fetch data for each timeframe
        timeframes = {
            '1': ('1 Minute', 1),
            '3': ('3 Minute', 2),
            '5': ('5 Minute', 3),
            '15': ('15 Minute', 5),
            '60': ('1 Hour', 10),
            '240': ('4 Hour', 30),
            'D': ('Daily', 60)
        }
        
        for resolution, (name, days) in timeframes.items():
            data[resolution] = self.fetch_historical_data(resolution, days)
        
        # Step 3: Fetch today's scan results
        print_subheader("Step 3: Fetching Today's Scan Results")
        scans = self.fetch_todays_scans()
        
        if scans:
            print("\n📊 Scan Summary:")
            for i, scan in enumerate(scans, 1):
                scan_time = scan.get('created_at', 'N/A')[:19]
                action = scan.get('action', 'N/A')
                signal = scan.get('signal', 'N/A')
                confidence = scan.get('confidence', 0)
                option_type = scan.get('option_type', 'N/A')
                strike = scan.get('strike', 0)
                spot = scan.get('spot_price', 0)
                
                print(f"\n   Scan #{i} @ {scan_time}")
                print(f"   Signal: {signal}")
                print(f"   Action: {action} | Option: {option_type} {strike}")
                print(f"   Confidence: {confidence}% | Spot: {spot}")
        
        # Step 4: Identify support/resistance from 4H and 1H data
        print_subheader("Step 4: Identifying Support/Resistance Zones")
        
        zones_4h = self.identify_support_resistance_zones(data.get('240', pd.DataFrame()), lookback=3)
        zones_1h = self.identify_support_resistance_zones(data.get('60', pd.DataFrame()), lookback=5)
        
        if zones_4h['support']:
            print("\n📉 4H Support Zones:")
            for s in zones_4h['support']:
                print(f"   {s['price']:.2f} @ {s['time']}")
        
        if zones_4h['resistance']:
            print("\n📈 4H Resistance Zones:")
            for r in zones_4h['resistance']:
                print(f"   {r['price']:.2f} @ {r['time']}")
        
        # Step 5: Detect manipulation events in lower timeframes
        print_subheader("Step 5: Detecting AMD (Manipulation) Events in LTF")
        
        all_manipulations = []
        
        for resolution in ['1', '3', '5']:
            df = data.get(resolution, pd.DataFrame())
            if not df.empty:
                manips = self.detect_manipulation_events(
                    df, 
                    zones_4h['support'] + zones_1h.get('support', []),
                    zones_4h['resistance'] + zones_1h.get('resistance', [])
                )
                all_manipulations.extend(manips)
        
        if all_manipulations:
            print(f"\n🎯 Found {len(all_manipulations)} Manipulation Events:")
            for m in all_manipulations:
                print(f"\n   Type: {m['type']}")
                print(f"   Time: {m['time']}")
                print(f"   Level: {m['level']:.2f}")
                print(f"   Low Hit: {m['low_hit']:.2f}")
                print(f"   Signal: {m['signal']}")
        else:
            print("\n⚠️ No clear manipulation events detected in the data")
            print("   This could be because:")
            print("   - Market moved within normal range")
            print("   - Support/resistance zones weren't cleanly broken")
            print("   - Data timing doesn't capture the exact event")
        
        # Step 6: Analyze scan accuracy
        print_subheader("Step 6: Analyzing Scan Accuracy vs AMD Events")
        
        accuracy = self.analyze_scan_accuracy(scans, all_manipulations)
        
        print(f"\n📊 Scan Statistics:")
        print(f"   Total Scans: {accuracy['total_scans']}")
        print(f"   PE Recommendations: {accuracy['pe_recommendations']}")
        print(f"   CE Recommendations: {accuracy['ce_recommendations']}")
        print(f"   Wait Recommendations: {accuracy['wait_recommendations']}")
        print(f"   Manipulation Detected: {'✅ Yes' if accuracy['manipulation_detected'] else '❌ No'}")
        
        if accuracy['missed_opportunities']:
            print(f"\n⚠️ Missed Opportunities ({len(accuracy['missed_opportunities'])}):")
            for opp in accuracy['missed_opportunities']:
                print(f"\n   Time: {opp['time']}")
                print(f"   Type: {opp['type']}")
                print(f"   Level: {opp['level']:.2f}")
                print(f"   Suggested: {opp['suggested_action']}")
        
        # Step 7: Root cause analysis
        print_subheader("Step 7: Root Cause Analysis - Why App Missed the AMD Pattern")
        
        self.explain_limitations()
        
        # Step 8: Market data summary
        print_subheader("Step 8: Today's NIFTY Price Action Summary")
        self.print_price_summary(data)
        
        print_header("ANALYSIS COMPLETE")
    
    def explain_limitations(self):
        """Explain why the app missed the AMD pattern"""
        print("""
🔍 WHY THE APP MISSED THE MANIPULATION PATTERN:

1. TIMEFRAME LIMITATION:
   - App analyzes: Monthly → Weekly → Daily → 4H → 1H → 15min
   - Missing: 1-minute and 3-minute timeframe analysis
   - AMD patterns in 1-3 min charts are NOT detected

2. ICT STRUCTURE FOCUS:
   - App looks for Higher Timeframe (HTF) bias first
   - LTF entries require HTF confirmation
   - Quick 1-3 min manipulations don't align with 15min+ structure

3. FVG TEST COUNT LOGIC:
   - App tracks FVG tests (1st test, 2nd test)
   - 3rd test at support that breaks = treated as BREAKDOWN not MANIPULATION
   - No reversal pattern recognition on 3rd/4th tests

4. NO REAL-TIME PRICE ACTION:
   - Scans are point-in-time snapshots
   - Can't detect quick fake breakouts and reversals
   - Manipulation happens in seconds/minutes

5. MISSING VOLUME ANALYSIS IN LTF:
   - Smart money manipulation often shows abnormal volume
   - App doesn't analyze 1-3 min volume spikes at key levels

🎯 WHAT SHOULD HAPPEN:

When price tests a key support zone for the 3rd time in LTF:
- If break is with LOW volume → likely manipulation → BUY CALL
- If price immediately recovers above support → confirm reversal
- Quick reversal to resistance = CALL opportunity

📈 RECOMMENDED IMPROVEMENTS:

1. Add 1-min and 3-min timeframe analysis for LTF entries
2. Implement "False Breakout" detection algorithm:
   - Track number of tests at key levels
   - Detect quick breaks followed by recovery
   - Flag these as potential reversals

3. Add Volume Profile Analysis:
   - Compare volume on break vs normal
   - Low volume breaks = likely manipulation

4. Implement Real-Time Alert System:
   - Monitor key zones continuously
   - Alert when manipulation pattern forms

5. Add "Smart Money Concept" patterns:
   - Accumulation phase detection
   - Manipulation (stop hunt) detection  
   - Distribution phase detection
""")
    
    def print_price_summary(self, data: dict):
        """Print today's price action summary"""
        # Get current quote
        try:
            quote = self.fyers_client.get_quotes(["NSE:NIFTY50-INDEX"])
            if quote and quote.get("d"):
                v = quote["d"][0]["v"]
                print(f"\n📊 Current NIFTY Snapshot:")
                print(f"   LTP: ₹{v.get('lp', 0):,.2f}")
                print(f"   Open: ₹{v.get('open_price', 0):,.2f}")
                print(f"   High: ₹{v.get('high_price', 0):,.2f}")
                print(f"   Low: ₹{v.get('low_price', 0):,.2f}")
                print(f"   Prev Close: ₹{v.get('prev_close_price', 0):,.2f}")
                
                change = v.get('lp', 0) - v.get('prev_close_price', 0)
                change_pct = (change / v.get('prev_close_price', 1)) * 100
                print(f"   Change: {change:+.2f} ({change_pct:+.2f}%)")
                
                # Calculate range
                day_range = v.get('high_price', 0) - v.get('low_price', 0)
                print(f"   Day Range: {day_range:.2f} points")
        except Exception as e:
            print(f"   ⚠️ Could not fetch current price: {e}")
        
        # Show 1-min data stats for today
        df_1m = data.get('1', pd.DataFrame())
        if not df_1m.empty:
            # Filter to today only
            today = datetime.now().date()
            df_today = df_1m[df_1m.index.date == today] if hasattr(df_1m.index, 'date') else df_1m
            
            if not df_today.empty:
                print(f"\n📈 Today's 1-Minute Analysis:")
                print(f"   Total 1-min candles: {len(df_today)}")
                print(f"   High of Day: ₹{df_today['high'].max():,.2f}")
                print(f"   Low of Day: ₹{df_today['low'].min():,.2f}")
                
                # Find largest 1-min moves
                df_today['range'] = df_today['high'] - df_today['low']
                largest_moves = df_today.nlargest(5, 'range')
                
                print(f"\n   Top 5 Volatility Candles (1-min):")
                for idx, row in largest_moves.iterrows():
                    print(f"   {idx}: Range={row['range']:.2f} pts, H={row['high']:.2f}, L={row['low']:.2f}")


def main():
    analyzer = NiftyAMDAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
