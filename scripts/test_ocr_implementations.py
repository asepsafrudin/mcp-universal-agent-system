#!/usr/bin/env python3
"""
Test Suite untuk OCR Implementations
Menguji PaddleOCR Optimized dan Vision OCR Local
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

def create_test_image() -> str:
    """Create test image dengan text"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create test invoice image
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to load font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except:
            font = ImageFont.load_default()
            font_bold = font
        
        # Draw test text
        text_content = """INVOICE #001
Date: 2024-01-15
Vendor: PT Example Indonesia
Address: Jl. Sudirman No. 123, Jakarta

Items:
1. Product A - Rp 500.000
2. Product B - Rp 750.000
3. Service C - Rp 250.000

Subtotal: Rp 1.500.000
Tax (10%): Rp 150.000
Total: Rp 1.650.000

Email: vendor@example.com
Phone: 021-1234567"""
        
        draw.text((50, 30), "INVOICE", fill='black', font=font_bold)
        draw.text((50, 80), text_content, fill='black', font=font)
        
        # Save
        test_path = "/tmp/test_invoice_ocr.jpg"
        img.save(test_path, quality=95)
        print(f"✅ Test image created: {test_path}")
        return test_path
        
    except ImportError:
        print("❌ PIL not installed. Install: pip install Pillow")
        return None
    except Exception as e:
        print(f"❌ Failed to create test image: {e}")
        return None


def test_paddle_ocr_optimized():
    """Test PaddleOCR Optimized"""
    print("\n" + "="*70)
    print("🧪 TESTING: PaddleOCR Optimized")
    print("="*70)
    
    try:
        from paddle_ocr_optimized import OptimizedPaddleOCRRouter, OptimizedConfig
        
        # Create test image
        test_image = create_test_image()
        if not test_image:
            print("❌ Cannot run test without test image")
            return False
        
        # Setup test environment
        test_input = Path("/tmp/test_ocr_input")
        test_output = Path("/tmp/test_ocr_output_paddle")
        test_input.mkdir(exist_ok=True)
        test_output.mkdir(exist_ok=True, parents=True)
        
        # Copy test image
        import shutil
        shutil.copy(test_image, test_input / "test_invoice.jpg")
        
        # Initialize router dengan config test
        config = OptimizedConfig()
        config.MAX_WORKERS = 1
        config.BATCH_SIZE = 1
        config.CACHE_ENABLED = False  # Disable cache untuk test
        config.CONFIDENCE_THRESHOLD = 0.6  # Lower threshold untuk test
        
        router = OptimizedPaddleOCRRouter(
            input_dir=str(test_input),
            output_dir=str(test_output),
            config=config
        )
        
        print(f"\n📁 Input: {test_input}")
        print(f"📁 Output: {test_output}")
        print(f"🎯 Confidence Threshold: {config.CONFIDENCE_THRESHOLD}")
        print(f"⚙️  Workers: {config.MAX_WORKERS}")
        
        # Run test
        print("\n⏳ Running OCR test...")
        import time
        start = time.time()
        
        results = router.process_batch()
        
        elapsed = time.time() - start
        
        # Verify results
        if not results:
            print("❌ No results returned")
            return False
        
        result = results[0]
        print(f"\n✅ Test completed in {elapsed:.2f}s")
        print(f"📄 File: {result.filename}")
        print(f"📊 Success: {result.success}")
        print(f"📈 Confidence: {result.confidence:.2f}")
        print(f"📄 Text Length: {len(result.text)} chars")
        print(f"🔤 Engine: {result.engine}")
        
        # Check content
        text_lower = result.text.lower()
        checks = {
            'invoice': 'invoice' in text_lower,
            'rp': 'rp' in text_lower or '500' in text_lower,
            'date': '2024' in text_lower or 'date' in text_lower,
        }
        
        print(f"\n📋 Content Checks:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
        
        all_passed = result.success and all(checks.values())
        
        if all_passed:
            print(f"\n✅ PaddleOCR Optimized TEST PASSED")
        else:
            print(f"\n⚠️  PaddleOCR Optimized TEST PARTIAL")
            print(f"   Text extracted: {result.text[:200]}...")
        
        # Cleanup
        shutil.rmtree(test_input, ignore_errors=True)
        shutil.rmtree(test_output, ignore_errors=True)
        
        return result.success
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_vision_ocr_local():
    """Test Vision OCR Local"""
    print("\n" + "="*70)
    print("🧪 TESTING: Vision OCR Local")
    print("="*70)
    
    try:
        from vision_ocr_local import LocalVisionOCRRouter
        
        # Create test image
        test_image = create_test_image()
        if not test_image:
            print("❌ Cannot run test without test image")
            return False
        
        # Setup test environment
        test_input = Path("/tmp/test_vision_input")
        test_output = Path("/tmp/test_vision_output")
        test_input.mkdir(exist_ok=True)
        test_output.mkdir(exist_ok=True, parents=True)
        
        # Copy test image
        import shutil
        shutil.copy(test_image, test_input / "test_invoice.jpg")
        
        # Check Ollama availability
        print("\n🔍 Checking Ollama availability...")
        import subprocess
        try:
            result = subprocess.run(
                ['curl', '-s', 'http://localhost:11434/api/tags'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                print("⚠️  Ollama not available. Skipping vision test.")
                print("   Please start Ollama: ollama serve")
                return None  # Skip, not fail
        except:
            print("⚠️  Cannot check Ollama. Skipping vision test.")
            return None
        
        # Initialize router
        router = LocalVisionOCRRouter(
            input_dir=str(test_input),
            output_dir=str(test_output),
            ollama_model="llava",
            vision_confidence_threshold=0.5,  # Lower untuk test
            use_enhancement=True
        )
        
        print(f"\n📁 Input: {test_input}")
        print(f"📁 Output: {test_output}")
        print(f"🤖 Vision Model: llava")
        print(f"🎯 Vision Threshold: 0.5")
        
        # Run test
        print("\n⏳ Running Vision OCR test (this may take 30-60s)...")
        import time
        start = time.time()
        
        results = await router.process_batch()
        
        elapsed = time.time() - start
        
        # Verify results
        if not results:
            print("❌ No results returned")
            return False
        
        result = results[0]
        print(f"\n✅ Test completed in {elapsed:.2f}s")
        print(f"📄 File: {result.filename}")
        print(f"📊 Success: {result.success}")
        print(f"📈 Confidence: {result.confidence:.2f}")
        print(f"📄 Text Length: {len(result.text)} chars")
        print(f"🔍 Method: {result.primary_method}")
        print(f"🤖 Vision Confidence: {result.vision_confidence:.2f}")
        print(f"🔤 OCR Confidence: {result.ocr_confidence:.2f}")
        
        # Check structured data
        print(f"\n📋 Structured Data:")
        structured = result.structured_data
        print(f"   Dates found: {len(structured.get('dates', []))}")
        print(f"   Amounts found: {len(structured.get('amounts', []))}")
        print(f"   Numbers found: {len(structured.get('numbers', []))}")
        
        # Check content
        text_lower = result.text.lower()
        checks = {
            'invoice': 'invoice' in text_lower,
            'amount': 'rp' in text_lower or '500' in text_lower or '1.500' in text_lower,
        }
        
        print(f"\n📋 Content Checks:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
        
        all_passed = result.success
        
        if all_passed:
            print(f"\n✅ Vision OCR Local TEST PASSED")
        else:
            print(f"\n⚠️  Vision OCR Local TEST PARTIAL")
        
        print(f"\n📝 Extracted Text Preview:")
        print(f"   {result.text[:300]}...")
        
        # Cleanup
        shutil.rmtree(test_input, ignore_errors=True)
        shutil.rmtree(test_output, ignore_errors=True)
        
        return result.success
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_dependencies():
    """Check required dependencies"""
    print("="*70)
    print("📦 CHECKING DEPENDENCIES")
    print("="*70)
    
    deps = {
        'PIL': False,
        'paddleocr': False,
        'psutil': False,
        'fitz': False,
        'numpy': False,
        'cv2': False,
    }
    
    # Check each dependency
    try:
        from PIL import Image
        deps['PIL'] = True
        print("✅ Pillow (PIL)")
    except:
        print("❌ Pillow (PIL) - Install: pip install Pillow")
    
    try:
        from paddleocr import PaddleOCR
        deps['paddleocr'] = True
        print("✅ PaddleOCR")
    except:
        print("❌ PaddleOCR - Install: pip install paddleocr paddlepaddle")
    
    try:
        import psutil
        deps['psutil'] = True
        print("✅ psutil")
    except:
        print("❌ psutil - Install: pip install psutil")
    
    try:
        import fitz
        deps['fitz'] = True
        print("✅ PyMuPDF (fitz)")
    except:
        print("❌ PyMuPDF - Install: pip install PyMuPDF")
    
    try:
        import numpy as np
        deps['numpy'] = True
        print("✅ numpy")
    except:
        print("❌ numpy - Install: pip install numpy")
    
    try:
        import cv2
        deps['cv2'] = True
        print("✅ OpenCV (cv2)")
    except:
        print("❌ OpenCV - Install: pip install opencv-python")
    
    all_ok = all(deps.values())
    
    if not all_ok:
        print("\n⚠️  Some dependencies missing. Install with:")
        print("   pip install Pillow paddleocr paddlepaddle psutil PyMuPDF numpy opencv-python")
    
    return all_ok


async def main():
    """Main test runner"""
    print("\n" + "="*70)
    print("🧪 OCR IMPLEMENTATION TEST SUITE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot run tests without all dependencies")
        return
    
    # Run tests
    results = {
        'paddle_ocr': False,
        'vision_ocr': False
    }
    
    # Test 1: PaddleOCR Optimized
    try:
        results['paddle_ocr'] = test_paddle_ocr_optimized()
    except Exception as e:
        print(f"\n❌ PaddleOCR test error: {e}")
        results['paddle_ocr'] = False
    
    # Test 2: Vision OCR Local
    try:
        vision_result = await test_vision_ocr_local()
        results['vision_ocr'] = vision_result if vision_result is not None else False
    except Exception as e:
        print(f"\n❌ Vision OCR test error: {e}")
        results['vision_ocr'] = False
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   Check logs above for details")
    
    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
