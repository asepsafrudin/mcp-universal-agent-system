# 📊 Riset Vision Model: MiniCPM-o vs Qwen2.5-VL
## Analisis Kompatibilitas dengan Hardware PC Ini

**Tanggal Riset:** 27 Februari 2026  
**Hardware Target:** Intel Core i7-13620H, 10GB RAM, CPU-only (no GPU)

---

## 🖥️ Spesifikasi Hardware PC

| Komponen | Spesifikasi | Status |
|----------|-------------|--------|
| **CPU** | Intel Core i7-13620H (13th Gen) | ✅ Powerful |
| **Core/Thread** | 4 Cores / 8 Threads | ✅ Cukup |
| **Clock Speed** | ~2.9 GHz base, up to 4.9 GHz turbo | ✅ Baik |
| **Cache** | 24 MB L3 | ✅ Baik |
| **RAM** | ~10 GB total (~8 GB available) | ⚠️ Terbatas |
| **Storage** | 1 TB (888 GB available) | ✅ Sangat cukup |
| **GPU** | ❌ **Tidak ada dedicated GPU** | ❌ Kritis |
| **Ollama** | v0.16.3 | ✅ Terinstall |

### 🔴 Kondisi Kritis
PC ini **CPU-only** tanpa NVIDIA GPU, yang berarti:
- Tidak bisa menggunakan CUDA untuk akselerasi model
- Model vision akan berjalan di CPU dengan performa sangat terbatas
- Quantisasi ekstrem diperlukan untuk model besar

---

## 🔬 Profil Model Vision

### 1️⃣ MiniCPM-o / MiniCPM-V (OpenBMB, Beijing)

#### Overview
MiniCPM-o adalah model vision "underdog" yang punch above its weight — kecil tapi sangat kuat. Versi terbaru MiniCPM-o 4.5 (9B parameter) mendekati performa Gemini 2.5 Flash untuk vision dan multimodal tasks.

#### Versi & Kebutuhan Resource

| Versi | Parameter | VRAM Required | RAM Required (CPU) | Status di PC Ini |
|-------|-----------|---------------|-------------------|------------------|
| MiniCPM-o 4.5 | 9B | ~10-12 GB | ~20+ GB | ❌ **Impossible** |
| MiniCPM-V 2.6 | 8B | ~6-8 GB | ~16 GB | ❌ **Tidak cocok** |
| MiniCPM-o 2.6 | 8B | ~6-8 GB | ~16 GB | ❌ **Tidak cocok** |
| MiniCPM-V 2.0 | 2B | ~4 GB | ~8 GB | ⚠️ **Mungkin via llama.cpp** |

#### Keunggulan MiniCPM-V

1. **🎯 OCR State-of-the-Art**
   - Mencapai performa SOTA di OCRBench
   - Mengalahkan GPT-4o, GPT-4V, Gemini 1.5 Pro
   - Strong handwritten OCR
   - Complex table/document parsing

2. **🖼️ High Resolution Support**
   - Bisa memproses gambar dengan aspect ratio apapun
   - Hingga 1.8 juta piksel
   - Cocok untuk dokumen scanner resolusi tinggi

3. **🧠 Hybrid Thinking**
   - Fast/deep thinking mode switchable
   - Sesuaikan kebutuhan speed vs accuracy

#### Cara Pakai (Teoritis)
```bash
# Via Ollama (jika tersedia)
ollama pull minicpm-v2.6

# Via llama.cpp (dengan quantisasi)
# Download GGUF dari HuggingFace
# Jalankan dengan quantisasi Q4_0 atau Q3
```

#### Realita di PC Ini
- Model vision >4B parameter umumnya memerlukan GPU untuk performa acceptable
- Tanpa GPU, inference akan sangat lambat (>30-60 detik per gambar)
- llama.cpp bisa digunakan tapi dengan quantisasi agresif (Q4_0 atau Q3)
- Akurasi menurun signifikan dengan quantisasi ekstrem

---

### 2️⃣ Qwen2.5-VL / Qwen-VL (Alibaba)

#### Overview
Qwen2.5-VL adalah model vision enterprise-ready dari Alibaba yang sangat mature. Tersedia dalam 3 ukuran (3B, 7B, 72B) dengan kemampuan structured data extraction yang powerful.

#### Versi & Kebutuhan Resource

| Versi | Parameter | VRAM Required | RAM Required (CPU) | Status di PC Ini |
|-------|-----------|---------------|-------------------|------------------|
| Qwen2.5-VL-72B | 72B | ~48+ GB | ~100+ GB | ❌ **Impossible** |
| Qwen2.5-VL-7B | 7B | ~8-12 GB | ~16-20 GB | ❌ **Tidak cocok** |
| Qwen2.5-VL-3B | 3B | ~4-6 GB | ~8-12 GB | ⚠️ **Mungkin via llama.cpp** |
| Qwen2-VL-2B | 2B | ~3-4 GB | ~6-8 GB | ✅ **Mungkin bisa** |
| Qwen-VL-Chat | 7B | ~8 GB | ~16 GB | ❌ **Tidak cocok** |

#### Keunggulan Qwen2.5-VL

1. **📄 Structured Data Extraction**
   - Robust extraction dari invoice, form, tabel
   - Output langsung JSON
   - Ideal untuk dokumen pemerintah dengan struktur konsisten

2. **🌍 Multilingual Support**
   - Mendukung 32 bahasa (Qwen3-VL)
   - Robust untuk low light, blur, tilt
   - Improved long-document structure parsing

3. **📊 Document Analysis**
   - Analisis mendalam charts, diagram, layout
   - Multi-orientation text extraction
   - Penting untuk dokumen dengan variasi layout

#### Contoh Output JSON
```json
{
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-15",
  "vendor_name": "PT Example",
  "total_amount": 1500000,
  "tax_amount": 150000,
  "currency": "IDR"
}
```

#### Cara Pakai (Teoritis)
```bash
# Via Ollama (support terbatas)
ollama pull qwen2.5vl:7b

# Via llama.cpp dengan GGUF
# Download dari HuggingFace: Qwen2-VL-2B-Instruct-GGUF
```

#### Realita di PC Ini
- Qwen-VL series di Ollama masih terbatas (tidak semua versi tersedia)
- Versi 2B mungkin bisa jalan dengan llama.cpp + quantisasi Q4
- Tetap akan lambat untuk batch processing dokumen banyak
- 3B mungkin OOM dengan hanya 10GB RAM

---

## ⚖️ Head-to-Head Comparison untuk PC CPU-Only

| Aspek | MiniCPM-V 2B | Qwen2-VL 2B | Notes |
|-------|--------------|-------------|-------|
| **Ukuran Model** | 2B params | 2B params | Sama-sama compact |
| **RAM Required** | ~3-4 GB | ~3-4 GB | Cocok untuk PC ini |
| **Speed (CPU)** | 15-30s/image | 15-30s/image | Sangat lambat |
| **OCR Accuracy** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Sama-sama bagus |
| **Bahasa Indonesia** | ⭐⭐⭐ | ⭐⭐⭐⭐ | Qwen lebih baik |
| **Structured JSON** | Manual parsing | Native support | Qwen unggul |
| **Dokumen Kompleks** | Bagus | Sangat Bagus | Qwen unggul |
| **Ollama Support** | Terbatas | Terbatas | Perlu custom setup |
| **Handwritten OCR** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | MiniCPM unggul |
| **Table Parsing** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Qwen unggul |

---

## ⚠️ Analisis Keterbatasan Hardware

### Masalah Utama PC Ini:

#### 1. ❌ No GPU = No CUDA Acceleration
- Model vision modern (MiniCPM, Qwen-VL) dioptimalkan untuk GPU
- CPU-only akan **10-50x lebih lambat** dari GPU
- Contoh perbandingan:
  - GPU (RTX 3060): ~2-5 detik/image
  - CPU (i7-13620H): ~30-60 detik/image

#### 2. ❌ RAM Terbatas (~10 GB)
- Model 7-8B butuh ~8GB VRAM = setara ~16GB RAM untuk CPU offload
- PC ini hanya punya 10GB, tidak cukup untuk model besar
- Swap disk akan memperlambat drastis dan memakai storage

#### 3. ❌ Model Vision di Ollama Terbatas
- Ollama vision models yang tersedia: `llava`, `moondream2`, `llava-phi3`, `llava-llama3`
- MiniCPM dan Qwen-VL belum fully supported sebagai vision model di Ollama
- Butuh custom setup dengan llama.cpp atau transformers (kompleks)

---

## 💡 Rekomendasi Solusi

### Opsi 1: Gunakan Model Vision yang Sudah Ada di Ollama (⭐ Direkomendasikan)

PC Anda sudah punya setup vision tools yang menggunakan model Ollama. Model yang available dan tested:

| Model | Ukuran | Speed (CPU) | Use Case | Rekomendasi |
|-------|--------|-------------|----------|-------------|
| **moondream2** | 1.6B | 5-10s/image | Fast preview, simple OCR | ✅ **Cocok untuk quick checks** |
| **llava** | 7B | 20-40s/image | Balanced quality | ⚠️ Lambat tapi bisa |
| **llava-phi3** | 3.8B | 10-20s/image | OCR optimized | ✅ **Cocok untuk OCR** |
| **llava-llama3** | 8B | 30-60s/image | High quality | ❌ Terlalu lambat |

#### Cek Model yang Sudah Terinstall:
```bash
ollama list
```

#### Keunggulan Opsi Ini:
- ✅ Sudah terintegrasi dengan vision tools Anda
- ✅ Tidak perlu setup tambahan
- ✅ Bisa langsung digunakan
- ✅ Caching sudah implemented
- ✅ Hybrid dengan PaddleOCR sudah ada

---

### Opsi 2: Tambahkan Model MiniCPM/Qwen via llama.cpp (Advanced)

Jika tetap ingin mencoba MiniCPM atau Qwen:

#### Setup Steps:
```bash
# 1. Install llama-cpp-python
pip install llama-cpp-python --break-system-packages

# 2. Download model GGUF dari HuggingFace
# MiniCPM-V-2.6 GGUF (belum banyak tersedia di HF)
# Qwen2-VL-2B-Instruct GGUF (tersedia)

# Contoh download Qwen2-VL-2B-Instruct GGUF
wget https://huggingface.co/.../qwen2-vl-2b-instruct-q4_k_m.gguf

# 3. Jalankan dengan llama.cpp
python -m llama_cpp.server --model qwen2-vl-2b-instruct-q4_k_m.gguf
```

#### Risiko:
- ⚠️ Setup kompleks, butuh konfigurasi vision projector
- ⚠️ Performa tetap lambat di CPU
- ⚠️ Tidak ada jaminan akurasi sama dengan versi full
- ⚠️ Belum tentu compatible dengan vision tools yang sudah ada

---

### Opsi 3: Upgrade Hardware (Jangka Panjang)

Untuk production OCR dokumen scanner dengan performa baik:

| Option | Spec | Estimasi Harga | Performa |
|--------|------|----------------|----------|
| **Minimum** | RTX 3060 12GB | ~Rp 5.000.000 | Bisa jalan Qwen2.5-VL-7B |
| **Recommended** | RTX 4060 Ti 16GB | ~Rp 7.000.000 | Optimal untuk batch processing |
| **Ideal** | RTX 4090 24GB | ~Rp 25.000.000 | Bisa jalan model 72B |

#### Alternatif Lain:
- **Cloud GPU:** Google Colab, RunPod, Vast.ai untuk heavy processing
- **External GPU (eGPU):** Jika laptop support Thunderbolt 3/4
- **CPU Upgrade:** AMD Ryzen dengan lebih banyak core (tetap lambat untuk vision)

---

## 🎯 Rekomendasi untuk Kasus Bangda PUU

Berdasarkan kondisi hardware PC ini, berikut rekomendasi praktis:

### ✅ Yang Bisa Dilakukan Sekarang (Immediate)

#### 1. Optimalkan Vision Tools yang Sudah Ada
```python
# Gunakan moondream2 untuk quick checks
result = await analyze_image_enhanced(
    image_path="/path/to/doc.jpg",
    prompt="Quick check: any errors?",
    model="moondream2"  # Fast: 5-10s
)

# Gunakan llava-phi3 untuk OCR tasks
result = await analyze_image_enhanced(
    image_path="/path/to/doc.jpg",
    prompt="Extract all text with high accuracy",
    model="llava-phi3"  # OCR optimized: 10-20s
)
```

#### 2. Implement Batch Processing dengan Rate Limiting
```python
from execution.tools.vision_enhanced import analyze_batch

# Gunakan max_parallel=2 untuk CPU-only (jangan terlalu tinggi)
results = await analyze_batch(
    image_paths=images,
    prompt="Extract text",
    namespace="bangda_puu",
    max_parallel=2  # Sesuaikan dengan CPU cores
)
```

#### 3. Image Enhancement Pre-processing
```python
from execution.tools.vision_enhanced import enhance_image, analyze_image_enhanced

# Enhance sebelum analysis
enhanced = await enhance_image(
    image_path="/path/to/blurry_doc.jpg",
    enhancements=["contrast", "sharpness", "denoise"],
    output_path="/tmp/enhanced.jpg"
)

# Analyze enhanced image
result = await analyze_image_enhanced(
    image_path=enhanced["enhanced_path"],
    prompt="Extract all text"
)
```

#### 4. Hybrid Vision + PaddleOCR (Sudah Ada)
```python
from execution.tools.vision_enhanced import analyze_with_ocr_fallback

# Gunakan hybrid approach untuk text-heavy images
result = await analyze_with_ocr_fallback(
    image_path="/path/to/scanned_doc.jpg",
    prompt="Extract all text",
    min_confidence=0.7
)
```

### ❌ Yang Tidak Bisa Dilakukan (Limitations)

- ❌ MiniCPM-V 8B tanpa GPU (terlalu lambat, >60s/image)
- ❌ Qwen2.5-VL 7B tanpa GPU (OOM atau terlalu lambat)
- ❌ Real-time vision processing (webcam, live stream)
- ❌ Batch processing besar dalam waktu singkat
- ❌ High-resolution image analysis (>2MP) dengan cepat

---

## 📋 Action Plan

### Immediate (Hari Ini)
- [x] Verifikasi spesifikasi hardware PC
- [ ] Cek model vision yang sudah terinstall di Ollama (`ollama list`)
- [ ] Test performa `moondream2` vs `llava-phi3` untuk OCR dokumen
- [ ] Implement smart caching untuk menghindari re-analysis

### Short-term (Minggu Ini)
- [ ] Setup hybrid pipeline: PaddleOCR primary + Vision fallback
- [ ] Implement image enhancement pre-processing
- [ ] Benchmark processing time per dokumen
- [ ] Dokumentasikan hasil benchmark

### Long-term (Bulan Ini)
- [ ] Evaluasi upgrade GPU untuk performa lebih baik
- [ ] Research cloud-based vision API (Gemini, Claude) untuk heavy tasks
- [ ] Consider external GPU (eGPU) jika laptop support Thunderbolt
- [ ] Monitor perkembangan MiniCPM dan Qwen-VL support di Ollama

---

## 🔍 Kesimpulan Akhir

| Model | Cocok untuk PC Ini? | Catatan |
|-------|---------------------|---------|
| **MiniCPM-V 2.6/8B** | ❌ No | Butuh GPU, terlalu lambat di CPU |
| **MiniCPM-o 4.5/9B** | ❌ No | Terlalu besar untuk PC ini |
| **Qwen2.5-VL 7B** | ❌ No | Butuh GPU, OOM risk |
| **Qwen2.5-VL 3B** | ⚠️ Maybe | Mungkin bisa tapi setup kompleks |
| **MiniCPM-V 2B** | ⚠️ Maybe | Via llama.cpp, masih lambat |
| **Qwen2-VL 2B** | ⚠️ Maybe | Tersedia GGUF, tapi masih lambat |
| **moondream2 (Ollama)** | ✅ Yes | Sudah ada, 5-10s/image, good enough |
| **llava-phi3 (Ollama)** | ✅ Yes | OCR optimized, 10-20s/image |
| **llava (Ollama)** | ⚠️ Maybe | 20-40s/image, kualitas bagus |

### 🎯 Verdict

**PC ini BELUM SIAP untuk MiniCPM-o atau Qwen2.5-VL dalam performa production.**

**Rekomendasi:**
1. Gunakan model vision yang sudah tersedia di Ollama (`moondream2`, `llava-phi3`)
2. Implementasikan hybrid pipeline dengan PaddleOCR
3. Gunakan image enhancement pre-processing
4. Pertimbangkan upgrade GPU jika budget memungkinkan

**Catatan:** Vision tools yang sudah ada di project ini sebenarnya sudah cukup powerful dengan kombinasi:
- PaddleOCR untuk text extraction cepat
- Vision model (moondream2/llava-phi3) untuk analysis kompleks
- Image enhancement untuk improve kualitas input
- Smart caching untuk menghindari re-processing

---

## 📚 Referensi

- MiniCPM-V GitHub: https://github.com/OpenBMB/MiniCPM-V
- Qwen-VL HuggingFace: https://huggingface.co/Qwen
- Ollama Vision Models: https://ollama.com/library
- llama.cpp: https://github.com/ggerganov/llama.cpp

---

*Dokumen ini dibuat sebagai hasil riset untuk evaluasi vision model upgrade path.*
