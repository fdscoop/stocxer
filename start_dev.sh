#!/bin/bash

# TradeWise Development Server Startup
# This script starts both backend and frontend servers

echo "🚀 TradeWise Development Server Startup"
echo "========================================"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️  Backend already running on port 8000${NC}"
else
    echo -e "${GREEN}Starting backend server...${NC}"
    cd /Users/bineshbalan/TradeWise
    source venv/bin/activate
    nohup python main.py > server.log 2>&1 &
    BACKEND_PID=$!
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    sleep 2
fi

# Check if frontend is already running
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️  Frontend already running on port 3000${NC}"
else
    echo -e "${GREEN}Starting frontend server...${NC}"
    cd /Users/bineshbalan/TradeWise/frontend
    nohup npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
fi

echo ""
echo "========================================="
echo -e "${GREEN}✅ TradeWise is running!${NC}"
echo ""
echo "📡 Backend:  http://localhost:8000"
echo "🌐 Frontend: http://localhost:3000"
echo ""
echo "📋 Logs:"
echo "   Backend:  tail -f server.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop servers:"
echo "   pkill -f 'python main.py'"
echo "   pkill -f 'node.*next dev'"
echo "========================================="
