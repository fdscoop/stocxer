"""
Index Options Analysis Module
Top-down analysis for NIFTY, BANKNIFTY, FINNIFTY, SENSEX, BANKEX, MIDCAPNIFTY
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IndexSymbol(Enum):
    """Supported indices for options trading"""
    NIFTY = "NSE:NIFTY50-INDEX"
    BANKNIFTY = "NSE:NIFTYBANK-INDEX"
    FINNIFTY = "NSE:FINNIFTY-INDEX"
    SENSEX = "BSE:SENSEX-INDEX"
    BANKEX = "BSE:BANKEX-INDEX"
    MIDCPNIFTY = "NSE:MIDCPNIFTY-INDEX"


# Index configurations
INDEX_CONFIG = {
    "NIFTY": {
        "symbol": "NSE:NIFTY50-INDEX",
        "lot_size": 25,
        "tick_size": 0.05,
        "strike_gap": 50,
        "option_prefix": "NIFTY",
        "exchange": "NSE"
    },
    "BANKNIFTY": {
        "symbol": "NSE:NIFTYBANK-INDEX",
        "lot_size": 15,
        "tick_size": 0.05,
        "strike_gap": 100,
        "option_prefix": "BANKNIFTY",
        "exchange": "NSE"
    },
    "FINNIFTY": {
        "symbol": "NSE:FINNIFTY-INDEX",
        "lot_size": 25,
        "tick_size": 0.05,
        "strike_gap": 50,
        "option_prefix": "FINNIFTY",
        "exchange": "NSE"
    },
    "SENSEX": {
        "symbol": "BSE:SENSEX-INDEX",
        "lot_size": 10,
        "tick_size": 0.05,
        "strike_gap": 100,
        "option_prefix": "SENSEX",
        "exchange": "BSE"
    },
    "BANKEX": {
        "symbol": "BSE:BANKEX-INDEX",
        "lot_size": 15,
        "tick_size": 0.05,
        "strike_gap": 100,
        "option_prefix": "BANKEX",
        "exchange": "BSE"
    },
    "MIDCPNIFTY": {
        "symbol": "NSE:MIDCPNIFTY-INDEX",
        "lot_size": 50,
        "tick_size": 0.05,
        "strike_gap": 25,
        "option_prefix": "MIDCPNIFTY",
        "exchange": "NSE"
    }
}


@dataclass
class MarketRegime:
    """Market regime analysis"""
    vix: float
    vix_trend: str  # rising, falling, stable
    vix_percentile: float
    regime: str  # low_vol, normal, high_vol, extreme
    trend: str  # bullish, bearish, sideways
    strength: float  # 0-100


@dataclass
class OptionStrike:
    """Single strike data"""
    strike: float
    call_ltp: float
    call_iv: float
    call_oi: int
    call_volume: int
    call_oi_change: int
    call_analysis: str  # Long Build, Short Build, Long Unwind, Short Cover
    put_ltp: float
    put_iv: float
    put_oi: int
    put_volume: int
    put_oi_change: int
    put_analysis: str


@dataclass
class FuturesData:
    """Futures contract data for enhanced signal accuracy"""
    symbol: str                    # e.g., "NSE:NIFTY26JANFUT"
    price: float                   # Current futures LTP
    basis: float                   # futures - spot
    basis_pct: float               # (basis / spot) * 100
    oi: int                        # Open interest
    volume: int                    # Today's volume
    oi_change: int                 # OI change from previous day
    oi_analysis: str               # "Long Build", "Short Build", etc.
    expiry_date: str               # Expiry date
    days_to_expiry: int
    next_month_symbol: str = ""    # Next month futures symbol
    next_month_price: float = 0    # Next month futures LTP
    rollover_cost: float = 0       # Next month - Current month price


@dataclass
class OptionChainAnalysis:
    """Complete option chain analysis"""
    index: str
    spot_price: float
    future_price: float
    basis: float
    basis_pct: float
    vix: float
    pcr_oi: float
    pcr_volume: float
    max_pain: float
    atm_strike: float
    atm_iv: float
    iv_skew: float  # Put IV - Call IV
    total_call_oi: int
    total_put_oi: int
    total_call_volume: int
    total_put_volume: int
    expiry_date: str
    days_to_expiry: int
    strikes: List[OptionStrike]
    support_levels: List[float]
    resistance_levels: List[float]
    oi_buildup_zones: Dict[str, List[float]]
    futures_data: Optional[FuturesData] = None  # Actual futures data


class IndexOptionsAnalyzer:
    """
    Comprehensive index options analyzer
    Performs top-down analysis for trading signals
    """
    
    def __init__(self, fyers_client):
        self.fyers = fyers_client
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 60  # seconds
        
        # VIX historical data cache (5-minute cache to avoid repeated API calls)
        self._vix_history_cache = None
        self._vix_cache_time = None
        self._vix_cache_duration = 300  # 5 minutes
    
    def calculate_vix_percentile(self, current_vix: float) -> tuple:
        """
        Calculate actual VIX percentile based on 1-year historical data
        
        Args:
            current_vix: Current India VIX value
            
        Returns:
            tuple: (percentile, vix_trend, avg_5d, min_1y, max_1y)
        """
        from datetime import datetime
        import numpy as np
        
        try:
            # Check cache
            now = datetime.now()
            if (self._vix_history_cache is not None and 
                self._vix_cache_time is not None and
                (now - self._vix_cache_time).seconds < self._vix_cache_duration):
                vix_df = self._vix_history_cache
            else:
                # Fetch fresh historical VIX data
                vix_df = self.fyers.get_historical_vix(days=252)
                self._vix_history_cache = vix_df
                self._vix_cache_time = now
                logger.info(f"📊 Fetched {len(vix_df)} days of historical VIX data")
            
            if vix_df is None or vix_df.empty:
                logger.warning("No historical VIX data available, using estimates")
                # Fallback to rough estimate
                return (min(100, (current_vix / 30) * 100), "stable", current_vix, 10.0, 30.0)
            
            # Get VIX close prices
            vix_closes = vix_df['close'].values
            
            # Calculate percentile
            percentile = (np.sum(vix_closes < current_vix) / len(vix_closes)) * 100
            
            # Calculate VIX trend (compare to 5-day average)
            if len(vix_closes) >= 5:
                avg_5d = np.mean(vix_closes[-5:])
                if current_vix > avg_5d * 1.05:  # 5% above 5-day avg
                    vix_trend = "rising"
                elif current_vix < avg_5d * 0.95:  # 5% below 5-day avg
                    vix_trend = "falling"
                else:
                    vix_trend = "stable"
            else:
                avg_5d = current_vix
                vix_trend = "stable"
            
            # 1-year min/max for context
            vix_min_1y = float(np.min(vix_closes))
            vix_max_1y = float(np.max(vix_closes))
            
            logger.info(f"📈 VIX: {current_vix:.2f} | Percentile: {percentile:.1f}% | Trend: {vix_trend} | 5D Avg: {avg_5d:.2f} | 1Y Range: {vix_min_1y:.2f}-{vix_max_1y:.2f}")
            
            return (round(percentile, 1), vix_trend, round(avg_5d, 2), round(vix_min_1y, 2), round(vix_max_1y, 2))
            
        except Exception as e:
            logger.error(f"Error calculating VIX percentile: {e}")
            # Fallback to rough estimate
            return (min(100, (current_vix / 30) * 100), "stable", current_vix, 10.0, 30.0)
    
    def get_market_regime(self) -> MarketRegime:
        """
        Analyze overall market regime based on VIX and trend
        
        VIX Levels:
        - < 12: Low volatility (sell options)
        - 12-18: Normal volatility
        - 18-25: High volatility (buy options)
        - > 25: Extreme volatility (hedge/reduce size)
        """
        try:
            # Fetch India VIX
            vix_data = self.fyers.get_quotes(["NSE:INDIAVIX-INDEX"])
            vix = 11.37  # Default
            
            if vix_data and vix_data.get("d"):
                vix = vix_data["d"][0]["v"].get("lp", 11.37)
            
            # Determine regime
            if vix < 12:
                regime = "low_vol"
                regime_desc = "Low Volatility - Favor selling options"
            elif vix < 18:
                regime = "normal"
                regime_desc = "Normal Volatility"
            elif vix < 25:
                regime = "high_vol"
                regime_desc = "High Volatility - Favor buying options"
            else:
                regime = "extreme"
                regime_desc = "Extreme Volatility - Reduce position size"
            
            # Get NIFTY trend
            nifty_data = self.fyers.get_quotes(["NSE:NIFTY50-INDEX"])
            trend = "sideways"
            strength = 50.0
            
            if nifty_data and nifty_data.get("d"):
                v = nifty_data["d"][0]["v"]
                change_pct = v.get("chp", 0)
                if change_pct > 0.5:
                    trend = "bullish"
                    strength = min(100, 50 + change_pct * 20)
                elif change_pct < -0.5:
                    trend = "bearish"
                    strength = min(100, 50 + abs(change_pct) * 20)
            
            # Calculate actual VIX percentile from historical data
            vix_percentile, vix_trend, vix_5d_avg, vix_min_1y, vix_max_1y = self.calculate_vix_percentile(vix)
            
            return MarketRegime(
                vix=vix,
                vix_trend=vix_trend,
                vix_percentile=vix_percentile,
                regime=regime,
                trend=trend,
                strength=strength
            )
        except Exception as e:
            logger.error(f"Error getting market regime: {e}")
            return MarketRegime(
                vix=15.0, vix_trend="stable", vix_percentile=50,
                regime="normal", trend="sideways", strength=50
            )
    
    def get_futures_data(self, index: str, spot_price: float) -> Optional[FuturesData]:
        """
        Fetch actual futures data for an index from Fyers API
        
        Args:
            index: Index name (NIFTY, BANKNIFTY, FINNIFTY)
            spot_price: Current spot price for basis calculation
            
        Returns:
            FuturesData with actual futures price, OI, volume, and analysis
        """
        try:
            # Map index to futures symbol prefix
            futures_map = {
                "NIFTY": "NIFTY",
                "BANKNIFTY": "NIFTYBANK",
                "FINNIFTY": "FINNIFTY",
                "MIDCPNIFTY": "MIDCPNIFTY"
            }
            
            fut_prefix = futures_map.get(index.upper())
            if not fut_prefix:
                logger.warning(f"No futures mapping for index: {index}")
                return None
            
            # Generate current and next month futures symbols
            # Fyers format: NSE:NIFTY{YY}{MMM}FUT (e.g., NSE:NIFTY26JANFUT)
            today = datetime.now()
            
            # Current month expiry (last Thursday)
            current_month = today.month
            current_year = today.year % 100  # 2-digit year
            
            # Month abbreviation mapping
            month_abbr = {
                1: "JAN", 2: "FEB", 3: "MAR", 4: "APR",
                5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG",
                9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"
            }
            
            # Current month symbol
            current_month_symbol = f"NSE:{fut_prefix}{current_year}{month_abbr[current_month]}FUT"
            
            # Next month symbol
            next_month = current_month + 1 if current_month < 12 else 1
            next_year = current_year if current_month < 12 else current_year + 1
            next_month_symbol = f"NSE:{fut_prefix}{next_year}{month_abbr[next_month]}FUT"
            
            logger.info(f"📊 Fetching futures data: {current_month_symbol}, {next_month_symbol}")
            
            # Fetch quotes for both months
            futures_response = self.fyers.get_quotes([current_month_symbol, next_month_symbol])
            
            if not futures_response or futures_response.get("code") != 200:
                logger.warning(f"Failed to fetch futures quotes: {futures_response}")
                return None
            
            futures_data_list = futures_response.get("d", [])
            
            current_futures = None
            next_futures = None
            
            for fut_data in futures_data_list:
                symbol = fut_data.get("n", "")
                vals = fut_data.get("v", {})
                
                if current_month_symbol in symbol or fut_prefix in symbol:
                    if month_abbr[current_month] in symbol:
                        current_futures = vals
                    elif month_abbr[next_month] in symbol:
                        next_futures = vals
            
            if not current_futures:
                # First item is usually current month
                if futures_data_list:
                    current_futures = futures_data_list[0].get("v", {})
                    if len(futures_data_list) > 1:
                        next_futures = futures_data_list[1].get("v", {})
            
            if not current_futures:
                logger.warning("No futures data found in response")
                return None
            
            # Extract data
            futures_price = current_futures.get("lp", 0) or current_futures.get("close_price", 0)
            futures_oi = current_futures.get("oi", 0) or 0
            futures_volume = current_futures.get("volume", 0) or 0
            price_change = current_futures.get("ch", 0) or 0
            
            # Calculate basis
            basis = futures_price - spot_price
            basis_pct = (basis / spot_price * 100) if spot_price > 0 else 0
            
            # OI change (from the response if available)
            oi_change = current_futures.get("oi_change", 0) or 0
            
            # Analyze OI
            oi_analysis = self.analyze_oi_change(oi_change, price_change)
            
            # Calculate days to expiry (last Thursday of current month)
            # Find last Thursday
            year = today.year
            month = current_month
            if month == 12:
                last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # Find last Thursday
            days_to_thursday = (last_day.weekday() - 3) % 7
            last_thursday = last_day - timedelta(days=days_to_thursday)
            days_to_expiry = (last_thursday - today).days
            if days_to_expiry < 0:
                # Already past expiry, move to next month
                days_to_expiry = 0
            
            # Next month data
            next_price = 0
            rollover_cost = 0
            if next_futures:
                next_price = next_futures.get("lp", 0) or next_futures.get("close_price", 0)
                rollover_cost = next_price - futures_price
            
            logger.info(f"✅ Futures: {current_month_symbol} @ ₹{futures_price:.2f}, Basis: {basis:.2f} ({basis_pct:.3f}%), OI: {futures_oi:,}")
            
            return FuturesData(
                symbol=current_month_symbol,
                price=round(futures_price, 2),
                basis=round(basis, 2),
                basis_pct=round(basis_pct, 4),
                oi=futures_oi,
                volume=futures_volume,
                oi_change=oi_change,
                oi_analysis=oi_analysis,
                expiry_date=last_thursday.strftime("%Y-%m-%d"),
                days_to_expiry=max(0, days_to_expiry),
                next_month_symbol=next_month_symbol,
                next_month_price=round(next_price, 2),
                rollover_cost=round(rollover_cost, 2)
            )
            
        except Exception as e:
            logger.error(f"Error fetching futures data for {index}: {e}")
            return None
    
    def get_expiry_dates(self, index: str) -> Dict[str, str]:
        """
        Get actual expiry dates dynamically from Fyers option chain.
        This ensures accuracy regardless of rule changes or holidays.
        """
        today = datetime.now()
        
        try:
            # Fetch actual option chain from Fyers
            symbol_map = {
                "NIFTY": "NSE:NIFTY50-INDEX",
                "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
                "FINNIFTY": "NSE:FINNIFTY-INDEX",
                "SENSEX": "BSE:SENSEX-INDEX",
                "BANKEX": "BSE:BANKEX-INDEX",
                "MIDCPNIFTY": "NSE:MIDCPNIFTY-INDEX"
            }
            
            fyers_symbol = symbol_map.get(index, "NSE:NIFTY50-INDEX")
            logger.info(f"Fetching expiries from Fyers for {fyers_symbol}")
            
            response = self.fyers.get_option_chain(fyers_symbol, strike_count=5)
            
            # Extract expiry dates from the expiryData field
            expiry_dates = []
            if response and response.get("code") == 200:
                data = response.get("data", {})
                expiry_data_list = data.get("expiryData", [])
                
                logger.info(f"Found {len(expiry_data_list)} expiries in expiryData")
                
                # Parse expiry dates from the date field (format: 'DD-MM-YYYY')
                for expiry_item in expiry_data_list:
                    date_str = expiry_item.get("date")
                    if date_str:
                        try:
                            expiry_date = datetime.strptime(date_str, "%d-%m-%Y")
                            expiry_dates.append(expiry_date)
                        except ValueError as e:
                            logger.warning(f"Could not parse expiry date: {date_str} - {e}")
                
                logger.info(f"Extracted {len(expiry_dates)} expiry dates from Fyers: {[d.strftime('%Y-%m-%d') for d in expiry_dates[:3]]}")
            
            # Sort expiries chronologically
            if expiry_dates:
                sorted_expiries = sorted(expiry_dates)
                
                # Weekly expiry is the nearest one
                weekly_expiry = sorted_expiries[0]
                
                # Next weekly is the second one
                next_weekly = sorted_expiries[1] if len(sorted_expiries) > 1 else weekly_expiry
                
                # Monthly expiry: find the last occurrence of expiry day in the month
                # This is the true monthly expiry (e.g., last Tuesday of the month)
                today = datetime.now()
                monthly_expiry = None
                
                for exp in sorted_expiries:
                    # Check if this expiry is the last occurrence of its weekday in the month
                    expiry_weekday = exp.weekday()
                    year, month = exp.year, exp.month
                    
                    # Get the last day of the month
                    if month == 12:
                        last_day_of_month = datetime(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        last_day_of_month = datetime(year, month + 1, 1) - timedelta(days=1)
                    
                    # Check if there's another occurrence of the same weekday later in the month
                    next_week = exp + timedelta(days=7)
                    is_last_occurrence = (next_week.month != exp.month) or (next_week > last_day_of_month)
                    
                    if is_last_occurrence:
                        monthly_expiry = exp
                        logger.info(f"Found monthly expiry: {exp.strftime('%Y-%m-%d')} (last {exp.strftime('%A')} of {exp.strftime('%B')})")
                        break
                
                # If no monthly found, default to a later expiry
                if not monthly_expiry:
                    monthly_expiry = sorted_expiries[2] if len(sorted_expiries) > 2 else sorted_expiries[-1]
                
                logger.info(f"✅ Using expiries from Fyers: Weekly={weekly_expiry.strftime('%Y-%m-%d')}, Next={next_weekly.strftime('%Y-%m-%d')}, Monthly={monthly_expiry.strftime('%Y-%m-%d')}")
                
                return {
                    "weekly": weekly_expiry.strftime("%Y-%m-%d"),
                    "weekly_days": (weekly_expiry - today).days,
                    "next_weekly": next_weekly.strftime("%Y-%m-%d"),
                    "next_weekly_days": (next_weekly - today).days,
                    "monthly": monthly_expiry.strftime("%Y-%m-%d"),
                    "monthly_days": (monthly_expiry - today).days
                }
            else:
                raise ValueError("No expiry dates found in option chain")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch expiries from Fyers: {e}. Using fallback calculation.")
            # Fallback: calculate next Tuesday only as last resort
            days_ahead = (1 - today.weekday()) % 7 or 7  # Next Tuesday
            weekly_expiry = today + timedelta(days=days_ahead)
            next_weekly = weekly_expiry + timedelta(days=7)
            
            # Last Tuesday of current month
            month = today.month
            year = today.year
            last_day = (datetime(year, month + 1, 1) - timedelta(days=1)).day if month < 12 else 31
            monthly_expiry = today
            for day in range(last_day, 0, -1):
                try:
                    d = datetime(year, month, day)
                    if d.weekday() == 1:  # Tuesday
                        monthly_expiry = d
                        break
                except:
                    continue
            
            return {
                "weekly": weekly_expiry.strftime("%Y-%m-%d"),
                "weekly_days": (weekly_expiry - today).days,
                "next_weekly": next_weekly.strftime("%Y-%m-%d"),
                "next_weekly_days": (next_weekly - today).days,
                "monthly": monthly_expiry.strftime("%Y-%m-%d"),
                "monthly_days": (monthly_expiry - today).days
            }

    
    def analyze_oi_change(self, oi_change: int, price_change: float) -> str:
        """
        Determine OI analysis based on OI change and price change
        
        Long Build: OI ↑, Price ↑ (Bullish)
        Short Build: OI ↑, Price ↓ (Bearish)
        Long Unwind: OI ↓, Price ↓ (Bearish unwinding)
        Short Cover: OI ↓, Price ↑ (Bullish unwinding)
        """
        if oi_change > 0:
            if price_change >= 0:
                return "Long Build"
            else:
                return "Short Build"
        else:
            if price_change >= 0:
                return "Short Cover"
            else:
                return "Long Unwind"
    
    def calculate_max_pain(self, strikes_data: List[Dict]) -> float:
        """
        Calculate Max Pain strike
        Max Pain = Strike where total loss to option buyers is maximum
        """
        if not strikes_data:
            return 0
        
        strikes = sorted(set(s.get("strike", 0) for s in strikes_data))
        min_pain = float('inf')
        max_pain_strike = strikes[len(strikes)//2]
        
        for test_strike in strikes:
            total_pain = 0
            for s in strikes_data:
                strike = s.get("strike", 0)
                call_oi = s.get("call_oi", 0)
                put_oi = s.get("put_oi", 0)
                
                # Call pain (if spot > strike)
                if test_strike > strike:
                    total_pain += (test_strike - strike) * call_oi
                
                # Put pain (if spot < strike)
                if test_strike < strike:
                    total_pain += (strike - test_strike) * put_oi
            
            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_strike = test_strike
        
        return max_pain_strike
    
    def get_support_resistance_from_oi(self, strikes_data: List[Dict], spot: float) -> Tuple[List[float], List[float]]:
        """
        Identify support and resistance levels from OI concentration
        
        High Put OI = Support (writers will defend)
        High Call OI = Resistance (writers will defend)
        """
        supports = []
        resistances = []
        
        if not strikes_data:
            return supports, resistances
        
        # Sort strikes
        sorted_strikes = sorted(strikes_data, key=lambda x: x.get("strike", 0))
        
        # Find strikes with high OI
        avg_call_oi = np.mean([s.get("call_oi", 0) for s in sorted_strikes])
        avg_put_oi = np.mean([s.get("put_oi", 0) for s in sorted_strikes])
        
        for s in sorted_strikes:
            strike = s.get("strike", 0)
            call_oi = s.get("call_oi", 0)
            put_oi = s.get("put_oi", 0)
            
            # Resistance: High call OI above spot
            if strike > spot and call_oi > avg_call_oi * 1.5:
                resistances.append(strike)
            
            # Support: High put OI below spot
            if strike < spot and put_oi > avg_put_oi * 1.5:
                supports.append(strike)
        
        return sorted(supports, reverse=True)[:3], sorted(resistances)[:3]
    
    def analyze_option_chain(self, index: str, expiry_type: str = "weekly") -> Optional[OptionChainAnalysis]:
        """
        Complete option chain analysis for an index
        
        Args:
            index: Index name (NIFTY, BANKNIFTY, etc.)
            expiry_type: "weekly" or "monthly"
        """
        try:
            config = INDEX_CONFIG.get(index)
            if not config:
                logger.error(f"Unknown index: {index}")
                return None
            
            # Get spot price
            spot_price = None
            try:
                spot_data = self.fyers.get_quotes([config["symbol"]])
                if spot_data and spot_data.get("d"):
                    spot_price = spot_data["d"][0]["v"]["lp"]
            except Exception as e:
                logger.error(f"❌ Failed to fetch spot price from Fyers: {e}")
            
            # Raise error if no spot price instead of using mock data
            if not spot_price:
                logger.error("❌ Fyers API authentication required. Cannot fetch live spot price.")
                raise Exception("❌ Fyers authentication required. Please authenticate to get live option chain data.")
            
            # Get ACTUAL futures data (not estimated)
            futures_data = self.get_futures_data(index, spot_price)
            
            if futures_data and futures_data.price > 0:
                # Use actual futures price and basis
                future_price = futures_data.price
                basis = futures_data.basis
                basis_pct = futures_data.basis_pct
                logger.info(f"✅ Using ACTUAL futures data: ₹{future_price:.2f}, Basis: {basis_pct:.4f}%")
            else:
                # Fallback to estimation if futures data unavailable
                future_price = spot_price * 1.001  # ~0.1% basis estimate
                basis = future_price - spot_price
                basis_pct = (basis / spot_price) * 100
                futures_data = None
                logger.warning(f"⚠️ Using ESTIMATED futures price: ₹{future_price:.2f} (futures data unavailable)")
            
            # Get VIX
            vix = 11.37  # Default value
            try:
                vix_data = self.fyers.get_quotes(["NSE:INDIAVIX-INDEX"])
                if vix_data and vix_data.get("d"):
                    vix = vix_data["d"][0]["v"]["lp"]
            except Exception as e:
                logger.warning(f"⚠️ Using default VIX value: {e}")
            
            # Get expiry dates
            expiries = self.get_expiry_dates(index)
            expiry_date = expiries["weekly"] if expiry_type == "weekly" else expiries["monthly"]
            days_to_expiry = expiries["weekly_days"] if expiry_type == "weekly" else expiries["monthly_days"]
            
            # Calculate ATM strike
            strike_gap = config["strike_gap"]
            atm_strike = round(spot_price / strike_gap) * strike_gap
            
            # Fetch REAL option chain data from Fyers
            logger.info(f"📡 Fetching actual option chain from Fyers for {index}")
            
            strikes_data = []
            total_call_oi = 0
            total_put_oi = 0
            total_call_volume = 0
            total_put_volume = 0
            
            chain_response = None
            try:
                chain_response = self.fyers.get_option_chain(config["symbol"], strike_count=15)
            except Exception as e:
                logger.warning(f"⚠️ Fyers API error: {e}. Using fallback estimation.")
            
            if chain_response and chain_response.get("code") == 200:
                options_chain = chain_response.get("data", {}).get("optionsChain", [])
                logger.info(f"✅ Fetched {len(options_chain)} strikes from Fyers")
                
                # Parse actual Fyers data
                for option_data in options_chain:
                    strike = option_data.get("strike_price", 0)
                    
                    # Skip index entry (strike_price = -1)
                    if strike <= 0:
                        continue
                    
                    option_type = option_data.get("option_type", "")
                    ltp = option_data.get("ltp", 0)
                    oi = option_data.get("oi", 0)
                    volume = option_data.get("volume", 0)
                    iv = option_data.get("iv", vix)  # Use IV from data or fallback to VIX
                    
                    # Find or create strike entry
                    strike_entry = next((s for s in strikes_data if s["strike"] == strike), None)
                    if not strike_entry:
                        strike_entry = {
                            "strike": strike,
                            "call_ltp": 0,
                            "call_iv": vix,
                            "call_oi": 0,
                            "call_volume": 0,
                            "call_oi_change": 0,
                            "call_analysis": "",
                            "put_ltp": 0,
                            "put_iv": vix,
                            "put_oi": 0,
                            "put_volume": 0,
                            "put_oi_change": 0,
                            "put_analysis": ""
                        }
                        strikes_data.append(strike_entry)
                    
                    # Update call or put data
                    if option_type == "CE":
                        strike_entry["call_ltp"] = round(ltp, 2)
                        strike_entry["call_iv"] = round(iv, 2)
                        strike_entry["call_oi"] = oi
                        strike_entry["call_volume"] = volume
                        strike_entry["call_oi_change"] = option_data.get("oi_change", 0)
                        strike_entry["call_analysis"] = self.analyze_oi_change(
                            strike_entry["call_oi_change"], 
                            option_data.get("price_change", 0)
                        )
                        total_call_oi += oi
                        total_call_volume += volume
                    elif option_type == "PE":
                        strike_entry["put_ltp"] = round(ltp, 2)
                        strike_entry["put_iv"] = round(iv, 2)
                        strike_entry["put_oi"] = oi
                        strike_entry["put_volume"] = volume
                        strike_entry["put_oi_change"] = option_data.get("oi_change", 0)
                        strike_entry["put_analysis"] = self.analyze_oi_change(
                            strike_entry["put_oi_change"],
                            option_data.get("price_change", 0)
                        )
                        total_put_oi += oi
                        total_put_volume += volume
                
                # Sort by strike
                strikes_data.sort(key=lambda x: x["strike"])
                logger.info(f"✅ Processed {len(strikes_data)} complete strikes with LIVE data")
                
            else:
                logger.warning("⚠️ Failed to fetch Fyers option chain, using fallback estimation")
                # Fallback to estimation only if API fails
                for i in range(-10, 11):
                    strike = atm_strike + (i * strike_gap)
                    distance = abs(strike - spot_price)
                    moneyness = distance / spot_price
                    
                    base_iv = vix / 100
                    iv_adjustment = 0.02 * (abs(i) / 5)
                    call_iv = (base_iv + iv_adjustment) * 100
                    put_iv = (base_iv + iv_adjustment + 0.005) * 100
                    
                    time_to_expiry = max(days_to_expiry / 365, 0.01)
                    call_ltp = max(0, spot_price - strike) + spot_price * call_iv/100 * np.sqrt(time_to_expiry) * 0.4
                    put_ltp = max(0, strike - spot_price) + spot_price * put_iv/100 * np.sqrt(time_to_expiry) * 0.4
                    
                    strikes_data.append({
                        "strike": strike,
                        "call_ltp": round(call_ltp, 2),
                        "call_iv": round(call_iv, 2),
                        "call_oi": 50000,
                        "call_volume": 15000,
                        "call_oi_change": 0,
                        "call_analysis": "",
                        "put_ltp": round(put_ltp, 2),
                        "put_iv": round(put_iv, 2),
                        "put_oi": 50000,
                        "put_volume": 15000,
                        "put_oi_change": 0,
                        "put_analysis": ""
                    })
                    
                    total_call_oi += 50000
                    total_put_oi += 50000
                    total_call_volume += 15000
                    total_put_volume += 15000
            
            # Calculate PCR
            pcr_oi = total_put_oi / max(total_call_oi, 1)
            pcr_volume = total_put_volume / max(total_call_volume, 1)
            
            # Calculate Max Pain
            max_pain = self.calculate_max_pain(strikes_data)
            
            # Get support/resistance from OI
            supports, resistances = self.get_support_resistance_from_oi(strikes_data, spot_price)
            
            # ATM IV
            atm_data = next((s for s in strikes_data if s["strike"] == atm_strike), None)
            atm_iv = atm_data["call_iv"] if atm_data else vix
            
            # IV Skew
            iv_skew = atm_data["put_iv"] - atm_data["call_iv"] if atm_data else 0
            
            # OI buildup zones
            bullish_zones = [s["strike"] for s in strikes_data if s["put_analysis"] == "Long Build" and s["strike"] < spot_price]
            bearish_zones = [s["strike"] for s in strikes_data if s["call_analysis"] == "Long Build" and s["strike"] > spot_price]
            
            return OptionChainAnalysis(
                index=index,
                spot_price=spot_price,
                future_price=future_price,
                basis=basis,
                basis_pct=basis_pct,
                vix=vix,
                pcr_oi=round(pcr_oi, 2),
                pcr_volume=round(pcr_volume, 2),
                max_pain=max_pain,
                atm_strike=atm_strike,
                atm_iv=round(atm_iv, 2),
                iv_skew=round(iv_skew, 2),
                total_call_oi=total_call_oi,
                total_put_oi=total_put_oi,
                total_call_volume=total_call_volume,
                total_put_volume=total_put_volume,
                expiry_date=expiry_date,
                days_to_expiry=days_to_expiry,
                strikes=[OptionStrike(**s) for s in strikes_data],
                support_levels=supports,
                resistance_levels=resistances,
                oi_buildup_zones={
                    "bullish": bullish_zones,
                    "bearish": bearish_zones
                },
                futures_data=futures_data  # Actual futures data (or None if unavailable)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing option chain: {e}")
            return None
    
    def generate_index_signal(self, index: str) -> Dict:
        """
        Generate trading signal using top-down analysis
        
        Analysis Flow:
        1. Market Regime (VIX) → Position sizing, strategy type
        2. Index Direction → Bullish/Bearish bias
        3. Option Chain → Entry levels, targets, stop loss
        4. Signal → Specific trade recommendation
        """
        try:
            # Step 1: Market Regime
            regime = self.get_market_regime()
            
            # Step 2: Option Chain Analysis
            chain = self.analyze_option_chain(index, "weekly")
            if not chain:
                return {"error": "Failed to analyze option chain"}
            
            # Step 3: Generate Signal
            signal = {
                "index": index,
                "timestamp": datetime.now().isoformat(),
                "market_regime": {
                    "vix": regime.vix,
                    "regime": regime.regime,
                    "trend": regime.trend,
                    "strength": regime.strength
                },
                "spot_analysis": {
                    "spot": chain.spot_price,
                    "future": chain.future_price,
                    "basis": chain.basis,
                    "basis_pct": chain.basis_pct
                },
                "options_analysis": {
                    "pcr_oi": chain.pcr_oi,
                    "pcr_volume": chain.pcr_volume,
                    "max_pain": chain.max_pain,
                    "atm_iv": chain.atm_iv,
                    "iv_skew": chain.iv_skew,
                    "days_to_expiry": chain.days_to_expiry
                },
                "levels": {
                    "support": chain.support_levels,
                    "resistance": chain.resistance_levels,
                    "max_pain": chain.max_pain
                },
                "signal": self._determine_signal(regime, chain),
                "strategy": self._suggest_strategy(regime, chain)
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return {"error": str(e)}
    
    def _determine_signal(self, regime: MarketRegime, chain: OptionChainAnalysis) -> Dict:
        """Determine overall signal from analysis"""
        
        # PCR Analysis
        # PCR > 1.2: Oversold (Bullish)
        # PCR < 0.8: Overbought (Bearish)
        # 0.8-1.2: Neutral
        pcr_signal = "neutral"
        if chain.pcr_oi > 1.2:
            pcr_signal = "bullish"
        elif chain.pcr_oi < 0.8:
            pcr_signal = "bearish"
        
        # Max Pain Analysis
        # Spot below max pain: Likely to move up
        # Spot above max pain: Likely to move down
        pain_signal = "neutral"
        pain_distance = (chain.max_pain - chain.spot_price) / chain.spot_price * 100
        if pain_distance > 0.5:
            pain_signal = "bullish"
        elif pain_distance < -0.5:
            pain_signal = "bearish"
        
        # IV Analysis
        # High IV (>20): Options expensive, favor selling
        # Low IV (<12): Options cheap, favor buying
        iv_signal = "neutral"
        if chain.atm_iv > 20:
            iv_signal = "high"
        elif chain.atm_iv < 12:
            iv_signal = "low"
        
        # Combine signals
        bullish_count = sum([
            pcr_signal == "bullish",
            pain_signal == "bullish",
            regime.trend == "bullish"
        ])
        
        bearish_count = sum([
            pcr_signal == "bearish",
            pain_signal == "bearish",
            regime.trend == "bearish"
        ])
        
        if bullish_count >= 2:
            direction = "BULLISH"
            confidence = bullish_count / 3 * 100
        elif bearish_count >= 2:
            direction = "BEARISH"
            confidence = bearish_count / 3 * 100
        else:
            direction = "NEUTRAL"
            confidence = 50
        
        return {
            "direction": direction,
            "confidence": round(confidence, 1),
            "pcr_signal": pcr_signal,
            "max_pain_signal": pain_signal,
            "iv_condition": iv_signal,
            "reasoning": self._get_reasoning(pcr_signal, pain_signal, regime.trend, chain)
        }
    
    def _get_reasoning(self, pcr: str, pain: str, trend: str, chain: OptionChainAnalysis) -> str:
        """Generate human-readable reasoning"""
        reasons = []
        
        if pcr == "bullish":
            reasons.append(f"PCR at {chain.pcr_oi:.2f} indicates oversold conditions")
        elif pcr == "bearish":
            reasons.append(f"PCR at {chain.pcr_oi:.2f} indicates overbought conditions")
        
        pain_distance = (chain.max_pain - chain.spot_price) / chain.spot_price * 100
        if abs(pain_distance) > 0.5:
            reasons.append(f"Max Pain at {chain.max_pain:.0f} ({pain_distance:+.1f}% from spot)")
        
        if chain.support_levels:
            reasons.append(f"Key support: {chain.support_levels[0]:.0f}")
        if chain.resistance_levels:
            reasons.append(f"Key resistance: {chain.resistance_levels[0]:.0f}")
        
        return " | ".join(reasons) if reasons else "No strong directional signals"
    
    def _suggest_strategy(self, regime: MarketRegime, chain: OptionChainAnalysis) -> Dict:
        """Suggest options strategy based on analysis"""
        
        strategies = []
        
        # Based on VIX regime
        if regime.regime == "low_vol":
            strategies.append({
                "name": "Iron Condor / Short Strangle",
                "type": "sell",
                "rationale": "Low VIX favors option selling strategies"
            })
        elif regime.regime == "high_vol":
            strategies.append({
                "name": "Long Straddle / Strangle",
                "type": "buy",
                "rationale": "High VIX may lead to large moves"
            })
        
        # Based on direction
        signal = self._determine_signal(regime, chain)
        
        if signal["direction"] == "BULLISH":
            strategies.append({
                "name": "Bull Call Spread",
                "type": "directional",
                "entry": chain.atm_strike,
                "target": chain.resistance_levels[0] if chain.resistance_levels else chain.atm_strike + 100,
                "stop_loss": chain.support_levels[0] if chain.support_levels else chain.atm_strike - 100
            })
            if regime.regime == "low_vol":
                strategies.append({
                    "name": "Bull Put Spread",
                    "type": "credit",
                    "sell_strike": chain.support_levels[0] if chain.support_levels else chain.atm_strike - 100,
                    "buy_strike": chain.support_levels[0] - 50 if chain.support_levels else chain.atm_strike - 150
                })
        
        elif signal["direction"] == "BEARISH":
            strategies.append({
                "name": "Bear Put Spread",
                "type": "directional",
                "entry": chain.atm_strike,
                "target": chain.support_levels[0] if chain.support_levels else chain.atm_strike - 100,
                "stop_loss": chain.resistance_levels[0] if chain.resistance_levels else chain.atm_strike + 100
            })
            if regime.regime == "low_vol":
                strategies.append({
                    "name": "Bear Call Spread",
                    "type": "credit",
                    "sell_strike": chain.resistance_levels[0] if chain.resistance_levels else chain.atm_strike + 100,
                    "buy_strike": chain.resistance_levels[0] + 50 if chain.resistance_levels else chain.atm_strike + 150
                })
        
        else:  # NEUTRAL
            strategies.append({
                "name": "Iron Condor",
                "type": "neutral",
                "upper_sell": chain.resistance_levels[0] if chain.resistance_levels else chain.atm_strike + 150,
                "lower_sell": chain.support_levels[0] if chain.support_levels else chain.atm_strike - 150
            })
        
        return {
            "primary": strategies[0] if strategies else None,
            "alternatives": strategies[1:] if len(strategies) > 1 else [],
            "position_size": "50%" if regime.regime == "extreme" else "100%",
            "risk_note": "High VIX - reduce size" if regime.regime in ["high_vol", "extreme"] else "Normal sizing"
        }


# Singleton instance
index_analyzer = None

def get_index_analyzer(fyers_client):
    global index_analyzer
    if index_analyzer is None:
        index_analyzer = IndexOptionsAnalyzer(fyers_client)
    return index_analyzer
