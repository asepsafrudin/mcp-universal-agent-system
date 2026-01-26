# MCP Subagents System

A high-performance Agentic MCP Server capable of decomposing complex tasks, creating execution plans, and orchestrating specialized sub-agents (File, Code, Terminal, Search) to complete objectives autonomously.

## Capabilities

- **Task Decomposition**: Breaks down vague user requests into actionable subtasks.
- **Autonomous Execution**: Uses specialized agents to execute file operations, code analysis, and terminal commands.
- **Execution Scheduler**: Manages dependencies between subtasks (e.g., "Read file A before modifying file B").
- **Safety First**: Includes `RiskClassifier` and `SandboxManager` (simulated) to prevent destructive actions without approval.

## Installation & Usage

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Server**
   ```bash
   python server.py
   ```

3. **Configure MCP Client (Antigravity IDE)**
   Add the following to your MCP settings file:
   ```json
   {
     "mcpServers": {
       "mcp-subagent-system": {
         "url": "http://localhost:8001"
       }
     }
   }
   ```

## Available Tools

### `execute_task`
Submits a high-level task to the system. The system will plan and execute it.
- **Input**: `task_content` (string)
- **Example**: "Audit the src directory and create a report of all security vulnerabilities."

### `get_system_health`
Returns the status of all internal components (scheduler, memory, context keys).

## Architecture

- **MCPCoordinator**: Entry point, manages the lifecycle of a request.
- **PlanningEngine**: Analyzes requests and generates `ExecutionPlan`.
- **ExecutionScheduler**: Routes subtasks to specific agents (`CodeAgent`, `FileAgent`, etc.).
- **Agents**: Specialized workers that perform the actual work.

## Detailed Workflow

### 1. Request Entry Point
When a task is submitted via `execute_task`:
```
User Request → MCPCoordinator.executePlan()
```
The coordinator receives the high-level task and begins orchestration.

### 2. Context Preparation
The system builds a **MultiLayerContext** containing:

| Context Layer | Purpose | Data |
|---------------|---------|------|
| **User Memory** | Tracks user patterns and preferences | Usage statistics, interaction history, learned patterns |
| **Project Context** | Understands codebase structure | File structure, dependencies, architecture |
| **Code Context** | Analyzes code elements | Functions, classes, imports, code patterns |
| **Task History** | Learns from past executions | Completed/failed tasks, performance metrics |
| **Merged Context** | Compressed knowledge representation | Embeddings for AI reasoning |

### 3. Task Planning Phase
**PlanningEngine** processes the request:

```
Request Analysis
    ↓
Task Decomposition → Break into SubTasks
    ↓
Dependency Analysis → Build dependency graph
    ↓
Risk Assessment → Classify risks
    ↓
Execution Plan (with priority order)
```

**Outputs:**
- `subtasks[]`: Array of atomic actions
- `dependencies`: Graph showing task ordering
- `estimatedTotalTime`: Projected execution duration
- `riskAssessment`: Security & safety evaluation

### 4. Agent Discovery & Registration
**MCPCoordinator** discovers available agents:
- **FileAgent**: Read, write, search, delete file operations
- **CodeAgent**: Code analysis, refactoring, pattern detection
- **TerminalAgent**: Execute system commands safely
- **SearchAgent**: Information retrieval and semantic search

Each agent registers capabilities and constraints with **AgentRegistryManager**.

### 5. Execution Scheduling
**ExecutionScheduler** orchestrates execution:

```
Execution Plan
    ↓
Dependency Resolution → Determine execution order
    ↓
Task Queue Management → Parallel where possible
    ↓
Agent Assignment → Route to appropriate agent
    ↓
Execution with Monitoring → Track progress
    ↓
Result Aggregation → Combine outputs
```

**Key Features:**
- Respects dependency constraints
- Executes independent tasks in parallel
- Monitors progress in real-time
- Handles failures gracefully

### 6. Specialized Agent Execution

#### FileAgent Operations
```typescript
Operations: read | write | search | delete
Input: { filePath, content?, pattern? }
Output: File contents or operation status
Security: Path validation, access checks
```

#### CodeAgent Operations
```typescript
Operations: analyze | refactor | search | validate
Input: { code, language, rules? }
Output: Analysis results, refactored code, issues
Features: Pattern detection, best practice validation
```

#### TerminalAgent Operations
```typescript
Operations: execute | validate | preview
Input: { command, cwd?, env? }
Output: Command output, exit code
Safety: Command whitelisting, sandboxing
```

#### SearchAgent Operations
```typescript
Operations: query | semantic | file-search
Input: { query, scope, filters? }
Output: Matched results with relevance scores
Features: Semantic similarity, embedding-based search
```

### 7. Risk Classification
Before execution, **RiskClassifier** evaluates:

| Risk Factor | Assessment | Action |
|------------|-----------|--------|
| **High-Risk Operations** | Delete, destructive writes | Requires confirmation |
| **Sensitive Paths** | System directories, configs | Restricted access |
| **Command Execution** | Arbitrary commands | Validation + sandboxing |
| **Security Implications** | Auth exposure, data access | Audit logging |

### 8. Sandbox Management
**SandboxManager** (simulated) provides:
- Execution isolation
- Resource limits
- Rollback capability
- Audit trail

### 9. Result Aggregation
**ResultAggregator** combines all subtask results:

```
SubTask Results[]
    ↓
Merge Outputs → Consolidate data
    ↓
Cross-Reference → Link dependencies
    ↓
Format Response → Prepare for user
    ↓
Final TaskResponse
```

### 10. Memory & Feedback
**MemoryManager** stores:
- Task outcomes
- Agent performance metrics
- Patterns and insights
- Context embeddings

**FeedbackHandler** processes:
- Execution success/failures
- User feedback
- Performance metrics
- Optimization opportunities

## Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Request                             │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              MCPCoordinator (Orchestrator)                   │
├─────────────────────────────────────────────────────────────┤
│ • Manages request lifecycle                                  │
│ • Coordinates all components                                 │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┬──────────────┐
        ↓                               ↓              ↓
┌──────────────────┐      ┌──────────────────┐  ┌────────────┐
│ ContextManager   │      │ PlanningEngine   │  │ Validators │
├──────────────────┤      ├──────────────────┤  ├────────────┤
│ • Build context  │      │ • Decompose task │  │ • Security │
│ • Merge layers   │      │ • Build graph    │  │ • Syntax   │
│ • Embeddings     │      │ • Assess risks   │  │ • Logic    │
└──────────────────┘      └────────┬─────────┘  └────────────┘
                                   ↓
                        ┌─────────────────────┐
                        │  ExecutionPlan      │
                        ├─────────────────────┤
                        │ • SubTasks[]        │
                        │ • Dependencies      │
                        │ • RiskAssessment    │
                        └────────────┬────────┘
                                     ↓
┌────────────────────────────────────────────────────────────┐
│          ExecutionScheduler (Dependency Resolver)          │
├────────────────────────────────────────────────────────────┤
│ • Resolve dependencies                                     │
│ • Schedule parallel execution                              │
│ • Route to appropriate agents                              │
└───┬──────────┬─────────┬────────────┬───────────────┬──────┘
    ↓          ↓         ↓            ↓               ↓
┌─────────┐┌──────────┐┌──────────┐┌────────────┐┌──────────┐
│FileAgent││CodeAgent ││Terminal  ││SearchAgent ││RiskClass │
│         ││          ││Agent     ││            ││ifier     │
├─────────┤├──────────┤├──────────┤├────────────┤├──────────┤
│FS Ops   ││Analysis  ││Execute   ││Query       ││Evaluate  │
│Read/Wri ││Refactor  ││Commands  ││Search      ││Safety    │
│Delete   ││Pattern   ││Sandbox   ││Semantic    ││Risks     │
└────┬────┘└────┬─────┘└────┬─────┘└────────┬───┘└──────────┘
     │          │           │              │
     └──────────┴───────────┴──────────────┘
                     ↓
        ┌────────────────────────┐
        │ ResultAggregator       │
        ├────────────────────────┤
        │ • Merge results        │
        │ • Cross-reference      │
        │ • Format response      │
        └───────────┬────────────┘
                    ↓
        ┌────────────────────────┐
        │ FeedbackHandler        │
        ├────────────────────────┤
        │ • Log execution        │
        │ • Update metrics       │
        │ • Store learnings      │
        └───────────┬────────────┘
                    ↓
        ┌────────────────────────┐
        │ MemoryManager          │
        ├────────────────────────┤
        │ • Cache results        │
        │ • Update embeddings    │
        │ • Persist learnings    │
        └────────────┬───────────┘
                     ↓
        ┌────────────────────────┐
        │  Final TaskResponse    │
        ├────────────────────────┤
        │ • Results from agents  │
        │ • Execution metrics    │
        │ • Risk assessments     │
        └────────────┬───────────┘
                     ↓
              User Response
```

## Task Status Lifecycle

Each subtask follows this status progression:

```
PENDING → SCHEDULED → IN_PROGRESS → COMPLETED/FAILED → ARCHIVED
   ↑                                          ↓
   └──────── RETRY (on failure) ─────────────┘
```

**Status Definitions:**
- **PENDING**: Waiting for dependencies to complete
- **SCHEDULED**: Assigned to agent, ready to execute
- **IN_PROGRESS**: Currently executing
- **COMPLETED**: Successfully finished
- **FAILED**: Execution error (eligible for retry)
- **ARCHIVED**: Result stored in memory

## Example Workflow: Code Audit Task

### User Request
```
"Audit the src directory and create a security report"
```

### System Decomposition
The PlanningEngine breaks this into:

| SubTask | Type | Operation | Dependencies |
|---------|------|-----------|--------------|
| 1 | FileAgent | search | None |
| 2 | CodeAgent | analyze | Task 1 |
| 3 | TerminalAgent | execute | Task 2 |
| 4 | FileAgent | write | Task 3 |

### Execution Flow
```
Task 1: Find all .ts files in src/
    ↓ (wait for completion)
Task 2: Analyze files for security issues (parallel: 4 files at once)
    ↓ (wait for completion)
Task 3: Generate report with statistics (run linter)
    ↓ (wait for completion)
Task 4: Write report to disk
    ↓ (complete)
Return aggregated report
```

### Context Usage
- **User Memory**: Recall previous audit preferences
- **Project Context**: Understand directory structure
- **Code Context**: Recognize patterns and anti-patterns
- **Task History**: Apply learnings from previous audits

## Performance Optimization

### Parallelization
- Independent subtasks execute concurrently
- Dependency graph ensures correct ordering
- I/O operations are non-blocking

### Caching
- Frequently accessed files cached
- Embedding results reused
- Context embeddings persist

### Learning
- Performance metrics tracked per agent
- Patterns detected for optimization
- Execution times improve over time
