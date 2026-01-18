"""
Machine Learning Module for Price Prediction
Implements various ML models for options and stock price forecasting
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import lightgbm as lgb
import joblib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FeatureEngineering:
    """Create features for ML models"""
    
    @staticmethod
    def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicator features"""
        df = df.copy()
        
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        for period in [5, 10, 20, 50]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        
        # Volatility
        df['volatility_10'] = df['returns'].rolling(window=10).std()
        df['volatility_20'] = df['returns'].rolling(window=20).std()
        
        # RSI
        df['rsi_14'] = FeatureEngineering._calculate_rsi(df['close'], 14)
        
        # MACD
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (2 * bb_std)
        df['bb_lower'] = df['bb_middle'] - (2 * bb_std)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # Volume features
        if 'volume' in df.columns:
            df['volume_sma_10'] = df['volume'].rolling(window=10).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma_10']
        
        # Price momentum
        for period in [1, 5, 10, 20]:
            df[f'momentum_{period}'] = df['close'].pct_change(periods=period)
        
        return df
    
    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features"""
        df = df.copy()
        
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['day_of_month'] = df.index.day
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        
        # Market session features (Indian market: 9:15 AM - 3:30 PM IST)
        df['is_opening_hour'] = (df['hour'] == 9).astype(int)
        df['is_closing_hour'] = (df['hour'] == 15).astype(int)
        df['is_mid_session'] = ((df['hour'] >= 11) & (df['hour'] <= 13)).astype(int)
        
        return df
    
    @staticmethod
    def add_lag_features(
        df: pd.DataFrame,
        target_col: str = 'close',
        lags: List[int] = [1, 2, 3, 5, 10]
    ) -> pd.DataFrame:
        """Add lagged features"""
        df = df.copy()
        
        for lag in lags:
            df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
        
        return df


class PricePredictor:
    """ML-based price prediction"""
    
    def __init__(self, model_type: str = "xgboost"):
        """
        Initialize predictor
        
        Args:
            model_type: "xgboost", "lightgbm", "random_forest", "gradient_boosting"
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_fitted = False
    
    def _create_model(self):
        """Create the ML model based on type"""
        if self.model_type == "xgboost":
            return xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
        elif self.model_type == "lightgbm":
            return lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
        elif self.model_type == "random_forest":
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == "gradient_boosting":
            return GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def prepare_features(
        self,
        df: pd.DataFrame,
        target_col: str = 'close'
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features and target for training
        
        Returns:
            Tuple of (features_df, target_series)
        """
        # Add all features
        df = FeatureEngineering.add_technical_indicators(df)
        df = FeatureEngineering.add_time_features(df)
        df = FeatureEngineering.add_lag_features(df, target_col)
        
        # Create target (next period's price)
        df['target'] = df[target_col].shift(-1)
        
        # Drop rows with NaN
        df = df.dropna()
        
        # Separate features and target
        exclude_cols = ['target', 'open', 'high', 'low', 'close', 'volume']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        X = df[feature_cols]
        y = df['target']
        
        self.feature_names = feature_cols
        
        return X, y
    
    def train(
        self,
        df: pd.DataFrame,
        target_col: str = 'close',
        test_size: float = 0.2
    ) -> Dict:
        """
        Train the model
        
        Returns:
            Dict with training metrics
        """
        logger.info(f"Training {self.model_type} model...")
        
        # Prepare features
        X, y = self.prepare_features(df, target_col)
        
        # Split data (time series split - no shuffle)
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = self._create_model()
        self.model.fit(X_train_scaled, y_train)
        self.is_fitted = True
        
        # Evaluate
        train_pred = self.model.predict(X_train_scaled)
        test_pred = self.model.predict(X_test_scaled)
        
        metrics = {
            "train_rmse": np.sqrt(mean_squared_error(y_train, train_pred)),
            "test_rmse": np.sqrt(mean_squared_error(y_test, test_pred)),
            "train_mae": mean_absolute_error(y_train, train_pred),
            "test_mae": mean_absolute_error(y_test, test_pred),
            "train_r2": r2_score(y_train, train_pred),
            "test_r2": r2_score(y_test, test_pred),
            "train_samples": len(X_train),
            "test_samples": len(X_test)
        }
        
        logger.info(f"Model trained. Test RMSE: {metrics['test_rmse']:.4f}, "
                   f"Test R2: {metrics['test_r2']:.4f}")
        
        return metrics
    
    def predict(self, df: pd.DataFrame, target_col: str = 'close') -> np.ndarray:
        """
        Make predictions on new data
        
        Returns:
            Array of predictions
        """
        if not self.is_fitted:
            raise Exception("Model not trained. Call train() first.")
        
        # Prepare features (without target)
        df_processed = FeatureEngineering.add_technical_indicators(df)
        df_processed = FeatureEngineering.add_time_features(df_processed)
        df_processed = FeatureEngineering.add_lag_features(df_processed, target_col)
        df_processed = df_processed.dropna()
        
        X = df_processed[self.feature_names]
        X_scaled = self.scaler.transform(X)
        
        predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def predict_next(
        self,
        df: pd.DataFrame,
        target_col: str = 'close',
        periods: int = 1
    ) -> List[float]:
        """
        Predict next N periods
        
        Returns:
            List of predicted prices
        """
        predictions = []
        df_temp = df.copy()
        
        for _ in range(periods):
            pred = self.predict(df_temp, target_col)
            predictions.append(pred[-1])
            
            # Add prediction as new row for next iteration
            # This is a simplified approach; in production, you'd need to
            # properly construct all features for the new row
            
        return predictions
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance"""
        if not self.is_fitted:
            raise Exception("Model not trained")
        
        if hasattr(self.model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            return importance_df
        else:
            return pd.DataFrame()
    
    def save_model(self, filepath: str):
        """Save trained model"""
        if not self.is_fitted:
            raise Exception("Model not trained")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_type': self.model_type
        }
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model"""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.model_type = model_data['model_type']
        self.is_fitted = True
        logger.info(f"Model loaded from {filepath}")


# Global predictor instance
price_predictor = PricePredictor(model_type="xgboost")
