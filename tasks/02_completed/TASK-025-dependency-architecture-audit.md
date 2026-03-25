# TASK-025: Dependency Architecture Audit & Fix

**Status:** 🟡 NOT STARTED  
**Priority:** CRITICAL  
**Type:** Architecture Fix  
**Created:** 2026-02-25  
**Estimated Duration:** 4-6 hours  

---

## 📋 Overview

Ini adalah **fix ketiga** untuk circular import di project ini. Pattern yang berulang menunjukkan ada **structural problem di dependency architecture** yang belum diselesaikan secara tuntas.

**Masalah Fundamental:**
```
Lazy import adalah taktis, bukan strategis.
```

Setiap kali fix dilakukan dengan lazy import, masalah yang sama muncul lagi di tempat lain. TASK-025 adalah kesempatan untuk memperbaiki dependency architecture secara fundamental.

---

## 🎯 Goals

1. **Audit Dependency Graph** - Mapping seluruh import relationships
2. **Define Import Rules** - Aturan jelas module mana boleh import mana
3. **Restructure Adapters** - Hapus atau reposisi adapters layer
4. **Implement Clean Architecture** - One-way dependency flow
5. **Verify All Tests Pass** - 100% test success rate

---

## 🔍 Root Cause Analysis

### Current Broken Pattern
```
┌─────────────────────────────────────────┐
│  tools/file/read.py                     │
│  → from adapters.tool_adapter import X  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  adapters/tool_adapter.py               │
│  → from tools.base import Y             │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  tools/base.py                          │
│  → from tools.file import Z             │
└─────────────────────────────────────────┘
```

**Problem:** `adapters` layer menjadi "middleman" yang menyebabkan circular dependency.

### Target Clean Architecture
```
┌─────────────────────────────────────────┐
│  Layer 4: Agents                        │
│  agents/                                │
│  → import from: skills, tools, core     │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Layer 3: Skills                        │
│  skills/                                │
│  → import from: tools, core             │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Layer 2: Tools                         │
│  tools/                                 │
│  → import from: core ONLY               │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Layer 1: Core                          │
│  core/                                  │
│  → NO imports from other layers         │
└─────────────────────────────────────────┘
```

**Adapters:** Dihapus atau dipindahkan ke layer yang tepat.

---

## 🏗️ Implementation Plan

### Phase 1: Audit (60 min)

#### Step 1.1: Generate Dependency Graph
```bash
# Tools untuk analysis
pip install pydeps
pydeps mcp-unified --output dependency-graph.png
```

#### Step 1.2: Manual Review
Review setiap file di:
- [ ] `tools/file/*.py`
- [ ] `tools/admin/*.py`
- [ ] `tools/code/*.py`
- [ ] `tools/media/*.py`
- [ ] `skills/planning/*.py`
- [ ] `skills/healing/*.py`
- [ ] `adapters/*.py`

Document semua cross-layer imports.

### Phase 2: Define Rules (30 min)

Buat file `docs/02-architecture/dependency-rules.md`:

```markdown
## Dependency Rules

### Layer 1: Core
- ✅ NO imports from tools, skills, agents, adapters
- ✅ Only standard library and external packages

### Layer 2: Tools
- ✅ Can import from: core
- ❌ Cannot import from: skills, agents, adapters

### Layer 3: Skills
- ✅ Can import from: tools, core
- ❌ Cannot import from: agents, adapters

### Layer 4: Agents
- ✅ Can import from: skills, tools, core
- ❌ Cannot import from: adapters

### Adapters
- ⚠️ TO BE DEPRECATED
- New code should NOT use adapters
- Existing adapters will be migrated
```

### Phase 3: Restructure (180 min)

#### Step 3.1: Hapus Adapters
Opsi A: **Hapus adapters layer sepenuhnya**
- Pindahkan `adapt_legacy_tool` ke `tools/base.py`
- Pindahkan `adapt_legacy_skill` ke `skills/base.py`
- Pindahkan `adapt_legacy_agent` ke `agents/base.py`

Opsi B: **Reposisi adapters ke entry points**
- Adapters hanya digunakan di `__init__.py` files
- Tidak boleh di-import dari module lain

**Rekomendasi:** Opsi A (hapus adapters)

#### Step 3.2: Fix Tools
Update semua tool files:
```python
# BEFORE (broken)
from adapters.tool_adapter import adapt_legacy_tool

@adapt_legacy_tool(...)
async def read_file(...):
    ...

# AFTER (clean)
from tools.base import register_tool, BaseTool

@register_tool(name="read_file")
class ReadFileTool(BaseTool):
    async def execute(self, task):
        ...
```

#### Step 3.3: Fix Skills
Update semua skill files:
```python
# BEFORE (broken)
from adapters.skill_adapter import adapt_legacy_skill

@adapt_legacy_skill(...)
async def create_plan(...):
    ...

# AFTER (clean)
from skills.base import register_skill, BaseSkill

@register_skill(name="create_plan")
class CreatePlanSkill(BaseSkill):
    async def execute(self, task):
        ...
```

### Phase 4: Testing (60 min)

#### Step 4.1: Import Tests
```python
# test_all_imports.py
def test_no_circular_imports():
    # Should not raise ImportError
    from agents import AgentOrchestrator
    from tools import tool_registry
    from skills import skill_registry
    from agents import agent_registry

def test_dependency_rules():
    # Tools should not import from skills
    # Core should not import from anyone
    ...
```

#### Step 4.2: Integration Tests
- [ ] Run `test_full_integration.py`
- [ ] Run `test_negative_cases.py`
- [ ] Run `test_adapter_migration.py`

### Phase 5: Documentation (30 min)

Update dokumentasi:
- [ ] `docs/02-architecture/dependency-rules.md`
- [ ] `docs/02-architecture/data-flow.md`
- [ ] Update README dengan architecture diagram

---

## 📊 Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **No Circular Imports** | 0 circular deps | `python -c "from agents import *"` passes |
| **All Tests Pass** | 100% | All integration tests pass |
| **Clean Architecture** | Verified | Dependency graph shows one-way flow |
| **No Adapters** | Removed | `adapters/` folder deleted or deprecated |
| **Documentation** | Complete | Architecture rules documented |

---

## 🚨 Critical Decisions

### Decision 1: Adapters Fate
**Option A:** Remove adapters completely
- Pros: Clean architecture, no middleman
- Cons: Breaking change for any code using adapters

**Option B:** Keep adapters as thin wrappers
- Pros: Backward compatibility
- Cons: Complexity remains

**Rekomendasi:** Option A - Remove adapters. Breaking change is acceptable karena project masih dalam development phase.

### Decision 2: Migration Strategy
**Option A:** Big bang migration
- Fix semua file sekaligus
- High risk, high reward

**Option B:** Incremental migration
- Fix per module (tools → skills → agents)
- Lower risk, takes longer

**Rekomendasi:** Option A - Big bang. Lebih baik selesai dalam 1 hari dengan full focus.

---

## 🎯 Deliverables

### Files to Modify
```
mcp-unified/
├── tools/
│   ├── file/read.py           # Remove adapters import
│   ├── file/write.py          # Remove adapters import
│   ├── file/list_dir.py       # Remove adapters import
│   ├── admin/shell.py         # Remove adapters import
│   ├── code/analyzer.py       # Remove adapters import
│   ├── code/self_review.py    # Remove adapters import
│   ├── media/vision.py        # Remove adapters import
│   └── base.py                # Add register_tool decorator
├── skills/
│   ├── planning/simple_planner.py   # Remove adapters import
│   ├── healing/self_healing.py      # Remove adapters import
│   └── base.py                      # Add register_skill decorator
├── agents/
│   └── base.py                # Add register_agent decorator
├── adapters/                  # DELETE or DEPRECATE
└── docs/
    └── 02-architecture/
        └── dependency-rules.md    # NEW
```

### New Files
- `docs/02-architecture/dependency-rules.md`
- `tests/test_dependency_graph.py`

---

## 🚀 Execution Plan

### Day 1: Preparation
- [ ] Backup current codebase
- [ ] Generate dependency graph
- [ ] Document current import issues

### Day 2: Migration
- [ ] Update `tools/base.py` with register_tool
- [ ] Migrate all tools (remove adapters)
- [ ] Update `skills/base.py` with register_skill
- [ ] Migrate all skills (remove adapters)

### Day 3: Cleanup & Testing
- [ ] Delete adapters folder
- [ ] Update all imports
- [ ] Run all tests
- [ ] Update documentation

---

## ⚠️ Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking changes | Project dalam development phase, acceptable |
| Test failures | Comprehensive test suite sebelum migration |
| Missing functionality | Feature parity checklist |
| Time overrun | Focus on critical path only |

---

## 📝 Notes

**Ini bukan sekadar "fix import"** — ini adalah kesempatan untuk memperbaiki dependency architecture secara fundamental sebelum Phase 5 (Domain Specialization) dimulai.

**Prinsip:**
- Clean architecture > backward compatibility (untuk sekarang)
- One-way dependencies > bidirectional
- Explicit > implicit

---

**Status:** 🟡 **NOT STARTED** - Ready for execution

**Next:** Execute migration setelah approval dari lead
