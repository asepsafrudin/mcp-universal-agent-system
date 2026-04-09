# TASK-042: OpenHands Observability Resources

**Dibuat:** 2026-04-09  
**Status:** ACTIVE  
**Priority:** MEDIUM  
**Assignee:** TBD

---

## Deskripsi

Tambahkan resource observability MCP untuk membantu debugging OpenHands dan service internal dari agent lain tanpa akses host langsung.

## Acceptance Criteria

- [ ] Ada resource untuk env context task aktif.
- [ ] Ada resource untuk status service aktif.
- [ ] Ada resource untuk ringkasan error terakhir.
- [ ] Ada resource untuk riwayat task atau workflow sebelumnya.
- [ ] Resource dapat dikonsumsi agent IDE lain.

## Subtasks

- [ ] 042-A: Rancang format resource observability.
- [ ] 042-B: Implementasi pembaca resource aktif.
- [ ] 042-C: Dokumentasikan penggunaan resource.

## Dependensi

- Depends on: TASK-039, TASK-040
- Blocks: TASK-045

## Risiko & Mitigasi

| Risiko | Mitigasi |
|--------|----------|
| Resource terlalu besar | Tampilkan ringkasan dan limit data |
| Agent bingung sumber mana yang dipakai | Tautkan resource ke README dan task notes |

## Catatan

Focus task ini adalah membuat debugging agent lebih transparan dan dapat diulang.
Prioritas eksekusi: #4.

---

## Log Perubahan

| Tanggal | Status | Oleh | Catatan |
|---------|--------|------|---------|
| 2026-04-09 | BACKLOG | agent | Task dibuat |
