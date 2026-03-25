#!/usr/bin/env python3
"""
Script untuk mengekstrak konten dari draft SKB 3 Menteri
- Draft lama: PDF
- Draft baru: DOCX
"""

import pdfplumber
from docx import Document
import sys

FOLDER = "OneDrive_PUU/PUU_2026/keputusan bersama 3 menteri sarpras olahraga"

def extract_pdf(filepath):
    """Ekstrak teks dari PDF"""
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        return f"Error extracting PDF: {e}"

def extract_docx(filepath):
    """Ekstrak teks dari DOCX"""
    text = ""
    try:
        doc = Document(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        return f"Error extracting DOCX: {e}"

def main():
    print("="*80)
    print("EKSTRAKSI DRAFT SKB 3 MENTERI - DRAFT BARU (DOCX)")
    print("="*80)
    
    draft_baru = f"{FOLDER}/SKB 3 Menteri Final as of 2 Maret 2026 clean_maju TTD.docx"
    content_baru = extract_docx(draft_baru)
    print(content_baru[:15000])  # Print first 15000 chars
    print("\n" + "="*80)
    print("... [dokumen dilanjutkan jika perlu]")
    
    print("\n\n")
    print("="*80)
    print("EKSTRAKSI DRAFT SKB 3 MENTERI - DRAFT LAMA (PDF)")
    print("="*80)
    
    draft_lama = f"{FOLDER}/draft keputusan bersama 3 menteri.pdf"
    content_lama = extract_pdf(draft_lama)
    print(content_lama[:15000])  # Print first 15000 chars
    print("\n" + "="*80)
    print("... [dokumen dilanjutkan jika perlu]")
    
    # Save full content to files for analysis
    with open(f"{FOLDER}/extracted_draft_baru.txt", "w", encoding="utf-8") as f:
        f.write(content_baru)
    
    with open(f"{FOLDER}/extracted_draft_lama.txt", "w", encoding="utf-8") as f:
        f.write(content_lama)
    
    print("\n\n✅ Ekstraksi selesai!")
    print(f"- Draft baru tersimpan di: {FOLDER}/extracted_draft_baru.txt")
    print(f"- Draft lama tersimpan di: {FOLDER}/extracted_draft_lama.txt")

if __name__ == "__main__":
    main()
