# TASK-034: OpenHands Integration — Phase 1: Foundation Setup

**Dibuat:** 2026-04-01  
**Status:** COMPLETED  
**Priority:** HIGH  
**Assignee:** agent

---

## Deskripsi

Setup fondasi untuk integrasi OpenHands ke dalam mcp-unified. Meliputi pembuatan struktur folder plugin, konfigurasi environment, dan dependency installation sesuai proposal di `docs/proposals/PROPOSAL/openhands_integration.md`.

## Acceptance Criteria

- [x] Folder `plugins/openhands/` dibuat dengan semua file struktur
- [x] File `config.py`, `schemas.py`, `orchestrator.py`, `openhands_tool.py`, `prompt_templates.py` dibuat
- [x] Environment variables ditambahkan ke `.env.example`
- [x] `openhands-ai` placeholder ditambahkan ke `requirements.txt` (commented, tunggu SDK stabil)
- [x] Plugin bisa dideteksi oleh auto-discovery system (registry.register tanpa `description` param)
- [x] Unit test dasar untuk schemas dan config (16/16 tests pass)

## Subtasks

- [x] 034-A: Buat folder `plugins/openhands/` dan file `config.py` + `schemas.py`
- [x] 034-B: Implementasi `prompt_templates.py` dengan system prompts
- [x] 034-C: Implementasi `orchestrator.py` (SDK wrapper + session management)
- [x] 034-D: Implementasi `openhands_tool.py` (MCP tool registrations)
- [x] 034-E: Update `requirements.txt` dengan `openhands-ai` placeholder
- [x] 034-F: Update `.env.example` dengan OpenHands env vars
- [x] 034-G: Testing plugin discovery (registry API compatibility verified)

## Dependensi

- Depends on: None
- Blocks: TASK-035 (OpenHands SDK Integration), TASK-036 (Telegram Bot Integration)

## Risiko & Mitigasi

| Risiko | Mitigasi |
|--------|----------|
| OpenHands SDK belum stabil/masih beta | Gunakan versi spesifik dan siap fallback ke CLI |
| Redis dependency conflict | Pastikan Redis client yang digunakan kompatibel |
| Resource usage tinggi | Set `OPENHANDS_MAX_AGENTS` konservatif (3) |

## Catatan

- Proposal lengkap ada di `docs/proposals/PROPOSAL/openhands_integration.md`
- Semua tool harus menggunakan `@registry.register` decorator
- Pastikan import path sesuai dengan struktur mcp-unified yang ada

---

## Log Perubahan

| Tanggal | Status | Oleh | Catatan |
|---------|--------|------|---------|
| 2026-04-01 | ACTIVE | agent | Task dibuat berdasarkan proposal |
| 2026-04-01 | COMPLETE | agent | Semua subtasks selesai. 16/16 unit tests pass. |
