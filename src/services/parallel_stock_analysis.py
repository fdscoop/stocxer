"""
Fast Parallel Stock Analysis for TradeWise
Target: Analyze 50 stocks in 10-15 seconds using parallel processing
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Nifty 50 constituents
NIFTY_50_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
    "ICICIBANK", "BHARTIARTL", "SBIN", "BAJFINANCE", "ITC",
    "LT", "KOTAKBANK", "ASIANPAINT", "AXISBANK", "HCLTECH",
    "MARUTI", "TITAN", "SUNPHARMA", "ULTRACEMCO", "NESTLEIND",
    "WIPRO", "ONGC", "NTPC", "POWERGRID", "M&M",
    "TATAMOTORS", "BAJAJFINSV", "TECHM", "JSWSTEEL", "ADANIENT",
    "HINDALCO", "COALINDIA", "INDUSINDBK", "TATASTEEL", "CIPLA",
    "GRASIM", "EICHERMOT", "BRITANNIA", "DRREDDY", "BPCL",
    "APOLLOHOSP", "DIVISLAB", "HEROMOTOCO", "SHRIRAMFIN", "TATACONSUM",
    "ADANIPORTS", "UPL", "BAJAJ-AUTO", "SBILIFE", "LTIM"
]


class FastStockAnalyzer:
    """
    Ultra-fast stock analysis using parallel processing
    
    Strategy:
    - Use ThreadPoolExecutor for concurrent API calls
    - Lightweight indicators only (RSI, EMA 20/50)
    - Target: <1 second per stock, <15s total for 50 stocks
    """
    
    def __init__(self, fyers_client, candle_cache: dict, cache_ttl: int = 180, max_workers: int = 10):
        """
        Args:
            fyers_client: Fyers API client instance
            candle_cache: Reference to global CANDLE_CACHE dictionary
            cache_ttl: Cache TTL in seconds
            max_workers: Number of parallel workers
        """
        self.fyers_client = fyers_client
        self.candle_cache = candle_cache
        self.cache_ttl = cache_ttl
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.stocks = NIFTY_50_STOCKS
    
    async def analyze_all_stocks(self, index: str = "NIFTY") -> Dict:
        """
        Analyze all 50 stocks in parallel
        
        Args:
            index: Index name (currently only NIFTY supported)
        
        Returns:
            Dict with aggregated results and top movers
        """
        start = asyncio.get_event_loop().time()
        logger.info(f"🚀 Starting parallel analysis of {len(self.stocks)} stocks")
        
        # Analyze in parallel using ThreadPoolExecutor
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.executor, self._analyze_stock_fast, stock)
            for stock in self.stocks
        ]
        
        # Gather results (with exception handling)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_results = []
        error_count = 0
        for r in results:
            if isinstance(r, Exception):
                logger.warning(f"Analysis error: {r}")
                error_count += 1
            else:
                valid_results.append(r)
        
        # Aggregate results
        bullish_count = len([r for r in valid_results if r["direction"] == "bullish"])
        bearish_count = len([r for r in valid_results if r["direction"] == "bearish"])
        neutral_count = len([r for r in valid_results if r["direction"] == "neutral"])
        
        elapsed = asyncio.get_event_loop().time() - start
        logger.info(f"✅ Analyzed {len(valid_results)}/50 stocks in {elapsed:.2f}s ({error_count} errors)")
        
        # Calculate expected direction and confidence
        total_analyzed = len(valid_results)
        if total_analyzed == 0:
            expected_direction = "NEUTRAL"
            confidence = 0
        else:
            if bullish_count > bearish_count:
                expected_direction = "BULLISH"
                confidence = (bullish_count - bearish_count) / total_analyzed * 100
            elif bearish_count > bullish_count:
                expected_direction = "BEARISH"
                confidence = (bearish_count - bullish_count) / total_analyzed * 100
            else:
                expected_direction = "NEUTRAL"
                confidence = 0
        
        return {
            "stocks_scanned": total_analyzed,
            "bullish_stocks": bullish_count,
            "bearish_stocks": bearish_count,
            "neutral_stocks": neutral_count,
            "bullish_pct": round(bullish_count / total_analyzed * 100, 1) if total_analyzed else 0,
            "bearish_pct": round(bearish_count / total_analyzed * 100, 1) if total_analyzed else 0,
            "expected_direction": expected_direction,
            "confidence": round(confidence, 1),
            "analysis_time": round(elapsed, 2),
            "top_movers": self._get_top_movers(valid_results)
        }
    
    def _analyze_stock_fast(self, symbol: str) -> Dict:
        """
        Fast single stock analysis using lightweight indicators
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
        
        Returns:
            Dict with direction, confidence, and key metrics
        """
        try:
            # Get cached candles (60-min resolution for speed)
            candles = self._get_stock_candles(symbol)
            
            if candles is None or len(candles) < 20:
                logger.debug(f"Insufficient data for {symbol}")
                return {
                    "symbol": symbol,
                    "direction": "neutral",
                    "confidence": 0,
                    "error": "insufficient_data"
                }
            
            # Extract close prices
            close = candles["close"]
            
            # Calculate RSI (14-period)
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Calculate EMAs
            ema_20 = close.ewm(span=20, adjust=False).mean()
            ema_50 = close.ewm(span=50, adjust=False).mean()
            
            # Scoring system (0-1 scale)
            bullish_score = 0
            bearish_score = 0
            
            # RSI signals (weight: 0.4)
            if current_rsi > 60:
                bullish_score += 0.4
            elif current_rsi < 40:
                bearish_score += 0.4
            
            # EMA crossover (weight: 0.3)
            if ema_20.iloc[-1] > ema_50.iloc[-1]:
                bullish_score += 0.3
            else:
                bearish_score += 0.3
            
            # Price vs EMA (weight: 0.3)
            if close.iloc[-1] > ema_20.iloc[-1]:
                bullish_score += 0.3
            else:
                bearish_score += 0.3
            
            # Determine direction
            if bullish_score > bearish_score:
                direction = "bullish"
                confidence = bullish_score
            elif bearish_score > bullish_score:
                direction = "bearish"
                confidence = bearish_score
            else:
                direction = "neutral"
                confidence = 0
            
            return {
                "symbol": symbol,
                "direction": direction,
                "confidence": round(confidence, 2),
                "rsi": round(current_rsi, 2),
                "price": round(close.iloc[-1], 2),
                "ema_20": round(ema_20.iloc[-1], 2),
                "ema_50": round(ema_50.iloc[-1], 2)
            }
        
        except Exception as e:
            logger.warning(f"Error analyzing {symbol}: {e}")
            return {
                "symbol": symbol,
                "direction": "neutral",
                "confidence": 0,
                "error": str(e)
            }
    
    def _get_stock_candles(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get candles with caching integration
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
        
        Returns:
            DataFrame with OHLCV data or None
        """
        # Create Fyers symbol
        fyers_symbol = f"NSE:{symbol}-EQ"
        resolution = "60"  # 60-min for balance of speed and accuracy
        
        # Create cache key
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # 60 days of data
        cache_key = f"{fyers_symbol}_{resolution}_{start_date.date()}_{end_date.date()}"
        
        now = datetime.now()
        
        # Check cache
        if cache_key in self.candle_cache:
            candles, cached_time = self.candle_cache[cache_key]
            age = (now - cached_time).total_seconds()
            
            if age < self.cache_ttl:
                return candles
        
        # Fetch from API
        try:
            df = self.fyers_client.get_historical_data(
                symbol=fyers_symbol,
                resolution=resolution,
                date_from=start_date,
                date_to=end_date
            )
            
            if df is not None and not df.empty:
                # Cache it
                self.candle_cache[cache_key] = (df, now)
                return df
        
        except Exception as e:
            logger.warning(f"Error fetching {symbol}: {e}")
        
        return None
    
    def _get_top_movers(self, results: List[Dict]) -> Dict:
        """
        Get top 3 bullish and bearish stocks
        
        Args:
            results: List of analysis results
        
        Returns:
            Dict with top bullish and bearish stocks
        """
        # Filter and sort
        bullish = sorted(
            [r for r in results if r["direction"] == "bullish"],
            key=lambda x: x["confidence"],
            reverse=True
        )[:3]
        
        bearish = sorted(
            [r for r in results if r["direction"] == "bearish"],
            key=lambda x: x["confidence"],
            reverse=True
        )[:3]
        
        return {
            "bullish": bullish,
            "bearish": bearish
        }


# Global instance will be initialized in main.py
fast_analyzer = None


def get_fast_analyzer(fyers_client, candle_cache: dict, cache_ttl: int = 180):
    """
    Get or create the global FastStockAnalyzer instance
    
    Args:
        fyers_client: Fyers API client
        candle_cache: Global CANDLE_CACHE dictionary
        cache_ttl: Cache TTL in seconds
    
    Returns:
        FastStockAnalyzer instance
    """
    global fast_analyzer
    if fast_analyzer is None:
        fast_analyzer = FastStockAnalyzer(fyers_client, candle_cache, cache_ttl)
    return fast_analyzer
