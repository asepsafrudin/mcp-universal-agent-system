# TASK-041: OpenHands Task Bridge

**Dibuat:** 2026-04-09  
**Status:** ✅ COMPLETED  
**Priority:** HIGH  
**Assignee:** TBD

---

## Deskripsi

Bangun bridge yang membuat OpenHands dapat membaca `ENV_CONTEXT.md`, service registry, dan endpoint internal yang aman tanpa butuh akses langsung ke Docker socket host.

## Acceptance Criteria

- [x] Bridge membaca env context task aktif.
- [x] Bridge membaca service registry internal.
- [x] Bridge dapat memanggil endpoint internal yang aman.
- [x] Tidak ada ketergantungan wajib pada Docker socket.

## Subtasks

- [x] 041-A: Tentukan interface bridge.
- [x] 041-B: Implementasi pembaca context + registry.
- [x] 041-C: Dokumentasikan pola pemakaian bridge.

## Dependensi

- Depends on: TASK-039, TASK-040
- Blocks: TASK-042, TASK-043, TASK-044

## Risiko & Mitigasi

| Risiko | Mitigasi |
|--------|----------|
| Bridge terlalu coupled ke satu service | Gunakan interface generik dan registry |
| Akses berlebih ke service internal | Batasi ke endpoint read-only / action terkontrol |

## Catatan

Task ini adalah pusat integrasi runtime OpenHands ke ekosistem `mcp-unified`.
Prioritas eksekusi: #3.

---

## Log Perubahan

| Tanggal | Status | Oleh | Catatan |
|---------|--------|------|---------|
| 2026-04-09 | BACKLOG | agent | Task dibuat |
