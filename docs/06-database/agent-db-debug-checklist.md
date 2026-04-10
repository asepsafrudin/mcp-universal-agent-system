# Agent DB Debug Checklist

Checklist singkat untuk membantu agent IDE, OpenHands, dan task sandbox saat koneksi ke knowledge base/PostgreSQL bermasalah.

## 1. Cek env runtime

Pastikan variabel berikut tersedia di proses yang menjalankan task:

- `DATABASE_URL`
- `PG_HOST`
- `PG_PORT`
- `PG_DATABASE`
- `PG_USER`
- `PG_PASSWORD`

Jika `DATABASE_URL` tidak ada, cek apakah `PG_*` masih cukup untuk membangun DSN.

## 2. Jangan asumsi `localhost`

Di sandbox/container:

- `localhost` bisa berarti container itu sendiri
- host machine belum tentu terlihat dari dalam sandbox
- pastikan DB benar-benar dapat dijangkau dari runtime task

## 3. Gunakan observability OpenHands

Jika task berjalan lewat OpenHands:

- baca `mcp://openhands/task/env-context`
- cek `mcp://openhands/task/{task_id}/status`
- cek `mcp://openhands/task/{task_id}/logs`

## 4. Cek workspace task

Di workspace task akan ada file:

- `ENV_CONTEXT.md`

File ini berisi snapshot env yang aman dan bisa dipakai untuk debugging awal.

## 5. Verifikasi database target

Pastikan target yang dipakai benar:

- `mcp_knowledge` untuk korespondensi / knowledge base
- `mcp` untuk `mcp-unified` lama atau runtime lain jika memang masih dipakai

## 6. Bila masih gagal

Catat:

- error persisnya
- task runtime yang dipakai
- apakah ini running di host, terminal lokal, atau sandbox/container
- apakah `DATABASE_URL` ada namun tidak bisa di-resolve / tidak bisa dijangkau

## 7. Rujukan tambahan

- [`agent-db-access-notes.md`](./agent-db-access-notes.md)
- [`README.md`](./README.md)
- [`../07-core-technical/agent-knowledge-integration.md`](../07-core-technical/agent-knowledge-integration.md)

