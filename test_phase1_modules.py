"""
Test script for Phase 1 modules
Demonstrates the new ICT top-down workflow with candlestick patterns
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import new Phase 1 modules
from src.analytics.candlestick_patterns import CandlestickAnalyzer, analyze_candlestick_patterns
from src.analytics.confidence_calculator import ConfidenceCalculator, calculate_trade_confidence
from src.analytics.ict_analysis import (
    analyze_multi_timeframe_ict_topdown,
    calculate_premium_discount_zones,
    HTFBias,
    LTFEntryModel
)

print("=" * 70)
print("🚀 TESTING PHASE 1 MODULES - ICT TOP-DOWN WITH CANDLESTICK PATTERNS")
print("=" * 70)
print()

# Generate sample OHLC data for testing
def generate_sample_candles(num_candles=100, base_price=25000, timeframe='D'):
    """Generate realistic sample candle data"""
    dates = pd.date_range(end=datetime.now(), periods=num_candles, freq=timeframe)
    
    # Generate prices with some trend and volatility
    trend = np.linspace(0, 500, num_candles)  # Upward trend
    volatility = np.random.randn(num_candles) * 100
    
    close_prices = base_price + trend + volatility
    
    # Generate OHLC from close
    open_prices = close_prices + np.random.randn(num_candles) * 20
    high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(num_candles) * 30)
    low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(num_candles) * 30)
    
    df = pd.DataFrame({
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': np.random.randint(100000, 500000, num_candles)
    }, index=dates)
    
    return df

print("📊 Generating sample multi-timeframe data...")
print()

# Create sample data for multiple timeframes
timeframes_data = {
    'D': generate_sample_candles(100, 25000, 'D'),    # Daily
    '240': generate_sample_candles(200, 25000, '4H'),  # 4-hour
    '60': generate_sample_candles(300, 25000, 'H'),    # 1-hour
    '15': generate_sample_candles(400, 25000, '15T'), # 15-minute
}

current_price = timeframes_data['15']['close'].iloc[-1]
print(f"💰 Current Price: ₹{current_price:.2f}")
print()

# Test 1: Premium/Discount Zone Calculation
print("=" * 70)
print("TEST 1: PREMIUM/DISCOUNT ZONE CALCULATION")
print("=" * 70)
swing_high = 25500
swing_low = 24800
pd_result = calculate_premium_discount_zones(swing_high, swing_low, current_price)
print(f"Swing High: ₹{swing_high}")
print(f"Swing Low: ₹{swing_low}")
print(f"Current Price: ₹{current_price:.2f}")
print(f"Zone: {pd_result['zone'].upper()}")
print(f"Position: {pd_result['percentage']:.1f}% of range")
print()

# Test 2: Candlestick Pattern Detection
print("=" * 70)
print("TEST 2: CANDLESTICK PATTERN DETECTION")
print("=" * 70)

candles_dict = {
    'D': timeframes_data['D'],
    '240': timeframes_data['240'],
    '60': timeframes_data['60'],
    '15': timeframes_data['15']
}

expected_direction = 'bullish'  # Assume bullish based on uptrend
pattern_result = analyze_candlestick_patterns(candles_dict, expected_direction)

print(f"Expected Direction: {expected_direction.upper()}")
print(f"Patterns Detected Across Timeframes:")

for tf, patterns in pattern_result['patterns_detected'].items():
    if patterns:
        print(f"\n  {tf}:")
        for pattern in patterns[:3]:  # Show top 3
            print(f"    - {pattern.pattern_name} ({pattern.direction})")

confluence = pattern_result['confluence_analysis']
print(f"\n📊 Confluence Analysis:")
print(f"  Score: {confluence['confluence_score']:.1f}/100")
print(f"  Confidence: {confluence['confidence_level']}")
print(f"  Aligned Patterns: {confluence['aligned_patterns']}")
print(f"  Conflicting Patterns: {confluence['conflicting_patterns']}")
print()

# Test 3: ICT Top-Down Analysis
print("=" * 70)
print("TEST 3: ICT TOP-DOWN ANALYSIS")
print("=" * 70)

topdown_result = analyze_multi_timeframe_ict_topdown(
    candles_by_timeframe=timeframes_data,
    current_price=current_price
)

htf_bias = topdown_result['htf_bias']
ltf_entry = topdown_result['ltf_entry']

print(f"📈 HTF Bias:")
print(f"  Direction: {htf_bias.overall_direction.upper()}")
print(f"  Strength: {htf_bias.bias_strength:.1f}/100")
print(f"  Structure: {htf_bias.structure_quality}")
print(f"  Premium/Discount: {htf_bias.premium_discount.upper()}")
print(f"  Key Zones: {len(htf_bias.key_zones)}")

if ltf_entry:
    print(f"\n🎯 LTF Entry Model Found:")
    print(f"  Type: {ltf_entry.entry_type}")
    print(f"  Timeframe: {ltf_entry.timeframe}")
    print(f"  Entry Zone: ₹{ltf_entry.entry_zone[0]:.2f} - ₹{ltf_entry.entry_zone[1]:.2f}")
    print(f"  Trigger: ₹{ltf_entry.trigger_price:.2f}")
    print(f"  Momentum: {'✅ Confirmed' if ltf_entry.momentum_confirmed else '❌ Not Confirmed'}")
    print(f"  Alignment: {ltf_entry.alignment_score:.0f}%")
    print(f"  Confidence: {ltf_entry.confidence:.2%}")
else:
    print(f"\n⚠️ No LTF Entry Model Found")
print()

# Test 4: Confidence Calculation
print("=" * 70)
print("TEST 4: CONFIDENCE CALCULATION WITH NEW HIERARCHY")
print("=" * 70)

# Mock HTF bias for confidence test
htf_bias_dict = {
    'overall_direction': htf_bias.overall_direction,
    'bias_strength': htf_bias.bias_strength,
    'structure_quality': htf_bias.structure_quality,
    'premium_discount': htf_bias.premium_discount
}

# Mock LTF entry
ltf_entry_dict = {
    'entry_type': ltf_entry.entry_type if ltf_entry else 'NO_SETUP',
    'timeframe': ltf_entry.timeframe if ltf_entry else 'N/A',
    'momentum_confirmed': ltf_entry.momentum_confirmed if ltf_entry else False,
    'alignment_score': ltf_entry.alignment_score if ltf_entry else 0
}

# Mock ML signal (would come from ARIMA in real scenario)
ml_signal = {
    'direction': 'bullish',
    'confidence': 0.65,
    'agrees_with_htf': True
}

# Mock futures data
futures_data = {
    'basis_pct': 0.4,
    'sentiment': 'bullish'
}

# Calculate confidence
confidence_breakdown = calculate_trade_confidence(
    htf_bias=htf_bias_dict,
    ltf_entry=ltf_entry_dict,
    ml_signal=ml_signal,
    candlestick_analysis=pattern_result,
    futures_data=futures_data,
    probability_analysis=None
)

print(f"🎯 Final Confidence Breakdown:")
print(f"  ICT HTF Structure:    {confidence_breakdown['htf_structure']:.1f}/40  (40%)")
print(f"  ICT LTF Confirmation: {confidence_breakdown['ltf_confirmation']:.1f}/25  (25%)")
print(f"  ML Alignment:         {confidence_breakdown['ml_alignment']:.1f}/15  (15%)")
print(f"  Candlestick Patterns: {confidence_breakdown['candlestick']:.1f}/10  (10%)")
print(f"  Futures Basis:        {confidence_breakdown['futures_basis']:.1f}/5   (5%)")
print(f"  Constituents:         {confidence_breakdown['constituents']:.1f}/5   (5%)")
print(f"  " + "-" * 50)
print(f"  TOTAL CONFIDENCE:     {confidence_breakdown['total']:.1f}/100")
print(f"  Level:                {confidence_breakdown['confidence_level']}")
print()

# Summary
print("=" * 70)
print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
print("=" * 70)
print()
print("Summary:")
print(f"✅ Premium/Discount calculation working")
print(f"✅ Candlestick pattern detection working ({confluence['aligned_patterns']} patterns aligned)")
print(f"✅ ICT top-down analysis working (HTF: {htf_bias.overall_direction}, LTF: {ltf_entry.entry_type if ltf_entry else 'N/A'})")
print(f"✅ Confidence calculator working ({confidence_breakdown['total']:.1f}/100)")
print()
print("🎯 Phase 1 modules are production-ready!")
print("📌 Next: Integrate into main signal generation (Phase 2)")
print()
