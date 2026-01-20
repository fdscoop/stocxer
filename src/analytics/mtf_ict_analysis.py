"""
Multi-Timeframe ICT Analysis Module
Analyzes Monthly → Weekly → Daily → 4H → 1H → 15min
Identifies Liquidity Zones, Fair Value Gaps, Order Blocks
Tracks FVG tests (1st test, 2nd test)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Timeframe(Enum):
    """Trading timeframes for analysis"""
    MONTHLY = "M"
    WEEKLY = "W"
    DAILY = "D"
    FOUR_HOUR = "240"
    ONE_HOUR = "60"
    FIFTEEN_MIN = "15"
    FIVE_MIN = "5"


# Fyers resolution mapping
FYERS_RESOLUTION = {
    Timeframe.MONTHLY: "M",
    Timeframe.WEEKLY: "W",
    Timeframe.DAILY: "D",
    Timeframe.FOUR_HOUR: "240",
    Timeframe.ONE_HOUR: "60",
    Timeframe.FIFTEEN_MIN: "15",
    Timeframe.FIVE_MIN: "5"
}

# Days of data needed for each timeframe
LOOKBACK_DAYS = {
    Timeframe.MONTHLY: 730,   # 2 years
    Timeframe.WEEKLY: 365,    # 1 year
    Timeframe.DAILY: 180,     # 6 months
    Timeframe.FOUR_HOUR: 60,  # 2 months
    Timeframe.ONE_HOUR: 30,   # 1 month
    Timeframe.FIFTEEN_MIN: 10, # 10 days
    Timeframe.FIVE_MIN: 5     # 5 days
}


@dataclass
class FairValueGap:
    """Fair Value Gap (FVG) structure"""
    type: str  # "bullish" or "bearish"
    high: float
    low: float
    midpoint: float
    timestamp: datetime
    timeframe: str
    filled: bool = False
    test_count: int = 0
    first_test_time: Optional[datetime] = None
    second_test_time: Optional[datetime] = None
    status: str = "active"  # active, tested_once, tested_twice, filled


@dataclass
class LiquidityZone:
    """Liquidity zone (equal highs/lows, swing points)"""
    type: str  # "buy_side" (above price) or "sell_side" (below price)
    level: float
    strength: int  # number of touches
    timestamps: List[datetime] = field(default_factory=list)
    swept: bool = False
    sweep_time: Optional[datetime] = None


@dataclass
class OrderBlock:
    """Order Block structure"""
    type: str  # "bullish" or "bearish"
    high: float
    low: float
    timestamp: datetime
    timeframe: str
    tested: bool = False
    test_count: int = 0
    valid: bool = True


@dataclass
class MarketStructure:
    """Market structure for a timeframe"""
    timeframe: str
    trend: str  # bullish, bearish, ranging
    last_high: float
    last_low: float
    break_of_structure: Optional[str] = None  # "bullish_bos", "bearish_bos"
    change_of_character: Optional[str] = None  # "bullish_choch", "bearish_choch"


@dataclass
class TimeframeAnalysis:
    """Complete analysis for a single timeframe"""
    timeframe: str
    market_structure: MarketStructure
    fair_value_gaps: List[FairValueGap]
    liquidity_zones: List[LiquidityZone]
    order_blocks: List[OrderBlock]
    bias: str  # bullish, bearish, neutral
    key_levels: List[float]


@dataclass
class MultiTimeframeAnalysis:
    """Complete MTF analysis"""
    symbol: str
    current_price: float
    timestamp: datetime
    analyses: Dict[str, TimeframeAnalysis]
    overall_bias: str
    confluence_zones: List[Dict]
    trade_setups: List[Dict]


class MultiTimeframeICTAnalyzer:
    """
    Multi-Timeframe ICT Analysis
    
    Analysis Flow:
    1. Monthly/Weekly: Identify major liquidity zones & FVGs
    2. Daily: Confirm trend direction
    3. 4H: Identify trading opportunities
    4. 1H/15min: Entry timing
    """
    
    def __init__(self, fyers_client):
        self.fyers = fyers_client
        self.cache = {}
    
    def get_ohlc_data(self, symbol: str, timeframe: Timeframe) -> pd.DataFrame:
        """Fetch OHLC data for given timeframe"""
        try:
            days = LOOKBACK_DAYS[timeframe]
            resolution = FYERS_RESOLUTION[timeframe]
            
            date_to = datetime.now()
            date_from = date_to - timedelta(days=days)
            
            df = self.fyers.get_historical_data(
                symbol=symbol,
                resolution=resolution,
                date_from=date_from,
                date_to=date_to
            )
            
            if df.empty:
                # Generate sample data for testing
                df = self._generate_sample_data(symbol, timeframe, days)
            
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} {timeframe}: {e}")
            return self._generate_sample_data(symbol, timeframe, LOOKBACK_DAYS[timeframe])
    
    def _generate_sample_data(self, symbol: str, timeframe: Timeframe, periods: int) -> pd.DataFrame:
        """Generate sample OHLC data for testing"""
        # Get current price
        try:
            quote = self.fyers.get_quotes([symbol])
            base_price = quote["d"][0]["v"]["lp"] if quote and quote.get("d") else 25000
        except:
            base_price = 25000
        
        # Generate realistic OHLC data
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='D')
        
        returns = np.random.normal(0.0002, 0.015, periods)
        prices = base_price * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.005, 0.005, periods)),
            'high': prices * (1 + np.random.uniform(0.002, 0.015, periods)),
            'low': prices * (1 - np.random.uniform(0.002, 0.015, periods)),
            'close': prices,
            'volume': np.random.randint(100000, 1000000, periods)
        }, index=dates)
        
        # Ensure high >= open, close and low <= open, close
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        return df
    
    def identify_swing_points(self, df: pd.DataFrame, lookback: int = 5) -> Tuple[List, List]:
        """Identify swing highs and swing lows"""
        swing_highs = []
        swing_lows = []
        
        for i in range(lookback, len(df) - lookback):
            # Swing High: Higher than surrounding candles
            if df['high'].iloc[i] == df['high'].iloc[i-lookback:i+lookback+1].max():
                swing_highs.append({
                    'price': df['high'].iloc[i],
                    'timestamp': df.index[i],
                    'index': i
                })
            
            # Swing Low: Lower than surrounding candles
            if df['low'].iloc[i] == df['low'].iloc[i-lookback:i+lookback+1].min():
                swing_lows.append({
                    'price': df['low'].iloc[i],
                    'timestamp': df.index[i],
                    'index': i
                })
        
        return swing_highs, swing_lows
    
    def identify_market_structure(self, df: pd.DataFrame, timeframe: str) -> MarketStructure:
        """
        Identify market structure: HH, HL (bullish) or LH, LL (bearish)
        
        Bullish: Higher Highs and Higher Lows
        Bearish: Lower Highs and Lower Lows
        """
        swing_highs, swing_lows = self.identify_swing_points(df)
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return MarketStructure(
                timeframe=timeframe,
                trend="ranging",
                last_high=df['high'].iloc[-1],
                last_low=df['low'].iloc[-1]
            )
        
        # Get last 4 swing points
        recent_highs = swing_highs[-2:]
        recent_lows = swing_lows[-2:]
        
        # Determine trend
        higher_high = recent_highs[-1]['price'] > recent_highs[-2]['price']
        higher_low = recent_lows[-1]['price'] > recent_lows[-2]['price']
        lower_high = recent_highs[-1]['price'] < recent_highs[-2]['price']
        lower_low = recent_lows[-1]['price'] < recent_lows[-2]['price']
        
        if higher_high and higher_low:
            trend = "bullish"
        elif lower_high and lower_low:
            trend = "bearish"
        else:
            trend = "ranging"
        
        # Check for Break of Structure (BOS) or Change of Character (CHoCH)
        bos = None
        choch = None
        
        current_price = df['close'].iloc[-1]
        
        if trend == "bullish" and current_price < recent_lows[-1]['price']:
            choch = "bearish_choch"
        elif trend == "bearish" and current_price > recent_highs[-1]['price']:
            choch = "bullish_choch"
        
        return MarketStructure(
            timeframe=timeframe,
            trend=trend,
            last_high=recent_highs[-1]['price'],
            last_low=recent_lows[-1]['price'],
            break_of_structure=bos,
            change_of_character=choch
        )
    
    def identify_fair_value_gaps(self, df: pd.DataFrame, timeframe: str) -> List[FairValueGap]:
        """
        Identify Fair Value Gaps (FVG)
        
        Bullish FVG: Gap between candle 1 high and candle 3 low (price moved up fast)
        Bearish FVG: Gap between candle 1 low and candle 3 high (price moved down fast)
        """
        fvgs = []
        current_price = df['close'].iloc[-1]
        
        for i in range(2, len(df)):
            candle1 = df.iloc[i-2]
            candle2 = df.iloc[i-1]  # The impulse candle
            candle3 = df.iloc[i]
            
            # Bullish FVG: Candle 3 low > Candle 1 high
            if candle3['low'] > candle1['high']:
                gap_high = candle3['low']
                gap_low = candle1['high']
                
                # Check if FVG has been filled or tested
                filled = False
                test_count = 0
                first_test = None
                second_test = None
                
                # Look at subsequent candles
                for j in range(i+1, len(df)):
                    if df['low'].iloc[j] <= gap_high:
                        test_count += 1
                        if test_count == 1:
                            first_test = df.index[j]
                        elif test_count == 2:
                            second_test = df.index[j]
                        
                        if df['low'].iloc[j] <= gap_low:
                            filled = True
                            break
                
                # Only include recent, unfilled FVGs
                if not filled and (current_price - gap_high) / current_price < 0.05:
                    status = "active"
                    if test_count >= 2:
                        status = "tested_twice"
                    elif test_count == 1:
                        status = "tested_once"
                    
                    fvgs.append(FairValueGap(
                        type="bullish",
                        high=gap_high,
                        low=gap_low,
                        midpoint=(gap_high + gap_low) / 2,
                        timestamp=df.index[i-1],
                        timeframe=timeframe,
                        filled=filled,
                        test_count=test_count,
                        first_test_time=first_test,
                        second_test_time=second_test,
                        status=status
                    ))
            
            # Bearish FVG: Candle 3 high < Candle 1 low
            if candle3['high'] < candle1['low']:
                gap_high = candle1['low']
                gap_low = candle3['high']
                
                filled = False
                test_count = 0
                first_test = None
                second_test = None
                
                for j in range(i+1, len(df)):
                    if df['high'].iloc[j] >= gap_low:
                        test_count += 1
                        if test_count == 1:
                            first_test = df.index[j]
                        elif test_count == 2:
                            second_test = df.index[j]
                        
                        if df['high'].iloc[j] >= gap_high:
                            filled = True
                            break
                
                if not filled and (gap_low - current_price) / current_price < 0.05:
                    status = "active"
                    if test_count >= 2:
                        status = "tested_twice"
                    elif test_count == 1:
                        status = "tested_once"
                    
                    fvgs.append(FairValueGap(
                        type="bearish",
                        high=gap_high,
                        low=gap_low,
                        midpoint=(gap_high + gap_low) / 2,
                        timestamp=df.index[i-1],
                        timeframe=timeframe,
                        filled=filled,
                        test_count=test_count,
                        first_test_time=first_test,
                        second_test_time=second_test,
                        status=status
                    ))
        
        # Return most recent FVGs
        return sorted(fvgs, key=lambda x: x.timestamp, reverse=True)[:10]
    
    def identify_liquidity_zones(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """
        Identify liquidity zones:
        - Equal highs (buy-side liquidity above)
        - Equal lows (sell-side liquidity below)
        - Swing highs/lows with multiple touches
        """
        zones = []
        current_price = df['close'].iloc[-1]
        tolerance = current_price * 0.001  # 0.1% tolerance
        
        # Find equal highs (buy-side liquidity)
        highs = df['high'].values
        for i in range(len(highs)):
            touches = []
            for j in range(len(highs)):
                if i != j and abs(highs[i] - highs[j]) < tolerance:
                    touches.append(df.index[j])
            
            if len(touches) >= 2 and highs[i] > current_price:
                zones.append(LiquidityZone(
                    type="buy_side",
                    level=highs[i],
                    strength=len(touches) + 1,
                    timestamps=[df.index[i]] + touches,
                    swept=False
                ))
        
        # Find equal lows (sell-side liquidity)
        lows = df['low'].values
        for i in range(len(lows)):
            touches = []
            for j in range(len(lows)):
                if i != j and abs(lows[i] - lows[j]) < tolerance:
                    touches.append(df.index[j])
            
            if len(touches) >= 2 and lows[i] < current_price:
                zones.append(LiquidityZone(
                    type="sell_side",
                    level=lows[i],
                    strength=len(touches) + 1,
                    timestamps=[df.index[i]] + touches,
                    swept=False
                ))
        
        # Remove duplicates and sort by strength
        unique_zones = []
        seen_levels = set()
        for zone in sorted(zones, key=lambda x: x.strength, reverse=True):
            rounded_level = round(zone.level, 0)
            if rounded_level not in seen_levels:
                seen_levels.add(rounded_level)
                unique_zones.append(zone)
        
        return unique_zones[:10]
    
    def identify_order_blocks(self, df: pd.DataFrame, timeframe: str) -> List[OrderBlock]:
        """
        Identify Order Blocks:
        - Bullish OB: Last down candle before up move
        - Bearish OB: Last up candle before down move
        """
        obs = []
        current_price = df['close'].iloc[-1]
        
        for i in range(2, len(df) - 1):
            candle = df.iloc[i]
            next_candle = df.iloc[i + 1]
            
            # Bullish Order Block
            if candle['close'] < candle['open']:  # Down candle
                if next_candle['close'] > next_candle['open']:  # Followed by up
                    if next_candle['close'] > candle['high']:  # Strong move
                        ob_high = candle['high']
                        ob_low = candle['low']
                        
                        # Check if still valid (price hasn't closed below)
                        valid = True
                        tested = False
                        test_count = 0
                        
                        for j in range(i + 2, len(df)):
                            if df['low'].iloc[j] <= ob_high and df['low'].iloc[j] >= ob_low:
                                tested = True
                                test_count += 1
                            if df['close'].iloc[j] < ob_low:
                                valid = False
                                break
                        
                        if valid and ob_high < current_price * 1.02:
                            obs.append(OrderBlock(
                                type="bullish",
                                high=ob_high,
                                low=ob_low,
                                timestamp=df.index[i],
                                timeframe=timeframe,
                                tested=tested,
                                test_count=test_count,
                                valid=valid
                            ))
            
            # Bearish Order Block
            if candle['close'] > candle['open']:  # Up candle
                if next_candle['close'] < next_candle['open']:  # Followed by down
                    if next_candle['close'] < candle['low']:  # Strong move
                        ob_high = candle['high']
                        ob_low = candle['low']
                        
                        valid = True
                        tested = False
                        test_count = 0
                        
                        for j in range(i + 2, len(df)):
                            if df['high'].iloc[j] >= ob_low and df['high'].iloc[j] <= ob_high:
                                tested = True
                                test_count += 1
                            if df['close'].iloc[j] > ob_high:
                                valid = False
                                break
                        
                        if valid and ob_low > current_price * 0.98:
                            obs.append(OrderBlock(
                                type="bearish",
                                high=ob_high,
                                low=ob_low,
                                timestamp=df.index[i],
                                timeframe=timeframe,
                                tested=tested,
                                test_count=test_count,
                                valid=valid
                            ))
        
        return sorted(obs, key=lambda x: x.timestamp, reverse=True)[:5]
    
    def analyze_timeframe(self, symbol: str, timeframe: Timeframe) -> TimeframeAnalysis:
        """Complete analysis for a single timeframe"""
        df = self.get_ohlc_data(symbol, timeframe)
        tf_str = timeframe.value
        
        # Market Structure
        structure = self.identify_market_structure(df, tf_str)
        
        # Fair Value Gaps
        fvgs = self.identify_fair_value_gaps(df, tf_str)
        
        # Liquidity Zones
        liquidity = self.identify_liquidity_zones(df)
        
        # Order Blocks
        obs = self.identify_order_blocks(df, tf_str)
        
        # Determine bias
        bullish_factors = sum([
            structure.trend == "bullish",
            len([f for f in fvgs if f.type == "bullish"]) > len([f for f in fvgs if f.type == "bearish"]),
            len([o for o in obs if o.type == "bullish"]) > len([o for o in obs if o.type == "bearish"])
        ])
        
        if bullish_factors >= 2:
            bias = "bullish"
        elif bullish_factors <= 1:
            bias = "bearish"
        else:
            bias = "neutral"
        
        # Key levels
        key_levels = []
        for fvg in fvgs[:3]:
            key_levels.append(fvg.midpoint)
        for ob in obs[:2]:
            key_levels.append((ob.high + ob.low) / 2)
        for liq in liquidity[:3]:
            key_levels.append(liq.level)
        
        return TimeframeAnalysis(
            timeframe=tf_str,
            market_structure=structure,
            fair_value_gaps=fvgs,
            liquidity_zones=liquidity,
            order_blocks=obs,
            bias=bias,
            key_levels=sorted(set(key_levels))
        )
    
    def find_confluence_zones(self, analyses: Dict[str, TimeframeAnalysis], current_price: float) -> List[Dict]:
        """Find price zones where multiple timeframe levels align"""
        all_levels = []
        
        for tf, analysis in analyses.items():
            weight = {
                "M": 5, "W": 4, "D": 3, "240": 2, "60": 1.5, "15": 1
            }.get(tf, 1)
            
            for fvg in analysis.fair_value_gaps:
                all_levels.append({
                    "level": fvg.midpoint,
                    "type": f"{fvg.type}_fvg",
                    "timeframe": tf,
                    "weight": weight,
                    "status": fvg.status
                })
            
            for ob in analysis.order_blocks:
                all_levels.append({
                    "level": (ob.high + ob.low) / 2,
                    "type": f"{ob.type}_ob",
                    "timeframe": tf,
                    "weight": weight
                })
            
            for liq in analysis.liquidity_zones:
                all_levels.append({
                    "level": liq.level,
                    "type": liq.type,
                    "timeframe": tf,
                    "weight": weight * liq.strength / 3
                })
        
        # Group nearby levels into confluence zones
        tolerance = current_price * 0.003  # 0.3% tolerance
        confluence = []
        used = set()
        
        for i, level in enumerate(all_levels):
            if i in used:
                continue
            
            zone = {
                "center": level["level"],
                "levels": [level],
                "total_weight": level["weight"]
            }
            
            for j, other in enumerate(all_levels):
                if j != i and j not in used:
                    if abs(level["level"] - other["level"]) < tolerance:
                        zone["levels"].append(other)
                        zone["total_weight"] += other["weight"]
                        used.add(j)
            
            if zone["total_weight"] >= 3:  # Minimum confluence
                zone["center"] = np.mean([l["level"] for l in zone["levels"]])
                zone["timeframes"] = list(set(l["timeframe"] for l in zone["levels"]))
                zone["distance_pct"] = (zone["center"] - current_price) / current_price * 100
                confluence.append(zone)
            
            used.add(i)
        
        return sorted(confluence, key=lambda x: x["total_weight"], reverse=True)[:5]
    
    def generate_trade_setups(self, analyses: Dict[str, TimeframeAnalysis], 
                             confluence: List[Dict], current_price: float) -> List[Dict]:
        """Generate potential trade setups based on MTF analysis"""
        setups = []
        
        # Determine overall bias from higher timeframes
        htf_bias = "neutral"
        htf_analyses = [analyses.get(tf) for tf in ["M", "W", "D"] if tf in analyses]
        bullish_count = sum(1 for a in htf_analyses if a and a.bias == "bullish")
        bearish_count = sum(1 for a in htf_analyses if a and a.bias == "bearish")
        
        if bullish_count > bearish_count:
            htf_bias = "bullish"
        elif bearish_count > bullish_count:
            htf_bias = "bearish"
        
        # Find setups from confluence zones
        for zone in confluence:
            distance = zone["distance_pct"]
            
            # Buy setup: Price above bullish confluence zone
            if distance < 0 and distance > -2:  # Zone is slightly below
                if htf_bias in ["bullish", "neutral"]:
                    setups.append({
                        "type": "BUY",
                        "entry_zone": zone["center"],
                        "reasoning": f"Bullish confluence from {', '.join(zone['timeframes'])} timeframes",
                        "weight": zone["total_weight"],
                        "action": "Wait for price to test zone then enter long",
                        "stop_loss": zone["center"] * 0.995,
                        "target_1": current_price * 1.01,
                        "target_2": current_price * 1.02
                    })
            
            # Sell setup: Price below bearish confluence zone
            elif distance > 0 and distance < 2:  # Zone is slightly above
                if htf_bias in ["bearish", "neutral"]:
                    setups.append({
                        "type": "SELL",
                        "entry_zone": zone["center"],
                        "reasoning": f"Bearish confluence from {', '.join(zone['timeframes'])} timeframes",
                        "weight": zone["total_weight"],
                        "action": "Wait for price to test zone then enter short",
                        "stop_loss": zone["center"] * 1.005,
                        "target_1": current_price * 0.99,
                        "target_2": current_price * 0.98
                    })
        
        # Check for FVG test setups
        for tf, analysis in analyses.items():
            for fvg in analysis.fair_value_gaps:
                if fvg.status == "tested_once":
                    if fvg.type == "bullish" and htf_bias != "bearish":
                        setups.append({
                            "type": "BUY_FVG_RETEST",
                            "entry_zone": fvg.midpoint,
                            "fvg_range": (fvg.low, fvg.high),
                            "timeframe": tf,
                            "reasoning": f"Bullish FVG on {tf} - First test complete, waiting for second test",
                            "action": "Enter long on second test of FVG",
                            "risk": "Low" if tf in ["D", "W", "M"] else "Medium"
                        })
                    elif fvg.type == "bearish" and htf_bias != "bullish":
                        setups.append({
                            "type": "SELL_FVG_RETEST",
                            "entry_zone": fvg.midpoint,
                            "fvg_range": (fvg.low, fvg.high),
                            "timeframe": tf,
                            "reasoning": f"Bearish FVG on {tf} - First test complete, waiting for second test",
                            "action": "Enter short on second test of FVG",
                            "risk": "Low" if tf in ["D", "W", "M"] else "Medium"
                        })
        
        return sorted(setups, key=lambda x: x.get("weight", 0), reverse=True)
    
    def analyze(self, symbol: str, timeframes: List[Timeframe] = None) -> MultiTimeframeAnalysis:
        """
        Perform complete multi-timeframe analysis
        
        Default timeframes: Monthly → Weekly → Daily → 4H → 1H
        """
        if timeframes is None:
            timeframes = [
                Timeframe.MONTHLY,
                Timeframe.WEEKLY,
                Timeframe.DAILY,
                Timeframe.FOUR_HOUR,
                Timeframe.ONE_HOUR
            ]
        
        # Get current price
        try:
            quote = self.fyers.get_quotes([symbol])
            current_price = quote["d"][0]["v"]["lp"] if quote and quote.get("d") else None
            
            # If Fyers quote fails, raise error instead of using mock data
            if not current_price:
                raise Exception("❌ Fyers API authentication required. No valid access token found.")
        except Exception as e:
            logger.error(f"❌ Failed to get spot price from Fyers: {e}")
            raise Exception(f"❌ Fyers authentication required. Please authenticate at /auth/url to get live data. Error: {str(e)}")
        
        # Analyze each timeframe
        analyses = {}
        for tf in timeframes:
            try:
                analysis = self.analyze_timeframe(symbol, tf)
                analyses[tf.value] = analysis
            except Exception as e:
                logger.error(f"Error analyzing {tf.value}: {e}")
        
        # Find confluence zones
        confluence = self.find_confluence_zones(analyses, current_price)
        
        # Generate trade setups
        setups = self.generate_trade_setups(analyses, confluence, current_price)
        
        # Determine overall bias
        biases = [a.bias for a in analyses.values()]
        bullish = biases.count("bullish")
        bearish = biases.count("bearish")
        
        if bullish > bearish + 1:
            overall_bias = "bullish"
        elif bearish > bullish + 1:
            overall_bias = "bearish"
        else:
            overall_bias = "neutral"
        
        return MultiTimeframeAnalysis(
            symbol=symbol,
            current_price=current_price,
            timestamp=datetime.now(),
            analyses=analyses,
            overall_bias=overall_bias,
            confluence_zones=confluence,
            trade_setups=setups
        )


# Singleton
mtf_analyzer = None

def get_mtf_analyzer(fyers_client):
    global mtf_analyzer
    if mtf_analyzer is None:
        mtf_analyzer = MultiTimeframeICTAnalyzer(fyers_client)
    return mtf_analyzer
