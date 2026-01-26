"""
Test script to verify news fetching and database storage
"""
import asyncio
import os
from datetime import datetime, timezone
from config.supabase_config import get_supabase_admin_client
from src.services.news_service import news_service

async def test_news_fetch():
    """Test the news fetch and storage pipeline"""
    
    print("=" * 70)
    print("🧪 TESTING NEWS FETCH AND STORAGE")
    print("=" * 70)
    print()
    
    # Step 1: Check environment variables
    print("1️⃣ Checking environment variables...")
    api_key = os.getenv("MARKETAUX_API_KEY")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not api_key:
        print("   ❌ MARKETAUX_API_KEY not found in environment")
        return
    else:
        print(f"   ✅ MARKETAUX_API_KEY: {api_key[:20]}...")
    
    if not supabase_url or not supabase_key:
        print("   ❌ Supabase credentials not found")
        return
    else:
        print(f"   ✅ Supabase URL: {supabase_url}")
    print()
    
    # Step 2: Check database tables
    print("2️⃣ Checking database tables...")
    try:
        supabase = get_supabase_admin_client()
        
        # Check if tables exist
        for table_name in ["market_news", "news_fetch_log", "market_sentiment_cache"]:
            try:
                response = supabase.table(table_name).select("id").limit(1).execute()
                print(f"   ✅ Table '{table_name}' exists")
            except Exception as e:
                print(f"   ❌ Table '{table_name}' not found: {e}")
                print()
                print("   📝 Please run database/news_schema.sql in Supabase SQL Editor")
                return
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return
    print()
    
    # Step 3: Check current news count
    print("3️⃣ Checking current news in database...")
    try:
        response = supabase.table("market_news").select("id", count="exact").execute()
        current_count = response.count if hasattr(response, 'count') else len(response.data or [])
        print(f"   📊 Current articles in database: {current_count}")
        
        # Get most recent article
        if current_count > 0:
            recent = supabase.table("market_news").select("*").order("fetched_at", desc=True).limit(1).execute()
            if recent.data:
                last_article = recent.data[0]
                print(f"   📰 Most recent article:")
                print(f"      Title: {last_article.get('title', 'N/A')[:60]}...")
                print(f"      Fetched: {last_article.get('fetched_at', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error checking database: {e}")
    print()
    
    # Step 4: Fetch new news
    print("4️⃣ Fetching new news from Marketaux API...")
    try:
        articles_stored = await news_service.fetch_and_store_news()
        print(f"   ✅ Successfully stored {articles_stored} articles")
    except Exception as e:
        print(f"   ❌ Error fetching news: {e}")
        import traceback
        print(traceback.format_exc())
        return
    print()
    
    # Step 5: Verify storage
    print("5️⃣ Verifying news was stored...")
    try:
        response = supabase.table("market_news").select("id", count="exact").execute()
        new_count = response.count if hasattr(response, 'count') else len(response.data or [])
        print(f"   📊 Articles in database after fetch: {new_count}")
        
        if new_count > current_count:
            print(f"   ✅ Successfully added {new_count - current_count} new articles!")
        else:
            print(f"   ⚠️ No new articles added (may be duplicates)")
        
        # Show recent articles
        recent = supabase.table("market_news").select("*").order("fetched_at", desc=True).limit(3).execute()
        if recent.data:
            print(f"\n   📰 Most recent articles:")
            for i, article in enumerate(recent.data, 1):
                print(f"\n   {i}. {article.get('title', 'N/A')[:60]}...")
                print(f"      Source: {article.get('source', 'N/A')}")
                print(f"      Sentiment: {article.get('sentiment', 'N/A')} (score: {article.get('sentiment_score', 0)})")
                print(f"      Fetched: {article.get('fetched_at', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error verifying storage: {e}")
    print()
    
    # Step 6: Check fetch log
    print("6️⃣ Checking fetch log...")
    try:
        response = supabase.table("news_fetch_log").select("*").order("fetch_time", desc=True).limit(3).execute()
        if response.data:
            print(f"   📝 Recent fetch attempts:")
            for i, log in enumerate(response.data, 1):
                print(f"\n   {i}. Fetch at {log.get('fetch_time', 'N/A')}")
                print(f"      Articles: {log.get('articles_fetched', 0)}")
                print(f"      Status: {log.get('api_response_code', 'N/A')}")
                if log.get('error_message'):
                    print(f"      Error: {log.get('error_message')}")
    except Exception as e:
        print(f"   ⚠️ Could not check fetch log: {e}")
    print()
    
    print("=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_news_fetch())
