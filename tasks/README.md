# Task Management System — Standar & Konvensi

**Versi:** 1.0  
**Dibuat:** 2026-02-20  
**Tujuan:** Menstandarisasi manajemen task untuk mencegah diskrepansi status

---

## 📁 Struktur Folder

```
/home/aseps/MCP/
├── tasks/
│   ├── README.md              # Dokumen ini
│   ├── active/                # Task yang sedang dikerjakan
│   │   ├── TASK-012-new-feature.md
│   │   └── TASK-013-bug-fix.md
│   ├── backlog/               # Task yang belum dimulai
│   │   └── TASK-014-future-idea.md
│   ├── completed/             # Task yang sudah selesai
│   │   └── TASK-001-security-hardening.md
│   └── status/                # Status dinamis tiap task
│       ├── TASK-012-status.md
│       └── TASK-013-status.md
├── docs/
│   └── reviews/               # Review reports (read-only setelah selesai)
│       └── YYYY-MM-DD/
│           └── task-XXX-review.md
└── scripts/
    └── task-manager.py        # Utility untuk manage tasks
```

---

## 📝 Konvensi Penamaan

### Task Files
```
TASK-{NNN}-{short-description}.md

Contoh:
✅ TASK-012-implement-auth.md
✅ TASK-013-fix-memory-leak.md
❌ task_012.md (kurang deskriptif)
❌ 012-auth.md (tanpa prefix TASK)
```

### Status Files
```
TASK-{NNN}-status.md

Contoh:
✅ TASK-012-status.md
❌ status-012.md
❌ 012-status.md
```

### Review Files
```
docs/reviews/YYYY-MM-DD/task-{NNN}-review.md

Contoh:
✅ docs/reviews/2026-02-20/task-012-review.md
```

---

## 🔄 Lifecycle Task

```
BACKLOG → ACTIVE → COMPLETED
   ↑         ↓         ↓
   └──── BLOCKED ←────┘
```

### Status Valid
- `BACKLOG` — Belum dimulai, dalam antrian
- `ACTIVE` — Sedang dikerjakan
- `BLOCKED` — Tertunda (butuh approval/dependency)
- `COMPLETED` — Selesai, sudah direview

---

## 📋 Format Task File (Template)

```markdown
# TASK-{NNN}: {Judul Task}

**Dibuat:** YYYY-MM-DD  
**Status:** {BACKLOG|ACTIVE|BLOCKED|COMPLETED}  
**Priority:** {CRITICAL|HIGH|MEDIUM|LOW}  
**Assignee:** {nama agent}

---

## Deskripsi

{Deskripsi singkat apa yang perlu dikerjakan}

## Acceptance Criteria

- [ ] Kriteria 1
- [ ] Kriteria 2
- [ ] Kriteria 3

## Subtasks

- [ ] {NNN}-A: {deskripsi}
- [ ] {NNN}-B: {deskripsi}

## Dependensi

- Depends on: TASK-{XXX} (jika ada)
- Blocks: TASK-{YYY} (jika ada)

## Catatan

{Catatan tambahan}

---

## Log Perubahan

| Tanggal | Status | Oleh | Catatan |
|---------|--------|------|---------|
| YYYY-MM-DD | BACKLOG | agent | Task dibuat |
| YYYY-MM-DD | ACTIVE | agent | Mulai mengerjakan |
| YYYY-MM-DD | COMPLETED | agent | Selesai, review di docs/reviews/ |
```

---

## 📊 Format Status File (Auto-generated)

```markdown
# TASK-{NNN} Status

**Task:** [{Judul}](../active/TASK-{NNN}-{desc}.md)  
**Last Updated:** YYYY-MM-DD HH:MM  
**Updated By:** {agent name}

---

## Current Status: {BACKLOG|ACTIVE|BLOCKED|COMPLETED}

## Progress Checklist
- [x] Subtask A
- [ ] Subtask B (in progress)
- [ ] Subtask C

## Verification
| Aspek | Status | Detail |
|-------|--------|--------|
| Code | ✅/❌ | {file yang diubah} |
| Tests | ✅/❌ | {X}/{Y} passed |
| Docs | ✅/❌ | {file review} |

## Blockers
{jika ada, atau "None"}

## Next Steps
{apa yang harus dilakukan selanjutnya}
```

---

## 🔍 Workflow

### 1. Membuat Task Baru

```bash
# 1. Copy template
cp tasks/template.md tasks/backlog/TASK-015-{deskripsi}.md

# 2. Edit isi task
# ... edit file ...

# 3. Generate status file
python3 scripts/task-manager.py create-status 015

# 4. Pindahkan ke active saat mulai mengerjakan
mv tasks/backlog/TASK-015-{desc}.md tasks/active/
```

### 2. Update Progress

```bash
# Update status file otomatis
python3 scripts/task-manager.py update-status 015 --status ACTIVE

# Atau edit manual
vim tasks/status/TASK-015-status.md
```

### 3. Menyelesaikan Task

```bash
# 1. Final verification
python3 scripts/task-manager.py verify 015

# 2. Generate review template
python3 scripts/task-manager.py create-review 015

# 3. Pindahkan ke completed
mv tasks/active/TASK-015-{desc}.md tasks/completed/

# 4. Update status
python3 scripts/task-manager.py update-status 015 --status COMPLETED
```

---

## 🛠️ Tools & Scripts

### task-manager.py Commands

```bash
# List semua task
python3 scripts/task-manager.py list

# Cek status satu task
python3 scripts/task-manager.py status 015

# Verifikasi task complete
python3 scripts/task-manager.py verify 015

# Cek diskrepansi
python3 scripts/task-manager.py audit

# Generate report
python3 scripts/task-manager.py report
```

---

## ⚠️ Aturan Penting

1. **Jangan edit file di `completed/`** — Read only
2. **Status file diupdate setelah setiap sesi kerja**
3. **Review docs dibuat saat task COMPLETED**
4. **Gunakan `scripts/task-manager.py` untuk consistency**

---

## 📚 Contoh Lengkap

Lihat folder `examples/` untuk:
- `sample-task.md` — Contoh task lengkap
- `sample-status.md` — Contoh status file
- `sample-review.md` — Contoh review file

---

## 🔗 Integrasi dengan Dokumentasi

- `/docs/` — Dokumentasi umum (architecture, guides)
- `/docs/reviews/` — Review reports (read-only, historical)
- `/tasks/` — Task management (active, dynamic)

**Prinsip:** `/docs` untuk hasil akhir, `/tasks` untuk proses.
