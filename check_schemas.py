"""Check table schemas in Supabase"""
from config.supabase_config import get_supabase_admin_client
import json

supabase = get_supabase_admin_client()

# Check option_scanner_results schema
print('=== OPTION_SCANNER_RESULTS TABLE ===')
try:
    result = supabase.table('option_scanner_results').select('*').limit(1).execute()
    if result.data:
        print('Sample record:')
        print(json.dumps(result.data[0], indent=2, default=str))
        print('\nColumns:', list(result.data[0].keys()))
    else:
        print('No records found')
except Exception as e:
    print(f'Error: {e}')

print('\n=== SCREENER_RESULTS TABLE ===')
try:
    result = supabase.table('screener_results').select('*').limit(1).execute()
    if result.data:
        print('Sample record:')
        print(json.dumps(result.data[0], indent=2, default=str))
        print('\nColumns:', list(result.data[0].keys()))
    else:
        print('No records found')
except Exception as e:
    print(f'Error: {e}')

print('\n=== AI_CHAT_HISTORY TABLE ===')
try:
    result = supabase.table('ai_chat_history').select('*').limit(1).execute()
    if result.data:
        print('Sample record:')
        print(json.dumps(result.data[0], indent=2, default=str))
        print('\nColumns:', list(result.data[0].keys()))
    else:
        print('No records found')
except Exception as e:
    print(f'Error: {e}')
