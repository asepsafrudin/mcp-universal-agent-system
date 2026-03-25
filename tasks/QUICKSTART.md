# Quickstart: Membuat Task Baru

**3 Langkah Mudah:**

---

## Step 1: Buat Task File di `tasks/backlog/`

```bash
# Copy template
cp tasks/template.md tasks/backlog/TASK-012-implement-auth.md

# Edit isi task
nano tasks/backlog/TASK-012-implement-auth.md
```

**Isi yang perlu diupdate:**
- `{NNN}` → nomor task (012)
- `{Judul Task}` → "Implement Authentication System"
- `YYYY-MM-DD` → tanggal hari ini
- Deskripsi, acceptance criteria, subtasks

---

## Step 2: Generate Status File

```bash
python3 scripts/task-manager.py create-status 12
```

Ini akan membuat: `tasks/status/TASK-012-status.md`

---

## Step 3: Saat Siap Mengerjakan

```bash
# Pindahkan dari backlog ke active
mv tasks/backlog/TASK-012-implement-auth.md tasks/active/

# Update status
python3 scripts/task-manager.py update-status 12 --status ACTIVE
```

---

## Ringkasan Folder

| Folder | Kapan Digunakan | Contoh Isi |
|--------|-----------------|------------|
| `tasks/backlog/` | **Task baru** — belum dimulai | TASK-013-future-idea.md |
| `tasks/active/` | **Sedang dikerjakan** | TASK-012-implement-auth.md |
| `tasks/completed/` | **Sudah selesai** | TASK-001-security.md |
| `tasks/status/` | **Status dinamis** — auto generated | TASK-012-status.md |

---

## Visual Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   BACKLOG       │ ──► │     ACTIVE      │ ──► │   COMPLETED     │
│  (tasks/backlog)│     │  (tasks/active) │     │ (tasks/completed│
│                 │     │                 │ │   │                 │
│ TASK-013.md     │     │ TASK-012.md     │ │   │ TASK-001.md     │
│ (baru dibuat)   │     │ (dikerjakan)    │ │   │ (sudah selesai) │
└─────────────────┘     └─────────────────┘ │   └─────────────────┘
                                            │
                                            ▼
                                    tasks/status/
                                    TASK-012-status.md
                                    (auto update)
```

---

## Contoh Lengkap

### Membuat Task-012:

```bash
# 1. Create from template
cp tasks/template.md tasks/backlog/TASK-012-implement-auth.md

# 2. Edit content
# ... edit file ...

# 3. Generate status
python3 scripts/task-manager.py create-status 12
# Output: ✅ Created status file: tasks/status/TASK-012-status.md

# 4. When ready to start
mv tasks/backlog/TASK-012-implement-auth.md tasks/active/
python3 scripts/task-manager.py update-status 12 --status ACTIVE

# 5. Work on the task...
# ... coding ...

# 6. When completed
mv tasks/active/TASK-012-implement-auth.md tasks/completed/
python3 scripts/task-manager.py update-status 12 --status COMPLETED

# 7. Create review doc in docs/reviews/YYYY-MM-DD/
```

---

## Aturan Penting

1. **Task baru SELALU mulai dari `backlog/`**
2. **Status file OTOMATIS di `status/`** — jangan edit manual
3. **Pindahkan ke `active/` saat mulai mengerjakan**
4. **Pindahkan ke `completed/` saat selesai + review**

---

## Command Cheat Sheet

```bash
# List semua task
python3 scripts/task-manager.py list

# Cek detail task
python3 scripts/task-manager.py status 12

# Update status
python3 scripts/task-manager.py update-status 12 --status BLOCKED

# Cek konsistensi
python3 scripts/task-manager.py audit
```
