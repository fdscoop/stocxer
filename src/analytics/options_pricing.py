"""
Options Pricing and Greeks Calculator
Uses Black-Scholes model and numerical methods
"""
import numpy as np
from scipy.stats import norm
from typing import Dict, Optional
# import QuantLib as ql  # Optional: for advanced derivatives pricing
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class OptionsPricer:
    """Calculate option prices and Greeks"""
    
    def __init__(self):
        self.risk_free_rate = 0.065  # Indian risk-free rate (~6.5%)
    
    def black_scholes_price(
        self,
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,  # in years
        volatility: float,
        option_type: str = "call",
        dividend_yield: float = 0.0
    ) -> float:
        """
        Calculate option price using Black-Scholes formula
        
        Args:
            spot_price: Current underlying price
            strike_price: Strike price
            time_to_expiry: Time to expiration in years
            volatility: Implied volatility (annualized)
            option_type: "call" or "put"
            dividend_yield: Dividend yield (annualized)
            
        Returns:
            Option price
        """
        if time_to_expiry <= 0:
            # At expiration
            if option_type.lower() == "call":
                return max(spot_price - strike_price, 0)
            else:
                return max(strike_price - spot_price, 0)
        
        d1 = (np.log(spot_price / strike_price) + 
              (self.risk_free_rate - dividend_yield + 0.5 * volatility**2) * time_to_expiry) / \
             (volatility * np.sqrt(time_to_expiry))
        
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        if option_type.lower() == "call":
            price = (spot_price * np.exp(-dividend_yield * time_to_expiry) * norm.cdf(d1) - 
                    strike_price * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(d2))
        else:
            price = (strike_price * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(-d2) - 
                    spot_price * np.exp(-dividend_yield * time_to_expiry) * norm.cdf(-d1))
        
        return price
    
    def calculate_greeks(
        self,
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        option_type: str = "call",
        dividend_yield: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate all Greeks for an option
        
        Returns:
            Dict with delta, gamma, theta, vega, rho
        """
        if time_to_expiry <= 0:
            return {
                "delta": 1.0 if option_type == "call" and spot_price > strike_price else 0.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
                "rho": 0.0
            }
        
        d1 = (np.log(spot_price / strike_price) + 
              (self.risk_free_rate - dividend_yield + 0.5 * volatility**2) * time_to_expiry) / \
             (volatility * np.sqrt(time_to_expiry))
        
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        # Delta
        if option_type.lower() == "call":
            delta = np.exp(-dividend_yield * time_to_expiry) * norm.cdf(d1)
        else:
            delta = -np.exp(-dividend_yield * time_to_expiry) * norm.cdf(-d1)
        
        # Gamma (same for calls and puts)
        gamma = (np.exp(-dividend_yield * time_to_expiry) * norm.pdf(d1)) / \
                (spot_price * volatility * np.sqrt(time_to_expiry))
        
        # Vega (same for calls and puts) - per 1% change in volatility
        vega = spot_price * np.exp(-dividend_yield * time_to_expiry) * \
               norm.pdf(d1) * np.sqrt(time_to_expiry) / 100
        
        # Theta (per day)
        if option_type.lower() == "call":
            theta = (-spot_price * norm.pdf(d1) * volatility * np.exp(-dividend_yield * time_to_expiry) / \
                    (2 * np.sqrt(time_to_expiry)) - 
                    self.risk_free_rate * strike_price * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(d2) +
                    dividend_yield * spot_price * np.exp(-dividend_yield * time_to_expiry) * norm.cdf(d1)) / 365
        else:
            theta = (-spot_price * norm.pdf(d1) * volatility * np.exp(-dividend_yield * time_to_expiry) / \
                    (2 * np.sqrt(time_to_expiry)) + 
                    self.risk_free_rate * strike_price * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(-d2) -
                    dividend_yield * spot_price * np.exp(-dividend_yield * time_to_expiry) * norm.cdf(-d1)) / 365
        
        # Rho (per 1% change in interest rate)
        if option_type.lower() == "call":
            rho = strike_price * time_to_expiry * np.exp(-self.risk_free_rate * time_to_expiry) * \
                  norm.cdf(d2) / 100
        else:
            rho = -strike_price * time_to_expiry * np.exp(-self.risk_free_rate * time_to_expiry) * \
                  norm.cdf(-d2) / 100
        
        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 4),
            "theta": round(theta, 4),
            "vega": round(vega, 4),
            "rho": round(rho, 4)
        }
    
    def calculate_implied_volatility(
        self,
        market_price: float,
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        option_type: str = "call",
        dividend_yield: float = 0.0
    ) -> Optional[float]:
        """
        Calculate implied volatility using Newton-Raphson method
        
        Returns:
            Implied volatility or None if calculation fails
        """
        if time_to_expiry <= 0:
            return None
        
        # Initial guess
        volatility = 0.3
        max_iterations = 100
        tolerance = 1e-5
        
        for i in range(max_iterations):
            price = self.black_scholes_price(
                spot_price, strike_price, time_to_expiry,
                volatility, option_type, dividend_yield
            )
            
            diff = market_price - price
            
            if abs(diff) < tolerance:
                return volatility
            
            # Calculate vega for Newton-Raphson
            d1 = (np.log(spot_price / strike_price) + 
                  (self.risk_free_rate - dividend_yield + 0.5 * volatility**2) * time_to_expiry) / \
                 (volatility * np.sqrt(time_to_expiry))
            
            vega = spot_price * np.exp(-dividend_yield * time_to_expiry) * \
                   norm.pdf(d1) * np.sqrt(time_to_expiry)
            
            if vega < 1e-10:
                return None
            
            volatility = volatility + diff / vega
            
            # Keep volatility in reasonable range
            volatility = max(0.01, min(volatility, 5.0))
        
        logger.warning(f"IV calculation did not converge after {max_iterations} iterations")
        return None
    
    def time_to_expiry_years(
        self,
        expiry_date: date,
        current_date: Optional[date] = None
    ) -> float:
        """
        Calculate time to expiry in years
        
        Args:
            expiry_date: Option expiry date
            current_date: Current date (defaults to today)
            
        Returns:
            Time to expiry in years
        """
        if current_date is None:
            current_date = date.today()
        
        days_to_expiry = (expiry_date - current_date).days
        return max(days_to_expiry / 365.0, 0.0)
    
    def calculate_option_metrics(
        self,
        spot_price: float,
        strike_price: float,
        market_price: float,
        time_to_expiry: float,
        option_type: str = "call",
        dividend_yield: float = 0.0
    ) -> Dict:
        """
        Calculate comprehensive option metrics
        
        Returns:
            Dict with price, Greeks, IV, intrinsic value, time value
        """
        # Intrinsic value
        if option_type.lower() == "call":
            intrinsic_value = max(spot_price - strike_price, 0)
        else:
            intrinsic_value = max(strike_price - spot_price, 0)
        
        # Time value
        time_value = market_price - intrinsic_value
        
        # Implied volatility
        iv = self.calculate_implied_volatility(
            market_price, spot_price, strike_price,
            time_to_expiry, option_type, dividend_yield
        )
        
        # Calculate Greeks using IV if available
        if iv:
            greeks = self.calculate_greeks(
                spot_price, strike_price, time_to_expiry,
                iv, option_type, dividend_yield
            )
            theoretical_price = self.black_scholes_price(
                spot_price, strike_price, time_to_expiry,
                iv, option_type, dividend_yield
            )
        else:
            greeks = {}
            theoretical_price = None
        
        return {
            "market_price": market_price,
            "theoretical_price": theoretical_price,
            "intrinsic_value": intrinsic_value,
            "time_value": time_value,
            "implied_volatility": iv,
            "greeks": greeks,
            "time_to_expiry_days": time_to_expiry * 365,
            "moneyness": spot_price / strike_price
        }


# Global pricer instance
options_pricer = OptionsPricer()
