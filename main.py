"""
FastAPI Backend for TradeWise
REST API endpoints for trading signals, analysis, and order management
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta, date
import pandas as pd
import logging
import os

from config.settings import settings
from src.api.fyers_client import fyers_client
from src.analytics.options_pricing import options_pricer
from src.analytics.ict_analysis import ict_analyzer
from src.analytics.stock_screener import get_stock_screener
from src.ml.price_prediction import price_predictor
from src.ml.time_series_models import ensemble_predictor, get_ml_signal
from src.trading.signal_generator import signal_generator, risk_manager
from src.services.auth_service import auth_service
from src.services.screener_service import screener_service
from src.models.auth_models import UserRegister, UserLogin, FyersTokenStore

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TradeWise API",
    description="Options trading analysis and signal generation API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Pydantic models for request/response
class OptionAnalysisRequest(BaseModel):
    symbol: str
    strike: float
    expiry_date: str  # Format: YYYY-MM-DD
    option_type: str  # "call" or "put"
    market_price: float


class SignalRequest(BaseModel):
    symbol: str
    lookback_days: int = 60
    include_options: bool = False


class OrderRequest(BaseModel):
    symbol: str
    quantity: int
    side: str  # "buy" or "sell"
    order_type: str = "market"  # "market" or "limit"
    price: Optional[float] = None


# Dashboard route (protected - requires authentication)
@app.get("/")
async def dashboard():
    """Serve the dashboard"""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/login.html")
async def login_page():
    """Serve the login page"""
    return FileResponse(os.path.join(static_dir, "login.html"))


@app.get("/screener.html")
async def screener_page():
    """Serve the screener page"""
    return FileResponse(os.path.join(static_dir, "screener.html"))


# Health check
@app.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "online",
        "service": "TradeWise API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# Authentication endpoints
@app.get("/auth/url")
async def get_auth_url():
    """Get Fyers authentication URL"""
    try:
        auth_url = fyers_client.generate_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/token")
async def set_auth_token(auth_code: str):
    """Set access token using auth code"""
    try:
        success = fyers_client.set_access_token(auth_code)
        if success:
            profile = fyers_client.get_profile()
            return {"status": "success", "profile": profile}
        else:
            raise HTTPException(status_code=400, detail="Failed to set token")
    except Exception as e:
        logger.error(f"Error setting token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# User Authentication Endpoints
# ============================================

@app.post("/api/auth/register")
async def register(user_data: UserRegister):
    """Register a new user"""
    return await auth_service.register_user(user_data)


@app.post("/api/auth/login")
async def login(login_data: UserLogin):
    """Login user"""
    return await auth_service.login_user(login_data)


@app.post("/api/auth/logout")
async def logout(authorization: str = Query(..., description="Bearer token")):
    """Logout user"""
    token = authorization.replace("Bearer ", "")
    return await auth_service.logout_user(token)


@app.get("/api/auth/me")
async def get_current_user(authorization: str = Query(..., description="Bearer token")):
    """Get current user profile"""
    token = authorization.replace("Bearer ", "")
    return await auth_service.get_current_user(token)


# ============================================
# Fyers Token Management Endpoints
# ============================================

@app.post("/api/fyers/token")
async def store_fyers_token(
    token_data: FyersTokenStore,
    authorization: str = Query(..., description="Bearer token")
):
    """Store Fyers authentication token for user"""
    token = authorization.replace("Bearer ", "")
    user = await auth_service.get_current_user(token)
    return await auth_service.store_fyers_token(user.id, token_data)


@app.get("/api/fyers/token")
async def get_fyers_token(authorization: str = Query(..., description="Bearer token")):
    """Get stored Fyers token"""
    token = authorization.replace("Bearer ", "")
    user = await auth_service.get_current_user(token)
    return await auth_service.get_fyers_token(user.id)


@app.delete("/api/fyers/token")
async def delete_fyers_token(authorization: str = Query(..., description="Bearer token")):
    """Delete stored Fyers token"""
    token = authorization.replace("Bearer ", "")
    user = await auth_service.get_current_user(token)
    return await auth_service.delete_fyers_token(user.id)


# Market data endpoints
@app.get("/market/quote/{symbol}")
async def get_quote(symbol: str):
    """Get current quote for symbol"""
    try:
        quote = fyers_client.get_quotes([symbol])
        return quote
    except Exception as e:
        logger.error(f"Error getting quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    resolution: str = Query("D", description="Candle resolution"),
    days: int = Query(365, description="Number of days of history")
):
    """Get historical data"""
    try:
        date_to = datetime.now()
        date_from = date_to - timedelta(days=days)
        
        df = fyers_client.get_historical_data(
            symbol=symbol,
            resolution=resolution,
            date_from=date_from,
            date_to=date_to
        )
        
        # Convert to JSON-serializable format
        data = df.reset_index().to_dict(orient='records')
        
        return {
            "symbol": symbol,
            "resolution": resolution,
            "records": len(data),
            "data": data
        }
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/option-chain/{symbol}")
async def get_option_chain(
    symbol: str,
    strike_count: int = Query(10, description="Number of strikes")
):
    """Get option chain"""
    try:
        chain = fyers_client.get_option_chain(
            symbol=symbol,
            strike_count=strike_count
        )
        return chain
    except Exception as e:
        logger.error(f"Error getting option chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analysis endpoints
@app.post("/analysis/options")
async def analyze_option(request: OptionAnalysisRequest):
    """Analyze a specific option contract"""
    try:
        # Parse expiry date
        expiry = datetime.strptime(request.expiry_date, "%Y-%m-%d").date()
        
        # Get current underlying price
        quote = fyers_client.get_quotes([request.symbol])
        spot_price = quote['d'][0]['v']['lp'] if quote['s'] == 'ok' else 0
        
        # Calculate time to expiry
        time_to_expiry = options_pricer.time_to_expiry_years(expiry)
        
        # Calculate comprehensive metrics
        metrics = options_pricer.calculate_option_metrics(
            spot_price=spot_price,
            strike_price=request.strike,
            market_price=request.market_price,
            time_to_expiry=time_to_expiry,
            option_type=request.option_type
        )
        
        return {
            "symbol": request.symbol,
            "spot_price": spot_price,
            "strike": request.strike,
            "expiry": request.expiry_date,
            "option_type": request.option_type,
            "analysis": metrics
        }
    except Exception as e:
        logger.error(f"Error analyzing option: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analysis/ict")
async def analyze_ict(symbol: str, days: int = 60):
    """Perform ICT analysis on symbol"""
    try:
        # Get historical data
        df = fyers_client.get_historical_data(
            symbol=symbol,
            resolution="D",
            date_from=datetime.now() - timedelta(days=days)
        )
        
        # Get current price
        quote = fyers_client.get_quotes([symbol])
        current_price = quote['d'][0]['v']['lp'] if quote['s'] == 'ok' else 0
        
        # Perform ICT analysis
        signal = ict_analyzer.generate_ict_signal(df, current_price)
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "analysis": signal
        }
    except Exception as e:
        logger.error(f"Error in ICT analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/signals/generate")
async def generate_signal(request: SignalRequest):
    """Generate comprehensive trading signal"""
    try:
        # Get historical data
        df = fyers_client.get_historical_data(
            symbol=request.symbol,
            resolution="D",
            date_from=datetime.now() - timedelta(days=request.lookback_days)
        )
        
        # Get current price
        quote = fyers_client.get_quotes([request.symbol])
        current_price = quote['d'][0]['v']['lp'] if quote['s'] == 'ok' else 0
        
        # Get option data if requested
        option_data = None
        if request.include_options:
            option_chain = fyers_client.get_option_chain(request.symbol)
            # Process option chain to extract useful metrics
            # (put/call ratio, IV, etc.)
            option_data = {"raw_chain": option_chain}
        
        # Generate comprehensive signal
        signal = signal_generator.generate_comprehensive_signal(
            historical_data=df,
            current_price=current_price,
            option_data=option_data
        )
        
        return {
            "symbol": request.symbol,
            "current_price": current_price,
            "signal": signal
        }
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/signals/strategy")
async def recommend_strategy(
    symbol: str,
    capital: float = 100000,
    risk_tolerance: str = "moderate"
):
    """Get option strategy recommendation"""
    try:
        # Generate signal first
        df = fyers_client.get_historical_data(
            symbol=symbol,
            resolution="D",
            date_from=datetime.now() - timedelta(days=60)
        )
        
        quote = fyers_client.get_quotes([symbol])
        current_price = quote['d'][0]['v']['lp'] if quote['s'] == 'ok' else 0
        
        signal = signal_generator.generate_comprehensive_signal(
            historical_data=df,
            current_price=current_price
        )
        
        # Get option chain
        option_chain_raw = fyers_client.get_option_chain(symbol)
        
        # Recommend strategy
        recommendation = signal_generator.recommend_option_strategy(
            signal=signal,
            spot_price=current_price,
            option_chain=[],  # Would need to process option_chain_raw
            capital=capital,
            risk_tolerance=risk_tolerance
        )
        
        return recommendation
    except Exception as e:
        logger.error(f"Error recommending strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Trading endpoints
@app.get("/trading/positions")
async def get_positions():
    """Get current positions"""
    try:
        positions = fyers_client.get_positions()
        return positions
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trading/orders")
async def get_orders():
    """Get order book"""
    try:
        orders = fyers_client.get_orders()
        return orders
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trading/order")
async def place_order(request: OrderRequest):
    """Place a new order"""
    try:
        side = 1 if request.side.lower() == "buy" else -1
        order_type = 2 if request.order_type.lower() == "market" else 1
        
        response = fyers_client.place_order(
            symbol=request.symbol,
            qty=request.quantity,
            side=side,
            order_type=order_type,
            limit_price=request.price or 0
        )
        
        return response
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trading/funds")
async def get_funds():
    """Get available funds"""
    try:
        funds = fyers_client.get_funds()
        return funds
    except Exception as e:
        logger.error(f"Error getting funds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ML endpoints
@app.post("/ml/train")
async def train_model(symbol: str, days: int = 365):
    """Train ML model on historical data"""
    try:
        # Get historical data
        df = fyers_client.get_historical_data(
            symbol=symbol,
            resolution="D",
            date_from=datetime.now() - timedelta(days=days)
        )
        
        # Train model
        metrics = price_predictor.train(df)
        
        # Save model
        model_path = f"models/saved_models/{symbol.replace(':', '_')}_model.pkl"
        price_predictor.save_model(model_path)
        
        return {
            "status": "success",
            "symbol": symbol,
            "training_metrics": metrics,
            "model_path": model_path
        }
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ml/predict")
async def predict_price(symbol: str, periods: int = 1):
    """Predict future price"""
    try:
        # Get historical data
        df = fyers_client.get_historical_data(
            symbol=symbol,
            resolution="D",
            date_from=datetime.now() - timedelta(days=60)
        )
        
        # Make prediction
        predictions = price_predictor.predict_next(df, periods=periods)
        
        return {
            "symbol": symbol,
            "current_price": float(df['close'].iloc[-1]),
            "predictions": [float(p) for p in predictions],
            "periods": periods
        }
    except Exception as e:
        logger.error(f"Error predicting price: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INDEX OPTIONS ENDPOINTS ====================

from src.analytics.index_options import get_index_analyzer, INDEX_CONFIG

@app.get("/index/list")
async def list_indices():
    """Get list of supported indices"""
    return {
        "indices": list(INDEX_CONFIG.keys()),
        "config": INDEX_CONFIG
    }


@app.get("/index/market-regime")
async def get_market_regime():
    """Get current market regime (VIX-based analysis)"""
    try:
        analyzer = get_index_analyzer(fyers_client)
        regime = analyzer.get_market_regime()
        return {
            "vix": regime.vix,
            "vix_trend": regime.vix_trend,
            "vix_percentile": regime.vix_percentile,
            "regime": regime.regime,
            "market_trend": regime.trend,
            "trend_strength": regime.strength,
            "recommendation": {
                "low_vol": "Favor option selling strategies (Iron Condor, Short Strangle)",
                "normal": "Balanced approach, directional trades OK",
                "high_vol": "Favor option buying, wide stops",
                "extreme": "Reduce position size, hedge existing positions"
            }.get(regime.regime, "Monitor closely")
        }
    except Exception as e:
        logger.error(f"Error getting market regime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/{index}/expiries")
async def get_expiry_dates(index: str):
    """Get weekly and monthly expiry dates for index"""
    try:
        analyzer = get_index_analyzer(fyers_client)
        expiries = analyzer.get_expiry_dates(index.upper())
        return {
            "index": index.upper(),
            "expiries": expiries
        }
    except Exception as e:
        logger.error(f"Error getting expiries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/{index}/chain")
async def get_option_chain_analysis(
    index: str,
    expiry: str = Query("weekly", description="weekly or monthly")
):
    """Get complete option chain analysis"""
    try:
        analyzer = get_index_analyzer(fyers_client)
        chain = analyzer.analyze_option_chain(index.upper(), expiry)
        
        if not chain:
            raise HTTPException(status_code=404, detail="Failed to fetch option chain")
        
        return {
            "index": chain.index,
            "spot_price": chain.spot_price,
            "future_price": chain.future_price,
            "basis": chain.basis,
            "basis_pct": chain.basis_pct,
            "vix": chain.vix,
            "pcr_oi": chain.pcr_oi,
            "pcr_volume": chain.pcr_volume,
            "max_pain": chain.max_pain,
            "atm_strike": chain.atm_strike,
            "atm_iv": chain.atm_iv,
            "iv_skew": chain.iv_skew,
            "expiry_date": chain.expiry_date,
            "days_to_expiry": chain.days_to_expiry,
            "totals": {
                "call_oi": chain.total_call_oi,
                "put_oi": chain.total_put_oi,
                "call_volume": chain.total_call_volume,
                "put_volume": chain.total_put_volume
            },
            "levels": {
                "support": chain.support_levels,
                "resistance": chain.resistance_levels
            },
            "oi_buildup": chain.oi_buildup_zones,
            "strikes": [
                {
                    "strike": s.strike,
                    "call": {
                        "ltp": s.call_ltp,
                        "iv": s.call_iv,
                        "oi": s.call_oi,
                        "volume": s.call_volume,
                        "oi_change": s.call_oi_change,
                        "analysis": s.call_analysis
                    },
                    "put": {
                        "ltp": s.put_ltp,
                        "iv": s.put_iv,
                        "oi": s.put_oi,
                        "volume": s.put_volume,
                        "oi_change": s.put_oi_change,
                        "analysis": s.put_analysis
                    }
                }
                for s in chain.strikes
            ]
        }
    except Exception as e:
        logger.error(f"Error getting option chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/{index}/signal")
async def get_index_signal(index: str):
    """
    Generate trading signal using top-down analysis
    
    Analysis Flow:
    1. Market Regime (VIX) → Position sizing
    2. Option Chain → PCR, Max Pain, OI
    3. Signal → Direction + Strategy
    """
    try:
        analyzer = get_index_analyzer(fyers_client)
        signal = analyzer.generate_index_signal(index.upper())
        return signal
    except Exception as e:
        logger.error(f"Error generating index signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/overview")
async def get_all_indices_overview():
    """Get quick overview of all supported indices"""
    try:
        indices = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
        overview = []
        
        for idx in indices:
            config = INDEX_CONFIG.get(idx)
            if config:
                quote = fyers_client.get_quotes([config["symbol"]])
                if quote and quote.get("d"):
                    v = quote["d"][0]["v"]
                    overview.append({
                        "index": idx,
                        "symbol": config["symbol"],
                        "ltp": v.get("lp", 0),
                        "change": v.get("ch", 0),
                        "change_pct": v.get("chp", 0),
                        "high": v.get("high_price", 0),
                        "low": v.get("low_price", 0),
                        "lot_size": config["lot_size"]
                    })
        
        # Add VIX
        vix_quote = fyers_client.get_quotes(["NSE:INDIAVIX-INDEX"])
        vix_data = None
        if vix_quote and vix_quote.get("d"):
            v = vix_quote["d"][0]["v"]
            vix_data = {
                "value": v.get("lp", 0),
                "change": v.get("ch", 0),
                "change_pct": v.get("chp", 0)
            }
        
        return {
            "indices": overview,
            "vix": vix_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MULTI-TIMEFRAME ICT ANALYSIS ====================

from src.analytics.mtf_ict_analysis import get_mtf_analyzer, Timeframe

@app.get("/mtf/{symbol}/analysis")
async def get_mtf_analysis(
    symbol: str,
    timeframes: str = Query("M,W,D,240,60", description="Comma-separated timeframes: M,W,D,240,60,15")
):
    """
    Multi-Timeframe ICT Analysis
    
    Analyzes: Monthly → Weekly → Daily → 4H → 1H → 15min
    Identifies: FVGs, Order Blocks, Liquidity Zones, Market Structure
    """
    try:
        analyzer = get_mtf_analyzer(fyers_client)
        
        # Parse timeframes
        tf_map = {
            "M": Timeframe.MONTHLY,
            "W": Timeframe.WEEKLY,
            "D": Timeframe.DAILY,
            "240": Timeframe.FOUR_HOUR,
            "60": Timeframe.ONE_HOUR,
            "15": Timeframe.FIFTEEN_MIN
        }
        
        requested_tfs = [tf_map[t.strip()] for t in timeframes.split(",") if t.strip() in tf_map]
        
        result = analyzer.analyze(symbol, requested_tfs)
        
        # Convert to JSON-serializable format
        return {
            "symbol": result.symbol,
            "current_price": result.current_price,
            "timestamp": result.timestamp.isoformat(),
            "overall_bias": result.overall_bias,
            "analyses": {
                tf: {
                    "timeframe": analysis.timeframe,
                    "market_structure": {
                        "trend": analysis.market_structure.trend,
                        "last_high": analysis.market_structure.last_high,
                        "last_low": analysis.market_structure.last_low,
                        "bos": analysis.market_structure.break_of_structure,
                        "choch": analysis.market_structure.change_of_character
                    },
                    "bias": analysis.bias,
                    "fair_value_gaps": [
                        {
                            "type": fvg.type,
                            "high": fvg.high,
                            "low": fvg.low,
                            "midpoint": fvg.midpoint,
                            "timestamp": fvg.timestamp.isoformat() if hasattr(fvg.timestamp, 'isoformat') else str(fvg.timestamp),
                            "status": fvg.status,
                            "test_count": fvg.test_count,
                            "first_test": fvg.first_test_time.isoformat() if fvg.first_test_time and hasattr(fvg.first_test_time, 'isoformat') else None,
                            "second_test": fvg.second_test_time.isoformat() if fvg.second_test_time and hasattr(fvg.second_test_time, 'isoformat') else None
                        }
                        for fvg in analysis.fair_value_gaps[:5]
                    ],
                    "order_blocks": [
                        {
                            "type": ob.type,
                            "high": ob.high,
                            "low": ob.low,
                            "tested": ob.tested,
                            "test_count": ob.test_count
                        }
                        for ob in analysis.order_blocks[:3]
                    ],
                    "liquidity_zones": [
                        {
                            "type": liq.type,
                            "level": liq.level,
                            "strength": liq.strength,
                            "swept": liq.swept
                        }
                        for liq in analysis.liquidity_zones[:5]
                    ],
                    "key_levels": analysis.key_levels[:10]
                }
                for tf, analysis in result.analyses.items()
            },
            "confluence_zones": [
                {
                    "center": zone["center"],
                    "weight": zone["total_weight"],
                    "timeframes": zone["timeframes"],
                    "distance_pct": zone["distance_pct"]
                }
                for zone in result.confluence_zones
            ],
            "trade_setups": result.trade_setups[:5]
        }
    except Exception as e:
        logger.error(f"Error in MTF analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mtf/{symbol}/fvg-status")
async def get_fvg_status(symbol: str):
    """
    Get FVG test status - First test, Second test tracking
    """
    try:
        analyzer = get_mtf_analyzer(fyers_client)
        result = analyzer.analyze(symbol, [Timeframe.DAILY, Timeframe.FOUR_HOUR, Timeframe.ONE_HOUR])
        
        fvg_status = []
        for tf, analysis in result.analyses.items():
            for fvg in analysis.fair_value_gaps:
                fvg_status.append({
                    "timeframe": tf,
                    "type": fvg.type,
                    "zone": f"{fvg.low:.2f} - {fvg.high:.2f}",
                    "midpoint": fvg.midpoint,
                    "status": fvg.status,
                    "test_count": fvg.test_count,
                    "first_test": fvg.first_test_time.isoformat() if fvg.first_test_time and hasattr(fvg.first_test_time, 'isoformat') else None,
                    "second_test": fvg.second_test_time.isoformat() if fvg.second_test_time and hasattr(fvg.second_test_time, 'isoformat') else None,
                    "trade_recommendation": _get_fvg_recommendation(fvg)
                })
        
        return {
            "symbol": symbol,
            "current_price": result.current_price,
            "fvg_analysis": sorted(fvg_status, key=lambda x: x["timeframe"])
        }
    except Exception as e:
        logger.error(f"Error getting FVG status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_fvg_recommendation(fvg) -> str:
    """Get trading recommendation based on FVG status"""
    if fvg.status == "active":
        return f"Wait for first test of {fvg.type} FVG"
    elif fvg.status == "tested_once":
        return f"ALERT: Watch for second test entry on {fvg.type} FVG"
    elif fvg.status == "tested_twice":
        return f"FVG tested twice - May be weakening or reversal imminent"
    return "Monitor"


# ==================== OPTIONS TIME ANALYSIS ====================

from src.analytics.options_time_analysis import options_time_analyzer

@app.get("/options/session")
async def get_current_session():
    """
    Get current market session analysis
    
    Sessions:
    - OPENING_VOLATILITY: 9:15-9:45 (High vol)
    - SESSION_1: 9:45-12:30 (Primary trading)
    - LUNCH_LULL: 12:30-13:30 (Low vol)
    - SESSION_2: 13:30-15:00 (Second push)
    - CLOSING_HOUR: 15:00-15:30 (Expiry pressure)
    """
    session = options_time_analyzer.get_current_session()
    return {
        "session": session.current_session,
        "start": session.session_start.isoformat(),
        "end": session.session_end.isoformat(),
        "minutes_elapsed": session.minutes_elapsed,
        "minutes_remaining": session.minutes_remaining,
        "volatility": session.volatility_expectation,
        "theta_impact": session.theta_impact,
        "recommendation": session.recommendation
    }


@app.get("/options/theta-decay")
async def get_theta_decay(days_to_expiry: int, iv: float = 15):
    """
    Analyze theta decay profile for given DTE
    """
    profile = options_time_analyzer.analyze_theta_decay(days_to_expiry, iv / 100)
    return {
        "days_to_expiry": profile.days_to_expiry,
        "hours_to_expiry": profile.hours_to_expiry,
        "theta": profile.current_theta,
        "daily_decay_pct": profile.daily_decay_pct,
        "hourly_decay_pct": profile.hourly_decay_pct,
        "decay_speed": profile.decay_acceleration,
        "strategy": profile.optimal_strategy
    }


@app.post("/options/project-price")
async def project_option_price(
    spot: float,
    strike: float,
    current_premium: float,
    target_move: float,
    days_to_expiry: int,
    iv: float = 15,
    option_type: str = "call",
    time_hours: Optional[float] = None
):
    """
    Project option price if underlying moves by target points
    
    Example: If NIFTY moves +50 points, what will the 25700 CE become?
    """
    projection = options_time_analyzer.project_option_price(
        spot=spot,
        strike=strike,
        current_option_price=current_premium,
        target_points=target_move,
        days_to_expiry=days_to_expiry,
        iv=iv / 100,
        option_type=option_type,
        time_horizon_hours=time_hours
    )
    
    return {
        "current": {
            "underlying": projection.underlying_current,
            "option_price": projection.current_option_price
        },
        "projected": {
            "underlying": projection.underlying_target,
            "option_price": projection.projected_option_price,
            "profit": projection.projected_profit,
            "profit_pct": projection.projected_profit_pct
        },
        "move_required": projection.points_move,
        "time_estimate": projection.time_required_estimate,
        "confidence": projection.confidence,
        "greeks": projection.greeks_used
    }


@app.post("/options/exit-targets")
async def calculate_exit_targets(
    entry_price: float,
    underlying: float,
    strike: float,
    days_to_expiry: int,
    iv: float = 15,
    option_type: str = "call",
    targets: str = "15,50,100"
):
    """
    Calculate underlying levels needed for target profit
    
    Example: If I buy at 100, what NIFTY level gives me +15, +50, +100 profit?
    """
    target_list = [float(t.strip()) for t in targets.split(",")]
    
    results = options_time_analyzer.calculate_exit_targets(
        entry_price=entry_price,
        underlying_price=underlying,
        strike=strike,
        days_to_expiry=days_to_expiry,
        iv=iv / 100,
        option_type=option_type,
        targets=target_list
    )
    
    return {
        "entry": {
            "option_price": entry_price,
            "underlying": underlying,
            "strike": strike,
            "type": option_type
        },
        "targets": results
    }


@app.get("/options/optimal-entry")
async def get_optimal_entry_time(trade_type: str, days_to_expiry: int):
    """
    Get optimal entry time recommendation
    
    trade_type: buy_call, buy_put, sell_call, sell_put
    """
    recommendation = options_time_analyzer.get_optimal_entry_time(trade_type, days_to_expiry)
    return recommendation


# ==================== NEWS & SENTIMENT ====================

from src.analytics.news_sentiment import news_analyzer

@app.get("/news/sentiment")
async def get_market_sentiment(symbol: Optional[str] = None):
    """
    Get market sentiment analysis from news
    """
    sentiment = news_analyzer.analyze_market_sentiment(symbol)
    
    return {
        "overall": sentiment.overall_sentiment,
        "score": sentiment.sentiment_score,
        "counts": {
            "bullish": sentiment.bullish_count,
            "bearish": sentiment.bearish_count,
            "neutral": sentiment.neutral_count
        },
        "themes": sentiment.key_themes,
        "mood": sentiment.market_mood,
        "implication": sentiment.trading_implication,
        "news": [
            {
                "title": n.title,
                "summary": n.summary,
                "source": n.source,
                "time": n.timestamp.isoformat(),
                "sentiment": n.sentiment,
                "score": n.sentiment_score,
                "keywords": n.keywords
            }
            for n in sentiment.news_items[:10]
        ]
    }


@app.get("/news/events")
async def get_event_calendar():
    """
    Get upcoming market events
    """
    events = news_analyzer.get_event_calendar()
    return {
        "events": events,
        "count": len(events)
    }


# ==================== TRADING SIGNALS ====================

@app.get("/signals/{symbol}/actionable")
async def get_actionable_trading_signal(symbol: str):
    """
    Get clear, actionable trading signals with specific strikes, prices, and timing
    
    Returns:
    - Exact option to buy/sell (strike + type)
    - Entry price and trigger levels
    - Target prices and stop loss
    - Best timing for entry
    - Risk/reward ratio
    """
    try:
        # Get MTF analysis
        mtf_analyzer = get_mtf_analyzer(fyers_client)
        from src.analytics.mtf_ict_analysis import Timeframe
        
        # DAY TRADING MODE: Use lower timeframes for intraday signals
        # 1H for context, 15min for setup, 5min for entry
        timeframes = [Timeframe.ONE_HOUR, Timeframe.FIFTEEN_MIN, Timeframe.FIVE_MIN]
        mtf_result = mtf_analyzer.analyze(symbol, timeframes)
        
        # Get current session
        session_info = options_time_analyzer.get_current_session()
        
        # DAY TRADING FILTER: Check if it's safe trading hours
        from datetime import datetime, time as dt_time
        now = datetime.now()
        current_time = now.time()
        
        # Block signals outside trading hours (9:30 AM - 2:00 PM for new entries)
        market_open = dt_time(9, 30)
        entry_cutoff = dt_time(14, 0)  # 2:00 PM
        
        is_trading_hours = market_open <= current_time <= entry_cutoff
        is_weekday = now.weekday() < 5  # Monday=0, Friday=4
        
        if not is_trading_hours or not is_weekday:
            return {
                "signal": "NO_ENTRY_WINDOW",
                "action": "WAIT",
                "reason": f"Outside day trading hours (9:30 AM - 2:00 PM). Current time: {current_time.strftime('%I:%M %p')}",
                "timing": "Wait for market open tomorrow" if not is_weekday else "Wait for 9:30 AM",
                "session_info": {
                    "current_time": current_time.strftime('%I:%M %p'),
                    "next_entry_window": "Monday 9:30 AM" if now.weekday() == 4 and current_time > entry_cutoff else "Tomorrow 9:30 AM" if current_time > entry_cutoff else "Today 9:30 AM"
                }
            }
        
        # Get option chain data (using index name from symbol)
        index_name = symbol.split(':')[1].replace('NIFTY50', 'NIFTY').replace('NIFTYBANK', 'BANKNIFTY').replace('-INDEX', '')
        
        chain_data = None
        try:
            # Get analyzed option chain data with LTP prices
            chain_res = await get_option_chain_analysis(index_name, "weekly")
            chain_data = chain_res
            logger.info(f"✅ Got option chain data for {index_name}")
            
            # DAY TRADING FILTER: Reject if expiring tomorrow (too much theta decay)
            days_to_expiry = chain_data.get('days_to_expiry', 7)
            if days_to_expiry <= 1:
                logger.warning(f"⚠️ Expiry in {days_to_expiry} day(s) - too risky for day trading")
                return {
                    "signal": "EXPIRY_TOO_CLOSE",
                    "action": "SKIP",
                    "reason": f"Option expiring in {days_to_expiry} day(s) - extreme theta decay risk",
                    "timing": "Wait for next weekly expiry",
                    "recommendation": "Day trading requires minimum 2-3 days to expiry. Use next week's options.",
                    "days_to_expiry": days_to_expiry
                }
            
            # Log sample strike data for debugging
            if chain_data.get("strikes"):
                sample = chain_data["strikes"][0]
                logger.info(f"📊 Sample strike data: {sample.get('strike')} - CE LTP: {sample.get('call', {}).get('ltp')}, PE LTP: {sample.get('put', {}).get('ltp')}")
                
        except Exception as e:
            logger.warning(f"Failed to get option chain data: {e}")
            
            # Try to get basic spot price at least
            try:
                spot_response = await fyers_client.get_quotes([symbol])
                spot_price = spot_response.get(symbol, {}).get('ltp', 25000)
                
                # Create minimal chain data for signal generation
                chain_data = {
                    "future_price": spot_price,
                    "atm_strike": round(spot_price / 50) * 50,
                    "strikes": [],
                    "days_to_expiry": 7,
                    "atm_iv": 15
                }
                logger.info(f"✅ Created fallback chain data with spot price: {spot_price}")
            except Exception as e2:
                logger.error(f"Could not get even basic spot price: {e2}")
        
        if not chain_data:
            # Ultimate fallback with NIFTY assumption
            chain_data = {
                "future_price": 25000,
                "atm_strike": 25000,
                "strikes": [],
                "days_to_expiry": 7,
                "atm_iv": 15
            }
            logger.warning("Using ultimate fallback chain data")
        
        # Fetch historical prices for ML prediction
        historical_prices = None
        try:
            # DAY TRADING: Get 15-minute intraday data for ML models (last 10 days)
            from datetime import datetime, timedelta
            today = datetime.now()
            start_date = today - timedelta(days=10)  # Last 10 trading days
            end_date = today
            
            # Try 15-minute data first (better for intraday)
            historical_df = fyers_client.get_historical_data(
                symbol=symbol,
                resolution="15",  # 15-minute candles
                date_from=start_date,
                date_to=end_date
            )
            
            # Fallback to hourly if 15-min fails
            if historical_df is None or historical_df.empty or len(historical_df) < 30:
                logger.warning("15-min data insufficient, trying hourly...")
                start_date = today - timedelta(days=30)
                historical_df = fyers_client.get_historical_data(
                    symbol=symbol,
                    resolution="60",  # Hourly
                    date_from=start_date,
                    date_to=end_date
                )
            
            if historical_df is not None and not historical_df.empty and len(historical_df) >= 30:
                # Get closing prices as pandas Series
                historical_prices = historical_df['close']
                logger.info(f"📊 Got {len(historical_prices)} intraday candles for ML analysis")
        except Exception as e:
            logger.warning(f"Could not fetch historical data for ML: {e}")
        
        # Always generate signal even with minimal data
        signal = _generate_actionable_signal(mtf_result, session_info, chain_data, historical_prices)
        
        # Ensure signal has all required fields
        if not signal.get("option"):
            signal["option"] = {
                "strike": chain_data.get("atm_strike", 25000),
                "type": "CE"
            }
        
        if not signal.get("entry"):
            signal["entry"] = {
                "price": 50,  # Basic fallback price
                "timing": "Market hours",
                "trigger_level": chain_data.get("future_price", 25000)
            }
        
        if not signal.get("targets"):
            entry_price = signal["entry"]["price"]
            signal["targets"] = {
                "target_1": round(entry_price * 1.3),
                "target_2": round(entry_price * 1.8),
                "stop_loss": round(entry_price * 0.75)
            }
        
        logger.info(f"✅ Generated signal: {signal['action']} {signal['option']['strike']} {signal['option']['type']} @ ₹{signal['entry']['price']}")
        return signal
        
    except Exception as e:
        logger.error(f"Error generating actionable signal: {e}")
        return {
            "signal": "ERROR",
            "reason": str(e),
            "action": "WAIT",
            "timing": "Check system",
            "option": {"strike": 25000, "type": "CE"},
            "entry": {"price": 50, "timing": "System error"},
            "targets": {"target_1": 65, "target_2": 90, "stop_loss": 35}
        }


def _estimate_option_price(spot_price: float, strike: float, action: str, chain_data: dict) -> float:
    """Estimate option price using Black-Scholes model with Greeks"""
    try:
        # Get ATM IV as baseline
        atm_iv = chain_data.get("atm_iv", 15) / 100 if chain_data.get("atm_iv") else 0.15
        dte = chain_data.get("days_to_expiry", 7)
        time_to_expiry = max(dte / 365.0, 0.001)  # Convert to years
        
        option_type = "call" if "CALL" in action else "put"
        
        # Use Black-Scholes for proper pricing
        bs_price = options_pricer.black_scholes_price(
            spot_price=spot_price,
            strike_price=strike,
            time_to_expiry=time_to_expiry,
            volatility=atm_iv,
            option_type=option_type
        )
        
        # Ensure minimum price
        return max(bs_price, 5.0)
        
    except Exception as e:
        logger.warning(f"Black-Scholes calculation failed: {e}, using fallback")
        # Fallback to simple estimation
        distance = abs(spot_price - strike) / spot_price
        if distance < 0.01:  # ATM
            return max(spot_price * 0.02, 50)
        elif distance < 0.05:  # Close to ATM
            return max(spot_price * 0.015, 25)
        else:  # Far OTM
            return max(spot_price * 0.005, 10)


def _generate_actionable_signal(mtf_result, session_info, chain_data, historical_prices=None):
    """Generate clear trading signal from MTF analysis with full Greeks integration and ML predictions"""
    
    spot_price = mtf_result.current_price
    overall_bias = mtf_result.overall_bias
    session = session_info.current_session
    
    # ==================== ML PREDICTION ANALYSIS ====================
    ml_signal = None
    ml_confidence = 0
    ml_direction = 'neutral'
    
    if historical_prices is not None and len(historical_prices) >= 50:
        try:
            # Get ML ensemble prediction (ARIMA + LSTM + Momentum)
            ml_result = get_ml_signal(historical_prices, steps=1)
            
            if ml_result.get('success'):
                ensemble = ml_result['predictions'].get('ensemble', {})
                ml_direction = ensemble.get('direction', 'neutral')
                ml_confidence = ensemble.get('direction_confidence', 0)
                
                ml_signal = {
                    'direction': ml_direction,
                    'confidence': ml_confidence,
                    'predicted_price': ensemble.get('predicted_price', spot_price),
                    'price_change_pct': ensemble.get('price_change_pct', 0),
                    'recommendation': ensemble.get('recommendation', 'Insufficient data'),
                    'arima': ml_result['predictions'].get('arima', {}),
                    'lstm': ml_result['predictions'].get('lstm', {}),
                    'momentum': ml_result['predictions'].get('momentum', {})
                }
                
                logger.info(f"🤖 ML Signal: {ml_direction} (confidence: {ml_confidence:.1%})")
                logger.info(f"   ARIMA: {ml_signal['arima'].get('direction', 'N/A')}")
                logger.info(f"   LSTM: {ml_signal['lstm'].get('direction', 'N/A')}")
                logger.info(f"   Momentum: {ml_signal['momentum'].get('direction', 'N/A')}")
                
        except Exception as e:
            logger.warning(f"ML prediction failed: {e}")
    else:
        logger.info("⚠️ Insufficient historical data for ML prediction (need 50+ candles)")
    # ================================================================
    
    # Get expiry and time-related data
    dte = chain_data.get("days_to_expiry", 7)
    time_to_expiry = max(dte / 365.0, 0.001)
    atm_iv = chain_data.get("atm_iv", 15) / 100 if chain_data.get("atm_iv") else 0.15
    
    # Get ATM strike
    atm_strike = chain_data.get("atm_strike", round(spot_price / 50) * 50)
    
    # Find the best FVG setup
    best_setup = None
    setup_timeframe = None
    
    for tf, analysis in mtf_result.analyses.items():
        for fvg in analysis.fair_value_gaps:
            distance_pct = abs(fvg.midpoint - spot_price) / spot_price * 100
            
            # Look for FVGs within 2% of current price
            if distance_pct < 2.0 and fvg.status in ['active', 'tested_once']:
                if not best_setup or distance_pct < abs(best_setup.midpoint - spot_price) / spot_price * 100:
                    best_setup = fvg
                    setup_timeframe = tf
    
    # Delta-based strike selection function
    def select_strike_by_delta(target_delta: float, option_type: str) -> int:
        """Select strike with delta closest to target"""
        strikes_to_check = range(atm_strike - 500, atm_strike + 550, 50)
        best_strike = atm_strike
        best_delta_diff = float('inf')
        
        for s in strikes_to_check:
            try:
                greeks = options_pricer.calculate_greeks(
                    spot_price=spot_price,
                    strike_price=s,
                    time_to_expiry=time_to_expiry,
                    volatility=atm_iv,
                    option_type=option_type
                )
                delta_diff = abs(abs(greeks['delta']) - target_delta)
                if delta_diff < best_delta_diff:
                    best_delta_diff = delta_diff
                    best_strike = s
            except:
                continue
        return best_strike
    
    # Generate signal based on setup
    if best_setup:
        if best_setup.type == 'bullish' and best_setup.status == 'active':
            signal_type = "BUY_CALL_FVG_TEST"
            action = "BUY CALL"
            # Select strike with ~0.40 delta for balanced risk/reward
            strike = select_strike_by_delta(0.40, "call")
            entry_trigger = best_setup.high if spot_price > best_setup.high else spot_price + 20
            timing = "Wait for pullback to FVG high" if spot_price > best_setup.high else "Enter on breakout"
                
        elif best_setup.type == 'bullish' and best_setup.status == 'tested_once':
            signal_type = "BUY_CALL_SECOND_TEST"
            action = "BUY CALL (STRONG)"
            # Higher delta (~0.50) for strong setups
            strike = select_strike_by_delta(0.50, "call")
            entry_trigger = best_setup.midpoint
            timing = "PRIORITY: Second test of bullish FVG"
            
        elif best_setup.type == 'bearish' and best_setup.status == 'active':
            signal_type = "BUY_PUT_FVG_TEST"
            action = "BUY PUT"
            strike = select_strike_by_delta(0.40, "put")
            entry_trigger = best_setup.low if spot_price < best_setup.low else spot_price - 20
            timing = "Wait for bounce to FVG low" if spot_price < best_setup.low else "Enter on breakdown"
                
        elif best_setup.type == 'bearish' and best_setup.status == 'tested_once':
            signal_type = "BUY_PUT_SECOND_TEST"
            action = "BUY PUT (STRONG)"
            strike = select_strike_by_delta(0.50, "put")
            entry_trigger = best_setup.midpoint
            timing = "PRIORITY: Second test of bearish FVG"
    
    else:
        # No clear FVG setup - use overall bias with OTM options
        if overall_bias == 'bullish':
            signal_type = "BUY_CALL_BIAS"
            action = "BUY CALL"
            strike = atm_strike + 100
            entry_trigger = spot_price + 30
            timing = "Bullish bias - enter on momentum"
        elif overall_bias == 'bearish':
            signal_type = "BUY_PUT_BIAS"
            action = "BUY PUT"
            strike = atm_strike - 100
            entry_trigger = spot_price - 30
            timing = "Bearish bias - enter on breakdown"
        else:
            return {
                "signal": "NO_CLEAR_SETUP",
                "action": "WAIT",
                "reason": "No clear directional bias or FVG setup",
                "timing": "Wait for better setup",
                "alternatives": [
                    "Consider Iron Condor for range-bound market",
                    "Wait for FVG test or clear breakout",
                    "Monitor for session volatility increase"
                ]
            }
    
    # Find option price from chain with robust error handling
    option_price = None
    strike_data = None
    price_source = "ESTIMATED"
    
    try:
        strikes = chain_data.get("strikes", [])
        if strikes:
            logger.info(f"🔍 Searching for strike {strike} in {len(strikes)} available strikes")
            
            # Find exact strike match
            strike_data = next((s for s in strikes if s.get("strike") == strike), None)
            
            if strike_data:
                option_type = "call" if "CALL" in action else "put"
                option_data = strike_data.get(option_type, {})
                
                # Try multiple price fields in order of preference
                option_price = (option_data.get("ltp") or 
                              option_data.get("ask") or 
                              option_data.get("mid_price") or
                              option_data.get("last_price"))
                
                # Ensure price is reasonable (not 0 or negative)
                if option_price and option_price > 0:
                    price_source = "LIVE_CHAIN"
                    logger.info(f"✅ Found LIVE price for {strike} {option_type.upper()}: ₹{option_price}")
                else:
                    option_price = None
                    strike_data = None
            
            # If exact strike not found, find nearest strike
            if not option_price and strikes:
                strikes_sorted = sorted(strikes, key=lambda x: abs(x.get("strike", 0) - strike))
                nearest_strike = strikes_sorted[0]
                option_type = "call" if "CALL" in action else "put"
                option_data = nearest_strike.get(option_type, {})
                
                option_price = (option_data.get("ltp") or 
                              option_data.get("ask") or 
                              option_data.get("mid_price") or
                              option_data.get("last_price"))
                              
                if option_price and option_price > 0:
                    old_strike = strike
                    strike = nearest_strike.get("strike", strike)  # Update to actual strike used
                    strike_data = nearest_strike
                    price_source = "LIVE_CHAIN_NEAREST"
                    logger.info(f"✅ Using nearest strike {strike} (requested {old_strike}), price: ₹{option_price}")
    
    except Exception as e:
        logger.error(f"Error finding option price for strike {strike}: {e}")
    
    # If still no price found, calculate estimated price
    if not option_price:
        option_price = _estimate_option_price(spot_price, strike, action, chain_data)
        logger.warning(f"Using estimated option price {option_price} for strike {strike}")
    
    # Store current LTP
    current_ltp = option_price
    
    # Analyze trend reversal probability based on FVG setup
    reversal_probability = 0.0
    reversal_confidence = "LOW"
    
    if best_setup:
        # Calculate reversal probability based on FVG characteristics
        prob_factors = []
        
        # Factor 1: FVG status (second test is stronger)
        if best_setup.status == 'tested_once':
            prob_factors.append(0.35)  # 35% weight - second test is strong
        elif best_setup.status == 'active':
            prob_factors.append(0.20)  # 20% weight - first test is moderate
        else:
            prob_factors.append(0.10)  # 10% weight - filled/tested twice is weak
        
        # Factor 2: Price position relative to FVG
        if best_setup.type == 'bullish':
            # For bullish FVG, better if price is at or below high
            distance_from_fvg = (spot_price - best_setup.high) / spot_price * 100
            if distance_from_fvg <= 0:  # Price at or below FVG high
                prob_factors.append(0.30)
            elif distance_from_fvg <= 0.5:  # Price slightly above
                prob_factors.append(0.20)
            else:
                prob_factors.append(0.10)
        else:  # bearish FVG
            # For bearish FVG, better if price is at or above low
            distance_from_fvg = (best_setup.low - spot_price) / spot_price * 100
            if distance_from_fvg <= 0:  # Price at or above FVG low
                prob_factors.append(0.30)
            elif distance_from_fvg <= 0.5:
                prob_factors.append(0.20)
            else:
                prob_factors.append(0.10)
        
        # Factor 3: FVG size (larger gaps are more significant)
        fvg_size_pct = abs(best_setup.high - best_setup.low) / spot_price * 100
        if fvg_size_pct >= 0.5:  # Large FVG (>0.5%)
            prob_factors.append(0.25)
        elif fvg_size_pct >= 0.3:  # Medium FVG
            prob_factors.append(0.15)
        else:  # Small FVG
            prob_factors.append(0.08)
        
        # Factor 4: Timeframe (higher timeframe FVGs are more reliable)
        if setup_timeframe in ['D', 'DAILY', 'W', 'WEEKLY']:
            prob_factors.append(0.10)  # Daily/Weekly is strong
        elif setup_timeframe in ['240', 'FOUR_HOUR']:
            prob_factors.append(0.07)
        else:
            prob_factors.append(0.04)
        
        reversal_probability = sum(prob_factors)
        
        # ==================== ML SIGNAL CONFIRMATION ====================
        # Factor 5: ML Model Agreement (ARIMA + LSTM + Momentum)
        ml_confirmation = 0
        ml_warning = None
        
        if ml_signal:
            # Check if ML prediction agrees with ICT setup direction
            expected_direction = 'bullish' if 'CALL' in action else 'bearish'
            
            if ml_direction == expected_direction:
                # ML agrees with ICT - boost confidence
                ml_boost = ml_confidence * 0.25  # Up to 25% boost
                prob_factors.append(ml_boost)
                ml_confirmation = ml_boost
                logger.info(f"✅ ML CONFIRMS {expected_direction.upper()}: +{ml_boost:.1%} confidence")
            elif ml_direction == 'neutral':
                # ML is neutral - slight penalty
                prob_factors.append(0.05)
                ml_confirmation = 0.05
                ml_warning = "⚠️ ML models show neutral - proceed with caution"
                logger.info(f"⚠️ ML neutral - no strong confirmation")
            else:
                # ML disagrees - significant warning
                prob_factors.append(0.0)  # No boost
                ml_confirmation = 0
                ml_warning = f"🚨 ML WARNS: {ml_direction.upper()} signal contradicts ICT {expected_direction}!"
                logger.warning(f"🚨 ML CONTRADICTS: ML says {ml_direction}, ICT says {expected_direction}")
        
        reversal_probability = sum(prob_factors)
        # ==============================================================
        
        # Determine confidence level (accounting for ML warnings)
        # If ML is neutral or contradicts, cap confidence lower
        ml_penalty = False
        if ml_signal and ml_direction == 'neutral':
            ml_penalty = True  # ML is uncertain
        elif ml_signal and ml_direction != 'neutral':
            expected_dir = 'bullish' if 'CALL' in action else 'bearish'
            if ml_direction != expected_dir:
                ml_penalty = True  # ML contradicts
        
        if reversal_probability >= 0.70 and not ml_penalty:
            reversal_confidence = "VERY HIGH"
        elif reversal_probability >= 0.65 and not ml_penalty:
            reversal_confidence = "HIGH"
        elif reversal_probability >= 0.55:
            # If ML penalty, cap at MODERATE even with higher probability
            reversal_confidence = "MODERATE" if ml_penalty else "HIGH"
        elif reversal_probability >= 0.40:
            reversal_confidence = "MODERATE"
        else:
            reversal_confidence = "LOW"
    else:
        prob_factors = []
        ml_confirmation = 0
        ml_warning = None
    
    # Calculate strategic entry price based on setup and reversal probability
    strategic_entry_price = current_ltp
    entry_reasoning = "Enter at current market price"
    
    if best_setup:
        # Analyze CE vs PE relative strength
        # Get both CE and PE data for the selected strike
        ce_data = None
        pe_data = None
        
        try:
            strikes = chain_data.get("strikes", [])
            strike_match = next((s for s in strikes if s.get("strike") == strike), None)
            if strike_match:
                ce_data = strike_match.get("call", {})
                pe_data = strike_match.get("put", {})
        except:
            pass
        
        # Calculate entry price adjustment based on FVG test number and reversal probability
        if best_setup.status == 'active':
            # FIRST TEST - More conservative, wait for confirmation
            if reversal_probability >= 0.55:
                # High probability - can be slightly aggressive
                strategic_entry_price = round(current_ltp * 1.03, 2)  # 3% premium
                entry_reasoning = f"💡 Try to buy at LTP ₹{current_ltp}, acceptable up to ₹{round(current_ltp * 1.03, 2)} (3% max premium)"
            else:
                # Moderate/low probability - very conservative
                strategic_entry_price = round(current_ltp * 1.02, 2)  # 2% premium
                entry_reasoning = f"💡 Try to buy at LTP ₹{current_ltp}, acceptable up to ₹{round(current_ltp * 1.02, 2)} (2% max premium)"
                
        elif best_setup.status == 'tested_once':
            # SECOND TEST - More aggressive, higher probability
            if reversal_probability >= 0.65:
                # Very high probability on second test - be aggressive
                strategic_entry_price = round(current_ltp * 1.08, 2)  # 8% premium
                entry_reasoning = f"⭐ STRONG 2nd test: Buy at LTP ₹{current_ltp}, max ₹{round(current_ltp * 1.08, 2)} (8% premium acceptable)"
            elif reversal_probability >= 0.50:
                # Good probability - moderately aggressive
                strategic_entry_price = round(current_ltp * 1.05, 2)  # 5% premium
                entry_reasoning = f"💪 Good 2nd test: Buy at LTP ₹{current_ltp}, max ₹{round(current_ltp * 1.05, 2)} (5% premium acceptable)"
            else:
                strategic_entry_price = round(current_ltp * 1.03, 2)
                entry_reasoning = f"⚠️ Weak 2nd test: Prefer LTP ₹{current_ltp}, max ₹{round(current_ltp * 1.03, 2)} (cautious)"
        
        # Adjust based on index movement momentum
        # If we're buying calls and index is moving up, or buying puts and index is moving down
        # we can afford to pay slightly more
        if best_setup.type == 'bullish' and "CALL" in action:
            # Bullish setup with calls - check if momentum is with us
            if spot_price > best_setup.midpoint:
                strategic_entry_price = round(strategic_entry_price * 1.02, 2)
                entry_reasoning += f" [Momentum: max ₹{strategic_entry_price}]"
        elif best_setup.type == 'bearish' and "PUT" in action:
            # Bearish setup with puts - check if momentum is with us  
            if spot_price < best_setup.midpoint:
                strategic_entry_price = round(strategic_entry_price * 1.02, 2)
                entry_reasoning += f" [Momentum: max ₹{strategic_entry_price}]"
                
    else:
        # No FVG setup - bias-based trade
        reversal_confidence = "LOW"
        reversal_probability = 0.30
        strategic_entry_price = round(current_ltp * 1.02, 2)
        entry_reasoning = "No clear FVG - bias-based entry at market price"
    
    # Calculate adaptive targets and stop loss based on option price and volatility
    # DAY TRADING MODE: Realistic intraday targets
    try:
        iv = chain_data.get("atm_iv", 15) / 100 if chain_data.get("atm_iv") else 0.15
        dte = chain_data.get("days_to_expiry", 7)
        
        # Adaptive profit targets based on strategic entry price
        entry_for_calc = strategic_entry_price
        
        # INTRADAY TARGETS: Lower profit expectations, tighter stops
        if entry_for_calc <= 20:  # Cheap options
            target_1 = entry_for_calc * 1.20  # 20% profit (realistic intraday)
            target_2 = entry_for_calc * 1.40  # 40% profit (stretch target)
            stop_loss = entry_for_calc * 0.85  # 15% loss (tight stop)
        elif entry_for_calc <= 50:  # Medium priced
            target_1 = entry_for_calc * 1.15  # 15% profit
            target_2 = entry_for_calc * 1.30  # 30% profit
            stop_loss = entry_for_calc * 0.90  # 10% loss
        else:  # Expensive options - very conservative
            target_1 = entry_for_calc * 1.10  # 10% profit
            target_2 = entry_for_calc * 1.20  # 20% profit
            stop_loss = entry_for_calc * 0.90 # 10% loss
            
        # Adjust for time decay (closer to expiry = tighter stops)
        # DAY TRADING: Exit by 3:15 PM regardless of profit/loss
        if dte <= 3:
            stop_loss = max(stop_loss, entry_for_calc * 0.85)  # Tighter stop for near expiry
            theta_warning = "⚠️ INTRADAY ONLY - Exit before 3:15 PM to avoid theta"
        elif dte <= 7:
            stop_loss = max(stop_loss, entry_for_calc * 0.90)
            theta_warning = "⏰ DAY TRADE - Exit by 3:15 PM or risk overnight theta"
        else:
            theta_warning = "✅ Can hold beyond today if needed"
            
    except Exception:
        # Fallback to conservative targets
        target_1 = strategic_entry_price * 1.3
        target_2 = strategic_entry_price * 1.8
        stop_loss = option_price * 0.7
        theta_warning = "Unknown theta impact"
    
    # Calculate Greeks for the selected option
    option_type = "call" if "CALL" in action else "put"
    try:
        greeks = options_pricer.calculate_greeks(
            spot_price=spot_price,
            strike_price=strike,
            time_to_expiry=time_to_expiry,
            volatility=atm_iv,
            option_type=option_type
        )
        
        # Calculate theoretical price using Black-Scholes
        bs_price = options_pricer.black_scholes_price(
            spot_price=spot_price,
            strike_price=strike,
            time_to_expiry=time_to_expiry,
            volatility=atm_iv,
            option_type=option_type
        )
    except Exception as e:
        logger.warning(f"Greeks calculation failed: {e}")
        greeks = {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}
        bs_price = current_ltp
    
    # Risk/Reward calculation based on strategic entry price
    risk_per_lot = strategic_entry_price - stop_loss
    reward_1 = target_1 - strategic_entry_price
    reward_2 = target_2 - strategic_entry_price
    
    # Session timing recommendation
    session_timing = _get_session_timing(session)
    
    # Gamma risk warning for weekly expiry
    gamma_warning = ""
    if dte <= 1 and abs(spot_price - strike) < 100:
        gamma_warning = "🔴 EXTREME GAMMA RISK - Near ATM on expiry day!"
    elif dte <= 3 and abs(spot_price - strike) < 150:
        gamma_warning = "🟠 HIGH GAMMA - Pin risk near strike"
    
    # Get expiry date from chain data for symbol generation
    expiry_date = chain_data.get("expiry_date", "")
    
    # Generate Fyers-compatible symbol
    option_suffix = "CE" if "CALL" in action else "PE"
    try:
        from datetime import datetime as dt
        if expiry_date:
            exp_dt = dt.strptime(expiry_date, "%Y-%m-%d") if isinstance(expiry_date, str) else expiry_date
            expiry_code = exp_dt.strftime("%y%m%d") if hasattr(exp_dt, 'strftime') else ""
        else:
            expiry_code = ""
    except:
        expiry_code = ""
    
    # Full trading symbol (e.g., NSE:NIFTY26012025600PE)
    index_name = chain_data.get("index", "NIFTY")
    full_symbol = f"NSE:{index_name}{expiry_code}{int(strike)}{option_suffix}" if expiry_code else f"{int(strike)} {option_suffix}"
    
    # Extract complete option chain info for the selected strike
    option_chain_info = None
    if strike_data:
        option_type = "call" if "CALL" in action else "put"
        selected_option = strike_data.get(option_type, {})
        opposite_option = strike_data.get("put" if option_type == "call" else "call", {})
        
        option_chain_info = {
            "selected_option": {
                "ltp": selected_option.get("ltp", 0),
                "iv": selected_option.get("iv", 0),
                "oi": selected_option.get("oi", 0),
                "volume": selected_option.get("volume", 0),
                "oi_change": selected_option.get("oi_change", 0),
                "analysis": selected_option.get("analysis", "")
            },
            "opposite_side": {
                "type": "CE" if option_type == "put" else "PE",
                "ltp": opposite_option.get("ltp", 0),
                "iv": opposite_option.get("iv", 0),
                "oi": opposite_option.get("oi", 0),
                "volume": opposite_option.get("volume", 0)
            },
            "strike_position": "ATM" if abs(strike - spot_price) < 50 else ("ITM" if (option_type == "call" and strike < spot_price) or (option_type == "put" and strike > spot_price) else "OTM"),
            "distance_from_spot": round(abs(strike - spot_price), 2),
            "distance_pct": round(abs(strike - spot_price) / spot_price * 100, 2)
        }
    
    return {
        "signal": signal_type,
        "action": action,
        "option": {
            "strike": strike,
            "type": option_suffix,
            "symbol": f"{int(strike)} {option_suffix}",
            "trading_symbol": full_symbol,
            "expiry_date": expiry_date,
            "expiry_info": {
                "days_to_expiry": dte,
                "is_weekly": dte <= 7,
                "time_to_expiry_years": round(time_to_expiry, 4)
            },
            "chain_data": option_chain_info
        },
        "pricing": {
            "ltp": round(current_ltp, 2),
            "entry_price": round(strategic_entry_price, 2),
            "entry_reasoning": entry_reasoning,
            "black_scholes_price": round(bs_price, 2),
            "iv_used": round(atm_iv * 100, 2),
            "price_source": price_source,
            "price_vs_bs": "Fair" if abs(option_price - bs_price) < 5 else ("Expensive" if option_price > bs_price else "Cheap")
        },
        "greeks": {
            "delta": round(greeks.get('delta', 0), 4),
            "gamma": round(greeks.get('gamma', 0), 4),
            "theta": round(greeks.get('theta', 0), 4),
            "vega": round(greeks.get('vega', 0), 4),
            "rho": round(greeks.get('rho', 0), 4),
            "interpretation": {
                "delta_meaning": f"Option moves ₹{abs(greeks.get('delta', 0) * 50):.1f} per ₹50 spot move",
                "theta_meaning": f"Loses ₹{abs(greeks.get('theta', 0)):.2f} per day from time decay",
                "gamma_meaning": f"Delta changes by {greeks.get('gamma', 0):.4f} per ₹1 spot move"
            }
        },
        "entry": {
            "price": round(strategic_entry_price, 2),
            "ltp": round(current_ltp, 2),
            "trigger_level": round(entry_trigger, 2),
            "timing": timing,
            "reasoning": entry_reasoning,
            "session_advice": session_timing
        },
        "targets": {
            "target_1": round(target_1, 2),
            "target_2": round(target_2, 2),
            "stop_loss": round(stop_loss, 2),
            "theta_warning": theta_warning,
            "gamma_warning": gamma_warning
        },
        "risk_reward": {
            "risk_per_lot": round(risk_per_lot, 2),
            "reward_1_per_lot": round(reward_1, 2),
            "reward_2_per_lot": round(reward_2, 2),
            "ratio_1": f"1:{(reward_1/risk_per_lot):.1f}" if risk_per_lot > 0 else "N/A",
            "ratio_2": f"1:{(reward_2/risk_per_lot):.1f}" if risk_per_lot > 0 else "N/A"
        },
        "setup_details": {
            "timeframe": setup_timeframe if best_setup else "Overall",
            "fvg_level": best_setup.midpoint if best_setup else None,
            "fvg_status": best_setup.status if best_setup else None,
            "reasoning": f"Based on {setup_timeframe} {best_setup.type} FVG" if best_setup else f"Based on {overall_bias} bias",
            "reversal_probability": round(reversal_probability * 100, 1) if best_setup else None,
            "confidence_level": reversal_confidence if best_setup else None,
            "probability_factors": {
                "fvg_status": f"{prob_factors[0]*100:.0f}%" if len(prob_factors) > 0 else "0%",
                "price_position": f"{prob_factors[1]*100:.0f}%" if len(prob_factors) > 1 else "0%",
                "fvg_size": f"{prob_factors[2]*100:.0f}%" if len(prob_factors) > 2 else "0%",
                "timeframe_weight": f"{prob_factors[3]*100:.0f}%" if len(prob_factors) > 3 else "0%",
                "ml_confirmation": f"{ml_confirmation*100:.0f}%" if ml_confirmation else "0%"
            } if best_setup else None
        },
        "ml_analysis": {
            "enabled": ml_signal is not None,
            "direction": ml_signal.get('direction', 'N/A') if ml_signal else 'N/A',
            "confidence": round(ml_signal.get('confidence', 0) * 100, 1) if ml_signal else 0,
            "predicted_price": ml_signal.get('predicted_price') if ml_signal else None,
            "price_change_pct": ml_signal.get('price_change_pct') if ml_signal else None,
            "recommendation": ml_signal.get('recommendation', 'ML not available') if ml_signal else 'ML not available',
            "warning": ml_warning,
            "models": {
                "arima": ml_signal.get('arima', {}).get('direction', 'N/A') if ml_signal else 'N/A',
                "lstm": ml_signal.get('lstm', {}).get('direction', 'N/A') if ml_signal else 'N/A',
                "momentum": ml_signal.get('momentum', {}).get('direction', 'N/A') if ml_signal else 'N/A'
            } if ml_signal else None
        },
        "confidence": reversal_confidence if best_setup else "MEDIUM",
        # TRADE RECOMMENDATION based on all factors
        "trade_recommendation": _get_trade_recommendation(
            reversal_probability if best_setup else 0,
            reversal_confidence if best_setup else "LOW",
            ml_signal,
            ml_warning
        ),
        # DAY TRADING MODE INDICATOR
        "trading_mode": {
            "mode": "INTRADAY",
            "description": "Day Trading (Exit by 3:15 PM)",
            "timeframes": "15min + 5min signals",
            "targets": "Quick 10-30% gains",
            "max_hold": "Same day only",
            "entry_window": "9:30 AM - 2:00 PM"
        },
        "market_context": {
            "spot_price": round(spot_price, 2),
            "atm_strike": atm_strike,
            "overall_bias": overall_bias,
            "iv_regime": "High" if atm_iv > 0.20 else ("Low" if atm_iv < 0.12 else "Normal")
        }
    }


def _get_trade_recommendation(probability: float, confidence: str, ml_signal: dict, ml_warning: str) -> dict:
    """
    Generate final trade recommendation based on all factors.
    Returns clear verdict: TAKE_TRADE, WAIT, or AVOID
    """
    verdict = "TAKE_TRADE"
    reasons = []
    risk_level = "MEDIUM"
    
    # Check ML status
    ml_direction = ml_signal.get('direction', 'neutral') if ml_signal else 'neutral'
    ml_confidence = ml_signal.get('confidence', 0) if ml_signal else 0
    
    # Determine verdict based on factors
    if probability >= 0.65 and confidence in ["VERY HIGH", "HIGH"] and ml_warning is None:
        verdict = "TAKE_TRADE"
        risk_level = "LOW"
        reasons.append("✅ Strong ICT setup with ML confirmation")
    elif probability >= 0.55 and ml_direction == 'neutral':
        verdict = "WAIT"
        risk_level = "MEDIUM"
        reasons.append("⚠️ ICT setup present but ML shows uncertainty")
        reasons.append("💡 Consider waiting for clearer ML signal or reducing position size")
    elif ml_warning and "CONTRADICTS" in str(ml_warning).upper():
        verdict = "AVOID"
        risk_level = "HIGH"
        reasons.append("🚨 ML contradicts ICT signal - high risk of false signal")
        reasons.append("💡 Wait for ML and ICT to align")
    elif probability < 0.50:
        verdict = "AVOID"
        risk_level = "HIGH"
        reasons.append("❌ Low probability setup - not worth the risk")
    elif confidence == "LOW" or confidence == "MODERATE":
        verdict = "WAIT"
        risk_level = "MEDIUM"
        reasons.append("⚠️ Setup confidence is low - wait for better opportunity")
    
    return {
        "verdict": verdict,
        "risk_level": risk_level,
        "reasons": reasons,
        "position_size_advice": "Full size" if verdict == "TAKE_TRADE" else ("Half size" if verdict == "WAIT" else "No trade"),
        "summary": f"{'✅ TRADE' if verdict == 'TAKE_TRADE' else '⏸️ WAIT' if verdict == 'WAIT' else '❌ AVOID'}: {reasons[0] if reasons else 'Based on overall analysis'}"
    }


def _get_session_timing(session):
    """Get session-specific timing advice for Indian market (Mon-Fri)"""
    from datetime import datetime
    
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()  # 0=Monday, 4=Friday
    
    # Market closed on weekends
    if weekday >= 5:
        return {
            "session": "CLOSED",
            "advice": "MARKET CLOSED: Weekend - Plan for Monday",
            "can_trade": False,
            "risk_level": "N/A"
        }
    
    # Define Indian market sessions (IST)
    from datetime import time
    market_open = time(9, 15)
    session_1_end = time(12, 30)  # First session: 9:15 AM - 12:30 PM
    session_2_end = time(15, 30)  # Second session: 12:30 PM - 3:30 PM
    
    # Pre-market
    if current_time < market_open:
        return {
            "session": "PRE_MARKET",
            "advice": "WAIT: Market opens at 9:15 AM IST",
            "can_trade": False,
            "risk_level": "N/A",
            "next_session": "Session 1 (9:15 AM - 12:30 PM)"
        }
    
    # Opening volatility (9:15 - 9:45)
    if current_time < time(9, 45):
        return {
            "session": "OPENING_VOLATILITY",
            "advice": "HIGH RISK: Opening volatility - Wait for 9:45 AM for better entries",
            "can_trade": True,
            "risk_level": "HIGH",
            "theta_impact": "Low (full day ahead)",
            "gamma_impact": "HIGH (volatile moves)"
        }
    
    # Session 1: 9:45 AM - 12:30 PM (Prime trading)
    if current_time < session_1_end:
        return {
            "session": "SESSION_1",
            "advice": "EXCELLENT: Primary trading session - Best time for directional trades",
            "can_trade": True,
            "risk_level": "MODERATE",
            "theta_impact": "Low",
            "gamma_impact": "Moderate",
            "strategy_tip": "Good for momentum trades, FVG tests"
        }
    
    # Lunch lull (12:30 - 1:30 PM)
    if current_time < time(13, 30):
        return {
            "session": "LUNCH_LULL",
            "advice": "AVOID: Low volume lunch period - Wait for Session 2",
            "can_trade": True,
            "risk_level": "LOW VOLUME",
            "theta_impact": "Moderate (half day gone)",
            "gamma_impact": "Low",
            "strategy_tip": "Avoid new positions, manage existing"
        }
    
    # Session 2: 1:30 PM - 3:00 PM (Afternoon momentum)
    if current_time < time(15, 0):
        return {
            "session": "SESSION_2",
            "advice": "GOOD: Afternoon momentum session - Watch for institutional moves",
            "can_trade": True,
            "risk_level": "MODERATE",
            "theta_impact": "Moderate to High",
            "gamma_impact": "Increasing",
            "strategy_tip": "Good for breakout trades, watch for reversals"
        }
    
    # Closing hour (3:00 PM - 3:30 PM)
    if current_time < session_2_end:
        return {
            "session": "CLOSING_HOUR",
            "advice": "CAUTION: Exit positions only - High gamma/theta risk",
            "can_trade": True,
            "risk_level": "HIGH",
            "theta_impact": "VERY HIGH (especially weekly expiry)",
            "gamma_impact": "EXTREME (pin risk near strikes)",
            "strategy_tip": "Close positions, avoid new entries"
        }
    
    # After hours
    return {
        "session": "CLOSED",
        "advice": "MARKET CLOSED: Plan for next trading day",
        "can_trade": False,
        "risk_level": "N/A",
        "next_session": "Tomorrow 9:15 AM" if weekday < 4 else "Monday 9:15 AM"
    }


@app.get("/options/quote/{index}/{strike}/{option_type}")
async def get_option_quote(
    index: str,
    strike: float,
    option_type: str,  # 'call' or 'put'
    expiry: Optional[str] = None
):
    """
    Get real-time option quote for specific strike and type
    Returns current LTP, bid, ask, volume, OI etc.
    """
    try:
        # Get current expiry if not provided
        if not expiry:
            symbol_info = await fyers_client.get_symbols(index)
            expiry = symbol_info["nearest_expiry"].strftime('%y%m%d')
        else:
            # Convert expiry format if needed
            try:
                if len(expiry) == 10:  # YYYY-MM-DD
                    exp_date = datetime.strptime(expiry, '%Y-%m-%d')
                    expiry = exp_date.strftime('%y%m%d')
            except:
                pass
        
        # Generate option symbol
        option_symbol = f"NSE:{index}{expiry}{int(strike)}{'CE' if option_type.lower() == 'call' else 'PE'}"
        
        # Get real-time quote
        try:
            quote_data = await fyers_client.get_quotes([option_symbol])
            option_data = quote_data.get(option_symbol, {})
            
            if not option_data:
                raise ValueError(f"No data for symbol {option_symbol}")
                
            # Extract relevant quote information
            return {
                "symbol": option_symbol,
                "strike": strike,
                "type": option_type.upper(),
                "expiry": expiry,
                "ltp": option_data.get("ltp", 0),
                "bid": option_data.get("bid", 0),
                "ask": option_data.get("ask", 0),
                "volume": option_data.get("volume", 0),
                "oi": option_data.get("oi", 0),
                "change": option_data.get("ch", 0),
                "change_pct": option_data.get("chp", 0),
                "high": option_data.get("high", 0),
                "low": option_data.get("low", 0),
                "mid_price": (option_data.get("bid", 0) + option_data.get("ask", 0)) / 2 if option_data.get("bid") and option_data.get("ask") else option_data.get("ltp", 0),
                "spread": option_data.get("ask", 0) - option_data.get("bid", 0) if option_data.get("bid") and option_data.get("ask") else 0,
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching quote for {option_symbol}: {e}")
            return {
                "symbol": option_symbol,
                "strike": strike,
                "type": option_type.upper(),
                "error": f"Quote unavailable: {str(e)}",
                "ltp": 0,
                "estimated": True
            }
            
    except Exception as e:
        logger.error(f"Error in get_option_quote: {e}")
        return {"error": str(e)}


@app.post("/orders/execute")
async def execute_order(order_data: dict):
    """
    Execute trading order (simulated execution for now)
    Can be extended to integrate with broker APIs
    """
    try:
        symbol = order_data.get("symbol", "")
        side = order_data.get("side", "BUY")  # BUY or SELL
        quantity = order_data.get("quantity", 1)
        price = order_data.get("price", 0)
        order_type = order_data.get("type", "MARKET")  # MARKET or LIMIT
        
        # Generate order ID
        order_id = f"TW{int(datetime.now().timestamp())}"
        
        # Get current market price for comparison
        try:
            if "CE" in symbol or "PE" in symbol:
                # Option order - extract details from symbol
                parts = symbol.split()
                if len(parts) >= 2:
                    strike_info = parts[0]
                    option_type_info = parts[1]
                    
                    # Get real-time quote for validation
                    quote_response = await get_option_quote(
                        index="NIFTY",  # Default to NIFTY for now
                        strike=float(strike_info.replace("CE", "").replace("PE", "")),
                        option_type="call" if "CE" in option_type_info else "put"
                    )
                    
                    market_price = quote_response.get("ltp", price)
                else:
                    market_price = price
            else:
                market_price = price
                
        except Exception as e:
            logger.warning(f"Could not get market price: {e}")
            market_price = price
        
        # Simulate order execution
        execution_price = market_price if order_type == "MARKET" else price
        
        # Calculate order value
        order_value = execution_price * quantity
        
        # Simulate order status
        status = "EXECUTED" if order_type == "MARKET" else "PENDING"
        if order_type == "LIMIT":
            # Simple logic - execute if limit price is reasonable
            price_diff_pct = abs(execution_price - market_price) / market_price * 100
            if price_diff_pct <= 2:  # Within 2% of market price
                status = "EXECUTED"
            else:
                status = "PENDING"
        
        # Store order (in production, this would go to database)
        order_details = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "order_price": price,
            "execution_price": execution_price,
            "order_value": order_value,
            "status": status,
            "order_type": order_type,
            "timestamp": datetime.now().isoformat(),
            "market_price_at_order": market_price
        }
        
        # Log the order
        logger.info(f"Order executed: {order_details}")
        
        return {
            "success": True,
            "order": order_details,
            "message": f"Order {order_id} {status.lower()} successfully",
            "execution_summary": {
                "symbol": symbol,
                "action": f"{side} {quantity} lots",
                "price": f"₹{execution_price:.2f}",
                "total_value": f"₹{order_value:,.2f}",
                "status": status
            }
        }
        
    except Exception as e:
        logger.error(f"Error executing order: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Order execution failed"
        }


@app.post("/alerts/create")
async def create_price_alert(alert_data: dict):
    """
    Create price alerts for entry and exit levels
    """
    try:
        symbol = alert_data.get("symbol", "")
        alert_type = alert_data.get("type", "PRICE")  # PRICE, ENTRY, EXIT
        target_price = alert_data.get("target_price", 0)
        condition = alert_data.get("condition", "ABOVE")  # ABOVE, BELOW
        message = alert_data.get("message", "Price alert triggered")
        
        alert_id = f"AL{int(datetime.now().timestamp())}"
        
        # Store alert (in production, this would go to database)
        alert_details = {
            "alert_id": alert_id,
            "symbol": symbol,
            "type": alert_type,
            "target_price": target_price,
            "condition": condition,
            "message": message,
            "status": "ACTIVE",
            "created_at": datetime.now().isoformat(),
            "triggered_at": None
        }
        
        logger.info(f"Alert created: {alert_details}")
        
        return {
            "success": True,
            "alert": alert_details,
            "message": f"Price alert {alert_id} created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/analysis/signal-reasoning/{index}")
async def get_signal_reasoning(index: str):
    """
    Get detailed reasoning behind the current trading signal
    """
    try:
        # Get current MTF analysis
        symbol = f"NSE:{index.upper()}50-INDEX" if index.upper() == "NIFTY" else f"NSE:{index.upper()}"
        
        # Get MTF data
        mtf_analysis = await get_mtf_analysis(symbol, "M,W,D,240,60,15")
        
        # Get current session info
        session_response = await get_options_session_info()
        
        # Get option chain for context
        try:
            chain_response = await get_option_chain(index, None)
        except:
            chain_response = {"future_price": 25000, "atm_strike": 25000}
        
        # Generate detailed reasoning
        reasoning = {
            "signal_strength": "HIGH" if mtf_analysis.get("overall_bias") in ["bullish", "bearish"] else "MEDIUM",
            "primary_driver": mtf_analysis.get("overall_bias", "neutral").upper(),
            "key_levels": [],
            "timeframe_analysis": {},
            "risk_factors": [],
            "confluence_factors": [],
            "session_context": session_response.get("current_session", "UNKNOWN"),
            "market_structure": "Unknown"
        }
        
        # Analyze key timeframes
        for tf, data in mtf_analysis.get("analyses", {}).items():
            tf_reasoning = {
                "bias": data.get("bias", "neutral"),
                "structure": data.get("market_structure", "range"),
                "key_points": []
            }
            
            # Add FVG information
            fvgs = data.get("fair_value_gaps", [])
            active_fvgs = [fvg for fvg in fvgs if fvg.get("status") == "active"]
            if active_fvgs:
                tf_reasoning["key_points"].append(f"{len(active_fvgs)} active FVG(s)")
                
            # Add order blocks
            obs = data.get("order_blocks", [])
            if obs:
                tf_reasoning["key_points"].append(f"{len(obs)} order block(s)")
                
            reasoning["timeframe_analysis"][tf] = tf_reasoning
        
        # Add confluence factors
        confluence_zones = mtf_analysis.get("confluence_zones", [])
        for zone in confluence_zones:
            if zone.get("strength", 0) >= 3:
                reasoning["confluence_factors"].append({
                    "level": zone.get("level", 0),
                    "strength": zone.get("strength", 0),
                    "components": zone.get("components", [])
                })
        
        # Add risk factors
        current_session = session_response.get("current_session", "")
        if current_session in ["OPENING_VOLATILITY", "CLOSING_HOUR"]:
            reasoning["risk_factors"].append("High volatility session - increased risk")
            
        if session_response.get("time_to_expiry", {}).get("days", 7) <= 2:
            reasoning["risk_factors"].append("Weekly expiry - high gamma risk")
        
        # Market structure assessment
        if mtf_analysis.get("overall_bias") == "bullish":
            reasoning["market_structure"] = "Bullish trend with buy-side liquidity targeting"
        elif mtf_analysis.get("overall_bias") == "bearish":
            reasoning["market_structure"] = "Bearish trend with sell-side liquidity targeting"
        else:
            reasoning["market_structure"] = "Range-bound market - reversal plays preferred"
        
        return {
            "index": index.upper(),
            "analysis_time": datetime.now().isoformat(),
            "reasoning": reasoning,
            "recommendation": {
                "strategy": "Directional options" if reasoning["signal_strength"] == "HIGH" else "Conservative spreads",
                "timeframe": "15min-1H" if reasoning["signal_strength"] == "HIGH" else "1H-4H",
                "position_size": "Full" if reasoning["signal_strength"] == "HIGH" else "Half"
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating signal reasoning: {e}")
        return {
            "error": str(e),
            "reasoning": {
                "signal_strength": "UNKNOWN",
                "primary_driver": "ERROR",
                "message": "Could not analyze signal reasoning"
            }
        }


@app.post("/options/refresh-signal-prices")
async def refresh_signal_prices(signals: dict):
    """
    Refresh option prices in trading signals with real-time quotes
    """
    try:
        updated_signals = []
        
        for signal in signals.get("signals", []):
            try:
                option_data = signal.get("option", {})
                strike = option_data.get("strike")
                option_type = "call" if option_data.get("type") == "CE" else "put"
                
                if strike:
                    # Get fresh quote
                    quote = await get_option_quote(
                        index=signals.get("index", "NIFTY"),
                        strike=strike,
                        option_type=option_type
                    )
                    
                    if not quote.get("error") and quote.get("ltp", 0) > 0:
                        # Update signal with fresh price
                        signal["entry"]["price"] = quote["ltp"]
                        signal["entry"]["bid"] = quote.get("bid", 0)
                        signal["entry"]["ask"] = quote.get("ask", 0)
                        signal["entry"]["spread"] = quote.get("spread", 0)
                        signal["entry"]["last_updated"] = quote["updated_at"]
                        
                        # Recalculate targets based on fresh price
                        fresh_price = quote["ltp"]
                        signal["targets"]["target_1"] = fresh_price * 1.3
                        signal["targets"]["target_2"] = fresh_price * 1.8
                        signal["targets"]["stop_loss"] = fresh_price * 0.75
                        
                updated_signals.append(signal)
                        
            except Exception as e:
                logger.error(f"Error updating signal prices: {e}")
                updated_signals.append(signal)  # Keep original on error
        
        return {
            "updated_signals": updated_signals,
            "refresh_time": datetime.now().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error in refresh_signal_prices: {e}")
        return {"error": str(e)}


# ============================================================================
# STOCK SCREENER ENDPOINTS
# ============================================================================

@app.get("/screener/scan")
async def scan_stocks(
    limit: int = Query(50, description="Number of stocks to scan (faster with lower numbers)"),
    min_confidence: float = Query(60.0, description="Minimum confidence level (0-100)"),
    randomize: bool = Query(True, description="Randomly sample stocks for variety"),
    authorization: str = Query(..., description="Bearer token (required)"),
):
    """
    Scan NSE stocks for high-confidence trading signals (Authentication Required)
    
    Args:
        limit: Number of stocks to scan (default 50, max recommended 200)
        min_confidence: Minimum confidence threshold (default 60%)
        randomize: Random sampling for variety (recommended True)
        authorization: Auth token (required) - results automatically saved to your account
        
    Returns:
        List of stocks with BUY/SELL signals meeting confidence criteria
    """
    try:
        # Authenticate user first
        token = authorization.replace("Bearer ", "")
        user = await auth_service.get_current_user(token)
        
        logger.info(f"Stock screener scan requested by {user.email}: limit={limit}, min_confidence={min_confidence}, randomize={randomize}")
        
        # Get screener instance
        screener = get_stock_screener(fyers_client)
        
        # Run scan
        signals = screener.scan_stocks(limit=limit, min_confidence=min_confidence, randomize=randomize)
        
        # Separate buy and sell signals
        buy_signals = [s for s in signals if s["action"] == "BUY"]
        sell_signals = [s for s in signals if s["action"] == "SELL"]
        
        result = {
            "status": "success",
            "scan_time": datetime.now().isoformat(),
            "stocks_scanned": limit,
            "min_confidence": min_confidence,
            "randomized": randomize,
            "total_signals": len(signals),
            "buy_signals": len(buy_signals),
            "sell_signals": len(sell_signals),
            "signals": {
                "buy": buy_signals,
                "sell": sell_signals
            },
            "top_picks": signals[:5]  # Top 5 highest confidence
        }
        
        # Save to database (user is already authenticated)
        try:
            scan_info = await screener_service.save_scan_results(
                user_id=user.id,
                scan_data=result,
                signals=result["signals"]
            )
            
            result["saved"] = True
            result["scan_id"] = scan_info["scan_id"]
            result["user_email"] = user.email
            logger.info(f"Saved scan results for user {user.email}")
        except Exception as e:
            logger.warning(f"Failed to save scan results: {e}")
            result["saved"] = False
        
        return result
        
    except Exception as e:
        logger.error(f"Error in stock screener: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/screener/stock/{symbol}")
async def analyze_single_stock(symbol: str, debug: bool = False):
    """
    Analyze a single stock for trading signals
    
    Args:
        symbol: Stock symbol (e.g., "TATAMOTORS" or "NSE:TATAMOTORS-EQ")
        debug: If True, return raw scoring data even if no signal
        
    Returns:
        Detailed signal analysis for the stock
    """
    try:
        # Format symbol
        if not symbol.startswith("NSE:"):
            symbol = f"NSE:{symbol}-EQ"
        
        logger.info(f"Analyzing single stock: {symbol}")
        
        # Get screener instance
        screener = get_stock_screener(fyers_client)
        
        # Analyze stock
        signal = screener.analyze_stock(symbol)
        
        if signal is None:
            # In debug mode, try to get raw scores
            if debug:
                try:
                    from datetime import datetime, timedelta
                    import pandas as pd
                    
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=30)
                    df = fyers_client.get_historical_data(symbol, "D", start_date, end_date)
                    
                    if df is not None and not df.empty:
                        # Calculate indicators
                        df['sma_5'] = df['close'].rolling(5).mean()
                        df['sma_10'] = df['close'].rolling(10).mean()
                        df['sma_20'] = df['close'].rolling(20).mean()
                        
                        delta = df['close'].diff()
                        gain = delta.where(delta > 0, 0).rolling(14).mean()
                        loss = -delta.where(delta < 0, 0).rolling(14).mean()
                        rs = gain / loss
                        df['rsi'] = 100 - (100 / (1 + rs))
                        
                        return {
                            "status": "debug",
                            "symbol": symbol,
                            "current_price": float(df['close'].iloc[-1]),
                            "sma_5": float(df['sma_5'].iloc[-1]) if not pd.isna(df['sma_5'].iloc[-1]) else None,
                            "sma_10": float(df['sma_10'].iloc[-1]) if not pd.isna(df['sma_10'].iloc[-1]) else None,
                            "sma_20": float(df['sma_20'].iloc[-1]) if not pd.isna(df['sma_20'].iloc[-1]) else None,
                            "rsi": float(df['rsi'].iloc[-1]) if not pd.isna(df['rsi'].iloc[-1]) else None,
                            "message": "No signal generated - scores below threshold (20 points)"
                        }
                except Exception as e:
                    pass
            
            return {
                "status": "no_signal",
                "symbol": symbol,
                "message": "No clear trading signal found or insufficient data"
            }
        
        return {
            "status": "success",
            "signal": signal
        }
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/screener/latest")
async def get_latest_scan(authorization: str = Query(..., description="Bearer token")):
    """Get latest saved scan results for user"""
    try:
        token = authorization.replace("Bearer ", "")
        user = await auth_service.get_current_user(token)
        
        latest_scan = await screener_service.get_latest_scan(user.id)
        
        if not latest_scan:
            return {
                "status": "no_data",
                "message": "No saved scans found"
            }
        
        return {
            "status": "success",
            **latest_scan
        }
        
    except Exception as e:
        logger.error(f"Error getting latest scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/screener/history")
async def get_scan_history(
    authorization: str = Query(..., description="Bearer token"),
    limit: int = Query(10, description="Number of scans to retrieve")
):
    """Get scan history for user"""
    try:
        token = authorization.replace("Bearer ", "")
        user = await auth_service.get_current_user(token)
        
        history = await screener_service.get_scan_history(user.id, limit)
        
        return {
            "status": "success",
            "scans": history
        }
        
    except Exception as e:
        logger.error(f"Error getting scan history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/screener/categories")
async def get_stock_categories():
    """Get available scan options and confidence level descriptions"""
    return {
        "scan_options": {
            "limit": {
                "description": "Number of stocks to scan",
                "recommended": 50,
                "range": "20-200",
                "notes": "Lower = faster scan, Higher = more comprehensive"
            },
            "randomize": {
                "description": "Random sampling for variety",
                "recommended": True,
                "notes": "Get different stocks each scan for broader coverage"
            }
        },
        "confidence_levels": {
            "60-70": "MODERATE - Consider with caution",
            "70-80": "HIGH - Good setup",
            "80-95": "VERY HIGH - Strong signal"
        },
        "total_stocks": "500+ NSE equity stocks",
        "sectors": [
            "Banking & Finance", "IT & Software", "Auto & Components",
            "Pharma & Healthcare", "Oil & Gas", "Metals & Mining",
            "Cement", "Power", "Telecom", "Consumer Goods",
            "Retail", "Real Estate", "Hotels", "Media", "Chemicals",
            "Textiles", "Engineering", "Diversified"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug_mode
    )


