"""
Index Constituents Data Module
Contains comprehensive data for NIFTY50, BANKNIFTY, SENSEX, and FINNIFTY
Including weights, sector classifications, and correlation data
"""
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Sector(Enum):
    """Sector classifications for stocks"""
    BANKING = "Banking"
    IT = "Information Technology"
    OIL_GAS = "Oil & Gas"
    FMCG = "FMCG"
    PHARMA = "Pharmaceuticals"
    AUTO = "Automobiles"
    METALS = "Metals & Mining"
    TELECOM = "Telecom"
    CEMENT = "Cement"
    POWER = "Power & Utilities"
    FINANCIALS = "Financial Services"
    REALTY = "Real Estate"
    INFRA = "Infrastructure"
    CONSUMER = "Consumer Durables"
    INSURANCE = "Insurance"
    NBFC = "NBFCs"
    CAPITAL_GOODS = "Capital Goods"
    DIVERSIFIED = "Diversified"


@dataclass
class StockConstituent:
    """Represents a stock in an index"""
    symbol: str              # NSE symbol (e.g., "RELIANCE")
    fyers_symbol: str        # Fyers format (e.g., "NSE:RELIANCE-EQ")
    name: str                # Full company name
    weight: float            # Index weight in percentage
    sector: Sector           # Sector classification
    beta: float = 1.0        # Historical beta vs index (1.0 = moves with market)
    avg_correlation: float = 0.7  # Average correlation with index


# =============================================================================
# NIFTY 50 CONSTITUENTS (Updated January 2026)
# =============================================================================
NIFTY50_CONSTITUENTS: List[StockConstituent] = [
    # Top Holdings (Weight > 4%)
    StockConstituent("RELIANCE", "NSE:RELIANCE-EQ", "Reliance Industries Ltd", 9.31, Sector.OIL_GAS, 1.05, 0.82),
    StockConstituent("HDFCBANK", "NSE:HDFCBANK-EQ", "HDFC Bank Ltd", 6.95, Sector.BANKING, 0.95, 0.85),
    StockConstituent("BHARTIARTL", "NSE:BHARTIARTL-EQ", "Bharti Airtel Ltd", 5.96, Sector.TELECOM, 0.85, 0.72),
    StockConstituent("TCS", "NSE:TCS-EQ", "Tata Consultancy Services", 5.57, Sector.IT, 0.75, 0.68),
    StockConstituent("ICICIBANK", "NSE:ICICIBANK-EQ", "ICICI Bank Ltd", 4.81, Sector.BANKING, 1.10, 0.88),
    StockConstituent("SBIN", "NSE:SBIN-EQ", "State Bank of India", 4.67, Sector.BANKING, 1.25, 0.85),
    
    # High Weight (2-4%)
    StockConstituent("INFY", "NSE:INFY-EQ", "Infosys Ltd", 3.82, Sector.IT, 0.80, 0.72),
    StockConstituent("BAJFINANCE", "NSE:BAJFINANCE-EQ", "Bajaj Finance Ltd", 3.45, Sector.NBFC, 1.30, 0.78),
    StockConstituent("HINDUNILVR", "NSE:HINDUNILVR-EQ", "Hindustan Unilever Ltd", 3.12, Sector.FMCG, 0.65, 0.55),
    StockConstituent("LT", "NSE:LT-EQ", "Larsen & Toubro Ltd", 2.89, Sector.INFRA, 1.15, 0.80),
    StockConstituent("MARUTI", "NSE:MARUTI-EQ", "Maruti Suzuki India Ltd", 2.56, Sector.AUTO, 1.10, 0.75),
    StockConstituent("HCLTECH", "NSE:HCLTECH-EQ", "HCL Technologies Ltd", 2.48, Sector.IT, 0.82, 0.70),
    StockConstituent("M&M", "NSE:M&M-EQ", "Mahindra & Mahindra Ltd", 2.35, Sector.AUTO, 1.05, 0.73),
    StockConstituent("KOTAKBANK", "NSE:KOTAKBANK-EQ", "Kotak Mahindra Bank Ltd", 2.28, Sector.BANKING, 0.90, 0.82),
    StockConstituent("ITC", "NSE:ITC-EQ", "ITC Ltd", 2.24, Sector.FMCG, 0.70, 0.58),
    StockConstituent("AXISBANK", "NSE:AXISBANK-EQ", "Axis Bank Ltd", 2.18, Sector.BANKING, 1.15, 0.85),
    StockConstituent("SUNPHARMA", "NSE:SUNPHARMA-EQ", "Sun Pharmaceutical Industries", 2.10, Sector.PHARMA, 0.75, 0.62),
    StockConstituent("TITAN", "NSE:TITAN-EQ", "Titan Company Ltd", 2.05, Sector.CONSUMER, 1.20, 0.72),
    StockConstituent("ULTRACEMCO", "NSE:ULTRACEMCO-EQ", "UltraTech Cement Ltd", 1.95, Sector.CEMENT, 1.10, 0.75),
    StockConstituent("NTPC", "NSE:NTPC-EQ", "NTPC Ltd", 1.85, Sector.POWER, 0.95, 0.70),
    
    # Medium Weight (1-2%)
    StockConstituent("ADANIPORTS", "NSE:ADANIPORTS-EQ", "Adani Ports and SEZ", 1.75, Sector.INFRA, 1.35, 0.65),
    StockConstituent("BAJAJFINSV", "NSE:BAJAJFINSV-EQ", "Bajaj Finserv Ltd", 1.68, Sector.NBFC, 1.25, 0.76),
    StockConstituent("ONGC", "NSE:ONGC-EQ", "Oil & Natural Gas Corporation", 1.62, Sector.OIL_GAS, 1.00, 0.68),
    StockConstituent("NESTLEIND", "NSE:NESTLEIND-EQ", "Nestle India Ltd", 1.55, Sector.FMCG, 0.55, 0.50),
    StockConstituent("ASIANPAINT", "NSE:ASIANPAINT-EQ", "Asian Paints Ltd", 1.48, Sector.CONSUMER, 0.85, 0.65),
    StockConstituent("BAJAJ-AUTO", "NSE:BAJAJ-AUTO-EQ", "Bajaj Auto Ltd", 1.42, Sector.AUTO, 0.90, 0.68),
    StockConstituent("POWERGRID", "NSE:POWERGRID-EQ", "Power Grid Corporation", 1.38, Sector.POWER, 0.75, 0.62),
    StockConstituent("SHRIRAMFIN", "NSE:SHRIRAMFIN-EQ", "Shriram Finance Ltd", 1.35, Sector.NBFC, 1.20, 0.72),
    StockConstituent("TATAMOTORS", "NSE:TATAMOTORS-EQ", "Tata Motors Ltd", 1.32, Sector.AUTO, 1.45, 0.78),
    StockConstituent("EICHERMOT", "NSE:EICHERMOT-EQ", "Eicher Motors Ltd", 1.28, Sector.AUTO, 1.00, 0.70),
    
    # Lower Weight (0.5-1%)
    StockConstituent("COALINDIA", "NSE:COALINDIA-EQ", "Coal India Ltd", 0.95, Sector.METALS, 0.90, 0.60),
    StockConstituent("TATASTEEL", "NSE:TATASTEEL-EQ", "Tata Steel Ltd", 0.92, Sector.METALS, 1.35, 0.72),
    StockConstituent("WIPRO", "NSE:WIPRO-EQ", "Wipro Ltd", 0.88, Sector.IT, 0.78, 0.68),
    StockConstituent("TECHM", "NSE:TECHM-EQ", "Tech Mahindra Ltd", 0.85, Sector.IT, 0.95, 0.70),
    StockConstituent("HINDALCO", "NSE:HINDALCO-EQ", "Hindalco Industries Ltd", 0.82, Sector.METALS, 1.40, 0.70),
    StockConstituent("GRASIM", "NSE:GRASIM-EQ", "Grasim Industries Ltd", 0.78, Sector.CEMENT, 1.05, 0.72),
    StockConstituent("JSWSTEEL", "NSE:JSWSTEEL-EQ", "JSW Steel Ltd", 0.75, Sector.METALS, 1.45, 0.68),
    StockConstituent("ADANIENT", "NSE:ADANIENT-EQ", "Adani Enterprises Ltd", 0.72, Sector.DIVERSIFIED, 1.80, 0.55),
    StockConstituent("DIVISLAB", "NSE:DIVISLAB-EQ", "Divi's Laboratories Ltd", 0.68, Sector.PHARMA, 0.85, 0.58),
    StockConstituent("DRREDDY", "NSE:DRREDDY-EQ", "Dr. Reddy's Laboratories", 0.65, Sector.PHARMA, 0.72, 0.55),
    StockConstituent("CIPLA", "NSE:CIPLA-EQ", "Cipla Ltd", 0.62, Sector.PHARMA, 0.78, 0.58),
    StockConstituent("HEROMOTOCO", "NSE:HEROMOTOCO-EQ", "Hero MotoCorp Ltd", 0.58, Sector.AUTO, 0.85, 0.65),
    StockConstituent("BRITANNIA", "NSE:BRITANNIA-EQ", "Britannia Industries Ltd", 0.55, Sector.FMCG, 0.65, 0.52),
    StockConstituent("INDUSINDBK", "NSE:INDUSINDBK-EQ", "IndusInd Bank Ltd", 0.52, Sector.BANKING, 1.30, 0.78),
    StockConstituent("APOLLOHOSP", "NSE:APOLLOHOSP-EQ", "Apollo Hospitals Enterprise", 0.50, Sector.PHARMA, 1.05, 0.62),
    StockConstituent("BPCL", "NSE:BPCL-EQ", "Bharat Petroleum Corporation", 0.48, Sector.OIL_GAS, 1.10, 0.65),
    StockConstituent("TATACONSUM", "NSE:TATACONSUM-EQ", "Tata Consumer Products", 0.45, Sector.FMCG, 0.80, 0.60),
    StockConstituent("SBILIFE", "NSE:SBILIFE-EQ", "SBI Life Insurance", 0.42, Sector.INSURANCE, 1.00, 0.70),
    StockConstituent("HDFCLIFE", "NSE:HDFCLIFE-EQ", "HDFC Life Insurance", 0.40, Sector.INSURANCE, 0.95, 0.68),
    StockConstituent("TRENT", "NSE:TRENT-EQ", "Trent Ltd", 0.38, Sector.CONSUMER, 1.25, 0.65),
]


# =============================================================================
# BANK NIFTY CONSTITUENTS (14 stocks)
# =============================================================================
BANKNIFTY_CONSTITUENTS: List[StockConstituent] = [
    StockConstituent("HDFCBANK", "NSE:HDFCBANK-EQ", "HDFC Bank Ltd", 27.72, Sector.BANKING, 0.85, 0.92),
    StockConstituent("ICICIBANK", "NSE:ICICIBANK-EQ", "ICICI Bank Ltd", 19.17, Sector.BANKING, 0.95, 0.94),
    StockConstituent("SBIN", "NSE:SBIN-EQ", "State Bank of India", 18.61, Sector.BANKING, 1.10, 0.90),
    StockConstituent("KOTAKBANK", "NSE:KOTAKBANK-EQ", "Kotak Mahindra Bank Ltd", 8.24, Sector.BANKING, 0.80, 0.88),
    StockConstituent("AXISBANK", "NSE:AXISBANK-EQ", "Axis Bank Ltd", 7.89, Sector.BANKING, 1.05, 0.92),
    StockConstituent("BANKBARODA", "NSE:BANKBARODA-EQ", "Bank of Baroda", 3.08, Sector.BANKING, 1.25, 0.82),
    StockConstituent("PNB", "NSE:PNB-EQ", "Punjab National Bank", 2.86, Sector.BANKING, 1.35, 0.78),
    StockConstituent("CANBK", "NSE:CANBK-EQ", "Canara Bank", 2.76, Sector.BANKING, 1.30, 0.80),
    StockConstituent("UNIONBANK", "NSE:UNIONBANK-EQ", "Union Bank of India", 2.63, Sector.BANKING, 1.35, 0.75),
    StockConstituent("AUBANK", "NSE:AUBANK-EQ", "AU Small Finance Bank", 1.48, Sector.BANKING, 1.15, 0.72),
    StockConstituent("INDUSINDBK", "NSE:INDUSINDBK-EQ", "IndusInd Bank Ltd", 1.44, Sector.BANKING, 1.20, 0.82),
    StockConstituent("IDFCFIRSTB", "NSE:IDFCFIRSTB-EQ", "IDFC First Bank Ltd", 1.39, Sector.BANKING, 1.40, 0.70),
    StockConstituent("YESBANK", "NSE:YESBANK-EQ", "Yes Bank Ltd", 1.39, Sector.BANKING, 1.60, 0.65),
    StockConstituent("FEDERALBNK", "NSE:FEDERALBNK-EQ", "Federal Bank Ltd", 1.34, Sector.BANKING, 1.10, 0.75),
]


# =============================================================================
# BSE SENSEX CONSTITUENTS (30 stocks)
# =============================================================================
SENSEX_CONSTITUENTS: List[StockConstituent] = [
    # Top Holdings
    StockConstituent("RELIANCE", "NSE:RELIANCE-EQ", "Reliance Industries Ltd", 11.74, Sector.OIL_GAS, 1.05, 0.82),
    StockConstituent("HDFCBANK", "NSE:HDFCBANK-EQ", "HDFC Bank Ltd", 8.62, Sector.BANKING, 0.95, 0.85),
    StockConstituent("BHARTIARTL", "NSE:BHARTIARTL-EQ", "Bharti Airtel Ltd", 7.38, Sector.TELECOM, 0.85, 0.72),
    StockConstituent("TCS", "NSE:TCS-EQ", "Tata Consultancy Services", 7.07, Sector.IT, 0.75, 0.68),
    StockConstituent("ICICIBANK", "NSE:ICICIBANK-EQ", "ICICI Bank Ltd", 6.14, Sector.BANKING, 1.10, 0.88),
    StockConstituent("SBIN", "NSE:SBIN-EQ", "State Bank of India", 5.67, Sector.BANKING, 1.25, 0.85),
    
    # Other Major Stocks
    StockConstituent("INFY", "NSE:INFY-EQ", "Infosys Ltd", 4.95, Sector.IT, 0.80, 0.72),
    StockConstituent("BAJFINANCE", "NSE:BAJFINANCE-EQ", "Bajaj Finance Ltd", 4.20, Sector.NBFC, 1.30, 0.78),
    StockConstituent("HINDUNILVR", "NSE:HINDUNILVR-EQ", "Hindustan Unilever Ltd", 3.85, Sector.FMCG, 0.65, 0.55),
    StockConstituent("LT", "NSE:LT-EQ", "Larsen & Toubro Ltd", 3.55, Sector.INFRA, 1.15, 0.80),
    StockConstituent("MARUTI", "NSE:MARUTI-EQ", "Maruti Suzuki India Ltd", 3.12, Sector.AUTO, 1.10, 0.75),
    StockConstituent("M&M", "NSE:M&M-EQ", "Mahindra & Mahindra Ltd", 2.85, Sector.AUTO, 1.05, 0.73),
    StockConstituent("HCLTECH", "NSE:HCLTECH-EQ", "HCL Technologies Ltd", 2.72, Sector.IT, 0.82, 0.70),
    StockConstituent("KOTAKBANK", "NSE:KOTAKBANK-EQ", "Kotak Mahindra Bank Ltd", 2.55, Sector.BANKING, 0.90, 0.82),
    StockConstituent("ITC", "NSE:ITC-EQ", "ITC Ltd", 2.48, Sector.FMCG, 0.70, 0.58),
    StockConstituent("SUNPHARMA", "NSE:SUNPHARMA-EQ", "Sun Pharmaceutical Industries", 2.35, Sector.PHARMA, 0.75, 0.62),
    StockConstituent("AXISBANK", "NSE:AXISBANK-EQ", "Axis Bank Ltd", 2.28, Sector.BANKING, 1.15, 0.85),
    StockConstituent("TITAN", "NSE:TITAN-EQ", "Titan Company Ltd", 2.15, Sector.CONSUMER, 1.20, 0.72),
    StockConstituent("ULTRACEMCO", "NSE:ULTRACEMCO-EQ", "UltraTech Cement Ltd", 2.05, Sector.CEMENT, 1.10, 0.75),
    StockConstituent("ADANIPORTS", "NSE:ADANIPORTS-EQ", "Adani Ports and SEZ", 1.92, Sector.INFRA, 1.35, 0.65),
    StockConstituent("NTPC", "NSE:NTPC-EQ", "NTPC Ltd", 1.85, Sector.POWER, 0.95, 0.70),
    StockConstituent("BAJAJFINSV", "NSE:BAJAJFINSV-EQ", "Bajaj Finserv Ltd", 1.78, Sector.NBFC, 1.25, 0.76),
    StockConstituent("NESTLEIND", "NSE:NESTLEIND-EQ", "Nestle India Ltd", 1.62, Sector.FMCG, 0.55, 0.50),
    StockConstituent("TECHM", "NSE:TECHM-EQ", "Tech Mahindra Ltd", 1.48, Sector.IT, 0.95, 0.70),
    StockConstituent("ASIANPAINT", "NSE:ASIANPAINT-EQ", "Asian Paints Ltd", 1.35, Sector.CONSUMER, 0.85, 0.65),
    StockConstituent("POWERGRID", "NSE:POWERGRID-EQ", "Power Grid Corporation", 1.28, Sector.POWER, 0.75, 0.62),
    StockConstituent("TATASTEEL", "NSE:TATASTEEL-EQ", "Tata Steel Ltd", 1.15, Sector.METALS, 1.35, 0.72),
    StockConstituent("WIPRO", "NSE:WIPRO-EQ", "Wipro Ltd", 1.05, Sector.IT, 0.78, 0.68),
    StockConstituent("INDUSINDBK", "NSE:INDUSINDBK-EQ", "IndusInd Bank Ltd", 0.95, Sector.BANKING, 1.30, 0.78),
    StockConstituent("TATAMOTORS", "NSE:TATAMOTORS-EQ", "Tata Motors Ltd", 0.88, Sector.AUTO, 1.45, 0.78),
]


# =============================================================================
# FINNIFTY (Nifty Financial Services) CONSTITUENTS (20 stocks)
# =============================================================================
FINNIFTY_CONSTITUENTS: List[StockConstituent] = [
    StockConstituent("HDFCBANK", "NSE:HDFCBANK-EQ", "HDFC Bank Ltd", 21.34, Sector.BANKING, 0.90, 0.92),
    StockConstituent("ICICIBANK", "NSE:ICICIBANK-EQ", "ICICI Bank Ltd", 14.83, Sector.BANKING, 1.00, 0.94),
    StockConstituent("SBIN", "NSE:SBIN-EQ", "State Bank of India", 13.64, Sector.BANKING, 1.15, 0.90),
    StockConstituent("BAJFINANCE", "NSE:BAJFINANCE-EQ", "Bajaj Finance Ltd", 8.83, Sector.NBFC, 1.20, 0.85),
    StockConstituent("KOTAKBANK", "NSE:KOTAKBANK-EQ", "Kotak Mahindra Bank Ltd", 6.25, Sector.BANKING, 0.85, 0.88),
    StockConstituent("AXISBANK", "NSE:AXISBANK-EQ", "Axis Bank Ltd", 5.84, Sector.BANKING, 1.10, 0.92),
    StockConstituent("BAJAJFINSV", "NSE:BAJAJFINSV-EQ", "Bajaj Finserv Ltd", 4.70, Sector.NBFC, 1.15, 0.82),
    StockConstituent("SBILIFE", "NSE:SBILIFE-EQ", "SBI Life Insurance", 3.07, Sector.INSURANCE, 0.95, 0.78),
    StockConstituent("SHRIRAMFIN", "NSE:SHRIRAMFIN-EQ", "Shriram Finance Ltd", 2.71, Sector.NBFC, 1.10, 0.75),
    StockConstituent("JIOFIN", "NSE:JIOFIN-EQ", "Jio Financial Services", 2.70, Sector.FINANCIALS, 1.25, 0.70),
    StockConstituent("HDFCLIFE", "NSE:HDFCLIFE-EQ", "HDFC Life Insurance", 2.39, Sector.INSURANCE, 0.90, 0.75),
    StockConstituent("MUTHOOTFIN", "NSE:MUTHOOTFIN-EQ", "Muthoot Finance Ltd", 2.27, Sector.NBFC, 1.05, 0.72),
    StockConstituent("CHOLAFIN", "NSE:CHOLAFIN-EQ", "Cholamandalam Investment", 2.16, Sector.NBFC, 1.15, 0.75),
    StockConstituent("PFC", "NSE:PFC-EQ", "Power Finance Corporation", 1.75, Sector.NBFC, 1.20, 0.68),
    StockConstituent("BSE", "NSE:BSE-EQ", "BSE Ltd", 1.60, Sector.FINANCIALS, 1.30, 0.65),
    StockConstituent("ICICIPRULI", "NSE:ICICIPRULI-EQ", "ICICI Prudential Life Insurance", 1.47, Sector.INSURANCE, 1.00, 0.72),
    StockConstituent("RECLTD", "NSE:RECLTD-EQ", "REC Ltd", 1.41, Sector.NBFC, 1.15, 0.65),
    StockConstituent("ICICIGI", "NSE:ICICIGI-EQ", "ICICI Lombard General Insurance", 1.39, Sector.INSURANCE, 0.85, 0.70),
    StockConstituent("SBICARD", "NSE:SBICARD-EQ", "SBI Cards and Payment Services", 1.21, Sector.FINANCIALS, 1.10, 0.72),
    StockConstituent("LICHSGFIN", "NSE:LICHSGFIN-EQ", "LIC Housing Finance", 0.43, Sector.NBFC, 1.20, 0.68),
]


# =============================================================================
# SECTOR WEIGHTS BY INDEX
# =============================================================================
NIFTY50_SECTOR_WEIGHTS: Dict[Sector, float] = {
    Sector.BANKING: 16.89,
    Sector.IT: 13.60,
    Sector.OIL_GAS: 11.41,
    Sector.FMCG: 9.36,
    Sector.NBFC: 6.48,
    Sector.AUTO: 9.93,
    Sector.PHARMA: 4.05,
    Sector.TELECOM: 5.96,
    Sector.CEMENT: 2.73,
    Sector.POWER: 3.23,
    Sector.METALS: 3.44,
    Sector.INFRA: 4.64,
    Sector.CONSUMER: 3.43,
    Sector.INSURANCE: 0.82,
    Sector.DIVERSIFIED: 0.72,
}

BANKNIFTY_SECTOR_WEIGHTS: Dict[Sector, float] = {
    Sector.BANKING: 100.0,  # Pure banking index
}

FINNIFTY_SECTOR_WEIGHTS: Dict[Sector, float] = {
    Sector.BANKING: 61.90,
    Sector.NBFC: 23.03,
    Sector.INSURANCE: 8.32,
    Sector.FINANCIALS: 6.75,
}


# =============================================================================
# INDEX DATA ACCESS FUNCTIONS
# =============================================================================
class IndexConstituentsManager:
    """Manager for index constituent data"""
    
    INDEX_MAP = {
        "NIFTY": NIFTY50_CONSTITUENTS,
        "NIFTY50": NIFTY50_CONSTITUENTS,
        "BANKNIFTY": BANKNIFTY_CONSTITUENTS,
        "BANKEX": BANKNIFTY_CONSTITUENTS,  # Alias
        "SENSEX": SENSEX_CONSTITUENTS,
        "FINNIFTY": FINNIFTY_CONSTITUENTS,
    }
    
    SECTOR_WEIGHT_MAP = {
        "NIFTY": NIFTY50_SECTOR_WEIGHTS,
        "NIFTY50": NIFTY50_SECTOR_WEIGHTS,
        "BANKNIFTY": BANKNIFTY_SECTOR_WEIGHTS,
        "SENSEX": NIFTY50_SECTOR_WEIGHTS,  # Similar structure
        "FINNIFTY": FINNIFTY_SECTOR_WEIGHTS,
    }
    
    @classmethod
    def get_constituents(cls, index_name: str) -> List[StockConstituent]:
        """Get all constituents for an index"""
        index_key = index_name.upper()
        if index_key not in cls.INDEX_MAP:
            logger.warning(f"Unknown index: {index_name}")
            return []
        return cls.INDEX_MAP[index_key]
    
    @classmethod
    def get_constituent_symbols(cls, index_name: str) -> List[str]:
        """Get list of Fyers symbols for an index"""
        constituents = cls.get_constituents(index_name)
        return [c.fyers_symbol for c in constituents]
    
    @classmethod
    def get_constituent_weights(cls, index_name: str) -> Dict[str, float]:
        """Get weight mapping {symbol: weight} for an index"""
        constituents = cls.get_constituents(index_name)
        return {c.fyers_symbol: c.weight for c in constituents}
    
    @classmethod
    def get_sector_weights(cls, index_name: str) -> Dict[Sector, float]:
        """Get sector weights for an index"""
        index_key = index_name.upper()
        return cls.SECTOR_WEIGHT_MAP.get(index_key, {})
    
    @classmethod
    def get_stocks_by_sector(cls, index_name: str) -> Dict[Sector, List[StockConstituent]]:
        """Group constituents by sector"""
        constituents = cls.get_constituents(index_name)
        sector_stocks: Dict[Sector, List[StockConstituent]] = {}
        
        for stock in constituents:
            if stock.sector not in sector_stocks:
                sector_stocks[stock.sector] = []
            sector_stocks[stock.sector].append(stock)
        
        return sector_stocks
    
    @classmethod
    def get_stock_info(cls, symbol: str, index_name: str = None) -> Optional[StockConstituent]:
        """Get stock info from any index or specific index"""
        # Normalize symbol
        if not symbol.startswith("NSE:"):
            symbol = f"NSE:{symbol}-EQ"
        
        if index_name:
            constituents = cls.get_constituents(index_name)
            for stock in constituents:
                if stock.fyers_symbol == symbol:
                    return stock
        else:
            # Search all indices
            for index_key in cls.INDEX_MAP:
                for stock in cls.INDEX_MAP[index_key]:
                    if stock.fyers_symbol == symbol:
                        return stock
        return None
    
    @classmethod
    def get_all_indices(cls) -> List[str]:
        """Get list of supported index names"""
        return ["NIFTY", "BANKNIFTY", "SENSEX", "FINNIFTY"]
    
    @classmethod
    def get_index_total_weight(cls, index_name: str) -> float:
        """Get total weight (should be ~100)"""
        constituents = cls.get_constituents(index_name)
        return sum(c.weight for c in constituents)
    
    @classmethod
    def normalize_weights(cls, index_name: str) -> Dict[str, float]:
        """Get normalized weights that sum to 1.0"""
        weights = cls.get_constituent_weights(index_name)
        total = sum(weights.values())
        if total > 0:
            return {k: v / total for k, v in weights.items()}
        return weights


# Global instance
index_manager = IndexConstituentsManager()
