
import json

# Mock results from CorrespondenceDashboard.search_letters
dashboard_results = [
    {
        "direktorat": "PUU", 
        "tipe": "masuk",
        "nomor_nd": "ND-123", 
        "dari": "Biro Umum", 
        "hal": "Permohonan Data",
        "posisi": "PUU", 
        "disposisi": "Proses"
    }
]

# The logic in ToolExecutor._exec_search_letters
def simulate_tool_executor(results):
    items = []
    headers_ref = []
    
    for r in results[:10]:
        # Cek apakah r memiliki struktur lama (Google Sheets style)
        if isinstance(r, dict) and "row_data" in r and "header" in r:
            row_data = r["row_data"]
            header = r["header"]
            headers_ref = header
            
            item_dict = {
                "direktorat": r.get("direktorat", "Unknown"),
                "match_on_hal": r.get("match_on_hal", False)
            }
            for i, h in enumerate(header):
                if i < len(row_data):
                    col_name = str(h).strip() or f"Column_{i}"
                    item_dict[col_name] = row_data[i]
            items.append(item_dict)
        else:
            # Fallback jika struktur baru (PostgreSQL style)
            items.append({"data": str(r)})
    
    return items

print("Testing ToolExecutor logic with Dashboard results...")
processed_items = simulate_tool_executor(dashboard_results)
print("--- PROCESSED ITEMS ---")
print(json.dumps(processed_items, indent=2))

if "data" in processed_items[0] and "nomor_nd" not in processed_items[0]:
    print("\n✅ VERIFIKASI BERHASIL: Temuan Inkonsistensi Valid! ToolExecutor tidak mengenali struktur dict baru.")
else:
    print("\n❌ VERIFIKASI GAGAL: ToolExecutor berhasil memetakan field secara otomatis.")
