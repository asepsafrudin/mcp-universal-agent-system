# Task: Olah Data Surat Luar 2026 (Bangda/ULA)

## 📋 Context
**Sheet ID**: `1N6K0mXrGU1aWaUAOB0O97n7LdpooKBI27hu3KqqOAYA`
**Sheet Name**: "data surat luar 2026"
**Tanggal Mulai**: 31 Mar 2026
**Status**: ✅ COMPLETED - ETL, Mailmerge, LTM Updated

## 📊 Struktur Sheet

### Tab 1: Surat Masuk (507 rows) - **DONE**
| Col | Header | DB Field |
|-----|--------|----------|
| A | F | timestamp_raw |
| B | Surat Dari | surat_dari |
| C | Nomor Surat | nomor_surat |
| D | Tgl Surat Masuk | tgl_surat |
| E | Tgl Diterima ULA | tgl_diterima_ula |
| F | Perihal | perihal |
| G | Arahan Menteri | arahan_menteri |
| H | Arahan Sekjen | arahan_sekjen |
| I | Agenda ULA | agenda_ula |
| J | Status Mailmerge | status_mailmerge |

### Tab 2: Lembar Disposisi Dirjen (507 rows) - **DONE**
### Tab 3: Dispo DJ/TU Pim (332 rows) - **DONE**
### Tab 4: Dispo Ses (202 rows) - **DONE**

## ✅ Database Tables Created

### Tabel Surat (baru)
| Table | Records | Purpose |
|-------|---------|---------|
| `surat_dari_luar_bangda` | 502 | Surat masuk dari luar (was surat_keluar_ula) |
| `lembar_disposisi_bangda` | 508 | Lembar disposisi Dirjen |
| `disposisi_distributions` | 534 | Combined dispo (531 linked) |
| `surat_untuk_substansi_puu` | 47 | Filtered untuk PUU processing |

### Format Numbers
| Type | Format | Contoh |
|------|--------|--------|
| Agenda ULA | XXX/L | 001/L |
| **Agenda PUU** | **XXX-L** | 001-L (dash format) |
| **No Agenda Ses** | **XXX/Set/L/YYYY** | 0030/Set/L/2026 |

## ✅ Scripts Created/Updated
| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/etl_surat_luar_2026.py` | ETL GSheets → DB with no_agenda_ses | ✅ Final |
| `scripts/mailmerge_puu_surat.py` | Mailmerge dengan disposisi template | ✅ Final |
| `scripts/create_surat_keluar_ula_table.sql` | Database schema (DDL) | ✅ Final |
| `scripts/generate_ula_disposisi_docs.py` | Generate DOCX disposisi | ✅ Legacy |

## ✅ Template & Mailmerge
| Component | Value |
|-----------|-------|
| Template ID | `1lQH-NMy1pU9Cw-iTsR9pDLex6kc9NeJALIG3I7uvWEI` |
| Target Folder | `1v5OjzdXBc9xX95FcRBopT6seze_p0H8Q` |
| Filename Format | `Disposisi - {agenda_puu}` |
| Placeholders | 7 (Surat Dari, Nomor Surat, Tgl Surat, Tgl Diterima PUU, No Agenda Ses, Agenda PUU, Perihal) |

## 🌐 Web GUI - Manajemen Surat PUU

### Quick Start
```bash
# Start dashboard (port 8081)
bash scripts/start_surat_puu_dashboard.sh

# Atau langsung:
cd /home/aseps/MCP/mcp-unified
PYTHONPATH=$(pwd) python3 knowledge/admin/surat_puu_app.py
```

### Akses
- **URL**: http://localhost:8081/surat-puu/dashboard
- **Login**: `admin` / `admin123`
- **Roles**: admin, reviewer, viewer

### Fitur
| Fitur | Detail |
|-------|--------|
| Tabel surat | 47 records dengan status + tanggal_diterima |
| Edit per record | Modal form: date picker tanggal_diterima + status + catatan |
| Status | pending → diterima → diproses → selesai |
| Filter | Search (agenda/surat_dari/nomor), status, date range |
| Export CSV | Download semua atau filtered data |
| Stats cards | Pending, Diterima, Diproses, Selesai, Total |

### File
| File | Path |
|------|------|
| App (FastAPI) | `mcp-unified/knowledge/admin/surat_puu_app.py` |
| Startup Script | `scripts/start_surat_puu_dashboard.sh` |

---

## 🚀 Cara Menggunakan

### ETL (Sync Sheet → DB) - Migrasi Awal Saja
```bash
source mcp-unified/.env
python3 scripts/etl_surat_luar_2026.py
```

### Mailmerge (Generate Disposisi Docs) - Migrasi Awal Saja
```bash
source mcp-unified/.env
python3 scripts/mailmerge_puu_surat.py          # All 47
python3 scripts/mailmerge_puu_surat.py --limit 5  # Test 5
python3 scripts/mailmerge_puu_surat.py --dry-run  # Preview
```

### Update Tanggal Diterima PUU (Operasional Harian)
**3 metode input:**

#### 1. Langsung ke SQL
```sql
UPDATE surat_untuk_substansi_puu
SET tanggal_diterima = '2026-03-31'::date
WHERE nomor_surat = 'XXX/YYY/ZZZ';
```

#### 2. Langsung ke Spreadsheet
Edit kolom **TGL DITERIMA PUU** di:
- [Export Surat PUU 2026](https://docs.google.com/spreadsheets/d/1G6h7IrvDbJ0Ikvtn1YXvpAHly5jb4cZCklNHhaGpyug/edit)
- [Dispo PUU](https://docs.google.com/spreadsheets/d/1GRLdIr0ONXKTGWxPqyJW9vgcwgaYkU8YdN6eAoVPAeQ/edit)

#### 3. Via Telegram Bot
Kirim perintah ke bot untuk update tanggal diterima.

## 📂 Files Reference
| File | Status |
|------|--------|
| ETL Script | `scripts/etl_surat_luar_2026.py` ✅ |
| Mailmerge Script | `scripts/mailmerge_puu_surat.py` ✅ |
| DDL Schema | `scripts/create_surat_keluar_ula_table.sql` ✅ |
| OAuth2 Token | `config/credentials/google/puubangda/token.json` ✅ |
| LTM Entry | `surat_luar_2026_bangda` ✅ |

## 📝 Session History
- **31 Mar 2026 14:35** - Tables created
- **31 Mar 2026 14:36** - ETL completed: 501 surat, 507 lembar dispo, 332 dispo DJ/TU, 202 dispo Ses
- **31 Mar 2026 14:39** - Document generator working, 10 test docs generated
- **31 Mar 2026 14:40** - Sync script created
- **31 Mar 2026 15:35** - Added `no_agenda_ses` column (format `XXX/Set/L/YYYY`)
- **31 Mar 2026 16:00** - Filename format: `Disposisi - {agenda_puu}` (dash format)
- **31 Mar 2026 16:05** - LTM updated
- **31 Mar 2026 18:17** - Web GUI created: `mcp-unified/knowledge/admin/surat_puu_app.py` (FastAPI, port 8081) + startup script

## 🔄 Key Changes from Original
1. **Table renamed**: `surat_keluar_ula` → `surat_dari_luar_bangda`
2. **New column**: `no_agenda_ses` with format `XXX/Set/L/YYYY`
3. **Agenda PUU format**: `XXX-L` (dash, bukan slash)
4. **Mailmerge**: Template `1lQH-NMy1pU9Cw-iTsR9pDLex6kc9NeJALIG3I7uvWEI` with 7 placeholders
5. **Tgl Diterima PUU**: Dikosongkan (diisi manual admin PUU)