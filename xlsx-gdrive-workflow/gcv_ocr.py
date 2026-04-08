#!/usr/bin/env python3
"""
GCV OCR - Google Cloud Vision API OCR untuk mengekstrak tabel dari gambar SPTJB.
API key loaded from .env file.
"""
import json
import re
import base64
import io
import os
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Load API key from environment
API_KEY = os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please set it in .env file.")


def gcv_ocr(image_path: str) -> str:
    """Google Cloud Vision DOCUMENT_TEXT_DETECTION."""
    with Image.open(image_path) as img:
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.convert('RGB').save(buffer, format='JPEG', quality=85)
        b64 = base64.b64encode(buffer.getvalue()).decode()
    
    url = f'https://vision.googleapis.com/v1/images:annotate?key={API_KEY}'
    payload = {
        'requests': [{
            'image': {'content': b64},
            'features': [{'type': 'DOCUMENT_TEXT_DETECTION', 'maxResults': 1}],
            'imageContext': {'languageHints': ['id', 'en']}
        }]
    }
    
    response = requests.post(url, json=payload, timeout=60)
    if response.status_code != 200:
        print(f"GCV error: {response.status_code} {response.text[:200]}")
        return ""
    
    result = response.json()
    resp = result.get('responses', [])
    if resp:
        full_text = resp[0].get('fullTextAnnotation', {}).get('text', '')
        if full_text:
            return full_text
        annotations = resp[0].get('textAnnotations', [])
        if annotations:
            return annotations[0].get('description', '')
    return ""


def parse_sptjb_from_gcv(text: str) -> Dict:
    """Parse SPTJB dari hasil GCV OCR - line-by-line approach for accuracy."""
    lines = text.split('\n')
    
    result = {
        "jenis_dokumen": "Surat Pernyataan Tanggung Jawab Belanja",
        "nomor": "",
        "satuan_kerja": {"kode": "", "nama": ""},
        "dipa": {"tanggal": "", "nomor": "", "revisi_ke": ""},
        "klasifikasi_belanja": "",
        "rincian_pembayaran": [],
        "total_jumlah_rp": 0,
        "total_potongan_rp": 0,
        "tempat_tanggal": "",
        "penandatangan": {"jabatan": "", "nama": ""}
    }
    
    # Extract Nomor from "Nomor : XXX" or "Nomor XXX"
    nomor_match = re.search(r'Nomor\s*[:\|]?\s*([A-Z0-9][A-Z0-9/\.]+(?:2025|20\d{2})?)', text)
    if nomor_match:
        result['nomor'] = nomor_match.group(1).strip()
    
    # Kode satuan kerja
    kode_match = re.search(r'Kode\s+(?:Sal|Satu|Sali|n\s+Ker|n\s+Kerja|an\s+Kerja)\s*[:\s]?\s*(\d{6})', text, re.IGNORECASE)
    if kode_match:
        result['satuan_kerja']['kode'] = kode_match.group(1)
    
    # Nama satuan kerja
    satker_match = re.search(r'(DITJEN\s+BINA\s+[A-Z\s]+?)(?:\s*TGL|\s+\d{1,2}\s+\w+\s+\d{4})', text, re.IGNORECASE)
    if satker_match:
        result['satuan_kerja']['nama'] = satker_match.group(1).strip()[:60]
    
    # DIPA info
    dipa_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})\s*/\s*([\d.]+)', text)
    if dipa_match:
        result['dipa']['tanggal'] = dipa_match.group(1).strip()
        result['dipa']['nomor'] = dipa_match.group(2).strip()
    
    # Revisi ke
    rev_match = re.search(r'Rev(?:isi|isie)\s*(?:ke)?\s*[:\s]?\s*(\d+)', text, re.IGNORECASE)
    if rev_match: result['dipa']['revisi_ke'] = rev_match.group(1)
    
    # Klasifikasi
    klas_match = re.search(r'(0[0-9]{1}/0[0-9]{1}/0[0-9]{1}/[A-Z0-9]+/[0-9]{6,7}|[0-9]{2}/[0-9]{2}/[0-9]{2}/[A-Z0-9]+/[0-9]{6})', text)
    if klas_match:
        result['klasifikasi_belanja'] = klas_match.group(1)
    
    # === TABLE PARSING (line-by-line) ===
    # Find where "No Akun" header starts
    table_start = -1
    for i, line in enumerate(lines):
        if re.search(r'^No\s+Aku|^No\s*Akun|N?\s*o\s+Aku', line, re.IGNORECASE):
            table_start = i + 1
            break
    
    if table_start > 0:
        # Collect all table content until the next major section
        table_lines = []
        for line in lines[table_start:]:
            line_clean = line.strip().lstrip('|').strip()
            if not line_clean:
                continue
            # Stop when seeing "Bukti-bukti" or "Demikian"
            if re.search(r'Bukti[- ]?|Demikian|Jakarta,|PEJABAT PEM', line_clean, re.IGNORECASE):
                break
            table_lines.append(line_clean)
        
        # Now parse table content
        # Expected structure per row (with continuation):
        # "1 522191 Yonatan Maryon Sisco, SH"
        # "Untuk Pembayaran ... bulan Maret Tahun Anggaran 2025"
        # "sesuai SK 800.1.2.5-012/Kep/Bangda/2025 tanggal 2 Januari 2025"
        # "Jumlah 5.513.000 0 13.783"
        
        items = []
        current_item = None
        
        for line in table_lines:
            # New row: "1 522191 Yonatan..." or "2 522191 Fannia..."
            row_match = re.match(r'^(\d{1,2})\s+(\d{6})\s+', line)
            if row_match:
                if current_item:
                    items.append(current_item)
                current_item = {
                    'no': int(row_match.group(1)),
                    'akun': row_match.group(2),
                    'penerima': '',
                    'uraian': '',
                    'jumlah_rp': 0,
                    'potongan_kehadiran_maret_rp': 0,
                    'potongan_peh_rp': 0,
                    '_raw': [line]
                }
            elif current_item:
                current_item['_raw'].append(line)
        
        if current_item:
            items.append(current_item)
        
        # Now parse each item's raw lines
        for item in items:
            raw = '\n'.join(item['_raw'])
            
            # Extract nama: "1 522191 Yonatan Maryon Sisco, SH" -> "Yonatan Maryon Sisco, SH"
            nama_match = re.match(r'^(\d{1,2})\s+(\d{6})\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3}(?:,\s*[A-Z\\.]+)?(?:,\s*(?:SH|MH|S\.Kom|A\.Md))?)', raw)
            if nama_match:
                item['penerima'] = nama_match.group(3).strip()
                # Get text after nama for uraian
                after_nama = raw[nama_match.end():].strip()
            else:
                after_nama = raw.strip()
                # Try fallback: extract any name-like pattern
                fallback_nama = re.search(r'([A-Z][a-zA-Z]+\s+(?:[A-Z][a-zA-Z]+\s+){0,2}(?:SH|MH|A\.Md|S\\.Kom))', after_nama)
                if fallback_nama:
                    item['penerima'] = fallback_nama.group(1).strip()
                    after_nama = after_nama[after_nama.index(fallback_nama.group(1)):].strip()
            
            # Extract jumlah - look for "Jumlah" line or numbers at end
            jumlah_match = re.search(r'Jumlah\s*([\d][\d.,]+)', raw)
            if not jumlah_match:
                # Look for standalone number at end of raw
                numbers = re.findall(r'(\d[\d.,]+)', after_nama)
                for n in numbers:
                    clean_n = n.replace('.', '').replace(',', '')
                    if len(clean_n) >= 5:
                        jumlah_match_groups = [n]
                        break
                else:
                    jumlah_match_groups = []
                if jumlah_match_groups:
                    clean = jumlah_match_groups[0].replace('.', '').replace(',', '')
                    if len(clean) > 3:
                        try:
                            item['jumlah_rp'] = int(clean)
                        except:
                            pass
            else:
                clean = jumlah_match.group(1).replace('.', '').replace(',', '')
                try:
                    item['jumlah_rp'] = int(clean)
                except:
                    pass
            
            # Extract potongan - look for small numbers (typically < 100000)
            # "5.513.000 0 13.783" -> potongan is the small numbers
            all_numbers = re.findall(r'(?<!\d)(\d[\d.]?\,{1,3}\d{1,3}|\d{3,})(?!,)(?!\d)', raw)
            all_clean = []
            for n in all_numbers:
                clean_n = n.replace('.', '').replace(',', '')
                if clean_n and len(clean_n) > 1:
                    try:
                        val = int(clean_n)
                        if val > 999:
                            all_clean.append(val)
                    except:
                        pass
            
            if all_clean:
                # Smallest 2-3 numbers are potongan, largest is jumlah
                all_clean.sort()
                if len(all_clean) >= 4:
                    # Jumlah = largest, potongan = 2nd and 3rd smallest (or 0 if less)
                    item['jumlah_rp'] = all_clean[-1]
                    if len(all_clean) >= 3:
                        item['potongan_kehadiran_maret_rp'] = all_clean[-3] if all_clean[-3] < all_clean[-2] else 0
                        item['potongan_peh_rp'] = all_clean[-2] if all_clean[-2] < all_clean[-1] else 0
            
            # Urain: text between nama and jumlah
            # Find the description part
            uraian_lines = []
            in_uraian = False
            for l in item['_raw']:
                if in_uraian:
                    if l.startswith('Jumlah') or re.match(r'^[\d,.\s]+$', l):
                        break
                    uraian_lines.append(l)
                elif item['penerima'] and l != item['_raw'][0]:
                    in_uraian = True
                    if l.find(item['penerima']) >= 0:
                        after_p = l[l.find(item['penerima']) + len(item['penerima']):].strip()
                        if after_p and after_p not in ['', ' ', '  ']:
                            uraian_lines.append(after_p)
                    else:
                        uraian_lines.append(l)
            
            uraian_text = ' '.join(uraian_lines).strip()
            uraian_text = re.sub(r'[\|\'"\\#£$%&*]', ' ', uraian_text)
            uraian_text = re.sub(r'\s+', ' ', uraian_text)
            item['uraian'] = uraian_text.strip()[:500]
            
            # Clean up temp
            del item['_raw']
        
        result['rincian_pembayaran'] = items
    
    result['total_jumlah_rp'] = sum(i.get('jumlah_rp', 0) for i in result['rincian_pembayaran'])
    result['total_potongan_rp'] = sum(
        i.get('potongan_kehadiran_maret_rp', 0) + i.get('potongan_peh_rp', 0)
        for i in result['rincian_pembayaran']
    )
    
    return result


def process_all():
    """Process semua gambar."""
    scan_dir = Path("arsip-2025/scan")
    extracted_dir = Path("arsip-extracted")
    extracted_dir.mkdir(exist_ok=True)
    
    png_files = sorted(scan_dir.glob("*.png"))
    print(f"Found {len(png_files)} files")
    print(f"Using GCV API key: {API_KEY[:10]}...{API_KEY[-4:]}")
    
    success = 0
    for png_file in png_files:
        print(f"\n🔍 GCV OCR: {png_file.name}")
        text = gcv_ocr(str(png_file))
        if not text:
            continue
        
        print(f"  ✅ OCR: {len(text)} chars")
        
        sptjb_data = parse_sptjb_from_gcv(text)
        
        data = {
            "key": f"{png_file.stem}_structured",
            "content": {
                "doc_id": png_file.stem,
                "filename": png_file.name,
                "doc_type": "SPTJB",
                "nomor_surat": sptjb_data.get('nomor', ''),
                "uraian": "SURAT PERNYATAAN TANGGUNG JAWAB BELANJA",
                "klasifikasi": sptjb_data.get('klasifikasi_belanja', ''),
                "satker": sptjb_data.get('satuan_kerja', {}).get('nama', ''),
                "extraction_date": __import__('datetime').datetime.now().isoformat(),
                "raw_ocr_full": text,
                "raw_ocr_snippet": text[:500] + '...' if len(text) > 500 else text,
                "items_count": len(sptjb_data.get('rincian_pembayaran', [])),
                "sptjb": sptjb_data
            }
        }
        
        json_path = extracted_dir / f"{png_file.stem}_structured.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Save markdown
        md_path = extracted_dir / f"{png_file.stem}_md.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"  📄 {sptjb_data.get('nomor', '-')} | {len(sptjb_data.get('rincian_pembayaran', []))} items")
        success += 1
    
    print(f"\n✅ GCV OCR complete: {success}/{len(png_files)} files")


if __name__ == "__main__":
    process_all()