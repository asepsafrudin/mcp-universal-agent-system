# TASK-038: OpenHands Admin UI Integration — Service Webserver Setup

**Dibuat:** 2026-04-01  
**Status:** BACKLOG  
**Priority:** MEDIUM  
**Assignee:** TBD

---

## Deskripsi

Integrasikan OpenHands service ke dalam Admin UI yang sudah ada (`services/service_controller.py`). Menyediakan web service manager untuk start/stop/monitor OpenHands agent dengan prosedur menjalankan webserver yang aman tanpa konflik port.

## Port Allocation Analysis

| Service | Port | Protocol | Status |
|---------|------|----------|--------|
| MCP SSE Server | 8000 | HTTP | Active (mcp_server_sse.py) |
| Knowledge Admin | 8080 | HTTP | Active (knowledge.admin.app) |
| Surat PUU Dashboard | 8081 | HTTP | Active (surat_puu_app.py) |
| LLM API | 8088 | HTTP | Active (llm_api) |
| WhatsApp Bot | 8008 | HTTP | Active (bot_server.py) |
| Telegram Webhook | 8443 | HTTPS | Optional |
| Telegram SQL Bot | Internal | - | Active |
| WAHA API | 3001 | HTTP | External service |
| SearxNG | 8090 | HTTP | Vane integration |
| Vane UI | 3000 | HTTP | Dev environment |
| Redis | 6379 | TCP | Active |
| PostgreSQL | 5432/5433 | TCP | Active |

### Port yang Tersedia untuk OpenHands Admin UI:
| Port | Status | Recommendation |
|------|--------|----------------|
| 8095 | FREE | ✅ Recommended |
| 8096 | FREE | ✅ Alternative |
| 8097 | FREE | ✅ Alternative |

## Acceptance Criteria

- [ ] Port conflict analysis lengkap dan terdokumentasi
- [ ] OpenHands service terdaftar di `get_all_service_status()`
- [ ] Functions `start_openhands_agent()` dan `stop_openhands_agent()` ada di service_controller.py
- [ ] Webserver startup procedure terdokumentasi
- [ ] No port conflict dengan service yang sudah running
- [ ] OpenHands agent bisa di-start/stop/restart via API

## Subtasks

### 038-A: Port Conflict Prevention Setup
- [ ] Buat environment variable `OPENHANDS_ADMIN_PORT=8095`
- [ ] Tambah port validation di config.py
- [ ] Buat pre-flight check script untuk cek port availability

### 038-B: Service Controller Integration
- [ ] Tambah OPENHANDS_LOG constant
- [ ] Implementasi `_openhands_status()` function
- [ ] Implementasi `start_openhands_agent()` function
- [ ] Implementasi `stop_openhands_agent()` function
- [ ] Register di LOG_PATHS dict
- [ ] Tambah ke all service status functions

### 038-C: OpenHands Webserver Module
- [ ] Buat `plugins/openhands/admin_server.py` (standalone FastAPI app)
- [ ] Endpoint: `GET /health` - health check
- [ ] Endpoint: `GET /services` - list all services
- [ ] Endpoint: `POST /services/{name}/start` - start service
- [ ] Endpoint: `POST /services/{name}/stop` - stop service
- [ ] Endpoint: `POST /services/{name}/restart` - restart service
- [ ] Endpoint: `GET /services/{name}/logs` - view logs
- [ ] Endpoint: `GET /tasks` - list active tasks

### 038-D: Startup Procedures Documentation
- [ ] Tulis `plugins/openhands/RUNBOOK.md` dengan startup guide
- [ ] Tulis systemd service file template
- [ ] Tulis `run_openhands_admin.sh` startup script
- [ ] Tambah ke `run_mcp_with_services.sh`

### 038-E: Testing & Validation
- [ ] Port conflict test
- [ ] Service lifecycle test (start/stop/restart)
- [ ] Integration test dengan service_controller.py
- [ ] End-to-end admin UI test

## Dependensi

- Depends on: TASK-034, TASK-035, TASK-036, TASK-037 (semua sudah selesai ✅)
- Blocks: None

## Risiko & Mitigasi

| Risiko | Mitigasi |
|--------|----------|
| Port conflict dengan service lain | Pre-flight port check, configurable port via env var |
| Memory exhaustion dengan banyak concurrent agents | Set `OPENHANDS_MAX_AGENTS=3` konservatif |
| Admin UI expose tanpa auth | Reuse existing admin UI auth mechanism |
| Redis connection leak | Proper connection pooling dan cleanup |

## Webserver Startup Procedure

### Option 1: Standalone Admin Server (Recommended)
```bash
# 1. Set environment variables
export OPENHANDS_ADMIN_PORT=8095
export REDIS_URL=redis://localhost:6379/0

# 2. Check port availability
lsof -ti:8095 && echo "Port 8095 in use!" || echo "Port 8095 available"

# 3. Start OpenHands Admin Server
cd /home/aseps/MCP/mcp-unified
python3 -m plugins.openhands.admin_server

# 4. Verify
curl http://localhost:8095/health
```

### Option 2: Integrated with Main MCP Server
```bash
# OpenHands tools available via existing MCP server (port 8000)
# No additional port needed

# Check available tools
curl -X POST http://localhost:8000/tools/list | jq '.tools[] | select(.name | contains("coding"))'

# Run coding task
curl -X POST http://localhost:8000/tools/call \
  -d '{"name": "run_coding_task", "arguments": {"task_description": "Test", "expected_output": "OK"}}'
```

### Option 3: systemd Service (Production)
```bash
# 1. Install service file
sudo cp mcp-unified/plugins/openhands/mcp-openhands-admin.service /etc/systemd/system/
sudo systemctl daemon-reload

# 2. Enable and start
sudo systemctl enable mcp-openhands-admin
sudo systemctl start mcp-openhands-admin

# 3. Check status
sudo systemctl status mcp-openhands-admin
```

## Conflict Prevention Checklist

```bash
#!/bin/bash
# check_ports.sh - Pre-flight port availability check

PORTS_TO_CHECK=(8000 8008 8080 8081 8088 8090 8095 8443)

echo "=== Port Availability Check ==="
for port in "${PORTS_TO_CHECK[@]}"; do
    if lsof -ti:$port > /dev/null 2>&1; then
        pid=$(lsof -ti:$port)
        echo "❌ Port $port: IN USE (PID: $pid)"
    else
        echo "✅ Port $port: AVAILABLE"
    fi
done
```

## Catatan

- OpenHands SDK v1.6.0 sudah ter-install dan ter-verify
- Telegram integration (TASK-036) sudah selesai - user bisa submit coding tasks via `/code` command
- App Developer Agent (TASK-037) sudah selesai - bisa handle app development tasks
- Admin UI integration ini fokus pada operational management bukan user interaction

---

## Log Perubahan

| Tanggal | Status | Oleh | Catatan |
|---------|--------|------|---------|
| 2026-04-01 | BACKLOG | agent | Task dibuat - berisi port analysis dan startup procedures |