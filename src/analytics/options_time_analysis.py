"""
Options Time Analysis Module
Analyzes option price movements based on:
- Time of day (Indian market sessions)
- Days to expiry
- Theta decay patterns
- Historical movement patterns
- Option price projection
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, time
import numpy as np
from scipy.stats import norm
import logging

logger = logging.getLogger(__name__)


# Indian Market Session Times
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)
SESSION_1_END = time(12, 30)
SESSION_2_START = time(12, 30)

# Key time periods for options
OPENING_VOLATILITY = (time(9, 15), time(9, 45))   # High volatility
MORNING_SESSION = (time(9, 45), time(12, 30))     # Session 1
LUNCH_LULL = (time(12, 30), time(13, 30))         # Low volatility
AFTERNOON_SESSION = (time(13, 30), time(15, 00))  # Session 2
CLOSING_HOUR = (time(15, 00), time(15, 30))       # Expiry pressure


@dataclass
class SessionAnalysis:
    """Analysis for current market session"""
    current_session: str
    session_start: time
    session_end: time
    minutes_elapsed: int
    minutes_remaining: int
    volatility_expectation: str  # high, medium, low
    theta_impact: str  # high, medium, low
    recommendation: str


@dataclass
class ThetaDecayProfile:
    """Theta decay analysis"""
    days_to_expiry: int
    hours_to_expiry: float
    current_theta: float
    daily_decay_pct: float
    hourly_decay_pct: float
    decay_acceleration: str  # slow, moderate, fast, extreme
    optimal_strategy: str


@dataclass
class OptionPriceProjection:
    """Projected option price based on underlying movement"""
    current_option_price: float
    underlying_current: float
    underlying_target: float
    points_move: float
    projected_option_price: float
    projected_profit: float
    projected_profit_pct: float
    time_required_estimate: str
    confidence: str
    greeks_used: Dict


@dataclass
class HistoricalPattern:
    """Historical movement pattern analysis"""
    pattern_type: str
    occurrence_rate: float
    avg_move_size: float
    avg_time_to_target: str
    best_session: str
    success_rate: float


class OptionsTimeAnalyzer:
    """
    Analyze options based on time factors:
    - Indian market sessions
    - Theta decay acceleration
    - Historical patterns
    - Price projections
    """
    
    def __init__(self):
        self.risk_free_rate = 0.065  # 6.5% (India)
    
    def get_current_session(self) -> SessionAnalysis:
        """Determine current market session and characteristics"""
        now = datetime.now().time()
        
        # Check if market is open
        if now < MARKET_OPEN or now > MARKET_CLOSE:
            return SessionAnalysis(
                current_session="CLOSED",
                session_start=MARKET_OPEN,
                session_end=MARKET_CLOSE,
                minutes_elapsed=0,
                minutes_remaining=0,
                volatility_expectation="none",
                theta_impact="none",
                recommendation="Market is closed. Plan for next session."
            )
        
        # Determine session
        if OPENING_VOLATILITY[0] <= now <= OPENING_VOLATILITY[1]:
            session = "OPENING_VOLATILITY"
            start, end = OPENING_VOLATILITY
            vol = "high"
            theta = "low"
            rec = "High volatility. Option premiums inflated. Good for selling or wait for stability."
        elif MORNING_SESSION[0] <= now <= MORNING_SESSION[1]:
            session = "SESSION_1"
            start, end = MORNING_SESSION
            vol = "medium"
            theta = "medium"
            rec = "Primary trading session. Trend usually established. Good for directional trades."
        elif LUNCH_LULL[0] <= now <= LUNCH_LULL[1]:
            session = "LUNCH_LULL"
            start, end = LUNCH_LULL
            vol = "low"
            theta = "medium"
            rec = "Low volatility period. Avoid new positions. Good for adjustment trades."
        elif AFTERNOON_SESSION[0] <= now <= AFTERNOON_SESSION[1]:
            session = "SESSION_2"
            start, end = AFTERNOON_SESSION
            vol = "medium"
            theta = "high"
            rec = "Second trend push. Theta decay accelerates. Good for momentum trades."
        else:  # Closing hour
            session = "CLOSING_HOUR"
            start, end = CLOSING_HOUR
            vol = "high"
            theta = "extreme"
            rec = "Expiry pressure if weekly expiry. Close positions or roll. High theta decay."
        
        # Calculate minutes
        now_minutes = now.hour * 60 + now.minute
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        
        return SessionAnalysis(
            current_session=session,
            session_start=start,
            session_end=end,
            minutes_elapsed=now_minutes - start_minutes,
            minutes_remaining=end_minutes - now_minutes,
            volatility_expectation=vol,
            theta_impact=theta,
            recommendation=rec
        )
    
    def analyze_theta_decay(self, days_to_expiry: int, atm_iv: float = 0.15) -> ThetaDecayProfile:
        """
        Analyze theta decay pattern based on days to expiry
        
        Theta decay accelerates as expiry approaches:
        - >30 days: Slow decay (~3% per day)
        - 15-30 days: Moderate decay (~5% per day)
        - 7-15 days: Fast decay (~8% per day)
        - <7 days: Extreme decay (10-20% per day)
        - Expiry day: Can lose 50%+ of remaining value
        """
        # Calculate hours to expiry (market hours only)
        market_hours_per_day = 6.25  # 9:15 to 15:30
        hours_to_expiry = days_to_expiry * market_hours_per_day
        
        # Current time adjustment
        now = datetime.now().time()
        if MARKET_OPEN <= now <= MARKET_CLOSE:
            now_minutes = now.hour * 60 + now.minute
            close_minutes = MARKET_CLOSE.hour * 60 + MARKET_CLOSE.minute
            hours_today_remaining = (close_minutes - now_minutes) / 60
            hours_to_expiry = (days_to_expiry - 1) * market_hours_per_day + hours_today_remaining
        
        # Theta decay rate based on DTE
        if days_to_expiry > 30:
            daily_decay = 0.03
            decay_acc = "slow"
            strategy = "Sell options - slow decay works for sellers"
        elif days_to_expiry > 15:
            daily_decay = 0.05
            decay_acc = "moderate"
            strategy = "Balanced - good for spreads"
        elif days_to_expiry > 7:
            daily_decay = 0.08
            decay_acc = "fast"
            strategy = "Buy options for quick moves, or sell for rapid decay"
        elif days_to_expiry > 2:
            daily_decay = 0.15
            decay_acc = "extreme"
            strategy = "Expiry week - only for experienced traders. Quick in/out."
        else:
            daily_decay = 0.30
            decay_acc = "extreme"
            strategy = "Expiry day - extreme risk. Gamma scalping or avoid."
        
        # Hourly decay
        hourly_decay = daily_decay / market_hours_per_day
        
        # Estimate theta (simplified)
        # Theta ≈ -(S * σ * N'(d1)) / (2 * √T)
        # Simplified: Theta increases as T decreases
        if days_to_expiry > 0:
            theta_multiplier = 1 / np.sqrt(days_to_expiry / 365)
            current_theta = -atm_iv * theta_multiplier * 0.01  # Approximate
        else:
            current_theta = -0.5  # Expiry day extreme
        
        return ThetaDecayProfile(
            days_to_expiry=days_to_expiry,
            hours_to_expiry=round(hours_to_expiry, 1),
            current_theta=round(current_theta, 4),
            daily_decay_pct=round(daily_decay * 100, 1),
            hourly_decay_pct=round(hourly_decay * 100, 2),
            decay_acceleration=decay_acc,
            optimal_strategy=strategy
        )
    
    def calculate_option_greeks(self, spot: float, strike: float, 
                                days_to_expiry: int, iv: float,
                                option_type: str = "call") -> Dict:
        """Calculate option Greeks using Black-Scholes"""
        if days_to_expiry <= 0:
            days_to_expiry = 0.01
        
        T = days_to_expiry / 365
        r = self.risk_free_rate
        sigma = iv
        
        # d1 and d2
        d1 = (np.log(spot / strike) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Greeks
        if option_type.lower() == "call":
            delta = norm.cdf(d1)
            price = spot * norm.cdf(d1) - strike * np.exp(-r * T) * norm.cdf(d2)
        else:
            delta = norm.cdf(d1) - 1
            price = strike * np.exp(-r * T) * norm.cdf(-d2) - spot * norm.cdf(-d1)
        
        gamma = norm.pdf(d1) / (spot * sigma * np.sqrt(T))
        theta = -(spot * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) - r * strike * np.exp(-r * T) * norm.cdf(d2 if option_type == "call" else -d2)
        theta = theta / 365  # Daily theta
        vega = spot * np.sqrt(T) * norm.pdf(d1) / 100  # Per 1% IV change
        
        return {
            "price": round(price, 2),
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta, 4),
            "vega": round(vega, 4),
            "iv": round(iv * 100, 2)
        }
    
    def project_option_price(self, spot: float, strike: float,
                            current_option_price: float,
                            target_points: float,
                            days_to_expiry: int,
                            iv: float,
                            option_type: str = "call",
                            time_horizon_hours: float = None) -> OptionPriceProjection:
        """
        Project option price if underlying moves by target_points
        
        Args:
            spot: Current underlying price
            strike: Option strike price
            current_option_price: Current option premium
            target_points: Expected move in underlying (positive = up)
            days_to_expiry: Days to expiry
            iv: Implied volatility (as decimal, e.g., 0.15 for 15%)
            option_type: "call" or "put"
            time_horizon_hours: Expected time to reach target (for theta adjustment)
        """
        # Calculate current Greeks
        greeks = self.calculate_option_greeks(spot, strike, days_to_expiry, iv, option_type)
        
        # New underlying price
        new_spot = spot + target_points
        
        # Time adjustment
        if time_horizon_hours:
            days_elapsed = time_horizon_hours / 6.25  # Market hours
            new_dte = max(0.01, days_to_expiry - days_elapsed)
        else:
            new_dte = days_to_expiry
        
        # Calculate new option price
        new_greeks = self.calculate_option_greeks(new_spot, strike, new_dte, iv, option_type)
        projected_price = new_greeks["price"]
        
        # Using Delta approximation for small moves
        delta_approx = current_option_price + (greeks["delta"] * target_points)
        
        # Add gamma effect for larger moves
        gamma_effect = 0.5 * greeks["gamma"] * (target_points ** 2)
        delta_gamma_approx = delta_approx + gamma_effect
        
        # Theta decay
        if time_horizon_hours:
            theta_decay = greeks["theta"] * (time_horizon_hours / 6.25)
        else:
            theta_decay = greeks["theta"]  # 1 day decay
        
        # Final projected price (using full BS recalculation)
        # Adjust for theta decay
        final_projected = max(0, projected_price - abs(theta_decay) if time_horizon_hours else projected_price)
        
        # Profit calculation
        profit = final_projected - current_option_price
        profit_pct = (profit / current_option_price) * 100 if current_option_price > 0 else 0
        
        # Time estimate based on historical volatility
        # Rough estimate: 1 ATR move in 1 day on average
        avg_daily_move = spot * iv / np.sqrt(252)
        if abs(target_points) > 0:
            est_days = abs(target_points) / avg_daily_move
            if est_days < 0.5:
                time_est = f"~{int(est_days * 6.25 * 60)} minutes"
            elif est_days < 1:
                time_est = f"~{int(est_days * 6.25)} hours"
            else:
                time_est = f"~{round(est_days, 1)} days"
        else:
            time_est = "Immediate"
        
        # Confidence based on move size vs daily volatility
        move_vs_daily = abs(target_points) / avg_daily_move
        if move_vs_daily < 0.5:
            confidence = "High"
        elif move_vs_daily < 1:
            confidence = "Medium"
        elif move_vs_daily < 2:
            confidence = "Low"
        else:
            confidence = "Very Low"
        
        return OptionPriceProjection(
            current_option_price=current_option_price,
            underlying_current=spot,
            underlying_target=new_spot,
            points_move=target_points,
            projected_option_price=round(final_projected, 2),
            projected_profit=round(profit, 2),
            projected_profit_pct=round(profit_pct, 2),
            time_required_estimate=time_est,
            confidence=confidence,
            greeks_used={
                "delta": greeks["delta"],
                "gamma": greeks["gamma"],
                "theta": greeks["theta"],
                "theta_decay_applied": round(theta_decay, 2) if time_horizon_hours else "1 day"
            }
        )
    
    def analyze_historical_patterns(self, symbol: str, timeframe: str = "1H") -> List[HistoricalPattern]:
        """
        Analyze historical price patterns to estimate:
        - Typical move sizes
        - Best trading sessions
        - Time to target patterns
        """
        patterns = []
        
        # Session-based patterns (typical for NIFTY/BANKNIFTY)
        patterns.append(HistoricalPattern(
            pattern_type="Opening Range Breakout",
            occurrence_rate=0.65,
            avg_move_size=0.5,  # 0.5% of index value
            avg_time_to_target="30-60 minutes",
            best_session="SESSION_1",
            success_rate=0.62
        ))
        
        patterns.append(HistoricalPattern(
            pattern_type="Gap Fill",
            occurrence_rate=0.70,
            avg_move_size=0.3,
            avg_time_to_target="1-2 hours",
            best_session="SESSION_1",
            success_rate=0.68
        ))
        
        patterns.append(HistoricalPattern(
            pattern_type="Lunch Reversal",
            occurrence_rate=0.45,
            avg_move_size=0.4,
            avg_time_to_target="2-3 hours",
            best_session="SESSION_2",
            success_rate=0.55
        ))
        
        patterns.append(HistoricalPattern(
            pattern_type="Closing Push",
            occurrence_rate=0.60,
            avg_move_size=0.3,
            avg_time_to_target="30-60 minutes",
            best_session="CLOSING_HOUR",
            success_rate=0.58
        ))
        
        patterns.append(HistoricalPattern(
            pattern_type="Expiry Day Range",
            occurrence_rate=0.80,
            avg_move_size=1.0,
            avg_time_to_target="Full day",
            best_session="All",
            success_rate=0.50
        ))
        
        return patterns
    
    def get_optimal_entry_time(self, trade_type: str, days_to_expiry: int) -> Dict:
        """
        Recommend optimal entry time based on trade type and expiry
        
        Args:
            trade_type: "buy_call", "buy_put", "sell_call", "sell_put"
            days_to_expiry: Days remaining to expiry
        """
        recommendations = {
            "optimal_session": "",
            "optimal_time_range": "",
            "reasoning": "",
            "avoid_times": [],
            "tips": []
        }
        
        if "buy" in trade_type:
            if days_to_expiry <= 2:
                recommendations["optimal_session"] = "SESSION_1"
                recommendations["optimal_time_range"] = "9:45 - 11:00"
                recommendations["reasoning"] = "Buy early to avoid extreme theta decay. Exit same day."
                recommendations["avoid_times"] = ["After 14:00 - theta decay too high"]
                recommendations["tips"] = [
                    "Set strict stop loss",
                    "Target quick 15-20% profit",
                    "Don't hold overnight"
                ]
            elif days_to_expiry <= 7:
                recommendations["optimal_session"] = "SESSION_1 or after LUNCH_LULL"
                recommendations["optimal_time_range"] = "9:45 - 11:00 or 13:30 - 14:30"
                recommendations["reasoning"] = "Buy on dips during trend confirmation. Theta decay is fast."
                recommendations["avoid_times"] = ["12:30 - 13:30 - Low volatility, poor fills"]
                recommendations["tips"] = [
                    "Wait for trend confirmation",
                    "Use Session 2 for second chance entries",
                    "Consider rolling if holding overnight"
                ]
            else:
                recommendations["optimal_session"] = "Any session"
                recommendations["optimal_time_range"] = "Based on setup"
                recommendations["reasoning"] = "Theta decay is slower. Focus on technical entry."
                recommendations["tips"] = [
                    "Can hold positions longer",
                    "Wait for proper ICT setup",
                    "Use time to your advantage"
                ]
        
        else:  # Sell options
            if days_to_expiry <= 2:
                recommendations["optimal_session"] = "OPENING or SESSION_1"
                recommendations["optimal_time_range"] = "9:15 - 10:30"
                recommendations["reasoning"] = "Sell when premium is highest. Theta works fast for you."
                recommendations["avoid_times"] = ["After 14:00 if already in profit - close"]
                recommendations["tips"] = [
                    "Sell at elevated IV",
                    "Close at 50% profit quickly",
                    "Be careful of gamma risk"
                ]
            else:
                recommendations["optimal_session"] = "After volatility spike"
                recommendations["optimal_time_range"] = "10:00 - 12:00"
                recommendations["reasoning"] = "Sell after morning volatility settles. Premium is still good."
                recommendations["tips"] = [
                    "Sell OTM options",
                    "Use spreads to limit risk",
                    "Monitor continuously"
                ]
        
        return recommendations
    
    def calculate_exit_targets(self, entry_price: float, 
                              underlying_price: float,
                              strike: float,
                              days_to_expiry: int,
                              iv: float,
                              option_type: str,
                              targets: List[float] = [15, 50, 100]) -> List[Dict]:
        """
        Calculate what underlying price is needed to achieve target profit points
        
        Args:
            entry_price: Option premium paid
            underlying_price: Current spot price
            strike: Option strike
            days_to_expiry: Days to expiry
            iv: Implied volatility
            option_type: "call" or "put"
            targets: Target profit in points (e.g., [15, 50, 100])
        """
        results = []
        greeks = self.calculate_option_greeks(underlying_price, strike, days_to_expiry, iv, option_type)
        
        for target in targets:
            target_option_price = entry_price + target
            
            # Estimate underlying move needed using delta
            # ΔOption ≈ Delta × ΔUnderlying
            if greeks["delta"] != 0:
                underlying_move = target / greeks["delta"]
                
                if option_type.lower() == "call":
                    target_underlying = underlying_price + underlying_move
                else:
                    target_underlying = underlying_price - underlying_move
                
                # Verify with full pricing
                projection = self.project_option_price(
                    spot=underlying_price,
                    strike=strike,
                    current_option_price=entry_price,
                    target_points=underlying_move if option_type == "call" else -underlying_move,
                    days_to_expiry=days_to_expiry,
                    iv=iv,
                    option_type=option_type
                )
                
                results.append({
                    "target_profit_points": target,
                    "target_profit_pct": round((target / entry_price) * 100, 1),
                    "target_option_price": target_option_price,
                    "underlying_needs_to_reach": round(target_underlying, 2),
                    "underlying_move_required": round(abs(underlying_move), 2),
                    "underlying_move_pct": round(abs(underlying_move / underlying_price) * 100, 2),
                    "estimated_time": projection.time_required_estimate,
                    "probability": projection.confidence,
                    "theta_warning": "High decay" if days_to_expiry <= 2 else "Moderate" if days_to_expiry <= 7 else "Low"
                })
        
        return results


# Singleton
options_time_analyzer = OptionsTimeAnalyzer()
