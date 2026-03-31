# 🔍 Analisis Root MCP - File Liar & Masalah Struktural

**Tanggal Pemeriksaan:** 2026-02-20  
**Analis:** Agent Review  
**Tujuan:** Identifikasi file-file yang menyebabkan kesulitan menjalankan mcp-unified

---

## 🚨 TEMUAN KRITIS (P0)

### 1. **Path Inconsistency - SCRIPT FATAL ERROR**
📄 File: `init_session.sh`
```bash
# BARIS BERBAHAYA:
exec "$MCP_CENTRAL/mcp_unified/start.sh"  # ❌ Path salah!
```
**Masalah:** 
- Direferensi: `mcp_unified/start.sh` (underscore)
- Yang ada: `mcp-unified/run.sh` (dash, nama berbeda)
- **Ini akan menyebabkan "file not found" saat init!**

### 2. **File Duplikat - Mengaburkan Identitas**
📄 File: `antigravity_agent` (tanpa ekstensi)
- Isinya **IDENTIK** dengan `.agent`
- Bisa membingungkan: mana yang sebenarnya dipakai?
- Sebaiknya hapus `antigravity_agent`, pertahankan `.agent`

### 3. **Kredensial Bocor di Repo**
📄 File: `.env.secret`
```
WIN_ADMIN_PASS=45ep54frudin
GITHUB_TOKEN=ghp_xxxxxx
```
**Bahaya:** File ini harusnya di `.gitignore`, tidak boleh commit!

---

## ⚠️ TEMUAN MENENGAH (P1)

### 4. **File Log Usang Mengganggu**
📄 File-file yang seharusnya dihapus/diignore:
- `server.log` (dari 2026-01-27, penuh dengan error PostgreSQL)
- `docker_output.txt` (output docker yang sudah usang)
- `meshcentral-backup-20260219-1006.tar.gz` (backup file 100MB+ di root)

### 5. **Script yang Mereferensi File Tidak Ada**
📄 `init_session.sh` mencoba menjalankan:
```bash
python3 "$MCP_CENTRAL/test_agent_compliance.py"
```
**Tapi file ini tidak ada di root!** Hanya ada di `mcp-unified/tests/`

### 6. **Direktori Kosong/Placeholder**
📁 `.mcp-hub/` - Sepenuhnya kosong, tidak ada fungsinya

### 7. **Script Windows di Linux Environment**
📄 `Clean-Installer-Cache-v2.ps1` - PowerShell script di server Linux

---

## 📊 TEMUAN RINGAN (P2)

### 8. **Konfigurasi Tersebar**
| File | Fungsi | Status |
|------|--------|--------|
| `.env` | Environment utama | ✅ Valid |
| `.env.example` | Template | ✅ Valid |
| `.env.secret` | Kredensial sensitif | ⚠️ Harus di .gitignore |
| `.qualityrc` | Quality standards | ✅ Valid |
| `antigravity-mcp-config.json` | Config MCP servers | ✅ Valid |

### 9. **Dependensi Eksternal Tidak Jelas**
Berdasarkan `server.log`, mcp-unified mencoba connect ke:
- PostgreSQL (port 5432) - ❌ Connection refused
- Redis (port 6379) - ❌ Connection refused  
- RabbitMQ (AMQP) - ❌ Connection refused

**Masalah:** Tidak ada dokumentasi cara menjalankan/mematikan dependensi ini.

---

## 🗂️ REKOMENDASI PEMBERSIHAN

### Langkah 1: Hapus File Berbahaya/Membingungkan
```bash
# Hapus duplikat
rm /home/aseps/MCP/antigravity_agent

# Hapus log usang
rm /home/aseps/MCP/server.log
rm /home/aseps/MCP/docker_output.txt

# Hapus backup besar dari root (pindahkan ke backup/)
mv /home/aseps/MCP/meshcentral-backup-20260219-1006.tar.gz /home/aseps/MCP/backups/

# Hapus direktori kosong
rm -rf /home/aseps/MCP/.mcp-hub

# Hapus script Windows (jika tidak diperlukan)
rm /home/aseps/MCP/Clean-Installer-Cache-v2.ps1
```

### Langkah 2: Perbaiki Script Rusak
```bash
# Edit init_session.sh - perbaiki path
# Dari: $MCP_CENTRAL/mcp_unified/start.sh
# Jadi:  $MCP_CENTRAL/mcp-unified/run.sh

# Comment atau hapus referensi ke test_agent_compliance.py
# atau pindahkan file test ke lokasi yang benar
```

### Langkah 3: Amankan Kredensial
```bash
# Tambahkan ke .gitignore
echo ".env.secret" >> /home/aseps/MCP/.gitignore
echo "*.tar.gz" >> /home/aseps/MCP/.gitignore
echo "server.log" >> /home/aseps/MCP/.gitignore
echo "docker_output.txt" >> /home/aseps/MCP/.gitignore

# Unstage jika sudah tercommit
git rm --cached .env.secret 2>/dev/null || true
```

### Langkah 4: Standarisasi Struktur
```
MCP/
├── mcp-unified/          ✅ Core server (sudah benar)
├── shared/               ✅ Shared utilities
├── scripts/              ✅ Task manager dkk
├── tasks/                ✅ Task management
├── docs/                 ✅ Dokumentasi
├── workspace/            ✅ Working directory
├── logs/                 ✅ Log files
├── backups/              🆕 Pindahkan backup di sini
├── .agent                ✅ Agent identity
├── .env                  ✅ Environment
├── .env.example          ✅ Template
└── .env.secret           ⚠️ Move to secrets/ atau .gitignore
```

---

## 🔧 MASALAH SPESIFIK "KESULITAN PERTAMA KALI"

Berdasarkan analisis, kesulitan menjalankan mcp-unified pertama kali disebabkan oleh:

### A. **Missing Dependencies**
```
server.log menunjukkan:
- PostgreSQL: Connection refused
- Redis: Connection refused  
- RabbitMQ: Connection refused
```
**Solusi:** Buat script `start_dependencies.sh` yang jelas.

### B. **Path Confusion**
- Ada `mcp-unified/` (dengan dash)
- Tapi script mereferensi `mcp_unified/` (dengan underscore)
- File `init_session.sh` mencoba jalankan file yang tidak ada

### C. **File yang Seharusnya Tidak Ada**
- `antigravity_agent` membingungkan (duplikat `.agent`)
- `server.log` menunjukkan error lama yang mengaburkan
- `.env.secret` bisa mengaburkan konfigurasi yang benar

### D. **Tidak Ada Quick Start Jelas**
User tidak tahu harus:
1. Jalankan PostgreSQL dulu?
2. Jalankan Redis dulu?
3. Jalankan RabbitMQ dulu?
4. Atau bisa langsung `run.sh`?

---

## ✅ CHECKLIST PEMBERSIHAN

- [ ] Hapus `antigravity_agent`
- [ ] Hapus `server.log`
- [ ] Hapus `docker_output.txt`
- [ ] Pindahkan `meshcentral-backup-*.tar.gz` ke `backups/`
- [ ] Hapus direktori `.mcp-hub/`
- [ ] Perbaiki path di `init_session.sh`
- [ ] Fix atau hapus referensi `test_agent_compliance.py`
- [ ] Tambahkan `.env.secret` ke `.gitignore`
- [ ] Buat `start_dependencies.sh` (atau dokumentasikan optional)
- [ ] Update `README.md` dengan cara menjalankan yang benar

---

## 📝 KESIMPULAN

**Ya, root MCP memang "kurang bersih".** Terdapat:
- 3+ file yang mengaburkan (duplikat, log usang, backup)
- 1 script dengan path yang salah (fatal)
- 1 file kredensial yang seharusnya private
- Direktori kosong tanpa fungsi
- Kurangnya dokumentasi cara start yang benar

**Rekomendasi:** Prioritaskan P0 (path fix & duplikat) untuk segera mengurangi kebingungan.


---
## Update 2026-03-30 (Automated Root Cleanup)
- Root export files `extraction_*.json` dipindahkan ke `archive/reports/`.
- `project_knowledge_bootstrap.json` dipindahkan ke `data/input/bootstrap/`.
- Config lokal root (`antigravity-mcp-config.json`, `cline_mcp_settings.json`) dipindahkan ke `config/local/`.
- Virtualenv legacy `venv/` dipindahkan ke `archive/runtime/root_exports/venv_legacy`; standard aktif: `.venv/`.

Catatan: update referensi path yang masih menunjuk lokasi lama bila ditemukan pada script/tooling.
