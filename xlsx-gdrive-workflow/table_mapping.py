#!/usr/bin/env python3
"""
Mapping tabel dari OCR text ke format spreadsheet.
Setiap item tabel dipetakan ke baris terpisah di sheet 'Table_Detail'.

Struktur kolom Tabel:
- doc_id
- no (nomor urut tabel)
- kode_akun
- penerima
- uraian (deskripsi pengeluaran)
- jumlah (angka uang)
- tanggal
- lokasi  
- nomor_spp (bukti)
- nomor_surat_tugas
"""
import json
import re
from pathlib import Path
from typing import List, Dict


def extract_table_items(ocr_text: str) -> List[Dict]:
    """
    Extract table items dari OCR text.
    Mengembalikan list of item dengan field: no, kode_akun, penerima, uraian, jumlah, tanggal, lokasi, nomor_spp, nomor_tugas
    """
    items = []
    lines = ocr_text.split('\n')
    
    # State machine untuk tracking posisi dalam tabel
    current_item = None
    
    for i, line in enumerate(lines):
        # Bersihkan line
        clean = line.strip().lstrip('|').strip()
        
        # Deteksi awal row baru: nomor urut (1-99) di awal
        # Pattern: "1 522191 |" atau "1 |522191 |"
        row_match = re.match(r'^(\d{1,2})\s+[|]?\s*(\d{4,6})\s*[|]?(.*)', clean)
        if row_match:
            if current_item:
                items.append(current_item)
            
            current_item = {
                'no': int(row_match.group(1)),
                'kode_akun': row_match.group(2),
                'penerima': '',
                'uraian': '',
                'jumlah': '',
                'tanggal': '',
                'lokasi': '',
                'nomor_spp': '',
                'nomor_tugas': '',
                'raw': clean
            }
            rest = row_match.group(3)
            _parse_row_content(rest, current_item)
        elif current_item:
            _parse_continuation(clean, current_item)
    
    if current_item:
        items.append(current_item)
    
    return items


def _parse_row_content(rest: str, item: Dict):
    """Parse isi baris tabel."""
    parts = [p.strip() for p in rest.split('|') if p.strip()]
    
    if not parts:
        return
    
    # Join semua parts untuk analisis
    full = ' '.join(parts)
    
    # Pattern: Nama, Deskripsi Jumlah Tanggal SPP/Tugas
    # Contoh: "Lucia Hapsari, Biaya perjalanan... 5.903.480 31-10-2025 020/F.2/..."
    
    # Ekstrak jumlah (pattern uang Indonesia)
    amount_match = re.search(r'([\d]+[.,]?\d{3}[.,]?\d*)\b', full.replace('.', 'X').replace(',', '.').replace('X', ','))
    if not amount_match:
        # Try simpler: just find numbers with separators
        amount_match = re.search(r'([\d]+[.,][\d]+[,.\d]*)', full)
    
    if amount_match:
        item['jumlah'] = amount_match.group(1)
    
    # Ekstrak tanggal
    date_match = re.search(r'(\d{1,2}-\d{1,2}-\d{4})', full)
    if date_match:
        item['tanggal'] = date_match.group(1)
    
    # Ekstrak nomor SPP (pattern: angka/huruf/...)
    spp_match = re.search(r'(\d{3}/[A-Z]\.\d/[A-Z]/\d+/[\d/]+)', full)
    if spp_match:
        item['nomor_spp'] = spp_match.group(1)
    else:
        spp_match2 = re.search(r'(\d{3}/[A-Z]\.[\d]+/[\d\/]+)', full)
        if spp_match2:
            item['nomor_spp'] = spp_match2.group(1)
    
    # Ekstrak nama (biasanya mengandung koma atau gelar: SH, MH)
    name_match = re.search(r'([A-Z][a-z]+ (?:[A-Z][a-z]+,? ){0,3}(?:SH|MH|S\.(?:Kom|E|H)|A\.(?:Md)?))', full)
    if name_match:
        item['penerima'] = name_match.group(1)
    elif ',' in full:
        # Try first part as name
        name_part = full.split(',')[0].strip()
        if 5 < len(name_part) < 40:
            item['penerima'] = name_part
    
    # Ekstrak uraian/deskripsi
    uraian_parts = [p for p in parts if not re.search(r'[\d]+[.,]?\d{3}', p) and not re.search(r'\d+/\w', p)]
    item['uraian'] = ' '.join(uraian_parts)[:100]
    
    # Ekstrak lokasi
    loc_match = re.search(r'(Jakarta|Donggala|Sulawesi|Prov\.[A-Z\s]+)', full)
    if loc_match:
        item['lokasi'] = loc_match.group(1)


def _parse_continuation(line: str, item: Dict):
    """Parse baris lanjutan dari item sebelumnya."""
    # Cek apakah mengandung informasi penting
    
    if 'Surat Tugas' in line:
        tugas_match = re.search(r'No\.([0-9A-Z/.]+)', line)
        if tugas_match:
            item['nomor_tugas'] = tugas_match.group(1)
    
    # Tanggal lanjutan
    if not item['tanggal']:
        date_match = re.search(r'(\d{1,2}-\d{1,2}-\d{4})', line)
        if date_match:
            item['tanggal'] = date_match.group(1)
    
    # SPP lanjutan
    if not item['nomor_spp']:
        spp_match = re.search(r'(\d{3}/[A-Z]\.\d/[A-Z]/[\d/]+)', line)
        if spp_match:
            item['nomor_spp'] = spp_match.group(1)
    
    # Jumlah lanjutan
    if not item['jumlah']:
        amount_match = re.search(r'[\d]+[.,]?[\d]+[,.\d]*', line)
        if amount_match:
            # Pastikan ini angka uang (> 3 digit)
            num = re.sub(r'[^\d]', '', amount_match.group())
            if len(num) > 3:
                item['jumlah'] = amount_match.group()


def process_all_documents(json_dir: Path = Path("arsip-extracted")) -> Dict[str, List[Dict]]:
    """Process semua dokumen dan extract tabel."""
    results = {}
    
    for json_file in sorted(json_dir.glob("*_structured.json")):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ocr_text = data.get('content', {}).get('raw_ocr_full', '')
        if not ocr_text:
            continue
        
        items = extract_table_items(ocr_text)
        
        if items:
            doc_id = data['content'].get('doc_id', json_file.stem)
            results[doc_id] = items
            
            # Update JSON
            data['content']['table_items'] = items
            data['content']['items_count'] = len(items)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    return results


def get_sheet_rows(results: Dict[str, List[Dict]]) -> List[List[str]]:
    """Convert results ke rows untuk GSheets.
    Kolom: doc_id | no | kode_akun | penerima | uraian | jumlah | tanggal | lokasi | nomor_spp | nomor_tugas
    """
    rows = []
    header = ['doc_id', 'no', 'kode_akun', 'penerima', 'uraian', 'jumlah', 'tanggal', 'lokasi', 'nomor_spp', 'nomor_tugas']
    rows.append(header)
    
    for doc_id, items in results.items():
        for item in items:
            row = [
                item.get('no', ''),
                item.get('kode_akun', ''),
                item.get('penerima', ''),
                item.get('uraian', ''),
                item.get('jumlah', ''),
                item.get('tanggal', ''),
                item.get('lokasi', ''),
                item.get('nomor_spp', ''),
                item.get('nomor_tugas', '')
            ]
            rows.append(row)
    
    return rows


def main():
    print("📊 Extract tabel dari dokumen arsip...")
    results = process_all_documents()
    
    print(f"\n✅ Total {len(results)} dokumen dengan tabel")
    
    # Preview beberapa item
    for doc_id, items in list(results.items())[:5]:
        print(f"\n📄 {doc_id} ({len(items)} items):")
        for item in items:
            print(f"  #{item.get('no')}: {item.get('penerima', '-')[:30]} | {item.get('jumlah')} | {item.get('tanggal')}")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent if '__file__' in dir() else '.')
    main()