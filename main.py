"""
FastAPI Backend for TradeWise
REST API endpoints for trading signals, analysis, and order management
"""
from fastapi import FastAPI, HTTPException, Query, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta, date, timezone, time
import pandas as pd
import logging
import os
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import settings
from src.api.fyers_client import fyers_client
from src.analytics.options_pricing import options_pricer
from src.analytics.ict_analysis import ict_analyzer
from src.analytics.stock_screener import get_stock_screener
from src.trading.signal_generator import signal_generator, risk_manager
from src.services.auth_service import auth_service
from src.services.screener_service import screener_service
from src.models.auth_models import UserRegister, UserLogin, FyersTokenStore

# News sentiment service for market analysis
try:
    from src.services.news_service import news_service, MarketauxNewsService
    NEWS_SERVICE_AVAILABLE = True
except ImportError as e:
    NEWS_SERVICE_AVAILABLE = False
    news_service = None
    logging.warning(f"News service not available: {e}")

# IST timezone utilities for consistent time handling across geographies
from src.utils.ist_utils import now_ist, get_ist_time, ist_timestamp, is_market_open, get_session_info as get_ist_session_info

# Configure logging (must be before ML imports)
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional ML imports (not required for production API)
try:
    from src.ml.price_prediction import price_predictor
    from src.ml.time_series_models import ensemble_predictor, get_ml_signal
    ML_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ML libraries not available: {e}. ML prediction endpoints will be disabled.")
    price_predictor = None
    ensemble_predictor = None
    get_ml_signal = None
    ML_AVAILABLE = False

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

# Initialize background scheduler
scheduler = AsyncIOScheduler()

# Storage for latest scan results (in-memory cache)
latest_scan_results = {
    "NIFTY": None,
    "BANKNIFTY": None,
    "FINNIFTY": None
}


async def auto_scan_options():
    """Background task to automatically scan options every 16 minutes"""
    try:
        logger.info("🔄 Auto-scan: Starting scheduled options scan...")
        
        indices = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
        
        for index in indices:
            try:
                logger.info(f"📊 Auto-scan: Scanning {index}...")
                
                # Check if we have a valid Fyers token
                if not fyers_client.access_token:
                    logger.warning(f"⚠️ Auto-scan: No Fyers token available, skipping {index}")
                    continue
                
                # Import the analyzer
                from src.analytics.index_options import get_index_analyzer
                
                # Get option chain data
                analyzer = get_index_analyzer(fyers_client)
                chain = analyzer.analyze_option_chain(index, "weekly")
                
                if not chain:
                    logger.warning(f"⚠️ Auto-scan: No chain data for {index}")
                    continue
                
                # Process options for scanning (using default filters)
                scanned_options = process_options_scan(
                    chain, 
                    min_volume=1000, 
                    min_oi=10000, 
                    strategy="all"
                )
                
                # Store results
                latest_scan_results[index] = {
                    "scan_time": datetime.now().isoformat(),
                    "index": index,
                    "spot_price": chain.spot_price,
                    "atm_strike": chain.atm_strike,
                    "days_to_expiry": chain.days_to_expiry,
                    "total_options": len(scanned_options),
                    "top_opportunities": scanned_options[:10],  # Top 10
                    "data_source": "live"
                }
                
                logger.info(f"✅ Auto-scan: {index} completed - {len(scanned_options)} options found")
                
                # Log top 3 opportunities
                if scanned_options:
                    logger.info(f"🎯 {index} Top 3:")
                    for i, opt in enumerate(scanned_options[:3], 1):
                        logger.info(f"   {i}. {opt['type']} {opt['strike']} - Score: {opt['score']:.0f}, LTP: ₹{opt['ltp']:.2f}")
                        
            except Exception as e:
                logger.error(f"❌ Auto-scan error for {index}: {e}")
                continue
        
        logger.info("✅ Auto-scan: Completed all indices")
        
    except Exception as e:
        logger.error(f"❌ Auto-scan: Critical error: {e}")


async def fetch_market_news():
    """
    Background task to fetch news from Marketaux API every 15 minutes.
    Stores news in Supabase for sentiment analysis.
    
    Rate limits:
    - 100 requests/day
    - 3 articles per request
    - Fetch every 15 minutes = ~96 requests/day (safe margin)
    """
    if not NEWS_SERVICE_AVAILABLE or not news_service:
        logger.warning("⚠️ News service not available, skipping news fetch")
        return
    
    try:
        logger.info("📰 Starting scheduled news fetch from Marketaux...")
        
        # Check if market hours (only fetch during trading hours to save API quota)
        # Indian market: 9:15 AM - 3:30 PM IST
        current_hour = now_ist().hour
        
        # Fetch during extended hours: 8 AM - 6 PM IST
        if 8 <= current_hour <= 18:
            articles_stored = await news_service.fetch_and_store_news()
            logger.info(f"✅ News fetch complete: {articles_stored} articles stored")
        else:
            logger.info("💤 Outside market hours, skipping news fetch to save API quota")
        
    except Exception as e:
        logger.error(f"❌ News fetch error: {e}")
        import traceback
        logger.error(traceback.format_exc())


# Startup event to load Fyers token from Supabase and start scheduler
@app.on_event("startup")
async def load_fyers_token_from_db():
    """Load any valid Fyers token from Supabase on startup"""
    try:
        from config.supabase_config import supabase_admin

        # Use admin client (service role key) to bypass RLS
        supabase = supabase_admin

        logger.info(f"🔍 Attempting to load Fyers tokens from database...")
        
        # Get any non-expired token from the database
        response = supabase.table("fyers_tokens").select("*").execute()
        
        logger.info(f"📊 Database response: {len(response.data) if response.data else 0} tokens found")
        
        if response.data:
            # Debug: Print all tokens
            for i, token in enumerate(response.data):
                logger.info(f"Token {i+1}: user={token.get('user_id', '')[:8]}..., expires_at={token.get('expires_at')}, has_token={bool(token.get('access_token'))}")
            
            # Find the most recently updated token
            tokens = sorted(response.data, key=lambda x: x.get("updated_at", ""), reverse=True)
            
            for token_data in tokens:
                access_token = token_data.get("access_token")
                logger.info(f"🎯 Checking token for user {token_data.get('user_id', '')[:8]}...")
                
                if not access_token:
                    logger.warning(f"⚠️ Token found but access_token field is empty")
                    continue
                
                # Check if token is not expired
                expires_at = token_data.get("expires_at")
                logger.info(f"🕐 Checking expiry: {expires_at}")
                
                if expires_at:
                    try:
                        # Handle different datetime formats
                        if expires_at.endswith('+00'):
                            expiry_time = datetime.fromisoformat(expires_at.replace('+00', '+00:00'))
                        else:
                            expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        
                        current_time = datetime.now(timezone.utc)
                        logger.info(f"🕐 Expiry: {expiry_time}, Current: {current_time}")
                        
                        if expiry_time > current_time:
                            # Token is still valid, use it
                            fyers_client.access_token = access_token
                            fyers_client._initialize_client()
                            logger.info(f"✅ Loaded VALID Fyers token from database (user: {token_data.get('user_id', '')[:8]}..., expires: {expiry_time})")
                            return
                        else:
                            time_expired = current_time - expiry_time
                            logger.warning(f"⚠️ Token expired {time_expired} ago at {expires_at}")
                            continue
                    except Exception as date_error:
                        logger.warning(f"⚠️ Error parsing expiry date '{expires_at}': {date_error}")
                        # If we can't parse expiry, use the token anyway
                        fyers_client.access_token = access_token
                        fyers_client._initialize_client()
                        logger.info(f"✅ Loaded Fyers token from database with unparseable expiry (user: {token_data.get('user_id', '')[:8]}...)")
                        return
                else:
                    # No expiry time, use the token anyway
                    logger.info(f"ℹ️ No expiry field found, using token anyway")
                    fyers_client.access_token = access_token
                    fyers_client._initialize_client()
                    logger.info(f"✅ Loaded Fyers token from database with no expiry (user: {token_data.get('user_id', '')[:8]}...)")
                    return
        else:
            logger.warning("⚠️ No token data found in database response")
        
        # Try fallback token from environment if database lookup failed
        if settings.fallback_auth_token and settings.fallback_user_id:
            logger.info("🔄 Trying fallback authentication token from environment...")
            fyers_client.access_token = settings.fallback_auth_token
            fyers_client._initialize_client()
            logger.info(f"✅ Using fallback Fyers token for user {settings.fallback_user_id[:8]}...")
            return
        
    except Exception as e:
        logger.error(f"❌ Error loading Fyers token from database: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Auto options scanner has been disabled
    # The scan is now only triggered on-demand from the frontend
    logger.info("ℹ️ Auto options scanner disabled - scans are on-demand only")
    
    # Start news fetch scheduler (every 15 minutes)
    if NEWS_SERVICE_AVAILABLE and news_service:
        try:
            # Add news fetch job - runs every 15 minutes
            scheduler.add_job(
                fetch_market_news,
                IntervalTrigger(minutes=15),
                id="news_fetch_job",
                name="Fetch Market News from Marketaux",
                replace_existing=True
            )
            
            # Start the scheduler if not already running
            if not scheduler.running:
                scheduler.start()
                logger.info("✅ Background scheduler started")
            
            logger.info("📰 News fetch scheduler configured - will fetch every 15 minutes")
            
            # Fetch news immediately on startup
            logger.info("📰 Fetching initial news on startup...")
            await fetch_market_news()
            
        except Exception as sched_error:
            logger.error(f"❌ Error setting up news scheduler: {sched_error}")
    else:
        logger.warning("⚠️ News service not available - MARKETAUX_API_KEY may not be set")


@app.on_event("shutdown")
async def shutdown_scheduler():
    """Shutdown the background scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("✅ Background scheduler stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {e}")
        logger.warning("⚠️ No valid Fyers tokens found in database or environment. Using mock data until authenticated.")
    except Exception as e:
        logger.warning(f"⚠️ Could not load Fyers token from database: {e}")
        
        # Try fallback token from environment
        if settings.fallback_auth_token and settings.fallback_user_id:
            logger.info("🔄 Using fallback authentication token from environment...")
            try:
                fyers_client.access_token = settings.fallback_auth_token
                fyers_client._initialize_client()
                logger.info(f"✅ Successfully loaded fallback Fyers token for user {settings.fallback_user_id[:8]}...")
                return
            except Exception as fallback_error:
                logger.error(f"❌ Failed to use fallback token: {fallback_error}")
        
        logger.warning("⚠️ Using mock data until authenticated.")


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


@app.get("/index-analyzer.html")
async def index_analyzer_page():
    """Serve the index probability analyzer page"""
    return FileResponse(os.path.join(static_dir, "index-analyzer.html"))


@app.get("/fyers-callback.html")
async def fyers_callback_page():
    """Serve the Fyers OAuth callback page"""
    return FileResponse(os.path.join(static_dir, "fyers-callback.html"))


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
@app.get("/auth/callback")
async def fyers_callback_get(
    auth_code: str = Query(..., description="Authorization code from Fyers"),
    state: str = Query(None, description="State parameter"),
    authorization: str = Header(None, description="Bearer token (required)")
):
    """Handle Fyers OAuth callback via GET (legacy)"""
    return await process_fyers_callback(auth_code, state, authorization)

@app.post("/auth/callback") 
async def fyers_callback_post(
    callback_data: dict,
    authorization: str = Header(None, description="Bearer token (required)")
):
    """Handle Fyers OAuth callback via POST"""
    try:
        auth_code = callback_data.get("auth_code")
        state = callback_data.get("state")
        
        if not auth_code:
            raise HTTPException(status_code=400, detail="Missing auth_code")
            
        return await process_fyers_callback(auth_code, state, authorization)
        
    except HTTPException as e:
        # Re-raise HTTP exceptions as-is to avoid double-wrapping
        raise e
    except Exception as e:
        logger.error(f"Fyers callback POST error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

async def process_fyers_callback(auth_code: str, state: str, authorization: str):
    """Common callback processing logic"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authentication required - please login first")
        
        token = authorization.replace("Bearer ", "")
        
        try:
            user = await auth_service.get_current_user(token)
        except HTTPException as e:
            if e.status_code == 401:
                # Supabase authentication failed - redirect to login
                raise HTTPException(
                    status_code=401, 
                    detail="Your TradeWise session has expired. Please login again."
                )
            else:
                raise e
        
        logger.info(f"Processing Fyers callback for user {user.email} with auth_code: {auth_code[:20]}...")
        
        # Exchange auth code for access token
        success = fyers_client.set_access_token(auth_code)
        if not success:
            logger.error("Failed to exchange authorization code")
            raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        
        logger.info(f"✅ Successfully obtained Fyers access token")
        
        # Calculate expiry (Fyers tokens typically last 24 hours)
        expires_at = datetime.now() + timedelta(hours=24)
        
        # Store token in database
        fyers_token_data = FyersTokenStore(
            access_token=fyers_client.access_token,
            expires_at=expires_at
        )
        
        await auth_service.store_fyers_token(user.id, fyers_token_data)
        logger.info(f"✅ Stored Fyers token in database for user {user.email}")
        
        # Get profile to verify token works
        profile = fyers_client.get_profile()
        logger.info(f"✅ Verified Fyers profile: {profile.get('display_name', 'Unknown')}")
        
        return {
            "status": "success",
            "message": "Fyers authentication successful",
            "profile": profile,
            "redirect": "/screener"
        }
        
    except Exception as e:
        logger.error(f"Fyers callback error: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@app.get("/auth/callback-redirect")
async def fyers_callback_redirect(
    auth_code: str = Query(..., description="Authorization code from Fyers"),
    state: str = Query(None, description="State parameter"),
    request: Request = None
):
    """Handle Fyers OAuth callback redirect (without auth token) and redirect to login"""
    try:
        # Determine if we're on the new frontend (Vercel) or old frontend (static)
        # Check if the request comes from Vercel or stocxer.in (new frontend)
        origin = request.headers.get('origin', '') if request else ''
        referer = request.headers.get('referer', '') if request else ''
        
        # Use /login for new frontend, /login.html for old frontend
        if 'vercel' in origin or 'vercel' in referer or 'stocxer.in' in origin or 'stocxer.in' in referer:
            redirect_url = f"/login?fyers_auth_code={auth_code}&state={state or ''}&message=Please login to complete Fyers authentication"
        else:
            redirect_url = f"/login.html?fyers_auth_code={auth_code}&state={state or ''}&message=Please login to complete Fyers authentication"
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Fyers callback redirect error: {e}")
        # Redirect to login with error message
        return RedirectResponse(url=f"/login?error=Authentication failed: {str(e)}", status_code=302)

@app.get("/auth/url")
async def get_auth_url():
    """Get Fyers authentication URL"""
    try:
        # Refresh settings to get latest ngrok URL
        fyers_client.refresh_settings()
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
async def get_fyers_token(authorization: str = Header(None, description="Bearer token")):
    """Get stored Fyers token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.replace("Bearer ", "")
    user = await auth_service.get_current_user(token)
    fyers_token = await auth_service.get_fyers_token(user.id)
    if not fyers_token:
        raise HTTPException(status_code=404, detail="No Fyers token found. Please connect your Fyers account.")
    return fyers_token


@app.delete("/api/fyers/token")
async def delete_fyers_token(authorization: str = Header(None, description="Bearer token")):
    """Delete stored Fyers token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.replace("Bearer ", "")
    user = await auth_service.get_current_user(token)
    return await auth_service.delete_fyers_token(user.id)


@app.post("/api/fyers/refresh-token")
async def refresh_fyers_token_from_db():
    """Manually refresh Fyers client with latest token from database"""
    try:
        from supabase import create_client
        supabase = create_client(settings.supabase_url, settings.supabase_key)
        
        # Get the most recent token
        response = supabase.table("fyers_tokens").select("*").order("updated_at", desc=True).limit(1).execute()
        
        if response.data:
            token_data = response.data[0]
            access_token = token_data.get("access_token")
            
            # Check expiry
            expires_at = token_data.get("expires_at")
            if expires_at:
                expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if expiry_time < datetime.now(timezone.utc):
                    return {"status": "error", "message": "Token expired", "expires_at": expires_at}
            
            # Update Fyers client
            fyers_client.access_token = access_token
            fyers_client._initialize_client()
            
            return {
                "status": "success",
                "message": "Fyers token refreshed from database",
                "user_id": token_data.get("user_id")[:8] + "...",
                "updated_at": token_data.get("updated_at")
            }
        else:
            return {"status": "error", "message": "No tokens found in database"}
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# News & Sentiment Analysis Endpoints
# ============================================

@app.get("/api/news")
async def get_market_news(
    hours: int = Query(4, description="Hours of news to fetch (1-24)"),
    indices: Optional[str] = Query(None, description="Comma-separated indices (NIFTY,BANKNIFTY,FINNIFTY)"),
    sectors: Optional[str] = Query(None, description="Comma-separated sectors"),
    limit: int = Query(20, description="Maximum articles to return")
):
    """
    Get recent market news from database.
    News is fetched from Marketaux API every 15 minutes and stored in Supabase.
    """
    if not NEWS_SERVICE_AVAILABLE or not news_service:
        raise HTTPException(status_code=503, detail="News service not available. MARKETAUX_API_KEY may not be set.")
    
    try:
        # Parse filters
        index_list = [i.strip().upper() for i in indices.split(",")] if indices else None
        sector_list = [s.strip().lower() for s in sectors.split(",")] if sectors else None
        
        # Fetch from database
        articles = await news_service.get_recent_news(
            hours=min(hours, 24),
            indices=index_list,
            sectors=sector_list,
            min_relevance=0.1,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(articles),
            "hours": hours,
            "filters": {
                "indices": index_list,
                "sectors": sector_list
            },
            "articles": articles
        }
        
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sentiment")
async def get_market_sentiment(
    time_window: str = Query("1hr", description="Time window: 15min, 1hr, 4hr, 1day")
):
    """
    Get aggregated market sentiment from cached analysis.
    Sentiment is computed from recent news articles.
    """
    if not NEWS_SERVICE_AVAILABLE or not news_service:
        # Fall back to simulated sentiment
        from src.analytics.news_sentiment import news_analyzer
        sentiment = news_analyzer.analyze_market_sentiment()
        return {
            "success": True,
            "data_source": "simulated",
            "time_window": time_window,
            "overall_sentiment": sentiment.overall_sentiment,
            "sentiment_score": sentiment.sentiment_score,
            "market_mood": sentiment.market_mood,
            "trading_implication": sentiment.trading_implication,
            "bullish_count": sentiment.bullish_count,
            "bearish_count": sentiment.bearish_count,
            "neutral_count": sentiment.neutral_count,
            "key_themes": sentiment.key_themes
        }
    
    try:
        valid_windows = ["15min", "1hr", "4hr", "1day"]
        if time_window not in valid_windows:
            raise HTTPException(status_code=400, detail=f"Invalid time_window. Must be one of: {valid_windows}")
        
        cached = await news_service.get_market_sentiment(time_window)
        
        if not cached:
            return {
                "success": True,
                "data_source": "none",
                "message": "No sentiment data available for this time window. News fetch may be pending.",
                "time_window": time_window
            }
        
        return {
            "success": True,
            "data_source": "real",
            "time_window": time_window,
            "overall_sentiment": cached.get("overall_sentiment"),
            "sentiment_score": cached.get("sentiment_score"),
            "market_mood": cached.get("market_mood"),
            "trading_implication": cached.get("trading_implication"),
            "total_articles": cached.get("total_articles"),
            "positive_count": cached.get("positive_count"),
            "negative_count": cached.get("negative_count"),
            "neutral_count": cached.get("neutral_count"),
            "key_themes": cached.get("key_themes"),
            "sector_sentiment": cached.get("sector_sentiment"),
            "computed_at": cached.get("computed_at"),
            "window_start": cached.get("window_start"),
            "window_end": cached.get("window_end")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sentiment/for-signal")
async def get_sentiment_for_signal(
    symbol: str = Query("NIFTY", description="Trading symbol"),
    signal_type: Optional[str] = Query(None, description="Signal type: BUY, SELL, HOLD")
):
    """
    Get sentiment data specifically for signal enhancement.
    Returns confidence adjustments and signal modifications based on news sentiment.
    """
    from src.analytics.news_sentiment import news_analyzer
    
    try:
        sentiment_data = await news_analyzer.get_sentiment_for_signal(
            symbol=symbol,
            signal_type=signal_type.upper() if signal_type else None
        )
        
        return {
            "success": True,
            "symbol": symbol,
            "signal_type": signal_type,
            **sentiment_data
        }
        
    except Exception as e:
        logger.error(f"Error getting sentiment for signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/news/fetch")
async def trigger_news_fetch():
    """
    Manually trigger a news fetch (for testing/admin).
    Use sparingly due to API rate limits (100/day).
    """
    if not NEWS_SERVICE_AVAILABLE or not news_service:
        raise HTTPException(status_code=503, detail="News service not available")
    
    try:
        articles_stored = await news_service.fetch_and_store_news()
        return {
            "success": True,
            "message": f"News fetch completed. {articles_stored} articles stored.",
            "articles_stored": articles_stored
        }
    except Exception as e:
        logger.error(f"Error in manual news fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/status")
async def get_news_service_status():
    """Get status of news service and API usage"""
    if not NEWS_SERVICE_AVAILABLE or not news_service:
        return {
            "success": False,
            "available": False,
            "reason": "News service not available. MARKETAUX_API_KEY may not be set."
        }
    
    try:
        # Get latest fetch log
        from config.supabase_config import get_supabase_admin_client
        supabase = get_supabase_admin_client()
        
        response = supabase.table("news_fetch_log").select("*").order(
            "fetch_time", desc=True
        ).limit(5).execute()
        
        fetch_logs = response.data or []
        
        # Count today's requests
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_response = supabase.table("news_fetch_log").select("id").gte(
            "fetch_time", today_start.isoformat()
        ).execute()
        
        requests_today = len(today_response.data) if today_response.data else 0
        
        # Get article count
        articles_response = supabase.table("market_news").select("id", count="exact").execute()
        total_articles = articles_response.count if hasattr(articles_response, 'count') else len(articles_response.data or [])
        
        return {
            "success": True,
            "available": True,
            "requests_today": requests_today,
            "daily_limit": 100,
            "requests_remaining": max(0, 100 - requests_today),
            "total_articles_stored": total_articles,
            "scheduler_running": scheduler.running if scheduler else False,
            "recent_fetches": [
                {
                    "time": log.get("fetch_time"),
                    "articles": log.get("articles_fetched"),
                    "status": log.get("api_response_code"),
                    "error": log.get("error_message")
                }
                for log in fetch_logs
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting news status: {e}")
        return {
            "success": False,
            "available": True,
            "error": str(e)
        }


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
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="ML features not available. Install ML dependencies: pip install scikit-learn xgboost statsmodels"
        )
    
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
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="ML features not available. Install ML dependencies: pip install scikit-learn xgboost statsmodels"
        )
    
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
    expiry: str = Query("weekly", description="weekly or monthly"),
    authorization: str = Header(None, description="Bearer token for authenticated access")
):
    """Get complete option chain analysis"""
    try:
        # Try to load user's Fyers token if authorization provided
        if authorization:
            try:
                token = authorization.replace("Bearer ", "")
                user = await auth_service.get_current_user(token)
                fyers_token = await auth_service.get_fyers_token(user.id)
                
                if fyers_token and fyers_token.access_token:
                    # Check expiry
                    now = datetime.now()
                    if fyers_token.expires_at:
                        if fyers_token.expires_at.tzinfo is not None:
                            now = now.replace(tzinfo=timezone.utc)
                        if fyers_token.expires_at > now:
                            # Token is valid, use it
                            fyers_client.access_token = fyers_token.access_token
                            fyers_client._initialize_client()
                            logger.info(f"✅ Using Fyers token from DB for user {user.email}")
            except Exception as auth_error:
                logger.debug(f"Auth check skipped: {auth_error}")
        
        analyzer = get_index_analyzer(fyers_client)
        
        try:
            chain = analyzer.analyze_option_chain(index.upper(), expiry)
            
            if not chain:
                # Return mock data instead of raising error
                logger.warning("Option chain analysis failed, returning mock data")
                return {
                    "index": index.upper(),
                    "spot_price": 24500.0,
                    "future_price": 24510.0,
                    "basis": 10.0,
                    "basis_pct": 0.04,
                    "vix": 15.0,
                    "pcr_oi": 0.9,
                    "pcr_volume": 0.85,
                    "max_pain": 24500,
                    "atm_strike": 24500,
                    "atm_iv": 18.0,
                    "iv_skew": 2.0,
                    "expiry_date": "2026-01-20",
                    "days_to_expiry": 1,
                    "totals": {
                        "call_oi": 50000000,
                        "put_oi": 45000000,
                        "call_volume": 2000000,
                        "put_volume": 1800000
                    },
                    "levels": {
                        "support": [24400, 24300, 24200],
                        "resistance": [24600, 24700, 24800]
                    },
                    "oi_buildup": [],
                    "strikes": [],
                    "error": "Live data unavailable due to API rate limits. Showing mock data."
                }
        except Exception as chain_error:
            logger.warning(f"Option chain analysis failed: {chain_error}, returning mock data")
            return {
                "index": index.upper(),
                "spot_price": 24500.0,
                "error": "Live data unavailable due to API rate limits. Showing mock data.",
                "strikes": []
            }
        
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
            ],
            # Actual futures data (if available)
            "futures_data": {
                "symbol": chain.futures_data.symbol,
                "price": chain.futures_data.price,
                "basis": chain.futures_data.basis,
                "basis_pct": chain.futures_data.basis_pct,
                "oi": chain.futures_data.oi,
                "volume": chain.futures_data.volume,
                "oi_change": chain.futures_data.oi_change,
                "oi_analysis": chain.futures_data.oi_analysis,
                "expiry_date": chain.futures_data.expiry_date,
                "days_to_expiry": chain.futures_data.days_to_expiry,
                "next_month_symbol": chain.futures_data.next_month_symbol,
                "next_month_price": chain.futures_data.next_month_price,
                "rollover_cost": chain.futures_data.rollover_cost
            } if chain.futures_data else None
        }
    except Exception as e:
        logger.error(f"Error getting option chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/{index}/signal")
async def get_index_signal(
    index: str,
    authorization: str = Header(None, description="Bearer token for authenticated access")
):
    """
    Generate trading signal using top-down analysis
    
    Analysis Flow:
    1. Market Regime (VIX) → Position sizing
    2. Option Chain → PCR, Max Pain, OI
    3. Signal → Direction + Strategy
    """
    try:
        # Try to load user's Fyers token if authorization provided
        if authorization:
            try:
                token = authorization.replace("Bearer ", "")
                user = await auth_service.get_current_user(token)
                fyers_token = await auth_service.get_fyers_token(user.id)
                
                if fyers_token and fyers_token.access_token:
                    # Check expiry
                    now = datetime.now()
                    if fyers_token.expires_at:
                        if fyers_token.expires_at.tzinfo is not None:
                            now = now.replace(tzinfo=timezone.utc)
                        if fyers_token.expires_at > now:
                            # Token is valid, use it
                            fyers_client.access_token = fyers_token.access_token
                            fyers_client._initialize_client()
                            logger.info(f"✅ Using Fyers token from DB for user {user.email}")
            except Exception as auth_error:
                logger.debug(f"Auth check skipped: {auth_error}")
        
        analyzer = get_index_analyzer(fyers_client)
        signal = analyzer.generate_index_signal(index.upper())
        return signal
    except Exception as e:
        logger.error(f"Error generating index signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/overview")
async def get_all_indices_overview(
    authorization: str = Header(None, description="Bearer token for authenticated access")
):
    """Get quick overview of all supported indices"""
    try:
        # Try to load user's Fyers token if authorization provided
        if authorization:
            try:
                token = authorization.replace("Bearer ", "")
                user = await auth_service.get_current_user(token)
                fyers_token = await auth_service.get_fyers_token(user.id)
                
                if fyers_token and fyers_token.access_token:
                    # Check expiry
                    now = datetime.now()
                    if fyers_token.expires_at:
                        if fyers_token.expires_at.tzinfo is not None:
                            now = now.replace(tzinfo=timezone.utc)
                        if fyers_token.expires_at > now:
                            # Token is valid, use it
                            fyers_client.access_token = fyers_token.access_token
                            fyers_client._initialize_client()
                            logger.info(f"✅ Using Fyers token from DB for user {user.email}")
            except Exception as auth_error:
                logger.debug(f"Auth check skipped: {auth_error}")
        
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
    timeframes: str = Query("M,W,D,240,60", description="Comma-separated timeframes: M,W,D,240,60,15"),
    authorization: str = Header(None, description="Bearer token for authenticated access")
):
    """
    Multi-Timeframe ICT Analysis
    
    Analyzes: Monthly → Weekly → Daily → 4H → 1H → 15min
    Identifies: FVGs, Order Blocks, Liquidity Zones, Market Structure
    """
    try:
        # Try to load user's Fyers token if authorization provided
        if authorization:
            try:
                token = authorization.replace("Bearer ", "")
                user = await auth_service.get_current_user(token)
                fyers_token = await auth_service.get_fyers_token(user.id)
                
                if fyers_token and fyers_token.access_token:
                    # Check expiry
                    now = datetime.now()
                    if fyers_token.expires_at:
                        if fyers_token.expires_at.tzinfo is not None:
                            now = now.replace(tzinfo=timezone.utc)
                        if fyers_token.expires_at > now:
                            # Token is valid, use it
                            fyers_client.access_token = fyers_token.access_token
                            fyers_client._initialize_client()
                            logger.info(f"✅ Using Fyers token from DB for user {user.email}")
            except Exception as auth_error:
                logger.debug(f"Auth check skipped: {auth_error}")
        
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
        
        try:
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
        except Exception as analysis_error:
            # If analysis fails due to rate limiting or other issues, return mock data
            logger.warning(f"MTF analysis failed, returning mock data: {analysis_error}")
            return {
                "symbol": symbol,
                "current_price": 24500.0,
                "timestamp": datetime.now().isoformat(),
                "overall_bias": "neutral",
                "analyses": {},
                "confluence_zones": [],
                "trade_setups": [],
                "error": "Live data unavailable due to API rate limits. Showing mock data."
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
async def get_actionable_trading_signal(
    symbol: str,
    authorization: str = Header(None, description="Bearer token for authenticated access")
):
    """
    Get clear, actionable trading signals with specific strikes, prices, and timing
    
    Returns:
    - Exact option to buy/sell (strike + type)
    - Entry price and trigger levels
    - Target prices and stop loss
    - Best timing for entry
    - Risk/reward ratio
    
    Analysis Flow:
    1. Multi-Timeframe ICT Analysis (Weekly → Daily → 4H → 1H → 15min)
    2. Option Chain Analysis (PCR, Max Pain, OI Distribution)
    3. ML Analysis (ARIMA + LSTM + Momentum)
    4. Signal Generation with confidence scoring
    """
    try:
        # Try to load user's Fyers token if authorization provided
        if authorization:
            try:
                token = authorization.replace("Bearer ", "")
                user = await auth_service.get_current_user(token)
                fyers_token = await auth_service.get_fyers_token(user.id)
                
                if fyers_token and fyers_token.access_token:
                    # Check expiry
                    now = datetime.now()
                    if fyers_token.expires_at:
                        if fyers_token.expires_at.tzinfo is not None:
                            now = now.replace(tzinfo=timezone.utc)
                        if fyers_token.expires_at > now:
                            # Token is valid, use it
                            fyers_client.access_token = fyers_token.access_token
                            fyers_client._initialize_client()
                            logger.info(f"✅ Using Fyers token from DB for user {user.email}")
            except Exception as auth_error:
                logger.debug(f"Auth check skipped: {auth_error}")
        
        # Normalize symbol to full format
        if ':' not in symbol:
            # Short form like "NIFTY" or "BANKNIFTY"
            if symbol.upper() in ['NIFTY', 'NIFTY50']:
                symbol = 'NSE:NIFTY50-INDEX'
            elif symbol.upper() in ['BANKNIFTY', 'NIFTYBANK']:
                symbol = 'NSE:NIFTYBANK-INDEX'
            else:
                symbol = f'NSE:{symbol.upper()}-INDEX'
        
        # Get MTF analysis with FULL ICT TOP-DOWN ANALYSIS
        mtf_analyzer = get_mtf_analyzer(fyers_client)
        from src.analytics.mtf_ict_analysis import Timeframe
        
        # FULL TOP-DOWN ICT ANALYSIS: MONTHLY → Weekly → Daily → 4H → 1H → 15min
        # Monthly is CRITICAL for identifying major trend reversals and liquidity zones
        timeframes = [
            Timeframe.MONTHLY,       # Major trend reversals & liquidity zones
            Timeframe.WEEKLY,        # Higher timeframe bias
            Timeframe.DAILY,         # Daily trend direction
            Timeframe.FOUR_HOUR,     # 4H structure
            Timeframe.ONE_HOUR,      # 1H for setup timing
            Timeframe.FIFTEEN_MIN    # 15min for entry precision
        ]
        logger.info(f"🔍 Performing full MTF ICT analysis: {[tf.value for tf in timeframes]}")
        mtf_result = mtf_analyzer.analyze(symbol, timeframes)
        logger.info(f"✅ MTF Analysis complete - Overall bias: {mtf_result.overall_bias}")
        
        # Log higher timeframe biases for debugging
        for tf_key, tf_analysis in mtf_result.analyses.items():
            logger.info(f"   {tf_key}: {tf_analysis.bias} - {tf_analysis.market_structure.trend}")
        
        # Get current session
        session_info = options_time_analyzer.get_current_session()
        
        # Get option chain data (using index name from symbol)
        index_name = symbol.split(':')[1].replace('NIFTY50', 'NIFTY').replace('NIFTYBANK', 'BANKNIFTY').replace('-INDEX', '')
        
        chain_data = None
        index_data = None  # Store index-specific data for UI
        try:
            # Get analyzed option chain data with LTP prices (pass authorization for token loading)
            chain_res = await get_option_chain_analysis(index_name, "weekly", authorization)
            chain_data = chain_res
            
            # Store index data for UI cards
            index_data = {
                "spot_price": chain_data.get("spot_price"),
                "future_price": chain_data.get("future_price"),
                "basis": chain_data.get("basis"),
                "basis_pct": chain_data.get("basis_pct"),
                "vix": chain_data.get("vix"),
                "pcr_oi": chain_data.get("pcr_oi"),
                "pcr_volume": chain_data.get("pcr_volume"),
                "max_pain": chain_data.get("max_pain"),
                "atm_strike": chain_data.get("atm_strike"),
                "atm_iv": chain_data.get("atm_iv"),
                "iv_skew": chain_data.get("iv_skew"),
                "support_levels": chain_data.get("levels", {}).get("support", []),
                "resistance_levels": chain_data.get("levels", {}).get("resistance", []),
                "total_call_oi": chain_data.get("totals", {}).get("call_oi", 0),
                "total_put_oi": chain_data.get("totals", {}).get("put_oi", 0),
                # Actual futures data
                "futures_data": chain_data.get("futures_data")
            }
            
            # Log futures data if available
            futures = chain_data.get("futures_data")
            if futures:
                logger.info(f"📊 FUTURES: {futures.get('symbol')} @ ₹{futures.get('price')}, Basis: {futures.get('basis_pct')}%, OI Analysis: {futures.get('oi_analysis')}")
            
            logger.info(f"✅ Got option chain data for {index_name}")
            
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
        
        # Fetch historical prices for ML prediction - need 50+ candles for proper ARIMA/LSTM
        historical_prices = None
        try:
            # ML ANALYSIS: Get sufficient historical data for ARIMA + LSTM models
            # ARIMA needs 50+ points minimum, LSTM works best with 200+
            # 
            # FYERS API LIMITS (Important!):
            # - Minute resolutions (1-240 min): Up to 100 days per request
            # - Daily (1D): Up to 366 days per request
            # - Data available from July 3, 2017
            # 
            # To avoid partial candles: range_to should be previous minute
            from datetime import datetime, timedelta
            today = datetime.now()
            # Subtract 1 minute to avoid partial candle
            safe_end_time = today - timedelta(minutes=1)
            
            # Step 1: Try Daily data first (most reliable for ML training)
            # Daily resolution: max 366 days per request
            logger.info("📊 Fetching historical data for ML analysis (respecting Fyers API limits)...")
            start_date_daily = safe_end_time - timedelta(days=365)  # 365 days (within 366 limit)
            
            historical_df = fyers_client.get_historical_data(
                symbol=symbol,
                resolution="D",  # Daily candles
                date_from=start_date_daily,
                date_to=safe_end_time
            )
            
            if historical_df is not None and not historical_df.empty and len(historical_df) >= 50:
                historical_prices = historical_df['close']
                logger.info(f"✅ Got {len(historical_prices)} DAILY candles for ML analysis (ideal for ARIMA/LSTM)")
            else:
                # Step 2: Fallback to hourly data (60-min)
                # Minute resolution: max 100 days per request
                logger.warning("Daily data insufficient, trying hourly (100-day lookback - max allowed)...")
                start_date_hourly = safe_end_time - timedelta(days=100)  # Max 100 days for minute data
                historical_df = fyers_client.get_historical_data(
                    symbol=symbol,
                    resolution="60",  # Hourly (60 min)
                    date_from=start_date_hourly,
                    date_to=safe_end_time
                )
                
                if historical_df is not None and not historical_df.empty and len(historical_df) >= 50:
                    historical_prices = historical_df['close']
                    logger.info(f"✅ Got {len(historical_prices)} HOURLY candles for ML analysis")
                else:
                    # Step 3: Try 4-hour (240 min) for more coverage
                    logger.warning("Hourly data insufficient, trying 4H (100-day lookback)...")
                    start_date_4h = safe_end_time - timedelta(days=100)
                    historical_df = fyers_client.get_historical_data(
                        symbol=symbol,
                        resolution="240",  # 4-hour candles
                        date_from=start_date_4h,
                        date_to=safe_end_time
                    )
                    
                    if historical_df is not None and not historical_df.empty and len(historical_df) >= 50:
                        historical_prices = historical_df['close']
                        logger.info(f"✅ Got {len(historical_prices)} 4H candles for ML analysis")
                    else:
                        # Step 4: Last resort - 15min data (will get ~2400 candles in 100 days)
                        logger.warning("4H data insufficient, trying 15-min (100-day lookback)...")
                        start_date_15min = safe_end_time - timedelta(days=100)
                        historical_df = fyers_client.get_historical_data(
                            symbol=symbol,
                            resolution="15",  # 15-minute candles
                            date_from=start_date_15min,
                            date_to=safe_end_time
                        )
                        
                        if historical_df is not None and not historical_df.empty and len(historical_df) >= 50:
                            historical_prices = historical_df['close']
                            logger.info(f"✅ Got {len(historical_prices)} 15-MIN candles for ML analysis")
                        else:
                            logger.warning(f"⚠️ Insufficient historical data for ML: only {len(historical_df) if historical_df is not None else 0} candles available")
        except Exception as e:
            logger.warning(f"Could not fetch historical data for ML: {e}")
        
        # ==================== INDEX PROBABILITY ANALYSIS ====================
        # Scan ALL constituent stocks to enhance signal with market-wide data
        probability_analysis = None
        constituent_recommendation = None
        
        if INDEX_ANALYSIS_AVAILABLE:
            try:
                logger.info(f"📊 Running constituent stock analysis for {index_name}...")
                prob_analyzer = get_probability_analyzer(fyers_client)
                prediction = prob_analyzer.analyze_index(index_name.upper())
                
                if prediction:
                    # Determine recommendation based on probability
                    if prediction.expected_direction == "BULLISH" and prediction.prob_up > 0.55:
                        constituent_recommendation = "CALL"
                    elif prediction.expected_direction == "BEARISH" and prediction.prob_down > 0.55:
                        constituent_recommendation = "PUT"
                    else:
                        constituent_recommendation = "NEUTRAL"
                    
                    probability_analysis = {
                        "stocks_scanned": prediction.total_stocks_analyzed,
                        "total_stocks": len(index_manager.get_constituents(index_name.upper())) if index_manager else prediction.total_stocks_analyzed,
                        "expected_direction": prediction.expected_direction,
                        "expected_move_pct": round(prediction.expected_move_pct, 2),
                        "confidence": round(prediction.prediction_confidence / 100, 3),  # Convert 0-100 to 0-1
                        "probability_up": round(prediction.prob_up, 3),
                        "probability_down": round(prediction.prob_down, 3),
                        "bullish_stocks": prediction.bullish_stocks,
                        "bearish_stocks": prediction.bearish_stocks,
                        "bullish_pct": round((prediction.bullish_stocks / max(1, prediction.total_stocks_analyzed)) * 100, 1),
                        "bearish_pct": round((prediction.bearish_stocks / max(1, prediction.total_stocks_analyzed)) * 100, 1),
                        "constituent_recommendation": constituent_recommendation,
                        "market_regime": prediction.regime.regime.value if prediction.regime else "unknown",
                        "top_movers": {
                            "bullish": [
                                {"symbol": s.symbol.split(":")[-1].replace("-EQ", ""), "probability": round(s.probability, 2)}
                                for s in sorted(prediction.stock_signals, key=lambda x: x.probability if x.trend_direction == "up" else 0, reverse=True)[:3]
                                if s.trend_direction == "up"
                            ],
                            "bearish": [
                                {"symbol": s.symbol.split(":")[-1].replace("-EQ", ""), "probability": round(s.probability, 2)}
                                for s in sorted(prediction.stock_signals, key=lambda x: x.probability if x.trend_direction == "down" else 0, reverse=True)[:3]
                                if s.trend_direction == "down"
                            ],
                            "volume_surge": [
                                {"symbol": s.symbol.split(":")[-1].replace("-EQ", ""), "has_surge": True}
                                for s in prediction.stock_signals if s.volume_surge
                            ][:3]
                        }
                    }
                    
                    logger.info(f"✅ Constituent analysis: {prediction.expected_direction} ({prediction.prob_up:.1%} up / {prediction.prob_down:.1%} down)")
                    logger.info(f"   Bullish: {prediction.bullish_stocks}, Bearish: {prediction.bearish_stocks}")
                    logger.info(f"   Recommendation from stocks: {constituent_recommendation}")
                    
            except Exception as prob_error:
                logger.warning(f"⚠️ Probability analysis failed: {prob_error}")
        # ====================================================================
        
        # Always generate signal even with minimal data
        # Pass probability analysis to enhance signal generation
        signal = _generate_actionable_signal(mtf_result, session_info, chain_data, historical_prices, probability_analysis)
        
        # Add index data for UI cards (critical for displaying index information)
        if index_data:
            signal["index_data"] = index_data
        else:
            # Create minimal index data from chain_data
            signal["index_data"] = {
                "spot_price": chain_data.get("spot_price") or chain_data.get("future_price"),
                "future_price": chain_data.get("future_price"),
                "vix": chain_data.get("vix", 15),
                "pcr_oi": chain_data.get("pcr_oi", 1.0),
                "max_pain": chain_data.get("max_pain"),
                "atm_iv": chain_data.get("atm_iv", 15),
                "support_levels": [],
                "resistance_levels": []
            }
        
        # Detect trend reversal signals from MTF analysis
        trend_reversal = _detect_trend_reversal(mtf_result)
        
        # Add MTF analysis summary for UI
        signal["mtf_analysis"] = {
            "overall_bias": mtf_result.overall_bias,
            "current_price": mtf_result.current_price,
            "timeframes_analyzed": list(mtf_result.analyses.keys()),
            "confluence_zones": [
                {
                    "center": zone.get("center"),
                    "weight": zone.get("total_weight"),
                    "timeframes": zone.get("timeframes", []),
                    "distance_pct": zone.get("distance_pct")
                }
                for zone in (mtf_result.confluence_zones or [])[:3]
            ],
            "timeframe_biases": {
                tf_key: {
                    "bias": tf_analysis.bias,
                    "trend": tf_analysis.market_structure.trend,
                    "fvg_count": len(tf_analysis.fair_value_gaps),
                    "ob_count": len(tf_analysis.order_blocks),
                    "bos": tf_analysis.market_structure.break_of_structure,
                    "choch": tf_analysis.market_structure.change_of_character
                }
                for tf_key, tf_analysis in mtf_result.analyses.items()
            },
            # TREND REVERSAL DETECTION
            "trend_reversal": trend_reversal
        }
        
        # Add probability analysis to signal if available
        if probability_analysis:
            signal["probability_analysis"] = probability_analysis
            signal["constituent_recommendation"] = constituent_recommendation
        
        # Update signal action if trend reversal is detected
        if trend_reversal["is_reversal"] and trend_reversal["confidence"] >= 60:
            logger.info(f"🔄 TREND REVERSAL DETECTED: {trend_reversal['direction']} - {trend_reversal['reason']}")
        
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
        
        # Save options signal to database for authenticated users
        try:
            if authorization:
                token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
                user = await auth_service.get_current_user(token)
                if user and user.id:
                    # Save the signal
                    save_result = await screener_service.save_options_signal(
                        user_id=str(user.id),
                        signal_data=signal,
                        index=index_name
                    )
                    if save_result.get("saved"):
                        logger.info(f"✅ Options signal saved to database for user {user.email}")
                        signal["saved_to_db"] = True
                        signal["signal_id"] = save_result.get("signal_id")
                    else:
                        logger.warning(f"⚠️ Could not save options signal: {save_result.get('error')}")
        except Exception as save_error:
            logger.warning(f"⚠️ Error saving options signal (non-fatal): {save_error}")
        
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


def _generate_actionable_signal(mtf_result, session_info, chain_data, historical_prices=None, probability_analysis=None):
    """Generate clear trading signal from MTF analysis with full Greeks integration, ML predictions, and constituent stock analysis"""
    
    spot_price = mtf_result.current_price
    overall_bias = mtf_result.overall_bias
    session = session_info.current_session
    
    # ==================== CONSTITUENT STOCK ANALYSIS ====================
    # Use probability analysis to enhance signal confidence
    constituent_boost = 0
    constituent_direction = 'neutral'
    
    if probability_analysis and not probability_analysis.get('error'):
        constituent_direction = probability_analysis.get('expected_direction', 'NEUTRAL').lower()
        prob_confidence = probability_analysis.get('confidence', 0)
        
        # Boost signal if constituent analysis aligns with overall bias
        if constituent_direction == overall_bias:
            constituent_boost = min(15, prob_confidence * 0.2)  # Up to 15% boost
            logger.info(f"🎯 Constituent analysis ALIGNS with bias: +{constituent_boost:.1f}% confidence boost")
        elif constituent_direction != 'neutral' and overall_bias != 'neutral':
            # Reduce confidence if conflicting signals
            constituent_boost = -5
            logger.info(f"⚠️ Constituent analysis CONFLICTS with bias: {constituent_boost}% confidence penalty")
        
        logger.info(f"📊 Constituent direction: {constituent_direction}, Overall bias: {overall_bias}")
    # ================================================================
    
    # ==================== FUTURES SENTIMENT ANALYSIS ====================
    # Use futures basis to boost signal confidence
    futures_boost = 0
    futures_sentiment = 'neutral'
    
    # Get futures data from chain_data if available
    futures_data = chain_data.get("futures_data") if chain_data else None
    if futures_data:
        basis_pct = futures_data.get("basis_pct", 0)
        futures_oi_analysis = futures_data.get("oi_analysis", "")
        
        # Analyze basis for sentiment
        # Premium > 0.3%: Bullish (institutions buying futures)
        # Discount < -0.1%: Bearish (institutions selling futures)
        if basis_pct > 0.3:
            futures_sentiment = 'bullish'
            if overall_bias == 'bullish':
                futures_boost = min(8, basis_pct * 15)  # Up to 8% boost
                logger.info(f"📈 FUTURES BULLISH: Basis {basis_pct:.3f}% → +{futures_boost:.1f}% confidence")
            elif overall_bias == 'bearish':
                futures_boost = -3  # Penalty for conflicting signal
                logger.info(f"⚠️ FUTURES CONFLICTS: Bullish basis vs bearish bias → {futures_boost}%")
        elif basis_pct < -0.1:
            futures_sentiment = 'bearish'
            if overall_bias == 'bearish':
                futures_boost = min(8, abs(basis_pct) * 15)  # Up to 8% boost
                logger.info(f"📉 FUTURES BEARISH: Basis {basis_pct:.3f}% → +{futures_boost:.1f}% confidence")
            elif overall_bias == 'bullish':
                futures_boost = -3  # Penalty for conflicting signal
                logger.info(f"⚠️ FUTURES CONFLICTS: Bearish basis vs bullish bias → {futures_boost}%")
        else:
            logger.info(f"📊 FUTURES NEUTRAL: Basis {basis_pct:.3f}% (within normal range)")
        
        # OI analysis can provide additional insight
        if futures_oi_analysis == "Long Build" and overall_bias == 'bullish':
            futures_boost += 2
            logger.info(f"📊 Futures OI: Long Build → additional +2% boost")
        elif futures_oi_analysis == "Short Build" and overall_bias == 'bearish':
            futures_boost += 2
            logger.info(f"📊 Futures OI: Short Build → additional +2% boost")
    # ================================================================
    
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
        # Generate bias-based mock ML predictions when no historical data
        ml_direction = overall_bias if overall_bias != 'neutral' else 'neutral'
        ml_confidence = 0.45 if overall_bias != 'neutral' else 0.35
        predicted_change = 0.3 if ml_direction == 'bullish' else (-0.3 if ml_direction == 'bearish' else 0.0)
        
        ml_signal = {
            'direction': ml_direction,
            'confidence': ml_confidence,
            'predicted_price': spot_price * (1 + predicted_change / 100),
            'price_change_pct': predicted_change,
            'recommendation': f"{'Buy bias' if ml_direction == 'bullish' else ('Sell bias' if ml_direction == 'bearish' else 'Wait')} (bias-based estimate)",
            'arima': {'direction': ml_direction, 'confidence': ml_confidence * 0.9},
            'momentum': {'direction': ml_direction, 'confidence': ml_confidence}
        }
        logger.info(f"🔮 ML Signal (estimated from bias): {ml_direction} (confidence: {ml_confidence:.1%})")
    # ================================================================
    
    # Get expiry and time-related data
    dte = chain_data.get("days_to_expiry", 7)
    time_to_expiry = max(dte / 365.0, 0.001)
    atm_iv = chain_data.get("atm_iv", 15) / 100 if chain_data.get("atm_iv") else 0.15
    
    # Get ATM strike
    atm_strike = chain_data.get("atm_strike", round(spot_price / 50) * 50)
    
    # Find the best FVG setup with 4-hour timeframe priority
    best_setup = None
    setup_timeframe = None
    four_hour_fvg = None  # Track 4H FVG separately
    four_hour_tf = None
    
    # First pass: Look for 4-hour FVG specifically
    for tf, analysis in mtf_result.analyses.items():
        if tf in ['240', 'FOUR_HOUR', '4H']:  # 4-hour timeframe variations
            for fvg in analysis.fair_value_gaps:
                distance_pct = abs(fvg.midpoint - spot_price) / spot_price * 100
                if distance_pct < 2.0 and fvg.status in ['active', 'tested_once']:
                    if not four_hour_fvg or distance_pct < abs(four_hour_fvg.midpoint - spot_price) / spot_price * 100:
                        four_hour_fvg = fvg
                        four_hour_tf = tf
    
    # Second pass: Find best FVG from all timeframes
    for tf, analysis in mtf_result.analyses.items():
        for fvg in analysis.fair_value_gaps:
            distance_pct = abs(fvg.midpoint - spot_price) / spot_price * 100
            
            # Look for FVGs within 2% of current price
            if distance_pct < 2.0 and fvg.status in ['active', 'tested_once']:
                if not best_setup or distance_pct < abs(best_setup.midpoint - spot_price) / spot_price * 100:
                    best_setup = fvg
                    setup_timeframe = tf
    
    # Prefer 4-hour FVG if it exists and is close enough
    if four_hour_fvg:
        distance_4h = abs(four_hour_fvg.midpoint - spot_price) / spot_price * 100
        if distance_4h < 1.5:  # 4H FVG within 1.5% gets priority
            best_setup = four_hour_fvg
            setup_timeframe = four_hour_tf
            logger.info(f"🎯 Using 4H FVG at {four_hour_fvg.midpoint} (distance: {distance_4h:.2f}%)")
    
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
            # NO CLEAR SETUP - but still generate a signal based on overall bias
            # This allows scanning anytime, even outside trading hours
            signal_type = "NO_CLEAR_SETUP"
            
            # Generate signal based on general bias (default to ATM call for neutral)
            if overall_bias == 'bullish':
                action = "WAIT (Bullish bias detected)"
                strike = atm_strike - 50  # Slightly ITM call
                entry_trigger = spot_price + 20
                timing = "Wait for bullish FVG test or breakout confirmation"
            elif overall_bias == 'bearish':
                action = "WAIT (Bearish bias detected)"
                strike = atm_strike + 50  # Slightly ITM put
                entry_trigger = spot_price - 20
                timing = "Wait for bearish FVG test or breakdown confirmation"
            else:
                action = "WAIT (Neutral - range-bound)"
                strike = atm_strike  # ATM for neutral
                entry_trigger = spot_price
                timing = "Wait for clear directional breakout"
            
            # Continue with full signal generation instead of returning early
            # This allows users to see pricing and strategy details even without a setup
    
    # Find option price from chain with robust error handling
    # CRITICAL: This section must properly fetch LIVE prices from the option chain
    option_price = None
    strike_data = None
    price_source = "ESTIMATED"
    
    try:
        strikes = chain_data.get("strikes", [])
        if strikes:
            logger.info(f"🔍 Searching for strike {strike} in {len(strikes)} available strikes")
            logger.info(f"   Sample strike structure: {list(strikes[0].keys()) if strikes else 'empty'}")
            
            # Find exact strike match
            strike_data = next((s for s in strikes if s.get("strike") == strike), None)
            
            if strike_data:
                option_type_key = "call" if "CALL" in action else "put"
                option_data = strike_data.get(option_type_key, {})
                
                # Log available fields for debugging
                logger.info(f"   Option data fields: {list(option_data.keys()) if option_data else 'empty'}")
                
                # Try multiple price fields in order of preference
                # The option chain endpoint returns 'ltp' as the live trading price
                option_price = (option_data.get("ltp") or 
                              option_data.get("ask") or 
                              option_data.get("mid_price") or
                              option_data.get("last_price") or
                              option_data.get("price"))  # Additional fallback
                
                # Ensure price is reasonable (not 0 or negative)
                if option_price and option_price > 0:
                    price_source = "LIVE_CHAIN"
                    logger.info(f"✅ Found LIVE price for {strike} {option_type_key.upper()}: ₹{option_price}")
                    
                    # Extract market depth data
                    strike_iv = option_data.get("iv", chain_data.get("atm_iv", 15))
                    strike_oi = option_data.get("oi", 0)
                    strike_volume = option_data.get("volume", 0)
                    strike_bid = option_data.get("bid", 0)
                    strike_ask = option_data.get("ask", 0)
                    strike_spread = strike_ask - strike_bid if (strike_bid and strike_ask) else 0
                    strike_spread_pct = (strike_spread / option_price * 100) if option_price > 0 else 0
                    
                    logger.info(f"   IV: {strike_iv}%, OI: {strike_oi:,}, Vol: {strike_volume:,}")
                    logger.info(f"   Bid: ₹{strike_bid:.2f}, Ask: ₹{strike_ask:.2f}, Spread: ₹{strike_spread:.2f} ({strike_spread_pct:.2f}%)")
                else:
                    option_price = None
                    strike_data = None
                    logger.warning(f"⚠️ Strike {strike} found but price is 0 or missing")
            
            # If exact strike not found, find nearest strike with valid price
            if not option_price and strikes:
                logger.info(f"⚠️ Exact strike {strike} not found or has no price, searching nearest...")
                
                # Sort by distance from desired strike
                strikes_sorted = sorted(strikes, key=lambda x: abs(x.get("strike", 0) - strike))
                
                # Find first strike with valid price
                for candidate_strike in strikes_sorted[:5]:  # Check up to 5 nearest strikes
                    option_type_key = "call" if "CALL" in action else "put"
                    option_data = candidate_strike.get(option_type_key, {})
                    
                    candidate_price = (option_data.get("ltp") or 
                                      option_data.get("ask") or 
                                      option_data.get("mid_price") or
                                      option_data.get("last_price") or
                                      option_data.get("price"))
                    
                    if candidate_price and candidate_price > 0:
                        old_strike = strike
                        strike = candidate_strike.get("strike", strike)
                        strike_data = candidate_strike
                        option_price = candidate_price
                        price_source = "LIVE_CHAIN_NEAREST"
                        logger.info(f"✅ Using nearest strike {strike} (requested {old_strike}), price: ₹{option_price}")
                        break
                
                if not option_price:
                    logger.warning(f"⚠️ Could not find any strike with valid price near {strike}")
    
    except Exception as e:
        logger.error(f"Error finding option price for strike {strike}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # If still no price found, calculate estimated price using Black-Scholes
    if not option_price or option_price <= 0:
        option_price = _estimate_option_price(spot_price, strike, action, chain_data)
        logger.warning(f"Using estimated option price {option_price} for strike {strike}")
    
    # Store current LTP
    current_ltp = option_price
    
    # Analyze trend reversal probability based on FVG setup
    reversal_probability = 0.0
    reversal_confidence = "LOW"
    reversal_direction = "UNKNOWN"  # BULLISH or BEARISH
    
    if best_setup:
        # Determine reversal direction from FVG type
        reversal_direction = "BULLISH" if best_setup.type == 'bullish' else "BEARISH"
        
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
        
        # ==================== CONSTITUENT STOCK BOOST ====================
        # Apply boost/penalty from constituent stock analysis
        if constituent_boost != 0:
            reversal_probability = min(1.0, reversal_probability + (constituent_boost / 100))
            logger.info(f"📊 Adjusted probability with constituent boost: {reversal_probability:.2%}")
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
        # No FVG setup - use overall bias for direction
        if overall_bias == 'bullish':
            reversal_direction = "BULLISH"
        elif overall_bias == 'bearish':
            reversal_direction = "BEARISH"
        else:
            reversal_direction = "NEUTRAL"
    
    # Calculate strategic entry price based on setup and reversal probability
    strategic_entry_price = current_ltp
    entry_reasoning = "Enter at current market price"
    
    # Analyze 4H FVG direction and distance for entry optimization
    moving_towards_4h_fvg = False
    distance_to_4h_fvg_pct = 0
    fvg_direction_msg = ""
    
    if four_hour_fvg and setup_timeframe in ['240', 'FOUR_HOUR', '4H']:
        # Calculate if price is moving towards 4H FVG
        distance_to_4h_fvg_pct = abs(four_hour_fvg.midpoint - spot_price) / spot_price * 100
        
        if four_hour_fvg.type == 'bullish':
            # Bullish FVG: price should move up towards FVG high
            if spot_price < four_hour_fvg.high:
                moving_towards_4h_fvg = True
                fvg_direction_msg = f"📈 Moving towards 4H bullish FVG at {four_hour_fvg.high:.0f} (+{distance_to_4h_fvg_pct:.1f}% away)"
            else:
                fvg_direction_msg = f"✅ Above 4H bullish FVG at {four_hour_fvg.high:.0f}"
        else:
            # Bearish FVG: price should move down towards FVG low
            if spot_price > four_hour_fvg.low:
                moving_towards_4h_fvg = True
                fvg_direction_msg = f"📉 Moving towards 4H bearish FVG at {four_hour_fvg.low:.0f} (-{distance_to_4h_fvg_pct:.1f}% away)"
            else:
                fvg_direction_msg = f"✅ Below 4H bearish FVG at {four_hour_fvg.low:.0f}"
        
        logger.info(fvg_direction_msg)
    
    if best_setup:
        # ==================== MARKET DEPTH ANALYSIS ====================
        # Analyze bid-ask spread and liquidity for execution quality BEFORE entry pricing
        liquidity_score = 100  # Default high score
        execution_quality = "EXCELLENT"
        spread_warning = None
        depth_data = {}
        
        try:
            if strike_data and option_data:
                bid = option_data.get("bid", 0)
                ask = option_data.get("ask", 0)
                spread = ask - bid if (bid and ask) else 0
                spread_pct = (spread / current_ltp * 100) if current_ltp > 0 else 0
                
                oi = option_data.get("oi", 0)
                volume = option_data.get("volume", 0)
                
                # Calculate liquidity score (0-100)
                # Factors: Spread %, OI, Volume
                spread_score = max(0, 100 - (spread_pct * 20))  # Penalize high spreads
                oi_score = min(100, (oi / 10000) * 100) if oi > 0 else 0  # Good if OI > 10k
                volume_score = min(100, (volume / 1000) * 100) if volume > 0 else 0  # Good if Vol > 1k
                
                liquidity_score = (spread_score * 0.5 + oi_score * 0.3 + volume_score * 0.2)
                
                # Determine execution quality
                if liquidity_score >= 80:
                    execution_quality = "EXCELLENT"
                elif liquidity_score >= 60:
                    execution_quality = "GOOD"
                elif liquidity_score >= 40:
                    execution_quality = "FAIR"
                    spread_warning = "⚠️ Moderate liquidity - expect some slippage"
                else:
                    execution_quality = "POOR"
                    spread_warning = "🚨 Low liquidity - high slippage risk. Avoid large positions!"
                
                # Wide spread warning
                if spread_pct > 5:
                    spread_warning = f"🚨 WIDE SPREAD: {spread_pct:.1f}% - execution may be difficult"
                elif spread_pct > 2:
                    spread_warning = f"⚠️ Moderate spread: {spread_pct:.1f}% - use limit orders"
                
                depth_data = {
                    "bid": round(bid, 2),
                    "ask": round(ask, 2),
                    "spread": round(spread, 2),
                    "spread_pct": round(spread_pct, 2),
                    "mid_price": round((bid + ask) / 2, 2) if (bid and ask) else current_ltp,
                    "oi": int(oi),
                    "volume": int(volume),
                    "liquidity_score": round(liquidity_score, 1),
                    "execution_quality": execution_quality,
                    "warning": spread_warning
                }
                
                logger.info(f"💧 Liquidity Score: {liquidity_score:.1f}/100 ({execution_quality})")
                if spread_warning:
                    logger.warning(f"   {spread_warning}")
                    
        except Exception as e:
            logger.warning(f"Could not calculate market depth: {e}")
        # ================================================================
        
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
        # LIQUIDITY ADJUSTMENT: Use mid-price for low liquidity options
        liquidity_adjusted_ltp = current_ltp
        if depth_data and depth_data.get('liquidity_score', 100) < 60:
            # Low liquidity - use mid-price between bid-ask instead of LTP
            mid_price = depth_data.get('mid_price', current_ltp)
            if mid_price > 0 and abs(mid_price - current_ltp) / current_ltp < 0.10:  # Within 10%
                liquidity_adjusted_ltp = mid_price
                entry_reasoning = f"⚠️ Low liquidity - using mid-price ₹{mid_price:.2f} instead of LTP ₹{current_ltp:.2f} | "
                logger.info(f"💧 Liquidity adjustment: LTP ₹{current_ltp:.2f} → Mid ₹{mid_price:.2f}")
        
        # SPECIAL CASE: 4H FVG with directional movement
        if four_hour_fvg and setup_timeframe in ['240', 'FOUR_HOUR', '4H']:
            if moving_towards_4h_fvg:
                # Price is moving towards 4H FVG - adjust entry based on distance
                if distance_to_4h_fvg_pct < 0.5:  # Very close (< 0.5%)
                    strategic_entry_price = round(liquidity_adjusted_ltp * 1.10, 2)  # 10% premium - high urgency
                    entry_reasoning += f"🎯 NEAR 4H FVG ({distance_to_4h_fvg_pct:.1f}% away): Buy aggressively at ₹{liquidity_adjusted_ltp:.2f}, max ₹{strategic_entry_price} (10% premium)"
                elif distance_to_4h_fvg_pct < 1.0:  # Close (< 1%)
                    strategic_entry_price = round(liquidity_adjusted_ltp * 1.05, 2)  # 5% premium
                    entry_reasoning += f"🎯 Approaching 4H FVG ({distance_to_4h_fvg_pct:.1f}% away): Buy at ₹{liquidity_adjusted_ltp:.2f}, max ₹{strategic_entry_price} (5% premium)"
                else:  # Moving towards but still distant
                    strategic_entry_price = round(liquidity_adjusted_ltp * 1.03, 2)  # 3% premium
                    entry_reasoning += f"➡️ Moving to 4H FVG ({distance_to_4h_fvg_pct:.1f}% away): Buy at ₹{liquidity_adjusted_ltp:.2f}, max ₹{strategic_entry_price} (3% premium)"
            else:
                # Already at or past 4H FVG - conservative entry
                strategic_entry_price = round(liquidity_adjusted_ltp * 1.02, 2)  # 2% premium only
                entry_reasoning += f"✅ AT 4H FVG zone: Conservative entry at ₹{liquidity_adjusted_ltp:.2f}, max ₹{strategic_entry_price} (2% premium)"
        
        elif best_setup.status == 'active':
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
    
    # ==================== DISCOUNT ZONE ANALYSIS ====================
    # Deep analysis of whether current price is in a discounted zone
    # This verifies the entry price is optimal, not inflated
    discount_zone_analysis = None
    try:
        # Determine market momentum from overall bias and FVG
        market_momentum = overall_bias if overall_bias in ['bullish', 'bearish'] else 'neutral'
        
        # Get OI analysis from the selected strike if available
        oi_analysis_str = 'neutral'
        if strike_data:
            option_type_key = "call" if "CALL" in action else "put"
            option_data = strike_data.get(option_type_key, {})
            analysis_text = option_data.get("analysis", "").lower()
            if "long build" in analysis_text or "long_build" in analysis_text:
                oi_analysis_str = "long_build"
            elif "short build" in analysis_text or "short_build" in analysis_text:
                oi_analysis_str = "short_build"
            elif "short cover" in analysis_text or "short_cover" in analysis_text:
                oi_analysis_str = "short_cover"
            elif "long unwind" in analysis_text or "long_unwind" in analysis_text:
                oi_analysis_str = "long_unwind"
        
        # Calculate discount zone using the comprehensive function
        discount_zone_analysis = calculate_discount_zone(
            option_ltp=current_ltp,
            spot_price=spot_price,
            strike=strike,
            option_type="CALL" if "CALL" in action else "PUT",
            iv=atm_iv,
            delta=greeks.get('delta', 0.4),
            dte=dte,
            avg_iv=0.15,  # Historical average for NIFTY
            market_momentum=market_momentum,
            oi_analysis=oi_analysis_str
        )
        
        # Log discount zone analysis
        logger.info(f"💰 Discount Zone Analysis: {discount_zone_analysis.get('status', 'unknown').upper()}")
        logger.info(f"   Current: ₹{current_ltp:.2f}, Best Entry: ₹{discount_zone_analysis.get('best_entry_price', current_ltp):.2f}")
        logger.info(f"   {discount_zone_analysis.get('reasoning', '')}")
        
    except Exception as e:
        logger.warning(f"Discount zone calculation failed: {e}")
        discount_zone_analysis = {
            "status": "unknown",
            "current_price": round(current_ltp, 2),
            "best_entry_price": round(current_ltp, 2),
            "max_entry_price": round(current_ltp * 1.05, 2),
            "supports_entry": True,
            "reasoning": "Unable to calculate discount zone"
        }
    # ================================================================
    
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
        # DISCOUNT ZONE ANALYSIS - Deep entry price validation
        "discount_zone": discount_zone_analysis if discount_zone_analysis else {
            "status": "unknown",
            "current_price": round(current_ltp, 2),
            "best_entry_price": round(current_ltp, 2),
            "max_entry_price": round(strategic_entry_price, 2),
            "target_price": round(target_1, 2),
            "expected_pullback_pct": 0.0,
            "time_feasible": True,
            "supports_entry": True,
            "reasoning": "Discount zone analysis pending"
        },
        "market_depth": depth_data if depth_data else {
            "liquidity_score": 50,
            "execution_quality": "UNKNOWN",
            "warning": "Market depth data unavailable"
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
            "best_entry_price": discount_zone_analysis.get('best_entry_price', current_ltp) if discount_zone_analysis else round(current_ltp, 2),
            "max_entry_price": discount_zone_analysis.get('max_entry_price', strategic_entry_price) if discount_zone_analysis else round(strategic_entry_price, 2),
            "trigger_level": round(entry_trigger, 2),
            "timing": timing,
            "reasoning": entry_reasoning,
            "session_advice": session_timing,
            "discount_status": discount_zone_analysis.get('status', 'unknown') if discount_zone_analysis else 'unknown',
            "supports_entry": discount_zone_analysis.get('supports_entry', True) if discount_zone_analysis else True
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
            "fvg_level": best_setup.midpoint if best_setup else spot_price,
            "fvg_status": best_setup.status if best_setup else "no_setup",
            "reasoning": f"Based on {setup_timeframe} {best_setup.type} FVG" if best_setup else f"Based on {overall_bias} bias - awaiting FVG setup",
            "reversal_direction": reversal_direction,
            "reversal_type": f"{reversal_direction} REVERSAL" if reversal_direction != "NEUTRAL" else "NO CLEAR DIRECTION",
            "reversal_probability": round(reversal_probability * 100, 1) if best_setup else (45.0 if overall_bias != 'neutral' else 35.0),
            "confidence_level": reversal_confidence if best_setup else ("MODERATE" if overall_bias != 'neutral' else "LOW"),
            # 4-HOUR FVG ANALYSIS
            "four_hour_fvg": {
                "detected": four_hour_fvg is not None,
                "level": four_hour_fvg.midpoint if four_hour_fvg else None,
                "type": four_hour_fvg.type if four_hour_fvg else None,
                "high": four_hour_fvg.high if four_hour_fvg else None,
                "low": four_hour_fvg.low if four_hour_fvg else None,
                "moving_towards": moving_towards_4h_fvg,
                "distance_pct": round(distance_to_4h_fvg_pct, 2) if four_hour_fvg else None,
                "direction_message": fvg_direction_msg if fvg_direction_msg else "No 4H FVG detected",
                "is_active_setup": setup_timeframe in ['240', 'FOUR_HOUR', '4H'] if setup_timeframe else False
            },
            "probability_factors": {
                "fvg_status": f"{prob_factors[0]*100:.0f}%" if len(prob_factors) > 0 else "0%",
                "price_position": f"{prob_factors[1]*100:.0f}%" if len(prob_factors) > 1 else "0%",
                "fvg_size": f"{prob_factors[2]*100:.0f}%" if len(prob_factors) > 2 else "0%",
                "timeframe_weight": f"{prob_factors[3]*100:.0f}%" if len(prob_factors) > 3 else "0%",
                "ml_confirmation": f"{ml_confirmation*100:.0f}%" if ml_confirmation else "0%"
            } if best_setup else {
                "fvg_status": "0% (no FVG)",
                "price_position": "25%" if overall_bias != 'neutral' else "15%",
                "fvg_size": "0%",
                "timeframe_weight": "10%",
                "ml_confirmation": "0%"
            }
        },
        "ml_analysis": {
            "enabled": ml_signal is not None,
            "status": "ACTIVE" if ml_signal else "INACTIVE",
            "direction": ml_signal.get('direction', 'neutral') if ml_signal else 'neutral',
            "confidence": round(ml_signal.get('confidence', 0) * 100, 1) if ml_signal else 0,
            "predicted_price": ml_signal.get('predicted_price') if ml_signal else spot_price,
            "price_change_pct": ml_signal.get('price_change_pct', 0) if ml_signal else 0,
            "recommendation": ml_signal.get('recommendation', 'Analysis pending') if ml_signal else 'Analysis pending',
            "warning": ml_warning,
            "models": {
                "arima": ml_signal.get('arima', {}).get('direction', 'neutral') if ml_signal else 'neutral',
                "momentum": ml_signal.get('momentum', {}).get('direction', 'neutral') if ml_signal else 'neutral'
            }
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
            "timeframes": "Monthly → Weekly → Daily → 4H → 1H → 15min ICT Analysis",
            "targets": "Quick 10-30% gains",
            "max_hold": "Same day only",
            "entry_window": "9:30 AM - 2:00 PM"
        },
        # MARKET CONTEXT - Complete data for UI cards
        "market_context": {
            "spot_price": round(spot_price, 2),
            "future_price": chain_data.get("future_price") or round(spot_price, 2),
            "atm_strike": atm_strike,
            "overall_bias": overall_bias,
            "iv_regime": "High" if atm_iv > 0.20 else ("Low" if atm_iv < 0.12 else "Normal"),
            "atm_iv": round(atm_iv * 100, 2),
            "vix": chain_data.get("vix", 15),
            "pcr_oi": chain_data.get("pcr_oi", 1.0),
            "pcr_volume": chain_data.get("pcr_volume", 1.0),
            "max_pain": chain_data.get("max_pain", atm_strike),
            "basis": chain_data.get("basis", 0),
            "basis_pct": chain_data.get("basis_pct", 0),
            "days_to_expiry": chain_data.get("days_to_expiry", 7),
            "support_levels": chain_data.get("levels", {}).get("support", []) if isinstance(chain_data.get("levels"), dict) else [],
            "resistance_levels": chain_data.get("levels", {}).get("resistance", []) if isinstance(chain_data.get("levels"), dict) else [],
            "total_call_oi": chain_data.get("totals", {}).get("call_oi", 0) if isinstance(chain_data.get("totals"), dict) else 0,
            "total_put_oi": chain_data.get("totals", {}).get("put_oi", 0) if isinstance(chain_data.get("totals"), dict) else 0
        },
        # THETA DECAY ANALYSIS - Important for option buying timing
        "theta_analysis": _get_theta_decay_analysis(dte, atm_iv, greeks.get('theta', 0)),
        # EXPIRY ANALYSIS - Best time to buy based on DTE
        "expiry_analysis": {
            "days_to_expiry": dte,
            "is_expiry_week": dte <= 5,
            "is_expiry_day": dte <= 1,
            "theta_decay_rate": "EXTREME" if dte <= 1 else ("FAST" if dte <= 3 else ("MODERATE" if dte <= 7 else "SLOW")),
            "best_entry_advice": _get_best_entry_advice(dte, greeks.get('theta', 0)),
            "time_value_warning": "⚠️ Expiry day - 50%+ value can be lost" if dte <= 1 else (
                "⚠️ Last 3 days - Rapid theta decay" if dte <= 3 else (
                "⚡ Expiry week - Consider quick trades" if dte <= 5 else "✅ Safe for swing trades"
            ))
        }
    }


def _get_theta_decay_analysis(dte: int, iv: float, current_theta: float) -> dict:
    """
    Comprehensive theta decay analysis for option trading decisions.
    Helps determine the best time to buy options based on time decay.
    """
    # Theta decay accelerates as expiry approaches
    # Standard decay pattern: sqrt(T) relationship
    
    if dte <= 0:
        dte = 1  # Avoid division by zero
    
    # Daily decay percentage based on DTE
    if dte <= 1:
        daily_decay_pct = 30.0  # Extreme - can lose 30%+ of remaining value
        decay_phase = "EXTREME"
        advice = "🚨 EXPIRY DAY: Avoid buying options. Extreme time decay. Only for gamma scalping."
        risk_level = "VERY HIGH"
    elif dte <= 3:
        daily_decay_pct = 15.0
        decay_phase = "FAST"
        advice = "⚠️ LAST 3 DAYS: High theta decay. Quick in/out trades only. Set tight stop losses."
        risk_level = "HIGH"
    elif dte <= 7:
        daily_decay_pct = 8.0
        decay_phase = "ACCELERATING"
        advice = "⚡ EXPIRY WEEK: Theta decay accelerating. Prefer ATM options for delta gains."
        risk_level = "MEDIUM-HIGH"
    elif dte <= 15:
        daily_decay_pct = 5.0
        decay_phase = "MODERATE"
        advice = "✅ GOOD FOR SWING: Moderate decay. Can hold 2-3 days if trend is strong."
        risk_level = "MEDIUM"
    elif dte <= 30:
        daily_decay_pct = 3.0
        decay_phase = "SLOW"
        advice = "✅ IDEAL FOR POSITIONAL: Slow decay allows time for move to develop."
        risk_level = "LOW"
    else:
        daily_decay_pct = 2.0
        decay_phase = "MINIMAL"
        advice = "✅ SAFE FOR LONG TERM: Minimal theta impact. Prefer slightly OTM options."
        risk_level = "VERY LOW"
    
    # Calculate expected decay
    hourly_decay_pct = daily_decay_pct / 6.25  # ~6.25 market hours per day
    
    # Best time to buy based on DTE and market session - USE IST
    now = get_ist_time()  # IST time for consistent session detection
    market_open = time(9, 15)
    market_close = time(15, 30)
    
    if now < market_open or now > market_close:
        best_buy_time = "Market Closed - Plan entry for next session"
    elif dte <= 3:
        best_buy_time = "Morning session (9:30-11:00) - Before afternoon theta acceleration"
    elif dte <= 7:
        best_buy_time = "First half (9:30-12:30) - Capture morning momentum"
    else:
        best_buy_time = "Any time during market hours - Low theta impact"
    
    return {
        "decay_phase": decay_phase,
        "daily_decay_pct": round(daily_decay_pct, 1),
        "hourly_decay_pct": round(hourly_decay_pct, 2),
        "current_theta": round(current_theta, 4),
        "theta_per_hour": round(current_theta / 6.25, 4) if current_theta else 0,
        "risk_level": risk_level,
        "advice": advice,
        "best_buy_time": best_buy_time,
        "remaining_value_estimate": f"~{100 - (daily_decay_pct * min(dte, 5))}% value retention if held to expiry" if dte <= 5 else "Good value retention expected",
        "strategy_recommendation": (
            "AVOID BUYING" if dte <= 1 else
            "SCALPING ONLY" if dte <= 3 else
            "INTRADAY/SWING" if dte <= 7 else
            "SWING/POSITIONAL" if dte <= 15 else
            "POSITIONAL"
        )
    }


def _get_best_entry_advice(dte: int, theta: float) -> str:
    """Get specific entry timing advice based on DTE and theta"""
    if dte <= 1:
        return "❌ NOT RECOMMENDED - Expiry day. Consider next week's expiry instead."
    elif dte <= 3:
        return "⚠️ Enter in morning session ONLY. Exit same day. Risk: " + ("HIGH" if theta < -0.5 else "MEDIUM")
    elif dte <= 5:
        return "⚡ Morning entry preferred (9:30-11:00). Can hold overnight if trend strong."
    elif dte <= 7:
        return "✅ Enter any time. Can hold 1-2 days. Theta decay manageable."
    else:
        return "✅ Safe entry window. Can hold for swing trades (3-5 days)."


def _detect_trend_reversal(mtf_result) -> dict:
    """
    Detect potential trend reversal from MTF ICT analysis.
    
    A trend reversal is indicated when:
    1. Higher timeframe (Monthly/Weekly) shows Change of Character (CHoCH)
    2. Multiple timeframes show conflicting biases (e.g., Monthly bearish but lower TFs bullish)
    3. Break of Structure (BOS) on significant timeframe
    
    Returns:
        Dict with reversal detection info:
        - is_reversal: bool
        - direction: "BULLISH_REVERSAL" | "BEARISH_REVERSAL" | "NONE"
        - confidence: 0-100
        - reason: explanation
        - key_levels: important levels to watch
    """
    reversal_info = {
        "is_reversal": False,
        "direction": "NONE",
        "confidence": 0,
        "reason": "No clear reversal signal detected",
        "key_levels": [],
        "timeframes_signaling": []
    }
    
    if not mtf_result or not mtf_result.analyses:
        return reversal_info
    
    # Check for CHoCH or BOS signals on different timeframes
    choch_signals = []
    bos_signals = []
    bias_conflicts = []
    
    # Priority order: Monthly > Weekly > Daily > 4H > 1H > 15min
    tf_priority = {'M': 6, 'W': 5, 'D': 4, '240': 3, '60': 2, '15': 1}
    
    for tf_key, analysis in mtf_result.analyses.items():
        ms = analysis.market_structure
        
        # Check for Change of Character (potential reversal)
        if ms.change_of_character:
            choch_signals.append({
                "timeframe": tf_key,
                "type": ms.change_of_character,
                "priority": tf_priority.get(tf_key, 0)
            })
        
        # Check for Break of Structure
        if ms.break_of_structure:
            bos_signals.append({
                "timeframe": tf_key,
                "type": ms.break_of_structure,
                "priority": tf_priority.get(tf_key, 0)
            })
    
    # Check for bias conflicts between timeframes
    biases = {tf: analysis.bias for tf, analysis in mtf_result.analyses.items()}
    
    # Monthly vs rest
    monthly_bias = biases.get('M', 'neutral')
    weekly_bias = biases.get('W', 'neutral')
    daily_bias = biases.get('D', 'neutral')
    
    # Detect significant conflicts
    if monthly_bias != 'neutral' and weekly_bias != 'neutral' and monthly_bias != weekly_bias:
        bias_conflicts.append(f"Monthly ({monthly_bias}) vs Weekly ({weekly_bias})")
    
    if weekly_bias != 'neutral' and daily_bias != 'neutral' and weekly_bias != daily_bias:
        bias_conflicts.append(f"Weekly ({weekly_bias}) vs Daily ({daily_bias})")
    
    # Determine if reversal is likely
    if choch_signals:
        # Sort by priority (highest first)
        choch_signals.sort(key=lambda x: x['priority'], reverse=True)
        strongest_choch = choch_signals[0]
        
        reversal_info["is_reversal"] = True
        
        if "bullish" in strongest_choch["type"].lower():
            reversal_info["direction"] = "BULLISH_REVERSAL"
            reversal_info["reason"] = f"Bullish CHoCH on {strongest_choch['timeframe']} timeframe - potential reversal from bearish to bullish"
        else:
            reversal_info["direction"] = "BEARISH_REVERSAL"
            reversal_info["reason"] = f"Bearish CHoCH on {strongest_choch['timeframe']} timeframe - potential reversal from bullish to bearish"
        
        # Confidence based on timeframe priority
        base_confidence = 40 + (strongest_choch["priority"] * 10)
        
        # Boost confidence if multiple timeframes confirm
        if len(choch_signals) > 1:
            base_confidence += 10
        
        reversal_info["confidence"] = min(base_confidence, 95)
        reversal_info["timeframes_signaling"] = [s["timeframe"] for s in choch_signals]
    
    elif bos_signals and len(bos_signals) >= 2:
        # Multiple BOS signals can indicate trend continuation OR reversal start
        bos_signals.sort(key=lambda x: x['priority'], reverse=True)
        reversal_info["is_reversal"] = True
        reversal_info["confidence"] = 50 + (len(bos_signals) * 5)
        
        if "bullish" in bos_signals[0]["type"].lower():
            reversal_info["direction"] = "BULLISH_REVERSAL"
            reversal_info["reason"] = f"Multiple bullish BOS signals - trend shifting upward"
        else:
            reversal_info["direction"] = "BEARISH_REVERSAL"
            reversal_info["reason"] = f"Multiple bearish BOS signals - trend shifting downward"
        
        reversal_info["timeframes_signaling"] = [s["timeframe"] for s in bos_signals]
    
    elif bias_conflicts:
        # Conflicting biases suggest market is in transition
        reversal_info["is_reversal"] = True
        reversal_info["confidence"] = 40
        reversal_info["direction"] = "UNCERTAIN_REVERSAL"
        reversal_info["reason"] = f"Conflicting biases: {', '.join(bias_conflicts)} - market in transition"
    
    # Add key levels to watch
    for tf_key, analysis in mtf_result.analyses.items():
        ms = analysis.market_structure
        if ms.last_high and ms.last_low:
            reversal_info["key_levels"].append({
                "timeframe": tf_key,
                "high": ms.last_high,
                "low": ms.last_low
            })
    
    return reversal_info


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
    """Get session-specific timing advice for Indian market (Mon-Fri) in IST"""
    # Use IST utilities for consistent timezone handling across geographies
    now = now_ist()
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
        session_info = options_time_analyzer.get_current_session()
        
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
            "session_context": session_info.get("current_session", "UNKNOWN"),
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
        current_session = session_info.get("current_session", "")
        if current_session in ["OPENING_VOLATILITY", "CLOSING_HOUR"]:
            reasoning["risk_factors"].append("High volatility session - increased risk")
            
        if session_info.get("time_to_expiry", {}).get("days", 7) <= 2:
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

@app.get("/screener/stocks/list")
async def get_stock_list():
    """
    Get searchable list of all available stocks
    
    Returns:
        List of stocks with symbol, name, and short_name for search/autocomplete
    """
    try:
        # Get comprehensive stock list from screener module
        from src.analytics.stock_screener import StockScreener
        
        # Get all stocks (full list, no limit)
        screener_instance = StockScreener(fyers_client)
        raw_stocks = screener_instance.get_nse_stocks_list(limit=None, randomize=False)
        
        # Get metadata from index constituents for richer data
        from src.analytics.index_constituents import index_manager
        
        stock_list = []
        seen_symbols = set()
        
        for stock in raw_stocks:
            if stock in seen_symbols:
                continue
            seen_symbols.add(stock)
            
            # Parse symbol: "NSE:RELIANCE-EQ" -> "RELIANCE"
            short_name = stock.replace("NSE:", "").replace("-EQ", "")
            
            # Try to get full name from index constituents
            stock_info = index_manager.get_stock_info(stock)
            full_name = stock_info.name if stock_info else short_name
            
            stock_list.append({
                "symbol": stock,
                "name": full_name,
                "short_name": short_name
            })
        
        # Sort by short_name for easy browsing
        stock_list.sort(key=lambda x: x["short_name"])
        
        return {
            "status": "success",
            "total": len(stock_list),
            "stocks": stock_list
        }
        
    except Exception as e:
        logger.error(f"Error getting stock list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/screener/scan")
async def scan_stocks(
    limit: int = Query(50, description="Number of stocks to scan (faster with lower numbers)"),
    min_confidence: float = Query(60.0, description="Minimum confidence level (0-100)"),
    randomize: bool = Query(True, description="Randomly sample stocks for variety"),
    symbols: str = Query(None, description="Optional: comma-separated list of symbols to scan (e.g., 'NSE:RELIANCE-EQ,NSE:TCS-EQ')"),
    authorization: str = Header(None, description="Bearer token (required)"),
):
    """
    Scan NSE stocks for high-confidence trading signals (Authentication Required)
    
    Args:
        limit: Number of stocks to scan (default 50, max recommended 200)
        min_confidence: Minimum confidence threshold (default 60%)
        randomize: Random sampling for variety (recommended True)
        authorization: Auth token in Authorization header (required) - results automatically saved to your account
        
    Returns:
        List of stocks with BUY/SELL signals meeting confidence criteria
    """
    try:
        # Authenticate user first
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
        token = authorization.replace("Bearer ", "")
        user = await auth_service.get_current_user(token)
        
        # Check if user has Fyers token for market data access
        fyers_token = await auth_service.get_fyers_token(user.id)
        if not fyers_token:
            logger.info(f"User {user.email} needs Fyers authentication")
            raise HTTPException(
                status_code=401, 
                detail={
                    "error": "fyers_auth_required",
                    "message": "Fyers API authentication required to fetch market data",
                    "auth_url": fyers_client.generate_auth_url(),
                    "user_authenticated": True
                }
            )
        
        # Check if Fyers token is expired (tokens expire in ~24 hours)
        if fyers_token.expires_at:
            # Handle both timezone-aware and timezone-naive datetimes
            now = datetime.now()
            if fyers_token.expires_at.tzinfo is not None:
                # expires_at is timezone-aware, make now timezone-aware too
                now = now.replace(tzinfo=timezone.utc)
                expires_at = fyers_token.expires_at
            else:
                # expires_at is timezone-naive, keep both naive
                expires_at = fyers_token.expires_at
            
            if expires_at < now:
                logger.info(f"Fyers token expired for user {user.email}")
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "fyers_token_expired", 
                        "message": "Your Fyers token has expired. Please re-authenticate to continue.",
                        "auth_url": fyers_client.generate_auth_url(),
                        "user_authenticated": True
                    }
                )
        
        # Set the Fyers token for this request
        fyers_client.access_token = fyers_token.access_token
        fyers_client._initialize_client()
        
        # Parse symbols if provided
        stocks_list = None
        if symbols:
            stocks_list = [s.strip() for s in symbols.split(",") if s.strip()]
            # Ensure proper format (NSE:SYMBOL-EQ)
            stocks_list = [
                s if s.startswith("NSE:") else f"NSE:{s}-EQ"
                for s in stocks_list
            ]
            logger.info(f"Stock screener scan requested by {user.email}: scanning {len(stocks_list)} specific stocks")
        else:
            logger.info(f"Stock screener scan requested by {user.email}: limit={limit}, min_confidence={min_confidence}, randomize={randomize}")
        
        # Get screener instance
        screener = get_stock_screener(fyers_client)
        
        # Run scan (pass stocks_list if specific symbols were provided)
        signals = screener.scan_stocks(
            limit=limit,
            min_confidence=min_confidence,
            randomize=randomize,
            stocks=stocks_list
        )
        
        # Integrate news sentiment into signals
        sentiment_data = None
        try:
            from src.analytics.news_sentiment import news_analyzer, get_sentiment_enhanced_signal
            
            # Get overall market sentiment for NIFTY (general market)
            sentiment_data = await news_analyzer.get_sentiment_for_signal(
                symbol="NIFTY",
                signal_type="BUY"  # Just to get market direction
            )
            
            # Apply sentiment adjustments to each signal
            if sentiment_data and sentiment_data.get("sentiment_score", 0) != 0:
                sentiment_score = sentiment_data.get("sentiment_score", 0)
                sentiment_overall = sentiment_data.get("sentiment", "neutral")
                
                for signal in signals:
                    signal_action = signal.get("action", "HOLD")
                    
                    # Adjust confidence based on sentiment alignment
                    if signal_action == "BUY" and sentiment_overall == "bullish":
                        # Bullish sentiment supports buy signal
                        boost = abs(sentiment_score) * 10  # Up to 10% confidence boost
                        signal["confidence"] = min(100, signal.get("confidence", 50) + boost)
                        signal["sentiment_support"] = True
                    elif signal_action == "SELL" and sentiment_overall == "bearish":
                        # Bearish sentiment supports sell signal
                        boost = abs(sentiment_score) * 10
                        signal["confidence"] = min(100, signal.get("confidence", 50) + boost)
                        signal["sentiment_support"] = True
                    elif signal_action == "BUY" and sentiment_overall == "bearish":
                        # Bearish sentiment conflicts with buy signal
                        reduction = abs(sentiment_score) * 5  # Up to 5% confidence reduction
                        signal["confidence"] = max(0, signal.get("confidence", 50) - reduction)
                        signal["sentiment_conflict"] = True
                    elif signal_action == "SELL" and sentiment_overall == "bullish":
                        # Bullish sentiment conflicts with sell signal
                        reduction = abs(sentiment_score) * 5
                        signal["confidence"] = max(0, signal.get("confidence", 50) - reduction)
                        signal["sentiment_conflict"] = True
                    
                    # Add sentiment reason to signal
                    if "reasons" in signal and isinstance(signal["reasons"], list):
                        if sentiment_overall != "neutral":
                            mood = sentiment_data.get("market_mood", "")
                            signal["reasons"].append(f"Market Sentiment: {sentiment_overall.capitalize()} ({mood})")
                
                # Re-sort by adjusted confidence
                signals = sorted(signals, key=lambda x: x.get("confidence", 0), reverse=True)
                
        except Exception as sentiment_error:
            logger.warning(f"Could not integrate sentiment into screener: {sentiment_error}")
        
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
            "sentiment_analysis": sentiment_data,  # Include market sentiment
            "signals": signals,  # Flat array for frontend compatibility
            "signals_by_type": {
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


# Also support POST with /api/ prefix for frontend compatibility
@app.post("/api/screener/scan")
async def scan_stocks_post(
    request: Request,
    authorization: str = Header(None, description="Bearer token (required)"),
):
    """
    POST endpoint for stock screener (frontend compatibility)
    Supports both random scanning and custom stock selection
    """
    try:
        body = await request.json()
        limit = body.get("limit", 50)
        min_confidence = body.get("min_confidence", 60.0)
        action = body.get("action", "BUY")
        randomize = body.get("randomize", True)
        symbols = body.get("symbols", None)  # Comma-separated or None
        
        # Re-use the GET endpoint logic
        return await scan_stocks(
            limit=limit,
            min_confidence=min_confidence,
            randomize=randomize,
            symbols=symbols,
            authorization=authorization
        )
    except Exception as e:
        logger.error(f"Error in POST screener scan: {e}")
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
async def get_latest_scan(authorization: str = Header(None, description="Bearer token")):
    """Get latest saved scan results for user"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
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
    authorization: str = Header(None, description="Bearer token"),
    limit: int = Query(10, description="Number of scans to retrieve")
):
    """Get scan history for user"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
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


@app.get("/screener/recent-signals")
async def get_recent_signals(
    authorization: str = Header(None, description="Bearer token"),
    hours: int = Query(2, description="Time range in hours"),
    limit: int = Query(20, description="Max signals to retrieve"),
    signal_type: str = Query("ALL", description="Filter by signal type: STOCK, OPTIONS, or ALL")
):
    """Get recent high-confidence signals from last N hours (includes both stock and options signals)"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
        token = authorization.replace("Bearer ", "")
        user = await auth_service.get_current_user(token)
        
        # Get stock signals
        stock_signals = {"buy": [], "sell": []}
        if signal_type.upper() in ["STOCK", "ALL"]:
            stock_signals = await screener_service.get_recent_signals(user.id, hours, limit)
        
        # Get options signals
        options_signals = []
        if signal_type.upper() in ["OPTIONS", "ALL"]:
            options_signals = await screener_service.get_recent_options_signals(user.id, hours, limit)
        
        return {
            "status": "success",
            "signals": stock_signals,
            "options_signals": options_signals,
            "time_range": f"Last {hours} hours",
            "signal_type_filter": signal_type.upper()
        }
        
    except Exception as e:
        logger.error(f"Error getting recent signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/screener/debug/check-data")
async def debug_check_stored_data(
    authorization: str = Header(None, description="Bearer token"),
    limit: int = Query(5, description="Number of records to check")
):
    """Debug endpoint to verify what data is stored in database"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
        token = authorization.replace("Bearer ", "")
        user = await auth_service.get_current_user(token)
        
        # Get recent signals with all fields
        response = await screener_service.supabase.table("screener_results")\
            .select("*")\
            .eq("user_id", user.id)\
            .order("scanned_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            "status": "success",
            "total_records": len(response.data),
            "sample_data": response.data,
            "fields_stored": list(response.data[0].keys()) if response.data else []
        }
        
    except Exception as e:
        logger.error(f"Error checking stored data: {e}")
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


# ==================== OPTIONS SCANNER ENDPOINTS ====================

@app.get("/options/scan/latest")
async def get_latest_scan_results(
    index: str = Query("NIFTY", description="Index to get results for")
):
    """
    Get latest auto-scan results without authentication
    Returns cached results from background scanner
    """
    try:
        index = index.upper()
        
        if index not in latest_scan_results:
            raise HTTPException(
                status_code=404, 
                detail=f"Invalid index. Choose from: {', '.join(latest_scan_results.keys())}"
            )
        
        results = latest_scan_results[index]
        
        if not results:
            return {
                "status": "pending",
                "message": f"No scan results available yet for {index}. Scanner runs every 16 minutes.",
                "next_scan": "Within 16 minutes"
            }
        
        return {
            "status": "success",
            "data": results,
            "scan_frequency": "Every 16 minutes",
            "indices_monitored": list(latest_scan_results.keys())
        }
        
    except Exception as e:
        logger.error(f"Error getting latest scan results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/options/scan/all")
async def get_all_latest_scans():
    """
    Get latest scan results for all monitored indices
    """
    try:
        available_scans = {}
        pending_scans = []
        
        for index in latest_scan_results.keys():
            if latest_scan_results[index]:
                available_scans[index] = latest_scan_results[index]
            else:
                pending_scans.append(index)
        
        return {
            "status": "success",
            "scan_frequency": "Every 16 minutes",
            "available_scans": available_scans,
            "pending_scans": pending_scans,
            "total_indices": len(latest_scan_results)
        }
        
    except Exception as e:
        logger.error(f"Error getting all scan results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/options/scan")
async def scan_options(
    index: str = Query("NIFTY", description="Index to scan options for (NIFTY, BANKNIFTY, FINNIFTY)"),
    expiry: str = Query("weekly", description="weekly or monthly"),
    min_volume: int = Query(1000, description="Minimum volume filter"),
    min_oi: int = Query(10000, description="Minimum Open Interest filter"),
    strategy: str = Query("all", description="all, momentum, reversal, volatility"),
    include_probability: bool = Query(True, description="Include constituent stock probability analysis"),
    authorization: str = Header(None, description="Bearer token (required)"),
):
    """
    Scan index options for trading opportunities with integrated probability analysis
    
    This endpoint now COMBINES:
    1. Option chain scanning (volume, OI, IV, Greeks)
    2. Index probability analysis (scans ALL constituent stocks)
    
    For NIFTY: Scans all 50 constituent stocks to predict index direction
    For BANKNIFTY: Scans all 14 bank stocks
    
    Args:
        index: Index to scan (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX, BANKEX)
        expiry: Expiry type (weekly, monthly)
        min_volume: Minimum volume threshold
        min_oi: Minimum Open Interest threshold
        strategy: Filter by strategy type (all, momentum, reversal, volatility)
        include_probability: Include constituent stock probability analysis (default: True)
        authorization: Auth token (required)
        
    Returns:
        Filtered and scored options with trading recommendations + index probability analysis
    """
    try:
        # Authenticate user first
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
        token = authorization.replace("Bearer ", "")
        user = await auth_service.get_current_user(token)
        
        # Try to load user's Fyers token if available
        try:
            fyers_token = await auth_service.get_fyers_token(user.id)
            
            if fyers_token and fyers_token.access_token:
                # Check expiry
                now = datetime.now()
                if fyers_token.expires_at:
                    if fyers_token.expires_at.tzinfo is not None:
                        now = now.replace(tzinfo=timezone.utc)
                    if fyers_token.expires_at > now:
                        # Token is valid, use it
                        fyers_client.access_token = fyers_token.access_token
                        fyers_client._initialize_client()
                        logger.info(f"✅ Using live Fyers token for user {user.email}")
                    else:
                        logger.warning(f"⚠️ Fyers token expired for user {user.email}")
                        fyers_client.access_token = None
                else:
                    logger.warning(f"⚠️ No expiry info for Fyers token")
                    fyers_client.access_token = None
        except Exception as token_error:
            logger.warning(f"Could not load Fyers token: {token_error}")
            fyers_client.access_token = None
        
        logger.info(f"Options scanner requested by {user.email}: {index}/{expiry}, min_vol={min_volume}, min_oi={min_oi}, strategy={strategy}")
        
        # ==================== INDEX PROBABILITY ANALYSIS ====================
        # Scan ALL constituent stocks to predict index direction
        probability_analysis = None
        recommended_option_type = None
        
        if include_probability and INDEX_ANALYSIS_AVAILABLE:
            try:
                logger.info(f"📊 Starting constituent stock analysis for {index}...")
                prob_analyzer = get_probability_analyzer(fyers_client)
                prediction = prob_analyzer.analyze_index(index.upper())
                
                if prediction:
                    # Determine recommended option type based on probability
                    if prediction.expected_direction == "BULLISH" and prediction.prob_up > 0.55:
                        recommended_option_type = "CALL"
                    elif prediction.expected_direction == "BEARISH" and prediction.prob_down > 0.55:
                        recommended_option_type = "PUT"
                    else:
                        recommended_option_type = "STRADDLE"  # Neutral - play both sides
                    
                    probability_analysis = {
                        "stocks_scanned": prediction.total_stocks_analyzed,
                        "total_stocks": len(index_manager.get_constituents(index.upper())) if index_manager else prediction.total_stocks_analyzed,
                        "expected_direction": prediction.expected_direction,
                        "expected_move_pct": round(prediction.expected_move_pct, 2),
                        "confidence": round(prediction.prediction_confidence / 100, 3),  # Convert 0-100 to 0-1
                        "probability_up": round(prediction.prob_up, 3),
                        "probability_down": round(prediction.prob_down, 3),
                        "bullish_stocks": prediction.bullish_stocks,
                        "bearish_stocks": prediction.bearish_stocks,
                        "bullish_pct": round((prediction.bullish_stocks / max(1, prediction.total_stocks_analyzed)) * 100, 1),
                        "bearish_pct": round((prediction.bearish_stocks / max(1, prediction.total_stocks_analyzed)) * 100, 1),
                        "recommended_option_type": recommended_option_type,
                        "market_regime": prediction.regime.regime.value if prediction.regime else "unknown",
                        "top_bullish_stocks": [
                            {"symbol": s.symbol.split(":")[-1].replace("-EQ", ""), "probability": round(s.probability, 2), "expected_move": round(s.expected_move_pct, 2)}
                            for s in sorted(prediction.stock_signals, key=lambda x: x.probability if x.trend_direction == "up" else 0, reverse=True)[:5]
                            if s.trend_direction == "up"
                        ],
                        "top_bearish_stocks": [
                            {"symbol": s.symbol.split(":")[-1].replace("-EQ", ""), "probability": round(s.probability, 2), "expected_move": round(s.expected_move_pct, 2)}
                            for s in sorted(prediction.stock_signals, key=lambda x: x.probability if x.trend_direction == "down" else 0, reverse=True)[:5]
                            if s.trend_direction == "down"
                        ],
                        "volume_surge_stocks": [
                            {"symbol": s.symbol.split(":")[-1].replace("-EQ", ""), "has_surge": True}
                            for s in prediction.stock_signals if s.volume_surge
                        ][:5]
                    }
                    
                    logger.info(f"✅ Probability analysis: {prediction.expected_direction} ({prediction.prob_up:.1%} up / {prediction.prob_down:.1%} down)")
                    logger.info(f"📈 Recommended: {recommended_option_type} options")
                    
            except Exception as prob_error:
                logger.warning(f"⚠️ Probability analysis failed: {prob_error}")
                probability_analysis = {"error": str(prob_error)}
        # ====================================================================
        
        # Get option chain data (will return mock data if no live token)
        try:
            analyzer = get_index_analyzer(fyers_client)
            chain = analyzer.analyze_option_chain(index.upper(), expiry)
            
            if not chain:
                # Return mock data for demo purposes
                mock_result = generate_mock_options_scan_data(index, expiry, min_volume, min_oi, strategy)
                if probability_analysis:
                    mock_result["probability_analysis"] = probability_analysis
                    mock_result["recommended_option_type"] = recommended_option_type
                return mock_result
                
        except Exception as chain_error:
            logger.warning(f"Option chain analysis failed: {chain_error}, returning demo data")
            mock_result = generate_mock_options_scan_data(index, expiry, min_volume, min_oi, strategy)
            if probability_analysis:
                mock_result["probability_analysis"] = probability_analysis
                mock_result["recommended_option_type"] = recommended_option_type
            return mock_result
        
        # Process options for scanning
        scanned_options = process_options_scan(chain, min_volume, min_oi, strategy)
        
        # If we have a recommended option type, boost those options' scores
        if recommended_option_type and recommended_option_type in ["CALL", "PUT"]:
            for opt in scanned_options:
                if opt["type"] == recommended_option_type:
                    opt["probability_boost"] = True
                    opt["score"] = opt["score"] * 1.2  # 20% boost for recommended type
                else:
                    opt["probability_boost"] = False
            # Re-sort after boosting
            scanned_options = sorted(scanned_options, key=lambda x: x["score"], reverse=True)
        
        # Integrate news sentiment into signals
        sentiment_data = None
        try:
            from src.analytics.news_sentiment import news_analyzer
            sentiment_data = await news_analyzer.get_sentiment_for_signal(
                symbol=index.upper(),
                signal_type=recommended_option_type  # Use recommended type as signal direction
            )
            
            # Apply sentiment-based adjustments to option scores
            if sentiment_data and sentiment_data.get("sentiment_score", 0) != 0:
                sentiment_score = sentiment_data.get("sentiment_score", 0)
                sentiment_overall = sentiment_data.get("sentiment", "neutral")
                
                for opt in scanned_options:
                    # Boost CALL options if bullish, PUT options if bearish
                    if opt["type"] == "CALL" and sentiment_overall == "bullish":
                        opt["sentiment_boost"] = True
                        opt["score"] = opt["score"] * (1 + abs(sentiment_score) * 0.15)  # Up to 15% boost
                    elif opt["type"] == "PUT" and sentiment_overall == "bearish":
                        opt["sentiment_boost"] = True
                        opt["score"] = opt["score"] * (1 + abs(sentiment_score) * 0.15)
                    # Reduce confidence for conflicting sentiment
                    elif opt["type"] == "CALL" and sentiment_overall == "bearish":
                        opt["sentiment_conflict"] = True
                        opt["score"] = opt["score"] * (1 - abs(sentiment_score) * 0.1)  # Up to 10% reduction
                    elif opt["type"] == "PUT" and sentiment_overall == "bullish":
                        opt["sentiment_conflict"] = True
                        opt["score"] = opt["score"] * (1 - abs(sentiment_score) * 0.1)
                    else:
                        opt["sentiment_boost"] = False
                        opt["sentiment_conflict"] = False
                
                # Re-sort after sentiment adjustments
                scanned_options = sorted(scanned_options, key=lambda x: x["score"], reverse=True)
                
        except Exception as sentiment_error:
            logger.warning(f"Could not integrate sentiment: {sentiment_error}")
        
        result = {
            "status": "success",
            "scan_time": datetime.now().isoformat(),
            "index": index.upper(),
            "expiry": expiry,
            "filters": {
                "min_volume": min_volume,
                "min_oi": min_oi,
                "strategy": strategy
            },
            "market_data": {
                "spot_price": chain.spot_price,
                "atm_strike": chain.atm_strike,
                "vix": getattr(chain, 'vix', None),
                "expiry_date": chain.expiry_date,
                "days_to_expiry": chain.days_to_expiry
            },
            "probability_analysis": probability_analysis,
            "recommended_option_type": recommended_option_type,
            "sentiment_analysis": sentiment_data,  # Include sentiment in response
            "total_options": len(scanned_options),
            "options": scanned_options[:50],  # Top 50 results
            "user_email": user.email,
            "data_source": "live" if fyers_client.access_token else "demo"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in options scanner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def generate_mock_options_scan_data(index: str, expiry: str, min_volume: int, min_oi: int, strategy: str):
    """Generate mock options scan data for demo purposes"""
    import random
    from datetime import datetime, timedelta
    
    spot_price = {
        "NIFTY": 24500,
        "BANKNIFTY": 50800,
        "FINNIFTY": 23200
    }.get(index, 24500)
    
    # Generate strikes around ATM
    atm_strike = round(spot_price / 50) * 50
    strikes = [atm_strike + (i * 50) for i in range(-10, 11)]
    
    options = []
    for strike in strikes:
        for option_type in ["CALL", "PUT"]:
            if random.random() > 0.3:  # Not all strikes have active options
                
                # Generate realistic option metrics
                moneyness = spot_price / strike
                is_itm = (option_type == "CALL" and moneyness > 1) or (option_type == "PUT" and moneyness < 1)
                
                volume = random.randint(min_volume, min_volume * 50)
                oi = random.randint(min_oi, min_oi * 5)
                
                # Basic Greeks calculation
                delta = calculate_simple_delta(spot_price, strike, option_type)
                gamma = calculate_simple_gamma(spot_price, strike)
                
                # Strategy scoring
                score = calculate_option_strategy_score(
                    spot_price, strike, option_type, volume, oi, delta, gamma, strategy
                )
                
                if score >= 40:  # Only include decent scoring options
                    options.append({
                        "strike": strike,
                        "type": option_type,
                        "ltp": calculate_mock_option_price(spot_price, strike, option_type),
                        "volume": volume,
                        "oi": oi,
                        "iv": random.uniform(15, 35),
                        "delta": delta,
                        "gamma": gamma,
                        "theta": random.uniform(-0.5, -5.0),
                        "vega": random.uniform(2, 15),
                        "score": score,
                        "strategy_match": get_strategy_match(score, strategy),
                        "recommendation": get_option_recommendation(score, option_type, moneyness)
                    })
    
    # Sort by score
    options.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "status": "success",
        "scan_time": datetime.now().isoformat(),
        "index": index.upper(),
        "expiry": expiry,
        "filters": {
            "min_volume": min_volume,
            "min_oi": min_oi,
            "strategy": strategy
        },
        "market_data": {
            "spot_price": spot_price,
            "atm_strike": atm_strike,
            "vix": 16.5,
            "expiry_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "days_to_expiry": 7
        },
        "total_options": len(options),
        "options": options[:50],
        "data_source": "demo"
    }


def process_options_scan(chain, min_volume: int, min_oi: int, strategy: str, 
                         fetch_historical: bool = True):
    """
    Process real option chain data for scanning with discount zone analysis.
    
    Args:
        chain: OptionChainAnalysis object with all strikes
        min_volume: Minimum volume filter
        min_oi: Minimum open interest filter
        strategy: Strategy type (all, momentum, reversal, volatility)
        fetch_historical: If True, fetch intraday history for top options (adds latency)
    """
    options = []
    spot_price = chain.spot_price
    index = getattr(chain, 'index', 'NIFTY')
    expiry_date = getattr(chain, 'expiry_date', None)
    
    # Get market context for discount zone calculations
    dte = getattr(chain, 'days_to_expiry', 7)  # Default 7 days
    avg_iv = 0.15  # Default average IV (can be enhanced with historical data)
    market_momentum = "neutral"  # Can be enhanced with MTF analysis integration
    
    # Determine market momentum from chain data if available
    pcr_oi = getattr(chain, 'pcr_oi', 1.0)
    if pcr_oi > 1.2:
        market_momentum = "bullish"  # High PCR = bullish
    elif pcr_oi < 0.8:
        market_momentum = "bearish"  # Low PCR = bearish
    
    for strike_data in chain.strikes:
        strike = strike_data.strike
        
        # Process CALL options
        if (strike_data.call_volume >= min_volume and 
            strike_data.call_oi >= min_oi):
            
            delta = calculate_simple_delta(spot_price, strike, "CALL")
            gamma = calculate_simple_gamma(spot_price, strike)
            score = calculate_option_strategy_score(
                spot_price, strike, "CALL", 
                strike_data.call_volume, strike_data.call_oi, 
                delta, gamma, strategy
            )
            
            # Calculate discount zone for this option
            call_iv = getattr(strike_data, 'call_iv', 0.15) or 0.15
            discount_zone = calculate_discount_zone(
                option_ltp=strike_data.call_ltp,
                spot_price=spot_price,
                strike=strike,
                option_type="CALL",
                iv=call_iv,
                delta=delta,
                dte=dte,
                avg_iv=avg_iv,
                market_momentum=market_momentum,
                oi_analysis=getattr(strike_data, 'call_analysis', 'neutral') or 'neutral'
            )
            
            # Calculate entry analysis metrics
            entry_analysis = analyze_entry_quality(
                option_ltp=strike_data.call_ltp,
                spot_price=spot_price,
                strike=strike,
                option_type="CALL",
                discount_zone=discount_zone,
                delta=delta,
                dte=dte,
                iv=call_iv,
                volume=strike_data.call_volume,
                oi=strike_data.call_oi
            )
            
            options.append({
                "strike": strike,
                "type": "CALL",
                "ltp": strike_data.call_ltp,
                "volume": strike_data.call_volume,
                "oi": strike_data.call_oi,
                "iv": call_iv,
                "delta": delta,
                "gamma": gamma,
                "score": score,
                "strategy_match": get_strategy_match(score, strategy),
                "recommendation": get_option_recommendation(score, "CALL", spot_price / strike),
                "discount_zone": discount_zone,
                "entry_analysis": entry_analysis
            })
        
        # Process PUT options
        if (strike_data.put_volume >= min_volume and 
            strike_data.put_oi >= min_oi):
            
            delta = calculate_simple_delta(spot_price, strike, "PUT")
            gamma = calculate_simple_gamma(spot_price, strike)
            score = calculate_option_strategy_score(
                spot_price, strike, "PUT", 
                strike_data.put_volume, strike_data.put_oi, 
                delta, gamma, strategy
            )
            
            # Calculate discount zone for this option
            put_iv = getattr(strike_data, 'put_iv', 0.15) or 0.15
            discount_zone = calculate_discount_zone(
                option_ltp=strike_data.put_ltp,
                spot_price=spot_price,
                strike=strike,
                option_type="PUT",
                iv=put_iv,
                delta=delta,
                dte=dte,
                avg_iv=avg_iv,
                market_momentum=market_momentum,
                oi_analysis=getattr(strike_data, 'put_analysis', 'neutral') or 'neutral'
            )
            
            # Calculate entry analysis metrics for PUT
            entry_analysis = analyze_entry_quality(
                option_ltp=strike_data.put_ltp,
                spot_price=spot_price,
                strike=strike,
                option_type="PUT",
                discount_zone=discount_zone,
                delta=delta,
                dte=dte,
                iv=put_iv,
                volume=strike_data.put_volume,
                oi=strike_data.put_oi
            )
            
            options.append({
                "strike": strike,
                "type": "PUT",
                "ltp": strike_data.put_ltp,
                "volume": strike_data.put_volume,
                "oi": strike_data.put_oi,
                "iv": put_iv,
                "delta": delta,
                "gamma": gamma,
                "score": score,
                "strategy_match": get_strategy_match(score, strategy),
                "recommendation": get_option_recommendation(score, "PUT", spot_price / strike),
                "discount_zone": discount_zone,
                "entry_analysis": entry_analysis
            })
    
    # Sort by score (highest first)
    sorted_options = sorted(options, key=lambda x: x["score"], reverse=True)
    
    # =====================================================
    # ENHANCED: Fetch historical context for top 5 options
    # This adds intraday price position analysis for better entry timing
    # =====================================================
    if fetch_historical and expiry_date and len(sorted_options) > 0:
        top_n = min(5, len(sorted_options))
        logger.info(f"📊 Fetching intraday history for top {top_n} options...")
        
        for i in range(top_n):
            opt = sorted_options[i]
            try:
                # Fetch historical context
                hist_ctx = get_option_historical_context(
                    index=index,
                    strike=opt["strike"],
                    option_type=opt["type"],
                    expiry_date=expiry_date,
                    current_ltp=opt["ltp"]
                )
                
                # Re-calculate discount zone with historical context
                if hist_ctx.get("has_history"):
                    enhanced_dz = calculate_discount_zone(
                        option_ltp=opt["ltp"],
                        spot_price=spot_price,
                        strike=opt["strike"],
                        option_type=opt["type"],
                        iv=opt.get("iv", 0.15),
                        delta=opt.get("delta", 0.5),
                        dte=dte,
                        avg_iv=avg_iv,
                        market_momentum=market_momentum,
                        oi_analysis=getattr(next((s for s in chain.strikes if s.strike == opt["strike"]), None), 
                                            'call_analysis' if opt["type"] == "CALL" else 'put_analysis', 'neutral') or 'neutral',
                        historical_context=hist_ctx
                    )
                    sorted_options[i]["discount_zone"] = enhanced_dz
                    sorted_options[i]["historical_context"] = hist_ctx
                    logger.debug(f"✅ Enhanced {opt['type']} {opt['strike']} with intraday data")
                    
            except Exception as e:
                logger.warning(f"Could not enhance {opt['type']} {opt['strike']}: {e}")
    
    return sorted_options


def get_option_historical_context(
    index: str,
    strike: float,
    option_type: str,
    expiry_date: str,
    current_ltp: float
) -> dict:
    """
    Fetch intraday historical context for an option to determine price position.
    
    This helps identify if current LTP is at day high (avoid) or day low (better entry).
    
    Args:
        index: Index name (NIFTY, BANKNIFTY, FINNIFTY)
        strike: Option strike price
        option_type: "CALL" or "PUT"
        expiry_date: Expiry date in YYYY-MM-DD format
        current_ltp: Current Last Traded Price
        
    Returns:
        dict with price position metrics
    """
    from datetime import datetime, timedelta
    
    result = {
        "has_history": False,
        "day_high": current_ltp,
        "day_low": current_ltp,
        "day_open": current_ltp,
        "vwap_estimate": current_ltp,
        "price_range": 0,
        "position_in_range_pct": 50,  # 0 = at day low, 100 = at day high
        "near_day_high": False,
        "near_day_low": False,
        "at_vwap": True,
        "recommendation": "neutral"
    }
    
    try:
        # Build option symbol for Fyers
        # Format: NSE:NIFTY{YYMM}{DD}{STRIKE}{CE/PE}
        # Example: NSE:NIFTY2612323000CE
        
        # Parse expiry date
        exp_dt = datetime.strptime(expiry_date, "%Y-%m-%d")
        exp_yy = exp_dt.strftime("%y")
        exp_mm = exp_dt.strftime("%m")
        exp_dd = exp_dt.strftime("%d")
        
        # Map index to option prefix
        option_prefix_map = {
            "NIFTY": "NIFTY",
            "BANKNIFTY": "BANKNIFTY",
            "FINNIFTY": "FINNIFTY",
            "MIDCPNIFTY": "MIDCPNIFTY"
        }
        
        prefix = option_prefix_map.get(index.upper(), index.upper())
        opt_type_suffix = "CE" if option_type.upper() == "CALL" else "PE"
        
        # Build symbol (e.g., NSE:NIFTY2612323000CE)
        option_symbol = f"NSE:{prefix}{exp_yy}{exp_mm}{exp_dd}{int(strike)}{opt_type_suffix}"
        
        logger.debug(f"📊 Fetching historical context for: {option_symbol}")
        
        # Fetch intraday data (5-min candles for today)
        today = datetime.now()
        market_open = today.replace(hour=9, minute=15, second=0, microsecond=0)
        
        df = fyers_client.get_historical_data(
            symbol=option_symbol,
            resolution="5",  # 5-minute candles
            date_from=market_open,
            date_to=today
        )
        
        if df is not None and not df.empty and len(df) >= 2:
            result["has_history"] = True
            
            # Calculate day metrics
            day_high = float(df['high'].max())
            day_low = float(df['low'].min())
            day_open = float(df['open'].iloc[0])
            
            # VWAP estimate (simplified: volume-weighted average of typical price)
            if 'volume' in df.columns and df['volume'].sum() > 0:
                typical_price = (df['high'] + df['low'] + df['close']) / 3
                vwap = (typical_price * df['volume']).sum() / df['volume'].sum()
            else:
                vwap = (day_high + day_low) / 2
            
            result["day_high"] = round(day_high, 2)
            result["day_low"] = round(day_low, 2)
            result["day_open"] = round(day_open, 2)
            result["vwap_estimate"] = round(vwap, 2)
            
            # Calculate price range and position
            price_range = day_high - day_low
            result["price_range"] = round(price_range, 2)
            
            if price_range > 0:
                position_pct = ((current_ltp - day_low) / price_range) * 100
                result["position_in_range_pct"] = round(max(0, min(100, position_pct)), 1)
            
            # Determine position flags
            # Near day high: within 10% of high or above 90th percentile
            result["near_day_high"] = result["position_in_range_pct"] >= 85
            result["near_day_low"] = result["position_in_range_pct"] <= 15
            
            # Within 5% of VWAP
            if vwap > 0:
                result["at_vwap"] = abs(current_ltp - vwap) / vwap < 0.05
            
            # Generate recommendation
            if result["near_day_high"]:
                result["recommendation"] = "wait_pullback"
            elif result["near_day_low"]:
                result["recommendation"] = "good_entry"
            elif result["at_vwap"]:
                result["recommendation"] = "fair_entry"
            else:
                result["recommendation"] = "neutral"
            
            logger.debug(f"📈 {option_symbol}: LTP={current_ltp}, Range={day_low}-{day_high}, Position={result['position_in_range_pct']:.0f}%, Rec={result['recommendation']}")
        else:
            logger.debug(f"⚠️ No intraday history for {option_symbol}")
            
    except Exception as e:
        logger.warning(f"Could not fetch option historical context: {e}")
    
    return result


def calculate_simple_delta(spot: float, strike: float, option_type: str) -> float:
    """Simplified delta calculation"""
    moneyness = spot / strike
    if option_type == "CALL":
        return max(0.1, min(0.9, 0.5 + (moneyness - 1) * 2))
    else:  # PUT
        return max(-0.9, min(-0.1, -0.5 - (moneyness - 1) * 2))


def calculate_simple_gamma(spot: float, strike: float) -> float:
    """Simplified gamma calculation (ATM options have highest gamma)"""
    diff = abs(spot - strike) / spot
    return 0.002 * max(0.1, (1 - diff * 10))


def calculate_mock_option_price(spot: float, strike: float, option_type: str) -> float:
    """Calculate mock option price"""
    intrinsic = max(0, spot - strike) if option_type == "CALL" else max(0, strike - spot)
    time_value = random.uniform(10, 200)  # Random time value
    return round(intrinsic + time_value, 2)


def calculate_option_strategy_score(spot: float, strike: float, option_type: str, 
                                   volume: int, oi: int, delta: float, gamma: float, 
                                   strategy: str) -> float:
    """Calculate composite score for option strategy matching"""
    score = 0
    
    # Volume score (25%)
    volume_score = min(25, (volume / 5000) * 25)
    
    # OI score (25%)
    oi_score = min(25, (oi / 20000) * 25)
    
    # Liquidity score (20%)
    liquidity_score = min(20, ((volume + oi / 10) / 10000) * 20)
    
    # Strategy-specific scoring (30%)
    strategy_score = 0
    moneyness = spot / strike
    
    if strategy == "momentum":
        # Favor ITM options with good delta
        if abs(delta) > 0.4:
            strategy_score = 30
        elif abs(delta) > 0.2:
            strategy_score = 20
        else:
            strategy_score = 10
    elif strategy == "reversal":
        # Favor OTM options at support/resistance
        if 0.95 <= moneyness <= 1.05:  # Near ATM
            strategy_score = 30
        elif 0.9 <= moneyness <= 1.1:  # Slightly OTM
            strategy_score = 25
        else:
            strategy_score = 10
    elif strategy == "volatility":
        # Favor high gamma options
        if gamma > 0.001:
            strategy_score = 30
        elif gamma > 0.0005:
            strategy_score = 20
        else:
            strategy_score = 10
    else:  # "all"
        strategy_score = 20  # Neutral scoring
    
    return volume_score + oi_score + liquidity_score + strategy_score


def get_strategy_match(score: float, strategy: str) -> str:
    """Get strategy match description"""
    if score >= 80:
        return f"Excellent {strategy} opportunity"
    elif score >= 60:
        return f"Good {strategy} setup"
    elif score >= 40:
        return f"Moderate {strategy} potential"
    else:
        return "Low confidence"


def get_option_recommendation(score: float, option_type: str, moneyness: float) -> str:
    """Get trading recommendation"""
    if score >= 80:
        action = "Strong BUY" if score >= 90 else "BUY"
    elif score >= 60:
        action = "Consider BUY"
    elif score >= 40:
        action = "WATCH"
    else:
        action = "AVOID"
    
    position = "ITM" if (option_type == "CALL" and moneyness > 1) or (option_type == "PUT" and moneyness < 1) else "OTM"
    return f"{action} - {position} {option_type}"


def analyze_entry_quality(
    option_ltp: float,
    spot_price: float,
    strike: float,
    option_type: str,
    discount_zone: dict,
    delta: float,
    dte: int,
    iv: float,
    volume: int,
    oi: int
) -> dict:
    """
    Comprehensive entry quality analysis to determine if current price is a good entry.
    
    This solves the problem of buying at short-term peaks by analyzing:
    1. Is the option in a discount zone or overpriced?
    2. Is there sufficient time to reach the target?
    3. Is liquidity adequate for good fills?
    4. What's the recommended entry price vs current LTP?
    5. Is the trend exhausted or still has momentum?
    
    Returns:
        dict with entry quality metrics and recommended actions
    """
    from src.utils.ist_utils import get_minutes_to_market_close, is_market_open, get_ist_time
    
    result = {
        "entry_grade": "C",           # A, B, C, D, F grades
        "entry_score": 50,            # 0-100 score
        "recommended_entry": option_ltp,
        "limit_order_price": option_ltp,
        "max_acceptable_price": option_ltp * 1.02,
        "wait_for_pullback": False,
        "pullback_target_price": option_ltp,
        "time_feasible": True,
        "time_remaining_minutes": 375,
        "estimated_minutes_to_target": 60,
        "liquidity_grade": "B",
        "theta_impact_per_hour": 0,
        "supports_immediate_entry": True,
        "entry_recommendation": "BUY",
        "reasoning": []
    }
    
    reasoning = []
    entry_score = 50  # Start neutral
    
    # =====================================================
    # 1. DISCOUNT ZONE ANALYSIS
    # =====================================================
    dz_status = discount_zone.get("status", "fair")
    dz_supports_entry = discount_zone.get("supports_entry", True)
    best_entry = discount_zone.get("best_entry_price", option_ltp)
    max_entry = discount_zone.get("max_entry_price", option_ltp * 1.02)
    iv_vs_avg = discount_zone.get("iv_vs_avg_pct", 0)
    expected_pullback = discount_zone.get("expected_pullback_pct", 0)
    
    if dz_status == "deep_discount":
        entry_score += 30
        reasoning.append("✅ DEEP DISCOUNT: IV significantly below average - excellent entry")
    elif dz_status == "discounted":
        entry_score += 20
        reasoning.append("✅ DISCOUNTED: IV below average - good entry zone")
    elif dz_status == "fair":
        entry_score += 5
        reasoning.append("⚡ FAIR VALUE: Consider limit order for better fill")
    elif dz_status == "premium":
        entry_score -= 15
        reasoning.append(f"🔶 PREMIUM: IV elevated +{iv_vs_avg:.0f}% - wait for pullback")
    elif dz_status == "high_premium":
        entry_score -= 30
        reasoning.append(f"🔴 HIGH PREMIUM: IV very elevated +{iv_vs_avg:.0f}% - avoid or wait")
    
    # =====================================================
    # 2. TIME FEASIBILITY CHECK
    # =====================================================
    market_open = is_market_open()
    minutes_remaining = get_minutes_to_market_close() if market_open else 375
    
    # Estimate time to target based on delta and typical index movement
    # Average intraday range for NIFTY/BANKNIFTY is ~1% 
    # With delta of 0.4, option needs ~50-60 points index move for 20 points profit
    avg_option_points_per_hour = abs(delta) * 15  # ~15 index points per hour average
    target_profit_points = option_ltp * 0.25  # Target 25% profit
    
    if avg_option_points_per_hour > 0:
        estimated_hours_to_target = target_profit_points / avg_option_points_per_hour
        estimated_minutes_to_target = estimated_hours_to_target * 60
    else:
        estimated_minutes_to_target = 180  # Default 3 hours
    
    result["time_remaining_minutes"] = minutes_remaining
    result["estimated_minutes_to_target"] = round(estimated_minutes_to_target)
    
    if market_open:
        if minutes_remaining < 60:  # Less than 1 hour to close
            if estimated_minutes_to_target > minutes_remaining:
                entry_score -= 20
                reasoning.append("⏰ TIME CONSTRAINT: Less than 1 hour - target may not be achievable today")
                result["time_feasible"] = False
            else:
                reasoning.append("⏰ Limited time but target seems achievable")
        elif minutes_remaining < 120:  # 1-2 hours
            if estimated_minutes_to_target > minutes_remaining:
                entry_score -= 10
                reasoning.append("⏰ TIME TIGHT: 1-2 hours remaining - reduce position size")
    
    # =====================================================
    # 3. THETA DECAY IMPACT
    # =====================================================
    # Calculate theta impact per hour (simplified)
    # Theta accelerates dramatically as expiry approaches
    if dte <= 0:
        theta_pct_per_hour = 15  # Expiry day - extreme
    elif dte <= 1:
        theta_pct_per_hour = 5   # Last day
    elif dte <= 2:
        theta_pct_per_hour = 2.5  # 2 days
    elif dte <= 5:
        theta_pct_per_hour = 1    # 3-5 days
    else:
        theta_pct_per_hour = 0.3  # More than a week
    
    theta_points_per_hour = option_ltp * theta_pct_per_hour / 100
    result["theta_impact_per_hour"] = round(theta_points_per_hour, 2)
    
    if dte <= 1:
        entry_score -= 15
        reasoning.append(f"⚠️ HIGH THETA: Losing ~₹{theta_points_per_hour:.1f}/hour to decay - quick trade only")
    elif dte <= 2:
        entry_score -= 5
        reasoning.append(f"📉 THETA DECAY: ~₹{theta_points_per_hour:.1f}/hour - time sensitive")
    
    # =====================================================
    # 4. LIQUIDITY ANALYSIS
    # =====================================================
    # Good liquidity = tight spreads, easy fills
    liquidity_score = 0
    
    if volume >= 10000:
        liquidity_score += 40
    elif volume >= 5000:
        liquidity_score += 30
    elif volume >= 1000:
        liquidity_score += 20
    else:
        liquidity_score += 10
        reasoning.append("⚠️ LOW VOLUME: May have difficulty getting fills")
    
    if oi >= 50000:
        liquidity_score += 40
    elif oi >= 20000:
        liquidity_score += 30
    elif oi >= 10000:
        liquidity_score += 20
    else:
        liquidity_score += 10
    
    if liquidity_score >= 70:
        result["liquidity_grade"] = "A"
    elif liquidity_score >= 50:
        result["liquidity_grade"] = "B"
    elif liquidity_score >= 30:
        result["liquidity_grade"] = "C"
        entry_score -= 5
    else:
        result["liquidity_grade"] = "D"
        entry_score -= 10
        reasoning.append("🔶 POOR LIQUIDITY: Wide spreads expected")
    
    # =====================================================
    # 5. CALCULATE RECOMMENDED ENTRY PRICES
    # =====================================================
    
    # If premium zone, recommend waiting for pullback
    if dz_status in ["premium", "high_premium"]:
        result["wait_for_pullback"] = True
        result["pullback_target_price"] = round(best_entry, 2)
        result["supports_immediate_entry"] = False
        result["limit_order_price"] = round(best_entry, 2)
        result["entry_recommendation"] = "WAIT"
    elif expected_pullback > 3:
        # Even at fair value, if pullback expected, suggest limit order
        result["limit_order_price"] = round(option_ltp * (1 - expected_pullback/200), 2)  # Aim for half the pullback
        result["entry_recommendation"] = "LIMIT_ORDER"
        reasoning.append(f"💡 Consider limit order at ₹{result['limit_order_price']:.0f} (expecting {expected_pullback:.0f}% pullback)")
    else:
        result["limit_order_price"] = round(option_ltp * 0.99, 2)  # 1% below LTP
        result["entry_recommendation"] = "BUY"
    
    result["recommended_entry"] = round(best_entry, 2)
    result["max_acceptable_price"] = round(max_entry, 2)
    
    # =====================================================
    # 6. FINAL SCORING AND GRADE
    # =====================================================
    
    # Clamp score between 0-100
    entry_score = max(0, min(100, entry_score))
    result["entry_score"] = entry_score
    
    # Assign grade
    if entry_score >= 80:
        result["entry_grade"] = "A"
        if not any("PREMIUM" in r or "AVOID" in r for r in reasoning):
            reasoning.insert(0, "🟢 EXCELLENT ENTRY: Strong buy opportunity")
    elif entry_score >= 65:
        result["entry_grade"] = "B"
        reasoning.insert(0, "🟡 GOOD ENTRY: Favorable conditions")
    elif entry_score >= 50:
        result["entry_grade"] = "C"
        reasoning.insert(0, "🟠 AVERAGE ENTRY: Proceed with caution")
    elif entry_score >= 35:
        result["entry_grade"] = "D"
        reasoning.insert(0, "🔴 POOR ENTRY: Consider waiting or smaller size")
        result["entry_recommendation"] = "WAIT"
        result["supports_immediate_entry"] = False
    else:
        result["entry_grade"] = "F"
        reasoning.insert(0, "⛔ AVOID: Unfavorable conditions for entry")
        result["entry_recommendation"] = "AVOID"
        result["supports_immediate_entry"] = False
    
    result["reasoning"] = reasoning
    
    return result


def calculate_discount_zone(
    option_ltp: float,
    spot_price: float,
    strike: float,
    option_type: str,
    iv: float,
    delta: float,
    dte: int,
    avg_iv: float = 0.15,  # Historical average IV (15% default for NIFTY)
    market_momentum: str = "neutral",  # "bullish", "bearish", "neutral"
    oi_analysis: str = "neutral",  # "long_build", "short_build", "long_unwind", "short_cover"
    historical_context: dict = None  # Optional: from get_option_historical_context()
) -> dict:
    """
    Calculate if current option price is in a discounted zone.
    
    This function determines whether the recommended buy price lies within a discounted
    zone rather than at an inflated or peak price. It considers:
    1. IV level relative to historical average
    2. Underlying momentum and trend direction
    3. Time feasibility for expected price movement
    4. OI analysis for institutional positioning
    5. Intraday price position (day high/low analysis)
    
    Args:
        option_ltp: Current option LTP (Last Traded Price)
        spot_price: Current underlying spot price
        strike: Option strike price
        option_type: "CALL" or "PUT"
        iv: Current implied volatility (as decimal, e.g., 0.15 for 15%)
        delta: Option delta
        dte: Days to expiry
        avg_iv: Historical average IV (default 15%)
        market_momentum: Current market momentum direction
        oi_analysis: OI-based analysis for positioning
        historical_context: Optional dict from get_option_historical_context()
        
    Returns:
        dict with:
            - status: "deep_discount", "discounted", "fair", "premium"
            - current_price: Current option LTP
            - best_entry_price: Recommended best entry price
            - max_entry_price: Maximum price to pay for entry
            - target_price: Expected target price
            - expected_pullback_pct: Expected % pullback before move
            - time_feasible: Whether time allows for entry setup
            - supports_entry: Boolean - should user enter now
            - reasoning: Explanation of the analysis
            - price_position: Intraday price position metrics (if available)
    """
    
    # Default response structure
    result = {
        "status": "fair",
        "current_price": round(option_ltp, 2),
        "best_entry_price": round(option_ltp, 2),
        "max_entry_price": round(option_ltp * 1.05, 2),
        "target_price": round(option_ltp * 1.3, 2),
        "expected_pullback_pct": 0.0,
        "time_feasible": True,
        "supports_entry": True,
        "reasoning": "Option priced at fair value"
    }
    
    if option_ltp <= 0:
        result["status"] = "invalid"
        result["supports_entry"] = False
        result["reasoning"] = "Invalid option price"
        return result
    
    # =====================================================
    # 1. IV ANALYSIS - Compare current IV to historical average
    # =====================================================
    iv_ratio = iv / avg_iv if avg_iv > 0 else 1.0
    iv_premium_pct = (iv_ratio - 1.0) * 100
    
    # IV Zones:
    # - Deep Discount: IV < 80% of average (rare, often after IV crush)
    # - Discounted: IV between 80-95% of average
    # - Fair: IV between 95-110% of average
    # - Premium: IV between 110-130% of average
    # - High Premium: IV > 130% of average (avoid buying)
    
    iv_zone = "fair"
    if iv_ratio < 0.80:
        iv_zone = "deep_discount"
    elif iv_ratio < 0.95:
        iv_zone = "discounted"
    elif iv_ratio <= 1.10:
        iv_zone = "fair"
    elif iv_ratio <= 1.30:
        iv_zone = "premium"
    else:
        iv_zone = "high_premium"
    
    # =====================================================
    # 2. MOMENTUM ANALYSIS - Does momentum support pullback?
    # =====================================================
    momentum_supports_pullback = False
    expected_pullback_pct = 0.0
    
    # For CALL options: Bullish momentum means price may already be elevated
    # A brief pullback before continuation is often expected
    if option_type == "CALL":
        if market_momentum == "bullish":
            # In bullish trend, expect minor pullback before continuation
            expected_pullback_pct = 3.0 if dte > 3 else 5.0
            momentum_supports_pullback = True
        elif market_momentum == "bearish":
            # Bearish momentum - calls may get cheaper, wait for reversal
            expected_pullback_pct = 8.0 if dte > 3 else 12.0
            momentum_supports_pullback = True
        else:
            expected_pullback_pct = 2.0
            momentum_supports_pullback = dte > 2
    
    # For PUT options: Bearish momentum means price may already be elevated
    elif option_type == "PUT":
        if market_momentum == "bearish":
            expected_pullback_pct = 3.0 if dte > 3 else 5.0
            momentum_supports_pullback = True
        elif market_momentum == "bullish":
            expected_pullback_pct = 8.0 if dte > 3 else 12.0
            momentum_supports_pullback = True
        else:
            expected_pullback_pct = 2.0
            momentum_supports_pullback = dte > 2
    
    # =====================================================
    # 3. OI ANALYSIS - Institutional positioning
    # =====================================================
    oi_supports_entry = True
    oi_reasoning = ""
    
    if option_type == "CALL":
        if oi_analysis == "long_build":
            oi_supports_entry = True
            oi_reasoning = "Institutional long building - bullish"
        elif oi_analysis == "short_build":
            oi_supports_entry = False
            oi_reasoning = "Writers adding positions - wait for pullback"
        elif oi_analysis == "short_cover":
            oi_supports_entry = True
            oi_reasoning = "Short covering - momentum building"
    else:  # PUT
        if oi_analysis == "long_build":
            oi_supports_entry = True
            oi_reasoning = "Institutional put building - bearish"
        elif oi_analysis == "short_build":
            oi_supports_entry = False
            oi_reasoning = "Put writers active - wait for better entry"
        elif oi_analysis == "short_cover":
            oi_supports_entry = True
            oi_reasoning = "Put short covering - downside momentum"
    
    # =====================================================
    # 4. TIME FEASIBILITY CHECK
    # =====================================================
    # Check if there's enough time for the expected pullback and move
    time_feasible = True
    time_warning = ""
    
    if dte <= 1:
        time_feasible = expected_pullback_pct <= 5.0
        time_warning = "Expiry day - very limited time for pullback"
    elif dte <= 2:
        time_feasible = expected_pullback_pct <= 8.0
        time_warning = "Last 2 days - quick entries only"
    elif dte <= 5:
        time_feasible = True
        time_warning = "Sufficient time for setup"
    else:
        time_feasible = True
        time_warning = "Good time horizon"
    
    # Calculate time available in minutes (IST trading hours)
    from src.utils.ist_utils import get_minutes_to_market_close, is_market_open
    minutes_remaining = get_minutes_to_market_close() if is_market_open() else 375  # Full day
    
    # Estimate time needed for pullback (rough heuristic)
    pullback_time_needed = expected_pullback_pct * 10  # ~10 minutes per 1% pullback expected
    time_feasible = time_feasible and (minutes_remaining >= pullback_time_needed or not is_market_open())
    
    # =====================================================
    # 5. CALCULATE ENTRY PRICES
    # =====================================================
    # Best entry: Current price adjusted for expected pullback
    # Max entry: Upper bound still considered acceptable
    
    best_entry_price = option_ltp * (1 - expected_pullback_pct / 100)
    
    # Max entry depends on IV zone
    if iv_zone in ["deep_discount", "discounted"]:
        max_entry_price = option_ltp * 1.02  # Can pay slightly more
    elif iv_zone == "fair":
        max_entry_price = option_ltp * 1.01  # Tight range
    elif iv_zone == "premium":
        max_entry_price = option_ltp * 0.95  # Wait for pullback
        best_entry_price = option_ltp * 0.90
    else:  # high_premium
        max_entry_price = option_ltp * 0.85  # Significant pullback needed
        best_entry_price = option_ltp * 0.80
    
    # Target price based on delta and expected move
    # Simplified: expect 30% gain for ATM options, scaled by delta
    target_multiplier = 1.3 if abs(delta) > 0.4 else (1.5 if abs(delta) > 0.2 else 1.2)
    target_price = option_ltp * target_multiplier
    
    # =====================================================
    # 6. DETERMINE FINAL STATUS AND RECOMMENDATION
    # =====================================================
    
    # Combine all factors
    if iv_zone in ["deep_discount", "discounted"]:
        if oi_supports_entry and time_feasible:
            status = iv_zone
            supports_entry = True
            reasoning = f"✅ {iv_zone.upper()}: IV {iv_premium_pct:+.1f}% vs avg. {oi_reasoning}. {time_warning}"
        else:
            status = iv_zone
            supports_entry = time_feasible
            reasoning = f"⚠️ {iv_zone.upper()}: IV low but {oi_reasoning}. {time_warning}"
    
    elif iv_zone == "fair":
        if oi_supports_entry and momentum_supports_pullback and time_feasible:
            status = "fair"
            supports_entry = True
            reasoning = f"✅ FAIR VALUE: IV normal. {oi_reasoning}. Expect {expected_pullback_pct:.0f}% pullback window."
        elif time_feasible:
            status = "fair"
            supports_entry = True
            reasoning = f"⚠️ FAIR VALUE: Consider limit order at ₹{best_entry_price:.2f} for better entry."
        else:
            status = "fair"
            supports_entry = False
            reasoning = f"⏳ FAIR VALUE but time constrained. {time_warning}"
    
    elif iv_zone == "premium":
        status = "premium"
        supports_entry = False
        best_entry_price = option_ltp * 0.90  # Need 10% pullback
        reasoning = f"🔶 PREMIUM: IV +{iv_premium_pct:.0f}% elevated. Wait for pullback to ₹{best_entry_price:.2f}."
    
    else:  # high_premium
        status = "high_premium"
        supports_entry = False
        best_entry_price = option_ltp * 0.80
        reasoning = f"🔴 HIGH PREMIUM: IV +{iv_premium_pct:.0f}% very elevated. Avoid or wait for significant pullback."
    
    # =====================================================
    # 7. INCORPORATE HISTORICAL PRICE POSITION
    # =====================================================
    price_position = None
    if historical_context and historical_context.get("has_history"):
        price_position = {
            "day_high": historical_context.get("day_high"),
            "day_low": historical_context.get("day_low"),
            "vwap": historical_context.get("vwap_estimate"),
            "position_in_range_pct": historical_context.get("position_in_range_pct", 50),
            "near_day_high": historical_context.get("near_day_high", False),
            "near_day_low": historical_context.get("near_day_low", False),
            "intraday_recommendation": historical_context.get("recommendation", "neutral")
        }
        
        # Adjust supports_entry based on intraday position
        if historical_context.get("near_day_high"):
            # Option is at intraday high - recommend waiting even if IV looks good
            if supports_entry:
                supports_entry = False  # Override to wait
                reasoning += " ⚠️ Also at intraday HIGH - wait for pullback."
        elif historical_context.get("near_day_low"):
            # Option is at intraday low - this is a good entry point
            if status in ["fair", "discounted", "deep_discount"]:
                reasoning += " ✅ Also at intraday LOW - excellent entry zone!"
    
    result = {
        "status": status,
        "current_price": round(option_ltp, 2),
        "best_entry_price": round(best_entry_price, 2),
        "max_entry_price": round(max_entry_price, 2),
        "target_price": round(target_price, 2),
        "expected_pullback_pct": round(expected_pullback_pct, 1),
        "iv_vs_avg_pct": round(iv_premium_pct, 1),
        "time_feasible": time_feasible,
        "minutes_remaining": minutes_remaining,
        "supports_entry": supports_entry,
        "momentum_direction": market_momentum,
        "reasoning": reasoning,
        "price_position": price_position
    }
    
    return result


# =============================================================================
# INDEX PROBABILITY ANALYSIS ENDPOINTS
# =============================================================================

# Import index analysis modules
try:
    from src.analytics.index_constituents import index_manager, IndexConstituentsManager
    from src.analytics.index_probability_analyzer import (
        IndexProbabilityAnalyzer, 
        get_probability_analyzer,
        IndexPrediction,
        StockSignal,
        SectorAnalysis,
        MarketRegime
    )
    from src.ml.index_ml_optimizer import IndexMLOptimizer, get_ml_optimizer
    INDEX_ANALYSIS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Index analysis modules not available: {e}")
    INDEX_ANALYSIS_AVAILABLE = False


@app.get("/index/probability/{index_name}")
async def analyze_index_probability(
    index_name: str,
    include_ml: bool = Query(True, description="Include ML optimization"),
    include_stocks: bool = Query(True, description="Include individual stock signals"),
    include_sectors: bool = Query(True, description="Include sector breakdown"),
    authorization: str = Header(None, description="Bearer token")
):
    """
    Comprehensive probability-based analysis for index movement
    
    Scans ALL constituent stocks of the index and predicts index direction using:
    - Market-cap weighted aggregation of all stocks
    - Probability-weighted signals (not binary buy/sell)
    - Sector-level analysis
    - Correlation filtering
    - Regime detection (trend/range/volatile)
    - Volume analysis for each stock
    - ML optimization (optional)
    
    For NIFTY50: Scans all 50 constituent stocks
    For BANKNIFTY: Scans all 14 constituent bank stocks
    For SENSEX: Scans all 30 constituent stocks
    For FINNIFTY: Scans all 20 financial stocks
    
    Args:
        index_name: NIFTY, BANKNIFTY, SENSEX, or FINNIFTY
        include_ml: Whether to apply ML optimization
        include_stocks: Include individual stock signals in response
        include_sectors: Include sector breakdown in response
        authorization: Auth token
        
    Returns:
        Complete probability analysis with expected index move
    """
    if not INDEX_ANALYSIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Index analysis modules not available")
    
    index_name = index_name.upper()
    valid_indices = ["NIFTY", "NIFTY50", "BANKNIFTY", "SENSEX", "FINNIFTY"]
    
    if index_name not in valid_indices:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid index. Supported: {valid_indices}"
        )
    
    try:
        # Get constituent count for this index
        constituents = index_manager.get_constituents(index_name)
        stock_count = len(constituents) if constituents else 0
        
        logger.info(f"🎯 Index probability analysis for {index_name} - Scanning {stock_count} constituent stocks")
        
        # Perform live analysis - this scans ALL constituent stocks
        analyzer = get_probability_analyzer(fyers_client)
        prediction = analyzer.analyze_index(index_name)
        
        # Apply ML optimization if requested
        ml_data = None
        if include_ml:
            try:
                ml_optimizer = get_ml_optimizer()
                
                # Get historical data for ML
                index_symbol = analyzer._get_index_symbol(index_name)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=120)
                
                df = fyers_client.get_historical_data(
                    symbol=index_symbol,
                    resolution="D",
                    date_from=start_date,
                    date_to=end_date
                )
                
                if df is not None and len(df) >= 60:
                    ml_pred = ml_optimizer.predict(index_name, df)
                    if ml_pred:
                        ml_data = {
                            "predicted_direction": ml_pred.predicted_direction,
                            "probability_up": round(ml_pred.probability_up, 3),
                            "probability_down": round(ml_pred.probability_down, 3),
                            "probability_flat": round(ml_pred.probability_flat, 3),
                            "ml_confidence": round(ml_pred.confidence, 1),
                            "model_type": ml_pred.model_type,
                            "top_features": ml_pred.feature_importance
                        }
            except Exception as ml_error:
                logger.warning(f"ML optimization skipped: {ml_error}")
        
        # Calculate expected point movement and range from current level
        current_level = prediction.current_level or 0
        expected_move_pct = prediction.expected_move_pct

        # Expected point movement = current_level × (expected_move_pct / 100)
        expected_points = round(current_level * (expected_move_pct / 100), 2) if current_level > 0 else 0

        # Calculate expected range (using typical daily volatility as spread)
        # Use regime's ATR percentile to estimate range spread
        atr_spread = prediction.regime.atr_percentile / 100 * 0.02  # Convert to decimal spread factor
        range_spread = max(0.005, min(0.02, atr_spread))  # Clamp between 0.5% and 2%

        if expected_move_pct >= 0:
            # Bullish: upside target further, downside closer
            expected_high = round(current_level * (1 + abs(expected_move_pct) / 100 + range_spread), 2)
            expected_low = round(current_level * (1 - range_spread / 2), 2)
        else:
            # Bearish: downside target further, upside closer
            expected_high = round(current_level * (1 + range_spread / 2), 2)
            expected_low = round(current_level * (1 - abs(expected_move_pct) / 100 - range_spread), 2)

        # Build response
        response = {
            "status": "success",
            "index": index_name,
            "stocks_scanned": prediction.total_stocks_analyzed,
            "timestamp": prediction.timestamp.isoformat(),
            "current_level": current_level,

            # Main prediction with POINT MOVEMENTS
            "prediction": {
                "expected_direction": prediction.expected_direction,
                "expected_move_pct": round(expected_move_pct, 3),
                "expected_points": expected_points,
                "expected_range": {
                    "high": expected_high,
                    "low": expected_low,
                    "points_up": round(expected_high - current_level, 2) if current_level > 0 else 0,
                    "points_down": round(current_level - expected_low, 2) if current_level > 0 else 0
                },
                "confidence": round(prediction.prediction_confidence, 1),
                "probability_up": round(prediction.prob_up, 3),
                "probability_down": round(prediction.prob_down, 3),
                "probability_neutral": round(prediction.prob_neutral, 3)
            },
            
            # Market regime
            "regime": {
                "type": prediction.regime.regime.value,
                "adx": round(prediction.regime.adx_value, 1),
                "volatility_level": prediction.regime.volatility_level,
                "trend_strength": round(prediction.regime.trend_strength, 1),
                "atr_percentile": round(prediction.regime.atr_percentile, 1)
            },
            
            # Stock summary
            "stock_summary": {
                "total_analyzed": prediction.total_stocks_analyzed,
                "bullish": prediction.bullish_stocks,
                "bearish": prediction.bearish_stocks,
                "neutral": prediction.neutral_stocks,
                "bullish_pct": round(prediction.bullish_stocks / max(prediction.total_stocks_analyzed, 1) * 100, 1),
                "bearish_pct": round(prediction.bearish_stocks / max(prediction.total_stocks_analyzed, 1) * 100, 1)
            },
            
            # Top contributors
            "top_bullish_contributors": [
                {
                    "symbol": s.symbol.replace("NSE:", "").replace("-EQ", ""),
                    "name": s.name,
                    "weight_pct": round(s.weight * 100, 2),
                    "expected_move": round(s.expected_move_pct, 2),
                    "probability": round(s.probability, 2),
                    "contribution": round(s.weighted_contribution * 100, 4),
                    "confidence": round(s.confidence_score, 1)
                }
                for s in prediction.top_bullish_contributors[:5]
            ],
            
            "top_bearish_contributors": [
                {
                    "symbol": s.symbol.replace("NSE:", "").replace("-EQ", ""),
                    "name": s.name,
                    "weight_pct": round(s.weight * 100, 2),
                    "expected_move": round(s.expected_move_pct, 2),
                    "probability": round(s.probability, 2),
                    "contribution": round(s.weighted_contribution * 100, 4),
                    "confidence": round(s.confidence_score, 1)
                }
                for s in prediction.top_bearish_contributors[:5]
            ],
            
            # ML prediction (if available)
            "ml_prediction": ml_data
        }

        # Add strike price recommendations based on expected range
        if current_level > 0:
            # Determine strike interval based on index
            if "BANK" in index_name.upper():
                strike_interval = 100  # BANKNIFTY uses 100-point strikes
            elif "FIN" in index_name.upper():
                strike_interval = 50   # FINNIFTY uses 50-point strikes
            else:
                strike_interval = 50   # NIFTY uses 50-point strikes

            # Calculate ATM strike
            atm_strike = round(current_level / strike_interval) * strike_interval

            # Recommended strikes based on direction and range
            if prediction.expected_direction == "BULLISH":
                # For bullish: recommend CE options
                target_strike = round(expected_high / strike_interval) * strike_interval
                response["option_recommendation"] = {
                    "bias": "BULLISH",
                    "recommended_option": "CE (Call)",
                    "atm_strike": atm_strike,
                    "target_strike": target_strike,
                    "suggested_strikes": {
                        "aggressive": atm_strike,  # ATM for higher delta
                        "moderate": atm_strike + strike_interval,  # 1 OTM
                        "conservative": atm_strike + (strike_interval * 2)  # 2 OTM
                    },
                    "expected_target": expected_high,
                    "stop_loss_level": expected_low,
                    "points_to_target": round(expected_high - current_level, 2),
                    "risk_reward": f"Risk {round(current_level - expected_low, 0)} pts for {round(expected_high - current_level, 0)} pts gain"
                }
            elif prediction.expected_direction == "BEARISH":
                # For bearish: recommend PE options
                target_strike = round(expected_low / strike_interval) * strike_interval
                response["option_recommendation"] = {
                    "bias": "BEARISH",
                    "recommended_option": "PE (Put)",
                    "atm_strike": atm_strike,
                    "target_strike": target_strike,
                    "suggested_strikes": {
                        "aggressive": atm_strike,  # ATM for higher delta
                        "moderate": atm_strike - strike_interval,  # 1 OTM
                        "conservative": atm_strike - (strike_interval * 2)  # 2 OTM
                    },
                    "expected_target": expected_low,
                    "stop_loss_level": expected_high,
                    "points_to_target": round(current_level - expected_low, 2),
                    "risk_reward": f"Risk {round(expected_high - current_level, 0)} pts for {round(current_level - expected_low, 0)} pts gain"
                }
            else:
                response["option_recommendation"] = {
                    "bias": "NEUTRAL",
                    "recommended_option": "Iron Condor / Strangle",
                    "atm_strike": atm_strike,
                    "range_high": expected_high,
                    "range_low": expected_low,
                    "suggestion": "Consider range-bound strategies or wait for clearer direction"
                }

        # Add sector analysis if requested
        if include_sectors and prediction.sector_analysis:
            response["sector_analysis"] = {
                sector_name: {
                    "sector_weight": round(sector.sector_weight, 2),
                    "stock_count": sector.stock_count,
                    "expected_move": round(sector.expected_sector_move, 3),
                    "avg_probability": round(sector.avg_probability, 2),
                    "signal": sector.sector_signal.value,
                    "confidence": round(sector.sector_confidence, 1),
                    "bullish_stocks": sector.bullish_stock_count,
                    "bearish_stocks": sector.bearish_stock_count,
                    "neutral_stocks": sector.neutral_stock_count
                }
                for sector_name, sector in prediction.sector_analysis.items()
            }
        
        # Add individual stock signals if requested
        if include_stocks:
            response["stock_signals"] = [
                {
                    "symbol": s.symbol.replace("NSE:", "").replace("-EQ", ""),
                    "name": s.name,
                    "sector": s.sector.value,
                    "weight_pct": round(s.weight * 100, 2),
                    "current_price": round(s.current_price, 2),
                    "price_change_pct": round(s.price_change_pct, 2),
                    "signal": s.signal_type.value,
                    "probability": round(s.probability, 2),
                    "expected_move": round(s.expected_move_pct, 2),
                    "contribution": round(s.weighted_contribution * 100, 4),
                    "confidence": round(s.confidence_score, 1),
                    "rsi": round(s.rsi, 1),
                    "trend": s.trend_direction,
                    "ema_alignment": s.ema_alignment,
                    "vwap_position": s.vwap_position,
                    "volume_surge": s.volume_surge,
                    "correlation": round(s.correlation_with_index, 2),
                    "bullish_factors": s.bullish_factors[:3],
                    "bearish_factors": s.bearish_factors[:3]
                }
                for s in sorted(prediction.stock_signals, key=lambda x: x.weight, reverse=True)
            ]
        
        return response
        
    except Exception as e:
        logger.error(f"Index probability analysis error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Check if it's an authentication error
        error_str = str(e).lower()
        if "authenticate" in error_str or "401" in error_str or "unauthorized" in error_str:
            raise HTTPException(
                status_code=401, 
                detail="Fyers API authentication required. Please log in to Fyers first."
            )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/surge-candidates/{index_name}")
async def get_surge_candidates(
    index_name: str,
    min_expected_move: float = Query(2.0, description="Minimum expected % move"),
    limit: int = Query(10, description="Maximum results")
):
    """
    Identify constituent stocks preparing for strong upward surge
    
    Scans ALL stocks in the index and returns those with:
    - Strong buy signals
    - High expected upward move (>= min_expected_move)
    - Good confidence scores (>= 60%)
    - Volume confirmation
    """
    if not INDEX_ANALYSIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Index analysis modules not available")
    
    try:
        analyzer = get_probability_analyzer(fyers_client)
        candidates = analyzer.get_surge_candidates(index_name.upper(), min_expected_move)
        
        return {
            "status": "success",
            "index": index_name.upper(),
            "min_expected_move": min_expected_move,
            "total_candidates": len(candidates),
            "candidates": [
                {
                    "symbol": s.symbol.replace("NSE:", "").replace("-EQ", ""),
                    "name": s.name,
                    "sector": s.sector.value,
                    "weight_pct": round(s.weight * 100, 2),
                    "current_price": round(s.current_price, 2),
                    "expected_move": round(s.expected_move_pct, 2),
                    "probability": round(s.probability, 2),
                    "confidence": round(s.confidence_score, 1),
                    "signal": s.signal_type.value,
                    "bullish_factors": s.bullish_factors[:3]
                }
                for s in candidates[:limit]
            ]
        }
    except Exception as e:
        logger.error(f"Surge candidates error: {e}")
        error_str = str(e).lower()
        if "authenticate" in error_str or "401" in error_str:
            raise HTTPException(status_code=401, detail="Fyers API authentication required")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/exhaustion-candidates/{index_name}")
async def get_exhaustion_candidates(
    index_name: str,
    min_expected_decline: float = Query(-2.0, description="Minimum expected % decline"),
    limit: int = Query(10, description="Maximum results")
):
    """
    Identify constituent stocks showing exhaustion (peak zones for selling)
    
    Scans ALL stocks in the index and returns those with:
    - Strong sell signals
    - High expected downward move (<= min_expected_decline)
    - Good confidence scores (>= 60%)
    - Overbought conditions (RSI > 70)
    """
    if not INDEX_ANALYSIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Index analysis modules not available")
    
    try:
        analyzer = get_probability_analyzer(fyers_client)
        candidates = analyzer.get_exhaustion_candidates(index_name.upper(), min_expected_decline)
        
        return {
            "status": "success",
            "index": index_name.upper(),
            "min_expected_decline": min_expected_decline,
            "total_candidates": len(candidates),
            "candidates": [
                {
                    "symbol": s.symbol.replace("NSE:", "").replace("-EQ", ""),
                    "name": s.name,
                    "sector": s.sector.value,
                    "weight_pct": round(s.weight * 100, 2),
                    "current_price": round(s.current_price, 2),
                    "expected_move": round(s.expected_move_pct, 2),
                    "probability": round(s.probability, 2),
                    "confidence": round(s.confidence_score, 1),
                    "signal": s.signal_type.value,
                    "bearish_factors": s.bearish_factors[:3]
                }
                for s in candidates[:limit]
            ]
        }
    except Exception as e:
        logger.error(f"Exhaustion candidates error: {e}")
        error_str = str(e).lower()
        if "authenticate" in error_str or "401" in error_str:
            raise HTTPException(status_code=401, detail="Fyers API authentication required")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/constituents/{index_name}")
async def get_index_constituents(index_name: str):
    """
    Get constituent stocks and weights for an index
    """
    if not INDEX_ANALYSIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Index analysis modules not available")
    
    constituents = index_manager.get_constituents(index_name.upper())
    if not constituents:
        raise HTTPException(status_code=404, detail=f"Index not found: {index_name}")
    
    return {
        "status": "success",
        "index": index_name.upper(),
        "total_stocks": len(constituents),
        "total_weight": round(sum(c.weight for c in constituents), 2),
        "constituents": [
            {
                "symbol": c.symbol,
                "fyers_symbol": c.fyers_symbol,
                "name": c.name,
                "weight": c.weight,
                "sector": c.sector.value,
                "beta": c.beta,
                "avg_correlation": c.avg_correlation
            }
            for c in sorted(constituents, key=lambda x: x.weight, reverse=True)
        ]
    }


@app.get("/index/sector-weights/{index_name}")
async def get_sector_weights(index_name: str):
    """
    Get sector weight breakdown for an index
    """
    if not INDEX_ANALYSIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Index analysis modules not available")
    
    sector_weights = index_manager.get_sector_weights(index_name.upper())
    sector_stocks = index_manager.get_stocks_by_sector(index_name.upper())
    
    if not sector_weights:
        raise HTTPException(status_code=404, detail=f"Index not found: {index_name}")
    
    return {
        "status": "success",
        "index": index_name.upper(),
        "sectors": [
            {
                "sector": sector.value,
                "weight": round(weight, 2),
                "stock_count": len(sector_stocks.get(sector, []))
            }
            for sector, weight in sorted(sector_weights.items(), key=lambda x: x[1], reverse=True)
        ]
    }


@app.get("/index/list")
async def list_supported_indices():
    """
    Get list of all supported indices for probability analysis
    """
    if not INDEX_ANALYSIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Index analysis modules not available")
    
    indices = index_manager.get_all_indices()
    
    return {
        "status": "success",
        "indices": [
            {
                "name": idx,
                "constituents_count": len(index_manager.get_constituents(idx)),
                "total_weight": round(index_manager.get_index_total_weight(idx), 2)
            }
            for idx in indices
        ]
    }


@app.post("/index/train-ml/{index_name}")
async def train_ml_model(
    index_name: str,
    days: int = Query(365, description="Days of historical data to use"),
    authorization: str = Header(None, description="Bearer token")
):
    """
    Train ML model for index prediction
    
    Uses historical data to train classification model for
    predicting index direction (UP/DOWN/FLAT)
    """
    if not INDEX_ANALYSIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Index analysis modules not available")
    
    try:
        from src.analytics.index_probability_analyzer import get_probability_analyzer
        
        analyzer = get_probability_analyzer(fyers_client)
        ml_optimizer = get_ml_optimizer()
        
        # Get historical data
        index_symbol = analyzer._get_index_symbol(index_name.upper())
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = fyers_client.get_historical_data(
            symbol=index_symbol,
            resolution="D",
            date_from=start_date,
            date_to=end_date
        )
        
        if df is None or len(df) < 100:
            raise HTTPException(
                status_code=400, 
                detail="Insufficient historical data for training"
            )
        
        # Train model
        metrics = ml_optimizer.train(index_name.upper(), df)
        
        # Save model
        ml_optimizer.save_model(index_name.upper())
        
        return {
            "status": "success",
            "index": index_name.upper(),
            "training_metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"ML training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/ml-status")
async def get_ml_model_status():
    """
    Get status of trained ML models
    """
    if not INDEX_ANALYSIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Index analysis modules not available")
    
    try:
        ml_optimizer = get_ml_optimizer()
        return {
            "status": "success",
            "models": ml_optimizer.get_model_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/quick-analysis/{index_name}")
async def quick_index_analysis(index_name: str):
    """
    Quick analysis summary for an index
    
    Returns a lightweight summary without individual stock details
    """
    if not INDEX_ANALYSIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Index analysis modules not available")
    
    try:
        analyzer = get_probability_analyzer(fyers_client)
        prediction = analyzer.analyze_index(index_name.upper())
        
        # Determine action recommendation
        if prediction.expected_direction == "BULLISH" and prediction.prediction_confidence >= 60:
            action = "Consider CALL options"
            action_strength = "Strong" if prediction.prediction_confidence >= 75 else "Moderate"
        elif prediction.expected_direction == "BEARISH" and prediction.prediction_confidence >= 60:
            action = "Consider PUT options"
            action_strength = "Strong" if prediction.prediction_confidence >= 75 else "Moderate"
        else:
            action = "Wait for clearer signals"
            action_strength = "Weak"
        
        return {
            "status": "success",
            "index": index_name.upper(),
            "timestamp": prediction.timestamp.isoformat(),
            "summary": {
                "direction": prediction.expected_direction,
                "expected_move": f"{prediction.expected_move_pct:+.2f}%",
                "confidence": f"{prediction.prediction_confidence:.0f}%",
                "regime": prediction.regime.regime.value,
                "action": action,
                "action_strength": action_strength
            },
            "probabilities": {
                "up": f"{prediction.prob_up * 100:.1f}%",
                "down": f"{prediction.prob_down * 100:.1f}%",
                "neutral": f"{prediction.prob_neutral * 100:.1f}%"
            },
            "stock_breakdown": {
                "total": prediction.total_stocks_analyzed,
                "bullish": f"{prediction.bullish_stocks} ({prediction.bullish_stocks/max(prediction.total_stocks_analyzed,1)*100:.0f}%)",
                "bearish": f"{prediction.bearish_stocks} ({prediction.bearish_stocks/max(prediction.total_stocks_analyzed,1)*100:.0f}%)",
                "neutral": f"{prediction.neutral_stocks} ({prediction.neutral_stocks/max(prediction.total_stocks_analyzed,1)*100:.0f}%)"
            }
        }
        
    except Exception as e:
        logger.error(f"Quick analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug_mode
    )


