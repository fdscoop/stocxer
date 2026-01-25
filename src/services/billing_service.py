"""
Billing Service
Core business logic for hybrid subscription + PAYG billing system
"""
import os
from typing import Optional, Tuple, Dict, List
from datetime import datetime, date, timedelta
from decimal import Decimal
from supabase import create_client, Client
from src.models.billing_models import (
    UserBillingStatus,
    TodayUsage,
    PlanLimits,
    BillingCheckResult,
    CreditTransaction,
    PricingConfig,
    UserSubscription,
    UserCredits,
    CreditPack,
    UsageLog
)


class BillingService:
    """Service for managing subscriptions and PAYG credits"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.pricing = PricingConfig()
    
    
    # ============================================
    # BILLING STATUS & CHECKS
    # ============================================
    
    async def get_user_billing_status(self, user_id: str) -> UserBillingStatus:
        """
        Get complete billing status for a user
        Returns subscription info, credits balance, usage, and limits
        """
        # Get subscription
        try:
            sub_response = self.supabase.table('user_subscriptions')\
                .select('*')\
                .eq('user_id', user_id)\
                .maybe_single()\
                .execute()
            subscription = sub_response.data if sub_response.data else None
        except Exception as e:
            subscription = None
        
        # Get credits
        try:
            credits_response = self.supabase.table('user_credits')\
                .select('*')\
                .eq('user_id', user_id)\
                .maybe_single()\
                .execute()
            
            if credits_response.data:
                credits = credits_response.data
            else:
                # Initialize user with 100 free credits if they don't have a record
                credits = await self._initialize_user_credits(user_id)
        except Exception as e:
            # If something goes wrong, try to initialize
            credits = await self._initialize_user_credits(user_id)
        
        # Get today's usage
        today = date.today()
        usage_response = self.supabase.table('usage_logs')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('usage_date', today.isoformat())\
            .execute()
        
        today_usage = TodayUsage()
        if usage_response.data:
            for log in usage_response.data:
                if log['scan_type'] == 'option_scan':
                    today_usage.option_scans = log['count']
                elif log['scan_type'] == 'stock_scan':
                    today_usage.stock_scans = log['count']
                elif log['scan_type'] == 'bulk_scan':
                    today_usage.bulk_scans = log['count']
        
        # Get plan limits
        plan_type = subscription['plan_type'] if subscription else 'free'
        try:
            limits_response = self.supabase.table('plan_limits')\
                .select('*')\
                .eq('plan_type', plan_type)\
                .maybe_single()\
                .execute()
            limits = PlanLimits(**limits_response.data) if limits_response.data else PlanLimits(plan_type='free')
        except Exception as e:
            limits = PlanLimits(plan_type='free')
        
        # Determine billing type
        has_active_sub = bool(
            subscription and 
            subscription.get('status') == 'active' and 
            subscription.get('plan_type') in ['medium', 'pro']
        )
        
        billing_type = 'subscription' if has_active_sub else 'payg'
        
        return UserBillingStatus(
            user_id=user_id,
            billing_type=billing_type,
            plan_type=plan_type,
            subscription_active=has_active_sub,
            subscription_end=subscription.get('current_period_end') if subscription else None,
            cancel_at_period_end=subscription.get('cancel_at_period_end', False) if subscription else False,
            credits_balance=Decimal(str(credits.get('balance', 0))),
            today_usage=today_usage,
            limits=limits,
            can_use_credits=True,
            has_active_subscription=has_active_sub
        )
    
    
    async def check_can_perform_action(
        self, 
        user_id: str, 
        action: str, 
        count: int = 1
    ) -> BillingCheckResult:
        """
        Check if user can perform an action (scan)
        Returns: BillingCheckResult with allowed status and reason
        
        Args:
            user_id: User ID
            action: 'option_scan', 'stock_scan', or 'bulk_scan'
            count: Number of items (for bulk scans)
        """
        billing_status = await self.get_user_billing_status(user_id)
        
        # For subscription users, check limits
        if billing_status.has_active_subscription:
            return await self._check_subscription_limits(billing_status, action, count)
        
        # For PAYG users (including free tier), check credits
        return await self._check_credits_balance(billing_status, action, count)
    
    
    async def _check_subscription_limits(
        self, 
        status: UserBillingStatus, 
        action: str, 
        count: int
    ) -> BillingCheckResult:
        """Check if subscription user is within their limits (monthly quota)"""
        limits = status.limits
        
        # Check monthly scan limit first (most important for medium/pro)
        if limits.monthly_scan_limit is not None:
            monthly_usage = await self._get_monthly_usage(status.user_id)
            total_monthly_scans = monthly_usage.get('total', 0)
            
            if total_monthly_scans + count > limits.monthly_scan_limit:
                remaining = limits.monthly_scan_limit - total_monthly_scans
                return BillingCheckResult(
                    allowed=False,
                    reason=f"Monthly scan quota exceeded. Used: {total_monthly_scans}/{limits.monthly_scan_limit}. Remaining: {remaining} scans.",
                    billing_type="subscription"
                )
        
        # If we have daily limits (shouldn't happen for medium/pro now), check those too
        usage = status.today_usage
        
        if action == 'option_scan':
            limit = limits.daily_option_scans
            current = usage.option_scans
            
            if limit is not None and current + count > limit:
                return BillingCheckResult(
                    allowed=False,
                    reason=f"Daily limit reached ({current}/{limit}).",
                    billing_type="subscription"
                )
        
        elif action == 'stock_scan':
            limit = limits.daily_stock_scans
            current = usage.stock_scans
            
            if limit is not None and current + count > limit:
                return BillingCheckResult(
                    allowed=False,
                    reason=f"Daily limit reached ({current}/{limit}).",
                    billing_type="subscription"
                )
        
        elif action == 'bulk_scan':
            scan_limit = limits.bulk_scan_limit
            daily_limit = limits.daily_bulk_scans
            current = usage.bulk_scans
            
            if scan_limit is not None and count > scan_limit:
                return BillingCheckResult(
                    allowed=False,
                    reason=f"Bulk scan limited to {scan_limit} stocks. Your plan: {status.plan_type}",
                    billing_type="subscription"
                )
            
            if daily_limit is not None and current + 1 > daily_limit:
                return BillingCheckResult(
                    allowed=False,
                    reason=f"Daily bulk scan limit reached ({current}/{daily_limit})",
                    billing_type="subscription"
                )
        
        return BillingCheckResult(
            allowed=True,
            reason="Within subscription limits",
            billing_type="subscription"
        )
    
    
    async def _check_credits_balance(
        self, 
        status: UserBillingStatus, 
        action: str, 
        count: int
    ) -> BillingCheckResult:
        """Check if PAYG user has sufficient credits"""
        cost = self.pricing.calculate_scan_cost(action, count)
        balance = status.credits_balance
        
        # Free tier check
        if status.plan_type == 'free' and balance <= 0:
            # Check free tier limits
            result = await self._check_subscription_limits(status, action, count)
            if not result.allowed:
                result.reason += " Buy credits or subscribe for more access."
            return result
        
        # Check credit balance
        if balance < cost:
            return BillingCheckResult(
                allowed=False,
                reason=f"Insufficient credits. Required: ₹{cost}, Balance: ₹{balance}",
                billing_type="credits",
                cost=cost,
                remaining_balance=balance
            )
        
        return BillingCheckResult(
            allowed=True,
            reason=f"Sufficient credits. Cost: ₹{cost}",
            billing_type="credits",
            cost=cost,
            remaining_balance=balance - cost
        )
    
    
    async def _get_monthly_usage(self, user_id: str) -> Dict:
        """
        Get total monthly usage for current month
        Returns dict with 'total', 'option_scans', 'stock_scans', 'bulk_scans'
        """
        today = date.today()
        month_start = date(today.year, today.month, 1)
        
        try:
            usage_response = self.supabase.table('usage_logs')\
                .select('scan_type, count')\
                .eq('user_id', user_id)\
                .gte('usage_date', month_start.isoformat())\
                .lte('usage_date', today.isoformat())\
                .execute()
            
            result = {
                'total': 0,
                'option_scans': 0,
                'stock_scans': 0,
                'bulk_scans': 0
            }
            
            if usage_response.data:
                for log in usage_response.data:
                    count = log.get('count', 1)
                    result['total'] += count
                    
                    if log['scan_type'] == 'option_scan':
                        result['option_scans'] += count
                    elif log['scan_type'] == 'stock_scan':
                        result['stock_scans'] += count
                    elif log['scan_type'] == 'bulk_scan':
                        result['bulk_scans'] += count
            
            return result
        except Exception as e:
            return {'total': 0, 'option_scans': 0, 'stock_scans': 0, 'bulk_scans': 0}
    
    
    # ============================================
    # USAGE TRACKING & DEDUCTIONS
    # ============================================
    
    async def deduct_for_action(
        self, 
        user_id: str, 
        action: str, 
        count: int = 1,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Deduct credits or log usage for an action
        Returns: (success, message)
        """
        billing_status = await self.get_user_billing_status(user_id)
        
        # For subscription users, just log usage
        if billing_status.has_active_subscription:
            return await self._log_usage(user_id, action, count, metadata)
        
        # For PAYG users, deduct credits
        return await self._deduct_credits(user_id, action, count, metadata)
    
    
    async def _log_usage(
        self, 
        user_id: str, 
        action: str, 
        count: int,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """Log usage for subscription user"""
        today = date.today()
        
        try:
            # Upsert usage log
            self.supabase.table('usage_logs').upsert({
                'user_id': user_id,
                'scan_type': action,
                'count': count,
                'usage_date': today.isoformat(),
                'metadata': metadata
            }, on_conflict='user_id,scan_type,usage_date').execute()
            
            return True, f"Usage logged: {count} {action}"
        except Exception as e:
            return False, f"Failed to log usage: {str(e)}"
    
    
    async def _deduct_credits(
        self, 
        user_id: str, 
        action: str, 
        count: int,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """Deduct credits for PAYG user"""
        cost = self.pricing.calculate_scan_cost(action, count)
        
        try:
            # Get current balance
            credits_response = self.supabase.table('user_credits')\
                .select('*')\
                .eq('user_id', user_id)\
                .single()\
                .execute()
            
            if not credits_response.data:
                return False, "Credits account not found"
            
            current_balance = Decimal(str(credits_response.data['balance']))
            
            if current_balance < cost:
                return False, f"Insufficient credits. Required: ₹{cost}, Balance: ₹{current_balance}"
            
            new_balance = current_balance - cost
            
            # Update balance
            self.supabase.table('user_credits').update({
                'balance': float(new_balance),
                'lifetime_spent': float(Decimal(str(credits_response.data['lifetime_spent'])) + cost)
            }).eq('user_id', user_id).execute()
            
            # Log transaction
            self.supabase.table('credit_transactions').insert({
                'user_id': user_id,
                'transaction_type': 'debit',
                'amount': float(cost),
                'balance_before': float(current_balance),
                'balance_after': float(new_balance),
                'description': f"{action.replace('_', ' ').title()} - {count} item(s)",
                'scan_type': action,
                'scan_count': count,
                'metadata': metadata
            }).execute()
            
            return True, f"Deducted ₹{cost}. New balance: ₹{new_balance}"
        
        except Exception as e:
            return False, f"Failed to deduct credits: {str(e)}"
    
    
    # ============================================
    # PAYMENT HISTORY TRACKING
    # ============================================
    
    async def log_payment_event(
        self, 
        user_id: str,
        payment_type: str,  # 'subscription', 'credits', 'refund'
        status: str,        # 'created', 'pending', 'captured', 'failed', 'refunded'
        amount_inr: int,
        razorpay_payment_id: Optional[str] = None,
        razorpay_order_id: Optional[str] = None,
        razorpay_signature: Optional[str] = None,
        payment_method: Optional[str] = None,
        failure_reason: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Log payment event in payment_history table for audit trail
        This provides complete payment lifecycle tracking separate from business logic
        """
        try:
            payment_data = {
                'user_id': user_id,
                'payment_type': payment_type,
                'status': status,
                'amount_inr': amount_inr,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_signature': razorpay_signature,
                'payment_method': payment_method,
                'failure_reason': failure_reason,
                'metadata': metadata or {},
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Insert or update payment record
            if razorpay_payment_id:
                # Check if payment already exists
                existing = self.supabase.table('payment_history')\
                    .select('*')\
                    .eq('razorpay_payment_id', razorpay_payment_id)\
                    .execute()
                
                if existing.data:
                    # Update existing payment
                    self.supabase.table('payment_history')\
                        .update({
                            'status': status,
                            'payment_method': payment_method,
                            'failure_reason': failure_reason,
                            'metadata': metadata or {},
                            'updated_at': datetime.now().isoformat()
                        })\
                        .eq('razorpay_payment_id', razorpay_payment_id)\
                        .execute()
                else:
                    # Insert new payment
                    self.supabase.table('payment_history').insert(payment_data).execute()
            else:
                # Insert new payment (for cases without razorpay_payment_id)
                self.supabase.table('payment_history').insert(payment_data).execute()
            
            return True, f"Payment event logged: {status}"
            
        except Exception as e:
            print(f"Failed to log payment event: {e}")
            return False, f"Failed to log payment event: {str(e)}"
    
    
    async def get_payment_history(
        self, 
        user_id: str, 
        limit: int = 20,
        payment_type: Optional[str] = None
    ) -> List[Dict]:
        """Get payment history for user"""
        try:
            query = self.supabase.table('payment_history')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)
            
            if payment_type:
                query = query.eq('payment_type', payment_type)
            
            response = query.execute()
            return response.data or []
            
        except Exception as e:
            print(f"Failed to get payment history: {e}")
            return []
    
    
    async def update_payment_status(
        self,
        razorpay_payment_id: str,
        status: str,
        payment_method: Optional[str] = None,
        failure_reason: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """Update payment status in payment_history"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if payment_method:
                update_data['payment_method'] = payment_method
            if failure_reason:
                update_data['failure_reason'] = failure_reason  
            if metadata:
                update_data['metadata'] = metadata
            
            self.supabase.table('payment_history')\
                .update(update_data)\
                .eq('razorpay_payment_id', razorpay_payment_id)\
                .execute()
            
            return True, f"Payment status updated to: {status}"
            
        except Exception as e:
            return False, f"Failed to update payment status: {str(e)}"


    # ============================================
    # CREDIT MANAGEMENT  
    # ============================================
    
    async def add_credits(
        self, 
        user_id: str, 
        amount: Decimal, 
        payment_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Add credits to user account
        Returns: (success, message, new_balance_dict)
        """
        try:
            # 🔒 PREVENT DOUBLE PROCESSING: Check if payment already processed
            if payment_id:
                existing_txn = self.supabase.table('credit_transactions')\
                    .select('*')\
                    .eq('razorpay_payment_id', payment_id)\
                    .execute()
                
                if existing_txn.data:
                    return False, f"Payment {payment_id} already processed", None
            
            # Get current balance
            credits_response = self.supabase.table('user_credits')\
                .select('*')\
                .eq('user_id', user_id)\
                .single()\
                .execute()
            
            if not credits_response.data:
                # Create credits account if not exists
                self.supabase.table('user_credits').insert({
                    'user_id': user_id,
                    'balance': float(amount),
                    'lifetime_purchased': float(amount),
                    'last_topped_up': datetime.now().isoformat()
                }).execute()
                
                current_balance = Decimal('0')
                new_balance = amount
            else:
                current_balance = Decimal(str(credits_response.data['balance']))
                new_balance = current_balance + amount
                
                # Update balance
                self.supabase.table('user_credits').update({
                    'balance': float(new_balance),
                    'lifetime_purchased': float(Decimal(str(credits_response.data['lifetime_purchased'])) + amount),
                    'last_topped_up': datetime.now().isoformat()
                }).eq('user_id', user_id).execute()
            
            # Log transaction with payment_id for idempotency
            self.supabase.table('credit_transactions').insert({
                'user_id': user_id,
                'transaction_type': 'purchase',
                'amount': float(amount),
                'balance_before': float(current_balance),
                'balance_after': float(new_balance),
                'description': description or f"Credit purchase: ₹{amount}",
                'razorpay_payment_id': payment_id,
                'metadata': {'source': 'webhook' if 'Webhook:' in (description or '') else 'frontend'}
            }).execute()
            
            return True, f"Added ₹{amount} credits", {
                'balance': float(new_balance),
                'amount_added': float(amount)
            }
        
        except Exception as e:
            return False, f"Failed to add credits: {str(e)}", None
    
    
    async def get_credit_packs(self) -> List[CreditPack]:
        """Get available credit packs"""
        response = self.supabase.table('credit_packs')\
            .select('*')\
            .eq('is_active', True)\
            .order('display_order')\
            .execute()
        
        return [CreditPack(**pack) for pack in response.data] if response.data else []
    
    
    async def get_transactions(self, user_id: str, limit: int = 10) -> List[CreditTransaction]:
        """Get recent credit transactions"""
        response = self.supabase.table('credit_transactions')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return [CreditTransaction(**txn) for txn in response.data] if response.data else []
    
    
    # ============================================
    # SUBSCRIPTION MANAGEMENT
    # ============================================
    
    async def create_subscription(
        self, 
        user_id: str, 
        plan_type: str,
        razorpay_subscription_id: Optional[str] = None,
        razorpay_payment_id: Optional[str] = None,
        period_months: int = 1
    ) -> Tuple[bool, str]:
        """Create or update user subscription"""
        if plan_type not in ['free', 'medium', 'pro']:
            return False, f"Invalid plan type: {plan_type}"
        
        try:
            now = datetime.now()
            period_end = now + timedelta(days=30 * period_months)
            
            # Upsert subscription
            self.supabase.table('user_subscriptions').upsert({
                'user_id': user_id,
                'plan_type': plan_type,
                'status': 'active',
                'razorpay_subscription_id': razorpay_subscription_id,
                'current_period_start': now.isoformat(),
                'current_period_end': period_end.isoformat(),
                'cancel_at_period_end': False
            }, on_conflict='user_id').execute()
            
            return True, f"Subscription created: {plan_type}"
        
        except Exception as e:
            return False, f"Failed to create subscription: {str(e)}"
    
    
    async def cancel_subscription(
        self, 
        user_id: str, 
        immediately: bool = False
    ) -> Tuple[bool, str]:
        """Cancel user subscription"""
        try:
            if immediately:
                # Downgrade to free immediately
                self.supabase.table('user_subscriptions').update({
                    'plan_type': 'free',
                    'status': 'cancelled',
                    'cancelled_at': datetime.now().isoformat()
                }).eq('user_id', user_id).execute()
                
                return True, "Subscription cancelled immediately"
            else:
                # Cancel at period end
                self.supabase.table('user_subscriptions').update({
                    'cancel_at_period_end': True,
                    'cancelled_at': datetime.now().isoformat()
                }).eq('user_id', user_id).execute()
                
                return True, "Subscription will cancel at period end"
        
        except Exception as e:
            return False, f"Failed to cancel subscription: {str(e)}"
    
    
    async def get_plan_limits(self, plan_type: str) -> Optional[PlanLimits]:
        """Get limits for a plan"""
        response = self.supabase.table('plan_limits')\
            .select('*')\
            .eq('plan_type', plan_type)\
            .single()\
            .execute()
        
        return PlanLimits(**response.data) if response.data else None
    
    
    async def _initialize_user_credits(self, user_id: str) -> Dict:
        """
        Initialize user credits with 100 free welcome bonus
        Returns the credits record
        """
        try:
            # Create user_credits record with 100 free credits
            credits_data = {
                'user_id': user_id,
                'balance': 100,
                'lifetime_purchased': 100,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table('user_credits').upsert(
                credits_data,
                on_conflict='user_id'
            ).execute()
            
            # Record welcome bonus transaction
            transaction_data = {
                'user_id': user_id,
                'transaction_type': 'bonus',
                'amount': 100,
                'balance_before': 0,
                'balance_after': 100,
                'description': 'Welcome bonus: 100 free credits',
                'created_at': datetime.now().isoformat()
            }
            
            self.supabase.table('credit_transactions').insert(
                transaction_data
            ).execute()
            
            return {'balance': 100, 'lifetime_purchased': 100, 'lifetime_spent': 0}
            
        except Exception as e:
            # If initialization fails, return default values
            return {'balance': 0, 'lifetime_purchased': 0, 'lifetime_spent': 0}

    
    async def deduct_credits(
        self,
        user_id: str,
        amount: Decimal,
        description: Optional[str] = None,
        scan_type: Optional[str] = None,
        scan_count: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """Deduct credits from user wallet"""
        try:
            # Get current balance
            response = self.supabase.table('user_credits').select('*').eq('user_id', user_id).single().execute()
            
            if not response.data:
                return False, "User credits not found", None
            
            current_balance = Decimal(str(response.data['balance']))
            
            if current_balance < amount:
                return False, f"Insufficient balance. Required: {amount}, Available: {current_balance}", None
            
            # Calculate new balance
            new_balance = current_balance - amount
            
            # Update user credits
            self.supabase.table('user_credits').update({
                'balance': float(new_balance),
                'lifetime_spent': float(Decimal(str(response.data['lifetime_spent'])) + amount),
                'updated_at': datetime.now().isoformat()
            }).eq('user_id', user_id).execute()
            
            # Record transaction
            self.supabase.table('credit_transactions').insert({
                'user_id': user_id,
                'transaction_type': 'debit',
                'amount': float(amount),
                'balance_before': float(current_balance),
                'balance_after': float(new_balance),
                'description': description or f"Usage deduction: {amount} credits",
                'scan_type': scan_type,
                'scan_count': scan_count,
                'metadata': metadata or {'action': 'usage_deduction'}
            }).execute()
            
            return True, f"Deducted {amount} credits", {'balance': float(new_balance)}
            
        except Exception as e:
            return False, f"Failed to deduct credits: {str(e)}", None
    
    
    async def get_today_usage(self, user_id: str) -> TodayUsage:
        """Get today's usage for a user"""
        try:
            today = date.today().isoformat()
            
            response = self.supabase.table('usage_logs').select('*').eq('user_id', user_id).eq('usage_date', today).execute()
            
            # Initialize usage counters
            stock_scans = 0
            option_scans = 0
            bulk_scans = 0
            chart_scans = 0
            
            # Sum up today's usage by type
            for usage in response.data:
                scan_type = usage['scan_type']
                count = usage['count']
                
                if scan_type == 'stock_scan':
                    stock_scans += count
                elif scan_type == 'option_scan':
                    option_scans += count
                elif scan_type == 'bulk_scan':
                    bulk_scans += count
                elif scan_type == 'chart_scan':
                    chart_scans += count
            
            return TodayUsage(
                stock_scans=stock_scans,
                option_scans=option_scans,
                bulk_scans=bulk_scans,
                chart_scans=chart_scans,
                total_scans=stock_scans + option_scans + bulk_scans + chart_scans
            )
            
        except Exception as e:
            # Return zero usage on error
            return TodayUsage(
                stock_scans=0,
                option_scans=0, 
                bulk_scans=0,
                chart_scans=0,
                total_scans=0
            )
    
    
    async def record_usage(
        self,
        user_id: str,
        scan_type: str,
        count: int = 1,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Record usage in usage_logs table"""
        try:
            today = date.today().isoformat()
            
            # Merge default metadata with provided metadata
            usage_metadata = {'recorded_at': datetime.now().isoformat()}
            if metadata:
                usage_metadata.update(metadata)
            
            # Upsert usage log (increment if exists)
            self.supabase.table('usage_logs').upsert({
                'user_id': user_id,
                'scan_type': scan_type,
                'count': count,
                'usage_date': today,
                'metadata': usage_metadata
            }, on_conflict='user_id,scan_type,usage_date').execute()
            
            return True
            
        except Exception as e:
            print(f"Failed to record usage: {e}")
            return False
    
    
    async def extend_subscription(
        self, 
        user_id: str, 
        months: int = 1
    ) -> Tuple[bool, str]:
        """Extend subscription period by specified months"""
        try:
            # Get current subscription
            response = self.supabase.table('user_subscriptions').select('*').eq('user_id', user_id).single().execute()
            
            if not response.data:
                return False, "No subscription found to extend"
            
            subscription = response.data
            
            # Parse current period end
            current_end = datetime.fromisoformat(subscription['current_period_end'].replace('Z', '+00:00'))
            
            # Calculate new end date
            new_end = current_end + timedelta(days=30 * months)
            
            # Update subscription
            self.supabase.table('user_subscriptions').update({
                'current_period_end': new_end.isoformat(),
                'status': 'active',
                'updated_at': datetime.now().isoformat()
            }).eq('user_id', user_id).execute()
            
            return True, f"Subscription extended by {months} month(s)"
            
        except Exception as e:
            return False, f"Failed to extend subscription: {str(e)}"
    
    
    async def cancel_subscription_by_razorpay_id(
        self, 
        razorpay_subscription_id: str
    ) -> Tuple[bool, str]:
        """Cancel subscription by Razorpay subscription ID"""
        try:
            # Find subscription by Razorpay ID
            response = self.supabase.table('user_subscriptions').select('*').eq('razorpay_subscription_id', razorpay_subscription_id).single().execute()
            
            if not response.data:
                return False, f"No subscription found with Razorpay ID: {razorpay_subscription_id}"
            
            subscription = response.data
            
            # Update subscription status
            self.supabase.table('user_subscriptions').update({
                'status': 'cancelled',
                'cancelled_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }).eq('id', subscription['id']).execute()
            
            return True, f"Subscription cancelled: {razorpay_subscription_id}"
            
        except Exception as e:
            return False, f"Failed to cancel subscription: {str(e)}"


# Global instance
billing_service = BillingService()
