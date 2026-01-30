# TradeWise - Quick Start Guide

## 🚀 Starting the Application

```bash
cd /Users/bineshbalan/TradeWise
./start_dev.sh
```

This starts both backend (port 8000) and frontend (port 3000).

---

## 🔍 Testing Options Scanner

### Quick Test (Command Line)
```bash
python test_options_scan_debug.py
```

**Expected time:** 90-180 seconds (for live data)  
**Expected result:** Live scan with probability analysis

### What You'll See:
```
✅ Backend health check
✅ Authentication (bineshch@gmail.com)
✅ Fyers token check
✅ Scanning 49/50 NIFTY constituent stocks
✅ Probability analysis (BULLISH/BEARISH prediction)
✅ Option chain analysis
✅ Top 5 options with scores
```

---

## 📊 Options Scanner Features

### What It Analyzes:

1. **ALL Constituent Stocks** (49-50 per index)
   - NIFTY: 50 stocks
   - BANKNIFTY: 14 banks
   - Scans each stock's trend
   - Predicts index direction

2. **Trend Reversal Detection** ✅
   - Multi-timeframe analysis
   - Order blocks & Fair Value Gaps
   - Volume surge detection
   - Momentum shifts

3. **Option Charts (CE & PE)** ✅
   - Price action analysis
   - Volume spikes
   - Open Interest buildup
   - Greeks evolution (Delta, Gamma, Theta, Vega)

4. **Trading Recommendations**
   - Exact strike prices
   - Entry price
   - Target levels
   - Stop loss

---

## 🎯 How to Use Dashboard

1. **Open:** http://localhost:3000
2. **Select Index:** NIFTY, BANKNIFTY, SENSEX, etc.
3. **Select Expiry:** Weekly or Monthly
4. **Click "Scan Options"**
5. **Wait:** 90-180 seconds (for live API data)
6. **Review Results:**
   - Probability analysis (% bullish/bearish)
   - Recommended option type (CE/PE)
   - Top options ranked by score
   - Entry/exit levels

---

## 📈 Understanding Results

### Probability Analysis
```
Expected Direction: BEARISH
Confidence: 31.2%
Probability Down: 66.5%
Recommended: PUT options

Translation:
→ 61% of NIFTY stocks are bearish
→ Index likely to fall
→ Trade PUT options for profit
```

### Option Score
```
Score: 102.6/100
⭐ Probability Boosted (+20%)

Translation:
→ Base score: 85.5
→ Matches probability direction
→ Gets 20% boost
→ Final score: 102.6
```

### Recommendations
```
PUT @ 24500
LTP: ₹38.00
Volume: 13.5M (excellent liquidity)
OI: 2M (strong interest)
Delta: -0.562 (good sensitivity)
Recommendation: Strong BUY - OTM PUT

Translation:
→ Buy at ₹38
→ High volume = easy entry/exit
→ Delta -0.56 = moves 56% of index move
→ Out-of-the-money = lower cost
```

---

## 🛠️ Troubleshooting

### Backend Not Running?
```bash
lsof -i :8000
# If nothing, start with:
./start_dev.sh
```

### Frontend Not Running?
```bash
lsof -i :3000
# If nothing:
cd frontend && npm run dev
```

### Check Logs
```bash
# Backend logs
tail -f server.log

# Frontend logs  
tail -f frontend.log
```

### Authentication Issues?
```bash
# Re-test with:
python test_options_scan_debug.py
```

---

## 📁 Useful Scripts

| Script | Purpose |
|--------|---------|
| `start_dev.sh` | Start both servers |
| `stop_dev.sh` | Stop all servers |
| `test_options_scan_debug.py` | Test scanner end-to-end |
| `start_server.sh` | Start backend only |

---

## 🔐 Credentials

**Email:** bineshch@gmail.com  
**Password:** Tra@2026

Used for testing and accessing the dashboard.

---

## ✅ Current Status

- ✅ Backend: Running on port 8000
- ✅ Frontend: Ready (start with script)
- ✅ Options Scanner: Fully operational
- ✅ Live Data: Connected to Fyers API
- ✅ Probability Analysis: Working (49/50 stocks)
- ✅ News Sentiment: Integrated
- ✅ Trend Reversals: Detected

---

## 🎓 Key Concepts

### What "Probability Analysis" Means
Instead of just looking at index charts, the scanner:
1. Scans ALL 50 NIFTY stocks individually
2. Checks if each is bullish or bearish
3. Aggregates to predict index direction
4. Recommends CE or PE options accordingly

**Example:**
- 30 stocks bearish (60%)
- 20 stocks bullish (40%)
- **Prediction:** Index will fall
- **Trade:** Buy PUT options

### What "Trend Reversal" Detection Means
The scanner checks:
- **Divergences:** Price up but momentum down = reversal
- **Order Blocks:** Where smart money entered
- **Fair Value Gaps:** Price imbalance zones
- **Volume Spikes:** Institutional activity

**Example:**
- Index at resistance
- Volume declining
- 60% stocks turning bearish
- **Signal:** Reversal likely, buy PUTs

### Why CE and PE Analysis
The scanner evaluates BOTH:
- **Call Options (CE):** Profit when index rises
- **Put Options (PE):** Profit when index falls

Based on probability analysis, it recommends which type to trade.

**Current Example:**
- 61% stocks bearish
- **Recommendation:** Trade PUTs
- Top 5 options are all PUTs
- Scores boosted for PUT options

---

## 📞 Support

If you encounter issues:

1. Check [OPTIONS_SCANNER_STATUS.md](OPTIONS_SCANNER_STATUS.md) for detailed status
2. Check [CONSOLE_ERRORS_FIX.md](CONSOLE_ERRORS_FIX.md) for common fixes
3. Run `python test_options_scan_debug.py` for diagnostics
4. Check logs: `tail -f server.log`

---

**Last Updated:** January 28, 2026  
**Test Status:** ✅ All systems operational  
**Data Source:** Live (Fyers API)
