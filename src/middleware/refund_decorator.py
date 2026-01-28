"""
Refund decorator for scan endpoints
Automatically refunds credits if scan fails
"""
from functools import wraps
from fastapi import HTTPException
from typing import Callable
from decimal import Decimal
import logging

from src.services.billing_service import billing_service
from src.middleware.token_middleware import ScanType, TOKEN_COSTS

logger = logging.getLogger(__name__)


async def refund_credits_on_failure(
    user_id: str,
    scan_type: ScanType,
    scan_count: int = 1,
    reason: str = "Scan failed"
) -> bool:
    """
    Refund credits to user when scan fails
    
    Args:
        user_id: User ID
        scan_type: Type of scan that failed
        scan_count: Number of scans that failed
        reason: Reason for refund
        
    Returns:
        True if refund successful, False otherwise
    """
    try:
        refund_amount = TOKEN_COSTS[scan_type] * scan_count
        
        # Add credits back to user account
        success, message, balance_data = await billing_service.add_credits(
            user_id=user_id,
            amount=refund_amount,
            description=f"Refund: {reason} - {scan_type.value}"
        )
        
        if success:
            logger.info(f"✅ Refunded ₹{refund_amount} to user {user_id[:8]} for failed {scan_type.value}")
            
            # Record refund transaction
            try:
                await billing_service.supabase.table('credit_transactions').insert({
                    'user_id': user_id,
                    'transaction_type': 'refund',
                    'amount': float(refund_amount),
                    'balance_before': balance_data.get('balance', 0) - float(refund_amount),
                    'balance_after': balance_data.get('balance', 0),
                    'description': f"Refund: {reason}",
                    'scan_type': scan_type.value,
                    'scan_count': scan_count
                }).execute()
            except Exception as txn_error:
                logger.warning(f"Failed to record refund transaction: {txn_error}")
            
            return True
        else:
            logger.error(f"Failed to refund ₹{refund_amount} to user {user_id[:8]}: {message}")
            return False
            
    except Exception as e:
        logger.error(f"Refund error for user {user_id[:8]}: {e}")
        return False


def with_refund_on_failure(scan_type: ScanType, scan_count: int = 1):
    """
    Decorator that refunds credits if the endpoint raises an exception
    
    Usage:
        @require_tokens(ScanType.OPTION_SCAN)
        @with_refund_on_failure(ScanType.OPTION_SCAN)
        async def scan_options(...):
            # Your scan logic
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = None
            
            # Try to extract user_id from kwargs (set by require_tokens decorator)
            authorization = kwargs.get('authorization')
            if authorization:
                try:
                    from src.services.auth_service import auth_service
                    user = await auth_service.get_current_user(authorization.replace('Bearer ', ''))
                    user_id = user.id
                except:
                    pass
            
            try:
                # Execute the original function
                result = await func(*args, **kwargs)
                return result
                
            except HTTPException as http_error:
                # HTTP errors from within the endpoint - refund credits
                # Refund on 500+ (server errors) AND 503 (Fyers data unavailable)
                if user_id and http_error.status_code >= 500:
                    # Handle error detail which can be string or dict
                    error_msg = http_error.detail
                    if isinstance(error_msg, dict):
                        error_msg = error_msg.get('message', str(error_msg))[:100]
                    else:
                        error_msg = str(error_msg)[:100]
                    
                    logger.warning(f"Scan failed with HTTP {http_error.status_code}, refunding credits")
                    await refund_credits_on_failure(
                        user_id=user_id,
                        scan_type=scan_type,
                        scan_count=scan_count,
                        reason=f"Server error: {error_msg}"
                    )
                raise
                
            except Exception as e:
                # Unexpected errors - refund credits
                if user_id:
                    logger.error(f"Scan failed with exception, refunding credits: {e}")
                    await refund_credits_on_failure(
                        user_id=user_id,
                        scan_type=scan_type,
                        scan_count=scan_count,
                        reason=f"Scan failed: {str(e)[:100]}"
                    )
                raise
        
        return wrapper
    return decorator
