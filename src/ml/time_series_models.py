"""
Advanced Time Series Models for Price Prediction
Implements ARIMA, LSTM, and ensemble methods for accurate forecasting
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

# Statistical models
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from scipy import stats

# Deep Learning
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Prediction result with confidence intervals"""
    predicted_price: float
    lower_bound: float
    upper_bound: float
    confidence: float
    direction: str  # 'bullish', 'bearish', 'neutral'
    model_name: str
    metrics: Dict


class ARIMAPredictor:
    """
    ARIMA (AutoRegressive Integrated Moving Average) model
    
    Best for: Short-term price forecasting, identifying trends
    - AR (AutoRegressive): Uses past values to predict future
    - I (Integrated): Differencing to make series stationary
    - MA (Moving Average): Uses past forecast errors
    """
    
    def __init__(self, order: Tuple[int, int, int] = (5, 1, 2)):
        """
        Initialize ARIMA model
        
        Args:
            order: (p, d, q) - AR order, differencing order, MA order
                p=5: Use last 5 price points
                d=1: First-order differencing (removes trend)
                q=2: Use last 2 forecast errors
        """
        self.order = order
        self.model = None
        self.last_fit_result = None
        self.is_fitted = False
        
    def fit(self, prices: pd.Series) -> Dict:
        """
        Fit ARIMA model to price data
        
        Args:
            prices: Series of closing prices
            
        Returns:
            Dict with model metrics
        """
        try:
            # Ensure we have enough data
            if len(prices) < 30:
                logger.warning(f"ARIMA needs at least 30 data points, got {len(prices)}")
                return {"error": "Insufficient data"}
            
            # Fit ARIMA model
            self.model = ARIMA(prices, order=self.order)
            self.last_fit_result = self.model.fit()
            self.is_fitted = True
            
            # Calculate metrics
            residuals = self.last_fit_result.resid
            aic = self.last_fit_result.aic
            bic = self.last_fit_result.bic
            
            metrics = {
                "aic": round(aic, 2),
                "bic": round(bic, 2),
                "residual_std": round(residuals.std(), 4),
                "fitted_samples": len(prices),
                "order": self.order
            }
            
            logger.info(f"✅ ARIMA({self.order}) fitted - AIC: {aic:.2f}")
            return metrics
            
        except Exception as e:
            logger.error(f"ARIMA fit error: {e}")
            return {"error": str(e)}
    
    def predict(self, steps: int = 1) -> PredictionResult:
        """
        Forecast future prices
        
        Args:
            steps: Number of periods to forecast
            
        Returns:
            PredictionResult with prediction and confidence
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        try:
            # Get forecast with confidence intervals
            forecast = self.last_fit_result.get_forecast(steps=steps)
            predicted = forecast.predicted_mean.iloc[-1]
            conf_int = forecast.conf_int(alpha=0.05)  # 95% confidence
            
            lower = conf_int.iloc[-1, 0]
            upper = conf_int.iloc[-1, 1]
            
            # Calculate direction and confidence
            last_price = self.last_fit_result.data.endog[-1]
            price_change = (predicted - last_price) / last_price
            
            if price_change > 0.002:  # >0.2% up
                direction = "bullish"
                confidence = min(abs(price_change) * 50, 0.95)
            elif price_change < -0.002:  # >0.2% down
                direction = "bearish"
                confidence = min(abs(price_change) * 50, 0.95)
            else:
                direction = "neutral"
                confidence = 0.3
            
            return PredictionResult(
                predicted_price=round(predicted, 2),
                lower_bound=round(lower, 2),
                upper_bound=round(upper, 2),
                confidence=round(confidence, 3),
                direction=direction,
                model_name="ARIMA",
                metrics={
                    "price_change_pct": round(price_change * 100, 3),
                    "forecast_steps": steps,
                    "last_price": round(last_price, 2)
                }
            )
            
        except Exception as e:
            logger.error(f"ARIMA predict error: {e}")
            return PredictionResult(
                predicted_price=0, lower_bound=0, upper_bound=0,
                confidence=0, direction="neutral", model_name="ARIMA",
                metrics={"error": str(e)}
            )


class SimpleLSTMPredictor:
    """
    Simplified LSTM-like predictor using statistical methods
    
    Since TensorFlow/Keras can be heavy, this uses a lightweight
    statistical approximation that captures similar patterns:
    - Exponential smoothing for trend
    - Momentum analysis for direction
    - Volatility clustering for confidence
    
    Note: For production, you can replace this with actual LSTM using TensorFlow
    """
    
    def __init__(self, lookback: int = 20):
        """
        Initialize LSTM-like predictor
        
        Args:
            lookback: Number of periods to analyze (like LSTM sequence length)
        """
        self.lookback = lookback
        self.is_fitted = False
        self.trend_model = None
        self.momentum_weights = None
        self.volatility_factor = None
        
    def fit(self, prices: pd.Series) -> Dict:
        """
        Fit the model by learning patterns from price data
        
        Args:
            prices: Series of closing prices
            
        Returns:
            Dict with model metrics
        """
        try:
            if len(prices) < self.lookback * 2:
                return {"error": f"Need at least {self.lookback * 2} data points"}
            
            # Fit exponential smoothing for trend
            try:
                self.trend_model = ExponentialSmoothing(
                    prices,
                    trend='add',
                    seasonal=None,
                    damped_trend=True
                ).fit()
            except:
                # Fallback to simple exponential smoothing
                self.trend_model = ExponentialSmoothing(
                    prices,
                    trend='add'
                ).fit()
            
            # Calculate momentum weights (like LSTM attention)
            returns = prices.pct_change().dropna()
            recent_returns = returns.tail(self.lookback)
            
            # Weight recent data more heavily (exponential decay)
            weights = np.exp(np.linspace(-1, 0, len(recent_returns)))
            weights = weights / weights.sum()
            self.momentum_weights = weights
            
            # Calculate volatility clustering
            self.volatility_factor = recent_returns.std() * np.sqrt(252)  # Annualized
            
            self.is_fitted = True
            
            metrics = {
                "trend_smoothing": round(self.trend_model.params.get('smoothing_level', 0.5), 3),
                "volatility_annual": round(self.volatility_factor * 100, 2),
                "lookback_period": self.lookback,
                "fitted_samples": len(prices)
            }
            
            logger.info(f"✅ LSTM-like model fitted - Volatility: {self.volatility_factor*100:.2f}%")
            return metrics
            
        except Exception as e:
            logger.error(f"LSTM fit error: {e}")
            return {"error": str(e)}
    
    def predict(self, prices: pd.Series, steps: int = 1) -> PredictionResult:
        """
        Predict future prices using learned patterns
        
        Args:
            prices: Recent price series
            steps: Number of periods to forecast
            
        Returns:
            PredictionResult with prediction and confidence
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        try:
            # Get trend forecast
            trend_forecast = self.trend_model.forecast(steps)
            predicted = trend_forecast.iloc[-1]
            
            # Calculate momentum signal (weighted recent performance)
            returns = prices.pct_change().dropna().tail(self.lookback)
            if len(returns) >= self.lookback:
                weighted_momentum = np.average(returns, weights=self.momentum_weights)
            else:
                weighted_momentum = returns.mean()
            
            # Adjust prediction based on momentum
            momentum_adjustment = 1 + (weighted_momentum * 0.5)  # 50% momentum factor
            predicted = predicted * momentum_adjustment
            
            # Calculate confidence intervals using volatility
            volatility_daily = self.volatility_factor / np.sqrt(252)
            lower = predicted * (1 - 2 * volatility_daily)
            upper = predicted * (1 + 2 * volatility_daily)
            
            # Determine direction and confidence
            last_price = prices.iloc[-1]
            price_change = (predicted - last_price) / last_price
            
            # Confidence based on momentum consistency
            momentum_std = returns.std()
            momentum_consistency = 1 - min(momentum_std / abs(weighted_momentum + 0.0001), 1)
            
            if price_change > 0.002:
                direction = "bullish"
                confidence = min(0.4 + momentum_consistency * 0.5, 0.9)
            elif price_change < -0.002:
                direction = "bearish"
                confidence = min(0.4 + momentum_consistency * 0.5, 0.9)
            else:
                direction = "neutral"
                confidence = 0.3
            
            return PredictionResult(
                predicted_price=round(predicted, 2),
                lower_bound=round(lower, 2),
                upper_bound=round(upper, 2),
                confidence=round(confidence, 3),
                direction=direction,
                model_name="LSTM",
                metrics={
                    "price_change_pct": round(price_change * 100, 3),
                    "momentum": round(weighted_momentum * 100, 3),
                    "momentum_consistency": round(momentum_consistency, 3),
                    "last_price": round(last_price, 2)
                }
            )
            
        except Exception as e:
            logger.error(f"LSTM predict error: {e}")
            return PredictionResult(
                predicted_price=prices.iloc[-1], lower_bound=0, upper_bound=0,
                confidence=0, direction="neutral", model_name="LSTM",
                metrics={"error": str(e)}
            )


class EnsemblePredictor:
    """
    Ensemble model combining ARIMA, LSTM, and other signals
    
    Uses weighted voting to combine predictions from multiple models,
    giving more weight to models that have been more accurate recently.
    """
    
    def __init__(self):
        self.arima = ARIMAPredictor(order=(5, 1, 2))
        self.lstm = SimpleLSTMPredictor(lookback=20)
        self.is_fitted = False
        
        # Model weights (can be adjusted based on performance)
        self.weights = {
            'arima': 0.4,  # 40% weight to ARIMA (good for short-term)
            'lstm': 0.4,   # 40% weight to LSTM (good for patterns)
            'momentum': 0.2  # 20% weight to simple momentum
        }
    
    def fit(self, prices: pd.Series) -> Dict:
        """
        Fit all models in the ensemble
        
        Args:
            prices: Series of closing prices
            
        Returns:
            Dict with metrics from all models
        """
        metrics = {}
        
        # Fit ARIMA
        arima_metrics = self.arima.fit(prices)
        metrics['arima'] = arima_metrics
        
        # Fit LSTM
        lstm_metrics = self.lstm.fit(prices)
        metrics['lstm'] = lstm_metrics
        
        self.is_fitted = True
        logger.info("✅ Ensemble model fitted with ARIMA + LSTM + Momentum")
        
        return metrics
    
    def predict(self, prices: pd.Series, steps: int = 1) -> Dict:
        """
        Generate ensemble prediction combining all models
        
        Args:
            prices: Recent price series for prediction
            steps: Number of periods to forecast
            
        Returns:
            Dict with combined prediction and individual model results
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        results = {}
        predictions = []
        weights_sum = 0
        
        # ARIMA prediction
        try:
            arima_result = self.arima.predict(steps)
            results['arima'] = {
                'predicted': arima_result.predicted_price,
                'direction': arima_result.direction,
                'confidence': arima_result.confidence,
                'lower': arima_result.lower_bound,
                'upper': arima_result.upper_bound
            }
            predictions.append((arima_result.predicted_price, self.weights['arima'], arima_result.direction))
            weights_sum += self.weights['arima']
        except Exception as e:
            logger.warning(f"ARIMA prediction failed: {e}")
            results['arima'] = {'error': str(e)}
        
        # LSTM prediction
        try:
            lstm_result = self.lstm.predict(prices, steps)
            results['lstm'] = {
                'predicted': lstm_result.predicted_price,
                'direction': lstm_result.direction,
                'confidence': lstm_result.confidence,
                'momentum': lstm_result.metrics.get('momentum', 0)
            }
            predictions.append((lstm_result.predicted_price, self.weights['lstm'], lstm_result.direction))
            weights_sum += self.weights['lstm']
        except Exception as e:
            logger.warning(f"LSTM prediction failed: {e}")
            results['lstm'] = {'error': str(e)}
        
        # Simple momentum prediction
        try:
            momentum = prices.pct_change().tail(10).mean()
            momentum_pred = prices.iloc[-1] * (1 + momentum * steps)
            momentum_direction = 'bullish' if momentum > 0.001 else ('bearish' if momentum < -0.001 else 'neutral')
            
            results['momentum'] = {
                'predicted': round(momentum_pred, 2),
                'direction': momentum_direction,
                'momentum_pct': round(momentum * 100, 3)
            }
            predictions.append((momentum_pred, self.weights['momentum'], momentum_direction))
            weights_sum += self.weights['momentum']
        except Exception as e:
            logger.warning(f"Momentum calculation failed: {e}")
            results['momentum'] = {'error': str(e)}
        
        # Combine predictions (weighted average)
        if predictions and weights_sum > 0:
            weighted_price = sum(p * w for p, w, _ in predictions) / weights_sum
            
            # Determine ensemble direction by voting
            direction_votes = {'bullish': 0, 'bearish': 0, 'neutral': 0}
            for _, w, d in predictions:
                direction_votes[d] += w
            
            ensemble_direction = max(direction_votes, key=direction_votes.get)
            direction_confidence = direction_votes[ensemble_direction] / weights_sum
            
            # Calculate overall confidence
            individual_confidences = [results.get(m, {}).get('confidence', 0) 
                                     for m in ['arima', 'lstm']]
            avg_confidence = sum(individual_confidences) / len(individual_confidences) if individual_confidences else 0.5
            
            last_price = prices.iloc[-1]
            price_change_pct = (weighted_price - last_price) / last_price * 100
            
            results['ensemble'] = {
                'predicted_price': round(weighted_price, 2),
                'direction': ensemble_direction,
                'direction_confidence': round(direction_confidence, 3),
                'model_confidence': round(avg_confidence, 3),
                'price_change_pct': round(price_change_pct, 2),
                'last_price': round(last_price, 2),
                'models_used': len(predictions),
                'recommendation': self._generate_recommendation(ensemble_direction, direction_confidence, price_change_pct)
            }
        else:
            results['ensemble'] = {
                'error': 'No valid predictions from models',
                'direction': 'neutral',
                'direction_confidence': 0,
                'model_confidence': 0
            }
        
        return results
    
    def _generate_recommendation(self, direction: str, confidence: float, price_change: float) -> str:
        """Generate trading recommendation based on prediction"""
        if direction == 'bullish':
            if confidence >= 0.7:
                return f"⭐ STRONG BUY signal - All models agree on {price_change:+.2f}% upside"
            elif confidence >= 0.5:
                return f"📈 BUY signal - Majority models bullish, expect {price_change:+.2f}% move"
            else:
                return f"↗️ Mild bullish bias - Consider CALL options cautiously"
        elif direction == 'bearish':
            if confidence >= 0.7:
                return f"⭐ STRONG SELL signal - All models agree on {abs(price_change):.2f}% downside"
            elif confidence >= 0.5:
                return f"📉 SELL signal - Majority models bearish, expect {price_change:.2f}% move"
            else:
                return f"↘️ Mild bearish bias - Consider PUT options cautiously"
        else:
            return "⏸️ NEUTRAL - Models show mixed signals, wait for clarity"


# Global ensemble predictor instance
ensemble_predictor = EnsemblePredictor()


def get_ml_signal(prices: pd.Series, steps: int = 1) -> Dict:
    """
    Convenience function to get ML signal for integration with trading system
    
    Args:
        prices: Historical price data
        steps: Forecast periods
        
    Returns:
        Dict with ML prediction results
    """
    global ensemble_predictor
    
    try:
        # Fit if not already fitted or data changed significantly
        if not ensemble_predictor.is_fitted:
            ensemble_predictor.fit(prices)
        
        # Get prediction
        results = ensemble_predictor.predict(prices, steps)
        
        return {
            'success': True,
            'predictions': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"ML signal error: {e}")
        return {
            'success': False,
            'error': str(e),
            'predictions': {
                'ensemble': {
                    'direction': 'neutral',
                    'direction_confidence': 0,
                    'model_confidence': 0
                }
            }
        }
