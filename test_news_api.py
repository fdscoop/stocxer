"""
Test script for Marketaux News API integration
Verifies that the API key works and data can be fetched
"""
import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import news service
from src.services.news_service import news_service

async def test_news_fetch():
    """Test fetching news from Marketaux API"""
    
    print("=" * 60)
    print("🧪 Testing Marketaux News API")
    print("=" * 60)
    
    # Check API key
    if not news_service.api_key:
        print("❌ ERROR: MARKETAUX_API_KEY not set in .env")
        return
    
    print(f"✅ API Key found: {news_service.api_key[:20]}...")
    print()
    
    # Test 1: Fetch news for India
    print("📰 Test 1: Fetching Indian market news...")
    try:
        articles = await news_service.fetch_news(
            countries="in",
            limit=3
        )
        
        print(f"✅ Fetched {len(articles)} articles")
        print()
        
        if articles:
            print("Sample Articles:")
            print("-" * 60)
            for i, article in enumerate(articles, 1):
                print(f"\n{i}. {article.title}")
                print(f"   Source: {article.source}")
                print(f"   Published: {article.published_at}")
                print(f"   Sentiment: {article.sentiment} (score: {article.sentiment_score})")
                print(f"   Relevance: {article.relevance_score}")
                print(f"   Impact: {article.impact_level}")
                print(f"   Indices: {', '.join(article.affected_indices) if article.affected_indices else 'None'}")
                print(f"   Sectors: {', '.join(article.affected_sectors) if article.affected_sectors else 'None'}")
                if article.description:
                    desc = article.description[:100] + "..." if len(article.description) > 100 else article.description
                    print(f"   Description: {desc}")
        else:
            print("⚠️ No articles returned (this might be okay if no recent news)")
        
        print()
        print("-" * 60)
        
    except Exception as e:
        print(f"❌ Error fetching news: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Check API rate limiting
    print("\n📊 Test 2: Checking rate limit status...")
    print(f"   Requests today: {news_service._request_count_today}")
    print(f"   Daily limit: {news_service.MAX_REQUESTS_PER_DAY}")
    print(f"   Remaining: {news_service.MAX_REQUESTS_PER_DAY - news_service._request_count_today}")
    print()
    
    # Test 3: Test with search query
    print("📰 Test 3: Fetching news with 'nifty' keyword...")
    try:
        articles = await news_service.fetch_news(
            search_query="nifty stock market",
            countries="in,us",
            limit=3
        )
        
        print(f"✅ Fetched {len(articles)} articles with keyword search")
        if articles:
            print(f"   First article: {articles[0].title}")
        print()
        
    except Exception as e:
        print(f"❌ Error with keyword search: {e}")
    
    # Test 4: Test storing to database (optional)
    print("💾 Test 4: Testing database storage...")
    try:
        if articles:
            stored = await news_service.store_articles(articles[:2])  # Store first 2
            print(f"✅ Stored {stored} articles to database")
        else:
            print("⚠️ No articles to store")
        print()
        
    except Exception as e:
        print(f"❌ Error storing to database: {e}")
        print("   (Make sure you've run the database/news_schema.sql in Supabase)")
    
    # Test 5: Test sentiment cache update
    print("🎯 Test 5: Testing sentiment cache update...")
    try:
        await news_service.update_sentiment_cache()
        print("✅ Sentiment cache updated")
        
        # Try to retrieve cached sentiment
        cached = await news_service.get_market_sentiment(time_window="1hr")
        if cached:
            print(f"   Cached sentiment: {cached.get('overall_sentiment')}")
            print(f"   Sentiment score: {cached.get('sentiment_score')}")
            print(f"   Total articles: {cached.get('total_articles')}")
        else:
            print("   ℹ️ No cached sentiment yet (this is normal on first run)")
        print()
        
    except Exception as e:
        print(f"❌ Error with sentiment cache: {e}")
    
    print("=" * 60)
    print("✅ Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_news_fetch())
