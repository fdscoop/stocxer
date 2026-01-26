#!/bin/bash

# Setup external cron job to keep news fetching every hour
# This works with Render free tier (solves the sleep issue)

echo "=================================================="
echo "📰 Setting up News Fetch Cron Job"
echo "=================================================="
echo ""

# Your API URL
API_URL="https://stocxer-ai.onrender.com"
FETCH_ENDPOINT="$API_URL/fetch-news"

echo "1. Testing API connection..."
if curl -s "$API_URL/health" | grep -q "online"; then
    echo "   ✅ API is online"
else
    echo "   ❌ API is offline or not responding"
    echo "   Please deploy your changes to Render first"
    exit 1
fi

echo ""
echo "2. Testing /fetch-news endpoint..."
RESPONSE=$(curl -s "$FETCH_ENDPOINT")
if echo "$RESPONSE" | grep -q "success"; then
    echo "   ✅ /fetch-news endpoint is working"
    echo "   Response: $RESPONSE"
else
    echo "   ❌ /fetch-news endpoint not found"
    echo "   Response: $RESPONSE"
    echo "   Please deploy your changes to Render first"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "🎯 NEXT STEPS:"
echo ""
echo "Option 1: Use cron-job.org (Recommended - Free & Easy)"
echo "   1. Go to https://cron-job.org"
echo "   2. Sign up for free account"
echo "   3. Create new cron job:"
echo "      Title: TradeWise News Fetcher"
echo "      URL: $FETCH_ENDPOINT"
echo "      Schedule: Every 1 hour"
echo "      Method: GET"
echo ""
echo "Option 2: Use GitHub Actions"
echo "   1. Create .github/workflows/fetch-news.yml"
echo "   2. Add the workflow from NEWS_SCHEDULER_SETUP.md"
echo "   3. Push to GitHub"
echo ""
echo "Option 3: Use EasyCron"
echo "   1. Go to https://www.easycron.com/"
echo "   2. Sign up (free plan)"
echo "   3. Add cron job with URL: $FETCH_ENDPOINT"
echo ""
echo "📊 Monitor your setup:"
echo "   Health: $API_URL/health"
echo "   Trigger manually: $FETCH_ENDPOINT"
echo ""
echo "💾 Check database in Supabase:"
echo "   Table: market_news"
echo "   Log: news_fetch_log"
echo ""
