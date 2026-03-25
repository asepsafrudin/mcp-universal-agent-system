#!/usr/bin/env python3
"""
Script OCR untuk memproses draft SE Sensus Ekonomi 2026
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def check_dependencies():
    """Cek apakah dependensi tersedia"""
    try:
        from paddleocr import PaddleOCR
        import fitz  # PyMuPDF
        return True
    except ImportError as e:
        print(f"❌ Dependensi tidak tersedia: {e}")
        print("Install dengan: pip install paddleocr PyMuPDF")
        return False

def extract_text_with_ocr(pdf_path, output_path):
    """Ekstrak teks dari PDF gambar menggunakan PaddleOCR"""
    try:
        from paddleocr import PaddleOCR
        import fitz  # PyMuPDF
        
        print(f"📄 Memproses: {pdf_path.name}")
        
        # Inisialisasi PaddleOCR
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang='id'  # Bahasa Indonesia
        )
        
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
            
            # OCR dengan PaddleOCR (menggunakan metode predict)
            result = ocr.predict(str(temp_img))
            
            # Ekstrak teks dari hasil OCR
            page_text = []
            if hasattr(result, 'text'):
                # Hasil langsung berupa string
                page_text.append(result.text)
            elif isinstance(result, list):
                for item in result:
                    if isinstance(item, tuple) and len(item) >= 2:
                        text = item[0]
                        page_text.append(text)
                    elif hasattr(item, 'text'):
                        page_text.append(item.text)
            
            all_text.append(f"\n--- Halaman {page_num + 1} ---\n")
            all_text.append("\n".join(page_text))
            
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
    print("OCR DRAFT SE SENSUS EKONOMI 2026")
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
    success, result = extract_text_with_ocr(pdf_path, output_path)
    
    if success:
        print(f"\n{'=' * 80}")
        print("HASIL OCR:")
        print("=" * 80)
        print(result[:2000] + "..." if len(result) > 2000 else result)
        print(f"\n{'=' * 80}")
        print(f"Total karakter: {len(result)}")
        print(f"File output: {output_path}")
    else:
        print(f"\n❌ Gagal: {result}")

if __name__ == "__main__":
    main()
