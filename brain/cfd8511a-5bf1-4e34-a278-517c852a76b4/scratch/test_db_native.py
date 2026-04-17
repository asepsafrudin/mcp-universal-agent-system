import asyncio
import json
import sys
from datetime import date, datetime
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from execution import registry
from core.bootstrap import initialize_all_components

async def main():
    # Initialize components (DB, Registry, etc)
    await initialize_all_components()
    
    # Test query for SKL-001
    print("\n--- Investigating SKL-001 ---")
    query_skl = "SELECT * FROM surat_keluar_puu WHERE nomor_nd = 'SKL-001'"
    res_skl = await registry.execute("query_db", {"query": query_skl, "namespace": "investigation"})
    print(json.dumps(res_skl, indent=2, default=str))
    
    # Get the REAL absolute latest data
    print("\n--- Getting Real Latest Data ---")
    query_latest = "SELECT * FROM surat_keluar_puu ORDER BY created_at DESC LIMIT 1"
    res_latest = await registry.execute("query_db", {"query": query_latest, "namespace": "investigation"})
    print(json.dumps(res_latest, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
