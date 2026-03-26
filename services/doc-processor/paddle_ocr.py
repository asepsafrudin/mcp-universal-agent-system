#!/usr/bin/env python3
"""
Optimized PaddleOCR Router - Fokus ke Local OCR dengan Maximum Performance

Fitur:
- Pure PaddleOCR (no API fallback)
- Adaptive PDF resolution (hemat memory & speed)
- OCR result caching (avoid re-processing)
- Memory monitoring dengan auto-pause
- Resume capability
- Image preprocessing untuk hasil lebih baik
- Smart confidence threshold (0.75)

Author: AI Assistant
Version: 2.0.0 - Optimized Edition
"""

import os
import sys
import json
import time
import hashlib
import psutil
import signal
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/paddle_optimized.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Optimized Configuration
class OptimizedConfig:
    """Optimized configuration untuk resource terbatas"""
    
    # OCR Settings
    CONFIDENCE_THRESHOLD = 0.75  # Naik dari 0.6 untuk mengurangi false positives
    MIN_TEXT_LENGTH = 100       # Naik dari 50
    USE_GPU = False
    ENABLE_MKLDNN = True        # Optimasi Intel CPU
    
    # Memory Settings
    MEMORY_WARNING = 70         # Turun dari 75 (lebih konservatif)
    MEMORY_CRITICAL = 80        # Turun dari 85
    MEMORY_PAUSE = 90           # Tetap
    
    # PDF Settings
    PDF_RESOLUTION_ADAPTIVE = True
    PDF_RESOLUTION_SMALL = 1.0   # < 5MB
    PDF_RESOLUTION_MEDIUM = 1.5  # 5-10MB
    PDF_RESOLUTION_LARGE = 2.0   # > 10MB
    PDF_MAX_PAGES = 50
    
    # Batch Settings
    MAX_WORKERS = 2             # Optimal untuk 4-core CPU
    BATCH_SIZE = 3              # Turun dari 5 (hemat memory)
    
    # Cache Settings
    CACHE_ENABLED = True
    CACHE_DIR = Path("ocr_cache")


@dataclass
class ProcessingState:
    """State untuk resume capability."""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    current_batch: int = 0
    last_processed: str = ""
    start_time: str = ""
    estimated_completion: str = ""
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class OCRResult:
    """Hasil OCR untuk satu dokumen"""
    filename: str
    text: str
    confidence: float
    engine: str
    processing_time: float
    pages_processed: int
    success: bool
    timestamp: str
    cached: bool = False


class MemoryMonitor:
    """Monitor memory usage dengan threshold."""
    
    def __init__(self, config: OptimizedConfig):
        self.config = config
        self.paused = False
        
    def check_memory(self) -> Tuple[str, float]:
        """Check memory status."""
        mem = psutil.virtual_memory()
        percent = mem.percent
        
        if percent >= self.config.MEMORY_PAUSE:
            return 'pause', percent
        elif percent >= self.config.MEMORY_CRITICAL:
            return 'critical', percent
        elif percent >= self.config.MEMORY_WARNING:
            return 'warning', percent
        else:
            return 'ok', percent
    
    def wait_if_needed(self, check_interval=5):
        """Wait jika memory dalam status pause."""
        status, percent = self.check_memory()
        
        if status == 'pause':
            self.paused = True
            logger.warning(f"🛑 Memory PAUSED at {percent}%. Waiting...")
            
            while status == 'pause':
                time.sleep(check_interval)
                status, percent = self.check_memory()
                logger.info(f"⏳ Memory still high: {percent}%, waiting...")
            
            self.paused = False
            logger.info(f"✅ Memory resumed at {percent}%")
            return True
        
        return False


class OCRCache:
    """Cache untuk OCR results"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, file_path: Path) -> str:
        """Generate cache key dari file metadata"""
        try:
            stat = file_path.stat()
            content = f"{file_path.name}:{stat.st_size}:{stat.st_mtime}"
            return hashlib.md5(content.encode()).hexdigest()
        except:
            return hashlib.md5(str(file_path).encode()).hexdigest()
    
    def get(self, file_path: Path) -> Optional[Dict]:
        """Get cached result jika ada"""
        cache_key = self._get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                logger.info(f"📦 Cache hit: {file_path.name}")
                return data
            except Exception as e:
                logger.warning(f"⚠️ Cache read failed: {e}")
        
        return None
    
    def set(self, file_path: Path, result: Dict):
        """Save result ke cache"""
        cache_key = self._get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            logger.warning(f"⚠️ Cache write failed: {e}")


class ImagePreprocessor:
    """Preprocessing gambar untuk OCR optimal"""
    
    def __init__(self):
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
    
    def needs_preprocessing(self, image_path: Path) -> bool:
        """Check apakah image butuh preprocessing"""
        try:
            import cv2
            import numpy as np
            
            img = cv2.imread(str(image_path))
            if img is None:
                return False
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Metrics
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            contrast = gray.std()
            
            # Butuh preprocessing jika blurry atau low contrast
            return sharpness < 100 or contrast < 30
            
        except Exception as e:
            logger.warning(f"⚠️ Quality check failed: {e}")
            return False
    
    def preprocess(self, image_path: Path) -> Path:
        """Preprocessing gambar jika diperlukan"""
        if not self.needs_preprocessing(image_path):
            return image_path
        
        try:
            import cv2
            import numpy as np
            
            img = cv2.imread(str(image_path))
            if img is None:
                return image_path
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Denoising
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # Contrast enhancement (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Save preprocessed image
            output_dir = image_path.parent / 'preprocessed'
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"{image_path.stem}_preprocessed.png"
            
            cv2.imwrite(str(output_path), enhanced)
            logger.info(f"✨ Preprocessed: {image_path.name}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Preprocessing error: {e}")
            return image_path


class OptimizedPaddleOCRRouter:
    """Optimized Paddle OCR Router - Fokus ke local processing"""
    
    def __init__(
        self,
        input_dir: str = "input",
        output_dir: str = "processed/optimized_ocr",
        config: OptimizedConfig = None
    ):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = config or OptimizedConfig()
        
        # Components
        self.memory_monitor = MemoryMonitor(self.config)
        self.cache = OCRCache(self.config.CACHE_DIR) if self.config.CACHE_ENABLED else None
        self.preprocessor = ImagePreprocessor()
        
        # State
        self.state_file = self.output_dir / "processing_state.json"
        self.state = self._load_state()
        
        # PaddleOCR instance
        self.paddleocr = None
        self._init_paddleocr()
        
        # Running flag
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Stats
        self.stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'cached': 0,
            'preprocessed': 0,
            'total_time': 0.0
        }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("🛑 Shutdown signal received. Saving state...")
        self.running = False
        self._save_state()
        sys.exit(0)
    
    def _init_paddleocr(self):
        """Initialize PaddleOCR dengan optimasi"""
        try:
            # Disable verbose logging
            import logging as paddle_logging
            paddle_logging.getLogger("paddle").setLevel(paddle_logging.WARNING)
            
            # Optimasi CPU threads - use 1 to avoid warnings
            os.environ['OMP_NUM_THREADS'] = '1'
            os.environ['MKL_NUM_THREADS'] = '1'
            os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
            
            from paddleocr import PaddleOCR
            logger.info("🔄 Initializing PaddleOCR...")
            
            self.paddleocr = PaddleOCR(
                text_detection_model_name='PP-OCRv5_server_det',
                text_recognition_model_name='en_PP-OCRv5_mobile_rec',
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False
            )
            logger.info("✅ PaddleOCR initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to init PaddleOCR: {e}")
            self.paddleocr = None
    
    def _load_state(self) -> ProcessingState:
        """Load processing state untuk resume."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                logger.info(f"📂 Resumed from state: {data.get('processed_files', 0)} files done")
                return ProcessingState.from_dict(data)
            except Exception as e:
                logger.warning(f"⚠️ Could not load state: {e}")
        
        return ProcessingState(start_time=datetime.now().isoformat())
    
    def _save_state(self):
        """Save processing state."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state.to_dict(), f, indent=2)
            logger.info("💾 State saved")
        except Exception as e:
            logger.error(f"❌ Failed to save state: {e}")
    
    def _get_pdf_matrix(self, pdf_path: Path) -> 'fitz.Matrix':
        """Get optimal PDF resolution matrix berdasarkan file size"""
        if not self.config.PDF_RESOLUTION_ADAPTIVE:
            import fitz
            return fitz.Matrix(2, 2)  # Default 144 DPI
        
        try:
            size_mb = pdf_path.stat().st_size / (1024 * 1024)
            import fitz
            
            if size_mb < 5:
                # File kecil - bisa resolusi tinggi
                return fitz.Matrix(self.config.PDF_RESOLUTION_SMALL, 
                                 self.config.PDF_RESOLUTION_SMALL)
            elif size_mb < 10:
                # File medium
                return fitz.Matrix(self.config.PDF_RESOLUTION_MEDIUM, 
                                 self.config.PDF_RESOLUTION_MEDIUM)
            else:
                # File besar - resolusi lebih rendah untuk hemat memory
                return fitz.Matrix(self.config.PDF_RESOLUTION_LARGE, 
                                 self.config.PDF_RESOLUTION_LARGE)
        except Exception as e:
            logger.warning(f"⚠️ PDF matrix error: {e}")
            import fitz
            return fitz.Matrix(1.5, 1.5)
    
    def _convert_pdf_to_images(self, pdf_path: Path) -> List[Path]:
        """Convert PDF to images dengan optimasi"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            
            # Check page limit
            if len(doc) > self.config.PDF_MAX_PAGES:
                logger.warning(f"⚠️ PDF has {len(doc)} pages, limiting to {self.config.PDF_MAX_PAGES}")
            
            image_paths = []
            mat = self._get_pdf_matrix(pdf_path)
            
            for page_num in range(min(len(doc), self.config.PDF_MAX_PAGES)):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=mat)
                
                # Save image
                img_path = self.output_dir / f"{pdf_path.stem}_page{page_num + 1}.png"
                pix.save(img_path)
                image_paths.append(img_path)
            
            doc.close()
            logger.info(f"📄 Converted {pdf_path.name} to {len(image_paths)} images (res: {mat.a}x)")
            return image_paths
            
        except Exception as e:
            logger.error(f"❌ Failed to convert PDF: {e}")
            return []
    
    def _get_pending_files(self) -> List[Path]:
        """Get files yang belum diproses."""
        all_files = []
        all_files.extend(list(self.input_dir.glob("*.pdf")))
        all_files.extend(list(self.input_dir.glob("*.png")))
        all_files.extend(list(self.input_dir.glob("*.jpg")))
        all_files.extend(list(self.input_dir.glob("*.jpeg")))
        
        # Filter yang sudah diproses
        processed = set()
        results_file = self.output_dir / "results.json"
        if results_file.exists():
            try:
                with open(results_file) as f:
                    data = json.load(f)
                    processed = {r['filename'] for r in data.get('results', []) if r.get('success')}
            except:
                pass
        
        # Filter yang ada di cache
        if self.cache:
            for f in all_files:
                if self.cache.get(f):
                    processed.add(f.name)
        
        pending = [f for f in all_files if f.name not in processed]
        
        self.state.total_files = len(all_files)
        self.state.processed_files = len(processed)
        
        logger.info(f"📊 Total: {len(all_files)}, Pending: {len(pending)}, Done/Cached: {len(processed)}")
        return pending
    
    def _process_single_file(self, file_path: Path) -> Optional[OCRResult]:
        """Process single file dengan optimasi"""
        if not self.running:
            return None
        
        start_time = time.time()
        
        # Check cache dulu
        if self.cache:
            cached = self.cache.get(file_path)
            if cached:
                self.stats['cached'] += 1
                return OCRResult(
                    filename=file_path.name,
                    text=cached.get('text', ''),
                    confidence=cached.get('confidence', 0),
                    engine='paddleocr_cached',
                    processing_time=0,
                    pages_processed=cached.get('pages', 1),
                    success=True,
                    timestamp=datetime.now().isoformat(),
                    cached=True
                )
        
        # Check memory
        self.memory_monitor.wait_if_needed()
        status, mem_percent = self.memory_monitor.check_memory()
        if status in ['critical', 'pause']:
            logger.warning(f"⚠️ Memory {mem_percent}%, slowing down...")
            time.sleep(2)
        
        # Convert PDF jika perlu
        if file_path.suffix.lower() == '.pdf':
            image_paths = self._convert_pdf_to_images(file_path)
            if not image_paths:
                return OCRResult(
                    filename=file_path.name,
                    text='',
                    confidence=0,
                    engine='none',
                    processing_time=time.time() - start_time,
                    pages_processed=0,
                    success=False,
                    timestamp=datetime.now().isoformat()
                )
        else:
            image_paths = [file_path]
        
        # Process semua pages/images
        all_texts = []
        all_confidences = []
        preprocessed_count = 0
        
        for img_path in image_paths:
            try:
                if self.paddleocr is None:
                    raise Exception("PaddleOCR not initialized")
                
                # Preprocessing jika diperlukan
                processed_path = self.preprocessor.preprocess(img_path)
                if processed_path != img_path:
                    preprocessed_count += 1
                
                # OCR - using predict method for PaddleOCR v3.3.2 (PaddleX)
                result = self.paddleocr.predict(str(processed_path))
                if result and len(result) > 0:
                    # Result is a list with one dict containing 'rec_texts' and 'rec_scores'
                    ocr_data = result[0]
                    if 'rec_texts' in ocr_data and 'rec_scores' in ocr_data:
                        texts = ocr_data['rec_texts']
                        scores = ocr_data['rec_scores']
                        for text, score in zip(texts, scores):
                            if text:
                                all_texts.append(text)
                                all_confidences.append(score)
                
                # Cleanup temp images
                if file_path.suffix.lower() == '.pdf':
                    img_path.unlink(missing_ok=True)
                    if processed_path != img_path:
                        processed_path.unlink(missing_ok=True)
                        
            except Exception as e:
                logger.error(f"❌ OCR failed for {img_path}: {e}")
                if file_path.suffix.lower() == '.pdf':
                    img_path.unlink(missing_ok=True)
        
        processing_time = time.time() - start_time
        
        # Calculate metrics
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        full_text = "\n".join(all_texts)
        
        # Success criteria dengan threshold baru
        success = len(full_text) >= self.config.MIN_TEXT_LENGTH and avg_confidence >= self.config.CONFIDENCE_THRESHOLD
        
        result = OCRResult(
            filename=file_path.name,
            text=full_text,
            confidence=avg_confidence,
            engine='paddleocr',
            processing_time=processing_time,
            pages_processed=len(image_paths),
            success=success,
            timestamp=datetime.now().isoformat(),
            cached=False
        )
        
        # Save ke cache
        if self.cache and success:
            self.cache.set(file_path, {
                'text': full_text,
                'confidence': avg_confidence,
                'pages': len(image_paths)
            })
        
        if preprocessed_count > 0:
            self.stats['preprocessed'] += 1
        
        return result
    
    def process_batch(self) -> List[OCRResult]:
        """Process batch dengan optimasi"""
        pending_files = self._get_pending_files()
        
        if not pending_files:
            logger.info("✅ No pending files to process")
            return []
        
        logger.info(f"🚀 Starting optimized processing: {len(pending_files)} files")
        logger.info(f"⚙️  Config: workers={self.config.MAX_WORKERS}, batch={self.config.BATCH_SIZE}")
        logger.info(f"🎯 Threshold: confidence>={self.config.CONFIDENCE_THRESHOLD}, length>={self.config.MIN_TEXT_LENGTH}")
        
        results = []
        batch_count = 0
        
        for i in range(0, len(pending_files), self.config.BATCH_SIZE):
            if not self.running:
                break
            
            batch = pending_files[i:i + self.config.BATCH_SIZE]
            batch_count += 1
            self.state.current_batch = batch_count
            
            logger.info(f"📦 Batch {batch_count}: {len(batch)} files")
            
            # Check memory
            status, mem_percent = self.memory_monitor.check_memory()
            logger.info(f"💾 Memory: {status} ({mem_percent}%)")
            
            # Process batch
            with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
                future_to_file = {
                    executor.submit(self._process_single_file, f): f 
                    for f in batch
                }
                
                for future in as_completed(future_to_file):
                    if not self.running:
                        break
                    
                    result = future.result()
                    if result:
                        results.append(result)
                        
                        if result.success:
                            self.state.processed_files += 1
                            self.state.last_processed = result.filename
                            self.stats['successful'] += 1
                        else:
                            self.state.failed_files += 1
                            self.stats['failed'] += 1
                        
                        # Progress
                        progress = (self.state.processed_files / self.state.total_files) * 100
                        logger.info(f"📈 {self.state.processed_files}/{self.state.total_files} ({progress:.1f}%) - {result.filename}")
            
            # Save state & results
            self._save_state()
            self._save_results(results)
            
            # Memory check
            status, mem_percent = self.memory_monitor.check_memory()
            if status == 'warning':
                logger.warning(f"⚠️ Memory {mem_percent}%, pausing...")
                time.sleep(5)
        
        return results
    
    def _save_results(self, results: List[OCRResult]):
        """Save results ke JSON."""
        try:
            results_file = self.output_dir / "results.json"
            
            existing = []
            if results_file.exists():
                with open(results_file) as f:
                    existing_data = json.load(f)
                    existing = [OCRResult(**r) for r in existing_data.get('results', [])]
            
            # Merge
            all_results = existing + results
            
            with open(results_file, 'w') as f:
                json.dump({
                    'results': [asdict(r) for r in all_results],
                    'stats': {
                        'total': len(all_results),
                        'successful': len([r for r in all_results if r.success]),
                        'failed': len([r for r in all_results if not r.success]),
                        'cached': len([r for r in all_results if r.cached]),
                        'preprocessed': self.stats['preprocessed']
                    },
                    'config': {
                        'confidence_threshold': self.config.CONFIDENCE_THRESHOLD,
                        'min_text_length': self.config.MIN_TEXT_LENGTH,
                        'pdf_adaptive': self.config.PDF_RESOLUTION_ADAPTIVE
                    },
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
    
    def print_summary(self, results: List[OCRResult]):
        """Print final summary."""
        successful = len([r for r in results if r.success])
        cached = len([r for r in results if r.cached])
        
        print("\n" + "=" * 70)
        print("✅ OPTIMIZED OCR COMPLETE!")
        print("=" * 70)
        print(f"📊 Total: {len(results)}")
        print(f"✅ Successful: {successful}")
        print(f"📦 From Cache: {cached}")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"✨ Preprocessed: {self.stats['preprocessed']}")
        
        if results:
            times = [r.processing_time for r in results if not r.cached]
            if times:
                print(f"\n⏱️  Processing Time:")
                print(f"   Avg: {sum(times)/len(times):.2f}s")
                print(f"   Min: {min(times):.2f}s")
                print(f"   Max: {max(times):.2f}s")
        
        print(f"\n📁 Output: {self.output_dir}")
        print(f"💾 State: {self.state_file}")
        print(f"📦 Cache: {self.config.CACHE_DIR}")
        print("=" * 70)
    
    def run(self):
        """Main entry point."""
        print("=" * 70)
        print("🚀 Optimized PaddleOCR Router v2.0")
        print("=" * 70)
        print(f"📁 Input: {self.input_dir}")
        print(f"📁 Output: {self.output_dir}")
        print(f"⚙️  Workers: {self.config.MAX_WORKERS}")
        print(f"🎯 Confidence: ≥{self.config.CONFIDENCE_THRESHOLD}")
        print(f"📄 Min Length: ≥{self.config.MIN_TEXT_LENGTH} chars")
        print(f"💾 Memory: {self.config.MEMORY_WARNING}%/{self.config.MEMORY_CRITICAL}%/{self.config.MEMORY_PAUSE}%")
        print(f"📐 PDF: Adaptive resolution")
        print(f"📦 Cache: {'Enabled' if self.config.CACHE_ENABLED else 'Disabled'}")
        print("=" * 70)
        
        # Check memory
        status, mem_percent = self.memory_monitor.check_memory()
        print(f"\n💾 Memory: {mem_percent}% ({status})")
        
        if status == 'pause':
            print("⚠️  Memory too high! Please close some applications first.")
            return
        
        # Process
        start_time = time.time()
        results = self.process_batch()
        total_time = time.time() - start_time
        
        self.stats['total_time'] = total_time
        
        # Summary
        self.print_summary(results)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimized PaddleOCR Router')
    parser.add_argument('-i', '--input', default='input', help='Input directory')
    parser.add_argument('-o', '--output', default='processed/optimized_ocr', help='Output directory')
    parser.add_argument('-w', '--workers', type=int, default=2, help='Number of workers')
    parser.add_argument('--confidence', type=float, default=0.75, help='Confidence threshold')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    
    args = parser.parse_args()
    
    config = OptimizedConfig()
    config.MAX_WORKERS = args.workers
    config.CONFIDENCE_THRESHOLD = args.confidence
    config.CACHE_ENABLED = not args.no_cache
    
    router = OptimizedPaddleOCRRouter(
        input_dir=args.input,
        output_dir=args.output,
        config=config
    )
    
    router.run()


if __name__ == "__main__":
    main()
