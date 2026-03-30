# Checkpoint: Perbaikan Struktur Database Korespondensi
**Tanggal**: 2026-03-30  
**Versi**: v2  
**Status**: SELESAI ✅

---

## Ringkasan Perubahan

### 1. Filter Surat Keluar PUU (Business Rule Baru)
- **Aturan**: NOMOR ND berakhiran `/PUU` = surat KELUAR dari PUU → EXCLUDE dari mailmerge
- **Dampak**: 38 dari 75 record di `surat_masuk_puu` ditandai `is_puu=FALSE`
- **DB**: Hapus 38 record dari `lembar_disposisi` dan `disposisi_documents`
- **ETL**: `is_puu_row()` diperbarui dengan parameter `nomor_nd` untuk filter outbound

### 2. Mapping Kode DARI → Nama Lengkap
- **Tujuan**: Mengisi field "Surat Dari" di lembar disposisi mailmerge
- **Format**: `"{dari_full} - {direktorat}"` (contoh: "Bagian Keuangan - Sekretariat")
- **Edge case**: Jika dari_full == direktorat → tampilkan satu saja
- **Lookup dict** `DARI_LOOKUP` ditambahkan di `generate_disposisi_docs.py`

### 3. Normalisasi Direktorat
- Source of truth: `korespondensi_raw_pool.source_sheet_name`
- Mapping: SEKRETARIAT→Sekretariat, PEIPD→Direktorat PEIPD, SUPD I-IV→Direktorat SUPD I-IV
- 37 records di `lembar_disposisi` dinormalisasi

### 4. Renumbering Agenda PUU
- Dari: non-consecutive (003, 004, 009, 010, 013...)
- Ke: consecutive 001-I s/d 037-I (urut tanggal_surat, id)

### 5. Fix Sync Script Bug
- **Bug**: `sync_disposisi_to_gdrive.py` skip upload jika file sudah ada di Drive
- **Fix**: Tambah flag `--force` → hapus file lama, upload ulang
- **Result**: 37 file di-force re-upload dengan konten benar

---

## State Database Saat Ini

| Tabel | Count | Keterangan |
|-------|-------|------------|
| surat_masuk_puu | 75 | 37 is_puu=TRUE, 38 is_puu=FALSE (outbound /PUU) |
| lembar_disposisi | 37 | agenda 001-I s/d 037-I, direktorat konsisten |
| disposisi_documents | 37 | semua sync_status='synced', tgl_surat terisi |
| Drive folder | 37 | file DOCX aktif, "Surat Dari" terisi dengan benar |

---

## Mapping Kode DARI (Lengkap)

| Kode (semua variasi) | Nama Lengkap |
|---|---|
| BU, UM | Bagian Umum |
| TU, TU.SUPD.II | Tata Usaha |
| PRC | Bagian Perencanaan |
| PUU | Substansi Perundang-Undangan |
| KEU | Bagian Keuangan |
| SD I, SD.I, SD. I, SD.1 | Subdit Wilayah I |
| SD II, SD.II | Subdit Wilayah II |
| SD III, SD.III | Subdit Wilayah III |
| SD IV, SD.IV, SD. IV | Subdit Wilayah IV |
| SD V, SD.V, sd v | Subdit Wilayah V |
| SD VI, SD.VI | Subdit Wilayah VI |
| SD PMIPD, SD.PMIPD, SD PIMPD | Subdit PMIPD |
| SD | Subdit |
| PEIPD | Direktorat PEIPD |
| PMIPD | Subdit PMIPD |
| SUPD I | Direktorat SUPD I |
| SUPD II | Direktorat SUPD II |
| SUPD III | Direktorat SUPD III |
| SUPD IV | Direktorat SUPD IV |
| PPK | Pejabat Pembuat Komitmen |
| BANGDA | Ditjen Bina Pembangunan Daerah |
| UN | (belum terdefinisi) |

---

## Sheet yang Diabaikan
- Sheet "surat keluar PUU" di spreadsheet SEKRETARIAT (id: `1tSqu5XljsU9a-ZCS_yk0dswWQgsHEWS9IhF32i4Ll9Y`)
- Fungsinya sama dengan filter nomor ND berakhiran /PUU

---

## File yang Diubah
- `scripts/etl_korespondensi_db_centric.py` — `is_puu_row()` update
- `scripts/generate_disposisi_docs.py` — DARI mapping + DIREKTORAT format
- `scripts/sync_disposisi_to_gdrive.py` — flag `--force` untuk re-upload

---

## Pekerjaan Berikutnya (Backlog)
- [ ] Mapping kode `UN` belum terdefinisi (user akan menyusulkan)
- [ ] ETL perlu skip sheet "surat keluar PUU" secara eksplisit di `korespondensi_source_config`
- [ ] Pertimbangkan menambah kolom `dari_full` di `surat_masuk_puu` untuk caching
