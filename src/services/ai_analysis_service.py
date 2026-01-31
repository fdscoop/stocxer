"""
Core AI analysis service using Cohere for intelligent signal analysis.
"""
import cohere
from typing import Dict, Any, List, Optional
import logging
import os
from datetime import datetime

from src.prompts.signal_explanation import (
    get_prompt_template,
    classify_query,
    get_system_context
)
from src.services.ai_context_builder import (
    build_query_context,
    format_signal_context,
    optimize_context_window
)
from src.services.ai_cache_service import ai_cache
from src.services.ai_cost_optimizer import get_cost_optimizers
from src.services.news_service import news_service
from src.models.ai_models import ChatResponse, Citation

logger = logging.getLogger(__name__)


class CohereAnalysisService:
    """
    AI-powered analysis service for trading signals using Cohere.
    
    Features:
    - Natural language explanations of signals
    - Risk analysis and trade planning
    - Multi-index comparisons
    - Context-aware responses with citations
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "command-r-plus-08-2024"):
        """
        Initialize Cohere AI service.
        
        Args:
            api_key: Cohere API key (defaults to env var)
            model: Cohere model to use (command-r-plus, command-r, command-light)
        """
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError("Cohere API key not provided. Set COHERE_API_KEY environment variable.")
        
        self.model = model
        # Initialize Cohere client with timeout
        self.client = cohere.Client(
            api_key=self.api_key,
            timeout=30  # 30 second timeout for API requests
        )
        logger.info(f"✅ Cohere AI service initialized with model: {model}")
    
    async def analyze_signal(
        self,
        query: str,
        signal_data: Optional[Dict[str, Any]] = None,
        scan_data: Optional[Dict[str, Any]] = None,
        scan_id: Optional[str] = None,
        use_cache: bool = True,
        authorization: Optional[str] = None
    ) -> ChatResponse:
        """
        Analyze a trading signal and answer user query.
        
        Args:
            query: User's question
            signal_data: Specific signal dictionary
            scan_data: Full scan results
            scan_id: Scan ID for caching
            use_cache: Whether to use cached responses
        
        Returns:
            ChatResponse with AI-generated answer
        """
        start_time = datetime.utcnow()
        
        # Get cost optimizers
        cost_tools = get_cost_optimizers()
        deduplicator = cost_tools['deduplicator']
        optimizer = cost_tools['optimizer']
        rate_limiter = cost_tools['rate_limiter']
        
        # Check rate limits first
        can_call, reason = rate_limiter.can_make_call()
        if not can_call:
            logger.warning(f"Rate limit hit: {reason}")
            return ChatResponse(
                response=f"Rate limit exceeded: {reason}. Please try again later.",
                citations=[],
                cached=False,
                tokens_used=0,
                confidence_score=0.0,
                query_type="rate_limited"
            )
        
        # Check for duplicate queries
        duplicate_response = deduplicator.is_duplicate(query, scan_id)
        if duplicate_response:
            logger.info("✅ Query deduplication - returning cached response")
            return ChatResponse(**duplicate_response)
        
        # 1. Classify the query intent
        query_type = classify_query(query)
        
        # 2. Check for Agentic Scan Trigger (Only if scan_data is NOT already provided)
        if query_type == "scan" and authorization and not scan_data:
            index = "NIFTY"
            query_lower = query.lower()
            if "banknifty" in query_lower: index = "BANKNIFTY"
            elif "finnifty" in query_lower: index = "FINNIFTY"
            
            logger.info(f"🤖 Triggering AGENTIC SCAN for {index}...")
            
            try:
                import httpx
                # Call the internal scan endpoint
                async with httpx.AsyncClient(timeout=60.0) as client:
                    # In production, we'd use an env var for the base URL, but for now we'll try to reach ourselves
                    # This respects all existing billing, fyers-auth and scan logic in main.py
                    headers = {"Authorization": authorization}
                    # Always use quick_scan=True for AI requests to keep it under 30s
                    scan_url = f"http://localhost:8000/options/scan?index={index}&quick_scan=True"
                    
                    response = await client.get(scan_url, headers=headers)
                    if response.status_code == 200:
                        scan_results = response.json()
                        logger.info(f"✅ Agentic scan complete for {index}")
                        
                        # Extract the best signal from scan results for analysis
                        signals = scan_results.get("signals", []) or scan_results.get("top_opportunities", [])
                        new_signal_data = signals[0] if signals else None
                        
                        # Recursively call analyze_signal with the fresh scan data
                        # We change query_type to 'explanation' so it analyzes the results it just found
                        return await self.analyze_signal(
                            query=f"Explain the best signal you found in your {index} scan",
                            signal_data=new_signal_data,
                            scan_data=scan_results,
                            use_cache=False,
                            authorization=authorization
                        )
                    else:
                        logger.error(f"❌ Internal scan request failed: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"❌ Agentic scan error: {str(e)}")
        
        # Check cache
        if use_cache and ai_cache and scan_id:
            cached = await ai_cache.get_cached_response(query, scan_id)
            if cached:
                return ChatResponse(
                    response=cached.get("response", ""),
                    citations=cached.get("citations", []),
                    cached=True,
                    tokens_used=cached.get("tokens_used", 0),
                    confidence_score=cached.get("confidence_score", 0.0),
                    query_type=cached.get("query_type")
                )
        
        # Classify query type
        query_type = classify_query(query)
        logger.info(f"Query classified as: {query_type}")
        
        # Fetch news and sentiment if applicable
        news_data = []
        sentiment_data = None
        
        try:
            # Only fetch news for market analysis or if index is specified
            target_indices = []
            if scan_data and (scan_data.get("index") or scan_data.get("symbol")):
                target_indices = [scan_data.get("index") or scan_data.get("symbol")]
            
            # Fetch both recent articles and aggregated sentiment
            news_data = await news_service.get_recent_news(hours=4, indices=target_indices, limit=5)
            sentiment_data = await news_service.get_market_sentiment(time_window="1hr")
            logger.info(f"📰 Fetched {len(news_data)} news articles and sentiment data")
        except Exception as e:
            logger.error(f"Error fetching news for AI context: {e}")

        # Build context
        context = build_query_context(
            query=query,
            scan_data=scan_data,
            signal_data=optimizer.optimize_signal_context(signal_data) if signal_data else None,
            news_data=news_data,
            sentiment_data=sentiment_data
        )
        
        # Debug log the context
        logger.info(f"📝 Built context ({len(context)} chars): {context[:500]}...")
        
        # Optimize context to fit token limits
        context = optimize_context_window(context, max_tokens=2500)
        context = optimizer.truncate_context(context, max_tokens=3000)
        
        # Get appropriate prompt template
        prompt_template = get_prompt_template(query_type)
        
        # Fill in the prompt with correct parameters based on query type
        prompt_params = {
            "query": query
        }
        
        # Add context parameter based on query type
        if query_type in ["explanation", "risk", "quick", "timing"]:
            prompt_params["signal_context"] = context
        elif query_type == "scalp":
            # Extract target amount from query for scalp questions
            import re
            target_match = re.search(r'₹\s*(\d+)|(\d+)\s*(rupees|rs|profit)', query.lower())
            target_amount = target_match.group(1) or target_match.group(2) if target_match else "5-15"
            prompt_params["signal_context"] = context
            prompt_params["target_amount"] = f"₹{target_amount}"
        elif query_type == "trade_plan":
            # Trade plan needs additional parameters
            prompt_params["signal_context"] = context
            prompt_params["capital"] = 50000  # Default capital
            prompt_params["risk_percentage"] = 2  # Default 2% risk
            prompt_params["risk_amount"] = 1000  # Default risk amount
            prompt_params["risk_profile"] = "Moderate"  # Default risk profile
        elif query_type == "constituent":
            prompt_params["probability_context"] = context
        elif query_type == "comparison":
            prompt_params["indices_context"] = context
        elif query_type == "scan":
            index = "NIFTY"
            if "banknifty" in query.lower(): index = "BANKNIFTY"
            elif "finnifty" in query.lower(): index = "FINNIFTY"
            prompt_params["index"] = index
        elif query_type == "greeting":
            pass # Only needs system_context and query
        elif query_type == "action_request":
            # No context needed for action requests - just the query
            pass
        else:  # general and fallback
            prompt_params["available_context"] = context
            
        prompt = prompt_template.format(**prompt_params)
        
        try:
            # Call Cohere API with tool calling support
            from src.services.ai_tools import COHERE_TOOLS, AIToolExecutor, format_tool_result_for_ai
            import asyncio
            
            # Initialize tool executor
            tool_executor = AIToolExecutor()
            
            # Use preamble for strict instruction following with dynamic context
            system_context = get_system_context()  # Get fresh context with current date/time
            
            # First call to Cohere with tools (with timeout)
            logger.info(f"🤖 Calling Cohere with tools enabled for query type: {query_type}")
            
            try:
                # Set timeout for Cohere API call (30 seconds)
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat,
                        message=prompt,
                        preamble=system_context,
                        model=self.model,
                        temperature=0.1,
                        tools=COHERE_TOOLS if authorization else [],
                    ),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.error("⏰ Cohere API timeout - retrying with shorter context")
                # Retry with more concise prompt
                short_prompt = f"USER QUERY: {query}\n\nDATA: {context[:1000]}...\n\nAnswer concisely."
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat,
                        message=short_prompt,
                        preamble=system_context,
                        model=self.model,
                        temperature=0.1,
                    ),
                    timeout=15.0
                )
            
            # Check if Cohere wants to use tools
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info(f"🔧 Cohere requested {len(response.tool_calls)} tool call(s)")
                
                # Execute each tool
                tool_results = []
                for tool_call in response.tool_calls:
                    tool_name = tool_call.name
                    tool_params = tool_call.parameters
                    
                    logger.info(f"⚙️ Executing tool: {tool_name}")
                    result = await tool_executor.execute_tool(
                        tool_name=tool_name,
                        parameters=tool_params,
                        authorization=authorization
                    )
                    
                    # Format result for AI
                    formatted_result = format_tool_result_for_ai(tool_name, result)
                    tool_results.append({
                        "call": tool_call,
                        "outputs": [{"result": formatted_result, "data": result}]
                    })
                    
                    # If it's a scan, update the context with fresh data
                    if tool_name == "scan_index" and result.get("success"):
                        scan_data = result.get("data", {})
                        signal_data = scan_data.get("signal", {})
                        # Update context with fresh scan data
                        context = build_query_context(
                            query=query,
                            scan_data=scan_data,
                            signal_data=signal_data,
                            news_data=news_data,
                            sentiment_data=sentiment_data
                        )
                
                # Second call to Cohere with tool results
                logger.info("🔄 Sending tool results back to Cohere for final response")
                
                # Build chat history properly
                chat_history = [
                    {"role": "USER", "message": prompt}
                ]
                
                # Add chatbot response with tool calls if it has text
                if hasattr(response, 'text') and response.text:
                    chat_history.append({
                        "role": "CHATBOT", 
                        "message": response.text,
                        "tool_calls": response.tool_calls
                    })
                else:
                    # If no text, just add tool calls
                    chat_history.append({
                        "role": "CHATBOT",
                        "message": "",
                        "tool_calls": response.tool_calls
                    })
                
                response = self.client.chat(
                    message="",  # Empty message when sending tool results
                    preamble=system_context,
                    model=self.model,
                    temperature=0.1,
                    tool_results=tool_results,
                    chat_history=chat_history
                )
            
            ai_response = response.text
            tokens_used = response.meta.get('tokens', {}).get('total_tokens', 0) if hasattr(response, 'meta') else 0
            
            # Extract citations if available
            citations = self._extract_citations(response, context)
            
            # Calculate confidence (basic heuristic)
            confidence_score = self._estimate_confidence(response)
            
            # Build response object
            chat_response = ChatResponse(
                response=ai_response,
                citations=citations,
                cached=False,
                tokens_used=tokens_used,
                confidence_score=confidence_score,
                query_type=query_type
            )
            
            # Cache the response
            if use_cache and ai_cache and scan_id:
                await ai_cache.cache_response(
                    query=query,
                    response=chat_response.dict(),
                    scan_id=scan_id
                )
            
            # Record successful API call
            rate_limiter.record_call()
            
            # Cache in deduplicator
            deduplicator.cache_query(query, chat_response.dict(), scan_id)
            
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"✅ AI response generated in {elapsed:.0f}ms (tokens: {tokens_used}, cost: ${tokens_used * 0.00015:.4f})")
            
            return chat_response
        
        except Exception as e:
            logger.error(f"Cohere API error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # User-friendly error message
            error_msg = str(e)
            if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                user_msg = "The AI service is taking longer than usual. Please try again in a moment."
            elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
                user_msg = "Too many requests. Please wait a moment and try again."
            else:
                user_msg = f"I encountered an error: {error_msg}. Please try again."
            
            # Return error response
            return ChatResponse(
                response=user_msg,
                citations=[],
                cached=False,
                tokens_used=0,
                confidence_score=0.0,
                query_type=query_type
            )
    
    async def explain_signal(
        self,
        signal_data: Dict[str, Any],
        detail_level: str = "normal"
    ) -> str:
        """
        Generate quick explanation of a signal.
        
        Args:
            signal_data: Signal dictionary
            detail_level: brief, normal, or detailed
        
        Returns:
            Explanation string
        """
        if detail_level == "brief":
            query = "Explain this signal in 2-3 sentences."
        elif detail_level == "detailed":
            query = "Provide a detailed explanation of this signal, including all key factors."
        else:
            query = "Explain why this is a buy/sell signal."
        
        response = await self.analyze_signal(
            query=query,
            signal_data=signal_data,
            use_cache=False  # Don't cache quick explanations
        )
        
        return response.response
    
    async def compare_indices(
        self,
        indices_data: List[Dict[str, Any]],
        comparison_type: str = "opportunity"
    ) -> ChatResponse:
        """
        Compare signals across multiple indices.
        
        Args:
            indices_data: List of scan results for different indices
            comparison_type: opportunity, risk, or technical
        
        Returns:
            ChatResponse with comparison analysis
        """
        if comparison_type == "opportunity":
            query = "Which index offers the best trading opportunity based on probability, setup quality, and risk/reward?"
        elif comparison_type == "risk":
            query = "Compare the risk profiles of these indices. Which has the lowest risk?"
        else:
            query = "Compare the technical setups across these indices. Which has the strongest confluence?"
        
        # Build comparison context
        context = build_query_context(comparison_data=indices_data)
        
        return await self.analyze_signal(
            query=query,
            scan_data={"comparison": context},
            use_cache=True
        )
    
    async def plan_trade(
        self,
        signal_data: Dict[str, Any],
        capital: float,
        risk_percentage: float = 2.0,
        risk_profile: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Generate detailed trade plan with position sizing.
        
        Args:
            signal_data: Trading signal
            capital: Available capital in INR
            risk_percentage: Max risk per trade (% of capital)
            risk_profile: conservative, moderate, or aggressive
        
        Returns:
            Trade plan dictionary
        """
        risk_amount = capital * (risk_percentage / 100)
        
        # Build specialized prompt for trade planning
        from src.prompts.signal_explanation import TRADE_PLAN_PROMPT
        
        context = format_signal_context(signal_data)
        
        prompt = TRADE_PLAN_PROMPT.format(
            system_context=SYSTEM_CONTEXT,
            signal_context=context,
            capital=capital,
            risk_percentage=risk_percentage,
            risk_amount=risk_amount,
            risk_profile=risk_profile
        )
        
        try:
            system_context = get_system_context()  # Get fresh context with current date/time
            response = self.client.chat(
                message=prompt,
                preamble=system_context,
                model=self.model,
                temperature=0.3
            )
            
            # Parse the response into structured format
            plan = {
                "recommendation": response.text,
                "capital": capital,
                "risk_percentage": risk_percentage,
                "risk_amount": risk_amount,
                "risk_profile": risk_profile,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return plan
        
        except Exception as e:
            logger.error(f"Trade plan generation error: {e}")
            return {
                "error": str(e),
                "recommendation": "Unable to generate trade plan at this time."
            }
    
    def _extract_citations(self, response: Any, context: str) -> List[Citation]:
        """
        Extract citations from Cohere response.
        
        Args:
            response: Cohere API response
            context: Original context provided
        
        Returns:
            List of Citation objects
        """
        citations = []
        
        # Cohere's citation format (if available)
        if hasattr(response, 'citations') and response.citations:
            for cite in response.citations:
                # Handle both dict and object formats
                if isinstance(cite, dict):
                    doc_ids = cite.get('document_ids', ['unknown'])
                    cite_text = cite.get('text', '')
                else:
                    # Cohere object format
                    doc_ids = getattr(cite, 'document_ids', ['unknown'])
                    cite_text = getattr(cite, 'text', '')
                
                citations.append(Citation(
                    type="data_reference",
                    source=doc_ids[0] if doc_ids else "unknown",
                    text=cite_text,
                    data={}
                ))
        
        # Fallback: Extract key data points mentioned
        # Look for specific patterns like "₹123.45", "65%", "NIFTY", etc.
        if not citations and context:
            # Simple extraction of key metrics
            if "Confidence:" in context:
                citations.append(Citation(
                    type="confidence",
                    source="probability_analysis",
                    text="Signal confidence score"
                ))
            
            if "Risk/Reward:" in context:
                citations.append(Citation(
                    type="risk_reward",
                    source="signal_targets",
                    text="Risk/reward ratio calculation"
                ))
        
        return citations
    
    def _estimate_confidence(self, response: Any) -> float:
        """
        Estimate AI's confidence in the response.
        
        This is a heuristic based on:
        - Presence of hedging language ("might", "could", "possibly")
        - Length and detail of response
        - Citation availability
        
        Args:
            response: Cohere API response
        
        Returns:
            Confidence score 0.0-1.0
        """
        text = response.text.lower()
        
        # Start with base confidence
        confidence = 0.8
        
        # Reduce for hedging language
        hedging_words = ["might", "could", "possibly", "perhaps", "maybe", "uncertain"]
        hedging_count = sum(1 for word in hedging_words if word in text)
        confidence -= hedging_count * 0.05
        
        # Increase for definitive language
        definitive_words = ["clearly", "definitely", "strong", "confirmed", "established"]
        definitive_count = sum(1 for word in definitive_words if word in text)
        confidence += definitive_count * 0.03
        
        # Increase if citations are present
        if hasattr(response, 'citations') and response.citations:
            confidence += 0.1
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def get_query_suggestions(self, scan_data: Dict[str, Any]) -> List[str]:
        """
        Generate smart query suggestions based on scan results.
        
        Args:
            scan_data: Scan results
        
        Returns:
            List of suggested queries
        """
        suggestions = []
        
        # Always available
        suggestions.append("💡 Why is this a buy/sell signal?")
        suggestions.append("⚠️ What are the key risks?")
        suggestions.append("📊 How confident should I be in this signal?")
        
        # Conditional suggestions based on data
        if scan_data.get("probability_analysis"):
            suggestions.append("📈 Explain the constituent stock analysis")
        
        if scan_data.get("mtf_analysis"):
            suggestions.append("🔄 What does the multi-timeframe analysis show?")
        
        if scan_data.get("theta_analysis"):
            suggestions.append("⏰ When is the best time to enter this trade?")
        
        # Position sizing
        suggestions.append("💰 How should I size this position with ₹50,000 capital?")
        
        return suggestions[:6]  # Return top 6 suggestions


# Global service instance
ai_service: Optional[CohereAnalysisService] = None

def get_ai_service() -> Optional[CohereAnalysisService]:
    """Get or initialize the AI service."""
    global ai_service
    
    if ai_service is None:
        try:
            ai_service = CohereAnalysisService()
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            return None
    
    return ai_service
