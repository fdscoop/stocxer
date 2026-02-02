#!/usr/bin/env python3
"""Test option scanner for all indices"""

import asyncio
import sys
sys.path.insert(0, '/Users/bineshbalan/TradeWise')

from src.analytics.index_options import IndexOptionsAnalyzer
from src.api.fyers_client import fyers_client

async def test():
    # Initialize fyers_client from DB token
    from supabase import create_client
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
    result = supabase.table('fyers_tokens').select('access_token').order('updated_at', desc=True).limit(1).execute()
    if result.data:
        fyers_client.access_token = result.data[0]['access_token']
        fyers_client._initialize_client()
        print(f'✅ Fyers client initialized')
    
    analyzer = IndexOptionsAnalyzer(fyers_client)
    
    for index in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
        print(f'\nTesting {index}...')
        try:
            result = analyzer.analyze_option_chain(index, 'weekly')
            if result:
                print(f'✅ {index}: spot={result.spot_price}, pcr={result.pcr_oi:.2f}, max_pain={result.max_pain}, strikes={len(result.strikes)}')
            else:
                print(f'❌ {index}: No result returned')
        except Exception as e:
            import traceback
            print(f'❌ {index} Error: {e}')
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
