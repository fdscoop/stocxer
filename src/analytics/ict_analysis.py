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


# ====================================================================
# NEW: Top-Down ICT Analysis Functions
# ====================================================================

@dataclass
class HTFBias:
    """Higher Timeframe Bias Analysis Result"""
    overall_direction: str  # 'bullish', 'bearish', 'neutral'
    bias_strength: float  # 0-100
    structure_quality: str  # 'HIGH', 'MEDIUM', 'LOW'
    premium_discount: str  # 'premium', 'equilibrium', 'discount'
    key_zones: List[Dict]  # List of important FVG/OB zones
    swing_high: float
    swing_low: float
    current_price: float


@dataclass
class LTFEntryModel:
    """Lower Timeframe Entry Model Result"""
    entry_type: str  # 'FVG_TEST_2ND', 'FVG_TEST', 'OB_TEST', 'CHOCH', 'BOS'
    timeframe: str  # Which LTF has the setup
    trigger_price: float  # Exact entry level
    entry_zone: Tuple[float, float]  # (low, high) entry range
    momentum_confirmed: bool
    alignment_score: float  # 0-100 (how well it aligns with HTF)
    confidence: float  # 0-1


def calculate_premium_discount_zones(
    swing_high: float,
    swing_low: float,
    current_price: float
) -> Dict:
    """
    Calculate if price is in premium, equilibrium, or discount zone
    
    Premium: 75-100% of swing range (expensive - avoid buying)
    Equilibrium: 25-75% of swing range (neutral)
    Discount: 0-25% of swing range (cheap - good for buying)
    
    Args:
        swing_high: Recent swing high
        swing_low: Recent swing low
        current_price: Current market price
        
    Returns:
        Dict with zone classification and percentage
    """
    swing_range = swing_high - swing_low
    if swing_range == 0:
        return {
            'zone': 'equilibrium',
            'percentage': 50.0,
            'swing_high': swing_high,
            'swing_low': swing_low
        }
    
    # Calculate position in range (0% = swing_low, 100% = swing_high)
    position_pct = ((current_price - swing_low) / swing_range) * 100
    position_pct = max(0, min(100, position_pct))  # Clamp to 0-100
    
    # Classify zone
    if position_pct >= 75:
        zone = 'premium'  # Expensive zone
    elif position_pct <= 25:
        zone = 'discount'  # Cheap zone
    else:
        zone = 'equilibrium'  # Fair value
    
    return {
        'zone': zone,
        'percentage': round(position_pct, 1),
        'swing_high': swing_high,
        'swing_low': swing_low,
        'equilibrium': swing_low + (swing_range * 0.5)
    }


def determine_htf_bias(
    analyses_by_timeframe: Dict[str, Dict],
    current_price: float,
    trading_mode: str = "auto"
) -> HTFBias:
    """
    Establish directional bias from higher timeframes
    Priority order adjusts based on trading mode:
    - LONGTERM: Monthly > Weekly > Daily > 4H
    - INTRADAY: Daily > 4H > 1H (ignores Monthly/Weekly)
    
    Args:
        analyses_by_timeframe: Dict mapping timeframe to ICT analysis results
            Keys: 'M', 'W', 'D', '240' (4H)
            Values: Dict with 'trend', 'fvgs', 'order_blocks', etc.
        current_price: Current market price
        trading_mode: 'intraday', 'longterm', or 'auto'
        
    Returns:
        HTFBias with overall direction and key zones
    """
    logger.info("=" * 60)
    logger.info("🎯 DETERMINING HTF BIAS")
    logger.info(f"   Trading Mode: {trading_mode.upper()}")
    logger.info("=" * 60)
    
    # CRITICAL FIX: Adjust timeframe priority based on trading mode
    # For INTRADAY: Ignore Monthly/Weekly, prioritize 4H and 1H
    if trading_mode.lower() == "intraday":
        # Intraday: Daily provides context, 4H/1H provide direction
        tf_priority = {'D': 1, '240': 3, '4H': 3, '60': 2, '1H': 2}  # 4H > 1H > Daily
        timeframes_to_analyze = ['D', '240', '4H', '60', '1H']
        logger.info("   📊 Using INTRADAY weights: 4H (3) > 1H (2) > D (1)")
    elif trading_mode.lower() == "longterm":
        # Long-term: Full HTF analysis
        tf_priority = {'M': 4, 'W': 3, 'D': 2, '240': 1, '4H': 1}
        timeframes_to_analyze = ['M', 'W', 'D', '240', '4H']
        logger.info("   📊 Using LONGTERM weights: M (4) > W (3) > D (2) > 4H (1)")
    else:
        # Auto: Default to balanced
        tf_priority = {'M': 4, 'W': 3, 'D': 2, '240': 1, '4H': 1}
        timeframes_to_analyze = ['M', 'W', 'D', '240', '4H']
        logger.info("   📊 Using AUTO weights (balanced)")
    
    # Collect trends from each timeframe
    trends = {}
    key_zones = []
    
    # Find swing range for premium/discount calculation
    swing_high = current_price
    swing_low = current_price
    
    for tf in timeframes_to_analyze:
        if tf not in analyses_by_timeframe:
            continue
            
        analysis = analyses_by_timeframe[tf]
        trend = analysis.get('trend', 'neutral')
        trends[tf] = trend
        
        # Collect swing points
        if 'swing_high' in analysis:
            swing_high = max(swing_high, analysis['swing_high'])
        if 'swing_low' in analysis:
            swing_low = min(swing_low, analysis['swing_low'])
        
        # Collect key FVG/OB zones
        for fvg in analysis.get('fvgs', [])[:3]:  # Top 3 FVGs
            key_zones.append({
                'type': 'FVG',
                'direction': fvg.gap_type,
                'timeframe': tf,
                'low': fvg.gap_low,
                'high': fvg.gap_high,
                'priority': tf_priority.get(tf, 0)
            })
        
        for ob in analysis.get('order_blocks', [])[:2]:  # Top 2 OBs
            key_zones.append({
                'type': 'OB',
                'direction': ob.block_type,
                'timeframe': tf,
                'low': ob.low,
                'high': ob.high,
                'priority': tf_priority.get(tf, 0)
            })
    
    # Weight trends by timeframe priority
    bullish_score = 0
    bearish_score = 0
    total_weight = 0
    
    for tf, trend in trends.items():
        weight = tf_priority.get(tf, 0)
        total_weight += weight
        
        if trend == 'uptrend':
            bullish_score += weight
        elif trend == 'downtrend':
            bearish_score += weight
    
    # Determine overall direction
    if total_weight == 0:
        overall_direction = 'neutral'
        bias_strength = 30
        structure_quality = 'LOW'
    else:
        bullish_pct = (bullish_score / total_weight) * 100
        bearish_pct = (bearish_score / total_weight) * 100
        
        if bullish_pct >= 60:
            overall_direction = 'bullish'
            bias_strength = bullish_pct
            structure_quality = 'HIGH' if bullish_pct >= 80 else 'MEDIUM'
        elif bearish_pct >= 60:
            overall_direction = 'bearish'
            bias_strength = bearish_pct
            structure_quality = 'HIGH' if bearish_pct >= 80 else 'MEDIUM'
        else:
            overall_direction = 'neutral'
            bias_strength = 50
            structure_quality = 'LOW'
    
    # Calculate premium/discount
    pd_zones = calculate_premium_discount_zones(swing_high, swing_low, current_price)
    
    # Sort key zones by priority
    key_zones.sort(key=lambda x: x['priority'], reverse=True)
    
    logger.info(f"📊 HTF Direction: {overall_direction.upper()}")
    logger.info(f"   Bias Strength: {bias_strength:.1f}/100")
    logger.info(f"   Structure Quality: {structure_quality}")
    logger.info(f"   Premium/Discount: {pd_zones['zone'].upper()} ({pd_zones['percentage']:.1f}%)")
    logger.info(f"   Key Zones: {len(key_zones)}")
    logger.info("=" * 60)
    
    return HTFBias(
        overall_direction=overall_direction,
        bias_strength=bias_strength,
        structure_quality=structure_quality,
        premium_discount=pd_zones['zone'],
        key_zones=key_zones[:10],  # Top 10 zones
        swing_high=swing_high,
        swing_low=swing_low,
        current_price=current_price
    )


def identify_ltf_entry_model(
    htf_bias: HTFBias,
    ltf_analyses: Dict[str, Dict],
    current_price: float
) -> Optional[LTFEntryModel]:
    """
    Find entry triggers on lower timeframes that align with HTF bias
    Only looks for setups that AGREE with HTF direction
    
    Args:
        htf_bias: HTF bias analysis
        ltf_analyses: Dict mapping LTF ('60', '15', '5', '3') to analysis
        current_price: Current market price
        
    Returns:
        LTFEntryModel if valid setup found, None otherwise
    """
    logger.info("=" * 60)
    logger.info("🔎 SEARCHING FOR LTF ENTRY MODEL")
    logger.info(f"   HTF Bias: {htf_bias.overall_direction.upper()}")
    logger.info("=" * 60)
    
    # Timeframe priority for entry (prefer higher LTF)
    ltf_order = ['60', '15', '5', '3']  # 1H > 15m > 5m > 3m
    
    best_entry = None
    best_score = 0
    
    for tf in ltf_order:
        if tf not in ltf_analyses:
            continue
        
        analysis = ltf_analyses[tf]
        fvgs = analysis.get('fvgs', [])
        order_blocks = analysis.get('order_blocks', [])
        structure_breaks = analysis.get('structure_breaks', [])
        
        # Look for FVG tests (highest priority)
        for i, fvg in enumerate(fvgs[-5:]):  # Check last 5 FVGs
            # Must align with HTF direction
            if fvg.gap_type != htf_bias.overall_direction:
                continue
            
            # Check if price is near FVG
            distance_pct = abs((fvg.gap_low + fvg.gap_high) / 2 - current_price) / current_price * 100
            if distance_pct > 2.0:  # More than 2% away
                continue
            
            # Determine if second test (higher probability)
            entry_type = 'FVG_TEST_2ND' if i > 0 else 'FVG_TEST'
            
            # Calculate alignment score
            alignment = 100 if fvg.gap_type == htf_bias.overall_direction else 0
            
            # Calculate overall score
            score = alignment * (1.5 if entry_type == 'FVG_TEST_2ND' else 1.0)
            score *= (1.2 if tf == '60' else 1.0)  # Bonus for 1H timeframe
            
            if score > best_score:
                best_score = score
                best_entry = LTFEntryModel(
                    entry_type=entry_type,
                    timeframe=tf,
                    trigger_price=(fvg.gap_low + fvg.gap_high) / 2,
                    entry_zone=(fvg.gap_low, fvg.gap_high),
                    momentum_confirmed=True,  # Assume confirmed if FVG exists
                    alignment_score=alignment,
                    confidence=0.75 if entry_type == 'FVG_TEST_2ND' else 0.60
                )
        
        # Look for Order Block tests
        for ob in order_blocks[-3:]:
            if ob.block_type != htf_bias.overall_direction:
                continue
            
            distance_pct = abs((ob.low + ob.high) / 2 - current_price) / current_price * 100
            if distance_pct > 1.5:
                continue
            
            alignment = 100 if ob.block_type == htf_bias.overall_direction else 0
            score = alignment * ob.strength
            
            if score > best_score:
                best_score = score
                best_entry = LTFEntryModel(
                    entry_type='OB_TEST',
                    timeframe=tf,
                    trigger_price=(ob.low + ob.high) / 2,
                    entry_zone=(ob.low, ob.high),
                    momentum_confirmed=ob.strength > 0.7,
                    alignment_score=alignment,
                    confidence=0.65
                )
    
    if best_entry:
        logger.info(f"✅ Found {best_entry.entry_type} on {best_entry.timeframe}")
        logger.info(f"   Entry Zone: {best_entry.entry_zone[0]:.2f} - {best_entry.entry_zone[1]:.2f}")
        logger.info(f"   Alignment: {best_entry.alignment_score:.0f}%")
    else:
        logger.info("⚠️ No valid LTF entry model found")
    
    logger.info("=" * 60)
    return best_entry


def analyze_multi_timeframe_ict_topdown(
    candles_by_timeframe: Dict[str, pd.DataFrame],
    current_price: float,
    trading_mode: str = "auto"
) -> Dict:
    """
    Complete top-down ICT analysis
    
    Phase 1: HTF Bias 
        - LONGTERM: (Monthly > Weekly > Daily > 4H)
        - INTRADAY: (Daily > 4H > 1H) - ignores Monthly/Weekly
    Phase 2: LTF Entry (1H > 15m > 5m > 3m)
    
    Args:
        candles_by_timeframe: Dict mapping timeframe to OHLC DataFrame
            HTF: Keys like 'M', 'W', 'D', '240'
            LTF: Keys like '60', '15', '5', '3'
        current_price: Current market price
        trading_mode: 'intraday', 'longterm', or 'auto'
        
    Returns:
        Dict with complete top-down analysis
    """
    logger.info("\n" + "=" * 60)
    logger.info("🚀 ICT TOP-DOWN ANALYSIS")
    logger.info(f"   Trading Mode: {trading_mode.upper()}")
    logger.info("=" * 60)
    
    analyzer = ICTAnalyzer()
    
    # Determine which HTF timeframes to analyze based on trading mode
    if trading_mode.lower() == "intraday":
        htf_timeframes = ['D', '240', '4H', '60', '1H']  # Skip M, W for intraday
        logger.info("   📊 INTRADAY: Using D, 4H, 1H (skipping M, W)")
    else:
        htf_timeframes = ['M', 'W', 'D', '240', '4H']
        logger.info("   📊 LONGTERM/AUTO: Using M, W, D, 4H")
    
    # Phase 1: Analyze HTF for bias
    htf_analyses = {}
    for tf in htf_timeframes:
        if tf not in candles_by_timeframe:
            continue
        
        df = candles_by_timeframe[tf]
        if df is None or len(df) < 20:
            continue
        
        try:
            # Run ICT analysis
            df_analyzed = analyzer.identify_market_structure(df)
            fvgs = analyzer.identify_fair_value_gaps(df)
            order_blocks = analyzer.identify_order_blocks(df)
            
            # Get swing points
            swing_highs = df_analyzed['swing_high'].dropna()
            swing_lows = df_analyzed['swing_low'].dropna()
            
            htf_analyses[tf] = {
                'trend': df_analyzed['trend'].iloc[-1] if 'trend' in df_analyzed.columns else 'neutral',
                'fvgs': fvgs,
                'order_blocks': order_blocks,
                'swing_high': swing_highs.iloc[-1] if len(swing_highs) > 0 else current_price,
                'swing_low': swing_lows.iloc[-1] if len(swing_lows) > 0 else current_price
            }
        except Exception as e:
            logger.warning(f"HTF analysis failed for {tf}: {e}")
    
    # Determine HTF bias - pass trading_mode for proper weighting
    htf_bias = determine_htf_bias(htf_analyses, current_price, trading_mode=trading_mode)
    
    # Phase 2: Analyze LTF for entry
    ltf_analyses = {}
    for tf in ['60', '15', '5', '3']:
        if tf not in candles_by_timeframe:
            continue
        
        df = candles_by_timeframe[tf]
        if df is None or len(df) < 10:
            continue
        
        try:
            df_analyzed = analyzer.identify_market_structure(df)
            fvgs = analyzer.identify_fair_value_gaps(df)
            order_blocks = analyzer.identify_order_blocks(df)
            
            ltf_analyses[tf] = {
                'fvgs': fvgs,
                'order_blocks': order_blocks,
                'structure_breaks': df_analyzed.get('structure_break', [])
            }
        except Exception as e:
            logger.warning(f"LTF analysis failed for {tf}: {e}")
    
    # Find LTF entry model
    ltf_entry = identify_ltf_entry_model(htf_bias, ltf_analyses, current_price)
    
    logger.info("=" * 60)
    logger.info("✅ TOP-DOWN ANALYSIS COMPLETE")
    logger.info("=" * 60 + "\n")
    
    return {
        'htf_bias': htf_bias,
        'ltf_entry': ltf_entry,
        'htf_analyses': htf_analyses,
        'ltf_analyses': ltf_analyses
    }
