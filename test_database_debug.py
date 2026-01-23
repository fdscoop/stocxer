"""
Debug database connectivity and check stored articles
"""
import asyncio
from config.supabase_config import get_supabase_admin_client
from datetime import datetime, timezone

async def debug_database():
    print("🔍 Debugging database connectivity...\n")
    
    try:
        supabase = get_supabase_admin_client()
        print("✅ Connected to Supabase")
        
        # Check if tables exist
        print("\n📊 Checking tables:")
        
        # Check market_news
        try:
            response = supabase.table("market_news").select("id", count="exact").execute()
            print(f"  ✅ market_news table exists: {response.count if hasattr(response, 'count') else len(response.data or [])} records")
        except Exception as e:
            print(f"  ❌ market_news table error: {e}")
        
        # Check news_fetch_log
        try:
            response = supabase.table("news_fetch_log").select("id", count="exact").execute()
            print(f"  ✅ news_fetch_log table exists: {response.count if hasattr(response, 'count') else len(response.data or [])} records")
        except Exception as e:
            print(f"  ❌ news_fetch_log table error: {e}")
        
        # Check market_sentiment_cache
        try:
            response = supabase.table("market_sentiment_cache").select("id", count="exact").execute()
            print(f"  ✅ market_sentiment_cache table exists: {response.count if hasattr(response, 'count') else len(response.data or [])} records")
        except Exception as e:
            print(f"  ❌ market_sentiment_cache table error: {e}")
        
        # Get all articles
        print("\n📰 All articles in market_news:")
        response = supabase.table("market_news").select("*").limit(10).execute()
        articles = response.data or []
        
        if articles:
            for i, article in enumerate(articles, 1):
                print(f"\n{i}. {article.get('title')}")
                print(f"   UUID: {article.get('article_uuid')}")
                print(f"   Published: {article.get('published_at')}")
                print(f"   Sentiment: {article.get('sentiment')} ({article.get('sentiment_score')})")
                print(f"   Source: {article.get('source')}")
        else:
            print("  ⚠️ No articles in database")
            print("  This means either:")
            print("  1. Tables haven't been created yet (run database/news_schema.sql)")
            print("  2. Articles failed to store (check logs above)")
        
        # Check fetch logs
        print("\n📝 Fetch logs:")
        response = supabase.table("news_fetch_log").select("*").order("fetch_time", desc=True).limit(5).execute()
        logs = response.data or []
        
        if logs:
            for log in logs:
                print(f"  {log.get('fetch_time')}: {log.get('articles_fetched')} articles, status: {log.get('api_response_code')}")
                if log.get('error_message'):
                    print(f"    Error: {log.get('error_message')}")
        else:
            print("  No fetch logs yet")
        
    except Exception as e:
        print(f"\n❌ Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_database())
