"""
Test script to verify AI tool calling is working
Run this to check if the AI can execute actions
"""
import asyncio
import httpx
import os
import json

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TOKEN = None  # Will be set after login

async def login():
    """Login and get auth token"""
    global TEST_TOKEN
    
    print("🔐 Logging in...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": input("Enter your email: "),
                "password": input("Enter your password: ")
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            TEST_TOKEN = data.get("access_token")
            print(f"✅ Logged in successfully!")
            print(f"📝 Token: {TEST_TOKEN[:30]}...")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False

async def test_ai_tool_calling(query: str):
    """Test AI chat with tool calling"""
    if not TEST_TOKEN:
        print("❌ Not logged in")
        return
    
    print(f"\n{'='*60}")
    print(f"🤖 Testing query: {query}")
    print(f"{'='*60}\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/ai/chat",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            json={
                "query": query,
                "use_cache": False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI Response:")
            print(f"\n{data['response']}\n")
            print(f"📊 Query Type: {data.get('query_type')}")
            print(f"🎯 Confidence: {data.get('confidence_score')}")
            print(f"💰 Tokens Used: {data.get('tokens_used')}")
            print(f"📦 Cached: {data.get('cached')}")
            
            if data.get('citations'):
                print(f"\n📚 Citations: {len(data['citations'])}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Details: {response.text}")

async def main():
    """Run all tests"""
    print("🧪 AI Tool Calling Test Suite")
    print("="*60)
    
    # Login first
    if not await login():
        return
    
    # Test 1: Scan request (should trigger scan_index tool)
    print("\n\n📊 Test 1: Scan Request")
    print("-"*60)
    await test_ai_tool_calling("scan nifty")
    
    # Test 2: Position query (should trigger get_fyers_positions tool)
    print("\n\n📈 Test 2: Fyers Positions")
    print("-"*60)
    await test_ai_tool_calling("show my fyers positions")
    
    # Test 3: Balance query (should trigger get_fyers_funds tool)
    print("\n\n💰 Test 3: Fyers Balance")
    print("-"*60)
    await test_ai_tool_calling("what's my account balance")
    
    # Test 4: Explanation (should NOT trigger tools)
    print("\n\n📖 Test 4: Explanation (No Tools)")
    print("-"*60)
    await test_ai_tool_calling("explain the latest signal")
    
    print("\n\n✅ All tests complete!")
    print("="*60)
    print("\n📋 What to check:")
    print("1. Did 'scan nifty' actually trigger a scan?")
    print("2. Did you see fresh data in the response?")
    print("3. Did Fyers positions/balance get fetched?")
    print("4. Check backend logs for tool execution messages")

if __name__ == "__main__":
    asyncio.run(main())
