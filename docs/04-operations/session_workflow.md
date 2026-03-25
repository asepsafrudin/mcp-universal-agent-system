# Session Workflow — Cara Kerja dengan MCP Hub

## Memulai Sesi Baru (< 30 detik)

### Step 1: Pastikan hub aktif
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

Jika tidak respond:
```bash
cd /home/aseps/MCP/mcp-unified && python3 mcp_server_sse.py &
```

### Step 2: Load context
```bash
cd /your/project/folder
python3 /home/aseps/MCP/shared/generate_context_brief.py
```

Output berisi semua yang perlu diketahui agent tentang project ini.
Paste ke agent atau biarkan `.agent` yang load otomatis.

### Step 3: Mulai kerja
Agent sudah tahu konteks. Langsung produktif.

---

## Mengakhiri Sesi (< 1 menit)

Simpan progress sebelum tutup:

```python
from shared.mcp_client import MCPClient
from shared.context_injector import ContextInjector

client = MCPClient()
injector = ContextInjector(client)

# Simpan ringkasan sesi
await injector.save_session_summary(
    "Implementasi SSE server selesai. Database constraint fix pending restart.",
    tags=["infrastructure", "mcp-server"]
)

# Simpan task yang masih aktif
await injector.save_active_task(
    "database_restart",
    "Restart SSE server untuk apply schema fix dari TASK-008-A",
    status="pending"
)
```

---

## Menyimpan Keputusan Penting

```python
await injector.save_decision(
    "use_sse_not_stdio",
    "MCP server menggunakan SSE transport untuk persistent connection",
    rationale="Memungkinkan multiple clients dari editor berbeda tanpa restart"
)
```

---

## Tips

- **Namespace** = nama project/folder. Semua memory ter-isolasi per namespace.
- **Satu hub, banyak project** — tidak perlu setup berbeda per project.
- **Save di akhir sesi** — brief sesi berikutnya akan jauh lebih informatif.
- **Git repo name** lebih stabil dari folder name sebagai namespace.
