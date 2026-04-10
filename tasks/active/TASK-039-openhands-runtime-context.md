# TASK-039: OpenHands Runtime Context Snapshot

**Dibuat:** 2026-04-09  
**Status:** ✅ COMPLETED  
**Priority:** HIGH  
**Assignee:** TBD

---

## Deskripsi

Tambahkan mekanisme snapshot environment runtime untuk task OpenHands agar agent dapat membaca konteks kerja yang konsisten dari workspace.

## Acceptance Criteria

- [ ] Snapshot env runtime ditulis ke workspace task.
- [ ] Snapshot memuat variabel inti yang relevan.
- [ ] Secret sensitif tidak dibocorkan mentah di file context.
- [ ] Format snapshot mudah dibaca agent lain.

## Subtasks

- [ ] 039-A: Tentukan daftar variabel environment minimum.
- [ ] 039-B: Implementasi writer `ENV_CONTEXT.md`.
- [ ] 039-C: Pastikan snapshot aman dan ter-normalisasi.

## Dependensi

- Depends on: None
- Blocks: TASK-041, TASK-042

## Risiko & Mitigasi

| Risiko | Mitigasi |
|--------|----------|
| Secret bocor ke workspace | Masking nilai sensitif sebelum ditulis |
| Format tidak konsisten | Gunakan template Markdown tetap |

## Catatan

Target utama task ini adalah memberi OpenHands dan agent IDE lain satu sumber konteks runtime yang stabil.
Prioritas eksekusi: #1.

---

## Log Perubahan

| Tanggal | Status | Oleh | Catatan |
|---------|--------|------|---------|
| 2026-04-09 | BACKLOG | agent | Task dibuat |
