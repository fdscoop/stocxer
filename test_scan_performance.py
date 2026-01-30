#!/usr/bin/env python3
"""
End-to-End Performance Test
Authenticates with Supabase and tests NIFTY scanning with real user credentials
"""

import asyncio
import requests
import time
import json
from datetime import datetime


class PerformanceTester:
    """Test TradeWise performance with real authentication"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.user_info = None
    
    def login(self, email: str, password: str):
        """Login with Supabase credentials"""
        print("=" * 70)
        print("🔐 STEP 1: Authentication")
        print("=" * 70)
        
        url = f"{self.base_url}/api/auth/login"
        payload = {
            "email": email,
            "password": password
        }
        
        print(f"\n📧 Logging in as: {email}")
        print(f"🌐 API URL: {url}")
        
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.user_info = data.get("user")
                
                print(f"✅ Login successful!")
                print(f"   User ID: {self.user_info.get('id')}")
                print(f"   Email: {self.user_info.get('email')}")
                print(f"   Token: {self.access_token[:20]}...")
                
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_nifty_scan(self, quick_mode=False):
        """Test NIFTY scanning with performance tracking"""
        mode_label = "QUICK" if quick_mode else "FULL"
        
        print("\n" + "=" * 70)
        print(f"📊 STEP 2: {mode_label} NIFTY SCAN TEST")
        print("=" * 70)
        
        if not self.access_token:
            print("❌ Not authenticated. Please login first.")
            return None
        
        url = f"{self.base_url}/signals/NSE:NIFTY50-INDEX/actionable"
        params = {"quick_mode": str(quick_mode).lower()}
        headers = {"authorization": f"Bearer {self.access_token}"}
        
        print(f"\n🎯 Testing {mode_label} scan...")
        print(f"   URL: {url}")
        print(f"   Quick Mode: {quick_mode}")
        print(f"   Starting at: {datetime.now().strftime('%H:%M:%S')}")
        
        # Start timer
        start_time = time.time()
        
        try:
            response = requests.get(url, params=params, headers=headers)
            
            # End timer
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n✅ Scan completed successfully!")
                print(f"   ⏱️  Total time: {elapsed:.2f}s")
                
                # Extract key information
                signal_type = data.get("signal_type", "N/A")
                confidence = data.get("confidence", 0)
                
                print(f"\n📈 Signal Results:")
                print(f"   Signal: {signal_type}")
                print(f"   Confidence: {confidence}%")
                
                # Check for constituent analysis (only in full mode)
                probability_analysis = data.get("probability_analysis")
                if probability_analysis:
                    print(f"\n📊 Constituent Analysis:")
                    print(f"   Stocks scanned: {probability_analysis.get('stocks_scanned', 0)}")
                    print(f"   Direction: {probability_analysis.get('expected_direction', 'N/A')}")
                    print(f"   Bullish: {probability_analysis.get('bullish_stocks', 0)} ({probability_analysis.get('bullish_pct', 0)}%)")
                    print(f"   Bearish: {probability_analysis.get('bearish_stocks', 0)} ({probability_analysis.get('bearish_pct', 0)}%)")
                    
                    # Check for analysis time
                    analysis_time = probability_analysis.get('analysis_time')
                    if analysis_time:
                        print(f"   ⚡ Parallel analysis time: {analysis_time}s")
                
                # Check for recommended option
                option = data.get("recommended_option")
                if option:
                    print(f"\n💡 Recommended Option:")
                    print(f"   Type: {option.get('type', 'N/A')}")
                    print(f"   Strike: {option.get('strike', 'N/A')}")
                    print(f"   Entry: ₹{option.get('entry_price', 0):.2f}")
                
                return {
                    "success": True,
                    "time": elapsed,
                    "mode": mode_label,
                    "data": data
                }
                
            else:
                print(f"❌ Scan failed: {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                return {
                    "success": False,
                    "time": elapsed,
                    "error": response.text
                }
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Scan error: {e}")
            return {
                "success": False,
                "time": elapsed,
                "error": str(e)
            }
    
    def run_performance_comparison(self):
        """Run both quick and full scans to compare performance"""
        print("\n" + "=" * 70)
        print("🚀 PERFORMANCE COMPARISON TEST")
        print("=" * 70)
        
        results = {}
        
        # Test 1: Quick scan
        print("\n\n")
        quick_result = self.test_nifty_scan(quick_mode=True)
        results['quick'] = quick_result
        
        # Wait a bit between tests
        print("\n⏳ Waiting 3 seconds before next test...")
        time.sleep(3)
        
        # Test 2: Full scan (first run - cache miss expected)
        print("\n\n")
        full_result_1 = self.test_nifty_scan(quick_mode=False)
        results['full_first'] = full_result_1
        
        # Wait a bit
        print("\n⏳ Waiting 3 seconds before next test...")
        time.sleep(3)
        
        # Test 3: Full scan (second run - cache hit expected)
        print("\n\n")
        full_result_2 = self.test_nifty_scan(quick_mode=False)
        results['full_cached'] = full_result_2
        
        # Summary
        print("\n\n" + "=" * 70)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 70)
        
        if quick_result and quick_result.get('success'):
            print(f"\n🚀 Quick Scan: {quick_result['time']:.2f}s")
        
        if full_result_1 and full_result_1.get('success'):
            print(f"📊 Full Scan (1st run): {full_result_1['time']:.2f}s")
        
        if full_result_2 and full_result_2.get('success'):
            print(f"⚡ Full Scan (cached): {full_result_2['time']:.2f}s")
            
            # Calculate improvement
            if full_result_1 and full_result_1.get('success'):
                improvement = ((full_result_1['time'] - full_result_2['time']) / full_result_1['time']) * 100
                print(f"\n🎉 Cache speedup: {improvement:.1f}% faster on 2nd run")
        
        print("\n" + "=" * 70)
        
        # Compare against baseline
        if full_result_1 and full_result_1.get('success'):
            baseline = 180  # Original 3-minute baseline
            current = full_result_1['time']
            improvement = ((baseline - current) / baseline) * 100
            
            print(f"\n🎯 OPTIMIZATION RESULTS:")
            print(f"   Baseline (before): ~{baseline}s (3 minutes)")
            print(f"   Current (after): {current:.2f}s")
            print(f"   Improvement: {improvement:.1f}% faster!")
            
            if current < 60:
                print(f"\n✅ TARGET ACHIEVED: Under 60 seconds! 🎉")
            elif current < 90:
                print(f"\n✅ GOOD: Under 90 seconds!")
            else:
                print(f"\n⚠️  Still room for improvement")
        
        return results


def main():
    """Main test execution"""
    print("\n" + "=" * 70)
    print("🚀 TradeWise Performance Test - End-to-End")
    print("=" * 70)
    print(f"Timestamp: {datetime.now()}")
    
    # Configuration
    BASE_URL = "http://localhost:8000"
    EMAIL = "bineshch@gmail.com"
    PASSWORD = "Tra@2026"
    
    # Initialize tester
    tester = PerformanceTester(base_url=BASE_URL)
    
    # Step 1: Login
    if not tester.login(EMAIL, PASSWORD):
        print("\n❌ Authentication failed. Cannot proceed with tests.")
        print("\nℹ️  Make sure the server is running:")
        print("   cd /Users/bineshbalan/TradeWise")
        print("   uvicorn main:app --reload")
        return
    
    # Step 2: Run performance tests
    results = tester.run_performance_comparison()
    
    # Final message
    print("\n" + "=" * 70)
    print("✅ Test Complete!")
    print("=" * 70)
    print("\nℹ️  Check the logs above for cache hit/miss messages:")
    print("   - Look for '✅ Cache HIT' messages")
    print("   - Look for '✅ Parallel constituent analysis' timing")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
