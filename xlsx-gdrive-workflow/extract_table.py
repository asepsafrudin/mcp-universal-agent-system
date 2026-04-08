#!/usr/bin/env python3
"""
Ekstrak tabel dari OCR text hasil scan SPTJB/SPP.
Struktur tabel yang diketahui:
- Header: Akun | Penerima | Uraian | Jumlah | Bukti/PPN
- Baris: no | kode | nama, deskripsi | jumlah | nomor_spp
"""
import json
import re
from pathlib import Path
from typing import List, Dict


def parse_table_from_ocr(ocr_text: str) -> List[Dict]:
    """
    Parse tabel dari OCR text.
    Mengembalikan list of dict dengan keys: no, akun, penerima, uraian, jumlah, bukti
    """
    items = []
    lines = ocr_text.split('\n')
    
    # Pola untuk baris tabel: nomor urut di awal baris
    # Format: "1 |524111 |Nama, Biaya ... | 5.903.480"
    # atau: "1 4111 |Nama | Deskripsi | Jumlah | Bukti"
    
    current_item = None
    
    for line in lines:
        line = line.strip().lstrip('|').strip()
        
        # Skip baris header dan non-tabel
        if not line or len(line) < 10:
            continue
            
        # Deteksi baris baru tabel (dimulai dengan nomor urut 1-99)
        no_match = re.match(r'^(\d{1,2})\s*[|]?\s*([0-9]+)\s*[|]?', line)
        if no_match:
            # Simpan item sebelumnya
            if current_item:
                items.append(current_item)
            
            no = int(no_match.group(1))
            akun = no_match.group(2)
            rest = line[no_match.end():]
            
            current_item = {
                'no': no,
                'akun': akun,
                'penerima': '',
                'uraian': '',
                'jumlah': '',
                'bukti': '',
                'raw': line
            }
            
            # Cek apakah ada pipe sebagai delimiter
            if '|' in rest:
                parts = [p.strip() for p in rest.split('|')]
                # Parse berdasarkan posisi
                if len(parts) >= 2:
                    # Cek apakah ada angka (jumlah) di akhir
                    for i, part in enumerate(parts):
                        if re.search(r'[0-9]+[\.,][0-9]{3}', part) and not current_item['jumlah']:
                            # Ini kolom jumlah
                            clean_jumlah = re.sub(r'[^\d,\.]', '', part)
                            current_item['jumlah'] = clean_jumlah
                        elif re.search(r'[0-9]+/[A-Z]', part) and not current_item['bukti']:
                            # Ini kolom bukti/SPP
                            current_item['bukti'] = part
                        elif part and not current_item['penerima'] and ',' in part:
                            # Nama penerima biasanya mengandung koma
                            current_item['penerima'] = part
                        elif part and not current_item['uraian']:
                            current_item['uraian'] = part
            continue
        
        # Lanjutan baris sebelumnya (uraian multi-line)
        if current_item:
            # Cek apakah baris mengandung informasi penting
            if re.search(r'[0-9]+[\.,][0-9]{3}', line) and not current_item['jumlah']:
                # Baris jumlah
                clean_jumlah = re.sub(r'[^\d,\.]', '', line)
                current_item['jumlah'] = clean_jumlah
            
            if re.search(r'[0-9]+/[A-Z]', line) and not current_item['bukti']:
                # Baris bukti/SPP
                bukti_match = re.search(r'([0-9]+/[A-Z][^\s]*(?:/[^/\s]+)*)', line)
                if bukti_match:
                    current_item['bukti'] = bukti_match.group(1)
            
            if 'sesuai Surat Tugas' in line or 'tanggal' in line:
                current_item['uraian'] += ' ' + line.strip()
    
    # Simpan item terakhir
    if current_item:
        items.append(current_item)
    
    return items


def parse_amount(amount_str: str) -> float:
    """Parse jumlah ke float."""
    if not amount_str:
        return 0
    # Remove everything except digits, comma, dot
    clean = re.sub(r'[^\d,\.]', '', amount_str)
    # Handle Indonesian format (comma as thousands, dot as decimal)
    if ',' in clean and '.' not in clean:
        clean = clean.replace(',', '.')
    elif ',' in clean and '.' in clean:
        # "5.903,480" -> comma is thousands, remove it
        # But this is ambiguous - assume Indonesian style: remove thousand sep
        if clean.rindex(',') > clean.rindex('.'):
            clean = clean.replace(',', '')  # European: 5.903.480 -> 5903480
        else:
            clean = clean.replace(',', '')  # US style: remove comma
    
    try:
        return float(clean)
    except ValueError:
        return 0


def format_amount(amount_str: str) -> str:
    """Format amount ke format angka yang konsisten."""
    if not amount_str:
        return "0"
    # Extract all digits
    digits = re.findall(r'[\d]+', amount_str.replace(',', '.').replace('.', ','))
    # Try to reconstruct
    clean = re.sub(r'[^\d]', '', amount_str)
    if not clean:
        return "0"
    return clean


def extract_all_tables(json_dir: Path) -> Dict[str, List[Dict]]:
    """Extract tabel dari semua JSON files."""
    results = {}
    
    for json_file in json_dir.glob("*_structured.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ocr_text = data.get('content', {}).get('raw_ocr_full', '')
        if not ocr_text:
            continue
        
        items = parse_table_from_ocr(ocr_text)
        if items:
            doc_id = data['content'].get('doc_id', json_file.stem)
            results[doc_id] = items
            
            # Update JSON dengan tabel items
            data['content']['table_items'] = items
            data['content']['items_count'] = len(items)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ {doc_id}: {len(items)} items")
    
    return results


def main():
    json_dir = Path("arsip-extracted")
    print(f"📊 Ekstrak tabel dari {len(list(json_dir.glob('*_structured.json')))} files...")
    
    results = extract_all_tables(json_dir)
    
    print(f"\n✅ Total {len(results)} dokumen dengan tabel:")
    for doc_id, items in results.items():
        print(f"\n📄 {doc_id} ({len(items)} items):")
        for item in items:
            print(f"  #{item['no']}: Akun={item['akun']}, Penerima={item['penerima'][:30] if item['penerima'] else '-'}, Jumlah={item['jumlah']}")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent if '__file__' in dir() else '.')
    main()