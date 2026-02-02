"""
AI Tools for Cohere Function Calling
Allows the AI to trigger actual actions: scans, Fyers API calls, etc.
"""
import logging
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)


# Tool Definitions for Cohere
COHERE_TOOLS = [
    {
        "name": "scan_index",
        "description": "Trigger a fresh options scan for NIFTY, BANKNIFTY, or FINNIFTY. Use this when user asks to 'scan', 'analyze', or 'check' an index.",
        "parameter_definitions": {
            "index": {
                "description": "The index to scan: NIFTY, BANKNIFTY, or FINNIFTY",
                "type": "str",
                "required": True
            },
            "expiry": {
                "description": "Expiry type: weekly, next_weekly, or monthly",
                "type": "str",
                "required": False
            }
        }
    },
    {
        "name": "get_fyers_positions",
        "description": "Get user's current Fyers positions (active trades). Use when user asks 'show my positions', 'what trades do I have', or 'my open positions'.",
        "parameter_definitions": {}
    },
    {
        "name": "get_fyers_funds",
        "description": "Get user's Fyers account balance and margin details. Use when user asks 'show my balance', 'how much margin', or 'my funds'.",
        "parameter_definitions": {}
    },
    {
        "name": "get_latest_scan",
        "description": "Get the most recent scan results from database if user just scanned. Use when user says 'explain the scan', 'tell me about the signal', without specifying which index.",
        "parameter_definitions": {}
    }
]


class AIToolExecutor:
    """
    Executes tools called by the AI.
    Bridges between Cohere's function calling and actual API endpoints.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def execute_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        authorization: str
    ) -> Dict[str, Any]:
        """
        Execute a tool call from the AI.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            authorization: Bearer token for authentication
        
        Returns:
            Result of the tool execution
        """
        logger.info(f"🔧 Executing tool: {tool_name} with params: {parameters}")
        
        try:
            if tool_name == "scan_index":
                return await self._scan_index(parameters, authorization)
            elif tool_name == "get_fyers_positions":
                return await self._get_fyers_positions(authorization)
            elif tool_name == "get_fyers_funds":
                return await self._get_fyers_funds(authorization)
            elif tool_name == "get_latest_scan":
                # Pass index parameter if provided
                index = parameters.get("index") if parameters else None
                return await self._get_latest_scan(authorization, index=index)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"❌ Tool execution error: {e}")
            return {"error": str(e)}
    
    async def _scan_index(self, params: Dict[str, Any], auth: str) -> Dict[str, Any]:
        """Trigger a fresh options scan."""
        index = params.get("index", "NIFTY").upper()
        expiry = params.get("expiry", "weekly")
        
        logger.info(f"📊 Scanning {index} with expiry={expiry}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{self.base_url}/options/scan"
            headers = {"Authorization": auth}
            params_dict = {
                "index": index,
                "expiry": expiry,
                "quick_scan": "true"
            }
            
            response = await client.get(url, headers=headers, params=params_dict)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Scan complete for {index}")
                return {
                    "success": True,
                    "index": index,
                    "data": data,
                    "message": f"Successfully scanned {index} options"
                }
            else:
                logger.error(f"❌ Scan failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Scan failed with status {response.status_code}",
                    "details": response.text
                }
    
    async def _get_fyers_positions(self, auth: str) -> Dict[str, Any]:
        """Get user's Fyers positions."""
        logger.info("📈 Getting Fyers positions")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{self.base_url}/fyers/positions"
            headers = {"Authorization": auth}
            
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "positions": data.get("netPositions", []),
                    "message": "Successfully fetched positions"
                }
            else:
                return {
                    "success": False,
                    "error": "Could not fetch positions",
                    "details": response.text
                }
    
    async def _get_fyers_funds(self, auth: str) -> Dict[str, Any]:
        """Get user's Fyers account balance."""
        logger.info("💰 Getting Fyers funds")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{self.base_url}/fyers/funds"
            headers = {"Authorization": auth}
            
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "funds": data.get("fund_limit", []),
                    "message": "Successfully fetched funds"
                }
            else:
                return {
                    "success": False,
                    "error": "Could not fetch funds",
                    "details": response.text
                }
    
    async def _get_latest_scan(self, auth: str, index: str = None) -> Dict[str, Any]:
        """Get latest scan from database, optionally filtered by index."""
        logger.info(f"📂 Getting latest scan from database{' for ' + index if index else ''}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Build URL with optional index parameter
            url = f"{self.base_url}/screener/latest"
            if index:
                url += f"?index={index.upper()}"
            headers = {"Authorization": auth}
            
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "success": True,
                        "data": data,
                        "index": data.get("index", index or "NIFTY"),
                        "message": f"Successfully fetched latest scan for {data.get('index', index or 'NIFTY')}"
                    }
                else:
                    return {
                        "success": False,
                        "message": data.get("message", "No scan data available"),
                        "suggestion": "Please run a fresh scan using 'scan nifty' or 'scan banknifty'"
                    }
            else:
                return {
                    "success": False,
                    "error": "Could not fetch scan data",
                    "details": response.text,
                    "suggestion": "Please run a fresh scan using 'scan nifty'"
                }


def format_tool_result_for_ai(tool_name: str, result: Dict[str, Any]) -> str:
    """
    Format tool execution result into text for AI context.
    
    Args:
        tool_name: Name of the tool that was executed
        result: Result from tool execution
    
    Returns:
        Formatted text for AI context
    """
    if not result.get("success"):
        return f"❌ {tool_name} failed: {result.get('error', 'Unknown error')}"
    
    if tool_name == "scan_index":
        data = result.get("data", {})
        index = result.get("index", "UNKNOWN")
        
        # Extract key information from scan
        signal = data.get("signal", {})
        action = signal.get("action", "UNKNOWN")
        confidence = signal.get("confidence", 0)
        
        return f"""✅ Fresh {index} scan completed successfully!

Signal: {action}
Confidence: {confidence}%
Strike: {signal.get('strike')} {signal.get('type')}
Current Price (LTP): ₹{signal.get('entry_price', 0):.2f}

Full scan data is now available in context."""
    
    elif tool_name == "get_fyers_positions":
        positions = result.get("positions", [])
        if not positions:
            return "You have no open positions in Fyers."
        
        pos_text = f"You have {len(positions)} open position(s):\n"
        for p in positions:
            pos_text += f"• {p.get('symbol')}: {p.get('qty')} @ ₹{p.get('buyAvg', 0):.2f}\n"
        return pos_text
    
    elif tool_name == "get_fyers_funds":
        funds = result.get("funds", [])
        if funds:
            fund = funds[0]
            return f"""💰 Your Fyers Account:
Available Balance: ₹{fund.get('availableBalance', 0):,.2f}
Total Balance: ₹{fund.get('totalBalance', 0):,.2f}"""
        return "Could not fetch fund details"
    
    return str(result)
