#!/usr/bin/env python3
"""
Historical Backtesting Framework for Signal Generation

Tests both OLD and NEW signal flows against historical NIFTY data
to compare signal quality, accuracy, and profitability.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Import authentication
from src.services.auth_service import auth_service
from src.models.auth_models import UserLogin
from src.api.fyers_client import FyersClient

# Import signal generation
from main import _generate_actionable_signal, _generate_actionable_signal_topdown

EMAIL = "bineshch@gmail.com"
PASSWORD = "Tra@2026"


class HistoricalBacktester:
    """Backtest signal generation on historical data"""
    
    def __init__(self, fyers_client):
        self.fyers = fyers_client
        self.results = []
    
    def fetch_historical_scenario(self, date: datetime, symbol="NSE:NIFTY50-INDEX") -> Dict:
        """
        Fetch historical data for a specific date
        
        Returns complete market snapshot as it was on that date
        """
        print(f"\n📅 Fetching data for {date.strftime('%Y-%m-%d')}...")
        
        # Define lookback periods for each timeframe (MAXIMUM DATA)
        # Fyers limits: Daily=366 days  Intraday=100 days
        timeframes = {
            'M': (366, 'M'),      # Monthly - 366 days max
            'W': (366, 'W'),      # Weekly - 366 days max
            'D': (366, 'D'),      # Daily - 366 days max (1 year)
            '240': (100, '240'),  # 4H - 100 days max
            '60': (100, '60'),    # 1H - 100 days max
            '15': (100, '15'),    # 15m - 100 days max
            '5': (100, '5'),      # 5m - 100 days max
            '3': (100, '3')       # 3m - 100 days max
        }
        
        historical_data = {}
        
        for tf_key, (days_back, resolution) in timeframes.items():
            start_date = date - timedelta(days=days_back)
            
            try:
                df = self.fyers.get_historical_data(
                    symbol=symbol,
                    resolution=resolution,
                    date_from=start_date,
                    date_to=date
                )
                
                if df is not None and len(df) > 0:
                    # Only include data UP TO the target date
                    df = df[df.index <= date]
                    historical_data[tf_key] = df
                    print(f"   ✅ {tf_key}: {len(df)} candles")
                else:
                    print(f"   ⚠️ {tf_key}: No data")
                    
            except Exception as e:
                print(f"   ❌ {tf_key}: Error - {e}")
        
        # Get spot price on that date (last close of daily data)
        spot_price = None
        if 'D' in historical_data and len(historical_data['D']) > 0:
            spot_price = historical_data['D'].iloc[-1]['close']
        
        return {
            'date': date,
            'spot_price': spot_price,
            'historical_data': historical_data
        }
    
    def create_mock_objects(self, scenario: Dict):
        """Create mock MTF result and session info for signal generation"""
        
        class MockMTFResult:
            def __init__(self, price, analyses):
                self.current_price = price
                self.overall_bias = 'neutral'
                self.analyses = analyses
        
        class MockAnalysis:
            def __init__(self, candles):
                self.candles = candles
                self.fair_value_gaps = []
                self.trend = 'neutral'
        
        class MockSessionInfo:
            current_session = "market_hours"
        
        mtf_analyses = {
            tf: MockAnalysis(df) 
            for tf, df in scenario['historical_data'].items()
        }
        
        mtf_result = MockMTFResult(scenario['spot_price'], mtf_analyses)
        session_info = MockSessionInfo()
        
        # Mock chain data (simplified)
        atm_strike = round(scenario['spot_price'] / 50) * 50
        chain_data = {
            'atm_strike': atm_strike,
            'atm_iv': 15.0,
            'days_to_expiry': 5,
            'expiry_date': (scenario['date'] + timedelta(days=5)).strftime("%Y-%m-%d"),
            'strikes': [],
            'futures_data': {
                'basis_pct': 0.25,  # Assume small premium
                'sentiment': 'neutral'
            }
        }
        
        # Historical prices for ML
        historical_prices = (
            scenario['historical_data']['D']['close'] 
            if 'D' in scenario['historical_data'] 
            else None
        )
        
        return mtf_result, session_info, chain_data, historical_prices
    
    def evaluate_signal_outcome(self, signal: Dict, actual_move: float) -> Dict:
        """
        Evaluate how the signal performed
        
        Args:
            signal: Generated signal
            actual_move: Actual NIFTY movement in points over next N days
        """
        predicted_direction = 'bullish' if 'CALL' in signal['action'] or 'BULL' in signal.get('signal', '') else 'bearish'
        actual_direction = 'bullish' if actual_move > 0 else 'bearish'
        
        direction_correct = (predicted_direction == actual_direction)
        
        # Simple P&L estimation (very rough)
        # Assumes entry at recommended price, exit at target or SL
        entry_price = signal['entry'].get('price', 0)
        target_1 = signal['targets'].get('target_1', entry_price * 1.5)
        stop_loss = signal['targets'].get('stop_loss', entry_price * 0.7)
        
        confidence = signal['confidence'].get('score', 50)
        
        # Rough P&L (if direction correct, assume 50% of target 1 hit)
        if direction_correct:
            pnl_pct = ((target_1 - entry_price) / entry_price) * 0.5  # 50% of target
        else:
            pnl_pct = ((stop_loss - entry_price) / entry_price)  # Hit stop loss
        
        return {
            'direction_correct': direction_correct,
            'predicted_direction': predicted_direction,
            'actual_direction': actual_direction,
            'actual_move': actual_move,
            'confidence': confidence,
            'entry_price': entry_price,
            'estimated_pnl_pct': pnl_pct * 100,
            'signal_quality': 'Good' if (direction_correct and confidence > 50) else 'Poor'
        }
    
    def backtest_scenario(self, date: datetime, forward_days: int = 3) -> Dict:
        """
        Backtest both OLD and NEW flows on a historical date
        
        Args:
            date: Historical date to test
            forward_days: Days to look forward for actual outcome
        """
        print("\n" + "=" * 80)
        print(f"🔙 BACKTESTING: {date.strftime('%Y-%m-%d')}")
        print("=" * 80)
        
        # Fetch historical scenario
        scenario = self.fetch_historical_scenario(date)
        
        if not scenario['spot_price']:
            print("❌ No spot price available for this date")
            return None
        
        print(f"\n📊 Spot Price: ₹{scenario['spot_price']}")
        
        # Create mock objects
        mtf_result, session_info, chain_data, historical_prices = self.create_mock_objects(scenario)
        
        # Generate signals with BOTH flows
        results = {
            'date': date.isoformat(),
            'spot_price': scenario['spot_price']
        }
        
        # Test OLD flow
        print("\n🔄 Testing OLD Flow...")
        try:
            old_signal = _generate_actionable_signal(
                mtf_result=mtf_result,
                session_info=session_info,
                chain_data=chain_data,
                historical_prices=historical_prices,
                probability_analysis=None
            )
            
            results['old_signal'] = {
                'signal': old_signal.get('signal'),
                'action': old_signal.get('action'),
                'strike': old_signal['option'].get('strike'),
                'confidence': old_signal['confidence'].get('score'),
                'generated': True
            }
            print(f"   ✅ Signal: {old_signal.get('action')} {old_signal['option'].get('strike')}")
            print(f"   ✅ Confidence: {old_signal['confidence'].get('score')}/100")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results['old_signal'] = {'generated': False, 'error': str(e)}
        
        # Test NEW flow
        print("\n🆕 Testing NEW Flow...")
        try:
            new_signal = _generate_actionable_signal_topdown(
                mtf_result=mtf_result,
                session_info=session_info,
                chain_data=chain_data,
                historical_prices=historical_prices,
                probability_analysis=None,
                use_new_flow=True
            )
            
            results['new_signal'] = {
                'signal': new_signal.get('signal'),
                'action': new_signal.get('action'),
                'strike': new_signal['option'].get('strike'),
                'confidence': new_signal['confidence'].get('score'),
                'htf_direction': new_signal.get('htf_analysis', {}).get('direction'),
                'htf_strength': new_signal.get('htf_analysis', {}).get('strength'),
                'ltf_found': new_signal.get('ltf_entry_model', {}).get('found'),
                'ml_agrees': new_signal.get('confirmation_stack', {}).get('ml_prediction', {}).get('agrees_with_htf'),
                'generated': True
            }
            print(f"   ✅ Signal: {new_signal.get('action')} {new_signal['option'].get('strike')}")
            print(f"   ✅ Confidence: {new_signal['confidence'].get('score')}/100")
            print(f"   ✅ HTF Direction: {new_signal.get('htf_analysis', {}).get('direction')}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results['new_signal'] = {'generated': False, 'error': str(e)}
        
        # Get actual outcome
        print(f"\n📈 Getting actual outcome ({forward_days} days forward)...")
        outcome_date = date + timedelta(days=forward_days)
        
        try:
            # Fetch spot price N days later
            future_data = self.fyers.get_historical_data(
                symbol="NSE:NIFTY50-INDEX",
                resolution="D",
                date_from=date,
                date_to=outcome_date
            )
            
            if future_data is not None and len(future_data) >= 2:
                start_price = future_data.iloc[0]['close']
                end_price = future_data.iloc[-1]['close']
                actual_move = end_price - start_price
                
                results['actual_outcome'] = {
                    'start_price': start_price,
                    'end_price': end_price,
                    'move_points': actual_move,
                    'move_pct': (actual_move / start_price) * 100,
                    'direction': 'bullish' if actual_move > 0 else 'bearish'
                }
                
                print(f"   ✅ Actual Move: {actual_move:+.2f} points ({results['actual_outcome']['move_pct']:+.2f}%)")
                print(f"   ✅ Direction: {results['actual_outcome']['direction'].upper()}")
                
                # Evaluate both signals
                if results.get('old_signal', {}).get('generated'):
                    results['old_signal']['evaluation'] = self.evaluate_signal_outcome(
                        old_signal, actual_move
                    )
                
                if results.get('new_signal', {}).get('generated'):
                    results['new_signal']['evaluation'] = self.evaluate_signal_outcome(
                        new_signal, actual_move
                    )
                
            else:
                print("   ⚠️ Could not get future data")
                results['actual_outcome'] = None
                
        except Exception as e:
            print(f"   ❌ Error getting outcome: {e}")
            results['actual_outcome'] = None
        
        self.results.append(results)
        return results
    
    def generate_backtest_report(self) -> str:
        """Generate comprehensive backtest report"""
        
        if not self.results:
            return "No backtest results available"
        
        report = []
        report.append("\n" + "=" * 80)
        report.append("📊 BACKTEST REPORT")
        report.append("=" * 80)
        
        total_tests = len(self.results)
        old_success = sum(1 for r in self.results if r.get('old_signal', {}).get('generated'))
        new_success = sum(1 for r in self.results if r.get('new_signal', {}).get('generated'))
        
        report.append(f"\nTotal Scenarios Tested: {total_tests}")
        report.append(f"OLD Flow Success Rate: {old_success}/{total_tests} ({old_success/total_tests*100:.1f}%)")
        report.append(f"NEW Flow Success Rate: {new_success}/{total_tests} ({new_success/total_tests*100:.1f}%)")
        
        # Accuracy comparison
        old_correct = sum(
            1 for r in self.results 
            if r.get('old_signal', {}).get('evaluation', {}).get('direction_correct')
        )
        new_correct = sum(
            1 for r in self.results 
            if r.get('new_signal', {}).get('evaluation', {}).get('direction_correct')
        )
        
        report.append(f"\n🎯 Direction Accuracy:")
        report.append(f"   OLD Flow: {old_correct}/{old_success} correct ({old_correct/old_success*100 if old_success > 0 else 0:.1f}%)")
        report.append(f"   NEW Flow: {new_correct}/{new_success} correct ({new_correct/new_success*100 if new_success > 0 else 0:.1f}%)")
        
        # Average confidence
        old_conf = [
            r.get('old_signal', {}).get('confidence', 0)
            for r in self.results
            if r.get('old_signal', {}).get('generated')
        ]
        new_conf = [
            r.get('new_signal', {}).get('confidence', 0)
            for r in self.results
            if r.get('new_signal', {}).get('generated')
        ]
        
        if old_conf:
            report.append(f"\n📊 Average Confidence:")
            report.append(f"   OLD Flow: {np.mean(old_conf):.1f}/100")
        if new_conf:
            report.append(f"   NEW Flow: {np.mean(new_conf):.1f}/100")
        
        # Detailed results
        report.append("\n" + "=" * 80)
        report.append("📋 DETAILED RESULTS")
        report.append("=" * 80)
        
        for i, result in enumerate(self.results, 1):
            report.append(f"\nScenario {i}: {result['date']}")
            report.append(f"Spot: ₹{result['spot_price']}")
            
            if result.get('actual_outcome'):
                outcome = result['actual_outcome']
                report.append(f"Actual: {outcome['move_points']:+.2f} pts ({outcome['direction'].upper()})")
            
            # OLD flow
            if result.get('old_signal', {}).get('generated'):
                old = result['old_signal']
                report.append(f"\n   OLD: {old['action']} {old['strike']} (Conf: {old['confidence']}/100)")
                if old.get('evaluation'):
                    ev = old['evaluation']
                    report.append(f"        → {'✅ CORRECT' if ev['direction_correct'] else '❌ WRONG'}")
                    report.append(f"        → Est. P&L: {ev['estimated_pnl_pct']:+.1f}%")
            
            # NEW flow
            if result.get('new_signal', {}).get('generated'):
                new = result['new_signal']
                report.append(f"\n   NEW: {new['action']} {new['strike']} (Conf: {new['confidence']}/100)")
                report.append(f"        HTF: {new.get('htf_direction', 'N/A')} ({new.get('htf_strength', 0):.1f})")
                report.append(f"        LTF: {'✅ Found' if new.get('ltf_found') else '❌ Not found'}")
                report.append(f"        ML: {'✅ Agrees' if new.get('ml_agrees') else '⚠️ Conflicts'}")
                if new.get('evaluation'):
                    ev = new['evaluation']
                    report.append(f"        → {'✅ CORRECT' if ev['direction_correct'] else '❌ WRONG'}")
                    report.append(f"        → Est. P&L: {ev['estimated_pnl_pct']:+.1f}%")
        
        return "\n".join(report)


async def main():
    """Run historical backtests"""
    
    print("=" * 80)
    print("🔙 HISTORICAL BACKTESTING - Signal Generation")
    print("=" * 80)
    
    # Step 1: Authenticate
    print("\n🔐 Authenticating...")
    try:
        login_data = UserLogin(email=EMAIL, password=PASSWORD)
        result = await auth_service.login_user(login_data)
        
        if not result or not result.access_token:
            print("❌ Login failed")
            return
        
        user = result.user
        print(f"✅ Logged in as: {user.email}")
        
        # Get Fyers token
        fyers_token = await auth_service.get_fyers_token(user.id)
        if not fyers_token or not fyers_token.access_token:
            print("❌ No Fyers token found!")
            return
        
        print(f"✅ Fyers token active")
        
        # Create Fyers client
        fyers_client = FyersClient()
        fyers_client.access_token = fyers_token.access_token
        fyers_client._initialize_client()
        
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Step 2: Define historical scenarios to test
    scenarios = [
        # Recent bearish move
        datetime(2026, 1, 20),  # Monday
        datetime(2026, 1, 22),  # Wednesday
        datetime(2026, 1, 24),  # Friday
        
        # Add more historical dates as needed
        # datetime(2025, 12, 15),  # Example: different market condition
    ]
    
    print(f"\n📅 Testing {len(scenarios)} historical scenarios...")
    
    # Step 3: Run backtests
    backtester = HistoricalBacktester(fyers_client)
    
    for scenario_date in scenarios:
        backtester.backtest_scenario(scenario_date, forward_days=3)
    
    # Step 4: Generate report
    report = backtester.generate_backtest_report()
    print(report)
    
    # Step 5: Save results
    output_file = 'backtest_results.json'
    with open(output_file, 'w') as f:
        json.dump(backtester.results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    print("\n✅ Backtesting Complete!")


if __name__ == "__main__":
    asyncio.run(main())
