"""
Redis-based caching service for AI responses.
Minimizes API costs by caching common queries.
"""
import hashlib
import json
import redis
from typing import Optional
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)


class AICacheService:
    """
    Cache AI responses to minimize Cohere API costs.
    
    Strategy:
    - Key = hash(normalized_query + scan_id + time_bucket)
    - TTL = 30 minutes (configurable)
    - Query normalization for better cache hits
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", default_ttl: int = 1800):
        """
        Initialize cache service.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds (30 minutes)
        """
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            self.default_ttl = default_ttl
            logger.info(f"✅ AI Cache connected to Redis (TTL: {default_ttl}s)")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Using in-memory cache.")
            self.redis_client = None
            self._memory_cache = {}  # Fallback to in-memory
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize query for better cache hits.
        
        Normalization steps:
        1. Lowercase
        2. Remove punctuation
        3. Remove extra whitespace
        4. Remove common filler words
        
        Args:
            query: Original query
        
        Returns:
            Normalized query string
        """
        # Lowercase
        normalized = query.lower()
        
        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Remove filler words
        filler_words = ['the', 'is', 'are', 'this', 'that', 'a', 'an']
        words = normalized.split()
        words = [w for w in words if w not in filler_words]
        
        # Remove extra whitespace
        normalized = ' '.join(words)
        
        return normalized.strip()
    
    def _get_time_bucket(self, minutes: int = 10) -> str:
        """
        Get time bucket to group queries within a time window.
        
        Example: 10:07 AM and 10:13 AM both map to "2026-01-31-10-10"
        
        Args:
            minutes: Bucket size in minutes
        
        Returns:
            Time bucket string
        """
        now = datetime.utcnow()
        bucket_minute = (now.minute // minutes) * minutes
        bucket_time = now.replace(minute=bucket_minute, second=0, microsecond=0)
        return bucket_time.strftime("%Y-%m-%d-%H-%M")
    
    def _generate_cache_key(self, query: str, scan_id: Optional[str] = None) -> str:
        """
        Generate cache key from query and context.
        
        Args:
            query: User query
            scan_id: Optional scan ID for context
        
        Returns:
            MD5 hash as cache key
        """
        normalized_query = self._normalize_query(query)
        time_bucket = self._get_time_bucket(minutes=10)
        
        # Build key components
        key_parts = [normalized_query, time_bucket]
        if scan_id:
            key_parts.append(scan_id)
        
        key_string = "|".join(key_parts)
        
        # Generate MD5 hash
        hash_key = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"ai_cache:{hash_key}"
    
    async def get_cached_response(
        self,
        query: str,
        scan_id: Optional[str] = None
    ) -> Optional[dict]:
        """
        Retrieve cached AI response if available.
        
        Args:
            query: User query
            scan_id: Optional scan ID
        
        Returns:
            Cached response dict or None
        """
        cache_key = self._generate_cache_key(query, scan_id)
        
        try:
            if self.redis_client:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    logger.info(f"✅ Cache HIT for query: {query[:50]}...")
                    return json.loads(cached_data)
            else:
                # Fallback to memory cache
                if cache_key in self._memory_cache:
                    cached_item = self._memory_cache[cache_key]
                    if cached_item['expires_at'] > datetime.utcnow():
                        logger.info(f"✅ Memory cache HIT for query: {query[:50]}...")
                        return cached_item['data']
                    else:
                        # Expired, remove it
                        del self._memory_cache[cache_key]
            
            logger.info(f"❌ Cache MISS for query: {query[:50]}...")
            return None
        
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    async def cache_response(
        self,
        query: str,
        response: dict,
        scan_id: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store AI response in cache.
        
        Args:
            query: User query
            response: AI response dictionary
            scan_id: Optional scan ID
            ttl: Time-to-live in seconds (uses default if None)
        
        Returns:
            True if cached successfully
        """
        cache_key = self._generate_cache_key(query, scan_id)
        ttl = ttl or self.default_ttl
        
        try:
            # Add metadata
            cache_data = {
                **response,
                "cached_at": datetime.utcnow().isoformat(),
                "query": query,
                "scan_id": scan_id
            }
            
            if self.redis_client:
                self.redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(cache_data)
                )
            else:
                # Fallback to memory cache
                self._memory_cache[cache_key] = {
                    'data': cache_data,
                    'expires_at': datetime.utcnow() + timedelta(seconds=ttl)
                }
            
            logger.info(f"💾 Cached response for query: {query[:50]}... (TTL: {ttl}s)")
            return True
        
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            return False
    
    def clear_cache(self, pattern: str = "ai_cache:*") -> int:
        """
        Clear cached responses matching pattern.
        
        Args:
            pattern: Redis key pattern
        
        Returns:
            Number of keys deleted
        """
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_client.delete(*keys)
                    logger.info(f"🗑️ Cleared {deleted} cached responses")
                    return deleted
            else:
                # Clear memory cache
                count = len(self._memory_cache)
                self._memory_cache.clear()
                logger.info(f"🗑️ Cleared {count} memory cached responses")
                return count
            
            return 0
        
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        try:
            if self.redis_client:
                info = self.redis_client.info("stats")
                keys_count = len(self.redis_client.keys("ai_cache:*"))
                
                return {
                    "total_keys": keys_count,
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "hit_rate": self._calculate_hit_rate(
                        info.get("keyspace_hits", 0),
                        info.get("keyspace_misses", 0)
                    )
                }
            else:
                return {
                    "total_keys": len(self._memory_cache),
                    "backend": "in-memory",
                    "note": "Limited stats available for in-memory cache"
                }
        
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Global cache instance
try:
    ai_cache = AICacheService()
except Exception as e:
    logger.warning(f"Failed to initialize AI cache: {e}")
    ai_cache = None
