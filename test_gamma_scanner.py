#!/usr/bin/env python3
"""Test the Expiry Gamma Scanner module"""

from src.analytics.expiry_gamma_scanner import (
    expiry_gamma_scanner, 
    analyze_expiry_day_option,
    get_theta_decay_schedule,
    MarketPhase
)

print('=' * 60)
print('EXPIRY GAMMA SCANNER TEST')
print('=' * 60)

# Test market phase
phase = expiry_gamma_scanner.get_market_phase()
print(f'\n1. Current market phase: {phase.value}')

# Test time remaining
time_left = expiry_gamma_scanner.get_time_remaining_minutes()
print(f'2. Time to close: {time_left:.0f} minutes')

# Test gamma analysis
print('\n3. Sample Gamma Analysis (NIFTY 25100 CE @ Rs.15, spot=25080):')
result = analyze_expiry_day_option(
    strike=25100,
    option_type='CE',
    premium=15,
    spot_price=25080,
    index='NIFTY'
)

analysis = result['analysis']
print(f'   Gamma Score: {analysis["gamma_score"]}/100')
print(f'   Is Opportunity: {analysis["is_opportunity"]}')
print(f'   Risk/Reward: {analysis["risk_reward"]}:1')
print(f'   Potential gain (50pt move): Rs.{analysis["potential_gain_50pt"]}')
print(f'   Theta loss (15min): Rs.{analysis["theta_loss_15min"]}')
print(f'   Moneyness: {analysis["moneyness_pct"]}%')
print(f'   Delta: {analysis["delta"]}')
print(f'   Gamma Multiplier: {analysis["gamma_multiplier"]}x')
print(f'   Risk Level: {analysis["risk_level"]}')
print(f'   Entry Reason: {analysis["entry_reason"]}')

# Test theta schedule
print('\n4. Theta Decay Schedule (Rs.50 premium, 2 hours remaining):')
schedule = get_theta_decay_schedule(50, 120)
print(f'   Total intervals: {len(schedule)}')
for item in schedule[:4]:
    print(f'   {item["time_to_close"]}: Rs.{item["expected_premium"]} (decay Rs.{item["theta_this_interval"]}, {item["decay_rate"]})')

print('\n' + '=' * 60)
print('TEST COMPLETE')
print('=' * 60)
