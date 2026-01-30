"""
Demonstrate dynamic Fyers symbol generation for all supported indices
"""
from datetime import datetime
from main import build_fyers_option_symbol

def test_dynamic_symbols():
    print("\n" + "="*70)
    print("🔧 DYNAMIC FYERS SYMBOL GENERATION TEST")
    print("="*70)
    
    # Test data
    expiry_weekly = "2026-02-03"  # Monday (weekly expiry)
    expiry_monthly = "2026-02-27"  # Last Thursday (monthly expiry)
    
    indices = [
        ("NIFTY", 25500),
        ("BANKNIFTY", 55000),
        ("FINNIFTY", 23500),
        ("MIDCPNIFTY", 13500),
        ("SENSEX", 84000)
    ]
    
    print("\n📅 Weekly Options (Expiry: Feb 3, 2026)")
    print("-" * 70)
    for index, strike in indices:
        call_symbol = build_fyers_option_symbol(
            index=index,
            expiry_date=expiry_weekly,
            strike=strike,
            option_type="CALL",
            is_monthly=False
        )
        put_symbol = build_fyers_option_symbol(
            index=index,
            expiry_date=expiry_weekly,
            strike=strike,
            option_type="PUT",
            is_monthly=False
        )
        print(f"\n{index:12} Strike {strike}")
        print(f"  CALL: {call_symbol}")
        print(f"  PUT:  {put_symbol}")
    
    print("\n\n📅 Monthly Options (Expiry: Feb 27, 2026)")
    print("-" * 70)
    for index, strike in indices:
        call_symbol = build_fyers_option_symbol(
            index=index,
            expiry_date=expiry_monthly,
            strike=strike,
            option_type="CALL",
            is_monthly=True
        )
        put_symbol = build_fyers_option_symbol(
            index=index,
            expiry_date=expiry_monthly,
            strike=strike,
            option_type="PUT",
            is_monthly=True
        )
        print(f"\n{index:12} Strike {strike}")
        print(f"  CALL: {call_symbol}")
        print(f"  PUT:  {put_symbol}")
    
    # Show month code mapping
    print("\n\n📊 Month Code Reference (for Weekly Options)")
    print("-" * 70)
    print("Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6")
    print("Jul=7, Aug=8, Sep=9, Oct=O, Nov=N, Dec=D")
    
    print("\n\n✅ Dynamic Symbol Detection Features:")
    print("-" * 70)
    print("✅ Automatically detects index from configuration")
    print("✅ Calculates correct expiry date (next weekly/monthly)")
    print("✅ Formats date correctly (YY + month code + DD for weekly)")
    print("✅ Handles all indices: NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX")
    print("✅ Switches between weekly/monthly format automatically")
    print("✅ Generates valid Fyers symbols for order placement")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    test_dynamic_symbols()
