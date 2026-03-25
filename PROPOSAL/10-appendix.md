# 10 - Appendix

**ADR, Migration Guide, References**

---

## 1. Architecture Decision Records (ADR)

### ADR-001: pgvector PRIMARY, Zvec CACHE

**Status:** Accepted  
**Date:** 2026-02-24

**Context:**
Butuh vector store untuk RAG. Ada banyak opsi: pgvector, Zvec, Chroma, Pinecone.

**Decision:**
- PRIMARY: PostgreSQL + pgvector (ACID, proven, enterprise-grade)
- CACHE: Zvec (local, low-latency)

**Consequences:**
- ✅ Durability dengan PostgreSQL
- ✅ Performance dengan Zvec cache
- ⚠️ Complexity dual-store management

---

### ADR-002: Circular Dependency Detection di Skill Registry

**Status:** Accepted  
**Date:** 2026-02-24

**Context:**
Skills bisa depend on other skills. Risk circular dependency.

**Decision:**
DFS-based cycle detection saat skill registration.

**Consequences:**
- ✅ Fail fast saat startup
- ✅ Clear error messages
- ⚠️ Slight registration overhead

---

## 2. Migration Guide

### From Monolith to Multi-Agent

**Step 1: Backup**
```bash
cp -r mcp-unified mcp-unified-backup
```

**Step 2: Setup New Structure**
```bash
mkdir -p mcp-server/{environment,tools,skills,knowledge,agents,core}
```

**Step 3: Migrate Tools**
```python
# Old: execution/tools/file_tools.py
# New: tools/file/read.py

from tools.base import BaseTool

class ReadFileTool(BaseTool):
    name = "read_file"
    # ... implementation
```

**Step 4: Test**
```bash
pytest tests/ -v
```

---

## 3. References

- [MCP Protocol](https://modelcontextprotocol.io/)
- [pgvector](https://github.com/pgvector/pgvector)
- [Alibaba Zvec](https://github.com/alibaba/zvec) *(placeholder)*
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)

---

**Prev:** [09-roadmap.md](09-roadmap.md)
