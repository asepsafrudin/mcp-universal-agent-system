# 03-development — Development Guide

Panduan development, task management, dan code standards untuk MCP Unified Server.

## 📋 Konten

| File | Deskripsi |
|------|-----------|
| [`task-system-refactoring.md`](./task-system-refactoring.md) | Proposal refaktorisasi sistem task |
| [`backlog.md`](./backlog.md) | Technical debt dan backlog items |
| [`ROOT_CLEANUP_ANALYSIS.md`](./ROOT_CLEANUP_ANALYSIS.md) | Analisis root folder cleanup |
| [`CONFIG_PRECEDENCE_MAP.md`](./CONFIG_PRECEDENCE_MAP.md) | Prioritas config lintas-agent (.vscode/.cursor/.gemini/.venv/serena) |

## 🗂️ Task System

Sistem task menggunakan struktur terpisah:

```
tasks/
├── README.md              # Overview task system
├── template.md            # Template task baru
├── active/                # Tasks aktif
├── backlog/               # Tasks backlog
├── completed/             # Tasks selesai
└── status/                # Status tracking
```

### Workflow Task

1. **Membuat Task**: Gunakan template dari `tasks/template.md`
2. **Development**: Kerjakan di folder `tasks/active/`
3. **Review**: Setelah selesai, pindah ke `tasks/completed/`
4. **Archive**: Review doc disimpan di `docs/reviews/`

### Status Task

| Task Range | Status |
|------------|--------|
| TASK-001 s/d TASK-011 | ✅ Completed |

📄 Detail: [`task-system-refactoring.md`](./task-system-refactoring.md)

## 📊 Backlog

Technical debt yang terdokumentasi:

- **BACKLOG-001**: LLM-based Self Healing
- **BACKLOG-002**: Syntax Error Auto-Fix

📄 Detail: [`backlog.md`](./backlog.md)

## 🔧 Root Cleanup

Analisis root folder dan rekomendasi pembersihan:

- Path inconsistencies
- File duplikat
- Kredensial yang perlu diamankan
- Script yang mereferensi file tidak ada

📄 Detail: [`ROOT_CLEANUP_ANALYSIS.md`](./ROOT_CLEANUP_ANALYSIS.md)

## 📖 Related Documentation

- **Task System** → [`../tasks/`](../tasks/)
- **Testing Guide** → [`../04-operations/testing.md`](../04-operations/testing.md)
- **Architecture** → [`../02-architecture/`](../02-architecture/)
