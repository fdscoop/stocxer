#!/bin/bash

# Stop TradeWise Development Servers

echo "🛑 Stopping TradeWise servers..."

# Stop backend
if pgrep -f "python main.py" > /dev/null; then
    pkill -f "python main.py"
    echo "✅ Backend server stopped"
else
    echo "ℹ️  Backend was not running"
fi

# Stop frontend
if pgrep -f "node.*next dev" > /dev/null; then
    pkill -f "node.*next dev"
    echo "✅ Frontend server stopped"
else
    echo "ℹ️  Frontend was not running"
fi

echo ""
echo "🔍 Verifying ports are free..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8000 still in use"
else
    echo "✅ Port 8000 is free"
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 3000 still in use"
else
    echo "✅ Port 3000 is free"
fi

echo ""
echo "✅ Done!"
