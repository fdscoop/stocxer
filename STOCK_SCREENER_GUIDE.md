# 📊 Stock Screener - User Guide

## Overview

The Stock Screener is a powerful feature that automatically scans penny stocks and medium stocks across NSE to identify high-confidence BUY/SELL signals using technical analysis.

## Features

### 1. **Multi-Category Scanning**
- **Penny Stocks** (₹1-50): High volatility, quick moves
- **Medium Stocks** (₹200-1000): Balanced risk-reward
- **All Stocks**: Combined scan of both categories

### 2. **Technical Analysis**
Each stock is analyzed using:
- **Moving Averages** (SMA 5, 10, 20)
- **RSI** (14-period Relative Strength Index)
- **Volume Analysis** (Surge detection)
- **Price Momentum** (5-day change %)

### 3. **Signal Generation**
Signals are generated only when:
- Confidence level ≥ 60% (configurable)
- Multiple indicators align (bullish or bearish)
- Clear entry, targets, and stop loss defined

## How It Works

### Signal Logic

**BULLISH SIGNALS (BUY)** are triggered when:
- ✅ Golden cross: SMA 5 > SMA 10 > SMA 20 (+30 points)
- ✅ Price above 20 SMA (+15 points)
- ✅ RSI oversold recovery (30-50) (+25 points)
- ✅ RSI healthy (50-70) (+15 points)
- 🔥 High volume on uptrend (+20 points)
- 🚀 Strong positive momentum >3% (+15 points)

**BEARISH SIGNALS (SELL)** are triggered when:
- ❌ Death cross: SMA 5 < SMA 10 < SMA 20 (+30 points)
- 📉 Price below 20 SMA (+15 points)
- ⚠️ RSI overbought >70 (+25 points)
- ⚠️ High volume on decline (+20 points)
- 📉 Weak momentum <-3% (+15 points)

**Minimum score required**: 50 points for signal generation

### Confidence Levels

- **60-70%**: MODERATE - Consider with caution
- **70-80%**: HIGH - Good setup
- **80-95%**: VERY HIGH - Strong signal

## Using the Dashboard

### Access
Navigate to: http://localhost:8000/static/screener.html

Or click the **"📊 Stock Screener"** button in the main dashboard header.

### Scanning Stocks

1. **Select Category**:
   - All Stocks (recommended for first scan)
   - Penny Stocks only
   - Medium Stocks only

2. **Set Minimum Confidence**:
   - 60% - More signals, lower quality
   - 70% - Balanced (recommended)
   - 80% - Fewer signals, higher quality

3. **Choose Action Filter**:
   - BUY Only (recommended for long positions)
   - SELL Only (for short positions)
   - All Signals

4. **Click "🔍 Scan Stocks"**

### Reading Results

Each stock card displays:

**Header**:
- Stock name and symbol
- Category (penny/medium)
- Action badge (BUY/SELL)

**Price & Confidence**:
- Current price
- Day change %
- Confidence level with color coding

**Targets & Stop Loss**:
- Target 1: 5% profit
- Target 2: 10% profit
- Stop Loss: 3% loss

**Technical Indicators**:
- RSI value
- 5-day momentum
- SMA 5 value
- Volume status (Normal/SURGE)

**Signal Reasons**:
- Top 3 reasons for the signal
- Quick explanation of setup

## API Endpoints

### 1. Scan Stocks
```bash
GET /screener/scan?category=all&min_confidence=70
```

**Parameters**:
- `category`: "penny", "medium", or "all"
- `min_confidence`: Minimum confidence level (0-100)

**Response**:
```json
{
  "status": "success",
  "total_signals": 15,
  "buy_signals": 10,
  "sell_signals": 5,
  "signals": {
    "buy": [...],
    "sell": [...]
  },
  "top_picks": [...]
}
```

### 2. Analyze Single Stock
```bash
GET /screener/stock/TATAMOTORS
```

**Response**:
```json
{
  "status": "success",
  "signal": {
    "symbol": "NSE:TATAMOTORS-EQ",
    "name": "TATAMOTORS",
    "current_price": 785.50,
    "action": "BUY",
    "confidence": 75.0,
    "category": "medium",
    "targets": {
      "target_1": 824.78,
      "target_2": 864.05,
      "stop_loss": 761.94
    },
    "indicators": {
      "rsi": 45.2,
      "sma_5": 780.25,
      "sma_20": 770.50,
      "momentum_5d": 2.5,
      "volume_surge": true
    },
    "reasons": [
      "✅ Golden cross - all MAs aligned",
      "✅ RSI oversold recovery: 45.2",
      "🔥 High volume on uptrend"
    ]
  }
}
```

### 3. Get Categories
```bash
GET /screener/categories
```

Returns available categories and confidence level descriptions.

## Stock List

### Penny Stocks (₹1-50)
- YESBANK, SUZLON, RPOWER
- VAKRANGEE, IDFC, SAIL
- PCJEWELLER, JETAIRWAYS, RCOM

### Medium Stocks (₹200-1000)
- **Automotive**: TATAMOTORS, ASHOKLEY, M&M
- **Steel**: TATASTEEL, JSWSTEEL, SAIL
- **Energy**: BPCL, IOC, ONGC, COALINDIA
- **Utilities**: NTPC, POWERGRID, GAIL
- **Banking**: SBIN, HDFCBANK, ICICIBANK, AXISBANK, INDUSINDBK
- **Public Banks**: BANKBARODA, PNB, CANBK
- **Metals**: VEDL, COALINDIA
- **Pharma**: SUNPHARMA, DRREDDY, CIPLA, LUPIN, DIVISLAB, BIOCON
- **Telecom**: IDEA, BHARTIARTL
- **Diversified**: RELIANCE, TCS, INFY, LT, ITC

## Trading Guidelines

### Entry Rules
1. Wait for confirmation:
   - Check volume: High volume = stronger signal
   - RSI not in extreme zones
   - Price near support/resistance

2. Position sizing:
   - 60-70% confidence: 25% of capital
   - 70-80% confidence: 50% of capital
   - 80-95% confidence: 75% of capital

3. Risk management:
   - Always set stop loss immediately
   - Risk only 1-2% of capital per trade
   - Don't trade penny stocks with >5% risk

### Exit Strategy

**For BUY signals**:
- Exit 50% at Target 1 (5% profit)
- Move stop loss to breakeven
- Exit remaining at Target 2 (10% profit)
- Cut loss at Stop Loss (3% loss)

**For SELL signals**:
- Same strategy in reverse
- Book profits quickly on penny stocks
- Hold medium stocks longer for Target 2

### Risk Warnings

**Penny Stocks (₹1-50)**:
- ⚠️ **HIGH RISK**: Extreme volatility
- ⚠️ Can move 10-20% in minutes
- ⚠️ Lower liquidity
- ⚠️ Higher spread costs
- ✅ Best for: Day trading, quick scalps
- ✅ Max position: 2-3% of capital

**Medium Stocks (₹200-1000)**:
- ⚠️ **MODERATE RISK**: Normal volatility
- ⚠️ Can move 3-5% in a session
- ✅ Better liquidity
- ✅ Lower spread costs
- ✅ Best for: Swing trading, position holding
- ✅ Max position: 5-10% of capital

## Performance Tips

### 1. Scan Timing
- **Morning (9:30-10:00 AM)**: Best for day trading setups
- **Post-lunch (2:00-2:30 PM)**: Good for swing trades
- **Avoid**: First 15 minutes (volatile)

### 2. Filter Optimization
- Start with 70% confidence
- Reduce to 60% if too few signals
- Increase to 80% for higher accuracy

### 3. Validation
- Cross-check with chart: Open TradingView
- Verify news: Check for corporate actions
- Check volumes: Compare with 30-day average

### 4. Auto-Refresh
- Dashboard auto-refreshes every 5 minutes
- Manual refresh: Click "🔄 Refresh" button
- API rate limits: Max 60 requests/minute

## Limitations

1. **Data Source**: Uses Fyers API (requires active session)
2. **Scan Speed**: Takes 30-60 seconds for full scan
3. **Historical Data**: Limited to last 30 days
4. **Market Hours**: Only works during trading hours
5. **Signal Lag**: Signals based on previous candle close

## Troubleshooting

### No Signals Found
- **Cause**: Market conditions not favorable
- **Solution**: Lower confidence threshold or try different category

### Scan Taking Too Long
- **Cause**: Network latency or API rate limits
- **Solution**: Scan smaller categories (penny or medium only)

### Stock Not Found
- **Cause**: Symbol format incorrect or not in list
- **Solution**: Use format "TATAMOTORS" or "NSE:TATAMOTORS-EQ"

### API Error
- **Cause**: Server not running or Fyers session expired
- **Solution**: Restart server or re-authenticate Fyers

## Example Workflow

### Morning Routine (9:30 AM)

1. Open Stock Screener
2. Set filters:
   - Category: "All Stocks"
   - Min Confidence: 70%
   - Action: "BUY Only"
3. Click "Scan Stocks"
4. Review top 5 picks
5. For each pick:
   - Open chart on TradingView
   - Verify signal visually
   - Check news/events
   - If validated, enter trade
6. Set alerts for Target 1, Target 2, Stop Loss

### Position Management

1. Monitor dashboard every 30 minutes
2. Check if signal still valid
3. Adjust stop loss if in profit
4. Exit at targets or before 3:15 PM (intraday)
5. Log trade: Entry, exit, profit/loss

## Support

For issues or questions:
1. Check server logs: `/tmp/tradewise.log`
2. Verify API: `curl http://localhost:8000/screener/categories`
3. Test single stock: `curl http://localhost:8000/screener/stock/SBIN`

## Updates

**Version 1.0** (Current):
- Penny & Medium stock scanning
- Technical indicators (MA, RSI, Volume)
- BUY/SELL signal generation
- Dashboard with filtering
- Auto-refresh capability

**Planned Features**:
- Advanced filters (sector, market cap)
- Backtesting capability
- Alert notifications
- Custom watchlist
- Signal history tracking
