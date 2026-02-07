#!/usr/bin/env python3
"""Test script to verify all ML modules can be imported and work together."""

import sys
sys.path.insert(0, '.')

print("=" * 60)
print("Testing Enhanced ML Module Imports")
print("=" * 60)

errors = []

# Test Speed Predictor
try:
    from src.ml.speed_predictor import SpeedPredictor, SpeedCategory
    print("✅ SpeedPredictor imported successfully")
except Exception as e:
    errors.append(f"SpeedPredictor: {e}")
    print(f"❌ SpeedPredictor failed: {e}")

# Test IV Predictor
try:
    from src.ml.iv_predictor import IVPredictor, IVDirection
    print("✅ IVPredictor imported successfully")
except Exception as e:
    errors.append(f"IVPredictor: {e}")
    print(f"❌ IVPredictor failed: {e}")

# Test Theta Scenario Planner
try:
    from src.ml.theta_scenario_planner import ThetaScenarioPlanner
    print("✅ ThetaScenarioPlanner imported successfully")
except Exception as e:
    errors.append(f"ThetaScenarioPlanner: {e}")
    print(f"❌ ThetaScenarioPlanner failed: {e}")

# Test XGBoost Direction Predictor
try:
    from src.ml.xgboost_direction import XGBoostDirectionPredictor
    print("✅ XGBoostDirectionPredictor imported successfully")
except Exception as e:
    errors.append(f"XGBoostDirectionPredictor: {e}")
    print(f"❌ XGBoostDirectionPredictor failed: {e}")

# Test Options P&L Simulator
try:
    from src.ml.options_simulator import OptionsPnLSimulator, TradeGrade
    print("✅ OptionsPnLSimulator imported successfully")
except Exception as e:
    errors.append(f"OptionsPnLSimulator: {e}")
    print(f"❌ OptionsPnLSimulator failed: {e}")

# Test Enhanced ML Service
try:
    from src.services.enhanced_ml_service import EnhancedMLService
    print("✅ EnhancedMLService imported successfully")
except Exception as e:
    errors.append(f"EnhancedMLService: {e}")
    print(f"❌ EnhancedMLService failed: {e}")

print("=" * 60)

if errors:
    print(f"❌ {len(errors)} import errors found:")
    for err in errors:
        print(f"   - {err}")
else:
    print("✅ All 6 ML modules imported successfully!")
    
    # Now test instantiation
    print("\n" + "=" * 60)
    print("Testing Module Instantiation")
    print("=" * 60)
    
    try:
        speed_predictor = SpeedPredictor()
        print("✅ SpeedPredictor instantiated")
    except Exception as e:
        print(f"❌ SpeedPredictor instantiation: {e}")
    
    try:
        iv_predictor = IVPredictor()
        print("✅ IVPredictor instantiated")
    except Exception as e:
        print(f"❌ IVPredictor instantiation: {e}")
    
    try:
        theta_planner = ThetaScenarioPlanner()
        print("✅ ThetaScenarioPlanner instantiated")
    except Exception as e:
        print(f"❌ ThetaScenarioPlanner instantiation: {e}")
    
    try:
        direction_predictor = XGBoostDirectionPredictor()
        print("✅ XGBoostDirectionPredictor instantiated")
    except Exception as e:
        print(f"❌ XGBoostDirectionPredictor instantiation: {e}")
    
    try:
        simulator = OptionsPnLSimulator()
        print("✅ OptionsPnLSimulator instantiated")
    except Exception as e:
        print(f"❌ OptionsPnLSimulator instantiation: {e}")
    
    try:
        ml_service = EnhancedMLService()
        print("✅ EnhancedMLService instantiated")
    except Exception as e:
        print(f"❌ EnhancedMLService instantiation: {e}")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
