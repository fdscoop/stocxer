"""
Option-Aware Practical ICT Analysis
Analyzes option chain to find strikes with best momentum for 5-15 point targets
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Correct lot sizes (Jan 2026)
LOT_SIZES = {
    "NIFTY": 65,
    "BANKNIFTY": 30,
    "FINNIFTY": 60,
    "MIDCPNIFTY": 120,
    "SENSEX": 20,
    "NIFTYNXT50": 25
}


class OptionAwarePracticalICT:
    """
    Complete system that:
    1. Analyzes index momentum
    2. Fetches option chain
    3. Finds best strike for 5/10/15 point targets
    4. Returns actionable trade with exact prices
    """
    
    def __init__(self, fyers_client):
        """
        Args:
            fyers_client: Your Fyers client for fetching option chain
        """
        self.fyers = fyers_client
        
        # Cache for ICT-based option type selection
        self.cached_candles = None
        self.cached_htf_bias = None
        self.cached_probability = None
    
    async def generate_option_signal(
        self,
        index: str,
        candles_by_timeframe: Dict[str, pd.DataFrame],
        spot_price: float,
        dte: int
    ) -> Dict:
        """
        Main entry point - generates complete option trading signal
        
        Args:
            index: Index symbol (NIFTY, BANKNIFTY, etc)
            candles_by_timeframe: Dict of timeframe -> DataFrame
            spot_price: Current spot price
            dte: Days to expiry
            
        Returns:
            Signal with specific strike, entry price, targets in option premium
        """
        
        logger.info("=" * 70)
        logger.info(f"🎯 OPTION-AWARE ICT: {index} | Spot: {spot_price:.2f} | DTE: {dte}")
        logger.info("=" * 70)
        
        # Step 1: Analyze index momentum
        index_signal = await self._analyze_index_momentum(
            candles_by_timeframe, 
            spot_price, 
            dte
        )
        
        if index_signal['signal'] == 'WAIT':
            return index_signal
        
        logger.info(f"📊 Index Signal: {index_signal['signal']} | Confidence: {index_signal['confidence']}%")
        
        # Step 2: Fetch live option chain
        option_chain = await self._fetch_option_chain(index)
        
        if not option_chain:
            logger.error("❌ Could not fetch option chain")
            return self._no_signal(index, spot_price, "Option chain unavailable")
        
        logger.info(f"✅ Option chain fetched: {len(option_chain)} strikes")
        
        # Step 3: Find best option strike based on momentum + target
        best_option = await self._find_best_option_for_target(
            option_chain=option_chain,
            direction=index_signal['signal'],
            spot_price=spot_price,
            index_target_points=index_signal['target_points'],
            dte=dte
        )
        
        if not best_option:
            logger.warning("⚠️ No suitable option found")
            return self._no_signal(index, spot_price, "No suitable strike found")
        
        logger.info(f"🎯 Best Option: {best_option['strike']} {best_option['type']} @ ₹{best_option['ltp']:.2f}")
        
        # Step 4: Calculate option premium targets
        option_targets = self._calculate_option_targets(
            best_option,
            index_signal['target_points'],
            spot_price
        )
        
        # Step 5: Build complete signal
        complete_signal = self._build_complete_signal(
            index_signal=index_signal,
            option=best_option,
            targets=option_targets,
            index=index,
            spot_price=spot_price
        )
        
        logger.info("=" * 70)
        logger.info(f"✅ SIGNAL READY: {complete_signal['action']}")
        logger.info(f"📍 Strike: {complete_signal['option']['strike']} {complete_signal['option']['type']}")
        logger.info(f"💰 Entry: ₹{complete_signal['option']['entry_price']:.2f}")
        logger.info(f"🎯 Target: ₹{complete_signal['targets']['target_1_price']:.2f} (+{complete_signal['targets']['target_1_points']:.0f} pts)")
        logger.info(f"🛑 Stop: ₹{complete_signal['targets']['stop_loss_price']:.2f} (-{complete_signal['targets']['stop_loss_points']:.0f} pts)")
        logger.info("=" * 70)
        
        return complete_signal
    
    # ==================== STEP 1: INDEX MOMENTUM ====================
    
    async def _analyze_index_momentum(self, candles, spot, dte):
        """Analyze index momentum using 3-tier system"""
        
        tf_15m = candles.get('15')
        tf_1h = candles.get('60')
        tf_4h = candles.get('240')
        tf_daily = candles.get('D')
        
        atr = self._calculate_atr(tf_daily) if tf_daily is not None else 50
        
        # Tier 1: Perfect setup
        tier1 = self._tier1_fvg_ob(tf_15m, tf_1h, spot, atr)
        if tier1:
            return tier1
        
        # Tier 2: Momentum
        tier2 = self._tier2_momentum(tf_15m, tf_1h, tf_4h, spot, atr)
        if tier2:
            return tier2
        
        # Tier 3: EMA
        tier3 = self._tier3_ema(tf_15m, spot, atr)
        if tier3:
            return tier3
        
        return {'signal': 'WAIT', 'confidence': 0}
    
    def _tier1_fvg_ob(self, tf_15m, tf_1h, price, atr):
        """Tier 1: FVG/OB setup"""
        if tf_15m is None or len(tf_15m) < 30:
            return None
        
        # FVGs
        fvgs = self._find_fvgs(tf_15m, 20)
        for fvg in fvgs:
            mid = (fvg['high'] + fvg['low']) / 2
            if abs(price - mid) / price * 100 < 0.3:
                htf = self._get_trend(tf_1h)
                if htf == fvg['type'] or htf != 'neutral':
                    return {
                        'signal': 'BUY' if fvg['type'] == 'bullish' else 'SELL',
                        'confidence': 80,
                        'target_points': min(15, int(atr * 0.3)),
                        'tier': 1,
                        'setup': 'FVG_RETEST'
                    }
        
        # Order Blocks
        obs = self._find_order_blocks(tf_15m, 25)
        for ob in obs:
            if ob['low'] <= price <= ob['high']:
                htf = self._get_trend(tf_1h)
                if htf == ob['type']:
                    return {
                        'signal': 'BUY' if ob['type'] == 'bullish' else 'SELL',
                        'confidence': 75,
                        'target_points': min(15, int(atr * 0.3)),
                        'tier': 1,
                        'setup': 'ORDER_BLOCK'
                    }
        return None
    
    def _tier2_momentum(self, tf_15m, tf_1h, tf_4h, price, atr):
        """Tier 2: HTF momentum"""
        if tf_1h is None:
            return None
        
        trend_1h = self._get_trend(tf_1h)
        trend_4h = self._get_trend(tf_4h) if tf_4h is not None else 'neutral'
        
        if trend_1h == 'neutral' or (trend_4h not in [trend_1h, 'neutral']):
            return None
        
        if tf_15m is not None:
            mom = self._check_rsi(tf_15m)
            if mom['direction'] == trend_1h and mom['strength'] > 0.5:
                if self._at_ema(tf_15m, price):
                    return {
                        'signal': 'BUY' if trend_1h == 'bullish' else 'SELL',
                        'confidence': 65,
                        'target_points': min(10, int(atr * 0.2)),
                        'tier': 2,
                        'setup': 'HTF_MOMENTUM'
                    }
        return None
    
    def _tier3_ema(self, tf_15m, price, atr):
        """Tier 3: EMA crossover"""
        if tf_15m is None or len(tf_15m) < 25:
            return None
        
        close = tf_15m['close']
        ema9 = close.ewm(span=9).mean()
        ema21 = close.ewm(span=21).mean()
        
        for i in range(-3, 0):
            now = ema9.iloc[i] > ema21.iloc[i]
            prev = ema9.iloc[i-1] > ema21.iloc[i-1]
            
            if now != prev:
                dist = abs(ema9.iloc[i] - ema21.iloc[i]) / price * 100
                if dist < 0.15:
                    last_bull = close.iloc[-1] > tf_15m['open'].iloc[-1]
                    if (now and last_bull) or (not now and not last_bull):
                        return {
                            'signal': 'BUY' if now else 'SELL',
                            'confidence': 58,
                            'target_points': max(5, int(atr * 0.1)),
                            'tier': 3,
                            'setup': 'EMA_CROSS'
                        }
        return None
    
    # ==================== STEP 2: FETCH OPTION CHAIN ====================
    
    async def _fetch_option_chain(self, index: str) -> Optional[List[Dict]]:
        """
        Fetch live option chain from Fyers
        Returns list of strikes with LTP, Greeks, OI, Volume
        """
        try:
            # Map index name to Fyers symbol
            index_map = {
                "NIFTY": "NSE:NIFTY50-INDEX",
                "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
                "FINNIFTY": "NSE:FINNIFTY-INDEX",
                "SENSEX": "BSE:SENSEX-INDEX",
                "BANKEX": "BSE:BANKEX-INDEX",
                "MIDCPNIFTY": "NSE:MIDCPNIFTY-INDEX"
            }
            
            fyers_symbol = index_map.get(index)
            if not fyers_symbol:
                logger.error(f"Unknown index: {index}")
                return None
            
            # Use existing Fyers option chain method
            chain_response = self.fyers.get_option_chain(
                symbol=fyers_symbol,
                strike_count=15  # Get 15 strikes above and below ATM
            )
            
            # Log the full response for debugging
            logger.info(f"Fyers option chain response status: {chain_response.get('s') if chain_response else 'None'}")
            if chain_response:
                logger.info(f"Response keys: {list(chain_response.keys())}")
                if chain_response.get('d'):
                    logger.info(f"Data keys: {list(chain_response.get('d', {}).keys())}")
            
            if not chain_response or chain_response.get('s') != 'ok':
                logger.error(f"Failed to fetch option chain: {chain_response}")
                return None
            
            # Parse option chain data
            options = []
            chain_data = chain_response.get('d', {}).get('optionsChain', [])
            
            for strike_data in chain_data:
                strike_price = strike_data.get('strike_price', 0)
                
                # CE (Call)
                ce_data = strike_data.get('call_options', {})
                if ce_data and ce_data.get('ltp', 0) > 0:
                    options.append({
                        'strike': strike_price,
                        'type': 'CE',
                        'ltp': ce_data.get('ltp', 0),
                        'bid': ce_data.get('bid', 0),
                        'ask': ce_data.get('ask', 0),
                        'delta': ce_data.get('delta', 0.5),  # Default if not available
                        'gamma': ce_data.get('gamma', 0),
                        'theta': ce_data.get('theta', 0),
                        'vega': ce_data.get('vega', 0),
                        'iv': ce_data.get('iv', 0),
                        'oi': ce_data.get('oi', 0),
                        'volume': ce_data.get('volume', 0),
                        'symbol': ce_data.get('trading_symbol', '')
                    })
                
                # PE (Put)
                pe_data = strike_data.get('put_options', {})
                if pe_data and pe_data.get('ltp', 0) > 0:
                    options.append({
                        'strike': strike_price,
                        'type': 'PE',
                        'ltp': pe_data.get('ltp', 0),
                        'bid': pe_data.get('bid', 0),
                        'ask': pe_data.get('ask', 0),
                        'delta': pe_data.get('delta', -0.5),  # Default if not available
                        'gamma': pe_data.get('gamma', 0),
                        'theta': pe_data.get('theta', 0),
                        'vega': pe_data.get('vega', 0),
                        'iv': pe_data.get('iv', 0),
                        'oi': pe_data.get('oi', 0),
                        'volume': pe_data.get('volume', 0),
                        'symbol': pe_data.get('trading_symbol', '')
                    })
            
            return options if options else None
        
        except Exception as e:
            logger.error(f"Error fetching option chain: {e}")
            return None
    
    # ==================== STEP 3: FIND BEST OPTION ====================
    
    async def _find_best_option_for_target(
        self,
        option_chain: List[Dict],
        direction: str,
        spot_price: float,
        index_target_points: int,
        dte: int
    ) -> Optional[Dict]:
        """
        Find best option strike that can achieve 5/10/15 point target
        
        Criteria:
        1. Strike selection based on momentum
        2. Sufficient delta (0.3-0.7 for movement)
        3. Good liquidity (volume > 1000, OI > 5000)
        4. Premium range (₹50-300 for affordability)
        """
        
        # CRITICAL FIX: Determine option type based on ICT levels + HTF bias + ML
        # Instead of simple: 'CE' if direction == 'BUY' else 'PE'
        option_type = self._determine_option_type_from_ict(
            direction=direction,
            spot_price=spot_price
        )
        
        logger.info(f"📊 Option Type Selected: {option_type} (based on ICT + HTF + ML)")
        
        # Filter options
        candidates = [
            opt for opt in option_chain
            if opt['type'] == option_type
            and opt['ltp'] > 50  # Min premium
            and opt['ltp'] < 300  # Max premium (affordable)
            and opt['volume'] > 500  # Min liquidity
            and abs(opt['delta']) > 0.25  # Min delta for movement
        ]
        
        if not candidates:
            logger.warning("No liquid options found in ₹50-300 range")
            return None
        
        # Score each option
        scored = []
        for opt in candidates:
            score = self._score_option_for_momentum(
                opt, 
                spot_price, 
                index_target_points,
                dte
            )
            scored.append((score, opt))
        
        # Sort by score
        scored.sort(reverse=True, key=lambda x: x[0])
        
        # Return best option
        if scored:
            best_score, best_opt = scored[0]
            logger.info(f"Selected {best_opt['strike']} {best_opt['type']} (score: {best_score:.2f})")
            return best_opt
        
        return None
    
    def _score_option_for_momentum(
        self, 
        option: Dict, 
        spot: float,
        index_points: int,
        dte: int
    ) -> float:
        """
        Score option based on:
        - Delta (higher = more movement)
        - Moneyness (ATM/slight OTM best)
        - Liquidity (volume + OI)
        - Premium affordability
        """
        score = 0
        
        # Delta score (0.4-0.6 is ideal for point targets)
        delta = abs(option['delta'])
        if 0.4 <= delta <= 0.6:
            score += 40
        elif 0.3 <= delta < 0.4 or 0.6 < delta <= 0.7:
            score += 25
        elif 0.2 <= delta < 0.3:
            score += 10
        
        # Moneyness score
        distance = abs(option['strike'] - spot) / spot * 100
        if distance < 0.5:  # Near ATM
            score += 30
        elif distance < 1.0:  # Slight OTM
            score += 20
        elif distance < 1.5:
            score += 10
        
        # Liquidity score
        if option['volume'] > 5000:
            score += 20
        elif option['volume'] > 2000:
            score += 15
        elif option['volume'] > 1000:
            score += 10
        
        # Premium affordability
        if 80 <= option['ltp'] <= 150:
            score += 10  # Sweet spot
        elif 50 <= option['ltp'] < 80 or 150 < option['ltp'] <= 200:
            score += 5
        
        return score
    
    # ==================== STEP 4: CALCULATE OPTION TARGETS ====================
    
    def _calculate_option_targets(
        self,
        option: Dict,
        index_points: int,
        spot: float
    ) -> Dict:
        """
        Calculate option premium targets based on delta
        
        Formula:
        Option movement ≈ Index movement × Delta
        
        Example:
        - Index moves 10 points
        - Option delta = 0.5
        - Option moves ≈ 10 × 0.5 × 0.7 = 3.5 points premium
        """
        
        entry_price = option['ltp']
        delta = abs(option['delta'])
        
        # Conservative estimate (delta decreases as option moves)
        # Use 70% of theoretical delta movement
        option_movement = index_points * delta * 0.7
        
        # Ensure minimum targets
        if index_points >= 15:  # Tier 1
            target_1_points = max(15, option_movement)
            target_2_points = max(25, option_movement * 1.5)
            stop_points = max(20, option_movement * 1.3)
        elif index_points >= 10:  # Tier 2
            target_1_points = max(10, option_movement)
            target_2_points = max(18, option_movement * 1.5)
            stop_points = max(15, option_movement * 1.5)
        else:  # Tier 3
            target_1_points = max(5, option_movement)
            target_2_points = max(10, option_movement * 1.8)
            stop_points = max(10, option_movement * 2)
        
        return {
            'entry_price': entry_price,
            'target_1_points': round(target_1_points, 1),
            'target_1_price': round(entry_price + target_1_points, 2),
            'target_2_points': round(target_2_points, 1),
            'target_2_price': round(entry_price + target_2_points, 2),
            'stop_loss_points': round(stop_points, 1),
            'stop_loss_price': round(entry_price - stop_points, 2),
            'expected_index_move': index_points,
            'delta_used': delta
        }
    
    # ==================== STEP 5: BUILD COMPLETE SIGNAL ====================
    
    def _build_complete_signal(
        self,
        index_signal: Dict,
        option: Dict,
        targets: Dict,
        index: str,
        spot_price: float
    ) -> Dict:
        """Build final signal with all details"""
        
        lot_size = LOT_SIZES.get(index, 50)
        
        return {
            'signal': index_signal['signal'],
            'action': f"{index_signal['signal']} {option['type']}",
            'confidence': {
                'score': index_signal['confidence'],
                'level': 'HIGH' if index_signal['confidence'] >= 75 else 'MEDIUM'
            },
            'tier': index_signal['tier'],
            'setup_type': index_signal['setup'],
            
            # Option details
            'option': {
                'strike': option['strike'],
                'type': option['type'],
                'entry_price': targets['entry_price'],
                'symbol': option['symbol'],
                'delta': option['delta'],
                'gamma': option['gamma'],
                'theta': option['theta'],
                'iv': option['iv'],
                'volume': option['volume'],
                'oi': option['oi']
            },
            
            # Targets in option premium
            'targets': {
                'target_1_points': targets['target_1_points'],
                'target_1_price': targets['target_1_price'],
                'target_2_points': targets['target_2_points'],
                'target_2_price': targets['target_2_price'],
                'stop_loss_points': targets['stop_loss_points'],
                'stop_loss_price': targets['stop_loss_price']
            },
            
            # Risk/Reward
            'risk_reward': {
                'risk_per_lot': round(targets['stop_loss_points'] * lot_size, 2),
                'reward_1_per_lot': round(targets['target_1_points'] * lot_size, 2),
                'reward_2_per_lot': round(targets['target_2_points'] * lot_size, 2),
                'ratio_1': f"1:{targets['target_1_points'] / targets['stop_loss_points']:.1f}",
                'ratio_2': f"1:{targets['target_2_points'] / targets['stop_loss_points']:.1f}"
            },
            
            # Index context
            'index_context': {
                'spot_price': spot_price,
                'expected_move': targets['expected_index_move'],
                'delta_factor': targets['delta_used']
            },
            
            'lot_size': lot_size,
            'timestamp': datetime.now().isoformat()
        }
    
    
    # ==================== ICT-BASED OPTION TYPE SELECTION ====================
    
    def _determine_option_type_from_ict(
        self,
        direction: str,
        spot_price: float
    ) -> str:
        """
        Determine CE or PE based on ICT levels, HTF bias, and ML confirmation
        
        Priority:
        1. ICT key levels (resistance → PE, support → CE)
        2. HTF bias (bearish → PE, bullish → CE)
        3. ML confirmation (bearish stocks → PE, bullish stocks → CE)
        4. Fallback to direction
        
        Returns:
            'CE' for Call options, 'PE' for Put options
        """
        
        logger.info("🎯 Determining Option Type (ICT + HTF + ML):")
        
        # Step 1: Check ICT key levels (highest priority)
        if self.cached_candles:
            tf_1h = self.cached_candles.get('60')
            tf_4h = self.cached_candles.get('240')
            
            if tf_1h is not None:
                # Find nearest resistance/support zones
                resistance_zones = self._find_resistance_zones(tf_1h, tf_4h, spot_price)
                support_zones = self._find_support_zones(tf_1h, tf_4h, spot_price)
                
                # Check if price is at resistance (within 0.3%)
                at_resistance = any(
                    abs(spot_price - zone) / spot_price < 0.003 
                    for zone in resistance_zones
                )
                
                # Check if price is at support (within 0.3%)
                at_support = any(
                    abs(spot_price - zone) / spot_price < 0.003 
                    for zone in support_zones
                )
                
                if at_resistance:
                    logger.info(f"   🔴 Price at RESISTANCE ({resistance_zones[0]:.2f}) → PE (Put)")
                    return 'PE'
                elif at_support:
                    logger.info(f"   🟢 Price at SUPPORT ({support_zones[0]:.2f}) → CE (Call)")
                    return 'CE'
        
        # Step 2: Use HTF bias (second priority) - CRITICAL FIX: Lowered threshold to >=30
        if self.cached_htf_bias:
            htf_direction = self.cached_htf_bias.get('overall_direction', 'neutral')
            htf_strength = self.cached_htf_bias.get('bias_strength', 0)
            
            # FIXED: Lowered threshold from >60 to >=30 to use HTF bias more often
            if htf_direction == 'bearish' and htf_strength >= 30:
                logger.info(f"   📉 HTF BEARISH (strength: {htf_strength:.0f}) → PE (Put)")
                return 'PE'
            elif htf_direction == 'bullish' and htf_strength >= 30:
                logger.info(f"   📈 HTF BULLISH (strength: {htf_strength:.0f}) → CE (Call)")
                return 'CE'
        
        # Step 3: Direction-based fallback (REMOVED ML override - it was conflicting with HTF)
        # When HTF is neutral/weak, use the direction passed from the caller
        fallback_type = 'CE' if direction == 'BUY' else 'PE'
        logger.info(f"   ⚠️ Using direction fallback: {direction} → {fallback_type}")
        return fallback_type
    
    def _find_resistance_zones(self, tf_1h, tf_4h, current_price):
        """Find ICT resistance zones (bearish OBs, bearish FVGs, swing highs)"""
        zones = []
        
        # Bearish Order Blocks from 1H
        obs = self._find_order_blocks(tf_1h, 25)
        for ob in obs:
            if ob['type'] == 'bearish' and ob['high'] >= current_price * 0.995:
                zones.append(ob['high'])
        
        # Bearish FVGs from 1H
        fvgs = self._find_fvgs(tf_1h, 20)
        for fvg in fvgs:
            if fvg['type'] == 'bearish' and fvg['low'] >= current_price * 0.995:
                zones.append(fvg['low'])
        
        # Swing highs from 4H
        if tf_4h is not None and len(tf_4h) > 20:
            recent_highs = tf_4h['high'].tail(20).nlargest(3)
            for high in recent_highs:
                if high >= current_price * 0.995:
                    zones.append(high)
        
        # Return top 5 nearest zones above current price
        unique_zones = sorted(set(zones))
        return [z for z in unique_zones if z >= current_price][:5]
    
    def _find_support_zones(self, tf_1h, tf_4h, current_price):
        """Find ICT support zones (bullish OBs, bullish FVGs, swing lows)"""
        zones = []
        
        # Bullish Order Blocks from 1H
        obs = self._find_order_blocks(tf_1h, 25)
        for ob in obs:
            if ob['type'] == 'bullish' and ob['low'] <= current_price * 1.005:
                zones.append(ob['low'])
        
        # Bullish FVGs from 1H
        fvgs = self._find_fvgs(tf_1h, 20)
        for fvg in fvgs:
            if fvg['type'] == 'bullish' and fvg['high'] <= current_price * 1.005:
                zones.append(fvg['high'])
        
        # Swing lows from 4H
        if tf_4h is not None and len(tf_4h) > 20:
            recent_lows = tf_4h['low'].tail(20).nsmallest(3)
            for low in recent_lows:
                if low <= current_price * 1.005:
                    zones.append(low)
        
        # Return top 5 nearest zones below current price
        unique_zones = sorted(set(zones), reverse=True)
        return [z for z in unique_zones if z <= current_price][:5]
    
    # ==================== HELPERS ====================
    
    def _find_fvgs(self, df, lookback=20):
        """Find Fair Value Gaps"""
        fvgs = []
        for i in range(len(df) - 3, max(len(df) - lookback, 2), -1):
            c1_h, c1_l = df['high'].iloc[i-2], df['low'].iloc[i-2]
            c3_h, c3_l = df['high'].iloc[i], df['low'].iloc[i]
            if c1_h < c3_l and (c3_l - c1_h) / df['close'].iloc[i] > 0.0015:
                fvgs.append({'type': 'bullish', 'high': c3_l, 'low': c1_h})
            elif c1_l > c3_h and (c1_l - c3_h) / df['close'].iloc[i] > 0.0015:
                fvgs.append({'type': 'bearish', 'high': c1_l, 'low': c3_h})
        return fvgs[:5]
    
    def _find_order_blocks(self, df, lookback=25):
        """Find Order Blocks"""
        obs = []
        for i in range(len(df) - 2, max(len(df) - lookback, 1), -1):
            curr = df['close'].iloc[i] - df['open'].iloc[i]
            next_m = df['close'].iloc[i+1] - df['open'].iloc[i+1]
            if curr < 0 and next_m > 0 and next_m > 1.5 * abs(curr):
                obs.append({'type': 'bullish', 'high': df['high'].iloc[i], 'low': df['low'].iloc[i]})
            elif curr > 0 and next_m < 0 and abs(next_m) > 1.5 * abs(curr):
                obs.append({'type': 'bearish', 'high': df['high'].iloc[i], 'low': df['low'].iloc[i]})
        return obs[:5]
    
    def _get_trend(self, df):
        """Get trend direction from EMAs"""
        if df is None or len(df) < 50:
            return 'neutral'
        close = df['close']
        ema20 = close.ewm(span=20).mean()
        ema50 = close.ewm(span=50).mean()
        if ema20.iloc[-1] > ema50.iloc[-1] and close.iloc[-1] > ema20.iloc[-1]:
            return 'bullish'
        elif ema20.iloc[-1] < ema50.iloc[-1] and close.iloc[-1] < ema20.iloc[-1]:
            return 'bearish'
        return 'neutral'
    
    def _check_rsi(self, df):
        """Check RSI momentum"""
        if df is None or len(df) < 14:
            return {'direction': 'neutral', 'strength': 0}
        close = df['close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss))
        curr = rsi.iloc[-1]
        if curr > 60:
            return {'direction': 'bullish', 'strength': (curr - 50) / 50}
        elif curr < 40:
            return {'direction': 'bearish', 'strength': (50 - curr) / 50}
        return {'direction': 'neutral', 'strength': 0.3}
    
    def _at_ema(self, df, price):
        """Check if price is near EMA20"""
        ema20 = df['close'].ewm(span=20).mean().iloc[-1]
        return abs(price - ema20) / price * 100 < 0.3
    
    def _calculate_atr(self, df, period=14):
        """Calculate ATR"""
        if df is None or len(df) < period:
            return 50
        h, l, c = df['high'], df['low'], df['close']
        tr = pd.concat([h - l, abs(h - c.shift()), abs(l - c.shift())], axis=1).max(axis=1)
        return tr.rolling(period).mean().iloc[-1]
    
    def _no_signal(self, index, price, reason):
        """Return no signal"""
        return {
            'signal': 'WAIT',
            'action': 'WAIT',
            'confidence': {'score': 0, 'level': 'NONE'},
            'reasoning': [reason],
            'timestamp': datetime.now().isoformat()
        }


# Global analyzer instance (will be initialized with fyers_client in main.py)
option_aware_ict = None
