"""
Token Billing Middleware
Pre-API validation for token balance and usage deduction
"""
from fastapi import HTTPException, Header
from typing import Optional, Dict
from decimal import Decimal
from enum import Enum

from src.services.billing_service import billing_service


class ScanType(str, Enum):
    """Types of scans with different token costs"""
    STOCK_SCAN = "stock_scan"
    OPTION_SCAN = "option_scan"
    CHART_SCAN = "chart_scan"
    BULK_SCAN = "bulk_scan"


# Token costs per action (PAYG Pricing - ₹1 = 1 credit, No expiry on credits)
# Stock Scan: ₹0.85 per scan (technical analysis of individual stocks)
# Option Scan: ₹0.98 per scan (comprehensive option chain analysis with Greeks)
# Chart Scan: ₹0.50 per chart (price action & pattern analysis)
# Bulk Scan: ₹5.00 per scan (scan up to 50 stocks simultaneously)
TOKEN_COSTS = {
    ScanType.STOCK_SCAN: Decimal("0.85"),    # ₹0.85 per stock scan
    ScanType.OPTION_SCAN: Decimal("0.98"),   # ₹0.98 per option scan  
    ScanType.CHART_SCAN: Decimal("0.50"),    # ₹0.50 per chart
    ScanType.BULK_SCAN: Decimal("5.00")      # ₹5.00 per bulk scan
}


class TokenValidationResult:
    """Result of token validation check"""
    def __init__(self, allowed: bool, message: str, balance_after: Optional[Decimal] = None):
        self.allowed = allowed
        self.message = message
        self.balance_after = balance_after


async def validate_and_deduct_tokens(
    user_id: str, 
    scan_type: ScanType,
    scan_count: int = 1,
    metadata: Optional[Dict] = None
) -> TokenValidationResult:
    """
    Validate user has sufficient tokens and deduct if allowed
    
    Logic:
    1. If user has active subscription, check limits first
    2. If subscription limit exceeded OR no subscription, use wallet
    3. Block request if insufficient wallet balance
    
    Args:
        user_id: User ID
        scan_type: Type of scan being performed
        scan_count: Number of scans (for bulk operations)
        metadata: Additional scan metadata (e.g., index, symbol)
    
    Returns:
        TokenValidationResult with allowed status and message
    """
    try:
        # Get user billing status
        billing_status = await billing_service.get_user_billing_status(user_id)
        
        # Calculate token cost
        token_cost = TOKEN_COSTS[scan_type] * scan_count
        
        # Check if user has active subscription
        if billing_status.subscription_active:
            # Check subscription limits first
            can_use_subscription = await check_subscription_limits(
                user_id, 
                scan_type, 
                scan_count,
                billing_status
            )
            
            if can_use_subscription:
                # Use subscription - no token deduction needed
                await record_subscription_usage(user_id, scan_type, scan_count, metadata)
                return TokenValidationResult(
                    allowed=True,
                    message=f"Using subscription ({billing_status.plan_type})",
                    balance_after=billing_status.credits_balance
                )
        
        # Use wallet (either no subscription or limits exceeded)
        if billing_status.credits_balance < token_cost:
            # Insufficient balance - block request
            return TokenValidationResult(
                allowed=False,
                message=f"""Token balance insufficient. Required: {token_cost}, Available: {billing_status.credits_balance}. 
                
Please:
• Subscribe to a plan
• Or use pay-as-you-go  
• Or add tokens to your wallet"""
            )
        
        # Deduct tokens from wallet
        success, message, balance_data = await billing_service.deduct_credits(
            user_id=user_id,
            amount=token_cost,
            description=f"{scan_type.value}: {scan_count} scan(s)",
            scan_type=scan_type.value,
            scan_count=scan_count,
            metadata=metadata
        )
        
        if not success:
            return TokenValidationResult(
                allowed=False,
                message=f"Failed to deduct tokens: {message}"
            )
        
        return TokenValidationResult(
            allowed=True,
            message=f"Deducted {token_cost} tokens from wallet",
            balance_after=balance_data.get('balance', billing_status.credits_balance)
        )
        
    except Exception as e:
        return TokenValidationResult(
            allowed=False,
            message=f"Token validation failed: {str(e)}"
        )


async def check_subscription_limits(
    user_id: str,
    scan_type: ScanType, 
    scan_count: int,
    billing_status
) -> bool:
    """Check if user can use subscription for this scan"""
    
    # Get today's usage
    today_usage = await billing_service.get_today_usage(user_id)
    
    # Get plan limits
    plan_limits = await billing_service.get_plan_limits(billing_status.plan_type)
    
    if not plan_limits:
        return False
    
    # Check specific limits based on scan type
    if scan_type == ScanType.STOCK_SCAN:
        daily_limit = plan_limits.daily_stock_scans
        current_usage = today_usage.stock_scans
        
    elif scan_type == ScanType.OPTION_SCAN:
        daily_limit = plan_limits.daily_option_scans
        current_usage = today_usage.option_scans
        
    elif scan_type == ScanType.BULK_SCAN:
        daily_limit = plan_limits.daily_bulk_scans
        current_usage = today_usage.bulk_scans
        
    elif scan_type == ScanType.CHART_SCAN:
        # Charts typically unlimited for subscribers
        return True
        
    else:
        return False
    
    # Check if within limits (None means unlimited)
    if daily_limit is None:
        return True
        
    return (current_usage + scan_count) <= daily_limit


async def record_subscription_usage(
    user_id: str,
    scan_type: ScanType,
    scan_count: int,
    metadata: Optional[Dict] = None
):
    """Record usage for subscription users"""
    await billing_service.record_usage(
        user_id=user_id,
        scan_type=scan_type.value,
        count=scan_count,
        metadata=metadata
    )


# Middleware decorator for API endpoints
def require_tokens(scan_type: ScanType, scan_count: int = 1):
    """
    Decorator to validate tokens before API execution
    
    Usage:
    @require_tokens(ScanType.STOCK_SCAN)
    async def stock_scan_endpoint(...)
    
    For stock scans, scan_count is calculated dynamically based on:
    - Number of symbols if provided
    - Limit parameter if randomizing
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from authorization header
            authorization = kwargs.get('authorization')
            if not authorization:
                raise HTTPException(status_code=401, detail="Authorization required")
            
            from src.services.auth_service import auth_service
            try:
                user = await auth_service.get_current_user(authorization.replace('Bearer ', ''))
                user_id = user.id
            except Exception as e:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Calculate dynamic scan count for stock scans
            actual_scan_count = scan_count
            if scan_type == ScanType.STOCK_SCAN:
                # Check if this is a POST request with body
                request = kwargs.get('request')
                if request:
                    try:
                        # Read and cache body
                        body_bytes = await request.body()
                        body = body_bytes.decode('utf-8')
                        import json
                        body_data = json.loads(body)
                        
                        symbols = body_data.get('symbols')
                        limit = body_data.get('limit', 50)
                        
                        if symbols:
                            # Count comma-separated symbols
                            actual_scan_count = len([s.strip() for s in symbols.split(',') if s.strip()])
                        else:
                            # Use limit for random scans
                            actual_scan_count = limit
                    except:
                        pass
                else:
                    # GET request - check symbols or limit param
                    symbols = kwargs.get('symbols')
                    limit = kwargs.get('limit', 50)
                    
                    if symbols:
                        actual_scan_count = len([s.strip() for s in symbols.split(',') if s.strip()])
                    else:
                        actual_scan_count = limit
            
            # Extract metadata from kwargs
            metadata = kwargs.get('scan_metadata', {})
            metadata['calculated_scan_count'] = actual_scan_count
            
            # Validate and deduct tokens
            validation_result = await validate_and_deduct_tokens(
                user_id, 
                scan_type, 
                actual_scan_count,
                metadata
            )
            
            if not validation_result.allowed:
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=validation_result.message
                )
            
            # Add validation info to kwargs for endpoint use
            kwargs['token_validation'] = validation_result
            
            # Proceed with original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator