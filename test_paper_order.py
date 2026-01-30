"""
Test script to manually trigger a paper trading order
This will:
1. Generate a signal from the options scanner
2. Place an order (which will be rejected due to ₹0 balance)
3. Create a paper position
"""
import asyncio
import sys
from src.services.paper_trading_service import paper_trading_service

async def test_paper_order():
    """Test paper trading order placement"""
    
    # Your user ID from the database
    user_id = "4f1d1b44-7459-43fa-8aec-f9b9a0605c4b"
    index = "NSE:NIFTY50-INDEX"  # Fixed: Use proper symbol format
    
    print(f"\n{'='*60}")
    print(f"🧪 TESTING PAPER TRADING ORDER PLACEMENT")
    print(f"{'='*60}\n")
    
    # Step 1: Generate signal
    print(f"📊 Step 1: Generating signal for {index}...")
    signal = await paper_trading_service.generate_signal(index, user_id)
    
    if not signal:
        print("❌ No signal generated")
        return
    
    print(f"✅ Signal generated: {signal.get('action', 'UNKNOWN')}")
    print(f"   Strike: {signal.get('strike', 'N/A')}")
    print(f"   Type: {signal.get('option_type', 'N/A')}")
    print(f"   Entry: ₹{signal.get('entry_price', 0)}")
    print(f"   Target 1: ₹{signal.get('target_1', 0)}")
    print(f"   Target 2: ₹{signal.get('target_2', 0)}")
    print(f"   Stop Loss: ₹{signal.get('stop_loss', 0)}")
    print(f"   Confidence: {signal.get('confidence', {}).get('score', 0)}%")
    
    # Step 2: Save signal
    print(f"\n💾 Step 2: Saving signal to database...")
    saved_signal = await paper_trading_service.save_signal(user_id, signal)
    
    if not saved_signal:
        print("❌ Failed to save signal")
        return
    
    signal_id = saved_signal.get("id")
    print(f"✅ Signal saved with ID: {signal_id}")
    
    # Step 3: Execute order
    action = signal.get("action", "")
    if "BUY" not in action:
        print(f"⚠️  Action is '{action}' - not a BUY signal, stopping test")
        return
    
    print(f"\n📦 Step 3: Executing order for signal...")
    print(f"   This will attempt to place a REAL order via Fyers API")
    print(f"   Expected: ORDER REJECTION (insufficient funds)")
    
    try:
        result = await paper_trading_service.execute_order(
            user_id=user_id,
            signal_id=signal_id,
            signal=signal,
            action=action
        )
        
        if result:
            print(f"\n✅ Order execution completed!")
            print(f"   Position ID: {result.get('id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Entry Price: ₹{result.get('entry_price')}")
            print(f"   Quantity: {result.get('quantity')}")
            print(f"\n📋 Order Response:")
            print(f"   {result.get('order_response', 'No response')}")
            print(f"\n💡 Paper position created successfully!")
            print(f"   Even though order was rejected, position is tracked as if it succeeded.")
        else:
            print("❌ Order execution failed")
            
    except Exception as e:
        print(f"❌ Error executing order: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Check positions
    print(f"\n📊 Step 4: Checking open positions...")
    open_count = await paper_trading_service._count_open_positions(user_id)
    print(f"✅ Open positions: {open_count}")
    
    print(f"\n{'='*60}")
    print(f"✅ TEST COMPLETE")
    print(f"{'='*60}\n")
    print(f"💡 Check the Paper Trading dashboard to see your position!")
    print(f"   URL: http://localhost:3000/paper-trading")
    print(f"\n")

if __name__ == "__main__":
    try:
        asyncio.run(test_paper_order())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(0)
