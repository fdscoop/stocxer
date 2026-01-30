# ✅ Automated Paper Trading - Implementation Checklist

## 📦 Files Delivered

### Database
- [x] `database/paper_trading_schema.sql` (5 tables, RLS, indexes, functions)

### Backend
- [x] `src/services/paper_trading_service.py` (Core trading logic, ~700 lines)
- [x] `main.py` (11 API endpoints added)

### Frontend
- [x] `frontend/components/trading/PaperTradingDashboard.tsx` (Full dashboard)

### Setup & Scripts
- [x] `setup_paper_trading.py` (Database verification)
- [x] `start_paper_trading.sh` (Quick start script)

### Documentation
- [x] `PAPER_TRADING_GUIDE.md` (Complete guide, 800+ lines)
- [x] `PAPER_TRADING_SUMMARY.md` (Implementation summary)
- [x] `PAPER_TRADING_QUICK_REF.md` (Quick reference card)

---

## 🎯 Setup Steps (Do This Now!)

### 1. Database Setup
```bash
# ⚠️ REQUIRED: Manual SQL execution in Supabase

1. Go to: https://app.supabase.com
2. Select your project
3. Navigate to: SQL Editor
4. Click: "New query"
5. Copy all content from: database/paper_trading_schema.sql
6. Paste into editor
7. Click: "Run"
8. Wait for: Success message

# ✅ Should see:
# - 5 tables created
# - Indexes created
# - Functions created
# - Triggers created
# - RLS policies enabled
```

### 2. Verify Setup
```bash
# Run verification script
python setup_paper_trading.py

# Expected output:
# ✓ Supabase credentials found
# ✓ Loaded SQL schema
# ✓ Table 'paper_trading_config' exists
# ✓ Table 'paper_trading_signals' exists
# ✓ Table 'paper_trading_positions' exists
# ✓ Table 'paper_trading_activity_log' exists
# ✓ Table 'paper_trading_performance' exists
# ✅ PAPER TRADING DATABASE SETUP COMPLETE!
```

### 3. Prepare Fyers Account
```bash
# ⚠️ CRITICAL for paper trading

# Option A: Withdraw funds (safest)
1. Login to Fyers
2. Go to: Funds → Withdraw
3. Withdraw all available balance
4. Wait for: Balance = ₹0

# Option B: Track balance (if withdrawal not possible)
# Just ensure you know the exact balance
# Orders will still be rejected if insufficient for the trade
```

### 4. Start Backend
```bash
# Quick start
./start_paper_trading.sh

# Or manual start
source venv/bin/activate
python main.py

# Expected output:
# INFO:     Started server process
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Test API
```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status": "healthy", ...}

# Test paper trading endpoint (need token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/paper-trading/config

# Should return:
# {"enabled": false, "indices": ["NIFTY"], ...}
```

### 6. Frontend Setup (Optional)
```bash
cd frontend

# Install dependencies (if not already)
npm install

# Start development server
npm run dev

# Expected output:
# ready - started server on 0.0.0.0:3000
# ✓ Compiled successfully
```

### 7. Create Next.js Page (If needed)
```typescript
// frontend/app/paper-trading/page.tsx

import PaperTradingDashboard from '@/components/trading/PaperTradingDashboard';

export default function PaperTradingPage() {
  return <PaperTradingDashboard />;
}
```

### 8. Add to Navigation
```typescript
// Add to your nav menu
{
  name: 'Paper Trading',
  href: '/paper-trading',
  icon: ActivityIcon,
  description: 'Automated paper trading'
}
```

---

## 🧪 Testing Checklist

### Phase 1: Basic Functionality
- [ ] Database tables created successfully
- [ ] Backend server starts without errors
- [ ] API endpoints return valid responses
- [ ] Frontend dashboard loads
- [ ] User can login and access dashboard

### Phase 2: Configuration
- [ ] User can view default config
- [ ] User can save config changes
- [ ] Config persists across sessions
- [ ] Validation works (min/max values)

### Phase 3: Order Testing (₹0 Balance)
- [ ] Fyers balance confirmed at ₹0
- [ ] System generates signal
- [ ] Order placed via Fyers API
- [ ] Order REJECTED (expected) ✅
- [ ] Paper position created anyway ✅
- [ ] Rejection logged in activity

### Phase 4: Position Management
- [ ] Positions visible in dashboard
- [ ] Current LTP updates
- [ ] Current P&L calculates correctly
- [ ] Targets and SL displayed
- [ ] Manual close works

### Phase 5: Automated Trading
- [ ] Scanner starts successfully
- [ ] Scans run on schedule (every 5 mins)
- [ ] Signals generated automatically
- [ ] Orders placed automatically
- [ ] Positions monitored every minute
- [ ] Exits trigger on target/SL
- [ ] EOD exit at 3:15 PM

### Phase 6: Performance
- [ ] Daily performance calculates
- [ ] Win rate accurate
- [ ] P&L totals correct
- [ ] Metrics update in real-time
- [ ] Historical data persists

### Phase 7: Activity Log
- [ ] All events logged
- [ ] Timestamps correct
- [ ] Error details captured
- [ ] Searchable/filterable

---

## 🎯 First Day Test Plan

### Morning (9:00 AM)
```
✅ Check Fyers balance = ₹0
✅ Start backend: python main.py
✅ Open dashboard: http://localhost:3000/paper-trading
✅ Login to account
✅ Configure settings:
   - Indices: NIFTY
   - Interval: 5 minutes
   - Max Positions: 3
   - Capital: ₹10,000
   - Min Confidence: 65%
✅ Save configuration
✅ Click "Start Trading"
```

### During Market (9:15 AM - 3:30 PM)
```
9:15 AM → Verify scanner started
9:20 AM → Check for first scan
9:25 AM → Look for signal generation
9:30 AM → Monitor order placement
         → Confirm rejection (₹0 balance)
         → Verify paper position created

Every 30 mins:
✅ Check open positions
✅ Review current P&L
✅ Check activity log
✅ Verify monitoring active

3:00 PM → Prepare for EOD
3:15 PM → Verify all positions closed
3:30 PM → Review daily performance
```

### Evening (After Market)
```
✅ Stop automated trading
✅ Review performance metrics:
   - Total trades
   - Win rate
   - Total P&L
   - Best/worst trades
✅ Check activity log for errors
✅ Note observations
✅ Plan next day adjustments
```

---

## 📊 Success Criteria

### Day 1
- [ ] At least 1 signal generated
- [ ] At least 1 order placed (and rejected)
- [ ] At least 1 paper position created
- [ ] Position monitoring working
- [ ] No system errors

### Week 1
- [ ] 5+ trades completed
- [ ] Performance metrics calculated
- [ ] Activity log comprehensive
- [ ] System stable and reliable
- [ ] Win rate > 50%

### Week 2
- [ ] 20+ trades completed
- [ ] Win rate > 55%
- [ ] Profit factor > 1.0
- [ ] Settings optimized
- [ ] Ready for real money

---

## 🚨 Common Issues & Solutions

### Issue: Database tables not found
```bash
# Solution: Run SQL schema in Supabase
# Go to: Supabase → SQL Editor
# Paste: database/paper_trading_schema.sql
# Click: Run
```

### Issue: "Scanner already running"
```bash
# Solution: Stop and restart
POST /api/paper-trading/stop
# Wait 10 seconds
POST /api/paper-trading/start
```

### Issue: No signals generated
```bash
# Check:
1. Market hours (9:15 - 3:30)?
2. Fyers token valid?
3. Min confidence too high?

# Solution:
- Wait for market hours
- Refresh Fyers token
- Lower min_confidence to 60%
```

### Issue: Positions not exiting
```bash
# Check:
1. Scanner still running?
2. Targets realistic?
3. Fyers API responding?

# Solution:
- Verify scanner status
- Manual close position
- Check Fyers API quota
```

---

## 🎓 Next Actions

### Immediate (Today)
1. [ ] Run database setup
2. [ ] Verify tables created
3. [ ] Start backend server
4. [ ] Test API endpoints
5. [ ] Access dashboard

### This Week
1. [ ] Run for 1 full day
2. [ ] Monitor closely
3. [ ] Review performance
4. [ ] Adjust settings
5. [ ] Document learnings

### Next Week
1. [ ] Optimize parameters
2. [ ] Increase confidence threshold
3. [ ] Test different intervals
4. [ ] Compare strategies
5. [ ] Prepare for live trading

### Week 3-4
1. [ ] Finalize settings
2. [ ] Fund Fyers account (small amount)
3. [ ] Start with ₹5k/trade
4. [ ] Compare paper vs real
5. [ ] Scale gradually

---

## 📈 Performance Targets

### Week 1
- **Trades:** 5-10
- **Win Rate:** 50%+
- **Profit Factor:** 1.0+
- **Goal:** Stability

### Week 2
- **Trades:** 15-20
- **Win Rate:** 55%+
- **Profit Factor:** 1.2+
- **Goal:** Consistency

### Week 3
- **Trades:** 20-30
- **Win Rate:** 60%+
- **Profit Factor:** 1.5+
- **Goal:** Optimization

### Week 4
- **Trades:** 30+
- **Win Rate:** 60%+
- **Profit Factor:** 1.5+
- **Goal:** Transition to real

---

## 🎉 You're All Set!

**Everything is implemented and ready:**

✅ Database schema (5 tables)  
✅ Backend service (700+ lines)  
✅ API endpoints (11 routes)  
✅ Frontend dashboard (full UI)  
✅ Setup scripts  
✅ Complete documentation  

**Next step:** 
👉 Run the database setup in Supabase  
👉 Then: `./start_paper_trading.sh`

**Good luck! 🚀**

---

*Checklist Created: January 30, 2026*  
*Estimated Setup Time: 15-30 minutes*  
*Estimated Testing Time: 1 day*  
*Path to Live Trading: 2-4 weeks*
