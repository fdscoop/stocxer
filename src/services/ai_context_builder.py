"""
Context builder for AI analysis.
Converts scan results and signals into optimized LLM context.
"""
from typing import Dict, Any, List, Optional
import json


def format_signal_context(signal: Dict[str, Any]) -> str:
    """
    Convert a trading signal into concise, structured text for LLM.
    THIS IS THE ACTUAL TRADING RECOMMENDATION - PRIORITIZE THIS DATA.

    Args:
        signal: Trading signal dictionary

    Returns:
        Formatted context string
    """
    from datetime import datetime
    import pytz

    lines = []
    
    # Add current timestamp and market status
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S IST')
    day_of_week = current_time.strftime('%A')
    current_hour = current_time.hour
    current_minute = current_time.minute
    
    # Check if market is open (Mon-Fri, 9:15 AM - 3:30 PM IST)
    is_weekend = current_time.weekday() >= 5  # 5=Saturday, 6=Sunday
    market_open_time = (current_hour > 9 or (current_hour == 9 and current_minute >= 15))
    market_close_time = (current_hour < 15 or (current_hour == 15 and current_minute <= 30))
    is_market_open = not is_weekend and market_open_time and market_close_time
    
    market_status = "OPEN 🟢" if is_market_open else "CLOSED 🔴"
    if is_weekend:
        market_status += f" ({day_of_week})"
    
    lines.append(f"Scan Time: {current_time_str}")
    lines.append(f"Market Status: {market_status}")
    lines.append("")

    # Basic signal info - THE MOST IMPORTANT PART
    action = signal.get("action", "UNKNOWN")
    direction = signal.get("direction", "UNKNOWN")
    
    # Get BOTH confidence values to avoid confusion
    confidence_obj = signal.get("confidence", {})
    confidence_breakdown = signal.get("confidence_breakdown", {})
    
    # Display confidence is what user sees in dashboard (confidence_breakdown.total)
    # ICT model confidence is the underlying score (confidence.score)
    display_confidence = confidence_breakdown.get("total", confidence_obj.get("score", 0) if isinstance(confidence_obj, dict) else confidence_obj)
    ict_confidence = confidence_obj.get("score", 0) if isinstance(confidence_obj, dict) else 0
    confidence_level = confidence_obj.get("level", "UNKNOWN") if isinstance(confidence_obj, dict) else "UNKNOWN"

    lines.append("🎯 SIGNAL ACTION: " + action)
    lines.append(f"📈 Direction: {direction}")
    
    # Show both confidence values clearly
    if display_confidence != ict_confidence and ict_confidence > 0:
        lines.append(f"💯 Confidence: {display_confidence}% (Signal Strength)")
        lines.append(f"🎲 ICT Model: {ict_confidence}% ({confidence_level} level)")
    else:
        lines.append(f"💯 Confidence: {display_confidence}% ({confidence_level} level)")
    
    # WHY WAIT/BUY/SELL - Critical reasoning
    if action == "WAIT":
        lines.append("")
        lines.append("⚠️ WHY WAIT:")
        # Look for reasoning in multiple possible fields
        entry_analysis = signal.get("entry_analysis", {})
        ltf_entry = signal.get("ltf_entry_model", {})
        htf_analysis = signal.get("htf_analysis", {})
        warnings = signal.get("warnings", [])
        
        if not ltf_entry.get("found"):
            lines.append("• No LTF (lower timeframe) entry trigger found")
        if htf_analysis.get("structure_quality") == "LOW":
            lines.append("• Structure quality is LOW - weak setup")
        if entry_analysis.get("wait_for_pullback"):
            lines.append("• Wait for better entry price (pullback needed)")
        if warnings:
            for warning in warnings[:3]:  # Show top 3 warnings
                lines.append(f"• {warning}")
        if not any([ltf_entry.get("found") is False, htf_analysis.get("structure_quality"), warnings]):
            lines.append("• Entry conditions not yet met - monitoring for trigger")
    
    # Option details - WHAT TO TRADE
    strike = signal.get("strike")
    option_type = signal.get("type")
    entry_price = signal.get("entry_price", 0)
    trading_symbol = signal.get("trading_symbol")
    
    if strike and option_type:
        lines.append("")
        lines.append("💰 WHAT TO TRADE:")
        lines.append(f"• Strike: {strike} {option_type}")
        lines.append(f"• Current Price (LTP): ₹{entry_price:.2f}")
        lines.append(f"• Symbol: {trading_symbol}")
    
    # Targets and stop loss - RISK MANAGEMENT
    target_1 = signal.get("target_1", 0)
    target_2 = signal.get("target_2", 0)
    stop_loss = signal.get("stop_loss", 0)
    risk_reward = signal.get("risk_reward", "N/A")
    
    if target_1 and entry_price:
        lines.append("")
        lines.append("🎯 TARGETS & RISK:")
        lines.append(f"• Target 1: ₹{target_1:.2f} (+{((target_1/entry_price - 1)*100):.0f}%)")
        lines.append(f"• Target 2: ₹{target_2:.2f} (+{((target_2/entry_price - 1)*100):.0f}%)")
        lines.append(f"• Stop Loss: ₹{stop_loss:.2f} ({((stop_loss/entry_price - 1)*100):.0f}%)")
        lines.append(f"• Risk/Reward: {risk_reward}")
    
    # Probability analysis
    prob = signal.get("probability_analysis")
    if prob:
        lines.append("")
        lines.append("📈 CONSTITUENT ANALYSIS:")
        total_stocks = prob.get('stocks_scanned', 0)
        bullish_pct = prob.get('bullish_pct', 0)
        bearish_pct = prob.get('bearish_pct', 0)
        
        lines.append(f"• {total_stocks} stocks analyzed")
        lines.append(f"• Bullish: {bullish_pct:.0f}% | Bearish: {bearish_pct:.0f}%")
        lines.append(f"• Expected Move: {prob.get('expected_move_pct', 0):.2f}%")
        
        # Show top movers
        top_movers = prob.get("top_movers", {})
        if top_movers:
            bullish_stocks = top_movers.get("bullish", [])[:3]
            bearish_stocks = top_movers.get("bearish", [])[:3]
            
            if bullish_stocks:
                stocks_str = ", ".join([s.get("symbol", "") for s in bullish_stocks])
                lines.append(f"• Top Bullish: {stocks_str}")
            if bearish_stocks:
                stocks_str = ", ".join([s.get("symbol", "") for s in bearish_stocks])
                lines.append(f"• Top Bearish: {stocks_str}")
    
    # MTF Analysis
    mtf = signal.get("mtf_analysis")
    if mtf:
        lines.append(f"\nMULTI-TIMEFRAME ANALYSIS:")
        lines.append(f"- Overall Bias: {mtf.get('overall_bias', 'Unknown')}")
        timeframes = mtf.get("timeframes_analyzed", [])
        if timeframes:
            lines.append(f"- Timeframes: {', '.join(timeframes)}")
        
        reversal = mtf.get("trend_reversal")
        if reversal and reversal.get("is_reversal"):
            lines.append(f"- Reversal Detected: {reversal.get('direction')} ({reversal.get('confidence', 0):.0f}% confidence)")
            lines.append(f"  Reason: {reversal.get('reason', 'Unknown')}")
    
    # Setup details
    setup = signal.get("setup_details")
    if setup:
        lines.append(f"\nSETUP DETAILS:")
        lines.append(f"- Type: {setup.get('reversal_type', 'Unknown')}")
        lines.append(f"- Timeframe: {setup.get('timeframe', 'Unknown')}")
        lines.append(f"- FVG Level: {setup.get('fvg_level', 0):.2f}")
        lines.append(f"- Reasoning: {setup.get('reasoning', 'N/A')}")
    
    # Market context
    market = signal.get("market_context")
    if market:
        lines.append("")
        lines.append("📊 MARKET CONTEXT:")
        spot = market.get('spot_price', 0)
        vix = market.get('vix', 0)
        max_pain = market.get('max_pain', 0)
        
        lines.append(f"• Spot Price: ₹{spot:,.2f}")
        if market.get('future_price'):
            lines.append(f"• Future Price: ₹{market.get('future_price', 0):,.2f}")
        lines.append(f"• ATM Strike: {market.get('atm_strike', 0)}")
        
        # VIX with interpretation
        if vix:
            vix_level = "LOW (calm market)" if vix < 15 else "MODERATE" if vix < 20 else "HIGH (volatile)"
            lines.append(f"• VIX: {vix:.2f} ({vix_level})")
        
        # Max Pain with interpretation
        if max_pain:
            distance_from_max_pain = ((spot - max_pain) / max_pain) * 100
            lines.append(f"• Max Pain: {max_pain} ({distance_from_max_pain:+.1f}% from spot)")
            if abs(distance_from_max_pain) < 1:
                lines.append(f"  → Price near max pain - likely to stay range-bound")
        
        if market.get('pcr_oi'):
            lines.append(f"• PCR (OI): {market.get('pcr_oi', 0):.2f}")
    
    # Greeks
    greeks = signal.get("greeks")
    if greeks:
        lines.append("")
        lines.append("📐 GREEKS:")
        delta = greeks.get('delta', 0)
        theta = greeks.get('theta', 0)
        gamma = greeks.get('gamma', 0)
        
        lines.append(f"• Delta: {delta:.3f}")
        lines.append(f"• Gamma: {gamma:.4f}")
        
        # Theta with decay interpretation
        if theta:
            lines.append(f"• Theta: {theta:.2f} (losing ₹{abs(theta):.2f} per day)")
            days_to_expiry = signal.get("days_to_expiry", 7)
            if days_to_expiry <= 3 and abs(theta) > 15:
                lines.append(f"  ⚠️ High theta + only {days_to_expiry} DTE = rapid premium decay!")
        
        if greeks.get('vega'):
            lines.append(f"• Vega: {greeks.get('vega', 0):.2f}")
    
    # Entry analysis
    entry_analysis = signal.get("entry_analysis")
    if entry_analysis:
        lines.append(f"\nENTRY ANALYSIS:")
        lines.append(f"- Entry Grade: {entry_analysis.get('entry_grade', 'C')}")
        lines.append(f"- Recommended Entry: ₹{entry_analysis.get('recommended_entry', 0):.2f}")
        lines.append(f"- Max Acceptable: ₹{entry_analysis.get('max_acceptable_price', 0):.2f}")
        
        if entry_analysis.get('wait_for_pullback'):
            lines.append(f"- CAUTION: Wait for pullback recommended")
    
    # Theta analysis
    theta_analysis = signal.get("theta_analysis")
    if theta_analysis:
        lines.append(f"\nTIME DECAY:")
        lines.append(f"- Decay Phase: {theta_analysis.get('decay_phase', 'Unknown')}")
        lines.append(f"- Daily Decay: {theta_analysis.get('daily_decay_pct', 0):.2f}%")
        lines.append(f"- Risk Level: {theta_analysis.get('risk_level', 'Unknown')}")
        lines.append(f"- Advice: {theta_analysis.get('advice', 'N/A')}")
    
    # Expiry day check
    days_to_expiry = signal.get("days_to_expiry")
    if days_to_expiry is None and market:
        days_to_expiry = market.get("days_to_expiry")
    
    if days_to_expiry == 0:
        lines.append(f"\n⚠️ EXPIRY DAY WARNING: Today is the expiry day for this contract.")
        lines.append(f"STRICT RULE: Do not recommend new entries. Focus on closing existing positions.")

    return "\n".join(lines)


def format_news_context(news_articles: List[Dict], sentiment: Optional[Dict] = None) -> str:
    """Format news and sentiment for LLM context."""
    lines = []
    
    if sentiment:
        lines.append("\nMARKET SENTIMENT ANALYSIS:")
        lines.append(f"- Overall Sentiment: {sentiment.get('overall_sentiment', 'Neutral').upper()}")
        lines.append(f"- Sentiment Score: {sentiment.get('sentiment_score', 0)}")
        lines.append(f"- Market Mood: {sentiment.get('market_mood', 'Unknown')}")
        lines.append(f"- Trading Implication: {sentiment.get('trading_implication', 'N/A')}")
        if sentiment.get("key_themes"):
            lines.append(f"- Key Themes: {', '.join(sentiment.get('key_themes', []))}")
            
    if news_articles:
        lines.append("\nRECENT MARKET NEWS:")
        for i, art in enumerate(news_articles[:5], 1):
            impact = art.get('impact_level', 'low').upper()
            lines.append(f"{i}. [{impact}] {art.get('title')}")
            if art.get('description'):
                lines.append(f"   Summary: {art.get('description')[:150]}...")
                
    return "\n".join(lines)


def format_probability_analysis(prob: Dict[str, Any]) -> str:
    """Format constituent probability analysis."""
    lines = []
    
    lines.append("CONSTITUENT STOCK ANALYSIS:")
    lines.append(f"- Total Stocks: {prob.get('total_stocks', 0)}")
    lines.append(f"- Stocks Analyzed: {prob.get('stocks_scanned', 0)}")
    lines.append(f"- Bullish Stocks: {prob.get('bullish_stocks', 0)} ({prob.get('bullish_pct', 0):.0f}%)")
    lines.append(f"- Bearish Stocks: {prob.get('bearish_stocks', 0)} ({prob.get('bearish_pct', 0):.0f}%)")
    lines.append(f"- Expected Direction: {prob.get('expected_direction', 'NEUTRAL')}")
    lines.append(f"- Expected Move: {prob.get('expected_move_pct', 0):.2f}%")
    lines.append(f"- Confidence: {prob.get('confidence', 0):.0f}%")
    lines.append(f"- Market Regime: {prob.get('market_regime', 'Unknown')}")
    
    # Top movers
    top_movers = prob.get("top_movers")
    if top_movers:
        bullish = top_movers.get("bullish", [])
        if bullish:
            lines.append("\nTOP BULLISH STOCKS:")
            for stock in bullish[:5]:
                lines.append(f"- {stock.get('symbol')}: {stock.get('probability', 0):.0f}% probability")
        
        bearish = top_movers.get("bearish", [])
        if bearish:
            lines.append("\nTOP BEARISH STOCKS:")
            for stock in bearish[:5]:
                lines.append(f"- {stock.get('symbol')}: {stock.get('probability', 0):.0f}% probability")
    
    return "\n".join(lines)


def format_scan_results(scan_data: Dict[str, Any]) -> str:
    """
    Format complete scan results for LLM context.

    Args:
        scan_data: Full scan results dictionary (may have 'results' wrapper from frontend)

    Returns:
        Formatted context string
    """
    from datetime import datetime
    import pytz

    lines = []

    # Handle frontend wrapper - extract actual results if nested
    # Frontend sends: {symbol, expiry, results: [...], probability: {...}}
    if "results" in scan_data and isinstance(scan_data["results"], list):
        # Frontend format: results is an array of signals
        actual_data = scan_data.copy()  # Keep the wrapper, we need probability etc
    elif "results" in scan_data and isinstance(scan_data["results"], dict):
        # Backend format: results is a nested dict
        actual_data = scan_data["results"]
    else:
        actual_data = scan_data

    lines.append("=" * 60)
    lines.append("ACTUAL SCAN DATA FROM USER - THIS IS REAL, LIVE DATA")
    lines.append("=" * 60)

    # Add current timestamp for context
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')
    lines.append(f"Data Retrieved At: {current_time}")
    lines.append("")

    # Header
    index = actual_data.get("index") or scan_data.get("symbol", "UNKNOWN")
    expiry = actual_data.get("expiry", "Unknown")
    lines.append(f"INDEX: {index}")
    lines.append(f"EXPIRY: {expiry}")
    lines.append(f"=" * 50)
    
    # Market data
    market_data = actual_data.get("market_data")
    if market_data:
        lines.append(f"\nMARKET DATA:")
        lines.append(f"- Spot Price: ₹{market_data.get('spot_price', 0):,.2f}")
        lines.append(f"- ATM Strike: {market_data.get('atm_strike', 0)}")
        lines.append(f"- Days to Expiry: {market_data.get('days_to_expiry', 0)}")
        if market_data.get("vix"):
            lines.append(f"- VIX: {market_data['vix']:.2f}")
    
    # Probability analysis - check both locations
    prob = actual_data.get("probability_analysis") or scan_data.get("probability")
    if prob:
        lines.append(f"\n{format_probability_analysis(prob)}")
    
    # Recommended option type
    rec_type = actual_data.get("recommended_option_type") or scan_data.get("recommendedOption")
    if rec_type:
        lines.append(f"\nRECOMMENDED: {rec_type}")
    
    # Top options - can be in "options" or "results" key
    options = actual_data.get("options", []) or actual_data.get("results", [])
    if options:
        lines.append(f"\nTOP {len(options)} SIGNALS:")
        for i, opt in enumerate(options[:5], 1):  # Show top 5
            # Handle different formats
            strike = opt.get('strike') or opt.get('strikePrice')
            opt_type = opt.get('type') or opt.get('optionType')
            ltp = opt.get('ltp') or opt.get('lastPrice') or opt.get('entry_price', 0)
            confidence = opt.get('confidence', 0)
            direction = opt.get('direction', '')
            action = opt.get('action', '')

            lines.append(f"\n{i}. {strike} {opt_type} - {direction} ({action})")
            lines.append(f"   LTP: ₹{ltp:.2f}")
            lines.append(f"   Confidence: {confidence}%")

            volume = opt.get('volume', 0)
            oi = opt.get('oi', 0) or opt.get('openInterest', 0)
            if volume:
                lines.append(f"   Volume: {volume:,}")
            if oi:
                lines.append(f"   OI: {oi:,}")

            # Greeks
            if opt.get('greeks'):
                greeks = opt['greeks']
                lines.append(f"   Delta: {greeks.get('delta', 0):.3f}, Theta: {greeks.get('theta', 0):.2f}")

            if opt.get("probability_boost"):
                lines.append(f"   ⭐ PROBABILITY BOOST")
    
    # MTF analysis
    mtf = actual_data.get("mtf_ict_analysis")
    if mtf:
        lines.append(f"\nMULTI-TIMEFRAME ICT:")
        lines.append(f"- Overall Bias: {mtf.get('overall_bias', 'Unknown')}")
    
    return "\n".join(lines)


def format_multiple_indices(indices_data: List[Dict[str, Any]]) -> str:
    """
    Format multiple index scans for comparison.
    
    Args:
        indices_data: List of scan result dictionaries
    
    Returns:
        Formatted comparison context
    """
    sections = []
    
    for scan in indices_data:
        index = scan.get("index", "UNKNOWN")
        sections.append(f"\n{'=' * 50}")
        sections.append(f"{index} ANALYSIS:")
        sections.append('=' * 50)
        sections.append(format_scan_results(scan))
    
    return "\n".join(sections)


def optimize_context_window(context: str, max_tokens: int = 2500) -> str:
    """
    Optimize context to fit within token limits.
    Rough estimate: 1 token ≈ 4 characters
    
    Args:
        context: Original context string
        max_tokens: Maximum tokens allowed
    
    Returns:
        Trimmed context string
    """
    max_chars = max_tokens * 4
    
    if len(context) <= max_chars:
        return context
    
    # Priority order for sections to keep
    important_keywords = [
        "SIGNAL:",
        "RECOMMENDED OPTION:",
        "TARGETS & RISK:",
        "CONSTITUENT ANALYSIS:",
        "PROBABILITY BOOST",
        "MARKET SENTIMENT ANALYSIS:",
        "RECENT MARKET NEWS:",
        "⚠️ EXPIRY DAY WARNING:",
        "Entry Grade:",
        "Confidence:"
    ]
    
    lines = context.split("\n")
    important_lines = []
    other_lines = []
    
    current_section_important = False
    for line in lines:
        if any(keyword in line for keyword in important_keywords):
            important_lines.append(line)
            current_section_important = True
        elif line.startswith("- ") and current_section_important:
            # Keep bullet points under important headers
            important_lines.append(line)
        else:
            if line.strip() == "":
                current_section_important = False
            other_lines.append(line)
    
    # Start with important lines
    result = "\n".join(important_lines)
    
    # Add other lines until we hit the limit
    for line in other_lines:
        if len(result) + len(line) + 1 <= max_chars:
            result += "\n" + line
        else:
            result += "\n...[Additional data truncated to fit context window]"
            break
    
    return result


def build_query_context(
    query: str,
    scan_data: Optional[Dict[str, Any]] = None,
    signal_data: Optional[Dict[str, Any]] = None,
    comparison_data: Optional[List[Dict[str, Any]]] = None,
    news_data: Optional[List[Dict]] = None,
    sentiment_data: Optional[Dict] = None
) -> str:
    """
    Build complete context for a user query.
    PRIORITY ORDER: Trading Signal > Scan Data > Comparison Data
    
    Args:
        query: User's question
        scan_data: Scan results if available
        signal_data: Specific signal if available (THE ACTUAL TRADE)
        comparison_data: Multiple scans for comparison
        news_data: Recent market news
        sentiment_data: Aggregated sentiment data
    
    Returns:
        Formatted context string with clear sections
    """
    context_parts = []
    
    # PRIORITY 1: Trading Signal (the actual actionable trade)
    if signal_data:
        context_parts.append("=" * 60)
        context_parts.append("📊 TRADING SIGNAL (THE ACTUAL RECOMMENDED TRADE)")
        context_parts.append("=" * 60)
        context_parts.append(format_signal_context(signal_data))
    
    # PRIORITY 2: Scan Data (overview/probability analysis)
    if scan_data:
        context_parts.append("")
        context_parts.append("=" * 60)
        context_parts.append("📈 SCAN OVERVIEW & PROBABILITY ANALYSIS")
        context_parts.append("=" * 60)
        context_parts.append(format_scan_results(scan_data))
    
    # PRIORITY 3: Comparison data
    if comparison_data:
        context_parts.append("")
        context_parts.append("=" * 60)
        context_parts.append("🔄 INDEX COMPARISON")
        context_parts.append("=" * 60)
        context_parts.append(format_multiple_indices(comparison_data))
    
    # Add news context if available
    if news_data or sentiment_data:
        context_parts.append("")
        context_parts.append(format_news_context(news_data or [], sentiment_data))
        
    if not context_parts:
        return """⚠️ NO DATA AVAILABLE
        
The user has not run a scan yet. Please tell them to:
1. Click "Scan NIFTY" (or BANKNIFTY/FINNIFTY) button on the dashboard
2. Wait for the scan to complete (10-15 seconds)
3. Then ask you to analyze the results

You cannot provide trading analysis without actual scan data."""
        
    return "\n".join(context_parts)
