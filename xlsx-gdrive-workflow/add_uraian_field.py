#!/usr/bin/env python3
"""
Script untuk menambahkan field "uraian" ke file JSON yang sudah ada.
Membaca raw_ocr_snippet dan mengekstrak uraian/judul dokumen.
"""
import json
import re
from pathlib import Path


def extract_uraian_from_ocr(ocr_text: str) -> str:
    """Ekstrak uraian/judul dari OCR text."""
    # Bersihkan karakter pipe dan whitespace
    lines = [l.strip().lstrip('|').strip() for l in ocr_text.split('\n') if l.strip()]
    
    # Pattern untuk judul dokumen resmi
    judul_patterns = [
        r'SURAT PERNYATAAN TANGGUNG JAWAB BELANJA',
        r'SURAT PERMINTAAN PEMBAYARAN',
        r'SURAT TANDA TERIMA',
        r'SURAT PERJANJIAN',
        r'SURAT KETERANGAN',
        r'SURAT KEPUTUSAN',
        r'SURAT TUGAS',
        r'BERITA ACARA',
        r'NOTA DINAS',
        r'MEMORANDUM',
    ]
    
    # Cek pattern judul
    for line in lines:
        for pattern in judul_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return line[:100]  # Batasi panjang
    
    # Fallback: ambil baris pertama yang panjang (> 10 char) dan bukan nomor/kode
    for line in lines:
        if len(line) > 10 and not re.match(r'^[\d/:]+$', line):
            return line[:100]
    
    return "UNKNOWN"


def add_uraian_to_json(json_file: Path) -> bool:
    """Tambahkan field uraian ke file JSON."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        content = data.get('content', {})
        
        # Sudah ada uraian? skip
        if 'uraian' in content and content['uraian']:
            print(f"  ⏭️ Skip (uraian sudah ada): {content.get('doc_id', 'unknown')}")
            return False
        
        # Ekstrak uraian dari raw_ocr_snippet
        ocr_text = content.get('raw_ocr_snippet', '')
        uraian = extract_uraian_from_ocr(ocr_text)
        
        # Update content
        content['uraian'] = uraian
        data['content'] = content
        
        # Save
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Added uraian: {uraian}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    extracted_dir = Path("arsip-extracted")
    json_files = list(extracted_dir.glob("*_structured.json"))
    
    print(f"📊 Found {len(json_files)} structured JSON files")
    
    updated = 0
    for json_file in json_files:
        print(f"Processing: {json_file.name}")
        if add_uraian_to_json(json_file):
            updated += 1
    
    print(f"\n✅ Updated {updated}/{len(json_files)} files")


if __name__ == "__main__":
    main()