"""
News and Sentiment Analysis Module
Fetches market news and performs sentiment analysis
for trading signal enhancement.

This module integrates with news service (Tradient primary, Marketaux fallback)
and provides sentiment analysis for options/stock scanning signals.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
import re
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

# Try to import news service for real data
# Primary: Tradient (free, 50+ articles, pre-computed sentiment)
# Fallback: Marketaux (100 requests/day limit)
try:
    from src.services.tradient_news_service import tradient_news_service as news_service, TradientNewsService
    NEWS_SERVICE_AVAILABLE = True
    NEWS_SERVICE_TYPE = "tradient"
    logger.info("✅ Using Tradient news service for sentiment analysis")
except ImportError:
    try:
        from src.services.news_service import news_service, MarketauxNewsService
        NEWS_SERVICE_AVAILABLE = True
        NEWS_SERVICE_TYPE = "marketaux"
        logger.warning("⚠️ Using legacy Marketaux news service")
    except ImportError:
        NEWS_SERVICE_AVAILABLE = False
        NEWS_SERVICE_TYPE = None
        news_service = None
        logger.warning("News service not available. Using simulated data.")


@dataclass
class NewsItem:
    """Single news item"""
    title: str
    summary: str
    source: str
    timestamp: datetime
    url: str
    sentiment: str  # positive, negative, neutral
    sentiment_score: float  # -1 to 1
    relevance: float  # 0 to 1
    keywords: List[str]


@dataclass
class MarketSentiment:
    """Overall market sentiment analysis"""
    overall_sentiment: str
    sentiment_score: float
    bullish_count: int
    bearish_count: int
    neutral_count: int
    key_themes: List[str]
    market_mood: str
    trading_implication: str
    news_items: List[NewsItem]


class NewsSentimentAnalyzer:
    """
    Analyze news sentiment for market direction
    
    Sources:
    - Economic Times
    - Moneycontrol
    - Reuters India
    - NSE/BSE announcements
    """
    
    def __init__(self):
        # Sentiment keywords
        self.bullish_keywords = [
            "rally", "surge", "jump", "gain", "rise", "bullish", "buy",
            "strong", "growth", "profit", "beat", "exceed", "upgrade",
            "positive", "optimistic", "recovery", "expansion", "boost",
            "breakout", "new high", "outperform", "upside", "bull run"
        ]
        
        self.bearish_keywords = [
            "fall", "drop", "decline", "crash", "bearish", "sell",
            "weak", "loss", "miss", "below", "downgrade", "negative",
            "pessimistic", "recession", "contraction", "cut", "selloff",
            "breakdown", "new low", "underperform", "downside", "bear"
        ]
        
        self.neutral_keywords = [
            "flat", "unchanged", "steady", "stable", "mixed", "range",
            "consolidate", "wait", "hold", "sideways"
        ]
        
        # Market-moving event keywords
        self.event_keywords = [
            "rbi", "fed", "interest rate", "inflation", "gdp", "jobs",
            "election", "budget", "policy", "fomc", "mpc", "earnings",
            "results", "dividend", "bonus", "split", "merger", "acquisition",
            "fii", "dii", "institutional"
        ]
    
    def analyze_text_sentiment(self, text: str) -> tuple:
        """
        Analyze sentiment of text using keyword matching
        Returns (sentiment, score)
        """
        text_lower = text.lower()
        
        bullish_score = sum(1 for kw in self.bullish_keywords if kw in text_lower)
        bearish_score = sum(1 for kw in self.bearish_keywords if kw in text_lower)
        neutral_score = sum(1 for kw in self.neutral_keywords if kw in text_lower)
        
        total = bullish_score + bearish_score + neutral_score
        if total == 0:
            return "neutral", 0.0
        
        # Calculate weighted score
        score = (bullish_score - bearish_score) / max(total, 1)
        score = max(-1, min(1, score))  # Clamp to [-1, 1]
        
        if score > 0.2:
            sentiment = "positive"
        elif score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return sentiment, round(score, 2)
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        text_lower = text.lower()
        found = []
        
        for kw in self.event_keywords + self.bullish_keywords + self.bearish_keywords:
            if kw in text_lower:
                found.append(kw)
        
        return list(set(found))[:5]
    
    def get_simulated_news(self, symbol: str = None) -> List[NewsItem]:
        """
        Get simulated news data with dynamic timestamps
        In production, this would fetch from real news APIs
        """
        import random
        
        # Get current hour to make news relevant to current session
        current_hour = datetime.now().hour
        
        # Generate recent news (within last 1-6 hours)
        news_templates = [
            {
                "title": "Nifty {action} {points} points on {trigger}",
                "summary": "Indian benchmark index shows {sentiment} momentum driven by {sector} stocks and {flow} flows.",
                "source": "Economic Times"
            },
            {
                "title": "Bank Nifty {action} as Q4 earnings {result}",
                "summary": "Banking stocks show {sentiment} trend with major banks reporting {quality} results.",
                "source": "Moneycontrol"
            },
            {
                "title": "FII {flow_type} of Rs {amount} crore in {session} session",
                "summary": "Foreign institutional investors continue {trend} in Indian equities today.",
                "source": "BSE"
            },
            {
                "title": "India VIX {vix_action} to {level}, signaling {mood} market",
                "summary": "Volatility index at {period} levels indicating {interpretation} among traders.",
                "source": "NSE"
            },
            {
                "title": "IT stocks {action} on {trigger}",
                "summary": "Technology sector shows {sentiment} with major players {trend}.",
                "source": "Reuters"
            }
        ]
        
        # Dynamic values based on current time
        news_data = [
            {
                "title": news_templates[0]["title"].format(
                    action=random.choice(["gains", "advances", "rises", "jumps"]),
                    points=random.randint(50, 200),
                    trigger=random.choice(["IT sector strength", "FII buying", "global cues"])
                ),
                "summary": news_templates[0]["summary"].format(
                    sentiment=random.choice(["bullish", "positive", "strong"]),
                    sector=random.choice(["banking", "IT", "auto", "pharma"]),
                    flow=random.choice(["FII", "DII", "retail"])
                ),
                "source": "Economic Times",
                "hours_ago": random.uniform(0.5, 2.0)
            },
            {
                "title": news_templates[1]["title"].format(
                    action=random.choice(["rallies", "gains", "advances"]),
                    result=random.choice(["beat estimates", "exceed expectations", "show strength"])
                ),
                "summary": news_templates[1]["summary"].format(
                    sentiment=random.choice(["positive", "strong", "bullish"]),
                    quality=random.choice(["strong", "robust", "healthy"])
                ),
                "source": "Moneycontrol",
                "hours_ago": random.uniform(0.3, 1.5)
            },
            {
                "title": news_templates[2]["title"].format(
                    flow_type=random.choice(["net buyers", "inflows"]),
                    amount=random.randint(1000, 5000),
                    session=random.choice(["morning", "early", "opening"])
                ),
                "summary": news_templates[2]["summary"].format(
                    trend=random.choice(["buying spree", "accumulation", "positive stance"])
                ),
                "source": "BSE",
                "hours_ago": random.uniform(0.2, 3.0)
            },
            {
                "title": news_templates[3]["title"].format(
                    vix_action=random.choice(["drops", "falls", "declines"]),
                    level=random.randint(11, 14),
                    mood=random.choice(["calm", "stable", "confident"])
                ),
                "summary": news_templates[3]["summary"].format(
                    period=random.choice(["multi-week", "recent", "current"]),
                    interpretation=random.choice(["confidence", "lack of fear", "optimism"])
                ),
                "source": "NSE",
                "hours_ago": random.uniform(0.5, 4.0)
            },
            {
                "title": news_templates[4]["title"].format(
                    action=random.choice(["gain", "advance", "rally"]),
                    trigger=random.choice(["strong Q4 guidance", "AI optimism", "deal wins"])
                ),
                "summary": news_templates[4]["summary"].format(
                    sentiment=random.choice(["strength", "resilience", "momentum"]),
                    trend=random.choice(["gaining ground", "moving higher", "showing strength"])
                ),
                "source": "Reuters",
                "hours_ago": random.uniform(1.0, 5.0)
            }
        ]
        
        news_items = []
        for item in news_data:
            sentiment, score = self.analyze_text_sentiment(item["title"] + " " + item["summary"])
            keywords = self.extract_keywords(item["title"] + " " + item["summary"])
            
            news_items.append(NewsItem(
                title=item["title"],
                summary=item["summary"],
                source=item["source"],
                timestamp=datetime.now() - timedelta(hours=item["hours_ago"]),
                url=f"https://example.com/news/{item['hours_ago']}",
                sentiment=sentiment,
                sentiment_score=score,
                relevance=0.8 if symbol and symbol.upper() in item["title"].upper() else 0.5,
                keywords=keywords
            ))
        
        return news_items
    
    async def get_real_news_from_db(self, 
                                    symbol: str = None,
                                    hours: int = 4,
                                    indices: List[str] = None) -> List[NewsItem]:
        """
        Get real news from database (fetched from Marketaux API).
        Falls back to simulated news if database is empty or service unavailable.
        """
        if not NEWS_SERVICE_AVAILABLE or not news_service:
            logger.info("News service not available, using simulated data")
            return self.get_simulated_news(symbol)
        
        try:
            # Determine which indices to filter by
            filter_indices = indices
            if not filter_indices and symbol:
                symbol_upper = symbol.upper()
                if "NIFTY" in symbol_upper and "BANK" not in symbol_upper:
                    filter_indices = ["NIFTY"]
                elif "BANKNIFTY" in symbol_upper or "BANK" in symbol_upper:
                    filter_indices = ["BANKNIFTY"]
                elif "FINNIFTY" in symbol_upper or "FIN" in symbol_upper:
                    filter_indices = ["FINNIFTY"]
            
            # Fetch from database
            articles = await news_service.get_recent_news(
                hours=hours,
                indices=filter_indices,
                min_relevance=0.1,
                limit=20
            )
            
            if not articles:
                logger.info("No articles in database, using simulated data")
                return self.get_simulated_news(symbol)
            
            # Convert to NewsItem format
            news_items = []
            for article in articles:
                published = article.get("published_at", "")
                try:
                    if isinstance(published, str):
                        timestamp = datetime.fromisoformat(published.replace("Z", "+00:00"))
                        # Convert to local time for display
                        timestamp = timestamp.replace(tzinfo=None)
                    else:
                        timestamp = published
                except:
                    timestamp = datetime.now()
                
                news_items.append(NewsItem(
                    title=article.get("title", ""),
                    summary=article.get("description", "") or article.get("snippet", ""),
                    source=article.get("source", "Unknown"),
                    timestamp=timestamp,
                    url=article.get("url", ""),
                    sentiment=article.get("sentiment", "neutral"),
                    sentiment_score=float(article.get("sentiment_score", 0) or 0),
                    relevance=float(article.get("relevance_score", 0.5) or 0.5),
                    keywords=article.get("keywords", []) or []
                ))
            
            logger.info(f"📰 Retrieved {len(news_items)} real news articles from database")
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching news from DB: {e}")
            return self.get_simulated_news(symbol)
    
    async def analyze_market_sentiment_async(self, 
                                             symbol: str = None,
                                             use_real_data: bool = True) -> MarketSentiment:
        """
        Analyze overall market sentiment from news (async version with real data).
        
        Args:
            symbol: Optional symbol to filter news relevance
            use_real_data: If True, fetch from database; else use simulated
        
        Returns:
            MarketSentiment with analysis results
        """
        if use_real_data and NEWS_SERVICE_AVAILABLE:
            news_items = await self.get_real_news_from_db(symbol, hours=4)
        else:
            news_items = self.get_simulated_news(symbol)
        
        return self._compute_market_sentiment(news_items)
    
    def analyze_market_sentiment(self, symbol: str = None) -> MarketSentiment:
        """
        Analyze overall market sentiment from news (sync version).
        Uses simulated data for backward compatibility.
        For real data, use analyze_market_sentiment_async().
        """
        news_items = self.get_simulated_news(symbol)
        return self._compute_market_sentiment(news_items)
    
    def _compute_market_sentiment(self, news_items: List[NewsItem]) -> MarketSentiment:
        """
        Compute market sentiment from a list of news items.
        Extracted logic for reuse between sync and async methods.
        """
        if not news_items:
            return MarketSentiment(
                overall_sentiment="neutral",
                sentiment_score=0.0,
                bullish_count=0,
                bearish_count=0,
                neutral_count=0,
                key_themes=[],
                market_mood="No Data - Unable to Assess",
                trading_implication="Insufficient news data for sentiment analysis.",
                news_items=[]
            )
        
        # Count sentiments
        positive = sum(1 for n in news_items if n.sentiment == "positive")
        negative = sum(1 for n in news_items if n.sentiment == "negative")
        neutral = sum(1 for n in news_items if n.sentiment == "neutral")
        
        # Calculate overall score (weighted by recency)
        total_score = 0
        total_weight = 0
        now = datetime.now()
        
        for item in news_items:
            # Handle timezone-aware timestamps
            item_time = item.timestamp
            if item_time.tzinfo:
                item_time = item_time.replace(tzinfo=None)
            
            hours_ago = (now - item_time).total_seconds() / 3600
            weight = 1 / (1 + hours_ago / 24)  # Decay over 24 hours
            total_score += item.sentiment_score * weight * item.relevance
            total_weight += weight * item.relevance
        
        avg_score = total_score / max(total_weight, 0.001)
        
        # Determine overall sentiment
        if avg_score > 0.15:
            overall = "bullish"
        elif avg_score < -0.15:
            overall = "bearish"
        else:
            overall = "neutral"
        
        # Extract key themes
        all_keywords = []
        for item in news_items:
            all_keywords.extend(item.keywords)
        
        keyword_counts = {}
        for kw in all_keywords:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        
        key_themes = sorted(keyword_counts.keys(), key=lambda x: keyword_counts[x], reverse=True)[:5]
        
        # Market mood
        if avg_score > 0.3:
            mood = "Very Optimistic - Risk On"
        elif avg_score > 0.1:
            mood = "Optimistic - Cautious Buying"
        elif avg_score > -0.1:
            mood = "Neutral - Wait and Watch"
        elif avg_score > -0.3:
            mood = "Pessimistic - Cautious"
        else:
            mood = "Very Pessimistic - Risk Off"
        
        # Trading implication
        if overall == "bullish":
            implication = "Favor long positions. Buy on dips. Consider bullish option strategies."
        elif overall == "bearish":
            implication = "Favor short positions or hedges. Sell on rallies. Consider protective puts."
        else:
            implication = "Mixed signals. Trade both sides or stay flat. Range-bound strategies work."
        
        return MarketSentiment(
            overall_sentiment=overall,
            sentiment_score=round(avg_score, 2),
            bullish_count=positive,
            bearish_count=negative,
            neutral_count=neutral,
            key_themes=key_themes,
            market_mood=mood,
            trading_implication=implication,
            news_items=sorted(news_items, key=lambda x: x.timestamp, reverse=True)
        )
    
    def get_event_calendar(self) -> List[Dict]:
        """
        Get upcoming market events that could impact trading
        """
        events = [
            {
                "event": "RBI MPC Meeting",
                "date": "2026-02-05",
                "importance": "High",
                "expected_impact": "Interest rate decision affects banking stocks and bond yields",
                "symbols_affected": ["BANKNIFTY", "NIFTY"]
            },
            {
                "event": "US Fed FOMC Decision",
                "date": "2026-01-29",
                "importance": "High",
                "expected_impact": "Global markets sensitive to Fed policy changes",
                "symbols_affected": ["NIFTY", "IT stocks"]
            },
            {
                "event": "India GDP Data",
                "date": "2026-02-28",
                "importance": "Medium",
                "expected_impact": "Economic growth data influences market sentiment",
                "symbols_affected": ["NIFTY", "BANKNIFTY"]
            },
            {
                "event": "Monthly Expiry",
                "date": "2026-01-30",
                "importance": "High",
                "expected_impact": "High volatility expected. Max pain levels important.",
                "symbols_affected": ["All indices"]
            },
            {
                "event": "Weekly Expiry (NIFTY)",
                "date": "2026-01-23",
                "importance": "Medium",
                "expected_impact": "Theta decay accelerates. Pin risk near key strikes.",
                "symbols_affected": ["NIFTY"]
            },
            {
                "event": "Q3 Results - Major Banks",
                "date": "2026-01-20",
                "importance": "High",
                "expected_impact": "Bank results could drive BANKNIFTY direction",
                "symbols_affected": ["BANKNIFTY", "FINNIFTY"]
            }
        ]
        
        # Sort by date
        events.sort(key=lambda x: x["date"])
        
        # Add days until event
        for event in events:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d")
            days_until = (event_date - datetime.now()).days
            event["days_until"] = max(0, days_until)
            event["status"] = "Upcoming" if days_until > 0 else "Today" if days_until == 0 else "Past"
        
        return [e for e in events if e["days_until"] >= 0]
    
    async def get_sentiment_for_signal(self, 
                                       symbol: str = None,
                                       signal_type: str = None) -> Dict:
        """
        Get sentiment data specifically for signal enhancement.
        
        Args:
            symbol: The trading symbol (e.g., 'NIFTY', 'BANKNIFTY')
            signal_type: The base signal type ('BUY', 'SELL', 'HOLD')
        
        Returns:
            Dict with sentiment adjustment data
        """
        result = {
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "confidence_adjustment": 0.0,
            "signal_adjustment": None,
            "market_mood": "Unknown",
            "key_themes": [],
            "news_count": 0,
            "latest_news": [],
            "reason": "No sentiment data available",
            "data_source": "simulated"
        }
        
        try:
            # Try to get cached sentiment from database first
            if NEWS_SERVICE_AVAILABLE and news_service:
                cached = await news_service.get_market_sentiment(time_window="1hr")
                
                if cached:
                    result["sentiment"] = cached.get("overall_sentiment", "neutral")
                    result["sentiment_score"] = float(cached.get("sentiment_score", 0) or 0)
                    result["market_mood"] = cached.get("market_mood", "Unknown")
                    result["key_themes"] = cached.get("key_themes", [])
                    result["news_count"] = cached.get("total_articles", 0)
                    result["data_source"] = "real"
                    
                    # Get signal adjustment if signal_type provided
                    if signal_type:
                        adjusted, conf_adj, reason = news_service.get_sentiment_signal_adjustment(
                            signal_type, cached, weight=0.2
                        )
                        result["signal_adjustment"] = adjusted if adjusted != signal_type else None
                        result["confidence_adjustment"] = conf_adj
                        result["reason"] = reason
                    else:
                        result["reason"] = cached.get("trading_implication", "")
                    
                    # Get latest news items
                    news_items = await self.get_real_news_from_db(symbol, hours=2)
                    result["latest_news"] = [
                        {
                            "title": n.title,
                            "source": n.source,
                            "sentiment": n.sentiment,
                            "timestamp": n.timestamp.isoformat() if hasattr(n.timestamp, 'isoformat') else str(n.timestamp)
                        }
                        for n in news_items[:5]
                    ]
                    
                    return result
            
            # Fallback to local analysis with simulated data
            sentiment = await self.analyze_market_sentiment_async(symbol, use_real_data=False)
            result["sentiment"] = sentiment.overall_sentiment
            result["sentiment_score"] = sentiment.sentiment_score
            result["market_mood"] = sentiment.market_mood
            result["key_themes"] = sentiment.key_themes
            result["news_count"] = len(sentiment.news_items)
            result["reason"] = sentiment.trading_implication
            result["latest_news"] = [
                {
                    "title": n.title,
                    "source": n.source,
                    "sentiment": n.sentiment,
                    "timestamp": n.timestamp.isoformat() if hasattr(n.timestamp, 'isoformat') else str(n.timestamp)
                }
                for n in sentiment.news_items[:5]
            ]
            
            # Calculate confidence adjustment based on sentiment alignment
            if signal_type:
                score = sentiment.sentiment_score
                if signal_type == "BUY" and sentiment.overall_sentiment == "bullish":
                    result["confidence_adjustment"] = abs(score) * 20  # Up to 20% boost
                elif signal_type == "SELL" and sentiment.overall_sentiment == "bearish":
                    result["confidence_adjustment"] = abs(score) * 20
                elif signal_type == "BUY" and sentiment.overall_sentiment == "bearish":
                    result["confidence_adjustment"] = -abs(score) * 20
                    if abs(score) > 0.3:
                        result["signal_adjustment"] = "HOLD"
                elif signal_type == "SELL" and sentiment.overall_sentiment == "bullish":
                    result["confidence_adjustment"] = -abs(score) * 20
                    if abs(score) > 0.3:
                        result["signal_adjustment"] = "HOLD"
            
        except Exception as e:
            logger.error(f"Error getting sentiment for signal: {e}")
        
        return result
    
    def apply_sentiment_to_signal(self, 
                                  signal: Dict,
                                  sentiment_data: Dict,
                                  weight: float = 0.2) -> Dict:
        """
        Apply sentiment adjustment to a trading signal.
        
        Args:
            signal: The original signal dict (must have 'action' and 'confidence')
            sentiment_data: Data from get_sentiment_for_signal()
            weight: How much weight to give sentiment (0-1)
        
        Returns:
            Enhanced signal dict with sentiment integration
        """
        enhanced = signal.copy()
        
        # Add sentiment data to signal
        enhanced["sentiment"] = {
            "overall": sentiment_data.get("sentiment", "neutral"),
            "score": sentiment_data.get("sentiment_score", 0),
            "mood": sentiment_data.get("market_mood", "Unknown"),
            "themes": sentiment_data.get("key_themes", []),
            "news_count": sentiment_data.get("news_count", 0),
            "data_source": sentiment_data.get("data_source", "simulated")
        }
        
        # Adjust confidence
        original_confidence = enhanced.get("confidence", 50)
        adjustment = sentiment_data.get("confidence_adjustment", 0) * weight
        new_confidence = max(0, min(100, original_confidence + adjustment))
        enhanced["confidence"] = round(new_confidence, 1)
        enhanced["confidence_adjusted_by_sentiment"] = round(adjustment, 1)
        
        # Adjust action if sentiment strongly conflicts
        signal_adjustment = sentiment_data.get("signal_adjustment")
        if signal_adjustment and signal_adjustment != enhanced.get("action"):
            enhanced["original_action"] = enhanced.get("action")
            enhanced["action"] = signal_adjustment
            enhanced["sentiment_override"] = True
            enhanced["sentiment_override_reason"] = sentiment_data.get("reason", "")
        
        # Add recent news to signal
        enhanced["recent_news"] = sentiment_data.get("latest_news", [])[:3]
        
        return enhanced


# Singleton
news_analyzer = NewsSentimentAnalyzer()


# Utility function for async sentiment integration
async def get_sentiment_enhanced_signal(signal: Dict, symbol: str = None) -> Dict:
    """
    Convenience function to enhance a signal with sentiment data.
    
    Args:
        signal: Original trading signal
        symbol: Trading symbol for filtering relevant news
    
    Returns:
        Enhanced signal with sentiment integration
    """
    sentiment_data = await news_analyzer.get_sentiment_for_signal(
        symbol=symbol,
        signal_type=signal.get("action")
    )
    return news_analyzer.apply_sentiment_to_signal(signal, sentiment_data)
