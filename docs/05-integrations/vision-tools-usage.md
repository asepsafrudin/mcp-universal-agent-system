# Vision Tools - Cara Penggunaan

> **🆕 Enhanced Vision Tools Tersedia!** 
> 
> Dokumentasi ini mencakup **Base Vision Tools**. Untuk kemampuan yang lebih powerful dengan batch processing, confidence scoring, structured extraction, OCR hybrid, dan lebih banyak fitur, lihat [Vision Enhanced Usage](./vision-enhanced-usage.md).

## Overview

Vision Tools memungkinkan AI untuk **melihat dan menganalisis gambar serta PDF** menggunakan model vision lokal via Ollama. Semua processing dilakukan **secara lokal** - tidak ada data yang dikirim ke cloud.

## Quick Comparison

| Feature | Base Vision | [Enhanced Vision](./vision-enhanced-usage.md) |
|---------|-------------|-----------------------------------------------|
| Basic Image Analysis | ✅ | ✅ |
| PDF Analysis | ✅ | ✅ |
| **Confidence Scoring** | ❌ | ✅ |
| **Smart Caching** | ❌ | ✅ |
| **Batch Processing** | ❌ | ✅ |
| **Image Comparison** | ❌ | ✅ |
| **Structured Extraction** | ❌ | ✅ |
| **Image Enhancement** | ❌ | ✅ |
| **URL Support** | ❌ | ✅ |
| **OCR Hybrid** | ❌ | ✅ |
| **Video Analysis** | ❌ | ✅ |

## Tools yang Tersedia (Base)

### 1. `analyze_image`
Menganalisis gambar tunggal (screenshot, foto, diagram, dll).

**Contoh Penggunaan:**

```python
from execution.tools.vision_tools import analyze_image

# Analisis screenshot UI
result = await analyze_image(
    image_path="/home/aseps/MCP/screenshot.png",
    prompt="Describe this UI and identify any error messages",
    namespace="my_project"
)

# Result:
# {
#     "success": True,
#     "description": "The screenshot shows a web application with a red error banner...",
#     "model": "moondream2",
#     "image_path": "/home/aseps/MCP/screenshot.png",
#     "namespace": "my_project"
# }
```

**Parameters:**
- `image_path` (required): Path absolut ke file gambar
- `prompt` (optional): Instruksi untuk vision model (default: "Describe this image in detail")
- `namespace` (optional): Namespace untuk menyimpan hasil ke memory
- `save_to_memory` (optional): Simpan hasil ke LTM (default: True)
- `model` (optional): Override model (default: dari env MCP_VISION_MODEL)

**Use Cases:**
- Debug UI errors dari screenshot
- Analisis diagram atau chart
- Membaca text dari gambar (OCR)
- Identifikasi objek dalam foto

---

### 2. `analyze_pdf_pages`
Mengekstrak dan menganalisis halaman PDF sebagai gambar.

**Contoh Penggunaan:**

```python
from execution.tools.vision_tools import analyze_pdf_pages

# Analisis semua halaman PDF
result = await analyze_pdf_pages(
    pdf_path="/home/aseps/MCP/document.pdf",
    prompt="Extract all text and describe any charts or tables",
    namespace="my_project"
)

# Analisis halaman tertentu saja
result = await analyze_pdf_pages(
    pdf_path="/home/aseps/MCP/report.pdf",
    prompt="Extract key findings and statistics",
    pages=[0, 1, 5],  # Halaman 1, 2, dan 6 (0-indexed)
    namespace="my_project"
)

# Result:
# {
#     "success": True,
#     "pages_analyzed": 3,
#     "total_pages": 10,
#     "content": "## Page 1\nThis report shows...\n\n## Page 2\nThe chart indicates...",
#     "per_page": [
#         {"page": 1, "content": "This report shows..."},
#         {"page": 2, "content": "The chart indicates..."}
#     ]
# }
```

**Parameters:**
- `pdf_path` (required): Path absolut ke file PDF
- `prompt` (optional): Instruksi untuk setiap halaman
- `pages` (optional): List nomor halaman (0-indexed). None = semua halaman
- `namespace` (optional): Namespace untuk memory
- `save_to_memory` (optional): Simpan hasil ke LTM (default: True)
- `model` (optional): Override model

**Use Cases:**
- Ekstrak text dari PDF yang tidak bisa di-copy
- Analisis dokumen scan atau foto dokumen
- Membaca laporan dengan chart/table
- Proses invoice atau receipt

---

### 3. `list_vision_results`
Melihat hasil analisis vision yang tersimpan di memory.

**Contoh Penggunaan:**

```python
from execution.tools.vision_tools import list_vision_results

# List hasil analisis
results = await list_vision_results(
    namespace="my_project",
    limit=10
)

# Result:
# {
#     "results": [
#         {
#             "key": "vision:screenshot.png",
#             "content": "The screenshot shows...",
#             "metadata": {"type": "image_analysis", "source": "vision_analysis"}
#         }
#     ]
# }
```

---

## Via MCP Registry

Semua vision tools juga bisa dipanggil via registry:

```python
from execution.registry import registry

# Analyze image via registry
result = await registry.execute("analyze_image", {
    "image_path": "/tmp/screenshot.png",
    "prompt": "What's wrong with this error message?",
    "namespace": "debug_session"
})

# Analyze PDF via registry
result = await registry.execute("analyze_pdf_pages", {
    "pdf_path": "/home/aseps/MCP/report.pdf",
    "pages": [0, 1],
    "namespace": "project_x"
})
```

---

## Via HTTP API (jika server running)

```bash
# Analyze image
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "analyze_image",
    "arguments": {
      "image_path": "/tmp/screenshot.png",
      "prompt": "Describe this UI",
      "namespace": "my_project"
    }
  }'

# Analyze PDF
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "analyze_pdf_pages",
    "arguments": {
      "pdf_path": "/home/aseps/MCP/document.pdf",
      "prompt": "Extract all text",
      "namespace": "my_project"
    }
  }'
```

---

## Alur Kerja Vision Tools

```
User Request
    ↓
[Path Security Check] ← path_utils.is_safe_path()
    ↓
[File Extension Validation]
    ↓
[Image Preprocessing] ← Resize, convert to base64
    ↓
[Ollama Vision API Call] ← curl subprocess with timeout
    ↓
[Save to Memory] ← LTM storage (optional)
    ↓
Return Result
```

---

## Error Handling

Vision tools menggunakan **graceful degradation** - jika ada masalah, akan return error yang jelas:

| Error | Penyebab | Solusi |
|-------|----------|--------|
| "Path outside allowed directories" | Path tidak diizinkan | Gunakan path di /home/aseps/MCP, /app, atau /tmp |
| "Extension '.xyz' not supported" | Format file tidak didukung | Gunakan format: .jpg, .jpeg, .png, .gif, .bmp, .webp, .pdf |
| "File not found" | File tidak ada | Periksa path file |
| "Vision model unavailable" | Ollama tidak running | Jalankan `ollama serve` |
| "Failed to preprocess image" | Pillow error | Pastikan `pip install Pillow` |
| "PyMuPDF tidak terinstall" | fitz tidak ada | Jalankan `pip install pymupdf` |

---

## Keamanan

- **Path validation**: Hanya path di `/app`, `/home/aseps/MCP`, `/tmp` yang diizinkan
- **Sensitive paths rejected**: `/etc`, `/root`, `/proc`, dll ditolak
- **No cloud upload**: Semua processing lokal via Ollama
- **File extension check**: Hanya format gambar dan PDF yang diizinkan

---

## Model Vision

### Model Default: `llava`
- Ukuran: ~4.7GB
- Kecepatan: Moderate
- Kualitas: Baik untuk berbagai use cases
- Recommended untuk: General purpose vision tasks

### Ganti Model
```bash
export MCP_VISION_MODEL=llava:latest  # default
# atau model lain yang tersedia di Ollama
```

---

## Setup (Setelah Memahami Penggunaan)

### 1. Install Dependencies
```bash
cd /home/aseps/MCP/mcp-unified
pip install Pillow pymupdf --break-system-packages
```

### 2. Pull Vision Model
```bash
ollama pull llava
```

### 3. Verifikasi
```bash
ollama list  # Pastikan llava terinstall
```

---

## Contoh Use Cases

### 1. Debug Error dari Screenshot
```python
result = await analyze_image(
    "/home/aseps/MCP/error_screenshot.png",
    prompt="Explain this error message and suggest how to fix it"
)
```

### 2. Analisis Dokumen - Laporan Keuangan
```python
# Analisis laporan keuangan PDF dengan chart dan tabel
result = await analyze_pdf_pages(
    pdf_path="/home/aseps/MCP/laporan_keuangan_q4.pdf",
    prompt="""
    Ekstrak informasi berikut:
    1. Total pendapatan dan pengeluaran
    2. Growth percentage dari quarter sebelumnya
    3. Deskripsikan trend dari chart yang ada
    4. Identifikasi kategori pengeluaran terbesar
    """,
    pages=[0, 1, 2, 3]  # Analisis 4 halaman pertama
)

# Hasil akan berisi:
# {
#     "success": True,
#     "pages_analyzed": 4,
#     "content": "## Page 1\nLaporan Keuangan Q4 2025...\n\n## Page 2\nChart menunjukkan kenaikan 15%..."
# }
```

### 3. Analisis Dokumen - Invoice/Receipt
```python
# Ekstrak data structured dari invoice
result = await analyze_pdf_pages(
    pdf_path="/home/aseps/MCP/invoice_vendor_abc.pdf",
    prompt="""
    Ekstrak data dalam format structured:
    - Invoice Number:
    - Invoice Date:
    - Due Date:
    - Vendor Name:
    - Vendor Address:
    - Total Amount:
    - Tax Amount:
    - Line Items (description, quantity, unit price, total):
    """
)

# Atau dari foto invoice (misalnya foto dari HP)
result = await analyze_image(
    image_path="/home/aseps/MCP/foto_invoice.jpg",
    prompt="Extract all invoice details: invoice number, date, vendor, items purchased, and total amount"
)
```

### 4. Analisis Dokumen - Contract/Perjanjian
```python
# Analisis kontrak untuk ekstrak key terms
result = await analyze_pdf_pages(
    pdf_path="/home/aseps/MCP/contract_vendor.pdf",
    prompt="""
    Analisis dokumen kontrak ini dan ekstrak:
    1. Parties involved (pihak-pihak)
    2. Contract value/nilai kontrak
    3. Contract duration/masa berlaku
    4. Key deliverables
    5. Payment terms
    6. Termination clauses
    7. Penalty clauses (jika ada)
    """,
    pages=[0, 1, 2, 3, 4]  # Biasanya halaman awal berisi key terms
)

# Summary kontrak yang panjang
result = await analyze_pdf_pages(
    pdf_path="/home/aseps/MCP/contract_20_pages.pdf",
    prompt="Provide a comprehensive summary of this contract, highlighting key obligations, risks, and important dates",
    pages=[0, 1, 2]  # Summary dari halaman awal
)
```

### 5. Analisis Chart/Graph
```python
result = await analyze_image(
    "/home/aseps/MCP/sales_chart.png",
    prompt="Describe the trend shown in this chart and identify key data points"
)
```

### 6. Baca Dokumen Scan (OCR)
```python
# Dokumen hasil scan yang tidak bisa di-copy text-nya
result = await analyze_pdf_pages(
    "/home/aseps/MCP/scanned_contract.pdf",
    prompt="Extract all text content from this scanned document with high accuracy",
    pages=[0, 1, 2]  # First 3 pages only
)

# Atau foto dokumen dari kamera
result = await analyze_image(
    image_path="/home/aseps/MCP/foto_ktp.jpg",
    prompt="Extract all readable text from this ID card image"
)
```

### 7. Batch Processing Multiple Documents
```python
# Proses multiple invoice sekaligus
invoices = [
    "/home/aseps/MCP/invoice_001.pdf",
    "/home/aseps/MCP/invoice_002.pdf",
    "/home/aseps/MCP/invoice_003.pdf"
]

results = []
for invoice in invoices:
    result = await analyze_pdf_pages(
        pdf_path=invoice,
        prompt="Extract: invoice number, date, vendor, and total amount",
        namespace="accounting_2024"
    )
    results.append(result)

# Semua hasil tersimpan di namespace "accounting_2024"
# Bisa di-retrieve dengan:
all_results = await list_vision_results(namespace="accounting_2024", limit=50)
```
