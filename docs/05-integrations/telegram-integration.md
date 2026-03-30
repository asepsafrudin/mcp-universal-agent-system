# 🤖 Telegram Bot Integration

Integrasi Telegram Bot untuk komunikasi two-way antara user Telegram dan AI.

Catatan arsitektur terbaru:
- Bot chat Telegram utama sekarang berjalan lewat `run.py` dan `bot.py`.
- Konteks percakapan bot Telegram dipisahkan dari memory agent/LTM/knowledge.
- Bridge agent dan SQL bot diperlakukan sebagai jalur terpisah, bukan konteks default chat.
- Entry point legacy diarsipkan ke folder `integrations/telegram/legacy/`.

## 📋 Overview

Integrasi ini menyediakan dua komponen utama:

1. **Telegram Bot** - Menerima pesan dari Telegram dan memproses chat operasional
2. **Telegram Tool** - Mengirim notifikasi dan pesan dari MCP ke Telegram

## 🏗️ Arsitektur

```
┌─────────────┐     HTTP/Webhook    ┌─────────────────┐
│   Telegram  │◄───────────────────►│  Telegram Bot   │
│    User     │                     │    Server       │
└─────────────┘                     └────────┬────────┘
                                            │
                                       MCP Protocol
                                            │
                                            ▼
                                     ┌─────────────┐
                                     │    MCP      │
                                     │   Server    │
                                     │   (AI/LLM)  │
                                     └─────────────┘
                                            │
                                            │ Telegram Tool
                                            ▼
                                     ┌─────────────┐
                                     │  Telegram   │
                                     │     API     │
                                     └─────────────┘
```

## 📁 Lokasi File

```
mcp-unified/
├── integrations/
│   └── telegram/
│       ├── bot.py              # Main Telegram bot class
│       ├── run.py              # Entry point bot utama
│       ├── run.sh              # Runner script
│       ├── .env.example        # Config template
│       └── README.md           # Documentation
│
└── tools/
    └── integrations/
        └── telegram/
            ├── telegram_tool.py    # MCP Tool
            └── __init__.py
```

## 🚀 Quick Start

### 1. Konfigurasi Token

Edit secret source terpusat:
```bash
cd /home/aseps/MCP
nano .env
```

Isi dengan:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_MODE=polling
```

Rekomendasi:
- Gunakan root `.env` sebagai source of truth tunggal.
- Alternatif yang lebih aman: simpan file di luar repo lalu set `MCP_SECRETS_FILE=/absolute/path/to/secrets.env`.
- Hindari menduplikasi secret yang sama di `mcp-unified/.env` dan `integrations/telegram/.env`.

### 2. Jalankan Bot

```bash
./run.sh
```

### 3. Test

1. Buka bot Anda di Telegram
2. Kirim `/start`
3. Test pengiriman pesan

## 🔧 Konfigurasi

### Environment Variables

| Variable | Required | Default | Deskripsi |
|----------|----------|---------|-----------|
| `TELEGRAM_BOT_TOKEN` | ✅ | - | Token dari @BotFather |
| `TELEGRAM_ALLOWED_USERS` | ❌ | - | User ID whitelist |
| `TELEGRAM_MODE` | ❌ | `polling` | `polling` atau `webhook` |
| `TELEGRAM_WEBHOOK_URL` | ⚠️ | - | URL untuk webhook |
| `MCP_SERVER_URL` | ❌ | `localhost:8000` | URL MCP server |

### Mode Operasi

**Polling Mode** (Development):
- Bot polling API setiap detik
- Tidak butuh public URL
- Default untuk local development

**Webhook Mode** (Production):
- Real-time updates
- Butuh HTTPS public endpoint
- Lebih efisien untuk production

## 💻 Penggunaan

### Dari Telegram

User dapat mengirim:
- **Teks** → Diproses oleh AI
- **Gambar** → Dianalisis dengan Vision Tool
- **Dokumen** → Diproses sesuai tipe

### Dari MCP (Telegram Tool)

```python
from tools.integrations.telegram import telegram_tool

# Kirim pesan
await telegram_tool.send_message(
    chat_id="123456789",
    message="Hello from MCP!"
)

# Kirim dengan format HTML
await telegram_tool.send_message(
    chat_id="@channel",
    message="<b>Bold</b> and <i>italic</i>",
    parse_mode="HTML"
)

# Kirim foto
await telegram_tool.send_photo(
    chat_id="123456789",
    photo_path="/path/to/image.png",
    caption="Screenshot"
)
```

### Via Task System

```python
from core.task import Task

task = Task(
    type="telegram",
    payload={
        "action": "send_message",
        "chat_id": "123456789",
        "message": "Task completed!",
        "parse_mode": "Markdown"
    }
)

result = await telegram_tool.execute(task)
```

## 📱 Bot Commands

| Command | Fungsi |
|---------|--------|
| `/start` | Mulai percakapan |
| `/help` | Panduan penggunaan |
| `/status` | Cek status server |
| `/reset` | Reset sesi |

## 🔒 Keamanan

### User Whitelist

Tambahkan di secret source terpusat:
```env
TELEGRAM_ALLOWED_USERS=123456789,987654321
```

Hanya user dengan ID tersebut yang bisa akses bot.

### Mendapatkan User ID

1. Buka [@userinfobot](https://t.me/userinfobot)
2. Kirim pesan apa saja
3. Bot akan reply dengan ID Anda

## 🐛 Troubleshooting

### Bot tidak merespon

```bash
# Cek log
cd mcp-unified/integrations/telegram
tail -f telegram_bot.log

# Cek proses
ps aux | grep bot_server

# Restart
kill $(cat telegram_bot.pid)
./run.sh
```

### Error Module Not Found

```bash
pip install python-telegram-bot aiohttp
```

### Invalid Token

Test token:
```bash
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

### Audit Migrasi Ke Secret Tunggal

```bash
python3 scripts/centralize_secrets_audit.py
python3 scripts/runtime_secret_check.py telegram
```

## 🔮 Catatan Integrasi AI

Bot chat utama sekarang sengaja dibuat tipis:
- chat Telegram memakai konteks lokal bot
- bridge agent tetap eksplisit
- SQL/knowledge bot dipisahkan ke service terdedikasi bila dibutuhkan

## 📚 Referensi

- [python-telegram-bot](https://docs.python-telegram-bot.org/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [@BotFather](https://t.me/botfather)

## 📝 Changelog

### v1.0.0
- ✅ Bot Server dengan polling mode
- ✅ Telegram Tool untuk kirim pesan
- ✅ Support teks, gambar, dokumen
- ✅ User whitelist security
- ✅ Webhook mode support
