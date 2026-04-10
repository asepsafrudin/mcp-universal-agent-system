# TASK-045: Agent Onboarding Documentation

## Quick Start for New Agents

### 1. Runtime Context
```
Read: /tasks/workspace/TASK-0XX/ENV_CONTEXT.md
MCP: access_mcp_resource(\"mcp-unified\", \"file:///system/config\")
```

### 2. Services
```
Read: /tasks/workspace/TASK-040/SERVICES_REGISTRY.md
MCP: scheduler_get_status()
```

### 3. Task Flow
```
1. List tasks: cat /home/aseps/MCP/TODO.md
2. Claim: touch tasks/workspace/TASK-0XX/CLAIMED_BY_AGENT.md
3. Work → Update status in TASK-0XX file  
4. Complete: Edit status → ✅ COMPLETED
```

### 4. Debugging & Observability
Gunakan resource dinamis untuk memantau task active:
- **Log Agent:** `mcp://openhands/task/logs?task_id=XYZ`
- **Status JSON:** `mcp://openhands/task/status?task_id=XYZ`

### 5. MCP Tools
```
memory_search(query=\"task progress\")
use_mcp_tool(\"mcp-unified\", \"scheduler_list_jobs\")
```

## Success Pattern
✅ TASK-039→045 → All OpenHands MCP integration COMPLETE

*Onboarding ready for production agents.*
