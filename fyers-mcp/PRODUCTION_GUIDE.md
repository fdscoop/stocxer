# MCP Server Production Deployment Guide

## How It Works

### Architecture
```
┌─────────────────┐
│  Claude Desktop │  (Runs on your Mac)
│   (Local App)   │
└────────┬────────┘
         │
         │ MCP Protocol (stdio)
         │
┌────────▼────────┐
│  MCP Server     │  (Runs on your Mac)
│  (Python)       │
└────────┬────────┘
         │
         │ HTTP/HTTPS
         │
┌────────▼────────┐
│  Backend API    │  (stocxer.in or localhost:8000)
│  (FastAPI)      │
└────────┬────────┘
         │
         │ API Calls
         │
┌────────▼────────┐
│  Fyers API      │
│  Supabase DB    │
└─────────────────┘
```

### Key Points
1. **MCP Server is ALWAYS local** - runs on your Mac, not on the server
2. **Backend API can be local or remote** - configurable via environment variable
3. **Fyers token stored in Supabase** - shared between web app and MCP server

## Configuration

### Development Setup (Local Testing)
```bash
# In .env file
TRADEWISE_API_URL=http://localhost:8000
```

**Use when:**
- Developing locally
- Testing changes before deployment
- Running both backend and MCP on same machine

### Production Setup (Using Deployed Backend)
```bash
# In .env file
TRADEWISE_API_URL=https://stocxer.in
```

**Use when:**
- Backend is deployed to production
- Want to use live production data
- Not running local backend

## How Users Use It

### Each User's Setup
1. **Install MCP server locally** on their computer
2. **Configure Claude Desktop** to connect to local MCP server
3. **Set API URL** to your production server (stocxer.in)
4. **Authenticate via your web app** (stocxer.in) to get Fyers token
5. MCP server loads token from Supabase → calls your API → gets data

### Authentication Flow
```
1. User visits https://stocxer.in
2. User logs in and connects Fyers account
3. Token saved to Supabase (your database)
4. MCP server on user's Mac loads token from Supabase
5. MCP server calls https://stocxer.in/signals/... using the token
6. Your backend uses the token to call Fyers API
7. Data flows back to Claude Desktop
```

## Deployment Checklist

### Your Backend (stocxer.in)
- ✅ Deploy FastAPI backend to production
- ✅ Ensure `/signals/{symbol}/actionable` endpoint works
- ✅ Ensure `/screener/stock/{symbol}` endpoint works
- ✅ Configure CORS to allow requests from anywhere
- ✅ Supabase tokens table accessible

### User's Machine (Each User)
- ✅ Install Python 3.11+
- ✅ Clone/download MCP server files
- ✅ Run `pip install mcp`
- ✅ Create `.env` file with `TRADEWISE_API_URL=https://stocxer.in`
- ✅ Add Supabase credentials to `.env`
- ✅ Configure Claude Desktop with MCP server path
- ✅ Restart Claude Desktop

## Testing Production Setup

### 1. Test Backend Endpoints
```bash
# Test from command line
curl https://stocxer.in/screener/stock/SBIN

# Should return stock analysis data
```

### 2. Test MCP Server Locally
```bash
cd fyers-mcp
export TRADEWISE_API_URL=https://stocxer.in
python test_server.py
```

### 3. Test from Claude Desktop
After configuring, ask Claude:
- "Analyze NIFTY index"
- "Get analysis for SBIN stock"

## Common Issues

### Issue: Connection Failed
**Cause:** Backend not accessible
**Fix:** Check if https://stocxer.in is online and endpoints work

### Issue: Authentication Error
**Cause:** No valid Fyers token in Supabase
**Fix:** User needs to authenticate via web app first

### Issue: Timeout
**Cause:** Index analysis takes too long (>120 seconds)
**Fix:** Optimize `/signals/.../actionable` endpoint or increase timeout

## Security Notes

1. **MCP server runs locally** - users' Fyers tokens never leave their machine in memory
2. **Tokens stored in Supabase** - your database, encrypted at rest
3. **API calls use HTTPS** - encrypted in transit
4. **No order placement** - MCP server is read-only by design

## Distribution

Users can install your MCP server via:

### Option 1: GitHub Release
1. Create GitHub repo for MCP server
2. Users clone and configure
3. Each user runs on their own machine

### Option 2: NPM Package (Future)
Package MCP server as installable npm module

### Option 3: Direct Download
Provide ZIP file with:
- `server.py`
- `requirements.txt`
- `.env.example`
- `README.md`

Users extract, configure, and run locally.

## Summary

**For Production:**
1. Deploy backend to stocxer.in ✅
2. Users install MCP server locally (each user, on their computer)
3. Users configure `TRADEWISE_API_URL=https://stocxer.in` ✅
4. MCP server calls your production API
5. Everything works the same as local dev!

The only change needed: Set `TRADEWISE_API_URL` to your production URL instead of localhost.
