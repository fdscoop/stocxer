"""
Test automated scanner with Bracket Order execution
This will:
1. Start the automated scanner
2. Scanner will detect signals automatically
3. Execute bracket orders with entry, target, and stop loss
4. Show order responses from Fyers
"""
import asyncio
from config.supabase_config import supabase_admin
from src.services.paper_trading_service import PaperTradingService

async def test_automated_scanner():
    print("\n" + "="*70)
    print("🤖 AUTOMATED SCANNER WITH BRACKET ORDER TEST")
    print("="*70)
    
    # Authenticate
    print(f"\n🔐 Authenticating...")
    auth_response = supabase_admin.auth.sign_in_with_password({
        "email": "bineshch@gmail.com",
        "password": "Tra@2026"
    })
    user_id = auth_response.user.id
    print(f"✅ Authenticated as: {auth_response.user.email}")
    
    # Get current config
    print(f"\n📊 Current Configuration:")
    config_response = supabase_admin.table("paper_trading_config")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    if config_response.data:
        config = config_response.data[0]
        print(f"   Enabled: {config['enabled']}")
        print(f"   Indices: {config['indices']}")
        print(f"   Scan Interval: {config['scan_interval_minutes']} minutes")
        print(f"   Max Positions: {config['max_positions']}")
        print(f"   Min Confidence: {config['min_confidence']}%")
    
    # Count current positions
    positions_response = supabase_admin.table("paper_trading_positions")\
        .select("id", count="exact")\
        .eq("user_id", user_id)\
        .eq("status", "OPEN")\
        .execute()
    
    open_positions = positions_response.count if positions_response.count else 0
    print(f"\n📈 Current Open Positions: {open_positions}/{config['max_positions']}")
    
    # Run one scan cycle manually (for testing)
    print(f"\n🔍 Running ONE scan cycle...")
    print(f"   This will scan: {', '.join(config['indices'])}")
    print(f"   Looking for signals with confidence >= {config['min_confidence']}%")
    print(f"   Will place BRACKET ORDERS (Entry + Target + Stop Loss)")
    print(f"\n" + "-"*70)
    
    service = PaperTradingService()
    
    # Scan each index
    for index in config['indices']:
        print(f"\n🔎 Scanning {index}...")
        
        try:
            # Generate signal
            signal = await service.generate_signal(index, user_id)
            
            if not signal:
                print(f"   ❌ No signal generated")
                continue
            
            action = signal.get("action", "WAIT")
            confidence = signal.get("confidence", {}).get("score", 0)
            
            print(f"   Action: {action}")
            print(f"   Confidence: {confidence}%")
            
            # FOR TESTING: Place order even if WAIT or low confidence
            print(f"   🧪 TEST MODE: Forcing order placement (ignoring action/confidence)")
            
            # Force action to BUY CALL for testing
            test_action = "BUY CALL"
            
            if True:  # Always execute for testing
                if True:  # Ignore confidence for testing
                    print(f"   ✅ Test mode: Executing order as {test_action}...")
                    
                    # Save signal (with original data)
                    saved_signal = await service.save_signal(user_id, signal)
                    
                    if saved_signal:
                        print(f"   Signal ID: {saved_signal['id']}")
                        print(f"   Symbol: {saved_signal['option_symbol']}")
                        print(f"   Entry: ₹{saved_signal['entry_price']}")
                        print(f"   Target: ₹{saved_signal['target_1']}")
                        print(f"   Stop Loss: ₹{saved_signal['stop_loss']}")
                        
                        # Execute bracket order
                        print(f"\n   🚀 Placing BRACKET ORDER...")
                        result = await service.execute_order(
                            saved_signal["id"],
                            user_id,
                            action="BUY"
                        )
                        
                        print(f"\n   📊 Order Execution Result:")
                        print(f"      Status: {result.get('status')}")
                        print(f"      Message: {result.get('message')}")
                        
                        order_resp = result.get('order_response', {})
                        if order_resp:
                            print(f"\n   🔍 Fyers Response:")
                            if 'entry_order' in order_resp:
                                entry = order_resp['entry_order']
                                print(f"      Entry Order:")
                                print(f"         Code: {entry.get('code')}")
                                print(f"         Message: {entry.get('message')}")
                                if entry.get('id'):
                                    print(f"         Order ID: {entry.get('id')}")
                                    print(f"         ✅ Order placed in Fyers!")
                            
                            if order_resp.get('bracket_order'):
                                print(f"      Bracket Order Type: {order_resp.get('order_type')}")
                                print(f"      Target: ₹{order_resp.get('target')}")
                                print(f"      Stop Loss: ₹{order_resp.get('stop_loss')}")
                        
                        # Check position created
                        if result.get('position'):
                            pos = result['position']
                            print(f"\n   📈 Paper Position Created:")
                            print(f"      ID: {pos.get('id')}")
                            print(f"      Quantity: {pos.get('quantity')}")
                            print(f"      Status: {pos.get('status')}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Show final positions
    print(f"\n" + "="*70)
    print(f"📊 SCAN COMPLETE - Checking Positions")
    print("="*70)
    
    final_positions = supabase_admin.table("paper_trading_positions")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("status", "OPEN")\
        .order("created_at", desc=True)\
        .limit(5)\
        .execute()
    
    if final_positions.data:
        print(f"\n✅ Open Positions: {len(final_positions.data)}")
        for idx, pos in enumerate(final_positions.data, 1):
            print(f"\n   Position {idx}:")
            print(f"      Index: {pos['index']}")
            print(f"      Symbol: {pos['option_symbol']}")
            print(f"      Strike: {pos['strike']} {pos['option_type']}")
            print(f"      Qty: {pos['quantity']}")
            print(f"      Entry: ₹{pos['entry_price']}")
            print(f"      Target 1: ₹{pos['target_1']}")
            print(f"      Stop Loss: ₹{pos['stop_loss']}")
            
            # Check for Fyers order ID
            order_resp = pos.get('order_response')
            if order_resp and isinstance(order_resp, dict):
                if order_resp.get('entry_order', {}).get('id'):
                    print(f"      🎯 Fyers Order ID: {order_resp['entry_order']['id']}")
    
    print(f"\n" + "="*70)
    print(f"💡 View dashboard at: http://localhost:3000/paper-trading")
    print(f"💡 Check Fyers orders at: https://myaccount.fyers.in/orders")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_automated_scanner())
