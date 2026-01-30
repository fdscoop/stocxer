"""
Test signal generation with index injection
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
    print(f"✅ Authenticated as: {auth_response.user.email}\n")
    
    service = PaperTradingService()
    
    # Test for each index
    for index in ['NIFTY', 'BANKNIFTY', 'SENSEX']:
        print(f"{'='*70}")
        print(f"Testing {index}")
        print(f"{'='*70}")
        
        # Generate signal
        signal = await service.generate_signal(index, user_id)
        
        if signal:
            print(f"✅ Signal generated")
            print(f"   Action: {signal.get('action')}")
            print(f"   Symbol: {signal.get('option', {}).get('trading_symbol')}")
            print(f"   Market Context Index: {signal.get('market_context', {}).get('index')}")
            
            # Save signal
            saved_signal = await service.save_signal(user_id, signal)
            
            if saved_signal:
                print(f"✅ Signal saved to database")
                print(f"   Signal ID: {saved_signal['id']}")
                print(f"   Database Index: {saved_signal['index']}")
                print(f"   Database Symbol: {saved_signal['option_symbol']}")
                
                # If actionable, test execute_order
                if signal.get('action') in ['BUY CALL', 'BUY PUT']:
                    print(f"\n📤 Testing order execution...")
                    result = await service.execute_order(saved_signal['id'], user_id, 'BUY')
                    print(f"   Result: {result.get('message')}")
                    
                    # Check created position
                    position_response = supabase_admin.table('paper_trading_positions')\
                        .select('*')\
                        .eq('signal_id', saved_signal['id'])\
                        .execute()
                    
                    if position_response.data:
                        position = position_response.data[0]
                        print(f"\n📊 Position created:")
                        print(f"   Position Index: {position['index']}")
                        print(f"   Position Symbol: {position['option_symbol']}")
                        print(f"   Position Quantity: {position['quantity']}")
            else:
                print(f"❌ Failed to save signal")
        else:
            print(f"❌ No signal generated")
        
        print(f"\n")

asyncio.run(test())
