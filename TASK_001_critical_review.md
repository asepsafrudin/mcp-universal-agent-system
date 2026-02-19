# TASK-001: Eksekusi Tinjauan Kritis — Initial Security & Architecture Hardening

**Dibuat:** 2026-02-19  
**Sumber:** Tinjauan kritis dari senior reviewer pada sesi analisis awal  
**Status:** 🔴 OPEN

---

## Konteks

Sistem MCP Unified Agent ini telah melalui tinjauan kritis eksternal. Ditemukan beberapa isu yang harus segera ditangani sebelum sistem ini layak digunakan lebih lanjut, baik untuk Operational (Mode 1) maupun Development (Mode 2).

Tugas ini memerintahkan kamu untuk menjalankan seluruh temuan tersebut secara berurutan.

---

## INSTRUKSI UNTUK AGENT

Baca seluruh task ini sampai selesai sebelum mulai mengerjakan apapun. Pahami urutan dan dependensinya. Lalu kerjakan dari atas ke bawah.

---

## [TASK-001-A] 🔴 CRITICAL — Isolasi `simulation/greyware_op/`

**Latar belakang:**  
Folder ini mengandung `c2_bot.js` (Command & Control bot), `duckyscript.txt` (USB keystroke injection payload), `ai_nmap.py` (AI-powered network scanner), dan PowerShell deployment scripts. Keberadaan folder ini dalam satu repo dengan production MCP server adalah risiko keamanan dan risiko reputasi yang nyata.

**Yang harus dilakukan:**

1. Buat file `simulation/greyware_op/ISOLATION_REQUIRED.md` dengan isi:
   - Penjelasan mengapa folder ini harus dipisah
   - Instruksi langkah-langkah untuk memindahkan ke repo terpisah
   - Peringatan bahwa folder ini tidak boleh dieksekusi di luar environment terkontrol

2. Buat file `SECURITY_NOTICE.md` di root project dengan isi:
   - Overview risiko keamanan folder simulation/greyware_op
   - Status isolasi saat ini
   - Referensi ke ISOLATION_REQUIRED.md

3. Tambahkan entry ke `.gitignore`:
   ```
   # SECURITY: Greyware simulation tools — must never reach remote repository
   simulation/greyware_op/
   simulation/meshcentral_server/meshcentral-data/
   ```

4. Verifikasi bahwa `.gitignore` sudah ada. Jika belum, buat dari awal dengan entry di atas plus standar Python/Node gitignore.

**Definisi selesai:** Ketiga file sudah ada, `.gitignore` sudah diupdate, tidak ada kode yang dieksekusi dari folder greyware_op.

---

## [TASK-001-B] 🔴 CRITICAL — Hapus Hardcoded Credentials

**Latar belakang:**  
Password `secure123` ditemukan hardcoded di README dan kemungkinan juga di file konfigurasi lain. Ini kebiasaan buruk yang sering tidak sengaja masuk ke production.

**Yang harus dilakukan:**

1. Baca file-file berikut dan identifikasi semua hardcoded credentials:
   - `mcp-unified/core/config.py`
   - `mcp-unified/test_config.json` (jika ada)
   - `antigravity-mcp-config.json`
   - Semua file `.sh`

2. Untuk setiap credential yang ditemukan di luar `.env`:
   - Ganti nilai aktual dengan referensi environment variable
   - Contoh: `password="secure123"` → `password=os.getenv("POSTGRES_PASSWORD", "")`

3. Buat file `.env.example` di root project:
   ```
   # PostgreSQL
   POSTGRES_USER=your_username
   POSTGRES_PASSWORD=your_secure_password_here
   POSTGRES_SERVER=localhost
   POSTGRES_DB=mcp

   # Redis
   REDIS_URL=redis://localhost:6379/0

   # Logging
   LOG_LEVEL=INFO
   ```

4. Pastikan `.env` dan `.env.local` masuk ke `.gitignore`.

5. Tambahkan comment di `config.py`:
   ```python
   # [REVIEWER] Credentials harus selalu dari environment variables
   # Jangan pernah hardcode nilai aktual di sini
   # Lihat .env.example untuk referensi
   ```

**Definisi selesai:** Tidak ada string password/secret aktual yang tersisa di file kode. `.env.example` sudah ada.

---

## [TASK-001-C] 🔴 CRITICAL — Hardening `run_shell` Whitelist

**Latar belakang:**  
Tool `run_shell` di `mcp-unified/execution/tools/shell_tools.py` disebutkan hanya mengizinkan "safe commands (ls, pwd, git, dll)" — tapi "dll" adalah ambigu dan berbahaya. Satu command yang lolos bisa jadi attack vector.

**Yang harus dilakukan:**

1. Baca `mcp-unified/execution/tools/shell_tools.py` secara penuh.

2. Identifikasi mekanisme whitelist yang ada saat ini. Catat temuanmu.

3. Implementasikan explicit whitelist sebagai constant di bagian atas file:
   ```python
   # [REVIEWER] Explicit whitelist — jangan tambahkan command tanpa review security
   ALLOWED_COMMANDS = frozenset([
       "ls", "ls -la", "ls -l",
       "pwd",
       "cat",
       "echo",
       "find",
       "grep",
       "git status",
       "git log",
       "git log --oneline",
       "git diff",
       "git branch",
       "python3 --version",
       "pip list",
       "pip show",
       "env",
       "whoami",
   ])
   ```

4. Pastikan fungsi validasi command menggunakan whitelist ini, bukan string matching yang bisa di-bypass.

5. Tambahkan input sanitization — tolak input yang mengandung: `;`, `&&`, `||`, `|`, `>`, `>>`, `` ` ``, `$()`.

6. Tambahkan logging setiap kali `run_shell` dipanggil: command apa, oleh siapa (jika ada context), timestamp.

**Definisi selesai:** `shell_tools.py` memiliki ALLOWED_COMMANDS yang eksplisit dan input sanitization yang berfungsi.

---

## [TASK-001-D] 🟡 HIGH — Memory Namespace Isolation

**Latar belakang:**  
Sistem ini akan digunakan di multiple projects (Mode 1 dan Mode 2). Tanpa namespace isolation, memories dari project A bisa "mencemari" context di project B — menghasilkan output yang tidak relevan atau salah.

**Yang harus dilakukan:**

1. Baca `mcp-unified/memory/longterm.py` secara penuh.

2. Identifikasi schema tabel `memories` di PostgreSQL. Periksa apakah sudah ada field untuk project/namespace isolation.

3. Jika belum ada:
   - Tambahkan field `namespace: str` ke model memory
   - Default value: `"default"`
   - Update semua fungsi `memory_save`, `memory_search`, `memory_list`, `memory_delete` untuk support parameter `namespace`
   - Pada `memory_search`, filter hanya return memories dari namespace yang sama kecuali diminta explicit

4. Buat migration note di `docs/` yang menjelaskan perubahan schema ini (jangan langsung ALTER TABLE — itu shell command yang butuh approval).

5. Update docstring semua fungsi yang diubah.

**Definisi selesai:** Semua operasi memory support namespace, default ke `"default"`, dan tidak ada cross-namespace contamination pada search.

---

## [TASK-001-E] 🟡 HIGH — MeshCentral Separation Plan

**Latar belakang:**  
`simulation/meshcentral_server/` adalah remote device management platform yang bundled di dalam MCP server. Ini scope creep yang menambah attack surface dan membingungkan boundary sistem.

**Yang harus dilakukan:**

1. Baca `simulation/meshcentral_server/package.json`.

2. Buat dokumen `docs/meshcentral_separation_plan.md` berisi:
   - Alasan teknis mengapa MeshCentral harus dipisah
   - Langkah-langkah pemisahan ke repo terpisah
   - Dampak ke sistem MCP jika dipisah (apakah ada dependency?)
   - Timeline rekomendasi

3. Tambahkan entry di `SECURITY_NOTICE.md` (yang dibuat di TASK-001-A) tentang MeshCentral.

**Definisi selesai:** Dokumen separation plan sudah ada dan lengkap.

---

## Laporan Akhir

Setelah semua task di atas selesai (atau sebagian selesai dengan alasan yang jelas), buat file:

**`docs/review_2026-02-19.md`**

Dengan format:
```markdown
# Review Log — 2026-02-19

## Executive Summary
[kondisi sistem sebelum dan sesudah task ini]

## Yang Dikerjakan
| Task | File | Tindakan | Status |
|------|------|----------|--------|

## Shell Commands yang Menunggu Approval
[list command yang perlu dijalankan user secara manual]

## Isu Baru yang Ditemukan
[temuan tambahan saat mengerjakan]

## Sisa Pekerjaan
[task yang belum bisa diselesaikan dan alasannya]
```

---

## Catatan Penting

- Jika saat mengerjakan task ini kamu menemukan isu lain yang belum ada di daftar — catat di laporan, jangan skip
- Jika ada task yang tidak bisa diselesaikan tanpa shell command — dokumentasikan command yang perlu dijalankan dan minta approval
- Urutan A → B → C → D → E adalah urutan prioritas, tapi jika ada dependency yang mengharuskan urutan berbeda, gunakan judgment-mu dan catat alasannya
