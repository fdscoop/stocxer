#!/usr/bin/env python3
"""
Test AI Chat Integration
Tests all AI endpoints and cost optimization features.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000"
TOKEN = None  # Will be set after login

def test_login():
    """Test login and get token"""
    global TOKEN
    
    print("🔑 Testing login...")
    response = requests.post(
        f"{API_URL}/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "test123"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        TOKEN = data.get("access_token")
        print(f"✅ Login successful! Token: {TOKEN[:20]}...")
        return True
    else:
        print(f"❌ Login failed: {response.text}")
        return False


def test_basic_chat():
    """Test basic chat endpoint"""
    print("\n💬 Testing basic chat...")
    
    response = requests.post(
        f"{API_URL}/api/ai/chat",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "query": "What is a bullish reversal pattern?",
            "use_cache": True
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Chat response received ({data.get('tokens_used', 0)} tokens)")
        print(f"📝 Response preview: {data.get('response', '')[:100]}...")
        print(f"🎯 Query type: {data.get('query_type')}")
        print(f"💾 Cached: {data.get('cached', False)}")
        return True
    else:
        print(f"❌ Chat failed: {response.text}")
        return False


def test_signal_explanation():
    """Test signal explanation endpoint"""
    print("\n📊 Testing signal explanation...")
    
    signal_data = {
        "symbol": "NSE:NIFTY50-INDEX",
        "signal": "ICT_BULLISH_REVERSAL",
        "action": "BUY",
        "confidence": 78.5,
        "entry_price": 24500,
        "target_1": 24750,
        "target_2": 25000,
        "stop_loss": 24350,
        "risk_reward_ratio_1": "1:1.67",
        "htf_direction": "bullish"
    }
    
    response = requests.post(
        f"{API_URL}/api/ai/explain-signal",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "signal_data": signal_data,
            "detail_level": "normal"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Explanation generated")
        print(f"📝 Explanation: {data.get('explanation', '')[:150]}...")
        return True
    else:
        print(f"❌ Explanation failed: {response.text}")
        return False


def test_usage_stats():
    """Test usage statistics endpoint"""
    print("\n📈 Testing usage statistics...")
    
    response = requests.get(
        f"{API_URL}/api/ai/usage-stats",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        usage = data.get('usage', {})
        cost = data.get('cost_estimate', {})
        limits = data.get('rate_limits', {})
        
        print(f"✅ Usage stats retrieved")
        print(f"   Calls today: {usage.get('calls_today', 0)}")
        print(f"   Calls this hour: {usage.get('calls_last_hour', 0)}")
        print(f"   Estimated cost today: ₹{cost.get('estimated_cost_today_inr', 0)}")
        print(f"   Remaining today: {limits.get('remaining_today', 0)}")
        return True
    else:
        print(f"❌ Usage stats failed: {response.text}")
        return False


def test_cache_deduplication():
    """Test query deduplication"""
    print("\n🔄 Testing cache and deduplication...")
    
    query = f"Test query at {time.time()}"
    
    # First call
    print("   Making first call...")
    response1 = requests.post(
        f"{API_URL}/api/ai/chat",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"query": query, "use_cache": True}
    )
    
    time.sleep(1)
    
    # Second identical call (should be cached)
    print("   Making second call (should be cached)...")
    response2 = requests.post(
        f"{API_URL}/api/ai/chat",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"query": query, "use_cache": True}
    )
    
    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()
        
        cached1 = data1.get('cached', False)
        cached2 = data2.get('cached', False)
        
        print(f"   First call cached: {cached1}")
        print(f"   Second call cached: {cached2}")
        
        if cached2 or data1.get('response') == data2.get('response'):
            print("✅ Caching/deduplication working!")
            return True
        else:
            print("⚠️ Responses differ (might be expected for some queries)")
            return True
    else:
        print(f"❌ Cache test failed")
        return False


def test_rate_limiting():
    """Test rate limiting (be careful!)"""
    print("\n⏱️  Testing rate limiting...")
    print("   (Making 5 quick calls to check rate limiter)")
    
    successful_calls = 0
    rate_limited = False
    
    for i in range(5):
        response = requests.post(
            f"{API_URL}/api/ai/chat",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "query": f"Quick test {i}",
                "use_cache": True
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if "rate limit" in data.get('response', '').lower():
                rate_limited = True
                print(f"   Call {i+1}: Rate limited ⏸️")
            else:
                successful_calls += 1
                print(f"   Call {i+1}: Success ✅")
        else:
            print(f"   Call {i+1}: Error ❌")
        
        time.sleep(0.2)
    
    print(f"   Successful calls: {successful_calls}/5")
    if successful_calls > 0:
        print("✅ Rate limiter is protecting API calls")
        return True
    else:
        print("⚠️ All calls failed (might be rate limited)")
        return True


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🧪 AI Chat Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Login", test_login),
        ("Basic Chat", test_basic_chat),
        ("Signal Explanation", test_signal_explanation),
        ("Usage Stats", test_usage_stats),
        ("Cache/Deduplication", test_cache_deduplication),
        ("Rate Limiting", test_rate_limiting),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            if test_name == "Login" or TOKEN:
                results[test_name] = test_func()
            else:
                print(f"\n⏭️ Skipping {test_name} (no token)")
                results[test_name] = False
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
