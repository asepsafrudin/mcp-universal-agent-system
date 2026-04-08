#!/usr/bin/env python3
'''
Arsip Database → GSheets Auto Append (dengan Mapping Engine)
Menggunakan column_mapping.json sebagai konfigurasi transformasi

Mapping kolom (berdasarkan column_mapping.json):
  A: Boks (doc_id)
  B: (empty)
  C: KODE KLASIFIKASI (konstan: 000.8)
  D: NOMOR SURAT
  E: URAIAN (doc_type - satker)
  F: KURUN WAKTU (YYYY-MM)
  G-I: (empty)
  J: Tingkat Perkembangan (konstan: baru)
  K: Keterangan (empty)
  L: Klasifikasi (extracted dari OCR)
  M: Hak Akses (empty)
  N: Akses Publik? (konstan: no)
  O: UNIT PENGOLAH (satker truncated 30 char)
'''
import json
import glob
from pathlib import Path
import asyncio
import sys

# Import MappingEngine
from mapping_engine import MappingEngine, ArsipDataLoader

# Spreadsheet ID
SPREADSHEET_ID = "18H6gIv61XTdUsA7zh0XoQqmRWQxlfuNvbRMq5n8AwRM"


def load_arsip_data():
    """Load data arsip menggunakan Mapping Engine."""
    engine = MappingEngine()
    loader = ArsipDataLoader()
    
    all_data = loader.load_all()
    if not all_data:
        return []
    
    rows = []
    for data in all_data:
        row = engine.transform_row(data)
        rows.append(row)
    
    return rows


def load_arsip_data_legacy():
    """Legacy method untuk backward compatibility."""
    rows = []
    extracted_dir = Path("arsip-extracted")
    for json_file in extracted_dir.glob("*_structured.json"):
        data = json.loads(json_file.read_text())
        structured = data['content']
        
        row = [
            structured['doc_id'],  # A Boks
            "",  # B
            "000.8",  # C KODE KLASIFIKASI
            structured['nomor_surat'],  # D NOMOR SURAT
            f"{structured['doc_type']} - {structured['satker'][:50]}",  # E URASIP
            structured['extraction_date'][:7],  # F KURUN WAKTU
            "",  # G-H-I
            "baru",  # Tingkat Perkembangan
            "",  # KeterangAN
            "",  # Klasifikasi
            "",  # Hak Akses
            "no",  # Akses Publik
            "",  # Dasar
            structured['satker'][:30]  # N UNIT PENGOLAH
        ]
        rows.append(row)
    return rows


async def append_to_sheets(rows):
    """Append rows to GSheets (simulasi)."""
    print(f"📊 Appending {len(rows)} rows to GSheets...")
    print("Real: use_mcp_tool('mcp-unified', 'sheets_append_values', {...})")


if __name__ == "__main__":
    use_mapping = "--legacy" not in sys.argv
    
    if use_mapping:
        print("🔄 Using Mapping Engine...")
        rows = load_arsip_data()
    else:
        print("🔄 Using Legacy method...")
        rows = load_arsip_data_legacy()
    
    print("Data ready for Sheet:")
    for i, row in enumerate(rows, 1):
        print(f"Row {i}: {row}")
    
    # asyncio.run(append_to_sheets(rows))
    print("\nCopy paste rows di atas ke Sheet row 20+")