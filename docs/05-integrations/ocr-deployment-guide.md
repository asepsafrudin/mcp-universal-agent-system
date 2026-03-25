# 📘 Deployment Guide - OCR Implementations

## ⚠️ Environment Compatibility Notice

**PaddleOCR** tidak kompatibel dengan Python versi terbaru di MCP environment.  
**Solusi:** Jalankan implementasi di environment **Bangda_PUU** yang sudah terkonfigurasi dengan PaddleOCR.

---

## 🎯 Environment Mapping

| Komponen | MCP Environment | Bangda_PUU Environment |
|----------|-----------------|------------------------|
| **Python Version** | 3.12 (latest) | 3.9/3.10 (stable) |
| **PaddleOCR** | ❌ Not supported | ✅ Available |
| **Vision Model (Ollama)** | ✅ Available | ✅ Available |
| **Recommended Use** | Vision OCR Local | PaddleOCR Optimized |

---

## 🚀 Deployment Options

### Option 1: Copy Files ke Bangda_PUU (Recommended)

```bash
# 1. Copy implementasi ke Bangda_PUU
cp /home/aseps/MCP/scripts/paddle_ocr_optimized.py \
   /home/aseps/Bangda_PUU/Dokumentasi_scanner/scripts/

cp /home/aseps/MCP/scripts/vision_ocr_local.py \
   /home/aseps/Bangda_PUU/Dokumentasi_scanner/scripts/

# 2. Jalankan di Bangda_PUU environment
cd /home/aseps/Bangda_PUU/Dokumentasi_scanner
python scripts/paddle_ocr_optimized.py -i input_dir -o output_dir
```

### Option 2: Gunakan Vision OCR di MCP (Alternative)

Karena Vision OCR menggunakan Ollama (via HTTP API), bisa berjalan di MCP:

```bash
# Pastikan Ollama running
curl http://localhost:11434/api/tags

# Jalankan Vision OCR
cd /home/aseps/MCP
python scripts/vision_ocr_local.py -i input_dir -o output_dir -m llava
```

---

## 📋 Pre-Deployment Checklist

### Untuk PaddleOCR Optimized (Bangda_PUU)

```bash
# 1. Verifikasi environment
cd /home/aseps/Bangda_PUU/Dokumentasi_scanner
python --version  # Should be 3.9 or 3.10

# 2. Cek PaddleOCR tersedia
python -c "from paddleocr import PaddleOCR; print('✅ PaddleOCR OK')"

# 3. Cek dependencies lain
python -c "import cv2; import fitz; import psutil; print('✅ All deps OK')"

# 4. Test dengan file kecil
mkdir -p test_input test_output
cp /path/to/sample.pdf test_input/
python scripts/paddle_ocr_optimized.py -i test_input -o test_output
```

### Untuk Vision OCR Local (MCP atau Bangda_PUU)

```bash
# 1. Verifikasi Ollama
curl http://localhost:11434/api/tags

# 2. Pastikan model tersedia
ollama list | grep llava

# 3. Test vision model
python scripts/vision_ocr_local.py -i test_input -o test_output
```

---

## 🔧 Konfigurasi per Environment

### Bangda_PUU (PaddleOCR Optimized)

**File:** `scripts/paddle_ocr_optimized.py`

```python
# Config untuk Bangda_PUU
config = OptimizedConfig()
config.MAX_WORKERS = 2              # Optimal untuk 4-core
config.BATCH_SIZE = 5               # Sesuaikan memory
config.CONFIDENCE_THRESHOLD = 0.75  # Tinggi untuk akurasi
config.PDF_RESOLUTION_ADAPTIVE = True
```

**Command:**
```bash
python scripts/paddle_ocr_optimized.py \
    -i /path/to/input \
    -o /path/to/output \
    -w 2 \
    --confidence 0.75
```

### MCP (Vision OCR Local)

**File:** `scripts/vision_ocr_local.py`

```python
# Config untuk MCP
router = LocalVisionOCRRouter(
    input_dir="input",
    output_dir="output",
    ollama_model="llava",              # atau "moondream2" untuk cepat
    vision_confidence_threshold=0.7,
    use_enhancement=True
)
```

**Command:**
```bash
python scripts/vision_ocr_local.py \
    -i /path/to/input \
    -o /path/to/output \
    -m llava \
    --vision-threshold 0.7
```

---

## 📁 File Locations

### Source Files (MCP)
```
/home/aseps/MCP/scripts/
├── paddle_ocr_optimized.py      # Untuk Bangda_PUU
├── vision_ocr_local.py          # Untuk MCP atau Bangda_PUU
└── test_ocr_implementations.py  # Test suite
```

### Deployment Target (Bangda_PUU)
```
/home/aseps/Bangda_PUU/Dokumentasi_scanner/scripts/
├── paddle_ocr_optimized.py      # Copy file ini
├── vision_ocr_local.py          # Copy file ini
└── (existing files...)
```

---

## 🔄 Workflow Hybrid (Recommended)

Untuk hasil terbaik, gunakan kedua environment:

### Step 1: High-Volume Processing (Bangda_PUU)
```bash
# Process 100+ files dengan PaddleOCR (cepat)
cd /home/aseps/Bangda_PUU/Dokumentasi_scanner
python scripts/paddle_ocr_optimized.py \
    -i batch_input \
    -o batch_output \
    -w 4
```

### Step 2: Quality Check (MCP)
```bash
# Review hasil dengan Vision Model (akurat)
cd /home/aseps/MCP
python scripts/vision_ocr_local.py \
    -i batch_output/low_confidence \
    -o quality_check \
    -m llava
```

---

## ⚡ Performance Expectations

### Bangda_PUU (PaddleOCR)
- **Speed:** ~2-5 detik/halaman
- **Throughput:** ~500-1000 halaman/jam
- **Resource:** CPU intensive, low memory
- **Best for:** Bulk processing, forms, tables

### MCP (Vision OCR)
- **Speed:** ~20-60 detik/halaman
- **Throughput:** ~60-180 halaman/jam
- **Resource:** Moderate CPU, Ollama memory
- **Best for:** Quality check, complex layouts

---

## 🐛 Troubleshooting

### Issue: "PaddleOCR not initialized"
**Cause:** Running di MCP environment  
**Solution:** Copy ke Bangda_PUU dan jalankan dari sana

### Issue: "Ollama not available"
**Cause:** Ollama service tidak running  
**Solution:** 
```bash
# Start Ollama
ollama serve &

# Verify
curl http://localhost:11434/api/tags
```

### Issue: "No module named 'langchain'"
**Cause:** Missing dependency  
**Solution:**
```bash
pip install langchain
# atau
cd /home/aseps/Bangda_PUU && source .venv/bin/activate
```

---

## 📊 Monitoring

### Check Progress
```bash
# Bangda_PUU - Real-time logs
tail -f logs/paddle_optimized.log

# MCP - Real-time logs
tail -f logs/vision_ocr_local.log
```

### Check Results
```bash
# View results JSON
cat output/results.json | jq '.stats'

# Count processed files
ls output/*.md | wc -l
```

---

## 🎓 Best Practices

1. **Selalu test dengan sample kecil dulu**
   ```bash
   mkdir -p test_input && cp sample.pdf test_input/
   python script.py -i test_input -o test_output
   ```

2. **Monitor memory usage**
   ```bash
   watch -n 5 'ps aux | grep python'
   ```

3. **Enable resume capability**
   - Jangan hapus `processing_state.json`
   - Script akan auto-resume jika interrupted

4. **Use caching**
   - Hasil OCR di-cache berdasarkan file hash
   - Re-running tidak akan re-process file yang sama

---

## 📞 Quick Reference

| Task | Command | Environment |
|------|---------|-------------|
| **Bulk OCR** | `paddle_ocr_optimized.py` | Bangda_PUU |
| **Quality Check** | `vision_ocr_local.py` | MCP |
| **Test** | `test_ocr_implementations.py` | Both |
| **Benchmark** | `benchmark_vision_models.py` | MCP |

---

## ✅ Deployment Checklist

- [ ] Copy files ke Bangda_PUU (jika pakai PaddleOCR)
- [ ] Verifikasi Python version compatible
- [ ] Test dengan 1-2 sample files
- [ ] Monitor memory dan CPU
- [ ] Verify output quality
- [ ] Production run

---

*Last Updated: 27 Februari 2026*  
*Note: PaddleOCR requires Python 3.9/3.10, use Bangda_PUU environment*
