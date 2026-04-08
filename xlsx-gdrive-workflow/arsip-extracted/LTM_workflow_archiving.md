# Dokumentasi Otomatisasi Pengolahan Arsip Pemerintah (SPM/SPTB) 2025

## 🎯 Objektif
Mengonversi hasil pemindaian fisik (.png) dokumen keuangan pemerintah (SPM/SPTB) menjadi data terstruktur (JSON) dan terintegrasi otomatis ke dalam Google Sheets secara akurat dan konsisten.

## 🛠️ Stack Teknologi
*   **OCR**: Google Cloud Vision API (Akurasi Tinggi).
*   **Semantic Refinement**: Groq LLM (Konteks tata letak & koreksi typo).
*   **Database**: JSON & Markdown Rangkuman.
*   **Output**: Google Sheets API.

## 📂 Struktur Folder
*   **Source PNG/MD**: `/home/aseps/MCP/xlsx-gdrive-workflow/arsip-2025/scan/`
*   **Extracted Data**: `/home/aseps/MCP/xlsx-gdrive-workflow/arsip-extracted/`
*   **Scripts**: `/home/aseps/MCP/mcp-unified/`

## ⚙️ Logika Utama (Kalibrasi LTM)

### 1. Robust Document Number Extraction
Menggunakan pola regex **`(\d{3}/F\.2/[^/\s\n]+/[^/\s\n]+/\d{4})`** untuk menangkap nomor surat resmi SPM tanpa terpengaruh oleh sampah teks atau kode satuan kerja yang terkadang ikut terekstrak di sekitarnya.

### 2. Multi-column Joining (Uraian Panjang)
Skrip `fix_summary_logic.py` telah dikalibrasi untuk menggabungkan teks uraian yang terpisah oleh tanda pipa (`|`) atau yang terbagi dalam beberapa baris (multi-line), memastikan rincian SK dan periode pembayaran (seperti "Agustus 2025") tersambung secara utuh.

### 3. Indonesian Currency Filtering
Pemisahan cerdas antara **Nomor Akun** dan **Nominal Uang** (Jumlah/Potongan) dengan filter yang mendukung format ribuan titik di Indonesia (`x.xxx.xxx`) dan mengabaikan angka di bawah 50.000 sebagai akun, bukan uang belanja.

### 4. Merged Row Logic (One Row per Document)
Logika pemadatan data untuk stakeholder:
*   Menggabungkan semua item rincian (Yonatan, Fannia, dsb) di bawah satu nomor surat yang sama.
*   Format sel Uraian: `Penerima - Uraian` dengan penomoran baris internal dalam satu sel.
*   Menghilangkan baris "sampah" (header tabel yang ikut terekstrak sebagai baris data).

## 🚀 Skrip Operasional (Python 3.12)
1.  **`fix_summary_logic.py`**: Mengekstrak MD mentah menjadi `arsip_summary.json` yang sudah rapi dan terkonsolidas (Merged).
2.  **`upload_to_sheets.py`**: Membersihkan range **D11:F100** di Google Sheet (ID: `18H6gIv6...8AwRM`) dan melakukan input data terbaru.
3.  **`final_audit.py`**: Melakukan verifikasi mandiri setelah sinkronisasi untuk memastikan keutuhan uraian (Self-Refinement).

---
> [!IMPORTANT]
> **Catatan Kritis**: Jika dokumen sangat panjang, selalu pastikan limit `max_tokens` di `context_refiner.py` diset minimal **4000** agar bagian tanda tangan dan tanggal di bawah tidak terpotong.
