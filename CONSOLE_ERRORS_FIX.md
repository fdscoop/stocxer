# Console Error Fixes

## Issues Identified

1. **News API 500 Error** - Backend server not running
2. **IndexedDB .ldb Errors** - Browser extension storage issues (MetaMask/crypto wallets)
3. **"No saved scans found"** - Expected behavior when no scans have been performed yet

---

## Solutions

### 1. Fix News API 500 Error

**Problem**: The backend server at `http://localhost:8000` is not running, causing the frontend to receive 500 errors when fetching news.

**Solution**: Start the backend server

```bash
# Option A: Start with the provided script
cd /Users/bineshbalan/TradeWise
./start_server.sh

# Option B: Start manually
source venv/bin/activate
python main.py
```

The server should show:
```
✅ Razorpay client initialized successfully
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Application startup complete
```

**Verify it's working**:
```bash
curl "http://localhost:8000/api/news?hours=6&limit=10"
```

---

### 2. Fix IndexedDB .ldb Errors

**Problem**: Browser console shows repeated errors:
```
Uncaught Error: IO error: .../106987.ldb: Unable to create writable file 
(ChromeMethodBFE: 9::NewWritableFile::8)
```

**Root Cause**: This is NOT your application code. It's caused by:
- Browser extensions (MetaMask, crypto wallets, etc.)
- Chrome/Brave browser trying to write to IndexedDB
- Permission issues with browser profile directory

**Solutions** (choose one):

#### Quick Fix: Disable the problematic extension
1. Open Chrome/Brave Extensions (chrome://extensions/)
2. Temporarily disable MetaMask or other crypto wallet extensions
3. Reload your application
4. Re-enable after testing

#### Alternative: Use Incognito Mode
- Open your app in an Incognito/Private window
- Extensions are typically disabled by default
- This confirms the issue is extension-related

#### Permanent Fix: Clear browser data
1. Open DevTools (F12)
2. Go to Application tab → Storage
3. Click "Clear site data"
4. Or manually clear IndexedDB for localhost

#### Update Browser Extensions
- Update MetaMask and other extensions to latest versions
- Some versions have known IndexedDB write issues

**Note**: These errors don't affect your application's functionality. They're warnings from browser extensions failing to write to their own storage.

---

### 3. "SES Removing unpermitted intrinsics" Warning

**What it is**: This is from the Secure EcmaScript (SES) lockdown used by MetaMask for security.

**Fix**: This is normal and can be ignored. If it bothers you, disable MetaMask when not needed.

---

## Testing After Fixes

1. **Start backend server**:
   ```bash
   cd /Users/bineshbalan/TradeWise
   source venv/bin/activate
   python main.py
   ```

2. **In another terminal, test the API**:
   ```bash
   curl "http://localhost:8000/api/news?hours=6&limit=10"
   ```

3. **Open frontend** and check console:
   - News API errors should be gone
   - .ldb errors will remain if extensions are enabled (this is OK)
   - "No saved scans" is expected until you run a scan

---

## Running Both Services

### Quick Start (Recommended)

Use the provided startup script:

```bash
cd /Users/bineshbalan/TradeWise
./start_dev.sh
```

This will automatically start both backend and frontend servers.

To stop all servers:
```bash
./stop_dev.sh
```

### Manual Start

**Terminal 1 - Backend**:
```bash
cd /Users/bineshbalan/TradeWise
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend**:
```bash
cd /Users/bineshbalan/TradeWise/frontend
npm run dev
```

Then open: `http://localhost:3000`

---

## Environment Check

Make sure you have:
- ✅ Virtual environment activated (`source venv/bin/activate`)
- ✅ All dependencies installed (`pip install -r requirements.txt`)
- ✅ Razorpay credentials in environment variables
- ✅ Supabase credentials configured
- ✅ Frontend running on port 3000
- ✅ Backend running on port 8000

---

## Summary

| Error | Cause | Impact | Fix |
|-------|-------|---------|-----|
| News API 500 | Backend not running | ❌ Critical | Start `python main.py` |
| .ldb errors | Browser extensions | ⚠️ Cosmetic | Disable extensions or ignore |
| SES lockdown | MetaMask security | ℹ️ Info only | Ignore |
| No saved scans | No scans run yet | ℹ️ Expected | Run an options scan |

**Priority**: Fix #1 (backend server) first. The .ldb errors are from browser extensions and don't break your app.
