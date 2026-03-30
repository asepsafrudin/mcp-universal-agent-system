# Secret Management Hardening

Dokumen ini menjadi acuan hardening secret untuk workspace MCP yang melibatkan:
- Codex MCP
- Antigravity
- `mcp-unified`
- Telegram integration
- VANE
- Serena

## Tujuan

- Minimalkan secret aktif pada saat runtime.
- Gunakan satu sumber secret terpusat.
- Terapkan principle of least privilege.
- Sediakan checklist rotasi dan verifikasi runtime tanpa mengekspos nilai secret.

## Temuan Audit

Risiko yang ditemukan di workspace ini:
- Secret provider AI pernah tersimpan literal di helper VANE dan connector riset.
- Token Telegram pernah muncul literal di script test/utilitas.
- Sebagian modul masih memakai fallback password default seperti `secure123` atau `mcp_password_2024`.
- Telegram dan `mcp-unified` memuat `.env` dari lokasi berbeda sehingga secret yang sama aktif di lebih dari satu file.
- VANE dapat mempersist environment-derived provider config ke `data/config.json`, yang memperpanjang umur secret di storage aplikasi.

## Arsitektur Secret Yang Direkomendasikan

Urutan prioritas runtime:
1. Environment process yang diinject oleh systemd, Docker, atau shell session.
2. File yang ditunjuk oleh `MCP_SECRETS_FILE`.
3. Root workspace `.env`.
4. `mcp-unified/.env` hanya sebagai fallback kompatibilitas.

Aturan operasional:
- Jangan simpan secret aktif di `mcp-unified/integrations/telegram/.env` kecuali memang ingin isolasi runtime Telegram.
- Jangan gunakan file utilitas/test sebagai tempat menyimpan token.
- Jangan commit secret ke repo, backup, atau artefak build.
- Hindari menyimpan secret yang sama di lebih dari satu file aktif.

## Principle Of Least Privilege

### Codex MCP

- Gunakan API key khusus workspace, bukan key pribadi utama.
- Batasi hanya scope/model yang dibutuhkan.
- Pisahkan key untuk development dan production.

### Antigravity

- Gunakan kredensial database dan RabbitMQ terpisah dari layanan lain.
- Jika memakai file konfigurasi MCP, pastikan hanya berisi endpoint yang dibutuhkan.

### `mcp-unified`

- Gunakan user PostgreSQL khusus aplikasi dengan hak minimal pada schema yang dipakai.
- Gunakan `RABBITMQ_URL` dengan user khusus queue MCP, bukan superuser broker.
- Jika JWT/API key dipakai, aktifkan key terpisah per environment.

### Telegram

- Gunakan satu bot token per bot/per environment.
- Isi `TELEGRAM_ALLOWED_USERS`, `TELEGRAM_ALLOWED_CHATS`, dan `TELEGRAM_ADMIN_USERS` secara eksplisit.
- Aktifkan `TELEGRAM_WEBHOOK_SECRET` saat mode webhook.
- Jangan aktifkan provider AI yang tidak dipakai.

### VANE

- Aktifkan hanya provider model yang benar-benar dipakai.
- Jangan masukkan provider key lewat helper script dengan literal secret.
- Evaluasi `data/config.json`; bila berisi provider API key, perlakukan sebagai secret-bearing file dan lindungi permission-nya.

### Serena

- Gunakan `SERENA_HOME` di direktori yang permission-nya terbatas.
- Jika Serena perlu akses provider upstream, gunakan key khusus Serena.
- Hindari berbagi token GitHub/OpenAI lintas tool jika tidak diperlukan.

## Langkah Hardening Yang Sudah Diterapkan

- Ditambahkan loader terpusat di [mcp-unified/core/secrets.py](/home/aseps/MCP/mcp-unified/core/secrets.py).
- Telegram config, MCP server, VANE connector, dan LLM API dependency sekarang memakai loader terpusat.
- Fallback hardcoded untuk Groq, Gemini, PostgreSQL, dan RabbitMQ dihapus dari jalur runtime utama.
- Test notifier Telegram diubah agar hanya membaca dari environment.
- Ditambahkan verifikasi runtime non-sensitive di [scripts/runtime_secret_check.py](/home/aseps/MCP/scripts/runtime_secret_check.py).

## Checklist Rotasi

Lakukan untuk setiap secret yang aktif:
1. Inventaris secret aktif per layanan dengan `python3 scripts/runtime_secret_check.py`.
2. Nonaktifkan atau hapus secret yang tidak dipakai.
3. Buat secret baru di provider masing-masing.
4. Update hanya sumber secret terpusat.
5. Restart layanan yang memakai secret tersebut.
6. Verifikasi runtime tanpa mencetak nilai secret.
7. Revoke secret lama setelah verifikasi sukses.
8. Catat tanggal rotasi, owner, dan alasan perubahan.

Prioritas rotasi sekarang:
1. Semua Groq/Gemini/OpenAI key yang pernah tersimpan literal di repo/helper script.
2. Telegram bot token yang pernah muncul literal di script test/archive.
3. Password PostgreSQL/RabbitMQ yang pernah menggunakan default atau fallback lemah.

## Checklist Verifikasi Runtime

Jalankan:

```bash
python3 scripts/runtime_secret_check.py
python3 scripts/runtime_secret_check.py telegram vane serena
```

Yang diverifikasi:
- `present: true/false`
- `length`

Yang tidak boleh dilakukan:
- `echo $SECRET`
- logging nilai header `Authorization`
- mencetak file `.env`
- screenshot panel secret manager

## Cleanup Manual Yang Masih Disarankan

- Hapus atau arsipkan `.env` duplikat di `mcp-unified/integrations/telegram/.env` setelah isi dipindah ke sumber terpusat.
- Periksa `mcp-unified/.env.backup.20260303_140553`; bila berisi secret aktif, pindahkan ke storage aman atau hapus dengan prosedur yang disetujui.
- Audit `services/database/compose.yaml`, `services/database/engine.sh`, dan dokumen lama yang masih mencontohkan password statis.
- Review file archive lama yang mungkin masih membawa token historis.

## Prosedur Operasional Singkat

1. Simpan semua secret aktif di satu file aman di luar repo atau di root `.env`.
2. Export `MCP_SECRETS_FILE` jika ingin memakai file di luar repo.
3. Restart `mcp-unified`, Telegram bot, VANE, dan Serena.
4. Jalankan `python3 scripts/runtime_secret_check.py`.
5. Pastikan tidak ada file lokal lain yang masih menjadi sumber secret aktif.
