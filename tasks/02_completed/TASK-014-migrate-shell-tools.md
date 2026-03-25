# TASK-014: Migrate Shell Tools to New Architecture

**Status:** COMPLETED
**Priority:** P1 - High  
**Created:** 2026-02-25  
**Started:** 2026-02-25  
**Assignee:** MCP System  
**Estimated Duration:** 2 hours  
**Parent:** TASK-012 (Phase 2 Migration)
**Depends on:** TASK-013 (File Tools - COMPLETED)

---

## 📋 Overview

Migrasi shell tools dari `execution/tools/shell_tools.py` ke struktur baru `tools/admin/` menggunakan adapter layer. Shell tools adalah komponen kedua dalam Phase 2 Migration yang bergantung pada `path_utils` (sudah dimigrasi di TASK-013).

---

## 🎯 Goals

1. ✅ Create `tools/admin/` directory structure
2. ✅ Migrate `shell_tools.py` → modular shell tools
3. ✅ Wrap using `@adapt_legacy_tool` decorator
4. ✅ Integrate dengan `path_utils` yang sudah dimigrasi
5. ✅ Register ke `tool_registry`
6. ✅ Test backward compatibility
7. ✅ Update security validation

---

## 📂 Source & Target

### Source Files
```
execution/tools/
├── shell_tools.py     → Shell command execution
└── path_utils.py      → ✅ Sudah dimigrasi ke tools/file/
```

### Target Structure
```
tools/
├── base.py            ✅ (exists)
├── __init__.py        ✅ (exists)
├── file/              ✅ (exists - has path_utils)
│   └── path_utils.py  ✅ (shared dependency)
└── admin/             🆕 (new folder)
    ├── __init__.py
    └── shell.py       🔄 (migrated from shell_tools.py)
```

---

## 📋 Migration Checklist

### 1. Setup Directory Structure
- [x] Create `tools/admin/` directory
- [x] Create `tools/admin/__init__.py`

### 2. Migrate shell_tools.py
- [x] Read source `execution/tools/shell_tools.py`
- [x] Extract functions:
  - [x] `run_shell()` - Main shell execution
  - [x] `execute_command()` - Command wrapper
  - [x] Helper functions (timeout, validation)
- [x] Migrate path validation to use `tools.file.path_utils`
- [x] Wrap menggunakan `@adapt_legacy_tool`

### 3. Security & Validation
- [x] Integrate `is_safe_path()` dari `tools.file.path_utils`
- [x] Maintain command whitelist/blacklist
- [x] Add timeout protection
- [x] Logging dengan observability.logger

### 4. Integration
- [x] Update `tools/admin/__init__.py` exports
- [x] Update `tools/__init__.py` untuk import admin tools
- [x] Register all shell tools ke `tool_registry`

### 5. Testing
- [x] Run existing shell tests (`test_shell_hardening.py`)
- [x] Verify backward compatibility
- [x] Test path validation integration
- [x] Test security boundaries

### 6. Documentation
- [x] Update migration log
- [x] Document new structure
- [x] Mark as COMPLETED

---

## 🔗 Dependencies

**Depends on:**
- TASK-012 (Phase 1 Foundation) - ✅ COMPLETE
- TASK-013 (File Tools Migration) - ✅ COMPLETE
  - `tools.file.path_utils.is_safe_path()`

**Blocks:**
- TASK-015 (Workspace Manager) - requires shell execution
- TASK-016 (Code Analyzer) - requires shell commands

---

## 📝 Migration Pattern

```python
# Old style (execution/tools/shell_tools.py)
async def run_shell(command: str, timeout: int = 30) -> Dict[str, Any]:
    '''Execute shell command with safety checks.'''
    # Security validation
    if not is_safe_command(command):
        return {"success": False, "error": "Unsafe command"}
    # Execute with timeout
    ...

# New style (tools/admin/shell.py)
from adapters.tool_adapter import adapt_legacy_tool
from tools.file.path_utils import is_safe_path

@adapt_legacy_tool(
    name="run_shell",
    description="Execute shell command with safety validation",
    parameters=[
        {
            "name": "command",
            "type": "string",
            "description": "Shell command to execute",
            "required": True
        },
        {
            "name": "timeout",
            "type": "integer",
            "description": "Timeout in seconds",
            "required": False,
            "default": 30
        }
    ],
    register=True
)
async def run_shell(command: str, timeout: int = 30) -> Dict[str, Any]:
    '''Execute shell command with safety checks.'''
    # Same implementation with shared path_utils
    ...

# Auto-registered ke tool_registry
# Available via both old and new interfaces
```

---

## 🛡️ Security Considerations

### Command Validation
- ✅ Whitelist approach: Only allow safe commands
- ✅ Blacklist: Reject dangerous commands (rm -rf, etc.)
- ✅ Path validation: Use shared `is_safe_path()`
- ✅ Timeout: Prevent hanging processes
- ✅ Output limits: Prevent memory exhaustion

### Safety Rules
```python
DANGEROUS_PATTERNS = [
    "rm -rf", "rm -fr", "rmdir /", "mkfs", "dd if",
    "> /dev", ":(){:|:&};:", "chmod -R 777 /",
    "wget.*|.*sh", "curl.*|.*sh",  # Pipe to shell
]
```

---

## ✅ Acceptance Criteria

- [x] Shell tools migrated to `tools/admin/`
- [x] Backward compatibility maintained
- [x] Path validation menggunakan shared `path_utils`
- [x] Security boundaries enforced
- [x] All tests pass (`test_shell_hardening.py`)
- [x] Documentation updated

---

## 🎉 Migration Results

### Files Created/Modified
| File | Description | Lines | Status |
|------|-------------|-------|--------|
| `tools/admin/__init__.py` | Module exports | 35 | ✅ Created |
| `tools/admin/shell.py` | Shell execution tool | 195 | ✅ Migrated |
| `tools/__init__.py` | Updated exports | +15 | ✅ Modified |

### Test Results (Real)
```
=== Testing Shell Tools Migration (Fixed) ===
1. Testing shell tools import...
   ✅ Shell tools imported successfully

2. Testing tool_registry...
   ✅ tool_registry has 4 tools registered
   Registered tools: ['read_file', 'write_file', 'list_dir', 'run_shell']
   ✅ run_shell registered in tool_registry

3. Testing shell execution (backward compatibility)...
   2026-02-25 11:24:10 [info] shell_command_attempt command=pwd
   2026-02-25 11:24:10 [info] shell_command_executing command=pwd
   2026-02-25 11:24:10 [info] shell_command_success command=pwd
   ✅ Shell execution working
   Output: /home/aseps/MCP/mcp-unified

=== 🎉 Shell Tools Migration Test PASSED ===
```

### Key Achievements
- ✅ **Backward Compatibility**: `run_shell()` tetap callable langsung
- ✅ **Dual Interface**: Bisa dipanggil sebagai fungsi atau via BaseTool registry
- ✅ **Shared Security**: Menggunakan `tools.file.path_utils.is_safe_path()`
- ✅ **Auto-registration**: Terdaftar di `tool_registry` secara otomatis
- ✅ **Security Maintained**: Whitelist + dangerous pattern detection aktif

### Architecture Pattern (New)
```python
# Implementation (core logic)
async def _run_shell_impl(command, user_context): ...

# Public API (backward compatible)
async def run_shell(command, user_context): 
    return await _run_shell_impl(command, user_context)

# Adapter Registration (for BaseTool)
_run_shell_wrapped = adapt_legacy_tool(...)(_run_shell_impl)
```

---

## 🚀 Next Steps

1. ✅ Execute migration - DONE
2. ✅ Verify functionality - DONE
3. ✅ Complete task - DONE
4. ⏭️ Move to next component:
   - **Option A**: Workspace Manager (TASK-015) - requires file + shell
   - **Option B**: Code Analyzer (TASK-016) - requires shell
   - **Option C**: Knowledge Layer (TASK-017) - RAG infrastructure

---

**Status:** ✅ COMPLETED  
**Last Updated:** 2026-02-25 11:30  
**Completion:** 100%
