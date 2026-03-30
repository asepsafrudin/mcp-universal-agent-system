# MCP Unified Agent System

Sistem MCP (Model Context Protocol) Universal yang menyediakan server terintegrasi dengan kemampuan long-term memory, sub-agent otonom, distributed execution, dan specialized agents untuk berbagai domain.

## 🎯 Overview

Proyek ini adalah implementasi **MCP (Model Context Protocol)** yang menyediakan:

- **Universal MCP Server** dengan long-term memory berbasis PostgreSQL + pgvector
- **Autonomous Sub-Agent System** untuk dekomposisi dan eksekusi tugas kompleks
- **Specialized Agents** (Legal, Research, Office, Admin, Code, Filesystem) untuk domain spesifik
- **Knowledge Layer** dengan RAG (Retrieval-Augmented Generation) infrastructure
- **🆕 Vane AI Search** — SearxNG + Groq AI untuk riset web cerdas dengan sitasi otomatis
- **Distributed Execution** untuk skalasi horizontal
- **Self-Healing Capabilities** untuk recovery otomatis
- **Task Scheduler** untuk eksekusi tugas terjadwal
- **Integration dengan Antigravity IDE** dan IDE lainnya

## 📁 Struktur Direktori

/home/aseps/MCP/
├── 📂 mcp-unified/         # Universal MCP Server & Core Logic
├── 📂 serena/              # Serena Semantic Coding Agent Toolkit
├── 📂 data/                # Data storage (input, processed, mcp-data, dll)
├── 📂 config/              # Kredensial & Konfigurasi Eksternal
├── 📂 tasks/               # Manajemen Task (01-05 structure)
├── 📂 docs/                # Central Documentation & Proposals
├── 📂 scripts/             # Internal utilities (.sh, .py)
├── 📂 tests/               # Unit testing & Data Uji
└── 📂 archive/             # Backup file & log lama

## 🔍 Vane AI Search Integration

> **TASK-031** — Integrasi selesai pada 2026-03-11

Sistem riset AI berbasis **SearxNG + Groq** yang terintegrasi ke dalam MCP Unified untuk kemampuan web research cerdas dengan sitasi otomatis.

### Arsitektur

```
Query Riset
    │
    ▼
┌─────────────────┐
│  ResearchAgent  │  ← Menerima task riset dari Orchestrator
│  (upgraded v2)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  VaneConnector  │  ← mcp-unified/integrations/vane_connector.py
│  (primary)      │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
┌───────┐  ┌──────────────────────┐
│SearxNG│  │   Groq API           │
│:8090  │  │   qwen/qwen3-32b     │
│(~5s)  │  │   (~10s)             │
└───┬───┘  └──────────┬───────────┘
    │                 │
    └────────┬────────┘
             ▼
    Jawaban + Sitasi
    (~15s total)
```

### Tools yang Tersedia

| Tool | Deskripsi | Use Case |
|------|-----------|----------|
| `vane_search(query)` | Pencarian web umum + AI synthesis | Research umum |
| `vane_legal_search(query, regulation)` | Riset hukum Indonesia | Analisis UU/PP |
| `vane_deep_research(query, sub_queries)` | Multi-query deep research | Laporan komprehensif |
| `vane_gap_fill(sub_urusan, bidang)` | Isi gap data UU 23/2014 | Inventory PUU |

### Cara Penggunaan

```python
# Import langsung
from mcp_unified.tools.research_tools import vane_search, vane_legal_search

# Pencarian cepat
result = await vane_search("SPM bidang kesehatan")
print(result["answer"])  # Jawaban dengan sitasi

# Riset hukum
result = await vane_legal_search(
    "pembagian kewenangan urusan pendidikan",
    regulation="UU 23/2014"
)
```

### Konfigurasi & Prasyarat

```bash
# 1. Pastikan Vane Docker berjalan
docker run -d -p 3000:3000 -p 8090:8080 \
  -e GROQ_API_KEY=<key> \
  -v vane-data:/home/vane/data \
  --name vane itzcrazykns1337/vane:latest

# 2. Set environment variables (atau buat .env)
export GROQ_API_KEY=gsk_xxx
export GROQ_MODEL=qwen/qwen3-32b
export SEARXNG_URL=http://localhost:8090

# 3. Test connector
python3 mcp-unified/integrations/vane_connector.py "query riset"
```

> ⚠️ **Catatan:** Vane `/api/search` (port 3000) TIDAK digunakan karena lambat (timeout >90s akibat full URL scraping). Connector langsung ke SearxNG port 8090 + Groq API.

## 🔐 Secret Management

Workspace ini sekarang diarahkan ke **single source of truth** untuk secret:
- Utama: `/home/aseps/MCP/.env`
- Alternatif lebih aman: file di luar repo melalui `MCP_SECRETS_FILE`

Verifikasi tanpa mengekspos nilai secret:

```bash
python3 scripts/centralize_secrets_audit.py
python3 scripts/runtime_secret_check.py
```

Praktik yang direkomendasikan:
- Jangan duplikasi secret yang sama di `mcp-unified/.env` dan `mcp-unified/integrations/telegram/.env`
- Gunakan satu key per tool/environment bila memungkinkan
- Rotasi manual untuk key yang pernah tersimpan literal di repo atau helper script

---

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

### 2. Knowledge Layer Architecture (RAG)

```
User Query
     │
     ▼
┌─────────────────┐
│ AgentKnowledge  │  ← Unified interface untuk knowledge
│     Bridge      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌──────────┐
│ File  │ │ Database │  ← Multiple knowledge sources
│  KB   │ │    KB    │
└───┬───┘ └────┬─────┘
    │          │
    └────┬─────┘
         ▼
┌─────────────────┐
│   RAG Engine    │  ← Retrieval-Augmented Generation
├─────────────────┤
│ • query()       │
│ • add_document  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PGVectorStore  │  ← PostgreSQL + pgvector
│  (PostgreSQL)   │
└─────────────────┘
```

### 3. Autonomous Task Execution Flow

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
│Specialized Agent│  ← Execute (File/Shell/Code/Legal/Research Agent)
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

### 4. Memory Workflow (LTM)

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

### 5. Self-Healing Loop

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

### Knowledge Operations (RAG)
| Tool | Deskripsi |
|------|-----------|
| `knowledge_query` | Query knowledge base dengan semantic search |
| `knowledge_add` | Tambah dokumen ke knowledge base |
| `knowledge_get_context` | Dapatkan context untuk LLM prompt |
| `knowledge_delete` | Hapus dokumen dari knowledge base |

### Shell Operations
| Tool | Deskripsi |
|------|-----------|
| `run_shell` | Execute safe shell commands (ls, pwd, git, dll) |

### Semantic Code & Editing (Serena)
| Tool | Deskripsi |
|------|-----------|
| `find_symbol` | Temukan lokasi presisi sebuah fungsi/kelas secara semantik |
| `find_referencing_symbols` | Cari seluruh pemanggil/referensi fungsi dalam project |
| `insert_after_symbol` | Sisipkan kode baru tepat di bawah struktur simbol |
| `replace_symbol` | Ganti langsung blok simbol tanpa modifikasi manual full-file |

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

### Office Document Operations
| Tool | Deskripsi |
|------|-----------|
| `docx_read` | Baca dokumen Word |
| `docx_write` | Tulis/buat dokumen Word |
| `docx_append` | Tambahkan konten ke dokumen Word |
| `xlsx_read` | Baca file Excel |
| `xlsx_write` | Tulis/buat file Excel |
| `xlsx_append` | Tambahkan data ke Excel |

### Legal Operations
| Tool | Deskripsi |
|------|-----------|
| `legal_analyze_document` | Analisis dokumen hukum |
| `legal_search_uu` | Cari dalam UU 23/2014 |
| `legal_process_spm` | Proses Standar Pelayanan Minimal |
| `legal_generate_report` | Generate laporan legal |

## 🤖 Specialized Agents

### 1. Legal Agent
Agent khusus untuk domain hukum dengan kemampuan:
- **Document Analysis**: Analisis dokumen hukum (UU, Perpres, Permendagri)
- **Knowledge Base Integration**: Integrasi dengan UU 23/2014 dan regulasi terkait
- **SPM Processing**: Pemrosesan Standar Pelayanan Minimal
- **Report Generation**: Generate laporan legal otomatis
- **Knowledge Bridge**: Koneksi ke database knowledge dengan RAG

**Lokasi**: `mcp-unified/agents/profiles/legal/`

### 2. Research Agent
Agent untuk riset dan pengumpulan data:
- **Web Scraping**: Scraping dari JDIH, Peraturan.go.id
- **Document Collection**: Koleksi dokumen perundang-undangan
- **Data Extraction**: Ekstraksi data terstruktur

**Lokasi**: `mcp-unified/agents/profiles/research/`

### 3. Code Agent
Agent untuk pengembangan kode:
- **Code Analysis**: Analisis dan review kode
- **Code Generation**: Generate kode dari spesifikasi
- **Refactoring**: Refactor kode existing

**Lokasi**: `mcp-unified/agents/profiles/code_agent.py`

### 4. Admin Agent
Agent untuk administrasi sistem:
- **System Monitoring**: Monitoring sistem
- **User Management**: Manajemen pengguna
- **Configuration**: Konfigurasi sistem

**Lokasi**: `mcp-unified/agents/profiles/admin_agent.py`

### 5. Filesystem Agent
Agent untuk operasi filesystem:
- **File Operations**: Operasi file dan direktori
- **Search**: Pencarian file
- **Organization**: Organisasi file

**Lokasi**: `mcp-unified/agents/profiles/filesystem_agent.py`

### 6. Office Admin Agent
Agent untuk administrasi office:
- **Document Processing**: Pemrosesan dokumen office
- **Report Generation**: Generate laporan
- **Data Management**: Manajemen data

**Lokasi**: `mcp-unified/agents/profiles/office_admin_agent.py`

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

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env dengan credentials Anda
nano .env
```

### 3. Inisialisasi Session

```bash
# Jalankan dari project manapun
source /home/aseps/MCP/init_session.sh
```

### 4. Menjalankan MCP Server

```bash
cd /home/aseps/MCP/mcp-unified
bash run.sh
```

### 5. Enable Scheduler (Optional)

```bash
# Enable systemd scheduler
sudo bash mcp-unified/scheduler/enable_scheduler.sh

# Atau enable legal agent scheduler
sudo bash mcp-unified/scheduler/enable_legal_agent_scheduler.sh
```

## ⚙️ Konfigurasi

### Environment Variables

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `POSTGRES_USER` | aseps | Database username |
| `POSTGRES_PASSWORD` | - | Database password |
| `POSTGRES_SERVER` | localhost | Database host |
| `POSTGRES_DB` | mcp | Database name |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection URL |
| `LOG_LEVEL` | INFO | Logging level |
| `TELEGRAM_BOT_TOKEN` | - | Telegram bot token |
| `TELEGRAM_CHAT_ID` | - | Telegram chat ID |

### Knowledge Layer Configuration

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `EMBEDDING_MODEL` | nomic-embed-text | Model embedding |
| `EMBEDDING_DIMENSION` | 768 | Dimensi embedding |
| `OLLAMA_URL` | http://localhost:11434 | Ollama endpoint |
| `RAG_TOP_K` | 5 | Jumlah hasil retrieval |
| `RAG_SIMILARITY_THRESHOLD` | 0.7 | Threshold similarity |
| `RAG_NAMESPACE` | default | Default namespace |

### Konfigurasi File

- **`mcp-unified/core/config.py`** - Konfigurasi aplikasi utama
- **`mcp-unified/knowledge/config.py`** - Konfigurasi knowledge layer
- **`antigravity-mcp-config.json`** - Konfigurasi untuk Antigravity IDE
- **`.env`** - Environment variables (jangan commit ke repo)

## 🏗️ Arsitektur Komponen

### Core Layer
- **Config**: Pydantic-based configuration management
- **Circuit Breaker**: Fault tolerance pattern
- **Rate Limiter**: Request throttling

### Execution Layer
- **Registry**: Tool registration dan discovery
- **MCP Proxy**: Bridge ke external MCP servers
- **Tools**: File, shell, office, dan utility operations

### Intelligence Layer
- **Planner**: Task decomposition dan planning
- **Self-Healing**: Automatic error recovery

### Knowledge Layer 🆕
- **RAG Engine**: Retrieval-Augmented Generation
- **Vector Store**: PostgreSQL + pgvector storage
- **Embedding Service**: Ollama-based embeddings
- **Document Loaders**: PDF, DOCX, Web loaders
- **Knowledge Bridge**: Unified interface untuk multiple sources

### Memory Layer
- **Long-term**: PostgreSQL + pgvector untuk persistent storage
- **Working**: Short-term context management
- **Token Manager**: Token usage optimization

### Agent Layer
- **Legal Agent**: Domain-specific agent untuk hukum
- **Research Agent**: Agent untuk riset dan data collection
- **Code Agent**: Agent untuk pengembangan kode
- **Admin Agent**: Agent untuk administrasi sistem
- **Inter-Agent Communication**: Komunikasi antar agent

### Observability Layer
- **Logger**: Structured JSON logging
- **Metrics**: Performance metrics collection

## 📋 Task Management

Sistem menggunakan folder-based task management:

- **`tasks/active/`** - Tugas yang sedang aktif dikerjakan
- **`tasks/completed/`** - Tugas yang sudah selesai
- **`tasks/status/`** - Status dan progress report

Format penamaan task: `TASK-XXX-nama-tugas.md`

## 🏛️ Bangda_PUU - Sistem Peraturan Perundang-undangan

Modul khusus untuk pengelolaan Peraturan Perundang-undangan:

- **UU 23/2014 Implementation**: Implementasi UU 23/2014 tentang Pemerintahan Daerah
- **Document Processing**: Processing dokumen lampiran dan regulasi
- **SPM Analysis**: Analisis Standar Pelayanan Minimal
- **Report Generation**: Generate laporan komprehensif

**Lokasi**: `Bangda_PUU/`

## ☁️ OneDrive Integration

Integrasi dengan OneDrive untuk sinkronisasi dokumen PUU:

```bash
# Process OneDrive PUU
cd OneDrive_PUU
python3 process_onedrive_puu_2026.py
```

## 🔒 Security Notes

- **Shell Command Safety**: Tool `run_shell` hanya mengizinkan safe commands
- **Database Credentials**: Simpan di `.env`, jangan commit ke repo
- **API Keys**: Gunakan environment variables
- **Certificates**: SSL certificates disimpan di `meshcentral-data/`
- **Auth Middleware**: bcrypt + JWT authentication
- **Audit Logging**: Event tracking untuk compliance

## 📊 Monitoring & Maintenance

### Check Database Status
```bash
docker exec mcp-pg psql -U aseps -d mcp -c "SELECT COUNT(*) FROM memories;"
```

### Check Scheduler Status
```bash
sudo systemctl status mcp-scheduler.timer
sudo systemctl status legal-agent-scheduler.timer
```

### Backup System
```bash
bash backup_system.sh
```

### Monitor Production
```bash
bash monitor_production.sh
```

### View Logs
```bash
# Scheduler logs
sudo journalctl -u mcp-scheduler -f

# Legal agent logs
sudo journalctl -u legal-agent-scheduler -f
```

## 🔗 Integrasi

### Antigravity IDE
Lihat `docs/05-integrations/` untuk panduan lengkap.

### Distributed MCP
Lihat `docs/02-architecture/` untuk setup distributed.

### Knowledge Database
Lihat `mcp-unified/docs/agent-knowledge-integration.md` untuk panduan integrasi knowledge database.

### Telegram Notifications
```bash
# Test Telegram notification
python3 test_telegram_notification.py
```

## 🧪 Testing

```bash
# Unit tests
cd mcp-unified
python3 -m pytest tests/

# Integration tests
python3 tests/verify_ltm_integration.py

# E2E tests
python3 tests/test_capabilities.py

# Office tools tests
python3 mcp-unified/tools/office/test_office_tools.py

# Knowledge connection test
python3 mcp-unified/scripts/test_knowledge_connection.py

# Benchmark tests
./run_benchmark.sh          # Quick baseline
./run_scaling_test.sh       # Worker optimization
./run_soak_test.sh          # Memory leak detection
```

## 📚 Referensi

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [UU 23/2014 - Pemerintahan Daerah](https://peraturan.bpk.go.id/Details/51828/uu-no-23-tahun-2014)

## 🗂️ Dokumentasi Tambahan

File-file dokumentasi teknis telah dipindahkan ke `archive/` untuk menjaga root directory tetap bersih:

| Dokumen | Lokasi Baru |
|---------|-------------|
| NEXT_STEPS.md | `archive/docs/` |
| AGENT_KNOWLEDGE_INTEGRATION_SUMMARY.md | `archive/docs/` |
| EXTRACTOR_SYSTEM_PROGRESS.md | `archive/docs/` |
| PRODUCTION_DEPLOYMENT_GUIDE.md | `archive/docs/` |
| Task Completion Summaries | `archive/docs/` |
| Test Reports (JSON) | `archive/reports/` |
| Utility Scripts | `archive/scripts/` |
| Log Files | `archive/temp/` |

## 📝 License

[License Information]

## 👥 Contributors

- [Author Name] - Initial development

---

*Dokumentasi ini di-update terakhir: Maret 2026*  
*Task aktif: lihat `tasks/active/`*  
*Task selesai: lihat `tasks/archive/`*  
*Status task: lihat `tasks/status/`*
