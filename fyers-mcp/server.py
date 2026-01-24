#!/usr/bin/env python3
"""
FYERS MCP Server
Model Context Protocol server for FYERS trading integration
Allows AI assistants (Claude, Cursor, etc.) to access your trading context
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Import FYERS client and services
from src.api.fyers_client import fyers_client
from src.analytics.index_options import IndexOptionsAnalyzer
from src.analytics.mtf_ict_analysis import MultiTimeframeICTAnalyzer
from config.supabase_config import supabase_admin

# MCP SDK imports
try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
except ImportError:
    print("ERROR: MCP SDK not installed. Run: pip install mcp")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fyers-mcp")

# Initialize server
server = Server("fyers-mcp")

# Backend API URL - configurable via environment variable
API_BASE_URL = os.getenv("TRADEWISE_API_URL", "http://localhost:8000")
logger.info(f"🌐 Using API: {API_BASE_URL}")

# Initialize analyzers
index_analyzer = None
ict_analyzer = None


def initialize_analyzers():
    """Initialize trading analyzers"""
    global index_analyzer, ict_analyzer
    try:
        if fyers_client.fyers:
            index_analyzer = IndexOptionsAnalyzer(fyers_client)
            ict_analyzer = MultiTimeframeICTAnalyzer(fyers_client)
            logger.info("✅ Analyzers initialized successfully")
        else:
            logger.warning("⚠️ Fyers client not authenticated. Some features will be limited.")
    except Exception as e:
        logger.error(f"❌ Error initializing analyzers: {e}")


# ============================================
# RESOURCES (Read-only data exposed to AI)
# ============================================

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available trading resources"""
    return [
        Resource(
            uri="fyers://portfolio/summary",
            name="Portfolio Summary",
            description="Overall portfolio value, P&L, and holdings",
            mimeType="application/json",
        ),
        Resource(
            uri="fyers://positions/current",
            name="Current Positions",
            description="All open positions with live P&L",
            mimeType="application/json",
        ),
        Resource(
            uri="fyers://orders/today",
            name="Today's Orders",
            description="All orders placed today",
            mimeType="application/json",
        ),
        Resource(
            uri="fyers://market/indices",
            name="Market Indices",
            description="NIFTY, BANKNIFTY, SENSEX live values",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific resource"""
    try:
        if uri == "fyers://portfolio/summary":
            funds = fyers_client.get_funds()
            positions = fyers_client.get_positions()
            
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "funds": funds,
                "positions_count": len(positions.get("netPositions", [])) if positions.get("s") == "ok" else 0,
                "status": "success"
            }, indent=2)
        
        elif uri == "fyers://positions/current":
            positions = fyers_client.get_positions()
            return json.dumps(positions, indent=2)
        
        elif uri == "fyers://orders/today":
            orders = fyers_client.get_orders()
            return json.dumps(orders, indent=2)
        
        elif uri == "fyers://market/indices":
            symbols = [
                "NSE:NIFTY50-INDEX",
                "NSE:NIFTYBANK-INDEX",
                "BSE:SENSEX-INDEX"
            ]
            quotes = fyers_client.get_quotes(symbols)
            return json.dumps(quotes, indent=2)
        
        else:
            return json.dumps({"error": "Unknown resource URI"})
    
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        return json.dumps({"error": str(e)})


# ============================================
# TOOLS (Actions AI can perform)
# ============================================

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available trading tools"""
    return [
        Tool(
            name="get_positions",
            description="Get all current open positions with live P&L, entry prices, and quantities",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_orders",
            description="Get all orders (pending, executed, cancelled) with status and details",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_portfolio_summary",
            description="Get complete portfolio summary including funds, margin, P&L, and holdings value",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_option_chain",
            description="Get live option chain data for an index with strikes, OI, volume, Greeks",
            inputSchema={
                "type": "object",
                "properties": {
                    "index": {
                        "type": "string",
                        "description": "Index name (NIFTY, BANKNIFTY, FINNIFTY, SENSEX)",
                        "enum": ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX"]
                    },
                    "expiry_type": {
                        "type": "string",
                        "description": "Expiry type (weekly, monthly)",
                        "enum": ["weekly", "monthly"],
                        "default": "weekly"
                    }
                },
                "required": ["index"],
            },
        ),
        Tool(
            name="analyze_index",
            description="Advanced multi-timeframe ICT analysis with Order Blocks, Fair Value Gaps, liquidity zones, and ML predictions. Returns actionable trading signals with specific option strikes, entry/exit prices, targets, stop loss, best timing, and confidence scores. Same comprehensive analysis used in TradeWise dashboard.",
            inputSchema={
                "type": "object",
                "properties": {
                    "index": {
                        "type": "string",
                        "description": "Index to analyze (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX, BANKEX)",
                    }
                },
                "required": ["index"],
            },
        ),
        Tool(
            name="analyze_stock",
            description="Analyze individual stocks using technical indicators (RSI, EMA, VWAP, momentum). Returns BUY/SELL/HOLD signals with confidence, targets, stop loss, and reasoning. Same method as the TradeWise stock screener page.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., 'SBIN', 'TCS', 'RELIANCE')",
                    }
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_stock_quote",
            description="Get live quote for a specific stock/index symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol in FYERS format (e.g., NSE:RELIANCE-EQ, NSE:NIFTY50-INDEX)",
                    }
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_historical_data",
            description="Get historical price data for technical analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Symbol in FYERS format",
                    },
                    "days": {
                        "type": "number",
                        "description": "Number of days of history",
                        "default": 60
                    },
                    "resolution": {
                        "type": "string",
                        "description": "Timeframe (D=daily, 60=1hr, 15=15min)",
                        "enum": ["D", "240", "60", "15", "5"],
                        "default": "D"
                    }
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="search_symbol",
            description="Search for stocks/indices by name or symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (company name or symbol)",
                    }
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution"""
    try:
        if name == "get_positions":
            result = fyers_client.get_positions()
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "get_orders":
            result = fyers_client.get_orders()
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "get_portfolio_summary":
            funds = fyers_client.get_funds()
            positions = fyers_client.get_positions()
            
            # Calculate total P&L from positions
            total_pnl = 0
            if positions.get("s") == "ok" and positions.get("netPositions"):
                for pos in positions["netPositions"]:
                    total_pnl += pos.get("pl", 0)
            
            summary = {
                "timestamp": datetime.now().isoformat(),
                "funds": funds,
                "total_pnl": total_pnl,
                "positions": positions,
                "status": "success"
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(summary, indent=2)
            )]
        
        elif name == "get_option_chain":
            index = arguments.get("index", "NIFTY")
            expiry_type = arguments.get("expiry_type", "weekly")
            
            if not index_analyzer:
                initialize_analyzers()
            
            if index_analyzer:
                chain_analysis = index_analyzer.analyze_option_chain(index, expiry_type)
                if chain_analysis:
                    result = {
                        "index": index,
                        "spot_price": chain_analysis.spot_price,
                        "atm_strike": chain_analysis.atm_strike,
                        "pcr": chain_analysis.pcr,
                        "max_pain": chain_analysis.max_pain,
                        "total_call_oi": chain_analysis.total_call_oi,
                        "total_put_oi": chain_analysis.total_put_oi,
                        "strikes": [
                            {
                                "strike": s.strike,
                                "call_oi": s.call_oi,
                                "put_oi": s.put_oi,
                                "call_volume": s.call_volume,
                                "put_volume": s.put_volume,
                                "call_ltp": s.call_ltp,
                                "put_ltp": s.put_ltp,
                            }
                            for s in chain_analysis.strikes[:10]  # Top 10 strikes
                        ],
                        "signal": chain_analysis.signal,
                        "confidence": chain_analysis.confidence
                    }
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]
            
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Failed to analyze option chain"})
            )]
        
        elif name == "analyze_index":
            # Use the same endpoint as dashboard: /signals/{symbol}/actionable
            import httpx
            index = arguments.get("index", "NIFTY")
            
            # Map index names to FYERS symbols (same as dashboard)
            symbol_map = {
                "NIFTY": "NSE:NIFTY50-INDEX",
                "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
                "FINNIFTY": "NSE:FINNIFTY-INDEX",
                "MIDCPNIFTY": "NSE:MIDCPNIFTY-INDEX",
                "SENSEX": "BSE:SENSEX-INDEX",
                "BANKEX": "BSE:BANKEX-INDEX"
            }
            symbol = symbol_map.get(index.upper(), "NSE:NIFTY50-INDEX")
            
            try:
                # Call the backend API's actionable signal endpoint (same as dashboard)
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{API_BASE_URL}/signals/{symbol}/actionable",
                        timeout=120.0  # Longer timeout for heavy analysis
                    )
                    if response.status_code == 200:
                        return [TextContent(
                            type="text",
                            text=json.dumps(response.json(), indent=2)
                        )]
                    else:
                        return [TextContent(
                            type="text",
                            text=json.dumps({"error": f"API returned {response.status_code}", "detail": response.text})
                        )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Failed to analyze: {str(e)}"})
                )]
        
        elif name == "analyze_stock":
            # Use the screener stock endpoint (same as dashboard)
            import httpx
            symbol = arguments.get("symbol", "")
            
            if not symbol:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Symbol is required"})
                )]
            
            try:
                # Call the backend API's screener stock endpoint
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{API_BASE_URL}/screener/stock/{symbol}",
                        timeout=60.0
                    )
                    if response.status_code == 200:
                        return [TextContent(
                            type="text",
                            text=json.dumps(response.json(), indent=2)
                        )]
                    else:
                        return [TextContent(
                            type="text",
                            text=json.dumps({"error": f"API returned {response.status_code}", "detail": response.text})
                        )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Failed to analyze stock: {str(e)}"})
                )]
        
        elif name == "get_stock_quote":
            symbol = arguments.get("symbol")
            if not symbol:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Symbol required"})
                )]
            
            quote = fyers_client.get_quotes([symbol])
            return [TextContent(
                type="text",
                text=json.dumps(quote, indent=2)
            )]
        
        elif name == "get_historical_data":
            symbol = arguments.get("symbol")
            days = arguments.get("days", 60)
            resolution = arguments.get("resolution", "D")
            
            date_from = datetime.now() - timedelta(days=days)
            df = fyers_client.get_historical_data(
                symbol=symbol,
                resolution=resolution,
                date_from=date_from
            )
            
            result = {
                "symbol": symbol,
                "resolution": resolution,
                "days": days,
                "records": len(df),
                "data": df.to_dict(orient="records")[-20:]  # Last 20 candles
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "search_symbol":
            query = arguments.get("query", "").upper()
            
            # Basic symbol search (could be enhanced with actual API)
            common_symbols = {
                "NIFTY": "NSE:NIFTY50-INDEX",
                "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
                "RELIANCE": "NSE:RELIANCE-EQ",
                "TCS": "NSE:TCS-EQ",
                "INFY": "NSE:INFY-EQ",
                "HDFC": "NSE:HDFCBANK-EQ",
                "ICICI": "NSE:ICICIBANK-EQ",
                "SBIN": "NSE:SBIN-EQ",
            }
            
            results = {k: v for k, v in common_symbols.items() if query in k}
            
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"})
            )]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]


async def load_token_from_supabase():
    """Load FYERS token from Supabase if not in .env"""
    if fyers_client.access_token:
        logger.info("✅ Using FYERS token from .env")
        return True
    
    try:
        from datetime import timezone
        logger.info("🔍 Fetching FYERS token from Supabase...")
        
        response = supabase_admin.table("fyers_tokens").select("*").order("updated_at", desc=True).execute()
        
        if not response.data:
            logger.warning("⚠️ No FYERS tokens in database")
            return False
        
        # Find first non-expired token
        for token_data in response.data:
            access_token = token_data.get("access_token")
            if not access_token:
                continue
            
            # Check expiry
            if token_data.get("expires_at"):
                expires_at = datetime.fromisoformat(token_data["expires_at"])
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                
                now = datetime.now(timezone.utc)
                if expires_at < now:
                    continue
            
            # Set token in fyers_client and initialize
            fyers_client.access_token = access_token
            fyers_client._initialize_client()
            logger.info(f"✅ Loaded token for user {token_data.get('user_id', '')[:8]}...")
            logger.info("✅ FYERS client initialized with token from Supabase")
            return True
        
        logger.warning("⚠️ All tokens in database expired")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error loading token from Supabase: {e}")
        return False


async def main():
    """Main server entry point"""
    logger.info("🚀 Starting FYERS MCP Server...")
    
    # Try to load token from Supabase if not in .env
    token_loaded = await load_token_from_supabase()
    
    if not token_loaded:
        logger.warning("⚠️ No valid FYERS token. Some features will be limited.")
        logger.info("Authenticate via TradeWise app to store token in database.")
    else:
        logger.info("✅ FYERS client initialized")
        initialize_analyzers()
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("✅ MCP Server running on stdio")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fyers-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
