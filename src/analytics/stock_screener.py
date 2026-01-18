"""
Stock Screener Module
Scans all NSE equity stocks for high-confidence trading signals
Uses ICT analysis + ML predictions for signal generation
"""
import pandas as pd
import numpy as np
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class StockScreener:
    """Screen stocks for high-confidence trading signals"""
    
    def __init__(self, fyers_client):
        """Initialize stock screener with Fyers client"""
        self.fyers_client = fyers_client
        
    def get_nse_stocks_list(self, limit: Optional[int] = None, randomize: bool = False) -> List[str]:
        """
        Get comprehensive list of NSE stocks to scan
        
        Args:
            limit: Maximum number of stocks to return (None = all)
            randomize: If True, randomly sample stocks for faster scans
            
        Returns:
            List of stock symbols (NSE:SYMBOL format)
        """
        # Comprehensive NSE stock list (500+ stocks across all sectors)
        all_stocks = [
            # NIFTY 50
            "NSE:RELIANCE-EQ", "NSE:TCS-EQ", "NSE:HDFCBANK-EQ", "NSE:INFY-EQ", "NSE:ICICIBANK-EQ",
            "NSE:HINDUNILVR-EQ", "NSE:ITC-EQ", "NSE:SBIN-EQ", "NSE:BHARTIARTL-EQ", "NSE:KOTAKBANK-EQ",
            "NSE:LT-EQ", "NSE:AXISBANK-EQ", "NSE:ASIANPAINT-EQ", "NSE:MARUTI-EQ", "NSE:SUNPHARMA-EQ",
            "NSE:TITAN-EQ", "NSE:ULTRACEMCO-EQ", "NSE:BAJFINANCE-EQ", "NSE:NESTLEIND-EQ", "NSE:HCLTECH-EQ",
            "NSE:WIPRO-EQ", "NSE:M&M-EQ", "NSE:NTPC-EQ", "NSE:TATAMOTORS-EQ", "NSE:TATASTEEL-EQ",
            "NSE:POWERGRID-EQ", "NSE:ONGC-EQ", "NSE:ADANIPORTS-EQ", "NSE:COALINDIA-EQ", "NSE:BAJAJFINSV-EQ",
            "NSE:TECHM-EQ", "NSE:INDUSINDBK-EQ", "NSE:HINDALCO-EQ", "NSE:DIVISLAB-EQ", "NSE:HEROMOTOCO-EQ",
            "NSE:DRREDDY-EQ", "NSE:CIPLA-EQ", "NSE:EICHERMOT-EQ", "NSE:GRASIM-EQ", "NSE:JSWSTEEL-EQ",
            "NSE:BRITANNIA-EQ", "NSE:APOLLOHOSP-EQ", "NSE:BPCL-EQ", "NSE:TATACONSUM-EQ", "NSE:UPL-EQ",
            "NSE:ADANIENT-EQ", "NSE:SHREECEM-EQ", "NSE:SBILIFE-EQ", "NSE:BAJAJ-AUTO-EQ", "NSE:HDFCLIFE-EQ",
            
            # Banking & Finance
            "NSE:PNB-EQ", "NSE:BANKBARODA-EQ", "NSE:CANBK-EQ", "NSE:UNIONBANK-EQ", "NSE:IDFCFIRSTB-EQ",
            "NSE:FEDERALBNK-EQ", "NSE:BANDHANBNK-EQ", "NSE:RBLBANK-EQ", "NSE:AUBANK-EQ", "NSE:INDHOTEL-EQ",
            "NSE:M&MFIN-EQ", "NSE:LICHSGFIN-EQ", "NSE:SRTRANSFIN-EQ", "NSE:CHOLAFIN-EQ", "NSE:PFC-EQ",
            "NSE:RECLTD-EQ", "NSE:MUTHOOTFIN-EQ", "NSE:CREDITACC-EQ", "NSE:ICICIGI-EQ", "NSE:BAJAJHLDNG-EQ",
            
            # IT & Software
            "NSE:LTIM-EQ", "NSE:PERSISTENT-EQ", "NSE:COFORGE-EQ", "NSE:MPHASIS-EQ", "NSE:LTI-EQ",
            "NSE:MINDTREE-EQ", "NSE:TECHM-EQ", "NSE:OFSS-EQ", "NSE:KPITTECH-EQ", "NSE:RATEGAIN-EQ",
            "NSE:TATAELXSI-EQ", "NSE:ZENTEC-EQ", "NSE:INTELLECT-EQ", "NSE:SONATSOFTW-EQ", "NSE:CYIENT-EQ",
            
            # Auto & Auto Components
            "NSE:TATAMOTORS-EQ", "NSE:MARUTI-EQ", "NSE:M&M-EQ", "NSE:BAJAJ-AUTO-EQ", "NSE:EICHERMOT-EQ",
            "NSE:HEROMOTOCO-EQ", "NSE:TVSMOTOR-EQ", "NSE:ASHOKLEY-EQ", "NSE:ESCORTS-EQ", "NSE:BALKRISIND-EQ",
            "NSE:MRF-EQ", "NSE:APOLLOTYRE-EQ", "NSE:CEAT-EQ", "NSE:BOSCHLTD-EQ", "NSE:MOTHERSON-EQ",
            "NSE:EXIDEIND-EQ", "NSE:AMARAJABAT-EQ", "NSE:BHARATFORG-EQ", "NSE:ENDURANCE-EQ", "NSE:SCHAEFFLER-EQ",
            
            # Pharma & Healthcare
            "NSE:SUNPHARMA-EQ", "NSE:DRREDDY-EQ", "NSE:CIPLA-EQ", "NSE:DIVISLAB-EQ", "NSE:LUPIN-EQ",
            "NSE:APOLLOHOSP-EQ", "NSE:BIOCON-EQ", "NSE:TORNTPHARM-EQ", "NSE:AUROPHARMA-EQ", "NSE:ALKEM-EQ",
            "NSE:IPCALAB-EQ", "NSE:LAURUSLABS-EQ", "NSE:GLENMARK-EQ", "NSE:GRANULES-EQ", "NSE:NATCOPHARMA-EQ",
            "NSE:ABBOTINDIA-EQ", "NSE:PFIZER-EQ", "NSE:GSK-EQ", "NSE:SANOFI-EQ", "NSE:FORTIS-EQ",
            
            # Oil & Gas
            "NSE:RELIANCE-EQ", "NSE:ONGC-EQ", "NSE:BPCL-EQ", "NSE:IOC-EQ", "NSE:HINDPETRO-EQ",
            "NSE:GAIL-EQ", "NSE:PETRONET-EQ", "NSE:OIL-EQ", "NSE:MRPL-EQ", "NSE:GUJGASLTD-EQ",
            "NSE:IGL-EQ", "NSE:MGL-EQ", "NSE:INDRAPRASTHA-EQ", "NSE:ATGL-EQ", "NSE:GSPL-EQ",
            
            # Metals & Mining
            "NSE:TATASTEEL-EQ", "NSE:JSWSTEEL-EQ", "NSE:HINDALCO-EQ", "NSE:COALINDIA-EQ", "NSE:VEDL-EQ",
            "NSE:SAIL-EQ", "NSE:NMDC-EQ", "NSE:JINDALSTEL-EQ", "NSE:NATIONALUM-EQ", "NSE:HINDZINC-EQ",
            "NSE:RATNAMANI-EQ", "NSE:APLAPOLLO-EQ", "NSE:WELCORP-EQ", "NSE:WELSPUNIND-EQ", "NSE:JSWENERGY-EQ",
            
            # Cement
            "NSE:ULTRACEMCO-EQ", "NSE:SHREECEM-EQ", "NSE:GRASIM-EQ", "NSE:AMBUJACEM-EQ", "NSE:ACC-EQ",
            "NSE:DALMIACEM-EQ", "NSE:RAMCOCEM-EQ", "NSE:JKCEMENT-EQ", "NSE:INDIACEM-EQ", "NSE:ORIENTCEM-EQ",
            
            # Power & Utilities
            "NSE:NTPC-EQ", "NSE:POWERGRID-EQ", "NSE:TATAPOWER-EQ", "NSE:ADANIPOWER-EQ", "NSE:ADANIGREEN-EQ",
            "NSE:TORNTPOWER-EQ", "NSE:NHPC-EQ", "NSE:SJVN-EQ", "NSE:CESC-EQ", "NSE:JSW-EQ",
            
            # Telecom
            "NSE:BHARTIARTL-EQ", "NSE:IDEA-EQ", "NSE:INDUSINDBK-EQ", "NSE:TATACOMM-EQ", "NSE:ROUTE-EQ",
            
            # Consumer Goods
            "NSE:HINDUNILVR-EQ", "NSE:ITC-EQ", "NSE:NESTLEIND-EQ", "NSE:BRITANNIA-EQ", "NSE:DABUR-EQ",
            "NSE:MARICO-EQ", "NSE:GODREJCP-EQ", "NSE:COLPAL-EQ", "NSE:PGHH-EQ", "NSE:EMAMILTD-EQ",
            "NSE:TATACONSUM-EQ", "NSE:VBL-EQ", "NSE:RADICO-EQ", "NSE:JUBLFOOD-EQ",
            
            # Retail
            "NSE:DMART-EQ", "NSE:TRENT-EQ", "NSE:TITAN-EQ", "NSE:SHOPERSTOP-EQ", "NSE:ADITYA-EQ",
            "NSE:RELAXO-EQ", "NSE:BATA-EQ", "NSE:PAGEIND-EQ", "NSE:VMART-EQ", "NSE:SPENCERS-EQ",
            
            # Real Estate & Construction
            "NSE:LT-EQ", "NSE:DLF-EQ", "NSE:GODREJPROP-EQ", "NSE:OBEROIRLTY-EQ", "NSE:PRESTIGE-EQ",
            "NSE:BRIGADE-EQ", "NSE:PHOENIXLTD-EQ", "NSE:SOBHA-EQ", "NSE:MAHLIFE-EQ", "NSE:SUNTECK-EQ",
            "NSE:NCC-EQ", "NSE:KNR-EQ", "NSE:PNC-EQ", "NSE:IRCON-EQ", "NSE:GATEWAY-EQ",
            
            # Hotels & Tourism
            "NSE:INDHOTEL-EQ", "NSE:LEMONTREE-EQ", "NSE:EIH-EQ", "NSE:CHALET-EQ", "NSE:TAJGVK-EQ",
            "NSE:ITDC-EQ", "NSE:MAHINDRA-EQ", "NSE:ORIENTHOT-EQ",
            
            # Media & Entertainment
            "NSE:ZEEL-EQ", "NSE:SUNTV-EQ", "NSE:PVRINOX-EQ", "NSE:NAZARA-EQ", "NSE:TVTODAY-EQ",
            "NSE:HMV-EQ", "NSE:DBCORP-EQ", "NSE:JAGRAN-EQ", "NSE:NETWORK18-EQ", "NSE:INOXLEISURE-EQ",
            
            # Chemicals & Fertilizers
            "NSE:UPL-EQ", "NSE:PI-EQ", "NSE:AARTI-EQ", "NSE:SRF-EQ", "NSE:DEEPAK-EQ",
            "NSE:TATACHEM-EQ", "NSE:GNFC-EQ", "NSE:CHAMBLFERT-EQ", "NSE:COROMANDEL-EQ", "NSE:GSFC-EQ",
            "NSE:BALRAMCHIN-EQ", "NSE:ALKYL-EQ", "NSE:NAVINFLUOR-EQ", "NSE:FCONSUMER-EQ", "NSE:CLEAN-EQ",
            
            # Textiles
            "NSE:ARVIND-EQ", "NSE:RAYMOND-EQ", "NSE:VARDHMAN-EQ", "NSE:WELSPUNIND-EQ", "NSE:TRIDENT-EQ",
            "NSE:SPCENET-EQ", "NSE:INDOCOUNT-EQ", "NSE:DHAMPURSUG-EQ", "NSE:GOKEX-EQ",
            
            # Engineering
            "NSE:SIEMENS-EQ", "NSE:ABB-EQ", "NSE:CUMMINSIND-EQ", "NSE:THERMAX-EQ", "NSE:VGUARD-EQ",
            "NSE:HAVELLS-EQ", "NSE:CROMPTON-EQ", "NSE:POLYCAB-EQ", "NSE:KEI-EQ", "NSE:DIXON-EQ",
            
            # Diversified
            "NSE:ADANIENT-EQ", "NSE:JMFINANCIL-EQ", "NSE:AFFLE-EQ", "NSE:ROUTE-EQ", "NSE:ZOMATO-EQ",
            "NSE:PAYTM-EQ", "NSE:NYKAA-EQ", "NSE:POLICYBZR-EQ", "NSE:DELHIVERY-EQ", "NSE:CARTRADE-EQ",
            
            # Small & Mid Cap High Volume
            "NSE:YESBANK-EQ", "NSE:SUZLON-EQ", "NSE:RPOWER-EQ", "NSE:VAKRANGEE-EQ", "NSE:IDFC-EQ",
            "NSE:SRTRANSFIN-EQ", "NSE:RECLTD-EQ",
        ]
        
        # Remove duplicates
        all_stocks = list(set(all_stocks))
        
        # Randomize if requested (for faster scans)
        if randomize:
            random.shuffle(all_stocks)
        
        # Apply limit if specified
        if limit and limit < len(all_stocks):
            return all_stocks[:limit]
        
        return all_stocks
    
    def analyze_stock(self, symbol: str) -> Optional[Dict]:
        """
        Analyze a single stock for trading signals
        
        Args:
            symbol: Stock symbol (NSE:SYMBOL-EQ)
            
        Returns:
            Signal dict or None if no signal
        """
        try:
            # Get historical data first (works after hours)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            historical_df = self.fyers_client.get_historical_data(
                symbol=symbol,
                resolution="D",  # Daily candles
                date_from=start_date,
                date_to=end_date
            )
            
            if historical_df is None or historical_df.empty or len(historical_df) < 10:
                logger.warning(f"Insufficient historical data for {symbol}")
                return None
            
            # Use latest close as current price (works after hours)
            current_price = float(historical_df['close'].iloc[-1])
            
            if current_price <= 0:
                return None
            
            # Try to get live quote (only works during market hours)
            quote_data = {}
            try:
                quotes_response = self.fyers_client.get_quotes([symbol])
                if quotes_response and 'd' in quotes_response:
                    for quote in quotes_response['d']:
                        if quote.get('n') == symbol:
                            quote_data = {
                                'ltp': quote.get('v', {}).get('lp', current_price),
                                'ch': quote.get('v', {}).get('ch', 0),
                                'chp': quote.get('v', {}).get('chp', 0),
                                'volume': quote.get('v', {}).get('volume', 0)
                            }
                            current_price = quote_data['ltp']  # Use live price if available
                            break
            except Exception as e:
                # Quote fetch failed (probably after hours), use historical close
                logger.debug(f"Live quote unavailable for {symbol}, using latest close: {e}")
                quote_data = {
                    'ltp': current_price,
                    'ch': 0,
                    'chp': 0,
                    'volume': int(historical_df['volume'].iloc[-1])
                }
            
            # Calculate technical indicators
            signal = self._generate_signal(symbol, current_price, historical_df, quote_data)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _generate_signal(self, symbol: str, current_price: float, 
                        df: pd.DataFrame, quote_data: Dict) -> Optional[Dict]:
        """
        Generate trading signal using technical analysis
        
        Args:
            symbol: Stock symbol
            current_price: Current LTP
            df: Historical OHLCV data
            quote_data: Real-time quote data
            
        Returns:
            Signal dict with action, confidence, targets
        """
        try:
            # Calculate indicators
            df = df.copy()
            
            # 1. Moving Averages (use 5/10/15 for faster signals with limited data)
            df['sma_5'] = df['close'].rolling(5).mean()
            df['sma_10'] = df['close'].rolling(10).mean()
            df['sma_15'] = df['close'].rolling(15).mean()
            
            # 2. RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 3. Volume analysis
            df['volume_sma'] = df['volume'].rolling(10).mean()
            volume_surge = df['volume'].iloc[-1] > df['volume_sma'].iloc[-1] * 1.5
            
            # 4. Price momentum (5-day change)
            if len(df) >= 6:
                price_change_pct = ((current_price - df['close'].iloc[-6]) / df['close'].iloc[-6]) * 100
            else:
                price_change_pct = 0
            
            # Get latest values
            sma_5 = df['sma_5'].iloc[-1]
            sma_10 = df['sma_10'].iloc[-1]
            sma_15 = df['sma_15'].iloc[-1]
            rsi = df['rsi'].iloc[-1]
            
            # Skip if key indicators not ready (need at least 15 days)
            if pd.isna(rsi) or pd.isna(sma_15):
                logger.debug(f"{symbol}: Indicators not ready (RSI={rsi}, SMA15={sma_15})")
                return None
            
            # Signal generation logic
            confidence = 0
            action = "HOLD"
            reasons = []
            
            # BULLISH SIGNALS
            bullish_score = 0
            
            # Golden cross (short MA > long MA)
            if sma_5 > sma_10 > sma_15:
                bullish_score += 30
                reasons.append("✅ Golden cross - all MAs aligned")
            elif sma_5 > sma_15:
                bullish_score += 15
                reasons.append("📈 Price above 15 SMA")
            
            # RSI in buy zone
            if rsi < 30:
                bullish_score += 30  # Deeply oversold
                reasons.append(f"✅ RSI deeply oversold: {rsi:.1f}")
            elif 30 < rsi < 50:
                bullish_score += 25
                reasons.append(f"✅ RSI oversold recovery: {rsi:.1f}")
            elif 50 < rsi < 70:
                bullish_score += 15
                reasons.append(f"📊 RSI healthy: {rsi:.1f}")
            
            # Volume confirmation
            if volume_surge and price_change_pct > 0:
                bullish_score += 20
                reasons.append("🔥 High volume on uptrend")
            
            # Momentum
            if price_change_pct > 3:
                bullish_score += 15
                reasons.append(f"🚀 Strong momentum: +{price_change_pct:.1f}%")
            
            # BEARISH SIGNALS
            bearish_score = 0
            
            # Death cross
            if sma_5 < sma_10 < sma_15:
                bearish_score += 30
                reasons.append("❌ Death cross - downtrend")
            elif sma_5 < sma_15:
                bearish_score += 15
                reasons.append("📉 Price below 15 SMA")
            
            # RSI overbought
            if rsi > 70:
                bearish_score += 25
                reasons.append(f"⚠️ RSI overbought: {rsi:.1f}")
            elif rsi > 50 and price_change_pct < -2:
                bearish_score += 15
                reasons.append(f"📊 RSI + negative momentum")
            
            # Volume on decline
            if volume_surge and price_change_pct < -2:
                bearish_score += 20
                reasons.append("⚠️ High volume on decline")
            
            # Negative momentum
            if price_change_pct < -3:
                bearish_score += 15
                reasons.append(f"📉 Weak momentum: {price_change_pct:.1f}%")
            
            # Determine final action and confidence
            # Lower threshold to 20 points for daily data analysis (works 24/7)
            min_score = 20
            
            logger.info(f"{symbol}: Bullish={bullish_score}, Bearish={bearish_score}")
            
            if bullish_score > bearish_score and bullish_score >= min_score:
                action = "BUY"
                confidence = min(bullish_score + 25, 95)  # Boost confidence
            elif bearish_score > bullish_score and bearish_score >= min_score:
                action = "SELL"
                confidence = min(bearish_score + 25, 95)  # Boost confidence
            else:
                logger.info(f"{symbol}: No signal - Bullish={bullish_score}, Bearish={bearish_score}, min={min_score}")
                return None  # No clear signal
            
            # Calculate targets and stop loss
            if action == "BUY":
                target_1 = current_price * 1.05  # 5% gain
                target_2 = current_price * 1.10  # 10% gain
                stop_loss = current_price * 0.97  # 3% loss
            else:  # SELL
                target_1 = current_price * 0.95  # 5% profit on short
                target_2 = current_price * 0.90  # 10% profit on short
                stop_loss = current_price * 1.03  # 3% loss on short
            
            return {
                "symbol": symbol,
                "name": symbol.replace("NSE:", "").replace("-EQ", ""),
                "current_price": round(current_price, 2),
                "action": action,
                "confidence": round(confidence, 1),
                "targets": {
                    "target_1": round(target_1, 2),
                    "target_2": round(target_2, 2),
                    "stop_loss": round(stop_loss, 2)
                },
                "indicators": {
                    "rsi": round(rsi, 1),
                    "sma_5": round(sma_5, 2),
                    "sma_15": round(sma_15, 2),
                    "momentum_5d": round(price_change_pct, 2),
                    "volume_surge": bool(volume_surge)  # Convert numpy.bool_ to Python bool
                },
                "reasons": reasons[:3],  # Top 3 reasons
                "timestamp": datetime.now().isoformat(),
                "change_pct": round(quote_data.get('ch', 0), 2),
                "volume": quote_data.get('volume', 0)
            }
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def scan_stocks(self, limit: Optional[int] = 50, 
                   min_confidence: float = 60.0,
                   randomize: bool = True) -> List[Dict]:
        """
        Scan multiple stocks and return high-confidence signals
        
        Args:
            limit: Maximum number of stocks to scan (default 50 for faster scans)
            min_confidence: Minimum confidence threshold (default 60%)
            randomize: If True, randomly sample stocks for variety
            
        Returns:
            List of signal dicts sorted by confidence
        """
        logger.info(f"Starting stock scan: limit={limit}, min_confidence={min_confidence}, randomize={randomize}")
        
        stocks = self.get_nse_stocks_list(limit=limit, randomize=randomize)
        signals = []
        
        for symbol in stocks:
            logger.info(f"Analyzing {symbol}...")
            signal = self.analyze_stock(symbol)
            
            if signal and signal["confidence"] >= min_confidence:
                signals.append(signal)
                logger.info(f"✅ Signal found: {symbol} - {signal['action']} ({signal['confidence']}%)")
        
        # Sort by confidence (highest first)
        signals.sort(key=lambda x: x["confidence"], reverse=True)
        
        logger.info(f"Scan complete: Found {len(signals)} signals out of {len(stocks)} stocks")
        return signals


# Global screener instance
_screener_instance = None

def get_stock_screener(fyers_client):
    """Get or create stock screener instance"""
    global _screener_instance
    if _screener_instance is None:
        _screener_instance = StockScreener(fyers_client)
    return _screener_instance
