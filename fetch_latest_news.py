"""
Fetch latest news from Marketaux and store in Supabase
"""
import asyncio
from datetime import datetime, timezone
from config.supabase_config import get_supabase_admin_client
from src.services.news_service import news_service

async def fetch_and_store_news():
    """Fetch latest news and store in database"""
    
    print("=" * 70)
    print("📰 Fetching Latest News from Marketaux API")
    print("=" * 70)
    print()
    
    # Check if API key is set
    if not news_service.api_key:
        print("❌ ERROR: MARKETAUX_API_KEY not set in .env")
        return
    
    print(f"✅ API Key configured: {news_service.api_key[:20]}...")
    print()
    
    # Step 1: Check if database tables exist
    print("🔍 Step 1: Checking database tables...")
    try:
        supabase = get_supabase_admin_client()
        
        # Try to query each table
        tables_exist = True
        for table_name in ["market_news", "news_fetch_log", "market_sentiment_cache"]:
            try:
                response = supabase.table(table_name).select("id").limit(1).execute()
                print(f"  ✅ {table_name} exists")
            except Exception as e:
                print(f"  ❌ {table_name} not found: {e}")
                tables_exist = False
        
        if not tables_exist:
            print()
            print("⚠️  Database tables not found!")
            print("📝 Please run the SQL from database/news_schema.sql in Supabase SQL Editor")
            print("   1. Go to Supabase Dashboard > SQL Editor")
            print("   2. Copy contents from database/news_schema.sql")
            print("   3. Execute the SQL")
            print()
            return
        
        print()
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return
    
    # Step 2: Fetch news from Marketaux API
    print("📰 Step 2: Fetching news from Marketaux API...")
    print()
    
    all_articles = []
    
    # Fetch 1: General Indian market news
    print("  Fetching Indian market news...")
    try:
        articles = await news_service.fetch_news(
            countries="in",
            limit=3
        )
        all_articles.extend(articles)
        print(f"  ✅ Fetched {len(articles)} articles")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Small delay to avoid rate limiting
    await asyncio.sleep(1)
    
    # Fetch 2: Search for "nifty" keyword
    print("  Fetching NIFTY-related news...")
    try:
        articles = await news_service.fetch_news(
            search_query="nifty stock market india",
            countries="in,us",
            limit=3
        )
        all_articles.extend(articles)
        print(f"  ✅ Fetched {len(articles)} articles")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    await asyncio.sleep(1)
    
    # Fetch 3: Search for "india market" keyword
    print("  Fetching general India market news...")
    try:
        articles = await news_service.fetch_news(
            search_query="india market sensex",
            countries="in",
            limit=3
        )
        all_articles.extend(articles)
        print(f"  ✅ Fetched {len(articles)} articles")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print()
    print(f"📊 Total articles fetched: {len(all_articles)}")
    print()
    
    if not all_articles:
        print("⚠️  No articles fetched. This could mean:")
        print("  - API rate limit reached")
        print("  - No recent news available")
        print("  - API key issue")
        return
    
    # Step 3: Store articles in database
    print("💾 Step 3: Storing articles in Supabase...")
    try:
        stored_count = await news_service.store_articles(all_articles)
        print(f"✅ Successfully stored {stored_count} articles")
        print()
    except Exception as e:
        print(f"❌ Error storing articles: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Display stored articles
    print("📰 Step 4: Verifying stored articles...")
    try:
        response = supabase.table("market_news").select("*").order(
            "published_at", desc=True
        ).limit(10).execute()
        
        stored_articles = response.data or []
        print(f"✅ Total articles in database: {len(stored_articles)}")
        print()
        
        if stored_articles:
            print("Latest articles:")
            print("-" * 70)
            for i, article in enumerate(stored_articles[:5], 1):
                print(f"\n{i}. {article.get('title')}")
                print(f"   Source: {article.get('source')}")
                print(f"   Published: {article.get('published_at')}")
                print(f"   Sentiment: {article.get('sentiment')} (score: {article.get('sentiment_score')})")
                print(f"   Relevance: {article.get('relevance_score')}")
                print(f"   Impact: {article.get('impact_level')}")
                
                indices = article.get('affected_indices') or []
                if indices:
                    print(f"   Indices: {', '.join(indices)}")
                
                sectors = article.get('affected_sectors') or []
                if sectors:
                    print(f"   Sectors: {', '.join(sectors)}")
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
    
    print()
    print("-" * 70)
    
    # Step 5: Update sentiment cache
    print("\n🎯 Step 5: Computing sentiment cache...")
    try:
        await news_service.update_sentiment_cache()
        print("✅ Sentiment cache updated")
        
        # Display cached sentiment
        cached = await news_service.get_market_sentiment(time_window="1hr")
        if cached:
            print()
            print("Market Sentiment (1-hour window):")
            print(f"  Overall: {cached.get('overall_sentiment').upper()}")
            print(f"  Score: {cached.get('sentiment_score')}")
            print(f"  Mood: {cached.get('market_mood')}")
            print(f"  Articles: {cached.get('total_articles')}")
            print(f"  Bullish: {cached.get('positive_count')} | " +
                  f"Bearish: {cached.get('negative_count')} | " +
                  f"Neutral: {cached.get('neutral_count')}")
            
            themes = cached.get('key_themes', [])
            if themes:
                print(f"  Key Themes: {', '.join(themes)}")
            
            print(f"  Trading Implication: {cached.get('trading_implication')}")
        
    except Exception as e:
        print(f"❌ Error updating sentiment cache: {e}")
    
    print()
    print("=" * 70)
    print("✅ News fetch and storage complete!")
    print("=" * 70)
    print()
    print("📊 API Usage:")
    print(f"  Requests today: {news_service._request_count_today}/100")
    print(f"  Remaining: {100 - news_service._request_count_today}")
    print()
    print("💡 Next steps:")
    print("  - News will auto-fetch every 15 minutes when the server runs")
    print("  - Use /api/news endpoint to retrieve news")
    print("  - Use /api/sentiment endpoint to get market sentiment")
    print("  - Use /api/news/status to check API usage")

if __name__ == "__main__":
    asyncio.run(fetch_and_store_news())
