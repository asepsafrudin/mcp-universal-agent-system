# Audit Findings & Recommendation: MCP Structure Standardization

**Tanggal**: 12 Maret 2026
**Auditor**: Antigravity (Senior AI Dev Engineer)

## 1. Temuan Audit (Current State)

### A. Root Directory Clutter (Kekacauan di Root)
Ditemukan banyak file temporer dan skrip pengujian yang berada di root, yang seharusnya berada di direktori khusus:
- **Extractions**: `extraction_*.json` (misal: `extraction_jdih_20260312_060026.json`)
- **Test Scripts**: `test_all_targets.py`, `test_vane_search.py`, `setup_vane_v2.py`.
- **Config**: `vane_config.json`, `vane_config_clean.json`.
- **Legacy Backups**: Folder `archive-review/` berisi skrip penting (`backup_system.sh`, `init_session.sh`) yang redundan.

### B. Fragmentasi Dokumentasi
Dokumentasi tersebar di 3 lokasi utama yang tumpang tindih:
1.  `/docs/` (Dokumentasi sistem utama)
2.  `/mcp-unified/docs/` (Dokumentasi teknis internal)
3.  `/archive/docs/` (Dokumentasi tugas yang selesai)

### C. Folder Data & Memory
Terdapat dua folder data yang membingungkan:
- `/data/`: Menyimpan data `document_management`.
- `/mcp-data/`: Menyimpan data `ltm` (Postgres/pgvector data).

### D. Redundansi Integrasi
Modul `Bangda_PUU` dan `OneDrive_PUU` berada di root, padahal keduanya merupakan bagian dari domain fungsi MCP.

---

## 2. Rekomendasi Struktur Target (Proposed Architecture)

### A. Konsolidasi Core & Execution
Pindahkan `mcp-unified` ke `/core/` atau biarkan sebagai modul utama namun bersihkan file-file non-inti di dalamnya.

### B. Struktur "Single Source of Truth" untuk Task
- Menggunakan satu folder `/tasks/` dengan subfolder:
  - `01_active/`: Tugas sedang berjalan.
  - `02_completed/`: Tugas selesai dalam sprint ini.
  - `03_archive/`: Tugas historis.
- Menghapus folder `tasks/status/` dan menggantinya dengan satu file `manifest.json` atau `README.md` status yang diupdate otomatis oleh agen.

### C. Sentralisasi Skrip & Infrastruktur
- Semua skrip operasional (`backup`, `restart`, `health-check`) dikumpulkan di `/infrastructure/ops/`.
- Semua skrip riset/utilitas yang jarang digunakan dipindahkan ke `/scripts/utils/`.

### D. Penataan Integrasi
- Gabungkan `Bangda_PUU` dan `OneDrive_PUU` di bawah folder `/domains/`.
- Pindahkan file konfigurasi `.json` ke `/config/`.

---

## 3. Tahap Transformasi (Safe Migration)

1.  **Preparation**: Buat folder-folder baru sesuai struktur target.
2.  **Mapping Config**: Update PATH pada file `.env` dan `config.py`.
3.  **Move & Sync**: Pindahkan file secara bertahap (per kategori) dan uji fungsionalitas di setiap tahap.
4.  **Cleaning**: Hapus direktori kosong dan skrip legacy.

## 4. Metadata Agen (Agent Governance)
Setiap folder harus memiliki `README.md` singkat yang menjelaskan fungsionalitasnya agar agen AI baru dapat langsung memahami konteks tanpa melakukan scanning mendalam.
