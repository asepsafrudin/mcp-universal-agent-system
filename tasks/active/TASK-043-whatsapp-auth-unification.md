# TASK-043: WhatsApp Auth Unification

**Dibuat:** 2026-04-09  
**Status:** ACTIVE  
**Priority:** HIGH  
**Assignee:** TBD

---

## Deskripsi

Satukan jalur autentikasi WhatsApp agar `mcp-unified` menjadi source of truth, termasuk flow QR device auth, basic auth/proxy auth jika ada, dan shared client yang dipakai service lain.

## Acceptance Criteria

- [ ] Jalur auth WhatsApp terpusat di `mcp-unified`.
- [ ] Service lain memakai shared client/session, bukan auth duplikat.
- [ ] Mode auth terdokumentasi dengan jelas.
- [ ] Flow kirim pesan dari dashboard anomali memakai jalur yang sama.

## Subtasks

- [ ] 043-A: Audit flow auth WAHA aktif.
- [ ] 043-B: Definisikan mode auth yang benar untuk runtime host.
- [ ] 043-C: Sinkronkan korespondensi-server ke shared client.

## Dependensi

- Depends on: TASK-040, TASK-041
- Blocks: None

## Risiko & Mitigasi

| Risiko | Mitigasi |
|--------|----------|
| Auth berbeda antar runtime | Jadikan satu source of truth dan dokumentasikan |
| 401 karena proxy/basic auth | Audit service host dan simpan mode auth yang benar |

## Catatan

Task ini harus diprioritaskan karena berdampak langsung ke pengiriman laporan anomali lewat WhatsApp.
Prioritas eksekusi: #5.

---

## Log Perubahan

| Tanggal | Status | Oleh | Catatan |
|---------|--------|------|---------|
| 2026-04-09 | BACKLOG | agent | Task dibuat |
