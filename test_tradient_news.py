"""
Test Tradient News Service Integration

This script tests:
1. Tradient API connection
2. News parsing and storage
3. Fallback to Marketaux
4. Sentiment cache updates
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from src.services.tradient_news_service import TradientNewsService, tradient_news_service


async def test_tradient_fetch():
    """Test fetching from Tradient API"""
    print("\n" + "="*60)
    print("TEST 1: Tradient API Fetch")
    print("="*60)
    
    articles, success = await tradient_news_service.fetch_from_tradient()
    
    print(f"\n✅ Success: {success}")
    print(f"📰 Articles fetched: {len(articles)}")
    
    if articles:
        print("\n📋 Sample articles:")
        for i, article in enumerate(articles[:5], 1):
            print(f"\n  {i}. {article.title[:80]}...")
            print(f"     Sentiment: {article.sentiment}")
            print(f"     Stock: {article.stock_name or 'General market'} ({article.stock_symbol or 'N/A'})")
            print(f"     Sector: {article.sector_name or 'N/A'}")
            print(f"     Category: {article.category}/{article.sub_category}")
            print(f"     Indices: {', '.join(article.affected_indices) or 'None'}")
    
    return success, len(articles)


async def test_full_flow():
    """Test complete news fetch and store flow"""
    print("\n" + "="*60)
    print("TEST 2: Full Fetch & Store Flow")
    print("="*60)
    
    # Fetch and store
    articles_stored = await tradient_news_service.fetch_and_store_news()
    
    print(f"\n✅ Articles stored in database: {articles_stored}")
    
    # Check service status
    status = tradient_news_service.get_service_status()
    print(f"\n📊 Service Status:")
    print(f"   Primary source: {status['primary_source']}")
    print(f"   Using fallback: {status['using_fallback']}")
    print(f"   Consecutive failures: {status['consecutive_failures']}")
    print(f"   Last fetch: {status['last_fetch_time']}")
    
    return articles_stored


async def test_sentiment_cache():
    """Test sentiment cache retrieval"""
    print("\n" + "="*60)
    print("TEST 3: Sentiment Cache")
    print("="*60)
    
    for window in ["15min", "1hr", "4hr", "1day"]:
        sentiment = await tradient_news_service.get_market_sentiment(window)
        
        if sentiment:
            print(f"\n📈 {window.upper()} Sentiment:")
            print(f"   Overall: {sentiment.get('overall_sentiment', 'N/A')}")
            print(f"   Score: {sentiment.get('sentiment_score', 0):.3f}")
            print(f"   Articles: {sentiment.get('total_articles', 0)}")
            print(f"   Mood: {sentiment.get('market_mood', 'N/A')[:60]}...")
        else:
            print(f"\n⚠️ {window.upper()}: No cached sentiment data")


async def test_recent_news():
    """Test recent news retrieval (used by scanners)"""
    print("\n" + "="*60)
    print("TEST 4: Recent News (Scanner Integration)")
    print("="*60)
    
    # Get recent news for NIFTY
    nifty_news = await tradient_news_service.get_recent_news(
        hours=4,
        indices=["NIFTY"],
        limit=5
    )
    print(f"\n📰 Recent NIFTY news: {len(nifty_news)} articles")
    
    # Get recent news for BANKNIFTY
    bank_news = await tradient_news_service.get_recent_news(
        hours=4,
        indices=["BANKNIFTY"],
        limit=5
    )
    print(f"📰 Recent BANKNIFTY news: {len(bank_news)} articles")
    
    # Get all recent news
    all_news = await tradient_news_service.get_recent_news(
        hours=24,
        limit=10
    )
    print(f"📰 All recent news (24h): {len(all_news)} articles")
    
    return len(all_news)


async def test_signal_adjustment():
    """Test sentiment-based signal adjustment"""
    print("\n" + "="*60)
    print("TEST 5: Signal Adjustment")
    print("="*60)
    
    sentiment = await tradient_news_service.get_market_sentiment("1hr")
    
    if sentiment:
        # Test BUY signal adjustment
        adj_buy, conf_buy, reason_buy = tradient_news_service.get_sentiment_signal_adjustment(
            "BUY", sentiment
        )
        print(f"\n🟢 BUY Signal:")
        print(f"   Adjusted: {adj_buy}")
        print(f"   Confidence adjustment: {conf_buy:+.1f}%")
        print(f"   Reason: {reason_buy}")
        
        # Test SELL signal adjustment
        adj_sell, conf_sell, reason_sell = tradient_news_service.get_sentiment_signal_adjustment(
            "SELL", sentiment
        )
        print(f"\n🔴 SELL Signal:")
        print(f"   Adjusted: {adj_sell}")
        print(f"   Confidence adjustment: {conf_sell:+.1f}%")
        print(f"   Reason: {reason_sell}")
    else:
        print("\n⚠️ No sentiment data for signal adjustment test")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 TRADIENT NEWS SERVICE TEST")
    print("="*60)
    print(f"Started at: {datetime.now().isoformat()}")
    
    try:
        # Test 1: API fetch
        success, count = await test_tradient_fetch()
        
        if not success:
            print("\n⚠️ Tradient API not available. Testing fallback...")
        
        # Test 2: Full flow with storage
        await test_full_flow()
        
        # Test 3: Sentiment cache
        await test_sentiment_cache()
        
        # Test 4: Recent news (scanner integration)
        await test_recent_news()
        
        # Test 5: Signal adjustment
        await test_signal_adjustment()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
