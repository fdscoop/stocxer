"""
Option Chart Analysis Module
Analyzes option premium price action for better entry timing

Features:
- Option OHLC data fetching and analysis
- Support/Resistance on option charts
- Discount zone detection (premium below average)
- Pullback analysis for optimal entries
- Swing low/high identification
- Entry zone recommendations
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, time
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def _convert_numpy_types(obj: Any) -> Any:
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_types(item) for item in obj]
    return obj


def _dataclass_to_dict(obj) -> Dict:
    """Convert dataclass to dict with numpy type conversion"""
    if hasattr(obj, '__dataclass_fields__'):
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            if hasattr(value, '__dataclass_fields__'):
                result[field_name] = _dataclass_to_dict(value)
            elif isinstance(value, list):
                result[field_name] = [
                    _dataclass_to_dict(item) if hasattr(item, '__dataclass_fields__') 
                    else _convert_numpy_types(item) 
                    for item in value
                ]
            else:
                result[field_name] = _convert_numpy_types(value)
        return result
    return _convert_numpy_types(obj)


@dataclass
class OptionSwingPoint:
    """Swing high or low on option chart"""
    price: float
    timestamp: datetime
    type: str  # "swing_high" or "swing_low"
    strength: int  # Number of candles on each side
    touched_count: int = 0  # Times price retested this level


@dataclass
class OptionSupportResistance:
    """Support/Resistance level on option chart"""
    level: float
    type: str  # "support" or "resistance"
    strength: float  # 0-1 score
    touches: int
    last_touch: Optional[datetime] = None
    distance_pct: float = 0.0  # Distance from current price


@dataclass
class DiscountZone:
    """Discount zone where premium is historically cheap"""
    lower_bound: float
    upper_bound: float
    avg_premium: float
    current_premium: float
    discount_pct: float  # How much below average
    is_in_discount: bool
    zone_type: str  # "deep_discount", "discount", "fair_value", "premium", "overpriced"


@dataclass
class PullbackAnalysis:
    """Analysis of potential pullback before main move"""
    current_price: float
    nearest_support: float
    nearest_resistance: float
    expected_pullback_level: float
    pullback_probability: float  # 0-1
    pullback_depth_pct: float
    should_wait: bool
    wait_reason: str
    limit_order_price: float
    max_acceptable_price: float
    
    def to_dict(self) -> Dict:
        return _dataclass_to_dict(self)


@dataclass
class OptionChartAnalysis:
    """Complete option chart analysis for entry optimization"""
    option_symbol: str
    current_premium: float
    timestamp: datetime
    
    # Price action analysis
    swing_highs: List[OptionSwingPoint]
    swing_lows: List[OptionSwingPoint]
    support_levels: List[OptionSupportResistance]
    resistance_levels: List[OptionSupportResistance]
    
    # Discount zone analysis
    discount_zone: DiscountZone
    
    # Pullback analysis
    pullback: PullbackAnalysis
    
    # Entry recommendation
    entry_grade: str  # A, B, C, D, F
    entry_recommendation: str  # "BUY_NOW", "WAIT", "LIMIT_ORDER", "AVOID"
    reasoning: List[str]
    
    # Targets based on option chart
    option_target_1: float  # Based on resistance
    option_target_2: float  # Based on higher resistance
    option_stop_loss: float  # Based on support
    
    # Time feasibility
    time_feasible: bool
    time_remaining_minutes: int
    theta_impact_per_hour: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with all numpy types converted to Python native types"""
        return _dataclass_to_dict(self)


class OptionChartAnalyzer:
    """
    Analyze option premium charts for better entry timing
    
    Key features:
    1. Identify swing lows for CALL entries (enter near option support)
    2. Identify swing highs for PUT entries (enter near option resistance)
    3. Detect discount zones where premium is historically cheap
    4. Analyze pullback probability before main move
    5. Calculate option-chart-based targets and stop-loss
    """
    
    def __init__(self, fyers_client):
        self.fyers = fyers_client
        self.cache = {}
        self.cache_duration = 60  # seconds
    
    def get_option_ohlc(self, option_symbol: str, resolution: str = "15", 
                        days: int = 5) -> Optional[pd.DataFrame]:
        """
        Fetch option OHLC data from Fyers
        
        Args:
            option_symbol: e.g., "NSE:NIFTY26JAN25000CE"
            resolution: "5", "15", "60" minutes
            days: Number of days of data
        
        Returns:
            DataFrame with OHLC data or None if not available
        """
        try:
            date_to = datetime.now()
            date_from = date_to - timedelta(days=days)
            
            df = self.fyers.get_historical_data(
                symbol=option_symbol,
                resolution=resolution,
                date_from=date_from,
                date_to=date_to
            )
            
            if df is not None and not df.empty:
                logger.info(f"📊 Fetched {len(df)} candles for {option_symbol}")
                return df
            else:
                logger.warning(f"⚠️ No data for {option_symbol} - Fyers authentication may be required")
                return None  # Return None instead of demo data
                
        except Exception as e:
            logger.error(f"Error fetching option OHLC: {e}")
            return None  # Return None instead of demo data
    
    def _generate_sample_option_data(self, symbol: str, days: int) -> pd.DataFrame:
        """Generate realistic sample option OHLC data for testing"""
        # Base premium estimation
        base_premium = 250  # Default ATM premium
        
        periods = days * 25  # ~25 candles per day (15-min)
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='15min')
        
        # Generate random walk with mean reversion
        np.random.seed(hash(symbol) % 2**32)
        returns = np.random.normal(0, 0.02, periods)  # 2% volatility per candle
        
        # Add mean reversion
        price_path = [base_premium]
        for r in returns:
            # Mean reversion factor
            deviation = (price_path[-1] - base_premium) / base_premium
            mean_reversion = -deviation * 0.1
            new_price = price_path[-1] * (1 + r + mean_reversion)
            price_path.append(max(5, new_price))  # Minimum premium 5
        
        price_path = price_path[1:]  # Remove initial seed
        
        # Create OHLC from price path
        df = pd.DataFrame({
            'open': price_path,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in price_path],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in price_path],
            'close': [p * (1 + np.random.normal(0, 0.005)) for p in price_path],
            'volume': np.random.randint(1000, 50000, periods)
        }, index=dates)
        
        # Ensure high >= max(open, close) and low <= min(open, close)
        df['high'] = df[['open', 'close', 'high']].max(axis=1)
        df['low'] = df[['open', 'close', 'low']].min(axis=1)
        
        return df
    
    def identify_swing_points(self, df: pd.DataFrame, 
                             strength: int = 3) -> Tuple[List[OptionSwingPoint], List[OptionSwingPoint]]:
        """
        Identify swing highs and lows in option price
        
        Args:
            df: DataFrame with OHLC data
            strength: Number of candles on each side to confirm swing
        
        Returns:
            (swing_highs, swing_lows)
        """
        swing_highs = []
        swing_lows = []
        
        highs = df['high'].values
        lows = df['low'].values
        
        for i in range(strength, len(df) - strength):
            # Check swing high
            is_swing_high = True
            for j in range(1, strength + 1):
                if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append(OptionSwingPoint(
                    price=highs[i],
                    timestamp=df.index[i],
                    type="swing_high",
                    strength=strength
                ))
            
            # Check swing low
            is_swing_low = True
            for j in range(1, strength + 1):
                if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append(OptionSwingPoint(
                    price=lows[i],
                    timestamp=df.index[i],
                    type="swing_low",
                    strength=strength
                ))
        
        return swing_highs, swing_lows
    
    def calculate_support_resistance(self, df: pd.DataFrame,
                                     swing_highs: List[OptionSwingPoint],
                                     swing_lows: List[OptionSwingPoint],
                                     current_price: float) -> Tuple[List[OptionSupportResistance], List[OptionSupportResistance]]:
        """
        Calculate support and resistance levels from swing points
        
        Clusters nearby swing points into zones
        """
        supports = []
        resistances = []
        
        tolerance = current_price * 0.02  # 2% tolerance for clustering
        
        # Process swing lows for support
        if swing_lows:
            low_prices = [s.price for s in swing_lows]
            low_clusters = self._cluster_levels(low_prices, tolerance)
            
            for cluster in low_clusters:
                avg_level = np.mean(cluster)
                if avg_level < current_price:  # Only levels below current price
                    distance = (current_price - avg_level) / current_price * 100
                    supports.append(OptionSupportResistance(
                        level=round(avg_level, 2),
                        type="support",
                        strength=min(1.0, len(cluster) * 0.25),
                        touches=len(cluster),
                        distance_pct=round(distance, 2)
                    ))
        
        # Process swing highs for resistance
        if swing_highs:
            high_prices = [s.price for s in swing_highs]
            high_clusters = self._cluster_levels(high_prices, tolerance)
            
            for cluster in high_clusters:
                avg_level = np.mean(cluster)
                if avg_level > current_price:  # Only levels above current price
                    distance = (avg_level - current_price) / current_price * 100
                    resistances.append(OptionSupportResistance(
                        level=round(avg_level, 2),
                        type="resistance",
                        strength=min(1.0, len(cluster) * 0.25),
                        touches=len(cluster),
                        distance_pct=round(distance, 2)
                    ))
        
        # Sort by distance from current price
        supports = sorted(supports, key=lambda x: x.distance_pct)
        resistances = sorted(resistances, key=lambda x: x.distance_pct)
        
        return supports[:5], resistances[:5]  # Top 5 each
    
    def _cluster_levels(self, prices: List[float], tolerance: float) -> List[List[float]]:
        """Cluster nearby price levels"""
        if not prices:
            return []
        
        sorted_prices = sorted(prices)
        clusters = [[sorted_prices[0]]]
        
        for price in sorted_prices[1:]:
            if price - clusters[-1][-1] <= tolerance:
                clusters[-1].append(price)
            else:
                clusters.append([price])
        
        return clusters
    
    def analyze_discount_zone(self, df: pd.DataFrame, 
                             current_price: float) -> DiscountZone:
        """
        Analyze if current premium is in a discount zone
        
        Uses historical price distribution to determine value
        """
        closes = df['close'].values
        lows = df['low'].values
        
        # Calculate statistics
        avg_premium = np.mean(closes)
        std_premium = np.std(closes)
        min_premium = np.min(lows)
        max_premium = np.max(closes)
        
        # Calculate percentile of current price
        percentile = np.percentile(closes, [10, 25, 50, 75, 90])
        
        # Determine zone
        if current_price <= percentile[0]:  # Below 10th percentile
            zone_type = "deep_discount"
            discount_pct = (avg_premium - current_price) / avg_premium * 100
        elif current_price <= percentile[1]:  # Below 25th percentile
            zone_type = "discount"
            discount_pct = (avg_premium - current_price) / avg_premium * 100
        elif current_price <= percentile[3]:  # Between 25th and 75th
            zone_type = "fair_value"
            discount_pct = (avg_premium - current_price) / avg_premium * 100
        elif current_price <= percentile[4]:  # Between 75th and 90th
            zone_type = "premium"
            discount_pct = (current_price - avg_premium) / avg_premium * -100
        else:  # Above 90th percentile
            zone_type = "overpriced"
            discount_pct = (current_price - avg_premium) / avg_premium * -100
        
        return DiscountZone(
            lower_bound=round(percentile[0], 2),
            upper_bound=round(percentile[4], 2),
            avg_premium=round(avg_premium, 2),
            current_premium=round(current_price, 2),
            discount_pct=round(discount_pct, 2),
            is_in_discount=zone_type in ["deep_discount", "discount"],
            zone_type=zone_type
        )
    
    def analyze_pullback(self, df: pd.DataFrame,
                        current_price: float,
                        supports: List[OptionSupportResistance],
                        option_type: str = "call") -> PullbackAnalysis:
        """
        Analyze probability and depth of pullback before main move
        
        For CALLS: Look for pullback to support before up move
        For PUTS: Look for pullback to resistance before down move
        """
        # Recent price action
        recent_closes = df['close'].tail(10).values
        recent_trend = (recent_closes[-1] - recent_closes[0]) / recent_closes[0]
        
        # Calculate ATR for volatility-based pullback estimate
        high_low = df['high'] - df['low']
        atr = high_low.rolling(14).mean().iloc[-1]
        atr_pct = atr / current_price
        
        # Find nearest support and resistance
        nearest_support = supports[0].level if supports else current_price * 0.95
        nearest_resistance = current_price * 1.10  # Default 10% above
        
        # Pullback analysis based on option type
        if option_type.lower() in ["call", "ce"]:
            # For calls, we want to enter near support
            if recent_trend > 0.02:  # Price has been rising
                # High probability of pullback after up move
                pullback_probability = min(0.8, 0.5 + recent_trend * 5)
                expected_pullback = nearest_support
                pullback_depth = (current_price - nearest_support) / current_price * 100
                should_wait = pullback_depth > 3  # Wait if pullback could be > 3%
                wait_reason = f"Price rallied {recent_trend*100:.1f}%. Expect pullback to ₹{nearest_support:.0f}" if should_wait else "Price near support, can enter"
            else:
                # Price already pulled back or sideways
                pullback_probability = 0.3
                expected_pullback = current_price * 0.98
                pullback_depth = 2
                should_wait = False
                wait_reason = "Price stable or already pulled back"
        else:
            # For puts, we want to enter near resistance
            if recent_trend < -0.02:  # Price has been falling
                pullback_probability = min(0.8, 0.5 + abs(recent_trend) * 5)
                expected_pullback = nearest_resistance
                pullback_depth = (nearest_resistance - current_price) / current_price * 100
                should_wait = pullback_depth > 3
                wait_reason = f"Price dropped {abs(recent_trend)*100:.1f}%. Expect pullback to ₹{nearest_resistance:.0f}" if should_wait else "Price near resistance"
            else:
                pullback_probability = 0.3
                expected_pullback = current_price * 1.02
                pullback_depth = 2
                should_wait = False
                wait_reason = "Price stable or already bounced"
        
        # Calculate limit order price (1% better than current)
        if option_type.lower() in ["call", "ce"]:
            limit_order_price = min(current_price * 0.97, nearest_support * 1.02)
            max_acceptable = current_price * 1.02
        else:
            limit_order_price = max(current_price * 1.03, nearest_resistance * 0.98)
            max_acceptable = current_price * 0.98
        
        return PullbackAnalysis(
            current_price=round(current_price, 2),
            nearest_support=round(nearest_support, 2),
            nearest_resistance=round(nearest_resistance, 2),
            expected_pullback_level=round(expected_pullback, 2),
            pullback_probability=round(pullback_probability, 2),
            pullback_depth_pct=round(pullback_depth, 2),
            should_wait=should_wait,
            wait_reason=wait_reason,
            limit_order_price=round(limit_order_price, 2),
            max_acceptable_price=round(max_acceptable, 2)
        )
    
    def calculate_time_feasibility(self, spot_current: float, 
                                   spot_target: float,
                                   iv: float,
                                   days_to_expiry: int) -> Tuple[bool, int, float]:
        """
        Check if the expected move is feasible within remaining market hours
        
        Returns:
            (is_feasible, minutes_remaining, theta_impact_per_hour)
        """
        from src.utils.ist_utils import get_ist_time
        
        now = get_ist_time()
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        # Calculate minutes remaining today
        if now < market_open:
            minutes_remaining = 375  # Full day
        elif now > market_close:
            minutes_remaining = 0
        else:
            now_minutes = now.hour * 60 + now.minute
            close_minutes = market_close.hour * 60 + market_close.minute
            minutes_remaining = close_minutes - now_minutes
        
        # Estimate time needed for move
        move_pct = abs(spot_target - spot_current) / spot_current
        
        # Average daily move based on IV
        avg_daily_move = iv / np.sqrt(252)  # Annualized IV to daily
        
        # Estimated hours for move
        if avg_daily_move > 0:
            days_for_move = move_pct / avg_daily_move
            hours_for_move = days_for_move * 6.25  # Market hours per day
        else:
            hours_for_move = 24  # Default
        
        # Is it feasible today?
        hours_remaining = minutes_remaining / 60
        is_feasible = hours_for_move <= hours_remaining or minutes_remaining == 0
        
        # Theta impact per hour (simplified)
        if days_to_expiry <= 0:
            theta_per_hour = 0.15  # 15% per hour on expiry day
        elif days_to_expiry <= 2:
            theta_per_hour = 0.05  # 5% per hour
        elif days_to_expiry <= 7:
            theta_per_hour = 0.02  # 2% per hour
        else:
            theta_per_hour = 0.005  # 0.5% per hour
        
        return is_feasible, minutes_remaining, theta_per_hour
    
    def get_entry_grade(self, discount_zone: DiscountZone,
                       pullback: PullbackAnalysis,
                       supports: List[OptionSupportResistance],
                       time_feasible: bool,
                       theta_per_hour: float) -> Tuple[str, str, List[str]]:
        """
        Calculate overall entry grade and recommendation
        
        Returns:
            (grade, recommendation, reasons)
        """
        score = 50  # Base score
        reasons = []
        
        # Discount zone scoring (+/- 20 points)
        if discount_zone.zone_type == "deep_discount":
            score += 20
            reasons.append(f"✅ Deep discount: {discount_zone.discount_pct:.1f}% below avg")
        elif discount_zone.zone_type == "discount":
            score += 10
            reasons.append(f"✅ Discount zone: {discount_zone.discount_pct:.1f}% below avg")
        elif discount_zone.zone_type == "premium":
            score -= 10
            reasons.append(f"⚠️ Premium zone: {abs(discount_zone.discount_pct):.1f}% above avg")
        elif discount_zone.zone_type == "overpriced":
            score -= 20
            reasons.append(f"❌ Overpriced: {abs(discount_zone.discount_pct):.1f}% above avg")
        
        # Pullback scoring (+/- 15 points)
        if not pullback.should_wait:
            score += 15
            reasons.append("✅ No pullback expected, good to enter")
        else:
            score -= 10
            reasons.append(f"⚠️ {pullback.wait_reason}")
        
        # Support proximity scoring (+/- 10 points)
        if supports:
            distance = (pullback.current_price - supports[0].level) / pullback.current_price * 100
            if distance <= 3:
                score += 10
                reasons.append(f"✅ Near support (₹{supports[0].level:.0f}), tight SL possible")
            elif distance <= 7:
                score += 5
                reasons.append(f"⚡ Moderate distance from support")
            else:
                score -= 5
                reasons.append(f"⚠️ Far from support, wide SL needed")
        
        # Time feasibility (+/- 10 points)
        if time_feasible:
            score += 5
            reasons.append("✅ Move feasible in today's session")
        else:
            score -= 10
            reasons.append("⚠️ Move may need more time than today")
        
        # Theta impact (+/- 5 points)
        if theta_per_hour > 0.05:
            score -= 10
            reasons.append(f"❌ High theta decay: {theta_per_hour*100:.1f}%/hr")
        elif theta_per_hour > 0.02:
            score -= 5
            reasons.append(f"⚠️ Moderate theta: {theta_per_hour*100:.1f}%/hr")
        else:
            reasons.append(f"✅ Low theta: {theta_per_hour*100:.1f}%/hr")
        
        # Convert score to grade
        if score >= 80:
            grade = "A"
            recommendation = "BUY_NOW"
        elif score >= 65:
            grade = "B"
            recommendation = "LIMIT_ORDER" if pullback.should_wait else "BUY_NOW"
        elif score >= 50:
            grade = "C"
            recommendation = "WAIT"
        elif score >= 35:
            grade = "D"
            recommendation = "WAIT"
        else:
            grade = "F"
            recommendation = "AVOID"
        
        return grade, recommendation, reasons
    
    def analyze_option(self, option_symbol: str, 
                      current_premium: float,
                      option_type: str,
                      spot_price: float,
                      spot_target: float,
                      strike: float,
                      iv: float,
                      days_to_expiry: int) -> OptionChartAnalysis:
        """
        Complete option chart analysis for entry optimization
        
        Args:
            option_symbol: Full Fyers symbol for option
            current_premium: Current option LTP
            option_type: "call" or "put"
            spot_price: Current underlying price
            spot_target: Expected underlying target
            strike: Option strike price
            iv: Implied volatility (decimal)
            days_to_expiry: Days to expiry
        
        Returns:
            Complete OptionChartAnalysis with entry recommendation
        """
        # Fetch option OHLC data
        df = self.get_option_ohlc(option_symbol, resolution="15", days=5)
        
        if df is None or df.empty:
            # Return basic analysis without chart data
            return self._create_basic_analysis(
                option_symbol, current_premium, option_type, days_to_expiry
            )
        
        # Use current premium from OHLC if available
        if not pd.isna(df['close'].iloc[-1]):
            current_premium = df['close'].iloc[-1]
        
        # Identify swing points
        swing_highs, swing_lows = self.identify_swing_points(df, strength=3)
        
        # Calculate support/resistance
        supports, resistances = self.calculate_support_resistance(
            df, swing_highs, swing_lows, current_premium
        )
        
        # Analyze discount zone
        discount_zone = self.analyze_discount_zone(df, current_premium)
        
        # Analyze pullback
        pullback = self.analyze_pullback(df, current_premium, supports, option_type)
        
        # Check time feasibility
        time_feasible, minutes_remaining, theta_per_hour = self.calculate_time_feasibility(
            spot_price, spot_target, iv, days_to_expiry
        )
        
        # Get entry grade
        grade, recommendation, reasons = self.get_entry_grade(
            discount_zone, pullback, supports, time_feasible, theta_per_hour
        )
        
        # Calculate targets from option chart
        if option_type.lower() in ["call", "ce"]:
            # For calls: target is resistance, stop is support
            target_1 = resistances[0].level if resistances else current_premium * 1.15
            target_2 = resistances[1].level if len(resistances) > 1 else current_premium * 1.30
            stop_loss = supports[0].level if supports else current_premium * 0.80
        else:
            # For puts: similar logic but inverted for short
            target_1 = resistances[0].level if resistances else current_premium * 1.15
            target_2 = resistances[1].level if len(resistances) > 1 else current_premium * 1.30
            stop_loss = supports[0].level if supports else current_premium * 0.80
        
        return OptionChartAnalysis(
            option_symbol=option_symbol,
            current_premium=round(current_premium, 2),
            timestamp=datetime.now(),
            swing_highs=swing_highs[-5:],  # Last 5
            swing_lows=swing_lows[-5:],
            support_levels=supports,
            resistance_levels=resistances,
            discount_zone=discount_zone,
            pullback=pullback,
            entry_grade=grade,
            entry_recommendation=recommendation,
            reasoning=reasons,
            option_target_1=round(target_1, 2),
            option_target_2=round(target_2, 2),
            option_stop_loss=round(stop_loss, 2),
            time_feasible=time_feasible,
            time_remaining_minutes=minutes_remaining,
            theta_impact_per_hour=round(theta_per_hour, 4)
        )
    
    def _create_basic_analysis(self, option_symbol: str, 
                               current_premium: float,
                               option_type: str,
                               days_to_expiry: int) -> Optional[OptionChartAnalysis]:
        """
        Return None when OHLC data not available.
        We do NOT generate demo/fake data - user should authenticate with Fyers first.
        """
        # IMPORTANT: Return None instead of fake data in production
        # This ensures users are not charged for failed data fetches
        # and prevents showing misleading demo signals
        logger.warning(f"❌ Cannot analyze {option_symbol} - no live data available. Fyers authentication required.")
        return None


# Singleton
option_chart_analyzer = None

def get_option_chart_analyzer(fyers_client):
    """Get or create option chart analyzer instance"""
    global option_chart_analyzer
    if option_chart_analyzer is None:
        option_chart_analyzer = OptionChartAnalyzer(fyers_client)
    return option_chart_analyzer
