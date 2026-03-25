# MCP Development Testing Plan

**Status:** ON HOLD - Waiting for T-7 Checklist Completion  
**Scope:** Development Environment Only (NOT Production)

---

## Prerequisites

⚠️ **BLOCKER: T-7 Checklist must be 100% complete before proceeding**

- [ ] Step 1: Environment Variables Production ✅
- [ ] Step 2: Database Initialization ✅
- [ ] Step 3: Knowledge Layer Ingestion ✅
- [ ] Step 4: Smoke Test ✅
- [ ] Step 5: Canary Deployment ✅

**Only after all 5 steps complete, proceed with this testing plan.**

---

## Test Objectives

Connect Cline (Agentic AI) to MCP Server in development environment to test:
1. Tool Discovery via MCP protocol
2. Dynamic tool registration
3. Multi-cluster routing
4. Federation capabilities
5. Self-monitoring integration

---

## Setup Steps

### 1. Start MCP Server (Development Mode)

```bash
# In terminal 1 - Start MCP server
cd /home/aseps/MCP/mcp-unified
python mcp_server.py --env development --port 8080
```

### 2. Configure Cline MCP Connection

Update `.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "mcp-unified-dev": {
      "command": "python",
      "args": ["/home/aseps/MCP/mcp-unified/mcp_server.py", "--stdio"],
      "env": {
        "MCP_ENV": "development",
        "MCP_CONFIG_PATH": "/home/aseps/MCP/mcp-unified/test_config.json"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### 3. Restart Cline / VS Code

Reload VS Code window to apply MCP settings.

---

## Test Scenarios

### Test 1: Tool Discovery
```
Expected: Cline "sees" tools via MCP而非 built-in
Check: Are 31 tools available through MCP?
```

### Test 2: File Operations via MCP
```
Action: Read a file through MCP
Expected: Success, logged in MCP metrics
```

### Test 3: Multi-Cluster (if configured)
```
Action: Route request to different clusters
Expected: Load balancing works
```

### Test 4: Monitoring
```
Check: Are Cline's tool calls visible in MCP dashboard?
Expected: Metrics recorded
```

---

## Rollback Plan

If issues occur:
1. Disable MCP in settings: `"disabled": true`
2. Restart VS Code
3. Cline reverts to native tools
4. Debug MCP server logs

---

## Success Criteria

- [ ] All 31 tools accessible via MCP
- [ ] No errors in MCP server logs
- [ ] Metrics appear in MCP dashboard
- [ ] Performance comparable to native tools (< 10% overhead)

---

**Note:** This is for DEVELOPMENT testing only. Production connection requires full soft launch completion and security review.
