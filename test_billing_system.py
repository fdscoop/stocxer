"""
Test script for billing system
Run this to verify the billing system is working correctly
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_billing_service():
    """Test billing service functionality"""
    print("🧪 Testing Billing Service...")
    
    try:
        from src.services.billing_service import billing_service
        print("✅ Billing service imported successfully")
        
        # Test pricing configuration
        from src.models.billing_models import PricingConfig
        pricing = PricingConfig()
        
        option_cost = pricing.calculate_scan_cost('option_scan', 1)
        stock_cost = pricing.calculate_scan_cost('stock_scan', 1)
        bulk_cost = pricing.calculate_scan_cost('bulk_scan', 50)
        
        print(f"✅ Pricing configured:")
        print(f"   - Option scan: ₹{option_cost}")
        print(f"   - Stock scan: ₹{stock_cost}")
        print(f"   - Bulk scan (50 stocks): ₹{bulk_cost}")
        
        # Test plan limits
        free_limits = await billing_service.get_plan_limits('free')
        medium_limits = await billing_service.get_plan_limits('medium')
        pro_limits = await billing_service.get_plan_limits('pro')
        
        if free_limits and medium_limits and pro_limits:
            print(f"✅ Plan limits configured:")
            print(f"   - Free: {free_limits.daily_option_scans} option scans/day")
            print(f"   - Medium: {medium_limits.daily_option_scans} option scans/day")
            print(f"   - Pro: {'Unlimited' if pro_limits.daily_option_scans is None else pro_limits.daily_option_scans}")
        
        # Test credit packs
        packs = await billing_service.get_credit_packs()
        if packs:
            print(f"✅ Credit packs configured: {len(packs)} packs")
            for pack in packs:
                print(f"   - {pack.name}: ₹{pack.amount_inr} = {pack.total_credits} credits")
        
        print("\n✅ All billing service tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing billing service: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_razorpay_service():
    """Test Razorpay service functionality"""
    print("\n🧪 Testing Razorpay Service...")
    
    try:
        from src.services.razorpay_service import razorpay_service
        print("✅ Razorpay service imported successfully")
        
        # Check if credentials are configured
        if not os.getenv('RAZORPAY_KEY_ID'):
            print("⚠️  RAZORPAY_KEY_ID not configured in .env")
            print("   Add your Razorpay test credentials to continue")
            return False
        
        print("✅ Razorpay credentials configured")
        
        # Test order creation (with test amount)
        success, order_data = razorpay_service.create_order(
            amount_inr=1,  # ₹1 for testing
            receipt="test_order_123",
            notes={'test': 'true'}
        )
        
        if success:
            print(f"✅ Order creation works")
            print(f"   - Order ID: {order_data.get('order_id', 'N/A')}")
        else:
            print(f"❌ Order creation failed: {order_data.get('error')}")
            return False
        
        print("\n✅ All Razorpay service tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Razorpay service: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_schema():
    """Test if database tables exist"""
    print("\n🧪 Testing Database Schema...")
    
    try:
        from config.supabase_config import supabase
        
        # Test if tables exist by querying them
        tables = [
            'user_subscriptions',
            'user_credits',
            'credit_transactions',
            'usage_logs',
            'plan_limits',
            'credit_packs',
            'payment_history'
        ]
        
        for table in tables:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                print(f"✅ Table exists: {table}")
            except Exception as e:
                print(f"❌ Table missing or error: {table} - {str(e)}")
                return False
        
        print("\n✅ All database tables exist!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        print("   Make sure you've run the migration: database/migrations/subscription_schema.sql")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("TRADEWISE BILLING SYSTEM TEST SUITE")
    print("=" * 60)
    print()
    
    results = []
    
    # Test billing service
    results.append(await test_billing_service())
    
    # Test Razorpay service
    results.append(await test_razorpay_service())
    
    # Test database schema
    results.append(await test_database_schema())
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\n🎉 Billing system is ready to use!")
        print("\nNext steps:")
        print("1. Start the server: uvicorn main:app --reload")
        print("2. Test billing endpoints: GET /api/billing/status")
        print("3. Configure Razorpay webhooks")
        print("4. Add billing checks to scan endpoints")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total})")
        print("\nPlease check the errors above and:")
        print("1. Run database migration if tables are missing")
        print("2. Configure Razorpay credentials in .env")
        print("3. Check Supabase connection")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
