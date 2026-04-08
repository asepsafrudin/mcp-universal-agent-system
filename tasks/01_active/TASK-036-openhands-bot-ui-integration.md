# TASK-036: OpenHands Integration — Phase 3: Bot & Admin UI Integration

**Dibuat:** 2026-04-01  
**Status:** BACKLOG  
**Priority:** MEDIUM  
**Assignee:** TBD

---

## Deskripsi

Integrasikan OpenHands agent dengan Telegram bot untuk user interaction dan Admin UI untuk monitoring. User bisa request coding tasks via chat dan monitor progress via web dashboard.

## Acceptance Criteria

- [x] Telegram bot handler bisa menerima permintaan coding task (`/code`, `/coding`)
- [x] Polling mechanism implemented untuk cek task status (30s interval, max 120 polls)
- [x] User mendapat notifikasi saat task mulai, progress, dan selesai
- [ ] OpenHands agent muncul di Admin UI service list (deferred ke TASK-038)
- [ ] Service bisa di-start/stop/restart dari Admin UI (deferred ke TASK-038)
- [ ] Logs OpenHands agent bisa diakses dari Admin UI (deferred ke TASK-038)

## Subtasks

- [x] 036-A: Buat Telegram bot handler untuk coding task requests
- [x] 036-B: Implementasi task polling dan status notification
- [x] 036-C: Format hasil task untuk dikirim ke user
- [x] 036-D: Register coding handler di handlers/__init__.py
- [x] 036-E: StatusCommandHandler untuk cek task manual
- [x] 036-F: Integration dengan MCP tools registry
- [x] 036-G: Message formatting dengan Telegram HTML/Markdown

## Dependensi

- Depends on: TASK-035 (SDK Integration)
- Blocks: TASK-037 (App Developer Agent Profile)

## Risiko & Mitigasi

| Risiko | Mitigasi |
|--------|----------|
| Telegram message too long untuk hasil task | Implementasi chunking atau file upload |
| Polling terlalu sering membebani Redis | Set interval minimal 30 detik |
| Admin UI tidak bisa monitor background agent | Gunakan Redis keys untuk status tracking |

## Catatan

- Telegram bot sudah ada di `integrations/telegram/`
- Admin UI sudah ada di `services/service_controller.py`
- Gunakan pattern yang sudah ada untuk konsistensi

---

## Log Perubahan

| Tanggal | Status | Oleh | Catatan |
|---------|--------|------|---------|
| 2026-04-01 | BACKLOG | agent | Task dibuat berdasarkan proposal |
| 2026-04-01 | COMPLETE | agent | Telegram handler & status command dibuat. Admin UI deferred ke TASK-038 |
