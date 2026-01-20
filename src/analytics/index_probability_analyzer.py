"""
Index Probability Analyzer
Comprehensive probability-based analysis for NIFTY, BANKNIFTY, SENSEX, and FINNIFTY

This module implements:
1. Weighted stock-level analysis using market-cap weights
2. Probability-weighted signals (not binary)
3. Sector-level aggregation
4. Correlation filtering
5. Regime detection (trend/range/volatile)
6. Expected index move calculation

Formula: Index Move = Σ(wᵢ × Pᵢ × Δpᵢ)
Where:
    wᵢ = index weight of stock i (normalized)
    Pᵢ = probability score (0-1) from analysis
    Δpᵢ = expected % move of stock i
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.analytics.index_constituents import (
    IndexConstituentsManager, 
    StockConstituent, 
    Sector,
    index_manager
)

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classification"""
    STRONG_TREND_UP = "Strong Uptrend"
    WEAK_TREND_UP = "Weak Uptrend"
    RANGE_BOUND = "Range Bound"
    WEAK_TREND_DOWN = "Weak Downtrend"
    STRONG_TREND_DOWN = "Strong Downtrend"
    HIGH_VOLATILITY = "High Volatility"


class SignalType(Enum):
    """Signal classification"""
    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    WEAK_BUY = "Weak Buy"
    NEUTRAL = "Neutral"
    WEAK_SELL = "Weak Sell"
    SELL = "Sell"
    STRONG_SELL = "Strong Sell"


@dataclass
class StockSignal:
    """Signal data for a single stock"""
    symbol: str
    name: str
    weight: float                    # Index weight (normalized 0-1)
    sector: Sector
    
    # Price data
    current_price: float
    price_change_pct: float          # Daily change %
    
    # Signal data
    signal_type: SignalType
    probability: float               # 0-1 probability score
    expected_move_pct: float         # Expected % move
    weighted_contribution: float     # weight × probability × expected_move
    
    # Indicators
    rsi: float
    trend_direction: str             # "up", "down", "neutral"
    volume_surge: bool
    vwap_position: str               # "above", "below", "at"
    ema_alignment: str               # "bullish", "bearish", "mixed"
    
    # Correlation and confidence
    correlation_with_index: float    # Rolling correlation
    confidence_score: float          # Overall confidence 0-100
    
    # Analysis reasons
    bullish_factors: List[str] = field(default_factory=list)
    bearish_factors: List[str] = field(default_factory=list)


@dataclass
class SectorAnalysis:
    """Analysis for a sector"""
    sector: Sector
    sector_weight: float             # Total weight of sector in index
    stock_count: int
    
    # Aggregated metrics
    expected_sector_move: float      # Weighted expected move for sector
    avg_probability: float
    bullish_stock_count: int
    bearish_stock_count: int
    neutral_stock_count: int
    
    # Sector signal
    sector_signal: SignalType
    sector_confidence: float
    
    # Individual stocks
    stocks: List[StockSignal] = field(default_factory=list)


@dataclass
class RegimeAnalysis:
    """Market regime analysis"""
    regime: MarketRegime
    adx_value: float                 # Average Directional Index
    atr_percentile: float            # ATR relative to historical
    volatility_level: str            # "low", "normal", "high", "extreme"
    trend_strength: float            # 0-100
    
    # Adjustments based on regime
    probability_multiplier: float    # Adjust signal probability
    move_size_multiplier: float      # Adjust expected move size


@dataclass
class IndexPrediction:
    """Complete index prediction"""
    index_name: str
    timestamp: datetime
    
    # Index level data
    current_level: float
    regime: RegimeAnalysis
    
    # Predicted move
    expected_move_pct: float         # Probability-weighted expected move
    expected_direction: str          # "BULLISH", "BEARISH", "NEUTRAL"
    prediction_confidence: float     # 0-100
    
    # Probability distribution
    prob_up: float                   # Probability index goes up
    prob_down: float                 # Probability index goes down
    prob_neutral: float              # Probability index stays flat
    
    # Component analysis
    total_stocks_analyzed: int
    bullish_stocks: int
    bearish_stocks: int
    neutral_stocks: int
    
    # Sector breakdown
    sector_analysis: Dict[str, SectorAnalysis] = field(default_factory=dict)
    
    # Top movers (most impact on index)
    top_bullish_contributors: List[StockSignal] = field(default_factory=list)
    top_bearish_contributors: List[StockSignal] = field(default_factory=list)
    
    # Raw stock signals
    stock_signals: List[StockSignal] = field(default_factory=list)


class IndexProbabilityAnalyzer:
    """
    Comprehensive probability-based index analyzer
    
    Uses institutional-grade methodology:
    1. Free-float market-cap weighting
    2. Probability-weighted signals
    3. Sector aggregation
    4. Correlation filtering
    5. Regime detection
    """
    
    def __init__(self, fyers_client):
        self.fyers_client = fyers_client
        
        # Configuration
        self.min_correlation = 0.3       # Minimum correlation to include stock
        self.correlation_window = 30     # Days for rolling correlation
        self.volatility_window = 20      # Days for ATR calculation
        self.adx_period = 14             # ADX calculation period
        
        # Expected move caps (realistic)
        self.max_daily_move = 5.0        # Max expected daily move %
        self.default_move_bullish = 1.5  # Default expected up move %
        self.default_move_bearish = -1.5 # Default expected down move %
        
        # Regime thresholds
        self.adx_strong_trend = 25
        self.adx_weak_trend = 15
        self.volatility_high_percentile = 80
        
    def analyze_index(
        self,
        index_name: str,
        include_correlation_filter: bool = True,
        parallel: bool = True
    ) -> IndexPrediction:
        """
        Perform comprehensive probability analysis for an index
        
        Args:
            index_name: NIFTY, BANKNIFTY, SENSEX, or FINNIFTY
            include_correlation_filter: Whether to filter by correlation
            parallel: Whether to analyze stocks in parallel
            
        Returns:
            IndexPrediction with complete analysis
        """
        logger.info(f"🎯 Starting probability analysis for {index_name}")
        start_time = datetime.now()
        
        # Get constituents
        constituents = index_manager.get_constituents(index_name)
        if not constituents:
            raise ValueError(f"Unknown index: {index_name}")
        
        # Get normalized weights (sum to 1.0)
        normalized_weights = index_manager.normalize_weights(index_name)
        
        # Analyze regime first (using index data if available)
        regime = self._analyze_regime(index_name)
        logger.info(f"📊 Market Regime: {regime.regime.value}")
        
        # Analyze all stocks
        stock_signals = self._analyze_all_stocks(
            constituents, 
            normalized_weights,
            regime,
            parallel
        )
        
        # Apply correlation filter if enabled
        if include_correlation_filter:
            stock_signals = self._apply_correlation_filter(stock_signals)
        
        # Aggregate by sector
        sector_analysis = self._aggregate_by_sector(stock_signals, index_name)
        
        # Calculate final index prediction
        prediction = self._calculate_index_prediction(
            index_name, stock_signals, sector_analysis, regime
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Analysis complete in {elapsed:.1f}s - Expected Move: {prediction.expected_move_pct:+.2f}%")
        
        return prediction
    
    def _analyze_regime(self, index_name: str) -> RegimeAnalysis:
        """Analyze market regime using index or constituent data"""
        try:
            # Try to get index data directly
            index_symbol = self._get_index_symbol(index_name)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            
            df = self.fyers_client.get_historical_data(
                symbol=index_symbol,
                resolution="D",
                date_from=start_date,
                date_to=end_date
            )
            
            if df is None or len(df) < 20:
                # Fallback to default regime
                return self._default_regime()
            
            return self._calculate_regime(df)
            
        except Exception as e:
            logger.warning(f"Could not analyze regime: {e}, using default")
            return self._default_regime()
    
    def _get_index_symbol(self, index_name: str) -> str:
        """Get Fyers symbol for index"""
        index_symbols = {
            "NIFTY": "NSE:NIFTY50-INDEX",
            "NIFTY50": "NSE:NIFTY50-INDEX",
            "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
            "SENSEX": "BSE:SENSEX-INDEX",
            "FINNIFTY": "NSE:FINNIFTY-INDEX",
        }
        return index_symbols.get(index_name.upper(), "NSE:NIFTY50-INDEX")
    
    def _calculate_regime(self, df: pd.DataFrame) -> RegimeAnalysis:
        """Calculate market regime from price data"""
        df = df.copy()
        
        # Calculate ADX
        adx = self._calculate_adx(df, period=self.adx_period)
        
        # Calculate ATR and its percentile
        atr = self._calculate_atr(df, period=self.volatility_window)
        atr_percentile = self._calculate_percentile(atr, df['close'].iloc[-1])
        
        # Determine trend direction
        ema_20 = df['close'].ewm(span=20).mean().iloc[-1]
        ema_50 = df['close'].ewm(span=50).mean().iloc[-1] if len(df) >= 50 else ema_20
        current_price = df['close'].iloc[-1]
        
        # Classify regime
        regime = self._classify_regime(adx, atr_percentile, current_price, ema_20, ema_50)
        
        # Calculate adjustments based on regime
        prob_mult, move_mult = self._get_regime_adjustments(regime, adx, atr_percentile)
        
        # Determine volatility level
        if atr_percentile > 90:
            vol_level = "extreme"
        elif atr_percentile > 80:
            vol_level = "high"
        elif atr_percentile > 30:
            vol_level = "normal"
        else:
            vol_level = "low"
        
        return RegimeAnalysis(
            regime=regime,
            adx_value=adx,
            atr_percentile=atr_percentile,
            volatility_level=vol_level,
            trend_strength=min(adx * 2, 100),  # Scale to 0-100
            probability_multiplier=prob_mult,
            move_size_multiplier=move_mult
        )
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average Directional Index"""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Directional Movement
            up_move = high - high.shift(1)
            down_move = low.shift(1) - low
            
            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
            
            # Smoothed averages
            atr = pd.Series(tr).ewm(span=period).mean()
            plus_di = 100 * pd.Series(plus_dm).ewm(span=period).mean() / atr
            minus_di = 100 * pd.Series(minus_dm).ewm(span=period).mean() / atr
            
            # ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
            adx = dx.ewm(span=period).mean()
            
            return float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 20.0
        except:
            return 20.0  # Default moderate trend
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 20) -> float:
        """Calculate Average True Range"""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            atr = tr.rolling(window=period).mean()
            return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0
        except:
            return 0
    
    def _calculate_percentile(self, atr: float, price: float) -> float:
        """Calculate ATR as percentile of price (volatility measure)"""
        if price <= 0:
            return 50.0
        atr_pct = (atr / price) * 100
        # Map to percentile (typical range 0.5-3% for indices)
        return min(max(atr_pct * 33.33, 0), 100)
    
    def _classify_regime(
        self, 
        adx: float, 
        atr_percentile: float,
        price: float,
        ema_20: float,
        ema_50: float
    ) -> MarketRegime:
        """Classify market regime based on indicators"""
        
        # Check for high volatility first
        if atr_percentile > self.volatility_high_percentile:
            return MarketRegime.HIGH_VOLATILITY
        
        # Determine direction
        is_bullish = price > ema_20 > ema_50
        is_bearish = price < ema_20 < ema_50
        
        # Classify based on ADX (trend strength)
        if adx >= self.adx_strong_trend:
            if is_bullish:
                return MarketRegime.STRONG_TREND_UP
            elif is_bearish:
                return MarketRegime.STRONG_TREND_DOWN
        elif adx >= self.adx_weak_trend:
            if is_bullish:
                return MarketRegime.WEAK_TREND_UP
            elif is_bearish:
                return MarketRegime.WEAK_TREND_DOWN
        
        return MarketRegime.RANGE_BOUND
    
    def _get_regime_adjustments(
        self, 
        regime: MarketRegime,
        adx: float,
        atr_percentile: float
    ) -> Tuple[float, float]:
        """Get probability and move size multipliers based on regime"""
        
        adjustments = {
            MarketRegime.STRONG_TREND_UP: (1.2, 1.3),    # Boost bullish signals
            MarketRegime.WEAK_TREND_UP: (1.0, 1.1),
            MarketRegime.RANGE_BOUND: (0.7, 0.8),        # Reduce confidence
            MarketRegime.WEAK_TREND_DOWN: (1.0, 1.1),
            MarketRegime.STRONG_TREND_DOWN: (1.2, 1.3),  # Boost bearish signals
            MarketRegime.HIGH_VOLATILITY: (0.8, 1.5),   # Lower confidence, larger moves
        }
        
        return adjustments.get(regime, (1.0, 1.0))
    
    def _default_regime(self) -> RegimeAnalysis:
        """Default regime when analysis fails"""
        return RegimeAnalysis(
            regime=MarketRegime.RANGE_BOUND,
            adx_value=20.0,
            atr_percentile=50.0,
            volatility_level="normal",
            trend_strength=40.0,
            probability_multiplier=1.0,
            move_size_multiplier=1.0
        )
    
    def _analyze_all_stocks(
        self,
        constituents: List[StockConstituent],
        normalized_weights: Dict[str, float],
        regime: RegimeAnalysis,
        parallel: bool = True
    ) -> List[StockSignal]:
        """Analyze all constituent stocks with rate limiting"""
        
        # Use sequential analysis with small delays to avoid API rate limits
        # Fyers has a limit of ~10 requests per second
        return self._analyze_stocks_sequential_with_rate_limit(constituents, normalized_weights, regime)
    
    def _analyze_stocks_sequential_with_rate_limit(
        self,
        constituents: List[StockConstituent],
        normalized_weights: Dict[str, float],
        regime: RegimeAnalysis
    ) -> List[StockSignal]:
        """Analyze stocks sequentially with rate limiting to avoid 429 errors"""
        import time
        
        signals = []
        batch_size = 5  # Process 5 stocks then wait
        delay_between_batches = 0.5  # 0.5 second delay between batches
        
        for i, stock in enumerate(constituents):
            try:
                signal = self._analyze_single_stock(stock, normalized_weights, regime)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error analyzing {stock.symbol}: {e}")
            
            # Rate limiting: pause after every batch
            if (i + 1) % batch_size == 0 and i < len(constituents) - 1:
                time.sleep(delay_between_batches)
        
        logger.info(f"📊 Successfully analyzed {len(signals)}/{len(constituents)} stocks")
        return signals
    
    def _analyze_stocks_parallel(
        self,
        constituents: List[StockConstituent],
        normalized_weights: Dict[str, float],
        regime: RegimeAnalysis
    ) -> List[StockSignal]:
        """Analyze stocks in parallel (disabled due to rate limits)"""
        signals = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:  # Reduced from 10 to 3
            futures = {
                executor.submit(
                    self._analyze_single_stock, stock, normalized_weights, regime
                ): stock
                for stock in constituents
            }
            
            for future in as_completed(futures):
                stock = futures[future]
                try:
                    signal = future.result()
                    if signal:
                        signals.append(signal)
                except Exception as e:
                    logger.error(f"Error analyzing {stock.symbol}: {e}")
        
        return signals
    
    def _analyze_stocks_sequential(
        self,
        constituents: List[StockConstituent],
        normalized_weights: Dict[str, float],
        regime: RegimeAnalysis
    ) -> List[StockSignal]:
        """Analyze stocks sequentially"""
        signals = []
        
        for stock in constituents:
            try:
                signal = self._analyze_single_stock(stock, normalized_weights, regime)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error analyzing {stock.symbol}: {e}")
        
        return signals
    
    def _analyze_single_stock(
        self,
        stock: StockConstituent,
        normalized_weights: Dict[str, float],
        regime: RegimeAnalysis
    ) -> Optional[StockSignal]:
        """Analyze a single stock and generate probability signal"""
        try:
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            
            df = self.fyers_client.get_historical_data(
                symbol=stock.fyers_symbol,
                resolution="D",
                date_from=start_date,
                date_to=end_date
            )
            
            if df is None or len(df) < 15:
                logger.debug(f"Insufficient data for {stock.symbol}")
                return None
            
            # Get current price
            current_price = float(df['close'].iloc[-1])
            if current_price <= 0:
                return None
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(df)
            
            # Generate probability-weighted signal
            signal_data = self._generate_probability_signal(
                stock, df, indicators, regime
            )
            
            # Get weight
            weight = normalized_weights.get(stock.fyers_symbol, 0)
            
            # Calculate weighted contribution
            weighted_contribution = (
                weight * 
                signal_data['probability'] * 
                signal_data['expected_move']
            )
            
            return StockSignal(
                symbol=stock.fyers_symbol,
                name=stock.name,
                weight=weight,
                sector=stock.sector,
                current_price=current_price,
                price_change_pct=indicators['daily_change'],
                signal_type=signal_data['signal_type'],
                probability=signal_data['probability'],
                expected_move_pct=signal_data['expected_move'],
                weighted_contribution=weighted_contribution,
                rsi=indicators['rsi'],
                trend_direction=indicators['trend'],
                volume_surge=indicators['volume_surge'],
                vwap_position=indicators['vwap_position'],
                ema_alignment=indicators['ema_alignment'],
                correlation_with_index=stock.avg_correlation,
                confidence_score=signal_data['confidence'],
                bullish_factors=signal_data['bullish_factors'],
                bearish_factors=signal_data['bearish_factors']
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {stock.symbol}: {e}")
            return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate all technical indicators for a stock"""
        df = df.copy()
        
        # Moving averages
        df['ema_5'] = df['close'].ewm(span=5).mean()
        df['ema_10'] = df['close'].ewm(span=10).mean()
        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['sma_50'] = df['close'].rolling(50).mean() if len(df) >= 50 else df['ema_20']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 0.0001)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # VWAP approximation (using typical price)
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['vwap'] = (df['typical_price'] * df['volume']).cumsum() / df['volume'].cumsum()
        
        # Volume
        df['volume_sma'] = df['volume'].rolling(10).mean()
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # Get latest values
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2] if len(df) > 1 else current_price
        
        return {
            'rsi': float(df['rsi'].iloc[-1]) if not pd.isna(df['rsi'].iloc[-1]) else 50,
            'ema_5': float(df['ema_5'].iloc[-1]),
            'ema_10': float(df['ema_10'].iloc[-1]),
            'ema_20': float(df['ema_20'].iloc[-1]),
            'vwap': float(df['vwap'].iloc[-1]) if not pd.isna(df['vwap'].iloc[-1]) else current_price,
            'macd': float(df['macd'].iloc[-1]) if not pd.isna(df['macd'].iloc[-1]) else 0,
            'macd_signal': float(df['macd_signal'].iloc[-1]) if not pd.isna(df['macd_signal'].iloc[-1]) else 0,
            'volume_surge': df['volume'].iloc[-1] > df['volume_sma'].iloc[-1] * 1.5 if not pd.isna(df['volume_sma'].iloc[-1]) else False,
            'daily_change': ((current_price - prev_price) / prev_price * 100) if prev_price > 0 else 0,
            'trend': self._determine_trend(df),
            'vwap_position': 'above' if current_price > df['vwap'].iloc[-1] else 'below',
            'ema_alignment': self._determine_ema_alignment(df)
        }
    
    def _determine_trend(self, df: pd.DataFrame) -> str:
        """Determine trend direction"""
        if len(df) < 20:
            return "neutral"
        
        ema_5 = df['ema_5'].iloc[-1] if 'ema_5' in df else df['close'].ewm(span=5).mean().iloc[-1]
        ema_20 = df['ema_20'].iloc[-1] if 'ema_20' in df else df['close'].ewm(span=20).mean().iloc[-1]
        price = df['close'].iloc[-1]
        
        if price > ema_5 > ema_20:
            return "up"
        elif price < ema_5 < ema_20:
            return "down"
        return "neutral"
    
    def _determine_ema_alignment(self, df: pd.DataFrame) -> str:
        """Determine EMA alignment"""
        if len(df) < 20:
            return "mixed"
        
        ema_5 = df['ema_5'].iloc[-1] if 'ema_5' in df else df['close'].ewm(span=5).mean().iloc[-1]
        ema_10 = df['ema_10'].iloc[-1] if 'ema_10' in df else df['close'].ewm(span=10).mean().iloc[-1]
        ema_20 = df['ema_20'].iloc[-1] if 'ema_20' in df else df['close'].ewm(span=20).mean().iloc[-1]
        
        if ema_5 > ema_10 > ema_20:
            return "bullish"
        elif ema_5 < ema_10 < ema_20:
            return "bearish"
        return "mixed"
    
    def _generate_probability_signal(
        self,
        stock: StockConstituent,
        df: pd.DataFrame,
        indicators: Dict,
        regime: RegimeAnalysis
    ) -> Dict:
        """Generate probability-weighted signal for a stock"""
        
        bullish_factors = []
        bearish_factors = []
        bullish_score = 0
        bearish_score = 0
        
        # 1. RSI Analysis (weight: 20)
        rsi = indicators['rsi']
        if rsi < 30:
            bullish_score += 20
            bullish_factors.append(f"RSI oversold ({rsi:.1f})")
        elif rsi < 40:
            bullish_score += 12
            bullish_factors.append(f"RSI low ({rsi:.1f})")
        elif rsi > 70:
            bearish_score += 20
            bearish_factors.append(f"RSI overbought ({rsi:.1f})")
        elif rsi > 60:
            bearish_score += 12
            bearish_factors.append(f"RSI elevated ({rsi:.1f})")
        
        # 2. EMA Alignment (weight: 25)
        ema_alignment = indicators['ema_alignment']
        if ema_alignment == "bullish":
            bullish_score += 25
            bullish_factors.append("EMA bullish alignment")
        elif ema_alignment == "bearish":
            bearish_score += 25
            bearish_factors.append("EMA bearish alignment")
        
        # 3. Trend Direction (weight: 20)
        trend = indicators['trend']
        if trend == "up":
            bullish_score += 20
            bullish_factors.append("Uptrend confirmed")
        elif trend == "down":
            bearish_score += 20
            bearish_factors.append("Downtrend confirmed")
        
        # 4. VWAP Position (weight: 15)
        if indicators['vwap_position'] == "above":
            bullish_score += 15
            bullish_factors.append("Above VWAP")
        else:
            bearish_score += 15
            bearish_factors.append("Below VWAP")
        
        # 5. Volume Confirmation (weight: 15)
        if indicators['volume_surge']:
            # Volume surge amplifies the direction
            if indicators['daily_change'] > 0:
                bullish_score += 15
                bullish_factors.append("High volume on up move")
            else:
                bearish_score += 15
                bearish_factors.append("High volume on down move")
        
        # 6. MACD (weight: 15)
        if indicators['macd'] > indicators['macd_signal']:
            bullish_score += 15
            bullish_factors.append("MACD bullish crossover")
        else:
            bearish_score += 15
            bearish_factors.append("MACD bearish crossover")
        
        # Calculate raw probability (0-1)
        total_score = bullish_score + bearish_score
        if total_score == 0:
            raw_probability = 0.5
        else:
            # Probability is directional: >0.5 = bullish, <0.5 = bearish
            raw_probability = bullish_score / total_score
        
        # Apply regime adjustment
        adjusted_probability = raw_probability
        
        # Determine signal type
        if raw_probability >= 0.7:
            signal_type = SignalType.STRONG_BUY
            expected_move = self.default_move_bullish * 1.5
        elif raw_probability >= 0.6:
            signal_type = SignalType.BUY
            expected_move = self.default_move_bullish
        elif raw_probability >= 0.55:
            signal_type = SignalType.WEAK_BUY
            expected_move = self.default_move_bullish * 0.5
        elif raw_probability <= 0.3:
            signal_type = SignalType.STRONG_SELL
            expected_move = self.default_move_bearish * 1.5
        elif raw_probability <= 0.4:
            signal_type = SignalType.SELL
            expected_move = self.default_move_bearish
        elif raw_probability <= 0.45:
            signal_type = SignalType.WEAK_SELL
            expected_move = self.default_move_bearish * 0.5
        else:
            signal_type = SignalType.NEUTRAL
            expected_move = 0
        
        # Apply regime move adjustment
        expected_move *= regime.move_size_multiplier
        
        # Cap expected move
        expected_move = max(min(expected_move, self.max_daily_move), -self.max_daily_move)
        
        # Calculate confidence (0-100)
        confidence = abs(raw_probability - 0.5) * 200  # Scale to 0-100
        confidence = min(confidence * regime.probability_multiplier, 100)
        
        return {
            'signal_type': signal_type,
            'probability': abs(raw_probability - 0.5) * 2,  # 0-1 scale (strength)
            'direction_probability': raw_probability,  # >0.5 = bullish
            'expected_move': expected_move,
            'confidence': confidence,
            'bullish_factors': bullish_factors,
            'bearish_factors': bearish_factors,
            'bullish_score': bullish_score,
            'bearish_score': bearish_score
        }
    
    def _apply_correlation_filter(self, signals: List[StockSignal]) -> List[StockSignal]:
        """Filter out stocks with low correlation to index"""
        filtered = []
        
        for signal in signals:
            if signal.correlation_with_index >= self.min_correlation:
                filtered.append(signal)
            else:
                logger.debug(f"Filtered {signal.symbol} - low correlation: {signal.correlation_with_index}")
        
        logger.info(f"Correlation filter: {len(filtered)}/{len(signals)} stocks passed")
        return filtered
    
    def _aggregate_by_sector(
        self,
        signals: List[StockSignal],
        index_name: str
    ) -> Dict[str, SectorAnalysis]:
        """Aggregate signals by sector"""
        sector_weights = index_manager.get_sector_weights(index_name)
        sector_groups: Dict[Sector, List[StockSignal]] = {}
        
        # Group by sector
        for signal in signals:
            if signal.sector not in sector_groups:
                sector_groups[signal.sector] = []
            sector_groups[signal.sector].append(signal)
        
        sector_analysis = {}
        
        for sector, stocks in sector_groups.items():
            if not stocks:
                continue
            
            # Calculate sector metrics
            total_sector_weight = sum(s.weight for s in stocks)
            
            # Weighted expected move for sector
            if total_sector_weight > 0:
                sector_expected_move = sum(
                    s.weighted_contribution for s in stocks
                ) / total_sector_weight * 100  # Normalize
            else:
                sector_expected_move = 0
            
            # Average probability
            avg_prob = np.mean([s.probability for s in stocks])
            
            # Count signals
            bullish_count = sum(1 for s in stocks if s.signal_type in [
                SignalType.STRONG_BUY, SignalType.BUY, SignalType.WEAK_BUY
            ])
            bearish_count = sum(1 for s in stocks if s.signal_type in [
                SignalType.STRONG_SELL, SignalType.SELL, SignalType.WEAK_SELL
            ])
            neutral_count = len(stocks) - bullish_count - bearish_count
            
            # Determine sector signal
            if bullish_count > bearish_count + neutral_count / 2:
                if avg_prob > 0.7:
                    sector_signal = SignalType.STRONG_BUY
                else:
                    sector_signal = SignalType.BUY
            elif bearish_count > bullish_count + neutral_count / 2:
                if avg_prob > 0.7:
                    sector_signal = SignalType.STRONG_SELL
                else:
                    sector_signal = SignalType.SELL
            else:
                sector_signal = SignalType.NEUTRAL
            
            sector_analysis[sector.value] = SectorAnalysis(
                sector=sector,
                sector_weight=sector_weights.get(sector, total_sector_weight * 100),
                stock_count=len(stocks),
                expected_sector_move=sector_expected_move,
                avg_probability=avg_prob,
                bullish_stock_count=bullish_count,
                bearish_stock_count=bearish_count,
                neutral_stock_count=neutral_count,
                sector_signal=sector_signal,
                sector_confidence=avg_prob * 100,
                stocks=sorted(stocks, key=lambda x: abs(x.weighted_contribution), reverse=True)
            )
        
        return sector_analysis
    
    def _calculate_index_prediction(
        self,
        index_name: str,
        signals: List[StockSignal],
        sector_analysis: Dict[str, SectorAnalysis],
        regime: RegimeAnalysis
    ) -> IndexPrediction:
        """Calculate final index prediction from all signals"""
        
        if not signals:
            return self._empty_prediction(index_name, regime)
        
        # Calculate weighted expected move
        # Formula: Index Move = Σ(wᵢ × Pᵢ × Δpᵢ)
        total_weighted_contribution = sum(s.weighted_contribution for s in signals)
        
        # Count signals by type
        bullish_stocks = sum(1 for s in signals if s.signal_type in [
            SignalType.STRONG_BUY, SignalType.BUY, SignalType.WEAK_BUY
        ])
        bearish_stocks = sum(1 for s in signals if s.signal_type in [
            SignalType.STRONG_SELL, SignalType.SELL, SignalType.WEAK_SELL
        ])
        neutral_stocks = len(signals) - bullish_stocks - bearish_stocks
        
        # Calculate probability distribution
        bullish_weight = sum(s.weight for s in signals if s.signal_type in [
            SignalType.STRONG_BUY, SignalType.BUY, SignalType.WEAK_BUY
        ])
        bearish_weight = sum(s.weight for s in signals if s.signal_type in [
            SignalType.STRONG_SELL, SignalType.SELL, SignalType.WEAK_SELL
        ])
        neutral_weight = 1 - bullish_weight - bearish_weight
        
        # Normalize probabilities
        total_weight = bullish_weight + bearish_weight + neutral_weight
        if total_weight > 0:
            prob_up = bullish_weight / total_weight
            prob_down = bearish_weight / total_weight
            prob_neutral = neutral_weight / total_weight
        else:
            prob_up = prob_down = 0.33
            prob_neutral = 0.34
        
        # Determine direction
        if total_weighted_contribution > 0.001:
            direction = "BULLISH"
        elif total_weighted_contribution < -0.001:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"
        
        # Calculate confidence
        avg_confidence = np.mean([s.confidence_score for s in signals])
        
        # Apply regime adjustment
        avg_confidence *= regime.probability_multiplier
        avg_confidence = min(avg_confidence, 95)
        
        # Get top contributors (by weighted contribution)
        sorted_signals = sorted(signals, key=lambda x: x.weighted_contribution, reverse=True)
        top_bullish = [s for s in sorted_signals if s.weighted_contribution > 0][:5]
        top_bearish = [s for s in sorted_signals if s.weighted_contribution < 0][-5:][::-1]
        
        # Get index current level
        try:
            index_symbol = self._get_index_symbol(index_name)
            quotes = self.fyers_client.get_quotes([index_symbol])
            if quotes and 'd' in quotes:
                current_level = quotes['d'][0]['v'].get('lp', 0)
            else:
                current_level = 0
        except:
            current_level = 0
        
        return IndexPrediction(
            index_name=index_name,
            timestamp=datetime.now(),
            current_level=current_level,
            regime=regime,
            expected_move_pct=total_weighted_contribution * 100,
            expected_direction=direction,
            prediction_confidence=avg_confidence,
            prob_up=prob_up,
            prob_down=prob_down,
            prob_neutral=prob_neutral,
            total_stocks_analyzed=len(signals),
            bullish_stocks=bullish_stocks,
            bearish_stocks=bearish_stocks,
            neutral_stocks=neutral_stocks,
            sector_analysis=sector_analysis,
            top_bullish_contributors=top_bullish,
            top_bearish_contributors=top_bearish,
            stock_signals=signals
        )
    
    def _empty_prediction(self, index_name: str, regime: RegimeAnalysis) -> IndexPrediction:
        """Return empty prediction when no data"""
        return IndexPrediction(
            index_name=index_name,
            timestamp=datetime.now(),
            current_level=0,
            regime=regime,
            expected_move_pct=0,
            expected_direction="NEUTRAL",
            prediction_confidence=0,
            prob_up=0.33,
            prob_down=0.33,
            prob_neutral=0.34,
            total_stocks_analyzed=0,
            bullish_stocks=0,
            bearish_stocks=0,
            neutral_stocks=0,
            sector_analysis={},
            top_bullish_contributors=[],
            top_bearish_contributors=[],
            stock_signals=[]
        )
    
    def get_surge_candidates(
        self,
        index_name: str,
        min_expected_move: float = 2.0
    ) -> List[StockSignal]:
        """
        Identify stocks preparing for strong upward surge
        
        Args:
            index_name: Index to analyze
            min_expected_move: Minimum expected % move to qualify
            
        Returns:
            List of potential surge candidates
        """
        prediction = self.analyze_index(index_name)
        
        surge_candidates = []
        for signal in prediction.stock_signals:
            if (signal.signal_type in [SignalType.STRONG_BUY, SignalType.BUY] and
                signal.expected_move_pct >= min_expected_move and
                signal.confidence_score >= 60):
                surge_candidates.append(signal)
        
        return sorted(surge_candidates, key=lambda x: x.expected_move_pct, reverse=True)
    
    def get_exhaustion_candidates(
        self,
        index_name: str,
        min_expected_move: float = -2.0
    ) -> List[StockSignal]:
        """
        Identify stocks showing exhaustion (peak zones for selling)
        
        Args:
            index_name: Index to analyze
            min_expected_move: Minimum expected % decline to qualify
            
        Returns:
            List of potential exhaustion/sell candidates
        """
        prediction = self.analyze_index(index_name)
        
        exhaustion_candidates = []
        for signal in prediction.stock_signals:
            if (signal.signal_type in [SignalType.STRONG_SELL, SignalType.SELL] and
                signal.expected_move_pct <= min_expected_move and
                signal.confidence_score >= 60):
                exhaustion_candidates.append(signal)
        
        return sorted(exhaustion_candidates, key=lambda x: x.expected_move_pct)


# Global analyzer instance
_probability_analyzer = None

def get_probability_analyzer(fyers_client) -> IndexProbabilityAnalyzer:
    """Get or create probability analyzer instance"""
    global _probability_analyzer
    if _probability_analyzer is None:
        _probability_analyzer = IndexProbabilityAnalyzer(fyers_client)
    return _probability_analyzer
