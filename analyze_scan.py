#!/usr/bin/env python3
"""Analyze scan results"""
import json

with open('/tmp/nifty_scan.json', 'r') as f:
    data = json.load(f)

print('=== SCAN SUMMARY ===')
print(f'Status: {data.get("status")}')
print(f'Spot Price: {data.get("market_data", {}).get("spot_price")}')
print(f'ATM Strike: {data.get("market_data", {}).get("atm_strike")}')
print(f'VIX: {data.get("market_data", {}).get("vix")}')
print(f'Days to Expiry: {data.get("market_data", {}).get("days_to_expiry")}')
print(f'Data Source: {data.get("data_source", "NOT SET")}')
print(f'Total Options: {data.get("total_options")}')
print()

print('=== PROBABILITY ANALYSIS ===')
prob = data.get('probability_analysis', {})
print(f'Direction: {prob.get("expected_direction")}')
print(f'Stocks Scanned: {prob.get("stocks_scanned")}')
print(f'Confidence: {prob.get("confidence")}')
print(f'Prob Up: {prob.get("probability_up")}')
print(f'Prob Down: {prob.get("probability_down")}')
print(f'Recommended: {prob.get("recommended_option_type")}')
print()

print('=== TOP 5 OPTIONS ===')
options = data.get('options', [])[:5]
for i, opt in enumerate(options):
    print(f'{i+1}. {opt.get("type")} {opt.get("strike")}: LTP={opt.get("ltp")}, Score={opt.get("score"):.1f}, OI={opt.get("oi")}')
    entry = opt.get('entry_analysis', {})
    if entry.get('entry_grade'):
        print(f'   Entry Grade: {entry.get("entry_grade")}, Rec: {entry.get("entry_recommendation")}')
        print(f'   SL: {entry.get("option_stop_loss")}, T1: {entry.get("option_target_1")}, T2: {entry.get("option_target_2")}')
