# 🤖 Telegram Bot Integration

Integrasi lengkap Telegram Bot dengan MCP Server untuk komunikasi two-way antara user Telegram dan AI.

## 📋 Overview

Integrasi ini menyediakan dua komponen utama:

1. **Telegram Bot Server** - Menerima pesan dari Telegram dan meneruskannya ke MCP
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
│       ├── bot_server.py       # Main bot server
│       ├── setup.py            # Setup script
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

### 1. Setup Bot

```bash
cd mcp-unified/integrations/telegram
python setup.py
```

### 2. Konfigurasi Token

Edit `.env` file:
```bash
nano .env
```

Isi dengan:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_MODE=polling
```

### 3. Jalankan Bot

```bash
./run.sh
```

### 4. Test

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

Tambahkan di `.env`:
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

## 🔮 Integrasi dengan AI (Future)

Untuk integrasi penuh dengan AI, modifikasi `process_message()` di `bot_server.py`:

```python
async def process_message(self, user_id: int, message: str) -> str:
    # Kirim ke MCP AI untuk diproses
    task = Task(
        type="chat_completion",
        payload={
            "message": message,
            "user_id": user_id,
            "context": self.user_sessions[user_id].get("context", [])
        }
    )
    
    # Proses melalui AI
    result = await self.mcp_client.process_task(task)
    return result.content
```

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
