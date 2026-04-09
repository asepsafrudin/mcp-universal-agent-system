# TASK-040: OpenHands Service Registry

**Dibuat:** 2026-04-09  
**Status:** ACTIVE  
**Priority:** HIGH  
**Assignee:** TBD

---

## Deskripsi

Buat registry layanan internal untuk `mcp-unified` agar OpenHands dan agent lain tidak perlu menebak URL, auth mode, atau health endpoint service penting.

## Acceptance Criteria

- [ ] Registry service internal tersedia dalam format yang mudah dibaca.
- [ ] Minimal service `waha`, `korespondensi`, `postgres_knowledge`, dan `admin_ui` terdaftar.
- [ ] Setiap service memiliki metadata base URL, health endpoint, dan auth mode.
- [ ] Registry dapat dipakai ulang oleh task lain.

## Subtasks

- [ ] 040-A: Definisikan struktur registry service.
- [ ] 040-B: Isi metadata service utama.
- [ ] 040-C: Dokumentasikan cara baca registry.

## Dependensi

- Depends on: TASK-039
- Blocks: TASK-041, TASK-042, TASK-043

## Risiko & Mitigasi

| Risiko | Mitigasi |
|--------|----------|
| Registry berbeda dari runtime nyata | Sinkronkan dengan env context snapshot |
| URL berubah tanpa dokumentasi | Tambahkan referensi ke README dan task notes |

## Catatan

Registry ini harus menjadi sumber referensi bersama untuk semua agent.
Prioritas eksekusi: #2.

---

## Log Perubahan

| Tanggal | Status | Oleh | Catatan |
|---------|--------|------|---------|
| 2026-04-09 | BACKLOG | agent | Task dibuat |
