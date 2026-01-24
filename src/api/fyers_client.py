"""
Fyers API Integration Module
Handles authentication, data fetching, and order placement
"""
from fyers_apiv3 import fyersModel
# from fyers_apiv3.FyersWebsocket import data_ws

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime, timedelta
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class FyersClient:
    """Wrapper for Fyers API with additional functionality"""
    
    def __init__(self):
        self.client_id = settings.fyers_client_id
        self.secret_key = settings.fyers_secret_key
        self.redirect_uri = settings.fyers_redirect_uri
        self.access_token = settings.fyers_access_token
        self.fyers = None
        
        if self.access_token:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Fyers client with access token"""
        import tempfile
        import os
        # Use temp directory for logs to avoid permission issues
        log_path = os.path.join(tempfile.gettempdir(), "fyers_logs")
        os.makedirs(log_path, exist_ok=True)
        
        self.fyers = fyersModel.FyersModel(
            client_id=self.client_id,
            token=self.access_token,
            log_path=log_path
        )
        logger.info("Fyers client initialized successfully")
    
    def refresh_settings(self):
        """Refresh settings from environment (useful when ngrok URL changes)"""
        from config.settings import settings
        self.client_id = settings.fyers_client_id
        self.secret_key = settings.fyers_secret_key
        self.redirect_uri = settings.fyers_redirect_uri
        self.access_token = settings.fyers_access_token
        logger.info(f"Settings refreshed. New redirect URI: {self.redirect_uri}")
    
    def generate_auth_url(self) -> str:
        """Generate authentication URL for user login"""
        session = fyersModel.SessionModel(
            client_id=self.client_id,
            secret_key=self.secret_key,
            redirect_uri=self.redirect_uri,
            response_type="code",
            grant_type="authorization_code"
        )
        return session.generate_authcode()
    
    def set_access_token(self, auth_code: str) -> bool:
        """
        Set access token using authorization code
        
        Args:
            auth_code: Authorization code from callback
            
        Returns:
            bool: Success status
        """
        try:
            session = fyersModel.SessionModel(
                client_id=self.client_id,
                secret_key=self.secret_key,
                redirect_uri=self.redirect_uri,
                response_type="code",
                grant_type="authorization_code"
            )
            session.set_token(auth_code)
            response = session.generate_token()
            
            if response["code"] == 200:
                self.access_token = response["access_token"]
                self._initialize_client()
                logger.info("Access token set successfully")
                return True
            else:
                logger.error(f"Failed to generate token: {response}")
                return False
        except Exception as e:
            logger.error(f"Error setting access token: {e}")
            return False
    
    def get_profile(self) -> Dict:
        """Get user profile information"""
        if not self.fyers:
            raise Exception("Client not initialized. Please authenticate first.")
        
        response = self.fyers.get_profile()
        return response
    
    def get_quotes(self, symbols: List[str]) -> Dict:
        """
        Get current quotes for given symbols
        
        Args:
            symbols: List of symbols (e.g., ["NSE:SBIN-EQ", "NSE:NIFTY23JAN17000CE"])
            
        Returns:
            Dict with quote data
        """
        if not self.fyers:
            raise Exception("Client not initialized")
        
        data = {"symbols": ",".join(symbols)}
        response = self.fyers.quotes(data)
        return response
    
    def get_historical_data(
        self,
        symbol: str,
        resolution: str = "D",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        cont_flag: str = "1"
    ) -> pd.DataFrame:
        """
        Get historical candle data
        
        Args:
            symbol: Trading symbol
            resolution: Candle resolution (1, 3, 5, 15, 30, 60, 120, D, W, M)
            date_from: Start date
            date_to: End date
            cont_flag: Continuation flag for futures
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.fyers:
            raise Exception("Client not initialized")
        
        if date_to is None:
            date_to = datetime.now()
        if date_from is None:
            date_from = date_to - timedelta(days=365)
        
        # Fyers API v3 requires date_format=0 for epoch timestamps
        # or date_format=1 for YYYY-MM-DD strings
        data = {
            "symbol": symbol,
            "resolution": resolution,
            "date_format": "0",  # 0 = Unix epoch timestamps
            "range_from": str(int(date_from.timestamp())),
            "range_to": str(int(date_to.timestamp())),
            "cont_flag": cont_flag
        }
        
        logger.info(f"📊 Fetching historical data: {symbol}, {resolution}, from {date_from} to {date_to}")
        
        response = self.fyers.history(data)
        
        if response.get("code") == 200 or response.get("s") == "ok":
            candles = response["candles"]
            df = pd.DataFrame(
                candles,
                columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
            df.set_index("timestamp", inplace=True)
            return df
        else:
            logger.error(f"Failed to fetch historical data: {response}")
            return pd.DataFrame()
    
    def get_option_chain(
        self,
        symbol: str,
        strike_count: int = 10,
        expiry_date: Optional[str] = None
    ) -> Dict:
        """
        Get option chain data
        
        Args:
            symbol: Underlying symbol (e.g., "NSE:NIFTY")
            strike_count: Number of strikes above and below ATM
            expiry_date: Expiry date in format "YYMMDD" (e.g., "230120")
            
        Returns:
            Dict with option chain data
        """
        if not self.fyers:
            raise Exception("Client not initialized")
        
        data = {
            "symbol": symbol,
            "strikecount": strike_count
        }
        
        if expiry_date:
            data["timestamp"] = expiry_date
        
        response = self.fyers.optionchain(data)
        return response
    
    def place_order(
        self,
        symbol: str,
        qty: int,
        side: int,  # 1 for Buy, -1 for Sell
        order_type: int = 2,  # 1=Limit, 2=Market, 3=SL, 4=SL-M
        product_type: str = "INTRADAY",  # INTRADAY, CNC, MARGIN
        limit_price: float = 0,
        stop_price: float = 0,
        validity: str = "DAY"
    ) -> Dict:
        """
        Place an order
        
        Args:
            symbol: Trading symbol
            qty: Quantity
            side: 1 for Buy, -1 for Sell
            order_type: Order type (1=Limit, 2=Market, 3=SL, 4=SL-M)
            product_type: Product type (INTRADAY, CNC, MARGIN)
            limit_price: Limit price (for limit orders)
            stop_price: Stop price (for SL orders)
            validity: Order validity (DAY, IOC)
            
        Returns:
            Dict with order response
        """
        if not self.fyers:
            raise Exception("Client not initialized")
        
        data = {
            "symbol": symbol,
            "qty": qty,
            "type": order_type,
            "side": side,
            "productType": product_type,
            "limitPrice": limit_price,
            "stopPrice": stop_price,
            "validity": validity,
            "disclosedQty": 0,
            "offlineOrder": False
        }
        
        response = self.fyers.place_order(data)
        logger.info(f"Order placed: {response}")
        return response
    
    def get_positions(self) -> Dict:
        """Get current positions"""
        if not self.fyers:
            raise Exception("Client not initialized")
        
        response = self.fyers.positions()
        return response
    
    def get_orders(self) -> Dict:
        """Get order book"""
        if not self.fyers:
            raise Exception("Client not initialized")
        
        response = self.fyers.orderbook()
        return response
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order"""
        if not self.fyers:
            raise Exception("Client not initialized")
        
        data = {"id": order_id}
        response = self.fyers.cancel_order(data)
        return response
    
    def get_funds(self) -> Dict:
        """Get available funds"""
        if not self.fyers:
            raise Exception("Client not initialized")
        
        response = self.fyers.funds()
        return response
    
    def get_historical_vix(self, days: int = 252) -> pd.DataFrame:
        """
        Fetch historical India VIX data for percentile calculation
        
        Args:
            days: Number of trading days of history (default: 252 = 1 year)
            
        Returns:
            DataFrame with VIX OHLCV data indexed by timestamp
        """
        if not self.fyers:
            raise Exception("Client not initialized")
        
        date_to = datetime.now()
        # Add buffer days for holidays/weekends
        date_from = date_to - timedelta(days=int(days * 1.5))
        
        try:
            df = self.get_historical_data(
                symbol="NSE:INDIAVIX-INDEX",
                resolution="D",
                date_from=date_from,
                date_to=date_to
            )
            
            if df is not None and not df.empty:
                # Return only the requested number of trading days
                return df.tail(days)
            else:
                logger.warning("No historical VIX data received")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error fetching historical VIX: {e}")
            return pd.DataFrame()


# Global client instance
fyers_client = FyersClient()
