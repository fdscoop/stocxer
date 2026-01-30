# 📋 Paper Trading - Quick Reference Card

## 🚀 Quick Start (3 Steps)

### 1️⃣ Database Setup
```bash
# Go to Supabase → SQL Editor
# Copy: database/paper_trading_schema.sql
# Paste & Run

# Verify
python setup_paper_trading.py
```

### 2️⃣ Start Server
```bash
# Ensure Fyers balance = ₹0
python main.py
```

### 3️⃣ Configure & Go
```
1. Login → Paper Trading
2. Configure settings
3. Click "Start Trading"
```

---

## ⚙️ Recommended Settings

| Setting | Value | Why |
|---------|-------|-----|
| **Indices** | NIFTY | Most liquid |
| **Scan Interval** | 5 mins | Balance frequency/API quota |
| **Max Positions** | 3 | Risk management |
| **Capital/Trade** | ₹10,000 | Conservative start |
| **Min Confidence** | 65% | High probability |
| **Trading Mode** | Intraday | Clear daily results |

---

## 📡 API Endpoints

### Status
```http
GET /api/paper-trading/status
```

### Start/Stop
```http
POST /api/paper-trading/start
POST /api/paper-trading/stop
```

### Positions
```http
GET /api/paper-trading/positions?status=OPEN
POST /api/paper-trading/positions/{id}/close
```

### Performance
```http
GET /api/paper-trading/performance?days=7
```

---

## 🔍 Monitoring

### Check Status
```bash
# API health
curl http://localhost:8000/health

# Paper trading status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/paper-trading/status
```

### View Logs
```bash
# Backend logs
tail -f backend.log

# Activity log (via dashboard)
Activity Log tab → Recent events
```

---

## 🎯 Expected Behavior

### ✅ Normal Flow
```
9:15 AM → Scanner starts
9:20 AM → First scan
         → Signal generated (BUY CALL, 70% confidence)
         → Order placed
         → REJECTED (₹0 balance) ✅
         → Paper position created ✅
9:21 AM → Position monitoring starts
         → Current LTP: ₹152
         → Target 1: ₹180
         → Current P&L: +₹100
9:45 AM → Target 1 hit
         → Position closed
         → Realized P&L: +₹1,500 ✅
```

### ⚠️ Important Notes
- **Orders WILL be rejected** (₹0 balance)
- **This is expected and correct** ✅
- **Positions still tracked** ✅
- **P&L calculated as if succeeded** ✅

---

## 🚨 Troubleshooting

### Scanner Not Starting
```python
# Check: Market closed?
# Check: Config enabled?
# Fix: Enable in dashboard
```

### No Signals Generated
```python
# Check: Market hours (9:15 - 3:30)?
# Check: Fyers token valid?
# Fix: Refresh token
```

### Positions Not Exiting
```python
# Check: Scanner running?
# Check: Targets reasonable?
# Fix: Manual close or adjust targets
```

---

## 📊 Performance Metrics

### Good Performance
- **Win Rate:** > 60%
- **Profit Factor:** > 1.5
- **Avg Win:** > Avg Loss * 1.5
- **Max Drawdown:** < 20%

### Warning Signs
- **Win Rate:** < 50%
- **Profit Factor:** < 1.0
- **Consecutive Losses:** > 5
- **Max Drawdown:** > 30%

---

## 🎯 Daily Routine

### Morning (9:00 AM)
- [ ] Check Fyers balance (should be ₹0)
- [ ] Verify Fyers token
- [ ] Start backend server
- [ ] Enable paper trading

### During Market (9:15 - 3:30 PM)
- [ ] Monitor positions (every 2 hours)
- [ ] Check activity log for errors
- [ ] Review current P&L
- [ ] Adjust settings if needed

### Evening (After 3:30 PM)
- [ ] Review daily performance
- [ ] Analyze win/loss trades
- [ ] Note observations
- [ ] Plan adjustments

---

## 🔐 Security Checklist

- [ ] Fyers token stored in .env (not committed)
- [ ] Supabase keys in .env (not committed)
- [ ] RLS policies enabled in Supabase
- [ ] Bearer token required for all endpoints
- [ ] Service role key only on server

---

## 📈 Optimization Tips

### Improve Win Rate
1. Increase `min_confidence` to 70%
2. Reduce `max_positions` to 2
3. Tighten stop-loss by 10%
4. Review signal quality

### Reduce Losses
1. Use tighter stop-loss
2. Take profits at Target 1
3. Avoid high volatility days
4. Review exit reasons

### Increase Profits
1. Let winners run to Target 2
2. Scale position sizing
3. Add more indices (BANKNIFTY)
4. Optimize scan frequency

---

## 🎓 Learning Path

### Week 1: Basics
- Understand system flow
- Monitor 1 trade end-to-end
- Review all exit reasons
- Check P&L calculations

### Week 2: Analysis
- Calculate your win rate
- Analyze best/worst trades
- Identify patterns
- Adjust confidence threshold

### Week 3: Optimization
- Test different settings
- Compare results
- Find optimal parameters
- Document learnings

### Week 4: Transition
- Fund Fyers account
- Start with ₹5k/trade
- Compare paper vs real
- Scale gradually

---

## 📞 Quick Help

### Error: "Scanner already running"
```bash
# Stop and restart
POST /api/paper-trading/stop
# Wait 10 seconds
POST /api/paper-trading/start
```

### Error: "Order rejected"
```bash
# This is NORMAL for paper trading ✅
# Position still created
# Check positions tab
```

### Error: "No signals generated"
```bash
# Check market hours
# Verify Fyers token
# Review activity log
# Lower min_confidence
```

---

## 🎯 Success Indicators

✅ **Week 1:** System running smoothly  
✅ **Week 2:** Win rate > 55%  
✅ **Week 3:** Profit factor > 1.2  
✅ **Week 4:** Ready for real money  

---

## 🔗 Useful Links

- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Dashboard:** http://localhost:3000/paper-trading
- **Complete Guide:** PAPER_TRADING_GUIDE.md

---

## 🎉 You're Ready!

**Remember:**
1. Keep Fyers balance at ₹0
2. Monitor regularly
3. Review performance
4. Adjust & improve
5. Transition when confident

**Good luck with your paper trading! 🚀**

---

*Last Updated: January 30, 2026*
