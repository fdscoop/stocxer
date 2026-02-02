#!/usr/bin/env python3
"""
Test all indices for ML module integration.
"""

import os
import requests
from dotenv import load_dotenv
from config.supabase_config import supabase_admin

load_dotenv()

def test_all_indices():
    # Authenticate
    auth = supabase_admin.auth.sign_in_with_password({
        'email': os.getenv('TEST_USER_EMAIL'),
        'password': os.getenv('TEST_USER_PASSWORD')
    })
    headers = {'Authorization': f'Bearer {auth.session.access_token}'}
    
    indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
    
    print('=' * 80)
    print('🔍 TESTING ALL INDICES FOR ML MODULE INTEGRATION')
    print('=' * 80)
    
    results = {}
    
    for idx in indices:
        print(f'\n📊 Testing {idx}...')
        try:
            # Call actionable signal endpoint
            resp = requests.get(
                f'http://localhost:8000/signals/{idx}/actionable',
                headers=headers,
                params={'expiry_type': 'weekly'},
                timeout=120
            )
            
            if resp.status_code == 200:
                data = resp.json()
                ml = data.get('enhanced_ml_prediction', {})
                
                if ml and not ml.get('error'):
                    modules = ml.get('available_modules', {})
                    dir_pred = ml.get('direction_prediction', {})
                    speed_pred = ml.get('speed_prediction', {})
                    iv_pred = ml.get('iv_prediction', {})
                    sim = ml.get('simulation', {})
                    combined = ml.get('combined_recommendation', {})
                    
                    print(f'   ✅ {idx} - ALL ML MODULES WORKING')
                    print(f'      Direction: {dir_pred.get("direction", "N/A")} ({dir_pred.get("confidence", 0):.0%})')
                    print(f'      Speed: {speed_pred.get("category", "N/A")} ({speed_pred.get("confidence", 0):.0%})')
                    print(f'      IV: {iv_pred.get("direction", "N/A")} ({iv_pred.get("confidence", 0):.0%})')
                    grade = sim.get('trade_grade', {})
                    print(f'      Grade: {grade.get("grade", "N/A")}')
                    print(f'      Action: {combined.get("action", "N/A")}')
                    results[idx] = '✅ PASS'
                else:
                    print(f'   ⚠️ {idx} - ML Error: {ml.get("error", "Unknown")}')
                    results[idx] = f'⚠️ ML Error'
            else:
                print(f'   ❌ {idx} - HTTP Error: {resp.status_code}')
                results[idx] = f'❌ HTTP {resp.status_code}'
        except Exception as e:
            print(f'   ❌ {idx} - Exception: {e}')
            results[idx] = f'❌ Exception'
    
    print('\n' + '=' * 80)
    print('📋 SUMMARY')
    print('=' * 80)
    for idx, result in results.items():
        print(f'   {idx}: {result}')
    
    print('\n' + '=' * 80)
    print('✅ INDEX TESTING COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    test_all_indices()
