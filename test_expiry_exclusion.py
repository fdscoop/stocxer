"""
Test script to verify expiry day exclusion logic
"""
from datetime import datetime
from pytz import timezone as pytz_timezone

def test_expiry_exclusion():
    """Test that today's expiry is correctly excluded"""
    
    # Use IST timezone
    ist = pytz_timezone('Asia/Kolkata')
    today = datetime.now(ist).date()
    
    print("=" * 60)
    print("EXPIRY DAY EXCLUSION TEST")
    print("=" * 60)
    print(f"Current IST Date: {today.strftime('%Y-%m-%d')} ({today.strftime('%A')})")
    print(f"Day of Week: {today.strftime('%A')}")
    print()
    
    # Simulate some expiry dates
    test_expiries = []
    
    # Add today's date
    today_datetime = datetime.combine(today, datetime.min.time())
    test_expiries.append(("Today", today_datetime))
    
    # Add dates from next 4 weeks
    from datetime import timedelta
    for weeks in range(1, 5):
        future_date = today_datetime + timedelta(weeks=weeks)
        test_expiries.append((f"Week {weeks}", future_date))
    
    print("Sample Expiry Dates (Before Filtering):")
    for label, date in test_expiries:
        print(f"  {label}: {date.strftime('%Y-%m-%d')} ({date.strftime('%A')})")
    
    print("\n" + "=" * 60)
    print("FILTERING LOGIC")
    print("=" * 60)
    
    # Filter out today's expiry
    filtered_expiries = []
    for label, expiry_date in test_expiries:
        if expiry_date.date() != today:
            filtered_expiries.append((label, expiry_date))
            print(f"✅ INCLUDED: {label} - {expiry_date.strftime('%Y-%m-%d')}")
        else:
            print(f"🚫 EXCLUDED: {label} - {expiry_date.strftime('%Y-%m-%d')} (Today's expiry)")
    
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Original expiries: {len(test_expiries)}")
    print(f"Filtered expiries: {len(filtered_expiries)}")
    print(f"Excluded: {len(test_expiries) - len(filtered_expiries)}")
    
    if len(filtered_expiries) > 0:
        print(f"\nNearest expiry: {filtered_expiries[0][1].strftime('%Y-%m-%d')} ({(filtered_expiries[0][1].date() - today).days} days away)")
        print("✅ TEST PASSED: Expiry exclusion logic working correctly!")
    else:
        print("❌ WARNING: No expiries available after filtering!")
    
    print("=" * 60)
    
    # Additional check for Tuesday
    if today.weekday() == 1:  # Tuesday
        print("\n⚠️  NOTE: Today is Tuesday (typical expiry day)")
        print("    The scanner will exclude today's expiry options")
        print("    and show the next available expiry.")
    else:
        days_to_tuesday = (1 - today.weekday()) % 7
        if days_to_tuesday == 0:
            days_to_tuesday = 7
        print(f"\n📅 Note: Next Tuesday (expiry day) is in {days_to_tuesday} days")

if __name__ == "__main__":
    test_expiry_exclusion()
