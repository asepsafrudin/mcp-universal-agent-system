#!/usr/bin/env python3
"""
Script OCR untuk memproses draft SE Sensus Ekonomi 2026
Menggunakan Tesseract OCR
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def check_dependencies():
    """Cek apakah dependensi tersedia"""
    try:
        import pytesseract
        from PIL import Image
        import fitz  # PyMuPDF
        return True
    except ImportError as e:
        print(f"❌ Dependensi tidak tersedia: {e}")
        print("Install dengan: pip install pytesseract pillow PyMuPDF")
        return False

def extract_text_with_tesseract(pdf_path, output_path):
    """Ekstrak teks dari PDF gambar menggunakan Tesseract OCR"""
    try:
        import pytesseract
        from PIL import Image
        import fitz  # PyMuPDF
        
        print(f"📄 Memproses: {pdf_path.name}")
        
        # Buka PDF dan konversi ke gambar
        pdf_document = fitz.open(pdf_path)
        all_text = []
        
        for page_num in range(len(pdf_document)):
            print(f"  📝 Halaman {page_num + 1}/{len(pdf_document)}")
            
            # Render halaman ke gambar
            page = pdf_document[page_num]
            mat = fitz.Matrix(2, 2)  # Scale 2x untuk kualitas lebih baik
            pix = page.get_pixmap(matrix=mat)
            
            # Simpan gambar sementara
            temp_img = output_path.parent / f"temp_page{page_num}.png"
            pix.save(str(temp_img))
            
            # OCR dengan Tesseract
            img = Image.open(temp_img)
            text = pytesseract.image_to_string(img, lang='ind')
            
            all_text.append(f"\n--- Halaman {page_num + 1} ---\n")
            all_text.append(text)
            
            # Hapus gambar sementara
            if temp_img.exists():
                temp_img.unlink()
        
        pdf_document.close()
        
        # Gabungkan semua teks
        full_text = "\n".join(all_text)
        
        # Simpan hasil
        output_path.write_text(full_text, encoding='utf-8')
        
        print(f"✅ Berhasil! Hasil disimpan di: {output_path}")
        return True, full_text
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, str(e)

def main():
    print("=" * 80)
    print("OCR DRAFT SE SENSUS EKONOMI 2026 - TESSERACT")
    print("=" * 80)
    print(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Cek dependensi
    if not check_dependencies():
        return
    
    # Path file
    base_dir = Path("/home/aseps/MCP/google_drive/SE dukungan Sensus Ekonomi")
    pdf_file = "draft SE sensus ekonomi 2026.pdf"
    pdf_path = base_dir / pdf_file
    
    if not pdf_path.exists():
        print(f"❌ File tidak ditemukan: {pdf_path}")
        return
    
    # Output path
    output_path = base_dir / "draft_se_ocr_result.txt"
    
    # Proses OCR
    success, result = extract_text_with_tesseract(pdf_path, output_path)
    
    if success:
        print(f"\n{'=' * 80}")
        print("HASIL OCR (2000 karakter pertama):")
        print("=" * 80)
        print(result[:2000] + "..." if len(result) > 2000 else result)
        print(f"\n{'=' * 80}")
        print(f"Total karakter: {len(result)}")
        print(f"File output: {output_path}")
    else:
        print(f"\n❌ Gagal: {result}")

if __name__ == "__main__":
    main()
