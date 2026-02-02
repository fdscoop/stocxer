"""
Test paper trading with REAL Fyers symbol format
This will attempt to place an actual order with Fyers
Expected: Order rejected due to insufficient funds
"""
import asyncio
from config.supabase_config import supabase_admin
from src.services.paper_trading_service import PaperTradingService

async def test_real_order():
    print("\n" + "="*60)
    print("🧪 REAL FYERS ORDER TEST")
    print("="*60)
    
    # Step 1: Authenticate
    print(f"\n🔐 Step 1: Authenticating...")
    try:
        import os
        auth_response = supabase_admin.auth.sign_in_with_password({
            "email": os.getenv("TEST_USER_EMAIL", "test@example.com"),
            "password": os.getenv("TEST_USER_PASSWORD", "test_password")
        })
        user_id = auth_response.user.id
        print(f"✅ Authenticated as: {auth_response.user.email}")
        print(f"   User ID: {user_id}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Step 2: Create signal with REAL Fyers symbol
    print(f"\n📊 Step 2: Creating signal with REAL Fyers symbol...")
    
    # Using a real NIFTY weekly options symbol
    # Format: NSE:NIFTY{YY}{M}{DD}{STRIKE}{CE/PE}
    # Where M is month code: 1-9 for Jan-Sep, O/N/D for Oct/Nov/Dec
    # For Feb 3, 2026 (Monday) expiry: NSE:NIFTY2620325500CE (26 = YY, 2 = Feb, 03 = DD)
    real_symbol = "NSE:NIFTY2620325500CE"  # NIFTY 3 Feb 2026 25500 CE
    
    mock_signal = {
        "index": "NIFTY",
        "action": "BUY CALL",
        "option_symbol": real_symbol,
        "strike": 25500,
        "option_type": "CE",
        "entry_price": 145.50,
        "target_1": 175.00,
        "target_2": 195.00,
        "stop_loss": 115.00,
        "confidence": {
            "score": 72,
            "breakdown": "Real symbol test"
        },
        "expiry_info": {
            "days_to_expiry": 4,
            "expiry_date": "2026-02-03"
        },
        "trading_mode": {
            "mode": "INTRADAY"
        }
    }
    
    print(f"✅ Using REAL Fyers symbol: {real_symbol}")
    print(f"   Strike: 25500 CE")
    print(f"   Entry: ₹145.50")
    
    # Step 3: Save signal to database
    print(f"\n💾 Step 3: Saving signal to database...")
    service = PaperTradingService()
    
    signal_data = {
        "user_id": user_id,
        "scan_id": None,
        "index": mock_signal["index"],
        "signal_type": mock_signal["action"],
        "option_symbol": mock_signal["option_symbol"],
        "strike": mock_signal["strike"],
        "option_type": mock_signal["option_type"],
        "entry_price": mock_signal["entry_price"],
        "stop_loss": mock_signal["stop_loss"],
        "target_1": mock_signal["target_1"],
        "target_2": mock_signal["target_2"],
        "confidence": mock_signal["confidence"]["score"],
        "trading_mode": mock_signal["trading_mode"]["mode"],
        "dte": mock_signal["expiry_info"]["days_to_expiry"],
        "status": "PENDING"
    }
    
    signal_response = supabase_admin.table("paper_trading_signals")\
        .insert(signal_data)\
        .execute()
    
    signal_id = signal_response.data[0]["id"]
    print(f"✅ Signal saved with ID: {signal_id}")
    
    # Step 4: Place order via Fyers
    print(f"\n📦 Step 4: Attempting REAL Fyers order placement...")
    print(f"   ⚠️  This will call the ACTUAL Fyers API")
    print(f"   ⚠️  Expected: Rejection due to insufficient funds")
    print(f"   ⚠️  Symbol: {real_symbol}")
    print()
    
    result = await service.execute_order(signal_id, user_id, "BUY")
    
    print(f"\n✅ ORDER EXECUTION COMPLETED!")
    print(f"\n📋 Result Status: {result.get('status')}")
    print(f"📋 Message: {result.get('message')}")
    
    print(f"\n🔍 Fyers API Response:")
    order_resp = result.get('order_response', {})
    if order_resp:
        print(f"   Code: {order_resp.get('code')}")
        print(f"   Message: {order_resp.get('message')}")
        print(f"   Status: {order_resp.get('s')}")
        if 'id' in order_resp:
            print(f"   ⚠️  ORDER ID RECEIVED: {order_resp.get('id')}")
            print(f"   ⚠️  This means order was ACCEPTED by Fyers!")
    else:
        print(f"   (Empty response)")
    
    print(f"\n💡 Rejection Reason:")
    print(f"   {result.get('rejection_reason', 'None')}")
    
    # Step 5: Check if order appears in Fyers order book
    print(f"\n📊 Step 5: Checking Fyers order book...")
    try:
        from src.api.fyers_client import fyers_client
        
        # First verify client is initialized
        if not fyers_client.fyers:
            # Get user's token
            token_response = supabase_admin.table("fyers_tokens")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("updated_at", desc=True)\
                .limit(1)\
                .execute()
            
            if token_response.data:
                fyers_client.access_token = token_response.data[0]["access_token"]
                fyers_client._initialize_client()
        
        orders = fyers_client.get_orders()
        print(f"✅ Fyers Orders Response: {orders}")
        
        if orders.get('orderBook'):
            print(f"   Total orders in book: {len(orders['orderBook'])}")
            # Check if our order is there
            for order in orders['orderBook']:
                if real_symbol in order.get('symbol', ''):
                    print(f"   🎯 FOUND OUR ORDER!")
                    print(f"      Symbol: {order.get('symbol')}")
                    print(f"      Status: {order.get('status')}")
                    print(f"      Message: {order.get('message')}")
        else:
            print(f"   📭 Order book is empty or order not found")
            
    except Exception as e:
        print(f"   ⚠️  Error checking order book: {e}")
    
    # Step 6: Check paper trading position
    print(f"\n📊 Step 6: Checking paper trading position...")
    position = result.get('position')
    if position:
        print(f"✅ Paper position created:")
        print(f"   ID: {position.get('id')}")
        print(f"   Symbol: {position.get('option_symbol')}")
        print(f"   Quantity: {position.get('quantity')}")
        print(f"   Entry: ₹{position.get('entry_price')}")
        print(f"   Status: {position.get('status')}")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE!")
    print("="*60)
    print(f"\n💡 Check your Fyers account at: https://myaccount.fyers.in/orders")
    print(f"💡 View paper positions at: http://localhost:3000/paper-trading")

if __name__ == "__main__":
    asyncio.run(test_real_order())
