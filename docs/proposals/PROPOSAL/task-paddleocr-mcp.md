# Task: Integrasi PaddleOCR Local Python Library ke mcp-unified

**Status:** 🔲 Belum dimulai  
**Prioritas:** Medium-High  
**Estimasi:** 3–5 hari kerja  
**Kategori:** `services/ocr` · `mcp-unified`

---

## Latar Belakang

Proyek **Bangda PUU** membutuhkan kemampuan OCR untuk memproses dokumen pemerintah Indonesia (scan PDF, foto surat, tabel regulasi, cap stempel). PaddleOCR 3.0 menyediakan MCP server resmi yang bisa diintegrasikan langsung ke `mcp-unified` menggunakan **Local Python Library mode** — fully offline, tanpa API key, tanpa data keluar dari mesin.

Pipeline yang akan diekspos sebagai MCP tools:
- `PP-OCRv5` — ekstraksi teks dari gambar/PDF
- `PP-StructureV3` — parsing dokumen ke Markdown terstruktur (tabel, heading, paragraf)

---

## Struktur Direktori Target

```
mcp-unified/
├── services/
│   └── ocr/                          ← direktori baru
│       ├── __init__.py
│       ├── service.py                ← wrapper PaddleOCR engine
│       ├── tools.py                  ← definisi MCP tools
│       ├── config.py                 ← konfigurasi pipeline
│       ├── utils.py                  ← helper: base64, file type, temp files
│       └── tests/
│           ├── __init__.py
│           ├── test_ocr.py
│           └── fixtures/
│               ├── sample_doc.jpg
│               └── sample_doc.pdf
├── docs/
│   └── services/
│       └── ocr.md                    ← dokumentasi tool untuk agent
└── AGENT_RULES.md                    ← update: tambahkan namespace ocr/
```

---

## Checklist Implementasi

### Phase 1 — Persiapan Environment

- [ ] **1.1** Verifikasi Python version di WSL Ubuntu (`python3 --version`, minimal 3.8)
- [ ] **1.2** Cek ketersediaan GPU/CUDA di WSL:
  ```bash
  nvidia-smi
  python3 -c "import paddle; paddle.utils.run_check()"
  ```
- [ ] **1.3** Install dependencies:
  ```bash
  # PaddlePaddle (pilih salah satu)
  pip install paddlepaddle-gpu  # jika ada CUDA GPU
  pip install paddlepaddle      # CPU only

  # PaddleOCR 3.x (API baru — TIDAK kompatibel dengan 2.x)
  pip install "paddleocr>=3.3.0"
  pip install paddleocr-mcp
  ```
- [ ] **1.4** Test instalasi dasar PaddleOCR 3.x:
  ```python
  from paddleocr import PaddleOCR
  # 3.x: parameter baru — BUKAN use_angle_cls/use_gpu lagi
  ocr = PaddleOCR(lang='en', device='cpu')
  result = list(ocr.predict('tests/fixtures/sample_doc.jpg'))
  for item in result:
      for line in item.get('rec_result', []):
          print(line['rec_text'], line['rec_score'])
  ocr.close()  # ← WAJIB di 3.x
  ```
- [ ] **1.5** Download model weights (auto-download dari HuggingFace saat pertama kali dijalankan):
  - `PP-OCRv5_server_det` — text detection (~5MB)
  - `PP-OCRv5_server_rec` — text recognition (~12MB)
  - `PP-DocLayout_plus-L` — layout detection untuk StructureV3 (~22MB)
  - Disimpan di `~/.paddlex/official_models/`
- [ ] **1.6** Siapkan test fixtures: 2–3 gambar dokumen pemerintah Indonesia (surat, tabel, berkas dengan cap)

---

### Phase 2 — Implementasi Core Service

- [ ] **2.1** Buat `services/ocr/config.py`:
  ```python
  # config.py
  # PaddleOCR 3.x API — parameter berbeda dari 2.x
  import os

  # --- PaddleOCR (PP-OCRv5) ---
  # Parameter 3.x: TIDAK ada use_angle_cls, use_gpu, show_log, enable_mkldnn
  # GPU/CPU dikontrol via 'device'; auto-detect jika tidak diset
  OCR_INIT_PARAMS = {
      "lang":                         os.getenv("PADDLEOCR_LANG", "en"),
      "text_detection_model_name":    "PP-OCRv5_server_det",
      "text_recognition_model_name":  "PP-OCRv5_server_rec",
      "use_doc_orientation_classify": False,   # hemat resource, enable jika scan miring
      "use_doc_unwarping":            False,   # enable jika dokumen melengkung
      "use_textline_orientation":     True,    # deteksi orientasi per baris teks
      "device":                       os.getenv("PADDLEOCR_DEVICE", "cpu"),
      # "paddlex_config": None,               # opsional: path ke YAML config
  }

  # --- PPStructureV3 ---
  STRUCTURE_INIT_PARAMS = {
      "lang":                         os.getenv("PADDLEOCR_LANG", "en"),
      "layout_detection_model_name":  "PP-DocLayout_plus-L",
      "text_detection_model_name":    "PP-OCRv5_server_det",
      "text_recognition_model_name":  "PP-OCRv5_server_rec",
      "use_doc_orientation_classify": False,
      "use_doc_unwarping":            False,
      "use_seal_recognition":         True,    # penting untuk dokumen pemerintah (cap/stempel)
      "use_table_recognition":        True,    # untuk tabel regulasi
      "use_formula_recognition":      False,   # nonaktif — hemat ~100MB RAM
      "use_chart_recognition":        False,   # nonaktif — tidak relevan untuk dokumen hukum
      "use_region_detection":         True,
      "device":                       os.getenv("PADDLEOCR_DEVICE", "cpu"),
  }

  # Batas ukuran file input (default 10MB)
  MAX_FILE_SIZE_MB = int(os.getenv("PADDLEOCR_MAX_FILE_MB", "10"))

  # Tipe file yang didukung di local mode
  # CATATAN: PDF bisa diproses langsung via PPStructureV3.predict()
  #          tetapi PaddleOCR.predict() hanya untuk gambar
  SUPPORTED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
  SUPPORTED_DOC_TYPES   = SUPPORTED_IMAGE_TYPES | {".pdf"}
  ```

- [ ] **2.2** Buat `services/ocr/service.py` — engine wrapper dengan lazy loading:
  ```python
  # service.py
  # PaddleOCR 3.x API:
  #   - Init: PaddleOCR(lang, device, text_detection_model_name, ...)
  #   - Infer: pipeline.predict(input)  ← returns iterator
  #   - Result: item['rec_result'] untuk OCR, item['markdown'] untuk Structure
  #   - Cleanup: pipeline.close()  ← WAJIB dipanggil
  import threading
  import tempfile
  import os
  from pathlib import Path
  from paddleocr import PaddleOCR, PPStructureV3
  from .config import OCR_INIT_PARAMS, STRUCTURE_INIT_PARAMS

  class OCREngine:
      """
      Singleton wrapper untuk PaddleOCR 3.x pipelines.
      Lazy-init: engine dibuat saat pertama kali dipanggil, bukan saat import.
      Thread-safe via double-checked locking.
      """
      _instance = None
      _lock = threading.Lock()
      _ocr: PaddleOCR | None = None
      _structure: PPStructureV3 | None = None
      _init_lock = threading.Lock()  # lock terpisah untuk init engine

      @classmethod
      def get_instance(cls) -> "OCREngine":
          if cls._instance is None:
              with cls._lock:
                  if cls._instance is None:
                      cls._instance = cls()
          return cls._instance

      def get_ocr(self) -> PaddleOCR:
          if self._ocr is None:
              with self._init_lock:
                  if self._ocr is None:
                      self._ocr = PaddleOCR(**OCR_INIT_PARAMS)
          return self._ocr

      def get_structure(self) -> PPStructureV3:
          if self._structure is None:
              with self._init_lock:
                  if self._structure is None:
                      self._structure = PPStructureV3(**STRUCTURE_INIT_PARAMS)
          return self._structure

      def run_ocr(self, image_path: str) -> dict:
          """
          Ekstraksi teks menggunakan PP-OCRv5.

          Returns:
              {
                "full_text": str,          # semua teks digabung per baris
                "lines": [
                  { "text": str, "score": float, "bbox": list },
                  ...
                ]
              }
          """
          ocr = self.get_ocr()
          # predict() returns iterator — konversi ke list
          raw = list(ocr.predict(image_path))
          return self._format_ocr_result(raw)

      def run_structure(self, file_path: str) -> str:
          """
          Parse struktur dokumen menggunakan PP-StructureV3.
          Mendukung gambar DAN PDF langsung.

          Returns:
              str Markdown (multi-halaman digabung dengan concatenate_markdown_pages)
          """
          structure = self.get_structure()
          raw = list(structure.predict(file_path))

          # Kumpulkan markdown per halaman lalu gabungkan
          markdown_pages = []
          for res in raw:
              md_info = res.markdown          # dict: {'markdown': str, 'markdown_images': {...}}
              if md_info:
                  markdown_pages.append(md_info)

          if not markdown_pages:
              return ""

          # Gunakan helper resmi untuk multi-page concat
          combined = structure.concatenate_markdown_pages(markdown_pages)
          return combined

      def _format_ocr_result(self, raw: list) -> dict:
          """
          Transformasi output PaddleOCR 3.x ke format bersih.

          Struktur raw result 3.x per item:
            item['rec_result'] = [
              { 'rec_text': str, 'rec_score': float, 'det_box': [[x,y],...] },
              ...
            ]
          """
          lines = []
          for item in raw:
              for line in item.get("rec_result", []):
                  lines.append({
                      "text":  line.get("rec_text", ""),
                      "score": round(line.get("rec_score", 0.0), 4),
                      "bbox":  line.get("det_box", []),
                  })
          return {
              "full_text": "\n".join(l["text"] for l in lines),
              "lines":     lines,
          }

      def warmup(self) -> None:
          """Pre-load kedua engine saat server start (opsional)."""
          self.get_ocr()
          self.get_structure()

      def close(self) -> None:
          """Release resources. Panggil saat server shutdown."""
          if self._ocr:
              self._ocr.close()
              self._ocr = None
          if self._structure:
              self._structure.close()
              self._structure = None
  ```

- [ ] **2.3** Buat `services/ocr/utils.py`:
  ```python
  # utils.py
  import base64
  import os
  import tempfile
  from pathlib import Path
  from .config import MAX_FILE_SIZE_MB, SUPPORTED_IMAGE_TYPES, SUPPORTED_DOC_TYPES

  def decode_base64_to_tempfile(b64_data: str, suffix: str = ".jpg") -> str:
      """Decode base64 image ke temporary file, return path."""
      data = base64.b64decode(b64_data)
      with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
          f.write(data)
          return f.name

  def validate_image_file(path: str) -> None:
      """Validasi file gambar (untuk ocr/extract_text — hanya gambar)."""
      _validate_common(path, SUPPORTED_IMAGE_TYPES)

  def validate_doc_file(path: str) -> None:
      """Validasi file dokumen (untuk ocr/parse_document — gambar + PDF)."""
      _validate_common(path, SUPPORTED_DOC_TYPES)

  def _validate_common(path: str, allowed_types: set) -> None:
      p = Path(path)
      if not p.exists():
          raise FileNotFoundError(f"File tidak ditemukan: {path}")
      size_mb = p.stat().st_size / (1024 * 1024)
      if size_mb > MAX_FILE_SIZE_MB:
          raise ValueError(f"File terlalu besar: {size_mb:.1f}MB (maks {MAX_FILE_SIZE_MB}MB)")
      if p.suffix.lower() not in allowed_types:
          raise ValueError(
              f"Tipe file tidak didukung: '{p.suffix}'. "
              f"Yang didukung: {sorted(allowed_types)}"
          )

  def cleanup_tempfile(path: str) -> None:
      try:
          os.unlink(path)
      except Exception:
          pass
  ```

- [ ] **2.4** Buat `services/ocr/tools.py` — definisi MCP tools:
  ```python
  # tools.py
  """
  MCP Tools untuk PaddleOCR 3.x service.
  Namespace: ocr/

  Tools:
    - ocr/extract_text    : ekstraksi teks dari gambar (PP-OCRv5)
    - ocr/parse_document  : parsing struktur dokumen ke Markdown (PP-StructureV3)
                            mendukung gambar DAN PDF
  """
  from mcp.server import Server
  from .service import OCREngine
  from .utils import (
      decode_base64_to_tempfile,
      validate_image_file,
      validate_doc_file,
      cleanup_tempfile,
  )

  def register_tools(server: Server) -> None:
      engine = OCREngine.get_instance()

      @server.tool("ocr/extract_text")
      async def extract_text(
          image_path: str = None,
          image_base64: str = None,
      ) -> dict:
          """
          Ekstraksi teks dari gambar dokumen menggunakan PP-OCRv5.
          Hanya menerima format gambar (jpg/png/bmp/tiff/webp).
          Untuk PDF, gunakan ocr/parse_document.

          Args:
              image_path  : Path absolut ke file gambar lokal
              image_base64: Gambar dalam format base64 (jpg/png)

          Returns:
              { "full_text": str, "lines": [{"text", "score", "bbox"}, ...] }
          """
          tmp = None
          try:
              if image_base64:
                  tmp = decode_base64_to_tempfile(image_base64)
                  path = tmp
              elif image_path:
                  path = image_path
              else:
                  raise ValueError("Harus menyertakan image_path atau image_base64")

              validate_image_file(path)
              return engine.run_ocr(path)
          finally:
              if tmp:
                  cleanup_tempfile(tmp)

      @server.tool("ocr/parse_document")
      async def parse_document(
          file_path: str = None,
          image_base64: str = None,
      ) -> str:
          """
          Parse struktur dokumen ke format Markdown menggunakan PP-StructureV3.
          Mendukung gambar (jpg/png/bmp/tiff/webp) DAN PDF langsung.
          Mengenali: judul, paragraf, tabel, heading, cap/stempel, formula.

          Args:
              file_path   : Path absolut ke file gambar atau PDF lokal
              image_base64: Gambar dalam format base64 (hanya gambar, bukan PDF)

          Returns:
              str Markdown dengan struktur dokumen terpelihara
          """
          tmp = None
          try:
              if image_base64:
                  tmp = decode_base64_to_tempfile(image_base64)
                  path = tmp
              elif file_path:
                  path = file_path
              else:
                  raise ValueError("Harus menyertakan file_path atau image_base64")

              validate_doc_file(path)
              return engine.run_structure(path)
          finally:
              if tmp:
                  cleanup_tempfile(tmp)
  ```

---

### Phase 3 — Integrasi ke mcp-unified

- [ ] **3.1** Register tools di entry point utama `mcp-unified`:
  ```python
  # Di main server registration (sesuaikan dengan struktur mcp-unified)
  from services.ocr.tools import register_tools as register_ocr_tools
  
  register_ocr_tools(server)
  ```

- [ ] **3.2** Update `AGENT_RULES.md` — tambahkan namespace `ocr/`:
  ```markdown
  ## Namespace: ocr/
  
  Tools untuk ekstraksi teks dan parsing dokumen dari gambar.
  
  | Tool | Deskripsi | Input | Output |
  |---|---|---|---|
  | `ocr/extract_text` | Ekstraksi teks + bounding box | image_path atau image_base64 | JSON: full_text, lines[] |
  | `ocr/parse_document` | Parsing dokumen ke Markdown | image_path atau image_base64 | Markdown string |
  
  **Kapan gunakan `extract_text`:** butuh teks mentah, koordinat, atau confidence score per baris.  
  **Kapan gunakan `parse_document`:** dokumen kompleks (tabel regulasi, formulir, surat resmi) yang perlu struktur dipertahankan untuk RAG.
  ```

- [ ] **3.3** Buat `docs/services/ocr.md` — dokumentasi lengkap untuk agent dan developer

- [ ] **3.4** Pastikan `services/ocr/__init__.py` mengekspos interface publik:
  ```python
  from .tools import register_tools
  from .service import OCREngine
  
  __all__ = ["register_tools", "OCREngine"]
  ```

---

### Phase 4 — Testing

- [ ] **4.1** Unit test `services/ocr/tests/test_ocr.py`:
  ```python
  import pytest
  from services.ocr.service import OCREngine
  from services.ocr.utils import validate_image_file, validate_doc_file

  SAMPLE_IMAGE = "services/ocr/tests/fixtures/sample_doc.jpg"
  SAMPLE_PDF   = "services/ocr/tests/fixtures/sample_doc.pdf"

  def test_ocr_engine_singleton():
      e1 = OCREngine.get_instance()
      e2 = OCREngine.get_instance()
      assert e1 is e2

  def test_extract_text_from_file():
      engine = OCREngine.get_instance()
      result = engine.run_ocr(SAMPLE_IMAGE)
      # 3.x result structure
      assert "full_text" in result
      assert "lines" in result
      assert isinstance(result["full_text"], str)
      assert len(result["lines"]) > 0
      # setiap line harus punya key yang benar
      for line in result["lines"]:
          assert "text" in line
          assert "score" in line
          assert "bbox" in line

  def test_parse_document_image_returns_markdown():
      engine = OCREngine.get_instance()
      result = engine.run_structure(SAMPLE_IMAGE)
      assert isinstance(result, str)
      assert len(result) > 0

  def test_parse_document_pdf_returns_markdown():
      """PP-StructureV3 di 3.x mendukung PDF langsung."""
      engine = OCREngine.get_instance()
      result = engine.run_structure(SAMPLE_PDF)
      assert isinstance(result, str)
      assert len(result) > 0

  def test_validate_image_rejects_pdf():
      """ocr/extract_text tidak boleh terima PDF."""
      with pytest.raises(ValueError, match="tidak didukung"):
          validate_image_file(SAMPLE_PDF)

  def test_validate_doc_accepts_pdf():
      """ocr/parse_document boleh terima PDF."""
      # tidak raise jika file ada
      validate_doc_file(SAMPLE_PDF)

  def test_validate_file_size_limit(tmp_path):
      big_file = tmp_path / "big.jpg"
      big_file.write_bytes(b"x" * (11 * 1024 * 1024))  # 11MB
      with pytest.raises(ValueError, match="terlalu besar"):
          validate_image_file(str(big_file))
  ```

- [ ] **4.2** Integration test: panggil MCP tool `ocr/extract_text` via MCP client
- [ ] **4.3** Test dengan dokumen nyata:
  - [ ] Surat dinas/resmi (teks Latin)
  - [ ] Tabel regulasi (PP/Perpres)
  - [ ] Dokumen dengan cap/stempel
  - [ ] Scan kualitas rendah (foto HP)
- [ ] **4.4** Benchmark latency:
  - Target: < 3 detik per gambar (CPU), < 1 detik (GPU)
  - Ukur first-call (model loading) vs subsequent calls

---

### Phase 5 — Optimasi & Konfigurasi systemd

- [ ] **5.1** Konfigurasi lazy loading — engine hanya inisialisasi saat tool pertama kali dipanggil (sudah di service.py via singleton)

- [ ] **5.2** Jika `mcp-unified` dijalankan via systemd, pastikan environment variables tersedia:
  ```ini
  # /etc/systemd/system/mcp-unified.service (tambahkan di bagian [Service])
  # 3.x: BUKAN PADDLEOCR_USE_GPU — gunakan PADDLEOCR_DEVICE
  Environment=PADDLEOCR_DEVICE=cpu
  Environment=PADDLEOCR_LANG=en
  Environment=PADDLEOCR_MAX_FILE_MB=10
  # Opsional: ganti sumber download model dari HuggingFace ke BOS Baidu
  # Environment=PADDLE_PDX_MODEL_SOURCE=BOS
  ```

- [ ] **5.3** Pertimbangkan memory: PP-StructureV3 membutuhkan ~1GB RAM saat semua sub-modul aktif. Jika WSL memory terbatas, nonaktifkan pipeline yang tidak digunakan di `config.py`:
  ```python
  # Di STRUCTURE_INIT_PARAMS — hemat resource untuk dokumen hukum:
  STRUCTURE_INIT_PARAMS = {
      ...
      "use_formula_recognition": False,   # hemat ~100MB — tidak ada formula di dokumen hukum
      "use_chart_recognition":   False,   # hemat ~200MB — tidak ada chart
      "use_doc_unwarping":       False,   # hemat startup time — enable jika scan melengkung
      ...
  }
  ```

- [ ] **5.4** Warm-up model sebelum systemd aktif melayani request — cegah timeout di request pertama:
  ```bash
  # Jalankan sekali manual untuk trigger download + warm-up
  python3 -c "
  from services.ocr.service import OCREngine
  e = OCREngine.get_instance()
  e.warmup()   # pre-load kedua engine
  e.close()
  print('Warm-up selesai')
  "
  ```

---

### Phase 6 — Dokumentasi

- [ ] **6.1** Update `README.md` di root `mcp-unified` — tambahkan section OCR service
- [ ] **6.2** Buat `docs/services/ocr.md`:
  - Deskripsi tools
  - Contoh penggunaan dari agent/Telegram bot
  - Limitasi (hanya gambar, bukan PDF langsung di local mode)
  - Troubleshooting umum
- [ ] **6.3** Catat versi model yang digunakan untuk reprodusibilitas

---

## Catatan Penting & Limitasi

### ⚠️ Limitasi & Perbedaan API 3.x vs 2.x

| Aspek | PaddleOCR 2.x (LAMA) | PaddleOCR 3.x (BENAR) |
|---|---|---|
| **Import Structure** | `from paddleocr import PPStructure` | `from paddleocr import PPStructureV3` |
| **Init params OCR** | `PaddleOCR(use_angle_cls=True, use_gpu=True, show_log=False)` | `PaddleOCR(lang='en', device='gpu:0', use_textline_orientation=True)` |
| **Init params Structure** | `PPStructure(table=True, ocr=True)` | `PPStructureV3(use_table_recognition=True, use_seal_recognition=True)` |
| **Inference call** | `ocr.ocr(path, cls=True)` | `list(ocr.predict(path))` |
| **Result keys OCR** | `bbox, (text, confidence)` | `item['rec_result'][i]['rec_text']`, `['rec_score']`, `['det_box']` |
| **Result keys Structure** | `item['type'], item['res']` | `res.markdown` dict → `{'markdown': str, 'markdown_images': {}}` |
| **Multi-page PDF concat** | manual | `pipeline.concatenate_markdown_pages(pages)` |
| **PDF support di local** | ❌ hanya gambar | ✅ PPStructureV3.predict() menerima PDF langsung |
| **Cleanup** | tidak perlu | `pipeline.close()` **WAJIB** dipanggil untuk release memory |
| **GPU param** | `use_gpu=True` | `device='gpu:0'` |
| **MKL-DNN** | `enable_mkldnn=True` | otomatis (via `PADDLEOCR_DEVICE=cpu`) |

### 💡 Tips untuk Dokumen Pemerintah Indonesia

- Gunakan `lang='en'` untuk dokumen Latin — Bahasa Indonesia terbaca baik dengan model ini
- Untuk **cap/stempel** berlapis teks, aktifkan `use_seal_recognition=True` di `STRUCTURE_INIT_PARAMS` (sudah default `True`)
- Untuk **tabel regulasi** (kolom pasal, isi, keterangan), pastikan `use_table_recognition=True`
- Scan dengan resolusi minimal **200 DPI** untuk hasil optimal
- `PPStructureV3.predict()` sudah bisa menerima **PDF langsung** di 3.x — tidak perlu konversi ke gambar dulu
- Selalu panggil `engine.close()` di shutdown hook server untuk mencegah memory leak

### 🔗 Integrasi dengan RAG Pipeline

Output `ocr/parse_document` (Markdown) bisa langsung dimasukkan ke RAG pipeline di `mcp-unified` tanpa post-processing tambahan. Contoh alur:

```
Dokumen scan (gambar)
    ↓ ocr/parse_document
Markdown terstruktur
    ↓ chunking
Vector store (ChromaDB)
    ↓ similarity search
LLM answer
```

---

## Referensi

- [PaddleOCR MCP Server Official Docs](https://www.paddleocr.ai/latest/en/version3.x/deployment/mcp_server.html)
- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- [PP-StructureV3 Documentation](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/pipeline/PP-StructureV3.md)
- [FastMCP v2 Documentation](https://github.com/jlowin/fastmcp)
- Task sebelumnya: `task-33.md` (AI Voice Bot demo), `task-bangda-puu-ocr.md`

---

*Dibuat: 2026-04-02 | mcp-unified project | Bangda PUU*
