"""
Pydantic models for AI chat and analysis features.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for AI chat endpoint."""
    query: str = Field(..., description="User's question or query")
    scan_id: Optional[str] = Field(None, description="Specific scan to analyze")
    scan_data: Optional[Dict[str, Any]] = Field(None, description="Scan results data")
    signal_data: Optional[Dict[str, Any]] = Field(None, description="Specific signal data")
    use_cache: bool = Field(True, description="Whether to use cached responses")
    index: Optional[str] = Field(None, description="Filter to specific index")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="Previous messages for context"
    )


class Citation(BaseModel):
    """Reference to a specific data point used in AI response."""
    type: str = Field(..., description="Type: signal, probability, market_data")
    source: str = Field(..., description="Reference to data point")
    text: str = Field(..., description="Excerpt or summary")
    data: Optional[Dict[str, Any]] = Field(None, description="Associated data")


class ChatResponse(BaseModel):
    """Response model for AI chat endpoint."""
    response: str = Field(..., description="AI-generated response")
    citations: List[Citation] = Field(default_factory=list, description="Data references")
    cached: bool = Field(False, description="Whether response was cached")
    tokens_used: int = Field(0, description="Tokens consumed by this query")
    confidence_score: float = Field(0.0, description="AI confidence in response (0-1)")
    query_type: Optional[str] = Field(None, description="Classified query type")


class ExplainSignalRequest(BaseModel):
    """Request to explain a specific signal."""
    signal_id: Optional[str] = Field(None, description="Signal ID from database")
    signal_data: Optional[Dict[str, Any]] = Field(None, description="Direct signal data")
    detail_level: str = Field("normal", description="brief, normal, or detailed")


class CompareIndicesRequest(BaseModel):
    """Request to compare signals across indices."""
    indices: List[str] = Field(..., description="List of indices to compare")
    comparison_type: str = Field("opportunity", description="opportunity, risk, or technical")


class TradePlanRequest(BaseModel):
    """Request to generate a trade plan."""
    signal_id: Optional[str] = Field(None, description="Signal to plan for")
    signal_data: Optional[Dict[str, Any]] = Field(None, description="Direct signal data")
    capital: float = Field(..., description="Available capital in INR")
    risk_percentage: float = Field(2.0, description="Max risk per trade (% of capital)")
    risk_profile: str = Field("moderate", description="conservative, moderate, or aggressive")


class TradePlanResponse(BaseModel):
    """Response with detailed trade plan."""
    recommendation: str = Field(..., description="Overall recommendation")
    position_size: Dict[str, Any] = Field(..., description="Lot sizing details")
    risk_analysis: Dict[str, Any] = Field(..., description="Risk breakdown")
    execution_plan: List[str] = Field(..., description="Step-by-step execution")
    contingencies: List[str] = Field(..., description="What-if scenarios")


class QuerySuggestion(BaseModel):
    """Smart query suggestion based on scan context."""
    query: str = Field(..., description="Suggested query text")
    category: str = Field(..., description="explanation, risk, comparison, timing")
    icon: str = Field("💡", description="Emoji for UI")
    priority: int = Field(0, description="Display priority (higher = more important)")


class AIAnalyticsLog(BaseModel):
    """Log entry for AI query analytics."""
    user_id: str
    query: str
    query_type: str
    scan_id: Optional[str] = None
    cached: bool = False
    tokens_used: int = 0
    response_time_ms: int = 0
    confidence_score: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
