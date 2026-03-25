# Discovery & Portability Design Document

## Overview

Dokumen ini merancang mekanisme agar **agent baru di folder manapun bisa langsung**:
1. ✅ Menemukan MCP Hub tanpa setup manual
2. ✅ Mengetahui tools yang tersedia
3. ✅ Mendapatkan konteks relevan dari project

**Problem Statement:**
> ">15 menit terbuang setiap sesi untuk jelaskan konteks ke agent"

**Goal:**
> "0 setup time — agent langsung productive"

---

## Pain Points Analysis

| Pain Point | Current State | Target State |
|------------|---------------|--------------|
| Setup time | >15 menit per sesi | 0 menit (auto-discover) |
| Context loss | Tiap sesi mulai dari nol | Konteks otomatis carry-over |
| Project awareness | Agent clueless tentang struktur | Auto-load project context |
| Tool discovery | Manual configuration | Auto-discovery tools |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DISCOVERY & PORTABILITY                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────┐  │
│  │   ANY FOLDER     │      │   MCP HUB        │      │  MEMORY      │  │
│  │   (Agent)        │      │   (/home/aseps)  │      │  (PostgreSQL)│  │
│  └────────┬─────────┘      └────────┬─────────┘      └──────────────┘  │
│           │                         │                                    │
│           │  1. Discovery           │                                    │
│           │  ─────────────────────>│                                    │
│           │  (Find .mcp marker)     │                                    │
│           │                         │                                    │
│           │  2. Connect             │                                    │
│           │  ─────────────────────>│                                    │
│           │  (Portable Client)      │                                    │
│           │                         │                                    │
│           │  3. Context Injection   │      ┌──────────────────────┐   │
│           │  <──────────────────────│<─────│  Load namespace:     │   │
│           │  (Project context)      │      │  /project/workspace  │   │
│           │                         │      └──────────────────────┘   │
│           │  4. Ready to Work       │                                    │
│           │  <──────────────────────│                                    │
│           │  (Tools + Context)      │                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Discovery Service

### Mekanisme: Hierarchical Discovery

Agent akan mencari MCP Hub dengan urutan:

```python
# Discovery priority (highest to lowest)
DISCOVERY_CHAIN = [
    # 1. Environment variable (explicit override)
    "MCP_HUB_PATH",
    
    # 2. Local marker file (current project)
    "./.mcp/config.json",
    
    # 3. Parent directories (up to /home)
    "../.mcp/config.json",
    "../../.mcp/config.json",
    "../../../.mcp/config.json",
    
    # 4. User home directory
    "~/.mcp/hub.json",
    
    # 5. Well-known location
    "/home/aseps/MCP/.mcp-hub",
]
```

### Marker File Format

```json
{
  "version": "1.0.0",
  "hub_path": "/home/aseps/MCP",
  "server": {
    "host": "localhost",
    "port": 8080,
    "protocol": "stdio"
  },
  "discovery": {
    "enabled": true,
    "auto_connect": true
  },
  "context": {
    "auto_load": true,
    "namespace_detection": "auto"
  }
}
```

---

## 2. Portable Client

### Universal MCP Client

File: `shared/mcp_client.py`

```python
"""
Universal MCP Client for Personal MCP Hub
Usage: Import and use immediately — no setup required
"""

class PortableMCPClient:
    """
    Auto-discovering, zero-config MCP client.
    
    Features:
    - Auto-discovers MCP Hub location
    - Auto-detects project namespace
    - Auto-injects context on connect
    - Unified interface for all tools
    """
    
    def __init__(self):
        self.hub_path = None
        self.namespace = None
        self.tools = []
        self._discover()
    
    def _discover(self):
        """Auto-discover MCP Hub location."""
        # Implementation: Try DISCOVERY_CHAIN
        pass
    
    def _detect_namespace(self):
        """Auto-detect project namespace from current directory."""
        # Implementation: Map folder to namespace
        pass
    
    async def get_context(self) -> dict:
        """Get project context from memory."""
        # Returns: project structure, recent memories, active tasks
        pass
    
    async def use_tool(self, tool_name: str, **kwargs):
        """Execute a tool with automatic context."""
        # Auto-inject namespace if needed
        pass
```

### Usage Examples

```python
# Example 1: Zero-config usage
from shared.mcp_client import PortableMCPClient

client = PortableMCPClient()  # Auto-discovers everything
context = await client.get_context()  # Gets project context
result = await client.use_tool("memory_search", query="database schema")
```

```python
# Example 2: File operations with auto-namespace
client = PortableMCPClient()
await client.use_tool("write_file", 
    path="./README.md", 
    content="# Project Overview")
# Automatically saves to correct namespace
```

---

## 3. Context Injector

### Namespace Detection

```python
# Namespace detection strategies
NAMESPACE_DETECTION = {
    "git_repo": "Use git remote URL as namespace",
    "folder_name": "Use folder name as namespace",
    "explicit": "Use .mcp/namespace file",
    "parent_chain": "Walk up to find .mcp marker",
}
```

### Context Bundle

Saat agent connect, sistem mengirimkan:

```json
{
  "context_bundle": {
    "project": {
      "name": "mcp-unified",
      "path": "/home/aseps/MCP/mcp-unified",
      "namespace": "mcp_unified",
      "git_branch": "main"
    },
    "memory": {
      "recent_searches": [...],
      "key_decisions": [...],
      "active_tasks": [...]
    },
    "tools": {
      "available": ["memory_save", "memory_search", "read_file", ...],
      "frequently_used": ["memory_search", "read_file"]
    },
    "workspace": {
      "structure": {...},
      "recent_files": [...],
      "open_tasks": [...]
    }
  }
}
```

---

## Implementation Phases

### Phase 1: Discovery Foundation
- [ ] Create `.mcp-hub` marker file
- [ ] Implement discovery chain logic
- [ ] Create `shared/mcp_client.py` skeleton

### Phase 2: Portable Client
- [ ] Implement auto-discovery
- [ ] Implement namespace detection
- [ ] Connect to MCP server via stdio

### Phase 3: Context Injection
- [ ] Create context bundle builder
- [ ] Implement auto-context loading
- [ ] Add project structure detection

### Phase 4: Integration
- [ ] Update documentation
- [ ] Create usage examples
- [ ] Add tests

---

## File Structure

```
/home/aseps/MCP/
├── .mcp-hub                          # Marker file for discovery
│
├── shared/
│   ├── mcp_client.py                # Portable client (NEW)
│   ├── discovery.py                 # Discovery logic (NEW)
│   └── context_injector.py          # Context injection (NEW)
│
├── mcp-unified/
│   ├── server/
│   │   └── context_bundle.py        # Context bundle builder (NEW)
│   └── ...
│
└── docs/
    └── DISCOVERY_PORTABILITY_DESIGN.md  # This document
```

---

## Success Metrics

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Setup time | >15 min | <30 sec | Time to first productive command |
| Context recall | 0% | 90%+ | Agent knows project structure |
| Tool discovery | Manual | Auto | `list_tools()` on connect |
| Namespace accuracy | N/A | 95%+ | Correct context loaded |

---

## Next Steps

1. **Approve design** — Review dan revisi jika diperlukan
2. **Implement Phase 1** — Discovery foundation
3. **Test portability** — Agent di folder berbeda
4. **Iterate** — Improve berdasarkan feedback

---

*Document Version: 1.0*
*Created: 2026-02-19*
*Phase: Discovery Complete → Ready for Implementation*
