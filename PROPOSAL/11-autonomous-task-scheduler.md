# 11 - Autonomous Task Scheduler

**MCP Unified Server - Autonomous Job Scheduling System**

---

## Executive Summary

Dokumen ini merinci implementasi Autonomous Task Scheduler untuk MCP Unified Server, memungkinkan eksekusi tugas terjadwal secara otomatis dengan integrasi penuh terhadap komponen existing (LTM, Planner, Self-Healing, dan Tool Registry).

---

## 1. Architecture Overview

### 1.1 System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    WSL UBUNTU (Native Server)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐     ┌─────────────────┐                   │
│  │  SCHEDULER      │────▶│  MCP SERVER     │                   │
│  │  (Systemd/Cron) │     │  (Native)       │                   │
│  │                 │     │  • File tools   │                   │
│  │  • Cron job     │     │  • Shell tools  │                   │
│  │  • Systemd timer│     │  • Memory (LTM) │                   │
│  │  • Queue worker │     │  • Planner      │                   │
│  │                 │     │  • Self-healing │                   │
│  └─────────────────┘     └─────────────────┘                   │
│           │                        │                            │
│           │              ┌─────────┴─────────┐                  │
│           │              │                   │                  │
│           │         ┌────▼────┐       ┌────▼────┐             │
│           │         │PostgreSQL│       │  Redis  │             │
│           │         │+ pgvector│       │ (Queue) │             │
│           │         │+ Jobs DB│       └─────────┘             │
│           │         └─────────┘                               │
│           │                                                    │
│           └───────────────────────────────────────────────┐   │
│                                                             │   │
│  ┌────────────────────────────────────────────────────────┐│   │
│  │  AUTONOMOUS EXECUTOR (Python Service)                  ││   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││   │
│  │  │  Job 1:     │  │  Job 2:     │  │  Job 3:     │    ││   │
│  │  │  Daily      │  │  Hourly     │  │  Event-     │    ││   │
│  │  │  backup     │  │  health     │  │  driven     │    ││   │
│  │  │  @ 02:00    │  │  check      │  │  deploy     │    ││   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    ││   │
│  │                                                         ││   │
│  │  Flow:                                                  ││   │
│  │  1. Scheduler trigger                                   ││   │
│  │  2. Load context dari LTM                               ││   │
│  │  3. Planner buat execution plan                       ││   │
│  │  4. Execute via MCP tools                               ││   │
│  │  5. Self-healing kalau error                            ││   │
│  │  6. Save result ke LTM                                  ││   │
│  └────────────────────────────────────────────────────────┘│   │
│                                                            │   │
└────────────────────────────────────────────────────────────┘   │
│                                                                 │
┌─────────────────────────────────────────────────────────────┐  │
│  VS CODE (Opsional - Monitoring Only)                        │  │
│  • View logs via SSH/WSL                                    │  │
│  • Manual override kalau perlu                              │  │
│  • Notifikasi ke desktop (Webhook/Discord/Slack)            │  │
└─────────────────────────────────────────────────────────────┘  │
```

### 1.2 Integration dengan Komponen Existing

| Komponen | Integration Point | Usage |
|----------|-------------------|-------|
| **LTM (PostgreSQL+pgvector)** | `memory/longterm.py` | Load context, save execution history |
| **Planner** | `intelligence/planner.py` | Generate execution plan untuk autonomous tasks |
| **Self-Healing** | `intelligence/self_healing.py` | Auto-fix pada execution failure |
| **Tool Registry** | `execution/registry.py` | Execute scheduled tasks via registered tools |
| **Redis** | `memory/working.py` | Hot queue untuk pending/running jobs |
| **Message Queue** | `messaging/queue_client.py` | Distributed job execution |
| **Telegram** | `integrations/telegram/` | Notifications |

---

## 2. Job Type Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    JOB TYPE HIERARCHY                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔧 SYSTEM MAINTENANCE (Critical - High Priority)               │
│  ├── backup_full          # Daily 02:00 - Full system backup    │
│  ├── backup_incremental   # Every 6h - Incremental files        │
│  ├── db_vacuum            # Weekly - PostgreSQL maintenance     │
│  ├── log_rotate           # Daily - Compress & archive logs     │
│  ├── disk_cleanup         # When disk >80% - Auto cleanup       │
│  └── cert_renewal         # Monthly - SSL cert check/renew      │
│                                                                 │
│  📊 MONITORING & REPORTING (Scheduled - Medium Priority)        │
│  ├── health_check         # Every 15m - System health snapshot  │
│  ├── compliance_scan      # Daily 09:00 - Security audit        │
│  ├── dependency_check     # Weekly - Outdated packages          │
│  ├── performance_report   # Daily 08:00 - Metrics summary       │
│  └── cost_analysis        # Monthly - Resource usage report     │
│                                                                 │
│  🔄 SYNC & REPLICATION (Event-driven - Variable Priority)       │
│  ├── git_sync_upstream    # On push - Auto sync forks           │
│  ├── mirror_repos         # Every 4h - Code mirror to backup    │
│  ├── sync_staging_prod    # On approval - Deploy pipeline       │
│  └── ltm_sync_remote      # Real-time - Distributed LTM sync    │
│                                                                 │
│  🤖 AUTONOMOUS TASKS (AI-driven - Context Priority)             │
│  ├── auto_heal_review     # On error - Analyze & fix patterns   │
│  ├── smart_cleanup        # Weekly - AI-suggested cleanup       │
│  ├── doc_auto_update      # On code change - Update docs        │
│  └── test_auto_gen        # On commit - Generate missing tests  │
│                                                                 │
│  🚨 ALERT & RESPONSE (Trigger-based - Highest Priority)         │
│  ├── incident_response    # On alert - Auto remediation         │
│  ├── failover_trigger     # On health fail - Switch to standby  │
│  └── escalation_notify    # On failure - Human escalation       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Persistence Architecture

### 3.1 Two-Layer Storage

```
┌─────────────────────────────────────────────────────────────────┐
│              PERSISTENCE ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 1: REDIS (Hot Queue - Runtime State)                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Key: mcp:queue:pending                                 │   │
│  │  Type: Sorted Set (by priority + timestamp)             │   │
│  │  Value: job_id, priority, scheduled_time                │   │
│  │                                                         │   │
│  │  Key: mcp:queue:running                                 │   │
│  │  Type: Hash                                             │   │
│  │  Value: job_id, started_at, worker_id, timeout          │   │
│  │                                                         │   │
│  │  Key: mcp:queue:locks:{job_type}                        │   │
│  │  Type: String (TTL = job timeout)                       │   │
│  │  Value: job_id (for exclusive jobs)                     │   │
│  │                                                         │   │
│  │  Key: mcp:scheduler:heartbeat                           │   │
│  │  Type: String                                           │   │
│  │  Value: last_tick_timestamp (watchdog)                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  LAYER 2: POSTGRESQL (Cold Storage - Audit & Recovery)          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Table: scheduler_jobs                                  │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │  id | name | type | status | created_at | started_at    │   │
│  │  completed_at | result | retry_count | error_log        │   │
│  │  execution_plan | context_used | worker_node            │   │
│  │                                                         │   │
│  │  Table: scheduler_job_definitions                       │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │  id | name | cron | type | enabled | last_run | next_run│   │
│  │  config_json | created_by | updated_at                  │   │
│  │                                                         │   │
│  │  Table: scheduler_notifications                         │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │  id | job_id | channel | status | sent_at | content     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  RECOVERY SCENARIO:                                             │
│  1. Scheduler crash → Redis data lost                           │
│  2. On restart → Query PostgreSQL: jobs with status 'running'   │
│  3. Re-queue jobs yang belum completed                          │
│  4. Resume dari last known state                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Database Schema

```sql
-- Job Definitions (Cold Storage)
CREATE TABLE IF NOT EXISTS scheduler_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    job_type TEXT NOT NULL,
    category TEXT NOT NULL,
    priority INTEGER DEFAULT 50 CHECK (priority >= 0 AND priority <= 100),
    schedule_type TEXT NOT NULL,
    schedule_expr TEXT NOT NULL,
    timezone TEXT DEFAULT 'Asia/Jakarta',
    task_config JSONB NOT NULL DEFAULT '{}',
    namespace TEXT DEFAULT 'default',
    max_concurrent INTEGER DEFAULT 1,
    exclusive_lock BOOLEAN DEFAULT false,
    worker_pool TEXT DEFAULT 'default',
    is_enabled BOOLEAN DEFAULT true,
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    last_run_status TEXT,
    last_run_output JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 300,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    UNIQUE(name, namespace)
);

-- Execution History
CREATE TABLE IF NOT EXISTS scheduler_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES scheduler_jobs(id) ON DELETE CASCADE,
    job_name TEXT NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    status TEXT NOT NULL,
    exit_code INTEGER,
    output JSONB,
    error_message TEXT,
    execution_plan JSONB,
    context_used JSONB,
    ltm_references JSONB,
    worker_node TEXT,
    recovery_attempts INTEGER DEFAULT 0,
    original_execution_id UUID REFERENCES scheduler_executions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notifications Log
CREATE TABLE IF NOT EXISTS scheduler_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES scheduler_jobs(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES scheduler_executions(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    notification_type TEXT NOT NULL,
    status TEXT NOT NULL,
    content JSONB NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Concurrency Management

### 4.1 Concurrency Pool Manager

```
┌─────────────────────────────────────────────────────────────────┐
│              CONCURRENCY POOL MANAGER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GLOBAL LIMITS:                                                 │
│  ├── Max concurrent jobs: 5 (default)                           │
│  ├── Max per job type:                                          │
│  │   ├── backup: 1 (exclusive - no parallel backup)             │
│  │   ├── monitoring: 3 (can parallel different checks)          │
│  │   ├── autonomous: 2 (resource intensive)                     │
│  │   └── sync: 2 (network limited)                              │
│  └── Max per priority:                                          │
│      ├── Critical (90-100): Unlimited (interrupt others)        │
│      ├── High (70-89): 3 slots                                  │
│      ├── Medium (40-69): 2 slots                                │
│      └── Low (0-39): 1 slot (background only)                   │
│                                                                 │
│  PREEMPTION RULES:                                              │
│  1. Critical job arrives → Pause lowest priority running job    │
│  2. Backup starts → Pause non-essential jobs (resume after)     │
│  3. Same-type exclusive → Queue (FIFO)                          │
│                                                                 │
│  WORKER POOLS:                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ CPU Pool    │  │ IO Pool     │  │ Network Pool│             │
│  │ (2 workers) │  │ (3 workers) │  │ (2 workers) │             │
│  │             │  │             │  │             │             │
│  │ autonomous  │  │ backup      │  │ sync        │             │
│  │ compliance  │  │ log_rotate  │  │ git_sync    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Directory Structure

```
mcp-unified/
├── scheduler/                    # Autonomous Scheduler Module
│   ├── __init__.py
│   ├── config.py                # Scheduler configuration
│   ├── database.py              # SQL schema & DB operations
│   ├── executor.py              # Core job execution engine
│   ├── manager.py               # Job CRUD & lifecycle
│   ├── queue.py                 # Redis queue management
│   ├── pools.py                 # Concurrency pool manager
│   ├── daemon.py                # Main scheduler daemon
│   ├── templates.py             # Job type definitions
│   ├── notifier.py              # Telegram + VS Code notifications
│   ├── recovery.py              # Crash recovery logic
│   └── tools.py                 # MCP tools for scheduler
│
├── systemd/                      # Systemd files
│   ├── mcp-scheduler.service
│   └── mcp-scheduler.timer
│
└── ...existing modules...
```

---

## 6. Implementation Status

### ✅ Phase 1: Core Infrastructure (COMPLETE)
- [x] Database schema implementation (`scheduler/database.py`)
- [x] Job templates definition (`scheduler/templates.py`) - 20+ templates
- [x] Concurrency pool manager (`scheduler/pools.py`)
- [x] Redis queue integration (`scheduler/queue.py`)

### ✅ Phase 2: Execution Engine (COMPLETE)
- [x] Job executor with LTM integration (`scheduler/executor.py`)
- [x] Self-healing integration (`PracticalSelfHealing`)
- [x] Recovery mechanism (`scheduler/recovery.py`)
- [x] Notification system (`scheduler/notifier.py`)

### ✅ Phase 3: Integration (COMPLETE)
- [x] MCP tools registration (`scheduler/tools.py`) - 10 tools
- [x] Integration with `mcp_server.py` (server initialization)

### ⏳ Phase 4: Deployment & Testing
- [ ] Systemd service setup
- [ ] API endpoints (REST/WebSocket)
- [ ] Extended test coverage

### 📊 Deliverables Summary
- **10 Python modules** (~4,800 lines)
- **20+ job templates** across 5 categories
- **7/7 core tests PASSED**
- **Fully integrated** dengan MCP server

---

## 7. Notification Channels

- **Telegram**: Status updates, failures, completions
- **VS Code**: Webhook notifications untuk IDE integration

---

## Related Documents

- [02-architecture-overview.md](02-architecture-overview.md) - Base architecture
- [03-core-components.md](03-core-components.md) - Core components detail
- [06-agents-layer.md](06-agents-layer.md) - Agent definitions
- [09-roadmap.md](09-roadmap.md) - Implementation roadmap

---

**Author**: MCP System  
**Date**: 2026-03-01  
**Status**: Proposed
