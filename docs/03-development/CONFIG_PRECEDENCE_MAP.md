# CONFIG_PRECEDENCE_MAP — Multi-Agent Config Baseline

Dokumen ini menetapkan urutan prioritas konfigurasi saat bekerja di workspace `/home/aseps/MCP`, agar perilaku agent konsisten lintas tool (Codex, Cursor, Gemini, Serena).

## Tujuan

1. Mencegah konflik konfigurasi antar-agent.
2. Menjamin path, env, dan endpoint MCP yang dipakai konsisten.
3. Memudahkan debugging saat ada perbedaan perilaku antar IDE/agent.

## Urutan Prioritas (Highest -> Lowest)

1. Instruksi runtime sesi aktif (system/developer/user instruction).
2. Dokumen operasional wajib di repo:
   - `docs/MANDATORY_CHECKS.md`
   - `docs/tinjauan_kritis.md`
3. Workspace config utama:
   - `.vscode/settings.json`
   - `.vscode/mcp.json`
4. Config agent lain sebagai enrichment/fallback:
   - `.cursor/mcp.json`
   - `.gemini/settings.json`
5. Runtime Python environment:
   - `.venv/pyvenv.cfg`
   - executable pada `.venv/bin/*`
6. Konfigurasi internal Serena (referensi implementasi):
   - `serena/` (symlink ke `services/serena/src/serena`)

## Baseline yang Harus Dipatuhi

1. Root workspace: `/home/aseps/MCP`
2. Python environment default: `/home/aseps/MCP/.venv`
3. MCP server baseline:
   - `mcp-unified` via `mcp-unified/mcp_server.py`
   - `serena` MCP aktif
   - `rust-mcp-filesystem` aktif
4. Untuk scope `korespondensi-server`, referensi tambahan boleh memakai entry di `.cursor/mcp.json`.

## Aturan Sinkronisasi

1. Jika `.vscode/mcp.json` dan `.cursor/mcp.json` berbeda:
   - Jadikan `.vscode/mcp.json` sebagai source of truth utama.
   - Ambil entry tambahan dari `.cursor/mcp.json` hanya jika belum ada di `.vscode`.
2. Jika `.gemini/settings.json` berbeda:
   - Perlakukan sebagai compatibility profile, bukan sumber utama.
3. Jika ada perubahan endpoint/credential penting:
   - Update minimal di `.vscode/*` dan satu config fallback (`.cursor` atau `.gemini`) agar tidak drift jauh.

## Checklist Awal Sesi

1. Jalankan health check:
   - `/home/aseps/MCP/scripts/mcp_health_check.sh`
2. Pastikan env Python:
   - `/home/aseps/MCP/.venv/bin/python3 --version`
3. Validasi config MCP utama:
   - `.vscode/mcp.json`
4. Bandingkan cepat fallback:
   - `.cursor/mcp.json`
   - `.gemini/settings.json`

## Catatan Implementasi

- Dokumen ini mengatur cara membaca dan memprioritaskan konfigurasi.
- Dokumen ini tidak menggantikan kebijakan keamanan/operasional yang sudah ada.

---

Last Updated: 2026-04-09
