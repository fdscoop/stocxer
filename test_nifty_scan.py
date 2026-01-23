"""
Test NIFTY options scanner with sentiment integration
"""
import asyncio
from datetime import datetime

async def scan_nifty_options():
    """Scan NIFTY options with sentiment integration"""
    
    print("=" * 80)
    print("📊 NIFTY Options Scanner with Sentiment Analysis")
    print("=" * 80)
    print()
    
    # Import after printing header
    from src.analytics.index_options import get_index_analyzer
    from src.api.fyers_client import fyers_client
    from src.analytics.news_sentiment import news_analyzer
    
    # Step 1: Get market sentiment
    print("🎯 Step 1: Fetching market sentiment...")
    try:
        sentiment_data = await news_analyzer.get_sentiment_for_signal(
            symbol="NIFTY",
            signal_type="BUY"
        )
        
        print(f"✅ Sentiment: {sentiment_data.get('sentiment', 'neutral').upper()}")
        print(f"   Score: {sentiment_data.get('sentiment_score', 0)}")
        print(f"   Mood: {sentiment_data.get('market_mood', 'Unknown')}")
        print(f"   News Count: {sentiment_data.get('news_count', 0)}")
        print(f"   Data Source: {sentiment_data.get('data_source', 'unknown')}")
        print()
        
        if sentiment_data.get('latest_news'):
            print("📰 Latest News Headlines:")
            for i, news in enumerate(sentiment_data.get('latest_news', [])[:3], 1):
                print(f"   {i}. {news.get('title')}")
                print(f"      Sentiment: {news.get('sentiment')} | Source: {news.get('source')}")
            print()
        
    except Exception as e:
        print(f"⚠️ Could not fetch sentiment: {e}")
        sentiment_data = None
        print()
    
    # Step 2: Analyze NIFTY options
    print("📊 Step 2: Analyzing NIFTY option chain...")
    try:
        analyzer = get_index_analyzer(fyers_client)
        chain = analyzer.analyze_option_chain("NIFTY", "weekly")
        
        if chain:
            print(f"✅ NIFTY Analysis:")
            print(f"   Spot Price: ₹{chain.spot_price:,.2f}")
            print(f"   ATM Strike: {chain.atm_strike}")
            print(f"   Days to Expiry: {chain.days_to_expiry}")
            print(f"   Total Options: {len(chain.calls)} calls, {len(chain.puts)} puts")
            print()
            
            # Step 3: Score and rank options
            print("🎯 Step 3: Scoring options with sentiment boost...")
            
            options = []
            
            # Score CALL options
            for call in chain.calls[:10]:  # Top 10 strikes
                score = 50  # Base score
                
                # Add technical scoring
                if hasattr(call, 'ltp') and call.ltp > 0:
                    score += 10
                if hasattr(call, 'volume') and call.volume > 1000:
                    score += 15
                if hasattr(call, 'oi') and call.oi > 10000:
                    score += 10
                
                # Apply sentiment boost for CALLs if bullish
                if sentiment_data:
                    sentiment = sentiment_data.get('sentiment', 'neutral')
                    sentiment_score = sentiment_data.get('sentiment_score', 0)
                    
                    if sentiment == 'bullish':
                        boost = abs(sentiment_score) * 15  # Up to 15% boost
                        score = score * (1 + boost / 100)
                        call.sentiment_boost = True
                    elif sentiment == 'bearish':
                        reduction = abs(sentiment_score) * 10
                        score = score * (1 - reduction / 100)
                        call.sentiment_conflict = True
                
                call.final_score = score
                options.append({
                    'type': 'CALL',
                    'strike': call.strike,
                    'ltp': getattr(call, 'ltp', 0),
                    'volume': getattr(call, 'volume', 0),
                    'oi': getattr(call, 'oi', 0),
                    'score': score,
                    'sentiment_boost': getattr(call, 'sentiment_boost', False),
                    'sentiment_conflict': getattr(call, 'sentiment_conflict', False)
                })
            
            # Score PUT options
            for put in chain.puts[:10]:
                score = 50
                
                if hasattr(put, 'ltp') and put.ltp > 0:
                    score += 10
                if hasattr(put, 'volume') and put.volume > 1000:
                    score += 15
                if hasattr(put, 'oi') and put.oi > 10000:
                    score += 10
                
                # Apply sentiment boost for PUTs if bearish
                if sentiment_data:
                    sentiment = sentiment_data.get('sentiment', 'neutral')
                    sentiment_score = sentiment_data.get('sentiment_score', 0)
                    
                    if sentiment == 'bearish':
                        boost = abs(sentiment_score) * 15
                        score = score * (1 + boost / 100)
                        put.sentiment_boost = True
                    elif sentiment == 'bullish':
                        reduction = abs(sentiment_score) * 10
                        score = score * (1 - reduction / 100)
                        put.sentiment_conflict = True
                
                put.final_score = score
                options.append({
                    'type': 'PUT',
                    'strike': put.strike,
                    'ltp': getattr(put, 'ltp', 0),
                    'volume': getattr(put, 'volume', 0),
                    'oi': getattr(put, 'oi', 0),
                    'score': score,
                    'sentiment_boost': getattr(put, 'sentiment_boost', False),
                    'sentiment_conflict': getattr(put, 'sentiment_conflict', False)
                })
            
            # Sort by score
            options.sort(key=lambda x: x['score'], reverse=True)
            
            print(f"✅ Top 10 Options (with sentiment adjustments):")
            print()
            print(f"{'Rank':<5} {'Type':<6} {'Strike':<8} {'LTP':<10} {'Volume':<12} {'OI':<12} {'Score':<8} {'Sentiment'}")
            print("-" * 90)
            
            for i, opt in enumerate(options[:10], 1):
                sentiment_indicator = ""
                if opt['sentiment_boost']:
                    sentiment_indicator = "🟢 BOOST"
                elif opt['sentiment_conflict']:
                    sentiment_indicator = "🔴 CONFLICT"
                else:
                    sentiment_indicator = "⚪ NEUTRAL"
                
                print(f"{i:<5} {opt['type']:<6} {opt['strike']:<8} "
                      f"₹{opt['ltp']:<9,.2f} {opt['volume']:<12,} "
                      f"{opt['oi']:<12,} {opt['score']:<8.1f} {sentiment_indicator}")
            
            print()
            print("-" * 90)
            
            # Summary
            boosted_calls = sum(1 for o in options if o['type'] == 'CALL' and o.get('sentiment_boost'))
            boosted_puts = sum(1 for o in options if o['type'] == 'PUT' and o.get('sentiment_boost'))
            
            print("\n📊 Sentiment Impact Summary:")
            print(f"   CALL options boosted: {boosted_calls}")
            print(f"   PUT options boosted: {boosted_puts}")
            
            if sentiment_data:
                print(f"\n💡 Trading Recommendation:")
                print(f"   {sentiment_data.get('reason', 'No specific recommendation')}")
                print(f"   {sentiment_data.get('market_mood', '')}")
        
        else:
            print("⚠️ No option chain data available (mock data mode)")
            print("   This is normal if Fyers is not authenticated")
            
            # Show sentiment anyway
            if sentiment_data:
                print(f"\n✅ Market Sentiment: {sentiment_data.get('sentiment', 'neutral').upper()}")
                print(f"   Score: {sentiment_data.get('sentiment_score', 0)}")
                print(f"   Mood: {sentiment_data.get('market_mood', 'Unknown')}")
                
                if sentiment_data.get('sentiment') == 'bullish':
                    print("\n💡 Recommendation: Consider CALL options (bullish sentiment)")
                elif sentiment_data.get('sentiment') == 'bearish':
                    print("\n💡 Recommendation: Consider PUT options (bearish sentiment)")
                else:
                    print("\n💡 Recommendation: Mixed signals, trade carefully")
        
    except Exception as e:
        print(f"❌ Error analyzing options: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("✅ Scan Complete!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(scan_nifty_options())
