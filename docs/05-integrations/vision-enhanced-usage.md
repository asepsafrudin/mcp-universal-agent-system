# Enhanced Vision Tools — Dokumentasi Lengkap

## Overview

Enhanced Vision Tools memperluas kemampuan vision MCP dengan fitur-fitur baru untuk analisis gambar yang lebih powerful dan fleksibel.

## Fitur Baru

1. ✅ **Enhanced Analysis** — Confidence scoring dan caching
2. ✅ **Batch Processing** — Proses multiple images secara parallel
3. ✅ **Image Comparison** — Bandingkan 2+ gambar
4. ✅ **Structured Extraction** — Ekstrak data terstruktur (JSON)
5. ✅ **Image Enhancement** — Auto-enhance sebelum analisis
6. ✅ **URL Support** — Analisis gambar dari URL
7. ✅ **OCR Hybrid** — Kombinasi vision + PaddleOCR
8. ✅ **Video Frame Analysis** — Analisis frame dari video
9. ✅ **Smart Caching** — Hindari re-analisis
10. ✅ **Progress Callbacks** — Real-time progress updates

---

## Tools Reference

### 1. `analyze_image_enhanced`

Analisis gambar dengan confidence scoring dan caching.

**Contoh Penggunaan:**

```python
from execution.tools.vision_enhanced import analyze_image_enhanced

# Basic usage
result = await analyze_image_enhanced(
    image_path="/home/aseps/MCP/screenshot.png",
    prompt="Describe this UI and identify any errors",
    namespace="my_project"
)

# Result structure
print(f"Success: {result.success}")
print(f"Content: {result.content}")
print(f"Confidence: {result.confidence:.2%}")  # 0.0 - 1.0
print(f"Model: {result.model}")
print(f"Processing time: {result.processing_time:.2f}s")

# Dengan progress callback
async def on_progress(stage: str, progress: float):
    print(f"Stage: {stage}, Progress: {progress:.0%}")

result = await analyze_image_enhanced(
    image_path="/home/aseps/MCP/document.jpg",
    prompt="Extract all text",
    namespace="my_project",
    progress_callback=on_progress,
    use_cache=True,           # Gunakan cache jika tersedia
    return_confidence=True    # Hitung confidence score
)
```

**Parameters:**
- `image_path` (str): Path absolut ke file gambar
- `prompt` (str, optional): Instruksi untuk vision model
- `namespace` (str, optional): Namespace untuk memory (default: "default")
- `model` (str, optional): Override model vision
- `use_cache` (bool, optional): Gunakan cache (default: True)
- `return_confidence` (bool, optional): Hitung confidence (default: True)
- `progress_callback` (callable, optional): Callback untuk progress updates

**Returns:** `VisionResult` object dengan:
- `success` (bool): Berhasil atau tidak
- `content` (str): Hasil analisis
- `confidence` (float): Confidence score (0.0 - 1.0)
- `model` (str): Model yang digunakan
- `processing_time` (float): Waktu processing dalam detik
- `image_path` (str): Path gambar
- `metadata` (dict): Metadata tambahan
- `error` (str, optional): Error message jika gagal

---

### 2. `analyze_batch`

Proses multiple images secara parallel.

**Contoh Penggunaan:**

```python
from execution.tools.vision_enhanced import analyze_batch

# Daftar gambar untuk diproses
images = [
    "/home/aseps/MCP/invoice_001.jpg",
    "/home/aseps/MCP/invoice_002.jpg",
    "/home/aseps/MCP/invoice_003.jpg",
    "/home/aseps/MCP/invoice_004.jpg",
]

# Progress callback
async def on_progress(current: int, total: int):
    print(f"Progress: {current}/{total}")

# Batch analysis
results = await analyze_batch(
    image_paths=images,
    prompt="Extract: invoice number, date, vendor, total amount",
    namespace="accounting_2024",
    max_parallel=4,  # Proses 4 gambar sekaligus
    progress_callback=on_progress
)

# Process results
for result in results:
    if result.success:
        print(f"✓ {result.image_path}: {result.confidence:.0%} confidence")
    else:
        print(f"✗ {result.image_path}: {result.error}")
```

**Parameters:**
- `image_paths` (List[str]): List path gambar
- `prompt` (str, optional): Instruksi untuk setiap gambar
- `namespace` (str, optional): Namespace untuk memory
- `model` (str, optional): Override model
- `max_parallel` (int, optional): Max concurrent processing (default: 4)
- `progress_callback` (callable, optional): Callback(current, total)

**Returns:** List of `VisionResult`

---

### 3. `compare_images`

Bandingkan multiple images.

**Contoh Penggunaan:**

```python
from execution.tools.vision_enhanced import compare_images

# Bandingkan 2+ gambar
result = await compare_images(
    image_paths=[
        "/home/aseps/MCP/screenshot_v1.png",
        "/home/aseps/MCP/screenshot_v2.png",
        "/home/aseps/MCP/screenshot_v3.png",
    ]
)

print(f"Confidence: {result.confidence:.0%}")
print("\nSimilarities:")
for sim in result.similarities:
    print(f"  • {sim}")

print("\nDifferences:")
for diff in result.differences:
    print(f"  • {diff}")

if result.recommendation:
    print(f"\n⚠ {result.recommendation}")
```

**Parameters:**
- `image_paths` (List[str]): List of 2+ image paths
- `comparison_prompt` (str, optional): Custom comparison instructions
- `detailed_analysis` (bool, optional): Detailed pairwise comparison

**Returns:** `ComparisonResult` dengan:
- `similarities` (List[str]): List of similarities
- `differences` (List[str]): List of differences
- `confidence` (float): Overall confidence
- `recommendation` (str, optional): Recommendation jika confidence rendah

---

### 4. `extract_structured_data`

Ekstrak data terstruktur dari gambar.

**Contoh Penggunaan:**

```python
from execution.tools.vision_enhanced import extract_structured_data

# Define schema untuk invoice
schema = {
    "invoice_number": "The invoice number/ID",
    "invoice_date": "Date of the invoice (YYYY-MM-DD format)",
    "due_date": "Payment due date (YYYY-MM-DD format)",
    "vendor_name": "Name of the vendor/company",
    "vendor_address": "Full address of the vendor",
    "total_amount": "Total amount to pay (number only)",
    "tax_amount": "Tax amount if shown (number only)",
    "currency": "Currency code (USD, EUR, IDR, etc.)"
}

# Extract data
result = await extract_structured_data(
    image_path="/home/aseps/MCP/invoice.pdf",
    schema=schema
)

if result.success:
    print("Extracted Data:")
    for field, value in result.data.items():
        print(f"  {field}: {value}")
    
    print(f"\nConfidence: {result.confidence:.0%}")
    
    if result.missing_fields:
        print(f"\n⚠ Missing fields: {', '.join(result.missing_fields)}")
else:
    print(f"Extraction failed: {result.raw_text}")
```

**Parameters:**
- `image_path` (str): Path ke image
- `schema` (Dict[str, str]): Dict dengan field names dan descriptions
- `model` (str, optional): Model override (default: OCR-optimized)

**Returns:** `StructuredExtraction` dengan:
- `success` (bool): Berhasil atau tidak
- `data` (Dict): Extracted data sebagai dict
- `raw_text` (str): Raw response text
- `confidence` (float): Confidence score
- `missing_fields` (List[str]): Fields yang tidak ditemukan

**Use Cases:**
- Ekstrak data dari invoice/receipt
- Ekstrak informasi dari form
- Ekstrak data dari ID cards
- Ekstrak metadata dari dokumen

---

### 5. `enhance_image`

Apply enhancements ke image sebelum analysis.

**Contoh Penggunaan:**

```python
from execution.tools.vision_enhanced import enhance_image, analyze_image_enhanced

# Enhance image sebelum analysis
enhanced = await enhance_image(
    image_path="/home/aseps/MCP/blurry_scan.jpg",
    enhancements=["contrast", "sharpness", "denoise", "upscale"],
    output_path="/home/aseps/MCP/enhanced_scan.jpg"
)

if enhanced["success"]:
    print(f"Enhancements applied: {enhanced['enhancements_applied']}")
    print(f"Original size: {enhanced['original_size']}")
    print(f"Enhanced size: {enhanced['enhanced_size']}")
    
    # Analyze enhanced image
    result = await analyze_image_enhanced(
        image_path=enhanced["enhanced_path"],
        prompt="Extract all text with high accuracy"
    )
```

**Available Enhancements:**
- `"contrast"`: Improve contrast (1.5x)
- `"sharpness"`: Sharpen image (2.0x)
- `"denoise"`: Remove noise dengan median filter
- `"upscale"`: Upscale ke minimum 1024px width

**Parameters:**
- `image_path` (str): Source image path
- `enhancements` (List[str], optional): List of enhancement types
- `output_path` (str, optional): Output path (default: temp file)

**Returns:** Dict dengan:
- `success` (bool): Berhasil atau tidak
- `original_path` (str): Source path
- `enhanced_path` (str): Output path
- `enhancements_applied` (List[str]): Applied enhancements
- `original_size` (tuple): Original dimensions
- `enhanced_size` (tuple): Enhanced dimensions

---

### 6. `analyze_image_url`

Download dan analyze image dari URL.

**Contoh Penggunaan:**

```python
from execution.tools.vision_enhanced import analyze_image_url

# Analyze image dari URL
result = await analyze_image_url(
    image_url="https://example.com/screenshot.png",
    prompt="Describe this UI layout",
    namespace="web_analysis",
    timeout=30  # Download timeout dalam detik
)

if result.success:
    print(f"Analysis: {result.content}")
    print(f"Confidence: {result.confidence:.0%}")
else:
    print(f"Error: {result.error}")
```

**Parameters:**
- `image_url` (str): URL ke image
- `prompt` (str, optional): Instruksi untuk vision model
- `namespace` (str, optional): Namespace untuk memory
- `model` (str, optional): Model override
- `timeout` (int, optional): Download timeout (default: 30)

**Returns:** `VisionResult`

---

### 7. `analyze_with_ocr_fallback`

Kombinasi vision model dengan OCR fallback.

**Contoh Penggunaan:**

```python
from execution.tools.vision_enhanced import analyze_with_ocr_fallback

# Analyze dengan hybrid approach
result = await analyze_with_ocr_fallback(
    image_path="/home/aseps/MCP/scanned_document.jpg",
    prompt="Extract all text from this document",
    namespace="documents",
    min_confidence=0.7  # Minimum confidence untuk vision-only
)

if result.success:
    print(f"Method: {result.metadata.get('method')}")
    print(f"Vision confidence: {result.metadata.get('vision_confidence', 0):.0%}")
    print(f"OCR confidence: {result.metadata.get('ocr_confidence', 0):.0%}")
    print(f"\nContent:\n{result.content}")
```

**How it works:**
1. Coba vision model terlebih dahulu
2. Jika confidence < `min_confidence`, fallback ke PaddleOCR
3. Return combined result dari kedua method

**Parameters:**
- `image_path` (str): Path ke image
- `prompt` (str, optional): Prompt untuk vision model
- `namespace` (str, optional): Namespace untuk memory
- `min_confidence` (float, optional): Threshold untuk fallback (default: 0.7)

**Returns:** `VisionResult` dengan metadata tambahan:
- `method`: "vision_only" atau "hybrid"
- `vision_confidence`: Confidence dari vision model
- `ocr_confidence`: Confidence dari OCR (jika used)
- `ocr_lines`: Jumlah lines yang di-extract oleh OCR

**Requirements:**
```bash
pip install paddleocr paddlepaddle --break-system-packages
```

---

### 8. `analyze_video_frames`

Extract dan analyze frames dari video.

**Contoh Penggunaan:**

```python
from execution.tools.vision_enhanced import analyze_video_frames

# Analyze frames dari video
result = await analyze_video_frames(
    video_path="/home/aseps/MCP/presentation.mp4",
    prompt="Describe the content of this frame",
    frame_interval=10,  # Analyze setiap 10 detik
    max_frames=10,      # Maximum 10 frames
    namespace="video_analysis"
)

if result["success"]:
    print(f"Video duration: {result['duration_seconds']:.1f}s")
    print(f"Frames analyzed: {result['frames_analyzed']}")
    
    for frame in result["results"]:
        print(f"\n[{frame['timestamp_formatted']}]")
        print(f"  {frame['analysis'][:100]}...")
        print(f"  Confidence: {frame['confidence']:.0%}")
```

**Parameters:**
- `video_path` (str): Path ke video file
- `prompt` (str, optional): Prompt untuk setiap frame
- `frame_interval` (int, optional): Interval antar frame dalam detik (default: 5)
- `max_frames` (int, optional): Maximum frames (default: 10)
- `namespace` (str, optional): Namespace untuk memory

**Returns:** Dict dengan:
- `success` (bool): Berhasil atau tidak
- `video_path` (str): Path video
- `duration_seconds` (float): Video duration
- `total_frames_in_video` (int): Total frames
- `frames_analyzed` (int): Frames yang dianalisis
- `frame_interval_seconds` (int): Interval yang digunakan
- `results` (List[Dict]): List frame analysis results

**Requirements:**
```bash
pip install opencv-python --break-system-packages
```

---

### 9. `clear_vision_cache`

Clear vision cache.

**Contoh Penggunaan:**

```python
from execution.tools.vision_enhanced import clear_vision_cache

# Clear cache jika diperlukan
clear_vision_cache()
print("Vision cache cleared")
```

---

### 10. `get_vision_stats`

Get vision system statistics.

**Contoh Penggunaan:**

```python
from execution.tools.vision_enhanced import get_vision_stats

# Get stats
stats = await get_vision_stats()

print("Vision System Stats:")
print(f"  Cache entries: {stats['cache_entries']}")
print(f"  Cache TTL: {stats['cache_ttl_seconds']}s")
print(f"  Batch size: {stats['batch_size']}")
print(f"  Confidence threshold: {stats['confidence_threshold']}")
print(f"  Default model: {stats['default_model']}")
print(f"  Available models: {', '.join(stats['available_models'].keys())}")
```

---

## Via Registry

Semua enhanced vision tools bisa dipanggil via registry:

```python
from execution.registry import registry

# Enhanced image analysis
result = await registry.execute("analyze_image_enhanced", {
    "image_path": "/tmp/screenshot.png",
    "prompt": "Describe this UI",
    "namespace": "debug_session"
})

# Batch processing
results = await registry.execute("analyze_batch", {
    "image_paths": ["/tmp/1.jpg", "/tmp/2.jpg"],
    "prompt": "Extract text",
    "namespace": "batch_job"
})

# Structured extraction
result = await registry.execute("extract_structured_data", {
    "image_path": "/tmp/invoice.jpg",
    "schema": {
        "invoice_number": "Invoice ID",
        "total": "Total amount"
    }
})
```

---

## Via HTTP API

```bash
# Enhanced image analysis
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "analyze_image_enhanced",
    "arguments": {
      "image_path": "/home/aseps/MCP/screenshot.png",
      "prompt": "Describe this UI",
      "namespace": "my_project",
      "use_cache": true,
      "return_confidence": true
    }
  }'

# Batch processing
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "analyze_batch",
    "arguments": {
      "image_paths": [
        "/home/aseps/MCP/1.jpg",
        "/home/aseps/MCP/2.jpg"
      ],
      "prompt": "Extract text",
      "namespace": "batch_job",
      "max_parallel": 4
    }
  }'

# Image comparison
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "compare_images",
    "arguments": {
      "image_paths": [
        "/home/aseps/MCP/v1.png",
        "/home/aseps/MCP/v2.png"
      ]
    }
  }'

# Structured extraction
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "extract_structured_data",
    "arguments": {
      "image_path": "/home/aseps/MCP/invoice.jpg",
      "schema": {
        "invoice_number": "Invoice ID",
        "total": "Total amount"
      }
    }
  }'

# Image enhancement
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "enhance_image",
    "arguments": {
      "image_path": "/home/aseps/MCP/blurry.jpg",
      "enhancements": ["contrast", "sharpness"],
      "output_path": "/home/aseps/MCP/enhanced.jpg"
    }
  }'

# URL analysis
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "analyze_image_url",
    "arguments": {
      "image_url": "https://example.com/image.png",
      "prompt": "Describe this image",
      "namespace": "url_analysis"
    }
  }'

# OCR hybrid
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "analyze_with_ocr_fallback",
    "arguments": {
      "image_path": "/home/aseps/MCP/scanned.jpg",
      "prompt": "Extract all text",
      "min_confidence": 0.7
    }
  }'

# Video frame analysis
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "analyze_video_frames",
    "arguments": {
      "video_path": "/home/aseps/MCP/video.mp4",
      "prompt": "Describe this frame",
      "frame_interval": 5,
      "max_frames": 10
    }
  }'
```

---

## Model Selection

Enhanced Vision Tools mendukung multiple model profiles:

```python
ENHANCED_MODELS = {
    "fast": "moondream2",      # Lightweight, fast (~1s)
    "balanced": "llava",        # Good balance (~3-5s)
    "quality": "llava-llama3",  # High quality (~5-10s)
    "ocr": "llava-phi3"         # Optimized for text (~3-5s)
}
```

**Contoh penggunaan:**

```python
from execution.tools.vision_enhanced import ENHANCED_MODELS, analyze_image_enhanced

# Gunakan model fast untuk quick analysis
result = await analyze_image_enhanced(
    image_path="/tmp/screenshot.png",
    prompt="Quick check: any errors?",
    model=ENHANCED_MODELS["fast"]
)

# Gunakan model quality untuk detailed analysis
result = await analyze_image_enhanced(
    image_path="/tmp/architecture.png",
    prompt="Analyze this system architecture diagram in detail",
    model=ENHANCED_MODELS["quality"]
)

# Gunakan model OCR untuk text extraction
result = await analyze_image_enhanced(
    image_path="/tmp/document.png",
    prompt="Extract all text with high accuracy",
    model=ENHANCED_MODELS["ocr"]
)
```

---

## Confidence Scoring

Confidence score dihitung berdasarkan beberapa faktor:

1. **Response Length** (0.0 - 0.3)
   - >500 chars: +0.3
   - >200 chars: +0.2
   - >50 chars: +0.1

2. **Uncertainty Penalty** (-0.05 per word)
   - "maybe", "perhaps", "possibly", "might", "could be"
   - "unclear", "difficult to tell", "hard to say", "not sure"

3. **Specificity Bonus** (+0.02 per indicator)
   - Numbers (\d+)
   - Directional words: left, right, top, bottom, center
   - Color names: red, blue, green, yellow, black, white

**Interpretasi Confidence:**
- **>0.8**: High confidence - reliable untuk decision making
- **0.6-0.8**: Medium confidence - good untuk general analysis
- **0.4-0.6**: Low confidence - verify hasil secara manual
- **<0.4**: Very low confidence - consider re-analysis atau OCR fallback

---

## Caching

Vision cache menyimpan hasil analysis untuk menghindari re-processing:

```python
# Cache diaktifkan secara default
result1 = await analyze_image_enhanced(
    image_path="/tmp/image.png",
    prompt="Describe this",
    use_cache=True  # Default
)
# Processing time: ~5s

# Panggilan kedua - menggunakan cache
result2 = await analyze_image_enhanced(
    image_path="/tmp/image.png",
    prompt="Describe this",
    use_cache=True
)
# Processing time: ~0s (cache hit)

# Disable cache jika perlu fresh analysis
result3 = await analyze_image_enhanced(
    image_path="/tmp/image.png",
    prompt="Describe this",
    use_cache=False
)
```

**Cache Configuration:**
- TTL: 1 jam (3600 detik)
- Key: hash(image_path + prompt + model)
- Auto-cleanup: Expired entries dihapus otomatis

---

## Real-World Use Cases

### 1. Invoice Processing Pipeline

```python
from execution.tools.vision_enhanced import (
    analyze_batch, extract_structured_data, analyze_with_ocr_fallback
)

# Schema untuk invoice
INVOICE_SCHEMA = {
    "invoice_number": "Invoice number/ID",
    "date": "Invoice date (YYYY-MM-DD)",
    "vendor": "Vendor name",
    "total": "Total amount",
    "tax": "Tax amount"
}

async def process_invoices(invoice_paths: List[str]):
    results = []
    
    for path in invoice_paths:
        # Try structured extraction terlebih dahulu
        structured = await extract_structured_data(path, INVOICE_SCHEMA)
        
        if structured.confidence < 0.7:
            # Fallback ke hybrid vision+OCR
            hybrid = await analyze_with_ocr_fallback(path, min_confidence=0.7)
            results.append(hybrid)
        else:
            results.append(structured)
    
    return results
```

### 2. UI Regression Testing

```python
from execution.tools.vision_enhanced import compare_images

async def test_ui_regression(baseline_path: str, current_path: str):
    result = await compare_images(
        image_paths=[baseline_path, current_path],
        comparison_prompt="Compare these UI screenshots and identify any visual changes"
    )
    
    if result.confidence < 0.7:
        return {"status": "UNCERTAIN", "recommendation": result.recommendation}
    
    if result.differences:
        return {
            "status": "REGRESSION_DETECTED",
            "differences": result.differences,
            "confidence": result.confidence
        }
    
    return {"status": "PASS", "confidence": result.confidence}
```

### 3. Document Archiving System

```python
from execution.tools.vision_enhanced import analyze_batch, extract_structured_data

async def archive_documents(document_paths: List[str], metadata_schema: dict):
    # Batch analyze all documents
    batch_results = await analyze_batch(
        image_paths=document_paths,
        prompt="Identify document type and main content",
        max_parallel=4
    )
    
    archived = []
    for path, analysis in zip(document_paths, batch_results):
        if not analysis.success:
            continue
        
        # Extract structured metadata
        metadata = await extract_structured_data(path, metadata_schema)
        
        archived.append({
            "path": path,
            "type": analysis.content[:100],
            "metadata": metadata.data if metadata.success else {},
            "confidence": min(analysis.confidence, metadata.confidence)
        })
    
    return archived
```

### 4. Video Content Analysis

```python
from execution.tools.vision_enhanced import analyze_video_frames

async def summarize_video(video_path: str):
    frames = await analyze_video_frames(
        video_path=video_path,
        prompt="Describe the main content and any text visible in this frame",
        frame_interval=30,  # Every 30 seconds
        max_frames=20
    )
    
    if not frames["success"]:
        return {"error": frames["error"]}
    
    # Compile summary
    key_moments = [
        f"[{f['timestamp_formatted']}] {f['analysis'][:150]}..."
        for f in frames["results"]
        if f["success"] and f["confidence"] > 0.6
    ]
    
    return {
        "duration": frames["duration_seconds"],
        "frames_analyzed": frames["frames_analyzed"],
        "summary": "\n".join(key_moments)
    }
```

---

## Setup Requirements

### Dependencies

```bash
# Core dependencies (sudah ada)
pip install Pillow pymupdf --break-system-packages

# Untuk OCR Hybrid
pip install paddleocr paddlepaddle --break-system-packages

# Untuk Video Frame Analysis
pip install opencv-python --break-system-packages
```

### Ollama Models

```bash
# Pull vision models
ollama pull llava          # Balanced (default)
ollama pull moondream2     # Fast
ollama pull llava-llama3   # Quality
ollama pull llava-phi3     # OCR-optimized
```

### Environment Variables

```bash
# Optional: Set default vision model
export MCP_VISION_MODEL=llava

# Optional: Set Ollama URL
export OLLAMA_URL=http://localhost:11434
```

---

## Performance Tips

1. **Use Batch Processing** — Proses multiple images sekaligus lebih cepat daripada sequential
2. **Enable Caching** — Hindari re-analysis gambar yang sama
3. **Choose Right Model** — Gunakan "fast" untuk quick checks, "quality" untuk detailed analysis
4. **Use OCR Fallback** — Untuk text-heavy images, hybrid approach lebih reliable
5. **Enhance Before Analysis** — Gambar buram/blurry lebih baik di-enhance terlebih dahulu
6. **Adjust Batch Size** — Sesuaikan `max_parallel` berdasarkan resource sistem

---

## Troubleshooting

### Low Confidence Scores
- Gunakan `enhance_image()` sebelum analysis
- Coba model yang berbeda (quality vs fast)
- Gunakan `analyze_with_ocr_fallback()` untuk text-heavy images

### OCR Not Available
```bash
pip install paddleocr paddlepaddle --break-system-packages
```

### Video Analysis Fails
```bash
pip install opencv-python --break-system-packages
```

### Cache Not Working
- Cache key di-generate dari `hash(image_path + prompt + model)`
- Pastikan ketiga parameter sama untuk cache hit
- Gunakan `clear_vision_cache()` untuk reset

### Out of Memory (Batch Processing)
- Kurangi `max_parallel` (default: 4)
- Proses dalam multiple smaller batches
- Monitor memory usage dengan `get_vision_stats()`

---

## Comparison: Base vs Enhanced

| Feature | Base Vision | Enhanced Vision |
|---------|-------------|-----------------|
| Basic Image Analysis | ✅ | ✅ |
| PDF Analysis | ✅ | ✅ |
| Confidence Scoring | ❌ | ✅ |
| Smart Caching | ❌ | ✅ |
| Batch Processing | ❌ | ✅ |
| Image Comparison | ❌ | ✅ |
| Structured Extraction | ❌ | ✅ |
| Image Enhancement | ❌ | ✅ |
| URL Support | ❌ | ✅ |
| OCR Hybrid | ❌ | ✅ |
| Video Frame Analysis | ❌ | ✅ |
| Progress Callbacks | ❌ | ✅ |
| Model Profiles | ❌ | ✅ |

---

## Next Steps

1. **Test Enhanced Tools**: Coba contoh-contoh di atas
2. **Benchmark Performance**: Bandingkan hasil dengan base vision
3. **Customize untuk Use Case**: Sesuaikan schema, prompts, dan thresholds
4. **Integrate ke Workflow**: Gunakan dalam pipeline yang lebih besar
5. **Monitor dan Optimize**: Track confidence scores dan processing times
