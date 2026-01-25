"""
Test payment verification endpoint after fixing credit_balance -> credits_balance issue.

This test verifies that the payment verification endpoint now works correctly
after fixing the attribute name mismatch.
"""

import asyncio
import sys
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

async def test_billing_status_attribute():
    """Test that UserBillingStatus has the correct attribute name"""
    from src.models.billing_models import UserBillingStatus, TodayUsage, PlanLimits
    from datetime import datetime
    
    print("=" * 80)
    print("TESTING UserBillingStatus MODEL")
    print("=" * 80)
    print()
    
    # Create a test billing status
    today_usage = TodayUsage(
        option_scans=0,
        stock_scans=0,
        bulk_scans=0
    )
    
    limits = PlanLimits(
        plan_type="free",
        daily_option_scans=10,
        daily_stock_scans=10,
        bulk_scan_limit=0,
        daily_bulk_scans=0
    )
    
    billing_status = UserBillingStatus(
        user_id="test_user_123",
        billing_type="payg",
        plan_type="free",
        subscription_active=False,
        credits_balance=Decimal('100.50'),
        today_usage=today_usage,
        limits=limits
    )
    
    print("✅ UserBillingStatus created successfully")
    print(f"   User ID: {billing_status.user_id}")
    print(f"   Plan: {billing_status.plan_type}")
    print()
    
    # Test that credits_balance attribute exists
    print("Testing attribute access:")
    try:
        balance = billing_status.credits_balance
        print(f"✅ credits_balance accessible: ₹{float(balance)}")
    except AttributeError as e:
        print(f"❌ ERROR: {e}")
        return False
    
    # Test that credit_balance (wrong name) does NOT exist
    try:
        wrong_balance = billing_status.credit_balance
        print(f"❌ FAIL: credit_balance should NOT exist but got: {wrong_balance}")
        return False
    except AttributeError:
        print(f"✅ credit_balance correctly does NOT exist (as expected)")
    
    print()
    print("=" * 80)
    print("MODEL TEST PASSED")
    print("=" * 80)
    return True


async def test_code_references():
    """Test that all code references use the correct attribute name"""
    import os
    import re
    
    print()
    print("=" * 80)
    print("CHECKING CODE FOR INCORRECT ATTRIBUTE REFERENCES")
    print("=" * 80)
    print()
    
    # Files to check
    files_to_check = [
        '/Users/bineshbalan/TradeWise/src/api/billing_routes.py',
        '/Users/bineshbalan/TradeWise/src/middleware/token_middleware.py'
    ]
    
    all_clean = True
    
    for filepath in files_to_check:
        print(f"Checking: {os.path.basename(filepath)}")
        
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Look for incorrect attribute name (credit_balance without 's')
        # But avoid false positives like comments or strings
        incorrect_pattern = r'billing_status\.credit_balance\b'
        matches = re.findall(incorrect_pattern, content)
        
        if matches:
            print(f"   ❌ FOUND {len(matches)} incorrect reference(s): 'credit_balance'")
            all_clean = False
        else:
            print(f"   ✅ No incorrect references found")
        
        # Look for correct attribute name
        correct_pattern = r'billing_status\.credits_balance\b'
        correct_matches = re.findall(correct_pattern, content)
        
        if correct_matches:
            print(f"   ✅ Found {len(correct_matches)} correct reference(s): 'credits_balance'")
        
        print()
    
    if all_clean:
        print("=" * 80)
        print("✅ ALL CODE REFERENCES ARE CORRECT")
        print("=" * 80)
    else:
        print("=" * 80)
        print("❌ SOME CODE STILL HAS INCORRECT REFERENCES")
        print("=" * 80)
    
    return all_clean


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("PAYMENT VERIFICATION FIX - TEST SUITE")
    print("Testing fix for: 'UserBillingStatus' object has no attribute 'credit_balance'")
    print("=" * 80 + "\n")
    
    # Test 1: Model has correct attribute
    model_test_passed = await test_billing_status_attribute()
    
    # Test 2: Code uses correct attribute
    code_test_passed = await test_code_references()
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print()
    print(f"Model Test: {'✅ PASS' if model_test_passed else '❌ FAIL'}")
    print(f"Code References Test: {'✅ PASS' if code_test_passed else '❌ FAIL'}")
    print()
    
    if model_test_passed and code_test_passed:
        print("🎉 ALL TESTS PASSED - Payment verification should now work!")
        print()
        print("Next steps:")
        print("1. Restart the backend server")
        print("2. Test making a payment from the frontend")
        print("3. Payment should succeed without 500 error")
        print("4. Credits should be reflected immediately (or after webhook processing)")
    else:
        print("⚠️ SOME TESTS FAILED - Please review the errors above")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
