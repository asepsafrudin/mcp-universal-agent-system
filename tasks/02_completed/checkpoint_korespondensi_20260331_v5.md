# Checkpoint: Korespondensi Internal PUU — v5 Final
**Tanggal**: 2026-03-31
**Versi**: v5 (Final — Data Cleaning + surat_keluar_puu)
**Status**: SELESAI ✅

---

## 📊 Database State

| Tabel | Records | Keterangan |
|-------|---------|------------|
| `surat_masuk_puu` | **48** | Surat masuk PUU (Agenda 001-I s/d 048-I) |
| `surat_keluar_puu` | **39** | Surat keluar PUU (NOMOR ND berakhiran /PUU) |
| `lembar_disposisi` | **48** | Lembar disposisi |
| `disposisi_documents` | **48** | Semua synced ke Google Drive |
| `disposisi_feedback` | **0** | Siap menerima input dari PIC |
| `korespondensi_raw_pool` | 1,464 | Pool data mentah |
| `dari_lookup` | 33 | Mapping kode DARI → nama lengkap |
| `korespondensi_source_config` | 6 | Konfigurasi sumber aktif |

---

## 📋 Fitur Baru yang Ditambahkan

### 1. Tabel `surat_keluar_puu`
File: `mcp-unified/migrations/009_surat_keluar_puu.sql`
- Mendeteksi surat keluar PUU otomatis dari NOMOR ND berakhiran `/PUU`
- Format agenda: menggunakan NOMOR ND asli (bukan sequence NNN-K)
- Auto-populate saat ETL dijalankan

### 2. ETL Script Updated
File: `scripts/etl_korespondensi_db_centric.py`
- Fungsi `is_puu_row()` → return tuple `(is_masuk, reason, is_keluar)`
- Fungsi baru `is_surat_keluar_puu()` untuk deteksi surat keluar
- Surat keluar otomatis masuk ke tabel `surat_keluar_puu`

### 3. Script Sync ke Google Drive
File: `scripts/sync_disposisi_to_gdrive.py`
- Menggunakan OAuth2 user credentials (bukan Service Account)
- Cred path: `/config/credentials/google/puubangda/`
- Auto refresh token jika expired

---

## 🔧 Pembersihan Data Hari Ini

### tanggal_diterima_puu (100% Complete)
| Kondisi | Sebelum | Sesudah |
|---------|---------|---------|
| ✅ Ada nilai | 25 (52%) | **48 (100%)** |
| ❌ NULL | 23 (48%) | **0 (0%)** |

**Metode pembersihan**:
1. Regex extract `PUU\s+(\d{1,2})/(\d{1,2})` dari filter_reason
2. Koreksi tahun 22 entri (2025 → 2026)
3. Manual update 1 entri outlier

### Sequence Angka
- Semua agenda sudah terurut: 001-I s/d 048-I
- Format: NNN-I untuk surat masuk, NOMOR ND untuk surat keluar

---

## 📂 Google Drive Export

**Folder**: `1s1WyweDstV0vYgP1SIfQk4rWwDGO0OYw`

| Item | Link |
|------|------|
| Surat Masuk Spreadsheet | https://docs.google.com/spreadsheets/d/18rhOMuGTC6ETAvKJAji3uchRhz5Eq-8MtDxVQJ_GnlE |
| Surat Keluar Spreadsheet | https://docs.google.com/spreadsheets/d/1jTowkXHY2f2GpKwU-xjTG-FpSN3gDtrdceSN_j8gf6E |
| 48 Dokumen Mailmerge | Folder disposisi docs (semua synced) |

### OAuth2 Token
- **Path**: `/config/credentials/google/puubangda/token.json`
- **Client ID**: 793855596652-ji1dke3l3ej5n6sfv8e9m3saffvqtie3.apps.googleusercontent.com
- **Status**: ✅ Valid (di-generate 31 Mar 2026)
- **Refresh token tersedia**: Ya (7 hari expiry)

---

## 📝 Script Penting

| File | Deskripsi |
|------|-----------|
| `scripts/etl_korespondensi_db_centric.py` | ETL sync dari Google Sheets (support masuk + keluar) |
| `scripts/generate_disposisi_docs.py` | Mailmerge template → DOCX |
| `scripts/sync_disposisi_to_gdrive.py` | Upload mailmerge ke Google Drive |

---

## ⚠️ Known Issues
- Duplikasi data dari surat yang sama di banyak sheets (unique_id berbeda)
- Format tanggal POSISI tidak konsisten (DD/M vs DD/MM) — otomatis ditangani regex
- Tahun asumsi 2026 (bisa berubah untuk data di luar 2026)

---

## 🚀 Cara Menjalankan Workflow

```bash
cd /home/aseps/MCP
export DATABASE_URL="postgres://mcp_user@localhost:5433/mcp_knowledge"

# 1. ETL Sync
python3 scripts/etl_korespondensi_db_centric.py

# 2. Mailmerge
python3 scripts/generate_disposisi_docs.py

# 3. Sync ke Drive
python3 scripts/sync_disposisi_to_gdrive.py --force