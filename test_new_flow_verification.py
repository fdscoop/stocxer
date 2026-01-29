"""
Quick test to see FULL signal response and verify NEW flow fields
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.services.auth_service import AuthService
from src.models.auth_models import UserLogin
from src.api.fyers_client import FyersClient
import httpx


async def main():
    print("🔍 Testing NEW Flow - Checking Response Fields")
    print("=" * 80)
    
    # Login
    auth_service = AuthService()
    login_data = UserLogin(email="bineshch@gmail.com", password="Tra@2026")
    token_response = await auth_service.login_user(login_data)
    print(f"✅ Logged in as: {login_data.email}\n")
    
    # Get Fyers token
    fyers_token_response = await auth_service.get_fyers_token(token_response.user.id)
    fyers_token = fyers_token_response.access_token
    print(f"✅ Fyers token retrieved\n")
    
    # Call signal endpoint
    print("📡 Calling: GET /signals/NSE:NIFTY50-INDEX/actionable")
    print("-" * 80)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://localhost:8000/signals/NSE:NIFTY50-INDEX/actionable",
                headers={"Authorization": f"Bearer {fyers_token}"}
            )
            
            if response.status_code == 200:
                signal = response.json()
                
                print("\n✅ SIGNAL GENERATED!\n")
                print("=" * 80)
                print("📊 FULL RESPONSE (JSON):")
                print("=" * 80)
                print(json.dumps(signal, indent=2))
                print("=" * 80)
                
                # Check for NEW flow fields
                print("\n🔍 CHECKING FOR NEW FLOW FIELDS:")
                print("-" * 80)
                
                has_htf = "htf_analysis" in signal
                has_ltf = "ltf_entry_model" in signal
                has_stack = "confirmation_stack" in signal
                has_breakdown = "confidence_breakdown" in signal
                
                print(f"✅ htf_analysis: {'FOUND' if has_htf else '❌ MISSING'}")
                print(f"✅ ltf_entry_model: {'FOUND' if has_ltf else '❌ MISSING'}")
                print(f"✅ confirmation_stack: {'FOUND' if has_stack else '❌ MISSING'}")
                print(f"✅ confidence_breakdown: {'FOUND' if has_breakdown else '❌ MISSING'}")
                
                print("\n" + "=" * 80)
                if has_htf and has_ltf and has_stack and has_breakdown:
                    print("🎉 NEW FLOW IS ACTIVE! All new fields present!")
                else:
                    print("⚠️  OLD FLOW STILL ACTIVE - New fields missing")
                print("=" * 80)
                
            else:
                print(f"❌ API Error: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
