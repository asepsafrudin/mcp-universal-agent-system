# MCP Unified Agent System

Sistem MCP (Model Context Protocol) Universal yang menyediakan server terintegrasi dengan kemampuan long-term memory, sub-agent otonom, dan distributed execution.

## 🎯 Overview

Proyek ini adalah implementasi **MCP (Model Context Protocol)** yang menyediakan:

- **Universal MCP Server** dengan long-term memory berbasis PostgreSQL + pgvector
- **Autonomous Sub-Agent System** untuk dekomposisi dan eksekusi tugas kompleks
- **Distributed Execution** untuk skalasi horizontal
- **Self-Healing Capabilities** untuk recovery otomatis
- **Integration dengan Antigravity IDE** dan IDE lainnya

## 📁 Struktur Direktori

```
/home/aseps/MCP/
├── 📄 README.md                          # Dokumentasi ini
├── 📄 .gitignore                         # Git ignore rules
├── 📄 antigravity-mcp-config.json       # Konfigurasi untuk Antigravity IDE
│
├── 🔧 Scripts & Utilities
│   ├── init_session.sh                  # Global initializer untuk MCP session
│   ├── backup_system.sh                 # System backup script
│   ├── recover_system.sh                # Disaster recovery script
│   ├── monitor_production.sh            # Production monitoring
│   └── setup_distributed.sh             # Distributed setup script
│
├── 📚 Documentation (docs/)
│   ├── ARCHITECTURE.md                  # Overview arsitektur sistem
│   ├── system_flow.md                   # Alur kerja sistem
│   ├── ANTIGRAVITY_INTEGRATION.md       # Panduan integrasi Antigravity IDE
│   ├── Lan_based_distributed_MCP.md     # Distributed MCP over LAN
│   ├── lan_based_implement.md           # Implementasi LAN-based
│   ├── production_readines_check.md     # Production readiness checklist
│   ├── testing_guide.md                 # Panduan testing
│   ├── tinjauan_kritis.md               # Tinjauan kritis sistem
│   └── dissaster_recovery_plan.md       # Disaster recovery plan
│
├── 🖥️ MCP Unified Server (mcp-unified/)
│   │
│   ├── 🚀 Entry Points
│   │   ├── mcp_server.py               # Main MCP server (stdio protocol)
│   │   ├── run.sh                      # Startup script
│   │   ├── worker_node.py              # Distributed worker node
│   │   └── requirements.txt            # Python dependencies
│   │
│   ├── ⚙️ Core (core/)
│   │   ├── __init__.py
│   │   ├── config.py                   # Configuration settings (Pydantic)
│   │   ├── server.py                   # Server core logic
│   │   ├── circuit_breaker.py          # Circuit breaker pattern
│   │   └── rate_limiter.py             # Rate limiting
│   │
│   ├── 🛠️ Execution (execution/)
│   │   ├── __init__.py
│   │   ├── registry.py                 # Tool registry & discovery
│   │   ├── workspace.py                # Workspace management
│   │   ├── mcp_proxy.py                # MCP proxy for remote tools
│   │   └── tools/
│   │       ├── file_tools.py           # File operations (list_dir, read_file, write_file)
│   │       └── shell_tools.py          # Shell operations (run_shell)
│   │
│   ├── 🧠 Intelligence (intelligence/)
│   │   ├── __init__.py
│   │   ├── planner.py                  # Task planning engine
│   │   └── self_healing.py             # Self-healing & recovery
│   │
│   ├── 💾 Memory (memory/)
│   │   ├── __init__.py
│   │   ├── longterm.py                 # Long-term memory (PostgreSQL + pgvector)
│   │   ├── working.py                  # Working memory
│   │   └── token_manager.py            # Token management
│   │
│   ├── 📨 Messaging (messaging/)
│   │   └── queue_client.py             # Distributed queue client
│   │
│   ├── 📊 Observability (observability/)
│   │   ├── __init__.py
│   │   ├── logger.py                   # Structured logging
│   │   └── metrics.py                  # Metrics collection
│   │
│   ├── 🔬 Simulation (simulation/)
│   │   ├── greyware_op/                # Greyware operations simulation
│   │   │   ├── ai_nmap.py              # AI-powered network scanner
│   │   │   ├── network_scanner.py      # Network scanning tools
│   │   │   ├── c2_bot.js               # C2 bot implementation
│   │   │   ├── config.json             # Configuration
│   │   │   ├── duckyscript.txt         # Ducky script payloads
│   │   │   ├── README.md               # Documentation
│   │   │   └── *.ps1                   # PowerShell deployment scripts
│   │   └── meshcentral_server/         # MeshCentral server
│   │       ├── package.json
│   │       ├── meshcentral-data/       # Server data & certificates
│   │       ├── meshcentral-files/      # File storage
│   │       └── meshcentral-backups/    # Auto-backups
│   │
│   └── 🧪 Tests (tests/)
│       ├── test_capabilities.py        # Capability tests
│       ├── test_self_healing.py        # Self-healing tests
│       ├── test_tokens.py              # Token management tests
│       └── verify_ltm_integration.py   # LTM integration verification
│
├── 📊 Logs (logs/)
│   └── [log files]
│
├── 💿 Data (mcp-data/)
│   └── [persistent data]
│
└── 🗂️ Workspace (workspace/)
    └── [transient outputs & temp files]
```

## 🔄 Workflow Sistem

### 1. High-Level Interaction Flow

```
┌─────────┐     ┌─────────────┐     ┌─────────────────┐
│  User   │────▶│ Agent/IDE   │────▶│  MCP Server     │
└─────────┘     └─────────────┘     └─────────────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
           ┌─────────────────┐   ┌─────────────────────┐   ┌─────────────────┐
           │  Memory Server  │   │  Sub-Agent System   │   │  Remote Tools   │
           │  (PostgreSQL)   │   │  (Autonomous)       │   │  (External MCP) │
           └─────────────────┘   └─────────────────────┘   └─────────────────┘
```

### 2. Autonomous Task Execution Flow

```
User Request
     │
     ▼
┌─────────────────┐
│  Planning Engine │  ← Analyze & Decompose task
└─────────────────┘
     │
     ▼
┌─────────────────┐
│    Scheduler    │  ← Queue & Route tasks
└─────────────────┘
     │
     ▼
┌─────────────────┐
│Specialized Agent│  ← Execute (File/Shell/Code Agent)
└─────────────────┘
     │
     ▼
┌─────────────────┐
│  Memory Server  │  ← Read/Write Context
└─────────────────┘
     │
     ▼
Result/Output
```

### 3. Memory Workflow (LTM)

```
Input Data (Chat/Code/Docs)
     │
     ▼
┌─────────────┐
│  Chunking   │  ← Split into logical segments
└─────────────┘
     │
     ▼
┌─────────────┐
│  Embedding  │  ← Convert to vector representation
└─────────────┘
     │
     ▼
┌─────────────┐     ┌──────────────────┐
│   Storage   │────▶│  PostgreSQL      │
└─────────────┘     │  (pgvector)      │
                    └──────────────────┘
                            │
                    ┌───────┴───────┐
                    ▼               ▼
            ┌──────────┐     ┌──────────┐
            │  Search  │     │  Recall  │
            │  (Query) │     │ (Context)│
            └──────────┘     └──────────┘
```

### 4. Self-Healing Loop

```
Task Execution
     │
     ▼
┌─────────────────┐     No    ┌─────────────────┐
│   Success?      │──────────▶│   Error Analysis │
└─────────────────┘           └─────────────────┘
     │                                │
    Yes                              ▼
     │                       ┌─────────────────┐
     │                       │  Recovery Plan  │
     │                       └─────────────────┘
     │                                │
     │                                ▼
     │                       ┌─────────────────┐
     │                       │  Retry/Correct  │
     │                       └─────────────────┘
     │                                │
     └────────────────────────────────┘
```

## 🛠️ Tools yang Tersedia

### File Operations
| Tool | Deskripsi |
|------|-----------|
| `list_dir` | List isi direktori |
| `read_file` | Baca isi file |
| `write_file` | Tulis/buat file baru |

### Memory Operations (Long-term Memory)
| Tool | Deskripsi |
|------|-----------|
| `memory_save` | Simpan informasi ke PostgreSQL dengan vector embeddings |
| `memory_search` | Cari dengan hybrid search (semantic + keyword) |
| `memory_list` | List semua memories dengan pagination |
| `memory_delete` | Hapus memory berdasarkan ID atau key |

### Shell Operations
| Tool | Deskripsi |
|------|-----------|
| `run_shell` | Execute safe shell commands (ls, pwd, git, dll) |

### Intelligence Operations
| Tool | Deskripsi |
|------|-----------|
| `create_plan` | Buat rencana eksekusi untuk tugas kompleks |
| `save_plan_experience` | Simpan pengalaman eksekusi untuk learning |
| `execute_task` | Eksekusi tugas tingkat tinggi secara otonom |

### Workspace Operations
| Tool | Deskripsi |
|------|-----------|
| `create_workspace` | Buat workspace baru untuk project |
| `cleanup_workspace` | Bersihkan workspace |

### Distributed Operations
| Tool | Deskripsi |
|------|-----------|
| `publish_remote_task` | Publish task ke distributed queue |

## 🚀 Cara Menggunakan

### 1. Prerequisites

```bash
# Pastikan PostgreSQL dengan pgvector berjalan
# Ganti placeholder values dengan credentials Anda
docker run -d --name mcp-pg \
  -e POSTGRES_DB=mcp \
  -e POSTGRES_USER=$POSTGRES_USER \
  -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
  -v ~/mcp-data/pg:/var/lib/postgresql/data \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### 2. Inisialisasi Session

```bash
# Jalankan dari project manapun
source /home/aseps/MCP/init_session.sh
```

### 3. Menjalankan MCP Server

```bash
cd /home/aseps/MCP/mcp-unified
bash run.sh
```

### 4. Testing

```bash
# Test capabilities
python3 tests/test_capabilities.py

# Test self-healing
python3 tests/test_self_healing.py

# Verify LTM integration
python3 tests/verify_ltm_integration.py
```

## ⚙️ Konfigurasi

### Environment Variables

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `POSTGRES_USER` | aseps | Database username |
| `POSTGRES_PASSWORD` | secure123 | Database password |
| `POSTGRES_SERVER` | localhost | Database host |
| `POSTGRES_DB` | mcp | Database name |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection URL |
| `LOG_LEVEL` | INFO | Logging level |
| `PYTHONPATH` | - | Python path untuk imports |

### Konfigurasi File

- **`mcp-unified/core/config.py`** - Konfigurasi aplikasi utama
- **`antigravity-mcp-config.json`** - Konfigurasi untuk Antigravity IDE
- **`mcp-unified/test_config.json`** - Konfigurasi untuk testing

## 🏗️ Arsitektur Komponen

### Core Layer
- **Config**: Pydantic-based configuration management
- **Circuit Breaker**: Fault tolerance pattern
- **Rate Limiter**: Request throttling

### Execution Layer
- **Registry**: Tool registration dan discovery
- **MCP Proxy**: Bridge ke external MCP servers
- **Tools**: File, shell, dan utility operations

### Intelligence Layer
- **Planner**: Task decomposition dan planning
- **Self-Healing**: Automatic error recovery

### Memory Layer
- **Long-term**: PostgreSQL + pgvector untuk persistent storage
- **Working**: Short-term context management
- **Token Manager**: Token usage optimization

### Observability Layer
- **Logger**: Structured JSON logging
- **Metrics**: Performance metrics collection

## 🔒 Security Notes

- **Shell Command Safety**: Tool `run_shell` hanya mengizinkan safe commands
- **Database Credentials**: Simpan di environment variables, jangan commit ke repo
- **Certificates**: SSL certificates disimpan di `meshcentral-data/`

## 📊 Monitoring & Maintenance

### Check Database Status
```bash
docker exec mcp-pg psql -U aseps -d mcp -c "SELECT COUNT(*) FROM memories;"
```

### Backup System
```bash
bash backup_system.sh
```

### Monitor Production
```bash
bash monitor_production.sh
```

### Cleanup Old Memories
```bash
# Via API call atau langsung ke database
curl -X POST http://localhost:8000/ -d '{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {"name": "memory_list", "arguments": {"limit": 50}},
  "id": 1
}'
```

## 🔗 Integrasi

### Antigravity IDE
Lihat [ANTIGRAVITY_INTEGRATION.md](docs/ANTIGRAVITY_INTEGRATION.md) untuk panduan lengkap.

### Distributed MCP
Lihat [Lan_based_distributed_MCP.md](docs/Lan_based_distributed_MCP.md) untuk setup distributed.

## 🧪 Testing

```bash
# Unit tests
cd mcp-unified
python3 -m pytest tests/

# Integration tests
python3 tests/verify_ltm_integration.py

# E2E tests
python3 tests/test_capabilities.py
```

## 📚 Referensi

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)

## 📝 License

[License Information]

## 👥 Contributors

- [Author Name] - Initial development

---

*Dokumentasi ini di-generate secara otomatis dan selalu sinkron dengan struktur project terkini.*
