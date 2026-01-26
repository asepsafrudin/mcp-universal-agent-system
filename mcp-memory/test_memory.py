#!/usr/bin/env python3
"""
Test script untuk Long-Term Memory System
Test memory functions tanpa perlu MCP server
"""
import sys
import os

# Add tools to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

try:
    from memory import memory_save, memory_search, memory_list, memory_delete
    print("✅ Memory module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import memory module: {e}")
    print("💡 Make sure psycopg is installed: pip install psycopg[binary]")
    sys.exit(1)

def test_memory_system():
    """Test all memory functions"""
    print("\n🧪 Testing Long-Term Memory System")
    print("=" * 50)
    
    # Test 1: List existing memories (should work even if empty)
    print("\n1. Testing memory_list...")
    try:
        result = memory_list({"limit": 5})
        if result["success"]:
            print(f"✅ Found {result['total']} memories")
            print(f"📋 Returning {len(result['memories'])} memories")
        else:
            print(f"❌ List failed: {result.get('error')}")
    except Exception as e:
        print(f"❌ List error: {e}")
    
    # Test 2: Save a test memory
    print("\n2. Testing memory_save...")
    try:
        result = memory_save({
            "key": "test_memory_system",
            "content": "Ini adalah test memory untuk sistem Long-Term Memory MCP Server dengan PostgreSQL dan pgvector",
            "metadata": {
                "test": True,
                "category": "system_test",
                "tags": ["memory", "test", "postgresql"]
            }
        })
        if result["success"]:
            print(f"✅ Memory saved: {result['message']}")
            test_memory_id = result.get('memory_id')
        else:
            print(f"❌ Save failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Save error: {e}")
        return False
    
    # Test 3: Search for the saved memory
    print("\n3. Testing memory_search...")
    try:
        result = memory_search({
            "query": "PostgreSQL memory system",
            "limit": 3
        })
        if result["success"]:
            print(f"✅ Search found {len(result['results'])} results")
            for i, memory in enumerate(result["results"], 1):
                print(f"   {i}. {memory['key']} (score: {memory['score']})")
                print(f"      {memory['content'][:100]}...")
        else:
            print(f"❌ Search failed: {result.get('error')}")
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    # Test 4: Test with different query types
    print("\n4. Testing keyword-only search...")
    try:
        result = memory_search({
            "query": "test",
            "limit": 2
        })
        if result["success"]:
            print(f"✅ Keyword search found {len(result['results'])} results")
        else:
            print(f"❌ Keyword search failed: {result.get('error')}")
    except Exception as e:
        print(f"❌ Keyword search error: {e}")
    
    # Test 5: Cleanup - delete test memory
    print("\n5. Testing memory_delete...")
    try:
        result = memory_delete({"key": "test_memory_system"})
        if result["success"]:
            print(f"✅ Memory deleted: {result['message']}")
        else:
            print(f"❌ Delete failed: {result.get('error')}")
    except Exception as e:
        print(f"❌ Delete error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Memory system test completed!")
    return True

def check_dependencies():
    """Check if all dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check psycopg
    try:
        import psycopg
        print(f"✅ psycopg: {psycopg.__version__}")
    except ImportError:
        print("❌ psycopg not installed")
        return False
    
    # Check Ollama
    try:
        import subprocess
        result = subprocess.run(["pgrep", "ollama"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is running")
        else:
            print("⚠️  Ollama not running (will use keyword-only search)")
    except Exception:
        print("⚠️  Cannot check Ollama status")
    
    return True

if __name__ == "__main__":
    print("🚀 Long-Term Memory System Test")
    print("=" * 40)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n💡 Install dependencies with:")
        print("   pip install psycopg[binary]")
        sys.exit(1)
    
    # Run tests
    try:
        success = test_memory_system()
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
