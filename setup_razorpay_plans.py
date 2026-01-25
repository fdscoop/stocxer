#!/usr/bin/env python3
"""
Setup Razorpay Subscription Plans
Creates required subscription plans in Razorpay for proper subscription management
"""
import os
from src.services.razorpay_service import razorpay_service

def setup_subscription_plans():
    """Create subscription plans in Razorpay"""
    print("🚀 Setting up Razorpay subscription plans...")
    
    if not razorpay_service.client:
        print("❌ Razorpay not configured. Please add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env")
        return False
    
    # Define plans
    plans = [
        {
            'name': 'Stocxer Medium Plan - Monthly',
            'amount_inr': 4999,
            'interval': 'monthly'
        },
        {
            'name': 'Stocxer Pro Plan - Monthly', 
            'amount_inr': 9999,
            'interval': 'monthly'
        }
    ]
    
    created_plans = []
    
    for plan_info in plans:
        print(f"\n📋 Creating plan: {plan_info['name']} (₹{plan_info['amount_inr']})")
        
        success, plan_data = razorpay_service.create_subscription_plan(
            name=plan_info['name'],
            amount_inr=plan_info['amount_inr'],
            interval=plan_info['interval']
        )
        
        if success:
            plan_id = plan_data.get('plan_id')
            print(f"✅ Plan created successfully: {plan_id}")
            print(f"   Status: {plan_data.get('status')}")
            print(f"   Amount: ₹{plan_data.get('amount', 0) // 100}")
            created_plans.append(plan_id)
        else:
            print(f"❌ Failed to create plan: {plan_data.get('error')}")
    
    print(f"\n🎉 Setup complete! Created {len(created_plans)} plans:")
    for plan_id in created_plans:
        print(f"   - {plan_id}")
    
    print("\n💡 Next steps:")
    print("   1. Test subscription creation in your app")
    print("   2. Configure webhooks in Razorpay dashboard:")
    print("      - subscription.charged")
    print("      - subscription.cancelled")
    print("      - payment.captured")
    print("      - payment.failed")
    print(f"   3. Webhook URL: {os.getenv('WEBHOOK_URL', 'https://your-domain.com')}/api/billing/webhook")
    
    return True

if __name__ == "__main__":
    setup_subscription_plans()