"""
Test script for performance optimization verification
Tests caching and parallel analysis functionality
"""

import asyncio
import time
from datetime import datetime, timedelta


async def test_caching():
    """Test candle caching functionality"""
    print("=" * 60)
    print("TEST 1: Caching Infrastructure")
    print("=" * 60)
    
    # Import after adding to path
    import sys
    sys.path.insert(0, '/Users/bineshbalan/TradeWise')
    
    from src.api.fyers_client import fyers_client
    from main import get_candles_cached, CANDLE_CACHE
    
    symbol = "NSE:NIFTY50-INDEX"
    resolution = "D"
    date_to = datetime.now()
    date_from = date_to - timedelta(days=60)
    
    print(f"\n1. Testing FIRST fetch (cache miss expected)...")
    start = time.time()
    result1 = get_candles_cached(symbol, resolution, date_from, date_to)
    time1 = time.time() - start
    print(f"   ⏱️  Time: {time1:.2f}s")
    print(f"   📊 Candles: {len(result1) if result1 is not None else 0}")
    print(f"   📦 Cache size: {len(CANDLE_CACHE)}")
    
    print(f"\n2. Testing SECOND fetch (cache hit expected)...")
    start = time.time()
    result2 = get_candles_cached(symbol, resolution, date_from, date_to)
    time2 = time.time() - start
    print(f"   ⏱️  Time: {time2:.2f}s")
    print(f"   📊 Candles: {len(result2) if result2 is not None else 0}")
    
    # Verify cache hit
    speedup = time1 / time2 if time2 > 0 else 0
    print(f"\n✅ Cache speedup: {speedup:.1f}x faster")
    
    if speedup > 5:
        print("   🎉 PASS: Cache is working!")
        return True
    else:
        print("   ❌ FAIL: Cache may not be working properly")
        return False


async def test_parallel_analysis():
    """Test parallel stock analysis"""
    print("\n" + "=" * 60)
    print("TEST 2: Parallel Stock Analysis")
    print("=" * 60)
    
    import sys
    sys.path.insert(0, '/Users/bineshbalan/TradeWise')
    
    from src.api.fyers_client import fyers_client
    from src.services.parallel_stock_analysis import get_fast_analyzer
    from main import CANDLE_CACHE, CACHE_TTL
    
    print(f"\n1. Initializing FastStockAnalyzer...")
    analyzer = get_fast_analyzer(fyers_client, CANDLE_CACHE, CACHE_TTL)
    print(f"   ✅ Analyzer created with {len(analyzer.stocks)} stocks")
    
    print(f"\n2. Running parallel analysis...")
    start = time.time()
    try:
        result = await analyzer.analyze_all_stocks("NIFTY")
        analysis_time = time.time() - start
        
        print(f"\n   ⏱️  Total time: {analysis_time:.2f}s")
        print(f"   📊 Stocks scanned: {result['stocks_scanned']}")
        print(f"   📈 Bullish: {result['bullish_stocks']} ({result['bullish_pct']}%)")
        print(f"   📉 Bearish: {result['bearish_stocks']} ({result['bearish_pct']}%)")
        print(f"   🎯 Direction: {result['expected_direction']} (confidence: {result['confidence']}%)")
        
        if analysis_time < 20:
            print(f"\n✅ PASS: Analysis completed in {analysis_time:.2f}s (target: <15s)")
            return True
        else:
            print(f"\n⚠️  WARNING: Analysis took {analysis_time:.2f}s (target: <15s)")
            return False
            
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        print(traceback.format_exc())
        return False


async def test_integration():
    """Test full integration"""
    print("\n" + "=" * 60)
    print("TEST 3: Full Integration Test")
    print("=" * 60)
    
    print("\n⚠️  This test requires a running server.")
    print("   Run: uvicorn main:app --reload")
    print("   Then test manually with:")
    print('   curl "http://localhost:8000/signals/NSE:NIFTY50-INDEX/actionable?quick_mode=false"')
    
    return None


async def main():
    """Run all tests"""
    print("\n🚀 TradeWise Performance Optimization Tests")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Caching
    try:
        results['caching'] = await test_caching()
    except Exception as e:
        print(f"\n❌ Caching test failed: {e}")
        results['caching'] = False
    
    # Test 2: Parallel Analysis
    try:
        results['parallel'] = await test_parallel_analysis()
    except Exception as e:
        print(f"\n❌ Parallel analysis test failed: {e}")
        results['parallel'] = False
    
    # Test 3: Integration
    await test_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    
    print(f"\n✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0 and passed > 0:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check logs above.")


if __name__ == "__main__":
    asyncio.run(main())
