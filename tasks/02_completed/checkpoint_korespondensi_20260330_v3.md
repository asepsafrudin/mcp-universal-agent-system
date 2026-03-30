# Checkpoint: Perbaikan Struktur Database Korespondensi v3
**Tanggal**: 2026-03-30
**Versi**: v3 (lanjutan dari v2)
**Status**: SELESAI ✅

---

## Ringkasan Perubahan (v3)

### 1. Database Sekarang Aktif
- Migrations 004, 005, 006 berhasil diaplikasikan ke `mcp_knowledge`
- ETL berhasil dijalankan → 750 baris dari 6 spreadsheet ter-ingest

### 2. Migration 006 — Fix Schema Gaps
File: `mcp-unified/migrations/006_fix_disposisi_schema.sql`

**Perbaikan:**
| Perubahan | Detail |
|---|---|
| `disposisi_documents.sync_status` | Kolom baru (`pending`/`synced`/`error`) — diperlukan generate & sync script |
| `disposisi_documents.synced_at` | Kolom baru — timestamp saat file berhasil di-upload Drive |
| `disposisi_documents.local_file_path` | Kolom baru — path file DOCX lokal |
| `UNIQUE (lembar_disposisi_id)` | Constraint baru — diperlukan ON CONFLICT clause |
| `surat_masuk_puu.dari_full` | Kolom baru — nama lengkap pengirim (caching) |
| `korespondensi_source_config.skip_sheets` | Kolom baru (JSONB) — daftar tab yang diabaikan ETL |
| Tabel `dari_lookup` | Tabel referensi baru — 33 baris mapping kode→nama lengkap |

### 3. ETL Diperbarui
File: `scripts/etl_korespondensi_db_centric.py`

**Perubahan:**
- Tambah `DARI_LOOKUP` dict + fungsi `map_dari()` untuk resolve nama lengkap
- `process_source()` sekarang terima parameter `skip_sheets` — otomatis skip tab yang masuk daftar
- `run_etl()` sekarang baca `skip_sheets` dari DB config (`korespondensi_source_config`)
- INSERT ke `surat_masuk_puu` sekarang mengisi kolom `dari_full`
- SEKRETARIAT: skip sheet "surat keluar PUU" ✅

### 4. DATABASE_URL Ditambahkan ke .env
```
DATABASE_URL=postgresql://mcp_user:mcp_password_2024@localhost:5433/mcp_knowledge
```
Script (`etl_korespondensi_db_centric.py`, `generate_disposisi_docs.py`, `sync_disposisi_to_gdrive.py`) sekarang bisa langsung dijalankan tanpa export manual.

---

## State Database Saat Ini

| Tabel | Count | Keterangan |
|-------|-------|------------|
| korespondensi_raw_pool | 725 | 6 unit, synced 2026-03-30 |
| surat_masuk_puu | 23 | is_puu=TRUE, dari_full terisi |
| lembar_disposisi | 23 | agenda 001-I s/d 023-I, direktorat konsisten |
| disposisi_documents | 0 | Belum digenerate (langkah berikutnya) |
| dari_lookup | 33 | Mapping kode→nama lengkap |
| korespondensi_source_config | 6 | SEKRETARIAT skip_sheets=["surat keluar PUU"] |

---

## Sumber Data per Unit

| Unit | Total Row | last_synced_at | skip_sheets |
|------|-----------|----------------|-------------|
| SEKRETARIAT | 364 | 2026-03-30 18:04 | ["surat keluar PUU"] |
| PEIPD | 63 | 2026-03-30 18:04 | [] |
| SUPD I | 68 | 2026-03-30 18:04 | [] |
| SUPD II | 123 | 2026-03-30 18:04 | [] |
| SUPD III | 71 | 2026-03-30 18:04 | [] |
| SUPD IV | 61 | 2026-03-30 18:04 | [] |

---

## File yang Diubah

| File | Perubahan |
|------|-----------|
| `mcp-unified/migrations/004_correspondence_schema.sql` | Baru — applied |
| `mcp-unified/migrations/005_korespondensi_db_centric.sql` | Baru — applied |
| `mcp-unified/migrations/006_fix_disposisi_schema.sql` | Baru — schema fixes |
| `scripts/etl_korespondensi_db_centric.py` | DARI_LOOKUP + skip_sheets + dari_full |
| `mcp-unified/.env` | Tambah DATABASE_URL |

---

## Pekerjaan Berikutnya (Backlog)

- [ ] **Mapping kode `UN`** — Konfirmasi dari user: mapping sementara = "Unit Pengelola (Belum Terdefinisi)"
- [ ] **Generate dokumen disposisi** — Jalankan `generate_disposisi_docs.py` setelah credentials Google Drive aktif
- [ ] **Sync ke Drive** — Jalankan `sync_disposisi_to_gdrive.py --force` setelah generate selesai
- [ ] **OAuth2 token SEKRETARIAT** — Token expired (`invalid_grant`), perlu `scripts/reauth_google_drive.py`
- [ ] **Cek surat_masuk_puu = 23 vs checkpoint v2 = 37** — Kemungkinan data spreadsheet berubah, atau filter beda

---

## Cara Menjalankan Ulang ETL

```bash
cd /home/aseps/MCP
source mcp-unified/.env  # atau export DATABASE_URL manual
python3 scripts/etl_korespondensi_db_centric.py
```

## Cara Generate + Sync Disposisi

```bash
# Generate DOCX lokal (perlu Google SA credentials)
python3 scripts/generate_disposisi_docs.py

# Sync ke Drive
python3 scripts/sync_disposisi_to_gdrive.py --force
```
