"""
Trade Confidence Calculator with Proper Hierarchy
ICT Structure (65%) > Candlestick Patterns (10%) > ML Models (15%) > Market Data (10%)

Centralizes confidence scoring to ensure ICT methodology drives decisions
"""

from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceBreakdown:
    """
    Detailed confidence score breakdown
    Total max: 100 points
    """
    htf_structure: float  # 0-40 points (HTF bias quality)
    ltf_confirmation: float  # 0-25 points (LTF entry model)
    ml_alignment: float  # 0-15 points (ARIMA/LSTM confirmation)
    candlestick: float  # 0-10 points (Pattern timing)
    futures_basis: float  # 0-5 points (Institutional positioning)
    constituents: float  # 0-5 points (Market breadth)
    
    @property
    def total(self) -> float:
        """Calculate total confidence score (0-100)"""
        return round(sum([
            self.htf_structure,
            self.ltf_confirmation,
            self.ml_alignment,
            self.candlestick,
            self.futures_basis,
            self.constituents
        ]), 1)
    
    @property
    def confidence_level(self) -> str:
        """Get confidence level label"""
        total = self.total
        if total >= 80:
            return "VERY HIGH"
        elif total >= 65:
            return "HIGH"
        elif total >= 50:
            return "MODERATE"
        elif total >= 35:
            return "LOW"
        else:
            return "VERY LOW"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'htf_structure': round(self.htf_structure, 1),
            'ltf_confirmation': round(self.ltf_confirmation, 1),
            'ml_alignment': round(self.ml_alignment, 1),
            'candlestick': round(self.candlestick, 1),
            'futures_basis': round(self.futures_basis, 1),
            'constituents': round(self.constituents, 1),
            'total': self.total,
            'confidence_level': self.confidence_level
        }


class ConfidenceCalculator:
    """
    Calculate trade confidence using proper hierarchy:
    
    1. ICT HTF Structure (40 points max)
       - Market structure clarity (BOS/CHoCH)
       - FVG/OB quality
       - Premium/Discount position
       
    2. ICT LTF Confirmation (25 points max)
       - Entry model type
       - HTF alignment
       - Momentum confirmation
       
    3. ML Alignment (15 points max)
       - ARIMA/LSTM agreement with ICT
       - Forecast confidence
       
    4. Candlestick Patterns (10 points max)
       - Multi-timeframe pattern confluence
       - Pattern strength
       
    5. Futures Basis (5 points max)
       - Institutional positioning
       
    6. Constituent Analysis (5 points max)
       - Market breadth
    """
    
    def calculate_htf_structure_score(
        self,
        htf_bias: Dict
    ) -> float:
        """
        Score HTF structure quality (0-40 points)
        
        Args:
            htf_bias: Dict with HTF analysis results
                - overall_direction: 'bullish'/'bearish'/'neutral'
                - bias_strength: 0-100
                - structure_quality: 'HIGH'/'MEDIUM'/'LOW'
                - premium_discount: 'premium'/'equilibrium'/'discount'
                - key_zones_count: Number of identified zones
                
        Returns:
            Score (0-40)
        """
        score = 0.0
        
        # Factor 1: Bias strength (0-15 points)
        bias_strength = htf_bias.get('bias_strength', 0)
        score += (bias_strength / 100) * 15
        
        # Factor 2: Structure quality (0-15 points)
        structure_quality = htf_bias.get('structure_quality', 'LOW')
        if structure_quality == 'HIGH':
            score += 15
        elif structure_quality == 'MEDIUM':
            score += 10
        else:  # LOW
            score += 5
        
        # Factor 3: Premium/Discount position (0-10 points)
        # Trading from discount zones (buying low) is ideal
        premium_discount = htf_bias.get('premium_discount', 'equilibrium')
        direction = htf_bias.get('overall_direction', 'neutral')
        
        if direction == 'bullish' and premium_discount == 'discount':
            score += 10  # Perfect: buying at discount in uptrend
        elif direction == 'bearish' and premium_discount == 'premium':
            score += 10  # Perfect: selling at premium in downtrend
        elif premium_discount == 'equilibrium':
            score += 5   # Neutral
        else:
            score += 2   # Poor: buying premium or selling discount
        
        logger.info(f"🔢 HTF Structure Score: {score:.1f}/40 (strength={bias_strength}, quality={structure_quality})")
        return min(score, 40.0)
    
    def calculate_ltf_confirmation_score(
        self,
        ltf_entry: Dict,
        htf_bias: Dict
    ) -> float:
        """
        Score LTF entry quality (0-25 points)
        
        Args:
            ltf_entry: Dict with LTF entry model
                - entry_type: 'FVG_TEST_2ND'/'FVG_TEST'/'OB_TEST'/'CHOCH'
                - timeframe: '15m'/'5m'/'3m'
                - momentum_confirmed: Boolean
                - alignment_score: 0-100
                
            htf_bias: HTF bias for alignment check
            
        Returns:
            Score (0-25)
        """
        score = 0.0
        
        # Factor 1: Entry model type (0-12 points)
        entry_type = ltf_entry.get('entry_type', '')
        if 'FVG_TEST_2ND' in entry_type or 'SECOND_TEST' in entry_type:
            score += 12  # Second test = highest probability
        elif 'FVG_TEST' in entry_type or 'OB_TEST' in entry_type:
            score += 8   # First test = good
        elif 'CHOCH' in entry_type or 'BOS' in entry_type:
            score += 6   # Structure break = moderate
        else:
            score += 3   # Other setups
        
        # Factor 2: HTF alignment (0-8 points)
        alignment_score = ltf_entry.get('alignment_score', 0)
        score += (alignment_score / 100) * 8
        
        # Factor 3: Momentum confirmation (0-5 points)
        if ltf_entry.get('momentum_confirmed', False):
            score += 5
        else:
            score += 1
        
        logger.info(f"🔢 LTF Confirmation Score: {score:.1f}/25 (entry={entry_type})")
        return min(score, 25.0)
    
    def calculate_ml_alignment_score(
        self,
        ml_signal: Optional[Dict],
        htf_bias: Dict
    ) -> float:
        """
        Score ML confirmation (0-15 points)
        
        ML should AGREE with ICT, not lead
        Full points only if ML confirms ICT bias
        
        Args:
            ml_signal: Dict with ML forecast
                - direction: 'bullish'/'bearish'/'neutral'
                - confidence: 0-1
                - agrees_with_htf: Boolean
                
            htf_bias: HTF bias for comparison
            
        Returns:
            Score (0-15)
        """
        if not ml_signal or ml_signal.get('error'):
            logger.info("🔢 ML Alignment Score: 5.0/15 (no ML signal available)")
            return 5.0  # Neutral score if ML unavailable
        
        score = 0.0
        htf_direction = htf_bias.get('overall_direction', 'neutral')
        ml_direction = ml_signal.get('direction', 'neutral')
        ml_confidence = ml_signal.get('confidence', 0)
        
        # Check agreement
        if ml_direction == htf_direction and htf_direction != 'neutral':
            # ML agrees with HTF - full points based on ML confidence
            score = ml_confidence * 15
            logger.info(f"✅ ML CONFIRMS HTF {htf_direction.upper()}: {score:.1f}/15")
        elif ml_direction == 'neutral':
            # ML neutral - partial score
            score = 7.5
            logger.info(f"⚠️ ML NEUTRAL: {score:.1f}/15")
        else:
            # ML conflicts with HTF - minimal score
            score = 2.0
            logger.warning(f"🚨 ML CONFLICTS: ML={ml_direction}, HTF={htf_direction} → {score:.1f}/15")
        
        return min(score, 15.0)
    
    def calculate_candlestick_score(
        self,
        candlestick_analysis: Optional[Dict],
        expected_direction: str
    ) -> float:
        """
        Score candlestick pattern confluence (0-10 points)
        
        Args:
            candlestick_analysis: Dict with pattern analysis
                - confluence_score: 0-100
                - aligned_patterns: Count
                - conflicting_patterns: Count
                
            expected_direction: Expected direction from ICT
            
        Returns:
            Score (0-10)
        """
        if not candlestick_analysis:
            logger.info("🔢 Candlestick Score: 4.0/10 (no pattern analysis)")
            return 4.0  # Neutral if unavailable
        
        confluence = candlestick_analysis.get('confluence_analysis', {})
        confluence_score = confluence.get('confluence_score', 0)
        
        # Convert 0-100 confluence to 0-10 points
        score = (confluence_score / 100) * 10
        
        aligned = confluence.get('aligned_patterns', 0)
        conflicting = confluence.get('conflicting_patterns', 0)
        
        logger.info(f"🔢 Candlestick Score: {score:.1f}/10 (confluence={confluence_score:.1f}%, aligned={aligned}, conflicts={conflicting})")
        return min(score, 10.0)
    
    def calculate_futures_basis_score(
        self,
        futures_data: Optional[Dict],
        htf_direction: str
    ) -> float:
        """
        Score futures basis alignment (0-5 points)
        
        Args:
            futures_data: Dict with futures analysis
                - basis_pct: Premium/discount percentage
                - sentiment: 'bullish'/'bearish'/'neutral'
                
            htf_direction: HTF bias direction
            
        Returns:
            Score (0-5)
        """
        if not futures_data:
            logger.info("🔢 Futures Basis Score: 2.5/5 (no futures data)")
            return 2.5  # Neutral
        
        futures_sentiment = futures_data.get('sentiment', 'neutral')
        basis_pct = abs(futures_data.get('basis_pct', 0))
        
        if futures_sentiment == htf_direction and htf_direction != 'neutral':
            # Futures agree - score based on basis strength
            score = min(basis_pct * 100, 5.0)  # Stronger basis = higher score
            logger.info(f"✅ Futures ALIGN with HTF: {score:.1f}/5")
        elif futures_sentiment == 'neutral':
            score = 2.5
            logger.info(f"📊 Futures NEUTRAL: {score:.1f}/5")
        else:
            score = 1.0
            logger.info(f"⚠️ Futures CONFLICT: {score:.1f}/5")
        
        return min(score, 5.0)
    
    def calculate_constituents_score(
        self,
        probability_analysis: Optional[Dict],
        htf_direction: str
    ) -> float:
        """
        Score constituent stock alignment (0-5 points)
        
        Args:
            probability_analysis: Dict with constituent analysis
                - expected_direction: 'BULLISH'/'BEARISH'/'NEUTRAL'
                - confidence: 0-1
                
            htf_direction: HTF bias direction
            
        Returns:
            Score (0-5)
        """
        if not probability_analysis:
            logger.info("🔢 Constituents Score: 2.5/5 (no constituent data)")
            return 2.5  # Neutral
        
        constituent_dir = probability_analysis.get('expected_direction', 'NEUTRAL').lower()
        constituent_conf = probability_analysis.get('confidence', 0)
        
        if constituent_dir == htf_direction and htf_direction != 'neutral':
            score = constituent_conf * 5
            logger.info(f"✅ Constituents ALIGN: {score:.1f}/5")
        elif constituent_dir == 'neutral':
            score = 2.5
            logger.info(f"📊 Constituents NEUTRAL: {score:.1f}/5")
        else:
            score = 1.0
            logger.info(f"⚠️ Constituents CONFLICT: {score:.1f}/5")
        
        return min(score, 5.0)
    
    def calculate_confidence(
        self,
        htf_bias: Dict,
        ltf_entry: Dict,
        ml_signal: Optional[Dict] = None,
        candlestick_analysis: Optional[Dict] = None,
        futures_data: Optional[Dict] = None,
        probability_analysis: Optional[Dict] = None
    ) -> ConfidenceBreakdown:
        """
        Calculate complete confidence breakdown
        
        Args:
            htf_bias: Higher timeframe bias analysis
            ltf_entry: Lower timeframe entry model
            ml_signal: ML forecast (optional)
            candlestick_analysis: Pattern analysis (optional)
            futures_data: Futures basis data (optional)
            probability_analysis: Constituent analysis (optional)
            
        Returns:
            ConfidenceBreakdown with full scoring
        """
        logger.info("=" * 60)
        logger.info("📊 CALCULATING TRADE CONFIDENCE")
        logger.info("=" * 60)
        
        htf_direction = htf_bias.get('overall_direction', 'neutral')
        
        breakdown = ConfidenceBreakdown(
            htf_structure=self.calculate_htf_structure_score(htf_bias),
            ltf_confirmation=self.calculate_ltf_confirmation_score(ltf_entry, htf_bias),
            ml_alignment=self.calculate_ml_alignment_score(ml_signal, htf_bias),
            candlestick=self.calculate_candlestick_score(candlestick_analysis, htf_direction),
            futures_basis=self.calculate_futures_basis_score(futures_data, htf_direction),
            constituents=self.calculate_constituents_score(probability_analysis, htf_direction)
        )
        
        logger.info("=" * 60)
        logger.info(f"🎯 FINAL CONFIDENCE: {breakdown.total}/100 ({breakdown.confidence_level})")
        logger.info(f"   HTF Structure: {breakdown.htf_structure:.1f}/40")
        logger.info(f"   LTF Confirmation: {breakdown.ltf_confirmation:.1f}/25")
        logger.info(f"   ML Alignment: {breakdown.ml_alignment:.1f}/15")
        logger.info(f"   Candlestick: {breakdown.candlestick:.1f}/10")
        logger.info(f"   Futures: {breakdown.futures_basis:.1f}/5")
        logger.info(f"   Constituents: {breakdown.constituents:.1f}/5")
        logger.info("=" * 60)
        
        return breakdown


# Global instance
confidence_calculator = ConfidenceCalculator()


def calculate_trade_confidence(
    htf_bias: Dict,
    ltf_entry: Dict,
    ml_signal: Optional[Dict] = None,
    candlestick_analysis: Optional[Dict] = None,
    futures_data: Optional[Dict] = None,
    probability_analysis: Optional[Dict] = None
) -> Dict:
    """
    Convenience function to calculate confidence and return as dict
    
    Returns:
        Dict with confidence breakdown
    """
    calculator = ConfidenceCalculator()
    breakdown = calculator.calculate_confidence(
        htf_bias=htf_bias,
        ltf_entry=ltf_entry,
        ml_signal=ml_signal,
        candlestick_analysis=candlestick_analysis,
        futures_data=futures_data,
        probability_analysis=probability_analysis
    )
    return breakdown.to_dict()
