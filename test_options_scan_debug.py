#!/usr/bin/env python3
"""
Comprehensive Options Scanner Debugging Script

This script tests the options scanner end-to-end with detailed logging
to help understand exactly what happens during a scan:

1. Authentication check
2. Fyers token validation  
3. Index constituent stock analysis (probability)
4. Option chain data fetching
5. Options filtering and scoring
6. Signal generation
7. Final result formatting

Usage:
    python test_options_scan_debug.py

Author: TradeWise Development Team
Date: Jan 28, 2026
"""

import requests
import json
import sys
from datetime import datetime
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "bineshch@gmail.com"
TEST_USER_PASSWORD = "Tra@2026"

# ANSI color codes for better output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(message: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{message.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_step(step_num: int, message: str):
    """Print a formatted step"""
    print(f"{Colors.BOLD}{Colors.BLUE}[Step {step_num}]{Colors.END} {message}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.MAGENTA}ℹ️  {message}{Colors.END}")

def print_json(data: dict, indent: int = 2):
    """Print formatted JSON"""
    print(json.dumps(data, indent=indent))

def test_backend_health() -> bool:
    """Test if backend is running"""
    print_step(1, "Checking backend health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend is online: {data.get('service')} v{data.get('version')}")
            print_info(f"News service: {data.get('news_service', {}).get('type', 'N/A')}")
            return True
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend. Is it running on port 8000?")
        print_info("Start with: python main.py")
        return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def get_auth_token() -> Optional[str]:
    """Get authentication token"""
    print_step(2, "Authenticating user...")
    
    # Try to register first (in case user doesn't exist)
    try:
        register_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "full_name": "Test User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if response.status_code == 200:
            print_info("User registered successfully")
    except:
        pass  # User might already exist
    
    # Now login
    try:
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            if token:
                print_success(f"Authenticated as: {TEST_USER_EMAIL}")
                print_info(f"Token: {token[:20]}...")
                return token
            else:
                print_error("No access token in response")
                return None
        else:
            print_error(f"Login failed: {response.status_code}")
            print_error(response.text)
            return None
            
    except Exception as e:
        print_error(f"Authentication failed: {e}")
        return None

def check_fyers_token(token: str) -> dict:
    """Check Fyers token status"""
    print_step(3, "Checking Fyers broker authentication...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/fyers-token", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('has_token'):
                print_success("Fyers token exists")
                if data.get('is_valid'):
                    print_success(f"Token is valid (expires: {data.get('expires_at')})")
                    return {"status": "valid", "data_source": "live"}
                else:
                    print_warning("Fyers token is expired")
                    return {"status": "expired", "data_source": "demo"}
            else:
                print_warning("No Fyers token found - will use demo data")
                return {"status": "missing", "data_source": "demo"}
        else:
            print_warning("Could not check Fyers status - using demo data")
            return {"status": "unknown", "data_source": "demo"}
            
    except Exception as e:
        print_warning(f"Fyers check failed: {e} - will use demo data")
        return {"status": "error", "data_source": "demo"}

def scan_options(token: str, index: str = "NIFTY", expiry: str = "weekly") -> dict:
    """Perform options scan with detailed logging"""
    print_step(4, f"Scanning {index} options (expiry: {expiry})...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "index": index,
            "expiry": expiry,
            "min_volume": 1000,
            "min_oi": 10000,
            "strategy": "all",
            "include_probability": True
        }
        
        print_info(f"Request URL: {BASE_URL}/options/scan")
        print_info(f"Parameters: {json.dumps(params, indent=2)}")
        
        # Make the request
        print(f"\n{Colors.YELLOW}⏳ Scanning (this may take 30-60 seconds for live data)...{Colors.END}")
        
        response = requests.get(
            f"{BASE_URL}/options/scan",
            headers=headers,
            params=params,
            timeout=120  # 2 minutes timeout
        )
        
        print(f"\n{Colors.BOLD}Response Status: {response.status_code}{Colors.END}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Scan completed successfully!")
            return data
            
        elif response.status_code == 401:
            error_data = response.json()
            print_error(f"Authentication failed: {error_data.get('detail')}")
            
            # Check if it's a Fyers auth issue
            if isinstance(error_data.get('detail'), dict):
                detail = error_data['detail']
                if detail.get('error') == 'fyers_auth_required':
                    print_warning("Fyers authentication required")
                    print_info(f"Auth URL: {detail.get('auth_url')}")
            
            return None
            
        elif response.status_code == 402:
            error_data = response.json()
            print_error(f"Insufficient credits: {error_data.get('detail')}")
            return None
            
        else:
            print_error(f"Scan failed with status {response.status_code}")
            print_error(response.text)
            return None
            
    except requests.exceptions.Timeout:
        print_error("Request timed out (>120s)")
        print_info("This usually means the backend is processing but taking too long")
        print_info("Check server.log for detailed error messages")
        return None
        
    except Exception as e:
        print_error(f"Scan request failed: {e}")
        return None

def analyze_scan_results(data: dict):
    """Analyze and display scan results"""
    print_step(5, "Analyzing scan results...")
    
    if not data:
        print_error("No data to analyze")
        return
    
    # Basic info
    print(f"\n{Colors.BOLD}📊 Scan Summary{Colors.END}")
    print(f"  Status: {data.get('status')}")
    print(f"  Index: {data.get('index')}")
    print(f"  Expiry: {data.get('expiry')}")
    print(f"  Scan Time: {data.get('scan_time')}")
    print(f"  Data Source: {data.get('data_source', 'N/A')}")
    print(f"  User: {data.get('user_email', 'N/A')}")
    
    # Market data
    if 'market_data' in data:
        market = data['market_data']
        print(f"\n{Colors.BOLD}📈 Market Data{Colors.END}")
        print(f"  Spot Price: {market.get('spot_price')}")
        print(f"  ATM Strike: {market.get('atm_strike')}")
        print(f"  VIX: {market.get('vix', 'N/A')}")
        print(f"  Expiry Date: {market.get('expiry_date')}")
        print(f"  Days to Expiry: {market.get('days_to_expiry')}")
    
    # Probability analysis
    if 'probability_analysis' in data and data['probability_analysis']:
        prob = data['probability_analysis']
        print(f"\n{Colors.BOLD}🎯 Probability Analysis (Constituent Stocks){Colors.END}")
        print(f"  Stocks Scanned: {prob.get('stocks_scanned', 0)}/{prob.get('total_stocks', 0)}")
        print(f"  Expected Direction: {prob.get('expected_direction')}")
        print(f"  Expected Move: {prob.get('expected_move_pct')}%")
        print(f"  Confidence: {prob.get('confidence') * 100:.1f}%")
        print(f"  Probability Up: {prob.get('probability_up') * 100:.1f}%")
        print(f"  Probability Down: {prob.get('probability_down') * 100:.1f}%")
        print(f"  Bullish Stocks: {prob.get('bullish_stocks')} ({prob.get('bullish_pct')}%)")
        print(f"  Bearish Stocks: {prob.get('bearish_stocks')} ({prob.get('bearish_pct')}%)")
        print(f"  Recommended Option Type: {prob.get('recommended_option_type')}")
        print(f"  Market Regime: {prob.get('market_regime')}")
        
        # Top stocks
        if prob.get('top_bullish_stocks'):
            print(f"\n  {Colors.GREEN}Top Bullish Stocks:{Colors.END}")
            for stock in prob['top_bullish_stocks'][:3]:
                print(f"    • {stock['symbol']}: {stock['probability']*100:.1f}% prob, {stock['expected_move']}% move")
        
        if prob.get('top_bearish_stocks'):
            print(f"\n  {Colors.RED}Top Bearish Stocks:{Colors.END}")
            for stock in prob['top_bearish_stocks'][:3]:
                print(f"    • {stock['symbol']}: {stock['probability']*100:.1f}% prob, {stock['expected_move']}% move")
    
    # Sentiment analysis
    if 'sentiment_analysis' in data and data['sentiment_analysis']:
        sent = data['sentiment_analysis']
        print(f"\n{Colors.BOLD}📰 News Sentiment{Colors.END}")
        print(f"  Sentiment: {sent.get('sentiment')}")
        print(f"  Score: {sent.get('sentiment_score')}")
        print(f"  News Count: {sent.get('news_count', 0)}")
    
    # Options results
    options_count = data.get('total_options', 0)
    print(f"\n{Colors.BOLD}🎲 Options Found{Colors.END}")
    print(f"  Total Options: {options_count}")
    
    if 'options' in data and data['options']:
        print(f"\n{Colors.BOLD}Top 5 Options:{Colors.END}")
        for i, opt in enumerate(data['options'][:5], 1):
            print(f"\n  #{i} {opt['type']} @ {opt['strike']}")
            print(f"      LTP: ₹{opt.get('ltp', 0):.2f}")
            print(f"      Volume: {opt.get('volume', 0):,}")
            print(f"      OI: {opt.get('oi', 0):,}")
            print(f"      IV: {opt.get('iv', 0):.1f}%")
            print(f"      Delta: {opt.get('delta', 0):.3f}")
            print(f"      Score: {opt.get('score', 0):.1f}/100")
            if opt.get('probability_boost'):
                print(f"      ⭐ Probability Boosted")
            if opt.get('sentiment_boost'):
                print(f"      📰 Sentiment Boosted")
            if opt.get('recommendation'):
                print(f"      💡 {opt['recommendation']}")

def main():
    """Main test execution"""
    print_header("TradeWise Options Scanner - Comprehensive Debug Test")
    print(f"{Colors.BOLD}Date:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Colors.BOLD}Backend:{Colors.END} {BASE_URL}\n")
    
    # Step 1: Check backend
    if not test_backend_health():
        print_error("\n❌ Backend is not running. Please start it first:")
        print_info("   cd /Users/bineshbalan/TradeWise")
        print_info("   ./start_dev.sh")
        sys.exit(1)
    
    # Step 2: Authenticate
    token = get_auth_token()
    if not token:
        print_error("\n❌ Authentication failed")
        sys.exit(1)
    
    # Step 3: Check Fyers token
    fyers_status = check_fyers_token(token)
    print_info(f"Data source will be: {fyers_status['data_source']}")
    
    # Step 4: Scan options
    print_header("Starting Options Scan")
    scan_results = scan_options(token, index="NIFTY", expiry="weekly")
    
    if not scan_results:
        print_error("\n❌ Scan failed")
        print_info("\nCheck server.log for detailed error messages:")
        print_info("   tail -f server.log")
        sys.exit(1)
    
    # Step 5: Analyze results
    analyze_scan_results(scan_results)
    
    # Success summary
    print_header("Test Completed Successfully")
    print_success("Options scanner is working correctly!")
    print_info(f"Found {scan_results.get('total_options', 0)} options matching criteria")
    print_info(f"Data source: {scan_results.get('data_source', 'N/A')}")
    
    if scan_results.get('data_source') == 'demo':
        print_warning("\n⚠️  Using demo data. To use live data:")
        print_info("   1. Open frontend: http://localhost:3000")
        print_info("   2. Click 'Connect Broker'")
        print_info("   3. Complete Fyers authentication")
    
    print("\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\n\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
