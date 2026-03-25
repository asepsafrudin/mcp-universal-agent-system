# TASK-016: Migrate Code Analyzer to New Architecture

**Status:** COMPLETED
**Priority:** P1 - High  
**Created:** 2026-02-25  
**Started:** 2026-02-25  
**Assignee:** MCP System  
**Estimated Duration:** 2 hours  
**Parent:** TASK-012 (Phase 2 Migration)
**Depends on:**
- TASK-013 (File Tools - ✅ COMPLETED)
- TASK-014 (Shell Tools - ✅ COMPLETED)
- TASK-015 (Workspace Manager - ✅ COMPLETED)

---

## 📋 Overview

Migrasi code analyzer dari `execution/tools/code_analyzer.py` ke struktur baru `tools/code/code_analyzer.py` menggunakan adapter layer. Code Analyzer adalah komponen keempat dalam Phase 2 Migration yang bergantung pada file tools, shell tools, dan workspace manager.

Code Analyzer menyediakan:
- Static code analysis (lint, format check)
- Code metrics calculation
- Security vulnerability scanning
- Integration dengan shell commands untuk external tools

---

## 🎯 Goals

1. ✅ Create `tools/code/` directory structure
2. ✅ Migrate `code_analyzer.py` → modular code analysis tools
3. ✅ Wrap using `@adapt_legacy_tool` decorator
4. ✅ Integrate dengan `tools.file`, `tools.admin`, dan `environment.workspace`
5. ✅ Register ke `tool_registry`
6. ✅ Test backward compatibility
7. ✅ Update integration dengan execution layer

---

## 📂 Source & Target

### Source Files
```
execution/tools/
├── code_analyzer.py   → Code analysis implementation
└── shell_tools.py     → ✅ Sudah dimigrasi
```

### Target Structure
```
tools/
├── code/              🆕 (new folder)
│   ├── __init__.py
│   └── analyzer.py    🔄 (migrated)
├── file/              ✅ (exists - dependency)
│   ├── read.py
│   └── path_utils.py
├── admin/             ✅ (exists - dependency)
│   └── shell.py
└── base.py            ✅ (exists)

environment/           ✅ (exists - dependency)
└── workspace.py
```

---

## 📋 Migration Checklist

### 1. Setup Directory Structure
- [x] Create `tools/code/` directory
- [x] Create `tools/code/__init__.py`

### 2. Read Source Code
- [x] Read `execution/tools/code_analyzer.py`
- [x] Identify functions:
  - [x] `analyze_code()` - Main analysis function
  - [x] `check_syntax()` - Syntax checking
  - [x] `get_code_metrics()` - Metrics calculation
  - [x] `run_linter()` - External linter execution

### 3. Migrate code_analyzer.py
- [x] Copy content dari `execution/tools/code_analyzer.py`
- [x] Update imports:
  - [x] `from execution.tools.file_tools` → `from tools.file`
  - [x] `from execution.tools.shell_tools` → `from tools.admin`
  - [x] `from execution.workspace` → `from environment.workspace`
- [x] Wrap functions menggunakan `@adapt_legacy_tool`
- [x] Maintain backward compatibility

### 4. Functions to Migrate
- [x] `analyze_code()` - Comprehensive code analysis
- [x] `check_syntax()` - Language-specific syntax check
- [x] `get_code_metrics()` - Lines, complexity, etc.
- [x] `run_linter()` - Run external linting tools

### 5. Integration
- [x] Create `tools/code/__init__.py` dengan exports
- [x] Update `tools/__init__.py` untuk include code tools
- [x] Register code analysis tools ke `tool_registry`

### 6. Testing
- [x] Test analyze_code dengan sample files
- [x] Test syntax checking
- [x] Test metrics calculation
- [x] Test linter integration
- [x] Verify backward compatibility

### 7. Documentation
- [x] Update migration log
- [x] Document new structure
- [x] Mark as COMPLETED

---

## 🔗 Dependencies

**Depends on:**
- TASK-012 (Phase 1 Foundation) - ✅ COMPLETE
- TASK-013 (File Tools Migration) - ✅ COMPLETE
  - `tools.file.read_file` - Read source code
  - `tools.file.path_utils.is_safe_path()` - Path validation
- TASK-014 (Shell Tools Migration) - ✅ COMPLETE
  - `tools.admin.run_shell` - Run external linters
- TASK-015 (Workspace Manager) - ✅ COMPLETE
  - `environment.workspace.workspace_manager` - Workspace isolation

**Blocks:**
- TASK-017 (Self Review Tool) - requires code analysis
- TASK-020 (Code Assistant Agent) - requires code tools

---

## 📝 Migration Pattern

```python
# Old style (execution/tools/code_analyzer.py)
from execution.tools.file_tools import read_file
from execution.tools.shell_tools import run_shell
from execution.workspace import workspace_manager

async def analyze_code(file_path: str) -> Dict[str, Any]:
    '''Analyze code for issues and metrics.'''
    # Read file
    content = await read_file(file_path)
    # Run analysis
    ...

# New style (tools/code/analyzer.py)
from tools.file import read_file
from tools.admin import run_shell
from environment.workspace import workspace_manager
from adapters.tool_adapter import adapt_legacy_tool

@adapt_legacy_tool(
    name="analyze_code",
    description="Analyze code file for syntax, metrics, and issues",
    parameters=[
        {
            "name": "file_path",
            "type": "string",
            "description": "Path to code file to analyze",
            "required": True
        }
    ],
    register=True
)
async def analyze_code(file_path: str) -> Dict[str, Any]:
    '''Analyze code for issues and metrics.'''
    # Same implementation with updated imports
    ...

# Auto-registered ke tool_registry
# Available via both old and new interfaces
```

---

## 🛡️ Security Considerations

- ✅ Path validation menggunakan `tools.file.path_utils.is_safe_path()`
- ✅ Workspace isolation untuk analysis operations
- ✅ Timeout untuk external linter processes
- ✅ Output sanitization untuk mencegah injection

---

## ✅ Acceptance Criteria

- [x] Code Analyzer migrated to `tools/code/analyzer.py`
- [x] Backward compatibility maintained
- [x] Integration dengan file tools berfungsi
- [x] Integration dengan shell tools berfungsi
- [x] Workspace isolation untuk analysis
- [x] All analysis operations tested
- [x] External linter integration working
- [x] Documentation updated

---

## 🎉 Migration Results

### Files Created/Modified
| File | Description | Lines | Status |
|------|-------------|-------|--------|
| `tools/code/__init__.py` | Module exports | 35 | ✅ Created |
| `tools/code/analyzer.py` | Code analyzer | 280 | ✅ Migrated |
| `tools/__init__.py` | Updated exports | +12 | ✅ Modified |

### Dependencies Updated
| Source | Old Import | New Import | Status |
|--------|------------|------------|--------|
| file_tools | `execution.tools.file_tools` | `tools.file` | ✅ Updated |
| shell_tools | `execution.tools.shell_tools` | `tools.admin` | ✅ Updated |
| workspace | `execution.workspace` | `environment.workspace` | ✅ Updated |

### Test Results (Real)
```
=== Testing Code Analyzer Migration ===
1. Testing code analysis...
   ✅ analyze_code working
   ✅ Syntax check passed
   ✅ Metrics calculated
   
2. Testing linter integration...
   ✅ External linter executed
   ✅ Output parsed correctly
   
3. Testing workspace integration...
   ✅ Workspace isolation maintained
   ✅ Safe path validation active
   
4. Testing tool_registry...
   ✅ analyze_code registered
   ✅ check_syntax registered
   ✅ get_code_metrics registered
   ✅ run_linter registered

=== 🎉 Code Analyzer Migration Test PASSED ===
```

### Key Achievements
- ✅ **Backward Compatibility**: API tetap sama
- ✅ **Shared Dependencies**: Menggunakan tools.file, tools.admin, environment.workspace
- ✅ **Auto-registration**: Code tools terdaftar di tool_registry
- ✅ **Security Maintained**: Path validation + workspace isolation
- ✅ **Integration Verified**: Linter integration berfungsi

---

## 🚀 Next Steps

1. ✅ Execute migration - DONE
2. ✅ Verify functionality - DONE
3. ✅ Complete task - DONE
4. ⏭️ Move to next component:
   - **Option A**: Self Review Tool (TASK-017) - requires code analysis
   - **Option B**: Knowledge Layer (TASK-018) - RAG infrastructure
   - **Option C**: Skills Migration (TASK-019) - Planner

---

**Status:** ✅ COMPLETED  
**Last Updated:** 2026-02-25 12:30  
**Completion:** 100%
