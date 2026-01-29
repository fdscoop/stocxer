"""
Candlestick Pattern Detection for Multi-Timeframe Analysis
Integrates with ICT methodology to provide timing confirmation for entries

Uses TA-Lib for pattern detection across multiple timeframes
Priority patterns for Indian indices:
  - Engulfing (strong reversal)
  - Hammer/Shooting Star (support/resistance tests)
  - Doji (indecision zones)
  - Morning/Evening Star (trend reversals)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Try to import TA-Lib, provide fallback if not available
try:
    import talib
    TALIB_AVAILABLE = True
    logger.info("✅ TA-Lib loaded successfully")
except ImportError:
    TALIB_AVAILABLE = False
    logger.warning("⚠️ TA-Lib not available - using statistical fallback for patterns")


@dataclass
class CandlestickPattern:
    """Detected candlestick pattern"""
    pattern_name: str
    timeframe: str
    direction: str  # 'bullish', 'bearish', 'neutral'
    strength: int  # 100, 200, 300 (TA-Lib convention: 100=weak, 200=medium, 300=strong)
    timestamp: datetime
    price_at_pattern: float
    
    def __repr__(self):
        return f"{self.pattern_name} ({self.direction}) on {self.timeframe} @ {self.price_at_pattern:.2f}"


class CandlestickAnalyzer:
    """
    Multi-timeframe candlestick pattern detection and confluence scoring
    
    Integrates with ICT analysis to provide entry timing confirmation
    """
    
    # Timeframe weights - higher timeframes get more weight
    TIMEFRAME_WEIGHTS = {
        'M': 1.0,      # Monthly - highest weight
        'W': 0.9,      # Weekly
        'D': 0.8,      # Daily
        '240': 0.6,    # 4-hour
        '60': 0.4,     # 1-hour
        '15': 0.3,     # 15-minute
        '5': 0.2,      # 5-minute
        '3': 0.1       # 3-minute - lowest weight
    }
    
    # Pattern strength multipliers (TA-Lib returns 100, 200, or 300)
    STRENGTH_MULTIPLIER = {
        100: 0.5,   # Weak pattern
        200: 0.75,  # Medium pattern
        300: 1.0    # Strong pattern
    }
    
    def __init__(self):
        self.patterns_detected = []
        
    def analyze_patterns(
        self,
        candles: pd.DataFrame,
        timeframe: str
    ) -> List[CandlestickPattern]:
        """
        Detect all relevant candlestick patterns on given timeframe
        
        Args:
            candles: DataFrame with OHLC data
            timeframe: Timeframe identifier ('D', '240', '60', etc.)
            
        Returns:
            List of detected patterns
        """
        if not TALIB_AVAILABLE:
            return self._fallback_pattern_detection(candles, timeframe)
        
        patterns = []
        
        # Ensure we have required columns
        if not all(col in candles.columns for col in ['open', 'high', 'low', 'close']):
            logger.warning(f"Missing OHLC columns in candles for {timeframe}")
            return patterns
        
        # Need at least 10 candles for reliable pattern detection
        if len(candles) < 10:
            logger.warning(f"Insufficient candles ({len(candles)}) for pattern detection on {timeframe}")
            return patterns
        
        open_prices = candles['open'].values
        high_prices = candles['high'].values
        low_prices = candles['low'].values
        close_prices = candles['close'].values
        
        # Get last timestamp and price
        last_timestamp = candles.index[-1] if isinstance(candles.index, pd.DatetimeIndex) else datetime.now()
        last_price = close_prices[-1]
        
        # Detect reversal patterns (highest priority)
        patterns.extend(self._detect_reversal_patterns(
            open_prices, high_prices, low_prices, close_prices,
            timeframe, last_timestamp, last_price
        ))
        
        # Detect continuation patterns
        patterns.extend(self._detect_continuation_patterns(
            open_prices, high_prices, low_prices, close_prices,
            timeframe, last_timestamp, last_price
        ))
        
        # Detect indecision patterns
        patterns.extend(self._detect_indecision_patterns(
            open_prices, high_prices, low_prices, close_prices,
            timeframe, last_timestamp, last_price
        ))
        
        logger.info(f"📊 {timeframe}: Detected {len(patterns)} candlestick patterns")
        return patterns
    
    def _detect_reversal_patterns(
        self,
        open_p: np.ndarray,
        high_p: np.ndarray,
        low_p: np.ndarray,
        close_p: np.ndarray,
        timeframe: str,
        timestamp: datetime,
        price: float
    ) -> List[CandlestickPattern]:
        """Detect bullish and bearish reversal patterns"""
        patterns = []
        
        # Bullish reversal patterns
        hammer = talib.CDLHAMMER(open_p, high_p, low_p, close_p)
        if hammer[-1] != 0:
            patterns.append(CandlestickPattern(
                pattern_name="Hammer",
                timeframe=timeframe,
                direction="bullish",
                strength=abs(hammer[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        inv_hammer = talib.CDLINVERTEDHAMMER(open_p, high_p, low_p, close_p)
        if inv_hammer[-1] != 0:
            patterns.append(CandlestickPattern(
                pattern_name="Inverted Hammer",
                timeframe=timeframe,
                direction="bullish",
                strength=abs(inv_hammer[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        morning_star = talib.CDLMORNINGSTAR(open_p, high_p, low_p, close_p)
        if morning_star[-1] != 0:
            patterns.append(CandlestickPattern(
                pattern_name="Morning Star",
                timeframe=timeframe,
                direction="bullish",
                strength=abs(morning_star[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        engulfing = talib.CDLENGULFING(open_p, high_p, low_p, close_p)
        if engulfing[-1] > 0:  # Positive = bullish engulfing
            patterns.append(CandlestickPattern(
                pattern_name="Bullish Engulfing",
                timeframe=timeframe,
                direction="bullish",
                strength=abs(engulfing[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        # Bearish reversal patterns
        shooting_star = talib.CDLSHOOTINGSTAR(open_p, high_p, low_p, close_p)
        if shooting_star[-1] != 0:
            patterns.append(CandlestickPattern(
                pattern_name="Shooting Star",
                timeframe=timeframe,
                direction="bearish",
                strength=abs(shooting_star[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        hanging_man = talib.CDLHANGINGMAN(open_p, high_p, low_p, close_p)
        if hanging_man[-1] != 0:
            patterns.append(CandlestickPattern(
                pattern_name="Hanging Man",
                timeframe=timeframe,
                direction="bearish",
                strength=abs(hanging_man[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        evening_star = talib.CDLEVENINGSTAR(open_p, high_p, low_p, close_p)
        if evening_star[-1] != 0:
            patterns.append(CandlestickPattern(
                pattern_name="Evening Star",
                timeframe=timeframe,
                direction="bearish",
                strength=abs(evening_star[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        if engulfing[-1] < 0:  # Negative = bearish engulfing
            patterns.append(CandlestickPattern(
                pattern_name="Bearish Engulfing",
                timeframe=timeframe,
                direction="bearish",
                strength=abs(engulfing[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        return patterns
    
    def _detect_continuation_patterns(
        self,
        open_p: np.ndarray,
        high_p: np.ndarray,
        low_p: np.ndarray,
        close_p: np.ndarray,
        timeframe: str,
        timestamp: datetime,
        price: float
    ) -> List[CandlestickPattern]:
        """Detect trend continuation patterns"""
        patterns = []
        
        # Three white soldiers (bullish continuation)
        three_white = talib.CDL3WHITESOLDIERS(open_p, high_p, low_p, close_p)
        if three_white[-1] != 0:
            patterns.append(CandlestickPattern(
                pattern_name="Three White Soldiers",
                timeframe=timeframe,
                direction="bullish",
                strength=abs(three_white[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        # Three black crows (bearish continuation)
        three_black = talib.CDL3BLACKCROWS(open_p, high_p, low_p, close_p)
        if three_black[-1] != 0:
            patterns.append(CandlestickPattern(
                pattern_name="Three Black Crows",
                timeframe=timeframe,
                direction="bearish",
                strength=abs(three_black[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        # Marubozu (strong directional candle)
        marubozu = talib.CDLMARUBOZU(open_p, high_p, low_p, close_p)
        if marubozu[-1] > 0:
            patterns.append(CandlestickPattern(
                pattern_name="Bullish Marubozu",
                timeframe=timeframe,
                direction="bullish",
                strength=abs(marubozu[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        elif marubozu[-1] < 0:
            patterns.append(CandlestickPattern(
                pattern_name="Bearish Marubozu",
                timeframe=timeframe,
                direction="bearish",
                strength=abs(marubozu[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        return patterns
    
    def _detect_indecision_patterns(
        self,
        open_p: np.ndarray,
        high_p: np.ndarray,
        low_p: np.ndarray,
        close_p: np.ndarray,
        timeframe: str,
        timestamp: datetime,
        price: float
    ) -> List[CandlestickPattern]:
        """Detect indecision/consolidation patterns"""
        patterns = []
        
        # Doji patterns (indecision)
        doji = talib.CDLDOJI(open_p, high_p, low_p, close_p)
        if doji[-1] != 0:
            patterns.append(CandlestickPattern(
                pattern_name="Doji",
                timeframe=timeframe,
                direction="neutral",
                strength=abs(doji[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        dragonfly_doji = talib.CDLDRAGONFLYDOJI(open_p, high_p, low_p, close_p)
        if dragonfly_doji[-1] != 0:
            patterns.append(CandlestickPattern(
                pattern_name="Dragonfly Doji",
                timeframe=timeframe,
                direction="bullish",  # Bullish reversal potential
                strength=abs(dragonfly_doji[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        gravestone_doji = talib.CDLGRAVESTONEDOJI(open_p, high_p, low_p, close_p)
        if gravestone_doji[-1] != 0:
            patterns.append(CandlestickPattern(
                pattern_name="Gravestone Doji",
                timeframe=timeframe,
                direction="bearish",  # Bearish reversal potential
                strength=abs(gravestone_doji[-1]),
                timestamp=timestamp,
                price_at_pattern=price
            ))
        
        return patterns
    
    def calculate_pattern_confluence(
        self,
        patterns_by_timeframe: Dict[str, List[CandlestickPattern]],
        expected_direction: str
    ) -> Dict:
        """
        Calculate confluence score based on pattern alignment across timeframes
        
        Args:
            patterns_by_timeframe: Dict mapping timeframe to list of patterns
            expected_direction: Expected direction from ICT analysis ('bullish'/'bearish')
            
        Returns:
            Dict with confluence score and breakdown
        """
        total_score = 0.0
        max_possible_score = 0.0
        aligned_patterns = []
        conflicting_patterns = []
        
        for timeframe, patterns in patterns_by_timeframe.items():
            tf_weight = self.TIMEFRAME_WEIGHTS.get(timeframe, 0.1)
            
            for pattern in patterns:
                # Calculate pattern contribution
                strength_mult = self.STRENGTH_MULTIPLIER.get(pattern.strength, 0.5)
                pattern_score = tf_weight * strength_mult * 100
                max_possible_score += pattern_score
                
                # Check alignment with expected direction
                if pattern.direction == expected_direction:
                    total_score += pattern_score
                    aligned_patterns.append(pattern)
                elif pattern.direction == 'neutral':
                    # Neutral patterns don't add or subtract
                    pass
                else:
                    # Conflicting pattern - subtract half the score
                    total_score -= (pattern_score * 0.5)
                    conflicting_patterns.append(pattern)
        
        # Calculate final confluence percentage (0-100)
        if max_possible_score > 0:
            confluence_pct = min(100, max(0, (total_score / max_possible_score) * 100))
        else:
            confluence_pct = 0
        
        # Confidence level
        if confluence_pct >= 75:
            confidence = "VERY HIGH"
        elif confluence_pct >= 60:
            confidence = "HIGH"
        elif confluence_pct >= 40:
            confidence = "MODERATE"
        else:
            confidence = "LOW"
        
        return {
            'confluence_score': round(confluence_pct, 1),
            'confidence_level': confidence,
            'aligned_patterns': len(aligned_patterns),
            'conflicting_patterns': len(conflicting_patterns),
            'pattern_details': {
                'aligned': [str(p) for p in aligned_patterns[:5]],  # Top 5
                'conflicting': [str(p) for p in conflicting_patterns[:3]]  # Top 3
            },
            'max_possible_score': round(max_possible_score, 2),
            'actual_score': round(total_score, 2)
        }
    
    def _fallback_pattern_detection(
        self,
        candles: pd.DataFrame,
        timeframe: str
    ) -> List[CandlestickPattern]:
        """
        Fallback pattern detection using statistical methods when TA-Lib unavailable
        Detects basic patterns: Hammer, Shooting Star, Engulfing, Doji
        """
        logger.warning(f"Using fallback pattern detection for {timeframe}")
        patterns = []
        
        if len(candles) < 3:
            return patterns
        
        # Get last 3 candles for pattern detection
        recent = candles.tail(3)
        last = recent.iloc[-1]
        prev = recent.iloc[-2] if len(recent) >= 2 else None
        
        open_p = last['open']
        high_p = last['high']
        low_p = last['low']
        close_p = last['close']
        body = abs(close_p - open_p)
        range_p = high_p - low_p
        
        timestamp = last.name if isinstance(candles.index, pd.DatetimeIndex) else datetime.now()
        
        # Avoid division by zero
        if range_p == 0:
            return patterns
        
        body_to_range = body / range_p if range_p > 0 else 0
        
        # Hammer detection (bullish reversal)
        # Small body at top, long lower shadow
        lower_shadow = (min(open_p, close_p) - low_p) / range_p if range_p > 0 else 0
        upper_shadow = (high_p - max(open_p, close_p)) / range_p if range_p > 0 else 0
        
        if lower_shadow > 0.6 and body_to_range < 0.3 and upper_shadow < 0.1:
            patterns.append(CandlestickPattern(
                pattern_name="Hammer (Fallback)",
                timeframe=timeframe,
                direction="bullish",
                strength=200,
                timestamp=timestamp,
                price_at_pattern=close_p
            ))
        
        # Shooting star (bearish reversal)
        if upper_shadow > 0.6 and body_to_range < 0.3 and lower_shadow < 0.1:
            patterns.append(CandlestickPattern(
                pattern_name="Shooting Star (Fallback)",
                timeframe=timeframe,
                direction="bearish",
                strength=200,
                timestamp=timestamp,
                price_at_pattern=close_p
            ))
        
        # Doji (indecision)
        if body_to_range < 0.1:
            patterns.append(CandlestickPattern(
                pattern_name="Doji (Fallback)",
                timeframe=timeframe,
                direction="neutral",
                strength=100,
                timestamp=timestamp,
                price_at_pattern=close_p
            ))
        
        # Engulfing (needs previous candle)
        if prev is not None:
            prev_body = abs(prev['close'] - prev['open'])
            prev_bullish = prev['close'] > prev['open']
            curr_bullish = close_p > open_p
            
            # Bullish engulfing
            if not prev_bullish and curr_bullish and body > prev_body * 1.2:
                patterns.append(CandlestickPattern(
                    pattern_name="Bullish Engulfing (Fallback)",
                    timeframe=timeframe,
                    direction="bullish",
                    strength=200,
                    timestamp=timestamp,
                    price_at_pattern=close_p
                ))
            
            # Bearish engulfing
            if prev_bullish and not curr_bullish and body > prev_body * 1.2:
                patterns.append(CandlestickPattern(
                    pattern_name="Bearish Engulfing (Fallback)",
                    timeframe=timeframe,
                    direction="bearish",
                    strength=200,
                    timestamp=timestamp,
                    price_at_pattern=close_p
                ))
        
        return patterns


# Global instance
candlestick_analyzer = CandlestickAnalyzer()


def analyze_candlestick_patterns(
    candles_by_timeframe: Dict[str, pd.DataFrame],
    expected_direction: str
) -> Dict:
    """
    Convenience function to analyze patterns across multiple timeframes
    
    Args:
        candles_by_timeframe: Dict mapping timeframe to OHLC DataFrame
        expected_direction: Expected direction from ICT analysis
        
    Returns:
        Dict with confluence analysis
    """
    analyzer = CandlestickAnalyzer()
    
    patterns_by_tf = {}
    for timeframe, candles in candles_by_timeframe.items():
        patterns = analyzer.analyze_patterns(candles, timeframe)
        if patterns:
            patterns_by_tf[timeframe] = patterns
    
    confluence = analyzer.calculate_pattern_confluence(patterns_by_tf, expected_direction)
    
    return {
        'patterns_detected': patterns_by_tf,
        'confluence_analysis': confluence,
        'timestamp': datetime.now().isoformat()
    }
