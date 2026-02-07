"""
Enhanced ICT Top-Down Analysis with AMD Detection

HIERARCHY:
1. HIGHER TIMEFRAME (HTF): Monthly, Weekly
   - Major liquidity zones (institutional levels)
   - Key support/resistance (swing highs/lows)
   - Overall market bias direction
   
2. MEDIUM TIMEFRAME (MTF): Daily, 4H
   - Day/Session ranges (Asian, London, NY)
   - 4H range identification
   - Premium/Discount zones
   - Current market phase identification
   
3. LOWER TIMEFRAME (LTF): 1H, 15min, 5min, 3min, 1min
   - Entry/Exit zones
   - AMD (Accumulation, Manipulation, Distribution) detection
   - Precise trigger points
   - Real-time manipulation alerts

FLOW:
1. HTF establishes WHAT to trade (direction)
2. MTF establishes WHEN to trade (session/range)  
3. LTF establishes WHERE to enter/exit (precise levels)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, time
from enum import Enum
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# TIMEFRAME DEFINITIONS
# ============================================================================

class TimeframeCategory(Enum):
    """Timeframe categories for top-down analysis"""
    HTF = "higher"    # Monthly, Weekly - Direction bias
    MTF = "medium"    # Daily, 4H - Session/Range context
    LTF = "lower"     # 1H to 1min - Entry/Exit timing


class Timeframe(Enum):
    """Individual timeframes with their properties"""
    MONTHLY = ("M", "D", 366, TimeframeCategory.HTF)
    WEEKLY = ("W", "D", 366, TimeframeCategory.HTF)
    DAILY = ("D", "D", 100, TimeframeCategory.MTF)
    FOUR_HOUR = ("240", "240", 60, TimeframeCategory.MTF)
    ONE_HOUR = ("60", "60", 30, TimeframeCategory.LTF)
    FIFTEEN_MIN = ("15", "15", 15, TimeframeCategory.LTF)
    FIVE_MIN = ("5", "5", 10, TimeframeCategory.LTF)
    THREE_MIN = ("3", "3", 5, TimeframeCategory.LTF)
    ONE_MIN = ("1", "1", 3, TimeframeCategory.LTF)
    
    def __init__(self, value, resolution, lookback_days, category):
        self._value_ = value
        self.resolution = resolution
        self.lookback_days = lookback_days
        self.category = category


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class LiquidityZone:
    """Major liquidity zone from HTF"""
    level: float
    zone_type: str  # "buy_side" (above) or "sell_side" (below)
    timeframe: str
    touches: int
    first_touch: datetime
    last_touch: datetime
    strength: float  # 0-100
    swept: bool = False
    sweep_time: Optional[datetime] = None


@dataclass
class RangeContext:
    """Session/Day range from MTF"""
    range_high: float
    range_low: float
    range_mid: float  # Equilibrium
    timeframe: str
    period_start: datetime
    period_end: Optional[datetime] = None
    current_position: str = "equilibrium"  # "premium", "discount", "equilibrium"
    expansion_phase: bool = False  # True if breaking out of range


@dataclass
class AMDPhase:
    """AMD (Accumulation, Manipulation, Distribution) detection"""
    phase: str  # "accumulation", "manipulation", "distribution"
    start_time: datetime
    end_time: Optional[datetime] = None
    key_level: float = 0
    manipulation_type: Optional[str] = None  # "bear_trap", "bull_trap", "stop_hunt"
    confidence: float = 0
    trade_signal: Optional[str] = None  # "BUY CALL", "BUY PUT"
    # Accumulation fields
    range_high: Optional[float] = None  # Top of accumulation range
    range_low: Optional[float] = None   # Bottom of accumulation range
    volume_ratio: Optional[float] = None  # Volume relative to average
    # Recovery after manipulation
    recovery_pts: float = 0  # Points recovered after manipulation (for bear/bull traps)
    # Distribution fields
    distribution_direction: Optional[str] = None  # "bullish" or "bearish"
    move_pct: Optional[float] = None  # Distribution move strength %


@dataclass
class EntryZone:
    """Precise entry zone from LTF"""
    entry_type: str  # "FVG_TEST", "OB_TEST", "AMD_REVERSAL", "RANGE_EXTREME"
    entry_price: float
    zone_low: float
    zone_high: float
    timeframe: str
    direction: str  # "long" or "short"
    stop_loss: float
    target_1: float
    target_2: float
    confidence: float
    trigger_condition: str  # Description of what confirms entry
    amd_phase: Optional[AMDPhase] = None


@dataclass
class TopDownAnalysis:
    """Complete top-down analysis result"""
    symbol: str
    current_price: float
    timestamp: datetime
    
    # HTF Analysis
    htf_bias: str  # "bullish", "bearish", "neutral"
    htf_liquidity_zones: List[LiquidityZone]
    htf_key_levels: Dict[str, float]  # {"weekly_high": x, "monthly_low": y, ...}
    
    # MTF Analysis
    mtf_range: RangeContext
    mtf_session: str  # "ASIA", "LONDON", "NY", "CLOSED"
    mtf_phase: str  # "expansion", "contraction", "ranging"
    
    # LTF Analysis
    ltf_entry_zones: List[EntryZone]
    ltf_amd_phases: List[AMDPhase]
    
    # Combined Signal
    recommended_action: str  # "BUY CALL", "BUY PUT", "WAIT"
    
    # Optional fields with defaults (must come after required fields)
    active_manipulation: Optional[AMDPhase] = None
    entry_zone: Optional[EntryZone] = None
    confidence: float = 0
    reasoning: str = ""
    
    # Full AMD Phase Detection
    accumulation_zones: Optional[List[Dict]] = None  # Detected accumulation ranges
    distribution_zones: Optional[List[Dict]] = None  # Detected distribution moves
    amd_sequence: Optional[Dict] = None  # Full A→M→D sequence if detected


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_session() -> str:
    """Determine current trading session based on IST time"""
    now = datetime.now()
    ist_time = now.time()
    
    # IST session times (India Standard Time = UTC+5:30)
    # Asian Session: 05:30 - 09:00 IST
    # London Session: 13:00 - 17:30 IST
    # NY Session: 18:00 - 01:00 IST
    # Indian Market: 09:15 - 15:30 IST
    
    if time(9, 15) <= ist_time <= time(15, 30):
        return "INDIAN"
    elif time(5, 30) <= ist_time <= time(9, 0):
        return "ASIA"
    elif time(13, 0) <= ist_time <= time(17, 30):
        return "LONDON"
    elif time(18, 0) <= ist_time or ist_time <= time(1, 0):
        return "NY"
    else:
        return "CLOSED"


def get_swing_points(df: pd.DataFrame, lookback: int = 5) -> Tuple[List[Dict], List[Dict]]:
    """Identify swing highs and swing lows"""
    swing_highs = []
    swing_lows = []
    
    for i in range(lookback, len(df) - lookback):
        # Swing High
        if df['high'].iloc[i] == df['high'].iloc[i-lookback:i+lookback+1].max():
            swing_highs.append({
                'price': df['high'].iloc[i],
                'time': df.index[i],
                'index': i
            })
        
        # Swing Low
        if df['low'].iloc[i] == df['low'].iloc[i-lookback:i+lookback+1].min():
            swing_lows.append({
                'price': df['low'].iloc[i],
                'time': df.index[i],
                'index': i
            })
    
    return swing_highs, swing_lows


def find_equal_levels(prices: pd.Series, tolerance_pct: float = 0.001) -> List[Dict]:
    """Find equal highs or equal lows (liquidity pools)"""
    levels = []
    values = prices.values
    indices = prices.index
    tolerance = prices.mean() * tolerance_pct
    
    for i in range(len(values)):
        touches = []
        for j in range(len(values)):
            if i != j and abs(values[i] - values[j]) < tolerance:
                touches.append({'time': indices[j], 'price': values[j]})
        
        if len(touches) >= 2:  # At least 3 total touches (including original)
            levels.append({
                'level': values[i],
                'touches': len(touches) + 1,
                'times': [indices[i]] + [t['time'] for t in touches]
            })
    
    # Remove duplicates
    seen = set()
    unique_levels = []
    for level in sorted(levels, key=lambda x: x['touches'], reverse=True):
        rounded = round(level['level'], 0)
        if rounded not in seen:
            seen.add(rounded)
            unique_levels.append(level)
    
    return unique_levels


# ============================================================================
# HTF ANALYZER
# ============================================================================

class HTFAnalyzer:
    """
    Higher Timeframe Analyzer
    
    Purpose: Establish overall market bias and identify major liquidity zones
    Timeframes: Monthly, Weekly
    """
    
    def __init__(self, fyers_client):
        self.fyers = fyers_client
    
    def get_data(self, symbol: str, timeframe: Timeframe) -> Optional[pd.DataFrame]:
        """Fetch and aggregate HTF data"""
        try:
            days = timeframe.lookback_days
            resolution = timeframe.resolution
            
            date_to = datetime.now()
            date_from = date_to - timedelta(days=days)
            
            df = self.fyers.get_historical_data(
                symbol=symbol,
                resolution=resolution,
                date_from=date_from,
                date_to=date_to
            )
            
            if df is None or df.empty:
                logger.warning(f"No data for {symbol} {timeframe.value}")
                return None
            
            # Aggregate to weekly/monthly if needed
            if timeframe == Timeframe.MONTHLY:
                df = df.resample('ME').agg({
                    'open': 'first', 'high': 'max', 
                    'low': 'min', 'close': 'last', 'volume': 'sum'
                }).dropna()
            elif timeframe == Timeframe.WEEKLY:
                df = df.resample('W').agg({
                    'open': 'first', 'high': 'max',
                    'low': 'min', 'close': 'last', 'volume': 'sum'
                }).dropna()
            
            return df
        except Exception as e:
            logger.error(f"Error fetching HTF data: {e}")
            return None
    
    def identify_liquidity_zones(self, df: pd.DataFrame, timeframe: str, current_price: float) -> List[LiquidityZone]:
        """Identify major liquidity zones from HTF data"""
        zones = []
        
        # Find equal highs (buy-side liquidity)
        buy_side = find_equal_levels(df['high'])
        for level_data in buy_side[:5]:  # Top 5
            if level_data['level'] > current_price:  # Only above current price
                zones.append(LiquidityZone(
                    level=level_data['level'],
                    zone_type="buy_side",
                    timeframe=timeframe,
                    touches=level_data['touches'],
                    first_touch=level_data['times'][0],
                    last_touch=level_data['times'][-1],
                    strength=min(100, level_data['touches'] * 25)
                ))
        
        # Find equal lows (sell-side liquidity)
        sell_side = find_equal_levels(df['low'])
        for level_data in sell_side[:5]:  # Top 5
            if level_data['level'] < current_price:  # Only below current price
                zones.append(LiquidityZone(
                    level=level_data['level'],
                    zone_type="sell_side",
                    timeframe=timeframe,
                    touches=level_data['touches'],
                    first_touch=level_data['times'][0],
                    last_touch=level_data['times'][-1],
                    strength=min(100, level_data['touches'] * 25)
                ))
        
        return zones
    
    def determine_bias(self, monthly_df: pd.DataFrame, weekly_df: pd.DataFrame, current_price: float) -> Tuple[str, float]:
        """Determine HTF bias from Monthly and Weekly structure"""
        
        # Get swing points
        m_highs, m_lows = get_swing_points(monthly_df, lookback=1) if monthly_df is not None else ([], [])
        w_highs, w_lows = get_swing_points(weekly_df, lookback=2) if weekly_df is not None else ([], [])
        
        bullish_score = 0
        bearish_score = 0
        
        # Monthly structure (weight: 50%)
        if len(m_highs) >= 2 and len(m_lows) >= 2:
            # Higher highs and higher lows = bullish
            if m_highs[-1]['price'] > m_highs[-2]['price'] and m_lows[-1]['price'] > m_lows[-2]['price']:
                bullish_score += 50
            # Lower highs and lower lows = bearish
            elif m_highs[-1]['price'] < m_highs[-2]['price'] and m_lows[-1]['price'] < m_lows[-2]['price']:
                bearish_score += 50
        
        # Weekly structure (weight: 50%)
        if len(w_highs) >= 2 and len(w_lows) >= 2:
            if w_highs[-1]['price'] > w_highs[-2]['price'] and w_lows[-1]['price'] > w_lows[-2]['price']:
                bullish_score += 50
            elif w_highs[-1]['price'] < w_highs[-2]['price'] and w_lows[-1]['price'] < w_lows[-2]['price']:
                bearish_score += 50
        
        # Determine bias
        if bullish_score > bearish_score + 20:
            return "bullish", bullish_score
        elif bearish_score > bullish_score + 20:
            return "bearish", bearish_score
        else:
            return "neutral", max(bullish_score, bearish_score)
    
    def get_key_levels(self, monthly_df: pd.DataFrame, weekly_df: pd.DataFrame) -> Dict[str, float]:
        """Get key HTF levels for reference"""
        levels = {}
        
        if monthly_df is not None and not monthly_df.empty:
            levels['monthly_high'] = monthly_df['high'].iloc[-1]
            levels['monthly_low'] = monthly_df['low'].iloc[-1]
            levels['prev_monthly_high'] = monthly_df['high'].iloc[-2] if len(monthly_df) > 1 else None
            levels['prev_monthly_low'] = monthly_df['low'].iloc[-2] if len(monthly_df) > 1 else None
        
        if weekly_df is not None and not weekly_df.empty:
            levels['weekly_high'] = weekly_df['high'].iloc[-1]
            levels['weekly_low'] = weekly_df['low'].iloc[-1]
            levels['prev_weekly_high'] = weekly_df['high'].iloc[-2] if len(weekly_df) > 1 else None
            levels['prev_weekly_low'] = weekly_df['low'].iloc[-2] if len(weekly_df) > 1 else None
        
        return levels
    
    def analyze(self, symbol: str, current_price: float, candles: Dict = None) -> Dict:
        """Run complete HTF analysis
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            candles: Optional pre-fetched candles dict with 'M'/'W' keys to avoid duplicate API calls
        """
        logger.info("=" * 60)
        logger.info("📊 HTF ANALYSIS (Monthly/Weekly)")
        logger.info("=" * 60)
        
        # Fetch data (use pre-fetched candles if available to avoid duplicate API calls)
        if candles:
            monthly_df = candles.get('M')
            weekly_df = candles.get('W')
            logger.info("   ✅ Using pre-fetched HTF candles (M/W)")
        else:
            monthly_df = self.get_data(symbol, Timeframe.MONTHLY)
            weekly_df = self.get_data(symbol, Timeframe.WEEKLY)
        
        # Get liquidity zones
        liquidity_zones = []
        if monthly_df is not None:
            liquidity_zones.extend(self.identify_liquidity_zones(monthly_df, "M", current_price))
        if weekly_df is not None:
            liquidity_zones.extend(self.identify_liquidity_zones(weekly_df, "W", current_price))
        
        # Determine bias
        bias, strength = self.determine_bias(monthly_df, weekly_df, current_price)
        
        # Get key levels
        key_levels = self.get_key_levels(monthly_df, weekly_df)
        
        logger.info(f"   HTF Bias: {bias.upper()} (strength: {strength})")
        logger.info(f"   Liquidity Zones: {len(liquidity_zones)}")
        logger.info(f"   Key Levels: {len(key_levels)}")
        
        return {
            'bias': bias,
            'strength': strength,
            'liquidity_zones': liquidity_zones,
            'key_levels': key_levels
        }


# ============================================================================
# MTF ANALYZER
# ============================================================================

class MTFAnalyzer:
    """
    Medium Timeframe Analyzer
    
    Purpose: Identify current session range and market phase
    Timeframes: Daily, 4H
    """
    
    def __init__(self, fyers_client):
        self.fyers = fyers_client
    
    def get_data(self, symbol: str, timeframe: Timeframe) -> Optional[pd.DataFrame]:
        """Fetch MTF data"""
        try:
            days = timeframe.lookback_days
            resolution = timeframe.resolution
            
            date_to = datetime.now()
            date_from = date_to - timedelta(days=days)
            
            df = self.fyers.get_historical_data(
                symbol=symbol,
                resolution=resolution,
                date_from=date_from,
                date_to=date_to
            )
            
            return df
        except Exception as e:
            logger.error(f"Error fetching MTF data: {e}")
            return None
    
    def identify_range(self, df: pd.DataFrame, timeframe: str, current_price: float) -> RangeContext:
        """Identify the current range context"""
        if df is None or df.empty:
            return RangeContext(
                range_high=current_price * 1.01,
                range_low=current_price * 0.99,
                range_mid=current_price,
                timeframe=timeframe,
                period_start=datetime.now()
            )
        
        # For Daily: Use today's range
        # For 4H: Use last few 4H candles
        if timeframe == "D":
            # Today's range
            today_df = df[df.index.date == datetime.now().date()]
            if not today_df.empty:
                range_high = today_df['high'].max()
                range_low = today_df['low'].min()
            else:
                # Use previous day
                range_high = df['high'].iloc[-1]
                range_low = df['low'].iloc[-1]
            period_start = datetime.combine(datetime.now().date(), time(9, 15))
        else:
            # 4H range - last 2-3 candles form the range
            range_high = df['high'].iloc[-3:].max()
            range_low = df['low'].iloc[-3:].min()
            period_start = df.index[-3]
        
        range_mid = (range_high + range_low) / 2
        
        # Determine current position
        if current_price > range_mid + (range_high - range_mid) * 0.3:
            position = "premium"
        elif current_price < range_mid - (range_mid - range_low) * 0.3:
            position = "discount"
        else:
            position = "equilibrium"
        
        # Check for expansion
        prev_range_high = df['high'].iloc[-4:-1].max() if len(df) > 4 else range_high
        prev_range_low = df['low'].iloc[-4:-1].min() if len(df) > 4 else range_low
        expansion = current_price > prev_range_high or current_price < prev_range_low
        
        return RangeContext(
            range_high=range_high,
            range_low=range_low,
            range_mid=range_mid,
            timeframe=timeframe,
            period_start=period_start,
            current_position=position,
            expansion_phase=expansion
        )
    
    def determine_phase(self, daily_df: pd.DataFrame, four_h_df: pd.DataFrame) -> str:
        """Determine current market phase"""
        if four_h_df is None or daily_df is None:
            return "ranging"
        
        # Check if market is trending or ranging
        if len(four_h_df) < 5:
            return "ranging"
        
        # Calculate recent volatility vs average
        recent_range = four_h_df['high'].iloc[-5:].max() - four_h_df['low'].iloc[-5:].min()
        avg_candle_range = (four_h_df['high'] - four_h_df['low']).mean()
        
        # Check directional move
        price_change = four_h_df['close'].iloc[-1] - four_h_df['close'].iloc[-5]
        
        if abs(price_change) > recent_range * 0.5:
            return "expansion"  # Strong directional move
        elif recent_range < avg_candle_range * 0.7:
            return "contraction"  # Squeeze before move
        else:
            return "ranging"
    
    def analyze(self, symbol: str, current_price: float, candles: Dict = None) -> Dict:
        """Run complete MTF analysis
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            candles: Optional pre-fetched candles dict with 'D'/'240' keys
        """
        logger.info("=" * 60)
        logger.info("📊 MTF ANALYSIS (Daily/4H)")
        logger.info("=" * 60)
        
        # Fetch data (use pre-fetched candles if available)
        if candles:
            daily_df = candles.get('D')
            four_h_df = candles.get('240') or candles.get('4H')
            logger.info("   ✅ Using pre-fetched MTF candles (D/4H)")
        else:
            daily_df = self.get_data(symbol, Timeframe.DAILY)
            four_h_df = self.get_data(symbol, Timeframe.FOUR_HOUR)
        
        # Get range context from 4H (more relevant for intraday)
        range_context = self.identify_range(four_h_df, "240", current_price)
        
        # Get session
        session = get_current_session()
        
        # Determine phase
        phase = self.determine_phase(daily_df, four_h_df)
        
        logger.info(f"   Session: {session}")
        logger.info(f"   4H Range: {range_context.range_low:.2f} - {range_context.range_high:.2f}")
        logger.info(f"   Position: {range_context.current_position.upper()}")
        logger.info(f"   Phase: {phase.upper()}")
        
        return {
            'range': range_context,
            'session': session,
            'phase': phase,
            'daily_df': daily_df,
            'four_h_df': four_h_df
        }


# ============================================================================
# LTF ANALYZER WITH AMD DETECTION
# ============================================================================

class LTFAnalyzer:
    """
    Lower Timeframe Analyzer with AMD Detection
    
    Purpose: Identify precise entry/exit zones and detect manipulation
    Timeframes: 1H, 15min, 5min, 3min, 1min
    
    AMD Phases:
    1. Accumulation: Smart money building positions (ranging, low volume)
    2. Manipulation: False breakout to trap retail (stop hunt)
    3. Distribution: Smart money taking profits (reversal)
    """
    
    def __init__(self, fyers_client):
        self.fyers = fyers_client
    
    def get_data(self, symbol: str, timeframe: Timeframe) -> Optional[pd.DataFrame]:
        """Fetch LTF data"""
        try:
            days = timeframe.lookback_days
            resolution = timeframe.resolution
            
            date_to = datetime.now()
            date_from = date_to - timedelta(days=days)
            
            df = self.fyers.get_historical_data(
                symbol=symbol,
                resolution=resolution,
                date_from=date_from,
                date_to=date_to
            )
            
            return df
        except Exception as e:
            logger.error(f"Error fetching LTF data: {e}")
            return None
    
    def detect_accumulation(self, df: pd.DataFrame, lookback: int = 10) -> List[Dict]:
        """
        Detect accumulation phase (smart money building positions):
        - Price in tight range (consolidation)
        - Lower than average volume (quiet building)
        - Multiple tests of same level (establishing range)
        - Returns range levels that become key levels for manipulation detection
        """
        if df is None or len(df) < lookback:
            return []
        
        accumulations = []
        
        for i in range(lookback, len(df)):
            window = df.iloc[i-lookback:i]
            
            # Check for tight range (consolidation)
            range_high = window['high'].max()
            range_low = window['low'].min()
            range_mid = (range_high + range_low) / 2
            range_size = (range_high - range_low) / window['close'].mean()
            avg_range = (df['high'] - df['low']).mean() / df['close'].mean()
            
            # Check for low volume (quiet accumulation)
            avg_volume = df['volume'].mean()
            window_volume = window['volume'].mean()
            
            # Count tests of range boundaries (level retests)
            tolerance = (range_high - range_low) * 0.1  # 10% of range
            high_tests = sum(1 for _, row in window.iterrows() 
                           if abs(row['high'] - range_high) < tolerance)
            low_tests = sum(1 for _, row in window.iterrows() 
                          if abs(row['low'] - range_low) < tolerance)
            level_tests = high_tests + low_tests
            
            if range_size < avg_range * 0.6 and window_volume < avg_volume * 0.8:
                # Calculate confidence based on multiple factors
                conf = 40
                if window_volume < avg_volume * 0.5:
                    conf += 15  # Very low volume = stronger accumulation
                if range_size < avg_range * 0.3:
                    conf += 10  # Very tight range
                if level_tests >= 4:
                    conf += 15  # Multiple level tests = established range
                elif level_tests >= 2:
                    conf += 8
                
                # Determine if accumulation is near end (volume starting to pick up)
                last_3_vol = window['volume'].iloc[-3:].mean() if len(window) >= 3 else window_volume
                breakout_imminent = last_3_vol > window_volume * 1.2
                
                accumulations.append({
                    'start_time': window.index[0],
                    'end_time': window.index[-1],
                    'range_high': float(range_high),
                    'range_low': float(range_low),
                    'range_mid': float(range_mid),
                    'range_size_pct': float(range_size * 100),
                    'volume_ratio': float(window_volume / avg_volume) if avg_volume > 0 else 0,
                    'level_tests': level_tests,
                    'confidence': min(conf, 90),
                    'breakout_imminent': breakout_imminent
                })
        
        # Deduplicate overlapping accumulation zones
        if len(accumulations) > 1:
            merged = [accumulations[0]]
            for acc in accumulations[1:]:
                prev = merged[-1]
                # If ranges overlap significantly, keep the higher confidence one
                if (abs(acc['range_high'] - prev['range_high']) / prev['range_high'] < 0.002 and
                    abs(acc['range_low'] - prev['range_low']) / prev['range_low'] < 0.002):
                    if acc['confidence'] > prev['confidence']:
                        merged[-1] = acc
                else:
                    merged.append(acc)
            accumulations = merged
        
        return accumulations[-5:] if accumulations else []
    
    def detect_manipulation(self, df: pd.DataFrame, key_levels: List[float], 
                           htf_zones: List[LiquidityZone]) -> List[AMDPhase]:
        """
        Detect manipulation (stop hunt / false breakout):
        - Quick break below/above key level
        - Immediate reversal
        - Often low volume on break, high on reversal
        
        This is the KEY function for AMD detection!
        """
        if df is None or len(df) < 10:
            return []
        
        manipulations = []
        avg_volume = df['volume'].mean()
        
        # === METHOD 1: Level-based detection ===
        # Combine key levels from HTF zones
        all_levels = key_levels.copy() if key_levels else []
        for zone in htf_zones:
            all_levels.append(zone.level)
        
        # Also find LTF swing points as potential manipulation targets
        swing_highs, swing_lows = get_swing_points(df, lookback=3)
        for sh in swing_highs[-5:]:
            all_levels.append(sh['price'])
        for sl in swing_lows[-5:]:
            all_levels.append(sl['price'])
        
        # Remove duplicates and sort
        all_levels = sorted(set([round(l, 0) for l in all_levels if l is not None]))
        
        # === METHOD 2: Direct pattern detection (CRITICAL for intraday) ===
        # This detects manipulation without needing predefined levels
        day_low = df['low'].min()
        day_high = df['high'].max()
        
        for i in range(5, len(df) - 3):
            current = df.iloc[i]
            low_i = current['low']
            high_i = current['high']
            close_i = current['close']
            open_i = current['open']
            vol_i = current['volume']
            
            # === BEAR TRAP: New local low with immediate recovery ===
            # Check if this makes a new local low
            is_local_low = all(df.iloc[j]['low'] > low_i for j in range(max(0, i-5), i))
            
            if is_local_low and low_i < day_low + (day_high - day_low) * 0.15:
                # Check recovery in next candles
                next_candles = df.iloc[i+1:min(i+6, len(df))]
                if not next_candles.empty:
                    recovery_high = next_candles['high'].max()
                    recovery_pts = recovery_high - low_i
                    
                    # Minimum 15 points recovery (or 0.06% for any index)
                    min_recovery = max(15, day_low * 0.0006)
                    
                    if recovery_pts > min_recovery:
                        # Calculate confidence
                        confidence = 50
                        
                        # Long lower wick on break candle = stronger rejection
                        candle_range = high_i - low_i
                        if candle_range > 0:
                            lower_wick = min(close_i, open_i) - low_i
                            lower_wick_ratio = lower_wick / candle_range
                            if lower_wick_ratio > 0.5:
                                confidence += 20  # Strong rejection wick
                        
                        # High volume on recovery = confirmation
                        if not next_candles.empty and next_candles['volume'].max() > avg_volume * 1.3:
                            confidence += 15
                        
                        # Close above open (bullish) on recovery
                        if not next_candles.empty and next_candles.iloc[0]['close'] > next_candles.iloc[0]['open']:
                            confidence += 10
                        
                        manipulations.append(AMDPhase(
                            phase="manipulation",
                            start_time=current.name,
                            end_time=next_candles.index[-1] if not next_candles.empty else None,
                            key_level=low_i,
                            manipulation_type="bear_trap",
                            confidence=min(95, confidence),
                            trade_signal="BUY CALL",
                            recovery_pts=recovery_pts
                        ))
            
            # === BULL TRAP: New local high with immediate rejection ===
            is_local_high = all(df.iloc[j]['high'] < high_i for j in range(max(0, i-5), i))
            
            if is_local_high and high_i > day_high - (day_high - day_low) * 0.15:
                next_candles = df.iloc[i+1:min(i+6, len(df))]
                if not next_candles.empty:
                    rejection_low = next_candles['low'].min()
                    rejection_pts = high_i - rejection_low
                    
                    min_rejection = max(15, day_high * 0.0006)
                    
                    if rejection_pts > min_rejection:
                        confidence = 50
                        
                        # Long upper wick on break candle
                        candle_range = high_i - low_i
                        if candle_range > 0:
                            upper_wick = high_i - max(close_i, open_i)
                            upper_wick_ratio = upper_wick / candle_range
                            if upper_wick_ratio > 0.5:
                                confidence += 20
                        
                        if not next_candles.empty and next_candles['volume'].max() > avg_volume * 1.3:
                            confidence += 15
                        
                        if not next_candles.empty and next_candles.iloc[0]['close'] < next_candles.iloc[0]['open']:
                            confidence += 10
                        
                        manipulations.append(AMDPhase(
                            phase="manipulation",
                            start_time=current.name,
                            end_time=next_candles.index[-1] if not next_candles.empty else None,
                            key_level=high_i,
                            manipulation_type="bull_trap",
                            confidence=min(95, confidence),
                            trade_signal="BUY PUT",
                            recovery_pts=rejection_pts
                        ))
        
        for level in all_levels:
            # Look for manipulation events at this level
            tolerance = df['close'].mean() * 0.002  # 0.2%
            
            for i in range(3, len(df) - 2):
                current = df.iloc[i]
                prev_candles = df.iloc[i-3:i]
                next_candles = df.iloc[i+1:i+3]
                
                # BEAR TRAP: Break below level then recover
                if current['low'] < level - tolerance:
                    # Previous candles were above
                    if all(prev_candles['close'] >= level - tolerance):
                        # Next candles recover above
                        if len(next_candles) >= 2 and all(next_candles['close'] >= level):
                            # Volume analysis
                            break_volume = current['volume']
                            avg_volume = df['volume'].iloc[:i].mean()
                            recovery_volume = next_candles['volume'].mean()
                            
                            # Low volume break + higher volume recovery = manipulation
                            confidence = 50
                            if break_volume < avg_volume * 0.8:
                                confidence += 15  # Low volume break
                            if recovery_volume > avg_volume * 1.2:
                                confidence += 20  # High volume recovery
                            
                            manipulations.append(AMDPhase(
                                phase="manipulation",
                                start_time=current.name,
                                end_time=next_candles.index[-1] if len(next_candles) > 0 else None,
                                key_level=level,
                                manipulation_type="bear_trap",
                                confidence=min(95, confidence),
                                trade_signal="BUY CALL"
                            ))
                
                # BULL TRAP: Break above level then reject
                if current['high'] > level + tolerance:
                    if all(prev_candles['close'] <= level + tolerance):
                        if len(next_candles) >= 2 and all(next_candles['close'] <= level):
                            break_volume = current['volume']
                            avg_volume = df['volume'].iloc[:i].mean()
                            recovery_volume = next_candles['volume'].mean()
                            
                            confidence = 50
                            if break_volume < avg_volume * 0.8:
                                confidence += 15
                            if recovery_volume > avg_volume * 1.2:
                                confidence += 20
                            
                            manipulations.append(AMDPhase(
                                phase="manipulation",
                                start_time=current.name,
                                end_time=next_candles.index[-1] if len(next_candles) > 0 else None,
                                key_level=level,
                                manipulation_type="bull_trap",
                                confidence=min(95, confidence),
                                trade_signal="BUY PUT"
                            ))
        
        # Deduplicate manipulations by time (keep highest confidence)
        seen_times = {}
        for m in manipulations:
            time_key = str(m.start_time)[:16]  # Round to minute
            if time_key not in seen_times or m.confidence > seen_times[time_key].confidence:
                seen_times[time_key] = m
        
        unique_manips = list(seen_times.values())
        
        # Return sorted by time (most recent first)
        return sorted(unique_manips, key=lambda x: x.start_time, reverse=True)[:10]
    
    def detect_distribution(self, df: pd.DataFrame, recent_manip: Optional[AMDPhase],
                            accumulation_zones: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Detect distribution phase (smart money taking profits / real move):
        - After manipulation, price moves decisively in the "true" direction
        - Increased volume on the move (commitment)
        - Clear directional candles (strong bodies, small wicks)
        - If follows manipulation, the direction confirms the trap
        
        ICT Context:
        - bear_trap manipulation → bullish distribution (the real move is UP)
        - bull_trap manipulation → bearish distribution (the real move is DOWN)
        """
        if df is None or len(df) < 5:
            return []
        
        distributions = []
        avg_vol = df['volume'].mean()
        avg_candle_range = (df['high'] - df['low']).mean()
        
        # Look for strong directional moves
        for i in range(3, len(df)):
            window = df.iloc[i-3:i+1]
            
            # Calculate move strength
            move = window['close'].iloc[-1] - window['close'].iloc[0]
            move_pct = abs(move) / window['close'].iloc[0] * 100
            
            # Check for volume increase (commitment to the move)
            window_vol = window['volume'].mean()
            
            # Check candle quality - strong bodies vs wicks
            body_ratios = []
            for _, candle in window.iterrows():
                candle_range = candle['high'] - candle['low']
                if candle_range > 0:
                    body = abs(candle['close'] - candle['open'])
                    body_ratios.append(body / candle_range)
            avg_body_ratio = sum(body_ratios) / len(body_ratios) if body_ratios else 0
            
            # Count directional candles (how many candles agree with the move)
            if move > 0:
                directional_count = sum(1 for _, c in window.iterrows() if c['close'] > c['open'])
            else:
                directional_count = sum(1 for _, c in window.iterrows() if c['close'] < c['open'])
            
            if move_pct > 0.2 and window_vol > avg_vol * 1.2:
                direction = 'bullish' if move > 0 else 'bearish'
                
                # Calculate confidence
                conf = 40
                if move_pct > 0.5:
                    conf += 10  # Strong move
                if move_pct > 0.8:
                    conf += 10  # Very strong move
                if window_vol > avg_vol * 1.8:
                    conf += 15  # High volume commitment
                elif window_vol > avg_vol * 1.4:
                    conf += 8
                if avg_body_ratio > 0.6:
                    conf += 10  # Strong candle bodies (conviction)
                if directional_count >= 3:
                    conf += 10  # Most candles agree with direction
                
                # Check if distribution follows a manipulation (A→M→D sequence)
                follows_manipulation = False
                confirms_trap = False
                if recent_manip:
                    manip_end = recent_manip.end_time or recent_manip.start_time
                    if isinstance(manip_end, pd.Timestamp):
                        manip_end_dt = manip_end.to_pydatetime()
                    else:
                        manip_end_dt = manip_end
                    
                    dist_start = window.index[0]
                    if isinstance(dist_start, pd.Timestamp):
                        dist_start_dt = dist_start.to_pydatetime()
                    else:
                        dist_start_dt = dist_start
                    
                    # Distribution should follow manipulation (within 60 min)
                    time_gap = (dist_start_dt - manip_end_dt).total_seconds()
                    if 0 <= time_gap <= 3600:  # Within 1 hour after manipulation
                        follows_manipulation = True
                        conf += 10
                        
                        # Check if distribution confirms the trap direction
                        # bear_trap → expect bullish distribution
                        # bull_trap → expect bearish distribution
                        if (recent_manip.manipulation_type == 'bear_trap' and direction == 'bullish'):
                            confirms_trap = True
                            conf += 15  # Full A→M→D confirmation!
                        elif (recent_manip.manipulation_type == 'bull_trap' and direction == 'bearish'):
                            confirms_trap = True
                            conf += 15  # Full A→M→D confirmation!
                
                # Check if distribution breaks out of accumulation range
                breaks_accumulation = False
                if accumulation_zones:
                    for acc in accumulation_zones:
                        if (direction == 'bullish' and window['close'].iloc[-1] > acc['range_high']):
                            breaks_accumulation = True
                            conf += 8
                        elif (direction == 'bearish' and window['close'].iloc[-1] < acc['range_low']):
                            breaks_accumulation = True
                            conf += 8
                
                distributions.append({
                    'start_time': window.index[0],
                    'end_time': window.index[-1],
                    'direction': direction,
                    'move_pct': float(move_pct),
                    'volume_ratio': float(window_vol / avg_vol) if avg_vol > 0 else 0,
                    'avg_body_ratio': float(avg_body_ratio),
                    'directional_candles': directional_count,
                    'confidence': min(conf, 95),
                    'follows_manipulation': follows_manipulation,
                    'confirms_trap': confirms_trap,
                    'breaks_accumulation': breaks_accumulation
                })
        
        # Deduplicate overlapping distributions
        if len(distributions) > 1:
            merged = [distributions[0]]
            for dist in distributions[1:]:
                prev = merged[-1]
                # If times overlap, keep the higher confidence one
                if dist['start_time'] <= prev['end_time']:
                    if dist['confidence'] > prev['confidence']:
                        merged[-1] = dist
                else:
                    merged.append(dist)
            distributions = merged
        
        return distributions[-5:] if distributions else []
    
    def find_entry_zones(self, df: pd.DataFrame, htf_bias: str, mtf_range: RangeContext,
                        amd_phases: List[AMDPhase]) -> List[EntryZone]:
        """Find precise entry zones based on AMD and structure"""
        if df is None or len(df) < 5:
            return []
        
        entry_zones = []
        current_price = df['close'].iloc[-1]
        
        # 1. Entry from recent manipulation (highest priority)
        for manip in amd_phases[:2]:  # Most recent 2
            if manip.confidence >= 60:
                if manip.manipulation_type == "bear_trap":
                    entry_zones.append(EntryZone(
                        entry_type="AMD_REVERSAL",
                        entry_price=manip.key_level,
                        zone_low=manip.key_level * 0.998,
                        zone_high=manip.key_level * 1.002,
                        timeframe=df.index.freqstr if hasattr(df.index, 'freqstr') else "LTF",
                        direction="long",
                        stop_loss=manip.key_level * 0.995,
                        target_1=manip.key_level * 1.01,
                        target_2=manip.key_level * 1.02,
                        confidence=manip.confidence,
                        trigger_condition="Enter on break above manipulation low recovery",
                        amd_phase=manip
                    ))
                elif manip.manipulation_type == "bull_trap":
                    entry_zones.append(EntryZone(
                        entry_type="AMD_REVERSAL",
                        entry_price=manip.key_level,
                        zone_low=manip.key_level * 0.998,
                        zone_high=manip.key_level * 1.002,
                        timeframe=df.index.freqstr if hasattr(df.index, 'freqstr') else "LTF",
                        direction="short",
                        stop_loss=manip.key_level * 1.005,
                        target_1=manip.key_level * 0.99,
                        target_2=manip.key_level * 0.98,
                        confidence=manip.confidence,
                        trigger_condition="Enter on break below manipulation high rejection",
                        amd_phase=manip
                    ))
        
        # 2. Entry at MTF range extremes (if aligned with HTF)
        if mtf_range.current_position == "discount" and htf_bias in ["bullish", "neutral"]:
            entry_zones.append(EntryZone(
                entry_type="RANGE_EXTREME",
                entry_price=mtf_range.range_low,
                zone_low=mtf_range.range_low * 0.998,
                zone_high=mtf_range.range_low * 1.005,
                timeframe="MTF",
                direction="long",
                stop_loss=mtf_range.range_low * 0.99,
                target_1=mtf_range.range_mid,
                target_2=mtf_range.range_high,
                confidence=60 if htf_bias == "bullish" else 45,
                trigger_condition="Enter long at 4H range low with bullish confirmation"
            ))
        elif mtf_range.current_position == "premium" and htf_bias in ["bearish", "neutral"]:
            entry_zones.append(EntryZone(
                entry_type="RANGE_EXTREME",
                entry_price=mtf_range.range_high,
                zone_low=mtf_range.range_high * 0.995,
                zone_high=mtf_range.range_high * 1.002,
                timeframe="MTF",
                direction="short",
                stop_loss=mtf_range.range_high * 1.01,
                target_1=mtf_range.range_mid,
                target_2=mtf_range.range_low,
                confidence=60 if htf_bias == "bearish" else 45,
                trigger_condition="Enter short at 4H range high with bearish confirmation"
            ))
        
        return sorted(entry_zones, key=lambda x: x.confidence, reverse=True)
    
    def detect_amd_sequence(self, accumulations: List[Dict], manipulations: List[AMDPhase],
                            distributions: List[Dict]) -> Optional[Dict]:
        """
        Detect a complete A→M→D sequence (the holy grail of ICT trading).
        
        A valid sequence:
        1. Accumulation (consolidation range) forms first
        2. Manipulation (false breakout / trap) breaks the range
        3. Distribution (real move) follows in opposite direction
        
        Finding a complete sequence significantly boosts confidence.
        """
        if not accumulations or not manipulations:
            return None
        
        best_sequence = None
        best_score = 0
        
        for acc in accumulations:
            acc_end = acc['end_time']
            acc_high = acc['range_high']
            acc_low = acc['range_low']
            
            # Find manipulation that broke the accumulation range
            for manip in manipulations:
                manip_start = manip.start_time
                
                # Manipulation should come after or near end of accumulation
                try:
                    if isinstance(acc_end, pd.Timestamp):
                        acc_end_dt = acc_end.to_pydatetime()
                    else:
                        acc_end_dt = acc_end
                    if isinstance(manip_start, pd.Timestamp):
                        manip_start_dt = manip_start.to_pydatetime()
                    else:
                        manip_start_dt = manip_start
                    
                    time_gap_am = (manip_start_dt - acc_end_dt).total_seconds()
                    if time_gap_am < -300 or time_gap_am > 7200:  # -5min to +2hr window
                        continue
                except:
                    continue
                
                # Check if manipulation broke the accumulation range
                manip_near_range = False
                if manip.manipulation_type == 'bear_trap':
                    # Bear trap should break below accumulation low
                    if manip.key_level <= acc_low * 1.002:  # Within 0.2%
                        manip_near_range = True
                elif manip.manipulation_type == 'bull_trap':
                    # Bull trap should break above accumulation high
                    if manip.key_level >= acc_high * 0.998:
                        manip_near_range = True
                
                if not manip_near_range:
                    continue
                
                # Score this A→M pair
                score = acc['confidence'] + manip.confidence
                
                # Look for distribution that confirms the sequence
                matching_dist = None
                if distributions:
                    expected_dir = 'bullish' if manip.manipulation_type == 'bear_trap' else 'bearish'
                    
                    for dist in distributions:
                        if dist.get('follows_manipulation') and dist.get('direction') == expected_dir:
                            matching_dist = dist
                            score += dist['confidence']
                            break
                        elif dist.get('direction') == expected_dir:
                            # Even without explicit follows_manipulation flag, check timing
                            matching_dist = dist
                            score += dist['confidence'] * 0.7
                            break
                
                if score > best_score:
                    best_score = score
                    best_sequence = {
                        'found': True,
                        'accumulation': {
                            'range_high': acc['range_high'],
                            'range_low': acc['range_low'],
                            'start_time': str(acc['start_time']),
                            'end_time': str(acc['end_time']),
                            'confidence': acc['confidence']
                        },
                        'manipulation': {
                            'type': manip.manipulation_type,
                            'key_level': manip.key_level,
                            'start_time': str(manip.start_time),
                            'confidence': manip.confidence,
                            'trade_signal': manip.trade_signal
                        },
                        'distribution': {
                            'direction': matching_dist['direction'] if matching_dist else 'pending',
                            'move_pct': matching_dist.get('move_pct', 0) if matching_dist else 0,
                            'confirms_trap': matching_dist.get('confirms_trap', False) if matching_dist else False,
                            'confidence': matching_dist.get('confidence', 0) if matching_dist else 0
                        } if matching_dist else None,
                        'sequence_complete': matching_dist is not None,
                        'sequence_score': round(best_score, 1),
                        'expected_direction': 'bullish' if manip.manipulation_type == 'bear_trap' else 'bearish'
                    }
        
        return best_sequence
    
    def analyze(self, symbol: str, current_price: float, htf_result: Dict, 
                mtf_result: Dict, candles: Dict = None) -> Dict:
        """Run complete LTF analysis with full AMD detection (Accumulation + Manipulation + Distribution)
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            htf_result: HTF analysis result with key_levels and liquidity_zones
            mtf_result: MTF analysis result with range context
            candles: Optional pre-fetched candles dict with '60'/'15'/'5'/'3'/'1' keys
        """
        logger.info("=" * 60)
        logger.info("📊 LTF ANALYSIS (1H to 1min) + FULL AMD DETECTION")
        logger.info("=" * 60)
        
        # Fetch data for multiple LTF timeframes (use pre-fetched if available)
        ltf_data = {}
        for tf in [Timeframe.ONE_HOUR, Timeframe.FIFTEEN_MIN, Timeframe.FIVE_MIN, 
                   Timeframe.THREE_MIN, Timeframe.ONE_MIN]:
            if candles and tf.value in candles:
                ltf_data[tf.value] = candles[tf.value]
            else:
                ltf_data[tf.value] = self.get_data(symbol, tf)
        
        fetched_count = sum(1 for v in ltf_data.values() if v is not None)
        logger.info(f"   📊 LTF data: {fetched_count} timeframes loaded")
        
        # Extract key levels from HTF
        key_levels = list(htf_result.get('key_levels', {}).values())
        key_levels = [l for l in key_levels if l is not None]
        
        # Get HTF liquidity zones
        htf_zones = htf_result.get('liquidity_zones', [])
        
        # Get MTF range
        mtf_range = mtf_result.get('range', RangeContext(
            range_high=current_price * 1.01,
            range_low=current_price * 0.99,
            range_mid=current_price,
            timeframe="240",
            period_start=datetime.now()
        ))
        
        # Add MTF range levels to key levels
        key_levels.extend([mtf_range.range_high, mtf_range.range_low, mtf_range.range_mid])
        
        today = datetime.now().date()
        
        # ============================================================
        # PHASE 1: ACCUMULATION DETECTION
        # Detect consolidation ranges FIRST — their boundaries become
        # key levels that feed into manipulation detection
        # ============================================================
        all_accumulations = []
        for tf_value in ['5', '3', '15']:  # 5min/3min best for accumulation ranges
            df = ltf_data.get(tf_value)
            if df is not None and not df.empty:
                accs = self.detect_accumulation(df, lookback=10)
                for acc in accs:
                    # Only include today's accumulations
                    acc_time = acc['end_time']
                    if isinstance(acc_time, pd.Timestamp):
                        acc_date = acc_time.date()
                    else:
                        acc_date = acc_time.date() if hasattr(acc_time, 'date') else today
                    
                    if acc_date == today:
                        acc['timeframe'] = f"{tf_value}m"
                        all_accumulations.append(acc)
        
        # Add accumulation range boundaries as key levels for manipulation detection
        for acc in all_accumulations:
            key_levels.extend([acc['range_high'], acc['range_low']])
        
        logger.info(f"   📦 Accumulation Zones: {len(all_accumulations)}")
        for acc in all_accumulations[:3]:
            logger.info(f"      Range: {acc['range_low']:.2f} - {acc['range_high']:.2f} "
                       f"(conf: {acc['confidence']}, vol_ratio: {acc.get('volume_ratio', 0):.2f}, "
                       f"tf: {acc.get('timeframe', '?')})")
        
        # ============================================================
        # PHASE 2: MANIPULATION DETECTION (existing - now enriched with accumulation levels)
        # ============================================================
        all_manipulations = []
        
        for tf_value in ['1', '3', '5']:  # Focus on lowest timeframes
            df = ltf_data.get(tf_value)
            if df is not None and not df.empty:
                manips = self.detect_manipulation(df, key_levels, htf_zones)
                for m in manips:
                    m.phase = f"{m.phase}_{tf_value}m"  # Tag with timeframe
                    # Only include today's manipulations for active trading
                    if isinstance(m.start_time, pd.Timestamp):
                        manip_date = m.start_time.date()
                    else:
                        manip_date = m.start_time.date() if hasattr(m.start_time, 'date') else today
                    
                    if manip_date == today:
                        all_manipulations.append(m)
        
        # Sort by time (most recent first) then by confidence
        all_manipulations = sorted(
            all_manipulations,
            key=lambda x: (x.start_time if isinstance(x.start_time, datetime) else x.start_time.to_pydatetime(), x.confidence),
            reverse=True
        )[:10]
        
        # ============================================================
        # PHASE 3: DISTRIBUTION DETECTION
        # Detect the real move AFTER manipulation — confirms the trap
        # ============================================================
        all_distributions = []
        recent_manip = all_manipulations[0] if all_manipulations else None
        
        for tf_value in ['1', '3', '5']:
            df = ltf_data.get(tf_value)
            if df is not None and not df.empty:
                dists = self.detect_distribution(df, recent_manip, all_accumulations)
                for dist in dists:
                    # Only include today's distributions
                    dist_time = dist['end_time']
                    if isinstance(dist_time, pd.Timestamp):
                        dist_date = dist_time.date()
                    else:
                        dist_date = dist_time.date() if hasattr(dist_time, 'date') else today
                    
                    if dist_date == today:
                        dist['timeframe'] = f"{tf_value}m"
                        all_distributions.append(dist)
        
        logger.info(f"   🎯 Distribution Moves: {len(all_distributions)}")
        for dist in all_distributions[:3]:
            logger.info(f"      {dist['direction'].upper()} move: {dist['move_pct']:.2f}% "
                       f"(conf: {dist['confidence']}, vol_ratio: {dist.get('volume_ratio', 0):.2f}, "
                       f"confirms_trap: {dist.get('confirms_trap', False)})")
        
        # ============================================================
        # PHASE 4: AMD SEQUENCE DETECTION
        # Look for complete A→M→D pattern — highest conviction signal
        # ============================================================
        amd_sequence = self.detect_amd_sequence(all_accumulations, all_manipulations, all_distributions)
        
        if amd_sequence:
            logger.info(f"   🔥 AMD SEQUENCE DETECTED!")
            logger.info(f"      Complete: {amd_sequence.get('sequence_complete', False)}")
            logger.info(f"      Score: {amd_sequence.get('sequence_score', 0)}")
            logger.info(f"      Expected Direction: {amd_sequence.get('expected_direction', '?')}")
            
            # Boost manipulation confidence if full sequence is confirmed
            if amd_sequence.get('sequence_complete') and all_manipulations:
                for m in all_manipulations:
                    if (m.manipulation_type == amd_sequence['manipulation']['type'] and
                        abs(m.key_level - amd_sequence['manipulation']['key_level']) < 1):
                        old_conf = m.confidence
                        m.confidence = min(m.confidence + 15, 95)  # +15% boost for full A→M→D
                        logger.info(f"      ⬆️ Boosted manipulation confidence: {old_conf:.0f} → {m.confidence:.0f}")
                        break
        else:
            logger.info(f"   ℹ️ No complete AMD sequence detected")
        
        # ============================================================
        # ENTRY ZONES + ACTIVE MANIPULATION (existing logic)
        # ============================================================
        best_df = None
        for tf_key in ['3', '1', '5']:
            df = ltf_data.get(tf_key)
            if df is not None and not df.empty:
                best_df = df
                break
        
        entry_zones = self.find_entry_zones(
            best_df, 
            htf_result.get('bias', 'neutral'),
            mtf_range,
            all_manipulations
        )
        
        # Check for active (recent) manipulation
        active_manip = None
        if all_manipulations:
            most_recent = all_manipulations[0]
            # Consider active if within last 30 minutes
            if isinstance(most_recent.start_time, datetime):
                time_diff = datetime.now() - most_recent.start_time
            else:
                time_diff = datetime.now() - most_recent.start_time.to_pydatetime()
            
            if time_diff.total_seconds() < 1800:  # 30 minutes
                active_manip = most_recent
        
        logger.info(f"   🕵️ Manipulations Detected: {len(all_manipulations)}")
        logger.info(f"   📍 Entry Zones Found: {len(entry_zones)}")
        logger.info(f"   ⚡ Active Manipulation: {'YES - ' + active_manip.manipulation_type if active_manip else 'NO'}")
        
        return {
            'amd_phases': all_manipulations,
            'entry_zones': entry_zones,
            'active_manipulation': active_manip,
            'accumulation_zones': all_accumulations,
            'distribution_zones': all_distributions,
            'amd_sequence': amd_sequence,
            'ltf_data': ltf_data
        }


# ============================================================================
# MAIN ANALYZER - COMBINES ALL THREE
# ============================================================================

class TopDownICTAnalyzer:
    """
    Complete Top-Down ICT Analysis with AMD Detection
    
    Flow:
    1. HTF (Monthly/Weekly) → Bias + Key Liquidity Zones
    2. MTF (Daily/4H) → Session Range + Market Phase
    3. LTF (1H-1min) → AMD Detection + Entry Zones
    """
    
    def __init__(self, fyers_client):
        self.fyers = fyers_client
        self.htf_analyzer = HTFAnalyzer(fyers_client)
        self.mtf_analyzer = MTFAnalyzer(fyers_client)
        self.ltf_analyzer = LTFAnalyzer(fyers_client)
    
    def analyze(self, symbol: str, candles_by_timeframe: Dict = None, current_price: float = None) -> TopDownAnalysis:
        """Run complete top-down analysis
        
        Args:
            symbol: Short symbol (NIFTY, BANKNIFTY, etc.) or full Fyers symbol
            candles_by_timeframe: Optional pre-fetched candles dict with keys like
                'M', 'W', 'D', '240', '60', '15', '5', '3', '1'
                When provided, skips duplicate Fyers API calls.
            current_price: Optional current price. When provided, skips Fyers quote API call.
        """
        logger.info("=" * 70)
        logger.info("🎯 TOP-DOWN ICT ANALYSIS WITH AMD DETECTION")
        logger.info(f"   Symbol: {symbol}")
        logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if candles_by_timeframe:
            logger.info(f"   ✅ Reusing {len(candles_by_timeframe)} pre-fetched timeframes (no duplicate API calls)")
        logger.info("=" * 70)
        
        # Convert short symbol to full Fyers format
        symbol_map = {
            "NIFTY": "NSE:NIFTY50-INDEX",
            "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
            "FINNIFTY": "NSE:FINNIFTY-INDEX",
            "MIDCPNIFTY": "NSE:MIDCPNIFTY-INDEX",
            "SENSEX": "BSE:SENSEX-INDEX",
            "BANKEX": "BSE:BANKEX-INDEX"
        }
        full_symbol = symbol_map.get(symbol.upper(), symbol)
        
        # Get current price (skip API call if already provided)
        if current_price is not None:
            logger.info(f"   Current Price: ₹{current_price:.2f} (provided, no API call)")
        else:
            try:
                quote = self.fyers.get_quotes([full_symbol])
                current_price = None
                
                if quote and quote.get("d"):
                    quote_data = quote["d"][0]
                    if isinstance(quote_data, dict):
                        if "v" in quote_data:
                            current_price = quote_data["v"].get("lp") or quote_data["v"].get("close")
                        elif "lp" in quote_data:
                            current_price = quote_data.get("lp")
                        elif "close" in quote_data:
                            current_price = quote_data.get("close")
                
                if not current_price:
                    logger.warning("Quote failed, trying historical data for current price...")
                    from datetime import timedelta
                    candles = self.fyers.get_historical_data(
                        symbol=full_symbol,
                        resolution="5",
                        date_from=datetime.now() - timedelta(days=1),
                        date_to=datetime.now()
                    )
                    if candles is not None and not candles.empty:
                        current_price = float(candles['close'].iloc[-1])
                    else:
                        raise Exception("Could not get current price from any source")
                        
                logger.info(f"   Current Price: ₹{current_price:.2f}")
            except Exception as e:
                logger.error(f"Failed to get price: {e}")
                raise
        
        # 1. HTF Analysis (pass pre-fetched candles if available)
        htf_result = self.htf_analyzer.analyze(full_symbol, current_price, candles=candles_by_timeframe)
        
        # 2. MTF Analysis (pass pre-fetched candles if available)
        mtf_result = self.mtf_analyzer.analyze(full_symbol, current_price, candles=candles_by_timeframe)
        
        # 3. LTF Analysis (pass pre-fetched candles if available — uses HTF and MTF context)
        ltf_result = self.ltf_analyzer.analyze(full_symbol, current_price, htf_result, mtf_result, candles=candles_by_timeframe)
        
        # Combine results
        return self._generate_signal(
            symbol, current_price, htf_result, mtf_result, ltf_result
        )
    
    def _generate_signal(self, symbol: str, current_price: float,
                        htf_result: Dict, mtf_result: Dict, ltf_result: Dict) -> TopDownAnalysis:
        """Generate final trading signal from full AMD analysis"""
        
        # Determine recommended action
        recommended_action = "WAIT"
        best_entry = None
        confidence = 0
        reasoning = ""
        
        entry_zones = ltf_result.get('entry_zones', [])
        active_manip = ltf_result.get('active_manipulation')
        htf_bias = htf_result.get('bias', 'neutral')
        amd_sequence = ltf_result.get('amd_sequence')
        distributions = ltf_result.get('distribution_zones', [])
        
        # Priority 0: Complete A→M→D sequence (highest conviction)
        if amd_sequence and amd_sequence.get('sequence_complete'):
            expected_dir = amd_sequence.get('expected_direction', '')
            recommended_action = "BUY CALL" if expected_dir == 'bullish' else "BUY PUT"
            confidence = min(amd_sequence.get('sequence_score', 0) / 3, 95)  # Avg of 3 phases
            reasoning = (f"🔥 Full A→M→D sequence: {amd_sequence['manipulation']['type']} "
                        f"at {amd_sequence['manipulation']['key_level']:.2f} → "
                        f"{expected_dir} distribution confirmed")
            
            # Find matching entry zone
            for ez in entry_zones:
                if ez.amd_phase and ez.amd_phase.manipulation_type == amd_sequence['manipulation']['type']:
                    best_entry = ez
                    break
        
        # Priority 1: Active manipulation with high confidence
        elif active_manip and active_manip.confidence >= 65:
            recommended_action = active_manip.trade_signal
            confidence = active_manip.confidence
            reasoning = f"Active {active_manip.manipulation_type} detected at {active_manip.key_level:.2f}"
            
            # Check if distribution confirms this manipulation
            if distributions:
                expected_dir = 'bullish' if active_manip.manipulation_type == 'bear_trap' else 'bearish'
                confirming_dist = next((d for d in distributions 
                                       if d.get('confirms_trap') and d.get('direction') == expected_dir), None)
                if confirming_dist:
                    confidence = min(confidence + 10, 95)
                    reasoning += f" + {expected_dir} distribution confirmed ({confirming_dist['move_pct']:.1f}% move)"
                elif any(d.get('direction') == expected_dir for d in distributions):
                    confidence = min(confidence + 5, 95)
                    reasoning += f" + {expected_dir} distribution developing"
            
            # Find matching entry zone
            for ez in entry_zones:
                if ez.amd_phase == active_manip:
                    best_entry = ez
                    break
        
        # Priority 2: High confidence entry zone aligned with HTF + MTF range
        elif entry_zones:
            best_zone = entry_zones[0]  # Already sorted by confidence
            mtf_range = mtf_result.get('range')
            
            # Check HTF alignment
            htf_aligned = (
                (best_zone.direction == "long" and htf_bias in ["bullish", "neutral"]) or
                (best_zone.direction == "short" and htf_bias in ["bearish", "neutral"])
            )
            
            # Check MTF premium/discount zone alignment (ICT key principle)
            # Bullish entries should be in DISCOUNT zone (below midpoint = smart money buys cheap)
            # Bearish entries should be in PREMIUM zone (above midpoint = smart money sells expensive)
            mtf_zone_aligned = True  # Default to True if no MTF range
            mtf_zone_bonus = 0
            
            if mtf_range and hasattr(mtf_range, 'range_mid') and best_zone.entry_price:
                in_discount = best_zone.entry_price < mtf_range.range_mid
                in_premium = best_zone.entry_price > mtf_range.range_mid
                
                if best_zone.direction == "long" and in_discount:
                    mtf_zone_aligned = True
                    mtf_zone_bonus = 5  # Bonus for buying in discount
                elif best_zone.direction == "short" and in_premium:
                    mtf_zone_aligned = True
                    mtf_zone_bonus = 5  # Bonus for selling in premium
                elif best_zone.direction == "long" and in_premium:
                    mtf_zone_aligned = False  # Buying at premium — risky
                    mtf_zone_bonus = -10
                elif best_zone.direction == "short" and in_discount:
                    mtf_zone_aligned = False  # Selling at discount — risky
                    mtf_zone_bonus = -10
            
            if htf_aligned and best_zone.confidence >= 50:
                adjusted_confidence = min(95, best_zone.confidence + mtf_zone_bonus)
                recommended_action = "BUY CALL" if best_zone.direction == "long" else "BUY PUT"
                confidence = adjusted_confidence
                best_entry = best_zone
                zone_label = ""
                if mtf_range and hasattr(mtf_range, 'current_position'):
                    zone_label = f" in {mtf_range.current_position.upper()} zone"
                reasoning = f"{best_zone.entry_type} at {best_zone.entry_price:.2f}{zone_label} aligned with HTF {htf_bias} bias"
                if not mtf_zone_aligned:
                    reasoning += f" ⚠️ (wrong MTF zone, confidence reduced)"
            elif not htf_aligned and best_zone.entry_type == "AMD_REVERSAL" and best_zone.confidence >= 70:
                # Override HTF if manipulation is very clear
                recommended_action = "BUY CALL" if best_zone.direction == "long" else "BUY PUT"
                confidence = best_zone.confidence * 0.8  # Reduce confidence for HTF conflict
                best_entry = best_zone
                reasoning = f"⚠️ AMD override: {best_zone.entry_type} at {best_zone.entry_price:.2f} (conflicts with HTF {htf_bias})"
        
        # Priority 3: Distribution-only signal (no active manipulation but clear move happening)
        elif distributions and not active_manip:
            best_dist = max(distributions, key=lambda d: d.get('confidence', 0))
            if best_dist.get('confidence', 0) >= 65 and best_dist.get('volume_ratio', 0) > 1.5:
                dist_dir = best_dist['direction']
                recommended_action = "BUY CALL" if dist_dir == 'bullish' else "BUY PUT"
                confidence = best_dist['confidence'] * 0.8  # Lower confidence without manipulation context
                reasoning = (f"Strong {dist_dir} distribution: {best_dist['move_pct']:.1f}% move "
                           f"with {best_dist['volume_ratio']:.1f}x volume")
        
        # Priority 4: No clear entry - wait
        if recommended_action == "WAIT":
            # Build informative wait reasoning
            parts = [f"HTF: {htf_bias}"]
            parts.append(f"Session: {mtf_result.get('session', 'unknown')}")
            if ltf_result.get('accumulation_zones'):
                latest_acc = ltf_result['accumulation_zones'][-1]
                parts.append(f"Accumulation at {latest_acc['range_low']:.0f}-{latest_acc['range_high']:.0f}")
            if amd_sequence and not amd_sequence.get('sequence_complete'):
                parts.append(f"A→M detected, awaiting distribution")
            reasoning = "No high-confidence entry. " + ", ".join(parts)
        
        logger.info("=" * 70)
        logger.info("🎯 FINAL SIGNAL")
        logger.info(f"   Action: {recommended_action}")
        logger.info(f"   Confidence: {confidence:.1f}%")
        logger.info(f"   Reasoning: {reasoning}")
        if amd_sequence:
            logger.info(f"   AMD Sequence: {'COMPLETE ✅' if amd_sequence.get('sequence_complete') else 'PARTIAL (A→M only)'}")
        logger.info("=" * 70)
        
        return TopDownAnalysis(
            symbol=symbol,
            current_price=current_price,
            timestamp=datetime.now(),
            htf_bias=htf_result.get('bias', 'neutral'),
            htf_liquidity_zones=htf_result.get('liquidity_zones', []),
            htf_key_levels=htf_result.get('key_levels', {}),
            mtf_range=mtf_result.get('range', RangeContext(
                range_high=current_price * 1.01,
                range_low=current_price * 0.99,
                range_mid=current_price,
                timeframe="240",
                period_start=datetime.now()
            )),
            mtf_session=mtf_result.get('session', 'CLOSED'),
            mtf_phase=mtf_result.get('phase', 'ranging'),
            ltf_entry_zones=ltf_result.get('entry_zones', []),
            ltf_amd_phases=ltf_result.get('amd_phases', []),
            active_manipulation=ltf_result.get('active_manipulation'),
            recommended_action=recommended_action,
            entry_zone=best_entry,
            confidence=confidence,
            reasoning=reasoning,
            accumulation_zones=ltf_result.get('accumulation_zones', []),
            distribution_zones=ltf_result.get('distribution_zones', []),
            amd_sequence=ltf_result.get('amd_sequence')
        )


# Singleton
_analyzer = None

def get_topdown_analyzer(fyers_client):
    global _analyzer
    if _analyzer is None:
        _analyzer = TopDownICTAnalyzer(fyers_client)
    return _analyzer
