# SOP: Ekstraksi Tanggal Diterima PUU dari Kolom POSISI

## 📋 Ringkasan

**Tujuan:** Mengekstrak tanggal diterima oleh PUU dari kolom `POSISI` pada data korespondensi internal.

**Kapan dijalankan:** Setiap kali proses ETL (Extract-Transform-Load) dari Google Sheets ke database PostgreSQL.

**Output:** Kolom `tanggal_diterima_puu` pada tabel `surat_masuk_puu`.

---

## 🎯 Dasar Pemikiran

Semua data yang mengandung kata **"PUU"** di kolom `POSISI` dianggap sebagai **Surat Masuk PUU** — yaitu korespondensi internal yang ditujukan kepada Kelompok Substansi Perundang-Undangan (PUU).

Format **DD/M** (hari/bulan) yang mengikuti kata "PUU" merupakan **tanggal diterima oleh PUU**, yang akan diverifikasi dengan placeholder `tanggal_diterima` pada file mail merge disposisi.

---

## 📝 Format POSISI yang Didukung

### 1. Format Normal
```
SES 9/3 PUU 11/3
```
- **Arti:** Surat masuk ke Sekretaris pada 9/3, diterima PUU pada 11/3
- **Tanggal diterima PUU:** `11/3`

### 2. Format Multi-unit (Anomali)
```
PRC, KEU, PUU, Umum 6/1
```
- **Arti:** Disposisi ke 4 unit sekaligus (PRC, KEU, PUU, Umum) pada 6/1
- **Tanggal diterima PUU:** `6/1`

### 3. Format Multi-step dengan Koreksi
```
SES 5/2 KOREKSI 5/2 SES 5/2 KOREKSI 6/2 SES 10/2 PUU 11/2
```
- **Arti:** Proses koreksi berulang, diterima PUU pada 11/2
- **Tanggal diterima PUU:** `11/2`

### 4. Format dengan Nama Orang
```
SES 19/1 PUU 20/1 (Pak Barjo)
```
- **Arti:** Diterima PUU pada 20/1, diantar oleh Pak Barjo
- **Tanggal diterima PUU:** `20/1`

---

## 🔧 Implementasi Teknis

### Lokasi File

| File | Fungsi |
|------|--------|
| `mcp-unified/integrations/korespondensi/utils.py` | Fungsi `extract_puu_received_date()` |
| `scripts/etl_korespondensi_db_centric.py` | Proses ETL yang menggunakan fungsi tersebut |
| `mcp-unified/migrations/007_add_tanggal_diterima_puu.sql` | Schema database |

### Fungsi Utama

```python
from integrations.korespondensi.utils import extract_puu_received_date

def extract_puu_received_date(posisi_str: str) -> Optional[str]:
    """
    Ekstrak tanggal diterima PUU dari kolom POSISI.
    
    Returns:
        String tanggal dalam format "DD/M" atau None jika tidak ada PUU
        
    Contoh:
        >>> extract_puu_received_date("SES 9/3 PUU 11/3")
        "11/3"
        
        >>> extract_puu_received_date("PRC, KEU, PUU, Umum 6/1")
        "6/1"
        
        >>> extract_puu_received_date("BU 15/1 SES 16/1")
        None
    """
```

---

## 📊 Proses ETL

### Alur Proses

```
Google Sheets → Fetch Data → Normalize → korespondensi_raw_pool
                                              ↓
                                      Filter PUU (POSISI mengandung "PUU")
                                              ↓
                                      Ekstrak tanggal_diterima_puu
                                              ↓
                                      surat_masuk_puu (UPSERT)
```

### Kode dalam ETL

```python
# Di dalam fungsi process_source()

# 1. Filter apakah baris ini surat masuk PUU
puu, reason = is_puu_row(dari_val, posisi_val, nomor_nd_raw)
if not puu:
    continue

# 2. Ekstrak tanggal diterima PUU dari kolom POSISI
tanggal_diterima_puu = None
puu_date_str = extract_puu_received_date(posisi_val)
if puu_date_str:
    parts = puu_date_str.split('/')
    if len(parts) == 2:
        try:
            puu_day = int(parts[0])
            puu_month = int(parts[1])
            # Asumsi tahun 2026 (atau 2025 untuk bulan Desember)
            puu_year = 2025 if puu_month == 12 else 2026
            tanggal_diterima_puu = date(puu_year, puu_month, puu_day)
        except (ValueError, TypeError):
            pass

# 3. Insert/update ke surat_masuk_puu termasuk tanggal_diterima_puu
cur.execute("""
    INSERT INTO surat_masuk_puu (
        unique_id, tanggal_surat, nomor_nd, 
        dari, dari_full, hal, no_agenda_dispo,
        is_puu, filter_reason, raw_pool_id, tanggal_diterima_puu
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE,%s,%s,%s)
    ON CONFLICT (unique_id) DO UPDATE SET
        tanggal_diterima_puu = COALESCE(EXCLUDED.tanggal_diterima_puu, surat_masuk_puu.tanggal_diterima_puu),
        updated_at = NOW()
""", (unique_id, tanggal, nomor_nd, dari, dari_full, hal, 
      no_agenda_dispo, reason, raw_id, tanggal_diterima_puu))
```

---

## ✅ Verifikasi

### Cek Data yang Sudah Terisi

```sql
SELECT 
    unique_id, 
    nomor_nd, 
    tanggal_surat,           -- Tanggal surat dibuat
    tanggal_diterima_puu,    -- Tanggal diterima PUU (dari POSISI)
    posisi
FROM surat_masuk_puu
WHERE tanggal_diterima_puu IS NOT NULL
ORDER BY tanggal_diterima_puu DESC
LIMIT 10;
```

### Validasi Konsistensi

```sql
-- Pastikan tanggal_diterima_puu >= tanggal_surat (surat diterima SETELAH ditulis)
SELECT 
    unique_id,
    tanggal_surat,
    tanggal_diterima_puu,
    tanggal_diterima_puu - tanggal_surat AS selisih_hari
FROM surat_masuk_puu
WHERE tanggal_diterima_puu IS NOT NULL
  AND tanggal_diterima_puu < tanggal_surat;  -- Seharusnya 0 baris
```

---

## 🔄 Kapan Menjalankan

| Trigger | Deskripsi |
|---------|-----------|
| **ETL Scheduled** | Setiap kali ETL berjalan (otomatis) |
| **Manual Sync** | Saat ada data baru di Google Sheets |
| **Data Recovery** | Saat memulihkan data dari backup |

---

## ⚠️ Catatan Penting

1. **Format tanggal:** Selalu dalam format `DD/M` (contoh: `11/3`, `6/1`, `27/12`)
2. **Tahun:** Diasumsikan 2026, kecuali untuk bulan Desember yang bisa jadi 2025
3. **Data tanpa PUU:** Jika POSISI tidak mengandung "PUU", maka `tanggal_diterima_puu = NULL`
4. **Anomali multi-unit:** Format `Unit1, Unit2, PUU, Unit3 DD/M` tetap diproses dengan benar
5. **Verifikasi Mail Merge:** Tanggal ini digunakan untuk mencocokkan dengan placeholder `tanggal_diterima` pada file disposisi

---

## 📚 Referensi

- Schema Database: `mcp-unified/migrations/005_korespondensi_db_centric.sql`
- Migration: `mcp-unified/migrations/007_add_tanggal_diterima_puu.sql`
- ETL Script: `scripts/etl_korespondensi_db_centric.py`
- Parser Utils: `mcp-unified/integrations/korespondensi/utils.py`

---

*Last Updated: 2026-03-31*