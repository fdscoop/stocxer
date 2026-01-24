"""
Billing and Subscription Data Models
Pydantic models for hybrid subscription + PAYG billing system
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime, date
from decimal import Decimal


# ============================================
# SUBSCRIPTION MODELS
# ============================================

class PlanLimits(BaseModel):
    """Subscription plan limits configuration"""
    plan_type: str
    daily_option_scans: Optional[int] = None  # None = unlimited
    daily_stock_scans: Optional[int] = None
    bulk_scan_limit: Optional[int] = None
    daily_bulk_scans: Optional[int] = None
    has_accuracy_tracking: bool = False
    has_priority_support: bool = False
    has_historical_data: bool = False
    has_early_access: bool = False


class UserSubscription(BaseModel):
    """User subscription details"""
    id: str
    user_id: str
    plan_type: str  # 'free', 'medium', 'pro'
    status: str  # 'active', 'cancelled', 'expired', 'trial'
    razorpay_subscription_id: Optional[str] = None
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SubscriptionRequest(BaseModel):
    """Request to create or update subscription"""
    plan_type: str = Field(..., pattern="^(medium|pro)$")
    
    @validator('plan_type')
    def validate_plan(cls, v):
        if v not in ['medium', 'pro']:
            raise ValueError('Plan must be medium or pro')
        return v


class SubscriptionCancelRequest(BaseModel):
    """Request to cancel subscription"""
    cancel_immediately: bool = False  # If True, cancel now. If False, at period end


# ============================================
# CREDITS (PAYG) MODELS
# ============================================

class UserCredits(BaseModel):
    """User credit balance"""
    user_id: str
    balance: Decimal
    lifetime_purchased: Decimal = Decimal('0')
    lifetime_spent: Decimal = Decimal('0')
    last_topped_up: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat() if v else None
        }


class CreditPack(BaseModel):
    """Available credit pack for purchase"""
    id: str
    name: str
    amount_inr: int  # Amount in INR
    credits: Decimal
    bonus_credits: Decimal = Decimal('0')
    is_active: bool = True
    
    @property
    def total_credits(self) -> Decimal:
        return self.credits + self.bonus_credits
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class CreditPurchaseRequest(BaseModel):
    """Request to purchase credits"""
    pack_id: str  # ID of the credit pack to purchase
    

class CreditTransaction(BaseModel):
    """Credit transaction record"""
    id: str
    user_id: str
    transaction_type: str  # 'purchase', 'debit', 'refund', 'bonus'
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    description: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    scan_type: Optional[str] = None
    scan_count: Optional[int] = None
    created_at: datetime
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


# ============================================
# USAGE TRACKING MODELS
# ============================================

class UsageLog(BaseModel):
    """Daily usage log for subscription users"""
    user_id: str
    scan_type: str  # 'option_scan', 'stock_scan', 'bulk_scan'
    count: int
    usage_date: date
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class TodayUsage(BaseModel):
    """Today's usage summary"""
    option_scans: int = 0
    stock_scans: int = 0
    bulk_scans: int = 0


# ============================================
# BILLING STATUS MODELS
# ============================================

class UserBillingStatus(BaseModel):
    """Complete billing status for a user"""
    user_id: str
    billing_type: str  # 'subscription' or 'payg'
    
    # Subscription info
    plan_type: str  # 'free', 'medium', 'pro', or 'payg'
    subscription_active: bool
    subscription_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    
    # Credits info
    credits_balance: Decimal = Decimal('0')
    
    # Usage info
    today_usage: TodayUsage
    limits: PlanLimits
    
    # Computed fields
    can_use_credits: bool = True
    has_active_subscription: bool = False
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat() if v else None
        }


class BillingCheckResult(BaseModel):
    """Result of billing check for an action"""
    allowed: bool
    reason: str
    billing_type: str  # 'subscription', 'credits', 'free_tier'
    cost: Optional[Decimal] = None  # Cost in INR if using credits
    remaining_balance: Optional[Decimal] = None
    usage_after: Optional[TodayUsage] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }


# ============================================
# PAYMENT MODELS
# ============================================

class PaymentHistory(BaseModel):
    """Payment record"""
    id: str
    user_id: str
    payment_type: str  # 'subscription', 'credits', 'refund'
    amount_inr: int  # In paisa
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    status: str  # 'created', 'pending', 'captured', 'failed', 'refunded'
    payment_method: Optional[str] = None
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RazorpayOrderRequest(BaseModel):
    """Request to create Razorpay order"""
    amount: int  # Amount in paisa (₹100 = 10000)
    currency: str = "INR"
    receipt: str
    notes: Optional[Dict[str, str]] = None


class RazorpayOrderResponse(BaseModel):
    """Razorpay order creation response"""
    order_id: str
    amount: int
    currency: str
    key_id: str  # Razorpay key for frontend


class RazorpayPaymentVerification(BaseModel):
    """Payment verification from frontend"""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_type: Optional[str] = None  # For subscription payments


class RazorpayWebhookEvent(BaseModel):
    """Webhook event from Razorpay"""
    event: str
    payload: Dict
    created_at: int


# ============================================
# PRICING CONFIGURATION
# ============================================

class PricingConfig(BaseModel):
    """Pricing configuration constants"""
    # PAYG Pricing (in INR)
    OPTION_SCAN_PRICE: Decimal = Decimal('0.98')
    STOCK_SCAN_PRICE: Decimal = Decimal('0.85')
    BULK_SCAN_BASE_PRICE: Decimal = Decimal('5.00')
    BULK_SCAN_PER_STOCK: Decimal = Decimal('0.50')
    
    # Subscription Pricing (in INR)
    MEDIUM_PLAN_MONTHLY: int = 499
    PRO_PLAN_MONTHLY: int = 999
    MEDIUM_PLAN_ANNUAL: int = 4990  # 2 months free
    PRO_PLAN_ANNUAL: int = 9990  # 2 months free
    
    @staticmethod
    def calculate_scan_cost(scan_type: str, count: int = 1) -> Decimal:
        """Calculate cost for a scan operation"""
        if scan_type == 'option_scan':
            return Decimal(str(count)) * PricingConfig.OPTION_SCAN_PRICE
        elif scan_type == 'stock_scan':
            return Decimal(str(count)) * PricingConfig.STOCK_SCAN_PRICE
        elif scan_type == 'bulk_scan':
            return PricingConfig.BULK_SCAN_BASE_PRICE + (Decimal(str(count)) * PricingConfig.BULK_SCAN_PER_STOCK)
        else:
            raise ValueError(f"Unknown scan type: {scan_type}")


# ============================================
# DASHBOARD MODELS
# ============================================

class BillingDashboard(BaseModel):
    """Complete billing dashboard data"""
    billing_status: UserBillingStatus
    recent_transactions: List[CreditTransaction] = []
    available_credit_packs: List[CreditPack] = []
    recent_payments: List[PaymentHistory] = []
    usage_history: List[UsageLog] = []  # Last 7 days
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


# ============================================
# ERROR MODELS
# ============================================

class BillingError(BaseModel):
    """Billing error response"""
    error: str
    error_code: str
    message: str
    details: Optional[Dict] = None
