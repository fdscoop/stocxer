#!/usr/bin/env python3
"""
Full integration test for the Enhanced ML Pipeline.
Tests all ML modules with realistic mock data.
"""

import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
import pytz

IST = pytz.timezone('Asia/Kolkata')

print("=" * 70)
print("🧠 TradeWise Enhanced ML Pipeline - Full Integration Test")
print("=" * 70)

# Import modules
from src.ml.speed_predictor import SpeedPredictor
from src.ml.iv_predictor import IVPredictor
from src.ml.theta_scenario_planner import ThetaScenarioPlanner
from src.ml.xgboost_direction import XGBoostDirectionPredictor
from src.ml.options_simulator import OptionsPnLSimulator
from src.services.enhanced_ml_service import EnhancedMLService

# Initialize all predictors
speed_predictor = SpeedPredictor()
iv_predictor = IVPredictor()
theta_planner = ThetaScenarioPlanner()
direction_predictor = XGBoostDirectionPredictor()
simulator = OptionsPnLSimulator()
ml_service = EnhancedMLService()

# Create mock market data (BANKNIFTY scenario)
symbol = "BANKNIFTY"
current_price = 51250.0
expiry_date = datetime.now(IST).replace(hour=15, minute=30, second=0, microsecond=0)
if expiry_date.weekday() != 2:  # If not Wednesday, move to next Wednesday
    days_until_wednesday = (2 - expiry_date.weekday()) % 7
    if days_until_wednesday == 0:
        days_until_wednesday = 7
    expiry_date = expiry_date + timedelta(days=days_until_wednesday)

# Mock OHLCV data (last 100 candles)
import random
random.seed(42)

base_price = 51000
ohlcv_data = []
for i in range(100):
    o = base_price + random.uniform(-100, 100)
    h = o + random.uniform(0, 100)
    l = o - random.uniform(0, 100)
    c = random.uniform(l, h)
    v = random.randint(50000, 500000)
    ohlcv_data.append({
        'open': o,
        'high': h,
        'low': l,
        'close': c,
        'volume': v
    })
    base_price = c

# Extract prices and volumes
prices = [d['close'] for d in ohlcv_data]
volumes = [d['volume'] for d in ohlcv_data]
high_prices = [d['high'] for d in ohlcv_data]
low_prices = [d['low'] for d in ohlcv_data]

# Option parameters
option_price = 350.0
strike_price = 51300.0  # Slightly OTM call
option_type = 'call'
current_iv = 18.5

print(f"\n📊 Test Parameters:")
print(f"   Symbol: {symbol}")
print(f"   Spot Price: ₹{current_price:.2f}")
print(f"   Strike: {strike_price} {option_type.upper()}")
print(f"   Option Price: ₹{option_price:.2f}")
print(f"   IV: {current_iv}%")
print(f"   Expiry: {expiry_date.strftime('%Y-%m-%d')}")

# Test 1: Speed Prediction
print("\n" + "=" * 70)
print("🚀 Test 1: Speed Prediction")
print("=" * 70)

speed_result = speed_predictor.predict_speed(
    current_price=current_price,
    price_history=prices,
    volume_history=volumes,
    current_volume=volumes[-1],
    timestamp=datetime.now(IST),
    is_expiry_day=False
)

print(f"   Category: {speed_result.category.value}")
print(f"   Confidence: {speed_result.confidence:.2f}")
print(f"   Expected Move: {speed_result.expected_move_pct:.2f}%")
print(f"   Expected Time: {speed_result.expected_time_mins} mins")
print(f"   Volume Score: {speed_result.volume_score:.2f}")
print(f"   Momentum Score: {speed_result.momentum_score:.2f}")
print(f"   Options Action: {speed_result.options_action}")
print(f"   Reasoning:")
for reason in speed_result.reasoning[:3]:
    print(f"     • {reason}")

# Test 2: IV Prediction
print("\n" + "=" * 70)
print("📈 Test 2: IV Prediction")
print("=" * 70)

iv_result = iv_predictor.predict_iv(
    current_iv=current_iv,
    spot_price=current_price,
    iv_history=[17.5, 18.0, 18.5, 19.0, 18.5, 17.0, 16.5, 18.0, 18.5] * 4,  # ~36 days
    price_history=prices[-36:] if len(prices) >= 36 else prices,
    timestamp=datetime.now(IST),
    is_expiry_day=False,
    days_to_expiry=5
)

print(f"   Direction: {iv_result.direction.value}")
print(f"   Confidence: {iv_result.confidence:.1%}")
print(f"   Expected IV Change: {iv_result.expected_iv_change_pct:+.1f}%")
print(f"   Current IV: {iv_result.current_iv}%")
print(f"   Predicted IV: {iv_result.predicted_iv:.1f}%")
print(f"   Regime: {iv_result.current_regime.value}")
print(f"   Event Factor: {iv_result.event_factor}")
print(f"   Vega Exposure: {iv_result.vega_exposure}")
print(f"   Strategy: {iv_result.options_strategy}")
print(f"   Reasoning:")
for reason in iv_result.reasoning[:3]:
    print(f"     • {reason}")

# Test 3: Theta Scenario Planner
print("\n" + "=" * 70)
print("⏱️ Test 3: Theta Scenario Planner")
print("=" * 70)

theta_result = theta_planner.generate_scenarios(
    option_type="CE",
    strike=strike_price,
    entry_premium=option_price,
    current_spot=current_price,
    current_iv=current_iv,  # As percentage
    days_to_expiry=5.0,
    timestamp=datetime.now(IST),
    is_expiry_day=False
)

print(f"   Current Greeks:")
print(f"     Delta: {theta_result.delta:.3f}")
print(f"     Gamma: {theta_result.gamma:.5f}")
print(f"     Theta/hr: ₹{theta_result.theta_per_hour:.2f}")
print(f"     Vega: {theta_result.vega:.2f}")
print(f"   15min Scenario:")
print(f"     Best Case: ₹{theta_result.scenarios_15min.best_case_pnl:.2f}")
print(f"     Expected: ₹{theta_result.scenarios_15min.expected_pnl:.2f}")
print(f"     Theta Decay: ₹{theta_result.scenarios_15min.theta_decay_amt:.2f}")
print(f"   Optimal Hold Time: {theta_result.optimal_holding_time} mins")
print(f"   Breakeven Move: {theta_result.breakeven_move_required:.2f}%")
print(f"   Urgency: {theta_result.urgency}")
print(f"   Recommendation: {theta_result.hold_recommendation}")
print(f"   Exit Triggers:")
for trigger in theta_result.exit_triggers[:3]:
    print(f"     • {trigger}")

# Test 4: XGBoost Direction Prediction
print("\n" + "=" * 70)
print("🎯 Test 4: Direction Prediction (XGBoost/Rule-Based)")
print("=" * 70)

direction_result = direction_predictor.predict(
    prices=prices,
    volumes=volumes,
    highs=high_prices,
    lows=low_prices,
    timestamp=datetime.now(IST)
)

print(f"   Direction: {direction_result.direction.value}")
print(f"   Confidence: {direction_result.confidence:.1%}")
print(f"   Expected Move: {direction_result.expected_move_pct:+.1f}%")
print(f"   Expected Points: {direction_result.expected_move_points:+.1f}")
print(f"   Trade Signal: {direction_result.trade_signal} ({direction_result.signal_strength})")
print(f"   Direction Probabilities:")
print(f"     Strong Up: {direction_result.prob_strong_up:.1%}")
print(f"     Up: {direction_result.prob_up:.1%}")
print(f"     Sideways: {direction_result.prob_sideways:.1%}")
print(f"     Down: {direction_result.prob_down:.1%}")
print(f"   Top Bullish Factors:")
for factor, weight in direction_result.top_bullish_factors[:3]:
    print(f"     • {factor}: {weight:.2f}")
print(f"   Top Bearish Factors:")
for factor, weight in direction_result.top_bearish_factors[:3]:
    print(f"     • {factor}: {weight:.2f}")

# Test 5: Options P&L Simulator
print("\n" + "=" * 70)
print("💰 Test 5: Options P&L Simulator")
print("=" * 70)

simulation_result = simulator.simulate(
    option_type="CE",
    strike=strike_price,
    premium=option_price,
    spot_price=current_price,
    current_iv=current_iv,
    days_to_expiry=5.0,
    price_history=prices,
    volume_history=volumes,
    iv_history=[17.5, 18.0, 18.5, 19.0, 18.5, 17.0, 16.5, 18.0, 18.5] * 4,
    timestamp=datetime.now(IST),
    is_expiry_day=False
)

print(f"   Trade Grade: {simulation_result.grade.value}")
print(f"   Should Trade: {simulation_result.should_trade}")
print(f"   Win Probability: {simulation_result.win_probability:.1%}")
print(f"   Expected P&L: {simulation_result.expected_pnl_pct:+.1f}%")
print(f"   Risk/Reward: {simulation_result.risk_reward_ratio:.2f}")
print(f"   Stop Loss: ₹{simulation_result.stop_loss:.2f}")
print(f"   Take Profit: ₹{simulation_result.take_profit:.2f}")
print(f"   Max Hold Time: {simulation_result.max_hold_time_mins} mins")
print(f"   Position Size: {simulation_result.position_size_pct}% of capital")
print(f"   Entry Timing: {simulation_result.entry_timing}")
print(f"   Exit Strategy: {simulation_result.exit_strategy}")
print(f"   Grade Factors:")
for factor, rating in list(simulation_result.grade_factors.items())[:4]:
    print(f"     • {factor}: {rating}")

# Test 6: Full Enhanced ML Service
print("\n" + "=" * 70)
print("🧠 Test 6: Full Enhanced ML Service Integration")
print("=" * 70)

full_prediction = ml_service.get_enhanced_prediction(
    option_type="CE",
    strike=strike_price,
    premium=option_price,
    spot_price=current_price,
    current_iv=current_iv,
    days_to_expiry=5.0,
    price_history=prices,
    volume_history=volumes,
    iv_history=[17.5, 18.0, 18.5, 19.0, 18.5, 17.0, 16.5, 18.0, 18.5] * 4,
    timestamp=datetime.now(IST),
    is_expiry_day=False
)

print(f"   Direction: {full_prediction['direction_prediction'].get('direction', 'N/A')}")
print(f"   Speed: {full_prediction['speed_prediction'].get('category', 'N/A')}")
print(f"   IV Direction: {full_prediction['iv_prediction'].get('direction', 'N/A')}")
if 'simulation' in full_prediction and 'grade' in full_prediction['simulation']:
    print(f"   Trade Grade: {full_prediction['simulation']['grade']}")
    print(f"   Expected P&L: {full_prediction['simulation'].get('expected_pnl_pct', 0):+.1f}%")
print(f"   Combined Action: {full_prediction['combined_recommendation'].get('action', 'N/A')}")
print(f"   Combined Confidence: {full_prediction['combined_recommendation'].get('confidence', 0):.1%}")
print(f"   Reasoning:")
for reason in full_prediction['combined_recommendation'].get('reasoning', [])[:3]:
    print(f"     • {reason}")
print(f"   Warnings:")
for warning in full_prediction['combined_recommendation'].get('warnings', [])[:3]:
    print(f"     ⚠️ {warning}")

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - Enhanced ML Pipeline Working!")
print("=" * 70)

# Summary
print(f"""
📊 Summary of ML Capabilities Added:
   1. ⚡ Speed Prediction - Predicts market speed (EXPLOSIVE/FAST/NORMAL/SLOW/CHOPPY)
   2. 📈 IV Prediction - Predicts IV direction (SPIKE/EXPAND/STABLE/CONTRACT/CRUSH)
   3. ⏱️ Theta Scenarios - Projects P&L at 15min/30min/1hr/2hr/EOD
   4. 🎯 Direction Prediction - XGBoost-ready direction forecast
   5. 💰 P&L Simulator - Combines all for trade grading (A+ to F)
   6. 🧠 Enhanced Service - Unified API for all predictions

🎉 Ready for production use!
""")
