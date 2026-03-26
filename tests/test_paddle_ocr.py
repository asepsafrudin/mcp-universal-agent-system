#!/usr/bin/env python3
"""Test PaddleOCR API"""
import os
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['OMP_NUM_THREADS'] = '1'

import fitz
from paddleocr import PaddleOCR

# Convert PDF
pdf_path = 'input/0161-UND-PUU-2026.pdf'
doc = fitz.open(pdf_path)
page = doc[0]
pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
img_path = '/tmp/test_page.png'
pix.save(img_path)
doc.close()
print(f"✅ Converted to {img_path}")

# Init OCR
ocr = PaddleOCR(
    text_detection_model_name='PP-OCRv5_server_det',
    text_recognition_model_name='en_PP-OCRv5_mobile_rec',
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False
)
print("✅ OCR initialized")

# Test predict
result = ocr.predict(img_path)
print(f"\n📊 Result type: {type(result)}")
print(f"📊 Result: {result}")

# Parse result
if result and len(result) > 0:
    print(f"\n✅ OCR SUCCESS!")
    print(f"Found {len(result)} text blocks")
    for i, item in enumerate(result[:3]):
        print(f"  {i+1}. {item}")
else:
    print("\n⚠️ No text found")

# Cleanup
os.remove(img_path)
