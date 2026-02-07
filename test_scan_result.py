#!/usr/bin/env python3
"""Quick test to show full scan results for expiry day"""
import requests

def show_scan(expiry, desc):
    print("=" * 60)
    print(f"📅 {desc}")
    print("=" * 60)
    
    r = requests.get(f'http://localhost:8000/signals/NIFTY/actionable?expiry={expiry}', timeout=120)
    d = r.json()
    
    print(f"Signal: {d.get('signal')}")
    print(f"Action: {d.get('action')}")
    print(f"Is Expiry Day: {d.get('is_expiry_day')}")
    print()
    
    opt = d.get('option', {})
    print(f"OPTION: {opt.get('type')} {opt.get('strike')} - {opt.get('trading_symbol')}")
    print(f"Expiry: {opt.get('expiry_date')} | DTE: {opt.get('expiry_info',{}).get('days_to_expiry')} days")
    print()
    
    p = d.get('pricing', {})
    print(f"LTP: Rs.{p.get('ltp')} | Entry: Rs.{p.get('entry_price')}")
    
    t = d.get('targets', {})
    print(f"Stop Loss: Rs.{t.get('stop_loss')}")
    print(f"Target 1: Rs.{t.get('target_1')}")
    print(f"Target 2: Rs.{t.get('target_2')}")
    print()
    
    c = d.get('confidence', {})
    print(f"Confidence: {c.get('score')} ({c.get('level')})")
    print()
    
    warnings = d.get('warnings', [])
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("No warnings")
    print()

if __name__ == "__main__":
    show_scan("weekly", "WEEKLY EXPIRY (Feb 3 - Expiry Day, 1 DTE)")
    print("\n")
    
    import time
    time.sleep(3)
    
    show_scan("next_weekly", "NEXT WEEKLY EXPIRY (Feb 10 - 8 DTE)")
