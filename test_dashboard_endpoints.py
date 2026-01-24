#!/usr/bin/env python3
"""
Test the exact endpoints used by dashboard
"""
import asyncio
import httpx

async def test_endpoints():
    print("=" * 70)
    print("Testing Dashboard Endpoints")
    print("=" * 70)
    print()
    
    async with httpx.AsyncClient() as client:
        # Test 1: Quick health check
        print("🧪 Test 1: Health Check")
        try:
            response = await client.get("http://localhost:8000/", timeout=5.0)
            print(f"✅ Backend is running - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Backend not running: {e}")
            return
        print()
        
        # Test 2: Stock screener endpoint (should be fast)
        print("🧪 Test 2: Stock Screener - /screener/stock/SBIN")
        try:
            response = await client.get("http://localhost:8000/screener/stock/SBIN", timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success - {data.get('symbol', 'N/A')}: {data.get('action', 'N/A')} @ ₹{data.get('current_price', 0):.2f}")
                print(f"   Confidence: {data.get('confidence', 0)}%, Target: ₹{data.get('target', 0):.2f}")
            else:
                print(f"⚠️  Status {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print()
        
        # Test 3: Index analysis endpoint (can be slow)
        print("🧪 Test 3: Index Analysis - /signals/NSE:NIFTY50-INDEX/actionable")
        print("   (This may take 30-60 seconds for full MTF analysis...)")
        try:
            response = await client.get(
                "http://localhost:8000/signals/NSE:NIFTY50-INDEX/actionable",
                timeout=120.0
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success - Action: {data.get('action', 'N/A')}")
                print(f"   Strike: {data.get('option', {}).get('strike', 'N/A')} {data.get('option', {}).get('type', 'N/A')}")
                print(f"   Entry: ₹{data.get('entry', {}).get('price', 0):.2f}")
                print(f"   Confidence: {data.get('confidence', 'N/A')}")
            else:
                print(f"⚠️  Status {response.status_code}: {response.text[:200]}")
        except asyncio.TimeoutError:
            print(f"❌ Timeout after 120 seconds - endpoint is too slow")
        except Exception as e:
            print(f"❌ Error: {e}")
        print()
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("If Test 3 timed out, the index analysis endpoint needs optimization")
    print("or Claude Desktop will face the same timeout issues.")
    print()

if __name__ == "__main__":
    asyncio.run(test_endpoints())
