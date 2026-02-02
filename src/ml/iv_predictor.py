"""
Implied Volatility (IV) Prediction Module
==========================================

Predicts the DIRECTION of IV change - this is often more important than
predicting price direction for options trading.

Why IV Prediction Matters:
- Same index move can result in profit or loss depending on IV change
- Example: NIFTY +1%, but if IV drops from 18 to 14, CE might be flat/down
- IV crush after events destroys option buyers
- IV expansion before events helps option buyers

IV Behavior Patterns (Rule-Based):
1. PRE-EVENT: IV expands (fear/uncertainty premium)
2. POST-EVENT: IV crushes (uncertainty resolved)
3. TREND MOVES: IV stays stable or slightly drops
4. SHARP REVERSALS: IV spikes (fear)
5. EXPIRY DAY: IV for expiring options drops to near-zero
6. VIX CORRELATION: High VIX = high IV environment

This module uses RULE-BASED prediction (not ML) because:
- IV patterns are well-documented and consistent
- Small dataset makes ML unreliable for IV
- Rules capture market microstructure better

Author: TradeWise ML Team
Created: 2026-02-02
"""

import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pytz

IST = pytz.timezone('Asia/Kolkata')


class IVDirection(Enum):
    """Predicted direction of IV change"""
    SPIKE = "SPIKE"         # IV expected to increase significantly (>20%)
    EXPAND = "EXPAND"       # IV expected to increase moderately (5-20%)
    STABLE = "STABLE"       # IV expected to stay roughly same (-5% to +5%)
    CONTRACT = "CONTRACT"   # IV expected to decrease moderately (5-20%)
    CRUSH = "CRUSH"         # IV expected to decrease significantly (>20%)


class IVRegime(Enum):
    """Current IV regime/environment"""
    VERY_LOW = "VERY_LOW"   # IV < 12 (Nifty) - rare, complacent market
    LOW = "LOW"             # IV 12-15 - calm market
    NORMAL = "NORMAL"       # IV 15-20 - typical
    ELEVATED = "ELEVATED"   # IV 20-25 - some fear
    HIGH = "HIGH"           # IV 25-35 - significant fear
    EXTREME = "EXTREME"     # IV > 35 - panic/crisis


@dataclass
class IVPrediction:
    """Result of IV prediction"""
    direction: IVDirection
    confidence: float  # 0-1
    expected_iv_change_pct: float  # Expected % change in IV
    current_iv: float
    predicted_iv: float
    
    # Context
    current_regime: IVRegime
    regime_percentile: float  # Where current IV sits historically (0-100)
    
    # Factor analysis
    event_factor: str  # "PRE_EVENT", "POST_EVENT", "NO_EVENT"
    time_factor: str  # Time-based IV behavior
    trend_factor: str  # How underlying trend affects IV
    expiry_factor: str  # Expiry day IV dynamics
    
    # Trading implications
    vega_exposure: str  # "LONG_VEGA", "SHORT_VEGA", "NEUTRAL"
    options_strategy: str  # Recommended strategy
    reasoning: List[str]
    
    # Risk metrics
    iv_risk_score: float  # 0-1, how risky is IV for option buyers


@dataclass
class MarketEvent:
    """Scheduled market event that affects IV"""
    name: str
    date: date
    time: Optional[datetime]  # Some events have specific times
    impact: str  # "HIGH", "MEDIUM", "LOW"
    typical_iv_behavior: str  # "EXPAND_BEFORE", "CRUSH_AFTER", etc.


class IVPredictor:
    """
    Rule-based IV direction predictor.
    
    Uses market structure knowledge to predict IV changes:
    - Event calendars (RBI, earnings, elections, etc.)
    - Time-of-day patterns
    - Current IV regime (mean reversion)
    - Price trend patterns
    - Expiry dynamics
    """
    
    def __init__(self):
        # IV percentile thresholds for Nifty
        self.iv_percentiles = {
            10: 11.5,   # 10th percentile
            25: 13.0,   # 25th percentile
            50: 15.5,   # Median
            75: 19.0,   # 75th percentile
            90: 24.0,   # 90th percentile
            95: 28.0,   # 95th percentile
        }
        
        # Regular events that affect IV
        self.recurring_events = [
            "RBI_POLICY",       # Every 2 months
            "MONTHLY_EXPIRY",   # Last Thursday
            "WEEKLY_EXPIRY",    # Every Thursday
            "US_FOMC",          # ~6 weeks
            "GDP_DATA",         # Quarterly
            "INFLATION_DATA",   # Monthly
        ]
        
        # IV behavior patterns
        self.patterns = {
            'pre_event_24h': 0.15,      # IV typically rises 15% before major event
            'pre_event_48h': 0.10,      # 10% rise 48h before
            'post_event_crush': -0.20,  # 20% drop after event
            'expiry_day_decay': -0.30,  # 30% IV drop on expiry for that strike
            'sharp_drop_spike': 0.25,   # 25% IV spike on sharp market drop
            'slow_rally_decay': -0.10,  # 10% IV decay in slow rallies
        }
    
    def predict_iv(
        self,
        current_iv: float,
        spot_price: float,
        iv_history: List[float],  # Historical IV readings (daily, last 30+)
        price_history: List[float],  # Corresponding price history
        timestamp: Optional[datetime] = None,
        is_expiry_day: bool = False,
        days_to_expiry: int = 7,
        upcoming_events: Optional[List[MarketEvent]] = None,
        vix_india: Optional[float] = None,  # India VIX if available
    ) -> IVPrediction:
        """
        Predict IV direction for the next trading session/hours.
        
        Args:
            current_iv: Current implied volatility (e.g., 16.5)
            spot_price: Current underlying price
            iv_history: Historical IV values (at least 30 days)
            price_history: Corresponding price history
            timestamp: Current time
            is_expiry_day: Whether it's expiry day
            days_to_expiry: Days until option expiry
            upcoming_events: List of scheduled events
            vix_india: India VIX value if available
        
        Returns:
            IVPrediction with direction, confidence, and trading recommendations
        """
        if timestamp is None:
            timestamp = datetime.now(IST)
        
        # Determine current IV regime
        regime = self._get_iv_regime(current_iv)
        percentile = self._get_iv_percentile(current_iv, iv_history)
        
        # Analyze each factor
        event_factor, event_iv_change = self._analyze_event_factor(
            timestamp, upcoming_events
        )
        
        time_factor, time_iv_change = self._analyze_time_factor(
            timestamp, is_expiry_day, days_to_expiry
        )
        
        trend_factor, trend_iv_change = self._analyze_trend_factor(
            price_history, iv_history
        )
        
        expiry_factor, expiry_iv_change = self._analyze_expiry_factor(
            is_expiry_day, days_to_expiry
        )
        
        # Regime mean reversion factor
        regime_factor, regime_iv_change = self._analyze_regime_factor(
            current_iv, percentile
        )
        
        # Combine factors with weights
        weights = {
            'event': 0.30,    # Events have strongest impact
            'regime': 0.25,   # Mean reversion is powerful
            'trend': 0.20,    # Price trend matters
            'expiry': 0.15,   # Expiry dynamics
            'time': 0.10,     # Intraday patterns
        }
        
        expected_iv_change = (
            weights['event'] * event_iv_change +
            weights['regime'] * regime_iv_change +
            weights['trend'] * trend_iv_change +
            weights['expiry'] * expiry_iv_change +
            weights['time'] * time_iv_change
        )
        
        # Determine direction
        direction = self._get_iv_direction(expected_iv_change)
        
        # Calculate predicted IV
        predicted_iv = current_iv * (1 + expected_iv_change)
        predicted_iv = max(8, min(50, predicted_iv))  # Bounds
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            event_factor, trend_factor, regime_factor, expected_iv_change
        )
        
        # Generate recommendation
        vega_exposure, strategy, reasoning = self._generate_recommendation(
            direction, confidence, regime, percentile,
            event_factor, is_expiry_day, days_to_expiry
        )
        
        # Calculate IV risk score for option buyers
        iv_risk = self._calculate_iv_risk(
            direction, expected_iv_change, regime, percentile
        )
        
        return IVPrediction(
            direction=direction,
            confidence=confidence,
            expected_iv_change_pct=expected_iv_change * 100,
            current_iv=current_iv,
            predicted_iv=predicted_iv,
            current_regime=regime,
            regime_percentile=percentile,
            event_factor=event_factor,
            time_factor=time_factor,
            trend_factor=trend_factor,
            expiry_factor=expiry_factor,
            vega_exposure=vega_exposure,
            options_strategy=strategy,
            reasoning=reasoning,
            iv_risk_score=iv_risk
        )
    
    def _get_iv_regime(self, current_iv: float) -> IVRegime:
        """Determine current IV regime."""
        if current_iv < 12:
            return IVRegime.VERY_LOW
        elif current_iv < 15:
            return IVRegime.LOW
        elif current_iv < 20:
            return IVRegime.NORMAL
        elif current_iv < 25:
            return IVRegime.ELEVATED
        elif current_iv < 35:
            return IVRegime.HIGH
        else:
            return IVRegime.EXTREME
    
    def _get_iv_percentile(
        self, 
        current_iv: float, 
        iv_history: List[float]
    ) -> float:
        """Calculate where current IV sits in historical distribution."""
        if not iv_history or len(iv_history) < 10:
            # Use standard percentiles
            for pct, value in sorted(self.iv_percentiles.items()):
                if current_iv <= value:
                    return pct
            return 99
        
        # Calculate from actual history
        sorted_iv = sorted(iv_history)
        count_below = sum(1 for iv in sorted_iv if iv <= current_iv)
        percentile = (count_below / len(sorted_iv)) * 100
        
        return percentile
    
    def _analyze_event_factor(
        self,
        timestamp: datetime,
        events: Optional[List[MarketEvent]]
    ) -> Tuple[str, float]:
        """
        Analyze how upcoming/recent events affect IV.
        
        Events cause IV expansion before and crush after.
        """
        if not events:
            return "NO_EVENT", 0.0
        
        current_date = timestamp.date()
        
        for event in events:
            days_until = (event.date - current_date).days
            
            if days_until == 0:
                # Event day
                if event.time and timestamp < event.time:
                    # Before event announcement
                    return "PRE_EVENT_IMMINENT", self.patterns['pre_event_24h']
                else:
                    # After event
                    return "POST_EVENT", self.patterns['post_event_crush']
            
            elif days_until == 1:
                # Day before event
                return "PRE_EVENT_24H", self.patterns['pre_event_24h']
            
            elif days_until == 2:
                return "PRE_EVENT_48H", self.patterns['pre_event_48h']
            
            elif days_until < 0 and days_until >= -1:
                # Just after event (yesterday)
                return "POST_EVENT_RECENT", self.patterns['post_event_crush'] * 0.5
        
        return "NO_EVENT", 0.0
    
    def _analyze_time_factor(
        self,
        timestamp: datetime,
        is_expiry_day: bool,
        days_to_expiry: int
    ) -> Tuple[str, float]:
        """
        Analyze intraday IV patterns.
        
        IV typically:
        - Slightly higher at open (uncertainty)
        - Lowest around lunch
        - Rises into close (overnight risk)
        """
        hour = timestamp.hour
        
        if is_expiry_day:
            if hour < 12:
                return "EXPIRY_MORNING", -0.05
            elif hour < 14:
                return "EXPIRY_AFTERNOON", -0.15
            else:
                return "EXPIRY_FINAL", -0.25
        
        if hour < 10:
            return "MARKET_OPEN", 0.02
        elif hour < 13:
            return "MORNING_SESSION", 0.0
        elif hour < 14:
            return "LUNCH_SESSION", -0.02
        else:
            return "CLOSING_SESSION", 0.03
    
    def _analyze_trend_factor(
        self,
        price_history: List[float],
        iv_history: List[float]
    ) -> Tuple[str, float]:
        """
        Analyze how price trend affects IV.
        
        Patterns:
        - Slow up trend: IV contracts (complacency)
        - Fast up trend: IV stable
        - Slow down trend: IV slightly expands
        - Fast down trend: IV spikes (fear)
        - Sideways: IV contracts (realized < implied)
        """
        if len(price_history) < 10:
            return "INSUFFICIENT_DATA", 0.0
        
        prices = np.array(price_history[-20:])
        
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        # Trend direction and strength
        total_return = (prices[-1] - prices[0]) / prices[0]
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        
        # Speed of move (return / time)
        speed = abs(total_return) / len(prices)
        
        if total_return > 0.02:  # Up trend
            if speed > 0.005:  # Fast
                return "FAST_UP_TREND", -0.05  # Slight IV drop
            else:
                return "SLOW_UP_TREND", -0.12  # More IV drop (complacency)
        
        elif total_return < -0.02:  # Down trend
            if speed > 0.005:  # Fast
                return "FAST_DOWN_TREND", 0.20  # IV spike (fear)
            else:
                return "SLOW_DOWN_TREND", 0.08  # Moderate IV rise
        
        else:  # Sideways
            return "SIDEWAYS", -0.08  # IV drops (realized < implied)
    
    def _analyze_expiry_factor(
        self,
        is_expiry_day: bool,
        days_to_expiry: int
    ) -> Tuple[str, float]:
        """
        Analyze expiry-related IV dynamics.
        
        As expiry approaches:
        - Far expiry options: Less affected
        - Near expiry: IV can spike or collapse
        - Expiry day: IV crushes to near-realized levels
        """
        if is_expiry_day:
            return "EXPIRY_DAY", self.patterns['expiry_day_decay']
        
        if days_to_expiry <= 1:
            return "EXPIRY_TOMORROW", -0.20
        elif days_to_expiry <= 3:
            return "NEAR_EXPIRY", -0.10
        elif days_to_expiry <= 7:
            return "APPROACHING_EXPIRY", -0.05
        else:
            return "FAR_EXPIRY", 0.0
    
    def _analyze_regime_factor(
        self,
        current_iv: float,
        percentile: float
    ) -> Tuple[str, float]:
        """
        Analyze mean reversion tendency.
        
        IV is strongly mean-reverting:
        - Very high IV tends to drop
        - Very low IV tends to rise
        """
        if percentile >= 90:
            # Extremely high IV - strong mean reversion
            return "EXTREME_HIGH_REGIME", -0.15
        elif percentile >= 75:
            return "HIGH_REGIME", -0.08
        elif percentile >= 50:
            return "NORMAL_REGIME", 0.0
        elif percentile >= 25:
            return "LOW_REGIME", 0.05
        else:
            # Extremely low IV - tends to spike
            return "EXTREME_LOW_REGIME", 0.12
    
    def _get_iv_direction(self, expected_change: float) -> IVDirection:
        """Convert expected change to direction category."""
        if expected_change > 0.15:
            return IVDirection.SPIKE
        elif expected_change > 0.05:
            return IVDirection.EXPAND
        elif expected_change > -0.05:
            return IVDirection.STABLE
        elif expected_change > -0.15:
            return IVDirection.CONTRACT
        else:
            return IVDirection.CRUSH
    
    def _calculate_confidence(
        self,
        event_factor: str,
        trend_factor: str,
        regime_factor: str,
        expected_change: float
    ) -> float:
        """Calculate confidence in IV prediction."""
        confidence = 0.5  # Base
        
        # High confidence scenarios
        high_confidence_events = ["PRE_EVENT_IMMINENT", "POST_EVENT", "PRE_EVENT_24H"]
        if event_factor in high_confidence_events:
            confidence += 0.25
        
        # Extreme regimes are predictable
        if regime_factor in ["EXTREME_HIGH_REGIME", "EXTREME_LOW_REGIME"]:
            confidence += 0.15
        
        # Strong trends have predictable IV behavior
        if trend_factor in ["FAST_DOWN_TREND", "SLOW_UP_TREND"]:
            confidence += 0.10
        
        # Larger expected changes = more confident (not ambiguous)
        if abs(expected_change) > 0.15:
            confidence += 0.10
        
        return min(0.92, max(0.35, confidence))
    
    def _generate_recommendation(
        self,
        direction: IVDirection,
        confidence: float,
        regime: IVRegime,
        percentile: float,
        event_factor: str,
        is_expiry_day: bool,
        days_to_expiry: int
    ) -> Tuple[str, str, List[str]]:
        """Generate trading recommendation based on IV prediction."""
        reasoning = []
        
        if direction == IVDirection.SPIKE:
            vega_exposure = "LONG_VEGA"
            strategy = "BUY_STRADDLES"
            reasoning.append("📈 IV SPIKE expected - options will become more expensive")
            reasoning.append("Buy options before IV rise to profit from vega")
            if event_factor.startswith("PRE_EVENT"):
                reasoning.append(f"Event approaching - IV expansion typical")
        
        elif direction == IVDirection.EXPAND:
            vega_exposure = "LONG_VEGA"
            strategy = "BUY_OPTIONS"
            reasoning.append("📈 IV EXPANSION expected - favorable for option buyers")
            reasoning.append("Vega gains will add to directional profits")
        
        elif direction == IVDirection.STABLE:
            vega_exposure = "NEUTRAL"
            if days_to_expiry <= 3:
                strategy = "SELL_OPTIONS"
                reasoning.append("📊 IV STABLE - theta decay will dominate")
            else:
                strategy = "DIRECTIONAL_SPREAD"
                reasoning.append("📊 IV STABLE - focus on direction, not vega")
        
        elif direction == IVDirection.CONTRACT:
            vega_exposure = "SHORT_VEGA"
            strategy = "SELL_OPTIONS"
            reasoning.append("📉 IV CONTRACTION expected - sell premium")
            reasoning.append("Option sellers profit as IV drops")
            if regime in [IVRegime.HIGH, IVRegime.ELEVATED]:
                reasoning.append(f"Currently in {regime.value} regime - good for premium selling")
        
        else:  # CRUSH
            vega_exposure = "SHORT_VEGA"
            strategy = "SELL_PREMIUM_AGGRESSIVE"
            reasoning.append("💥 IV CRUSH expected - very dangerous for option buyers")
            reasoning.append("Even correct directional bets may lose money!")
            if is_expiry_day:
                reasoning.append("Expiry day IV collapse in progress")
            if event_factor == "POST_EVENT":
                reasoning.append("Post-event IV crush - classic pattern")
        
        # Confidence modifier
        if confidence < 0.5:
            reasoning.append(f"⚠️ Low confidence ({confidence:.0%}) - hedge vega exposure")
        
        # Percentile context
        if percentile > 80:
            reasoning.append(f"IV at {percentile:.0f}th percentile - historically high")
        elif percentile < 20:
            reasoning.append(f"IV at {percentile:.0f}th percentile - historically low")
        
        return vega_exposure, strategy, reasoning
    
    def _calculate_iv_risk(
        self,
        direction: IVDirection,
        expected_change: float,
        regime: IVRegime,
        percentile: float
    ) -> float:
        """
        Calculate IV risk score for option buyers.
        
        Higher score = riskier to buy options (IV likely to hurt you).
        """
        risk = 0.5  # Base
        
        # Direction risk
        if direction in [IVDirection.CRUSH, IVDirection.CONTRACT]:
            risk += 0.25
        elif direction == IVDirection.STABLE:
            risk += 0.10
        elif direction == IVDirection.EXPAND:
            risk -= 0.15
        elif direction == IVDirection.SPIKE:
            risk -= 0.25
        
        # Regime risk (high IV = risky to buy, might drop)
        if percentile > 80:
            risk += 0.15
        elif percentile < 30:
            risk -= 0.10
        
        # Magnitude of expected change
        if expected_change < -0.15:
            risk += 0.10
        
        return max(0.1, min(0.95, risk))
    
    def get_iv_scenarios(
        self,
        current_iv: float,
        spot_price: float,
        strike: float,
        premium: float,
        option_type: str,
        days_to_expiry: int
    ) -> Dict:
        """
        Generate IV scenarios showing impact on option P&L.
        
        Shows what happens if IV rises, stays same, or drops.
        """
        scenarios = {}
        
        iv_changes = {
            'iv_spike_20': current_iv * 1.20,
            'iv_up_10': current_iv * 1.10,
            'iv_stable': current_iv,
            'iv_down_10': current_iv * 0.90,
            'iv_crush_20': current_iv * 0.80,
        }
        
        # Simplified vega calculation
        # Vega ≈ S * sqrt(T) * 0.004 for ATM options
        time_factor = np.sqrt(days_to_expiry / 365)
        atm_factor = 1 - min(0.5, abs(strike - spot_price) / spot_price)
        vega = spot_price * time_factor * 0.004 * atm_factor
        
        for scenario_name, new_iv in iv_changes.items():
            iv_change = new_iv - current_iv
            vega_pnl = vega * iv_change
            pnl_pct = (vega_pnl / premium) * 100 if premium > 0 else 0
            
            scenarios[scenario_name] = {
                'new_iv': round(new_iv, 2),
                'iv_change': round(iv_change, 2),
                'vega_pnl': round(vega_pnl, 2),
                'pnl_pct': round(pnl_pct, 1),
                'impact': 'POSITIVE' if vega_pnl > 0 else 'NEGATIVE' if vega_pnl < 0 else 'NEUTRAL'
            }
        
        return scenarios


def create_iv_predictor() -> IVPredictor:
    """Factory function to create an IVPredictor instance."""
    return IVPredictor()
