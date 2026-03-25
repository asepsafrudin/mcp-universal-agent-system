# TASK-027: Phase 6 - Adapters Cleanup

**Status:** COMPLETED
**Priority:** CRITICAL  
**Phase:** Phase 6 Completion  
**Created:** 2026-02-25  
**Estimated Duration:** 3-4 hours  

---

## 📋 Overview

**Goal:** Hapus `adapters` module sepenuhnya dan refactor semua dependent files untuk menggunakan direct imports.

**Context:**
- Adapters adalah legacy compatibility layer dari Phase 4 migration
- Semua tools/skills/agents sekarang mengakses adapters via lazy imports (TASK-025 fix)
- Phase 6 akan menghapus adapters dan menggunakan direct imports ke base classes

**Files Affected:** 11 files dengan lazy imports

---

## 🎯 Objectives

1. **Refactor Tools Layer** (5 files) - Remove `adapters.tool_adapter` dependency
2. **Refactor Skills Layer** (2 files) - Remove `adapters.skill_adapter` dependency  
3. **Refactor Agents Layer** (1 file) - Remove `adapters.agent_adapter` dependency
4. **Delete Adapters Module** (4 files) - Remove entire `adapters/` directory
5. **Update Documentation** - Remove adapters references dari docs

---

## 🏗️ Implementation Plan

### Step 1: Tools Layer Refactoring (90 min)
Files to refactor:
- [ ] `tools/file/write.py` - Remove `get_write_file_tool()` lazy wrapper
- [ ] `tools/file/list_dir.py` - Remove `get_list_dir_tool()` lazy wrapper
- [ ] `tools/admin/shell.py` - Remove `get_run_shell_tool()` lazy wrapper
- [ ] `tools/media/vision.py` - Remove vision tool lazy wrappers
- [ ] `tools/code/self_review.py` - Remove self_review lazy wrappers

**Pattern:** Replace `@adapt_legacy_tool` decorator dengan direct `@register_tool` decorator dari `tools.base`.

### Step 2: Skills Layer Refactoring (45 min)
Files to refactor:
- [ ] `skills/planning/simple_planner.py` - Remove lazy skill adapter import
- [ ] `skills/healing/self_healing.py` - Remove lazy skill adapter import

**Pattern:** Replace `@adapt_legacy_skill` dengan `@register_skill` dari `skills.base`.

### Step 3: Agents Layer Refactoring (30 min)
Files to check:
- [ ] `agents/profiles/*.py` - Verify no adapter imports

**Note:** Agents sudah menggunakan `@register_agent` decorator, tidak perlu refactor.

### Step 4: Delete Adapters Module (30 min)
Remove files:
- [ ] `adapters/__init__.py`
- [ ] `adapters/tool_adapter.py`
- [ ] `adapters/skill_adapter.py`
- [ ] `adapters/agent_adapter.py`

### Step 5: Testing & Verification (45 min)
- [ ] Run full integration tests
- [ ] Verify no circular imports
- [ ] Verify all 15 tools still registered
- [ ] Verify all 3 skills still registered
- [ ] Verify all 6 agents still registered

---

## 📝 Migration Pattern

### BEFORE (with adapters)
```python
# tools/file/write.py
_my_tool = None

def get_write_file_tool():
    global _my_tool
    if _my_tool is None:
        from adapters.tool_adapter import adapt_legacy_tool
        
        @adapt_legacy_tool(...)
        async def _wrapped():
            return await write_file()
        
        _my_tool = _wrapped
    return _my_tool
```

### AFTER (direct import)
```python
# tools/file/write.py
from tools.base import register_tool

@register_tool(name="write_file", ...)
async def write_file(...):
    ...
```

---

## ⚠️ Risk Mitigation

**Risk:** Breaking changes jika refactor tidak sempurna
**Mitigation:** 
1. Refactor satu file per step
2. Test setelah setiap file
3. Keep backups (git history)
4. Rollback plan ready

**Risk:** Circular imports kembali muncul
**Mitigation:**
1. Verify dependency rules compliance
2. Run grep audit setelah setiap change
3. Integration test final verification

---

## ✅ Success Criteria

- [ ] Zero files import from `adapters.*`
- [ ] Adapters module deleted
- [ ] All 15 tools registered and working
- [ ] All 3 skills registered and working
- [ ] All 6 agents registered and working
- [ ] No circular imports
- [ ] Integration tests: 7/7 PASSED

---

## 🚀 Next Phase

After Phase 6 complete:
- **Phase 7:** Performance Optimization
- **Phase 8:** Production Hardening

---

**Status:** Ready to start Step 1
