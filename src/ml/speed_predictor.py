"""
Speed Prediction Module for Options Trading
============================================

Predicts the SPEED of price movement, not just direction.
This is critical for options trading because:
- FAST move: Premium explodes (gamma effect) - BUY options
- SLOW move: Premium decays (theta eats it) - SELL options or avoid

Speed Categories:
- EXPLOSIVE: >1% move in <15 mins (rare, high conviction events)
- FAST: >0.5% move in <30 mins (breakouts, news reactions)
- NORMAL: 0.2-0.5% over 1-2 hours (typical trending)
- SLOW: <0.2% over 2+ hours (theta killer, avoid buying)
- CHOPPY: Multiple small reversals (worst for options buyers)

Factors that indicate FAST moves:
1. Volume surge (>2x average)
2. Time of day (first 30 mins, last 30 mins are faster)
3. Breakout from consolidation (Bollinger squeeze)
4. News/events proximity
5. Options OI buildup at nearby strikes
6. Index correlation divergence (Bank Nifty vs Nifty)

Author: TradeWise ML Team
Created: 2026-02-02
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pytz

IST = pytz.timezone('Asia/Kolkata')


class SpeedCategory(Enum):
    """Speed of expected price movement"""
    EXPLOSIVE = "EXPLOSIVE"  # >1% in <15 mins
    FAST = "FAST"            # >0.5% in <30 mins
    NORMAL = "NORMAL"        # 0.2-0.5% in 1-2 hours
    SLOW = "SLOW"            # <0.2% in 2+ hours
    CHOPPY = "CHOPPY"        # Multiple reversals, worst for buyers


@dataclass
class SpeedPrediction:
    """Result of speed prediction"""
    category: SpeedCategory
    confidence: float  # 0-1
    expected_move_pct: float  # Expected % move
    expected_time_mins: int  # Expected time for move
    
    # Factor scores (0-1)
    volume_score: float
    time_of_day_score: float
    volatility_squeeze_score: float
    momentum_score: float
    
    # Trading recommendation
    options_action: str  # "BUY_CALLS", "BUY_PUTS", "SELL_OPTIONS", "AVOID"
    reasoning: List[str]
    
    # Risk metrics
    max_theta_loss_pct: float  # Max % loss from theta if prediction wrong
    breakeven_time_mins: int  # Time before theta decay exceeds potential gain


class SpeedPredictor:
    """
    Predicts speed/velocity of price movement using multiple factors.
    
    This is NOT a direction predictor - it tells you HOW FAST the move will be.
    Critical for options because:
    - Fast moves = gamma profits > theta losses
    - Slow moves = theta losses > any directional gains
    """
    
    def __init__(self):
        # Market timing constants (IST)
        self.market_open = 9 * 60 + 15  # 9:15 AM in minutes
        self.market_close = 15 * 60 + 30  # 3:30 PM in minutes
        
        # Fast periods (in minutes from midnight)
        self.fast_periods = [
            (9 * 60 + 15, 9 * 60 + 45),   # Opening 30 mins: FAST
            (14 * 60 + 30, 15 * 60 + 30),  # Last hour: FAST
        ]
        
        # Slow periods
        self.slow_periods = [
            (12 * 60, 13 * 60 + 30),  # Lunch lull: SLOW
        ]
        
        # Expiry day special timing
        self.expiry_fast_periods = [
            (9 * 60 + 15, 10 * 60),        # Opening: Very fast
            (13 * 60 + 30, 15 * 60 + 30),  # Post-lunch to close: Extreme
        ]
    
    def predict_speed(
        self,
        current_price: float,
        price_history: List[float],  # Last 50+ candles (5-min preferred)
        volume_history: List[float],  # Corresponding volumes
        current_volume: float,
        timestamp: Optional[datetime] = None,
        is_expiry_day: bool = False,
        nearby_oi_data: Optional[Dict] = None,  # OI at nearby strikes
        recent_news_score: float = 0.0,  # 0-1, how impactful recent news is
    ) -> SpeedPrediction:
        """
        Predict the speed of upcoming price movement.
        
        Args:
            current_price: Current spot price
            price_history: Historical prices (5-min candles, at least 50)
            volume_history: Historical volumes
            current_volume: Current candle/period volume
            timestamp: Current time (defaults to now IST)
            is_expiry_day: Whether it's options expiry day
            nearby_oi_data: OI data at nearby strikes
            recent_news_score: Impact score of recent news (0-1)
        
        Returns:
            SpeedPrediction with category, confidence, and trading recommendation
        """
        if timestamp is None:
            timestamp = datetime.now(IST)
        
        # Calculate individual factor scores
        volume_score = self._calculate_volume_score(
            volume_history, current_volume
        )
        
        time_score = self._calculate_time_of_day_score(
            timestamp, is_expiry_day
        )
        
        squeeze_score = self._calculate_volatility_squeeze_score(
            price_history
        )
        
        momentum_score = self._calculate_momentum_score(
            price_history
        )
        
        # OI-based speed indicator
        oi_score = self._calculate_oi_speed_score(nearby_oi_data) if nearby_oi_data else 0.5
        
        # News impact
        news_score = recent_news_score
        
        # Combine scores with weights
        # Volume and squeeze are most predictive of speed
        weights = {
            'volume': 0.25,
            'time': 0.15,
            'squeeze': 0.25,
            'momentum': 0.15,
            'oi': 0.10,
            'news': 0.10
        }
        
        combined_score = (
            weights['volume'] * volume_score +
            weights['time'] * time_score +
            weights['squeeze'] * squeeze_score +
            weights['momentum'] * momentum_score +
            weights['oi'] * oi_score +
            weights['news'] * news_score
        )
        
        # Expiry day multiplier - everything is faster
        if is_expiry_day:
            combined_score = min(1.0, combined_score * 1.3)
        
        # Determine speed category
        category, expected_move, expected_time = self._categorize_speed(
            combined_score, is_expiry_day
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            volume_score, squeeze_score, momentum_score, combined_score
        )
        
        # Generate trading recommendation
        action, reasoning = self._generate_recommendation(
            category, confidence, is_expiry_day, 
            volume_score, squeeze_score, time_score
        )
        
        # Calculate risk metrics
        max_theta_loss = self._estimate_theta_loss(
            current_price, expected_time, is_expiry_day
        )
        
        breakeven_time = self._calculate_breakeven_time(
            expected_move, is_expiry_day
        )
        
        return SpeedPrediction(
            category=category,
            confidence=confidence,
            expected_move_pct=expected_move,
            expected_time_mins=expected_time,
            volume_score=volume_score,
            time_of_day_score=time_score,
            volatility_squeeze_score=squeeze_score,
            momentum_score=momentum_score,
            options_action=action,
            reasoning=reasoning,
            max_theta_loss_pct=max_theta_loss,
            breakeven_time_mins=breakeven_time
        )
    
    def _calculate_volume_score(
        self, 
        volume_history: List[float], 
        current_volume: float
    ) -> float:
        """
        Calculate speed score based on volume surge.
        
        Volume surge indicates institutional activity and potential fast moves.
        """
        if not volume_history or len(volume_history) < 10:
            return 0.5  # Neutral if no data
        
        avg_volume = np.mean(volume_history[-20:])  # Last 20 periods average
        
        if avg_volume == 0:
            return 0.5
        
        volume_ratio = current_volume / avg_volume
        
        # Score mapping:
        # 0.5x or less = 0.1 (very slow)
        # 1.0x = 0.4 (normal)
        # 2.0x = 0.7 (fast)
        # 3.0x+ = 0.95 (explosive)
        
        if volume_ratio <= 0.5:
            return 0.1
        elif volume_ratio <= 1.0:
            return 0.2 + (volume_ratio - 0.5) * 0.4  # 0.2 to 0.4
        elif volume_ratio <= 2.0:
            return 0.4 + (volume_ratio - 1.0) * 0.3  # 0.4 to 0.7
        elif volume_ratio <= 3.0:
            return 0.7 + (volume_ratio - 2.0) * 0.2  # 0.7 to 0.9
        else:
            return min(0.98, 0.9 + (volume_ratio - 3.0) * 0.05)  # 0.9+
    
    def _calculate_time_of_day_score(
        self, 
        timestamp: datetime, 
        is_expiry_day: bool
    ) -> float:
        """
        Calculate speed score based on time of day.
        
        Market has predictable fast/slow periods.
        """
        # Get current time in minutes from midnight
        current_mins = timestamp.hour * 60 + timestamp.minute
        
        # Check if market is closed
        if current_mins < self.market_open or current_mins > self.market_close:
            return 0.0  # No trading
        
        periods = self.expiry_fast_periods if is_expiry_day else self.fast_periods
        
        # Check fast periods
        for start, end in periods:
            if start <= current_mins <= end:
                # How far into the fast period are we?
                progress = (current_mins - start) / (end - start)
                # Peak speed in middle of period
                if is_expiry_day and current_mins >= 14 * 60:  # After 2 PM on expiry
                    return 0.95  # Extremely fast
                return 0.7 + 0.2 * (1 - abs(progress - 0.5) * 2)
        
        # Check slow periods
        for start, end in self.slow_periods:
            if start <= current_mins <= end:
                return 0.25  # Slow
        
        # Normal periods
        return 0.5
    
    def _calculate_volatility_squeeze_score(
        self, 
        price_history: List[float]
    ) -> float:
        """
        Detect Bollinger Band squeeze - precursor to fast moves.
        
        When Bollinger Bands contract (low volatility), a breakout is coming.
        This is one of the best predictors of imminent fast movement.
        """
        if len(price_history) < 20:
            return 0.5
        
        prices = np.array(price_history[-30:])
        
        # Calculate Bollinger Bands
        sma = np.mean(prices[-20:])
        std = np.std(prices[-20:])
        
        # Current bandwidth (how tight the bands are)
        if sma == 0:
            return 0.5
        
        current_bandwidth = (2 * std) / sma
        
        # Historical bandwidth for comparison
        if len(price_history) >= 50:
            hist_std = np.std(prices[-50:-20])
            hist_bandwidth = (2 * hist_std) / np.mean(prices[-50:-20])
        else:
            hist_bandwidth = current_bandwidth
        
        # Squeeze ratio (lower = tighter squeeze = higher score)
        if hist_bandwidth == 0:
            squeeze_ratio = 1.0
        else:
            squeeze_ratio = current_bandwidth / hist_bandwidth
        
        # Also check if price is at band edge (breakout imminent)
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std
        current_price = prices[-1]
        
        # Distance from bands (0 = at middle, 1 = at band edge)
        band_position = abs(current_price - sma) / (std + 0.0001)
        band_position = min(2.0, band_position) / 2.0  # Normalize to 0-1
        
        # Combine squeeze tightness and band position
        # Tight squeeze + at band edge = very high score
        if squeeze_ratio <= 0.5:  # Very tight squeeze
            base_score = 0.85
        elif squeeze_ratio <= 0.7:  # Moderate squeeze
            base_score = 0.7
        elif squeeze_ratio <= 1.0:  # Normal
            base_score = 0.5
        else:  # Expanded (already volatile)
            base_score = 0.6  # Still decent if already moving
        
        # Add band position bonus
        score = base_score + band_position * 0.15
        
        return min(0.98, score)
    
    def _calculate_momentum_score(
        self, 
        price_history: List[float]
    ) -> float:
        """
        Calculate momentum score - strong momentum = faster continuation.
        
        Uses Rate of Change (ROC) and acceleration.
        """
        if len(price_history) < 10:
            return 0.5
        
        prices = np.array(price_history)
        
        # 5-period ROC
        roc_5 = (prices[-1] - prices[-6]) / prices[-6] * 100 if len(prices) > 5 else 0
        
        # 10-period ROC
        roc_10 = (prices[-1] - prices[-11]) / prices[-11] * 100 if len(prices) > 10 else 0
        
        # Acceleration (ROC of ROC)
        if len(prices) > 15:
            prev_roc_5 = (prices[-6] - prices[-11]) / prices[-11] * 100
            acceleration = roc_5 - prev_roc_5
        else:
            acceleration = 0
        
        # Score based on absolute momentum
        abs_roc = abs(roc_5)
        
        if abs_roc >= 0.5:  # Strong momentum
            base_score = 0.8
        elif abs_roc >= 0.3:  # Moderate
            base_score = 0.6
        elif abs_roc >= 0.1:  # Weak
            base_score = 0.4
        else:  # Flat
            base_score = 0.2
        
        # Acceleration bonus (momentum increasing)
        if abs(acceleration) > 0.1:
            base_score += 0.1
        
        return min(0.95, base_score)
    
    def _calculate_oi_speed_score(
        self, 
        nearby_oi_data: Dict
    ) -> float:
        """
        Calculate speed score from options OI data.
        
        Large OI buildup at nearby strikes indicates:
        - Market makers hedging = potential for fast gamma moves
        - High OI strikes act as magnets = potential fast moves to/through them
        """
        if not nearby_oi_data:
            return 0.5
        
        # Extract OI metrics
        call_oi = nearby_oi_data.get('total_call_oi', 0)
        put_oi = nearby_oi_data.get('total_put_oi', 0)
        pcr = nearby_oi_data.get('pcr', 1.0)
        max_pain = nearby_oi_data.get('max_pain_strike', 0)
        current_price = nearby_oi_data.get('spot_price', 0)
        
        # Distance to max pain (closer = faster potential move)
        if current_price > 0 and max_pain > 0:
            distance_pct = abs(current_price - max_pain) / current_price * 100
            if distance_pct < 0.5:  # Very close to max pain
                oi_score = 0.3  # Likely to stay here = slow
            elif distance_pct < 1.0:
                oi_score = 0.5  # Could break either way
            else:
                oi_score = 0.7  # Likely move toward max pain
        else:
            oi_score = 0.5
        
        # Extreme PCR indicates potential fast reversal
        if pcr < 0.5 or pcr > 1.5:
            oi_score += 0.2
        
        return min(0.95, oi_score)
    
    def _categorize_speed(
        self, 
        combined_score: float, 
        is_expiry_day: bool
    ) -> Tuple[SpeedCategory, float, int]:
        """
        Convert combined score to speed category and expected move.
        
        Returns: (category, expected_move_pct, expected_time_mins)
        """
        if combined_score >= 0.85:
            category = SpeedCategory.EXPLOSIVE
            expected_move = 1.2 if is_expiry_day else 0.8
            expected_time = 10 if is_expiry_day else 15
        elif combined_score >= 0.70:
            category = SpeedCategory.FAST
            expected_move = 0.6 if is_expiry_day else 0.4
            expected_time = 20 if is_expiry_day else 30
        elif combined_score >= 0.45:
            category = SpeedCategory.NORMAL
            expected_move = 0.3
            expected_time = 60 if is_expiry_day else 90
        elif combined_score >= 0.30:
            category = SpeedCategory.SLOW
            expected_move = 0.15
            expected_time = 120
        else:
            category = SpeedCategory.CHOPPY
            expected_move = 0.1
            expected_time = 180
        
        return category, expected_move, expected_time
    
    def _calculate_confidence(
        self,
        volume_score: float,
        squeeze_score: float,
        momentum_score: float,
        combined_score: float
    ) -> float:
        """
        Calculate confidence in the speed prediction.
        
        High confidence when multiple factors agree.
        """
        scores = [volume_score, squeeze_score, momentum_score]
        
        # Check agreement between factors
        std_dev = np.std(scores)
        
        # Low std dev = factors agree = higher confidence
        agreement_factor = max(0, 1 - std_dev * 2)
        
        # Base confidence from combined score magnitude
        if combined_score >= 0.7 or combined_score <= 0.3:
            base_confidence = 0.75  # Clear signal either way
        else:
            base_confidence = 0.5  # Ambiguous
        
        confidence = base_confidence * 0.6 + agreement_factor * 0.4
        
        return min(0.95, max(0.3, confidence))
    
    def _generate_recommendation(
        self,
        category: SpeedCategory,
        confidence: float,
        is_expiry_day: bool,
        volume_score: float,
        squeeze_score: float,
        time_score: float
    ) -> Tuple[str, List[str]]:
        """
        Generate trading recommendation based on speed prediction.
        """
        reasoning = []
        
        if category == SpeedCategory.EXPLOSIVE:
            action = "BUY_OPTIONS"
            reasoning.append("🚀 EXPLOSIVE move expected - gamma will dominate theta")
            reasoning.append(f"Volume surge detected (score: {volume_score:.2f})")
            if squeeze_score > 0.7:
                reasoning.append("Volatility squeeze breaking out - expect sharp move")
        
        elif category == SpeedCategory.FAST:
            action = "BUY_OPTIONS"
            reasoning.append("⚡ FAST move expected - favorable risk/reward for options")
            if is_expiry_day:
                reasoning.append("Expiry day gamma amplification in effect")
            if time_score > 0.6:
                reasoning.append("Current market timing favors fast moves")
        
        elif category == SpeedCategory.NORMAL:
            if confidence > 0.65:
                action = "BUY_OPTIONS_CAUTIOUS"
                reasoning.append("📊 NORMAL speed - options viable with tight stop loss")
                reasoning.append("Consider slightly ITM options to reduce theta risk")
            else:
                action = "SELL_OPTIONS"
                reasoning.append("📊 NORMAL speed, low confidence - consider selling premium")
        
        elif category == SpeedCategory.SLOW:
            action = "SELL_OPTIONS"
            reasoning.append("🐢 SLOW move expected - theta will eat option premium")
            reasoning.append("If directional view, consider futures or sell spreads")
            if not is_expiry_day:
                reasoning.append("Wait for better setup or sell premium")
        
        else:  # CHOPPY
            action = "AVOID"
            reasoning.append("⚠️ CHOPPY conditions - worst case for option buyers")
            reasoning.append("Multiple whipsaws will destroy premium")
            reasoning.append("Either sell iron condors or stay out")
        
        # Confidence modifier
        if confidence < 0.5:
            reasoning.append(f"⚠️ Low confidence ({confidence:.0%}) - reduce position size")
        
        return action, reasoning
    
    def _estimate_theta_loss(
        self,
        current_price: float,
        expected_time_mins: int,
        is_expiry_day: bool
    ) -> float:
        """
        Estimate maximum theta loss if speed prediction is wrong.
        
        Returns percentage of premium that could be lost to theta.
        """
        # ATM options lose roughly:
        # - Normal day: ~3-5% of premium per hour
        # - Expiry day: ~10-30% per hour (accelerating)
        
        hours = expected_time_mins / 60
        
        if is_expiry_day:
            # Exponential decay on expiry
            if expected_time_mins < 60:
                hourly_decay = 0.25  # 25% per hour
            else:
                hourly_decay = 0.15
        else:
            hourly_decay = 0.04  # 4% per hour
        
        total_decay = hourly_decay * hours
        
        return min(0.5, total_decay)  # Cap at 50%
    
    def _calculate_breakeven_time(
        self,
        expected_move_pct: float,
        is_expiry_day: bool
    ) -> int:
        """
        Calculate time until theta decay exceeds potential directional gain.
        
        After this time, even a correct directional bet loses money.
        """
        # ATM option delta ~0.5
        # For 1% index move, option moves ~0.5% (simplified)
        # Need move to happen before theta eats 0.5% of premium
        
        option_gain_pct = expected_move_pct * 0.5  # Delta effect
        
        if is_expiry_day:
            # Theta is 10-25% per hour on expiry
            breakeven_time = (option_gain_pct / 0.20) * 60  # minutes
        else:
            # Theta is ~4% per hour normally
            breakeven_time = (option_gain_pct / 0.04) * 60
        
        return int(min(180, max(5, breakeven_time)))


def create_speed_predictor() -> SpeedPredictor:
    """Factory function to create a SpeedPredictor instance."""
    return SpeedPredictor()
