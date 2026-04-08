#!/usr/bin/env python3
"""
Arsip PUU → GSheets AUTO APPEND
Using gspread + Service Account dengan Mapping Engine Konfigurasi

Kolom Spreadsheet (berdasarkan column_mapping.json):
A: Boks (doc_id)
B: (empty)
C: KODE KLASIFIKASI (konstan: 000.8)
D: NOMOR SURAT
E: URAIAN (doc_type - satker)
F: KURUN WAKTU (YYYY-MM)
G-I: (empty)
J: Tingkat Perkembangan (konstan: baru)
K: Keterangan (empty)
L: Klasifikasi (extracted dari satker)
M: Hak Akses (empty)
N: Akses Publik? (konstan: no)
O: UNIT PENGOLAH (satker truncated 30 char)
"""
import json
import sys
from pathlib import Path

# Tambahkan path ke mapping_engine
sys.path.insert(0, str(Path(__file__).parent))

from mapping_engine import MappingEngine, ArsipDataLoader

# Konfigurasi Spreadsheet
SPREADSHEET_ID = "18H6gIv61XTdUsA7zh0XoQqmRWQxlfuNvbRMq5n8AwRM"
SA_JSON = "/home/aseps/MCP/config/credentials/google/mcp-gmail-482015-682b788ee191.json"


def load_arsip_data_with_mapping() -> list:
    """
    Load data arsip menggunakan Mapping Engine.
    
    Returns:
        List of rows ready untuk di-append ke GSheets
    """
    engine = MappingEngine()
    loader = ArsipDataLoader()
    
    print(f"📊 Loading {loader.count()} structured files...")
    
    all_data = loader.load_all()
    if not all_data:
        print("⚠️ Tidak ada data arsip ditemukan!")
        return []
    
    rows = []
    for data in all_data:
        # Validasi
        errors = engine.validate_data(data)
        if errors:
            print(f"⚠️ Validation errors in {data.get('doc_id', 'unknown')}: {errors}")
            # Continue anyway untuk non-critical errors
        
        # Transform row
        row = engine.transform_row(data)
        rows.append(row)
        
        # Debug output (optional)
        doc_id = data.get("doc_id", "unknown")
        print(f"  ✓ Mapped: {doc_id}")
    
    return rows


def load_arsip_data_legacy() -> list:
    """
    Legacy method untuk backward compatibility.
    Menggunakan parsing manual tanpa mapping engine.
    """
    rows = []
    extracted_dir = Path("arsip-extracted")
    
    for json_file in extracted_dir.glob("*_structured.json"):
        data = json.loads(json_file.read_text())
        structured = data['content']
        
        row = [
            structured['doc_id'],  # A: Boks
            "",  # B: empty
            "000.8",  # C: KODE KLASIFIKASI  
            structured['nomor_surat'],  # D: NOMOR SURAT
            f"{structured['doc_type']} - {structured['satker'][:50]}",  # E: URAIAN
            structured['extraction_date'][:7],  # F: KURUN WAKTU
            "", "", "",  # G,H,I empty
            "baru",  # J: Tingkat Perkembangan
            "",  # K: Keterangan
            "",  # L: Klasifikasi (seharusnya extract dari satker)
            "",  # M: Hak Akses  
            "no",  # N: Akses Publik? 
            structured['satker'][:30]  # O: UNIT PENGOLAH
        ]
        rows.append(row)
    
    return rows


def main(use_mapping=True):
    """
    Main function untuk append rows ke GSheets.
    
    Args:
        use_mapping: Gunakan Mapping Engine (True) atau legacy method (False)
    """
    # Load data
    if use_mapping:
        print("🔄 Using Mapping Engine (recommended)...")
        rows = load_arsip_data_with_mapping()
    else:
        print("🔄 Using Legacy method...")
        rows = load_arsip_data_legacy()
    
    if not rows:
        print("❌ No data to append!")
        return
    
    print(f"\n📊 Total {len(rows)} rows ready for GSheets")
    print("\n📋 Preview rows:")
    print("-" * 80)
    for i, row in enumerate(rows, 1):
        print(f"Row {i} (A-O):")
        cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
        for col, val in zip(cols, row):
            if val:  # Hanya tampilkan yang tidak empty
                preview = str(val)[:40] + "..." if len(str(val)) > 40 else val
                print(f"  {col}: {preview}")
        print()
    
    # Uncomment untuk append ke GSheets (memerlukan gspread dan credentials)
    """
    import gspread
    from google.oauth2.service_account import Credentials
    
    # Auth
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(SA_JSON, scopes=scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    
    # Append
    print(f"📤 Appending {len(rows)} rows to GSheets...")
    sheet.append_rows(rows)
    print("✅ SUCCESS! Rows appended to sheet row 20+")
    """
    
    print("\n📝 Untuk append ke GSheets:")
    print("   1. Pastikan gspread terinstall: pip install gspread")
    print("   2. Uncomment kode GSheets di fungsi main()")
    print("   3. Pastikan file credentials tersedia")
    print("   4. Run: python sheet_append.py")


if __name__ == "__main__":
    # Parse args
    use_mapping = "--legacy" not in sys.argv
    
    main(use_mapping=use_mapping)