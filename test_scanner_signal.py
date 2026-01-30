"""
Test paper trading with REAL signal from scanner
This uses the actual signal from /signals/NSE:NIFTY50-INDEX/actionable
"""
import asyncio
import httpx
from config.supabase_config import supabase_admin
from src.services.paper_trading_service import PaperTradingService

async def test_with_real_signal():
    print("\n" + "="*60)
    print("🧪 PAPER TRADING WITH REAL SCANNER SIGNAL")
    print("="*60)
    
    # Step 1: Authenticate
    print(f"\n🔐 Step 1: Authenticating...")
    try:
        auth_response = supabase_admin.auth.sign_in_with_password({
            "email": "bineshch@gmail.com",
            "password": "Tra@2026"
        })
        user_id = auth_response.user.id
        print(f"✅ Authenticated as: {auth_response.user.email}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Step 2: Use real signal from scanner (from curl result)
    print(f"\n📊 Step 2: Using real signal from scanner...")
    
    # This is the actual signal from /signals/NSE:NIFTY50-INDEX/actionable
    signal_data = {
        'action': 'WAIT',  # Scanner says WAIT, but we'll use it for testing
        'option': {
            'strike': 25550,
            'type': 'CE',
            'trading_symbol': 'NSE:NIFTY2620325550CE',  # FIXED: Correct Fyers format
            'expiry_info': {
                'days_to_expiry': 4
            }
        },
        'pricing': {
            'entry_price': 139.3
        },
        'targets': {
            'target_1': 195.02,
            'target_2': 250.74,
            'stop_loss': 83.58
        },
        'confidence_breakdown': {
            'total': 22.5
        }
    }
    
    print(f"✅ Signal received from scanner:")
    print(f"   Action: {signal_data['action']} (confidence: {signal_data['confidence_breakdown']['total']}%)")
    print(f"   Trading Symbol: {signal_data['option']['trading_symbol']}")
    print(f"   Strike: {signal_data['option']['strike']} {signal_data['option']['type']}")
    print(f"   Entry: ₹{signal_data['pricing']['entry_price']}")
    
    # For testing, treat as BUY_CALL (even though scanner says WAIT)
    action = 'BUY_CALL'
    print(f"\n   💡 For testing purposes, treating as: {action}")
    
    # Step 3: Format the signal for paper trading
    print(f"\n💾 Step 3: Preparing signal for paper trading...")
    
    # Add NSE: prefix if not present
    trading_symbol = signal_data['option']['trading_symbol']
    if not trading_symbol.startswith('NSE:'):
        trading_symbol = f"NSE:{trading_symbol}"
    else:
        trading_symbol = signal_data['option']['trading_symbol']  # Already has NSE: prefix
    
    print(f"   Full Fyers symbol: {trading_symbol}")
    
    paper_signal = {
        "user_id": user_id,
        "scan_id": None,
        "index": "NIFTY",
        "signal_type": action,
        "option_symbol": trading_symbol,
        "strike": signal_data['option']['strike'],
        "option_type": signal_data['option']['type'],
        "entry_price": signal_data['pricing']['entry_price'],
        "stop_loss": signal_data['targets']['stop_loss'],
        "target_1": signal_data['targets']['target_1'],
        "target_2": signal_data['targets']['target_2'],
        "confidence": signal_data['confidence_breakdown']['total'],
        "trading_mode": "INTRADAY",
        "dte": signal_data['option']['expiry_info']['days_to_expiry'],
        "status": "PENDING"
    }
    
    # Step 4: Save signal to database
    signal_response = supabase_admin.table("paper_trading_signals")\
        .insert(paper_signal)\
        .execute()
    
    signal_id = signal_response.data[0]["id"]
    print(f"✅ Signal saved with ID: {signal_id}")
    
    # Step 5: Execute order via Fyers
    print(f"\n📦 Step 5: Placing order via Fyers API...")
    print(f"   Symbol: {trading_symbol}")
    print(f"   Strike: {paper_signal['strike']} {paper_signal['option_type']}")
    print(f"   Entry: ₹{paper_signal['entry_price']}")
    print(f"   Target 1: ₹{paper_signal['target_1']}")
    print(f"   Target 2: ₹{paper_signal['target_2']}")
    print(f"   Stop Loss: ₹{paper_signal['stop_loss']}")
    print(f"\n   ⚠️  Attempting REAL Fyers order placement...")
    
    service = PaperTradingService()
    result = await service.execute_order(signal_id, user_id, "BUY")
    
    print(f"\n✅ ORDER EXECUTION COMPLETED!")
    print(f"\n📋 Status: {result.get('status')}")
    print(f"📋 Message: {result.get('message')}")
    
    # Step 6: Check Fyers response
    print(f"\n🔍 Fyers API Response:")
    order_resp = result.get('order_response', {})
    if order_resp:
        print(f"   Code: {order_resp.get('code')}")
        print(f"   Message: {order_resp.get('message')}")
        print(f"   Status: {order_resp.get('s')}")
        if 'id' in order_resp:
            print(f"\n   🎯 ORDER ID: {order_resp.get('id')}")
            print(f"   ✅ Order was placed in Fyers!")
            print(f"   ✅ Check: https://myaccount.fyers.in/orders")
    
    print(f"\n💡 Rejection Reason:")
    print(f"   {result.get('rejection_reason', 'None')}")
    
    # Step 7: Check paper position
    print(f"\n📊 Step 7: Paper Trading Position Created:")
    position = result.get('position')
    if position:
        print(f"   ID: {position.get('id')}")
        print(f"   Symbol: {position.get('option_symbol')}")
        print(f"   Quantity: {position.get('quantity')}")
        print(f"   Entry: ₹{position.get('entry_price')}")
        print(f"   Target 1: ₹{position.get('target_1')}")
        print(f"   Target 2: ₹{position.get('target_2')}")
        print(f"   Stop Loss: ₹{position.get('stop_loss')}")
        print(f"   Status: {position.get('status')}")
    
    # Step 8: Get all open positions
    print(f"\n📊 Step 8: All Open Positions:")
    positions_response = supabase_admin.table("paper_trading_positions")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("status", "OPEN")\
        .order("created_at", desc=True)\
        .execute()
    
    if positions_response.data:
        print(f"   Total open positions: {len(positions_response.data)}")
        for idx, pos in enumerate(positions_response.data[:5], 1):
            print(f"\n   Position {idx}:")
            print(f"      Symbol: {pos['option_symbol']}")
            print(f"      Strike: {pos['strike']} {pos['option_type']}")
            print(f"      Qty: {pos['quantity']}")
            print(f"      Entry: ₹{pos['entry_price']}")
            print(f"      Current P&L: ₹{pos.get('current_pnl', 0)}")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE!")
    print("="*60)
    print(f"\n💡 View all positions at: http://localhost:3000/paper-trading")

if __name__ == "__main__":
    asyncio.run(test_with_real_signal())
