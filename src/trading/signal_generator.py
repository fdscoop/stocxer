"""
Trading Signal Generator and Decision Engine
Combines ICT analysis, ML predictions, and options Greeks
"""
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, date
import logging

from src.analytics.ict_analysis import ict_analyzer
from src.analytics.options_pricing import options_pricer
from src.ml.price_prediction import price_predictor

logger = logging.getLogger(__name__)


class SignalGenerator:
    """Generate trading signals by combining multiple analysis methods"""
    
    def __init__(self):
        self.min_confidence = 0.6  # Minimum confidence to generate signal
        self.weights = {
            'ict': 0.4,
            'ml': 0.3,
            'options': 0.3
        }
    
    def generate_comprehensive_signal(
        self,
        historical_data: pd.DataFrame,
        current_price: float,
        option_data: Optional[Dict] = None
    ) -> Dict:
        """
        Generate comprehensive trading signal
        
        Args:
            historical_data: Historical OHLCV data
            current_price: Current underlying price
            option_data: Optional dict with option chain data
            
        Returns:
            Dict with signal, confidence, and detailed analysis
        """
        signals = {}
        
        # 1. ICT Analysis
        try:
            ict_signal = ict_analyzer.generate_ict_signal(
                historical_data,
                current_price
            )
            signals['ict'] = ict_signal
            logger.info(f"ICT Signal: {ict_signal['signal']} (confidence: {ict_signal['confidence']})")
        except Exception as e:
            logger.error(f"ICT analysis failed: {e}")
            signals['ict'] = {'signal': 'neutral', 'confidence': 0.0}
        
        # 2. ML Prediction
        try:
            if price_predictor.is_fitted:
                predictions = price_predictor.predict_next(
                    historical_data,
                    periods=1
                )
                predicted_price = predictions[0]
                price_change_pct = (predicted_price - current_price) / current_price
                
                # Generate signal based on prediction
                if price_change_pct > 0.01:  # >1% up
                    ml_signal = 'buy'
                    ml_confidence = min(abs(price_change_pct) * 10, 1.0)
                elif price_change_pct < -0.01:  # >1% down
                    ml_signal = 'sell'
                    ml_confidence = min(abs(price_change_pct) * 10, 1.0)
                else:
                    ml_signal = 'neutral'
                    ml_confidence = 0.0
                
                signals['ml'] = {
                    'signal': ml_signal,
                    'confidence': ml_confidence,
                    'predicted_price': predicted_price,
                    'expected_change_pct': price_change_pct * 100
                }
                logger.info(f"ML Signal: {ml_signal} (predicted: {predicted_price:.2f}, "
                          f"change: {price_change_pct*100:.2f}%)")
            else:
                signals['ml'] = {'signal': 'neutral', 'confidence': 0.0}
                logger.warning("ML model not trained, skipping ML prediction")
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            signals['ml'] = {'signal': 'neutral', 'confidence': 0.0}
        
        # 3. Options Analysis (if option data provided)
        if option_data:
            try:
                options_signal = self._analyze_options(option_data, current_price)
                signals['options'] = options_signal
                logger.info(f"Options Signal: {options_signal['signal']} "
                          f"(confidence: {options_signal['confidence']})")
            except Exception as e:
                logger.error(f"Options analysis failed: {e}")
                signals['options'] = {'signal': 'neutral', 'confidence': 0.0}
        else:
            signals['options'] = {'signal': 'neutral', 'confidence': 0.0}
        
        # Combine signals
        final_signal = self._combine_signals(signals)
        
        return final_signal
    
    def _analyze_options(
        self,
        option_data: Dict,
        current_price: float
    ) -> Dict:
        """
        Analyze options data for trading signals
        
        Args:
            option_data: Dict with option chain information
            current_price: Current underlying price
            
        Returns:
            Dict with signal and confidence
        """
        # This is a placeholder for options analysis
        # You would typically analyze:
        # - Put/Call ratio
        # - Open interest distribution
        # - IV skew
        # - Max pain theory
        # - Greeks positioning
        
        signal = 'neutral'
        confidence = 0.0
        reasons = []
        
        # Example: Analyze Put/Call ratio
        if 'put_call_ratio' in option_data:
            pcr = option_data['put_call_ratio']
            if pcr > 1.5:  # High put activity - potentially bullish
                signal = 'buy'
                confidence = 0.6
                reasons.append(f"High Put/Call ratio: {pcr:.2f}")
            elif pcr < 0.7:  # High call activity - potentially bearish
                signal = 'sell'
                confidence = 0.6
                reasons.append(f"Low Put/Call ratio: {pcr:.2f}")
        
        # Analyze IV percentile
        if 'iv_percentile' in option_data:
            iv_pct = option_data['iv_percentile']
            if iv_pct > 80:
                reasons.append(f"High IV percentile: {iv_pct}% - volatility overpriced")
                confidence += 0.2
            elif iv_pct < 20:
                reasons.append(f"Low IV percentile: {iv_pct}% - volatility underpriced")
                confidence += 0.2
        
        return {
            'signal': signal,
            'confidence': min(confidence, 1.0),
            'reasons': reasons
        }
    
    def _combine_signals(self, signals: Dict) -> Dict:
        """
        Combine multiple signals into final recommendation
        
        Args:
            signals: Dict with ICT, ML, and options signals
            
        Returns:
            Dict with final signal and confidence
        """
        # Calculate weighted score
        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0
        
        for source, weight in self.weights.items():
            if source in signals:
                signal_data = signals[source]
                confidence = signal_data.get('confidence', 0.0)
                signal = signal_data.get('signal', 'neutral')
                
                if signal == 'buy':
                    buy_score += weight * confidence
                elif signal == 'sell':
                    sell_score += weight * confidence
                
                total_weight += weight
        
        # Normalize scores
        if total_weight > 0:
            buy_score /= total_weight
            sell_score /= total_weight
        
        # Determine final signal
        if buy_score > sell_score and buy_score >= self.min_confidence:
            final_signal = 'buy'
            final_confidence = buy_score
        elif sell_score > buy_score and sell_score >= self.min_confidence:
            final_signal = 'sell'
            final_confidence = sell_score
        else:
            final_signal = 'neutral'
            final_confidence = max(buy_score, sell_score)
        
        return {
            'signal': final_signal,
            'confidence': round(final_confidence, 2),
            'buy_score': round(buy_score, 2),
            'sell_score': round(sell_score, 2),
            'component_signals': signals,
            'timestamp': datetime.now().isoformat()
        }
    
    def recommend_option_strategy(
        self,
        signal: Dict,
        spot_price: float,
        option_chain: List[Dict],
        capital: float = 100000,
        risk_tolerance: str = 'moderate'
    ) -> Dict:
        """
        Recommend specific option strategy based on signal
        
        Args:
            signal: Trading signal from generate_comprehensive_signal
            spot_price: Current underlying price
            option_chain: List of available options
            capital: Available capital
            risk_tolerance: 'conservative', 'moderate', 'aggressive'
            
        Returns:
            Dict with recommended strategy and positions
        """
        recommendation = {
            'signal': signal['signal'],
            'confidence': signal['confidence'],
            'strategy': None,
            'positions': [],
            'risk_reward': None,
            'max_risk': None,
            'max_profit': None
        }
        
        if signal['signal'] == 'neutral' or signal['confidence'] < self.min_confidence:
            recommendation['strategy'] = 'Stay out - No clear signal'
            return recommendation
        
        # Bullish signal
        if signal['signal'] == 'buy':
            if risk_tolerance == 'aggressive':
                recommendation['strategy'] = 'Long Call'
                recommendation['description'] = 'Buy ATM or slightly OTM call option'
            elif risk_tolerance == 'moderate':
                recommendation['strategy'] = 'Bull Call Spread'
                recommendation['description'] = 'Buy ATM call, sell OTM call'
            else:
                recommendation['strategy'] = 'Cash Secured Put Selling'
                recommendation['description'] = 'Sell OTM puts to collect premium'
        
        # Bearish signal
        else:  # sell signal
            if risk_tolerance == 'aggressive':
                recommendation['strategy'] = 'Long Put'
                recommendation['description'] = 'Buy ATM or slightly OTM put option'
            elif risk_tolerance == 'moderate':
                recommendation['strategy'] = 'Bear Put Spread'
                recommendation['description'] = 'Buy ATM put, sell OTM put'
            else:
                recommendation['strategy'] = 'Covered Call'
                recommendation['description'] = 'Sell OTM calls if holding underlying'
        
        # Calculate position sizing based on capital and risk
        max_risk_pct = {
            'conservative': 0.02,
            'moderate': 0.05,
            'aggressive': 0.10
        }
        max_risk = capital * max_risk_pct.get(risk_tolerance, 0.05)
        recommendation['max_risk'] = max_risk
        
        return recommendation


class RiskManager:
    """Manage trading risk and position sizing"""
    
    def __init__(self, max_position_size: float = 100000):
        self.max_position_size = max_position_size
        self.max_loss_per_trade = 0.02  # 2% max loss per trade
    
    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        confidence: float
    ) -> int:
        """
        Calculate position size based on risk parameters
        
        Returns:
            Number of contracts/shares
        """
        # Risk amount
        risk_amount = account_balance * self.max_loss_per_trade * confidence
        
        # Risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)
        
        if risk_per_unit == 0:
            return 0
        
        # Calculate position size
        position_size = int(risk_amount / risk_per_unit)
        
        # Apply maximum position size limit
        max_units = int(self.max_position_size / entry_price)
        position_size = min(position_size, max_units)
        
        return position_size
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        signal_type: str,
        atr: Optional[float] = None,
        support_resistance: Optional[float] = None
    ) -> float:
        """
        Calculate stop loss level
        
        Args:
            entry_price: Entry price
            signal_type: 'buy' or 'sell'
            atr: Average True Range (for ATR-based stops)
            support_resistance: Support/resistance level
            
        Returns:
            Stop loss price
        """
        if support_resistance:
            return support_resistance
        
        # Use ATR if available (2x ATR stop)
        if atr:
            if signal_type == 'buy':
                return entry_price - (2 * atr)
            else:
                return entry_price + (2 * atr)
        
        # Default: 2% stop
        if signal_type == 'buy':
            return entry_price * 0.98
        else:
            return entry_price * 1.02
    
    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        risk_reward_ratio: float = 2.0
    ) -> float:
        """Calculate take profit level based on risk-reward ratio"""
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward_ratio
        
        if entry_price > stop_loss:  # Long position
            return entry_price + reward
        else:  # Short position
            return entry_price - reward


# Global instances
signal_generator = SignalGenerator()
risk_manager = RiskManager()
