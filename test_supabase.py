"""
Test Supabase Connection and Authentication
"""
from config.settings import settings
from supabase import create_client

print("=" * 60)
print("SUPABASE CONNECTION TEST")
print("=" * 60)

print(f"\n1. Configuration:")
print(f"   URL: {settings.supabase_url}")
print(f"   Key Length: {len(settings.supabase_key)} characters")
print(f"   Key Prefix: {settings.supabase_key[:30]}...")
print(f"   Key Suffix: ...{settings.supabase_key[-20:]}")

print(f"\n2. Creating Supabase client...")
try:
    supabase = create_client(settings.supabase_url, settings.supabase_key)
    print("   ✅ Client created successfully")
except Exception as e:
    print(f"   ❌ Failed to create client: {e}")
    exit(1)

print(f"\n3. Testing database connection...")
try:
    result = supabase.table("users").select("count", count="exact").execute()
    print(f"   ✅ Database accessible")
    print(f"   Users count: {result.count if hasattr(result, 'count') else 'N/A'}")
except Exception as e:
    print(f"   ❌ Database query failed: {e}")

print(f"\n4. Testing authentication signup...")
try:
    # Try to sign up with a test email
    test_email = f"test_{id(supabase)}@example.com"
    response = supabase.auth.sign_up({
        "email": test_email,
        "password": "testpassword123"
    })
    
    if response.user:
        print(f"   ✅ Signup works! Test user created: {test_email}")
        print(f"   User ID: {response.user.id}")
    else:
        print(f"   ⚠️ Signup returned no user")
        
except Exception as e:
    error_msg = str(e)
    print(f"   ❌ Signup failed: {error_msg}")
    
    if "Invalid API key" in error_msg or "401" in error_msg:
        print("\n" + "=" * 60)
        print("ISSUE: Invalid API Key")
        print("=" * 60)
        print("\nTo fix this:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project: cxbcpmouqkajlxzmbomu")
        print("3. Go to Settings → API")
        print("4. Copy the 'anon' or 'public' key (NOT service_role key)")
        print("5. Update SUPABASE_KEY in your .env file")
        print("\n6. IMPORTANT: Enable Email Authentication:")
        print("   - Go to Authentication → Providers")
        print("   - Enable 'Email' provider")
        print("   - Click Save")
    elif "email" in error_msg.lower():
        print("\n   This might mean email authentication is disabled.")
        print("   Go to Authentication → Providers → Enable Email")

print("\n" + "=" * 60)
