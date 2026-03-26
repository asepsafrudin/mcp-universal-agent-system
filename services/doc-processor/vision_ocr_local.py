#!/usr/bin/env python3
"""
Vision OCR with Local Fallback - Fokus ke Vision Model + Local OCR

Fitur:
- Vision Model (Ollama) sebagai primary
- Local PaddleOCR sebagai fallback
- No external API calls (100% local processing)
- Structured data extraction support
- Image enhancement pipeline
- Confidence scoring

Author: AI Assistant
Version: 1.0.0 - Local Only Edition
"""

import os
import sys
import json
import time
import asyncio
import base64
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class VisionOCRResult:
    """Hasil Vision OCR"""
    filename: str
    text: str
    structured_data: Dict
    confidence: float
    primary_method: str  # 'vision', 'ocr_fallback', 'hybrid'
    vision_confidence: float
    ocr_confidence: float
    processing_time: float
    success: bool
    timestamp: str


class LocalVisionOCRRouter:
    """
    Vision OCR Router dengan 100% local processing.
    Primary: Vision Model (Ollama)
    Fallback: Local PaddleOCR
    """
    
    def __init__(
        self,
        input_dir: str = "input",
        output_dir: str = "processed/vision_ocr_local",
        ollama_model: str = "llava",
        vision_confidence_threshold: float = 0.7,
        ocr_confidence_threshold: float = 0.75,
        use_enhancement: bool = True
    ):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.ollama_model = ollama_model
        self.vision_threshold = vision_confidence_threshold
        self.ocr_threshold = ocr_confidence_threshold
        self.use_enhancement = use_enhancement
        
        # Initialize PaddleOCR (lazy load)
        self.paddleocr = None
        
        # Cache
        self.cache_dir = self.output_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
    
    def _init_paddleocr(self):
        """Lazy initialization PaddleOCR"""
        if self.paddleocr is None:
            try:
                from paddleocr import PaddleOCR
                logger.info("🔄 Initializing PaddleOCR (fallback)...")
                self.paddleocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='en',
                    use_gpu=False,
                    show_log=False,
                    enable_mkldnn=True
                )
                logger.info("✅ PaddleOCR fallback ready")
            except Exception as e:
                logger.error(f"❌ PaddleOCR init failed: {e}")
                self.paddleocr = None
    
    def _get_cache_key(self, file_path: Path, method: str) -> str:
        """Generate cache key"""
        stat = file_path.stat()
        content = f"{file_path.name}:{stat.st_size}:{stat.st_mtime}:{method}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached(self, file_path: Path, method: str) -> Optional[Dict]:
        """Get cached result"""
        cache_key = self._get_cache_key(file_path, method)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def _save_cached(self, file_path: Path, method: str, result: Dict):
        """Save to cache"""
        cache_key = self._get_cache_key(file_path, method)
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
        except:
            pass
    
    def _enhance_image(self, image_path: Path) -> Path:
        """Enhance image quality untuk vision model"""
        if not self.use_enhancement:
            return image_path
        
        try:
            from PIL import Image, ImageEnhance, ImageFilter
            
            with Image.open(image_path) as img:
                # Convert ke RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Enhance contrast
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.3)
                
                # Enhance sharpness
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.5)
                
                # Save enhanced
                enhanced_path = self.output_dir / f"{image_path.stem}_enhanced.jpg"
                img.save(enhanced_path, quality=95)
                
                logger.info(f"✨ Enhanced: {image_path.name}")
                return enhanced_path
                
        except Exception as e:
            logger.warning(f"⚠️ Enhancement failed: {e}")
            return image_path
    
    async def _call_ollama_vision(self, image_path: Path, prompt: str) -> Tuple[str, float]:
        """Call Ollama Vision model"""
        try:
            import aiohttp
            
            # Convert image to base64
            with open(image_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            # Prepare payload
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            }
            
            # Call Ollama API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'http://localhost:11434/api/generate',
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        text = data.get('response', '')
                        
                        # Calculate confidence berdasarkan response quality
                        confidence = self._calculate_vision_confidence(text)
                        
                        return text, confidence
                    else:
                        return "", 0.0
                        
        except Exception as e:
            logger.error(f"❌ Ollama vision error: {e}")
            return "", 0.0
    
    def _calculate_vision_confidence(self, text: str) -> float:
        """Calculate confidence score dari vision response"""
        confidence = 0.5
        
        # Length factor
        length = len(text)
        if length > 500:
            confidence += 0.3
        elif length > 200:
            confidence += 0.2
        elif length > 50:
            confidence += 0.1
        
        # Uncertainty penalty
        uncertainty_words = ["maybe", "perhaps", "possibly", "unclear", "not sure"]
        for word in uncertainty_words:
            if word in text.lower():
                confidence -= 0.05
        
        # Specificity bonus
        import re
        if re.search(r'\d+', text):
            confidence += 0.05
        
        return max(0.0, min(1.0, confidence))
    
    def _ocr_with_paddle(self, image_path: Path) -> Tuple[str, float]:
        """OCR dengan local PaddleOCR"""
        self._init_paddleocr()
        
        if self.paddleocr is None:
            return "", 0.0
        
        try:
            result = self.paddleocr.ocr(str(image_path), cls=True)
            
            texts = []
            confidences = []
            
            if result and result[0]:
                for line in result[0]:
                    if line:
                        texts.append(line[1][0])
                        confidences.append(line[1][1])
            
            full_text = '\n'.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return full_text, avg_confidence
            
        except Exception as e:
            logger.error(f"❌ PaddleOCR error: {e}")
            return "", 0.0
    
    def _extract_structured_data(self, text: str) -> Dict:
        """Extract structured data dari text"""
        import re
        
        structured = {
            'raw_text': text,
            'dates': re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text),
            'amounts': re.findall(r'[\d.,]+\s*(?:Rp|IDR|USD|\$)', text),
            'numbers': re.findall(r'\d+', text),
            'emails': re.findall(r'[\w.-]+@[\w.-]+\.\w+', text),
            'phones': re.findall(r'[\d\-\+\(\)\s]{10,}', text)
        }
        
        return structured
    
    async def process_single_file(self, file_path: Path) -> VisionOCRResult:
        """Process single file dengan Vision + Local OCR fallback"""
        start_time = time.time()
        
        # Check cache
        cached = self._get_cached(file_path, "vision_ocr")
        if cached:
            return VisionOCRResult(
                filename=file_path.name,
                text=cached.get('text', ''),
                structured_data=cached.get('structured', {}),
                confidence=cached.get('confidence', 0),
                primary_method='cached',
                vision_confidence=0,
                ocr_confidence=0,
                processing_time=0,
                success=True,
                timestamp=datetime.now().isoformat()
            )
        
        # Enhance image
        image_path = self._enhance_image(file_path)
        
        # Method 1: Vision Model (Primary)
        logger.info(f"🔍 Vision analysis: {file_path.name}")
        vision_prompt = """Extract all text from this image accurately.
Preserve the layout and formatting.
If there are tables, extract them in structured format.
Return the extracted text only."""
        
        vision_text, vision_confidence = await self._call_ollama_vision(image_path, vision_prompt)
        
        # If vision confidence is good, use vision result
        if vision_confidence >= self.vision_threshold and len(vision_text) > 50:
            structured = self._extract_structured_data(vision_text)
            
            result = VisionOCRResult(
                filename=file_path.name,
                text=vision_text,
                structured_data=structured,
                confidence=vision_confidence,
                primary_method='vision',
                vision_confidence=vision_confidence,
                ocr_confidence=0,
                processing_time=time.time() - start_time,
                success=True,
                timestamp=datetime.now().isoformat()
            )
            
            # Cache result
            self._save_cached(file_path, "vision_ocr", {
                'text': vision_text,
                'structured': structured,
                'confidence': vision_confidence
            })
            
            logger.info(f"✅ Vision success (confidence: {vision_confidence:.2f})")
            return result
        
        # Method 2: Local OCR Fallback
        logger.info(f"🔄 Vision low confidence ({vision_confidence:.2f}), trying local OCR...")
        ocr_text, ocr_confidence = self._ocr_with_paddle(image_path)
        
        # Combine atau pilih yang terbaik
        if ocr_confidence >= self.ocr_threshold:
            # Use OCR result
            final_text = ocr_text
            final_confidence = ocr_confidence
            method = 'ocr_fallback'
        elif len(vision_text) > len(ocr_text):
            # Vision has more content
            final_text = vision_text
            final_confidence = vision_confidence
            method = 'vision_low_confidence'
        else:
            # Combine both
            final_text = f"[Vision Analysis]\n{vision_text}\n\n[OCR Text]\n{ocr_text}"
            final_confidence = max(vision_confidence, ocr_confidence)
            method = 'hybrid'
        
        structured = self._extract_structured_data(final_text)
        
        result = VisionOCRResult(
            filename=file_path.name,
            text=final_text,
            structured_data=structured,
            confidence=final_confidence,
            primary_method=method,
            vision_confidence=vision_confidence,
            ocr_confidence=ocr_confidence,
            processing_time=time.time() - start_time,
            success=len(final_text) > 10,
            timestamp=datetime.now().isoformat()
        )
        
        # Cache
        if result.success:
            self._save_cached(file_path, "vision_ocr", {
                'text': final_text,
                'structured': structured,
                'confidence': final_confidence
            })
        
        logger.info(f"✅ Processed with {method} (confidence: {final_confidence:.2f})")
        return result
    
    async def process_batch(self) -> List[VisionOCRResult]:
        """Process batch files"""
        all_files = []
        all_files.extend(list(self.input_dir.glob("*.pdf")))
        all_files.extend(list(self.input_dir.glob("*.png")))
        all_files.extend(list(self.input_dir.glob("*.jpg")))
        all_files.extend(list(self.input_dir.glob("*.jpeg")))
        
        # Filter processed
        processed = set()
        results_file = self.output_dir / "results.json"
        if results_file.exists():
            try:
                with open(results_file) as f:
                    data = json.load(f)
                    processed = {r['filename'] for r in data.get('results', [])}
            except:
                pass
        
        pending = [f for f in all_files if f.name not in processed]
        
        if not pending:
            logger.info("✅ No pending files")
            return []
        
        logger.info(f"🚀 Processing {len(pending)} files with Vision OCR (100% local)")
        
        results = []
        for i, file_path in enumerate(pending, 1):
            logger.info(f"📄 [{i}/{len(pending)}] {file_path.name}")
            
            try:
                result = await self.process_single_file(file_path)
                results.append(result)
                
                # Save progress
                self._save_results(results)
                
            except Exception as e:
                logger.error(f"❌ Failed {file_path.name}: {e}")
                results.append(VisionOCRResult(
                    filename=file_path.name,
                    text='',
                    structured_data={},
                    confidence=0,
                    primary_method='failed',
                    vision_confidence=0,
                    ocr_confidence=0,
                    processing_time=0,
                    success=False,
                    timestamp=datetime.now().isoformat()
                ))
        
        return results
    
    def _save_results(self, results: List[VisionOCRResult]):
        """Save results to JSON"""
        try:
            results_file = self.output_dir / "results.json"
            
            with open(results_file, 'w') as f:
                json.dump({
                    'results': [asdict(r) for r in results],
                    'stats': {
                        'total': len(results),
                        'successful': len([r for r in results if r.success]),
                        'by_method': {
                            'vision': len([r for r in results if r.primary_method == 'vision']),
                            'ocr_fallback': len([r for r in results if r.primary_method == 'ocr_fallback']),
                            'hybrid': len([r for r in results if r.primary_method == 'hybrid']),
                            'cached': len([r for r in results if r.primary_method == 'cached'])
                        }
                    },
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
    
    def print_summary(self, results: List[VisionOCRResult]):
        """Print summary"""
        successful = [r for r in results if r.success]
        
        by_method = {}
        for r in successful:
            by_method[r.primary_method] = by_method.get(r.primary_method, 0) + 1
        
        print("\n" + "=" * 70)
        print("🎯 VISION OCR COMPLETE (100% Local)")
        print("=" * 70)
        print(f"📊 Total: {len(results)}")
        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(results) - len(successful)}")
        
        if by_method:
            print(f"\n📈 By Method:")
            for method, count in by_method.items():
                print(f"   {method}: {count}")
        
        if successful:
            times = [r.processing_time for r in successful]
            print(f"\n⏱️  Avg Time: {sum(times)/len(times):.2f}s")
        
        print(f"\n📁 Output: {self.output_dir}")
        print("=" * 70)
    
    async def run(self):
        """Main entry point"""
        print("=" * 70)
        print("🎯 Vision OCR with Local Fallback")
        print("=" * 70)
        print(f"📁 Input: {self.input_dir}")
        print(f"📁 Output: {self.output_dir}")
        print(f"🤖 Vision Model: {self.ollama_model}")
        print(f"🎯 Vision Threshold: ≥{self.vision_threshold}")
        print(f"🔤 OCR Threshold: ≥{self.ocr_threshold}")
        print(f"✨ Enhancement: {'Enabled' if self.use_enhancement else 'Disabled'}")
        print(f"💰 API Cost: $0.00 (100% local processing)")
        print("=" * 70)
        
        results = await self.process_batch()
        self.print_summary(results)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Vision OCR with Local Fallback')
    parser.add_argument('-i', '--input', default='input', help='Input directory')
    parser.add_argument('-o', '--output', default='processed/vision_ocr_local', help='Output directory')
    parser.add_argument('-m', '--model', default='llava', help='Ollama vision model')
    parser.add_argument('--vision-threshold', type=float, default=0.7, help='Vision confidence threshold')
    parser.add_argument('--no-enhancement', action='store_true', help='Disable image enhancement')
    
    args = parser.parse_args()
    
    router = LocalVisionOCRRouter(
        input_dir=args.input,
        output_dir=args.output,
        ollama_model=args.model,
        vision_confidence_threshold=args.vision_threshold,
        use_enhancement=not args.no_enhancement
    )
    
    asyncio.run(router.run())


if __name__ == "__main__":
    main()
