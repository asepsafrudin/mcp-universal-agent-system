#!/usr/bin/env python3
"""
Ollama Llava OCR - Menggunakan vision model dari mcp-unified untuk OCR tabel SPTJB.
Pendekatan: Convert gambar jadi base64, kirim ke Llava, minta output terstruktur.
"""
import json
import re
import base64
import io
import os
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-unified"))

from PIL import Image

OLLAMA_URL = "http://localhost:11434"
VISION_MODEL = "llava"
VISION_TIMEOUT = 120  # 2 menit untuk OCR yang lebih lama


def image_to_base64(image_path: str, max_size: int = 2048) -> Optional[str]:
    """Load image, resize, convert ke base64."""
    try:
        with Image.open(image_path) as img:
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=90)
            return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        print(f"  ❌ Error processing image: {e}")
        return None


# Working GCV API key (billing enabled on project #501243520118)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "AIzaSyCbbOGZoJ6bQcaubDpw8uvubi6TF4O4FPE")

def call_gcloud_vision(image_base64: str) -> Optional[str]:
    """Fallback: Google Cloud Vision DOCUMENT_TEXT_DETECTION for OCR."""
    import requests
    print("  🔄 Fallback ke Google Cloud Vision API...")
    
    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
    payload = {
        "requests": [{
            "image": {"content": image_base64},
            "features": [
                {"type": "DOCUMENT_TEXT_DETECTION", "maxResults": 1}
            ],
            "imageContext": {"languageHints": ["id", "en"]}
        }]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code != 200:
            print(f"  ❌ GCV error {response.status_code}: {response.text[:200]}")
            return None
        
        result = response.json()
        resp = result.get("responses", [])
        if resp:
            full_text = resp[0].get("fullTextAnnotation", {}).get("text", "")
            if full_text:
                print(f"  ✅ GCV success: {len(full_text)} chars")
                return full_text
            # Fallback ke textAnnotations
            annotations = resp[0].get("textAnnotations", [])
            if annotations:
                return annotations[0].get("description", "")
        return None
    except Exception as e:
        print(f"  ❌ GCV request error: {e}")
        return None


def call_ollama_vision(image_base64: str, prompt: str, model: str = VISION_MODEL) -> Optional[str]:
    """Panggil Ollama vision model via Python requests, fallback ke GCV."""
    import requests
    
    # Coba Ollama dulu
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=VISION_TIMEOUT
        )
        
        if response.status_code != 200:
            print(f"  ⚠️ Ollama error: {response.status_code}")
            raise Exception("Ollama unavailable")
        
        data = response.json()
        text = data.get("response", "")
        if text:
            return text
        
        raise Exception("Empty response")
        
    except Exception as e:
        print(f"  ⚠️ Ollama failed: {e}")
        # Fallback ke Google Cloud Vision
        return call_gcloud_vision(image_base64)


SPTJB_TABLE_PROMPT = """
You are a document analysis AI. This image is a "Surat Pernyataan Tanggung Jawab Belanja" (SPTJB).

Please extract ALL information from this document and return it as a JSON with these exact fields:

{
  "nomor": "nomor surat",
  "kode_satuan_kerja": "kode satker (contoh: 039729)",
  "nama_satuan_kerja": "nama satker lengkap",
  "dipa_tanggal": "tanggal DIPA",
  "dipa_nomor": "nomor DIPA",
  "dipa_revisi_ke": "nomor revisi (angka saja)",
  "klasifikasi_belanja": "kode klasifikasi belanja",
  "table_items": [
    {
      "no": 1,
      "akun": "kode akun",
      "penerima": "nama lengkap penerima (gelar seperti SH, MH tetap ada)",
      "uraian": "deskripsi lengkap pembayaran (jelaskan semua detail termasuk bulan, tahun anggaran, SK, tanggal)",
      "jumlah_rp": 5513000,
      "potongan_kehadiran_maret_rp": 0,
      "potongan_peh_rp": 0
    }
  ],
  "total_jumlah_rp": 11026000,
  "tempat_tanggal": "Jakarta, 3 Maret 2025",
  "penandatangan_nama": "nama penandatangan",
  "penandatangan_jabatan": "jabatan penandatangan",
  "penandatangan_nip": "NIP penandatangan"
}

IMPORTANT RULES:
1. Extract ALL rows from the table, not just first 2
2. For potongan_kehadiran_maret_rp and potongan_peh_rp - look for small numbers at end of table rows (like 13783)
3. Clean ALL text - remove OCR noise like |, ", #, etc.
4. Uraian must be COMPLETE description - include month, year, SK number, date, and purpose
5. Jumlah should be integer (no thousand separators) - example: 5513000
6. Return ONLY valid JSON, no markdown, no explanation
7. If table has 5 rows, all 5 must be extracted

Return valid JSON only.
"""


def parse_ollama_response(response: str) -> Dict:
    """Parse JSON response dari Ollama."""
    try:
        # Coba langsung parse
        return json.loads(response)
    except json.JSONDecodeError:
        # Coba extract JSON dari response yang mungkin punya text lain
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
    return {}


def process_image_ollama(image_path: str, output_json: str) -> Dict:
    """Process single image dengan Ollama Llava."""
    print(f"\n🔍 Ollama OCR: {Path(image_path).name}")
    
    # Convert image to base64
    img_base64 = image_to_base64(str(image_path))
    if not img_base64:
        return {}
    
    # Call Ollama vision
    print("  📤 Sending to Llava...")
    response = call_ollama_vision(img_base64, SPTJB_TABLE_PROMPT)
    
    if not response:
        print("  ❌ No response from Llava")
        return {}
    
    # Parse response
    data = parse_ollama_response(response)
    if not data:
        print("  ❌ Failed to parse JSON response")
        print(f"  Response: {response[:500]}...")
        return {}
    
    print(f"  ✅ Success: {len(data.get('table_items', []))} items extracted")
    
    # Build full JSON structure
    table_items = data.get('table_items', [])
    
    # Calculate totals
    total_jumlah = sum(item.get('jumlah_rp', 0) for item in table_items)
    total_potongan = sum(
        item.get('potongan_kehadiran_maret_rp', 0) + item.get('potongan_peh_rp', 0) 
        for item in table_items
    )
    
    full_data = {
        "key": f"{Path(image_path).stem}_structured",
        "content": {
            "doc_id": Path(image_path).stem,
            "filename": Path(image_path).name,
            "doc_type": "SPTJB",
            "nomor_surat": data.get('nomor', ''),
            "satker": data.get('nama_satuan_kerja', ''),
            "uraian": "SURAT PERNYATAAN TANGGUNG JAWAB BELANJA",
            "klasifikasi": data.get('klasifikasi_belanja', ''),
            "extraction_date": __import__('datetime').datetime.now().isoformat(),
            "raw_ocr_full": response,
            "raw_ocr_snippet": response[:500] if len(response) > 500 else response,
            "items_count": len(table_items),
            "sptjb": {
                "jenis_dokumen": "Surat Pernyataan Tanggung Jawab Belanja",
                "nomor": data.get('nomor', ''),
                "satuan_kerja": {
                    "kode": data.get('kode_satuan_kerja', ''),
                    "nama": data.get('nama_satuan_kerja', '')
                },
                "dipa": {
                    "tanggal": data.get('dipa_tanggal', ''),
                    "nomor": data.get('dipa_nomor', ''),
                    "revisi_ke": data.get('dipa_revisi_ke', '')
                },
                "klasifikasi_belanja": data.get('klasifikasi_belanja', ''),
                "rincian_pembayaran": [
                    {
                        "no": item.get("no", i+1),
                        "akun": item.get("akun", ""),
                        "penerima": item.get("penerima", ""),
                        "uraian": item.get("uraian", ""),
                        "jumlah_rp": item.get("jumlah_rp", 0),
                        "potongan_kehadiran_maret_rp": item.get("potongan_kehadiran_maret_rp", 0),
                        "potongan_peh_rp": item.get("potongan_peh_rp", 0)
                    }
                    for i, item in enumerate(table_items)
                ],
                "total_jumlah_rp": total_jumlah,
                "total_potongan_rp": total_potongan,
                "keterangan": "Bukti-bukti pengeluaran anggaran dan asli setoran (SSP/BPN) disimpan oleh Pengguna Anggaran/Kuasa Pengguna Anggaran untuk kelengkapan administrasi dan pemeriksaan aparat pengawasan fungsional.",
                "tempat_tanggal": data.get('tempat_tanggal', ''),
                "penandatangan": {
                    "jabatan": data.get('penandatangan_jabatan', ''),
                    "nama": data.get('penandatangan_nama', '')
                }
            }
        }
    }
    
    # Save JSON
    output_path = Path(output_json)
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, indent=2, ensure_ascii=False)
    print(f"  📄 Saved: {output_path}")
    
    # Save markdown
    md_path = output_path.parent / f"{Path(image_path).stem}_md.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# SPTJB - {full_data['content']['nomor_surat']}\n\n")
        f.write(f"**Uraian**: {full_data['content']['uraian']}\n\n")
        f.write(f"**Klasifikasi**: {full_data['content']['klasifikasi']}\n\n")
        f.write(f"**Satker**: {full_data['content']['satker']}\n\n")
        f.write("## Rincian Pembayaran\n\n")
        for item in table_items:
            f.write(f"### {item.get('no')}. {item.get('penerima', 'N/A')}\n")
            f.write(f"**Akun**: {item.get('akun', '')} | **Jumlah**: Rp {item.get('jumlah_rp', 0):,}\n\n")
            f.write(f"**Uraian**: {item.get('uraian', '')}\n\n")
            if item.get('potongan_kehadiran_maret_rp', 0) > 0:
                f.write(f"**Potongan Kehadiran Maret**: Rp {item['potongan_kehadiran_maret_rp']:,}\n\n")
            if item.get('potongan_peh_rp', 0) > 0:
                f.write(f"**Potongan PEH**: Rp {item['potongan_peh_rp']:,}\n\n")
    
    # Summary
    sptjb = full_data['content']['sptjb']
    print(f"  📋 {sptjb['nomor']}")
    print(f"  💰 {len(table_items)} items, Total: Rp {total_jumlah:,}")
    for item in table_items[:3]:
        print(f"     #{item.get('no')}: {item.get('penerima', 'N/A')[:40]} | Rp {item.get('jumlah_rp', 0):,}")
    if len(table_items) > 3:
        print(f"     ... and {len(table_items) - 3} more items")
    
    return full_data


def main():
    """Process semua gambar di arsip-2025/scan/"""
    scan_dir = Path("arsip-2025/scan")
    extracted_dir = Path("arsip-extracted")
    extracted_dir.mkdir(exist_ok=True)
    
    png_files = sorted(scan_dir.glob("*.png"))
    if not png_files:
        print("❌ No PNG files found!")
        return
    
    print(f"📁 Found {len(png_files)} PNG files")
    print(f"🤖 Using Ollama Llava vision model")
    
    # Test dulu apakah Ollama jalan
    try:
        result = subprocess.run(
            ["curl", "-s", f"{OLLAMA_URL}/api/tags"],
            capture_output=True, text=True, timeout=5
        )
        tags = json.loads(result.stdout)
        models = [m['name'] for m in tags.get('models', [])]
        print(f"📡 Available models: {models}")
        
        if not any('llava' in m or 'mllama' in m.lower() for m in models):
            print("⚠️  Llava model not found. Pulling llava...")
            subprocess.run(["ollama", "pull", "llava"], check=True)
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running on localhost:11434")
        return
    
    success = 0
    for png_file in png_files:
        output_json = extracted_dir / f"{png_file.stem}_structured.json"
        try:
            if process_image_ollama(png_file, output_json):
                success += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ Ollama OCR complete: {success}/{len(png_files)} files")


if __name__ == "__main__":
    main()