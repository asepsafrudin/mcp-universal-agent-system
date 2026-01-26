#!/usr/bin/env python3
"""
Contoh Penggunaan MCP Tools dari Python
Demonstrasi bagaimana menggunakan MCP server dari code
"""

import sys
import os

# Add project root to path
sys.path.insert(0, '/home/aseps/MCP')
from shared.mcp_client import (
    mcp_list_dir,
    mcp_read_file,
    mcp_write_file,
    mcp_memory_save,
    mcp_memory_search,
    mcp_run_shell
)

def example_file_operations():
    """Contoh penggunaan file operations"""
    print("📁 File Operations Example")
    print("=" * 50)
    
    # List directory
    print("\n1. List directory:")
    result = mcp_list_dir("/workspace")
    if result["status"] == "success":
        print(f"   ✅ Found: {result['data']}")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    # Read file
    print("\n2. Read file:")
    result = mcp_read_file("/workspace/README.md")
    if result["status"] == "success":
        content = result['data']
        print(f"   ✅ Read {len(content)} characters")
        print(f"   Preview: {content[:100]}...")
    else:
        print(f"   ❌ Error: {result['error']}")

def example_memory_operations():
    """Contoh penggunaan memory operations"""
    print("\n\n💾 Memory Operations Example")
    print("=" * 50)
    
    # Save to memory
    print("\n1. Save to memory:")
    result = mcp_memory_save(
        key="project_context",
        content="MCP Server adalah universal tool server dengan long-term memory menggunakan PostgreSQL + pgvector"
    )
    if result["status"] == "success":
        print(f"   ✅ Saved to memory")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    # Search memory
    print("\n2. Search memory:")
    result = mcp_memory_search("MCP Server")
    if result["status"] == "success":
        results = result['data'].get('results', [])
        print(f"   ✅ Found {len(results)} results")
        for i, r in enumerate(results[:3], 1):
            print(f"   {i}. {r['key']}: {r['content'][:50]}...")
    else:
        print(f"   ❌ Error: {result['error']}")

def example_shell_operations():
    """Contoh penggunaan shell operations"""
    print("\n\n🔧 Shell Operations Example")
    print("=" * 50)
    
    # Run shell command
    print("\n1. Run shell command (ls):")
    result = mcp_run_shell("ls -la /workspace")
    if result["status"] == "success":
        print(f"   ✅ Command output:")
        print(f"   {result['data']}")
    else:
        print(f"   ❌ Error: {result['error']}")

def example_workflow():
    """Contoh workflow lengkap"""
    print("\n\n🎯 Complete Workflow Example")
    print("=" * 50)
    print("\nScenario: Analyze project and save findings to memory")
    
    # 1. List project structure
    print("\n1. Exploring project structure...")
    result = mcp_list_dir("/workspace")
    if result["status"] == "success":
        print(f"   ✅ Found directories and files")
    
    # 2. Read important file
    print("\n2. Reading README.md...")
    result = mcp_read_file("/workspace/README.md")
    if result["status"] == "success":
        content = result['data']
        print(f"   ✅ Read {len(content)} characters")
        
        # 3. Save analysis to memory
        print("\n3. Saving analysis to memory...")
        analysis = f"Project README contains {len(content)} characters. Key info: {content[:200]}"
        result = mcp_memory_save(
            key="project_readme_analysis",
            content=analysis
        )
        if result["status"] == "success":
            print(f"   ✅ Analysis saved to long-term memory")
    
    # 4. Verify saved memory
    print("\n4. Verifying saved memory...")
    result = mcp_memory_search("README analysis")
    if result["status"] == "success":
        results = result['data'].get('results', [])
        if results:
            print(f"   ✅ Found {len(results)} related memories")
            print(f"   Latest: {results[0]['key']}")

if __name__ == "__main__":
    print("🧪 MCP Tools Usage Examples")
    print("=" * 50)
    print("\nNote: Make sure MCP server is running!")
    print("Run: bash /home/aseps/MCP/mcp-quickstart.sh")
    print()
    
    try:
        # Run examples
        example_file_operations()
        example_memory_operations()
        example_shell_operations()
        example_workflow()
        
        print("\n\n✅ All examples completed!")
        print("\n💡 Tips:")
        print("   - Use memory_save untuk menyimpan context penting")
        print("   - Use memory_search untuk retrieve information dari session sebelumnya")
        print("   - Use hybrid search strategy untuk best results")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Pastikan PostgreSQL running: docker ps | grep mcp-pg")
        print("   2. Pastikan MCP server path benar")
        print("   3. Check logs untuk detail error")
