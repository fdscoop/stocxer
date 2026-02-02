"""
Enhanced ML Signal Service
===========================

This service integrates all the new ML prediction modules:
1. XGBoost Direction Predictor
2. Speed Predictor
3. IV Predictor
4. Theta Scenario Planner
5. Options P&L Simulator

Provides a unified interface for the main.py signal generation.

Author: TradeWise ML Team
Created: 2026-02-02
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import pytz
from dataclasses import asdict

logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')

# Import all ML modules
try:
    from src.ml.speed_predictor import SpeedPredictor, SpeedPrediction, SpeedCategory
    SPEED_PREDICTOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Speed predictor not available: {e}")
    SPEED_PREDICTOR_AVAILABLE = False

try:
    from src.ml.iv_predictor import IVPredictor, IVPrediction, IVDirection
    IV_PREDICTOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"IV predictor not available: {e}")
    IV_PREDICTOR_AVAILABLE = False

try:
    from src.ml.theta_scenario_planner import ThetaScenarioPlanner, ThetaScenarioResult
    THETA_PLANNER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Theta planner not available: {e}")
    THETA_PLANNER_AVAILABLE = False

try:
    from src.ml.xgboost_direction import XGBoostDirectionPredictor, DirectionPrediction, Direction
    DIRECTION_PREDICTOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"XGBoost direction predictor not available: {e}")
    DIRECTION_PREDICTOR_AVAILABLE = False

try:
    from src.ml.options_simulator import OptionsPnLSimulator, OptionsSimulationResult
    SIMULATOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Options simulator not available: {e}")
    SIMULATOR_AVAILABLE = False


class EnhancedMLService:
    """
    Unified ML service that provides enhanced predictions for options trading.
    
    Combines:
    - Direction prediction (XGBoost)
    - Speed prediction (rule-based)
    - IV prediction (rule-based)
    - Theta scenario planning
    - Full P&L simulation
    """
    
    def __init__(self):
        # Initialize all predictors
        if SPEED_PREDICTOR_AVAILABLE:
            self.speed_predictor = SpeedPredictor()
            logger.info("✅ Speed predictor initialized")
        else:
            self.speed_predictor = None
            
        if IV_PREDICTOR_AVAILABLE:
            self.iv_predictor = IVPredictor()
            logger.info("✅ IV predictor initialized")
        else:
            self.iv_predictor = None
            
        if THETA_PLANNER_AVAILABLE:
            self.theta_planner = ThetaScenarioPlanner()
            logger.info("✅ Theta scenario planner initialized")
        else:
            self.theta_planner = None
            
        if DIRECTION_PREDICTOR_AVAILABLE:
            self.direction_predictor = XGBoostDirectionPredictor()
            logger.info("✅ XGBoost direction predictor initialized")
        else:
            self.direction_predictor = None
            
        if SIMULATOR_AVAILABLE:
            self.simulator = OptionsPnLSimulator()
            logger.info("✅ Options P&L simulator initialized")
        else:
            self.simulator = None
    
    def get_enhanced_prediction(
        self,
        option_type: str,
        strike: float,
        premium: float,
        spot_price: float,
        current_iv: float,
        days_to_expiry: float,
        price_history: List[float],
        volume_history: Optional[List[float]] = None,
        iv_history: Optional[List[float]] = None,
        timestamp: Optional[datetime] = None,
        is_expiry_day: bool = False,
    ) -> Dict[str, Any]:
        """
        Get comprehensive ML-enhanced prediction for an option trade.
        
        Returns a dictionary with:
        - direction_prediction: XGBoost direction forecast
        - speed_prediction: Expected speed of price movement
        - iv_prediction: Expected IV direction
        - theta_scenarios: Time-based P&L scenarios
        - simulation_result: Full P&L simulation with grade
        """
        if timestamp is None:
            timestamp = datetime.now(IST)
        
        result = {
            'timestamp': timestamp.isoformat(),
            'available_modules': {
                'direction': DIRECTION_PREDICTOR_AVAILABLE,
                'speed': SPEED_PREDICTOR_AVAILABLE,
                'iv': IV_PREDICTOR_AVAILABLE,
                'theta': THETA_PLANNER_AVAILABLE,
                'simulator': SIMULATOR_AVAILABLE
            }
        }
        
        # 1. Direction Prediction
        if self.direction_predictor and len(price_history) >= 20:
            try:
                direction_pred = self.direction_predictor.predict(
                    prices=price_history,
                    volumes=volume_history,
                    timestamp=timestamp
                )
                result['direction_prediction'] = {
                    'direction': direction_pred.direction.value,
                    'confidence': direction_pred.confidence,
                    'expected_move_pct': direction_pred.expected_move_pct,
                    'expected_move_points': direction_pred.expected_move_points,
                    'trade_signal': direction_pred.trade_signal,
                    'signal_strength': direction_pred.signal_strength,
                    'probabilities': {
                        'strong_up': direction_pred.prob_strong_up,
                        'up': direction_pred.prob_up,
                        'sideways': direction_pred.prob_sideways,
                        'down': direction_pred.prob_down,
                        'strong_down': direction_pred.prob_strong_down
                    },
                    'top_bullish_factors': direction_pred.top_bullish_factors,
                    'top_bearish_factors': direction_pred.top_bearish_factors,
                    'model_version': direction_pred.model_version
                }
                logger.info(f"✅ Direction: {direction_pred.direction.value} ({direction_pred.confidence:.0%})")
            except Exception as e:
                logger.error(f"Direction prediction failed: {e}")
                result['direction_prediction'] = {'error': str(e)}
        else:
            result['direction_prediction'] = {'error': 'Insufficient data or module unavailable'}
        
        # 2. Speed Prediction
        if self.speed_predictor and len(price_history) >= 20:
            try:
                speed_pred = self.speed_predictor.predict_speed(
                    current_price=spot_price,
                    price_history=price_history,
                    volume_history=volume_history or [1000000] * len(price_history),
                    current_volume=volume_history[-1] if volume_history else 1000000,
                    timestamp=timestamp,
                    is_expiry_day=is_expiry_day
                )
                result['speed_prediction'] = {
                    'category': speed_pred.category.value,
                    'confidence': speed_pred.confidence,
                    'expected_move_pct': speed_pred.expected_move_pct,
                    'expected_time_mins': speed_pred.expected_time_mins,
                    'factors': {
                        'volume_score': speed_pred.volume_score,
                        'time_of_day_score': speed_pred.time_of_day_score,
                        'volatility_squeeze_score': speed_pred.volatility_squeeze_score,
                        'momentum_score': speed_pred.momentum_score
                    },
                    'options_action': speed_pred.options_action,
                    'reasoning': speed_pred.reasoning,
                    'risk': {
                        'max_theta_loss_pct': speed_pred.max_theta_loss_pct,
                        'breakeven_time_mins': speed_pred.breakeven_time_mins
                    }
                }
                logger.info(f"✅ Speed: {speed_pred.category.value} ({speed_pred.confidence:.0%})")
            except Exception as e:
                logger.error(f"Speed prediction failed: {e}")
                result['speed_prediction'] = {'error': str(e)}
        else:
            result['speed_prediction'] = {'error': 'Insufficient data or module unavailable'}
        
        # 3. IV Prediction
        if self.iv_predictor:
            try:
                iv_pred = self.iv_predictor.predict_iv(
                    current_iv=current_iv,
                    spot_price=spot_price,
                    iv_history=iv_history or [current_iv] * 30,
                    price_history=price_history,
                    timestamp=timestamp,
                    is_expiry_day=is_expiry_day,
                    days_to_expiry=int(days_to_expiry)
                )
                result['iv_prediction'] = {
                    'direction': iv_pred.direction.value,
                    'confidence': iv_pred.confidence,
                    'expected_iv_change_pct': iv_pred.expected_iv_change_pct,
                    'current_iv': iv_pred.current_iv,
                    'predicted_iv': iv_pred.predicted_iv,
                    'regime': {
                        'current': iv_pred.current_regime.value,
                        'percentile': iv_pred.regime_percentile
                    },
                    'factors': {
                        'event': iv_pred.event_factor,
                        'time': iv_pred.time_factor,
                        'trend': iv_pred.trend_factor,
                        'expiry': iv_pred.expiry_factor
                    },
                    'trading': {
                        'vega_exposure': iv_pred.vega_exposure,
                        'options_strategy': iv_pred.options_strategy,
                        'reasoning': iv_pred.reasoning
                    },
                    'iv_risk_score': iv_pred.iv_risk_score
                }
                logger.info(f"✅ IV: {iv_pred.direction.value} ({iv_pred.confidence:.0%})")
            except Exception as e:
                logger.error(f"IV prediction failed: {e}")
                result['iv_prediction'] = {'error': str(e)}
        else:
            result['iv_prediction'] = {'error': 'Module unavailable'}
        
        # 4. Theta Scenarios
        if self.theta_planner:
            try:
                theta_result = self.theta_planner.generate_scenarios(
                    option_type=option_type,
                    strike=strike,
                    entry_premium=premium,
                    current_spot=spot_price,
                    current_iv=current_iv,
                    days_to_expiry=days_to_expiry,
                    timestamp=timestamp,
                    is_expiry_day=is_expiry_day
                )
                result['theta_scenarios'] = {
                    'greeks': {
                        'delta': theta_result.delta,
                        'gamma': theta_result.gamma,
                        'theta_per_hour': theta_result.theta_per_hour,
                        'vega': theta_result.vega
                    },
                    'scenarios': {
                        '15min': self._format_time_scenario(theta_result.scenarios_15min),
                        '30min': self._format_time_scenario(theta_result.scenarios_30min),
                        '1hour': self._format_time_scenario(theta_result.scenarios_1hour),
                        '2hour': self._format_time_scenario(theta_result.scenarios_2hour),
                        'eod': self._format_time_scenario(theta_result.scenarios_eod)
                    },
                    'summary': {
                        'optimal_holding_time_mins': theta_result.optimal_holding_time,
                        'max_theta_loss_today': theta_result.max_theta_loss_today,
                        'breakeven_move_required': theta_result.breakeven_move_required
                    },
                    'recommendations': {
                        'urgency': theta_result.urgency,
                        'hold_recommendation': theta_result.hold_recommendation,
                        'exit_triggers': theta_result.exit_triggers
                    }
                }
                logger.info(f"✅ Theta scenarios generated")
            except Exception as e:
                logger.error(f"Theta scenario generation failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
                result['theta_scenarios'] = {'error': str(e)}
        else:
            result['theta_scenarios'] = {'error': 'Module unavailable'}
        
        # 5. Full Simulation (if simulator available)
        if self.simulator and all([
            result.get('direction_prediction', {}).get('direction'),
            result.get('speed_prediction', {}).get('category'),
            result.get('iv_prediction', {}).get('direction')
        ]):
            try:
                sim_result = self.simulator.simulate(
                    option_type=option_type,
                    strike=strike,
                    premium=premium,
                    spot_price=spot_price,
                    current_iv=current_iv,
                    days_to_expiry=days_to_expiry,
                    price_history=price_history,
                    volume_history=volume_history,
                    iv_history=iv_history,
                    timestamp=timestamp,
                    is_expiry_day=is_expiry_day
                )
                result['simulation'] = self.simulator.to_dict(sim_result)
                logger.info(f"✅ Simulation: Grade {sim_result.grade.value}, Expected P&L: {sim_result.expected_pnl_pct:.1f}%")
            except Exception as e:
                logger.error(f"Simulation failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
                result['simulation'] = {'error': str(e)}
        else:
            result['simulation'] = {'error': 'Prerequisites not met or module unavailable'}
        
        # 6. Generate Combined Trading Recommendation
        result['combined_recommendation'] = self._generate_combined_recommendation(result)
        
        return result
    
    def _format_time_scenario(self, scenario) -> Dict:
        """Format a TimeScenario for JSON output."""
        return {
            'time_horizon_mins': scenario.time_horizon_mins,
            'description': scenario.description,
            'price_scenarios': {
                'up_fast': scenario.price_up_fast,
                'up_slow': scenario.price_up_slow,
                'flat': scenario.price_flat,
                'down_slow': scenario.price_down_slow,
                'down_fast': scenario.price_down_fast
            },
            'summary': {
                'best_case_pnl': scenario.best_case_pnl,
                'worst_case_pnl': scenario.worst_case_pnl,
                'expected_pnl': scenario.expected_pnl,
                'theta_decay_amt': scenario.theta_decay_amt
            },
            'risk': {
                'time_decay_risk': scenario.time_decay_risk,
                'profitable_scenarios': scenario.profitable_scenarios,
                'risk_reward_ratio': scenario.risk_reward_ratio
            }
        }
    
    def _generate_combined_recommendation(self, result: Dict) -> Dict:
        """
        Generate a combined trading recommendation from all predictions.
        
        This is the MASTER recommendation that considers all factors.
        """
        recommendation = {
            'action': 'WAIT',
            'confidence': 0,
            'reasoning': [],
            'key_factors': {},
            'warnings': []
        }
        
        # Check direction
        dir_pred = result.get('direction_prediction', {})
        if dir_pred.get('direction'):
            direction = dir_pred['direction']
            dir_confidence = dir_pred.get('confidence', 0)
            
            if direction in ['STRONG_UP', 'UP']:
                recommendation['key_factors']['direction'] = 'BULLISH'
            elif direction in ['STRONG_DOWN', 'DOWN']:
                recommendation['key_factors']['direction'] = 'BEARISH'
            else:
                recommendation['key_factors']['direction'] = 'NEUTRAL'
            
            recommendation['key_factors']['direction_confidence'] = dir_confidence
        
        # Check speed
        speed_pred = result.get('speed_prediction', {})
        if speed_pred.get('category'):
            speed = speed_pred['category']
            speed_confidence = speed_pred.get('confidence', 0)
            
            recommendation['key_factors']['speed'] = speed
            recommendation['key_factors']['speed_confidence'] = speed_confidence
            
            if speed in ['SLOW', 'CHOPPY']:
                recommendation['warnings'].append(f"⚠️ {speed} conditions - theta will dominate")
        
        # Check IV
        iv_pred = result.get('iv_prediction', {})
        if iv_pred.get('direction'):
            iv_dir = iv_pred['direction']
            iv_risk = iv_pred.get('iv_risk_score', 0.5)
            
            recommendation['key_factors']['iv_direction'] = iv_dir
            recommendation['key_factors']['iv_risk'] = iv_risk
            
            if iv_dir in ['CRUSH', 'CONTRACT']:
                recommendation['warnings'].append(f"⚠️ IV {iv_dir} expected - vega will hurt option buyers")
        
        # Check simulation result
        sim = result.get('simulation', {})
        if sim.get('trade_grade'):
            grade = sim['trade_grade']['grade']
            expected_pnl = sim.get('expected_values', {}).get('expected_pnl_pct', 0)
            win_prob = sim.get('expected_values', {}).get('win_probability', 0)
            
            recommendation['key_factors']['grade'] = grade
            recommendation['key_factors']['expected_pnl_pct'] = expected_pnl
            recommendation['key_factors']['win_probability'] = win_prob
            
            # Final action based on grade
            if grade in ['A+', 'A']:
                recommendation['action'] = 'BUY'
                recommendation['confidence'] = 0.8
                recommendation['reasoning'].append(f"✅ Grade {grade}: Excellent setup with aligned factors")
            elif grade in ['B+', 'B']:
                recommendation['action'] = 'BUY_CAUTIOUS'
                recommendation['confidence'] = 0.6
                recommendation['reasoning'].append(f"📊 Grade {grade}: Good setup, use proper risk management")
            elif grade == 'C':
                recommendation['action'] = 'AVOID'
                recommendation['confidence'] = 0.5
                recommendation['reasoning'].append(f"⚠️ Grade {grade}: Marginal setup, consider skipping")
            else:
                recommendation['action'] = 'DO_NOT_TRADE'
                recommendation['confidence'] = 0.7
                recommendation['reasoning'].append(f"🚫 Grade {grade}: Factors against you, avoid this trade")
        
        return recommendation
    
    def quick_pnl_check(
        self,
        option_type: str,
        strike: float,
        premium: float,
        current_spot: float,
        target_spot: float,
        time_mins: int,
        current_iv: float,
        days_to_expiry: float
    ) -> Dict:
        """
        Quick P&L check for "what if" scenarios.
        
        E.g., "If NIFTY goes to 25200 in 30 mins, what's my P&L?"
        """
        if not self.theta_planner:
            return {'error': 'Theta planner not available'}
        
        return self.theta_planner.quick_pnl_estimate(
            option_type=option_type,
            strike=strike,
            premium=premium,
            current_spot=current_spot,
            target_spot=target_spot,
            time_mins=time_mins,
            current_iv=current_iv,
            days_to_expiry=days_to_expiry
        )


# Global instance
_enhanced_ml_service = None

def get_enhanced_ml_service() -> EnhancedMLService:
    """Get or create the enhanced ML service singleton."""
    global _enhanced_ml_service
    if _enhanced_ml_service is None:
        _enhanced_ml_service = EnhancedMLService()
    return _enhanced_ml_service
