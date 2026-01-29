"""
Check today's scan data from production database
"""
import os
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Connect to Supabase with service key (has admin access)
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("❌ Missing SUPABASE credentials in .env file")
    print("Need SUPABASE_URL and SUPABASE_SERVICE_KEY")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

# User email
user_email = "bineshch@gmail.com"

print("=" * 80)
print("TODAY'S SCAN DATA FOR:", user_email)
print("=" * 80)

try:
    # Get user ID directly from usage_logs by email search
    # First, let's just query all usage logs for this email
    print(f"Searching for scans by email: {user_email}")
    
    # Get today's date range
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    three_days_ago = today - timedelta(days=3)
    
    print(f"Date range: {three_days_ago} to {tomorrow}")
    print()
    
    # Query usage_logs directly
    response = supabase.table("usage_logs")\
        .select("*")\
        .eq("scan_type", "option_scan")\
        .gte("created_at", three_days_ago.isoformat())\
        .order("created_at", desc=True)\
        .limit(50)\
        .execute()
    
    if not response.data:
        print("❌ No scans found in database")
        exit(1)
    
    print(f"✅ Found {len(response.data)} scan(s)\n")
    
    for i, scan in enumerate(response.data, 1):
        print(f"\n{'='*80}")
        print(f"SCAN #{i}")
        print(f"{'='*80}")
        print(f"Time: {scan.get('created_at')}")
        print(f"Scan Type: {scan.get('scan_type')}")
        
        metadata = scan.get('metadata', {})
        print(f"\nMetadata:")
        print(f"  Index: {metadata.get('index', 'N/A')}")
        print(f"  Expiry: {metadata.get('expiry', 'N/A')}")
        print(f"  Min Volume: {metadata.get('min_volume', 'N/A')}")
        print(f"  Min OI: {metadata.get('min_oi', 'N/A')}")
        
        # Check for probability analysis
        prob_analysis = metadata.get('probability_analysis', {})
        if prob_analysis:
            print(f"\nProbability Analysis:")
            print(f"  Expected Direction: {prob_analysis.get('expected_direction', 'N/A')}")
            print(f"  Recommended Option: {prob_analysis.get('recommended_option_type', 'N/A')}")
            print(f"  Probability Up: {prob_analysis.get('probability_up', 'N/A')}")
            print(f"  Probability Down: {prob_analysis.get('probability_down', 'N/A')}")
            print(f"  Bullish Stocks: {prob_analysis.get('bullish_stocks', 'N/A')}")
            print(f"  Bearish Stocks: {prob_analysis.get('bearish_stocks', 'N/A')}")
            print(f"  Stocks Scanned: {prob_analysis.get('stocks_scanned', 'N/A')}")
        
        # Get scan results
        scan_results = metadata.get('scan_results', {})
        if scan_results:
            options = scan_results.get('options', [])
            print(f"\nTop Options Found: {len(options)}")
            
            if options:
                print(f"\nTop 3 Recommendations:")
                for j, opt in enumerate(options[:3], 1):
                    print(f"\n  {j}. {opt.get('strike')} {opt.get('type')}")
                    print(f"     LTP: ₹{opt.get('ltp', 'N/A')}")
                    print(f"     Score: {opt.get('score', 'N/A')}")
                    print(f"     Recommendation: {opt.get('recommendation', 'N/A')}")
                    print(f"     IV: {opt.get('iv', 'N/A')}%")
        
        print(f"\n{'-'*80}")
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
