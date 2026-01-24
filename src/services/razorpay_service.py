"""
Razorpay Payment Integration Service
Handles payment gateway operations for credit purchases and subscriptions
"""
import os
import hmac
import hashlib
from typing import Dict, Optional, Tuple
import razorpay
from decimal import Decimal


class RazorpayService:
    """Service for Razorpay payment gateway integration"""
    
    def __init__(self):
        self.key_id = os.getenv('RAZORPAY_KEY_ID')
        self.key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        
        if not self.key_id or not self.key_secret:
            print("⚠️  WARNING: Razorpay credentials not configured. Payment features will be disabled.")
            print("   Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env to enable payments.")
            self.client = None
        else:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
    
    
    # ============================================
    # ORDER CREATION
    # ============================================
    
    def create_order(
        self, 
        amount_inr: int, 
        receipt: str, 
        notes: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Create Razorpay order for credit purchase
        
        Args:
            amount_inr: Amount in INR (will be converted to paisa)
            receipt: Unique receipt identifier
            notes: Additional metadata
        
        Returns:
            (success, order_data)
        """
        if not self.client:
            return False, {'error': 'Razorpay not configured'}
        
        try:
            # Convert to paisa (₹100 = 10000 paisa)
            amount_paisa = amount_inr * 100
            
            order_data = {
                'amount': amount_paisa,
                'currency': 'INR',
                'receipt': receipt,
                'notes': notes or {}
            }
            
            order = self.client.order.create(data=order_data)
            
            return True, {
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'key_id': self.key_id,
                'receipt': order['receipt']
            }
        
        except Exception as e:
            return False, {'error': str(e)}
    
    
    # ============================================
    # PAYMENT VERIFICATION
    # ============================================
    
    def verify_payment_signature(
        self, 
        order_id: str, 
        payment_id: str, 
        signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature
        
        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID
            signature: Payment signature from frontend
        
        Returns:
            True if signature is valid
        """
        try:
            # Create signature string
            message = f"{order_id}|{payment_id}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                self.key_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
        
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False
    
    
    def fetch_payment(self, payment_id: str) -> Tuple[bool, Dict]:
        """
        Fetch payment details from Razorpay
        
        Args:
            payment_id: Razorpay payment ID
        
        Returns:
            (success, payment_data)
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            
            return True, {
                'id': payment['id'],
                'order_id': payment['order_id'],
                'amount': payment['amount'],
                'currency': payment['currency'],
                'status': payment['status'],
                'method': payment['method'],
                'email': payment.get('email'),
                'contact': payment.get('contact'),
                'created_at': payment['created_at']
            }
        
        except Exception as e:
            return False, {'error': str(e)}
    
    
    # ============================================
    # SUBSCRIPTION MANAGEMENT
    # ============================================
    
    def create_subscription(
        self, 
        plan_id: str, 
        customer_email: str,
        customer_contact: str,
        notes: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Create Razorpay subscription
        
        Args:
            plan_id: Razorpay plan ID (created in dashboard)
            customer_email: Customer email
            customer_contact: Customer phone number
            notes: Additional metadata
        
        Returns:
            (success, subscription_data)
        """
        try:
            subscription_data = {
                'plan_id': plan_id,
                'customer_notify': 1,
                'quantity': 1,
                'total_count': 12,  # 12 months for annual
                'notes': notes or {}
            }
            
            subscription = self.client.subscription.create(data=subscription_data)
            
            return True, {
                'subscription_id': subscription['id'],
                'plan_id': subscription['plan_id'],
                'status': subscription['status'],
                'current_start': subscription.get('current_start'),
                'current_end': subscription.get('current_end'),
                'short_url': subscription.get('short_url')
            }
        
        except Exception as e:
            return False, {'error': str(e)}
    
    
    def cancel_subscription(
        self, 
        subscription_id: str, 
        cancel_at_cycle_end: bool = False
    ) -> Tuple[bool, Dict]:
        """
        Cancel Razorpay subscription
        
        Args:
            subscription_id: Razorpay subscription ID
            cancel_at_cycle_end: If True, cancel at end of billing cycle
        
        Returns:
            (success, subscription_data)
        """
        try:
            subscription = self.client.subscription.cancel(
                subscription_id,
                data={'cancel_at_cycle_end': 1 if cancel_at_cycle_end else 0}
            )
            
            return True, {
                'subscription_id': subscription['id'],
                'status': subscription['status'],
                'ended_at': subscription.get('ended_at')
            }
        
        except Exception as e:
            return False, {'error': str(e)}
    
    
    def fetch_subscription(self, subscription_id: str) -> Tuple[bool, Dict]:
        """
        Fetch subscription details
        
        Args:
            subscription_id: Razorpay subscription ID
        
        Returns:
            (success, subscription_data)
        """
        try:
            subscription = self.client.subscription.fetch(subscription_id)
            
            return True, {
                'subscription_id': subscription['id'],
                'plan_id': subscription['plan_id'],
                'status': subscription['status'],
                'current_start': subscription.get('current_start'),
                'current_end': subscription.get('current_end'),
                'charge_at': subscription.get('charge_at'),
                'paid_count': subscription.get('paid_count'),
                'remaining_count': subscription.get('remaining_count')
            }
        
        except Exception as e:
            return False, {'error': str(e)}
    
    
    # ============================================
    # WEBHOOK VERIFICATION
    # ============================================
    
    def verify_webhook_signature(
        self, 
        payload: str, 
        signature: str, 
        secret: Optional[str] = None
    ) -> bool:
        """
        Verify Razorpay webhook signature
        
        Args:
            payload: Webhook payload (raw body)
            signature: X-Razorpay-Signature header
            secret: Webhook secret (defaults to RAZORPAY_WEBHOOK_SECRET env var)
        
        Returns:
            True if signature is valid
        """
        try:
            webhook_secret = secret or os.getenv('RAZORPAY_WEBHOOK_SECRET')
            
            if not webhook_secret:
                print("Warning: RAZORPAY_WEBHOOK_SECRET not set")
                return False
            
            # Generate expected signature
            expected_signature = hmac.new(
                webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
        
        except Exception as e:
            print(f"Webhook verification error: {e}")
            return False
    
    
    # ============================================
    # REFUND MANAGEMENT
    # ============================================
    
    def create_refund(
        self, 
        payment_id: str, 
        amount: Optional[int] = None,
        notes: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Create a refund for a payment
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to refund in paisa (None = full refund)
            notes: Additional metadata
        
        Returns:
            (success, refund_data)
        """
        try:
            refund_data = {
                'notes': notes or {}
            }
            
            if amount is not None:
                refund_data['amount'] = amount
            
            refund = self.client.payment.refund(payment_id, refund_data)
            
            return True, {
                'refund_id': refund['id'],
                'payment_id': refund['payment_id'],
                'amount': refund['amount'],
                'status': refund['status']
            }
        
        except Exception as e:
            return False, {'error': str(e)}
    
    
    def fetch_refund(self, refund_id: str) -> Tuple[bool, Dict]:
        """
        Fetch refund details
        
        Args:
            refund_id: Razorpay refund ID
        
        Returns:
            (success, refund_data)
        """
        try:
            refund = self.client.refund.fetch(refund_id)
            
            return True, {
                'refund_id': refund['id'],
                'payment_id': refund['payment_id'],
                'amount': refund['amount'],
                'status': refund['status'],
                'created_at': refund['created_at']
            }
        
        except Exception as e:
            return False, {'error': str(e)}


# Global instance
razorpay_service = RazorpayService()
