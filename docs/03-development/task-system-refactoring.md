# Proposal Refaktorisasi Sistem Task & Review

**Dibuat:** 2026-02-20  
**Masalah:** Diskrepansi status task antara file TASK_XXX.md (root) dan implementasi kode aktual

---

## 1. Masalah yang Ditemukan

### 1.1 Duplikasi Status
- File `TASK_XXX.md` di root berisi deskripsi task + status
- File `docs/review_YYYY-MM-DD.md` berisi laporan completion
- Implementasi kode aktual di `mcp-unified/`
- **Hasil:** 3 sumber kebenaran yang tidak sinkron

### 1.2 Temuan Aktual (19 Feb 2026)
| Task | File Root | Implementasi Kode | Status Aktual |
|------|-----------|-------------------|---------------|
| 001 | 🔴 OPEN | ✅ DONE | COMPLETED |
| 002 | 🔴 OPEN | ✅ DONE | COMPLETED |
| 003 | 🔴 OPEN | ✅ DONE | COMPLETED |
| 004 | 🔴 OPEN | ✅ DONE | COMPLETED |
| 005 | 🔴 OPEN | ✅ DONE | COMPLETED |
| 006 | 🔴 OPEN | ❓ UNCHECKED | UNKNOWN |
| 007 | 🔴 OPEN | ✅ DONE | COMPLETED |
| 008 | 🔴 OPEN | ✅ DONE | COMPLETED |
| 009 | 🔴 OPEN | ✅ DONE | COMPLETED |
| 010 | 🔴 OPEN | ✅ DONE | COMPLETED |
| 011 | 🔴 OPEN | ✅ DONE | COMPLETED |

---

## 2. Proposal Solusi

### 2.1 SINGLE SOURCE OF TRUTH

**Hapus duplikasi dengan sistem berikut:**

```
sistem-baru/
├── .agent/
│   └── tasks/              # Definisi task (readonly setelah dibuat)
│       ├── 001-security-hardening.md
│       ├── 002-code-hardening.md
│       └── ...
├── .agent/
│   └── status/             # Status dinamis (diupdate oleh agent)
│       ├── 001-status.md   # OPEN | IN_PROGRESS | COMPLETED
│       ├── 002-status.md
│       └── ...
└── docs/
    └── reviews/            # Laporan review tetap di sini
        └── YYYY-MM-DD/
            ├── task-001-review.md
            └── summary.md
```

### 2.2 FORMAT STATUS FILE

**File:** `.agent/status/XXX-status.md`

```markdown
# Task-001 Status

**Last Updated:** 2026-02-19 14:30  
**Updated By:** agent-mcp

## Current Status: ✅ COMPLETED

## Completion Checklist
- [x] 001-A: Greyware isolation
- [x] 001-B: Hardcoded credentials
- [x] 001-C: Shell whitelist
- [x] 001-D: Memory namespace
- [x] 001-E: MeshCentral separation

## Verification
- Code Inspection: ✅ PASS
- Tests: 15/15 PASS
- Review Doc: docs/reviews/2026-02-19/task-001-review.md

## Blockers
None.
```

### 2.3 AUTOMATED STATUS CHECK

**Script:** `scripts/verify_task_status.py`

```python
#!/usr/bin/env python3
"""
Verifikasi status task dengan membandingkan:
1. Definisi task (.agent/tasks/)
2. Status file (.agent/status/)
3. Implementasi kode (mcp-unified/)
4. Test results (tests/)
"""

TASKS = range(1, 12)

def verify_task(task_num):
    # 1. Baca definisi task
    # 2. Baca status file
    # 3. Inspeksi kode untuk checkmarks
    # 4. Jalankan tests terkait
    # 5. Bandingkan & laporkan diskrepansi
    pass

if __name__ == "__main__":
    for task in TASKS:
        verify_task(task)
```

### 2.4 GIT HOOKS UNTUK SYNC

**Pre-commit hook:**
```bash
#!/bin/bash
# Cek apakah ada diskrepansi status task
python3 scripts/verify_task_status.py --check-sync
if [ $? -ne 0 ]; then
    echo "❌ Task status tidak sinkron. Jalankan: python3 scripts/update_task_status.py"
    exit 1
fi
```

---

## 3. Implementasi Bertahap

### Phase 1: Cleanup (Hari 1)
1. [ ] Audit semua task files (TASK_001 s/d TASK_011)
2. [ ] Update status di root files berdasarkan implementasi aktual
3. [ ] Hapus file task yang sudah obsolete
4. [ ] Consolidate review files

### Phase 2: Restrukturisasi (Hari 2-3)
1. [ ] Buat direktori `.agent/tasks/` dan `.agent/status/`
2. [ ] Pindahkan definisi task ke `.agent/tasks/`
3. [ ] Buat status files dengan format baru
4. [ ] Update semua path referensi

### Phase 3: Automation (Hari 4-5)
1. [ ] Implementasi `scripts/verify_task_status.py`
2. [ ] Setup git hooks
3. [ ] Dokumentasikan workflow baru
4. [ ] Training untuk agent/agent baru

---

## 4. Workflow Baru

### Saat Membuat Task Baru
```bash
# 1. Buat definisi task
.agent/tasks/new-task-template.md

# 2. Buat status file (OPEN)
.agent/status/XXX-status.md  # status = OPEN

# 3. Implementasi kode
# ... coding ...

# 4. Update status (IN_PROGRESS → COMPLETED)
# Otomatis oleh script atau manual oleh agent
```

### Saat Verifikasi Status
```bash
# Single command untuk cek semua task
python3 scripts/verify_task_status.py

# Output:
# Task-001: ✅ COMPLETED (code: ✅ tests: ✅ docs: ✅)
# Task-002: ✅ COMPLETED (code: ✅ tests: ✅ docs: ✅)
# Task-003: ⚠️  PARTIAL (code: ✅ tests: ❌ docs: ⚠️)
# ...
```

---

## 5. Keuntungan

| Aspek | Sebelum | Sesudah |
|-------|---------|---------|
| Source of Truth | 3 sumber (TASK_, review_, kode) | 1 sumber (.agent/status/) |
| Verifikasi | Manual, error-prone | Automated, reliable |
| Visibility | Buruk (file tersebar) | Baik (terpusat di .agent/) |
| Maintenance | Sulit | Mudah dengan scripts |
| Audit Trail | Terpisah | Terintegrasi |

---

## 6. Rekomendasi Segera

**Untuk mencegah kebingungan saat ini:**

1. **Update file TASK_XXX.md** untuk mencerminkan status COMPLETED berdasarkan implementasi kode
2. **Tambahkan header di setiap TASK_XXX.md:**
   ```markdown
   > ⚠️ **NOTE:** Status task ini mungkin outdated. 
   > Lihat `.agent/status/` untuk status aktual atau jalankan:
   > `python3 scripts/verify_task_status.py`
   ```
3. **Hapus file task yang sudah tidak relevan** setelah migrasi ke sistem baru

---

## Lampiran: Checklist Refaktorisasi

- [ ] Audit semua task files
- [ ] Update status berdasarkan implementasi aktual
- [ ] Buat struktur direktori baru
- [ ] Implementasi verification script
- [ ] Setup git hooks
- [ ] Dokumentasikan workflow baru
- [ ] Hapus file-file lama
- [ ] Training/knowledge transfer

---

**Dibuat oleh:** MCP Agent  
**Status:** Proposal - Menunggu Approval
