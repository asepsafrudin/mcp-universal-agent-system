#!/usr/bin/env python3
"""Uji coba 1 file menggunakan Ollama OCR"""
import sys
sys.path.append('.')
from ollama_ocr import process_image_ollama
from pathlib import Path
from PIL import Image

# Ambil 1 file pertama
png_files = sorted(Path("arsip-2025/scan").glob("*.png"))
target = png_files[0]
output_json = f"test_result_{target.stem}.json"

print(f"=== UJI COBA OLLAMA OCR (1 FILE) ===")
print(f"📄 File: {target.name}")
print(f"📏 Ukuran: {Image.open(target).size}")
print(f"💾 Output: {output_json}")
print("-" * 50)

try:
    result = process_image_ollama(str(target), output_json)
    print("\n✅ TESTING SELESAI!")
    print("\n📊 HASIL EKSTRAKSI (JSON Preview):")
    if result and 'content' in result:
        sptjb = result['content'].get('sptjb', {})
        print(f"   Nomor Surat : {sptjb.get('nomor', '-')}")
        print(f"   Satker      : {sptjb.get('satuan_kerja', {}).get('nama', '-')[:40]}...")
        print(f"   DIPA        : {sptjb.get('dipa', {})}")
        print(f"   Klasifikasi : {sptjb.get('klasifikasi_belanja', '-')}")
        print(f"   Items       : {len(sptjb.get('rincian_pembayaran', []))} baris")
        
        rincian = sptjb.get('rincian_pembayaran', [])
        total_rp = sptjb.get('total_jumlah_rp', 0)
        print(f"\n🧾 Rincian Pembayaran:")
        for item in rincian:
            print(f"   #{item['no']} | {item['akun']} | {item['penerima'][:25]}... | Rp {item['jumlah_rp']:,}")
        print(f"   💰 TOTAL JUMLAH: Rp {total_rp:,}")
        
        print(f"\n👤 Penandatangan:")
        pen = sptjb.get('penandatangan', {})
        print(f"   Nama    : {pen.get('nama', '-')}")
        print(f"   Jabatan : {pen.get('jabatan', '-')}")
        
    else:
        print("❌ Gagal mengekstrak data.")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()