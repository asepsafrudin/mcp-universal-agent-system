# Proposal: Injeksi Data Korespondensi ke Bot Telegram Aria

**Status**: `POTENTIAL`
**Tanggal**: 2026-04-17
**Author**: Antigravity AI (atas permintaan Admin)
**Prioritas**: Medium-High
**Estimasi Effort**: 2–5 hari kerja

---

## 📋 Ringkasan Eksekutif

Bot Telegram Aria saat ini hanya mengakses sebagian kecil data dari `korespondensi-server`. Proposal ini mengidentifikasi **6 modul fitur** yang dapat diinjeksikan dari data yang sudah ada di PostgreSQL (`mcp_knowledge`), tanpa memerlukan infrastruktur baru. Total data yang belum dimanfaatkan: **±8.000 baris** data korespondensi, SDM, dan dokumen.

---

## 📊 Inventori Data yang Tersedia

| Tabel | Baris | Status Saat Ini |
|-------|-------|-----------------|
| `korespondensi_raw_pool` | **2.201** | ❌ Belum diakses bot |
| `onedrive_puu_files` | **4.417** | ❌ Belum diakses bot |
| `surat_masuk_puu_internal` | **50** | ✅ Sudah diakses (via VIEW) |
| `surat_keluar_puu` | **45** | ⚠️ Schema terdaftar, belum ada tool |
| `surat_dari_luar_bangda` | **578** | ❌ Belum diakses bot |
| `lembar_disposisi_bangda` | **584** | ❌ Belum diakses bot |
| `disposisi_distributions` | **606** | ❌ Belum diakses bot |
| `surat_untuk_substansi_puu` | **54** | ❌ Belum diakses bot — **54 pending!** |
| `staff_details` | **169** | ❌ Belum ada tool — data SDM lengkap |
| `vision_results` | **30** | ❌ Belum diakses bot — OCR dokumen |
| `correspondence_events` | **52** | ❌ Timeline surat — belum ada tool |
| `master_json` | **1** | ❌ Struktur org 2026 lengkap |

---

## 🎯 6 Modul Fitur yang Diusulkan

---

### MODUL 1 — Tools Agentic Database Diperluas

**Status Saat Ini**: Bot hanya punya `query_database`, `list_db_tables`, `describe_db_table`.

**Yang Diusulkan** — tambah ke `tool_executor.py`:

| Tool Baru | Sumber Data | Fungsi |
|-----------|------------|--------|
| `search_raw_pool` | `korespondensi_raw_pool` | Cari surat dari 2.201 pool lintas substansi |
| `get_agenda_pending` | `surat_untuk_substansi_puu` | Ambil surat pending di substansi PUU |
| `get_disposisi_chain` | `disposisi_distributions` | Lacak rantai disposisi suatu surat |
| `get_surat_keluar` | `surat_keluar_puu` | Ambil data surat keluar PUU |
| `get_surat_luar_bangda` | `surat_dari_luar_bangda` | Cari surat dari instansi eksternal |

**Contoh Implementasi**:

```python
# tool: search_raw_pool
async def search_raw_pool(query: str, limit: int = 10) -> dict:
    """Cari surat dari seluruh pool 2201 korespondensi lintas substansi."""
    sql = """
        SELECT nomor_nd, tanggal, dari, LEFT(hal, 100) as hal,
               source_sheet_name, LEFT(posisi, 60) as posisi
        FROM korespondensi_raw_pool
        WHERE hal ILIKE %s OR nomor_nd ILIKE %s OR dari ILIKE %s
        ORDER BY tanggal DESC LIMIT %s
    """
    q = f'%{query}%'
    return execute_query(sql, [q, q, q, limit])

# tool: get_agenda_pending
async def get_agenda_pending() -> dict:
    """Ambil semua surat yang masih pending di substansi PUU."""
    sql = """
        SELECT agenda, surat_dari, LEFT(isi_disposisi, 80) as isi,
               tanggal_diterima, status,
               CURRENT_DATE - tanggal_diterima AS hari_pending
        FROM surat_untuk_substansi_puu
        WHERE status = 'pending'
        ORDER BY tanggal_diterima ASC
    """
    return execute_query(sql)

# tool: get_disposisi_chain
async def get_disposisi_chain(nomor_disposisi: str) -> dict:
    """Lacak rantai disposisi — dari siapa ke siapa, dengan instruksi."""
    sql = """
        SELECT dari, kepada, tanggal_disposisi,
               LEFT(isi_disposisi, 120) as instruksi, batas_waktu
        FROM disposisi_distributions
        WHERE nomor_disposisi ILIKE %s
        ORDER BY tanggal_disposisi
    """
    return execute_query(sql, [f'%{nomor_disposisi}%'])
```

**Contoh Dialog:**
```
User: "Aria, ada surat pending apa di PUU?"
Aria: [memanggil get_agenda_pending()]
      "Ada 54 surat pending di substansi PUU. Yang paling lama:
       📌 0018/L dari Kemenko PMK (sudah 99 hari pending sejak 9 Jan 2026)
       📌 0047/L dari Sekjen Kemendagri (sudah 94 hari)"
```

---

### MODUL 2 — Laporan Otomatis On-Demand (`/laporan`)

**Yang Diusulkan** — tambah command handler baru di `bot.py`:

```
/laporan          → Ringkasan harian lintas tabel
/laporan puu      → Status surat masuk/keluar PUU hari ini
/laporan pending  → Semua agenda yang belum selesai
/laporan dispo    → Distribusi disposisi bulan ini
```

**Contoh Output `/laporan puu`:**
```
📋 Laporan PUU — 17 April 2026

📬 Surat Masuk PUU:
  • Total: 50 surat (5 masuk bulan ini)
  • Terbaru: 500.12/1219/SD I dari Subdit Wil. I (15 Apr)

📤 Surat Keluar PUU:
  • Total: 45 surat
  • Terbaru: 100.4.3/70/PUU (14 Apr)

⏳ Pending di Substansi PUU: 54 surat
  ⚠️  3 surat pending > 90 hari
  ⚠️  12 surat pending > 30 hari
```

---

### MODUL 3 — Pencarian Arsip Dokumen (OCR-based)

**Infrastruktur yang ada**:
- **4.417 file PDF** di `onedrive_puu_files` (PUU 2024–2026)
- **30 dokumen** sudah di-OCR di `vision_results` (confidence avg: ~0.92)

**Yang Diusulkan**:

```python
# tool: search_documents
async def search_documents(query: str, year: int = None) -> dict:
    """Full-text search di arsip dokumen yang sudah di-OCR."""
    sql = """
        SELECT file_name, confidence_score,
               LEFT(extracted_text, 200) as preview,
               processed_at
        FROM vision_results
        WHERE extracted_text ILIKE %s
          AND (%s IS NULL OR EXTRACT(YEAR FROM processed_at) = %s)
        ORDER BY confidence_score DESC LIMIT 5
    """
    return execute_query(sql, [f'%{query}%', year, year])
```

**Catatan**: Perlu diperluas dengan menjalankan OCR lebih banyak dari 4.417 file yang belum diproses.

---

### MODUL 4 — Direktori SDM & Struktur Organisasi

**Data yang ada**: 169 pegawai (124 PNS + 45 PPPK) dengan:
- `nama, nip, pangkat, status_kepegawaian`
- `jabatan_fungsional, penugasan_tim, unit_id`
- `master_json`: Struktur org 2026 lengkap (unit, jabatan, relasi hierarki)

```python
# tool: search_staff
async def search_staff(query: str, unit: str = None) -> dict:
    """Cari informasi pegawai berdasarkan nama, jabatan, atau tim."""
    sql = """
        SELECT nama, nip, pangkat, status_kepegawaian,
               jabatan_fungsional, penugasan_tim, unit_id
        FROM staff_details
        WHERE (nama ILIKE %s OR jabatan_fungsional ILIKE %s
               OR penugasan_tim ILIKE %s)
          AND (%s IS NULL OR unit_id ILIKE %s)
        ORDER BY nama LIMIT 10
    """
    q = f'%{query}%'
    u = f'%{unit}%' if unit else None
    return execute_query(sql, [q, q, q, unit, u])
```

**Contoh Dialog:**
```
User: "Siapa yang ada di Bagian Perencanaan?"
Aria: "Tim Bagian Perencanaan terdiri dari:
       • GUNAWAN EKO MOVIANTO — PJ Bagian Perencanaan (PNS, Pembina Tk.I IV/b)
       • AHMAD WASHIL — Ketua Penyusunan Program dan Anggaran
       • ..."
```

---

### MODUL 5 — Notifikasi Proaktif (Scheduler)

**Infrastruktur**: Tabel `scheduler_jobs` & `scheduler_executions` sudah ada tapi **kosong**.

**Yang Diusulkan** — isi `scheduler_jobs` dengan:

| Job | Trigger | Aksi |
|-----|---------|------|
| `daily_summary` | Setiap 07:30 WIB | Kirim ringkasan harian ke chat admin |
| `pending_alert` | Setiap Senin 08:00 | Alert surat pending > 7 hari |
| `new_surat_monitor` | Setiap 30 menit | Deteksi surat baru masuk ke raw_pool |
| `deadline_reminder` | Setiap hari 09:00 | Reminder batas waktu disposisi |

**Implementasi**: Integrasikan dengan `APScheduler` atau `Celery` yang sudah ada di ekosistem MCP.

---

### MODUL 6 — Analitik Tren Korespondensi

**Yang Diusulkan** — query analitik yang bisa dijawab Aria:

```sql
-- "Substansi mana yang paling banyak kirim surat ke PUU?"
SELECT source_sheet_name, COUNT(*) as jumlah
FROM korespondensi_raw_pool
WHERE posisi ~ '(?i)PUU' AND tanggal >= DATE_TRUNC('year', CURRENT_DATE)
GROUP BY 1 ORDER BY 2 DESC;

-- "Tren surat masuk per bulan 2026"
SELECT DATE_TRUNC('month', tanggal) as bulan, COUNT(*) as jumlah
FROM korespondensi_raw_pool
WHERE tanggal >= '2026-01-01'
GROUP BY 1 ORDER BY 1;

-- "Rata-rata waktu penyelesaian surat PUU"
SELECT AVG(tanggal_selesai - tanggal_diterima) as rata_rata_hari
FROM surat_untuk_substansi_puu
WHERE tanggal_selesai IS NOT NULL;
```

---

## 🗺️ Roadmap Implementasi

### Fase 1 — Quick Win (1–2 Hari)
- [ ] Tambah `search_raw_pool` ke `tool_executor.py`
- [ ] Tambah `get_agenda_pending` ke `tool_executor.py`
- [ ] Tambah `get_disposisi_chain` ke `tool_executor.py`
- [ ] Update schema di `text_to_sql_service.py` dan `ai_service.py`

### Fase 2 — Menengah (2–3 Hari)
- [ ] Implementasi command `/laporan` + sub-commands
- [ ] Tambah `search_staff` + `get_org_structure` ke `tool_executor.py`
- [ ] Tambah `search_documents` (OCR-based) ke `tool_executor.py`

### Fase 3 — Advanced (3–5 Hari)
- [ ] Isi `scheduler_jobs` dengan notifikasi proaktif
- [ ] Integrasikan APScheduler/Celery untuk trigger otomatis
- [ ] Dashboard analitik tren via Telegram

---

## 📁 File yang Perlu Diubah

| File | Perubahan |
|------|-----------|
| `mcp-unified/execution/tool_executor.py` | Tambah 5 tools baru (Modul 1) |
| `mcp-unified/integrations/telegram/services/ai_service.py` | Update system prompt schema |
| `mcp-unified/integrations/telegram/services/text_to_sql_service.py` | Update DATABASE_SCHEMA |
| `mcp-unified/integrations/telegram/bot.py` | Tambah handler `/laporan` (Modul 2) |
| `mcp-unified/integrations/telegram/config/constants.py` | Tambah konstanta tool baru |

---

## ⚠️ Catatan & Risiko

> [!NOTE]
> Semua data sudah ada di PostgreSQL — tidak perlu ETL atau integrasi baru. Implementasi murni menambah tools dan query.

> [!WARNING]
> `surat_untuk_substansi_puu` memiliki **54 surat dengan status 'pending'** — beberapa sudah > 90 hari. Ini bisa menjadi temuan audit sensitif jika diekspos ke bot admin tanpa kontrol akses yang tepat.

> [!TIP]
> Mulai dari **Modul 1 Fase 1** (3 tools baru) sebagai proof-of-concept. Estimasi: 2–3 jam implementasi, langsung terasa manfaatnya.
