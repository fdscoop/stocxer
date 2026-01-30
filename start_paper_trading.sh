#!/bin/bash

# =============================================================================
# PAPER TRADING - QUICK START SCRIPT
# =============================================================================
# This script helps you quickly set up and test the paper trading system
# =============================================================================

set -e  # Exit on error

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║        🤖 AUTOMATED PAPER TRADING - QUICK START                  ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 installed${NC}"

# Check virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment not found${NC}"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
echo -e "${GREEN}✓ Virtual environment ready${NC}"

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Check dependencies
echo "Checking dependencies..."
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""

# Step 2: Environment variables
echo -e "${BLUE}Step 2: Checking environment variables...${NC}"
echo ""

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Please create .env file with your Supabase credentials"
    exit 1
fi

if ! grep -q "SUPABASE_URL" .env; then
    echo -e "${RED}❌ SUPABASE_URL not found in .env${NC}"
    exit 1
fi

if ! grep -q "SUPABASE_SERVICE_ROLE_KEY" .env; then
    echo -e "${RED}❌ SUPABASE_SERVICE_ROLE_KEY not found in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment variables configured${NC}"
echo ""

# Step 3: Database setup
echo -e "${BLUE}Step 3: Database setup...${NC}"
echo ""

echo "⚠️  You need to manually run the SQL schema in Supabase"
echo ""
echo "Steps:"
echo "1. Go to: https://app.supabase.com"
echo "2. Navigate to: SQL Editor"
echo "3. Open: database/paper_trading_schema.sql"
echo "4. Copy all content"
echo "5. Paste in SQL Editor and click 'Run'"
echo ""
read -p "Have you completed the database setup? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠ Please complete database setup first${NC}"
    echo "File location: database/paper_trading_schema.sql"
    exit 1
fi

# Verify tables
echo "Verifying database tables..."
python3 setup_paper_trading.py || {
    echo -e "${RED}❌ Database verification failed${NC}"
    echo "Please ensure you've run the SQL schema in Supabase"
    exit 1
}

echo ""

# Step 4: Fyers setup
echo -e "${BLUE}Step 4: Fyers configuration...${NC}"
echo ""

if ! grep -q "FYERS_CLIENT_ID" .env; then
    echo -e "${RED}❌ Fyers credentials not found${NC}"
    echo "Please add to .env:"
    echo "  FYERS_CLIENT_ID=your_client_id"
    echo "  FYERS_SECRET_KEY=your_secret_key"
    echo "  FYERS_ACCESS_TOKEN=your_access_token"
    exit 1
fi

echo -e "${GREEN}✓ Fyers credentials configured${NC}"
echo ""

echo -e "${YELLOW}⚠️  IMPORTANT: Keep your Fyers balance at ₹0 for paper trading${NC}"
echo "   Orders will be rejected but positions will be tracked"
echo ""
read -p "Is your Fyers balance at ₹0? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠ Please set your Fyers balance to ₹0 for testing${NC}"
    exit 1
fi

echo ""

# Step 5: Start server
echo -e "${BLUE}Step 5: Starting backend server...${NC}"
echo ""

echo "Starting FastAPI server..."
python3 main.py &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}❌ Server failed to start${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✓ Backend server running (PID: $SERVER_PID)${NC}"
echo ""

# Step 6: Instructions
echo -e "${BLUE}Step 6: Next steps...${NC}"
echo ""

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ SETUP COMPLETE!                             ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

echo "🎯 What's Running:"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/health"
echo ""

echo "🚀 Quick Test:"
echo "   1. Open your browser"
echo "   2. Go to: http://localhost:8000/docs"
echo "   3. Find: Paper Trading endpoints"
echo "   4. Test: GET /api/paper-trading/config"
echo ""

echo "📱 Frontend Setup (if using Next.js):"
echo "   cd frontend"
echo "   npm install"
echo "   npm run dev"
echo "   Open: http://localhost:3000/paper-trading"
echo ""

echo "📊 Paper Trading Dashboard:"
echo "   1. Login to your account"
echo "   2. Navigate to Paper Trading section"
echo "   3. Configure settings:"
echo "      - Indices: NIFTY"
echo "      - Scan Interval: 5 minutes"
echo "      - Max Positions: 3"
echo "      - Capital Per Trade: ₹10,000"
echo "      - Min Confidence: 65%"
echo "   4. Click 'Start Trading'"
echo ""

echo "🔍 Monitor Progress:"
echo "   • View Positions tab for active trades"
echo "   • Check Activity Log for events"
echo "   • Review Performance for metrics"
echo ""

echo "⚠️  IMPORTANT REMINDERS:"
echo "   1. Keep Fyers balance at ₹0"
echo "   2. Orders will be REJECTED (expected)"
echo "   3. Positions will be tracked anyway"
echo "   4. Monitor logs: tail -f backend.log"
echo ""

echo "📖 Documentation:"
echo "   • Complete Guide: PAPER_TRADING_GUIDE.md"
echo "   • API Reference: http://localhost:8000/docs"
echo "   • Database Schema: database/paper_trading_schema.sql"
echo ""

echo "🛑 To Stop:"
echo "   kill $SERVER_PID"
echo "   Or: ./stop_dev.sh"
echo ""

echo -e "${GREEN}Happy Paper Trading! 🎉${NC}"
echo ""

# Keep script running to show logs
echo "Press Ctrl+C to stop monitoring logs..."
echo ""
tail -f backend.log 2>/dev/null || {
    echo "Backend log not found. Server output:"
    wait $SERVER_PID
}
