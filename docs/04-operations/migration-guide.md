# MCP Migration Guide

**Version:** 1.0.0  
**Last Updated:** 2026-02-25  
**Applies to:** MCP v1.0.0+

---

## Overview

Guide ini menjelaskan cara bermigrasi ke sistem MCP Unified dari berbagai sistem lama.

### Supported Migration Paths

1. **From Legacy Adapters** → MCP Unified (4-layer architecture)
2. **From Standalone Tools** → MCP Tool System
3. **From Custom Agents** → MCP Agent Framework

---

## Migration from Legacy Adapters

### Background

Versi lama MCP menggunakan "adapters" pattern yang sekarang sudah deprecated. Arsitektur baru menggunakan 4-layer clean architecture.

**Old (Deprecated):**
```
adapters/
  file_adapter.py
  shell_adapter.py
  workspace_adapter.py
```

**New (Current):**
```
tools/
  file/
    read.py
    write.py
  admin/
    shell.py
environment/
  workspace.py
```

### Migration Steps

#### 1. Update Imports

**Before:**
```python
from adapters.file_adapter import FileAdapter
from adapters.shell_adapter import ShellAdapter
```

**After:**
```python
from tools.file.read import read_file_tool
from tools.admin.shell import shell_tool
```

#### 2. Update Tool Calls

**Before:**
```python
adapter = FileAdapter()
result = adapter.read_file("/path/to/file")
```

**After:**
```python
from tools.file.read import read_file

result = await read_file(path="/path/to/file")
```

#### 3. Workspace Management

**Before:**
```python
from adapters.workspace_adapter import WorkspaceAdapter

ws = WorkspaceAdapter()
ws.set_workspace("/tmp/workspace")
```

**After:**
```python
from environment.workspace import WorkspaceManager

ws = WorkspaceManager()
await ws.set_workspace("/tmp/workspace")
```

### Breaking Changes

| Feature | Old | New | Action Required |
|---------|-----|-----|-----------------|
| File operations | `FileAdapter` | `tools.file.*` | Update imports |
| Shell execution | `ShellAdapter` | `tools.admin.shell` | Update calls |
| Workspace | `WorkspaceAdapter` | `environment.workspace` | Update initialization |
| Error handling | Adapter exceptions | Tool exceptions | Update exception handling |

---

## Migration from Standalone Tools

### Converting Custom Tools

**Before (Standalone):**
```python
# my_custom_tool.py
class MyTool:
    def execute(self, params):
        return {"result": "done"}
```

**After (MCP Tool):**
```python
# tools/custom/my_tool.py
from tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    name = "my_tool"
    description = "My custom tool"
    
    parameters = {
        "input": {
            "type": "string",
            "description": "Input parameter"
        }
    }
    
    async def execute(self, input: str) -> ToolResult:
        return ToolResult.success(result="done")
```

### Registration

```python
# In tools/__init__.py or during startup
from tools.custom.my_tool import MyTool
from execution.registry import ToolRegistry

registry = ToolRegistry()
registry.register(MyTool())
```

---

## Migration from Custom Agents

### Converting Custom Agents

**Before (Custom):**
```python
class MyAgent:
    def process(self, task):
        # Custom logic
        return result
```

**After (MCP Agent):**
```python
from agents.base import BaseAgent, AgentProfile

class MyAgent(BaseAgent):
    profile = AgentProfile(
        name="my_agent",
        description="My custom agent",
        capabilities=["custom_task"],
        permissions=["tools:execute"]
    )
    
    async def execute(self, task, context=None):
        # Agent logic
        return {"result": "done"}
```

### Using Agent Profiles

```python
from agents.profiles.code_agent import CodeAgentProfile

profile = CodeAgentProfile()
agent = BaseAgent(profile=profile)
```

---

## Data Migration

### Database Migration

#### PostgreSQL/pgvector

```bash
# Backup existing data
pg_dump -h localhost -U mcp_user mcp_db > mcp_backup.sql

# Run migration scripts
python scripts/migrate_database.py --from v0.9 --to v1.0

# Verify
python scripts/verify_migration.py
```

#### Memory Namespace Migration

```bash
# Migrate memory namespaces
python -c "
from memory.longterm import LongTermMemory

# Old namespace
old_ltm = LongTermMemory(namespace='legacy')
memories = old_ltm.get_all()

# New namespace
new_ltm = LongTermMemory(namespace='mcp_v1')
for mem in memories:
    new_ltm.store(mem)
"
```

### Configuration Migration

**Old (.env):**
```bash
ADAPTER_MODE=legacy
FILE_ADAPTER_ENABLED=true
```

**New (.env):**
```bash
MCP_ENV=production
TOOL_DEFAULT_TIMEOUT=30
SECURITY_JWT_SECRET=xxx
```

---

## Rollback Procedures

### If Migration Fails

1. **Stop Services:**
```bash
sudo systemctl stop mcp-unified
```

2. **Restore Database:**
```bash
psql -h localhost -U mcp_user mcp_db < mcp_backup.sql
```

3. **Restore Configuration:**
```bash
cp .env.backup .env
```

4. **Restart Previous Version:**
```bash
cd /opt/mcp-unified-legacy
./run.sh
```

---

## Pre-Migration Checklist

- [ ] Backup database
- [ ] Backup configuration files
- [ ] Test migration in staging environment
- [ ] Prepare rollback plan
- [ ] Notify users of maintenance window
- [ ] Verify all integrations work post-migration

## Post-Migration Checklist

- [ ] Verify all tools execute correctly
- [ ] Check agent functionality
- [ ] Validate security settings
- [ ] Run integration tests
- [ ] Monitor logs for errors
- [ ] Update documentation

---

## Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'adapters'`
**Solution:** Update imports to use new module paths (tools.* instead of adapters.*)

**Issue:** `AttributeError: 'WorkspaceAdapter' has no attribute 'set_workspace'`
**Solution:** Use `environment.workspace.WorkspaceManager` instead

**Issue:** Tool execution fails with permission error
**Solution:** Check RBAC permissions and API key roles

**Issue:** Database connection fails after migration
**Solution:** Verify connection string format and credentials

---

## Version Compatibility

| MCP Version | Migration Path | Status |
|-------------|----------------|--------|
| v0.8.x | Direct to v1.0 | ✅ Supported |
| v0.9.x | Direct to v1.0 | ✅ Supported |
| v1.0.0 | Current | ✅ Current |

---

## Support

For migration assistance:
- Check troubleshooting section above
- Review architecture docs: `docs/02-architecture/`
- Contact: mcp-support@example.com
