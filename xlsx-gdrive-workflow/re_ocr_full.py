#!/usr/bin/env python3
"""
Re-OCR semua file PNG dan update JSON dengan full OCR text.
Bug fix: raw_ocr_snippet di JSON cuma 500 char, tapi seharusnya full OCR.
"""
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime


def ocr_image(image_path: str) -> str:
    """Tesseract OCR - full text without limit."""
    result = subprocess.run([
        "tesseract", image_path, "stdout", 
        "-l", "ind+eng", "--psm", "6"
    ], capture_output=True, text=True, encoding="utf-8")
    return result.stdout.strip()


def extract_uraian(ocr_text: str) -> str:
    """Ekstrak uraian/judul dari OCR text."""
    lines = [l.strip().lstrip('|').strip() for l in ocr_text.split('\n') if l.strip()]
    
    judul_patterns = [
        r'SURAT PERNYATAAN TANGGUNG JAWAB BELANJA',
        r'SURAT PERMINTAAN PEMBAYARAN',
        r'SURAT TANDA TERIMA',
        r'SURAT PERJANJIAN',
        r'BERITA ACARA',
    ]
    
    for line in lines:
        for pattern in judul_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return line[:100]
    
    for line in lines:
        if len(line) > 10 and not re.match(r'^[\d/:]+$', line):
            return line[:100]
    
    return "UNKNOWN"


def extract_klasifikasi(ocr_text: str) -> str:
    """Ekstrak kode klasifikasi dari OCR."""
    match = re.search(r'Klasifikasi Belanja[\s\:]+([A-Z0-9/]+)', ocr_text)
    return match.group(1) if match else ""


def extract_nomor_surat(ocr_text: str) -> str:
    """Ekstrak nomor surat dari OCR."""
    # Pattern: "Nomor : 002/F.2/LS/11172025" atau "Nomor: 003/F.2/LS/IN2025"
    match = re.search(r'Nomor\s*[:\|]?\s*([A-Z0-9][A-Z0-9/\.]+)', ocr_text)
    if match:
        val = match.group(1).strip().lstrip('|').strip()
        if len(val) > 3 and not val.isdigit():
            return val
    return "unknown"


def extract_satker(ocr_text: str) -> str:
    """Ekstrak nama satker dari OCR."""
    match = re.search(r'Nama Satuan Kerja[\s\:\.\+]+([^\n]+)', ocr_text)
    if match:
        return match.group(1).strip().lstrip('|').strip()
    match = re.search(r'(DITJEN BINA BANGDA[^\n]+)', ocr_text)
    return match.group(1).strip() if match else "unknown"


def extract_doc_type(ocr_text: str) -> str:
    """Detect doc type dari OCR."""
    if "SURAT PERMINTAAN PEMBAYARAN" in ocr_text or "SPP" in ocr_text:
        return "SPP"
    elif "SURAT PERNYATAAN TANGGUNG JAWAB" in ocr_text or "SPTJB" in ocr_text:
        return "SPTJB"
    return "UNKNOWN"


def extract_items(ocr_text: str) -> list:
    """Ekstrak baris yang mengandung nilai uang (Rp)."""
    items = []
    for line in ocr_text.split('\n'):
        if re.search(r'Rp[\s\.]*[0-9,.]+', line) or re.search(r'[0-9]+\.[0-9]{3},[0-9]+', line):
            items.append({"raw": line.strip()})
    return items[:10]


def process_file(png_path: Path, json_path: Path) -> bool:
    """Re-OCR single file dan update JSON."""
    print(f"\n🔍 OCR: {png_path.name}")
    
    # Full OCR
    ocr_text = ocr_image(png_path)
    ocr_len = len(ocr_text)
    print(f"   Full OCR: {ocr_len} chars")
    
    # Extract semua fields
    doc_id = png_path.stem
    doc_type = extract_doc_type(ocr_text)
    nomor_surat = extract_nomor_surat(ocr_text)
    satker = extract_satker(ocr_text)
    uraian = extract_uraian(ocr_text)
    klasifikasi = extract_klasifikasi(ocr_text)
    items = extract_items(ocr_text)
    
    # Build structured JSON
    structured = {
        "doc_id": doc_id,
        "filename": png_path.name,
        "doc_type": doc_type,
        "nomor_surat": nomor_surat,
        "satker": satker,
        "uraian": uraian,
        "klasifikasi": klasifikasi,
        "extraction_date": datetime.now().isoformat(),
        "items_count": len(items),
        "raw_ocr_full": ocr_text,  # FULL OCR text, no truncation
        "raw_ocr_snippet": ocr_text[:500] + "..." if ocr_len > 500 else ocr_text,
        "items": items
    }
    
    # Save JSON
    data = {"key": f"{doc_id}_structured", "content": structured}
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"   ✅ Saved: {json_path}")
    
    # Save full markdown
    md_path = json_path.with_name(png_path.stem + "_md.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {doc_type} - {nomor_surat}\n")
        f.write(f"**Uraian**: {uraian}\n")
        f.write(f"**Klasifikasi**: {klasifikasi}\n")
        f.write(f"**Satker**: {satker}\n\n")
        f.write("```\n")
        f.write(ocr_text)
        f.write("\n```\n")
    print(f"   📄 Markdown: {md_path}")
    
    # Print summary
    print(f"   📋 Uraian: {uraian}")
    print(f"   🏷️  Klasifikasi: {klasifikasi}")
    print(f"   💰 Items: {len(items)}")
    
    return True


def main():
    scan_dir = Path("arsip-2025/scan")
    extracted_dir = Path("arsip-extracted")
    
    png_files = list(scan_dir.glob("*.png"))
    print(f"📁 Found {len(png_files)} PNG files")
    
    success = 0
    for png_file in png_files:
        json_path = extracted_dir / f"{png_file.stem}_structured.json"
        try:
            if process_file(png_file, json_path):
                success += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n{'='*50}")
    print(f"✅ Re-OCR complete: {success}/{len(png_files)} files")


if __name__ == "__main__":
    main()