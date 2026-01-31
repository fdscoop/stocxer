"""
AI Cost Optimization Strategies
Reduces Cohere API costs through intelligent caching and query optimization.
"""

from typing import Dict, Any, Optional
import hashlib
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class QueryDeduplicator:
    """
    Deduplicates similar queries to avoid redundant API calls.
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.recent_queries: Dict[str, Dict[str, Any]] = {}
        
    def normalize_query(self, query: str) -> str:
        """Normalize query for comparison."""
        # Lowercase, remove extra spaces, common variations
        normalized = query.lower().strip()
        normalized = ' '.join(normalized.split())
        
        # Replace common variations
        replacements = {
            "what's": "what is",
            "can you": "please",
            "could you": "please",
            "explain to me": "explain",
            "tell me about": "explain",
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
            
        return normalized
    
    def get_query_hash(self, query: str, context_id: Optional[str] = None) -> str:
        """Generate hash for query + context."""
        normalized = self.normalize_query(query)
        hash_input = f"{normalized}:{context_id or 'global'}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def is_duplicate(self, query: str, context_id: Optional[str] = None, ttl_minutes: int = 10) -> Optional[Dict]:
        """
        Check if query is a duplicate of recent query.
        
        Returns cached response if found, None otherwise.
        """
        query_hash = self.get_query_hash(query, context_id)
        
        if query_hash in self.recent_queries:
            cached = self.recent_queries[query_hash]
            cached_time = cached.get('timestamp')
            
            # Check if cache is still valid
            if cached_time and datetime.now() - cached_time < timedelta(minutes=ttl_minutes):
                logger.info(f"✅ Query deduplication hit: {query[:50]}...")
                return cached.get('response')
        
        return None
    
    def cache_query(self, query: str, response: Dict, context_id: Optional[str] = None):
        """Cache query and response."""
        query_hash = self.get_query_hash(query, context_id)
        self.recent_queries[query_hash] = {
            'query': query,
            'response': response,
            'timestamp': datetime.now()
        }
        
        # Cleanup old entries (keep last 100)
        if len(self.recent_queries) > 100:
            oldest_keys = sorted(
                self.recent_queries.keys(),
                key=lambda k: self.recent_queries[k]['timestamp']
            )[:20]
            for key in oldest_keys:
                del self.recent_queries[key]


class ContextWindowOptimizer:
    """
    Optimizes context sent to AI to minimize token usage.
    """
    
    MAX_CONTEXT_TOKENS = 4000  # Conservative limit for Cohere
    AVG_CHARS_PER_TOKEN = 4    # Approximate
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count from text."""
        return len(text) // ContextWindowOptimizer.AVG_CHARS_PER_TOKEN
    
    @staticmethod
    def truncate_context(context: str, max_tokens: int = MAX_CONTEXT_TOKENS) -> str:
        """Truncate context to fit within token limit."""
        max_chars = max_tokens * ContextWindowOptimizer.AVG_CHARS_PER_TOKEN
        
        if len(context) <= max_chars:
            return context
        
        # Truncate but keep end (most recent data)
        truncated = "...[earlier data omitted]...\n\n" + context[-max_chars:]
        logger.warning(f"Context truncated from {len(context)} to {len(truncated)} chars")
        return truncated
    
    @staticmethod
    def optimize_signal_context(signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove unnecessary fields from signal data to reduce tokens.
        Keep all essential trading signal fields.
        """
        if not signal_data:
            return {}
            
        # Keep all essential fields for trading signal analysis
        essential_fields = [
            # Core signal fields
            'action', 'direction', 'confidence', 'strike', 'type', 'option_type',
            'entry_price', 'target_1', 'target_2', 'stop_loss', 
            'risk_reward', 'risk_reward_2', 'trading_symbol', 'symbol',
            # Timing fields
            'expiry_date', 'days_to_expiry',
            # Analysis fields
            'mtf_bias', 'reversal_detected', 'reversal_type', 'reversal_description',
            'sentiment_score', 'sentiment_direction', 'market_mood',
            # Entry analysis
            'entry_analysis', 'discount_zone', 'liquidity_score', 'liquidity_grade',
            # Greeks (important for options)
            'greeks', 'delta', 'theta', 'gamma', 'vega',
            # Probability analysis
            'probability_analysis', 'confidence_adjustments'
        ]
        
        optimized = {}
        for field in essential_fields:
            if field in signal_data and signal_data[field] is not None:
                optimized[field] = signal_data[field]
        
        return optimized if optimized else signal_data  # Return original if no fields matched


class RateLimiter:
    """
    Rate limiting for AI API calls to prevent cost overruns.
    """
    
    def __init__(
        self,
        max_calls_per_minute: int = 10,
        max_calls_per_hour: int = 100,
        max_calls_per_day: int = 1000
    ):
        self.max_per_minute = max_calls_per_minute
        self.max_per_hour = max_calls_per_hour
        self.max_per_day = max_calls_per_day
        
        self.calls_minute: list = []
        self.calls_hour: list = []
        self.calls_day: list = []
    
    def can_make_call(self) -> tuple[bool, str]:
        """
        Check if call is allowed within rate limits.
        
        Returns (allowed, reason)
        """
        now = datetime.now()
        
        # Clean old entries
        self.calls_minute = [t for t in self.calls_minute if now - t < timedelta(minutes=1)]
        self.calls_hour = [t for t in self.calls_hour if now - t < timedelta(hours=1)]
        self.calls_day = [t for t in self.calls_day if now - t < timedelta(days=1)]
        
        # Check limits
        if len(self.calls_minute) >= self.max_per_minute:
            return False, "Rate limit: Too many calls per minute"
        
        if len(self.calls_hour) >= self.max_per_hour:
            return False, "Rate limit: Too many calls per hour"
        
        if len(self.calls_day) >= self.max_per_day:
            return False, "Rate limit: Daily limit reached"
        
        return True, "OK"
    
    def record_call(self):
        """Record a successful API call."""
        now = datetime.now()
        self.calls_minute.append(now)
        self.calls_hour.append(now)
        self.calls_day.append(now)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return {
            'calls_last_minute': len(self.calls_minute),
            'calls_last_hour': len(self.calls_hour),
            'calls_today': len(self.calls_day),
            'limits': {
                'per_minute': self.max_per_minute,
                'per_hour': self.max_per_hour,
                'per_day': self.max_per_day
            }
        }


# Global instances
query_deduplicator = QueryDeduplicator()
context_optimizer = ContextWindowOptimizer()
rate_limiter = RateLimiter(
    max_calls_per_minute=10,
    max_calls_per_hour=100,
    max_calls_per_day=500  # Conservative for free tier
)


def get_cost_optimizers():
    """Get all cost optimization tools."""
    return {
        'deduplicator': query_deduplicator,
        'optimizer': context_optimizer,
        'rate_limiter': rate_limiter
    }
