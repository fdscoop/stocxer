"""
Directly test signal save with index
"""
import asyncio
from src.services.paper_trading_service import PaperTradingService
from config.supabase_config import supabase_admin

async def test():
    # Authenticate
    auth_response = supabase_admin.auth.sign_in_with_password({
        'email': 'bineshch@gmail.com',
        'password': 'Tra@2026'
    })
    user_id = auth_response.user.id
    print(f"✅ Authenticated\n")
    
    service = PaperTradingService()
    
    # Create a mock BANKNIFTY signal
    mock_signal_banknifty = {
        "action": "BUY CALL",
        "market_context": {
            "index": "BANKNIFTY"  # This should be injected by generate_signal
        },
        "option": {
            "trading_symbol": "NSE:BANKNIFTY26FEB60000CE",
            "strike": 60000,
            "type": "CE",
            "expiry_info": {"days_to_expiry": 25}
        },
        "entry": {"price": 990.95},
        "targets": {
            "target_1": 1387.33,
            "target_2": 1500,
            "stop_loss": 594.57
        },
        "confidence": {"score": 75},
        "trading_mode": {"mode": "INTRADAY"}
    }
    
    print("Testing BANKNIFTY signal save...")
    saved_signal = await service.save_signal(user_id, mock_signal_banknifty)
    
    if saved_signal:
        print(f"✅ Signal saved")
        print(f"   Signal ID: {saved_signal['id']}")
        print(f"   Index: {saved_signal['index']}")
        print(f"   Symbol: {saved_signal['option_symbol']}")
        
        # Test execute_order
        print(f"\n📤 Testing order execution...")
        result = await service.execute_order(saved_signal['id'], user_id, 'BUY')
        print(f"   Message: {result.get('message')}")
        
        # Check position
        position_response = supabase_admin.table('paper_trading_positions')\
            .select('*')\
            .eq('signal_id', saved_signal['id'])\
            .execute()
        
        if position_response.data:
            position = position_response.data[0]
            print(f"\n📊 Position created:")
            print(f"   Index: {position['index']}")
            print(f"   Symbol: {position['option_symbol']}")
            print(f"   Quantity: {position['quantity']}")
            print(f"   Expected lot size for BANKNIFTY: 30")
            print(f"   Actual quantity should be multiple of 30")
    else:
        print(f"❌ Failed to save signal")
    
    print(f"\n{'='*70}")
    
    # Create a mock SENSEX signal  
    mock_signal_sensex = {
        "action": "BUY CALL",
        "market_context": {
            "index": "SENSEX"
        },
        "option": {
            "trading_symbol": "NSE:SENSEX26FEB82000CE",
            "strike": 82000,
            "type": "CE",
            "expiry_info": {"days_to_expiry": 25}
        },
        "entry": {"price": 500},
        "targets": {
            "target_1": 650,
            "target_2": 700,
            "stop_loss": 350
        },
        "confidence": {"score": 70},
        "trading_mode": {"mode": "INTRADAY"}
    }
    
    print("Testing SENSEX signal save...")
    saved_signal = await service.save_signal(user_id, mock_signal_sensex)
    
    if saved_signal:
        print(f"✅ Signal saved")
        print(f"   Signal ID: {saved_signal['id']}")
        print(f"   Index: {saved_signal['index']}")
        print(f"   Symbol: {saved_signal['option_symbol']}")
        
        # Test execute_order
        print(f"\n📤 Testing order execution...")
        result = await service.execute_order(saved_signal['id'], user_id, 'BUY')
        print(f"   Message: {result.get('message')}")
        
        # Check position
        position_response = supabase_admin.table('paper_trading_positions')\
            .select('*')\
            .eq('signal_id', saved_signal['id'])\
            .execute()
        
        if position_response.data:
            position = position_response.data[0]
            print(f"\n📊 Position created:")
            print(f"   Index: {position['index']}")
            print(f"   Symbol: {position['option_symbol']}")
            print(f"   Quantity: {position['quantity']}")
            print(f"   Expected lot size for SENSEX: 10")
            print(f"   Actual quantity should be multiple of 10")
    else:
        print(f"❌ Failed to save signal")

asyncio.run(test())
