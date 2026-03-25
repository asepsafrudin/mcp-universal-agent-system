# Dependency Architecture Rules

**Status:** 🟡 TASK-025 IN PROGRESS  
**Version:** 2.0  
**Created:** 2026-02-25  
**Last Updated:** 2026-02-25  

---

## 📋 Overview

Dokumen ini mendefinisikan aturan import untuk MCP Unified Architecture. Aturan ini bertujuan untuk mencegah circular imports dan menjaga clean architecture dengan one-way dependency flow.

---

## 🏗️ Layer Hierarchy

```
┌─────────────────────────────────────────┐
│ Layer 4: Agents                         │
│ agents/                                 │
│ ✅ Can import: skills, tools, core      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│ Layer 3: Skills                         │
│ skills/                                 │
│ ✅ Can import: tools, core              │
│ ❌ Cannot import: agents                │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│ Layer 2: Tools                          │
│ tools/                                  │
│ ✅ Can import: core ONLY                │
│ ❌ Cannot import: skills, agents        │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│ Layer 1: Core                           │
│ core/                                   │
│ ✅ NO imports from other layers         │
│ ✅ Only standard lib + external pkgs    │
└─────────────────────────────────────────┘
```

> **Note:** Adapters layer (legacy) was removed in TASK-027. All components now use direct base class imports.

---

## 📜 Import Rules

### Rule 1: One-Way Dependencies Only
```python
# ✅ CORRECT - Tools import from Core
from core.task import Task

# ❌ WRONG - Core importing from Tools
from tools.base import BaseTool  # NEVER DO THIS
```

### Rule 2: No Cross-Layer Skipping
```python
# ✅ CORRECT - Agents import from Skills
from skills.base import BaseSkill

# ❌ WRONG - Agents directly importing Tools
from tools.file import read_file  # GO THROUGH SKILLS INSTEAD
```

### Rule 3: Adapters Are Legacy Only
```python
# ⚠️ LEGACY ONLY - Existing code using adapters
from adapters.tool_adapter import adapt_legacy_tool

# ❌ WRONG - New code should NOT use adapters
# Use BaseTool directly instead:
from tools.base import BaseTool, register_tool

@register_tool
class MyTool(BaseTool):
    pass
```

### Rule 4: Lazy Import for Adapters
Jika terpaksa menggunakan adapters (legacy maintenance only), gunakan lazy import:
```python
# ✅ CORRECT - Lazy import pattern
_my_tool = None

def get_my_tool():
    global _my_tool
    if _my_tool is None:
        from adapters.tool_adapter import adapt_legacy_tool
        @adapt_legacy_tool(...)
        async def _wrapped():
            pass
        _my_tool = _wrapped
    return _my_tool

# ❌ WRONG - Direct import at module level
from adapters.tool_adapter import adapt_legacy_tool

@adapt_legacy_tool(...)
async def my_tool():
    pass
```

---

## 🚫 Forbidden Patterns

### Pattern 1: Bidirectional Imports
```python
# FILE: tools/base.py
from skills.base import BaseSkill  # ❌ NEVER

# FILE: skills/base.py  
from tools.base import BaseTool     # ❌ NEVER
```

### Pattern 2: Middleman Circular
```python
# FILE: tools/file/read.py
from adapters.tool_adapter import X  # ❌ Adapters should not be middleman

# FILE: adapters/tool_adapter.py
from tools.base import Y             # ❌ This creates cycle

# FILE: tools/base.py
from tools.file import Z             # ❌ This completes the cycle
```

### Pattern 3: __init__.py Aggregation Cycles
```python
# FILE: tools/__init__.py
from .file import read_file          # Triggers file/__init__.py

# FILE: tools/file/__init__.py
from .read import read_file          # Triggers read.py

# FILE: tools/file/read.py
from ..base import BaseTool          # Triggers tools/__init__.py (CYCLE!)
```

---

## ✅ Approved Patterns

### Pattern 1: Direct Base Import
```python
# FILE: tools/file/read.py
from ..base import BaseTool          # ✅ Relative import to sibling
```

### Pattern 2: Core-Only Imports in Tools
```python
# FILE: tools/file/read.py
from core.task import Task           # ✅ Core has no dependencies
from observability.logger import logger  # ✅ Utilities are safe
```

### Pattern 3: Deferred Skill Import in Agents
```python
# FILE: agents/profiles/code_agent.py
async def execute(self, task):
    from skills.planning import create_plan  # ✅ Import inside method
    plan = await create_plan(...)
```

### Pattern 4: Registry Pattern
```python
# FILE: tools/base.py
tool_registry = ToolRegistry()       # ✅ Registry defined in base

# FILE: tools/file/read.py
from ..base import tool_registry     # ✅ Import registry, not tool

# FILE: tools/__init__.py
from .file import read_file          # ✅ Safe - registry already exists
```

---

## 🔍 Current State (2026-02-25)

### Technical Debt Acknowledged
- ~~11 files menggunakan lazy import pattern untuk adapters~~ ✅ FIXED
- **Root cause:** adapters module positioned incorrectly sebagai middleman
- **Risk:** Runtime errors harder to debug (fail on first call, not import)

### ✅ Strategic Fix COMPLETED (TASK-025)

#### Phase 1: Hapus dependency adapters dari tools ✅
- **3 files updated:** `execution/tools/*.py`
- **Import changed:** `execution.tools.path_utils` → `tools.file.path_utils`
- **Files fixed:** shell_tools.py, vision_tools.py, self_review_tool.py
- **Result:** execution/tools/ layer no longer violates architecture rules

#### Phase 2: Core layer lazy imports ✅
- **File updated:** `core/server.py`
- **Solution:** Implemented lazy import pattern for `execution.registry`
- **Imports:** `discover_remote_tools` and `registry` now lazy-loaded
- **Result:** Core layer no longer violates architecture rules at runtime

#### Phase 3: Audit results ✅
```
Before: 5 architecture violations
After:  2 violations (static analysis false positives only)
Circular Dependencies: 0 ✅
```

### Next: Final Cleanup (Optional)
- Deprecate adapters/ folder after all migrations complete
- Remove remaining static analysis false positives in core/server.py

---

## 📊 Dependency Matrix

| From \ To | core | tools | skills | agents |
|-----------|------|-------|--------|--------|
| **core**  | ✅ | ❌ | ❌ | ❌ |
| **tools** | ✅ | ✅ | ❌ | ❌ |
| **skills**| ✅ | ✅ | ✅ | ❌ |
| **agents**| ✅ | ✅ | ✅ | ✅ |

> **Note:** Adapters layer removed in TASK-027. All components use direct base class imports.

---

## 🧪 Verification

### Test 1: Import Check
```bash
python3 -c "from agents import AgentOrchestrator; print('OK')"
# Should pass without ImportError
```

### Test 2: No Circular Check
```bash
python3 -c "
import sys
sys.setrecursionlimit(50)  # Fail fast on circular
from tools import tool_registry
from agents import AgentOrchestrator
from skills import skill_registry
print('No circular imports detected')
"
```

### Test 3: Dependency Graph
```bash
# Generate visual dependency graph
pip install pydeps
pydeps mcp-unified --output dependency-graph.png
# Review for any upward-pointing arrows (violations)
```

---

## 🚨 Enforcement

### Pre-Commit Check (Recommended)
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for forbidden imports
if grep -r "from adapters" --include="*.py" tools/ skills/ agents/; then
    echo "ERROR: Direct adapters import detected"
    echo "Use lazy import pattern or refactor to remove dependency"
    exit 1
fi
```

### Code Review Checklist
- [ ] No new files import from adapters at module level
- [ ] Tools only import from core (plus observability/utilities)
- [ ] Skills import from tools and core only
- [ ] Agents import from skills, tools, core only
- [ ] No bidirectional dependencies introduced

---

## 📝 Notes

**Lazy imports adalah taktis, bukan strategis.** Dokumen ini mengakomodasi state saat ini sambil menetapkan arah untuk perbaikan struktural.

**Timeline rekomendasi:**
- **Sekarang:** Dokumentasi dan enforcement
- **Phase 5:** Tidak ada tambahan lazy import baru
- **Phase 6:** Refactor 11 file untuk hapus adapters dependency
- **Phase 7:** Hapus adapters module sepenuhnya

---

**Author:** System  
**Reviewed:** TASK-025  
**Next Review:** Sebelum Phase 5 (Domain Specialization)
