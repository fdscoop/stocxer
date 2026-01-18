# TradeWise Quick Start Guide

## ✅ Setup Complete

Your TradeWise application is now ready to use!

## Running the Server

The server is currently running on `http://localhost:8000`

To restart the server if it stops:

```bash
cd /Users/bineshbalan/TradeWise
python main.py
```

## Accessing the API

### 1. **Interactive API Documentation (Swagger UI)**
   - **URL**: http://localhost:8000/docs
   - Try all endpoints directly from the browser
   - Test requests and see responses in real-time

### 2. **Alternative API Documentation (ReDoc)**
   - **URL**: http://localhost:8000/redoc
   - Read-only but well-organized documentation

### 3. **OpenAPI Schema (JSON)**
   - **URL**: http://localhost:8000/openapi.json
   - Raw OpenAPI specification

## Quick Test Commands

### Test API Health
```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "status": "online",
  "service": "TradeWise API",
  "version": "1.0.0",
  "timestamp": "2026-01-18T00:49:35.187335"
}
```

### Test Options Analysis
```bash
curl -X POST http://localhost:8000/analysis/options \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NSE:NIFTY",
    "strike": 18000,
    "expiry_date": "2024-01-25",
    "option_type": "call",
    "market_price": 150.50
  }'
```

### Run Examples
```bash
python examples/usage_examples.py
```

## Next Steps

### 1. **Configure Fyers API (Optional)**
   Edit `.env` with your Fyers credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

### 2. **Install Optional Dependencies**

   **For TA-Lib (technical analysis):**
   ```bash
   # macOS
   brew install ta-lib
   pip install ta-lib
   
   # Ubuntu/Debian
   sudo apt-get install ta-lib
   pip install ta-lib
   ```

   **For QuantLib (advanced derivatives):**
   ```bash
   pip install quantlib-python
   ```

   **For Prophet (time series forecasting):**
   ```bash
   pip install prophet
   ```

### 3. **Train ML Model**
   ```bash
   curl -X POST http://localhost:8000/ml/train?symbol=NSE:SBIN-EQ&days=365
   ```

### 4. **Generate Trading Signals**
   ```bash
   curl -X POST http://localhost:8000/signals/generate \
     -H "Content-Type: application/json" \
     -d '{
       "symbol": "NSE:NIFTY50-INDEX",
       "lookback_days": 60,
       "include_options": true
     }'
   ```

## Available Endpoints

### Authentication
- `GET /auth/url` - Get Fyers authentication URL
- `POST /auth/token?auth_code=YOUR_CODE` - Set access token

### Market Data
- `GET /market/quote/{symbol}` - Get current quote
- `GET /market/historical/{symbol}?resolution=D&days=365` - Get historical data
- `GET /market/option-chain/{symbol}?strike_count=10` - Get option chain

### Analysis
- `POST /analysis/options` - Analyze option
- `POST /analysis/ict?symbol=NSE:NIFTY&days=60` - ICT analysis
- `POST /signals/generate` - Generate trading signal
- `POST /signals/strategy` - Get strategy recommendation

### Trading (requires Fyers auth)
- `GET /trading/positions` - Current positions
- `GET /trading/orders` - Order book
- `POST /trading/order` - Place order
- `GET /trading/funds` - Available funds

### Machine Learning
- `POST /ml/train?symbol=NSE:SBIN-EQ&days=365` - Train model
- `POST /ml/predict?symbol=NSE:SBIN-EQ&periods=5` - Predict prices

## Project Structure

```
TradeWise/
├── config/
│   └── settings.py           # Configuration
├── src/
│   ├── api/
│   │   └── fyers_client.py   # Fyers API wrapper
│   ├── analytics/
│   │   ├── options_pricing.py # Greeks & pricing
│   │   └── ict_analysis.py    # ICT patterns
│   ├── ml/
│   │   └── price_prediction.py # ML models
│   └── trading/
│       └── signal_generator.py # Signals & risk mgmt
├── models/
│   └── saved_models/          # Trained models
├── data/
│   ├── raw/                   # Raw data
│   └── processed/             # Processed data
├── logs/                      # Application logs
├── main.py                    # FastAPI app
├── requirements.txt           # Dependencies
└── examples/
    └── usage_examples.py      # Example usage
```

## Features Overview

### Options Pricing ✅
- Black-Scholes pricing model
- Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
- Implied volatility calculation
- Intrinsic and time value decomposition

### ICT Analysis ✅
- Market structure identification
- Order blocks detection
- Fair Value Gaps (FVG)
- Liquidity levels
- Signal generation with confidence scores

### Machine Learning ✅
- XGBoost, LightGBM, Random Forest models
- 30+ technical indicators
- Time series forecasting
- Model persistence and reloading

### Signal Generation ✅
- Combines multiple analysis methods
- Weighted scoring system
- Option strategy recommendations
- Risk management tools

### API Backend ✅
- 20+ REST endpoints
- Complete documentation
- Error handling
- JSON responses

## Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill the process if needed
kill -9 <PID>

# Try a different port (edit main.py)
```

### Missing dependencies
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check what's installed
pip list | grep -E "(fastapi|pandas|sklearn|xgboost)"
```

### Import errors
```bash
# Ensure you're in the right directory
cd /Users/bineshbalan/TradeWise

# Check Python path
python -c "import sys; print(sys.path)"
```

## Performance Tips

1. **For large datasets**: Use proper database (PostgreSQL)
2. **For real-time**: Set up WebSocket connections
3. **For backtesting**: Use dedicated backtesting framework
4. **For production**: Deploy with proper error handling and monitoring

## Next Integration Points

1. **Connect to Fyers API** - Add your credentials in `.env`
2. **Set up Database** - PostgreSQL + Redis for caching
3. **Train ML Models** - Use historical data for predictions
4. **Implement Strategy** - Combine signals into trading strategy
5. **Monitor & Log** - Track performance and errors

## Support Resources

- **ReadMe**: See README.md for full documentation
- **Examples**: See examples/usage_examples.py for code samples
- **API Docs**: Open http://localhost:8000/docs in browser

---

**Server Status**: ✅ Running on http://localhost:8000
**Last Updated**: 2026-01-18
