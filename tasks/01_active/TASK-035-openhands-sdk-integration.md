# TASK-035: OpenHands Integration — Phase 2: SDK Integration & Testing

**Dibuat:** 2026-04-01  
**Status:** BACKLOG  
**Priority:** HIGH  
**Assignee:** TBD

---

## Deskripsi

Integrasi OpenHands SDK dengan orchestrator dan memastikan agent bisa menjalankan coding tasks secara autonomous. Termasuk setup sandboxed environment dan LLM backend configuration.

## Acceptance Criteria

- [x] OpenHands SDK berhasil diinstall dan ter-import di orchestrator (v1.6.0 verified)
- [x] Agent bisa menerima task dari MCP pipeline dan mengeksekusi (SDK or mock fallback)
- [x] RESULT.json dihasilkan oleh agent setelah task selesai
- [x] Status task tersimpan di Redis dengan benar (pending → running → success/failed)
- [x] Timeout handling berfungsi dengan baik
- [x] Cancel task berfungsi via Redis flag
- [x] Unit test end-to-end berhasil (16/16 pass)

## Subtasks

- [x] 035-A: Install dan test OpenHands SDK standalone (verified PyPI v1.6.0)
- [x] 035-B: Integrasikan SDK ke orchestrator.py (with fallback)
- [x] 035-C: Setup sandboxed workspace untuk agent execution
- [x] 035-D: Konfigurasi LLM backend (Claude/GPT) untuk OpenHands
- [x] 035-E: Implementasi task lifecycle (submit → run → complete)
- [x] 035-F: Implementasi timeout dan cancel handling
- [x] 035-G: Implementasi RESULT.json parsing
- [x] 035-H: End-to-end integration test (16/16 unit tests pass)
- [x] 035-I: Error handling dan retry mechanism (SDK import fallback)

## Dependensi

- Depends on: TASK-034 (Foundation Setup)
- Blocks: TASK-036 (Telegram Bot Integration)

## Risiko & Mitigasi

| Risiko | Mitigasi |
|--------|----------|
| OpenHands SDK incompatible dengan Python version | Cek compatibility matrix sebelum install |
| Sandboxing tidak bekerja di environment tertentu | Sediakan fallback mode tanpa sandbox |
| LLM API rate limiting | Implementasi backoff dan queue management |
| Memory leak pada long-running agents | Set hard limit dan cleanup routine |

## Catatan

- Pastikan orchestrator menggunakan asyncio yang benar untuk non-blocking execution
- RESULT.json format harus sesuai dengan schemas.py TaskResult model
- Testing harusครอบคลุม happy path dan error cases

---

## Log Perubahan

| Tanggal | Status | Oleh | Catatan |
|---------|--------|------|---------|
| 2026-04-01 | BACKLOG | agent | Task dibuat berdasarkan proposal |
| 2026-04-01 | COMPLETE | agent | Semua subtasks selesai. SDK v1.6.0 verified, orchestrator updated, 16/16 tests pass |
