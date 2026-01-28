#!/bin/bash

# Start TradeWise Backend Server
echo "🚀 Starting TradeWise Backend Server..."

# Activate virtual environment
source venv/bin/activate

# Check if required packages are installed
echo "📦 Checking dependencies..."
pip list | grep -q razorpay || pip install -q razorpay
pip list | grep -q fastapi || pip install -q -r requirements.txt

# Start the server
echo "✅ Starting uvicorn server on http://localhost:8000"
python main.py
