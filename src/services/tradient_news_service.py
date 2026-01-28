"""
Tradient News Service
Fetches news from Tradient API (primary) with Marketaux fallback.
Provides pre-computed sentiment analysis for Indian stock market.

Tradient API: https://api.tradient.org/v1/api/market/news
- No rate limits (public API)
- Pre-computed sentiment (positive/negative/neutral)
- Rich stock metadata (NSE/BSE codes, sectors, market cap)
- 50+ articles per fetch

Fallback: Marketaux API if Tradient is unavailable
"""

import os
import logging
import httpx
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
import asyncio

from config.supabase_config import get_supabase_admin_client

logger = logging.getLogger(__name__)


@dataclass
class TradientArticle:
    """Parsed article from Tradient API"""
    article_id: str  # Unique ID from Tradient
    title: str
    text: str  # Short description
    sentiment: str  # positive, negative, neutral (pre-computed)
    category: str  # stocks, commodities, global, co_actions_results, ipo
    sub_category: str  # results, corporate_action, order&deals, normal_news
    published_at: datetime
    
    # Stock metadata
    stock_name: str = ""
    stock_symbol: str = ""  # sm_symbol
    isin_code: str = ""
    nse_scrip_code: int = 0
    bse_scrip_code: int = 0
    display_symbol: str = ""
    
    # Additional metadata
    sector_name: str = ""
    marketcap: str = ""  # Large Cap, Mid Cap, Small Cap
    market_cap_value: float = 0  # cd_mcap in crores
    
    # Computed fields
    source: str = "tradient"
    url: str = ""
    affected_indices: List[str] = field(default_factory=list)
    affected_sectors: List[str] = field(default_factory=list)


class TradientNewsService:
    """
    Service to fetch news from Tradient API and store in Supabase.
    Falls back to Marketaux if Tradient is unavailable.
    
    Focus: Indian stock market news with pre-computed sentiment
    - NSE/BSE stock-specific news
    - Corporate actions (results, dividends, board meetings)
    - IPO updates
    - Commodity markets
    - Global market impact
    """
    
    # Tradient API configuration
    TRADIENT_API_URL = "https://api.tradient.org/v1/api/market/news"
    TRADIENT_TIMEOUT = 30  # seconds
    
    # Marketaux fallback configuration
    MARKETAUX_API_URL = "https://api.marketaux.com/v1/news/all"
    MARKETAUX_TIMEOUT = 15
    
    # Sector mappings for index impact
    SECTOR_TO_INDEX = {
        "Banks": "BANKNIFTY",
        "Banking": "BANKNIFTY",
        "IT - Software": "NIFTY",
        "Pharmaceuticals": "NIFTY",
        "Oil & Gas": "NIFTY",
        "Cement": "NIFTY",
        "Auto": "NIFTY",
        "Metals": "NIFTY",
        "FMCG": "NIFTY",
        "Realty": "NIFTY",
        "Power Generation & Distribution": "NIFTY",
        "Insurance": "FINNIFTY",
        "NBFC": "FINNIFTY",
        "Financial Services": "FINNIFTY",
    }
    
    # Category importance for filtering
    HIGH_PRIORITY_CATEGORIES = ["stocks", "co_actions_results", "ipo"]
    MEDIUM_PRIORITY_CATEGORIES = ["commodities", "global"]
    
    def __init__(self, marketaux_api_key: Optional[str] = None):
        """Initialize with optional Marketaux fallback key"""
        self.marketaux_api_key = marketaux_api_key or os.getenv("MARKETAUX_API_KEY")
        self.supabase = get_supabase_admin_client()
        self._last_fetch_time = None
        self._consecutive_failures = 0
        self._using_fallback = False
    
    async def fetch_from_tradient(self) -> Tuple[List[TradientArticle], bool]:
        """
        Fetch news from Tradient API.
        
        Returns:
            (list of articles, success flag)
        """
        try:
            logger.info("📰 Fetching news from Tradient API...")
            
            async with httpx.AsyncClient(timeout=self.TRADIENT_TIMEOUT) as client:
                response = await client.get(self.TRADIENT_API_URL)
                
                if response.status_code != 200:
                    logger.warning(f"⚠️ Tradient API returned status {response.status_code}")
                    return [], False
                
                data = response.json()
                
                if data.get("status") != 200:
                    logger.warning(f"⚠️ Tradient API error: {data.get('message')}")
                    return [], False
                
                articles = []
                latest_news = data.get("data", {}).get("latest_news", [])
                
                for item in latest_news:
                    try:
                        article = self._parse_tradient_article(item)
                        if article:
                            articles.append(article)
                    except Exception as e:
                        logger.error(f"Error parsing Tradient article: {e}")
                        continue
                
                logger.info(f"✅ Fetched {len(articles)} articles from Tradient")
                self._consecutive_failures = 0
                self._using_fallback = False
                return articles, True
                
        except httpx.TimeoutException:
            logger.error("⏱️ Tradient API timeout")
            self._consecutive_failures += 1
            return [], False
            
        except Exception as e:
            logger.error(f"❌ Tradient API error: {e}")
            self._consecutive_failures += 1
            return [], False
    
    def _parse_tradient_article(self, item: Dict) -> Optional[TradientArticle]:
        """Parse a single article from Tradient API response"""
        news_obj = item.get("news_object", {})
        metadata = item.get("metadata", {}) or {}
        
        # Required fields
        article_id = str(item.get("article_id", ""))
        title = news_obj.get("title", "")
        text = news_obj.get("text", "")
        sentiment = news_obj.get("overall_sentiment", "neutral")
        
        if not article_id or not title:
            return None
        
        # Parse timestamp (milliseconds to datetime)
        publish_timestamp = item.get("publish_date", 0)
        if publish_timestamp:
            published_at = datetime.fromtimestamp(publish_timestamp / 1000, tz=timezone.utc)
        else:
            published_at = datetime.now(timezone.utc)
        
        # Stock metadata
        stock_name = item.get("stock_name", "") or ""
        stock_symbol = item.get("sm_symbol", "") or ""
        isin_code = item.get("isin_code", "") or ""
        nse_scrip_code = item.get("nse_scrip_code", 0) or 0
        bse_scrip_code = item.get("bse_scrip_code", 0) or 0
        display_symbol = item.get("display_symbol", "") or ""
        
        # Additional metadata
        sector_name = metadata.get("sector_name", "") or ""
        marketcap = metadata.get("marketcap", "") or ""
        market_cap_value = metadata.get("cd_mcap", 0) or 0
        
        # Category info
        category = item.get("category", "stocks") or "stocks"
        sub_category = item.get("sub_category", "normal_news") or "normal_news"
        
        # Build article URL
        article_slug = item.get("article_slug", "")
        url = f"https://tradient.org/news/{article_slug}" if article_slug else ""
        
        # Determine affected indices based on sector
        affected_indices = []
        if sector_name:
            index = self.SECTOR_TO_INDEX.get(sector_name)
            if index:
                affected_indices.append(index)
        
        # If no specific index, check if it's a general market news
        if not affected_indices and category in ["stocks", "co_actions_results"]:
            affected_indices.append("NIFTY")
        
        # Affected sectors (from sector_name)
        affected_sectors = [sector_name.lower()] if sector_name else []
        
        return TradientArticle(
            article_id=f"tradient_{article_id}",
            title=title,
            text=text,
            sentiment=sentiment,
            category=category,
            sub_category=sub_category,
            published_at=published_at,
            stock_name=stock_name,
            stock_symbol=stock_symbol,
            isin_code=isin_code,
            nse_scrip_code=nse_scrip_code,
            bse_scrip_code=bse_scrip_code,
            display_symbol=display_symbol,
            sector_name=sector_name,
            marketcap=marketcap,
            market_cap_value=market_cap_value,
            source="tradient",
            url=url,
            affected_indices=affected_indices,
            affected_sectors=affected_sectors
        )
    
    async def fetch_from_marketaux_fallback(self) -> Tuple[List[TradientArticle], bool]:
        """
        Fallback to Marketaux API if Tradient is unavailable.
        
        Returns:
            (list of articles in TradientArticle format, success flag)
        """
        if not self.marketaux_api_key:
            logger.warning("⚠️ Marketaux API key not available for fallback")
            return [], False
        
        try:
            logger.info("🔄 Falling back to Marketaux API...")
            self._using_fallback = True
            
            params = {
                "api_token": self.marketaux_api_key,
                "countries": "in",
                "filter_entities": "true",
                "language": "en",
                "limit": 10
            }
            
            async with httpx.AsyncClient(timeout=self.MARKETAUX_TIMEOUT) as client:
                response = await client.get(self.MARKETAUX_API_URL, params=params)
                
                if response.status_code != 200:
                    logger.warning(f"⚠️ Marketaux API returned status {response.status_code}")
                    return [], False
                
                data = response.json()
                articles = []
                
                for item in data.get("data", []):
                    try:
                        article = self._parse_marketaux_article(item)
                        if article:
                            articles.append(article)
                    except Exception as e:
                        logger.error(f"Error parsing Marketaux article: {e}")
                        continue
                
                logger.info(f"✅ Fetched {len(articles)} articles from Marketaux (fallback)")
                return articles, True
                
        except Exception as e:
            logger.error(f"❌ Marketaux fallback error: {e}")
            return [], False
    
    def _parse_marketaux_article(self, item: Dict) -> Optional[TradientArticle]:
        """Parse Marketaux article into TradientArticle format for compatibility"""
        article_uuid = item.get("uuid", "")
        title = item.get("title", "")
        description = item.get("description", "") or ""
        
        if not article_uuid or not title:
            return None
        
        # Parse timestamp
        published_str = item.get("published_at", "")
        try:
            published_at = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
        except:
            published_at = datetime.now(timezone.utc)
        
        # Compute sentiment from description
        sentiment, _ = self._analyze_sentiment(f"{title} {description}")
        
        # Get source info
        source_name = item.get("source", "Unknown")
        source_domain = item.get("source_domain", "")
        url = item.get("url", "")
        
        return TradientArticle(
            article_id=f"marketaux_{article_uuid}",
            title=title,
            text=description[:500] if description else "",
            sentiment=sentiment,
            category="stocks",
            sub_category="normal_news",
            published_at=published_at,
            source=f"marketaux:{source_name}",
            url=url,
            affected_indices=["NIFTY"],  # Default for India news
            affected_sectors=[]
        )
    
    def _analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Simple sentiment analysis for fallback"""
        text_lower = text.lower()
        
        bullish_keywords = [
            "rally", "surge", "jump", "gain", "rise", "bullish", "buy", "strong", "growth",
            "profit", "beat", "exceed", "upgrade", "positive", "optimistic", "recovery"
        ]
        
        bearish_keywords = [
            "fall", "drop", "decline", "crash", "bearish", "sell", "weak", "loss", "miss",
            "below", "downgrade", "negative", "pessimistic", "recession", "contraction"
        ]
        
        bullish_count = sum(1 for kw in bullish_keywords if kw in text_lower)
        bearish_count = sum(1 for kw in bearish_keywords if kw in text_lower)
        
        if bullish_count > bearish_count:
            return "positive", 0.5
        elif bearish_count > bullish_count:
            return "negative", -0.5
        else:
            return "neutral", 0.0
    
    async def fetch_and_store_news(self) -> int:
        """
        Main method to fetch news and store in database.
        Tries Tradient first, falls back to Marketaux if needed.
        
        Returns:
            Number of articles stored
        """
        logger.info("🔄 Starting news fetch (Tradient primary, Marketaux fallback)...")
        
        # Try Tradient first
        articles, success = await self.fetch_from_tradient()
        
        # Fallback to Marketaux if Tradient fails
        if not success or len(articles) == 0:
            logger.warning("⚠️ Tradient unavailable, trying Marketaux fallback...")
            articles, success = await self.fetch_from_marketaux_fallback()
        
        if not articles:
            logger.warning("⚠️ No articles fetched from any source")
            return 0
        
        # Store articles
        stored = await self.store_articles(articles)
        
        # Update sentiment cache
        await self.update_sentiment_cache()
        
        # Log fetch
        await self._log_fetch(
            articles_count=stored,
            status_code=200 if success else 500,
            error=None if success else "Both APIs failed",
            source="tradient" if not self._using_fallback else "marketaux"
        )
        
        self._last_fetch_time = datetime.now(timezone.utc)
        
        logger.info(f"✅ News fetch complete. {stored} articles stored. Source: {'Tradient' if not self._using_fallback else 'Marketaux (fallback)'}")
        
        return stored
    
    async def store_articles(self, articles: List[TradientArticle]) -> int:
        """Store articles in Supabase database"""
        if not articles:
            return 0
        
        stored = 0
        
        for article in articles:
            try:
                # Convert sentiment to score
                sentiment_score = 0.5 if article.sentiment == "positive" else (-0.5 if article.sentiment == "negative" else 0.0)
                
                # Compute relevance (higher for stock-specific news)
                relevance_score = 0.8 if article.stock_symbol else 0.5
                if article.category in self.HIGH_PRIORITY_CATEGORIES:
                    relevance_score = min(relevance_score + 0.2, 1.0)
                
                # Compute impact level
                if article.marketcap == "Large Cap" or article.category == "ipo":
                    impact_level = "high"
                elif article.marketcap == "Mid Cap" or article.category == "co_actions_results":
                    impact_level = "medium"
                else:
                    impact_level = "low"
                
                # Build data for insertion (compatible with existing schema)
                data = {
                    "article_uuid": article.article_id,
                    "title": article.title,
                    "description": article.text,
                    "snippet": article.text[:200] if article.text else None,
                    "source": article.source,
                    "source_domain": "tradient.org" if "tradient" in article.source else None,
                    "url": article.url,
                    "image_url": None,
                    "published_at": article.published_at.isoformat(),
                    "keywords": [article.category, article.sub_category, article.stock_symbol] if article.stock_symbol else [article.category, article.sub_category],
                    "entities": {
                        "stock_name": article.stock_name,
                        "stock_symbol": article.stock_symbol,
                        "isin_code": article.isin_code,
                        "nse_scrip_code": article.nse_scrip_code,
                        "bse_scrip_code": article.bse_scrip_code,
                        "sector_name": article.sector_name,
                        "marketcap": article.marketcap,
                        "market_cap_value": article.market_cap_value
                    },
                    "sentiment": article.sentiment,
                    "sentiment_score": sentiment_score,
                    "relevance_score": relevance_score,
                    "impact_level": impact_level,
                    "affected_indices": article.affected_indices,
                    "affected_sectors": article.affected_sectors,
                    "language": "en",
                    "countries": ["IN"]
                }
                
                # Upsert to avoid duplicates
                self.supabase.table("market_news").upsert(
                    data,
                    on_conflict="article_uuid"
                ).execute()
                
                stored += 1
                
            except Exception as e:
                logger.error(f"Error storing article {article.article_id}: {e}")
        
        logger.info(f"💾 Stored {stored}/{len(articles)} articles in database")
        return stored
    
    async def _log_fetch(self, articles_count: int, status_code: int, error: Optional[str], source: str):
        """Log the fetch attempt"""
        try:
            self.supabase.table("news_fetch_log").insert({
                "articles_fetched": articles_count,
                "api_response_code": status_code,
                "error_message": error,
                "query_params": {"source": source, "fallback": self._using_fallback},
                "credits_remaining": None
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log fetch: {e}")
    
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
                
                # Calculate average sentiment score
                scores = [a.get("sentiment_score", 0) or 0 for a in articles]
                avg_score = sum(scores) / len(scores) if scores else 0
                
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
                        if kw:
                            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
                
                top_keywords = dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10])
                
                # Calculate sector sentiment
                sector_scores = {}
                for article in articles:
                    for sector in (article.get("affected_sectors") or []):
                        if sector:
                            if sector not in sector_scores:
                                sector_scores[sector] = []
                            sector_scores[sector].append(article.get("sentiment_score", 0) or 0)
                
                sector_sentiment = {
                    sector: round(sum(scores) / len(scores), 3) if scores else 0
                    for sector, scores in sector_scores.items()
                }
                
                # Calculate index sentiment
                nifty_articles = [a for a in articles if "NIFTY" in (a.get("affected_indices") or [])]
                banknifty_articles = [a for a in articles if "BANKNIFTY" in (a.get("affected_indices") or [])]
                
                nifty_sentiment = sum(a.get("sentiment_score", 0) or 0 for a in nifty_articles) / max(len(nifty_articles), 1)
                banknifty_sentiment = sum(a.get("sentiment_score", 0) or 0 for a in banknifty_articles) / max(len(banknifty_articles), 1)
                
                # Generate market mood and trading implications
                market_mood = self._generate_market_mood(overall, avg_score, positive, negative, total)
                trading_implication = self._generate_trading_implication(overall, avg_score, nifty_sentiment, banknifty_sentiment)
                
                # Upsert to cache
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
                    "nifty_sentiment": round(nifty_sentiment, 3),
                    "banknifty_sentiment": round(banknifty_sentiment, 3),
                    "sector_sentiment": sector_sentiment,
                    "market_mood": market_mood,
                    "trading_implication": trading_implication,
                    "computed_at": now.isoformat()
                }
                
                # Delete old cache for this window and insert new
                self.supabase.table("market_sentiment_cache").delete().eq(
                    "time_window", window_name
                ).execute()
                
                self.supabase.table("market_sentiment_cache").insert(cache_data).execute()
                
            logger.info("✅ Sentiment cache updated")
            
        except Exception as e:
            logger.error(f"Error updating sentiment cache: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _generate_market_mood(self, overall: str, score: float, positive: int, negative: int, total: int) -> str:
        """Generate human-readable market mood"""
        if overall == "bullish":
            if score > 0.4:
                return "Strong bullish sentiment - Markets showing optimism"
            else:
                return "Mild bullish sentiment - Cautiously optimistic"
        elif overall == "bearish":
            if score < -0.4:
                return "Strong bearish sentiment - Markets showing concern"
            else:
                return "Mild bearish sentiment - Some caution in markets"
        else:
            return "Neutral sentiment - Markets in wait-and-watch mode"
    
    def _generate_trading_implication(self, overall: str, score: float, nifty: float, banknifty: float) -> str:
        """Generate trading implication based on sentiment"""
        implications = []
        
        if overall == "bullish":
            implications.append("Consider long positions on dips")
        elif overall == "bearish":
            implications.append("Consider hedging or reducing exposure")
        else:
            implications.append("Range-bound trading expected")
        
        if nifty > 0.2:
            implications.append("NIFTY sentiment positive")
        elif nifty < -0.2:
            implications.append("NIFTY sentiment negative")
        
        if banknifty > 0.2:
            implications.append("BANKNIFTY sentiment positive")
        elif banknifty < -0.2:
            implications.append("BANKNIFTY sentiment negative")
        
        return ". ".join(implications)
    
    async def get_recent_news(self,
                              hours: int = 4,
                              indices: List[str] = None,
                              sectors: List[str] = None,
                              min_relevance: float = 0.1,
                              limit: int = 20) -> List[Dict]:
        """
        Get recent news from database.
        Compatible with MarketauxNewsService interface for news_sentiment.py.
        
        Args:
            hours: How many hours back to fetch
            indices: Filter by affected indices (NIFTY, BANKNIFTY, FINNIFTY)
            sectors: Filter by affected sectors
            min_relevance: Minimum relevance score
            limit: Max articles to return
        
        Returns:
            List of article dicts
        """
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            query = self.supabase.table("market_news").select("*").gte(
                "published_at", cutoff.isoformat()
            ).gte("relevance_score", min_relevance).order("published_at", desc=True).limit(limit * 2)
            
            response = query.execute()
            articles = response.data or []
            
            # Filter by indices if specified
            if indices:
                filtered = []
                for article in articles:
                    article_indices = article.get("affected_indices") or []
                    if any(idx in article_indices for idx in indices):
                        filtered.append(article)
                articles = filtered
            
            # Filter by sectors if specified
            if sectors:
                filtered = []
                for article in articles:
                    article_sectors = article.get("affected_sectors") or []
                    if any(sector in article_sectors for sector in sectors):
                        filtered.append(article)
                articles = filtered
            
            return articles[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching recent news from DB: {e}")
            return []
    
    async def get_latest_news(self, 
                              limit: int = 20,
                              category: Optional[str] = None,
                              stock_symbol: Optional[str] = None) -> List[Dict]:
        """
        Get latest news from database.
        
        Args:
            limit: Max articles to return
            category: Filter by category (stocks, commodities, etc.)
            stock_symbol: Filter by stock symbol
        
        Returns:
            List of article dicts
        """
        try:
            query = self.supabase.table("market_news").select("*").order("published_at", desc=True).limit(limit)
            
            if category:
                # Filter by category in keywords
                pass  # Supabase array filtering is complex, handle in Python
            
            response = query.execute()
            articles = response.data or []
            
            # Apply filters in Python
            if category:
                articles = [a for a in articles if category in (a.get("keywords") or [])]
            
            if stock_symbol:
                articles = [
                    a for a in articles 
                    if stock_symbol.upper() in (a.get("entities", {}).get("stock_symbol", "") or "").upper()
                ]
            
            return articles[:limit]
            
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
                                        weight: float = 0.2) -> Tuple[str, float, str]:
        """
        Adjust trading signal based on sentiment.
        Compatible with existing scanner/screener integration.
        
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
                adjusted_signal = "HOLD"
        
        elif base_signal == "SELL" and overall == "bullish":
            confidence_adjustment = -weight * abs(score) * 100
            reason = f"⚠️ Bullish sentiment conflicts with sell signal. {mood}"
            if abs(score) > 0.3:
                adjusted_signal = "HOLD"
        
        else:
            reason = f"Neutral sentiment. {mood}"
        
        return adjusted_signal, round(confidence_adjustment, 1), reason
    
    def get_service_status(self) -> Dict:
        """Get current service status for health checks"""
        return {
            "primary_source": "tradient",
            "fallback_source": "marketaux" if self.marketaux_api_key else None,
            "using_fallback": self._using_fallback,
            "consecutive_failures": self._consecutive_failures,
            "last_fetch_time": self._last_fetch_time.isoformat() if self._last_fetch_time else None,
            "fallback_available": bool(self.marketaux_api_key)
        }


# Create singleton instance (replaces old news_service)
tradient_news_service = TradientNewsService()

# Alias for backward compatibility
news_service = tradient_news_service
