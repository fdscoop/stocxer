"""
Billing Middleware
Decorators and utilities for billing checks on API endpoints
"""
from functools import wraps
from fastapi import HTTPException, Header
from typing import Optional, Callable
from src.services.billing_service import billing_service
from src.services.auth_service import auth_service


async def get_user_from_token(authorization: Optional[str]) -> Optional[str]:
    """Extract user ID from authorization token"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    user = await auth_service.get_current_user(token)
    
    return user.id if user else None


async def check_billing_for_scan(
    user_id: str,
    scan_type: str,
    count: int = 1
) -> dict:
    """
    Check if user can perform a scan and return billing info
    
    Args:
        user_id: User ID
        scan_type: 'option_scan', 'stock_scan', or 'bulk_scan'
        count: Number of items to scan
    
    Returns:
        dict with billing_allowed, reason, and billing_info
    
    Raises:
        HTTPException if billing check fails
    """
    try:
        # Check if user can perform action
        result = await billing_service.check_can_perform_action(
            user_id=user_id,
            action=scan_type,
            count=count
        )
        
        if not result.allowed:
            raise HTTPException(
                status_code=402,  # Payment Required
                detail={
                    'error': 'BILLING_LIMIT_REACHED',
                    'message': result.reason,
                    'billing_type': result.billing_type,
                    'cost': float(result.cost) if result.cost else None,
                    'remaining_balance': float(result.remaining_balance) if result.remaining_balance else None
                }
            )
        
        return {
            'billing_allowed': True,
            'billing_type': result.billing_type,
            'cost': float(result.cost) if result.cost else None,
            'reason': result.reason
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Billing check failed: {str(e)}"
        )


async def deduct_billing_for_scan(
    user_id: str,
    scan_type: str,
    count: int = 1,
    metadata: Optional[dict] = None
) -> dict:
    """
    Deduct credits or log usage after successful scan
    
    Args:
        user_id: User ID
        scan_type: 'option_scan', 'stock_scan', or 'bulk_scan'
        count: Number of items scanned
        metadata: Additional metadata to store
    
    Returns:
        dict with success status and message
    """
    try:
        success, message = await billing_service.deduct_for_action(
            user_id=user_id,
            action=scan_type,
            count=count,
            metadata=metadata
        )
        
        if not success:
            # Log warning but don't fail the request
            print(f"Warning: Failed to deduct billing for {user_id}: {message}")
        
        return {
            'billing_deducted': success,
            'billing_message': message
        }
    
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error deducting billing: {e}")
        return {
            'billing_deducted': False,
            'billing_message': str(e)
        }


def require_billing_check(scan_type: str):
    """
    Decorator to require billing check before endpoint execution
    
    Usage:
        @app.get("/api/scan")
        @require_billing_check('option_scan')
        async def scan_options(authorization: str = Header(None)):
            # ... endpoint logic
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract authorization from kwargs
            authorization = kwargs.get('authorization')
            
            if not authorization:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            # Get user ID
            user_id = await get_user_from_token(authorization)
            
            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token"
                )
            
            # Extract count from request (if applicable)
            count = kwargs.get('count', 1)
            
            # Check billing
            await check_billing_for_scan(user_id, scan_type, count)
            
            # Execute original function
            result = await func(*args, **kwargs)
            
            # Deduct billing after successful execution
            await deduct_billing_for_scan(user_id, scan_type, count)
            
            return result
        
        return wrapper
    return decorator


# Utility function to get billing summary in response
async def add_billing_info_to_response(response: dict, user_id: str) -> dict:
    """
    Add billing information to API response
    Useful for showing remaining credits/usage to frontend
    """
    try:
        status = await billing_service.get_user_billing_status(user_id)
        
        response['billing'] = {
            'plan_type': status.plan_type,
            'credits_balance': float(status.credits_balance),
            'today_usage': {
                'option_scans': status.today_usage.option_scans,
                'stock_scans': status.today_usage.stock_scans,
                'bulk_scans': status.today_usage.bulk_scans
            },
            'limits': {
                'daily_option_scans': status.limits.daily_option_scans,
                'daily_stock_scans': status.limits.daily_stock_scans,
                'bulk_scan_limit': status.limits.bulk_scan_limit
            }
        }
        
        return response
    
    except Exception as e:
        print(f"Error adding billing info: {e}")
        return response
