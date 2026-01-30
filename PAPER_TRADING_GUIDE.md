# 🤖 Automated Paper Trading System - Complete Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [How It Works](#how-it-works)
6. [Testing Strategy](#testing-strategy)
7. [API Reference](#api-reference)
8. [Frontend Usage](#frontend-usage)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## 🎯 Overview

The Automated Paper Trading System allows you to:

- ✅ **Test order execution logic** with ₹0 Fyers balance
- 📊 **Track paper positions** even when orders are rejected
- 🤖 **Automate signal generation** every N minutes
- 🎯 **Monitor targets/stop-loss** automatically
- 📈 **Analyze performance** with detailed metrics
- 📝 **Log all activities** for audit trail

### Key Features

| Feature | Description |
|---------|-------------|
| **Automated Scanning** | Scans NIFTY/BANKNIFTY/FINNIFTY every 5 minutes |
| **Order Testing** | Places real orders (rejected due to ₹0 balance) |
| **Position Tracking** | Tracks positions as if orders succeeded |
| **Target Monitoring** | Checks targets/SL every minute |
| **Auto Exit** | Closes positions at 3:15 PM |
| **Performance Analytics** | Daily P&L, win rate, profit factor |
| **Activity Logging** | Complete audit trail |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   AUTOMATED PAPER TRADING                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  9:15 AM ──► Start Monitoring                           │
│     │                                                     │
│     ├──► Every 5 mins: Scan NIFTY                       │
│     │        └──► Generate Signal                        │
│     │              └──► If BUY → Place Order             │
│     │                    (Rejected - ₹0 balance)         │
│     │                    └──► Create Paper Position      │
│     │                                                     │
│     ├──► Every 1 min: Check Open Positions              │
│     │        └──► Get Current LTP                        │
│     │              ├──► If >= Target → Exit              │
│     │              ├──► If <= Stop Loss → Exit           │
│     │              └──► Update Current P&L               │
│     │                                                     │
│  3:15 PM ──► Close All Positions (EOD Exit)              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Database Schema

**5 Tables:**

1. `paper_trading_config` - User settings
2. `paper_trading_signals` - Generated signals
3. `paper_trading_positions` - Open/closed positions
4. `paper_trading_activity_log` - Complete audit trail
5. `paper_trading_performance` - Daily metrics

---

## 🚀 Installation & Setup

### Step 1: Database Setup

1. **Go to Supabase SQL Editor**
   ```
   Dashboard → SQL Editor → New Query
   ```

2. **Copy & paste** `database/paper_trading_schema.sql`

3. **Run** the SQL to create tables

4. **Verify setup:**
   ```bash
   python setup_paper_trading.py
   ```

### Step 2: Backend Setup

**No additional setup needed!** The service is automatically imported in `main.py`.

Verify endpoints are loaded:
```bash
# Start server
python main.py

# Check health
curl http://localhost:8000/health
```

### Step 3: Frontend Setup

**Add route in Next.js:**

```typescript
// frontend/app/paper-trading/page.tsx

import PaperTradingDashboard from '@/components/trading/PaperTradingDashboard';

export default function PaperTradingPage() {
  return <PaperTradingDashboard />;
}
```

**Update navigation:**
```typescript
// Add to your navigation menu
{
  name: 'Paper Trading',
  href: '/paper-trading',
  icon: ActivityIcon
}
```

---

## ⚙️ Configuration

### Default Settings

```json
{
  "enabled": false,
  "indices": ["NIFTY"],
  "scan_interval_minutes": 5,
  "max_positions": 3,
  "capital_per_trade": 10000,
  "min_confidence": 65,
  "trading_mode": "intraday"
}
```

### Configuration Options

| Setting | Description | Range | Default |
|---------|-------------|-------|---------|
| `enabled` | Enable/disable paper trading | boolean | `false` |
| `indices` | Indices to trade | array | `["NIFTY"]` |
| `scan_interval_minutes` | Minutes between scans | 1-60 | `5` |
| `max_positions` | Maximum simultaneous positions | 1-10 | `3` |
| `capital_per_trade` | Capital per position (₹) | 5000+ | `10000` |
| `min_confidence` | Minimum signal confidence (%) | 50-100 | `65` |
| `trading_mode` | Trading style | intraday/swing | `intraday` |

---

## 🔄 How It Works

### 1. Signal Generation

**Every 5 minutes** (configurable):

```python
# System calls your existing endpoint
signal = GET /signals/NIFTY/actionable

# If signal is actionable (BUY CALL / BUY PUT)
if signal.action in ["BUY CALL", "BUY PUT"]:
    if signal.confidence >= min_confidence:
        # Save signal to database
        # Execute order
```

### 2. Order Execution

```python
# Calculate quantity
lots = capital_per_trade / (entry_price * lot_size)
quantity = lots * lot_size

# Place order with Fyers
order = fyers.place_order(
    symbol=option_symbol,
    qty=quantity,
    type="MARKET",
    side="BUY"
)

# Expected result: REJECTED (₹0 balance)
# But we still create paper position!
```

### 3. Position Monitoring

**Every 1 minute:**

```python
# Get current LTP from Fyers
current_price = fyers.get_quote(option_symbol)

# Check exit conditions
if current_price >= target_2:
    exit_position(reason="TARGET_2", price=target_2)
elif current_price >= target_1:
    exit_position(reason="TARGET_1", price=target_1)
elif current_price <= stop_loss:
    exit_position(reason="STOP_LOSS", price=stop_loss)

# Update unrealized P&L
current_pnl = (current_price - entry_price) * quantity
```

### 4. Position Exit

```python
# Calculate P&L
pnl = (exit_price - entry_price) * quantity
pnl_pct = (pnl / (entry_price * quantity)) * 100

# Update position
position.status = "CLOSED"
position.exit_price = exit_price
position.exit_reason = reason
position.pnl = pnl

# Update daily performance
update_performance_metrics()
```

---

## 🧪 Testing Strategy

### Phase 1: Order Rejection (₹0 Balance)

**Objective:** Verify order placement logic works

**Steps:**
1. Keep Fyers balance at ₹0
2. Enable paper trading
3. Wait for signal generation
4. System places order → **REJECTED** ❌
5. Paper position created → **SUCCESS** ✅

**Expected Results:**
- Order rejection logged
- Position created with status "OPEN"
- Entry price recorded
- Activity logged

### Phase 2: Target/Stop-Loss Monitoring

**Objective:** Verify exit logic works

**Steps:**
1. Create paper positions
2. Monitor LTP every minute
3. When target/SL hit → exit
4. Verify P&L calculation

**Expected Results:**
- Position exits at correct price
- P&L calculated accurately
- Daily performance updated
- Exit reason logged

### Phase 3: Full Automation

**Objective:** Verify end-to-end automation

**Steps:**
1. Configure settings
2. Start automated trading
3. Let it run for 1 full day
4. Review performance

**Expected Results:**
- Scans run on schedule
- Signals generated automatically
- Positions managed automatically
- Performance tracked accurately

---

## 📡 API Reference

### Authentication

All endpoints require Bearer token:
```
Authorization: Bearer <your-token>
```

### Endpoints

#### Get Configuration
```http
GET /api/paper-trading/config
```

**Response:**
```json
{
  "enabled": true,
  "indices": ["NIFTY", "BANKNIFTY"],
  "scan_interval_minutes": 5,
  "max_positions": 3,
  "capital_per_trade": 10000,
  "min_confidence": 65
}
```

#### Save Configuration
```http
POST /api/paper-trading/config
Content-Type: application/json

{
  "enabled": true,
  "indices": ["NIFTY"],
  "scan_interval_minutes": 5,
  "max_positions": 3,
  "capital_per_trade": 10000,
  "min_confidence": 65
}
```

#### Start Trading
```http
POST /api/paper-trading/start
```

**Response:**
```json
{
  "status": "success",
  "message": "Automated trading started"
}
```

#### Stop Trading
```http
POST /api/paper-trading/stop
```

#### Get Positions
```http
GET /api/paper-trading/positions?status=OPEN
```

**Query Params:**
- `status`: `OPEN` | `CLOSED` | `ALL`

**Response:**
```json
{
  "status": "success",
  "positions": [
    {
      "id": "uuid",
      "index": "NIFTY",
      "option_symbol": "NSE:NIFTY24JAN24500CE",
      "strike": 24500,
      "option_type": "CE",
      "quantity": 50,
      "entry_price": 150.50,
      "current_ltp": 175.25,
      "current_pnl": 1237.50,
      "status": "OPEN",
      "target_1": 180,
      "target_2": 200,
      "stop_loss": 140
    }
  ]
}
```

#### Get Performance
```http
GET /api/paper-trading/performance?days=7
```

**Response:**
```json
{
  "status": "success",
  "performance": [
    {
      "date": "2026-01-30",
      "total_trades": 5,
      "winning_trades": 3,
      "losing_trades": 2,
      "win_rate": 60.0,
      "total_pnl": 2500.00,
      "avg_win": 1500.00,
      "avg_loss": -750.00,
      "profit_factor": 2.0
    }
  ]
}
```

#### Get Status
```http
GET /api/paper-trading/status
```

**Response:**
```json
{
  "status": "success",
  "config": { ... },
  "is_running": true,
  "open_positions": 2,
  "market_open": true,
  "today_performance": { ... }
}
```

#### Close Position
```http
POST /api/paper-trading/positions/{position_id}/close
```

---

## 🖥️ Frontend Usage

### Dashboard Components

**Performance Cards:**
- Total Trades
- Win Rate
- Total P&L
- Open Positions

**Tabs:**
1. **Positions** - View all positions
2. **Configuration** - Adjust settings
3. **Performance** - Daily metrics
4. **Activity** - Audit trail

### Configuration Panel

1. **Select Indices:** NIFTY, BANKNIFTY, FINNIFTY
2. **Scan Interval:** 1-60 minutes
3. **Max Positions:** 1-10
4. **Capital Per Trade:** ₹5000+
5. **Min Confidence:** 50-100%
6. **Trading Mode:** Intraday / Swing

### Starting Trading

1. Configure settings
2. Save configuration
3. Click "Start Trading"
4. Monitor positions in real-time

---

## 🔧 Troubleshooting

### Scanner Not Starting

**Issue:** "Scanner already running" or "Paper trading not enabled"

**Solution:**
```python
# Check status
GET /api/paper-trading/status

# If stuck, restart server
# Then re-enable in config
```

### Orders Not Being Placed

**Issue:** No positions created

**Solution:**
1. Check market hours (9:15 AM - 3:30 PM)
2. Verify Fyers token is valid
3. Check signal confidence >= min_confidence
4. Review activity log for errors

### Positions Not Exiting

**Issue:** Positions remain open past target

**Solution:**
1. Verify scanner is running
2. Check Fyers API quota
3. Review current LTP vs targets
4. Check activity log for monitoring errors

### Performance Not Updating

**Issue:** Daily performance shows 0

**Solution:**
1. Ensure positions are closed (not just open)
2. Check date filtering
3. Verify P&L calculation
4. Run manual performance update

---

## 📊 Best Practices

### Testing Phase (₹0 Balance)

1. ✅ **Start small:** 1 index, low frequency
2. ✅ **Monitor closely:** Check every hour
3. ✅ **Review logs:** Verify order rejections
4. ✅ **Test exits:** Manually close positions
5. ✅ **Analyze performance:** Review daily metrics

### Production Phase (Real Money)

1. 🚀 **Add balance:** Fund Fyers account
2. 🎯 **Gradual increase:** Start with ₹10k per trade
3. 📊 **Monitor closely:** First week daily review
4. 🔧 **Adjust settings:** Based on performance
5. 📈 **Scale up:** Increase capital gradually

### Risk Management

| Risk | Mitigation |
|------|------------|
| Over-trading | Set `max_positions` conservatively |
| Low confidence | Set `min_confidence` >= 70% |
| Large losses | Use strict stop-loss |
| API failures | Monitor activity log |
| Market gaps | Avoid expiry day |

---

## 📈 Performance Metrics

### Key Metrics Tracked

1. **Win Rate:** % of profitable trades
2. **Profit Factor:** Gross profit / Gross loss
3. **Avg Win:** Average profit per winning trade
4. **Avg Loss:** Average loss per losing trade
5. **Max Drawdown:** Largest cumulative loss
6. **Avg Trade Duration:** Minutes in position

### Sample Performance Report

```
Daily Performance Summary
─────────────────────────────────────
Date: 2026-01-30
Total Trades: 5
Winning Trades: 3 (60%)
Total P&L: ₹2,500.00
Avg Win: ₹1,500.00
Avg Loss: -₹750.00
Profit Factor: 2.0
Avg Duration: 45 minutes
─────────────────────────────────────
```

---

## 🎯 Next Steps

### Week 1: Testing
- [ ] Run paper trading with ₹0 balance
- [ ] Verify order rejections
- [ ] Monitor position tracking
- [ ] Review daily performance

### Week 2: Analysis
- [ ] Analyze win rate
- [ ] Review exit reasons
- [ ] Optimize confidence threshold
- [ ] Adjust position sizing

### Week 3: Transition
- [ ] Fund Fyers account
- [ ] Start with small capital
- [ ] Monitor live trades
- [ ] Compare paper vs real results

### Week 4: Scale
- [ ] Increase capital
- [ ] Add more indices
- [ ] Optimize scan frequency
- [ ] Refine strategy

---

## 📞 Support

**Questions?**
- Check Activity Log for errors
- Review API responses
- Verify Fyers token status
- Check Supabase RLS policies

**Issues?**
1. Stop automated trading
2. Review recent activity
3. Check configuration
4. Restart service

---

## 🎉 Success Checklist

✅ Database tables created  
✅ Backend service running  
✅ API endpoints working  
✅ Frontend dashboard accessible  
✅ Configuration saved  
✅ Scanner started  
✅ Signal generated  
✅ Order placed (rejected)  
✅ Position created  
✅ Target/SL monitored  
✅ Position exited  
✅ Performance calculated  

**You're ready for automated paper trading! 🚀**

---

*Last Updated: January 30, 2026*
