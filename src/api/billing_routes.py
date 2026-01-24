"""
Billing API Endpoints
REST API endpoints for subscription and PAYG billing management
"""
from fastapi import APIRouter, HTTPException, Header, Request
from typing import Optional
from decimal import Decimal
import uuid
import json

from src.services.billing_service import billing_service
from src.services.razorpay_service import razorpay_service
from src.services.auth_service import auth_service
from src.models.billing_models import (
    SubscriptionRequest,
    SubscriptionCancelRequest,
    CreditPurchaseRequest,
    RazorpayPaymentVerification,
    BillingDashboard
)

# Create router
router = APIRouter(prefix="/api/billing", tags=["billing"])


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Extract and verify user from authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user = await auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user.id


# ============================================
# BILLING STATUS & DASHBOARD
# ============================================

@router.get("/status")
async def get_billing_status(authorization: str = Header(None)):
    """
    Get complete billing status for the current user
    Returns plan, credits, usage, and limits
    """
    try:
        user_id = await get_current_user_id(authorization)
        status = await billing_service.get_user_billing_status(user_id)
        return status.dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get billing status: {str(e)}")


@router.get("/dashboard")
async def get_billing_dashboard(authorization: str = Header(None)):
    """
    Get complete billing dashboard data
    Includes status, transactions, packs, and usage history
    """
    try:
        user_id = await get_current_user_id(authorization)
        
        # Get billing status
        status = await billing_service.get_user_billing_status(user_id)
        
        # Get recent transactions
        transactions = await billing_service.get_transactions(user_id, limit=20)
        
        # Get available credit packs
        credit_packs = await billing_service.get_credit_packs()
        
        dashboard = BillingDashboard(
            billing_status=status,
            recent_transactions=transactions,
            available_credit_packs=credit_packs,
            recent_payments=[],  # TODO: Add payment history
            usage_history=[]  # TODO: Add usage history
        )
        
        return dashboard.dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


# ============================================
# CREDIT PURCHASE (PAYG)
# ============================================

@router.post("/credits/create-order")
async def create_credit_order(
    request: CreditPurchaseRequest,
    authorization: str = Header(None)
):
    """
    Create Razorpay order for credit purchase
    Returns order details for frontend payment flow
    """
    try:
        user_id = await get_current_user_id(authorization)
        
        # Get credit pack details
        credit_packs = await billing_service.get_credit_packs()
        pack = next((p for p in credit_packs if p.id == request.pack_id), None)
        
        if not pack:
            raise HTTPException(status_code=404, detail="Credit pack not found")
        
        # Create Razorpay order (receipt max 40 chars)
        # Use short user ID prefix and random string
        short_user_id = user_id[:8]
        receipt = f"c_{short_user_id}_{uuid.uuid4().hex[:12]}"
        success, order_data = razorpay_service.create_order(
            amount_inr=pack.amount_inr,
            receipt=receipt,
            notes={
                'user_id': user_id,
                'pack_id': pack.id,
                'credits': str(pack.credits),
                'bonus_credits': str(pack.bonus_credits)
            }
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to create order: {order_data.get('error')}")
        
        return {
            'order': order_data,
            'pack': pack.dict(),
            'user_id': user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create credit order: {str(e)}")


@router.post("/credits/verify-payment")
async def verify_credit_payment(
    verification: RazorpayPaymentVerification,
    authorization: str = Header(None)
):
    """
    Verify Razorpay payment and add credits to user account
    Called after successful payment on frontend
    """
    try:
        user_id = await get_current_user_id(authorization)
        
        # Verify payment signature
        is_valid = razorpay_service.verify_payment_signature(
            order_id=verification.razorpay_order_id,
            payment_id=verification.razorpay_payment_id,
            signature=verification.razorpay_signature
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
        
        # Fetch payment details
        success, payment_data = razorpay_service.fetch_payment(verification.razorpay_payment_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to fetch payment details")
        
        if payment_data['status'] != 'captured':
            raise HTTPException(status_code=400, detail=f"Payment not captured: {payment_data['status']}")
        
        # Extract pack details from order notes (stored during order creation)
        # Fetch order to get notes
        # For now, calculate from amount (₹100 order = 100 credits + bonus)
        amount_inr = payment_data['amount'] // 100  # Convert paisa to rupees
        
        # Determine credits based on pack
        credit_packs = await billing_service.get_credit_packs()
        pack = next((p for p in credit_packs if p.amount_inr == amount_inr), None)
        
        if not pack:
            # Fallback: 1:1 ratio if pack not found
            credits_to_add = Decimal(str(amount_inr))
        else:
            credits_to_add = pack.total_credits
        
        # Add credits to user account
        success, message, balance_data = await billing_service.add_credits(
            user_id=user_id,
            amount=credits_to_add,
            payment_id=verification.razorpay_payment_id,
            description=f"Credit purchase: ₹{amount_inr} ({pack.name if pack else 'Custom'})"
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return {
            'success': True,
            'message': message,
            'credits_added': float(credits_to_add),
            'new_balance': balance_data['balance'],
            'payment_id': verification.razorpay_payment_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify payment: {str(e)}")


@router.get("/credits/packs")
async def get_credit_packs():
    """
    Get available credit packs (public endpoint)
    """
    try:
        packs = await billing_service.get_credit_packs()
        return [pack.dict() for pack in packs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get credit packs: {str(e)}")


@router.get("/credits/transactions")
async def get_credit_transactions(
    limit: int = 20,
    authorization: str = Header(None)
):
    """
    Get credit transaction history
    """
    try:
        user_id = await get_current_user_id(authorization)
        transactions = await billing_service.get_transactions(user_id, limit=limit)
        return [txn.dict() for txn in transactions]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transactions: {str(e)}")


# ============================================
# SUBSCRIPTION MANAGEMENT
# ============================================

@router.get("/subscription/details")
async def get_subscription_details(authorization: str = Header(None)):
    """
    Get current subscription details for the user
    """
    try:
        user_id = await get_current_user_id(authorization)
        
        # Get billing status which includes subscription info
        status = await billing_service.get_user_billing_status(user_id)
        
        # Return subscription details
        return {
            'user_id': user_id,
            'plan_type': status.plan_type,
            'subscription_active': status.subscription_active,
            'subscription_start': status.subscription_end,  # Using end date as a proxy for now
            'subscription_end': status.subscription_end,
            'auto_renew': True if status.subscription_active else False,
            'payment_method': 'razorpay',
            'amount_paid': 4999 if status.plan_type == 'medium' else 9999 if status.plan_type == 'pro' else 0,
            'next_billing_date': status.subscription_end
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subscription details: {str(e)}")


@router.post("/subscription/create-order")
async def create_subscription_order(
    request: SubscriptionRequest,
    authorization: str = Header(None)
):
    """
    Create Razorpay order for subscription payment
    """
    try:
        user_id = await get_current_user_id(authorization)
        
        # Validate plan
        if request.plan_type not in ['medium', 'pro']:
            raise HTTPException(status_code=400, detail="Invalid plan type")
        
        # Get plan price
        plan_prices = {
            'medium': 4999,
            'pro': 9999
        }
        amount_inr = plan_prices[request.plan_type]
        
        # Create Razorpay order
        order = razorpay_service.create_order(
            amount_inr=amount_inr,
            currency='INR',
            notes={
                'user_id': user_id,
                'plan_type': request.plan_type,
                'billing_period': 'monthly',
                'order_type': 'subscription'
            }
        )
        
        return {
            'order': order,
            'plan_type': request.plan_type,
            'amount': amount_inr,
            'user_id': user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create subscription order: {str(e)}")


@router.post("/subscription/verify-payment")
async def verify_subscription_payment(
    verification: RazorpayPaymentVerification,
    authorization: str = Header(None)
):
    """
    Verify subscription payment and activate subscription
    """
    try:
        user_id = await get_current_user_id(authorization)
        
        # Verify payment signature
        is_valid = razorpay_service.verify_payment_signature(
            order_id=verification.razorpay_order_id,
            payment_id=verification.razorpay_payment_id,
            signature=verification.razorpay_signature
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
        
        # Get plan type from request body
        plan_type = verification.plan_type or 'medium'
        
        # Activate subscription
        success, message = await billing_service.create_subscription(
            user_id=user_id,
            plan_type=plan_type,
            period_months=1
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return {
            'success': True,
            'message': 'Subscription activated successfully',
            'plan_type': plan_type,
            'payment_id': verification.razorpay_payment_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify subscription payment: {str(e)}")


@router.post("/subscription/create")
async def create_subscription(
    request: SubscriptionRequest,
    authorization: str = Header(None)
):
    """
    Create or upgrade subscription
    For now, creates directly. In production, would create Razorpay subscription
    """
    try:
        user_id = await get_current_user_id(authorization)
        
        # Validate plan
        if request.plan_type not in ['medium', 'pro']:
            raise HTTPException(status_code=400, detail="Invalid plan type")
        
        # TODO: Create Razorpay subscription and get subscription ID
        # For now, create directly after payment
        
        success, message = await billing_service.create_subscription(
            user_id=user_id,
            plan_type=request.plan_type,
            period_months=1
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return {
            'success': True,
            'message': message,
            'plan_type': request.plan_type
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")


@router.post("/subscription/cancel")
async def cancel_subscription(
    request: SubscriptionCancelRequest,
    authorization: str = Header(None)
):
    """
    Cancel subscription
    """
    try:
        user_id = await get_current_user_id(authorization)
        
        success, message = await billing_service.cancel_subscription(
            user_id=user_id,
            immediately=request.cancel_immediately
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return {
            'success': True,
            'message': message
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {str(e)}")


@router.get("/plans")
async def get_plans():
    """
    Get all available plans with their limits (public endpoint)
    """
    try:
        plans = []
        for plan_type in ['free', 'medium', 'pro']:
            limits = await billing_service.get_plan_limits(plan_type)
            if limits:
                plans.append(limits.dict())
        return plans
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plans: {str(e)}")


# ============================================
# WEBHOOKS
# ============================================

@router.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request):
    """
    Handle Razorpay webhooks for payment/subscription events
    """
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get('X-Razorpay-Signature', '')
        
        # Verify webhook signature
        is_valid = razorpay_service.verify_webhook_signature(
            payload=body.decode(),
            signature=signature
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        # Parse event data
        event_data = json.loads(body)
        event_type = event_data.get('event')
        
        # Handle different event types
        if event_type == 'payment.captured':
            # Payment successful - credits should already be added via verify_payment
            pass
        
        elif event_type == 'payment.failed':
            # Payment failed - log for debugging
            payload = event_data.get('payload', {})
            payment = payload.get('payment', {}).get('entity', {})
            print(f"Payment failed: {payment.get('id')}")
        
        elif event_type == 'subscription.charged':
            # Subscription payment successful - renew subscription
            payload = event_data.get('payload', {})
            subscription = payload.get('subscription', {}).get('entity', {})
            # TODO: Update subscription period
        
        elif event_type == 'subscription.cancelled':
            # Subscription cancelled
            payload = event_data.get('payload', {})
            subscription = payload.get('subscription', {}).get('entity', {})
            # TODO: Handle subscription cancellation
        
        return {'status': 'ok'}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


# Export router
__all__ = ['router']
