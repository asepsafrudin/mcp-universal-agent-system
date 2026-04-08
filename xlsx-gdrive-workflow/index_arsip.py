#!/usr/bin/env python
"""
Arsip Indexing Workflow - FIXED & IMPROVED
Scan PNG → OCR Tesseract → Parse Structured → Save to Memory + Knowledge Base

Supports multiple document types:
- SPTJB (Surat Pernyataan Tanggung Jawab Belanja)
- SPP (Surat Permintaan Pembayaran)
- STT (Surat Tanda Terima)
- Other arsip documents

Usage:
    python index_arsip.py                    # Process all PNG files
    python index_arsip.py --scan-dir DIR     # Process specific directory
    python index_arsip.py --single FILE      # Process single file
    python index_arsip.py --dry-run          # Preview without saving
"""
import os
import json
import re
import subprocess
import glob
import argparse
from pathlib import Path
from datetime import datetime
import asyncio


# ============================================================
# CONFIGURATION
# ============================================================
SCAN_DIR = Path(__file__).parent / "arsip-2025" / "scan"
EXTRACTED_DIR = Path(__file__).parent / "arsip-extracted"
NAMESPACE = "arsip-puu-2025"

# Ensure extracted directory exists
EXTRACTED_DIR.mkdir(exist_ok=True)


# ============================================================
# OCR ENGINE
# ============================================================
def ocr_image(image_path: str, language: str = "ind+eng") -> str:
    """
    Perform OCR using Tesseract.
    
    Args:
        image_path: Path to image file
        language: Language hint (default: ind+eng for Indonesian + English)
    
    Returns:
        Extracted text string
    """
    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Check tesseract available
    try:
        subprocess.run(["tesseract", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("Tesseract OCR not installed! Install with: sudo apt install tesseract-ocr")
    
    result = subprocess.run([
        "tesseract", image_path, "stdout",
        "-l", language, "--psm", "3", "--oem", "1"
    ], capture_output=True, text=True, encoding="utf-8")
    
    if result.returncode != 0:
        print(f"  ⚠️ Tesseract stderr: {result.stderr[:200]}")
    
    return result.stdout.strip()


def gcv_ocr(image_path: str, api_key: str = None) -> str:
    """
    Perform OCR using Google Cloud Vision API (more accurate for tables).
    Requires: pip install requests Pillow
    """
    try:
        import base64
        import io
        import requests
        from PIL import Image
    except ImportError:
        print("⚠️ GCV requires requests and Pillow. pip install requests Pillow")
        return ""
    
    if api_key is None:
        api_key = os.environ.get("GCV_API_KEY", "AIzaSyCbbOGZoJ6bQcaubDpw8uvubi6TF4O4FPE")
    
    try:
        with Image.open(image_path) as img:
            img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            img.convert('RGB').save(buffer, format='JPEG', quality=90)
            b64 = base64.b64encode(buffer.getvalue()).decode()
        
        url = f'https://vision.googleapis.com/v1/images:annotate?key={api_key}'
        payload = {
            'requests': [{
                'image': {'content': b64},
                'features': [{'type': 'DOCUMENT_TEXT_DETECTION', 'maxResults': 1}],
                'imageContext': {'languageHints': ['id', 'en']}
            }]
        }
        
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code != 200:
            print(f"  ⚠️ GCV error: {response.status_code}")
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
    except Exception as e:
        print(f"  ⚠️ GCV exception: {e}")
    
    return ""


# ============================================================
# PARSER ENGINE
# ============================================================
def detect_doc_type(ocr_text: str) -> str:
    """Detect document type from OCR text."""
    text_upper = ocr_text.upper()
    
    if "SURAT PERNYATAAN TANGGUNG JAWAB BELANJA" in text_upper or "SPTJB" in text_upper:
        return "SPTJB"
    elif "SURAT PERMINTAAN PEMBAYARAN" in text_upper or "SPP" in text_upper:
        return "SPP"
    elif "SURAT TANDA TERIMA" in text_upper or "STT" in text_upper:
        return "STT"
    elif "DISPOSISI" in text_upper:
        return "DISPOSISI"
    elif "SURAT KELUAR" in text_upper:
        return "SURAT_KELUAR"
    elif "SURAT MASUK" in text_upper:
        return "SURAT_MASUK"
    else:
        return "UNKNOWN"


def extract_nomor_surat(ocr_text: str, doc_type: str) -> str:
    """Extract nomor surat from OCR text."""
    # Try multiple patterns
    patterns = [
        r'Nomor\s*:\s*([A-Z0-9][A-Z0-9/\.]+)',
        r'Nomor\s+([\d]{1,4}/[A-Z0-9\./]+)',
        r'No\.?\s*:\s*([A-Z0-9][A-Z0-9/\.]+)',
        r'No\.?\s+([A-Z0-9][A-Z0-9/\.]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return "unknown"


def extract_satker(ocr_text: str) -> str:
    """Extract nama satuan kerja."""
    patterns = [
        r'Nama\s+Satuan\s+Kerja\s*:\s*(.+?)(?:\n|$)',
        r'(DITJEN\s+[A-Z\s]+?)(?:\n|TGL|\d{1,2}\s+\w+\s+\d{4})',
        r'(KEMENTERIAN[^\\n]+?)(?:\n|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:100]
    
    return ""


def extract_klasifikasi(ocr_text: str) -> str:
    """Extract klasifikasi belanja."""
    patterns = [
        r'(0[0-9]{1}/[0-9]{2}/[0-9]{2,4}/[A-Z0-9]+/[0-9]{5,7})',
        r'(0[0-9]{1}/[0-9]{2}/[0-9]{2}/[A-Z0-9]+/[0-9]{5})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, ocr_text)
        if match:
            return match.group(1).strip()
    
    return ""


def extract_table_items(ocr_text: str, doc_type: str) -> list:
    """
    Extract table items from the document.
    Returns list of dicts with: no, akun, penerima, uraian, jumlah, etc.
    """
    items = []
    lines = ocr_text.split('\n')
    
    if doc_type == "SPTJB":
        # Find table start - more flexible pattern matching for OCR text
        table_start = -1
        for i, line in enumerate(lines):
            # Look for table header patterns in OCR text
            if re.search(r'No\s*.*Aku|Bukti\s*Pajak|Akun\s*Penerima', line, re.IGNORECASE):
                table_start = i + 1
                break
        
        if table_start < 0:
            return items
        
        # Collect table content until end markers
        table_lines = []
        for line in lines[table_start:]:
            line_clean = line.strip().lstrip('|').strip()
            if not line_clean:
                continue
            # Stop at section boundaries
            if re.search(r'^Bukti[- ]?pengeluaran|^Demikian|^Jakarta,|^PEJABAT|^NIP|^Pengguna Anggaran', line_clean, re.IGNORECASE):
                break
            table_lines.append(line_clean)
        
        # Parse each item - handle OCR artifacts
        current_item = None
        for line in table_lines:
            # New row detection: "1 | 524113" or "1 524113" or similar OCR variants
            # Also handle pipes and other OCR artifacts
            clean_line = re.sub(r'[|]', ' ', line).strip()
            clean_line = re.sub(r'\s+', ' ', clean_line)
            
            # Try multiple row patterns for OCR text
            row_match = re.match(r'^(\d{1,2})\s+(\d{5,6})\s+', clean_line)
            if not row_match:
                # Try with pipe separator: "1 | 524113"
                row_match = re.match(r'^(\d{1,2})\s*\|\s*(\d{5,6})\s+', clean_line)
            if not row_match:
                # Try with OCR artifacts: "2 | 524133) 'Sukma..."
                row_match = re.match(r'^(\d{1,2})\s*\|\s*(\d{5,6})\)?\s*[\'"]?\s*([A-Z])', clean_line)
            
            if row_match:
                if current_item:
                    items.append(current_item)
                current_item = {
                    'no': int(row_match.group(1)),
                    'akun': row_match.group(2),
                    'penerima': '',
                    'uraian': '',
                    'tanggal': '',
                    'nomor_bpn': '',
                    'jumlah_rp': 0,
                    '_raw': [line]
                }
            elif current_item:
                current_item['_raw'].append(line)
        
        if current_item:
            items.append(current_item)
        
        # Debug: show raw lines if no items found
        if not items and table_lines:
            print(f"    ⚠️ Table lines found but no items parsed. First 3 lines:")
            for l in table_lines[:3]:
                print(f"      {l[:80]}")
        
        # Parse raw data for each item
        for item in items:
            raw = '\n'.join(item['_raw'])
            _parse_sptjb_item(item, raw)
            del item['_raw']  # Clean up
    
    return items


def _parse_sptjb_item(item: dict, raw: str):
    """Parse a single SPTJB table row from raw text."""
    # Clean up OCR artifacts first
    clean_raw = re.sub(r'[|\'"\\#£$%&*]', ' ', raw)
    clean_raw = re.sub(r'\s+', ' ', clean_raw)
    
    # Extract nama penerima - multiple patterns for OCR variants
    patterns_nama = [
        # Standard: "1 524113 Faisal Baharuddin, SH, Cs"
        r'^(\d{1,2})\s+(\d{5,6})\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+(?:,\s*[A-Z\.]+)?)',
        # With artifacts: "2 | 524133) 'Sukma Adi Nugroho, SH, Cs"
        r'^(\d{1,2})\s*\|\s*(\d{5,6})\)?\s*[\'"]?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+(?:,\s*[A-Z\.]+)?)',
        # Just name with title: "Faisal Baharuddin, SH"
        r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?,\s*(?:SH|MH|S\.Kom|A\.Md)(?:\s+Cs)?)',
    ]
    
    for pattern in patterns_nama:
        nama_match = re.search(pattern, clean_raw)
        if nama_match:
            # Group 3 for patterns 1,2; Group 1 for pattern 3
            if len(nama_match.groups()) >= 3:
                item['penerima'] = nama_match.group(3).strip()
            else:
                item['penerima'] = nama_match.group(1).strip()
            break
    
    if not item.get('penerima'):
        # Last resort: look for "Name, SH" or "Name, MH" pattern anywhere
        fallback = re.search(r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*,\s*(?:SH|MH|S\.Kom|A\.Md))', clean_raw)
        if fallback:
            item['penerima'] = fallback.group(1).strip()
    
    # Extract tanggal - look for DD-MM-YYYY or DD/MM/YYYY
    tgl_match = re.search(r'(\d{2}[-/]\d{2}[-/]\d{4})', raw)
    if tgl_match:
        item['tanggal'] = tgl_match.group(1)
    
    # Extract Nomor BPN - look for patterns like "001/F.2/010.06.WA/524113"
    bpn_patterns = [
        r'(\d{3}/[A-Z0-9\./]+WA/\d{6})',
        r'(\d{3}/F\.2/[A-Z0-9\./]+)',
        r'(\d{3}/[A-Z0-9\./]+/524113)',
    ]
    for bpn_pat in bpn_patterns:
        bpn_match = re.search(bpn_pat, raw)
        if bpn_match:
            item['nomor_bpn'] = bpn_match.group(1)
            break
    
    # Extract jumlah - look for money amounts (e.g., 340.000, 2.550.000)
    # Money pattern: digits with dot separators
    money_matches = re.findall(r'([\d]{1,3}(?:\.[\d]{3})+(?:000)?)', clean_raw)
    jumlah_candidates = []
    for m in money_matches:
        clean_m = m.replace('.', '').replace(',', '')
        if len(clean_m) >= 4:
            try:
                val = int(clean_m)
                if val > 50000:  # Filter: only amounts > 50k
                    jumlah_candidates.append(val)
            except ValueError:
                pass
    
    # Also check for "Jumlah" line
    jumlah_line_match = re.search(r'[Jj]umlah\s+([\d][\d.,]+)', raw, re.IGNORECASE)
    if jumlah_line_match:
        clean_j = jumlah_line_match.group(1).replace('.', '').replace(',', '')
        try:
            val = int(clean_j)
            if val > 1000:
                # Use the Jumlah line value (most reliable)
                item['jumlah_rp'] = val
        except ValueError:
            pass
    
    # If no Jumlah line found, use the largest number from candidates
    if not item.get('jumlah_rp') and jumlah_candidates:
        item['jumlah_rp'] = max(jumlah_candidates)
    
    # Extract uraian - look for description keywords
    uraian_patterns = [
        r'Biaya\s+(?:Transport|Perjalanan|makan|Honor|akomodasi)[^,\n|]*',
        r'Untuk\s+pembayaran[^,\n|]*',
        r'Dalam\s+rangka[^,\n|]*',
        r'Rapat[^,\n|]{10,}',
    ]
    
    for uraian_pat in uraian_patterns:
        uraian_match = re.search(uraian_pat, clean_raw, re.IGNORECASE)
        if uraian_match:
            item['uraian'] = uraian_match.group(0).strip()[:500]
            break
    
    # If no uraian found, use context around the name
    if not item.get('uraian') and item.get('penerima'):
        name_idx = clean_raw.find(item['penerima'])
        if name_idx >= 0:
            # Get text after name, up to first date or BPN number
            after_name = clean_raw[name_idx + len(item['penerima']):]
            # Stop at date or BPN pattern
            stop_match = re.search(r'\d{2}[-/]\d{2}[-/]\d{4}|\d{3}/F\.2/', after_name)
            if stop_match:
                uraian_text = after_name[:stop_match.start()].strip()
            else:
                uraian_text = after_name[:300].strip()
            
            # Clean up
            uraian_text = re.sub(r'[|\'"\\#£$%&*]', ' ', uraian_text)
            uraian_text = re.sub(r'\s+', ' ', uraian_text)
            if uraian_text and len(uraian_text) > 10:
                item['uraian'] = uraian_text


def extract_penandatangan(ocr_text: str) -> dict:
    """Extract penandatangan info."""
    result = {
        "jabatan": "",
        "nama": "",
        "nip": "",
        "tempat_tanggal": ""
    }
    
    # Jabatan
    jabatan_match = re.search(r'(PEJABAT PEMBUAT KOMITMEN[^\\n]*)', ocr_text, re.IGNORECASE)
    if jabatan_match:
        result['jabatan'] = jabatan_match.group(1).strip()
    
    # NIP
    nip_match = re.search(r'NIP\.?\s*([\d\s]+)', ocr_text)
    if nip_match:
        result['nip'] = nip_match.group(1).strip()
    
    # Tempat tanggal
    tgl_match = re.search(r'([A-Z][a-z]+,\s*\d+\s+\w+\s+\d{4})', ocr_text)
    if tgl_match:
        result['tempat_tanggal'] = tgl_match.group(1).strip()
    
    return result


def parse_structured(ocr_text: str, filename: str) -> dict:
    """
    Main parser function. Converts OCR text to structured JSON.
    
    Args:
        ocr_text: Raw OCR text
        filename: Original filename
    
    Returns:
        Structured data dictionary
    """
    doc_id = Path(filename).stem
    doc_type = detect_doc_type(ocr_text)
    
    # Extract basic fields
    nomor_surat = extract_nomor_surat(ocr_text, doc_type)
    satker = extract_satker(ocr_text)
    klasifikasi = extract_klasifikasi(ocr_text)
    
    # Extract uraian (document title)
    uraian = ""
    text_upper = ocr_text.upper()
    if "SURAT PERNYATAAN TANGGUNG JAWAB BELANJA" in text_upper:
        uraian = "SURAT PERNYATAAN TANGGUNG JAWAB BELANJA"
    elif "SURAT PERMINTAAN PEMBAYARAN" in text_upper:
        uraian = "SURAT PERMINTAAN PEMBAYARAN"
    elif "SURAT TANDA TERIMA" in text_upper:
        uraian = "SURAT TANDA TERIMA"
    else:
        # Fallback: first meaningful line
        first_lines = [l.strip() for l in ocr_text.split('\n') 
                       if l.strip() and len(l.strip()) > 10]
        uraian = first_lines[0].lstrip('|').strip() if first_lines else "UNKNOWN"
    
    # Extract table items
    items = extract_table_items(ocr_text, doc_type)
    
    # Extract penandatangan
    penandatangan = extract_penandatangan(ocr_text)
    
    # Calculate totals from items
    total_jumlah = sum(i.get('jumlah_rp', 0) for i in items)
    
    # Build structured data
    structured = {
        "doc_id": doc_id,
        "filename": filename,
        "doc_type": doc_type,
        "nomor_surat": nomor_surat,
        "satker": satker,
        "uraian": uraian,
        "klasifikasi": klasifikasi,
        "extraction_date": datetime.now().isoformat(),
        "items_count": len(items),
        "total_jumlah_rp": total_jumlah,
        "penandatangan": penandatangan,
        "items": items,
        "raw_ocr_snippet": ocr_text[:500] + "..." if len(ocr_text) > 500 else ocr_text
    }
    
    return structured


# ============================================================
# STORAGE
# ============================================================
async def save_to_memory(key: str, content: dict, namespace: str = NAMESPACE):
    """Save structured data to memory (with file backup)."""
    print(f"  💾 Saving to memory: {key}")
    
    # Backup to file (in case memory is not available)
    backup_path = EXTRACTED_DIR / f"{key}.json"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump({"key": key, "namespace": namespace, "content": content}, 
                  f, indent=2, ensure_ascii=False)
    
    print(f"  📄 Backup: {backup_path}")
    return backup_path


async def save_as_markdown(doc_id: str, ocr_text: str, structured: dict) -> Path:
    """Save OCR result as markdown file."""
    md_path = EXTRACTED_DIR / f"{doc_id}_md.md"
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {structured.get('doc_type', 'Document')} - {structured.get('nomor_surat', '')}\n\n")
        f.write(f"**Doc ID**: {doc_id}\n")
        f.write(f"**Type**: {structured.get('doc_type', 'UNKNOWN')}\n")
        f.write(f"**Satker**: {structured.get('satker', '-')}\n")
        f.write(f"**Klasifikasi**: {structured.get('klasifikasi', '-')}\n")
        f.write(f"**Extracted**: {structured.get('extraction_date', '-')}\n\n")
        
        if structured.get('items'):
            f.write(f"## Table Data ({structured['items_count']} items)\n\n")
            total = sum(i.get('jumlah_rp', 0) for i in structured['items'])
            f.write(f"**Total**: Rp {total:,.0f}\n\n")
        
        f.write("---\n\n")
        f.write("## Raw OCR Text\n\n")
        f.write("```\n")
        f.write(ocr_text)
        f.write("\n```\n")
    
    print(f"  📄 Markdown: {md_path}")
    return md_path


# ============================================================
# MAIN WORKFLOW
# ============================================================
async def process_single_file(png_path: Path, use_gcv: bool = False, 
                              dry_run: bool = False) -> dict:
    """
    Process a single PNG file through the full pipeline.
    
    Args:
        png_path: Path to PNG file
        use_gcv: Use Google Cloud Vision instead of Tesseract
        dry_run: Only preview, don't save
    
    Returns:
        Structured data dictionary
    """
    print(f"\n{'='*60}")
    print(f"🔍 Processing: {png_path.name}")
    print(f"{'='*60}")
    
    # Step 1: OCR
    print("\n📷 Running OCR...")
    if use_gcv:
        ocr_text = gcv_ocr(str(png_path))
        engine = "GCV"
    else:
        ocr_text = ocr_image(str(png_path))
        engine = "Tesseract"
    
    if not ocr_text:
        print("  ❌ OCR returned empty text!")
        return {}
    
    print(f"  ✅ OCR ({engine}): {len(ocr_text)} characters")
    
    # Step 2: Parse
    print("\n🔧 Parsing structured data...")
    structured = parse_structured(ocr_text, png_path.name)
    
    print(f"  📄 Type: {structured['doc_type']}")
    print(f"  📄 Nomor: {structured['nomor_surat']}")
    print(f"  📄 Satker: {structured['satker'][:50]}...")
    print(f"  📄 Items: {structured['items_count']}")
    
    if structured['total_jumlah_rp'] > 0:
        print(f"  💰 Total: Rp {structured['total_jumlah_rp']:,.0f}")
    
    # Print items preview
    if structured['items']:
        print("\n  📋 Items preview:")
        for item in structured['items'][:3]:
            print(f"    - {item.get('penerima', '?')}: Rp {item.get('jumlah_rp', 0):,}")
    
    # Step 3: Save (unless dry run)
    if dry_run:
        print("\n  ⏭️ Dry run - not saving")
        return structured
    
    print("\n💾 Saving results...")
    await save_to_memory(f"{structured['doc_id']}_structured", structured)
    await save_as_markdown(structured['doc_id'], ocr_text, structured)
    
    print(f"\n✅ Done: {png_path.name}")
    return structured


async def index_folder(scan_dir: Path = SCAN_DIR, use_gcv: bool = False,
                       max_files: int = 0, dry_run: bool = False) -> list:
    """
    Process all PNG files in scan directory.
    
    Args:
        scan_dir: Directory to scan
        use_gcv: Use Google Cloud Vision
        max_files: Max files to process (0 = all)
        dry_run: Preview mode
    
    Returns:
        List of structured data dictionaries
    """
    if not scan_dir.exists():
        raise FileNotFoundError(f"Scan directory not found: {scan_dir}")
    
    png_files = sorted(scan_dir.glob("*.png"))
    if not png_files:
        print(f"⚠️ No PNG files found in {scan_dir}")
        return []
    
    if max_files > 0:
        png_files = png_files[:max_files]
    
    print(f"\n{'='*60}")
    print(f"ARSIP INDEXING WORKFLOW")
    print(f"{'='*60}")
    print(f"📁 Scan dir: {scan_dir}")
    print(f"📄 Files to process: {len(png_files)}")
    print(f"🔤 OCR Engine: {'GCV' if use_gcv else 'Tesseract'}")
    print(f"📦 Output: {EXTRACTED_DIR}")
    if dry_run:
        print(f"⏭️ Mode: DRY RUN")
    
    results = []
    success = 0
    failed = 0
    
    for png_file in png_files:
        try:
            result = await process_single_file(png_file, use_gcv=use_gcv, 
                                               dry_run=dry_run)
            if result:
                results.append(result)
                success += 1
        except Exception as e:
            print(f"  ❌ Error processing {png_file.name}: {e}")
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")
    print(f"📄 Total: {len(png_files)}")
    print(f"\n📦 Results saved to: {EXTRACTED_DIR}")
    
    return results


# ============================================================
# CLI ENTRY POINT
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Arsip Indexing Workflow")
    parser.add_argument("--scan-dir", type=str, default=str(SCAN_DIR),
                        help="Directory containing PNG files to process")
    parser.add_argument("--single", type=str, default="",
                        help="Process single PNG file")
    parser.add_argument("--gcv", action="store_true",
                        help="Use Google Cloud Vision OCR")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview mode - don't save results")
    parser.add_argument("--max", type=int, default=0,
                        help="Maximum files to process (0 = all)")
    
    args = parser.parse_args()
    
    if args.single:
        # Process single file
        png_path = Path(args.single)
        if not png_path.exists():
            print(f"❌ File not found: {png_path}")
            return
        result = asyncio.run(process_single_file(png_path, 
                                                  use_gcv=args.gcv,
                                                  dry_run=args.dry_run))
        if result and not args.dry_run:
            print(f"\n✅ Processing complete: {result['doc_id']}")
    else:
        # Process folder
        scan_dir = Path(args.scan_dir)
        asyncio.run(index_folder(scan_dir=scan_dir,
                                 use_gcv=args.gcv,
                                 max_files=args.max,
                                 dry_run=args.dry_run))


if __name__ == "__main__":
    main()