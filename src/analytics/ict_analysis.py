"""
ICT (Inner Circle Trader) Analysis Module
Implements key ICT concepts for market structure analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class OrderBlock:
    """Represents an order block"""
    start_time: datetime
    end_time: datetime
    high: float
    low: float
    block_type: str  # "bullish" or "bearish"
    strength: float  # 0-1 score based on volume and size


@dataclass
class FairValueGap:
    """Represents a Fair Value Gap (FVG)"""
    time: datetime
    gap_high: float
    gap_low: float
    gap_type: str  # "bullish" or "bearish"
    filled: bool = False


@dataclass
class LiquidityLevel:
    """Represents a liquidity level"""
    time: datetime
    price: float
    level_type: str  # "buy_side" or "sell_side"
    swept: bool = False


class ICTAnalyzer:
    """Analyze market using ICT concepts"""
    
    def __init__(self):
        self.min_gap_size_percent = 0.001  # Minimum gap size as % of price
        self.order_block_lookback = 20  # Number of candles to look back
    
    def identify_market_structure(
        self,
        df: pd.DataFrame,
        swing_strength: int = 5
    ) -> pd.DataFrame:
        """
        Identify market structure (Higher Highs, Lower Lows, etc.)
        
        Args:
            df: DataFrame with OHLC data
            swing_strength: Number of candles on each side for swing identification
            
        Returns:
            DataFrame with structure levels added
        """
        df = df.copy()
        
        # Identify swing highs and lows
        df['swing_high'] = df['high'][(
            (df['high'].shift(swing_strength) < df['high']) &
            (df['high'].shift(-swing_strength) < df['high'])
        )]
        
        df['swing_low'] = df['low'][(
            (df['low'].shift(swing_strength) > df['low']) &
            (df['low'].shift(-swing_strength) > df['low'])
        )]
        
        # Identify market structure breaks
        df['structure_break'] = self._identify_structure_breaks(df)
        
        # Determine trend
        df['trend'] = self._determine_trend(df)
        
        return df
    
    def _identify_structure_breaks(self, df: pd.DataFrame) -> pd.Series:
        """Identify breaks in market structure"""
        breaks = pd.Series(index=df.index, data=None, dtype='object')
        
        swing_highs = df['swing_high'].dropna()
        swing_lows = df['swing_low'].dropna()
        
        for i in range(1, len(df)):
            current_high = df['high'].iloc[i]
            current_low = df['low'].iloc[i]
            
            # Check for bullish break (close above previous swing high)
            if not swing_highs.empty:
                last_swing_high = swing_highs[swing_highs.index < df.index[i]].iloc[-1] \
                    if len(swing_highs[swing_highs.index < df.index[i]]) > 0 else None
                if last_swing_high and current_high > last_swing_high:
                    breaks.iloc[i] = 'bullish'
            
            # Check for bearish break (close below previous swing low)
            if not swing_lows.empty:
                last_swing_low = swing_lows[swing_lows.index < df.index[i]].iloc[-1] \
                    if len(swing_lows[swing_lows.index < df.index[i]]) > 0 else None
                if last_swing_low and current_low < last_swing_low:
                    breaks.iloc[i] = 'bearish'
        
        return breaks
    
    def _determine_trend(self, df: pd.DataFrame) -> pd.Series:
        """Determine overall trend based on structure"""
        trend = pd.Series(index=df.index, data='neutral', dtype='object')
        
        swing_highs = df['swing_high'].dropna()
        swing_lows = df['swing_low'].dropna()
        
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            # Uptrend: Higher Highs and Higher Lows
            if swing_highs.iloc[-1] > swing_highs.iloc[-2] and \
               swing_lows.iloc[-1] > swing_lows.iloc[-2]:
                trend.iloc[-1] = 'uptrend'
            # Downtrend: Lower Highs and Lower Lows
            elif swing_highs.iloc[-1] < swing_highs.iloc[-2] and \
                 swing_lows.iloc[-1] < swing_lows.iloc[-2]:
                trend.iloc[-1] = 'downtrend'
        
        # Forward fill the trend
        trend = trend.replace('neutral', np.nan).fillna(method='ffill').fillna('neutral')
        
        return trend
    
    def identify_fair_value_gaps(
        self,
        df: pd.DataFrame
    ) -> List[FairValueGap]:
        """
        Identify Fair Value Gaps (FVG) - imbalances in price
        
        A bullish FVG occurs when the high of candle 1 < low of candle 3
        A bearish FVG occurs when the low of candle 1 > high of candle 3
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of FairValueGap objects
        """
        fvgs = []
        
        for i in range(2, len(df)):
            candle_1_high = df['high'].iloc[i-2]
            candle_1_low = df['low'].iloc[i-2]
            candle_3_high = df['high'].iloc[i]
            candle_3_low = df['low'].iloc[i]
            
            # Bullish FVG
            if candle_1_high < candle_3_low:
                gap_size = candle_3_low - candle_1_high
                if gap_size / df['close'].iloc[i] > self.min_gap_size_percent:
                    fvgs.append(FairValueGap(
                        time=df.index[i],
                        gap_high=candle_3_low,
                        gap_low=candle_1_high,
                        gap_type="bullish"
                    ))
            
            # Bearish FVG
            elif candle_1_low > candle_3_high:
                gap_size = candle_1_low - candle_3_high
                if gap_size / df['close'].iloc[i] > self.min_gap_size_percent:
                    fvgs.append(FairValueGap(
                        time=df.index[i],
                        gap_high=candle_1_low,
                        gap_low=candle_3_high,
                        gap_type="bearish"
                    ))
        
        logger.info(f"Identified {len(fvgs)} Fair Value Gaps")
        return fvgs
    
    def identify_order_blocks(
        self,
        df: pd.DataFrame
    ) -> List[OrderBlock]:
        """
        Identify Order Blocks - last up/down candle before strong move
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of OrderBlock objects
        """
        order_blocks = []
        
        for i in range(1, len(df) - 1):
            current_close = df['close'].iloc[i]
            current_open = df['open'].iloc[i]
            next_close = df['close'].iloc[i+1]
            next_open = df['open'].iloc[i+1]
            
            # Bullish order block: down candle followed by strong up move
            if current_close < current_open:  # Down candle
                if next_close > next_open and \
                   (next_close - next_open) > 2 * abs(current_close - current_open):
                    
                    # Calculate strength based on volume if available
                    strength = 0.7
                    if 'volume' in df.columns:
                        avg_volume = df['volume'].iloc[max(0, i-20):i].mean()
                        if df['volume'].iloc[i+1] > 1.5 * avg_volume:
                            strength = 0.9
                    
                    order_blocks.append(OrderBlock(
                        start_time=df.index[i],
                        end_time=df.index[i+1],
                        high=df['high'].iloc[i],
                        low=df['low'].iloc[i],
                        block_type="bullish",
                        strength=strength
                    ))
            
            # Bearish order block: up candle followed by strong down move
            elif current_close > current_open:  # Up candle
                if next_close < next_open and \
                   (next_open - next_close) > 2 * abs(current_close - current_open):
                    
                    strength = 0.7
                    if 'volume' in df.columns:
                        avg_volume = df['volume'].iloc[max(0, i-20):i].mean()
                        if df['volume'].iloc[i+1] > 1.5 * avg_volume:
                            strength = 0.9
                    
                    order_blocks.append(OrderBlock(
                        start_time=df.index[i],
                        end_time=df.index[i+1],
                        high=df['high'].iloc[i],
                        low=df['low'].iloc[i],
                        block_type="bearish",
                        strength=strength
                    ))
        
        logger.info(f"Identified {len(order_blocks)} Order Blocks")
        return order_blocks
    
    def identify_liquidity_levels(
        self,
        df: pd.DataFrame,
        lookback_period: int = 50
    ) -> List[LiquidityLevel]:
        """
        Identify liquidity levels (equal highs/lows where stops might be)
        
        Args:
            df: DataFrame with OHLC data
            lookback_period: Period to look back for equal levels
            
        Returns:
            List of LiquidityLevel objects
        """
        liquidity_levels = []
        tolerance = 0.002  # 0.2% tolerance for "equal" levels
        
        # Look for equal highs (buy-side liquidity)
        for i in range(lookback_period, len(df)):
            window = df['high'].iloc[i-lookback_period:i]
            max_high = window.max()
            
            # Count how many times price touched this level
            touches = sum(abs(window - max_high) / max_high < tolerance)
            
            if touches >= 2:  # At least double top
                liquidity_levels.append(LiquidityLevel(
                    time=df.index[i],
                    price=max_high,
                    level_type="buy_side"
                ))
        
        # Look for equal lows (sell-side liquidity)
        for i in range(lookback_period, len(df)):
            window = df['low'].iloc[i-lookback_period:i]
            min_low = window.min()
            
            touches = sum(abs(window - min_low) / min_low < tolerance)
            
            if touches >= 2:  # At least double bottom
                liquidity_levels.append(LiquidityLevel(
                    time=df.index[i],
                    price=min_low,
                    level_type="sell_side"
                ))
        
        logger.info(f"Identified {len(liquidity_levels)} Liquidity Levels")
        return liquidity_levels
    
    def check_liquidity_sweep(
        self,
        current_price: float,
        liquidity_level: LiquidityLevel,
        tolerance: float = 0.001
    ) -> bool:
        """Check if a liquidity level has been swept"""
        if liquidity_level.level_type == "buy_side":
            return current_price > liquidity_level.price * (1 + tolerance)
        else:
            return current_price < liquidity_level.price * (1 - tolerance)
    
    def generate_ict_signal(
        self,
        df: pd.DataFrame,
        current_price: float
    ) -> Dict:
        """
        Generate trading signal based on ICT analysis
        
        Returns:
            Dict with signal, confidence, and reasoning
        """
        # Add market structure
        df_analyzed = self.identify_market_structure(df)
        
        # Identify patterns
        fvgs = self.identify_fair_value_gaps(df)
        order_blocks = self.identify_order_blocks(df)
        liquidity_levels = self.identify_liquidity_levels(df)
        
        signal = "neutral"
        confidence = 0.0
        reasons = []
        
        # Check current trend
        current_trend = df_analyzed['trend'].iloc[-1]
        
        # Check if price is near order block
        for ob in order_blocks[-5:]:  # Check last 5 order blocks
            if ob.block_type == "bullish" and \
               ob.low <= current_price <= ob.high and \
               current_trend == "uptrend":
                signal = "buy"
                confidence += 0.3 * ob.strength
                reasons.append(f"Price at bullish order block ({ob.low:.2f}-{ob.high:.2f})")
            
            elif ob.block_type == "bearish" and \
                 ob.low <= current_price <= ob.high and \
                 current_trend == "downtrend":
                signal = "sell"
                confidence += 0.3 * ob.strength
                reasons.append(f"Price at bearish order block ({ob.low:.2f}-{ob.high:.2f})")
        
        # Check for unfilled FVGs
        for fvg in fvgs[-5:]:
            if not fvg.filled and fvg.gap_low <= current_price <= fvg.gap_high:
                if fvg.gap_type == "bullish":
                    if signal != "sell":
                        signal = "buy"
                        confidence += 0.25
                        reasons.append(f"Price in bullish FVG ({fvg.gap_low:.2f}-{fvg.gap_high:.2f})")
                else:
                    if signal != "buy":
                        signal = "sell"
                        confidence += 0.25
                        reasons.append(f"Price in bearish FVG ({fvg.gap_low:.2f}-{fvg.gap_high:.2f})")
        
        # Check liquidity sweeps
        for liq in liquidity_levels[-5:]:
            if self.check_liquidity_sweep(current_price, liq):
                if liq.level_type == "buy_side" and current_trend == "downtrend":
                    signal = "sell"
                    confidence += 0.2
                    reasons.append(f"Buy-side liquidity swept at {liq.price:.2f}")
                elif liq.level_type == "sell_side" and current_trend == "uptrend":
                    signal = "buy"
                    confidence += 0.2
                    reasons.append(f"Sell-side liquidity swept at {liq.price:.2f}")
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        return {
            "signal": signal,
            "confidence": round(confidence, 2),
            "trend": current_trend,
            "reasons": reasons,
            "order_blocks": len(order_blocks),
            "fair_value_gaps": len(fvgs),
            "liquidity_levels": len(liquidity_levels)
        }


# Global analyzer instance
ict_analyzer = ICTAnalyzer()
