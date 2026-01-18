"""
Authentication and User Management
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """User registration model"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse
    expires_at: Optional[datetime] = None
    message: Optional[str] = None  # For email confirmation messages


class FyersTokenStore(BaseModel):
    """Fyers token storage model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None


class FyersTokenResponse(BaseModel):
    """Fyers token response"""
    id: str
    user_id: str
    access_token: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ScreenerResultModel(BaseModel):
    """Screener result database model"""
    scan_id: str
    symbol: str
    name: str
    current_price: float
    action: str
    confidence: float
    target_1: Optional[float] = None
    target_2: Optional[float] = None
    stop_loss: Optional[float] = None
    rsi: Optional[float] = None
    sma_5: Optional[float] = None
    sma_15: Optional[float] = None
    momentum_5d: Optional[float] = None
    volume_surge: bool = False
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    reasons: Optional[list] = None
    scan_params: Optional[dict] = None


class ScreenerScanModel(BaseModel):
    """Screener scan session model"""
    scan_id: str
    stocks_scanned: int
    total_signals: int
    buy_signals: int
    sell_signals: int
    min_confidence: float
    scan_params: Optional[dict] = None
