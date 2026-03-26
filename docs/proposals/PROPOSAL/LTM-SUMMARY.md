# LTM Summary: MCP Multi-Agent Architecture Proposal

**Stored:** 2026-02-24  
**Namespace:** mcp-architecture-planning  
**Status:** ACTIVE

---

## Key Decisions (MUST REMEMBER)

### 1. Three-Layer Architecture
- **Tools**: Execution layer (WHAT to do)
- **Skills**: Intelligence layer (HOW to think)  
- **Knowledge**: RAG layer (WHAT to know)

### 2. Knowledge Store Strategy
- **PRIMARY**: PostgreSQL + pgvector (ACID, proven durability)
- **CACHE**: Zvec (local, low-latency, optional)
- **Pattern**: Cache-first query, fallback to primary

### 3. Critical Fixes (from Senior Review)
- ✅ asyncio.Lock untuk thread-safe state
- ✅ Circular dependency detection di SkillRegistry
- ✅ @abstractmethod di semua base classes
- ✅ Task/TaskResult schema terdefinisi

---

## File Locations

```
MCP/PROPOSAL/
├── 01-executive-summary.md      # Start here
├── 02-architecture-overview.md  # Directory structure
├── 03-core-components.md        # Base classes & schema
├── 04-knowledge-layer.md        # RAG: pgvector + Zvec
├── 05-skills-layer.md           # Skill registry
├── 06-agents-layer.md           # Orchestrator
├── 07-domain-examples.md        # Legal, Admin, Mailroom
├── 08-security-audit.md         # Auth & RBAC
├── 09-roadmap.md                # 14-week timeline
├── 10-appendix.md               # ADR & migration
└── LTM-SUMMARY.md               # This file
```

---

## Quick Reference

### Start New Domain
```bash
# 1. Add skills
mkdir skills/{newdomain}/
# 2. Add tools  
mkdir tools/{newdomain}/
# 3. Add knowledge loader
mkdir knowledge/loaders/{newdomain}/
# 4. Create agent profile
agents/profiles/{newdomain}_assistant.py
```

### Key Configuration
```yaml
knowledge:
  stores:
    primary: {type: pgvector, host: ..., db: ...}
    cache: {type: zvec, path: ./cache/knowledge.zvec}
```

---

## Next Actions (When Resuming)

1. Review `01-executive-summary.md` untuk refresh
2. Check `09-roadmap.md` untuk current phase
3. Implement sesuai phase yang aktif

---

**DO NOT DELETE THIS FOLDER** - This is the architectural blueprint.
