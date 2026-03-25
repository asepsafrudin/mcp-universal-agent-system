# 🔬 Riset Mendalam: Hybrid PaddleOCR Architecture
## Optimasi OCR untuk Dokumen Scanner dengan Resource Terbatas

**Tanggal:** 27 Februari 2026  
**Fokus:** Analisis & Optimasi Hybrid PaddleOCR Pipeline  
**Hardware:** Intel i7-13620H, 10GB RAM, CPU-only

---

## 📋 Executive Summary

Berdasarkan analisis kode existing, sistem Anda sudah memiliki **3 arsitektur Hybrid OCR** yang berbeda:

| Arsitektur | Lokasi | Engine Utama | Fallback | Status |
|------------|--------|--------------|----------|--------|
| **Safe Paddle Router** | `Bangda_PUU/scripts/` | PaddleOCR | Gemini Vision | Production |
| **Hybrid OCR Pipeline** | `Bangda_PUU/scripts/` | PaddleOCR | Gemini + Groq | Development |
| **Vision + OCR Fallback** | `MCP/execution/tools/` | Vision Model | PaddleOCR | MCP Integration |

**Rekomendasi:** Fokus optimasi pada **Safe Paddle Router** karena sudah paling mature dengan fitur monitoring lengkap.

---

## 🏗️ Arsitektur 1: Safe Paddle OCR Router

### Lokasi File
```
../Bangda_PUU/Dokumentasi_scanner/scripts/paddle_ocr_safe_router.py
```

### Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SAFE PADDLE OCR ROUTER                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. INPUT HANDLING                                            │
│    - PDF files → Convert to images (PyMuPDF)                 │
│    - Image files → Process directly                          │
│    - Resume capability dari processing_state.json            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. MEMORY MONITORING                                         │
│    - Warning threshold: 75%                                  │
│    - Critical threshold: 85%                                 │
│    - Pause threshold: 90% (auto-pause processing)            │
│    - Auto-resume saat memory turun                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. SMART OCR ROUTING                                         │
│                                                              │
│   ┌──────────────┐    Confidence >= 0.6?    ┌──────────────┐ │
│   │  PaddleOCR   │ ───────────────────────> │   Success    │ │
│   │   Primary    │                          │  (Return)    │ │
│   └──────────────┘                          └──────────────┘ │
│          │                                           ▲       │
│          │ Confidence < 0.6 or Fail                   │       │
│          ▼                                           │       │
│   ┌──────────────┐    Text length > 50?      ┌───────┘       │
│   │ Gemini       │ ───────────────────────> │               │
│   │ Fallback     │    Yes & Good result     │               │
│   └──────────────┘                          │               │
│          │                                  │               │
│          │ Both failed                      │               │
│          ▼                                  │               │
│   ┌──────────────┐                          │               │
│   │ Return best  │ ───────────────────────> │               │
│   │ effort       │                          │               │
│   └──────────────┘                          └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. STATE MANAGEMENT                                          │
│    - Auto-save setiap batch                                  │
│    - Graceful shutdown (Ctrl+C handling)                     │
│    - Resume dari last processed file                         │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

#### 1. Memory Monitoring System
```python
class MemoryMonitor:
    - warning_threshold=75%    # Warning log
    - critical_threshold=85%   # Slow down processing
    - pause_threshold=90%      # Pause & wait
```

**Optimasi:** Threshold sudah optimal untuk 10GB RAM. Pada CPU-only, memory spike terjadi saat:
- PDF conversion (PyMuPDF load ke memory)
- PaddleOCR initialization
- Batch processing dengan banyak workers

#### 2. Smart Routing Logic
```python
# Confidence threshold untuk routing
if confidence >= 0.6 and len(text) > 50:
    return paddle_result  # Success
else:
    return gemini_fallback(image)  # Fallback
```

**Analisis:**
- Threshold 0.6 agak rendah - bisa naik ke 0.75 untuk mengurangi API calls
- Text length check (>50 chars) bagus untuk menghindari false positives
- Gemini fallback akan significant cost untuk batch besar

#### 3. Batch Processing dengan ThreadPool
```python
with ThreadPoolExecutor(max_workers=2) as executor:
    # Process batch size: 5 files
```

**Optimasi:**
- `max_workers=2` optimal untuk 4-core CPU (menghindari oversubscription)
- `batch_size=5` kecil untuk memory management
- Bisa ditingkatkan ke 4 workers untuk speed (dengan risiko memory spike)

---

## 🏗️ Arsitektur 2: Hybrid OCR Pipeline

### Lokasi File
```
../Bangda_PUU/Dokumentasi_scanner/scripts/hybrid_ocr_pipeline.py
```

### 3-Stage Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│              HYBRID OCR PIPELINE (3-Stage)                   │
└─────────────────────────────────────────────────────────────┘

Stage 1: PREPROCESSING (Lokal - Gratis)
├─ Deskewing (luruskan rotasi)
├─ Denoising (fastNlMeansDenoising)
├─ CLAHE Contrast Enhancement
└─ Output: preprocessed/image_preprocessed.png

Stage 2: SMART OCR ROUTER
├─ PaddleOCR primary (confidence threshold: 0.85)
├─ Gemini fallback (untuk handwriting/low confidence)
└─ Output: raw_text + confidence + engine_used

Stage 3: POSTPROCESSING (Groq - Murah)
├─ Structure text (markdown/JSON)
├─ Entity extraction (dates, names, amounts)
├─ OCR error correction
└─ Output: structured_text + entities.json
```

### Perbandingan dengan Safe Router

| Aspek | Safe Router | Hybrid Pipeline |
|-------|-------------|-----------------|
| **Preprocessing** | ❌ Manual/External | ✅ Built-in (OpenCV) |
| **Postprocessing** | ❌ None | ✅ Groq LLM |
| **Memory Monitor** | ✅ Advanced | ❌ Basic |
| **Resume Capability** | ✅ Yes | ❌ No |
| **Cost Optimization** | ✅ Gemini only fallback | ⚠️ Groq always |
| **Maturity** | ✅ Production | ⚠️ Development |

---

## 🏗️ Arsitektur 3: Vision + OCR Fallback (MCP Integration)

### Lokasi File
```
mcp-unified/execution/tools/vision_enhanced.py
```

### Konsep Terbalik

```
Traditional:    PaddleOCR → (fallback) → Vision Model
MCP Approach:   Vision Model → (fallback) → PaddleOCR
```

### Use Case
Cocok untuk:
- Analysis dokumen kompleks (butuh understanding konteks)
- Ekstraksi structured data dengan schema
- Kasus dimana text extraction saja tidak cukup

### Kode Implementation
```python
async def analyze_with_ocr_fallback(
    image_path: str,
    prompt: str = "Extract all text",
    min_confidence: float = 0.7
):
    # 1. Try vision model first
    vision_result = await analyze_image_enhanced(...)
    
    if vision_result.confidence >= min_confidence:
        return vision_result  # Success
    
    # 2. Fallback to PaddleOCR
    ocr = PaddleOCR(...)
    result = ocr.ocr(image_path, cls=True)
    
    # 3. Combine results
    return VisionResult(
        content=f"Vision: {...}\n\nOCR: {...}",
        metadata={"method": "hybrid"}
    )
```

---

## 🔍 Analisis Bottleneck & Optimasi

### 1. PDF Conversion Bottleneck

**Masalah:**
```python
# PyMuPDF conversion dengan Matrix(2,2) = 4x resolusi
mat = fitz.Matrix(2, 2)
pix = page.get_pixmap(matrix=mat)
```

**Impact:**
- PDF 1 halaman A4 → ~2-5MB image
- Memory spike saat batch processing
- Conversion time: 1-3 detik per halaman

**Optimasi:**
```python
# Gunakan resolusi lebih rendah untuk draft
mat = fitz.Matrix(1.5, 1.5)  # 2.25x (vs 4x)

# Atau adaptive berdasarkan PDF size
file_size = pdf_path.stat().st_size
if file_size > 10MB:
    mat = fitz.Matrix(1, 1)  # 1x untuk file besar
```

### 2. PaddleOCR Initialization

**Masalah:**
```python
# Setiap instance butuh ~2GB memory saat init
self.paddleocr = PaddleOCR(
    use_angle_cls=True,
    lang='en',
    use_gpu=False,
    show_log=False,
    enable_mkldnn=True
)
```

**Optimasi (Sudah Bagus):**
- ✅ `enable_mkldnn=True` - Optimasi Intel CPU
- ✅ Single instance shared (tidak recreate)
- ✅ `show_log=False` - Reduce I/O overhead

**Tambahan:**
```python
# Limit threads untuk menghindari CPU oversubscription
import os
os.environ['OMP_NUM_THREADS'] = '4'  # Match CPU cores
```

### 3. Gemini Fallback Cost

**Masalah:**
- Gemini Vision API ~$0.0015 per image (Flash)
- 131 dokumen × $0.0015 = ~$0.20 per batch
- Bisa mahal jika trigger terlalu sering

**Optimasi Threshold:**
```python
# Naikkan threshold untuk mengurangi fallback
confidence_threshold = 0.75  # was 0.6

# Tambahkan text length check lebih ketat
if confidence >= 0.75 and len(text) > 100:
    return paddle_result
```

### 4. Memory Leak Potential

**Identified Issues:**
```python
# Di hybrid_ocr_pipeline.py - Tidak ada cleanup
# PyMuPDF images tidak di-unlink setelah OCR

# Fix:
for img_path in image_paths:
    try:
        result = ocr.ocr(str(img_path), cls=True)
    finally:
        img_path.unlink(missing_ok=True)  # Cleanup
```

---

## 💡 Rekomendasi Optimasi

### Immediate (Hari Ini)

#### 1. Naikkan Confidence Threshold
```python
# Safe Router: paddle_ocr_safe_router.py
confidence_threshold = 0.75  # dari 0.6
```

**Impact:**
- ↓ 30-50% Gemini API calls
- ↑ Akurasi (hanya fallback saat benar-benar perlu)
- ↓ Biaya

#### 2. Adaptive PDF Resolution
```python
def get_pdf_matrix(file_path: Path) -> fitz.Matrix:
    """Adaptive resolution based on file size"""
    size_mb = file_path.stat().st_size / (1024 * 1024)
    
    if size_mb > 10:
        return fitz.Matrix(1, 1)      # 72 DPI
    elif size_mb > 5:
        return fitz.Matrix(1.5, 1.5)  # 108 DPI
    else:
        return fitz.Matrix(2, 2)      # 144 DPI (default)
```

#### 3. Add OCR Result Caching
```python
# Cache hasil OCR untuk menghindari re-processing
def get_cache_key(file_path: Path) -> str:
    import hashlib
    stat = file_path.stat()
    content = f"{file_path}:{stat.st_size}:{stat.st_mtime}"
    return hashlib.md5(content.encode()).hexdigest()
```

### Short-term (Minggu Ini)

#### 4. Implement Parallel PDF Conversion
```python
# Convert PDF pages in parallel
from concurrent.futures import ProcessPoolExecutor

def convert_pdf_parallel(pdf_path: Path, max_workers: int = 4):
    doc = fitz.open(pdf_path)
    pages = list(range(len(doc)))
    
    with ProcessPoolExecutor(max_workers) as executor:
        image_paths = list(executor.map(
            convert_single_page,
            [(pdf_path, p) for p in pages]
        ))
    
    return [p for p in image_paths if p]
```

#### 5. Smart Batch Sizing
```python
def calculate_optimal_batch(file_count: int, avg_file_size_mb: float) -> int:
    """Calculate optimal batch size based on memory"""
    available_mb = psutil.virtual_memory().available / (1024 * 1024)
    estimated_per_file_mb = avg_file_size_mb * 5  # 5x for processing overhead
    
    max_batch = int(available_mb * 0.5 / estimated_per_file_mb)
    return min(max_batch, 10, file_count)  # Max 10, or file_count
```

#### 6. Preprocessing Integration
```python
# Integrasi preprocessing dari hybrid_ocr_pipeline.py
# ke safe router untuk hasil lebih baik

class AdaptivePreprocessor:
    def preprocess(self, image_path: Path) -> Path:
        # Check if preprocessing needed
        img = cv2.imread(str(image_path))
        
        # Analyze image quality
        variance = cv2.Laplacian(img, cv2.CV_64F).var()
        
        if variance < 100:  # Blurry
            return self.enhance(image_path)
        else:
            return image_path  # Skip preprocessing
```

### Long-term (Bulan Ini)

#### 7. Implement Quality Prediction
```python
# Gunakan simple heuristik untuk prediksi kualitas OCR
# sebelum processing (save time & cost)

def predict_ocr_quality(image_path: Path) -> float:
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Metrics
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    contrast = gray.std()
    brightness = gray.mean()
    
    # Score 0-1
    score = min(1.0, (sharpness / 500) * (contrast / 50))
    return score
```

#### 8. Hybrid Strategy Configuration
```python
# Config file untuk tuning tanpa code change
HYBRID_CONFIG = {
    "paddleocr": {
        "confidence_threshold": 0.75,
        "min_text_length": 100,
        "use_gpu": False,
        "enable_mkldnn": True
    },
    "fallback": {
        "enabled": True,
        "engine": "gemini",  # or "vision_model"
        "max_daily_calls": 100
    },
    "pdf": {
        "resolution_scale": "adaptive",  # or 1.0, 1.5, 2.0
        "max_pages": 50
    },
    "memory": {
        "warning": 75,
        "critical": 85,
        "pause": 90
    }
}
```

---

## 📊 Benchmark & Expected Performance

### Current Performance (Estimasi)

| Operasi | Waktu (per file) | Resource |
|---------|------------------|----------|
| PDF Conversion (1 page) | 1-3 detik | ~50MB RAM |
| PaddleOCR (1 page) | 2-5 detik | ~200MB RAM |
| Gemini Fallback | 3-10 detik | ~10MB RAM + API |
| Preprocessing | 1-2 detik | ~100MB RAM |

### Projected Performance (Setelah Optimasi)

| Operasi | Waktu (per file) | Improvement |
|---------|------------------|-------------|
| PDF Conversion (adaptive) | 0.5-2 detik | **40% faster** |
| PaddleOCR (optimized) | 1.5-3 detik | **30% faster** |
| Gemini Fallback (reduced) | Rarely triggered | **50% less API calls** |
| **Total (131 files)** | **~15-20 menit** | **vs 30-40 menit** |

---

## 🎯 Implementation Roadmap

### Week 1: Quick Wins
- [ ] Naikkan confidence threshold ke 0.75
- [ ] Implement adaptive PDF resolution
- [ ] Add OCR result caching
- [ ] Test dengan 10 sample dokumen

### Week 2: Integration
- [ ] Integrasi preprocessing ke Safe Router
- [ ] Implement smart batch sizing
- [ ] Add quality prediction heuristic
- [ ] Benchmark vs baseline

### Week 3: Production
- [ ] Deploy ke production pipeline
- [ ] Monitor API usage & cost
- [ ] Fine-tune thresholds berdasarkan hasil
- [ ] Dokumentasikan SOP

---

## 🔧 Code Snippets untuk Implementasi

### 1. Optimized Safe Router Config
```python
# paddle_ocr_safe_router.py - Config section

class OptimizedConfig:
    """Optimized configuration untuk resource terbatas"""
    
    # OCR
    CONFIDENCE_THRESHOLD = 0.75  # Naik dari 0.6
    MIN_TEXT_LENGTH = 100       # Naik dari 50
    
    # Memory
    MEMORY_WARNING = 70         # Turun dari 75
    MEMORY_CRITICAL = 80        # Turun dari 85
    MEMORY_PAUSE = 90           # Tetap
    
    # PDF
    PDF_RESOLUTION_ADAPTIVE = True
    PDF_MAX_PAGES = 50
    
    # Batch
    MAX_WORKERS = 2             # Tetap (optimal untuk 4-core)
    BATCH_SIZE = 3              # Turun dari 5 (memory)
```

### 2. Caching Decorator
```python
import functools
import hashlib
import json
from pathlib import Path

def ocr_cache(cache_dir: Path = Path("ocr_cache")):
    """Decorator untuk caching OCR results"""
    cache_dir.mkdir(exist_ok=True)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(image_path: Path, *args, **kwargs):
            # Generate cache key
            stat = image_path.stat()
            key = f"{image_path.name}_{stat.st_size}_{stat.st_mtime}"
            cache_key = hashlib.md5(key.encode()).hexdigest()
            cache_file = cache_dir / f"{cache_key}.json"
            
            # Check cache
            if cache_file.exists():
                with open(cache_file) as f:
                    return json.load(f)
            
            # Execute
            result = func(image_path, *args, **kwargs)
            
            # Save cache
            with open(cache_file, 'w') as f:
                json.dump(result, f)
            
            return result
        return wrapper
    return decorator
```

### 3. Monitoring Dashboard (Simple)
```python
# Add ke safe router untuk real-time monitoring

def print_progress_summary(state: ProcessingState):
    """Print real-time progress"""
    total = state.total_files
    done = state.processed_files
    failed = state.failed_files
    
    progress = done / total * 100 if total > 0 else 0
    
    print(f"\n{'='*50}")
    print(f"Progress: {done}/{total} ({progress:.1f}%)")
    print(f"Success: {done - failed} | Failed: {failed}")
    
    # ETA calculation
    if done > 0:
        elapsed = time.time() - start_time
        rate = done / elapsed
        remaining = (total - done) / rate
        print(f"ETA: {remaining/60:.1f} minutes")
    print(f"{'='*50}\n")
```

---

## 📚 Referensi & Resources

### Dokumentasi PaddleOCR
- GitHub: https://github.com/PaddlePaddle/PaddleOCR
- Optimal Settings: https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_en/FAQ_en.md

### PyMuPDF (fitz)
- Documentation: https://pymupdf.readthedocs.io/
- Performance Tips: https://pymupdf.readthedocs.io/en/latest/faq.html#performance

### Gemini Vision API
- Pricing: https://ai.google.dev/pricing
- Best Practices: https://ai.google.dev/tutorials/image_inference

---

## 🎓 Kesimpulan

### Apa yang Sudah Baik ✅
1. **Safe Router** sudah mature dengan monitoring lengkap
2. **Memory management** sudah robust
3. **Resume capability** penting untuk batch besar
4. **ThreadPool sizing** sudah optimal untuk CPU

### Apa yang Perlu Dioptimasi ⚠️
1. **Confidence threshold** terlalu rendah (0.6 → 0.75)
2. **PDF resolution** bisa adaptive (save memory & time)
3. **Caching** belum ada (re-processing waste)
4. **Preprocessing** belum integrated (hybrid pipeline lebih baik)

### Expected Impact 📈
- **40% faster** dengan adaptive resolution
- **50% less API cost** dengan higher threshold
- **Zero re-processing** dengan caching
- **Better accuracy** dengan preprocessing integration

---

*Dokumen ini dibuat untuk optimasi Hybrid PaddleOCR pipeline.*
*Last Updated: 27 Februari 2026*
