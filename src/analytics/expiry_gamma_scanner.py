"""
Expiry Day Gamma Scanner
========================

Specialized analysis for expiry day trading in Indian markets.

Key Insights:
- Theta decays ONLY during market hours (9:15 AM - 3:30 PM IST = 6.25 hours)
- On expiry day, gamma dominates when premium is low (₹5-25)
- Best window: 1:30 PM - 3:00 PM (post-lunch directional moves)
- Small index moves (50-100 pts) can cause 300-1000% option gains

Strategy:
- Track premium decay in 15-min intervals
- Identify when premium hits "gamma sweet spot" (₹10-25)
- Look for index at key support/resistance
- Enter on breakout with momentum confirmation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

try:
    import pytz
    IST = pytz.timezone('Asia/Kolkata')
except ImportError:
    IST = None

logger = logging.getLogger(__name__)


class MarketPhase(Enum):
    """Indian market trading phases"""
    PRE_OPEN = "pre_open"           # Before 9:15
    OPENING = "opening"             # 9:15 - 10:00 (volatile, avoid)
    MORNING_DECAY = "morning_decay" # 10:00 - 12:00 (theta crushing)
    LUNCH = "lunch"                 # 12:00 - 1:30 (consolidation)
    GAMMA_WINDOW = "gamma_window"   # 1:30 - 3:00 (SWEET SPOT!)
    FINAL_HOUR = "final_hour"       # 3:00 - 3:30 (exit only)
    CLOSED = "closed"               # After 3:30


@dataclass
class GammaOpportunity:
    """Represents a potential gamma scalping opportunity"""
    symbol: str
    strike: int
    option_type: str  # CE or PE
    premium: float
    spot_price: float
    
    # Greeks (estimated for expiry day)
    delta: float
    gamma: float
    theta_per_15min: float
    
    # Analysis
    moneyness_pct: float  # Distance from ATM
    time_remaining_minutes: float
    
    # Opportunity scoring
    gamma_score: float  # 0-100
    risk_reward_ratio: float
    potential_gain_50pt: float  # Expected gain if index moves 50 points
    
    # Signals
    is_gamma_opportunity: bool
    entry_reason: str
    risk_level: str  # LOW, MEDIUM, HIGH, EXTREME


class ExpiryDayGammaScanner:
    """
    Scanner for expiry day gamma trading opportunities
    
    Indian Market Timing:
    - Market hours: 9:15 AM - 3:30 PM IST (375 minutes)
    - Best gamma window: 1:30 PM - 3:00 PM IST
    - 15-minute intervals for tracking
    """
    
    # Market timing constants (IST)
    MARKET_OPEN_HOUR = 9
    MARKET_OPEN_MINUTE = 15
    MARKET_CLOSE_HOUR = 15
    MARKET_CLOSE_MINUTE = 30
    TOTAL_MARKET_MINUTES = 375  # 6 hours 15 minutes
    
    # Gamma sweet spot timing
    GAMMA_WINDOW_START_HOUR = 13
    GAMMA_WINDOW_START_MINUTE = 30
    GAMMA_WINDOW_END_HOUR = 15
    GAMMA_WINDOW_END_MINUTE = 0
    
    # Premium thresholds for gamma plays
    MIN_PREMIUM_FOR_GAMMA = 5
    MAX_PREMIUM_FOR_GAMMA = 30
    IDEAL_PREMIUM_LOW = 10
    IDEAL_PREMIUM_HIGH = 20
    
    def __init__(self, fyers_client=None):
        self.fyers_client = fyers_client
        self._cache = {}
    
    def get_current_ist_time(self) -> datetime:
        """Get current time in IST"""
        if IST:
            return datetime.now(IST)
        # Fallback: assume system is in IST
        return datetime.now()
    
    def get_market_phase(self, ist_time: Optional[datetime] = None) -> MarketPhase:
        """Determine current market phase"""
        if ist_time is None:
            ist_time = self.get_current_ist_time()
        
        hour = ist_time.hour
        minute = ist_time.minute
        time_val = hour * 60 + minute  # Minutes since midnight
        
        market_open = self.MARKET_OPEN_HOUR * 60 + self.MARKET_OPEN_MINUTE  # 9:15 = 555
        market_close = self.MARKET_CLOSE_HOUR * 60 + self.MARKET_CLOSE_MINUTE  # 15:30 = 930
        gamma_start = self.GAMMA_WINDOW_START_HOUR * 60 + self.GAMMA_WINDOW_START_MINUTE  # 13:30 = 810
        gamma_end = self.GAMMA_WINDOW_END_HOUR * 60 + self.GAMMA_WINDOW_END_MINUTE  # 15:00 = 900
        
        if time_val < market_open:
            return MarketPhase.PRE_OPEN
        elif time_val < 600:  # Before 10:00
            return MarketPhase.OPENING
        elif time_val < 720:  # Before 12:00
            return MarketPhase.MORNING_DECAY
        elif time_val < gamma_start:  # Before 13:30
            return MarketPhase.LUNCH
        elif time_val < gamma_end:  # Before 15:00
            return MarketPhase.GAMMA_WINDOW
        elif time_val < market_close:  # Before 15:30
            return MarketPhase.FINAL_HOUR
        else:
            return MarketPhase.CLOSED
    
    def get_time_remaining_minutes(self, ist_time: Optional[datetime] = None) -> float:
        """Get minutes remaining until market close (15:30 IST)"""
        if ist_time is None:
            ist_time = self.get_current_ist_time()
        
        market_close = ist_time.replace(
            hour=self.MARKET_CLOSE_HOUR,
            minute=self.MARKET_CLOSE_MINUTE,
            second=0,
            microsecond=0
        )
        
        if ist_time >= market_close:
            return 0
        
        remaining = (market_close - ist_time).total_seconds() / 60
        return max(0, remaining)
    
    def calculate_intraday_theta(
        self,
        premium: float,
        time_remaining_minutes: float,
        moneyness_pct: float
    ) -> Dict:
        """
        Calculate realistic intraday theta decay for Indian markets.
        
        Unlike Black-Scholes (24-hour decay), this calculates decay
        ONLY for actual trading minutes.
        
        Theta decay accelerates as expiry approaches:
        - >3 hours: ~15% per hour
        - 1-3 hours: ~25% per hour  
        - <1 hour: ~50% per hour (extreme)
        
        Args:
            premium: Current option premium
            time_remaining_minutes: Minutes until 15:30 IST
            moneyness_pct: Distance from ATM as percentage
            
        Returns:
            Dict with theta analysis
        """
        if time_remaining_minutes <= 0:
            return {
                "theta_per_15min": premium,  # Full decay
                "theta_per_hour": premium,
                "decay_rate": "EXPIRED",
                "expected_premium_at_close": 0
            }
        
        # Decay rate based on time remaining
        if time_remaining_minutes > 180:  # >3 hours
            hourly_decay_rate = 0.15
            decay_category = "MODERATE"
        elif time_remaining_minutes > 60:  # 1-3 hours
            hourly_decay_rate = 0.25
            decay_category = "HIGH"
        elif time_remaining_minutes > 30:  # 30min - 1 hour
            hourly_decay_rate = 0.40
            decay_category = "VERY_HIGH"
        else:  # <30 minutes
            hourly_decay_rate = 0.60
            decay_category = "EXTREME"
        
        # Adjust for moneyness (OTM options decay faster)
        if abs(moneyness_pct) > 1.0:  # OTM
            hourly_decay_rate *= 1.3
        elif abs(moneyness_pct) < 0.3:  # ATM
            hourly_decay_rate *= 0.9
        
        # Calculate theta values
        theta_per_hour = premium * hourly_decay_rate
        theta_per_15min = theta_per_hour / 4
        
        # Expected premium at close (if no directional move)
        hours_remaining = time_remaining_minutes / 60
        expected_at_close = premium * ((1 - hourly_decay_rate) ** hours_remaining)
        
        return {
            "theta_per_15min": round(theta_per_15min, 2),
            "theta_per_hour": round(theta_per_hour, 2),
            "hourly_decay_rate_pct": round(hourly_decay_rate * 100, 1),
            "decay_category": decay_category,
            "expected_premium_at_close": round(max(0, expected_at_close), 2),
            "time_remaining_minutes": round(time_remaining_minutes, 0),
            "intervals_remaining": int(time_remaining_minutes / 15)
        }
    
    def calculate_expiry_day_gamma(
        self,
        premium: float,
        strike: float,
        spot_price: float,
        time_remaining_minutes: float,
        option_type: str = "CE"
    ) -> Dict:
        """
        Calculate gamma dynamics for expiry day.
        
        On expiry day with low premium, gamma becomes MASSIVE.
        Small underlying moves cause huge premium changes.
        
        Args:
            premium: Current option premium
            strike: Strike price
            spot_price: Current index/stock price
            time_remaining_minutes: Minutes until close
            option_type: CE or PE
            
        Returns:
            Dict with gamma analysis
        """
        # Calculate moneyness
        if option_type.upper() == "CE":
            moneyness = (spot_price - strike) / strike * 100
            intrinsic = max(0, spot_price - strike)
        else:
            moneyness = (strike - spot_price) / strike * 100
            intrinsic = max(0, strike - spot_price)
        
        time_value = max(0, premium - intrinsic)
        
        # Estimate delta based on moneyness and time
        if time_remaining_minutes < 60:  # Last hour - delta very binary
            if moneyness > 0.5:  # ITM
                estimated_delta = min(0.95, 0.70 + moneyness * 0.1)
            elif moneyness > -0.5:  # ATM
                estimated_delta = 0.50 + moneyness * 0.3
            else:  # OTM
                estimated_delta = max(0.05, 0.30 + moneyness * 0.2)
        else:
            # More time = more gradual delta
            if moneyness > 0:
                estimated_delta = min(0.85, 0.50 + moneyness * 0.15)
            else:
                estimated_delta = max(0.15, 0.50 + moneyness * 0.15)
        
        # Gamma multiplier (how much premium changes per 1% index move)
        # Gamma is HIGHEST when: ATM + Low time + Low premium
        base_gamma = 1.0
        
        # ATM bonus
        if abs(moneyness) < 0.3:
            base_gamma *= 2.5
        elif abs(moneyness) < 0.7:
            base_gamma *= 1.8
        elif abs(moneyness) < 1.0:
            base_gamma *= 1.3
        
        # Time bonus (less time = higher gamma)
        if time_remaining_minutes < 30:
            base_gamma *= 3.0
        elif time_remaining_minutes < 60:
            base_gamma *= 2.5
        elif time_remaining_minutes < 120:
            base_gamma *= 2.0
        elif time_remaining_minutes < 180:
            base_gamma *= 1.5
        
        # Low premium bonus (gamma explosion zone)
        if premium < 10:
            base_gamma *= 2.0
        elif premium < 20:
            base_gamma *= 1.5
        elif premium < 30:
            base_gamma *= 1.2
        
        gamma_multiplier = min(base_gamma, 15.0)  # Cap at 15x
        
        # Calculate potential moves
        # For a 50-point NIFTY move
        index_move_50pt = 50
        index_move_pct = index_move_50pt / spot_price * 100
        
        potential_gain_50pt = premium * gamma_multiplier * index_move_pct
        potential_gain_100pt = premium * gamma_multiplier * (100 / spot_price * 100)
        
        return {
            "moneyness_pct": round(moneyness, 3),
            "intrinsic_value": round(intrinsic, 2),
            "time_value": round(time_value, 2),
            "estimated_delta": round(estimated_delta, 3),
            "gamma_multiplier": round(gamma_multiplier, 2),
            "potential_gain_50pt_move": round(potential_gain_50pt, 2),
            "potential_gain_100pt_move": round(potential_gain_100pt, 2),
            "potential_pct_gain_50pt": round(potential_gain_50pt / max(premium, 0.1) * 100, 1),
            "is_gamma_zone": self.MIN_PREMIUM_FOR_GAMMA <= premium <= self.MAX_PREMIUM_FOR_GAMMA
        }
    
    def analyze_gamma_opportunity(
        self,
        symbol: str,
        strike: int,
        option_type: str,
        premium: float,
        spot_price: float,
        volume: int = 0,
        oi: int = 0,
        ist_time: Optional[datetime] = None
    ) -> GammaOpportunity:
        """
        Full analysis of a potential gamma scalping opportunity.
        
        Args:
            symbol: Option symbol
            strike: Strike price
            option_type: CE or PE
            premium: Current premium
            spot_price: Current index price
            volume: Trading volume (optional)
            oi: Open interest (optional)
            ist_time: Current IST time (optional)
            
        Returns:
            GammaOpportunity dataclass with full analysis
        """
        if ist_time is None:
            ist_time = self.get_current_ist_time()
        
        time_remaining = self.get_time_remaining_minutes(ist_time)
        market_phase = self.get_market_phase(ist_time)
        
        # Calculate moneyness
        if option_type.upper() == "CE":
            moneyness = (spot_price - strike) / strike * 100
        else:
            moneyness = (strike - spot_price) / strike * 100
        
        # Get theta analysis
        theta_analysis = self.calculate_intraday_theta(
            premium, time_remaining, moneyness
        )
        
        # Get gamma analysis
        gamma_analysis = self.calculate_expiry_day_gamma(
            premium, strike, spot_price, time_remaining, option_type
        )
        
        # Calculate risk/reward
        theta_loss_15min = theta_analysis["theta_per_15min"]
        potential_gain = gamma_analysis["potential_gain_50pt_move"]
        risk_reward = potential_gain / max(theta_loss_15min, 0.1)
        
        # Score the opportunity (0-100)
        gamma_score = 0
        entry_reasons = []
        
        # Premium in sweet spot (+30 points)
        if self.IDEAL_PREMIUM_LOW <= premium <= self.IDEAL_PREMIUM_HIGH:
            gamma_score += 30
            entry_reasons.append(f"Premium in ideal range (₹{premium})")
        elif self.MIN_PREMIUM_FOR_GAMMA <= premium <= self.MAX_PREMIUM_FOR_GAMMA:
            gamma_score += 15
            entry_reasons.append(f"Premium in gamma zone (₹{premium})")
        
        # Market phase bonus (+25 points)
        if market_phase == MarketPhase.GAMMA_WINDOW:
            gamma_score += 25
            entry_reasons.append("In gamma window (1:30-3:00 PM)")
        elif market_phase == MarketPhase.LUNCH:
            gamma_score += 10
            entry_reasons.append("Approaching gamma window")
        
        # Near ATM bonus (+20 points)
        if abs(moneyness) < 0.3:
            gamma_score += 20
            entry_reasons.append("ATM strike")
        elif abs(moneyness) < 0.7:
            gamma_score += 10
            entry_reasons.append("Near ATM")
        
        # Risk/Reward bonus (+15 points)
        if risk_reward > 10:
            gamma_score += 15
            entry_reasons.append(f"Excellent R:R ({risk_reward:.1f}:1)")
        elif risk_reward > 5:
            gamma_score += 10
            entry_reasons.append(f"Good R:R ({risk_reward:.1f}:1)")
        
        # Time bonus (+10 points)
        if 60 < time_remaining < 120:  # 1-2 hours left
            gamma_score += 10
            entry_reasons.append("Optimal time window")
        
        # Determine risk level
        if premium < 10:
            risk_level = "EXTREME"  # Can go to 0 quickly
        elif premium < 20:
            risk_level = "HIGH"
        elif premium < 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Determine if it's a valid opportunity
        is_opportunity = (
            gamma_score >= 50 and
            self.MIN_PREMIUM_FOR_GAMMA <= premium <= self.MAX_PREMIUM_FOR_GAMMA and
            time_remaining > 30 and  # At least 30 min to close
            market_phase in [MarketPhase.LUNCH, MarketPhase.GAMMA_WINDOW]
        )
        
        return GammaOpportunity(
            symbol=symbol,
            strike=strike,
            option_type=option_type,
            premium=premium,
            spot_price=spot_price,
            delta=gamma_analysis["estimated_delta"],
            gamma=gamma_analysis["gamma_multiplier"],
            theta_per_15min=theta_analysis["theta_per_15min"],
            moneyness_pct=moneyness,
            time_remaining_minutes=time_remaining,
            gamma_score=gamma_score,
            risk_reward_ratio=risk_reward,
            potential_gain_50pt=gamma_analysis["potential_gain_50pt_move"],
            is_gamma_opportunity=is_opportunity,
            entry_reason=" | ".join(entry_reasons) if entry_reasons else "No strong signals",
            risk_level=risk_level
        )
    
    def scan_for_gamma_opportunities(
        self,
        index: str,
        spot_price: float,
        option_chain: List[Dict],
        ist_time: Optional[datetime] = None
    ) -> Dict:
        """
        Scan option chain for gamma scalping opportunities.
        
        Args:
            index: NIFTY or BANKNIFTY
            spot_price: Current index price
            option_chain: List of option data dicts
            ist_time: Current IST time
            
        Returns:
            Dict with scan results and top opportunities
        """
        if ist_time is None:
            ist_time = self.get_current_ist_time()
        
        market_phase = self.get_market_phase(ist_time)
        time_remaining = self.get_time_remaining_minutes(ist_time)
        
        opportunities = []
        
        for opt in option_chain:
            # Check both CE and PE
            for opt_type in ["CE", "PE"]:
                premium_key = f"{opt_type.lower()}_ltp" if f"{opt_type.lower()}_ltp" in opt else "ltp"
                premium = opt.get(premium_key, opt.get("call" if opt_type == "CE" else "put", {}).get("ltp", 0))
                
                if premium is None or premium <= 0:
                    continue
                
                # Skip if not in gamma zone
                if not (self.MIN_PREMIUM_FOR_GAMMA <= premium <= self.MAX_PREMIUM_FOR_GAMMA):
                    continue
                
                strike = opt.get("strike", opt.get("strikePrice", 0))
                if strike <= 0:
                    continue
                
                symbol = f"{index}{strike}{opt_type}"
                
                opportunity = self.analyze_gamma_opportunity(
                    symbol=symbol,
                    strike=strike,
                    option_type=opt_type,
                    premium=premium,
                    spot_price=spot_price,
                    volume=opt.get("volume", 0),
                    oi=opt.get("oi", 0),
                    ist_time=ist_time
                )
                
                if opportunity.is_gamma_opportunity:
                    opportunities.append(opportunity)
        
        # Sort by gamma score
        opportunities.sort(key=lambda x: x.gamma_score, reverse=True)
        
        # Get top 5
        top_opportunities = opportunities[:5]
        
        return {
            "index": index,
            "spot_price": spot_price,
            "scan_time": ist_time.isoformat() if ist_time else None,
            "market_phase": market_phase.value,
            "time_remaining_minutes": round(time_remaining, 0),
            "is_gamma_window": market_phase == MarketPhase.GAMMA_WINDOW,
            "total_opportunities_found": len(opportunities),
            "top_opportunities": [
                {
                    "symbol": opp.symbol,
                    "strike": opp.strike,
                    "type": opp.option_type,
                    "premium": opp.premium,
                    "gamma_score": opp.gamma_score,
                    "risk_reward": round(opp.risk_reward_ratio, 1),
                    "potential_gain_50pt": opp.potential_gain_50pt,
                    "theta_loss_15min": opp.theta_per_15min,
                    "moneyness_pct": round(opp.moneyness_pct, 2),
                    "delta": opp.delta,
                    "gamma": opp.gamma,
                    "risk_level": opp.risk_level,
                    "entry_reason": opp.entry_reason
                }
                for opp in top_opportunities
            ],
            "trading_advice": self._get_trading_advice(market_phase, time_remaining, len(opportunities))
        }
    
    def _get_trading_advice(
        self,
        market_phase: MarketPhase,
        time_remaining: float,
        opportunities_count: int
    ) -> Dict:
        """Generate trading advice based on current conditions"""
        
        advice = {
            "action": "WAIT",
            "message": "",
            "risk_warning": ""
        }
        
        if market_phase == MarketPhase.CLOSED:
            advice["action"] = "MARKET_CLOSED"
            advice["message"] = "Market is closed. Plan for next session."
        
        elif market_phase == MarketPhase.PRE_OPEN:
            advice["action"] = "WAIT"
            advice["message"] = "Market not yet open. Wait for 9:15 AM IST."
        
        elif market_phase == MarketPhase.OPENING:
            advice["action"] = "WATCH_ONLY"
            advice["message"] = "Opening volatility - avoid trading. Watch for direction."
            advice["risk_warning"] = "Wide spreads and high volatility in opening."
        
        elif market_phase == MarketPhase.MORNING_DECAY:
            advice["action"] = "MONITOR"
            advice["message"] = "Theta decay phase. Track premiums falling to gamma zone (₹10-20)."
        
        elif market_phase == MarketPhase.LUNCH:
            advice["action"] = "PREPARE"
            advice["message"] = "Consolidation phase. Identify key levels for breakout."
            if opportunities_count > 0:
                advice["message"] += f" Found {opportunities_count} potential setups."
        
        elif market_phase == MarketPhase.GAMMA_WINDOW:
            advice["action"] = "ACTIVE_SCAN"
            advice["message"] = "🎯 GAMMA WINDOW ACTIVE! Look for breakout with volume."
            advice["risk_warning"] = "Only trade with clear direction. Set tight exits."
            if opportunities_count > 0:
                advice["message"] += f" {opportunities_count} opportunities identified!"
        
        elif market_phase == MarketPhase.FINAL_HOUR:
            advice["action"] = "EXIT_ONLY"
            advice["message"] = "Final 30 minutes - EXIT positions only. Extreme decay."
            advice["risk_warning"] = "⚠️ Do NOT open new positions. Liquidity dropping."
        
        return advice
    
    def get_15min_decay_schedule(
        self,
        premium: float,
        time_remaining_minutes: float,
        moneyness_pct: float = 0
    ) -> List[Dict]:
        """
        Generate expected premium at each 15-minute interval until close.
        
        Useful for tracking if actual decay matches expected decay.
        
        Args:
            premium: Current premium
            time_remaining_minutes: Minutes until close
            moneyness_pct: Distance from ATM
            
        Returns:
            List of expected premiums at each 15-min interval
        """
        schedule = []
        current_premium = premium
        remaining = time_remaining_minutes
        
        interval = 0
        while remaining > 0:
            # Calculate theta for this interval
            theta = self.calculate_intraday_theta(
                current_premium, remaining, moneyness_pct
            )
            
            schedule.append({
                "interval": interval,
                "minutes_remaining": round(remaining, 0),
                "time_to_close": f"{int(remaining // 60)}h {int(remaining % 60)}m",
                "expected_premium": round(current_premium, 2),
                "theta_this_interval": theta["theta_per_15min"],
                "decay_rate": theta["decay_category"]
            })
            
            # Decay premium for next interval
            current_premium = max(0, current_premium - theta["theta_per_15min"])
            remaining -= 15
            interval += 1
        
        return schedule


# Global scanner instance
expiry_gamma_scanner = ExpiryDayGammaScanner()


# Convenience functions
def analyze_expiry_day_option(
    strike: int,
    option_type: str,
    premium: float,
    spot_price: float,
    index: str = "NIFTY"
) -> Dict:
    """Quick analysis of a single option for expiry day gamma play"""
    
    symbol = f"{index}{strike}{option_type}"
    opportunity = expiry_gamma_scanner.analyze_gamma_opportunity(
        symbol=symbol,
        strike=strike,
        option_type=option_type,
        premium=premium,
        spot_price=spot_price
    )
    
    return {
        "symbol": opportunity.symbol,
        "strike": opportunity.strike,
        "type": opportunity.option_type,
        "premium": opportunity.premium,
        "spot_price": opportunity.spot_price,
        "analysis": {
            "gamma_score": opportunity.gamma_score,
            "is_opportunity": opportunity.is_gamma_opportunity,
            "risk_reward": round(opportunity.risk_reward_ratio, 1),
            "potential_gain_50pt": round(opportunity.potential_gain_50pt, 2),
            "theta_loss_15min": round(opportunity.theta_per_15min, 2),
            "moneyness_pct": round(opportunity.moneyness_pct, 2),
            "delta": round(opportunity.delta, 3),
            "gamma_multiplier": round(opportunity.gamma, 2),
            "risk_level": opportunity.risk_level,
            "entry_reason": opportunity.entry_reason
        },
        "market_phase": expiry_gamma_scanner.get_market_phase().value,
        "time_remaining_minutes": round(expiry_gamma_scanner.get_time_remaining_minutes(), 0)
    }


def get_theta_decay_schedule(
    premium: float,
    time_remaining_minutes: float = None
) -> List[Dict]:
    """Get expected theta decay at 15-min intervals"""
    if time_remaining_minutes is None:
        time_remaining_minutes = expiry_gamma_scanner.get_time_remaining_minutes()
    
    return expiry_gamma_scanner.get_15min_decay_schedule(
        premium, time_remaining_minutes
    )
