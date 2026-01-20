"""
ML Probability Optimizer for Index Analysis
Enhances probability-based predictions using machine learning

This module:
1. Analyzes historical patterns for signal accuracy
2. Uses classification models (Logistic Regression, XGBoost)
3. Predicts: up / flat / down with probability
4. Optimizes probability scores based on historical performance
5. Provides feature importance for signal refinement
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import joblib
import os

# ML imports
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import TimeSeriesSplit, cross_val_score
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    import xgboost as xgb
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MLPrediction:
    """ML model prediction output"""
    predicted_direction: str          # "UP", "DOWN", "FLAT"
    probability_up: float             # Probability of up move
    probability_down: float           # Probability of down move
    probability_flat: float           # Probability of flat
    confidence: float                 # Model confidence (0-100)
    model_type: str                   # Model used
    feature_importance: Dict[str, float]  # Top features


class IndexMLOptimizer:
    """
    ML-based probability optimizer for index predictions
    
    Uses classification models to predict index direction
    and optimize probability scores
    """
    
    def __init__(self, model_type: str = "xgboost"):
        """
        Initialize ML optimizer
        
        Args:
            model_type: "xgboost", "random_forest", "logistic", "gradient_boosting"
        """
        self.model_type = model_type
        self.models: Dict[str, object] = {}  # One model per index
        self.scalers: Dict[str, StandardScaler] = {}
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_names: List[str] = []
        self.is_fitted: Dict[str, bool] = {}
        
        # Model storage path
        self.model_dir = os.path.join(os.path.dirname(__file__), '../../models/saved_models')
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Direction thresholds
        self.up_threshold = 0.3      # % move to classify as UP
        self.down_threshold = -0.3   # % move to classify as DOWN
        
    def _create_model(self):
        """Create the classification model"""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available")
            return None
            
        if self.model_type == "xgboost":
            return xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                use_label_encoder=False,
                eval_metric='mlogloss'
            )
        elif self.model_type == "random_forest":
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == "logistic":
            return LogisticRegression(
                max_iter=1000,
                random_state=42,
                multi_class='multinomial'
            )
        elif self.model_type == "gradient_boosting":
            return GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def prepare_features(
        self,
        df: pd.DataFrame,
        stock_signals: Optional[List[Dict]] = None
    ) -> pd.DataFrame:
        """
        Prepare features for ML model
        
        Features:
        1. Technical indicators (index level)
        2. Aggregated stock signals (if available)
        3. Regime indicators
        4. Time features
        """
        features = df.copy()
        
        # =====================================
        # 1. Price-based features
        # =====================================
        features['returns'] = features['close'].pct_change() * 100
        features['log_returns'] = np.log(features['close'] / features['close'].shift(1)) * 100
        
        # Momentum
        for period in [1, 3, 5, 10]:
            features[f'momentum_{period}'] = features['close'].pct_change(period) * 100
        
        # =====================================
        # 2. Moving Averages
        # =====================================
        for period in [5, 10, 20, 50]:
            features[f'sma_{period}'] = features['close'].rolling(period).mean()
            features[f'ema_{period}'] = features['close'].ewm(span=period).mean()
            features[f'price_vs_sma_{period}'] = (
                (features['close'] - features[f'sma_{period}']) / features[f'sma_{period}'] * 100
            )
        
        # =====================================
        # 3. Volatility features
        # =====================================
        features['volatility_5'] = features['returns'].rolling(5).std()
        features['volatility_10'] = features['returns'].rolling(10).std()
        features['volatility_20'] = features['returns'].rolling(20).std()
        
        # ATR
        high_low = features['high'] - features['low']
        high_close = abs(features['high'] - features['close'].shift(1))
        low_close = abs(features['low'] - features['close'].shift(1))
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        features['atr_14'] = tr.rolling(14).mean()
        features['atr_pct'] = features['atr_14'] / features['close'] * 100
        
        # =====================================
        # 4. RSI
        # =====================================
        delta = features['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 0.0001)
        features['rsi_14'] = 100 - (100 / (1 + rs))
        
        # RSI derivatives
        features['rsi_oversold'] = (features['rsi_14'] < 30).astype(int)
        features['rsi_overbought'] = (features['rsi_14'] > 70).astype(int)
        
        # =====================================
        # 5. MACD
        # =====================================
        ema_12 = features['close'].ewm(span=12).mean()
        ema_26 = features['close'].ewm(span=26).mean()
        features['macd'] = ema_12 - ema_26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        features['macd_histogram'] = features['macd'] - features['macd_signal']
        
        # =====================================
        # 6. Bollinger Bands
        # =====================================
        features['bb_middle'] = features['close'].rolling(20).mean()
        bb_std = features['close'].rolling(20).std()
        features['bb_upper'] = features['bb_middle'] + (2 * bb_std)
        features['bb_lower'] = features['bb_middle'] - (2 * bb_std)
        features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / features['bb_middle'] * 100
        features['bb_position'] = (
            (features['close'] - features['bb_lower']) / 
            (features['bb_upper'] - features['bb_lower'] + 0.0001)
        )
        
        # =====================================
        # 7. ADX (Trend Strength)
        # =====================================
        features['adx'] = self._calculate_adx(features)
        
        # =====================================
        # 8. Volume features
        # =====================================
        if 'volume' in features.columns:
            features['volume_sma_10'] = features['volume'].rolling(10).mean()
            features['volume_ratio'] = features['volume'] / (features['volume_sma_10'] + 1)
            features['volume_trend'] = features['volume'].rolling(5).mean() / (features['volume'].rolling(20).mean() + 1)
        
        # =====================================
        # 9. Time features
        # =====================================
        if isinstance(features.index, pd.DatetimeIndex):
            features['day_of_week'] = features.index.dayofweek
            features['day_of_month'] = features.index.day
            features['month'] = features.index.month
            features['is_month_start'] = (features.index.day <= 5).astype(int)
            features['is_month_end'] = (features.index.day >= 25).astype(int)
        
        # =====================================
        # 10. Lag features
        # =====================================
        for lag in [1, 2, 3, 5]:
            features[f'return_lag_{lag}'] = features['returns'].shift(lag)
            features[f'rsi_lag_{lag}'] = features['rsi_14'].shift(lag)
        
        return features
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ADX"""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            up_move = high - high.shift(1)
            down_move = low.shift(1) - low
            
            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
            
            atr = pd.Series(tr).ewm(span=period).mean()
            plus_di = 100 * pd.Series(plus_dm).ewm(span=period).mean() / (atr + 0.0001)
            minus_di = 100 * pd.Series(minus_dm).ewm(span=period).mean() / (atr + 0.0001)
            
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
            adx = dx.ewm(span=period).mean()
            
            return adx
        except:
            return pd.Series(index=df.index, data=20)
    
    def prepare_target(self, df: pd.DataFrame, horizon: int = 1) -> pd.Series:
        """
        Prepare target variable (next day direction)
        
        Classes:
        - 0: DOWN (< -0.3%)
        - 1: FLAT (-0.3% to +0.3%)
        - 2: UP (> +0.3%)
        """
        future_return = df['close'].pct_change(horizon).shift(-horizon) * 100
        
        target = pd.Series(index=df.index, data=1)  # Default FLAT
        target[future_return > self.up_threshold] = 2   # UP
        target[future_return < self.down_threshold] = 0  # DOWN
        
        return target
    
    def train(
        self,
        index_name: str,
        df: pd.DataFrame,
        test_size: float = 0.2,
        prediction_horizon: int = 1
    ) -> Dict:
        """
        Train ML model for an index
        
        Args:
            index_name: Index identifier
            df: Historical OHLCV data
            test_size: Fraction for testing
            prediction_horizon: Days ahead to predict
            
        Returns:
            Training metrics
        """
        if not ML_AVAILABLE:
            return {"error": "ML libraries not available"}
        
        logger.info(f"Training ML model for {index_name}...")
        
        # Prepare features and target
        features_df = self.prepare_features(df)
        target = self.prepare_target(df, prediction_horizon)
        
        # Align and clean
        features_df['target'] = target
        features_df = features_df.dropna()
        
        if len(features_df) < 100:
            return {"error": "Insufficient data for training"}
        
        # Select feature columns
        exclude_cols = ['target', 'open', 'high', 'low', 'close', 'volume']
        feature_cols = [c for c in features_df.columns if c not in exclude_cols]
        self.feature_names = feature_cols
        
        X = features_df[feature_cols]
        y = features_df['target']
        
        # Time series split
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Initialize scaler
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = self._create_model()
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_pred = model.predict(X_train_scaled)
        test_pred = model.predict(X_test_scaled)
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        # Store model
        self.models[index_name] = model
        self.scalers[index_name] = scaler
        self.is_fitted[index_name] = True
        
        # Get feature importance
        feature_importance = {}
        if hasattr(model, 'feature_importances_'):
            for name, imp in zip(feature_cols, model.feature_importances_):
                feature_importance[name] = float(imp)
        
        # Cross-validation score
        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = cross_val_score(
            self._create_model(), 
            scaler.fit_transform(X), 
            y, 
            cv=tscv,
            scoring='accuracy'
        )
        
        metrics = {
            "index": index_name,
            "model_type": self.model_type,
            "train_accuracy": train_acc,
            "test_accuracy": test_acc,
            "cv_accuracy_mean": cv_scores.mean(),
            "cv_accuracy_std": cv_scores.std(),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "feature_importance": dict(sorted(
                feature_importance.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10])  # Top 10
        }
        
        logger.info(f"Model trained. Test Accuracy: {test_acc:.2%}")
        
        return metrics
    
    def predict(
        self,
        index_name: str,
        df: pd.DataFrame
    ) -> Optional[MLPrediction]:
        """
        Make prediction for current state
        
        Args:
            index_name: Index identifier
            df: Recent OHLCV data (at least 60 days)
            
        Returns:
            MLPrediction object
        """
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available")
            return None
            
        if index_name not in self.is_fitted or not self.is_fitted[index_name]:
            logger.warning(f"Model not trained for {index_name}")
            # Try to load saved model
            if not self._load_model(index_name):
                return None
        
        try:
            # Prepare features
            features_df = self.prepare_features(df)
            features_df = features_df.dropna()
            
            if len(features_df) == 0:
                return None
            
            # Get latest row
            X = features_df[self.feature_names].iloc[-1:].values
            X_scaled = self.scalers[index_name].transform(X)
            
            # Predict
            model = self.models[index_name]
            prediction = model.predict(X_scaled)[0]
            
            # Get probabilities
            if hasattr(model, 'predict_proba'):
                probs = model.predict_proba(X_scaled)[0]
                # Classes: 0=DOWN, 1=FLAT, 2=UP
                prob_down = probs[0] if len(probs) > 0 else 0.33
                prob_flat = probs[1] if len(probs) > 1 else 0.34
                prob_up = probs[2] if len(probs) > 2 else 0.33
            else:
                prob_down = prob_flat = 0.33
                prob_up = 0.34 if prediction == 2 else 0.33
            
            # Map prediction to direction
            direction_map = {0: "DOWN", 1: "FLAT", 2: "UP"}
            predicted_direction = direction_map.get(prediction, "FLAT")
            
            # Calculate confidence
            confidence = max(prob_up, prob_down, prob_flat) * 100
            
            # Get feature importance
            feature_importance = {}
            if hasattr(model, 'feature_importances_'):
                for name, imp in zip(self.feature_names, model.feature_importances_):
                    feature_importance[name] = float(imp)
                feature_importance = dict(sorted(
                    feature_importance.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5])
            
            return MLPrediction(
                predicted_direction=predicted_direction,
                probability_up=prob_up,
                probability_down=prob_down,
                probability_flat=prob_flat,
                confidence=confidence,
                model_type=self.model_type,
                feature_importance=feature_importance
            )
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def optimize_probability(
        self,
        index_name: str,
        rule_based_prediction: Dict,
        df: pd.DataFrame
    ) -> Dict:
        """
        Optimize rule-based prediction using ML
        
        Combines rule-based analysis with ML predictions
        for enhanced accuracy
        
        Args:
            index_name: Index identifier
            rule_based_prediction: Prediction from IndexProbabilityAnalyzer
            df: Recent OHLCV data
            
        Returns:
            Optimized prediction dict
        """
        # Get ML prediction
        ml_pred = self.predict(index_name, df)
        
        if ml_pred is None:
            # Return rule-based as-is
            return rule_based_prediction
        
        # Extract rule-based values
        rb_prob_up = rule_based_prediction.get('prob_up', 0.33)
        rb_prob_down = rule_based_prediction.get('prob_down', 0.33)
        rb_expected_move = rule_based_prediction.get('expected_move_pct', 0)
        rb_confidence = rule_based_prediction.get('prediction_confidence', 50)
        
        # Combine probabilities (weighted average)
        # Give 60% weight to rule-based (more interpretable) and 40% to ML
        rule_weight = 0.6
        ml_weight = 0.4
        
        optimized_prob_up = (rb_prob_up * rule_weight + ml_pred.probability_up * ml_weight)
        optimized_prob_down = (rb_prob_down * rule_weight + ml_pred.probability_down * ml_weight)
        optimized_prob_flat = 1 - optimized_prob_up - optimized_prob_down
        
        # Normalize
        total = optimized_prob_up + optimized_prob_down + optimized_prob_flat
        if total > 0:
            optimized_prob_up /= total
            optimized_prob_down /= total
            optimized_prob_flat /= total
        
        # Determine optimized direction
        if optimized_prob_up > max(optimized_prob_down, optimized_prob_flat):
            optimized_direction = "BULLISH"
        elif optimized_prob_down > max(optimized_prob_up, optimized_prob_flat):
            optimized_direction = "BEARISH"
        else:
            optimized_direction = "NEUTRAL"
        
        # Adjust expected move based on ML direction agreement
        if ml_pred.predicted_direction == "UP" and rb_expected_move > 0:
            # ML agrees with bullish, boost expected move
            optimized_move = rb_expected_move * 1.2
        elif ml_pred.predicted_direction == "DOWN" and rb_expected_move < 0:
            # ML agrees with bearish, boost expected move
            optimized_move = rb_expected_move * 1.2
        elif ml_pred.predicted_direction == "FLAT":
            # ML predicts flat, reduce expected move
            optimized_move = rb_expected_move * 0.7
        else:
            # Disagreement, reduce confidence in move
            optimized_move = rb_expected_move * 0.8
        
        # Combine confidence
        optimized_confidence = (rb_confidence * rule_weight + ml_pred.confidence * ml_weight)
        
        # Build optimized result
        optimized = {
            **rule_based_prediction,
            'prob_up': optimized_prob_up,
            'prob_down': optimized_prob_down,
            'prob_neutral': optimized_prob_flat,
            'expected_move_pct': optimized_move,
            'expected_direction': optimized_direction,
            'prediction_confidence': optimized_confidence,
            'ml_prediction': {
                'direction': ml_pred.predicted_direction,
                'prob_up': ml_pred.probability_up,
                'prob_down': ml_pred.probability_down,
                'prob_flat': ml_pred.probability_flat,
                'confidence': ml_pred.confidence,
                'model_type': ml_pred.model_type,
                'top_features': ml_pred.feature_importance
            },
            'optimization_applied': True
        }
        
        return optimized
    
    def save_model(self, index_name: str):
        """Save trained model to disk"""
        if index_name not in self.is_fitted or not self.is_fitted[index_name]:
            logger.warning(f"No trained model for {index_name}")
            return False
        
        try:
            model_path = os.path.join(self.model_dir, f'{index_name.lower()}_model.joblib')
            scaler_path = os.path.join(self.model_dir, f'{index_name.lower()}_scaler.joblib')
            
            model_data = {
                'model': self.models[index_name],
                'feature_names': self.feature_names,
                'model_type': self.model_type
            }
            
            joblib.dump(model_data, model_path)
            joblib.dump(self.scalers[index_name], scaler_path)
            
            logger.info(f"Model saved for {index_name}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def _load_model(self, index_name: str) -> bool:
        """Load trained model from disk"""
        try:
            model_path = os.path.join(self.model_dir, f'{index_name.lower()}_model.joblib')
            scaler_path = os.path.join(self.model_dir, f'{index_name.lower()}_scaler.joblib')
            
            if not os.path.exists(model_path) or not os.path.exists(scaler_path):
                return False
            
            model_data = joblib.load(model_path)
            self.models[index_name] = model_data['model']
            self.feature_names = model_data['feature_names']
            self.model_type = model_data['model_type']
            self.scalers[index_name] = joblib.load(scaler_path)
            self.is_fitted[index_name] = True
            
            logger.info(f"Model loaded for {index_name}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def get_model_status(self) -> Dict:
        """Get status of all trained models"""
        return {
            index: {
                'is_fitted': self.is_fitted.get(index, False),
                'model_type': self.model_type
            }
            for index in ['NIFTY', 'BANKNIFTY', 'SENSEX', 'FINNIFTY']
        }


# Global optimizer instance
_ml_optimizer = None

def get_ml_optimizer(model_type: str = "xgboost") -> IndexMLOptimizer:
    """Get or create ML optimizer instance"""
    global _ml_optimizer
    if _ml_optimizer is None:
        _ml_optimizer = IndexMLOptimizer(model_type)
    return _ml_optimizer
