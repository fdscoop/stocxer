"""
Theta Scenario Planner
======================

Projects option P&L across different time horizons and price scenarios.
This is the "what-if" calculator that answers:
"If NIFTY moves X points in Y minutes, what happens to my option?"

Key Scenarios:
1. Fast move in your favor (best case - gamma + delta)
2. Slow move in your favor (theta eats gains)
3. No move (theta decay kills you)
4. Move against you (delta + theta double loss)
5. Reversal after initial move (worst case)

Time Horizons:
- 15 minutes (scalping)
- 30 minutes (intraday swing)
- 1 hour (positional intraday)
- 2 hours (half-day)
- End of day
- Next day (overnight risk)

Author: TradeWise ML Team
Created: 2026-02-02
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pytz
import math

IST = pytz.timezone('Asia/Kolkata')


class ScenarioOutcome(Enum):
    """Outcome classification for a scenario"""
    BIG_WIN = "BIG_WIN"         # >50% profit
    GOOD_WIN = "GOOD_WIN"       # 20-50% profit
    SMALL_WIN = "SMALL_WIN"     # 5-20% profit
    BREAKEVEN = "BREAKEVEN"     # -5% to +5%
    SMALL_LOSS = "SMALL_LOSS"   # 5-20% loss
    BAD_LOSS = "BAD_LOSS"       # 20-50% loss
    WIPEOUT = "WIPEOUT"         # >50% loss


@dataclass
class TimeScenario:
    """A single time-based scenario projection"""
    time_horizon_mins: int
    description: str
    
    # Price scenarios
    price_up_fast: Dict   # Quick move in favor
    price_up_slow: Dict   # Slow move in favor
    price_flat: Dict      # No movement
    price_down_slow: Dict # Slow move against
    price_down_fast: Dict # Quick move against
    
    # Summary
    best_case_pnl: float
    worst_case_pnl: float
    expected_pnl: float  # Probability-weighted
    theta_decay_amt: float
    
    # Risk assessment
    time_decay_risk: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    profitable_scenarios: int  # Out of 5
    risk_reward_ratio: float


@dataclass
class ThetaScenarioResult:
    """Complete theta scenario analysis"""
    option_type: str
    strike: float
    entry_premium: float
    current_spot: float
    days_to_expiry: float
    current_iv: float
    
    # Greeks
    delta: float
    gamma: float
    theta_per_hour: float
    vega: float
    
    # Time scenarios
    scenarios_15min: TimeScenario
    scenarios_30min: TimeScenario
    scenarios_1hour: TimeScenario
    scenarios_2hour: TimeScenario
    scenarios_eod: TimeScenario
    
    # Summary
    optimal_holding_time: int  # Minutes
    max_theta_loss_today: float
    breakeven_move_required: float
    
    # Recommendations
    urgency: str  # "EXECUTE_NOW", "HAVE_TIME", "WAIT_FOR_SETUP"
    hold_recommendation: str
    exit_triggers: List[str]


class ThetaScenarioPlanner:
    """
    Projects option P&L across time and price scenarios.
    
    Uses Black-Scholes approximations for quick calculations.
    Shows traders exactly what to expect under different conditions.
    """
    
    def __init__(self):
        # Market constants
        self.risk_free_rate = 0.07  # India ~7%
        self.trading_minutes_per_day = 375  # 9:15 - 3:30
        
        # Price move assumptions (as % of spot)
        self.move_sizes = {
            'fast_up': 0.005,    # +0.5%
            'slow_up': 0.002,   # +0.2%
            'flat': 0.0,
            'slow_down': -0.002,
            'fast_down': -0.005
        }
        
        # Move probabilities (for expected value calc)
        self.move_probabilities = {
            'fast_up': 0.15,
            'slow_up': 0.25,
            'flat': 0.20,
            'slow_down': 0.25,
            'fast_down': 0.15
        }
    
    def generate_scenarios(
        self,
        option_type: str,  # "CE" or "PE"
        strike: float,
        entry_premium: float,
        current_spot: float,
        current_iv: float,  # As percentage, e.g., 16.5
        days_to_expiry: float,  # Can be fractional
        timestamp: Optional[datetime] = None,
        is_expiry_day: bool = False,
    ) -> ThetaScenarioResult:
        """
        Generate comprehensive time-based P&L scenarios.
        
        Args:
            option_type: "CE" (call) or "PE" (put)
            strike: Option strike price
            entry_premium: Entry/current premium
            current_spot: Current underlying price
            current_iv: Implied volatility as % (e.g., 16.5)
            days_to_expiry: Days until expiry (can be 0.5 for half day)
            timestamp: Current timestamp
            is_expiry_day: Whether it's expiry day
        
        Returns:
            ThetaScenarioResult with all projections
        """
        if timestamp is None:
            timestamp = datetime.now(IST)
        
        # Convert IV to decimal
        iv = current_iv / 100
        
        # Calculate Greeks
        delta, gamma, theta, vega = self._calculate_greeks(
            option_type, strike, current_spot, iv, days_to_expiry
        )
        
        # Theta per hour
        theta_per_hour = theta / 24 if days_to_expiry > 0 else theta * 10  # Accelerated on expiry
        
        # On expiry day, adjust for accelerated decay
        if is_expiry_day:
            theta_per_hour *= (1 + (15 - timestamp.hour) / 5)  # More decay as day progresses
        
        # Calculate minutes until market close
        mins_until_close = self._minutes_until_close(timestamp)
        
        # Generate scenarios for different time horizons
        time_horizons = [15, 30, 60, 120, mins_until_close]
        horizon_names = ['15min', '30min', '1hour', '2hour', 'eod']
        
        scenarios = {}
        for mins, name in zip(time_horizons, horizon_names):
            if mins <= 0:
                mins = 15  # Minimum scenario
            
            scenario = self._calculate_time_scenario(
                option_type, strike, entry_premium, current_spot, iv,
                days_to_expiry, delta, gamma, theta_per_hour, vega,
                mins, is_expiry_day
            )
            scenarios[name] = scenario
        
        # Calculate optimal holding time
        optimal_time = self._calculate_optimal_holding(scenarios, theta_per_hour, entry_premium)
        
        # Calculate max theta loss for the day
        hours_remaining = mins_until_close / 60
        max_theta_loss = abs(theta_per_hour * hours_remaining)
        
        # Breakeven move required
        breakeven_move = self._calculate_breakeven_move(
            delta, gamma, theta_per_hour, entry_premium, 60
        )
        
        # Generate recommendations
        urgency, hold_rec, exit_triggers = self._generate_recommendations(
            scenarios, optimal_time, is_expiry_day, days_to_expiry,
            delta, entry_premium
        )
        
        return ThetaScenarioResult(
            option_type=option_type,
            strike=strike,
            entry_premium=entry_premium,
            current_spot=current_spot,
            days_to_expiry=days_to_expiry,
            current_iv=current_iv,
            delta=delta,
            gamma=gamma,
            theta_per_hour=theta_per_hour,
            vega=vega,
            scenarios_15min=scenarios['15min'],
            scenarios_30min=scenarios['30min'],
            scenarios_1hour=scenarios['1hour'],
            scenarios_2hour=scenarios['2hour'],
            scenarios_eod=scenarios['eod'],
            optimal_holding_time=optimal_time,
            max_theta_loss_today=max_theta_loss,
            breakeven_move_required=breakeven_move,
            urgency=urgency,
            hold_recommendation=hold_rec,
            exit_triggers=exit_triggers
        )
    
    def _calculate_greeks(
        self,
        option_type: str,
        strike: float,
        spot: float,
        iv: float,
        days_to_expiry: float
    ) -> Tuple[float, float, float, float]:
        """
        Calculate option Greeks using Black-Scholes approximations.
        """
        if days_to_expiry <= 0:
            days_to_expiry = 0.001  # Prevent division by zero
        
        T = days_to_expiry / 365
        r = self.risk_free_rate
        
        # Moneyness
        moneyness = spot / strike
        
        # d1 and d2
        try:
            d1 = (np.log(moneyness) + (r + 0.5 * iv**2) * T) / (iv * np.sqrt(T))
            d2 = d1 - iv * np.sqrt(T)
        except:
            d1, d2 = 0, 0
        
        # N(d1) and N(d2) - using approximation
        from scipy.stats import norm
        nd1 = norm.cdf(d1)
        nd2 = norm.cdf(d2)
        npd1 = norm.pdf(d1)
        
        # Delta
        if option_type == "CE":
            delta = nd1
        else:  # PE
            delta = nd1 - 1
        
        # Gamma (same for calls and puts)
        gamma = npd1 / (spot * iv * np.sqrt(T))
        
        # Theta (per day, as negative)
        theta_component1 = -(spot * npd1 * iv) / (2 * np.sqrt(T))
        if option_type == "CE":
            theta_component2 = -r * strike * np.exp(-r * T) * nd2
        else:
            theta_component2 = r * strike * np.exp(-r * T) * (1 - nd2)
        theta = (theta_component1 + theta_component2) / 365
        
        # Vega
        vega = spot * np.sqrt(T) * npd1 / 100  # Per 1% IV change
        
        return delta, gamma, theta, vega
    
    def _calculate_time_scenario(
        self,
        option_type: str,
        strike: float,
        entry_premium: float,
        current_spot: float,
        iv: float,
        days_to_expiry: float,
        delta: float,
        gamma: float,
        theta_per_hour: float,
        vega: float,
        time_mins: int,
        is_expiry_day: bool
    ) -> TimeScenario:
        """Calculate P&L for all price scenarios at a specific time horizon."""
        
        time_hours = time_mins / 60
        
        # Theta decay for this period
        theta_decay = theta_per_hour * time_hours
        
        # Calculate each price scenario
        price_scenarios = {}
        
        for move_name, move_pct in self.move_sizes.items():
            new_spot = current_spot * (1 + move_pct)
            
            # Price change
            price_change = new_spot - current_spot
            
            # Option P&L calculation using Greeks
            # Delta P&L
            delta_pnl = delta * price_change
            
            # Gamma P&L (second order)
            gamma_pnl = 0.5 * gamma * price_change**2
            
            # Total option price change (ignoring vega for simplicity)
            option_pnl = delta_pnl + gamma_pnl + theta_decay
            
            # Calculate percentage P&L
            pnl_pct = (option_pnl / entry_premium) * 100 if entry_premium > 0 else 0
            
            # Determine outcome
            outcome = self._classify_outcome(pnl_pct)
            
            price_scenarios[move_name] = {
                'spot_move': move_pct * 100,
                'new_spot': new_spot,
                'delta_pnl': round(delta_pnl, 2),
                'gamma_pnl': round(gamma_pnl, 2),
                'theta_cost': round(theta_decay, 2),
                'total_pnl': round(option_pnl, 2),
                'pnl_pct': round(pnl_pct, 1),
                'outcome': outcome.value,
                'new_premium': round(entry_premium + option_pnl, 2)
            }
        
        # Calculate summary stats
        pnls = [s['total_pnl'] for s in price_scenarios.values()]
        pcts = [s['pnl_pct'] for s in price_scenarios.values()]
        
        best_case = max(pnls)
        worst_case = min(pnls)
        
        # Expected P&L
        expected = sum(
            price_scenarios[k]['total_pnl'] * self.move_probabilities[k.replace('price_', '').replace('_', '_')]
            for k in self.move_sizes.keys()
        )
        
        # Count profitable scenarios
        profitable = sum(1 for pnl in pnls if pnl > 0)
        
        # Time decay risk
        if is_expiry_day and time_mins > 60:
            decay_risk = "CRITICAL"
        elif abs(theta_decay) > entry_premium * 0.10:
            decay_risk = "HIGH"
        elif abs(theta_decay) > entry_premium * 0.05:
            decay_risk = "MEDIUM"
        else:
            decay_risk = "LOW"
        
        # Risk/reward ratio
        if worst_case != 0:
            rr_ratio = abs(best_case / worst_case)
        else:
            rr_ratio = 0
        
        return TimeScenario(
            time_horizon_mins=time_mins,
            description=self._get_horizon_description(time_mins),
            price_up_fast=price_scenarios['fast_up'],
            price_up_slow=price_scenarios['slow_up'],
            price_flat=price_scenarios['flat'],
            price_down_slow=price_scenarios['slow_down'],
            price_down_fast=price_scenarios['fast_down'],
            best_case_pnl=round(best_case, 2),
            worst_case_pnl=round(worst_case, 2),
            expected_pnl=round(expected, 2),
            theta_decay_amt=round(theta_decay, 2),
            time_decay_risk=decay_risk,
            profitable_scenarios=profitable,
            risk_reward_ratio=round(rr_ratio, 2)
        )
    
    def _classify_outcome(self, pnl_pct: float) -> ScenarioOutcome:
        """Classify P&L percentage into outcome category."""
        if pnl_pct > 50:
            return ScenarioOutcome.BIG_WIN
        elif pnl_pct > 20:
            return ScenarioOutcome.GOOD_WIN
        elif pnl_pct > 5:
            return ScenarioOutcome.SMALL_WIN
        elif pnl_pct > -5:
            return ScenarioOutcome.BREAKEVEN
        elif pnl_pct > -20:
            return ScenarioOutcome.SMALL_LOSS
        elif pnl_pct > -50:
            return ScenarioOutcome.BAD_LOSS
        else:
            return ScenarioOutcome.WIPEOUT
    
    def _get_horizon_description(self, mins: int) -> str:
        """Get human-readable description of time horizon."""
        if mins <= 15:
            return "Scalping window"
        elif mins <= 30:
            return "Quick swing"
        elif mins <= 60:
            return "1 hour hold"
        elif mins <= 120:
            return "2 hour position"
        elif mins <= 240:
            return "Half day"
        else:
            return "End of day"
    
    def _calculate_optimal_holding(
        self,
        scenarios: Dict,
        theta_per_hour: float,
        entry_premium: float
    ) -> int:
        """
        Calculate optimal holding time based on expected P&L curve.
        
        Returns minutes where expected P&L is maximized.
        """
        best_expected = float('-inf')
        optimal_mins = 15
        
        for name, scenario in scenarios.items():
            # Adjust for risk/reward
            adjusted_expected = scenario.expected_pnl - (abs(scenario.worst_case_pnl) * 0.3)
            
            if adjusted_expected > best_expected:
                best_expected = adjusted_expected
                optimal_mins = scenario.time_horizon_mins
        
        return optimal_mins
    
    def _calculate_breakeven_move(
        self,
        delta: float,
        gamma: float,
        theta_per_hour: float,
        entry_premium: float,
        time_mins: int
    ) -> float:
        """
        Calculate the minimum price move needed to break even after theta.
        """
        theta_loss = abs(theta_per_hour * (time_mins / 60))
        
        if delta == 0:
            return 0
        
        # Simple approximation: breakeven = theta_loss / delta
        breakeven_move = theta_loss / abs(delta)
        
        return round(breakeven_move, 2)
    
    def _minutes_until_close(self, timestamp: datetime) -> int:
        """Calculate minutes until market close."""
        market_close_mins = 15 * 60 + 30  # 3:30 PM
        current_mins = timestamp.hour * 60 + timestamp.minute
        
        remaining = market_close_mins - current_mins
        return max(0, remaining)
    
    def _generate_recommendations(
        self,
        scenarios: Dict,
        optimal_time: int,
        is_expiry_day: bool,
        days_to_expiry: float,
        delta: float,
        entry_premium: float
    ) -> Tuple[str, str, List[str]]:
        """Generate trading recommendations based on scenarios."""
        
        exit_triggers = []
        
        # Urgency assessment
        if is_expiry_day:
            urgency = "EXECUTE_NOW"
            hold_rec = "SHORT HOLD ONLY - Exit by 2 PM unless strong momentum"
            exit_triggers.append("Exit before 2:30 PM regardless of P&L")
        elif scenarios['1hour'].expected_pnl < -entry_premium * 0.1:
            urgency = "EXECUTE_NOW"
            hold_rec = "Time working against you - need quick move"
            exit_triggers.append(f"Exit if no ₹{abs(scenarios['30min'].theta_decay_amt):.0f}+ move in 30 mins")
        elif days_to_expiry <= 1:
            urgency = "EXECUTE_NOW"
            hold_rec = "Expiry tomorrow - don't hold overnight"
            exit_triggers.append("Exit by 3 PM today")
        else:
            urgency = "HAVE_TIME"
            hold_rec = f"Can hold up to {optimal_time} minutes for best risk/reward"
        
        # Add P&L-based exit triggers
        profit_target = entry_premium * 0.3  # 30% profit
        stop_loss = entry_premium * 0.2  # 20% loss
        
        exit_triggers.append(f"Take profit at ₹{profit_target:.0f} gain (+30%)")
        exit_triggers.append(f"Stop loss at ₹{stop_loss:.0f} loss (-20%)")
        
        # Add theta-based trigger
        exit_triggers.append(f"Exit if flat after {optimal_time} mins (theta erosion)")
        
        return urgency, hold_rec, exit_triggers
    
    def quick_pnl_estimate(
        self,
        option_type: str,
        strike: float,
        premium: float,
        current_spot: float,
        target_spot: float,
        time_mins: int,
        current_iv: float,
        days_to_expiry: float
    ) -> Dict:
        """
        Quick P&L estimate for a specific price target.
        
        Useful for: "If NIFTY goes to 25200 in 30 mins, what's my P&L?"
        """
        iv = current_iv / 100
        
        delta, gamma, theta, vega = self._calculate_greeks(
            option_type, strike, current_spot, iv, days_to_expiry
        )
        
        price_change = target_spot - current_spot
        time_hours = time_mins / 60
        
        delta_pnl = delta * price_change
        gamma_pnl = 0.5 * gamma * price_change**2
        theta_cost = (theta / 24) * time_hours
        
        total_pnl = delta_pnl + gamma_pnl + theta_cost
        pnl_pct = (total_pnl / premium) * 100 if premium > 0 else 0
        
        return {
            'spot_move': round(price_change, 2),
            'spot_move_pct': round((price_change / current_spot) * 100, 2),
            'delta_pnl': round(delta_pnl, 2),
            'gamma_pnl': round(gamma_pnl, 2),
            'theta_cost': round(theta_cost, 2),
            'total_pnl': round(total_pnl, 2),
            'pnl_pct': round(pnl_pct, 1),
            'new_premium': round(premium + total_pnl, 2),
            'outcome': self._classify_outcome(pnl_pct).value
        }


def create_theta_planner() -> ThetaScenarioPlanner:
    """Factory function to create a ThetaScenarioPlanner instance."""
    return ThetaScenarioPlanner()
