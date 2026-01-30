"""
Simple test to place a paper trading order with authentication
"""
import asyncio
import sys
from datetime import datetime
from src.services.paper_trading_service import paper_trading_service
from config.supabase_config import get_supabase_client

async def test_paper_order_simple():
    """Test paper trading with authentication"""
    
    print(f"\n{'='*60}")
    print(f"🧪 PAPER TRADING ORDER TEST (WITH AUTH)")
    print(f"{'='*60}\n")
    
    # Step 1: Authenticate
    print("🔐 Step 1: Authenticating...")
    try:
        supabase = get_supabase_client()
        auth_response = supabase.auth.sign_in_with_password({
            "email": "bineshch@gmail.com",
            "password": "Tra@2026"
        })
        
        user = auth_response.user
        user_id = str(user.id)
        print(f"✅ Authenticated as: {user.email}")
        print(f"   User ID: {user_id}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Step 2: Create a mock signal (simulating buy signal from scanner)
    print(f"\n📊 Step 2: Creating test signal...")
    
    # Mock signal data (as if it came from options scanner)
    mock_signal = {
        "index": "NIFTY",
        "action": "BUY CALL",  # or "BUY PUT"
        "option_symbol": "NSE:NIFTY2630325500CE",  # Example
        "strike": 25500,
        "option_type": "CE",
        "entry_price": 150.50,
        "target_1": 180.00,
        "target_2": 200.00,
        "stop_loss": 120.00,
        "confidence": {
            "score": 75,
            "breakdown": "Mock signal for testing"
        },
        "trading_mode": "intraday",
        "dte": 0,
        "expiry": "2026-02-03"
    }
    
    print(f"✅ Test signal created:")
    print(f"   Action: {mock_signal['action']}")
    print(f"   Strike: {mock_signal['strike']} {mock_signal['option_type']}")
    print(f"   Entry: ₹{mock_signal['entry_price']}")
    print(f"   Target 1: ₹{mock_signal['target_1']}")
    print(f"   Target 2: ₹{mock_signal['target_2']}")
    print(f"   Stop Loss: ₹{mock_signal['stop_loss']}")
    print(f"   Confidence: {mock_signal['confidence']['score']}%")
    
    # Step 3: Save signal to database
    print(f"\n💾 Step 3: Saving signal to database...")
    try:
        # Save signal directly to database
        signal_data = {
            "user_id": user_id,
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
            "trading_mode": mock_signal["trading_mode"].upper(),
            "dte": mock_signal["dte"],
            "status": "PENDING"
        }
        
        response = paper_trading_service.supabase.table("paper_trading_signals")\
            .insert(signal_data)\
            .execute()
        
        if not response.data:
            print("❌ Failed to save signal")
            return
        
        saved_signal = response.data[0]
        signal_id = saved_signal.get("id")
        print(f"✅ Signal saved with ID: {signal_id}")
    except Exception as e:
        print(f"❌ Error saving signal: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Execute order (will attempt real Fyers order, expected to be rejected)
    print(f"\n📦 Step 4: Placing order via Fyers API...")
    print(f"   ⚠️  This will attempt a REAL order placement")
    print(f"   ⚠️  Expected: REJECTION due to insufficient funds (₹0 balance)")
    
    try:
        result = await paper_trading_service.execute_order(
            signal_id=signal_id,
            user_id=user_id,
            action="BUY"
        )
        
        if result:
            print(f"\n✅ ORDER PLACEMENT COMPLETED!")
            print(f"\n📋 Position Details:")
            print(f"   Position ID: {result.get('id')}")
            print(f"   Symbol: {result.get('option_symbol')}")
            print(f"   Strike: {result.get('strike')} {result.get('option_type')}")
            print(f"   Quantity: {result.get('quantity')}")
            print(f"   Entry Price: ₹{result.get('entry_price')}")
            print(f"   Status: {result.get('status')}")
            
            print(f"\n🔍 Fyers Order Response:")
            order_response = result.get('order_response', {})
            if order_response:
                print(f"   {order_response}")
            else:
                print(f"   (Order was rejected as expected)")
            
            print(f"\n💡 Paper Position Created:")
            print(f"   Even though the Fyers order was rejected,")
            print(f"   a paper trading position has been created!")
            print(f"   You can track this position as if it was real.")
        else:
            print("❌ Order execution returned no result")
    
    except Exception as e:
        print(f"❌ Error executing order: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 5: Check positions
    print(f"\n📊 Step 5: Checking open positions...")
    try:
        open_count = await paper_trading_service._count_open_positions(user_id)
        print(f"✅ You now have {open_count} open position(s)")
    except Exception as e:
        print(f"⚠️  Could not count positions: {e}")
    
    # Step 6: View in database
    print(f"\n🔍 Step 6: Retrieving position from database...")
    try:
        positions_response = paper_trading_service.supabase.table("paper_trading_positions")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "OPEN")\
            .execute()
        
        if positions_response.data:
            for pos in positions_response.data:
                print(f"\n   Position: {pos.get('option_symbol')}")
                print(f"   Entry: ₹{pos.get('entry_price')}")
                print(f"   Quantity: {pos.get('quantity')}")
                print(f"   Target 1: ₹{pos.get('target_1')}")
                print(f"   Target 2: ₹{pos.get('target_2')}")
                print(f"   Stop Loss: ₹{pos.get('stop_loss')}")
    except Exception as e:
        print(f"⚠️  Could not retrieve positions: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ TEST COMPLETE!")
    print(f"{'='*60}\n")
    print(f"📱 View your paper trading positions at:")
    print(f"   http://localhost:3000/paper-trading")
    print(f"\n")

if __name__ == "__main__":
    try:
        asyncio.run(test_paper_order_simple())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(0)
