"""
Marketaux News Service
Fetches news from Marketaux API and stores in Supabase for sentiment analysis.

Rate Limits:
- 100 requests per day
- 3 articles per request (free tier)
- Fetch every 15 minutes = ~96 requests/day (safe margin)

API Documentation: https://www.marketaux.com/documentation
"""

import os
import logging
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
import json
import asyncio

from config.supabase_config import get_supabase_admin_client

logger = logging.getLogger(__name__)


@dataclass
class MarketauxArticle:
    """Parsed article from Marketaux API"""
    article_uuid: str
    title: str
    description: Optional[str]
    snippet: Optional[str]
    source: str
    source_domain: Optional[str]
    url: str
    image_url: Optional[str]
    published_at: datetime
    keywords: List[str]
    entities: Dict
    sentiment: str
    sentiment_score: float
    relevance_score: float
    impact_level: str
    affected_indices: List[str]
    affected_sectors: List[str]
    language: str
    countries: List[str]


class MarketauxNewsService:
    """
    Service to fetch news from Marketaux API and store in Supabase.
    
    Focus: Indian stock market news
    - NSE/BSE related news
    - RBI, SEBI announcements
    - FII/DII activity
    - Major index movements (NIFTY, BANKNIFTY)
    - Sector-specific news
    """
    
    # Marketaux API configuration
    BASE_URL = "https://api.marketaux.com/v1/news/all"
    
    # Rate limiting
    MAX_REQUESTS_PER_DAY = 100
    ARTICLES_PER_REQUEST = 3  # Free tier limit
    
    # Indian market keywords for filtering
    INDIA_KEYWORDS = [
        "india", "nifty", "sensex", "bse", "nse", "rbi", "sebi", 
        "rupee", "inr", "mumbai", "indian", "fii", "dii",
        "reliance", "tcs", "infosys", "hdfc", "icici", "sbi",
        "nifty50", "banknifty", "finnifty", "midcap", "smallcap"
    ]
    
    # Sector mappings
    SECTOR_KEYWORDS = {
        "banking": ["bank", "banking", "hdfc", "icici", "sbi", "kotak", "axis", "pnb", "rbi", "credit", "loan", "npa"],
        "it": ["it", "tech", "software", "tcs", "infosys", "wipro", "hcl", "techm", "digital", "ai", "cloud"],
        "pharma": ["pharma", "drug", "medicine", "sunpharma", "cipla", "drreddy", "biocon", "healthcare", "hospital"],
        "auto": ["auto", "car", "vehicle", "tata motors", "maruti", "mahindra", "bajaj", "hero", "ev", "electric vehicle"],
        "oil": ["oil", "gas", "petroleum", "reliance", "ongc", "bpcl", "ioc", "crude", "fuel"],
        "metal": ["metal", "steel", "iron", "tata steel", "jsw", "hindalco", "vedanta", "copper", "aluminium"],
        "fmcg": ["fmcg", "consumer", "hul", "itc", "nestle", "britannia", "dabur", "marico"],
        "realty": ["realty", "real estate", "property", "dlf", "godrej", "sobha", "housing"],
        "infra": ["infra", "infrastructure", "construction", "l&t", "adani", "power", "road", "railway"],
        "telecom": ["telecom", "airtel", "jio", "vodafone", "5g", "spectrum", "broadband"]
    }
    
    # Index keywords
    INDEX_KEYWORDS = {
        "NIFTY": ["nifty", "nifty50", "nifty 50", "sensex", "index", "benchmark"],
        "BANKNIFTY": ["banknifty", "bank nifty", "banking index", "bank index", "psu bank", "private bank"],
        "FINNIFTY": ["finnifty", "financial", "nbfc", "insurance", "fin nifty"]
    }
    
    # Sentiment keywords for scoring
    BULLISH_KEYWORDS = [
        "rally", "surge", "jump", "gain", "rise", "bullish", "buy", "strong", "growth",
        "profit", "beat", "exceed", "upgrade", "positive", "optimistic", "recovery",
        "expansion", "boost", "breakout", "high", "outperform", "upside", "bull",
        "inflow", "accumulation", "buying", "support", "momentum"
    ]
    
    BEARISH_KEYWORDS = [
        "fall", "drop", "decline", "crash", "bearish", "sell", "weak", "loss", "miss",
        "below", "downgrade", "negative", "pessimistic", "recession", "contraction",
        "cut", "selloff", "breakdown", "low", "underperform", "downside", "bear",
        "outflow", "selling", "resistance", "correction", "slump", "plunge"
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key"""
        self.api_key = api_key or os.getenv("MARKETAUX_API_KEY")
        
        if not self.api_key:
            logger.warning("⚠️ MARKETAUX_API_KEY not set. News fetching will be disabled.")
        
        self.supabase = get_supabase_admin_client()
        self._request_count_today = 0
        self._last_request_date = None
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        today = datetime.now(timezone.utc).date()
        
        if self._last_request_date != today:
            self._request_count_today = 0
            self._last_request_date = today
        
        if self._request_count_today >= self.MAX_REQUESTS_PER_DAY:
            logger.warning(f"⚠️ Rate limit reached: {self._request_count_today}/{self.MAX_REQUESTS_PER_DAY} requests today")
            return False
        
        return True
    
    def _increment_request_count(self):
        """Increment the request counter"""
        self._request_count_today += 1
        logger.info(f"📊 API requests today: {self._request_count_today}/{self.MAX_REQUESTS_PER_DAY}")
    
    def _analyze_sentiment(self, text: str) -> tuple[str, float]:
        """
        Analyze sentiment of text using keyword matching.
        Returns (sentiment, score) where score is -1 to 1
        """
        text_lower = text.lower()
        
        bullish_count = sum(1 for kw in self.BULLISH_KEYWORDS if kw in text_lower)
        bearish_count = sum(1 for kw in self.BEARISH_KEYWORDS if kw in text_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            return "neutral", 0.0
        
        # Calculate weighted score
        score = (bullish_count - bearish_count) / max(total, 1)
        score = max(-1.0, min(1.0, score))  # Clamp to [-1, 1]
        
        if score > 0.2:
            sentiment = "positive"
        elif score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return sentiment, round(score, 3)
    
    def _calculate_relevance(self, article: Dict) -> float:
        """Calculate relevance score for Indian market (0 to 1)"""
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        
        # Count India-related keywords
        india_matches = sum(1 for kw in self.INDIA_KEYWORDS if kw in text)
        
        # Check if any Indian entities mentioned
        entities = article.get("entities", []) or []
        indian_entities = sum(1 for e in entities if e.get("country") == "IN")
        
        # Calculate score
        keyword_score = min(india_matches / 5, 1.0)  # Max out at 5 keywords
        entity_score = min(indian_entities / 2, 1.0)  # Max out at 2 entities
        
        relevance = (keyword_score * 0.6) + (entity_score * 0.4)
        return round(min(relevance * 1.5, 1.0), 3)  # Boost but cap at 1.0
    
    def _identify_affected_indices(self, text: str) -> List[str]:
        """Identify which indices are affected by the news"""
        text_lower = text.lower()
        affected = []
        
        for index, keywords in self.INDEX_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                affected.append(index)
        
        # If no specific index found but it's India market news, add NIFTY
        if not affected and any(kw in text_lower for kw in self.INDIA_KEYWORDS):
            affected.append("NIFTY")
        
        return affected
    
    def _identify_affected_sectors(self, text: str) -> List[str]:
        """Identify which sectors are affected by the news"""
        text_lower = text.lower()
        affected = []
        
        for sector, keywords in self.SECTOR_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                affected.append(sector)
        
        return affected
    
    def _determine_impact_level(self, article: Dict, sentiment_score: float, relevance: float) -> str:
        """Determine the market impact level of the news"""
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        
        # High impact keywords
        high_impact_keywords = [
            "rbi", "fed", "rate", "policy", "election", "budget", "gdp", "inflation",
            "fii", "crash", "rally", "major", "significant", "breaking", "urgent",
            "sebi", "government", "regulatory", "ban", "approval"
        ]
        
        high_impact_count = sum(1 for kw in high_impact_keywords if kw in text)
        
        # Calculate impact score
        impact_score = (
            abs(sentiment_score) * 0.3 +
            relevance * 0.3 +
            min(high_impact_count / 3, 1.0) * 0.4
        )
        
        if impact_score >= 0.6:
            return "high"
        elif impact_score >= 0.3:
            return "medium"
        else:
            return "low"
    
    def _parse_article(self, article: Dict) -> Optional[MarketauxArticle]:
        """Parse API response into MarketauxArticle based on Marketaux API format"""
        try:
            # Extract basic info
            uuid = article.get("uuid")
            if not uuid:
                return None
            
            title = article.get("title", "")
            description = article.get("description", "")
            full_text = f"{title} {description}"
            
            # Parse published date (format: "2026-01-23T00:55:39.000000Z")
            published_str = article.get("published_at", "")
            try:
                # Handle the microseconds format
                if ".000000Z" in published_str:
                    published_str = published_str.replace(".000000Z", "+00:00")
                elif "Z" in published_str:
                    published_str = published_str.replace("Z", "+00:00")
                published_at = datetime.fromisoformat(published_str)
            except:
                published_at = datetime.now(timezone.utc)
            
            # Extract entities data
            entities = article.get("entities", []) or []
            
            # Try to get sentiment from entities first (more accurate from API)
            entity_sentiment_score = None
            for entity in entities:
                if entity.get("sentiment_score") is not None:
                    entity_sentiment_score = entity.get("sentiment_score")
                    break  # Use first entity's sentiment
            
            # Use entity sentiment if available, otherwise analyze ourselves
            if entity_sentiment_score is not None:
                sentiment_score = float(entity_sentiment_score)
                if sentiment_score > 0.2:
                    sentiment = "positive"
                elif sentiment_score < -0.2:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
            else:
                sentiment, sentiment_score = self._analyze_sentiment(full_text)
            
            # Calculate relevance (API returns null, so we calculate ourselves)
            relevance = self._calculate_relevance(article)
            
            # Identify affected indices and sectors
            affected_indices = self._identify_affected_indices(full_text)
            affected_sectors = self._identify_affected_sectors(full_text)
            
            # Determine impact level
            impact_level = self._determine_impact_level(article, sentiment_score, relevance)
            
            # Extract keywords - API may return empty string ""
            keywords_raw = article.get("keywords", "") or ""
            if isinstance(keywords_raw, str):
                if keywords_raw.strip():
                    keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
                else:
                    keywords = []
            else:
                keywords = keywords_raw
            
            # Extract countries from entities
            countries = []
            for entity in entities:
                country = entity.get("country")
                if country and country not in countries:
                    countries.append(country)
            
            # Extract source (may come as domain like "seekingalpha.com")
            source = article.get("source", "Unknown")
            source_domain = source  # Source IS the domain in this API
            
            return MarketauxArticle(
                article_uuid=uuid,
                title=title,
                description=description,
                snippet=article.get("snippet"),
                source=source,
                source_domain=source_domain,
                url=article.get("url", ""),
                image_url=article.get("image_url"),
                published_at=published_at,
                keywords=keywords[:10],  # Limit keywords
                entities={"entities": entities[:10]},  # Store as JSONB
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                relevance_score=relevance,
                impact_level=impact_level,
                affected_indices=affected_indices,
                affected_sectors=affected_sectors,
                language=article.get("language", "en"),
                countries=countries
            )
            
        except Exception as e:
            logger.error(f"Error parsing article: {e}")
            return None
    
    async def fetch_news(self, 
                        search_query: Optional[str] = None,
                        countries: str = "in",  # India by default
                        limit: int = 3) -> List[MarketauxArticle]:
        """
        Fetch news from Marketaux API.
        
        Args:
            search_query: Optional search keywords
            countries: Country codes (default: "in" for India)
            limit: Number of articles (max 3 for free tier)
        
        Returns:
            List of parsed articles
        """
        if not self.api_key:
            logger.warning("⚠️ No API key configured")
            return []
        
        if not self._check_rate_limit():
            return []
        
        # Build query parameters
        params = {
            "api_token": self.api_key,
            "countries": countries,
            "filter_entities": "true",
            "language": "en",
            "limit": min(limit, self.ARTICLES_PER_REQUEST)
        }
        
        # Add search query if provided
        if search_query:
            params["search"] = search_query
        
        # Add topics related to finance/markets
        params["topics"] = "business,finance"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                
                self._increment_request_count()
                
                if response.status_code != 200:
                    logger.error(f"❌ Marketaux API error: {response.status_code} - {response.text}")
                    await self._log_fetch(0, response.status_code, response.text, params)
                    return []
                
                data = response.json()
                articles = data.get("data", [])
                
                logger.info(f"📰 Fetched {len(articles)} articles from Marketaux")
                
                # Parse articles
                parsed = []
                for article in articles:
                    parsed_article = self._parse_article(article)
                    if parsed_article and parsed_article.relevance_score > 0.1:
                        parsed.append(parsed_article)
                
                # Log the fetch
                credits = data.get("meta", {}).get("credits_remaining")
                await self._log_fetch(len(parsed), response.status_code, None, params, credits)
                
                return parsed
                
        except Exception as e:
            logger.error(f"❌ Error fetching news: {e}")
            await self._log_fetch(0, 0, str(e), params)
            return []
    
    async def _log_fetch(self, 
                        articles_count: int, 
                        status_code: int, 
                        error: Optional[str],
                        params: Dict,
                        credits: Optional[int] = None):
        """Log the fetch attempt to database"""
        try:
            self.supabase.table("news_fetch_log").insert({
                "articles_fetched": articles_count,
                "api_response_code": status_code,
                "error_message": error,
                "query_params": params,
                "credits_remaining": credits
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log fetch: {e}")
    
    async def store_articles(self, articles: List[MarketauxArticle]) -> int:
        """
        Store articles in Supabase database.
        Uses upsert to avoid duplicates.
        
        Returns:
            Number of articles stored/updated
        """
        if not articles:
            return 0
        
        stored = 0
        
        for article in articles:
            try:
                # Convert to dict for insertion
                data = {
                    "article_uuid": article.article_uuid,
                    "title": article.title,
                    "description": article.description,
                    "snippet": article.snippet,
                    "source": article.source,
                    "source_domain": article.source_domain,
                    "url": article.url,
                    "image_url": article.image_url,
                    "published_at": article.published_at.isoformat(),
                    "keywords": article.keywords,
                    "entities": article.entities,
                    "sentiment": article.sentiment,
                    "sentiment_score": article.sentiment_score,
                    "relevance_score": article.relevance_score,
                    "impact_level": article.impact_level,
                    "affected_indices": article.affected_indices,
                    "affected_sectors": article.affected_sectors,
                    "language": article.language,
                    "countries": article.countries
                }
                
                # Upsert to avoid duplicates
                self.supabase.table("market_news").upsert(
                    data, 
                    on_conflict="article_uuid"
                ).execute()
                
                stored += 1
                
            except Exception as e:
                logger.error(f"Error storing article {article.article_uuid}: {e}")
        
        logger.info(f"💾 Stored {stored}/{len(articles)} articles in database")
        return stored
    
    async def fetch_and_store_news(self) -> int:
        """
        Main method to fetch news and store in database.
        Called by the scheduler every 15 minutes.
        
        Returns:
            Number of articles stored
        """
        logger.info("🔄 Starting scheduled news fetch...")
        
        total_stored = 0
        
        # Fetch general Indian market news
        articles = await self.fetch_news(countries="in", limit=3)
        total_stored += await self.store_articles(articles)
        
        # Small delay to avoid hitting rate limits too fast
        await asyncio.sleep(1)
        
        # Fetch with specific keywords for better coverage (alternate between queries)
        queries = [
            "nifty sensex market",
            "rbi sebi india stock",
            "fii dii investment india"
        ]
        
        # Use current minute to rotate queries (spread across the day)
        current_minute = datetime.now().minute
        query_index = (current_minute // 15) % len(queries)
        
        articles = await self.fetch_news(
            search_query=queries[query_index],
            countries="in,us",  # Include US for global impact
            limit=3
        )
        total_stored += await self.store_articles(articles)
        
        logger.info(f"✅ News fetch complete. Total articles stored: {total_stored}")
        
        # Update sentiment cache
        await self.update_sentiment_cache()
        
        return total_stored
    
    async def update_sentiment_cache(self):
        """Update the pre-computed sentiment aggregations"""
        try:
            now = datetime.now(timezone.utc)
            
            # Calculate sentiment for different time windows
            windows = [
                ("15min", timedelta(minutes=15)),
                ("1hr", timedelta(hours=1)),
                ("4hr", timedelta(hours=4)),
                ("1day", timedelta(days=1))
            ]
            
            for window_name, window_delta in windows:
                window_start = now - window_delta
                
                # Get articles in this window
                response = self.supabase.table("market_news").select("*").gte(
                    "published_at", window_start.isoformat()
                ).lte("published_at", now.isoformat()).execute()
                
                articles = response.data or []
                
                if not articles:
                    continue
                
                # Calculate aggregates
                total = len(articles)
                positive = sum(1 for a in articles if a.get("sentiment") == "positive")
                negative = sum(1 for a in articles if a.get("sentiment") == "negative")
                neutral = total - positive - negative
                
                # Weighted average sentiment score
                total_score = 0
                total_weight = 0
                
                for article in articles:
                    score = article.get("sentiment_score", 0) or 0
                    relevance = article.get("relevance_score", 0.5) or 0.5
                    
                    # Weight by recency and relevance
                    published = datetime.fromisoformat(article["published_at"].replace("Z", "+00:00"))
                    hours_ago = (now - published).total_seconds() / 3600
                    recency_weight = 1 / (1 + hours_ago / 24)
                    
                    weight = recency_weight * relevance
                    total_score += score * weight
                    total_weight += weight
                
                avg_score = total_score / max(total_weight, 0.001)
                
                # Determine overall sentiment
                if avg_score > 0.15:
                    overall = "bullish"
                elif avg_score < -0.15:
                    overall = "bearish"
                else:
                    overall = "neutral"
                
                # Extract top keywords
                keyword_counts = {}
                for article in articles:
                    for kw in (article.get("keywords") or []):
                        keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
                
                top_keywords = dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10])
                
                # Calculate sector sentiment
                sector_scores = {}
                for article in articles:
                    score = article.get("sentiment_score", 0) or 0
                    for sector in (article.get("affected_sectors") or []):
                        if sector not in sector_scores:
                            sector_scores[sector] = {"total": 0, "count": 0}
                        sector_scores[sector]["total"] += score
                        sector_scores[sector]["count"] += 1
                
                sector_sentiment = {
                    sector: round(data["total"] / data["count"], 3)
                    for sector, data in sector_scores.items()
                    if data["count"] > 0
                }
                
                # Market mood and trading implication
                if avg_score > 0.3:
                    mood = "Very Optimistic - Risk On"
                    implication = "Favor long positions. Consider bullish option strategies."
                elif avg_score > 0.1:
                    mood = "Optimistic - Cautious Buying"
                    implication = "Buy on dips. Look for quality setups."
                elif avg_score > -0.1:
                    mood = "Neutral - Wait and Watch"
                    implication = "Mixed signals. Range-bound strategies work best."
                elif avg_score > -0.3:
                    mood = "Pessimistic - Cautious"
                    implication = "Consider hedges. Sell on rallies."
                else:
                    mood = "Very Pessimistic - Risk Off"
                    implication = "Favor shorts or stay flat. Consider protective puts."
                
                # Upsert cache
                cache_data = {
                    "time_window": window_name,
                    "window_start": window_start.isoformat(),
                    "window_end": now.isoformat(),
                    "overall_sentiment": overall,
                    "sentiment_score": round(avg_score, 3),
                    "total_articles": total,
                    "positive_count": positive,
                    "negative_count": negative,
                    "neutral_count": neutral,
                    "top_keywords": top_keywords,
                    "key_themes": list(top_keywords.keys())[:5],
                    "sector_sentiment": sector_sentiment,
                    "market_mood": mood,
                    "trading_implication": implication,
                    "computed_at": now.isoformat()
                }
                
                self.supabase.table("market_sentiment_cache").upsert(
                    cache_data,
                    on_conflict="time_window,window_start"
                ).execute()
            
            logger.info("✅ Sentiment cache updated")
            
        except Exception as e:
            logger.error(f"Error updating sentiment cache: {e}")
    
    async def get_recent_news(self, 
                             hours: int = 4,
                             indices: Optional[List[str]] = None,
                             sectors: Optional[List[str]] = None,
                             min_relevance: float = 0.1,
                             limit: int = 20) -> List[Dict]:
        """
        Get recent news from database for analysis.
        
        Args:
            hours: How far back to look
            indices: Filter by affected indices
            sectors: Filter by affected sectors
            min_relevance: Minimum relevance score
            limit: Maximum number of articles
        
        Returns:
            List of news articles
        """
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            query = self.supabase.table("market_news").select("*").gte(
                "published_at", cutoff.isoformat()
            ).gte("relevance_score", min_relevance).order(
                "published_at", desc=True
            ).limit(limit)
            
            response = query.execute()
            articles = response.data or []
            
            # Filter by indices if specified
            if indices:
                articles = [
                    a for a in articles 
                    if any(idx in (a.get("affected_indices") or []) for idx in indices)
                ]
            
            # Filter by sectors if specified
            if sectors:
                articles = [
                    a for a in articles 
                    if any(sec in (a.get("affected_sectors") or []) for sec in sectors)
                ]
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching news from DB: {e}")
            return []
    
    async def get_market_sentiment(self, time_window: str = "1hr") -> Optional[Dict]:
        """
        Get cached market sentiment for a time window.
        
        Args:
            time_window: One of '15min', '1hr', '4hr', '1day'
        
        Returns:
            Cached sentiment data or None
        """
        try:
            response = self.supabase.table("market_sentiment_cache").select("*").eq(
                "time_window", time_window
            ).order("computed_at", desc=True).limit(1).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error fetching sentiment cache: {e}")
            return None
    
    def get_sentiment_signal_adjustment(self, 
                                        base_signal: str,
                                        sentiment_data: Dict,
                                        weight: float = 0.2) -> tuple[str, float, str]:
        """
        Adjust trading signal based on sentiment.
        
        Args:
            base_signal: Original signal ('BUY', 'SELL', 'HOLD')
            sentiment_data: Sentiment data from cache
            weight: How much weight to give sentiment (0-1)
        
        Returns:
            (adjusted_signal, confidence_adjustment, reason)
        """
        if not sentiment_data:
            return base_signal, 0, "No sentiment data available"
        
        overall = sentiment_data.get("overall_sentiment", "neutral")
        score = sentiment_data.get("sentiment_score", 0)
        mood = sentiment_data.get("market_mood", "")
        
        confidence_adjustment = 0
        reason = ""
        adjusted_signal = base_signal
        
        # Strong sentiment alignment boosts confidence
        if base_signal == "BUY" and overall == "bullish":
            confidence_adjustment = weight * abs(score) * 100
            reason = f"Bullish sentiment supports long position. {mood}"
        
        elif base_signal == "SELL" and overall == "bearish":
            confidence_adjustment = weight * abs(score) * 100
            reason = f"Bearish sentiment supports short position. {mood}"
        
        # Conflicting sentiment reduces confidence
        elif base_signal == "BUY" and overall == "bearish":
            confidence_adjustment = -weight * abs(score) * 100
            reason = f"⚠️ Bearish sentiment conflicts with buy signal. {mood}"
            if abs(score) > 0.3:
                adjusted_signal = "HOLD"  # Strong bearish overrides buy
        
        elif base_signal == "SELL" and overall == "bullish":
            confidence_adjustment = -weight * abs(score) * 100
            reason = f"⚠️ Bullish sentiment conflicts with sell signal. {mood}"
            if abs(score) > 0.3:
                adjusted_signal = "HOLD"  # Strong bullish overrides sell
        
        else:
            reason = f"Neutral sentiment. {mood}"
        
        return adjusted_signal, round(confidence_adjustment, 1), reason


# Singleton instance
news_service = MarketauxNewsService()
