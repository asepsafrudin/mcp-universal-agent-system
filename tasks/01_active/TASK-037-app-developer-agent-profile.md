# TASK-037: OpenHands Integration — Phase 4: App Developer Agent Profile

**Dibuat:** 2026-04-01  
**Status:** BACKLOG  
**Priority:** MEDIUM  
**Assignee:** TBD

---

## Deskripsi

Buat agent profile khusus "App Developer" yang mengintegrasikan OpenHands sebagai specialized agent di MCP Unified. Agent ini akan menjadi "code_agent" yang ditingkatkan dengan kemampuan autonomous coding.

## Acceptance Criteria

- [x] File `agents/profiles/app_developer_agent.py` dibuat
- [x] Agent profile terdaftar dengan nama `app_developer_agent`
- [x] Agent bisa handle task type terkait app development
- [x] Agent menggunakan OpenHands tools (`run_coding_task`, `get_task_status`)
- [x] Agent memiliki skill composition untuk full app development lifecycle
- [x] Integration test dengan orchestrator berhasil
- [x] Agent terdaftar di `agents/profiles/__init__.py`

## Subtasks

- [x] 037-A: Buat `app_developer_agent.py` di `agents/profiles/`
- [x] 037-B: Definisikan AgentProfile dengan capabilities dan tools_whitelist
- [x] 037-C: Implementasi `can_handle()` untuk app development tasks
- [x] 037-D: Implementasi `execute()` dengan OpenHands delegation
- [x] 037-E: Register agent di `agents/profiles/__init__.py`
- [x] 037-F: Agent registration verified via @register_agent decorator

## Dependensi

- Depends on: TASK-036 (Bot & UI Integration)
- Blocks: None

## Risiko & Mitigasi

| Risiko | Mitigasi |
|--------|----------|
| Agent profile tidak ter-discover dengan benar | Pastikan decorator `@register_agent` digunakan |
| Task routing tidak optimal ke agent ini | Update orchestrator routing logic |
| Conflict dengan code_agent yang ada | Definisikan boundary jelas antara code_agent dan app_developer_agent |

## Catatan

- App Developer Agent berbeda dari code_agent: fokus pada full app development lifecycle (scaffolding, coding, testing, deployment)
- code_agent fokus pada code analysis dan review
- Gunakan inspirasi dari MetaGPT untuk multi-role capabilities

## App Development Capabilities

Agent ini harus bisa handle:
- Web app scaffolding (FastAPI, Flask, etc.)
- CRUD API generation
- Database schema creation
- Testing setup dan generation
- Deployment script generation
- Documentation generation

---

## Log Perubahan

| Tanggal | Status | Oleh | Catatan |
|---------|--------|------|---------|
| 2026-04-01 | BACKLOG | agent | Task dibuat berdasarkan proposal |
| 2026-04-01 | COMPLETE | agent | Semua subtasks selesai. Agent profile dibuat dan terdaftar |
