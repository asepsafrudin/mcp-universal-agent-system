# API Documentation - MCP Server

## Overview

MCP Server mengimplementasikan Model Context Protocol (MCP) menggunakan JSON-RPC 2.0 over STDIN/STDOUT. Dokumentasi ini menyediakan detail lengkap tentang API endpoints, request/response formats, dan contoh penggunaan.

## Base URL
```
stdin/stdout (local process)
```

## Protocol
JSON-RPC 2.0 over text lines

## Authentication
Tidak ada authentication diperlukan (untuk environment trusted)

---

## Endpoints

### 1. List Available Tools

Mendapatkan daftar semua tools yang tersedia di server.

#### Request
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

#### Response
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "write_file",
        "description": "Tulis teks ke file (dukung /host/..., /workspace/...)",
        "inputSchema": {
          "type": "object",
          "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"}
          },
          "required": ["path", "content"]
        }
      },
      {
        "name": "read_file",
        "description": "Baca isi file (dukung /host/..., /workspace/...)",
        "inputSchema": {
          "type": "object",
          "properties": {"path": {"type": "string"}},
          "required": ["path"]
        }
      },
      {
        "name": "list_dir",
        "description": "List isi direktori",
        "inputSchema": {
          "type": "object",
          "properties": {"path": {"type": "string"}}
        }
      },
      {
        "name": "run_shell",
        "description": "Jalankan command aman: ls, pwd, git, dll",
        "inputSchema": {
          "type": "object",
          "properties": {"command": {"type": "string"}},
          "required": ["command"]
        }
      }
    ]
  }
}
```

---

### 2. Execute Tool

Menjalankan tool tertentu dengan parameter yang diberikan.

#### Request
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      // tool-specific arguments
    }
  },
  "id": 2
}
```

#### Response
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"success\": true, \"message\": \"Tool executed successfully\"}"
    }]
  }
}
```

---

## Tools Reference

### write_file

Menulis konten teks ke file.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path file target |
| `content` | string | Yes | Konten yang akan ditulis |

#### Examples

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "write_file",
    "arguments": {
      "path": "/workspace/example.txt",
      "content": "Hello World!\nThis is a test file."
    }
  },
  "id": 1
}
```

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"success\": true, \"message\": \"File ditulis ke: /workspace/example.txt\"}"
    }]
  }
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "Internal: Permission denied"
  }
}
```

---

### read_file

Membaca konten dari file.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path file yang akan dibaca |

#### Examples

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "/workspace/example.txt"
    }
  },
  "id": 2
}
```

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"success\": true, \"content\": \"Hello World!\\nThis is a test file.\", \"path\": \"/workspace/example.txt\"}"
    }]
  }
}
```

---

### list_dir

Mendapatkan daftar file dan direktori dalam sebuah direktori.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | No | Path direktori (default: current directory) |

#### Examples

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "list_dir",
    "arguments": {
      "path": "/workspace"
    }
  },
  "id": 3
}
```

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"success\": true, \"path\": \"/workspace\", \"directories\": [\"src\", \"docs\"], \"files\": [\"README.md\", \"main.py\"]}"
    }]
  }
}
```

---

### run_shell

Menjalankan command shell yang aman.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `command` | string | Yes | Command yang akan dijalankan |

#### Allowed Commands
- `ls` - List files and directories
- `pwd` - Print working directory
- `whoami` - Display current user
- `date` - Display current date/time
- `df` - Display disk space usage
- `free` - Display memory usage
- `git` - Git version control commands
- `cat` - Display file contents
- `find` - Search for files and directories

#### Examples

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "run_shell",
    "arguments": {
      "command": "ls -la /workspace"
    }
  },
  "id": 4
}
```

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"success\": true, \"stdout\": \"total 12\\ndrwxr-xr-x 2 user user 4096 Dec 29 10:00 .\\ndrwxr-xr-x 3 user user 4096 Dec 29 09:00 ..\\n-rw-r--r-- 1 user user  256 Dec 29 10:00 example.txt\", \"stderr\": \"\", \"returncode\": 0}"
    }]
  }
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "error": {
    "code": -32603,
    "message": "Internal: Command 'rm' tidak diizinkan."
  }
}
```

---

## Path Mapping

MCP Server mendukung path mapping untuk mengakses file di berbagai lokasi:

### Path Prefixes
| Prefix | Maps To | Description |
|--------|---------|-------------|
| `/workspace/` | `/app/` | Container workspace directory |
| `/host/` | `/home/aseps/` | Host filesystem (WSL home) |
| `<no prefix>` | `<relative>` | Relative to container current directory |

### Examples
- `/workspace/file.txt` → `/app/file.txt`
- `/host/documents/readme.md` → `/home/aseps/documents/readme.md`
- `data.txt` → `<current-dir>/data.txt`

---

## Error Handling

### Standard JSON-RPC Errors

| Code | Message | Description |
|------|---------|-------------|
| -32600 | Invalid Request | Request is not a valid JSON-RPC object |
| -32601 | Method not found | Requested method does not exist |
| -32602 | Invalid params | Requested method parameters are invalid |
| -32603 | Internal error | Internal server error |

### MCP Server Specific Errors

#### Tool Execution Errors
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "Internal: File tidak ditemukan"
  }
}
```

#### Timeout Errors
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "error": {
    "code": -32603,
    "message": "Internal: Timeout (>10 detik)"
  }
}
```

#### Permission Errors
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "error": {
    "code": -32603,
    "message": "Internal: Permission denied"
  }
}
```

---

## Rate Limiting

Tidak ada rate limiting yang diimplementasikan. Server ini dirancang untuk trusted environments dengan trusted clients.

---

## Examples

### Complete Session Example

```python
import json
import subprocess
import sys

def send_request(request):
    """Send JSON-RPC request and get response."""
    print(json.dumps(request))
    sys.stdout.flush()
    
    response_line = sys.stdin.readline()
    return json.loads(response_line.strip())

# 1. List available tools
tools_request = {
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
}
response = send_request(tools_request)
print("Available tools:", response)

# 2. Write a file
write_request = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "write_file",
        "arguments": {
            "path": "/workspace/test.txt",
            "content": "Hello, MCP Server!"
        }
    },
    "id": 2
}
response = send_request(write_request)
print("Write result:", response)

# 3. Read the file back
read_request = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "read_file",
        "arguments": {
            "path": "/workspace/test.txt"
        }
    },
    "id": 3
}
response = send_request(read_request)
print("Read result:", response)
```

---

## SDK Examples

### Python Client Example

```python
import json
import subprocess
import threading
import queue

class MCPClient:
    def __init__(self):
        self.process = subprocess.Popen(
            ['python3', 'mcp_server.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.request_id = 0
        self.responses = {}
        
        # Start response listener
        threading.Thread(target=self._listen, daemon=True).start()
    
    def _listen(self):
        """Listen for responses from MCP server."""
        for line in iter(self.process.stdout.readline, ''):
            if line.strip():
                try:
                    response = json.loads(line)
                    msg_id = response.get('id')
                    if msg_id:
                        self.responses[msg_id] = response
                except json.JSONDecodeError:
                    continue
    
    def call_tool(self, name, arguments):
        """Call a tool on MCP server."""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            },
            "id": self.request_id
        }
        
        # Send request
        self.process.stdin.write(json.dumps(request) + '\n')
        self.process.stdin.flush()
        
        # Wait for response
        while self.request_id not in self.responses:
            pass
        
        response = self.responses.pop(self.request_id)
        
        if 'error' in response:
            raise Exception(f"Tool error: {response['error']}")
        
        # Extract content from response
        content = response['result']['content'][0]['text']
        return json.loads(content)
    
    def list_tools(self):
        """List available tools."""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": self.request_id
        }
        
        self.process.stdin.write(json.dumps(request) + '\n')
        self.process.stdin.flush()
        
        while self.request_id not in self.responses:
            pass
        
        response = self.responses.pop(self.request_id)
        return response['result']['tools']

# Usage example
client = MCPClient()

# List tools
tools = client.list_tools()
print("Available tools:", [tool['name'] for tool in tools])

# Write a file
result = client.call_tool('write_file', {
    'path': '/workspace/example.txt',
    'content': 'Hello, World!'
})
print("Write result:", result)

# Read the file
result = client.call_tool('read_file', {
    'path': '/workspace/example.txt'
})
print("Read result:", result['content'])
```

### JavaScript/Node.js Client Example

```javascript
const { spawn } = require('child_process');

class MCPClient {
    constructor() {
        this.process = spawn('python3', ['mcp_server.py']);
        this.requestId = 0;
        this.responses = new Map();
        
        this.process.stdout.on('data', (data) => {
            const lines = data.toString().split('\n').filter(line => line.trim());
            lines.forEach(line => {
                try {
                    const response = JSON.parse(line);
                    if (response.id !== undefined) {
                        this.responses.set(response.id, response);
                    }
                } catch (e) {
                    console.error('Failed to parse response:', line);
                }
            });
        });
    }
    
    sendRequest(request) {
        return new Promise((resolve, reject) => {
            this.requestId++;
            request.id = this.requestId;
            
            const sendData = JSON.stringify(request) + '\n';
            this.process.stdin.write(sendData);
            
            // Wait for response
            const checkResponse = () => {
                if (this.responses.has(this.requestId)) {
                    const response = this.responses.get(this.requestId);
                    this.responses.delete(this.requestId);
                    
                    if (response.error) {
                        reject(new Error(`Tool error: ${response.error.message}`));
                    } else {
                        resolve(response);
                    }
                } else {
                    setTimeout(checkResponse, 10);
                }
            };
            
            checkResponse();
        });
    }
    
    async listTools() {
        const response = await this.sendRequest({
            jsonrpc: "2.0",
            method: "tools/list"
        });
        return response.result.tools;
    }
    
    async callTool(name, arguments) {
        const response = await this.sendRequest({
            jsonrpc: "2.0",
            method: "tools/call",
            params: {
                name: name,
                arguments: arguments
            }
        });
        
        const content = response.result.content[0].text;
        return JSON.parse(content);
    }
}

// Usage example
async function main() {
    const client = new MCPClient();
    
    try {
        // List tools
        const tools = await client.listTools();
        console.log("Available tools:", tools.map(tool => tool.name));
        
        // Write a file
        const writeResult = await client.callTool('write_file', {
            path: '/workspace/example.txt',
            content: 'Hello, World!'
        });
        console.log("Write result:", writeResult);
        
        // Read the file
        const readResult = await client.callTool('read_file', {
            path: '/workspace/example.txt'
        });
        console.log("Read result:", readResult.content);
        
    } catch (error) {
        console.error('Error:', error);
    }
}

main();
```

---

## Changelog

### v1.0.0 (2025-12-29)
- Initial release
- Implemented JSON-RPC 2.0 protocol
- Added 4 core tools: write_file, read_file, list_dir, run_shell
- Added Docker containerization
- Added path mapping support
- Added security features (command whitelist, timeout protection)
