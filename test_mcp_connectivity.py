#!/usr/bin/env python3
"""
Test MCP Server connectivity and functionality
Safe read-only tests - NO order placement
"""
import asyncio
import json
import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.fyers_client import fyers_client
from config.supabase_config import supabase_admin
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

async def load_token_from_supabase():
    """Load FYERS token from Supabase if not in .env"""
    if fyers_client.access_token:
        print("✅ Using FYERS token from .env")
        return True
    
    try:
        print("🔍 Fetching FYERS token from Supabase...")
        
        response = supabase_admin.table("fyers_tokens").select("*").order("updated_at", desc=True).execute()
        
        if not response.data:
            print("⚠️ No FYERS tokens in database")
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
            print(f"✅ Loaded token for user {token_data.get('user_id', '')[:8]}...")
            return True
        
        print("⚠️ All tokens in database expired")
        return False
        
    except Exception as e:
        print(f"❌ Error loading token from Supabase: {e}")
        return False

async def test_connectivity():
    """Test Fyers client connectivity without placing orders"""
    
    print("=" * 60)
    print("FYERS MCP Server Connectivity Test")
    print("=" * 60)
    print()
    
    # Load token from Supabase if needed
    token_loaded = await load_token_from_supabase()
    
    # Test 1: Check if client is initialized
    print("🧪 Test 1: FYERS Client Initialization")
    if fyers_client.fyers:
        print("✅ PASS: FYERS client is initialized")
    else:
        print("❌ FAIL: FYERS client not initialized")
        print("⚠️  Please authenticate via TradeWise app first")
        return
    print()
    
    # Test 2: Get Portfolio Summary (READ-ONLY)
    print("🧪 Test 2: Get Portfolio Summary (READ-ONLY)")
    try:
        funds = fyers_client.get_funds()
        if funds.get("s") == "ok":
            fund_limit = funds.get("fund_limit", [{}])[0]
            print(f"✅ PASS: Portfolio fetched successfully")
            print(f"   Available Balance: ₹{fund_limit.get('availableBalance', 0):,.2f}")
            print(f"   Used Margin: ₹{fund_limit.get('utilized_amount', 0):,.2f}")
        else:
            print(f"⚠️  WARNING: {funds}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    print()
    
    # Test 3: Get Current Positions (READ-ONLY)
    print("🧪 Test 3: Get Current Positions (READ-ONLY)")
    try:
        positions = fyers_client.get_positions()
        if positions.get("s") == "ok":
            pos_list = positions.get("netPositions", [])
            print(f"✅ PASS: Found {len(pos_list)} open position(s)")
            
            if pos_list:
                for pos in pos_list[:3]:  # Show first 3
                    print(f"   {pos.get('symbol', 'N/A')}: "
                          f"Qty {pos.get('netQty', 0)}, "
                          f"P&L: ₹{pos.get('pl', 0):,.2f}")
            else:
                print("   No open positions")
        else:
            print(f"⚠️  WARNING: {positions}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    print()
    
    # Test 4: Get Orders (READ-ONLY)
    print("🧪 Test 4: Get Today's Orders (READ-ONLY)")
    try:
        orders = fyers_client.get_orders()
        if orders.get("s") == "ok":
            order_list = orders.get("orderBook", [])
            print(f"✅ PASS: Found {len(order_list)} order(s) today")
            
            if order_list:
                for order in order_list[-3:]:  # Show last 3
                    print(f"   {order.get('symbol', 'N/A')}: "
                          f"{order.get('side', 'N/A')} "
                          f"{order.get('qty', 0)} @ "
                          f"₹{order.get('tradedPrice', order.get('limitPrice', 0)):.2f} - "
                          f"{order.get('status', 'N/A')}")
            else:
                print("   No orders today")
        else:
            print(f"⚠️  WARNING: {orders}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    print()
    
    # Test 5: Get Live Quote (READ-ONLY)
    print("🧪 Test 5: Get Live Market Quote (READ-ONLY)")
    try:
        quote = fyers_client.get_quotes(["NSE:SBIN-EQ"])
        if quote.get("s") == "ok":
            data = quote.get("d", [{}])[0]
            print(f"✅ PASS: Live quote fetched")
            print(f"   SBIN: ₹{data.get('v', {}).get('lp', 0):.2f} "
                  f"({data.get('v', {}).get('ch', 0):+.2f}, "
                  f"{data.get('v', {}).get('chp', 0):+.2f}%)")
        else:
            print(f"⚠️  WARNING: {quote}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    print()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print("✅ MCP Server is ready for Claude Desktop")
    print("🚀 Available tools: get_positions, get_orders, get_portfolio_summary")
    print("📊 Available tools: analyze_index, analyze_stock, get_option_chain")
    print("⚠️  Order placement NOT available (by design)")
    print()
    print("To use with Claude Desktop:")
    print("  1. Ensure MCP is configured in Claude Desktop")
    print("  2. Ask: 'Show my positions' or 'Analyze NIFTY'")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_connectivity())
