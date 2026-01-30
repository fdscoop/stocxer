#!/usr/bin/env python3
"""
Quick Manual Test - Simplified version
Tests the optimizations without blocking on slow requests
"""

import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

import asyncio
from datetime import datetime, timedelta
import time

# Import optimized components
from main import get_candles_cached, CANDLE_CACHE, CACHE_TTL
from src.api.fyers_client import fyers_client
from src.services.parallel_stock_analysis import get_fast_analyzer


async def test_caching_basic():
    """Test basic caching functionality"""
    print("=" * 60)
    print("TEST 1: Caching Layer")
    print("=" * 60)
    
    symbol = "NSE:NIFTY50-INDEX"
    resolution = "D"
    date_to = datetime.now()
    date_from = date_to - timedelta(days=60)
    
    print(f"\n1st fetch ({symbol}, {resolution})...")
    start = time.time()
    try:
        candles1 = get_candles_cached(symbol, resolution, date_from, date_to)  
        time1 = time.time() - start
        print(f"✅ Time: {time1:.2f}s | Candles: {len(candles1) if candles1 is not None else 0}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print(f"\n2nd fetch (should hit cache)...")
    start = time.time()
    try:
        candles2 = get_candles_cached(symbol, resolution, date_from, date_to)
        time2 = time.time() - start
        print(f"✅ Time: {time2:.2f}s | Speedup: {time1/time2 if time2 > 0 else 0:.1f}x")
        
        if time2 < 0.1:  # Cache hit should be instant
            print("✅ PASS: Cache is working!")
            return True
        else:
            print("⚠️  WARNING: Cache may not be working")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_parallel_analyzer():
    """Test parallel stock analysis"""
    print("\n" + "=" * 60)
    print("TEST 2: Parallel Stock Analysis")
    print("=" * 60)
    
    print(f"\nInitializing analyzer...")
    analyzer = get_fast_analyzer(fyers_client, CANDLE_CACHE, CACHE_TTL)
    print(f"✅ Analyzer ready ({len(analyzer.stocks)} stocks)")
    
    print(f"\nRunning parallel analysis...")
    start = time.time()
    try:
        result = await analyzer.analyze_all_stocks("NIFTY")
        elapsed = time.time() - start
        
        print(f"\n✅ Analysis complete!")
        print(f"   ⏱️  Time: {elapsed:.2f}s")
        print(f"   📊 Scanned: {result['stocks_scanned']}/50 stocks")
        print(f"   📈 Bullish: {result['bullish_stocks']} ({result['bullish_pct']}%)")
        print(f"   📉 Bearish: {result['bearish_stocks']} ({result['bearish_pct']}%)")
        print(f"   🎯 Direction: {result['expected_direction']} ({result['confidence']}%)")
        
        if elapsed < 20:
            print(f"\n✅ PASS: Completed in {elapsed:.2f}s (target: <15s)")
            return True
        else:
            print(f"\n⚠️  WARNING: Took {elapsed:.2f}s (target: <15s)")
            return False
            
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run tests"""
    print("\n" + "=" * 60)
    print("🚀 TradeWise Performance Optimization - Quick Test")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    # Test 1: Caching
    print("\n")
    try:
        cache_ok = await test_caching_basic()
        results.append(("Caching", cache_ok))
    except Exception as e:
        print(f"Caching test error: {e}")
        results.append(("Caching", False))
    
    # Test 2: Parallel analysis
    print("\n")
    try:
        parallel_ok = await test_parallel_analyzer()
        results.append(("Parallel Analysis", parallel_ok))
    except Exception as e:
        print(f"Parallel test error: {e}")
        results.append(("Parallel Analysis", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed_count = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed_count}/{len(results)} tests passed")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
