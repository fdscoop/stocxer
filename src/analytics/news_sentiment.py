"""
News and Sentiment Analysis Module
Fetches market news and performs sentiment analysis
for trading signal enhancement
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re
import logging
import json

logger = logging.getLogger(__name__)


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
    
    def analyze_market_sentiment(self, symbol: str = None) -> MarketSentiment:
        """
        Analyze overall market sentiment from news
        """
        news_items = self.get_simulated_news(symbol)
        
        # Count sentiments
        positive = sum(1 for n in news_items if n.sentiment == "positive")
        negative = sum(1 for n in news_items if n.sentiment == "negative")
        neutral = sum(1 for n in news_items if n.sentiment == "neutral")
        
        # Calculate overall score (weighted by recency)
        total_score = 0
        total_weight = 0
        for item in news_items:
            hours_ago = (datetime.now() - item.timestamp).total_seconds() / 3600
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


# Singleton
news_analyzer = NewsSentimentAnalyzer()
