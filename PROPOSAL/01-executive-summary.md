# Proposal Refactoring: MCP Server - Multi-Agent Architecture

**Versi:** 1.2  
**Tanggal:** 24 Februari 2026  
**Status:** Final Draft

---

## 1. Executive Summary

Proposal ini mengusulkan refactoring besar-besaran pada arsitektur MCP (Model Context Protocol) Server dari struktur monolitik menjadi **Multi-Agent Domain-Driven Architecture**. Perubahan ini memungkinkan agen untuk memiliki multi-talenta spesifik domain dengan pemisahan yang jelas antara Tools, Skills, dan Knowledge.

### Key Highlights:
- **Pemisahan eksplisit:** Tools (execution) ↔ Skills (intelligence) ↔ Knowledge (RAG)
- **Multi-talenta:** Support multiple expertise per agen (Legal, Admin, Coding, Research, dll)
- **Namespace isolation:** Mencegah cross-domain contamination
- **Modular & extensible:** Mudah menambah domain baru

---

## 2. Problem Statement (Struktur Saat Ini)

### 2.1 Current Architecture
```
mcp-unified/
├── execution/        # Mix of tools & infrastructure
│   ├── tools/        # File, shell, vision tools
│   └── workspace.py  # Infrastructure tapi di execution/
├── intelligence/     # Skills tapi nama folder tidak eksplisit
│   ├── planner.py    # Single skill: planning
│   └── self_healing.py
├── memory/           # LTM & Working memory
│   ├── longterm.py   # PostgreSQL + pgvector
│   └── working.py    # Redis
└── ...
```

### 2.2 Issues Identified

| Issue | Impact | Evidence |
|-------|--------|----------|
| **LTM vs RAG** | Knowledge tidak bisa retrieve external docs | `memory/longterm.py` hanya personal memory |
| **Skills tidak modular** | Tidak bisa multi-talenta | `intelligence/planner.py` hardcoded |
| **Tools generic** | Tidak ada domain-specific tools | Semua tools di `execution/tools/` |
| **Workspace salah lokasi** | Semantic confusion | Infrastructure di `execution/` |
| **No Skill Registry** | Tidak ada discovery mechanism | Hanya ToolRegistry yang ada |

### 2.3 Missing Capabilities
- ❌ RAG (Retrieval-Augmented Generation) system
- ❌ Domain-specific agents (Legal, Admin, Medical, etc.)
- ❌ Multi-agent orchestration
- ❌ Skill discovery & registration
- ❌ Knowledge base versioning

---

## 3. Solution Overview

### 3.1 Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT LAYER                               │
│         (Domain-specific: Legal, Admin, Code)               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    SKILLS LAYER                              │
│         (Planning, Research, Communication, etc.)           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    TOOLS LAYER                               │
│         (Web, File, DB, Browser, Document, etc.)            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE LAYER                            │
│    (pgvector PRIMARY + Zvec CACHE + Versioning)             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Key Decisions (ADR)

| Decision | Rationale |
|----------|-----------|
| **pgvector PRIMARY, Zvec CACHE** | PostgreSQL = proven ACID durability; Zvec = local low-latency cache |
| **Circular dep detection** | Prevent runtime errors saat skill composition |
| **asyncio.Lock untuk state** | Thread-safe failover mechanism |
| **Task/TaskResult schema** | Standardized contract antar semua layer |

---

## 4. Document Series

Dokumen proposal ini dipecah menjadi seri file:

| # | File | Konten |
|---|------|--------|
| 01 | `01-executive-summary.md` | Ringkasan & masalah (file ini) |
| 02 | `02-architecture-overview.md` | Struktur direktori & layer diagram |
| 03 | `03-core-components.md` | Base classes, Task/TaskResult, Registry |
| 04 | `04-knowledge-layer.md` | RAG: pgvector + Zvec + versioning |
| 05 | `05-skills-layer.md` | Skill registry & circular dep detection |
| 06 | `06-agents-layer.md` | Agent profiles & orchestrator |
| 07 | `07-domain-examples.md` | Legal, Admin, Mailroom implementations |
| 08 | `08-security-audit.md` | Auth, RBAC, audit logging |
| 09 | `09-roadmap.md` | Implementation phases & success criteria |
| 10 | `10-appendix.md` | ADR, migration guide, benchmarks |

---

## 5. Quick Start

Untuk membaca proposal lengkap:
1. Mulai dari `01-executive-summary.md` (file ini)
2. Lanjut ke `02-architecture-overview.md` untuk struktur detail
3. Lihat `07-domain-examples.md` untuk use cases konkret
4. Cek `09-roadmap.md` untuk timeline implementasi

---

**Prepared by:** AI Architecture Assistant  
**Date:** 24 Februari 2026  
**Version:** 1.2
