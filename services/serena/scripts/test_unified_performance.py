import json
import time
from pprint import pprint

from serena.agent import SerenaAgent
from serena.config.serena_config import SerenaConfig
from serena.tools import FindSymbolTool, FindReferencingSymbolsTool

def main():
    print("🚀 Menginisialisasi Uji Performa Serena Agent pada mcp-unified...")
    start_time = time.time()
    
    # Path to the unified MCP project
    project_path = "/home/aseps/MCP/mcp-unified"
    
    # Setup configuration
    serena_config = SerenaConfig.from_config_file()
    serena_config.web_dashboard = False
    
    # Create the agent
    agent = SerenaAgent(project=project_path, serena_config=serena_config)
    
    print(f"⏱️ Waktu Overhead Inisialisasi awal: {time.time() - start_time:.2f} detik.")
    
    # 1. Test FindSymbolTool
    find_symbol_tool = agent.get_tool(FindSymbolTool)
    print("\n[Uji Coba 1] Mencari definisi fungsi 'initialize_components' menggunakan semantik...")
    t1 = time.time()
    try:
        # Applying tool
        res1 = agent.execute_task(lambda: find_symbol_tool.apply("initialize_components"))
        print(f"✅ Sukses dalam {time.time() - t1:.4f} detik!")
        
        # res1 might be a string or JSON depending on the tool's implementation
        try:
            summary = json.loads(res1)
            print(f"➡️ Total Simbol Ditemukan: {len(summary) if isinstance(summary, list) else 1}")
            previewStr = str(summary)[:200]
        except:
            previewStr = str(res1)[:200]
        print(f"   Cuplikan Output: {previewStr}...")
    except Exception as e:
        print(f"❌ Gagal: {e}")
        
    # 2. Test FindReferencingSymbolsTool
    find_refs_tool = agent.get_tool(FindReferencingSymbolsTool)
    print("\n[Uji Coba 2] Mencari pemanggil dari fungsi 'initialize_db'...")
    t2 = time.time()
    try:
        # Applying tool
        res2 = agent.execute_task(lambda: find_refs_tool.apply("initialize_db", filepath="mcp_server.py"))
        print(f"✅ Sukses dalam {time.time() - t2:.4f} detik!")
        try:
            summary2 = json.loads(res2)
            print(f"➡️ Total Referensi Ditemukan: {len(summary2) if isinstance(summary2, list) else 1}")
            previewStr2 = str(summary2)[:200]
        except:
            previewStr2 = str(res2)[:200]
        print(f"   Cuplikan Output: {previewStr2}...")
    except Exception as e:
        print(f"❌ Gagal: {e}")

if __name__ == "__main__":
    main()
