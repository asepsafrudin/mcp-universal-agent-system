# 02 - Architecture Overview

**Struktur Direktori & Layer Architecture**

---

## 1. New Directory Structure

```
mcp-server/
├── 📁 environment/          # Infrastructure layer
│   ├── workspace.py         # Isolated workspace manager
│   ├── config.py            # Centralized configuration
│   └── registry.py          # Base registry pattern
│
├── 📁 tools/                # Execution layer (WHAT to do)
│   ├── __init__.py
│   ├── registry.py          # ToolRegistry
│   ├── base.py              # BaseTool abstract class
│   ├── web/                 # Web Search/Browsing
│   │   ├── search.py
│   │   └── browse.py
│   ├── code/                # Code Execution
│   │   ├── interpreter.py
│   │   └── linter.py
│   ├── file/                # File Management
│   │   ├── read.py
│   │   ├── write.py
│   │   └── edit.py
│   ├── git/                 # GitHub/Repo Access
│   │   ├── clone.py
│   │   └── pr.py
│   ├── database/            # Database Query
│   │   ├── sql.py
│   │   └── supabase.py
│   ├── integration/         # Email/Calendar/SaaS
│   │   ├── email.py
│   │   ├── calendar.py
│   │   └── stripe.py
│   ├── browser/             # Browser Automation
│   │   └── automate.py
│   ├── document/            # Document Processing
│   │   ├── pdf.py
│   │   └── ocr.py
│   ├── media/               # Image/Media
│   │   ├── vision.py
│   │   └── generate.py
│   └── admin/               # Office Admin Tools
│       ├── spreadsheet_parser.py
│       ├── disposisi_generator.py
│       └── notification_sender.py
│
├── 📁 skills/               # Intelligence layer (HOW to think)
│   ├── __init__.py
│   ├── registry.py          # SkillRegistry (with circular dep detection)
│   ├── base.py              # BaseSkill abstract class
│   ├── planning/            # Task Planning
│   │   ├── simple_planner.py
│   │   ├── hierarchical.py
│   │   └── adaptive.py
│   ├── healing/             # Self-Healing
│   │   ├── practical.py
│   │   └── llm_based.py
│   ├── research/            # Research Methodology
│   │   ├── synthesizer.py
│   │   └── fact_checker.py
│   ├── coding/              # Code Intelligence
│   │   ├── architect.py
│   │   ├── debugger.py
│   │   └── reviewer.py
│   ├── communication/       # Human Interaction
│   │   ├── summarizer.py
│   │   ├── translator.py
│   │   └── presenter.py
│   ├── legal/               # Legal Reasoning
│   │   ├── analyzer.py
│   │   ├── researcher.py
│   │   ├── citator.py
│   │   └── drafter.py
│   └── admin/               # Admin Skills
│       ├── correspondence.py
│       ├── scheduler.py
│       ├── mailroom.py
│       └── reporter.py
│
├── 📁 knowledge/            # RAG layer (WHAT to know)
│   ├── __init__.py
│   ├── base.py              # KnowledgeBase abstract class
│   ├── loaders/             # Document Ingestion
│   │   ├── url.py
│   │   ├── file.py
│   │   ├── github.py
│   │   └── legal/
│   │       ├── uu_loader.py
│   │       └── putusan.py
│   ├── chunkers/            # Text Segmentation
│   │   ├── semantic.py
│   │   ├── fixed.py
│   │   └── recursive.py
│   ├── embeddings/          # Vectorization
│   │   ├── ollama.py
│   │   ├── openai.py
│   │   └── huggingface.py
│   ├── retrievers/          # Search Strategies
│   │   ├── similarity.py
│   │   ├── keyword.py
│   │   └── hybrid.py
│   ├── stores/              # Vector Databases
│   │   ├── pgvector.py      # PRIMARY: PostgreSQL (ACID, proven)
│   │   ├── zvec.py          # CACHE: Alibaba Zvec (local, low-latency)
│   │   └── chroma.py        # Alternative store
│   ├── cache/               # Cache management
│   │   ├── zvec_cache.py    # Zvec cache with TTL
│   │   ├── invalidator.py   # Cache invalidation
│   │   └── warmer.py        # Pre-warm cache
│   ├── versioning/          # Knowledge versioning
│   │   ├── manager.py       # Version control for KB
│   │   └── diff.py          # Compare versions
│   └── generators/          # Answer Synthesis
│       ├── qa.py
│       └── summary.py
│
├── 📁 memory/               # Agent Memory (LTM + Working)
│   ├── __init__.py
│   ├── longterm.py          # PostgreSQL (personal memory)
│   ├── working.py           # Redis (session cache)
│   └── episodic.py          # Event/episode memory
│
├── 📁 agents/               # Agent Definitions
│   ├── __init__.py
│   ├── base.py              # BaseAgent class
│   ├── profiles/            # Pre-configured agents
│   │   ├── legal_assistant.py
│   │   ├── office_assistant.py
│   │   ├── code_assistant.py
│   │   └── mailroom_manager.py
│   └── orchestrator.py      # Multi-agent coordination
│
├── 📁 core/                 # System Core
│   ├── server.py            # FastAPI app
│   ├── task.py              # Task & TaskResult definitions
│   ├── circuit_breaker.py
│   ├── rate_limiter.py
│   └── security.py          # Auth, RBAC, audit
│
├── 📁 observability/        # Monitoring
│   ├── logger.py
│   └── metrics.py
│
└── 📁 tests/                # Test Suites
    ├── unit/
    ├── integration/
    └── domain/              # Domain-specific tests
```

---

## 2. Three-Layer Architecture Diagram

### 2.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT LAYER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Legal Agent │  │ Admin Agent │  │ Code Agent  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                    SKILLS LAYER                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Planning   │ │   Research   │ │ Communication│        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                    TOOLS LAYER                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │  Web Search  │ │ File Manager │ │   Calendar   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE LAYER                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Legal KB   │ │   Admin KB   │ │   Code KB    │        │
│  │  (RAG-based) │ │  (RAG-based) │ │  (RAG-based) │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Example

**Scenario:** Legal Agent menangani kasus "Sewa rumah atap bocor"

```
User Input
    ↓
┌─────────────────────────────────────────┐
│  AGENT: Legal Assistant                 │
│  - Menerima task dari user              │
│  - Koordinasi skills yang diperlukan    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  SKILL: legal.researcher                │
│  - Cari peraturan terkait sewa-menyewa  │
│  - Query ke: knowledge.hukum-perdata    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  KNOWLEDGE: pgvector (primary)          │
│  - Retrieve: Pasal 1552, 1571, 1600 BW  │
│  - Fallback ke Zvec cache jika ada      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  SKILL: legal.analyzer                  │
│  - Interpretasi hak dan kewajiban       │
│  - Gunakan TOOL: document.pdf untuk     │
│    generate analisis tertulis           │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  TOOL: document.pdf                     │
│  - Generate PDF analisis hukum          │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  SKILL: legal.drafter                   │
│  - Draft surat peringatan ke pemilik    │
│  - Gunakan TOOL: email.sender           │
└─────────────────────────────────────────┘
    ↓
Output ke User
```

---

## 3. Key Design Principles

### 3.1 Separation of Concerns

| Layer | Responsibility | Example |
|-------|---------------|---------|
| **Agent** | Domain expertise, task delegation | `LegalAgent` knows hukum perdata |
| **Skill** | How to think, methodology | `Researcher` knows cara riset |
| **Tool** | What to execute, actions | `EmailSender` kirim email |
| **Knowledge** | What to know, facts | `HukumPerdataKB` store UU |

### 3.2 Namespace Isolation

Setiap domain punya namespace terpisah:

```python
# Legal knowledge - isolated
knowledge://hukum-perdata
knowledge://putusan-pengadilan

# Admin knowledge - isolated  
knowledge://admin-kantor
knowledge://template-surat

# No cross-contamination!
```

### 3.3 Plugin Architecture

Tambah domain baru = tambah folder baru, tanpa ubah core:

```
skills/
├── legal/           # Existing
├── admin/           # Existing
└── medical/         # NEW - just add this folder
    ├── __init__.py
    ├── diagnosis.py
    └── drug_checker.py
```

---

## 4. Cross-References

- Lihat `03-core-components.md` untuk base classes detail
- Lihat `04-knowledge-layer.md` untuk RAG implementation
- Lihat `07-domain-examples.md` untuk use cases konkret

---

**Prev:** [01-executive-summary.md](01-executive-summary.md)  
**Next:** [03-core-components.md](03-core-components.md)
