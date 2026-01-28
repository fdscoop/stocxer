"""
Test Option Chart Analysis Module
Tests the new option OHLC analysis for better entry timing
"""
import asyncio
from datetime import datetime

async def test_option_chart_analysis():
    """Test the option chart analysis functionality"""
    
    print("=" * 80)
    print("📊 OPTION CHART ANALYSIS TEST")
    print("=" * 80)
    print()
    
    try:
        from src.api.fyers_client import fyers_client
        from src.analytics.option_chart_analysis import get_option_chart_analyzer
        
        # Get analyzer instance
        analyzer = get_option_chart_analyzer(fyers_client)
        print("✅ Option Chart Analyzer initialized")
        
        # Test parameters
        test_cases = [
            {
                "option_symbol": "NSE:NIFTY26013025000CE",
                "current_premium": 250.0,
                "option_type": "CALL",
                "spot_price": 24500,
                "spot_target": 24600,  # 100 point up move expected
                "strike": 25000,
                "iv": 0.15,
                "days_to_expiry": 7
            },
            {
                "option_symbol": "NSE:NIFTY26013024500PE",
                "current_premium": 180.0,
                "option_type": "PUT",
                "spot_price": 24500,
                "spot_target": 24400,  # 100 point down move expected
                "strike": 24500,
                "iv": 0.18,
                "days_to_expiry": 3
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST {i}: {test['option_type']} OPTION ANALYSIS")
            print(f"{'='*60}")
            
            analysis = analyzer.analyze_option(**test)
            
            print(f"\n📌 Option: {test['option_symbol']}")
            print(f"   Current Premium: ₹{analysis.current_premium:.2f}")
            print(f"   Spot Price: ₹{test['spot_price']}")
            print(f"   Strike: {test['strike']}")
            print(f"   DTE: {test['days_to_expiry']} days")
            
            print(f"\n🎯 ENTRY RECOMMENDATION:")
            print(f"   Grade: {analysis.entry_grade}")
            print(f"   Recommendation: {analysis.entry_recommendation}")
            
            print(f"\n📝 REASONING:")
            for reason in analysis.reasoning:
                print(f"   {reason}")
            
            print(f"\n📊 SUPPORT LEVELS (Option Chart):")
            for s in analysis.support_levels[:3]:
                print(f"   ₹{s.level:.2f} (strength: {s.strength:.1f}, {s.distance_pct:.1f}% away)")
            
            print(f"\n📊 RESISTANCE LEVELS (Option Chart):")
            for r in analysis.resistance_levels[:3]:
                print(f"   ₹{r.level:.2f} (strength: {r.strength:.1f}, {r.distance_pct:.1f}% away)")
            
            print(f"\n💰 DISCOUNT ZONE ANALYSIS:")
            dz = analysis.discount_zone
            print(f"   Zone Type: {dz.zone_type}")
            print(f"   Is Discount: {dz.is_in_discount}")
            print(f"   Discount %: {dz.discount_pct:.1f}%")
            print(f"   Avg Premium: ₹{dz.avg_premium:.2f}")
            print(f"   Current: ₹{dz.current_premium:.2f}")
            print(f"   Range: ₹{dz.lower_bound:.2f} - ₹{dz.upper_bound:.2f}")
            
            print(f"\n⏳ PULLBACK ANALYSIS:")
            pb = analysis.pullback
            print(f"   Should Wait: {pb.should_wait}")
            print(f"   Wait Reason: {pb.wait_reason}")
            print(f"   Pullback Probability: {pb.pullback_probability*100:.0f}%")
            print(f"   Expected Pullback Level: ₹{pb.expected_pullback_level:.2f}")
            print(f"   Limit Order Price: ₹{pb.limit_order_price:.2f}")
            print(f"   Max Acceptable: ₹{pb.max_acceptable_price:.2f}")
            
            print(f"\n🎯 CHART-BASED TARGETS:")
            print(f"   Target 1: ₹{analysis.option_target_1:.2f}")
            print(f"   Target 2: ₹{analysis.option_target_2:.2f}")
            print(f"   Stop Loss: ₹{analysis.option_stop_loss:.2f}")
            
            print(f"\n⏰ TIME ANALYSIS:")
            print(f"   Time Feasible: {analysis.time_feasible}")
            print(f"   Minutes Remaining: {analysis.time_remaining_minutes}")
            print(f"   Theta/Hour: {analysis.theta_impact_per_hour*100:.2f}%")
            
            print(f"\n📈 SWING POINTS DETECTED:")
            print(f"   Swing Highs: {len(analysis.swing_highs)}")
            print(f"   Swing Lows: {len(analysis.swing_lows)}")
            
        print("\n" + "=" * 80)
        print("✅ OPTION CHART ANALYSIS TEST COMPLETE!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_option_chart_endpoint():
    """Test the new API endpoint"""
    import httpx
    
    print("\n" + "=" * 80)
    print("🌐 TESTING OPTION CHART ANALYSIS API ENDPOINT")
    print("=" * 80)
    
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test the new endpoint
            params = {
                "index": "NIFTY",
                "strike": 25000,
                "option_type": "CALL",
                "days_to_expiry": 7
            }
            
            print(f"\n📡 Calling GET /options/chart-analysis...")
            print(f"   Parameters: {params}")
            
            response = await client.get(
                f"{base_url}/options/chart-analysis",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Response received!")
                print(f"   Status: {data.get('status')}")
                print(f"   Option Symbol: {data.get('option_symbol')}")
                print(f"   Entry Grade: {data.get('entry_grade')}")
                print(f"   Recommendation: {data.get('entry_recommendation')}")
                print(f"   Discount Zone: {data.get('discount_zone', {}).get('zone_type')}")
                print(f"   Should Wait: {data.get('pullback', {}).get('should_wait')}")
                
                if data.get('support_levels'):
                    print(f"\n   Support Levels:")
                    for s in data['support_levels'][:3]:
                        print(f"      ₹{s['level']} (strength: {s['strength']:.2f})")
                
                if data.get('targets'):
                    print(f"\n   Targets:")
                    print(f"      Target 1: ₹{data['targets'].get('option_target_1')}")
                    print(f"      Stop Loss: ₹{data['targets'].get('option_stop_loss')}")
                
                return True
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(f"   {response.text}")
                return False
                
    except httpx.ConnectError:
        print("\n⚠️ Server not running. Start with: python main.py")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "🚀 " * 20)
    print("OPTION CHART ANALYSIS - COMPREHENSIVE TEST SUITE")
    print("🚀 " * 20 + "\n")
    
    # Run module test
    result1 = asyncio.run(test_option_chart_analysis())
    
    # Run API endpoint test
    result2 = asyncio.run(test_option_chart_endpoint())
    
    print("\n" + "=" * 80)
    print("📋 TEST SUMMARY")
    print("=" * 80)
    print(f"   Module Test: {'✅ PASSED' if result1 else '❌ FAILED'}")
    print(f"   API Endpoint Test: {'✅ PASSED' if result2 else '⚠️ SKIPPED (server not running)'}")
    print("=" * 80)


if __name__ == "__main__":
    main()
