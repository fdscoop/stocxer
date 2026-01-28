#!/usr/bin/env python3
"""Test the option scan with fyers_symbol field"""

import requests
import json
import asyncio
from src.services.auth_service import auth_service
from src.models.auth_models import UserLogin

async def get_token():
    login_data = UserLogin(email='bineshch@gmail.com', password='Tra@2026')
    result = await auth_service.login_user(login_data)
    return result.access_token

def run_scan():
    token = asyncio.run(get_token())
    print(f"Got token: {token[:50]}...")
    
    headers = {'Authorization': f'Bearer {token}'}
    print("Making scan request...")
    
    try:
        resp = requests.get('http://localhost:8000/options/scan?index=NIFTY', headers=headers, timeout=120)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            d = resp.json()
            print(f"\n=== Scan Results ===")
            print(f"Data Source: {d.get('data_source')}")
            print(f"Total Options: {d.get('total_options')}")
            print(f"Expiry: {d.get('market_data', {}).get('expiry_date')}")
            
            opts = d.get('options', [])[:5]
            print(f"\nTop 5 Options:")
            for o in opts:
                print(f"\n  {o.get('type')} {o.get('strike')}:")
                print(f"    Fyers Symbol: {o.get('fyers_symbol', 'NOT SET')}")
                print(f"    LTP: {o.get('ltp')}")
                entry = o.get('entry_analysis', {})
                print(f"    Entry Grade: {entry.get('entry_grade', 'N/A')}")
                print(f"    SL: {entry.get('option_stop_loss', 'N/A')}")
                print(f"    T1: {entry.get('option_target_1', 'N/A')}")
            
            # Save full response
            with open('/tmp/scan_result.json', 'w') as f:
                json.dump(d, f, indent=2)
            print("\nFull result saved to /tmp/scan_result.json")
        else:
            print(f"Error: {resp.text[:500]}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    run_scan()
