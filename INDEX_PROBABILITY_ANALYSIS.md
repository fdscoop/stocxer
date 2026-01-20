# Index Probability Analysis System

## Overview

This system provides comprehensive probability-based analysis for Indian market indices by scanning **ALL constituent stocks** and aggregating their signals to predict index direction.

## Supported Indices

| Index | Stocks Scanned | Description |
|-------|----------------|-------------|
| **NIFTY50** | 50 stocks | Top 50 companies by market cap on NSE |
| **BANKNIFTY** | 14 stocks | All banking stocks in the Bank Nifty index |
| **SENSEX** | 30 stocks | BSE's benchmark index of 30 stocks |
| **FINNIFTY** | 20 stocks | Nifty Financial Services index stocks |

## How It Works

### 1. Stock-Level Analysis (Each Constituent)

For **every stock** in the index, the system:

- **Fetches Historical Data**: 60 days of daily OHLCV data via Fyers API
- **Calculates Technical Indicators**:
  - RSI (14-period)
  - EMA 5, 10, 20
  - VWAP (Volume Weighted Average Price)
  - MACD (12, 26, 9)
  - Volume analysis vs 10-day average

- **Generates Probability Signal**:
  - RSI Analysis (20% weight): Oversold (<30) = Bullish, Overbought (>70) = Bearish
  - EMA Alignment (25% weight): EMA5 > EMA10 > EMA20 = Bullish
  - Trend Direction (20% weight): Price vs EMAs
  - VWAP Position (15% weight): Above VWAP = Bullish
  - Volume Confirmation (15% weight): High volume amplifies direction
  - MACD (15% weight): MACD > Signal = Bullish

### 2. Probability Calculation

```
Stock Probability = Bullish Score / (Bullish Score + Bearish Score)
```

- Probability > 0.7 → **Strong Buy** (Expected +2.25% move)
- Probability 0.6-0.7 → **Buy** (Expected +1.5% move)
- Probability 0.55-0.6 → **Weak Buy** (Expected +0.75% move)
- Probability 0.45-0.55 → **Neutral** (No significant move expected)
- Probability 0.4-0.45 → **Weak Sell** (Expected -0.75% move)
- Probability 0.3-0.4 → **Sell** (Expected -1.5% move)
- Probability < 0.3 → **Strong Sell** (Expected -2.25% move)

### 3. Market-Cap Weighted Aggregation

The core formula:
```
Index Move = Σ(wᵢ × Pᵢ × Δpᵢ)
```

Where:
- `wᵢ` = Index weight of stock i (normalized to sum = 1.0)
- `Pᵢ` = Probability score (0-1) from analysis
- `Δpᵢ` = Expected % move of stock i

**Example for NIFTY50**:
- RELIANCE (9.31% weight) shows BUY signal with 70% probability, expected +1.5% move
- Contribution = 0.0931 × 0.70 × 1.5 = 0.098%

### 4. Sector-Level Aggregation

Stocks are grouped by sector:
- Banking, IT, Oil & Gas, FMCG, Pharma, Auto, etc.
- Each sector gets a composite signal based on constituent stock signals
- Sector weights are considered (e.g., Banking = 16.89% of NIFTY)

### 5. Market Regime Detection

Uses ADX (Average Directional Index) to classify market:
- **Strong Trend Up**: ADX > 25 with bullish EMAs
- **Weak Trend Up**: ADX 15-25 with bullish EMAs
- **Range Bound**: ADX < 15
- **Weak Trend Down**: ADX 15-25 with bearish EMAs
- **Strong Trend Down**: ADX > 25 with bearish EMAs
- **High Volatility**: ATR > 80th percentile

Regime adjustments:
- Strong trends boost signal confidence by 20%
- Range-bound reduces confidence by 30%

### 6. Correlation Filtering

Stocks with correlation < 0.3 to the index are filtered out, as they don't reliably indicate index direction.

## API Endpoints

### Main Analysis
```
GET /index/probability/{index_name}
```

**Parameters**:
- `index_name`: NIFTY, BANKNIFTY, SENSEX, FINNIFTY
- `include_ml`: Include ML optimization (default: true)
- `include_stocks`: Include all stock signals (default: true)
- `include_sectors`: Include sector breakdown (default: true)

**Response includes**:
- `stocks_scanned`: Number of stocks analyzed
- `prediction.expected_direction`: BULLISH/BEARISH/NEUTRAL
- `prediction.expected_move_pct`: Predicted % move
- `prediction.confidence`: 0-100 confidence score
- `prediction.probability_up/down/neutral`: Probability distribution
- `stock_summary`: Bullish/Bearish/Neutral stock counts
- `top_bullish_contributors`: Top 5 stocks pushing index up
- `top_bearish_contributors`: Top 5 stocks pushing index down
- `sector_analysis`: Breakdown by sector
- `stock_signals`: Individual stock analysis (if include_stocks=true)

### Surge Candidates
```
GET /index/surge-candidates/{index_name}?min_expected_move=2.0
```

Returns stocks with Strong Buy signals expecting >2% move.

### Exhaustion Candidates
```
GET /index/exhaustion-candidates/{index_name}?min_expected_decline=-2.0
```

Returns overbought stocks with Strong Sell signals.

### Constituents
```
GET /index/constituents/{index_name}
```

Lists all constituent stocks with weights.

## Volume Analysis

Volume is crucial for signal confirmation:

1. **Volume Surge Detection**: Current volume > 1.5x 10-day average
2. **Volume Direction**: 
   - High volume on up-day = Bullish confirmation
   - High volume on down-day = Bearish confirmation
3. **Volume-Price Divergence**: 
   - Rising price with falling volume = Weak signal
   - Rising price with rising volume = Strong signal

## What The System Checks

✅ **Does it scan ALL constituent stocks?**
- YES - All 50 stocks for NIFTY50
- YES - All 14 stocks for BANKNIFTY
- YES - All 30 stocks for SENSEX
- YES - All 20 stocks for FINNIFTY

✅ **Does it calculate probability of price movement?**
- YES - Each stock gets a probability score (0-1)
- YES - Index gets aggregated probability

✅ **Does it consider volume?**
- YES - Volume surge detection
- YES - Volume confirms directional moves

✅ **Does it predict index movement?**
- YES - Expected move % calculated
- YES - Direction (BULLISH/BEARISH/NEUTRAL)
- YES - Time-based analysis via regime detection

✅ **Does it identify best buy signals?**
- YES - Surge candidates endpoint
- YES - Top bullish contributors
- YES - Strong Buy signals with confidence scores

## Requirements

- **Fyers API Authentication**: Required for live data
- Without auth, endpoint returns 401 error

## Usage Example

```python
# Analyze NIFTY50
response = requests.get("http://localhost:8000/index/probability/NIFTY")

# Check how many stocks were scanned
print(f"Stocks scanned: {response['stocks_scanned']}")  # Should be 50

# Get prediction
print(f"Direction: {response['prediction']['expected_direction']}")
print(f"Expected Move: {response['prediction']['expected_move_pct']}%")
print(f"Confidence: {response['prediction']['confidence']}%")

# See breakdown
print(f"Bullish stocks: {response['stock_summary']['bullish']}")
print(f"Bearish stocks: {response['stock_summary']['bearish']}")
```
