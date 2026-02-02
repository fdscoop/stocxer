"""
XGBoost Direction Prediction Model
===================================

Upgraded direction prediction using XGBoost instead of ARIMA+Momentum.

Why XGBoost:
- Handles non-linear relationships (markets aren't linear)
- Works well with multiple features
- Fast inference for real-time predictions
- Handles missing data gracefully
- Provides feature importance (explainability)

Features Used:
1. Technical indicators (RSI, MACD, Bollinger, etc.)
2. Volume patterns
3. Time of day
4. Recent momentum
5. Volatility regime
6. Options flow signals (if available)

This model predicts:
- Direction: UP / DOWN / SIDEWAYS
- Magnitude: Expected % move
- Confidence: How sure we are

Author: TradeWise ML Team
Created: 2026-02-02
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import pytz
import pickle
import os

IST = pytz.timezone('Asia/Kolkata')


class Direction(Enum):
    """Predicted price direction"""
    STRONG_UP = "STRONG_UP"     # >0.5% expected
    UP = "UP"                   # 0.2-0.5% expected
    SIDEWAYS = "SIDEWAYS"       # -0.2% to +0.2%
    DOWN = "DOWN"               # -0.5% to -0.2%
    STRONG_DOWN = "STRONG_DOWN" # <-0.5% expected


@dataclass
class DirectionPrediction:
    """Result of direction prediction"""
    direction: Direction
    confidence: float  # 0-1
    expected_move_pct: float
    expected_move_points: float
    
    # Probabilities for each direction
    prob_strong_up: float
    prob_up: float
    prob_sideways: float
    prob_down: float
    prob_strong_down: float
    
    # Feature importance for this prediction
    top_bullish_factors: List[Tuple[str, float]]
    top_bearish_factors: List[Tuple[str, float]]
    
    # Model metadata
    model_version: str
    features_used: int
    
    # Trading recommendation
    trade_signal: str  # "BUY", "SELL", "HOLD"
    signal_strength: str  # "STRONG", "MODERATE", "WEAK"


class TechnicalFeatureExtractor:
    """
    Extracts technical features from price/volume data for ML model.
    """
    
    @staticmethod
    def calculate_rsi(prices: np.ndarray, period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return 50.0  # Neutral
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(prices: np.ndarray) -> Tuple[float, float, float]:
        """Calculate MACD, Signal, and Histogram."""
        if len(prices) < 26:
            return 0.0, 0.0, 0.0
        
        # EMA calculations
        ema_12 = TechnicalFeatureExtractor._ema(prices, 12)
        ema_26 = TechnicalFeatureExtractor._ema(prices, 26)
        
        macd_line = ema_12 - ema_26
        
        # Signal line (9-period EMA of MACD)
        # Simplified: use recent MACD values
        signal = macd_line * 0.9  # Approximation
        histogram = macd_line - signal
        
        return macd_line, signal, histogram
    
    @staticmethod
    def _ema(prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return prices[-1]
        
        multiplier = 2 / (period + 1)
        ema = prices[-period]
        
        for price in prices[-period + 1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    @staticmethod
    def calculate_bollinger_bands(
        prices: np.ndarray, 
        period: int = 20
    ) -> Tuple[float, float, float, float]:
        """
        Calculate Bollinger Bands.
        Returns: (upper, middle, lower, %B position)
        """
        if len(prices) < period:
            return prices[-1], prices[-1], prices[-1], 0.5
        
        middle = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper = middle + (2 * std)
        lower = middle - (2 * std)
        
        # %B: where price is relative to bands (0 = lower, 1 = upper)
        current = prices[-1]
        if upper == lower:
            pct_b = 0.5
        else:
            pct_b = (current - lower) / (upper - lower)
        
        return upper, middle, lower, pct_b
    
    @staticmethod
    def calculate_atr(
        highs: np.ndarray, 
        lows: np.ndarray, 
        closes: np.ndarray, 
        period: int = 14
    ) -> float:
        """Calculate Average True Range."""
        if len(closes) < period + 1:
            return abs(highs[-1] - lows[-1])
        
        tr_list = []
        for i in range(-period, 0):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_list.append(tr)
        
        return np.mean(tr_list)
    
    @staticmethod
    def calculate_momentum(prices: np.ndarray, periods: List[int] = [5, 10, 20]) -> Dict[str, float]:
        """Calculate momentum over different periods."""
        momentum = {}
        
        for p in periods:
            if len(prices) > p:
                mom = (prices[-1] - prices[-p-1]) / prices[-p-1] * 100
                momentum[f'momentum_{p}'] = mom
            else:
                momentum[f'momentum_{p}'] = 0.0
        
        return momentum
    
    @staticmethod
    def calculate_volume_features(volumes: np.ndarray) -> Dict[str, float]:
        """Calculate volume-based features."""
        if len(volumes) < 20:
            return {
                'volume_ratio': 1.0,
                'volume_trend': 0.0,
                'volume_spike': False
            }
        
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Volume trend (is volume increasing?)
        recent_avg = np.mean(volumes[-5:])
        older_avg = np.mean(volumes[-20:-5])
        volume_trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        
        # Volume spike detection
        volume_spike = volume_ratio > 2.0
        
        return {
            'volume_ratio': volume_ratio,
            'volume_trend': volume_trend,
            'volume_spike': volume_spike
        }


class XGBoostDirectionPredictor:
    """
    XGBoost-based direction prediction model.
    
    Uses technical indicators and market context to predict
    short-term price direction.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_names = []
        self.model_version = "1.0.0"
        
        # Try to load pre-trained model
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            # Use rule-based fallback until model is trained
            self.model = None
    
    def predict(
        self,
        prices: List[float],
        volumes: Optional[List[float]] = None,
        highs: Optional[List[float]] = None,
        lows: Optional[List[float]] = None,
        timestamp: Optional[datetime] = None,
        additional_features: Optional[Dict] = None
    ) -> DirectionPrediction:
        """
        Predict price direction.
        
        Args:
            prices: Historical prices (at least 50 candles recommended)
            volumes: Historical volumes (optional but improves accuracy)
            highs: High prices (optional, for ATR)
            lows: Low prices (optional, for ATR)
            timestamp: Current time (for time-of-day features)
            additional_features: Extra features (options flow, etc.)
        
        Returns:
            DirectionPrediction with direction, confidence, and factors
        """
        if timestamp is None:
            timestamp = datetime.now(IST)
        
        # Extract features
        features = self._extract_features(
            prices, volumes, highs, lows, timestamp, additional_features
        )
        
        # Make prediction
        if self.model is not None:
            # Use trained XGBoost model
            prediction = self._predict_with_model(features)
        else:
            # Use rule-based fallback
            prediction = self._predict_rule_based(features)
        
        return prediction
    
    def _extract_features(
        self,
        prices: List[float],
        volumes: Optional[List[float]],
        highs: Optional[List[float]],
        lows: Optional[List[float]],
        timestamp: datetime,
        additional: Optional[Dict]
    ) -> Dict[str, float]:
        """Extract all features for prediction."""
        
        prices_arr = np.array(prices)
        features = {}
        
        # Price-based features
        features['current_price'] = prices[-1]
        features['price_change_1'] = (prices[-1] - prices[-2]) / prices[-2] * 100 if len(prices) > 1 else 0
        features['price_change_5'] = (prices[-1] - prices[-6]) / prices[-6] * 100 if len(prices) > 5 else 0
        
        # RSI
        features['rsi_14'] = TechnicalFeatureExtractor.calculate_rsi(prices_arr, 14)
        features['rsi_7'] = TechnicalFeatureExtractor.calculate_rsi(prices_arr, 7)
        
        # MACD
        macd, signal, hist = TechnicalFeatureExtractor.calculate_macd(prices_arr)
        features['macd'] = macd
        features['macd_signal'] = signal
        features['macd_histogram'] = hist
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower, bb_pct = TechnicalFeatureExtractor.calculate_bollinger_bands(prices_arr)
        features['bb_position'] = bb_pct
        features['bb_width'] = (bb_upper - bb_lower) / bb_middle if bb_middle > 0 else 0
        
        # Momentum
        momentum = TechnicalFeatureExtractor.calculate_momentum(prices_arr)
        features.update(momentum)
        
        # Volume features
        if volumes:
            vol_features = TechnicalFeatureExtractor.calculate_volume_features(np.array(volumes))
            features['volume_ratio'] = vol_features['volume_ratio']
            features['volume_trend'] = vol_features['volume_trend']
            features['volume_spike'] = 1.0 if vol_features['volume_spike'] else 0.0
        else:
            features['volume_ratio'] = 1.0
            features['volume_trend'] = 0.0
            features['volume_spike'] = 0.0
        
        # ATR (volatility)
        if highs and lows:
            features['atr'] = TechnicalFeatureExtractor.calculate_atr(
                np.array(highs), np.array(lows), prices_arr
            )
            features['atr_pct'] = features['atr'] / prices[-1] * 100
        else:
            features['atr'] = 0
            features['atr_pct'] = 0
        
        # Time features
        features['hour'] = timestamp.hour
        features['minute'] = timestamp.minute
        features['is_first_hour'] = 1.0 if timestamp.hour == 9 else 0.0
        features['is_last_hour'] = 1.0 if timestamp.hour >= 15 else 0.0
        features['is_lunch'] = 1.0 if 12 <= timestamp.hour < 13 else 0.0
        
        # Day of week (Thursday = expiry)
        features['day_of_week'] = timestamp.weekday()
        features['is_expiry_day'] = 1.0 if timestamp.weekday() == 3 else 0.0
        
        # Additional features if provided
        if additional:
            features.update(additional)
        
        self.feature_names = list(features.keys())
        
        return features
    
    def _predict_with_model(self, features: Dict[str, float]) -> DirectionPrediction:
        """Make prediction using trained XGBoost model."""
        # Convert features to array
        X = np.array([[features[f] for f in self.feature_names]])
        
        # Get probability predictions
        probs = self.model.predict_proba(X)[0]
        
        # Class mapping (model trained with these classes)
        classes = [Direction.STRONG_DOWN, Direction.DOWN, Direction.SIDEWAYS, 
                   Direction.UP, Direction.STRONG_UP]
        
        # Get prediction
        pred_idx = np.argmax(probs)
        direction = classes[pred_idx]
        confidence = probs[pred_idx]
        
        # Expected move based on direction
        move_map = {
            Direction.STRONG_UP: 0.6,
            Direction.UP: 0.3,
            Direction.SIDEWAYS: 0.0,
            Direction.DOWN: -0.3,
            Direction.STRONG_DOWN: -0.6
        }
        expected_move = move_map[direction]
        
        # Get feature importances
        importances = self.model.feature_importances_
        feature_importance = list(zip(self.feature_names, importances))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        # Separate bullish and bearish factors
        bullish_features = ['momentum_5', 'momentum_10', 'rsi_14', 'volume_ratio']
        bearish_features = ['rsi_14', 'bb_position', 'macd_histogram']
        
        bullish = [(f, v) for f, v in feature_importance if f in bullish_features][:3]
        bearish = [(f, v) for f, v in feature_importance if f in bearish_features][:3]
        
        return DirectionPrediction(
            direction=direction,
            confidence=confidence,
            expected_move_pct=expected_move,
            expected_move_points=expected_move * features['current_price'] / 100,
            prob_strong_up=probs[4],
            prob_up=probs[3],
            prob_sideways=probs[2],
            prob_down=probs[1],
            prob_strong_down=probs[0],
            top_bullish_factors=bullish,
            top_bearish_factors=bearish,
            model_version=self.model_version,
            features_used=len(self.feature_names),
            trade_signal=self._get_trade_signal(direction, confidence),
            signal_strength=self._get_signal_strength(confidence)
        )
    
    def _predict_rule_based(self, features: Dict[str, float]) -> DirectionPrediction:
        """
        Rule-based prediction as fallback when no trained model available.
        
        Uses classic technical analysis rules.
        """
        score = 0.0  # -1 to +1 scale
        
        # RSI signals
        rsi = features.get('rsi_14', 50)
        if rsi < 30:
            score += 0.3  # Oversold = bullish
        elif rsi > 70:
            score -= 0.3  # Overbought = bearish
        elif rsi < 40:
            score += 0.1
        elif rsi > 60:
            score -= 0.1
        
        # MACD signals
        macd_hist = features.get('macd_histogram', 0)
        if macd_hist > 0:
            score += 0.2
        else:
            score -= 0.2
        
        # Momentum signals
        mom_5 = features.get('momentum_5', 0)
        if mom_5 > 0.3:
            score += 0.25
        elif mom_5 < -0.3:
            score -= 0.25
        elif mom_5 > 0:
            score += 0.1
        else:
            score -= 0.1
        
        # Bollinger Band position
        bb_pos = features.get('bb_position', 0.5)
        if bb_pos < 0.1:  # Near lower band
            score += 0.2
        elif bb_pos > 0.9:  # Near upper band
            score -= 0.2
        
        # Volume confirmation
        vol_ratio = features.get('volume_ratio', 1.0)
        if vol_ratio > 1.5:
            score *= 1.2  # Amplify signal with volume
        
        # Time of day adjustment
        if features.get('is_first_hour', 0):
            score *= 1.1  # First hour trends continue
        if features.get('is_lunch', 0):
            score *= 0.7  # Lunch = less reliable
        
        # Convert score to direction
        if score > 0.4:
            direction = Direction.STRONG_UP
            expected_move = 0.5
        elif score > 0.15:
            direction = Direction.UP
            expected_move = 0.25
        elif score > -0.15:
            direction = Direction.SIDEWAYS
            expected_move = 0.0
        elif score > -0.4:
            direction = Direction.DOWN
            expected_move = -0.25
        else:
            direction = Direction.STRONG_DOWN
            expected_move = -0.5
        
        # Confidence based on score magnitude and factor agreement
        confidence = min(0.85, 0.4 + abs(score) * 0.5)
        
        # Calculate pseudo-probabilities
        probs = self._score_to_probabilities(score)
        
        # Feature analysis for explanation
        bullish_factors = []
        bearish_factors = []
        
        if rsi < 40:
            bullish_factors.append(('rsi_oversold', 0.3))
        if rsi > 60:
            bearish_factors.append(('rsi_overbought', 0.3))
        if mom_5 > 0:
            bullish_factors.append(('positive_momentum', abs(mom_5) / 2))
        if mom_5 < 0:
            bearish_factors.append(('negative_momentum', abs(mom_5) / 2))
        if macd_hist > 0:
            bullish_factors.append(('macd_bullish', 0.2))
        if macd_hist < 0:
            bearish_factors.append(('macd_bearish', 0.2))
        
        return DirectionPrediction(
            direction=direction,
            confidence=confidence,
            expected_move_pct=expected_move,
            expected_move_points=expected_move * features.get('current_price', 25000) / 100,
            prob_strong_up=probs['strong_up'],
            prob_up=probs['up'],
            prob_sideways=probs['sideways'],
            prob_down=probs['down'],
            prob_strong_down=probs['strong_down'],
            top_bullish_factors=bullish_factors[:3],
            top_bearish_factors=bearish_factors[:3],
            model_version="rule_based_1.0",
            features_used=len(features),
            trade_signal=self._get_trade_signal(direction, confidence),
            signal_strength=self._get_signal_strength(confidence)
        )
    
    def _score_to_probabilities(self, score: float) -> Dict[str, float]:
        """Convert score to probability distribution."""
        # Use softmax-like distribution centered on score
        import math
        
        centers = {
            'strong_down': -0.6,
            'down': -0.3,
            'sideways': 0.0,
            'up': 0.3,
            'strong_up': 0.6
        }
        
        # Calculate distances and convert to probabilities
        raw_probs = {}
        for name, center in centers.items():
            distance = abs(score - center)
            raw_probs[name] = math.exp(-distance * 3)
        
        # Normalize
        total = sum(raw_probs.values())
        return {k: v/total for k, v in raw_probs.items()}
    
    def _get_trade_signal(self, direction: Direction, confidence: float) -> str:
        """Get trading signal from direction and confidence."""
        if confidence < 0.45:
            return "HOLD"
        
        if direction in [Direction.STRONG_UP, Direction.UP]:
            return "BUY"
        elif direction in [Direction.STRONG_DOWN, Direction.DOWN]:
            return "SELL"
        else:
            return "HOLD"
    
    def _get_signal_strength(self, confidence: float) -> str:
        """Get signal strength from confidence."""
        if confidence >= 0.7:
            return "STRONG"
        elif confidence >= 0.5:
            return "MODERATE"
        else:
            return "WEAK"
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
        validation_split: float = 0.2
    ) -> Dict[str, float]:
        """
        Train the XGBoost model on historical data.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target labels (0-4 for the 5 direction classes)
            feature_names: Names of features
            validation_split: Fraction for validation
        
        Returns:
            Training metrics
        """
        try:
            import xgboost as xgb
            from sklearn.model_selection import train_test_split
        except ImportError:
            raise ImportError("xgboost and scikit-learn required for training")
        
        self.feature_names = feature_names
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )
        
        # Create XGBoost model
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            objective='multi:softprob',
            num_class=5,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
        
        # Train
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=10,
            verbose=False
        )
        
        # Calculate metrics
        train_acc = self.model.score(X_train, y_train)
        val_acc = self.model.score(X_val, y_val)
        
        return {
            'train_accuracy': train_acc,
            'validation_accuracy': val_acc,
            'n_samples': len(X),
            'n_features': X.shape[1]
        }
    
    def save_model(self, path: str):
        """Save trained model to disk."""
        if self.model is not None:
            with open(path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'feature_names': self.feature_names,
                    'version': self.model_version
                }, f)
    
    def load_model(self, path: str):
        """Load trained model from disk."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.feature_names = data['feature_names']
            self.model_version = data.get('version', '1.0.0')


def create_direction_predictor(model_path: Optional[str] = None) -> XGBoostDirectionPredictor:
    """Factory function to create a direction predictor."""
    return XGBoostDirectionPredictor(model_path)
