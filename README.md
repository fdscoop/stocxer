# TradeWise 📈

An intelligent options trading platform for the Indian market that combines ICT (Inner Circle Trader) concepts, machine learning predictions, and quantitative analysis to generate trading signals.

## Features

- **Options Pricing & Greeks**: Calculate Black-Scholes prices, implied volatility, and all Greeks (Delta, Gamma, Theta, Vega, Rho)
- **ICT Analysis**: Market structure, order blocks, fair value gaps, and liquidity levels
- **Machine Learning**: Price prediction using XGBoost, LightGBM, and Random Forest
- **Fyers Integration**: Complete integration with Fyers API for Indian markets
- **Signal Generation**: Comprehensive signals combining multiple analysis methods
- **Risk Management**: Position sizing and stop-loss calculation
- **REST API**: FastAPI backend with comprehensive endpoints

## Tech Stack

- **Backend**: Python 3.10+, FastAPI
- **ML/Analytics**: scikit-learn, XGBoost, LightGBM, TensorFlow
- **Quantitative Finance**: QuantLib, scipy
- **Technical Analysis**: TA-Lib, pandas-ta
- **Broker Integration**: Fyers API v3
- **Database**: PostgreSQL, Redis

## Project Structure

```
TradeWise/
├── config/
│   └── settings.py          # Configuration management
├── src/
│   ├── api/
│   │   └── fyers_client.py  # Fyers API integration
│   ├── analytics/
│   │   ├── options_pricing.py    # Options pricing & Greeks
│   │   └── ict_analysis.py       # ICT analysis module
│   ├── ml/
│   │   └── price_prediction.py   # ML models
│   └── trading/
│       └── signal_generator.py   # Signal generation & risk management
├── models/
│   └── saved_models/        # Trained ML models
├── data/
│   ├── raw/                 # Raw market data
│   └── processed/           # Processed data
├── logs/                    # Application logs
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
└── .env.example            # Environment variables template
```

## Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL (optional, for data storage)
- Redis (optional, for caching)
- TA-Lib (requires system installation)

### 1. Clone the repository

```bash
cd TradeWise
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install TA-Lib (required for technical analysis)

**macOS:**
```bash
brew install ta-lib
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ta-lib
```

**Windows:**
Download pre-built wheels from https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your Fyers API credentials:

```env
FYERS_CLIENT_ID=your_client_id
FYERS_SECRET_KEY=your_secret_key
FYERS_REDIRECT_URI=http://localhost:8000/callback
```

### 6. Create necessary directories

```bash
mkdir -p logs models/saved_models data/raw data/processed
```

## Quick Start

### 1. Start the API server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### 2. View API documentation

Open your browser and navigate to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 3. Authenticate with Fyers

```bash
# Get authentication URL
curl http://localhost:8000/auth/url

# After authentication, set the access token
curl -X POST "http://localhost:8000/auth/token?auth_code=YOUR_AUTH_CODE"
```

## Usage Examples

### Get Market Quote

```python
import requests

response = requests.get("http://localhost:8000/market/quote/NSE:SBIN-EQ")
print(response.json())
```

### Analyze an Option

```python
import requests

payload = {
    "symbol": "NSE:NIFTY",
    "strike": 18000,
    "expiry_date": "2024-01-25",
    "option_type": "call",
    "market_price": 150.50
}

response = requests.post("http://localhost:8000/analysis/options", json=payload)
print(response.json())
```

### Generate Trading Signal

```python
import requests

payload = {
    "symbol": "NSE:NIFTY50-INDEX",
    "lookback_days": 60,
    "include_options": True
}

response = requests.post("http://localhost:8000/signals/generate", json=payload)
signal = response.json()

print(f"Signal: {signal['signal']['signal']}")
print(f"Confidence: {signal['signal']['confidence']}")
```

### Train ML Model

```python
import requests

response = requests.post(
    "http://localhost:8000/ml/train?symbol=NSE:SBIN-EQ&days=365"
)
print(response.json())
```

### Get Option Strategy Recommendation

```python
import requests

response = requests.post(
    "http://localhost:8000/signals/strategy",
    params={
        "symbol": "NSE:NIFTY50-INDEX",
        "capital": 100000,
        "risk_tolerance": "moderate"
    }
)
print(response.json())
```

## Core Modules

### 1. Options Pricing (`src/analytics/options_pricing.py`)

```python
from src.analytics.options_pricing import options_pricer

# Calculate option price and Greeks
metrics = options_pricer.calculate_option_metrics(
    spot_price=18000,
    strike_price=18000,
    market_price=150,
    time_to_expiry=0.1,  # 36.5 days
    option_type="call"
)

print(f"Delta: {metrics['greeks']['delta']}")
print(f"Implied Volatility: {metrics['implied_volatility']}")
```

### 2. ICT Analysis (`src/analytics/ict_analysis.py`)

```python
from src.analytics.ict_analysis import ict_analyzer
import pandas as pd

# Assuming df is your OHLCV DataFrame
signal = ict_analyzer.generate_ict_signal(df, current_price=18000)

print(f"ICT Signal: {signal['signal']}")
print(f"Confidence: {signal['confidence']}")
print(f"Reasons: {signal['reasons']}")
```

### 3. Price Prediction (`src/ml/price_prediction.py`)

```python
from src.ml.price_prediction import price_predictor

# Train model
metrics = price_predictor.train(historical_df)
print(f"Test R2 Score: {metrics['test_r2']}")

# Make predictions
predictions = price_predictor.predict_next(historical_df, periods=5)
print(f"Next 5 day predictions: {predictions}")
```

### 4. Signal Generation (`src/trading/signal_generator.py`)

```python
from src.trading.signal_generator import signal_generator

signal = signal_generator.generate_comprehensive_signal(
    historical_data=df,
    current_price=18000,
    option_data={"put_call_ratio": 1.2}
)

print(f"Final Signal: {signal['signal']}")
print(f"Confidence: {signal['confidence']}")
```

## API Endpoints

### Authentication
- `GET /auth/url` - Get Fyers authentication URL
- `POST /auth/token` - Set access token

### Market Data
- `GET /market/quote/{symbol}` - Get current quote
- `GET /market/historical/{symbol}` - Get historical data
- `GET /market/option-chain/{symbol}` - Get option chain

### Analysis
- `POST /analysis/options` - Analyze specific option
- `POST /analysis/ict` - Perform ICT analysis
- `POST /signals/generate` - Generate comprehensive signal
- `POST /signals/strategy` - Get strategy recommendation

### Trading
- `GET /trading/positions` - Get current positions
- `GET /trading/orders` - Get order book
- `POST /trading/order` - Place new order
- `GET /trading/funds` - Get available funds

### Machine Learning
- `POST /ml/train` - Train ML model
- `POST /ml/predict` - Predict future prices

## Configuration

Key settings in `config/settings.py`:

- **Fyers API credentials**: Set via environment variables
- **Database connections**: PostgreSQL and Redis URLs
- **ML parameters**: Training intervals, minimum samples
- **Trading parameters**: Max position size, risk per trade
- **Logging**: Log level and file path

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
# Format code
black src/

# Lint code
flake8 src/
```

## Key Concepts

### ICT (Inner Circle Trader)

- **Order Blocks**: Last bearish/bullish candle before strong move
- **Fair Value Gaps**: Price imbalances that tend to fill
- **Liquidity Levels**: Areas where stops accumulate
- **Market Structure**: Higher highs/lows for trend identification

### Options Greeks

- **Delta**: Rate of change of option price with underlying
- **Gamma**: Rate of change of delta
- **Theta**: Time decay
- **Vega**: Sensitivity to volatility changes
- **Rho**: Sensitivity to interest rate changes

### Signal Generation

Signals are generated by combining:
1. **ICT Analysis** (40% weight): Market structure and patterns
2. **ML Predictions** (30% weight): Price forecasts
3. **Options Analysis** (30% weight): Put/Call ratio, IV, Greeks

## Roadmap

- [ ] Add WebSocket support for real-time data
- [ ] Implement backtesting framework
- [ ] Add more ML models (LSTM, Transformer)
- [ ] Portfolio management module
- [ ] Mobile app integration
- [ ] Advanced option strategies (Iron Condor, Butterfly, etc.)
- [ ] Multi-timeframe analysis
- [ ] Sentiment analysis from news/social media

## Risk Disclaimer

⚠️ **Important**: This software is for educational and research purposes only. Trading in options and derivatives involves substantial risk and is not suitable for all investors. Past performance is not indicative of future results. Always do your own research and consult with a qualified financial advisor before making any investment decisions.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Email: support@tradewise.example.com

## Acknowledgments

- Fyers for providing API access to Indian markets
- QuantLib community for quantitative finance tools
- The ICT trading community for market structure concepts

---

**Made with ❤️ for Indian Options Traders**
