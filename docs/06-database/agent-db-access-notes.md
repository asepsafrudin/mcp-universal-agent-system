# Agent DB Access Notes

Dokumen ini menjelaskan cara kerja akses database untuk agent IDE, OpenHands, dan MCP tools di repo ini.

## Ringkasan

- Knowledge dan state korespondensi memakai PostgreSQL lokal.
- Koneksi yang dipakai untuk `korespondensi-server` ada di database `mcp_knowledge`.
- Konfigurasi environment harus lengkap, termasuk `PG_PASSWORD` dan `DATABASE_URL`, agar agent tidak salah fallback ke default kosong.
- OpenHands sandbox bisa berjalan terisolasi, jadi agent harus selalu memverifikasi env runtime sebelum asumsi koneksi database.

## Environment Penting

Untuk `korespondensi-server`:

- `PG_HOST=localhost`
- `PG_PORT=5433`
- `PG_DATABASE=mcp_knowledge`
- `PG_USER=mcp_user`
- `PG_PASSWORD=mcp_password_2024`
- `DATABASE_URL=postgresql://mcp_user:mcp_password_2024@localhost:5433/mcp_knowledge`

Catatan runtime:
- `korespondensi-server/src/server.py` sekarang memuat `.env` dari root project dan `mcp-unified/.env` sebelum fallback ke env lokal
- ini membantu agent / service yang berjalan dengan working directory berbeda tetap memakai credential yang sama

## Titik Konfigurasi

- Cursor MCP config: `.cursor/mcp.json`
- Web server DB helper: `korespondensi-server/src/database.py`
- Knowledge config: `mcp-unified/knowledge/config.py`
- OpenHands prompt rules: `mcp-unified/plugins/openhands/prompt_templates.py`

## Catatan Operasional

- Jangan asumsikan `localhost` di dalam sandbox adalah host machine.
- Jika agent berada di container/sandbox terpisah, cek apakah DB bisa dijangkau dari environment itu.
- Jika perlu debugging, mulai dari:
  - `echo $DATABASE_URL`
  - `env | grep -E '^(PG|POSTGRES|DATABASE_URL)'`
  - uji koneksi DB dari proses yang sama dengan agent
