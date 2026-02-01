"""
NEW: ICT Top-Down Signal Generation Function
This will be inserted into main.py at line 2708 (before _generate_actionable_signal)
"""

def _generate_actionable_signal_topdown(mtf_result, session_info, chain_data, historical_prices=None, probability_analysis=None, use_new_flow=True):
    """
    Generate trading signal using ICT top-down methodology
    
    Flow: HTF Bias → LTF Entry → Confirmation Stack (ML + Candlesticks + Futures) → Confidence
    
    Args:
        mtf_result: Multi-timeframe ICT analysis result
        session_info: Market session information
        chain_data: Option chain data
        historical_prices: Historical price data for ML
        probability_analysis: Constituent stock analysis
        use_new_flow: If True, use new ICT-first flow; if False, fall back to old flow
    
    Returns:
        Complete signal dictionary with ICT analysis, confirmations, and confidence breakdown
    """
    
    if not use_new_flow:
        # Feature flag: Fall back to old flow
        return _generate_actionable_signal(mtf_result, session_info, chain_data, historical_prices, probability_analysis)
    
    spot_price = mtf_result.current_price
    session = session_info.current_session
    
    logger.info("=" * 70)
    logger.info("🎯 ICT TOP-DOWN SIGNAL GENERATION (NEW FLOW)")
    logger.info("=" * 70)
    
    # ==================== PHASE 1: DATA VALIDATION ====================
    logger.info("\n📊 Phase 1: Data Validation")
    
    # Get expiry and basic option data
    dte = chain_data.get("days_to_expiry", 7)
    time_to_expiry = max(dte / 365.0, 0.001)
    atm_iv = chain_data.get("atm_iv", 15) / 100 if chain_data.get("atm_iv") else 0.15
    atm_strike = chain_data.get("atm_strike", round(spot_price / 50) * 50)
    expiry_date = chain_data.get("expiry_date", "Unknown")
    
    logger.info(f"   Spot Price: ₹{spot_price}")
    logger.info(f"   ATM Strike: {atm_strike}")
    logger.info(f"   DTE: {dte} days")
    logger.info(f"   IV: {atm_iv * 100:.1f}%")
    
    # ==================== PHASE 2: ICT TOP-DOWN ANALYSIS ====================
    logger.info("\n📈 Phase 2: ICT Top-Down Analysis (HTF → LTF)")
    
    # Prepare multi-timeframe candles from mtf_result
    candles_by_timeframe = {}
    for tf, analysis in mtf_result.analyses.items():
        if hasattr(analysis, 'candles') and analysis.candles is not None:
            candles_by_timeframe[tf] = analysis.candles
    
    # Run complete top-down ICT analysis
    topdown_result = analyze_multi_timeframe_ict_topdown(
        candles_by_timeframe=candles_by_timeframe,
        current_price=spot_price
    )
    
    htf_bias = topdown_result['htf_bias']
    ltf_entry = topdown_result['ltf_entry']
    
    logger.info(f"\n   ✅ HTF BIAS:")
    logger.info(f"      Direction: {htf_bias.overall_direction.upper()}")
    logger.info(f"      Strength: {htf_bias.bias_strength:.1f}/100")
    logger.info(f"      Structure: {htf_bias.structure_quality}")
    logger.info(f"      Premium/Discount: {htf_bias.premium_discount.upper()}")
    logger.info(f"      Key Zones: {len(htf_bias.key_zones)}")
    
    if ltf_entry:
        logger.info(f"\n   ✅ LTF ENTRY MODEL FOUND:")
        logger.info(f"      Type: {ltf_entry.entry_type}")
        logger.info(f"      Timeframe: {ltf_entry.timeframe}")
        logger.info(f"      Entry Zone: ₹{ltf_entry.entry_zone[0]:.2f} - ₹{ltf_entry.entry_zone[1]:.2f}")
        logger.info(f"      Trigger: ₹{ltf_entry.trigger_price:.2f}")
        logger.info(f"      Momentum: {'✅' if ltf_entry.momentum_confirmed else '❌'}")
        logger.info(f"      Alignment: {ltf_entry.alignment_score:.0f}%")
        logger.info(f"      Confidence: {ltf_entry.confidence:.2%}")
    else:
        logger.info(f"\n   ⚠️ NO LTF ENTRY MODEL FOUND")
        logger.info(f"      Will use HTF bias for trade direction")
    
    # ==================== PHASE 3: CONFIRMATION STACK ====================
    logger.info("\n🔍 Phase 3: Confirmation Stack (ML + Candlesticks + Futures)")
    
    # 3.1: ML Prediction (15% weight - CONFIRMATION ONLY)
    ml_signal = None
    ml_direction = 'neutral'
    ml_confidence = 0
    
    if historical_prices is not None and len(historical_prices) >= 50:
        try:
            ml_result = get_ml_signal(historical_prices, steps=1)
            
            if ml_result.get('success'):
                ensemble = ml_result['predictions'].get('ensemble', {})
                ml_direction = ensemble.get('direction', 'neutral')
                ml_confidence = ensemble.get('direction_confidence', 0)
                
                ml_signal = {
                    'direction': ml_direction,
                    'confidence': ml_confidence,
                    'predicted_price': ensemble.get('predicted_price', spot_price),
                    'price_change_pct': ensemble.get('price_change_pct', 0),
                    'arima': ml_result['predictions'].get('arima', {}),
                    'lstm': ml_result['predictions'].get('lstm', {}),
                    'momentum': ml_result['predictions'].get('momentum', {})
                }
                
                # Check alignment with HTF bias
                agrees_with_htf = ml_direction == htf_bias.overall_direction
                logger.info(f"\n   🤖 ML PREDICTION:")
                logger.info(f"      Direction: {ml_direction.upper()}")
                logger.info(f"      Confidence: {ml_confidence:.1%}")
                logger.info(f"      Alignment: {'✅ AGREES' if agrees_with_htf else '⚠️ CONFLICTS'} with HTF")
                
        except Exception as e:
            logger.warning(f"   ⚠️ ML prediction failed: {e}")
    else:
        logger.info(f"   ⚠️ Insufficient data for ML (need 50+ candles)")
    
    # 3.2: Candlestick Pattern Analysis (10% weight)
    candlestick_analysis = None
    try:
        candlestick_analysis = analyze_candlestick_patterns(
            candles_by_timeframe, 
            expected_direction=htf_bias.overall_direction
        )
        
        confluence = candlestick_analysis['confluence_analysis']
        logger.info(f"\n   🕯️ CANDLESTICK PATTERNS:")
        logger.info(f"      Confluence Score: {confluence['confluence_score']:.1f}/100")
        logger.info(f"      Confidence: {confluence['confidence_level']}")
        logger.info(f"      Aligned: {confluence['aligned_patterns']}")
        logger.info(f"      Conflicting: {confluence['conflicting_patterns']}")
        
    except Exception as e:
        logger.warning(f"   ⚠️ Candlestick analysis failed: {e}")
    
    # 3.3: Futures Sentiment Analysis (5% weight)
    futures_data = chain_data.get("futures_data")
    futures_sentiment = 'neutral'
    futures_basis_pct = 0
    
    if futures_data:
        futures_basis_pct = futures_data.get("basis_pct", 0)
        
        if futures_basis_pct > 0.3:
            futures_sentiment = 'bullish'
        elif futures_basis_pct < -0.1:
            futures_sentiment = 'bearish'
        
        agrees_with_htf = futures_sentiment == htf_bias.overall_direction or futures_sentiment == 'neutral'
        logger.info(f"\n   📊 FUTURES SENTIMENT:")
        logger.info(f"      Basis: {futures_basis_pct:.3f}%")
        logger.info(f"      Sentiment: {futures_sentiment.upper()}")
        logger.info(f"      Alignment: {'✅ AGREES' if agrees_with_htf else '⚠️ CONFLICTS'} with HTF")
    
    # 3.4: Constituent Stock Analysis (5% weight)
    constituent_direction = 'neutral'
    constituent_confidence = 0
    
    if probability_analysis and not probability_analysis.get('error'):
        constituent_direction = probability_analysis.get('expected_direction', 'NEUTRAL').lower()
        constituent_confidence = probability_analysis.get('confidence', 0)
        
        agrees_with_htf = constituent_direction == htf_bias.overall_direction
        logger.info(f"\n   🏢 CONSTITUENT STOCKS:")
        logger.info(f"      Direction: {constituent_direction.upper()}")
        logger.info(f"      Confidence: {constituent_confidence:.1f}%")
        logger.info(f"      Alignment: {'✅ AGREES' if agrees_with_htf else '⚠️ CONFLICTS'} with HTF")
    
    # ==================== PHASE 4: TRADE DECISION LOGIC ====================
    logger.info("\n🎯 Phase 4: Trade Decision Logic")
    
    # Determine trade direction (ICT first, but can be overridden by strong LTF momentum!)
    trade_direction = htf_bias.overall_direction
    momentum_override_active = False
    
    # ENHANCEMENT: If HTF is neutral but LTF has a momentum entry, use LTF direction
    if trade_direction == 'neutral' and ltf_entry:
        entry_type = ltf_entry.entry_type if ltf_entry else ''
        if 'MOMENTUM' in entry_type or ltf_entry.alignment_score >= 50:
            # Determine direction from entry type or zone
            if ltf_entry.entry_zone:
                # If trigger price is below current price, expecting up move (bullish)
                # If trigger price is above current price, expecting down move (bearish)
                if 'bullish' in entry_type.lower() or ltf_entry.trigger_price < spot_price:
                    trade_direction = 'bullish'
                elif 'bearish' in entry_type.lower() or ltf_entry.trigger_price > spot_price:
                    trade_direction = 'bearish'
                else:
                    # Infer from FVG/OB direction if available
                    trade_direction = 'bullish'  # Default to bullish on momentum
            
            momentum_override_active = True
            logger.info(f"   🔥 MOMENTUM OVERRIDE: HTF neutral → Using LTF {trade_direction.upper()}")
            logger.info(f"      Entry Type: {entry_type}")
            logger.info(f"      Alignment Score: {ltf_entry.alignment_score}")
    
    # Check for liquidity reversal opportunity
    is_reversal_play = False
    if htf_bias.premium_discount == 'premium' and htf_bias.overall_direction == 'bearish':
        # Price at premium in bearish market - potential liquidity grab before drop
        if ltf_entry and ltf_entry.entry_type in ['FVG_TEST_2ND', 'OB_TEST']:
            is_reversal_play = True
            logger.info(f"   🔄 LIQUIDITY REVERSAL OPPORTUNITY")
            logger.info(f"      Price at PREMIUM in bearish market")
            logger.info(f"      LTF entry model confirms reversal setup")
    
    elif htf_bias.premium_discount == 'discount' and htf_bias.overall_direction == 'bullish':
        # Price at discount in bullish market - potential liquidity grab before rally
        if ltf_entry and ltf_entry.entry_type in ['FVG_TEST_2ND', 'OB_TEST']:
            is_reversal_play = True
            logger.info(f"   🔄 LIQUIDITY REVERSAL OPPORTUNITY")
            logger.info(f"      Price at DISCOUNT in bullish market")
            logger.info(f"      LTF entry model confirms reversal setup")
    
    # Determine option type and strike
    if trade_direction == 'bullish':
        option_type = 'call'
        action = "BUY CALL"
        
        # Select strike based on setup quality
        if ltf_entry and ltf_entry.confidence > 0.6:
            target_delta = 0.50  # ATM for strong setups
        elif htf_bias.bias_strength > 60:
            target_delta = 0.45  # Slightly OTM for strong HTF
        elif momentum_override_active:
            target_delta = 0.45  # Slightly OTM for momentum plays
        else:
            target_delta = 0.40  # OTM for weaker setups
            
    elif trade_direction == 'bearish':
        option_type = 'put'
        action = "BUY PUT"
        
        if ltf_entry and ltf_entry.confidence > 0.6:
            target_delta = 0.50
        elif htf_bias.bias_strength > 60:
            target_delta = 0.45
        elif momentum_override_active:
            target_delta = 0.45
        else:
            target_delta = 0.40
            
    else:  # Still neutral after all checks
        option_type = 'call'  # Default to call in neutral
        action = "WAIT"
        target_delta = 0.40
    
    logger.info(f"   Direction: {trade_direction.upper()}")
    logger.info(f"   Option Type: {option_type.upper()}")
    logger.info(f"   Target Delta: {target_delta}")
    if momentum_override_active:
        logger.info(f"   ⚡ Momentum Override: ACTIVE")
    
    # Delta-based strike selection
    def select_strike_by_delta(target_delta: float, opt_type: str) -> int:
        """Select strike with delta closest to target"""
        strikes_to_check = range(atm_strike - 500, atm_strike + 550, 50)
        best_strike = atm_strike
        best_delta_diff = float('inf')
        
        for s in strikes_to_check:
            try:
                greeks = options_pricer.calculate_greeks(
                    spot_price=spot_price,
                    strike_price=s,
                    time_to_expiry=time_to_expiry,
                    volatility=atm_iv,
                    option_type=opt_type
                )
                delta_diff = abs(abs(greeks['delta']) - target_delta)
                if delta_diff < best_delta_diff:
                    best_delta_diff = delta_diff
                    best_strike = s
            except:
                continue
        return best_strike
    
    strike = select_strike_by_delta(target_delta, option_type)
    logger.info(f"   Selected Strike: {strike}")
    
    # Determine entry trigger
    if ltf_entry:
        entry_trigger = ltf_entry.trigger_price
        timing = f"{ltf_entry.entry_type} on {ltf_entry.timeframe}"
    else:
        if trade_direction == 'bullish':
            entry_trigger = spot_price + 20
            timing = "Bullish bias - enter on momentum"
        elif trade_direction == 'bearish':
            entry_trigger = spot_price - 20
            timing = "Bearish bias - enter on breakdown"
        else:
            entry_trigger = spot_price
            timing = "Wait for clear setup"
    
    #  ==================== PHASE 5: NEW CONFIDENCE SCORING ====================
    logger.info("\n📊 Phase 5: Confidence Calculation (New Hierarchy)")
    
    # Prepare data for confidence calculator
    htf_bias_dict = {
        'overall_direction': htf_bias.overall_direction,
        'bias_strength': htf_bias.bias_strength,
        'structure_quality': htf_bias.structure_quality,
        'premium_discount': htf_bias.premium_discount
    }
    
    ltf_entry_dict = {
        'entry_type': ltf_entry.entry_type if ltf_entry else 'NO_SETUP',
        'timeframe': ltf_entry.timeframe if ltf_entry else 'N/A',
        'momentum_confirmed': ltf_entry.momentum_confirmed if ltf_entry else False,
        'alignment_score': ltf_entry.alignment_score if ltf_entry else 0
    }
    
    ml_signal_dict = {
        'direction': ml_direction,
        'confidence': ml_confidence,
        'agrees_with_htf': ml_direction == htf_bias.overall_direction if ml_direction != 'neutral' else True
    }
    
    futures_dict = {
        'basis_pct': futures_basis_pct,
        'sentiment': futures_sentiment
    }
    
    # Calculate new confidence score
    confidence_breakdown = calculate_trade_confidence(
        htf_bias=htf_bias_dict,
        ltf_entry=ltf_entry_dict,
        ml_signal=ml_signal_dict,
        candlestick_analysis=candlestick_analysis,
        futures_data=futures_dict,
        probability_analysis=probability_analysis
    )
    
    total_confidence = confidence_breakdown['total']
    confidence_level = confidence_breakdown['confidence_level']
    
    logger.info(f"\n   📊 CONFIDENCE BREAKDOWN:")
    logger.info(f"      ICT HTF Structure:    {confidence_breakdown['htf_structure']:.1f}/40")
    logger.info(f"      ICT LTF Confirmation: {confidence_breakdown['ltf_confirmation']:.1f}/25")
    logger.info(f"      ML Alignment:         {confidence_breakdown['ml_alignment']:.1f}/15")
    logger.info(f"      Candlestick Patterns: {confidence_breakdown['candlestick']:.1f}/10")
    logger.info(f"      Futures Basis:        {confidence_breakdown['futures_basis']:.1f}/5")
    logger.info(f"      Constituents:         {confidence_breakdown['constituents']:.1f}/5")
    logger.info(f"      {'─' * 50}")
    logger.info(f"      TOTAL CONFIDENCE:     {total_confidence:.1f}/100 ({confidence_level})")
    
    # Calculate pricing and Greeks (same as old flow)
    greeks = options_pricer.calculate_greeks(
        spot_price=spot_price,
        strike_price=strike,
        time_to_expiry=time_to_expiry,
        volatility=atm_iv,
        option_type=option_type
    )
    
    # Find option price from chain
    option_price = None
    price_source = "ESTIMATED"
    strikes = chain_data.get("strikes", [])
    
    if strikes:
        strike_data = next((s for s in strikes if s.get("strike") == strike), None)
        if strike_data:
            option_data = strike_data.get(option_type, {})
            option_price = (option_data.get("ltp") or 
                          option_data.get("ask") or 
                          option_data.get("mid_price"))
            if option_price and option_price > 0:
                price_source = "LIVE_CHAIN"
    
    # Fallback to Black-Scholes if needed
    if not option_price or option_price <= 0:
        option_price = greeks.get('price', spot_price * 0.02)
    
    current_ltp = option_price
    
    # Calculate targets and stop-loss
    if ltf_entry:
        # Use LTF entry zone for tight stop
        if trade_direction == 'bullish':
            stop_loss = option_price * 0.7  # 30% stop
            target_1 = option_price * 1.5   # 50% target
            target_2 = option_price * 2.0   # 100% target
        else:
            stop_loss = option_price * 0.7
            target_1 = option_price * 1.5
            target_2 = option_price * 2.0
    else:
        # Wider stops without LTF confirmation
        stop_loss = option_price * 0.6   # 40% stop
        target_1 = option_price * 1.4    # 40% target
        target_2 = option_price * 1.8    # 80% target
    
    risk_per_lot = (current_ltp - stop_loss) * 50  # NIFTY lot size
    reward_1 = (target_1 - current_ltp) * 50
    reward_2 = (target_2 - current_ltp) * 50
    
    logger.info("=" * 70)
    logger.info("✅ SIGNAL GENERATION COMPLETE")
    logger.info("=" * 70)
    
    # Build the response (enhanced structure)
    signal_type = f"ICT_{trade_direction.upper()}_{'REVERSAL' if is_reversal_play else ltf_entry.entry_type if ltf_entry else 'BIAS'}"
    expiry_date_str = expiry_date if isinstance(expiry_date, str) else expiry_date.strftime("%Y-%m-%d")
    option_suffix = "CE" if option_type == "call" else "PE"
    full_symbol = f"NIFTY{expiry_date_str.replace('-', '')}{strike}{option_suffix}"
    
    return {
        "signal": signal_type,
        "action": action,
        "option": {
            "strike": strike,
            "type": option_suffix,
            "symbol": f"{int(strike)} {option_suffix}",
            "trading_symbol": full_symbol,
            "expiry_date": expiry_date_str,
            "expiry_info": {
                "days_to_expiry": dte,
                "is_weekly": dte <= 7,
                "time_to_expiry_years": round(time_to_expiry, 4)
            }
        },
        "pricing": {
            "ltp": round(current_ltp, 2),
            "entry_price": round(current_ltp, 2),
            "price_source": price_source,
            "iv_used": round(atm_iv * 100, 2)
        },
        "entry": {
            "price": round(current_ltp, 2),
            "trigger_level": round(entry_trigger, 2),
            "timing": timing,
            "session_advice": f"{session} session"
        },
        "targets": {
            "target_1": round(target_1, 2),
            "target_2": round(target_2, 2),
            "stop_loss": round(stop_loss, 2)
        },
        "risk_reward": {
            "risk_per_lot": round(risk_per_lot, 2),
            "reward_1_per_lot": round(reward_1, 2),
            "reward_2_per_lot": round(reward_2, 2),
            "ratio_1": f"1:{(reward_1/risk_per_lot):.1f}" if risk_per_lot > 0 else "N/A",
            "ratio_2": f"1:{(reward_2/risk_per_lot):.1f}" if risk_per_lot > 0 else "N/A"
        },
        "greeks": {
            "delta": round(greeks.get('delta', 0), 4),
            "gamma": round(greeks.get('gamma', 0), 4),
            "theta": round(greeks.get('theta', 0), 4),
            "vega": round(greeks.get('vega', 0), 4)
        },
        # NEW: ICT Analysis Section
        "htf_analysis": {
            "direction": htf_bias.overall_direction,
            "strength": htf_bias.bias_strength,
            "structure_quality": htf_bias.structure_quality,
            "premium_discount": htf_bias.premium_discount,
            "key_zones_count": len(htf_bias.key_zones),
            "timeframe_breakdown": {
                tf: {
                    "trend": analysis.trend,
                    "strength": getattr(analysis, 'trend_strength', 0)
                }
                for tf, analysis in htf_bias.timeframe_breakdowns.items()
            } if hasattr(htf_bias, 'timeframe_breakdowns') else {}
        },
        # NEW: LTF Entry Model
        "ltf_entry_model": {
            "found": ltf_entry is not None,
            "entry_type": ltf_entry.entry_type if ltf_entry else None,
            "timeframe": ltf_entry.timeframe if ltf_entry else None,
            "entry_zone": [round(ltf_entry.entry_zone[0], 2), round(ltf_entry.entry_zone[1], 2)] if ltf_entry else None,
            "trigger_price": round(ltf_entry.trigger_price, 2) if ltf_entry else None,
            "momentum_confirmed": ltf_entry.momentum_confirmed if ltf_entry else False,
            "alignment_score": ltf_entry.alignment_score if ltf_entry else 0,
            "confidence": round(ltf_entry.confidence * 100, 1) if ltf_entry else 0
        },
        # NEW: Confirmation Stack
        "confirmation_stack": {
            "ml_prediction": {
                "direction": ml_direction,
                "confidence": round(ml_confidence * 100, 1) if ml_confidence else 0,
                "agrees_with_htf": ml_direction == htf_bias.overall_direction,
                "price_target": ml_signal['predicted_price'] if ml_signal else None
            } if ml_signal else {"available": False},
            "candlestick_patterns": {
                "confluence_score": candlestick_analysis['confluence_analysis']['confluence_score'] if candlestick_analysis else 0,
                "confidence_level": candlestick_analysis['confluence_analysis']['confidence_level'] if candlestick_analysis else "N/A",
                "aligned_patterns": candlestick_analysis['confluence_analysis']['aligned_patterns'] if candlestick_analysis else 0
            } if candlestick_analysis else {"available": False},
            "futures_sentiment": {
                "basis_pct": round(futures_basis_pct, 3),
                "sentiment": futures_sentiment,
                "agrees_with_htf": futures_sentiment == htf_bias.overall_direction or futures_sentiment == 'neutral'
            } if futures_data else {"available": False},
            "constituents": {
                "direction": constituent_direction,
                "confidence": round(constituent_confidence, 1),
                "agrees_with_htf": constituent_direction == htf_bias.overall_direction
            } if probability_analysis else {"available": False}
        },
        # NEW: Confidence Breakdown
        "confidence_breakdown": {
            "total": round(total_confidence, 1),
            "level": confidence_level,
            "components": {
                "ict_htf_structure": round(confidence_breakdown['htf_structure'], 1),
                "ict_ltf_confirmation": round(confidence_breakdown['ltf_confirmation'], 1),
                "ml_alignment": round(confidence_breakdown['ml_alignment'], 1),
                "candlestick_patterns": round(confidence_breakdown['candlestick'], 1),
                "futures_basis": round(confidence_breakdown['futures_basis'], 1),
                "constituents": round(confidence_breakdown['constituents'], 1)
            },
            "weights": {
                "ict_total": 65,
                "ml": 15,
                "candlestick": 10,
                "market_data": 10
            }
        },
        "confidence": {
            "score": round(total_confidence, 1),
            "level": confidence_level
        },
        "is_reversal_play": is_reversal_play,
        "spot_price": spot_price,
        "timestamp": datetime.now().isoformat()
    }
