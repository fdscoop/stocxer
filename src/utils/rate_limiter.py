"""
Fyers API Rate Limiter
Handles rate limiting to comply with Fyers API v3 limits:
- 10 requests per second
- 200 requests per minute
- 100,000 requests per day

This module provides:
1. Token bucket rate limiting
2. Request queuing
3. Automatic retry with backoff
4. Request batching for quotes
"""
import time
import asyncio
from collections import deque
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional, List, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for Fyers API
    
    Limits:
    - Per Second: 10 requests
    - Per Minute: 200 requests  
    - Per Day: 100,000 requests
    """
    
    def __init__(
        self,
        requests_per_second: int = 8,   # Leave buffer (limit is 10)
        requests_per_minute: int = 180,  # Leave buffer (limit is 200)
        requests_per_day: int = 90000    # Leave buffer (limit is 100000)
    ):
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        
        # Token buckets for each rate limit
        self.second_bucket = requests_per_second
        self.minute_bucket = requests_per_minute
        self.day_bucket = requests_per_day
        
        # Timestamps for bucket refill
        self.last_second_refill = time.time()
        self.last_minute_refill = time.time()
        self.last_day_refill = time.time()
        
        # Request tracking
        self.second_requests = deque(maxlen=1000)
        self.minute_requests = deque(maxlen=10000)
        self.daily_request_count = 0
        self.day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Thread safety
        self.lock = Lock()
        
        # Statistics
        self.total_requests = 0
        self.throttled_requests = 0
        self.cache_hits = 0
        
        logger.info(f"🚦 Rate limiter initialized: {requests_per_second}/s, {requests_per_minute}/min, {requests_per_day}/day")
    
    def _refill_buckets(self):
        """Refill token buckets based on elapsed time"""
        now = time.time()
        
        # Refill second bucket
        elapsed_seconds = now - self.last_second_refill
        if elapsed_seconds >= 1.0:
            self.second_bucket = min(
                self.second_bucket + int(elapsed_seconds * self.requests_per_second),
                self.requests_per_second
            )
            self.last_second_refill = now
        
        # Refill minute bucket
        elapsed_minutes = (now - self.last_minute_refill) / 60
        if elapsed_minutes >= 1.0:
            self.minute_bucket = min(
                self.minute_bucket + int(elapsed_minutes * self.requests_per_minute),
                self.requests_per_minute
            )
            self.last_minute_refill = now
        
        # Reset daily bucket at midnight
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if today > self.day_start:
            self.day_bucket = self.requests_per_day
            self.daily_request_count = 0
            self.day_start = today
            logger.info("🌅 Daily rate limit reset")
    
    def _clean_old_requests(self):
        """Remove requests older than tracking window"""
        now = time.time()
        
        # Clean second window (1.5 seconds to be safe)
        while self.second_requests and now - self.second_requests[0] > 1.5:
            self.second_requests.popleft()
        
        # Clean minute window (65 seconds to be safe)
        while self.minute_requests and now - self.minute_requests[0] > 65:
            self.minute_requests.popleft()
    
    def can_make_request(self) -> tuple[bool, float]:
        """
        Check if a request can be made now
        
        Returns:
            (can_make, wait_time): Boolean and suggested wait time if throttled
        """
        with self.lock:
            self._refill_buckets()
            self._clean_old_requests()
            
            now = time.time()
            
            # Check per-second limit
            recent_second = sum(1 for t in self.second_requests if now - t < 1.0)
            if recent_second >= self.requests_per_second:
                wait_time = 1.0 - (now - self.second_requests[0]) if self.second_requests else 1.0
                return False, max(0.1, wait_time)
            
            # Check per-minute limit
            recent_minute = sum(1 for t in self.minute_requests if now - t < 60.0)
            if recent_minute >= self.requests_per_minute:
                wait_time = 60.0 - (now - self.minute_requests[0]) if self.minute_requests else 1.0
                return False, max(0.1, wait_time)
            
            # Check daily limit
            if self.daily_request_count >= self.requests_per_day:
                # Wait until midnight
                tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                wait_time = (tomorrow - datetime.now()).total_seconds()
                logger.error(f"🚫 Daily limit reached! Need to wait {wait_time/3600:.1f} hours")
                return False, wait_time
            
            return True, 0.0
    
    def record_request(self):
        """Record that a request was made"""
        with self.lock:
            now = time.time()
            self.second_requests.append(now)
            self.minute_requests.append(now)
            self.daily_request_count += 1
            self.total_requests += 1
    
    def wait_if_needed(self) -> float:
        """
        Wait if rate limit would be exceeded
        
        Returns:
            Time waited in seconds
        """
        total_waited = 0.0
        max_wait = 30.0  # Don't wait more than 30 seconds
        
        while total_waited < max_wait:
            can_make, wait_time = self.can_make_request()
            
            if can_make:
                self.record_request()
                return total_waited
            
            # Log throttling
            if total_waited == 0:
                self.throttled_requests += 1
                logger.warning(f"⏳ Rate limited, waiting {wait_time:.2f}s...")
            
            # Wait
            actual_wait = min(wait_time, max_wait - total_waited)
            time.sleep(actual_wait)
            total_waited += actual_wait
        
        logger.error(f"⚠️ Rate limit wait exceeded {max_wait}s, proceeding anyway")
        self.record_request()
        return total_waited
    
    async def wait_if_needed_async(self) -> float:
        """Async version of wait_if_needed"""
        total_waited = 0.0
        max_wait = 30.0
        
        while total_waited < max_wait:
            can_make, wait_time = self.can_make_request()
            
            if can_make:
                self.record_request()
                return total_waited
            
            if total_waited == 0:
                self.throttled_requests += 1
                logger.warning(f"⏳ Rate limited (async), waiting {wait_time:.2f}s...")
            
            actual_wait = min(wait_time, max_wait - total_waited)
            await asyncio.sleep(actual_wait)
            total_waited += actual_wait
        
        logger.error(f"⚠️ Rate limit wait exceeded {max_wait}s, proceeding anyway")
        self.record_request()
        return total_waited
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        with self.lock:
            now = time.time()
            return {
                "total_requests": self.total_requests,
                "throttled_requests": self.throttled_requests,
                "cache_hits": self.cache_hits,
                "daily_request_count": self.daily_request_count,
                "daily_limit": self.requests_per_day,
                "daily_remaining": self.requests_per_day - self.daily_request_count,
                "recent_per_second": sum(1 for t in self.second_requests if now - t < 1.0),
                "recent_per_minute": sum(1 for t in self.minute_requests if now - t < 60.0),
                "throttle_rate": f"{(self.throttled_requests / max(1, self.total_requests)) * 100:.1f}%"
            }
    
    def record_cache_hit(self):
        """Record a cache hit (request avoided)"""
        with self.lock:
            self.cache_hits += 1


class RequestBatcher:
    """
    Batch multiple quote requests into single API calls
    Fyers quotes endpoint supports up to 50 symbols per request
    """
    
    def __init__(self, max_batch_size: int = 50, max_wait_ms: int = 100):
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.pending_symbols: List[str] = []
        self.lock = Lock()
    
    def batch_quotes(self, symbols: List[str]) -> List[List[str]]:
        """
        Split symbols into batches of max_batch_size
        
        Args:
            symbols: List of symbols to quote
            
        Returns:
            List of symbol batches
        """
        batches = []
        for i in range(0, len(symbols), self.max_batch_size):
            batches.append(symbols[i:i + self.max_batch_size])
        return batches


class RetryHandler:
    """
    Handle API errors with exponential backoff retry
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if request should be retried based on error"""
        if attempt >= self.max_retries:
            return False
        
        error_str = str(error).lower()
        
        # Retry on rate limit errors
        if "429" in error_str or "rate limit" in error_str or "request limit" in error_str:
            return True
        
        # Retry on timeout errors
        if "timeout" in error_str or "timed out" in error_str:
            return True
        
        # Retry on temporary server errors
        if "500" in error_str or "502" in error_str or "503" in error_str or "504" in error_str:
            return True
        
        # Don't retry on client errors (invalid symbol, etc.)
        if "invalid" in error_str or "not found" in error_str or "-300" in error_str:
            return False
        
        return False
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        rate_limiter: Optional[RateLimiter] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Async function to execute
            rate_limiter: Optional rate limiter to use
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Result from function
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Wait for rate limit if provided
                if rate_limiter:
                    await rate_limiter.wait_if_needed_async()
                
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                return result
                
            except Exception as e:
                last_error = e
                
                if not self.should_retry(e, attempt):
                    raise
                
                delay = self.calculate_delay(attempt)
                logger.warning(f"⚠️ API error (attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                logger.info(f"   Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_error


# Global rate limiter instance
fyers_rate_limiter = RateLimiter()
fyers_retry_handler = RetryHandler()
fyers_request_batcher = RequestBatcher()


def rate_limited(func):
    """Decorator to add rate limiting to a function"""
    def wrapper(*args, **kwargs):
        fyers_rate_limiter.wait_if_needed()
        return func(*args, **kwargs)
    return wrapper


def rate_limited_async(func):
    """Decorator to add rate limiting to an async function"""
    async def wrapper(*args, **kwargs):
        await fyers_rate_limiter.wait_if_needed_async()
        return await func(*args, **kwargs)
    return wrapper
