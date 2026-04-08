#!/usr/bin/env python3
"""
PaddleOCR Tabel Extractor - OCR yang lebih akurat untuk tabel SPTJB.
PaddleOCR memiliki kemampuan layout analysis yang lebih baik untuk tabel.
"""
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import os


def check_paddleocr():
    """Cek dan install PaddleOCR jika diperlukan."""
    import os
    os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_textline_orientation=True, lang='en')
        return True
    except ImportError:
        print("📦 Installing PaddleOCR...")
        subprocess.run([sys.executable, "-m", "pip", "install", "paddleocr", "paddlepaddle"], check=True)
        return True
    except Exception as e:
        print(f"⚠️  PaddleOCR issue: {e}")
        return False


def run_paddleocr(image_path: str) -> Dict:
    """
    Jalankan PaddleOCR pada gambar dan return hasil lengkap.
    PaddleOCR mengembalikan: boxes, text, confidence
    """
    import os
    os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
    from paddleocr import PaddleOCR
    
    # Load model - gunakan English yang tersedia
    # Versi baru PaddleOCR punya API berbeda
    ocr = PaddleOCR(use_textline_orientation=True, lang='en')
    
    # Run OCR
    result = ocr.ocr(image_path)
    
    return result


def extract_table_structure(result) -> List[Dict]:
    """
    Extract tabel dari PaddleOCR result dengan mempertimbangkan posisi (boxes).
    """
    if not result or not result[0]:
        return []
    
    # PaddleOCR result format: [[box, (text, confidence)], ...]
    # Flatten semua hasil (OCR bisa return per line atau multi-line)
    items = []
    
    for line in result:
        if not line:
            continue
        for word_info in line:
            box = word_info[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text = word_info[1][0]
            confidence = word_info[1][1]
            
            # Hitung posisi rata-rata untuk sorting
            y_min = min(p[1] for p in box)
            x_min = min(p[0] for p in box)
            
            items.append({
                'text': text,
                'confidence': confidence,
                'x': x_min,
                'y': y_min,
                'box': box
            })
    
    # Sort by Y (row) then X (column)
    items.sort(key=lambda x: (x['y'], x['x']))
    
    return items


def group_into_rows(items: List[Dict], y_tolerance: float = 15) -> List[List[Dict]]:
    """
    Group OCR items ke dalam baris berdasarkan posisi Y.
    Items dengan Y yang berdekatan dianggap dalam baris yang sama.
    """
    if not items:
        return []
    
    rows = []
    current_row = [items[0]]
    current_y = items[0]['y']
    
    for item in items[1:]:
        if abs(item['y'] - current_y) <= y_tolerance:
            # Masih dalam baris yang sama
            current_row.append(item)
            current_y = (current_y + item['y']) / 2  # rata-rata Y
        else:
            # Baris baru
            rows.append(sorted(current_row, key=lambda x: x['x']))
            current_row = [item]
            current_y = item['y']
    
    # Tambahkan baris terakhir
    if current_row:
        rows.append(sorted(current_row, key=lambda x: x['x']))
    
    return rows


def parse_table_rows(rows: List[List[Dict]]) -> List[Dict]:
    """
    Parse baris-baris tabel yang sudah digrup ke struktur rincian pembayaran.
    """
    rincian = []
    in_table = False
    current_item = None
    item_parts = {}  # Store multi-line parts
    
    for row_data in rows:
        row_text = ' '.join(item['text'] for item in row_data).strip()
        
        # Deteksi header tabel
        if re.search(r'(?:Kode\s+)?Akun|Penerima|Uraian', row_text, re.IGNORECASE):
            in_table = True
            continue
        
        if not in_table:
            # Cek awal tabel dengan mencari nomor urut + kode akun
            if re.search(r'^\d{1,2}\s+5\d{5}', row_text):
                in_table = True
            else:
                continue
        
        # Parse baris tabel: nomor urut + kode akun di awal
        row_match = re.match(r'(\d{1,2})\s+(\d{6})\s*(.*)', row_text)
        if row_match:
            # Simpan item sebelumnya jika ada
            if current_item:
                current_item['uraian'] = current_item.get('uraian', '').strip()
                rincian.append(current_item)
            
            current_item = {
                'no': int(row_match.group(1)),
                'akun': row_match.group(2),
                'penerima': '',
                'uraian': row_match.group(3),
                'jumlah_rp': 0,
                'potongan_kehadiran_maret_rp': 0,
                'potongan_peh_rp': 0,
                '_raw': row_text
            }
            item_parts = {'uraian': [row_match.group(3)]}
        elif current_item:
            # Baris lanjutan dari item saat ini
            continue_text = row_text
            
            # Cek apakah ada jumlah di baris ini
            amount_match = re.search(r'([\d]{1,3}(?:[\.,]\d{3})+)\s*$', continue_text)
            if amount_match:
                # Cek apakah ada beberapa angka (jumlah + potongan)
                amounts = re.findall(r'[\d]{1,3}(?:[\.,]\d{3})+', continue_text)
                clean_amounts = [a.replace('.', '').replace(',', '') for a in amounts]
                int_amounts = [int(a) for a in clean_amounts if len(a.replace('.', '')) > 3]
                
                if int_amounts:
                    current_item['jumlah_rp'] = int_amounts[0]
                    if len(int_amounts) > 1:
                        current_item['potongan_kehadiran_maret_rp'] = int_amounts[-2] if len(int_amounts) > 2 else 0
                        current_item['potongan_peh_rp'] = int_amounts[-1]
            else:
                # Lanjutan uraian
                if current_item['uraian']:
                    current_item['uraian'] += ' ' + continue_text
                else:
                    current_item['uraian'] = continue_text
    
    # Simpan item terakhir
    if current_item:
        current_item['uraian'] = current_item.get('uraian', '').strip()
        rincian.append(current_item)
    
    # Bersihkan uraian dari noise karakter
    for item in rincian:
        if item.get('uraian'):
            # Bersihkan karakter OCR yang tidak diinginkan
            item['uraian'] = re.sub(r'[\|\x00-\x1f\x7f-\x9f]', ' ', item['uraian'])
            item['uraian'] = re.sub(r'\s+', ' ', item['uraian']).strip()
            
            # Ekstrak nama penerima jika belum ada
            if not item.get('penerima') and ',' in item['uraian']:
                parts = item['uraian'].split(',', 1)
                name = parts[0].strip()
                if 5 < len(name) < 50 and re.search(r'[A-Z][a-z]+', name):
                    item['penerima'] = name
                    item['uraian'] = item['uraian'][len(parts[0]):].strip(' ,')
    
    return rincian


def process_image_paddle(image_path: str, json_path: str) -> Dict:
    """
    Process single image dengan PaddleOCR dan simpan hasil ke JSON.
    """
    print(f"\n🔍 PaddleOCR: {Path(image_path).name}")
    
    # Jalankan PaddleOCR
    result = run_paddleocr(image_path)
    
    # Extract semua text dalam order reading
    ocr_text = ""
    ocr_items = extract_table_structure(result)
    
    # Reconstruct text dalam urutan logis
    rows = group_into_rows(ocr_items)
    for row_data in rows:
        line_text = ' '.join(item['text'] for item in row_data)
        ocr_text += line_text + '\n'
    
    full_text = ocr_text.strip()
    
    # Import fungsi parsing dari sptjb_parser
    sys.path.insert(0, str(Path(__file__).parent))
    from sptjb_parser import parse_sptjb
    
    # Parse dengan teks dari PaddleOCR
    sptjb_data = parse_sptjb(full_text)
    
    # Parsing tabel khusus yang lebih akurat
    table_rincian = parse_table_rows(rows)
    if table_rincian:
        sptjb_data['rincian_pembayaran'] = table_rincian
        sptjb_data['total_jumlah_rp'] = sum(i.get('jumlah_rp', 0) for i in table_rincian)
        sptjb_data['total_potongan_rp'] = sum(
            i.get('potongan_kehadiran_maret_rp', 0) + i.get('potongan_peh_rp', 0)
            for i in table_rincian
        )
    
    # Build JSON structure
    data = {
        "key": f"{Path(image_path).stem}_structured",
        "content": {
            "doc_id": Path(image_path).stem,
            "filename": Path(image_path).name,
            "doc_type": "SPTJB" if "SURAT PERNYATAAN TANGGUNG JAWAB" in full_text else "UNKNOWN",
            "nomor_surat": sptjb_data.get('nomor', ''),
            "uraian": sptjb_data.get('jenis_dokumen', ''),
            "klasifikasi": sptjb_data.get('klasifikasi_belanja', ''),
            "satker": sptjb_data.get('satuan_kerja', {}).get('nama', ''),
            "extraction_date": __import__('datetime').datetime.now().isoformat(),
            "raw_ocr_full": full_text,
            "raw_ocr_snippet": full_text[:500] + '...' if len(full_text) > 500 else full_text,
            "sptjb": sptjb_data,
            "items_count": len(table_rincian)
        }
    }
    
    # Save JSON
    json_path = Path(json_path)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"   ✅ Saved: {json_path}")
    
    # Save markdown
    md_path = json_path.with_stem(Path(image_path).stem + "_md")
    with open(md_path.with_suffix('.md'), 'w', encoding='utf-8') as f:
        f.write(f"# {data['content']['doc_type']} - {data['content']['nomor_surat']}\n\n")
        f.write(full_text)
    
    # Summary
    print(f"   📋 Uraian: {sptjb_data.get('jenis_dokumen', '')}")
    print(f"   🏷️  Klasifikasi: {sptjb_data.get('klasifikasi_belanja', '')}")
    print(f"   💰 Items: {len(table_rincian)}")
    for item in table_rincian[:3]:
        print(f"      #{item.get('no')}: {item.get('uraian', '')[:60]}... | Rp {item.get('jumlah_rp', 0):,}")
    
    return data


def process_all_images():
    """Process semua gambar dengan PaddleOCR."""
    scan_dir = Path("arsip-2025/scan")
    extracted_dir = Path("arsip-extracted")
    extracted_dir.mkdir(exist_ok=True)
    
    png_files = list(scan_dir.glob("*.png"))
    if not png_files:
        print("❌ No PNG files found!")
        return
    
    print(f"📁 Found {len(png_files)} PNG files")
    print("⚠️  PaddleOCR mungkin butuh waktu beberapa menit per gambar...")
    
    success = 0
    for png_file in png_files:
        json_path = extracted_dir / f"{png_file.stem}_structured.json"
        try:
            process_image_paddle(str(png_file), str(json_path))
            success += 1
        except Exception as e:
            print(f"   ❌ Error processing {png_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ PaddleOCR complete: {success}/{len(png_files)} files")


def main():
    if not check_paddleocr():
        print("❌ Failed to install PaddleOCR")
        return
    
    process_all_images()


if __name__ == "__main__":
    main()