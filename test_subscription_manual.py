#!/usr/bin/env python3
"""
Test Regular Subscription Payment Flow
Tests the non-recurring subscription payment approach
"""
import asyncio
import os
from src.services.razorpay_service import razorpay_service

async def test_subscription_order():
    """Test regular order creation for subscription payment"""
    print("🧪 Testing subscription order creation (non-recurring)...")
    
    if not razorpay_service.client:
        print("❌ Razorpay not configured")
        return False
    
    print("📋 Creating order for Medium plan (₹4999)")
    
    success, order_data = razorpay_service.create_order(
        amount_inr=4999,
        receipt='test_sub_monthly_123',
        notes={
            'project': 'stocxer-tradewise',
            'user_id': 'test_user_123',
            'plan_type': 'medium',
            'billing_period': 'monthly',
            'order_type': 'subscription'
        }
    )
    
    if success:
        print("✅ Subscription order created successfully!")
        print(f"   Order ID: {order_data.get('id')}")
        print(f"   Amount: ₹{order_data.get('amount', 0) // 100}")
        print(f"   Currency: {order_data.get('currency')}")
        print("   User pays manually each month ✨")
        return True
    else:
        print(f"❌ Order creation failed: {order_data.get('error')}")
        return False

if __name__ == "__main__":
    asyncio.run(test_subscription_order())