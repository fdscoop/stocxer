#!/usr/bin/env python3
"""
Test Razorpay Subscription Creation
Quick test to verify the subscription API works
"""
import asyncio
import os
from src.services.razorpay_service import razorpay_service

async def test_subscription_creation():
    """Test subscription creation without customer object"""
    print("🧪 Testing subscription creation...")
    
    if not razorpay_service.client:
        print("❌ Razorpay not configured")
        return False
    
    # Use existing plan IDs from setup
    plan_id = 'plan_S8Epld37obAsh9'  # Medium plan
    
    print(f"📋 Creating subscription with plan: {plan_id}")
    
    success, sub_data = razorpay_service.create_subscription(
        plan_id=plan_id,
        customer_email='test@example.com',
        customer_name='Test User',
        user_id='test_user_123'
    )
    
    if success:
        print("✅ Subscription created successfully!")
        print(f"   Subscription ID: {sub_data.get('subscription_id')}")
        print(f"   Status: {sub_data.get('status')}")
        print(f"   Short URL: {sub_data.get('short_url')}")
        return True
    else:
        print(f"❌ Subscription creation failed: {sub_data.get('error')}")
        return False

if __name__ == "__main__":
    asyncio.run(test_subscription_creation())