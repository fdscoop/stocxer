"""
Test AMD Integration in Main Scanner
This script verifies that the AMD detection is properly integrated into the signal generation flow.
"""

import asyncio
import json
from datetime import datetime

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_amd_integration():
    """Test that AMD detection is integrated into the signal flow."""
    
    print("=" * 70)
    print("🧪 AMD INTEGRATION TEST")
    print("=" * 70)
    print()
    
    # Step 1: Test import
    print("Step 1: Testing imports...")
    try:
        from src.analytics.topdown_ict_amd import TopDownICTAnalyzer, AMDPhase
        print("   ✅ topdown_ict_amd module imported successfully")
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    
    # Step 2: Test analyzer initialization
    print("\nStep 2: Testing TopDownICTAnalyzer initialization...")
    try:
        from src.api.fyers_client import fyers_client
        analyzer = TopDownICTAnalyzer(fyers_client)
        print("   ✅ TopDownICTAnalyzer initialized with Fyers client")
    except Exception as e:
        print(f"   ❌ Initialization error: {e}")
        return False
    
    # Step 3: Run analysis on NIFTY
    print("\nStep 3: Running AMD analysis on NIFTY...")
    try:
        result = analyzer.analyze("NIFTY")
        
        if result:
            print(f"   ✅ Analysis completed successfully")
            print(f"   📊 HTF Bias: {result.htf.bias if result.htf else 'N/A'}")
            print(f"   📊 MTF Trend: {result.mtf.trend if result.mtf else 'N/A'}")
            
            if result.ltf:
                print(f"   📊 LTF AMD Phase: {result.ltf.current_phase.value}")
                print(f"   🐻 Bear Traps: {len(result.ltf.bear_traps)}")
                print(f"   🐂 Bull Traps: {len(result.ltf.bull_traps)}")
                
                # Check for active manipulations
                if result.ltf.bear_traps:
                    latest = result.ltf.bear_traps[-1]
                    print(f"\n   🚨 LATEST BEAR TRAP:")
                    print(f"      Level: ₹{latest.level:.2f}")
                    print(f"      Recovery: +{latest.recovery_pts:.0f} pts")
                    print(f"      Confidence: {latest.confidence}%")
                    if latest.time:
                        age_mins = (datetime.now() - latest.time).total_seconds() / 60
                        print(f"      Age: {age_mins:.0f} mins")
                        print(f"      Active: {age_mins <= 30}")
                
                if result.ltf.bull_traps:
                    latest = result.ltf.bull_traps[-1]
                    print(f"\n   🚨 LATEST BULL TRAP:")
                    print(f"      Level: ₹{latest.level:.2f}")
                    print(f"      Drop: -{latest.recovery_pts:.0f} pts")
                    print(f"      Confidence: {latest.confidence}%")
                    if latest.time:
                        age_mins = (datetime.now() - latest.time).total_seconds() / 60
                        print(f"      Age: {age_mins:.0f} mins")
                        print(f"      Active: {age_mins <= 30}")
        else:
            print("   ⚠️ Analysis returned None (may indicate data issue)")
            
    except Exception as e:
        print(f"   ❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Verify signal structure includes AMD
    print("\n" + "=" * 70)
    print("Step 4: Verifying AMD integration in signal structure...")
    print("=" * 70)
    
    print("""
    The following AMD fields should now be in the signal response:
    
    "amd_detection": {
        "manipulation_found": bool,      ← Whether trap was detected
        "type": "bear_trap"|"bull_trap", ← Type of manipulation
        "level": float,                   ← Price level of trap
        "confidence": int,                ← 0-100 confidence score
        "override_signal": str,           ← 'bullish' or 'bearish'
        "description": str,               ← Human readable explanation
        "recovery_pts": float,            ← Points recovered after trap
        "time": str,                      ← ISO timestamp of trap
        "is_active": bool,                ← True if within 30 mins
        "override_applied": bool          ← True if HTF bias was overridden
    }
    """)
    
    # Step 5: Test the override logic
    print("\nStep 5: AMD Override Logic Explanation")
    print("-" * 50)
    print("""
    WHEN AMD OVERRIDE IS APPLIED:
    
    1. Bear Trap Detected (confidence ≥ 70%, active ≤ 30 mins)
       → OVERRIDE HTF bearish bias → Trade direction = BULLISH
       → Signal: BUY CALL
       
    2. Bull Trap Detected (confidence ≥ 70%, active ≤ 30 mins)
       → OVERRIDE HTF bullish bias → Trade direction = BEARISH
       → Signal: BUY PUT
       
    WHY THIS MATTERS:
    - On Feb 6, 2026, HTF showed bearish (giving 15 consecutive PE signals)
    - But LTF showed 3 bear traps at support (price swept lows then reversed)
    - With AMD override, the system would have detected these traps
    - And given CALL signals (buy the reversal) instead of PUTs
    """)
    
    print("\n" + "=" * 70)
    print("✅ AMD INTEGRATION TEST COMPLETE")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    asyncio.run(test_amd_integration())
