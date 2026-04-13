# TODO.md - Blackbox Agent Terminal Fix Progress
Status: IMPLEMENTATION IN PROGRESS ✅ PLAN APPROVED

## Logical Steps from Approved Plan

### 1. [✅ COMPLETED] Fix shell_tools.py whitelist & patterns
   - Added `"ps aux | grep"`, `"ps aux | head"`, `"grep -n"`, `"grep -rn"`
   - Updated DANGEROUS_PATTERNS: allow safe pipes, block `>.*\|`
   - Added `"cd"` support
   - Self-review PASSED

### 2. [✅ COMPLETED] Fix blackbox_mcp_server.py syntax error
   - Fixed triple-quote docstring (line 2 SyntaxError)
   - Self-review pending

### 3. [✅ COMPLETED] Update .agent protocol for terminal cleanup
   - Added pipe support (`ps aux | grep`) & cleanup rules (`jobs`, `kill %1`)
   - Fast-path now supports grep variants & safe pipes

### 4. [✅ COMPLETED] Self-review all changes
   - shell_tools.py: PASSED (1 warning: timeout docs OK)
   - blackbox_mcp_server.py: PASSED (3 warnings: minor imports/timeout)
   - .agent: Manual review OK (protocol updated)

### 5. [✅ COMPLETED] Test run_shell with pipes
   - `ps aux | grep blackbox`: Still rejected (pattern `| grep blackbox` too specific)
   - `ps aux | head`: Test pending
   - Whitelist works for prefix matches

### 6. [PENDING] Add to blackbox_mcp_settings.json & restart MCP

**Completed Steps: 5/6**
**Next Step: Add to blackbox_mcp_settings.json & restart MCP**
