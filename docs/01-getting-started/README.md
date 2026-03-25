# 01-getting-started — Memulai dengan MCP Unified

Folder ini berisi semua yang perlu Anda ketahui untuk memulai dengan MCP Unified Server.

## 📋 Konten

| File | Deskripsi |
|------|-----------|
| [`quickstart.md`](./quickstart.md) | Quick start guide untuk menjalankan server |
| [`session-brief.md`](./session-brief.md) | Konteks session dan status pengembangan |

## 🚀 Quick Start

```bash
# 1. Clone/setup
cd /home/aseps/MCP

# 2. Environment setup
cp .env.example .env
# Edit .env dengan konfigurasi Anda

# 3. Start dependencies
docker-compose up -d postgres redis

# 4. Run server
cd mcp-unified && ./run.sh

# 5. Verify
curl http://localhost:8000/health
```

## 🎯 Status Session

**Siapa**: Developer membangun Personal MCP Hub  
**Status**: Sudah melalui full review cycle (TASK-001 s/d TASK-011)  
**Fase Sekarang**: Merancang mekanisme **Discovery & Portability**  

📄 Detail: [`session-brief.md`](./session-brief.md)

## 📖 Next Steps

1. **Memahami Arsitektur** → [`02-architecture/`](../02-architecture/)
2. **Development Guide** → [`03-development/`](../03-development/)
3. **Operasional** → [`04-operations/`](../04-operations/)
