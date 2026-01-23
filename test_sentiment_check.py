"""
Quick test to check cached sentiment after articles are stored
"""
import asyncio
from src.services.news_service import news_service

async def check_sentiment():
    print("🎯 Checking cached sentiment...\n")
    
    for window in ["15min", "1hr", "4hr", "1day"]:
        cached = await news_service.get_market_sentiment(time_window=window)
        
        if cached:
            print(f"Time Window: {window}")
            print(f"  Overall Sentiment: {cached.get('overall_sentiment')}")
            print(f"  Sentiment Score: {cached.get('sentiment_score')}")
            print(f"  Market Mood: {cached.get('market_mood')}")
            print(f"  Total Articles: {cached.get('total_articles')}")
            print(f"  Bullish: {cached.get('positive_count')} | Bearish: {cached.get('negative_count')} | Neutral: {cached.get('neutral_count')}")
            print(f"  Key Themes: {', '.join(cached.get('key_themes', []))}")
            print(f"  Sector Sentiment: {cached.get('sector_sentiment')}")
            print(f"  Trading Implication: {cached.get('trading_implication')}")
            print()
        else:
            print(f"{window}: No data yet\n")
    
    # Get recent news from DB
    print("📰 Recent news in database:")
    articles = await news_service.get_recent_news(hours=24, limit=10)
    print(f"Total articles in last 24 hours: {len(articles)}\n")
    
    if articles:
        for i, article in enumerate(articles[:5], 1):
            print(f"{i}. {article.get('title')}")
            print(f"   Sentiment: {article.get('sentiment')} ({article.get('sentiment_score')})")
            print(f"   Relevance: {article.get('relevance_score')}")
            print()

if __name__ == "__main__":
    asyncio.run(check_sentiment())
