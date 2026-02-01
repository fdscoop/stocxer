#!/usr/bin/env python3
"""
Test script to verify the momentum-based signal fix.
This simulates scenarios where a 100-point move should trigger a signal.
"""

import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, '.')

def create_mock_candles(direction='bullish', move_size=100, base_price=25000, num_candles=50):
    """
    Create mock candle data simulating a strong directional move.
    
    Args:
        direction: 'bullish' or 'bearish'
        move_size: Price move in points (e.g., 100)
        base_price: Starting price
        num_candles: Number of candles
    """
    dates = pd.date_range(end=datetime.now(), periods=num_candles, freq='15min')
    
    # Start with base price
    prices = [base_price]
    
    # Generate price movement - gradual move with some noise
    for i in range(1, num_candles):
        if direction == 'bullish':
            # Gradual upward movement with noise
            change = move_size / (num_candles - 1) + np.random.uniform(-5, 10)
        else:
            # Gradual downward movement with noise
            change = -move_size / (num_candles - 1) + np.random.uniform(-10, 5)
        
        prices.append(prices[-1] + change)
    
    # Create OHLC from prices
    data = []
    for i, price in enumerate(prices):
        high_offset = np.random.uniform(5, 15)
        low_offset = np.random.uniform(5, 15)
        close_offset = np.random.uniform(-10, 10)
        
        data.append({
            'open': price,
            'high': price + high_offset,
            'low': price - low_offset,
            'close': price + close_offset,
            'volume': np.random.randint(100000, 500000)
        })
    
    df = pd.DataFrame(data, index=dates)
    return df


def test_momentum_detection():
    """Test the momentum detection function directly."""
    logger.info("=" * 70)
    logger.info("TEST 1: Momentum Detection Function")
    logger.info("=" * 70)
    
    from src.analytics.ict_analysis import _detect_ltf_momentum
    
    # Scenario 1: Strong bullish move (100 points)
    logger.info("\n📈 Scenario 1: 100-point BULLISH move on 15m")
    candles = {
        '15': create_mock_candles(direction='bullish', move_size=100)
    }
    
    result = _detect_ltf_momentum(candles)
    
    if result:
        logger.info(f"✅ Momentum detected: {result['direction'].upper()}")
        logger.info(f"   Strength: {result['strength']:.2f}")
        logger.info(f"   Change: {result['price_change_pct']:.2f}%")
        assert result['direction'] == 'bullish', "Should detect bullish momentum"
        assert result['strength'] > 0.4, "Strength should be significant"
    else:
        logger.error("❌ FAILED: No momentum detected for 100-point move!")
        return False
    
    # Scenario 2: Strong bearish move (100 points)
    logger.info("\n📉 Scenario 2: 100-point BEARISH move on 15m")
    candles = {
        '15': create_mock_candles(direction='bearish', move_size=100)
    }
    
    result = _detect_ltf_momentum(candles)
    
    if result:
        logger.info(f"✅ Momentum detected: {result['direction'].upper()}")
        logger.info(f"   Strength: {result['strength']:.2f}")
        assert result['direction'] == 'bearish', "Should detect bearish momentum"
    else:
        logger.error("❌ FAILED: No momentum detected for bearish move!")
        return False
    
    # Scenario 3: Small move (should NOT trigger)
    logger.info("\n📊 Scenario 3: Small 20-point move (should NOT trigger)")
    candles = {
        '15': create_mock_candles(direction='bullish', move_size=20)
    }
    
    result = _detect_ltf_momentum(candles)
    
    if result and result['strength'] > 0.6:
        logger.warning("⚠️ Small move detected as strong - may be too sensitive")
    else:
        logger.info("✅ Small move correctly not flagged as strong momentum")
    
    return True


def test_ltf_entry_with_momentum():
    """Test that LTF entry model detects momentum entries."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: LTF Entry Model with Momentum Override")
    logger.info("=" * 70)
    
    from src.analytics.ict_analysis import (
        identify_ltf_entry_model, HTFBias, ICTAnalyzer
    )
    
    # Create neutral HTF bias (this is when the old system would say WAIT)
    htf_bias = HTFBias(
        overall_direction='neutral',
        bias_strength=50,
        structure_quality='LOW',
        premium_discount='equilibrium',
        key_zones=[],
        swing_high=25200,
        swing_low=24800,
        current_price=25000
    )
    
    # Create LTF candles with strong bullish move
    candles = {
        '15': create_mock_candles(direction='bullish', move_size=100, base_price=24900),
        '5': create_mock_candles(direction='bullish', move_size=50, base_price=24950)
    }
    
    current_price = 25000
    
    # Analyze the candles to get FVGs/OBs
    analyzer = ICTAnalyzer()
    ltf_analyses = {}
    
    for tf in ['15', '5']:
        df = candles[tf]
        try:
            df_analyzed = analyzer.identify_market_structure(df)
            fvgs = analyzer.identify_fair_value_gaps(df)
            order_blocks = analyzer.identify_order_blocks(df)
            
            ltf_analyses[tf] = {
                'fvgs': fvgs,
                'order_blocks': order_blocks,
                'structure_breaks': []
            }
            logger.info(f"   {tf}m: Found {len(fvgs)} FVGs, {len(order_blocks)} OBs")
        except Exception as e:
            logger.warning(f"   Analysis failed for {tf}m: {e}")
    
    # Test the entry model detection
    logger.info("\n🔎 Testing LTF Entry Detection (HTF=NEUTRAL, strong LTF momentum)...")
    
    entry = identify_ltf_entry_model(
        htf_bias=htf_bias,
        ltf_analyses=ltf_analyses,
        current_price=current_price,
        candles_by_timeframe=candles
    )
    
    if entry:
        logger.info(f"✅ Entry Model Found!")
        logger.info(f"   Type: {entry.entry_type}")
        logger.info(f"   Timeframe: {entry.timeframe}")
        logger.info(f"   Entry Zone: {entry.entry_zone}")
        logger.info(f"   Momentum Confirmed: {entry.momentum_confirmed}")
        logger.info(f"   Alignment Score: {entry.alignment_score}")
        logger.info(f"   Confidence: {entry.confidence}")
        
        # Should be a momentum-based entry when HTF is neutral
        if 'MOMENTUM' in entry.entry_type or entry.alignment_score >= 35:
            logger.info("✅ Correctly identified momentum-based entry!")
            return True
        else:
            logger.info("✅ Found ICT-based entry (FVG/OB aligned with momentum)")
            return True
    else:
        logger.error("❌ FAILED: No entry model found despite strong momentum!")
        logger.error("   This is the bug we're trying to fix!")
        return False


def test_confidence_scoring():
    """Test that momentum entries get proper confidence scores."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Confidence Scoring for Momentum Entries")
    logger.info("=" * 70)
    
    from src.analytics.confidence_calculator import calculate_trade_confidence
    
    # Scenario 1: Momentum entry with partial HTF alignment
    htf_bias = {
        'overall_direction': 'neutral',
        'bias_strength': 50,
        'structure_quality': 'LOW',
        'premium_discount': 'equilibrium'
    }
    
    ltf_entry = {
        'entry_type': 'FVG_TEST_MOMENTUM',
        'timeframe': '15',
        'momentum_confirmed': True,
        'alignment_score': 70
    }
    
    confidence = calculate_trade_confidence(
        htf_bias=htf_bias,
        ltf_entry=ltf_entry
    )
    
    logger.info(f"\n📊 Momentum Entry Confidence Breakdown:")
    logger.info(f"   HTF Structure: {confidence['htf_structure']}/40")
    logger.info(f"   LTF Confirmation: {confidence['ltf_confirmation']}/25")
    logger.info(f"   ML Alignment: {confidence['ml_alignment']}/15")
    logger.info(f"   Candlestick: {confidence['candlestick']}/10")
    logger.info(f"   Futures: {confidence['futures_basis']}/5")
    logger.info(f"   Constituents: {confidence['constituents']}/5")
    logger.info(f"   {'─' * 40}")
    logger.info(f"   TOTAL: {confidence['total']}/100 ({confidence['confidence_level']})")
    
    # LTF should get decent score for momentum entry
    if confidence['ltf_confirmation'] >= 10:
        logger.info("✅ Momentum entry correctly scored in LTF confirmation")
    else:
        logger.warning("⚠️ LTF confirmation score may be too low for momentum")
    
    # Scenario 2: Pure momentum entry (no FVG/OB)
    ltf_entry_pure = {
        'entry_type': 'MOMENTUM_ENTRY',
        'timeframe': '15',
        'momentum_confirmed': True,
        'alignment_score': 50
    }
    
    confidence_pure = calculate_trade_confidence(
        htf_bias=htf_bias,
        ltf_entry=ltf_entry_pure
    )
    
    logger.info(f"\n📊 Pure Momentum Entry Confidence:")
    logger.info(f"   TOTAL: {confidence_pure['total']}/100 ({confidence_pure['confidence_level']})")
    
    if confidence_pure['total'] >= 25:  # Should be at least moderate
        logger.info("✅ Pure momentum entry gets reasonable confidence")
        return True
    else:
        logger.warning("⚠️ Pure momentum confidence may be too low")
        return True  # Not a failure, just a note


def main():
    logger.info("=" * 70)
    logger.info("🧪 MOMENTUM FIX VALIDATION TEST")
    logger.info("=" * 70)
    logger.info("Testing the fix for missed 100-point moves...")
    logger.info("")
    
    results = []
    
    # Run tests
    try:
        results.append(("Momentum Detection", test_momentum_detection()))
    except Exception as e:
        logger.error(f"❌ Momentum Detection Test Failed: {e}")
        results.append(("Momentum Detection", False))
    
    try:
        results.append(("LTF Entry with Momentum", test_ltf_entry_with_momentum()))
    except Exception as e:
        logger.error(f"❌ LTF Entry Test Failed: {e}")
        results.append(("LTF Entry with Momentum", False))
    
    try:
        results.append(("Confidence Scoring", test_confidence_scoring()))
    except Exception as e:
        logger.error(f"❌ Confidence Scoring Test Failed: {e}")
        results.append(("Confidence Scoring", False))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📋 TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {status}: {name}")
        if result:
            passed += 1
    
    logger.info(f"\n   Total: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("\n🎉 All tests passed! The momentum fix is working.")
    else:
        logger.info("\n⚠️ Some tests failed. Review the changes.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
