# 05-integrations — Integrasi Third-Party

Dokumentasi integrasi dengan sistem dan layanan eksternal.

## 📋 Konten

| File | Deskripsi |
|------|-----------|
| [`antigravity.md`](./antigravity.md) | Antigravity MCP integration |
| [`discovery-portability.md`](./discovery-portability.md) | Discovery & portability design |
| [`lan-distributed.md`](./lan-distributed.md) | LAN-based distributed MCP |
| [`lan-implementation.md`](./lan-implementation.md) | Implementasi LAN distributed |
| [`meshcentral-separation.md`](./meshcentral-separation.md) | MeshCentral separation plan |
| [`vision-tools-usage.md`](./vision-tools-usage.md) | Vision Tools - Base (Image & PDF analysis) |
| [`vision-enhanced-usage.md`](./vision-enhanced-usage.md) | 🆕 Enhanced Vision Tools (Advanced capabilities) |

## 🔌 Integrasi Utama

### Antigravity MCP

Integrasi dengan Antigravity MCP untuk extended filesystem capabilities:

- Konfigurasi di `antigravity-mcp-config.json`
- Server: `rust-mcp-filesystem`
- Capabilities: Advanced file operations

📄 Detail: [`antigravity.md`](./antigravity.md)

## 🌐 LAN Distributed MCP

### Arsitektur Distributed

Sistem MCP yang dapat berjalan di multiple nodes dalam LAN:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Node 1    │◄───►│   Node 2    │◄───►│   Node 3    │
│  (Master)   │     │  (Worker)   │     │  (Worker)   │
└──────┬──────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│   Shared    │
│   Memory    │
└─────────────┘
```

📄 Detail: [`lan-distributed.md`](./lan-distributed.md)
📄 Implementasi: [`lan-implementation.md`](./lan-implementation.md)

## 🔍 Discovery & Portability

### Problem Statement

> "Bagaimana agent baru yang dibuka di folder manapun bisa langsung menemukan bahwa MCP hub ini ada, mengetahui tools yang tersedia, dan mendapatkan konteks yang relevan — tanpa setup manual."

### Solusi yang Dirancang

1. **Service Discovery**: Auto-detection MCP hub
2. **Context Injection**: Automatic context provision
3. **Tool Registry**: Dynamic tool discovery

📄 Detail: [`discovery-portability.md`](./discovery-portability.md)

## 🔧 MeshCentral Separation

Rencana pemisahan MeshCentral dari core MCP:

- **Timeline**: 10 hari
- **Rationale**: Separation of concerns
- **Migration steps**: Documented

📄 Detail: [`meshcentral-separation.md`](./meshcentral-separation.md)

## 👁️ Vision Tools

Vision Tools memungkinkan AI untuk menganalisis gambar dan PDF menggunakan model vision lokal via Ollama.

### 🆕 Enhanced Vision Tools (Baru!)

Enhanced Vision Tools menyediakan kemampuan analisis gambar yang lebih powerful dengan fitur-fitur canggih:

| Feature | Deskripsi |
|---------|-----------|
| **Confidence Scoring** | Reliability metrics untuk setiap analysis |
| **Smart Caching** | Hindari re-analysis dengan cache otomatis |
| **Batch Processing** | Proses multiple images secara parallel |
| **Image Comparison** | Bandingkan 2+ gambar untuk identifikasi perbedaan |
| **Structured Extraction** | Ekstrak data terstruktur (JSON) dari gambar |
| **Image Enhancement** | Auto-enhance sebelum analysis (contrast, sharpness, denoise) |
| **URL Support** | Analisis gambar langsung dari URL |
| **OCR Hybrid** | Kombinasi vision + PaddleOCR untuk text extraction terbaik |
| **Video Frame Analysis** | Extract dan analyze frames dari video |
| **Progress Callbacks** | Real-time progress updates untuk long operations |

### Tools Tersedia

#### Base Vision Tools
| Tool | Fungsi |
|------|--------|
| `analyze_image` | Analisis gambar tunggal |
| `analyze_pdf_pages` | Analisis PDF halaman demi halaman |
| `list_vision_results` | List hasil analisis tersimpan |

#### Enhanced Vision Tools
| Tool | Fungsi |
|------|--------|
| `analyze_image_enhanced` | Analisis dengan confidence scoring & caching |
| `analyze_batch` | Batch processing multiple images |
| `compare_images` | Bandingkan multiple images |
| `extract_structured_data` | Ekstrak data terstruktur (JSON) |
| `enhance_image` | Image enhancement (contrast, sharpness, denoise) |
| `analyze_image_url` | Analisis gambar dari URL |
| `analyze_with_ocr_fallback` | Vision + OCR hybrid approach |
| `analyze_video_frames` | Analisis frames dari video |
| `clear_vision_cache` | Clear vision cache |
| `get_vision_stats` | Get vision system statistics |

### Quick Start

```python
# Basic enhanced analysis
from execution.tools.vision_enhanced import analyze_image_enhanced

result = await analyze_image_enhanced(
    image_path="/home/aseps/MCP/screenshot.png",
    prompt="Describe this UI",
    return_confidence=True
)

print(f"Description: {result.content}")
print(f"Confidence: {result.confidence:.0%}")
```

### Setup

```bash
# Base Dependencies
pip install Pillow pymupdf --break-system-packages

# Untuk OCR Hybrid
pip install paddleocr paddlepaddle --break-system-packages

# Untuk Video Analysis
pip install opencv-python --break-system-packages

# Vision Models
ollama pull llava          # Balanced (default)
ollama pull moondream2     # Fast
ollama pull llava-llama3   # High quality
ollama pull llava-phi3     # OCR-optimized
```

📄 **Base Vision**: [`vision-tools-usage.md`](./vision-tools-usage.md)
📄 **Enhanced Vision**: [`vision-enhanced-usage.md`](./vision-enhanced-usage.md)

## 📖 Related Documentation

- **Architecture** → [`../02-architecture/`](../02-architecture/)
- **Database** → [`../06-database/`](../06-database/)
- **Getting Started** → [`../01-getting-started/`](../01-getting-started/)
