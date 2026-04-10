# Agent Startup Matrix

Ringkasan cepat untuk melihat agent/runtime mana memakai env mana, resource apa yang tersedia, dan database target yang seharusnya dipakai.

## 1. Cursor / IDE MCP

- Config utama: [`.cursor/mcp.json`](../../.cursor/mcp.json)
- Env penting:
  - `PG_HOST`
  - `PG_PORT`
  - `PG_DATABASE`
  - `PG_USER`
  - `PG_PASSWORD`
  - `DATABASE_URL`
- Catatan:
  - dipakai oleh agent IDE yang membaca MCP config workspace
  - cocok untuk debugging koneksi awal sebelum masuk ke runtime server

## 2. `korespondensi-server`

- Entry point: [`korespondensi-server/src/server.py`](../../korespondensi-server/src/server.py)
- Env load order:
  1. root `/.env`
  2. `mcp-unified/.env`
  3. env lokal proses
- DB target:
  - `mcp_knowledge`
  - port `5433`
- Catatan:
  - server ini sekarang memuat shared env project terlebih dahulu
  - default password fallback masih ada di kode, tapi sebaiknya runtime env tetap lengkap

## 3. `mcp-unified` MCP Server

- Entry point:
  - [`mcp-unified/mcp_server.py`](../../mcp-unified/mcp_server.py)
  - [`mcp-unified/mcp_server_sse.py`](../../mcp-unified/mcp_server_sse.py)
- Env load order:
  - shared secrets via `core/secrets.py`
- DB target:
  - knowledge layer umumnya memakai `mcp_knowledge`
  - bootstrap juga menyalakan komponen memory/knowledge lain sesuai env runtime

## 4. OpenHands Task Runtime

- Orchestrator: [`mcp-unified/plugins/openhands/orchestrator.py`](../../mcp-unified/plugins/openhands/orchestrator.py)
- Prompt rules: [`mcp-unified/plugins/openhands/prompt_templates.py`](../../mcp-unified/plugins/openhands/prompt_templates.py)
- Observability resource:
  - `mcp://openhands/task/env-context`
  - `mcp://openhands/task/{task_id}/status`
  - `mcp://openhands/task/{task_id}/logs`
- Env context:
  - disimpan ke `ENV_CONTEXT.md` dalam workspace task
- Catatan:
  - sandbox bisa berbeda dari host
  - agent harus cek runtime env sebelum asumsi koneksi DB

## 5. Debug Path yang Disarankan

Jika koneksi knowledge DB gagal:

1. Cek `DATABASE_URL`
2. Cek `PG_HOST`, `PG_PORT`, `PG_DATABASE`, `PG_USER`, `PG_PASSWORD`
3. Cek apakah target DB memang `mcp_knowledge`
4. Cek resource `mcp://openhands/task/env-context`
5. Cek `ENV_CONTEXT.md`
6. Baru cek apakah sandbox punya akses jaringan ke host DB

## 6. Referensi Lain

- [agent-db-access-notes.md](./agent-db-access-notes.md)
- [agent-db-debug-checklist.md](./agent-db-debug-checklist.md)
- [../07-core-technical/agent-knowledge-integration.md](../07-core-technical/agent-knowledge-integration.md)

