# mcp-unified Activation Audit - 2026-03-28

## Current Runtime Status

- `mcp-unified` SSE server is running on `127.0.0.1:8000`.
- Health check result:

```json
{"status":"healthy","service":"mcp-unified","version":"1.0.0","transport":"SSE","host":"127.0.0.1","port":8000,"tools_available":28}
```

- Active process on port `8000`:

```text
/usr/bin/python3 /home/aseps/MCP/mcp-unified/mcp_server_sse.py
```

- `5432` and `5433` are accepting PostgreSQL connections.
- `3000` is listening and returns `401 Unauthorized` on `/`, which indicates a live service with auth enforcement.
- `8088` is not listening, so the standalone LLM API is currently inactive.

## PID File Cleanup

The following stale PID files were archived to avoid false status detection:

- `/home/aseps/MCP/mcp-unified/mcp_server_sse.pid.stale-20260328`
- `/home/aseps/MCP/mcp-unified/services/llm_api/api_server.pid.stale-20260328`
- `/home/aseps/MCP/mcp-unified/integrations/telegram/sql_bot.pid.stale-20260328`
- `/home/aseps/MCP/mcp-unified/integrations/telegram/telegram_bot.pid.stale-20260328`

## Audit Findings

- The main MCP SSE entrypoint is healthy and already active.
- Earlier "down" signals for localhost services were caused by sandbox restrictions, not actual service failure.
- Telegram and SQL bot processes are not currently active, and their old PID files were stale.
- WhatsApp-related runtime likely exists behind port `3000`, but auth/session readiness still needs service-specific verification.
- Historical Telegram logs contain bot-token exposure in request URLs and should be treated as sensitive artifacts even after token rotation.

## Safe Bring-up Order

1. Confirm root secrets file `/home/aseps/MCP/.env` is current.
2. Verify database readiness on `5432` and `5433`.
3. Verify `mcp_server_sse.py` health on `http://127.0.0.1:8000/health`.
4. Validate WAHA auth/session on port `3000` with the expected credentials.
5. Start or verify auxiliary services only if needed:
   - LLM API on `8088`
   - Telegram bot
   - Telegram SQL bot
   - scheduler and worker services

## Follow-up Tasks

- Remove or securely archive historical Telegram logs that contain exposed token URLs.
- Standardize a single operational startup path between `run_mcp_with_services.sh`, `run.sh`, and `mcp-unified.service`.
- Add a lightweight status script that checks health endpoints and flags stale PID files without exposing secrets.
