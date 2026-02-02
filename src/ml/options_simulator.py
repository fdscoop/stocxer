"""
Options P&L Simulator
=====================

This is the MASTER component that brings together:
1. Direction Prediction (XGBoost)
2. Speed Prediction 
3. IV Prediction
4. Theta Scenario Planning

It answers the ultimate question:
"Given my ML predictions, should I buy this option, and what P&L can I expect?"

Key Outputs:
- Simulated P&L under different scenarios
- Probability-weighted expected P&L
- Risk-adjusted recommendation
- Entry/Exit timing guidance

Author: TradeWise ML Team
Created: 2026-02-02
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import pytz

from src.ml.speed_predictor import SpeedPredictor, SpeedCategory, SpeedPrediction
from src.ml.iv_predictor import IVPredictor, IVDirection, IVPrediction
from src.ml.theta_scenario_planner import ThetaScenarioPlanner, ThetaScenarioResult
from src.ml.xgboost_direction import XGBoostDirectionPredictor, Direction, DirectionPrediction

IST = pytz.timezone('Asia/Kolkata')


class TradeGrade(Enum):
    """Overall trade quality grade"""
    A_PLUS = "A+"   # Excellent setup - high confidence, all factors aligned
    A = "A"         # Very good setup
    B_PLUS = "B+"   # Good setup with minor concerns
    B = "B"         # Decent setup
    C = "C"         # Marginal - proceed with caution
    D = "D"         # Poor setup - high risk
    F = "F"         # Do not trade - factors against you


@dataclass
class SimulatedScenario:
    """A single P&L simulation scenario"""
    name: str
    probability: float
    
    # Input assumptions
    price_move_pct: float
    time_elapsed_mins: int
    iv_change_pct: float
    
    # P&L breakdown
    delta_pnl: float
    gamma_pnl: float
    theta_pnl: float
    vega_pnl: float
    total_pnl: float
    pnl_pct: float
    
    # Outcome
    final_premium: float
    outcome: str  # "WIN", "LOSS", "BREAKEVEN"


@dataclass
class MLPredictionSummary:
    """Summary of all ML predictions"""
    direction: str
    direction_confidence: float
    expected_move_pct: float
    
    speed: str
    speed_confidence: float
    
    iv_direction: str
    iv_confidence: float
    expected_iv_change_pct: float
    
    # Combined assessment
    factors_aligned: int  # Out of 3
    overall_signal: str


@dataclass
class OptionsSimulationResult:
    """Complete simulation result"""
    # Option details
    option_type: str
    strike: float
    premium: float
    spot_price: float
    days_to_expiry: float
    
    # ML Predictions Summary
    predictions: MLPredictionSummary
    
    # Simulated Scenarios (5 main scenarios)
    best_case: SimulatedScenario
    likely_win: SimulatedScenario
    base_case: SimulatedScenario
    likely_loss: SimulatedScenario
    worst_case: SimulatedScenario
    
    # Expected Values
    expected_pnl: float  # Probability-weighted
    expected_pnl_pct: float
    win_probability: float
    
    # Risk Metrics
    max_loss: float
    max_gain: float
    risk_reward_ratio: float
    sharpe_estimate: float
    
    # Trade Grade
    grade: TradeGrade
    grade_factors: Dict[str, str]
    
    # Recommendations
    should_trade: bool
    position_size_pct: float  # % of capital to risk
    entry_timing: str
    exit_strategy: str
    stop_loss: float
    take_profit: float
    max_hold_time_mins: int


class OptionsPnLSimulator:
    """
    Master simulator that combines all ML predictions to simulate
    realistic option P&L scenarios.
    """
    
    def __init__(self):
        self.speed_predictor = SpeedPredictor()
        self.iv_predictor = IVPredictor()
        self.theta_planner = ThetaScenarioPlanner()
        self.direction_predictor = XGBoostDirectionPredictor()
    
    def simulate(
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
    ) -> OptionsSimulationResult:
        """
        Run complete P&L simulation using all ML models.
        
        Args:
            option_type: "CE" or "PE"
            strike: Option strike price
            premium: Current option premium
            spot_price: Current underlying price
            current_iv: Current implied volatility (e.g., 16.5)
            days_to_expiry: Days until expiry
            price_history: Historical prices (50+ candles)
            volume_history: Historical volumes
            iv_history: Historical IV values
            timestamp: Current timestamp
            is_expiry_day: Whether it's expiry day
        
        Returns:
            OptionsSimulationResult with complete analysis
        """
        if timestamp is None:
            timestamp = datetime.now(IST)
        
        # ============================================
        # STEP 1: Get ML Predictions
        # ============================================
        
        # Direction prediction
        direction_pred = self.direction_predictor.predict(
            prices=price_history,
            volumes=volume_history,
            timestamp=timestamp
        )
        
        # Speed prediction
        speed_pred = self.speed_predictor.predict_speed(
            current_price=spot_price,
            price_history=price_history,
            volume_history=volume_history or [1000000] * len(price_history),
            current_volume=volume_history[-1] if volume_history else 1000000,
            timestamp=timestamp,
            is_expiry_day=is_expiry_day
        )
        
        # IV prediction
        iv_pred = self.iv_predictor.predict_iv(
            current_iv=current_iv,
            spot_price=spot_price,
            iv_history=iv_history or [current_iv] * 30,
            price_history=price_history,
            timestamp=timestamp,
            is_expiry_day=is_expiry_day,
            days_to_expiry=int(days_to_expiry)
        )
        
        # Theta scenarios
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
        
        # ============================================
        # STEP 2: Create Prediction Summary
        # ============================================
        
        prediction_summary = self._create_prediction_summary(
            direction_pred, speed_pred, iv_pred, option_type
        )
        
        # ============================================
        # STEP 3: Simulate P&L Scenarios
        # ============================================
        
        scenarios = self._simulate_scenarios(
            option_type, strike, premium, spot_price, current_iv,
            days_to_expiry, direction_pred, speed_pred, iv_pred,
            theta_result, is_expiry_day
        )
        
        # ============================================
        # STEP 4: Calculate Expected Values
        # ============================================
        
        expected_pnl = sum(s.probability * s.total_pnl for s in scenarios.values())
        expected_pnl_pct = (expected_pnl / premium) * 100 if premium > 0 else 0
        
        win_scenarios = [s for s in scenarios.values() if s.total_pnl > 0]
        win_probability = sum(s.probability for s in win_scenarios)
        
        # ============================================
        # STEP 5: Risk Metrics
        # ============================================
        
        max_loss = min(s.total_pnl for s in scenarios.values())
        max_gain = max(s.total_pnl for s in scenarios.values())
        
        risk_reward = abs(max_gain / max_loss) if max_loss != 0 else 0
        
        # Sharpe estimate (simplified)
        pnls = [s.total_pnl for s in scenarios.values()]
        std_dev = np.std(pnls) if len(pnls) > 1 else 1
        sharpe = expected_pnl / std_dev if std_dev > 0 else 0
        
        # ============================================
        # STEP 6: Grade the Trade
        # ============================================
        
        grade, grade_factors = self._grade_trade(
            prediction_summary, scenarios, expected_pnl_pct, 
            win_probability, risk_reward, is_expiry_day
        )
        
        # ============================================
        # STEP 7: Generate Recommendations
        # ============================================
        
        should_trade, position_size, timing, exit_strat, stop, target, max_hold = \
            self._generate_recommendations(
                grade, prediction_summary, expected_pnl_pct, premium,
                theta_result, is_expiry_day
            )
        
        return OptionsSimulationResult(
            option_type=option_type,
            strike=strike,
            premium=premium,
            spot_price=spot_price,
            days_to_expiry=days_to_expiry,
            predictions=prediction_summary,
            best_case=scenarios['best_case'],
            likely_win=scenarios['likely_win'],
            base_case=scenarios['base_case'],
            likely_loss=scenarios['likely_loss'],
            worst_case=scenarios['worst_case'],
            expected_pnl=round(expected_pnl, 2),
            expected_pnl_pct=round(expected_pnl_pct, 1),
            win_probability=round(win_probability, 2),
            max_loss=round(max_loss, 2),
            max_gain=round(max_gain, 2),
            risk_reward_ratio=round(risk_reward, 2),
            sharpe_estimate=round(sharpe, 2),
            grade=grade,
            grade_factors=grade_factors,
            should_trade=should_trade,
            position_size_pct=position_size,
            entry_timing=timing,
            exit_strategy=exit_strat,
            stop_loss=round(stop, 2),
            take_profit=round(target, 2),
            max_hold_time_mins=max_hold
        )
    
    def _create_prediction_summary(
        self,
        direction: DirectionPrediction,
        speed: SpeedPrediction,
        iv: IVPrediction,
        option_type: str
    ) -> MLPredictionSummary:
        """Create unified summary of all ML predictions."""
        
        # Check alignment
        factors_aligned = 0
        
        # Direction alignment for option type
        if option_type == "CE":
            direction_favorable = direction.direction in [Direction.UP, Direction.STRONG_UP]
        else:
            direction_favorable = direction.direction in [Direction.DOWN, Direction.STRONG_DOWN]
        
        if direction_favorable:
            factors_aligned += 1
        
        # Speed alignment (FAST/EXPLOSIVE is good for buying options)
        if speed.category in [SpeedCategory.FAST, SpeedCategory.EXPLOSIVE]:
            factors_aligned += 1
        
        # IV alignment (not crushing)
        if iv.direction not in [IVDirection.CRUSH, IVDirection.CONTRACT]:
            factors_aligned += 1
        
        # Overall signal
        if factors_aligned == 3:
            overall = "STRONG_BUY"
        elif factors_aligned == 2:
            overall = "BUY"
        elif factors_aligned == 1:
            overall = "WEAK_BUY"
        else:
            overall = "AVOID"
        
        return MLPredictionSummary(
            direction=direction.direction.value,
            direction_confidence=direction.confidence,
            expected_move_pct=direction.expected_move_pct,
            speed=speed.category.value,
            speed_confidence=speed.confidence,
            iv_direction=iv.direction.value,
            iv_confidence=iv.confidence,
            expected_iv_change_pct=iv.expected_iv_change_pct,
            factors_aligned=factors_aligned,
            overall_signal=overall
        )
    
    def _simulate_scenarios(
        self,
        option_type: str,
        strike: float,
        premium: float,
        spot_price: float,
        current_iv: float,
        days_to_expiry: float,
        direction: DirectionPrediction,
        speed: SpeedPrediction,
        iv: IVPrediction,
        theta: ThetaScenarioResult,
        is_expiry_day: bool
    ) -> Dict[str, SimulatedScenario]:
        """
        Simulate 5 key scenarios based on ML predictions.
        """
        scenarios = {}
        
        # Get base parameters
        delta = theta.delta
        gamma = theta.gamma
        vega = theta.vega
        theta_per_hour = theta.theta_per_hour
        
        # Determine move direction for option
        is_call = option_type == "CE"
        
        # Scenario 1: BEST CASE
        # Fast move in your favor + IV stable/up
        if is_call:
            price_move = direction.expected_move_pct * 1.5 / 100  # Exceeds expectation
        else:
            price_move = -direction.expected_move_pct * 1.5 / 100
        
        scenarios['best_case'] = self._calculate_scenario(
            "Best Case: Fast favorable move",
            probability=0.10,
            price_move_pct=price_move * 100,
            time_mins=speed.expected_time_mins,
            iv_change_pct=max(0, iv.expected_iv_change_pct),  # IV helps
            premium=premium, spot=spot_price, delta=delta, gamma=gamma,
            theta_per_hour=theta_per_hour, vega=vega, current_iv=current_iv
        )
        
        # Scenario 2: LIKELY WIN
        # Move as predicted + IV stable
        if is_call:
            price_move = direction.expected_move_pct / 100
        else:
            price_move = -direction.expected_move_pct / 100
        
        scenarios['likely_win'] = self._calculate_scenario(
            "Likely Win: Move as predicted",
            probability=0.25,
            price_move_pct=price_move * 100,
            time_mins=int(speed.expected_time_mins * 1.2),
            iv_change_pct=0,  # IV stable
            premium=premium, spot=spot_price, delta=delta, gamma=gamma,
            theta_per_hour=theta_per_hour, vega=vega, current_iv=current_iv
        )
        
        # Scenario 3: BASE CASE
        # Small move, takes longer than expected
        if is_call:
            price_move = direction.expected_move_pct * 0.3 / 100
        else:
            price_move = -direction.expected_move_pct * 0.3 / 100
        
        time_factor = 2.0 if is_expiry_day else 1.5
        scenarios['base_case'] = self._calculate_scenario(
            "Base Case: Slow partial move",
            probability=0.35,
            price_move_pct=price_move * 100,
            time_mins=int(speed.expected_time_mins * time_factor),
            iv_change_pct=iv.expected_iv_change_pct * 0.5,
            premium=premium, spot=spot_price, delta=delta, gamma=gamma,
            theta_per_hour=theta_per_hour, vega=vega, current_iv=current_iv
        )
        
        # Scenario 4: LIKELY LOSS
        # No move + theta decay + IV drop
        scenarios['likely_loss'] = self._calculate_scenario(
            "Likely Loss: No move, theta decay",
            probability=0.20,
            price_move_pct=0,
            time_mins=int(speed.expected_time_mins * 2),
            iv_change_pct=min(-5, iv.expected_iv_change_pct),  # IV hurts
            premium=premium, spot=spot_price, delta=delta, gamma=gamma,
            theta_per_hour=theta_per_hour, vega=vega, current_iv=current_iv
        )
        
        # Scenario 5: WORST CASE
        # Move against you + IV crush
        if is_call:
            price_move = -abs(direction.expected_move_pct) / 100
        else:
            price_move = abs(direction.expected_move_pct) / 100
        
        scenarios['worst_case'] = self._calculate_scenario(
            "Worst Case: Move against + IV crush",
            probability=0.10,
            price_move_pct=price_move * 100,
            time_mins=int(speed.expected_time_mins * 2),
            iv_change_pct=-15,  # Significant IV drop
            premium=premium, spot=spot_price, delta=delta, gamma=gamma,
            theta_per_hour=theta_per_hour, vega=vega, current_iv=current_iv
        )
        
        return scenarios
    
    def _calculate_scenario(
        self,
        name: str,
        probability: float,
        price_move_pct: float,
        time_mins: int,
        iv_change_pct: float,
        premium: float,
        spot: float,
        delta: float,
        gamma: float,
        theta_per_hour: float,
        vega: float,
        current_iv: float
    ) -> SimulatedScenario:
        """Calculate P&L for a single scenario."""
        
        price_change = spot * (price_move_pct / 100)
        time_hours = time_mins / 60
        iv_change = current_iv * (iv_change_pct / 100)
        
        # P&L components
        delta_pnl = delta * price_change
        gamma_pnl = 0.5 * gamma * price_change ** 2
        theta_pnl = theta_per_hour * time_hours  # Negative for buyers
        vega_pnl = vega * iv_change
        
        total_pnl = delta_pnl + gamma_pnl + theta_pnl + vega_pnl
        pnl_pct = (total_pnl / premium) * 100 if premium > 0 else 0
        
        final_premium = premium + total_pnl
        
        if pnl_pct > 5:
            outcome = "WIN"
        elif pnl_pct < -5:
            outcome = "LOSS"
        else:
            outcome = "BREAKEVEN"
        
        return SimulatedScenario(
            name=name,
            probability=probability,
            price_move_pct=round(price_move_pct, 2),
            time_elapsed_mins=time_mins,
            iv_change_pct=round(iv_change_pct, 1),
            delta_pnl=round(delta_pnl, 2),
            gamma_pnl=round(gamma_pnl, 2),
            theta_pnl=round(theta_pnl, 2),
            vega_pnl=round(vega_pnl, 2),
            total_pnl=round(total_pnl, 2),
            pnl_pct=round(pnl_pct, 1),
            final_premium=round(max(0, final_premium), 2),
            outcome=outcome
        )
    
    def _grade_trade(
        self,
        predictions: MLPredictionSummary,
        scenarios: Dict[str, SimulatedScenario],
        expected_pnl_pct: float,
        win_prob: float,
        risk_reward: float,
        is_expiry_day: bool
    ) -> Tuple[TradeGrade, Dict[str, str]]:
        """Grade the overall trade quality."""
        
        score = 0
        factors = {}
        
        # Factor 1: Direction + Speed + IV alignment (max 30 points)
        alignment_score = predictions.factors_aligned * 10
        score += alignment_score
        factors['ml_alignment'] = f"{predictions.factors_aligned}/3 factors aligned"
        
        # Factor 2: Expected P&L (max 25 points)
        if expected_pnl_pct > 20:
            pnl_score = 25
        elif expected_pnl_pct > 10:
            pnl_score = 20
        elif expected_pnl_pct > 5:
            pnl_score = 15
        elif expected_pnl_pct > 0:
            pnl_score = 10
        else:
            pnl_score = 0
        score += pnl_score
        factors['expected_pnl'] = f"{expected_pnl_pct:.1f}% expected"
        
        # Factor 3: Win probability (max 25 points)
        if win_prob > 0.6:
            win_score = 25
        elif win_prob > 0.5:
            win_score = 20
        elif win_prob > 0.4:
            win_score = 15
        else:
            win_score = 5
        score += win_score
        factors['win_probability'] = f"{win_prob:.0%} win rate"
        
        # Factor 4: Risk/Reward (max 20 points)
        if risk_reward > 2.0:
            rr_score = 20
        elif risk_reward > 1.5:
            rr_score = 15
        elif risk_reward > 1.0:
            rr_score = 10
        else:
            rr_score = 5
        score += rr_score
        factors['risk_reward'] = f"{risk_reward:.2f}:1 R/R"
        
        # Expiry day penalty
        if is_expiry_day:
            score -= 10
            factors['expiry_penalty'] = "Expiry day risk (-10)"
        
        # Convert score to grade
        if score >= 85:
            grade = TradeGrade.A_PLUS
        elif score >= 75:
            grade = TradeGrade.A
        elif score >= 65:
            grade = TradeGrade.B_PLUS
        elif score >= 55:
            grade = TradeGrade.B
        elif score >= 45:
            grade = TradeGrade.C
        elif score >= 30:
            grade = TradeGrade.D
        else:
            grade = TradeGrade.F
        
        factors['total_score'] = f"{score}/100"
        
        return grade, factors
    
    def _generate_recommendations(
        self,
        grade: TradeGrade,
        predictions: MLPredictionSummary,
        expected_pnl_pct: float,
        premium: float,
        theta: ThetaScenarioResult,
        is_expiry_day: bool
    ) -> Tuple[bool, float, str, str, float, float, int]:
        """Generate trading recommendations."""
        
        # Should trade?
        should_trade = grade in [TradeGrade.A_PLUS, TradeGrade.A, TradeGrade.B_PLUS, TradeGrade.B]
        
        # Position size (% of capital)
        if grade == TradeGrade.A_PLUS:
            position_size = 5.0
        elif grade == TradeGrade.A:
            position_size = 4.0
        elif grade == TradeGrade.B_PLUS:
            position_size = 3.0
        elif grade == TradeGrade.B:
            position_size = 2.0
        else:
            position_size = 1.0  # Minimal if trading anyway
        
        # Entry timing
        speed = predictions.speed
        if speed in ["EXPLOSIVE", "FAST"]:
            timing = "ENTER_NOW - Fast move imminent"
        elif speed == "NORMAL":
            timing = "WAIT_FOR_DIP - Enter on minor pullback"
        else:
            timing = "RECONSIDER - Slow conditions"
        
        # Exit strategy
        if is_expiry_day:
            exit_strat = "SCALP - Exit within 30-60 mins, no overnight"
        elif grade in [TradeGrade.A_PLUS, TradeGrade.A]:
            exit_strat = "RIDE_MOMENTUM - Trail stop, let winners run"
        else:
            exit_strat = "QUICK_PROFIT - Take profit at +20%, strict stop"
        
        # Stop loss (% of premium)
        if is_expiry_day:
            stop_pct = 0.25  # Tight stop on expiry
        elif grade in [TradeGrade.A_PLUS, TradeGrade.A]:
            stop_pct = 0.30  # Give room for good setups
        else:
            stop_pct = 0.20  # Tight for marginal setups
        
        stop_loss = premium * stop_pct
        
        # Take profit
        if grade == TradeGrade.A_PLUS:
            target_pct = 0.50  # 50% profit for best setups
        elif grade == TradeGrade.A:
            target_pct = 0.40
        elif grade == TradeGrade.B_PLUS:
            target_pct = 0.30
        else:
            target_pct = 0.20
        
        take_profit = premium * target_pct
        
        # Max hold time
        if is_expiry_day:
            max_hold = theta.optimal_holding_time
        else:
            max_hold = min(120, theta.optimal_holding_time * 2)
        
        return should_trade, position_size, timing, exit_strat, stop_loss, take_profit, max_hold
    
    def to_dict(self, result: OptionsSimulationResult) -> Dict:
        """Convert simulation result to dictionary for API response."""
        return {
            'option_details': {
                'type': result.option_type,
                'strike': result.strike,
                'premium': result.premium,
                'spot_price': result.spot_price,
                'days_to_expiry': result.days_to_expiry
            },
            'ml_predictions': {
                'direction': result.predictions.direction,
                'direction_confidence': result.predictions.direction_confidence,
                'expected_move_pct': result.predictions.expected_move_pct,
                'speed': result.predictions.speed,
                'speed_confidence': result.predictions.speed_confidence,
                'iv_direction': result.predictions.iv_direction,
                'iv_confidence': result.predictions.iv_confidence,
                'expected_iv_change_pct': result.predictions.expected_iv_change_pct,
                'factors_aligned': result.predictions.factors_aligned,
                'overall_signal': result.predictions.overall_signal
            },
            'scenarios': {
                'best_case': asdict(result.best_case),
                'likely_win': asdict(result.likely_win),
                'base_case': asdict(result.base_case),
                'likely_loss': asdict(result.likely_loss),
                'worst_case': asdict(result.worst_case)
            },
            'expected_values': {
                'expected_pnl': result.expected_pnl,
                'expected_pnl_pct': result.expected_pnl_pct,
                'win_probability': result.win_probability
            },
            'risk_metrics': {
                'max_loss': result.max_loss,
                'max_gain': result.max_gain,
                'risk_reward_ratio': result.risk_reward_ratio,
                'sharpe_estimate': result.sharpe_estimate
            },
            'trade_grade': {
                'grade': result.grade.value,
                'factors': result.grade_factors
            },
            'recommendations': {
                'should_trade': result.should_trade,
                'position_size_pct': result.position_size_pct,
                'entry_timing': result.entry_timing,
                'exit_strategy': result.exit_strategy,
                'stop_loss': result.stop_loss,
                'take_profit': result.take_profit,
                'max_hold_time_mins': result.max_hold_time_mins
            }
        }


def create_simulator() -> OptionsPnLSimulator:
    """Factory function to create the P&L simulator."""
    return OptionsPnLSimulator()
