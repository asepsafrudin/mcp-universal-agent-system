#!/usr/bin/env python3
"""
Parser SPTJB - Extract semua field dari OCR text ke struktur JSON yang lengkap.
Mengikuti struktur yang didefinisikan oleh user.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


MONTH_ID = {
    'Januari': '01', 'Februari': '02', 'Maret': '03', 'April': '04',
    'Mei': '05', 'Juni': '06', 'Juli': '07', 'Agustus': '08',
    'September': '09', 'Oktober': '10', 'November': '11', 'Desember': '12'
}

MONTH_ID_LOWER = {k.lower(): v for k, v in MONTH_ID.items()}


def parse_sptjb(ocr_text: str) -> Dict:
    """Parse dokumen SPTJB dari OCR text ke struktur JSON lengkap."""
    lines = ocr_text.split('\n')
    full_text = ocr_text
    
    result = {
        "jenis_dokumen": "Surat Pernyataan Tanggung Jawab Belanja",
        "nomor": extract_nomor(ocr_text),
        "satuan_kerja": extract_satuan_kerja(ocr_text),
        "dipa": extract_dipa(ocr_text),
        "klasifikasi_belanja": extract_klasifikasi(ocr_text),
        "rincian_pembayaran": [],
        "total_jumlah_rp": 0,
        "total_potongan_rp": 0,
        "keterangan": "",
        "tempat_tanggal": extract_tempat_tanggal(ocr_text),
        "penandatangan": extract_penandatangan(ocr_text)
    }
    
    # Extract rincian pembayaran (tabel)
    rincian = extract_rincian_pembayaran(ocr_text)
    result["rincian_pembayaran"] = rincian
    
    # Hitung total
    total = sum(item.get('jumlah_rp', 0) for item in rincian)
    total_potongan = sum(item.get('potongan_peh_rp', 0) + item.get('potongan_kehadiran_maret_rp', 0) for item in rincian)
    result["total_jumlah_rp"] = total
    result["total_potongan_rp"] = total_potongan
    
    # Extract keterangan
    result["keterangan"] = extract_keterangan(ocr_text)
    
    return result


def extract_nomor(text: str) -> str:
    """Extract nomor surat."""
    match = re.search(r'Nomor\s*[:|]?\s*([A-Z0-9][A-Z0-9/\.]+)', text)
    if match:
        return match.group(1).strip().lstrip('|').strip()
    return ""


def extract_satuan_kerja(text: str) -> Dict:
    """Extract satuan kerja (kode dan nama)."""
    kode = ""
    nama = ""
    
    # Kode satuan kerja
    kode_match = re.search(r'Kode\s+Satuan\s+Kerja\s*[:\|]?\s*(\d+)', text, re.IGNORECASE)
    if kode_match:
        kode = kode_match.group(1).strip()
    
    # Nama satuan kerja
    nama_match = re.search(r'Nama\s+Satuan\s+Kerja\s*[:\+\|]\s*([^\n|]+)', text, re.IGNORECASE)
    if nama_match:
        nama = nama_match.group(1).strip().lstrip('|').strip()
    else:
        # Fallback
        nama_match = re.search(r'(DITJEN BINA BANGDA[^|\n]+)', text)
        if nama_match:
            nama = nama_match.group(1).strip()
    
    return {"kode": kode, "nama": nama}


def extract_dipa(text: str) -> Dict:
    """Extract DIPA (tanggal, nomor, revisi_ke)."""
    tanggal = ""
    nomor = ""
    revisi_ke = ""
    
    # Pattern: "Tanggal/No. DIPA Revisi ke 02 : 27 Februari 2025 / 010.06.1.039729/2025"
    # atau "Tgl/No. DIPA Revisike 01 : 21 Februari 2025 / 010.06.1.039729/2025"
    
    dipa_match = re.search(
        r'Revisi[\ske]*\s*(\d+)\s*[:|]\s*(\d{1,2}\s+\w+\s+\d{4})\s*/\s*([\d/.]+)',
        text, re.IGNORECASE
    )
    
    if dipa_match:
        revisi_ke = dipa_match.group(1).strip()
        tanggal = dipa_match.group(2).strip()
        nomor = dipa_match.group(3).strip()
    else:
        # Alternate pattern
        tgl_match = re.search(r'(\d{1,2}\s+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+\d{4})', text, re.IGNORECASE)
        if tgl_match:
            tanggal = tgl_match.group(1).strip()
        
        nom_match = re.search(r'(\d{3}\.\d{2}\.\d\.\d{6}/\d{4})', text)
        if nom_match:
            nomor = nom_match.group(1).strip()
        
        rev_match = re.search(r'Revisi[\ske]*\s*(\d+)', text, re.IGNORECASE)
        if rev_match:
            revisi_ke = rev_match.group(1).strip()
    
    return {
        "tanggal": tanggal,
        "nomor": nomor,
        "revisi_ke": revisi_ke
    }


def extract_klasifikasi(text: str) -> str:
    """Extract kode klasifikasi belanja."""
    match = re.search(r'Klasifikasi\s+Belanja\s*[:|]?\s*([A-Z0-9/]+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def extract_rincian_pembayaran(text: str) -> List[Dict]:
    """
    Extract rincian pembayaran dari tabel dalam dokumen SPTJB.
    Pattern yang diharapkan:
    No | Akun | Penerima | Uraian | Jumlah | Potongan Kehadiran | Potongan PEH
    """
    rincian = []
    lines = text.split('\n')
    
    current_item = None
    in_table = False
    
    # Flag untuk mulai tabel
    for i, line in enumerate(lines):
        clean = line.strip().lstrip('|').strip()
        
        # Deteksi header tabel
        # Header bisa terpisah-pisah barisnya di PaddleOCR
        if not in_table:
            if any(kw in clean for kw in ['Akun', 'Penerima', 'Uraian']):
                # Jika sudah melihat minimal 2 kata kunci di baris ini atau baris sebelumnya
                # Untuk simplifikasi, jika melihat 'Akun' atau 'Uraian' kita asumsikan mulai tabel
                in_table = True
                continue
        
        # Deteksi baris tabel baru: nomor urut dan akun
        # Regex yang lebih toleran: angka 1-2 digit (no), lalu 5-6 digit (akun)
        row_match = re.match(r'^(\d{1,2})\s*[|]?\s*(\d{5,6}[a-zA-Z0-9]?)\s*[|]?\s*(.*)', clean)
        
        is_no_only = re.match(r'^(\d{1,2})$', clean)
        next_is_akun = False
        if i + 1 < len(lines):
            next_clean = lines[i+1].strip().lstrip('|').strip()
            # Cek akun dengan toleransi noise (contoh: 52219t)
            if re.match(r'^(\d{5,6}[a-zA-Z0-9]?)$', next_clean):
                next_is_akun = True

        if row_match or (is_no_only and next_is_akun):
            if current_item:
                rincian.append(current_item)
            
            if row_match:
                no = int(row_match.group(1))
                akun = row_match.group(2)
                rest = row_match.group(3)
            else:
                no = int(is_no_only.group(1))
                akun = lines[i+1].strip().lstrip('|').strip()
                rest = ""
                lines[i+1] = "" # Mark as processed
            
            # Normalisasi akun (ambil hanya angka)
            akun_clean = re.sub(r'\D', '', akun)
            
            current_item = {
                "no": no,
                "akun": akun_clean,
                "penerima": "",
                "uraian": rest,
                "jumlah_rp": 0,
                "potongan_kehadiran_maret_rp": 0,
                "potongan_peh_rp": 0
            }
            
            if rest:
                _parse_table_row(rest, current_item)
            
        elif current_item and clean:
            # Lanjutan dari baris sebelumnya
            current_item['uraian'] += ' ' + clean
    
    # Add last item
    if current_item:
        rincian.append(current_item)
    
    # Bersihkan rincian
    for item in rincian:
        # Bersihkan noise OCR: |, ', ", dll
        item['uraian'] = re.sub(r'[\|\'"\\#£$%&*]', ' ', item['uraian'].strip())
        item['uraian'] = re.sub(r'\s+', ' ', item['uraian']).strip()
        
        # Bersihkan nama penerima
        if item['penerima']:
            item['penerima'] = re.sub(r'[\|\'"\\#£$%&*]', ' ', item['penerima'])
            item['penerima'] = re.sub(r'\s+', ' ', item['penerima']).strip()
        
        # Extract nama penerima jika belum ada
        if not item['penerima'] and ',' in item['uraian']:
            parts = item['uraian'].split(',', 1)
            name_part = parts[0].strip()
            if 5 < len(name_part) < 50:
                item['penerima'] = name_part
                item['uraian'] = item['uraian'][len(parts[0]) + 1:].strip()
    
    return rincian


def _parse_table_row(rest: str, item: Dict):
    """Parse satu baris tabel."""
    # Pisahkan berdasarkan pipe
    parts = [p.strip() for p in rest.split('|') if p.strip()]
    
    if not parts:
        return
    
    full = ' '.join(parts)
    
    # Extract jumlah (format Indonesia: 5.513.000 atau 5,513)
    # Cari pattern angka dengan pemisah ribuan
    amount_matches = re.findall(r'[\d]{1,3}(?:[.,][\d]{3})+', full.replace(' ', ''))
    if amount_matches:
        # Biasanya jumlah yang paling besar atau paling kiri
        amounts = []
        for m in amount_matches:
            # Convert to number
            clean = m.replace('.', '').replace(',', '')
            try:
                amounts.append(int(clean))
            except:
                pass
        
        if amounts:
            # Yang terbesar biasanya jumlah utama
            amounts.sort(reverse=True)
            item['jumlah_rp'] = amounts[0]
    
    # Extract potongan kehadiran/PEH
    # "13.783" biasanya potongan kecil di akhir baris
    small_amounts = re.findall(r'(?:^|[\s|])(\d{2,5}(?:[.,]\d{3})?)(?:[\s|]|$)', full)
    
    return item


def extract_keterangan(text: str) -> str:
    """Extract keterangan dari dokumen."""
    # Cari paragraf tentang bukti pengeluaran
    match = re.search(
        r'(Bukti[- ]?\s*bukti\s+pengeluaran.+?fungsional[.])',
        text, re.IGNORECASE | re.DOTALL
    )
    if match:
        return match.group(1).strip()
    
    # Fallback: cari kalimat "Demikian"
    match = re.search(r'(Demikian\s+Surat.+?dibuat\s+dengan\s+sebenarnya[.])', text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return ""


def extract_tempat_tanggal(text: str) -> str:
    """Extract tempat dan tanggal penandatangan."""
    # Pattern: "Jakarta, 3 Maret 2025"
    match = re.search(
        r'([A-Z][a-z]+),\s*(\d{1,2}\s+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+\d{4})',
        text
    )
    if match:
        return f"{match.group(1)}, {match.group(2)}"
    
    # Fallback
    match = re.search(r'Jakarta,\s*(\d+\s+\w+\s+\d+)', text, re.IGNORECASE)
    if match:
        return f"Jakarta, {match.group(1)}"
    
    return ""


def extract_penandatangan(text: str) -> Dict:
    """Extract penandatangan."""
    jabatan = ""
    nama = ""
    
    # Jabatan
    jab_match = re.search(r'((?:PEJABAT PEMBUAT KOMITMEN|BENDAHARA PENGELUARAN)[^\n]*)', text, re.IGNORECASE)
    if jab_match:
        jabatan = jab_match.group(1).strip().lstrip('|').strip()
    
    # Nama (biasanya sebelum NIP/IP)
    nama_match = re.search(r'([A-Z][A-Z\s.,]+)\s*(?:IP|NIP)[.\s]*[\d]+', text)
    if nama_match:
        candidates = nama_match.group(1).strip()
        # Split jika ada beberapa nama
        names = [n.strip() for n in candidates.split() if len(n.strip()) > 2]
        # Ambil yang terakhir sebagai nama penandatangan
        if names:
            nama = names[-1] if len(names) <= 3 else ' '.join(names[-2:])
    
    return {"jabatan": jabatan, "nama": nama}


def process_all_files(json_dir: Path = Path("arsip-extracted")):
    """Process semua file dan update dengan struktur baru."""
    for json_file in sorted(json_dir.glob("*_structured.json")):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ocr_full = data.get('content', {}).get('raw_ocr_full', '')
        if not ocr_full:
            continue
        
        # Parse SPTJB
        sptjb_data = parse_sptjb(ocr_full)
        
        # Update content dengan struktur baru
        data['content']['sptjb'] = sptjb_data
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Preview
        doc_id = data['content'].get('doc_id', json_file.stem)
        rincian_count = len(sptjb_data.get('rincian_pembayaran', []))
        total = sptjb_data.get('total_jumlah_rp', 0)
        print(f"✓ {doc_id}: {rincian_count} rincian, Total Rp {total:,.0f}")


def main():
    print("📄 Parsing SPTJB dari OCR text...")
    process_all_files()


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent if '__file__' in dir() else '.')
    main()