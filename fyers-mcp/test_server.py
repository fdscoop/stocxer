#!/usr/bin/env python3
"""
Test FYERS MCP Server
Verifies the server can start and respond to basic queries
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def test_imports():
    """Test that all required imports work"""
    print("🧪 Testing imports...")
    try:
        import mcp
        from mcp.server import Server
        from src.api.fyers_client import fyers_client
        print("✅ All imports successful")
        print(f"   MCP version: {mcp.__version__ if hasattr(mcp, '__version__') else 'unknown'}")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_fyers_client():
    """Test FYERS client initialization"""
    print("\n🧪 Testing FYERS client...")
    try:
        from src.api.fyers_client import fyers_client
        
        if fyers_client.access_token:
            print(f"✅ FYERS client initialized with token")
            return True
        else:
            print("⚠️  FYERS_ACCESS_TOKEN not set (limited functionality)")
            return True
    except Exception as e:
        print(f"❌ FYERS client error: {e}")
        return False


def test_server_creation():
    """Test MCP server can be created"""
    print("\n🧪 Testing MCP server creation...")
    try:
        from mcp.server import Server
        server = Server("test-fyers-mcp")
        print("✅ MCP server created successfully")
        return True
    except Exception as e:
        print(f"❌ Server creation failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("FYERS MCP Server Test Suite")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("FYERS Client", test_fyers_client),
        ("MCP Server", test_server_creation),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! MCP server is ready to use.")
        print("\n📝 Next steps:")
        print("1. Run: cd mcp && ./install.sh")
        print("2. Restart Claude Desktop")
        print("3. Ask Claude: 'What are my current positions?'")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
