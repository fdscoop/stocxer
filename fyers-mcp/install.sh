#!/bin/bash
# Installation script for FYERS MCP

echo "🚀 Installing FYERS MCP Server..."
echo "=================================="

# Install MCP SDK
echo "📦 Installing MCP SDK..."
pip install mcp anthropic

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please create .env with your FYERS credentials:"
    echo "  FYERS_CLIENT_ID=your_client_id"
    echo "  FYERS_SECRET_KEY=your_secret_key"
    echo "  FYERS_ACCESS_TOKEN=your_access_token"
    exit 1
fi

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
    echo "📱 Detected macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CONFIG_DIR="$HOME/.config/Claude"
    echo "🐧 Detected Linux"
else
    # Windows
    CONFIG_DIR="$APPDATA/Claude"
    echo "🪟 Detected Windows"
fi

# Create config directory
mkdir -p "$CONFIG_DIR"

# Get absolute path
MCP_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$MCP_DIR")"

# Create Claude Desktop config
echo "⚙️  Configuring Claude Desktop..."
cat > "$CONFIG_DIR/claude_desktop_config.json" << EOF
{
  "mcpServers": {
    "fyers": {
      "command": "python",
      "args": [
        "$MCP_DIR/server.py"
      ],
      "env": {
        "PYTHONPATH": "$PROJECT_DIR"
      }
    }
  }
}
EOF

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Make sure your .env file has FYERS credentials"
echo "2. Restart Claude Desktop"
echo "3. Look for 🔌 icon in Claude to see connected MCP servers"
echo "4. Try asking: 'What are my current positions?'"
echo ""
echo "💡 Config file location: $CONFIG_DIR/claude_desktop_config.json"
