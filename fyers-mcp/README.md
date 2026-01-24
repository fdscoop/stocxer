# FYERS MCP - AI Assistant Integration

Connect your FYERS trading account to AI assistants like Claude Desktop, Cursor, and Windsurf. Your AI assistant will have instant access to your positions, orders, portfolio, and market analysis.

## 🌟 Features

### Resources (Read-only context)
- **Portfolio Summary** - Overall funds, margin, P&L
- **Current Positions** - All open positions with live updates
- **Today's Orders** - Complete order book
- **Market Indices** - NIFTY, BANKNIFTY, SENSEX live data

### Tools (Actions AI can perform)
- `get_positions` - View all open positions
- `get_orders` - Check order status
- `get_portfolio_summary` - Complete portfolio overview
- `get_option_chain` - Live option chain with OI, volume, Greeks
- `analyze_index` - ICT + ML analysis (Order Blocks, FVGs, Probability)
- `get_stock_quote` - Live quotes for any symbol
- `get_historical_data` - Price history for technical analysis
- `search_symbol` - Find stock symbols

## 🚀 Quick Installation

### For Claude Desktop (Recommended)

1. **Install MCP SDK**
   ```bash
   cd /Users/bineshbalan/TradeWise/mcp
   pip install mcp
   ```

2. **Run Installation Script**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Restart Claude Desktop**
   - Close Claude Desktop completely
   - Reopen it
   - Look for 🔌 icon at the bottom to verify connection

### For Cursor / Windsurf

1. **Install MCP SDK**
   ```bash
   pip install mcp
   ```

2. **Add to your AI assistant settings**
   ```json
   {
     "mcp": {
       "servers": {
         "fyers": {
           "command": "python",
           "args": ["/Users/bineshbalan/TradeWise/mcp/server.py"]
         }
       }
     }
   }
   ```

## 💬 Example Conversations

Once installed, you can ask Claude:

**Portfolio & Positions**
- *"What are my current positions?"*
- *"Show me my portfolio P&L"*
- *"Do I have any NIFTY positions open?"*

**Option Analysis**
- *"Get the NIFTY option chain and tell me the PCR ratio"*
- *"What's the max pain for BANKNIFTY this week?"*
- *"Show me high OI strikes for FINNIFTY"*

**Market Analysis**
- *"Analyze NIFTY using ICT concepts - show me order blocks"*
- *"What's the multi-timeframe trend for BANKNIFTY?"*
- *"Get RELIANCE stock quote"*

**Advanced Queries**
- *"Based on my current NIFTY positions, should I hedge?"*
- *"Compare the option chain with my open positions"*
- *"What's the probability analysis for BANKNIFTY?"*

## 🔧 Configuration

### Environment Variables

Make sure your `.env` file contains:
```bash
# FYERS API Credentials
FYERS_CLIENT_ID=your_client_id
FYERS_SECRET_KEY=your_secret_key  
FYERS_ACCESS_TOKEN=your_access_token  # Optional - loaded from Supabase if not set

# TradeWise Backend API
TRADEWISE_API_URL=http://localhost:8000  # Development
# TRADEWISE_API_URL=https://stocxer.in  # Production

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Switching Between Development and Production

**Development Mode (Local Backend)**
```bash
TRADEWISE_API_URL=http://localhost:8000
```

**Production Mode (Deployed Backend)**
```bash
TRADEWISE_API_URL=https://stocxer.in
```

After changing the URL, restart Claude Desktop to apply changes.

### Manual Configuration

Edit Claude Desktop config at:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fyers": {
      "command": "python",
      "args": ["/Users/bineshbalan/TradeWise/mcp/server.py"],
      "env": {
        "PYTHONPATH": "/Users/bineshbalan/TradeWise"
      }
    }
  }
}
```

## 🔍 Troubleshooting

### MCP Server Not Connecting

1. **Check if MCP SDK is installed**
   ```bash
   pip list | grep mcp
   ```

2. **Test server manually**
   ```bash
   python /Users/bineshbalan/TradeWise/mcp/server.py
   ```

3. **Check Claude Desktop logs**
   - macOS: `~/Library/Logs/Claude/mcp*.log`
   - Look for connection errors

### No Data Returned

1. **Verify FYERS token is valid**
   ```bash
   echo $FYERS_ACCESS_TOKEN
   ```

2. **Check server logs** - Server prints connection status

3. **Re-authenticate with FYERS**
   - Visit `/auth/url` endpoint in your app
   - Complete OAuth flow

### Limited Features

If you see "⚠️ Some features limited":
- Set `FYERS_ACCESS_TOKEN` in your environment
- Server needs valid token for live data

## 🎯 What Makes This Special

### vs Traditional Trading Platforms

**Sensibull, Quantsapp, Opstra:**
- ❌ Copy-paste data to ask questions
- ❌ Manual analysis required
- ❌ No AI context awareness

**Stocxer AI with MCP:**
- ✅ AI knows your positions automatically
- ✅ Ask questions in natural language
- ✅ Get personalized analysis instantly

### Security

- **Read-only access** - Cannot place orders or modify positions
- **Local execution** - MCP server runs on your machine
- **No data sharing** - Your data stays private
- **Token-based** - Uses your existing FYERS credentials

## 📚 API Reference

### Resources

| URI | Description |
|-----|-------------|
| `fyers://portfolio/summary` | Funds, margin, total P&L |
| `fyers://positions/current` | All open positions |
| `fyers://orders/today` | Today's order book |
| `fyers://market/indices` | NIFTY, BANKNIFTY, SENSEX |

### Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `get_positions` | None | Open positions with P&L |
| `get_orders` | None | Order book with status |
| `get_portfolio_summary` | None | Complete portfolio data |
| `get_option_chain` | index, expiry_type | OI, volume, Greeks, PCR |
| `analyze_index` | index, timeframes | ICT analysis with signals |
| `get_stock_quote` | symbol | Live quote data |
| `get_historical_data` | symbol, days, resolution | Price history |
| `search_symbol` | query | Matching symbols |

## 🚀 Advanced Usage

### Custom Prompts

Create saved prompts in Claude:

```
System: You have access to my FYERS trading account via MCP. 
When I ask about positions or market analysis, use the FYERS tools 
to get real-time data. Always check current positions before 
suggesting trades.
```

### Integration with Other Tools

Combine FYERS MCP with:
- **Filesystem MCP** - Save analysis reports
- **Browser MCP** - Fetch news for context
- **SQL MCP** - Query historical trade data

## 📊 Dashboard Integration

The MCP server uses the same backend as your web dashboard:
- Same FYERS client
- Same analyzers (ICT, ML, Options)
- Same data sources

This ensures consistency between your web UI and AI assistant.

## 🎓 Learning Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/claude/desktop/mcp)
- [FYERS API Docs](https://fyers.in/api-docs)

## 🆘 Support

Issues or questions?
1. Check logs: `~/Library/Logs/Claude/mcp*.log`
2. Test manually: `python mcp/server.py`
3. Open GitHub issue with logs

## 📝 License

Part of Stocxer AI - FDS COOP LLP

---

**Made with ❤️ for serious traders who want AI-powered insights**
