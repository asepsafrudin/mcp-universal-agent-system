# MCP API Documentation

**Version:** 1.0.0  
**Last Updated:** 2026-02-25  
**Base URL:** `http://localhost:8000` (development) / `https://api.mcp.local` (production)

---

## Authentication

MCP API menggunakan dua metode autentikasi:

### 1. API Key ( untuk service-to-service )
```
X-API-Key: your-api-key-here
```

### 2. JWT Bearer Token ( untuk user sessions )
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Mendapatkan JWT Token:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "X-API-Key: your-api-key"
```

---

## Endpoints

### Health & Status

#### GET /health
Health check endpoint.

**Auth:** None  
**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-25T14:30:00Z"
}
```

#### GET /ready
Readiness probe untuk Kubernetes.

**Auth:** None  
**Response:**
```json
{
  "ready": true,
  "checks": {
    "database": "ok",
    "memory": "ok"
  }
}
```

---

### Tools

#### GET /tools/list
List all available tools.

**Auth:** API Key or JWT  
**Response:**
```json
{
  "tools": [
    {
      "name": "file_read",
      "description": "Read file contents",
      "parameters": {
        "path": "string (required)"
      }
    }
  ]
}
```

#### POST /tools/call
Execute a tool.

**Auth:** API Key or JWT + Permission `tools:execute`  
**Request:**
```json
{
  "tool": "file_read",
  "parameters": {
    "path": "/path/to/file.txt"
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": "file contents...",
  "execution_time": 0.123
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "File not found",
  "error_code": "FILE_NOT_FOUND"
}
```

---

### Agents

#### GET /agents/list
List all registered agents.

**Auth:** JWT  
**Response:**
```json
{
  "agents": [
    {
      "id": "agent-001",
      "name": "Code Assistant",
      "status": "idle",
      "capabilities": ["code", "review"]
    }
  ]
}
```

#### POST /agents/execute
Execute an agent with a task.

**Auth:** JWT + Permission `agents:execute`  
**Request:**
```json
{
  "agent_id": "code_agent",
  "task": "Review this code for bugs",
  "context": {
    "code": "def hello(): pass"
  }
}
```

**Response:**
```json
{
  "task_id": "task-123",
  "status": "completed",
  "result": "Code review complete...",
  "execution_time": 2.5
}
```

---

### Authentication

#### POST /auth/login
Login dengan API key untuk mendapatkan JWT token.

**Auth:** API Key  
**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### GET /auth/me
Get current user info.

**Auth:** JWT  
**Response:**
```json
{
  "user_id": "user-123",
  "role": "developer",
  "permissions": ["tools:execute", "agents:read"]
}
```

---

### Admin (Admin Only)

#### POST /admin/keys
Create new API key.

**Auth:** JWT + Role `admin`  
**Request:**
```json
{
  "name": "Service Key",
  "role": "service",
  "expires_days": 90
}
```

**Response:**
```json
{
  "key_id": "key-123",
  "api_key": "mcp_xxxxxxxxxxxx",
  "created_at": "2026-02-25T14:30:00Z"
}
```

**⚠️ Note:** API key hanya ditampilkan sekali!

#### GET /admin/keys
List all API keys.

**Auth:** JWT + Role `admin`  
**Response:**
```json
{
  "keys": [
    {
      "key_id": "key-123",
      "name": "Service Key",
      "role": "service",
      "created_at": "2026-02-25T14:30:00Z",
      "last_used": "2026-02-25T15:00:00Z"
    }
  ]
}
```

#### DELETE /admin/keys/{key_id}
Revoke an API key.

**Auth:** JWT + Role `admin`  
**Response:** `204 No Content`

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `TOOL_NOT_FOUND` | 404 | Tool tidak ditemukan |
| `TOOL_EXECUTION_ERROR` | 400 | Error saat menjalankan tool |
| `AGENT_NOT_FOUND` | 404 | Agent tidak ditemukan |
| `FILE_NOT_FOUND` | 404 | File tidak ditemukan |
| `INVALID_PATH` | 400 | Path tidak valid |

---

## Rate Limiting

- **Authenticated:** 1000 requests/hour
- **Anonymous:** 100 requests/hour (health endpoints only)

**Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1708876800
```

---

## Webhooks (Future)

### Tool Execution Complete
```json
{
  "event": "tool.execution.completed",
  "task_id": "task-123",
  "tool": "file_read",
  "status": "success",
  "timestamp": "2026-02-25T14:30:00Z"
}
```

---

## SDK Examples

### Python
```python
import requests

class MCPClient:
    def __init__(self, api_key, base_url="http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
    
    def call_tool(self, tool, parameters):
        response = requests.post(
            f"{self.base_url}/tools/call",
            headers={"X-API-Key": self.api_key},
            json={"tool": tool, "parameters": parameters}
        )
        return response.json()

# Usage
client = MCPClient("your-api-key")
result = client.call_tool("file_read", {"path": "/tmp/test.txt"})
```

### cURL
```bash
# Call a tool
curl -X POST http://localhost:8000/tools/call \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_read",
    "parameters": {"path": "/tmp/test.txt"}
  }'
```

---

## Changelog

### v1.0.0 (2026-02-25)
- Initial API release
- Authentication with API Key + JWT
- Tool execution endpoints
- Agent management
- Admin API key management
