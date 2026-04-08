#!/usr/bin/env python3
"""
Batch OCR + NLP + LLM extraction untuk semua file PNG di arsip-2025/scan.
Menggunakan PaddleOCR, NLP processor, dan GROQ Qwen3-32b untuk ekstraksi.
"""
import os
import sys
import json
import glob
from pathlib import Path

# Add mcp-unified to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-unified"))

from services.ocr.service import OCREngine
from services.ocr.nlp_processor import get_nlp_processor
from services.ocr.context_refiner import get_context_refiner

# Configuration
SCAN_DIR = Path(__file__).parent / "arsip-2025" / "scan"
OUTPUT_DIR = Path(__file__).parent / "arsip-extracted"
OUTPUT_DIR.mkdir(exist_ok=True)

# Initialize engines
print("🔧 Initializing OCR engine...")
ocr_engine = OCREngine()
nlp = get_nlp_processor()
refiner = get_context_refiner()

print(f"📁 Scanning directory: {SCAN_DIR}")
print(f"💾 Output directory: {OUTPUT_DIR}")

# Find all PNG files
png_files = sorted(glob.glob(str(SCAN_DIR / "*.png")))
print(f"📊 Found {len(png_files)} PNG files")

results = []
for i, png_file in enumerate(png_files, 1):
    filename = Path(png_file).stem
    print(f"\n{'='*60}")
    print(f"[{i}/{len(png_files)}] Processing: {filename}.png")
    print(f"{'='*60}")
    
    try:
        # Step 1: OCR
        print("  🔍 OCR extraction...")
        ocr_result = ocr_engine.run_ocr(png_file)
        raw_text = ocr_result.get("full_text", "")
        confidence = 0.0
        if ocr_result.get("lines"):
            confidence = sum(line.get("score", 0) for line in ocr_result["lines"]) / len(ocr_result["lines"])
        print(f"  ✓ OCR completed (confidence: {confidence:.2f})")
        
        # Step 2: NLP
        print("  📝 NLP processing...")
        normalized = nlp.normalize(raw_text)
        entities = nlp.extract_entities(normalized)
        quality = nlp.assess_quality({"lines": [{"text": line, "score": confidence} for line in normalized.split("\n")]})
        print(f"  ✓ NLP completed (quality: {quality['quality_score']:.2f})")
        
        # Step 3: LLM extraction (SPM)
        print("  🤖 LLM SPM extraction...")
        spm_data = refiner.extract_spm_document(normalized)
        print(f"  ✓ SPM extracted: {spm_data.get('nomor', 'N/A')}")
        
        # Step 4: Context
        print("  📋 Context extraction...")
        context = refiner.extract_context(normalized)
        print(f"  ✓ Context: {context.get('jenis_dokumen', 'N/A')}")
        
        # Build result
        result = {
            "key": f"{filename}_structured",
            "content": {
                "doc_id": filename,
                "doc_type": context.get("jenis_dokumen", "SPM"),
                "nomor_surat": entities.get("nomor_surat", spm_data.get("nomor", "")),
                "satker": spm_data.get("satuan_kerja", {}).get("nama", entities.get("nama_satuan_kerja", "")),
                "uraian": raw_text[:200],
                "klasifikasi": spm_data.get("klasifikasi_belanja", ""),
                "extraction_date": "2026-04-02",
                "raw_ocr_full": raw_text,
                "ocr_confidence": confidence,
                "nlp_quality": quality["quality_score"],
                "sptjb": spm_data
            }
        }
        
        # Save to JSON
        output_file = OUTPUT_DIR / f"{filename}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"  💾 Saved: {output_file.name}")
        results.append({
            "file": filename,
            "status": "success",
            "nomor": spm_data.get("nomor", ""),
            "confidence": confidence,
            "quality": quality["quality_score"]
        })
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append({
            "file": filename,
            "status": "error",
            "error": str(e)
        })

# Summary
print(f"\n{'='*60}")
print("📊 EXTRACTION SUMMARY")
print(f"{'='*60}")
print(f"Total files: {len(png_files)}")
print(f"Successful: {sum(1 for r in results if r['status'] == 'success')}")
print(f"Failed: {sum(1 for r in results if r['status'] == 'error')}")

# Save summary
summary_file = OUTPUT_DIR / "extraction_summary.json"
with open(summary_file, "w", encoding="utf-8") as f:
    json.dump({
        "total": len(png_files),
        "successful": sum(1 for r in results if r['status'] == 'success'),
        "failed": sum(1 for r in results if r['status'] == 'error'),
        "results": results
    }, f, indent=2, ensure_ascii=False)

print(f"\n💾 Summary saved: {summary_file}")
print("✅ Extraction complete!")