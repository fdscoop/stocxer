"""
Test News Sentiment API endpoints like a frontend user would
Makes HTTP requests to the FastAPI server
"""
import requests
import json
from time import sleep

# API Base URL
BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_response(response):
    """Pretty print JSON response"""
    if response.status_code == 200:
        print(f"✅ Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Status: {response.status_code}")
        print(response.text)

# Test 1: Check news service status
print_section("TEST 1: Check News Service Status")
print(f"GET {BASE_URL}/api/news/status")
try:
    response = requests.get(f"{BASE_URL}/api/news/status")
    print_response(response)
except Exception as e:
    print(f"❌ Error: {e}")
    print("⚠️  Make sure the server is running: uvicorn main:app --reload")

sleep(1)

# Test 2: Get market sentiment
print_section("TEST 2: Get Market Sentiment (1-hour window)")
print(f"GET {BASE_URL}/api/sentiment?time_window=1hr")
try:
    response = requests.get(f"{BASE_URL}/api/sentiment?time_window=1hr")
    print_response(response)
except Exception as e:
    print(f"❌ Error: {e}")

sleep(1)

# Test 3: Get sentiment for different time windows
print_section("TEST 3: Get Sentiment for All Time Windows")
for window in ["15min", "1hr", "4hr", "1day"]:
    print(f"\n📊 {window} window:")
    try:
        response = requests.get(f"{BASE_URL}/api/sentiment?time_window={window}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Sentiment: {data.get('overall_sentiment', 'N/A').upper()}")
            print(f"     Score: {data.get('sentiment_score', 0)}")
            print(f"     Mood: {data.get('market_mood', 'Unknown')}")
            print(f"     Articles: {data.get('total_articles', 0)}")
        else:
            print(f"  ⚠️  No data for {window}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

sleep(1)

# Test 4: Get recent news articles
print_section("TEST 4: Get Recent News Articles")
print(f"GET {BASE_URL}/api/news?hours=24&limit=5")
try:
    response = requests.get(f"{BASE_URL}/api/news?hours=24&limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"Total articles: {data.get('count', 0)}")
        print("\nArticles:")
        for i, article in enumerate(data.get('articles', [])[:5], 1):
            print(f"\n{i}. {article.get('title')}")
            print(f"   Source: {article.get('source')}")
            print(f"   Sentiment: {article.get('sentiment')} ({article.get('sentiment_score')})")
            print(f"   Published: {article.get('published_at')}")
    else:
        print_response(response)
except Exception as e:
    print(f"❌ Error: {e}")

sleep(1)

# Test 5: Get sentiment for NIFTY signal
print_section("TEST 5: Get Sentiment for NIFTY Trading Signal")
print(f"GET {BASE_URL}/api/sentiment/for-signal?symbol=NIFTY&signal_type=BUY")
try:
    response = requests.get(f"{BASE_URL}/api/sentiment/for-signal?symbol=NIFTY&signal_type=BUY")
    print_response(response)
except Exception as e:
    print(f"❌ Error: {e}")

sleep(1)

# Test 6: Filter news by index
print_section("TEST 6: Get NIFTY-specific News")
print(f"GET {BASE_URL}/api/news?hours=24&indices=NIFTY&limit=3")
try:
    response = requests.get(f"{BASE_URL}/api/news?hours=24&indices=NIFTY&limit=3")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"Total NIFTY articles: {data.get('count', 0)}")
        for i, article in enumerate(data.get('articles', []), 1):
            print(f"\n{i}. {article.get('title')}")
            print(f"   Indices: {', '.join(article.get('affected_indices', []))}")
    else:
        print_response(response)
except Exception as e:
    print(f"❌ Error: {e}")

sleep(1)

# Test 7: Filter news by sector
print_section("TEST 7: Get Banking Sector News")
print(f"GET {BASE_URL}/api/news?hours=24&sectors=banking&limit=3")
try:
    response = requests.get(f"{BASE_URL}/api/news?hours=24&sectors=banking&limit=3")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"Total banking articles: {data.get('count', 0)}")
        for i, article in enumerate(data.get('articles', []), 1):
            print(f"\n{i}. {article.get('title')}")
            print(f"   Sectors: {', '.join(article.get('affected_sectors', []))}")
    else:
        print_response(response)
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("✅ All API Tests Complete!")
print("=" * 80)
print("\n💡 These are the same endpoints your frontend will call:")
print("   - /api/news/status - Check service status and API usage")
print("   - /api/sentiment - Get overall market sentiment")
print("   - /api/sentiment/for-signal - Get sentiment for specific signals")
print("   - /api/news - Get recent news with filters")
print("\n📝 The sentiment is automatically integrated into:")
print("   - Options scanner: /api/options/scan")
print("   - Stock screener: /api/screener/scan")
