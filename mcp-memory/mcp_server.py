#!/usr/bin/env python3
import asyncio
import json
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from tools.file_writer import write_file
from tools.read_file import read_file
from tools.list_dir import list_dir
from tools.run_shell import run_shell
try:
    from tools.memory import memory_save, memory_search, memory_list, memory_delete
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    if MEMORY_AVAILABLE:
        from tools.memory import pool
        try:
            await pool.open()
            print("✅ Memory connection pool opened")
        except Exception as e:
            print(f"❌ Failed to open memory pool: {e}")

def get_base_tools():
    """Get basic file and shell tools"""
    return [
        {
            "name": "write_file",
            "description": "Tulis teks ke file (dukung /host/..., /workspace/...)",
            "inputSchema": {
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
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

def get_memory_tools():
    """Get memory-related tools if available"""
    if not MEMORY_AVAILABLE:
        return []

    return [
        {
            "name": "memory_save",
            "description": "Simpan memori ke PostgreSQL dengan hybrid search (keyword + semantic)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "content": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["key", "content"]
            }
        },
        {
            "name": "memory_search",
            "description": "Cari memori dengan hybrid, semantic, atau keyword search",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                    "strategy": {"type": "string", "enum": ["hybrid", "semantic", "keyword"]}
                },
                "required": ["query"]
            }
        },
        {
            "name": "memory_list",
            "description": "List semua memories dengan pagination",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                    "offset": {"type": "integer", "minimum": 0}
                }
            }
        },
        {
            "name": "memory_delete",
            "description": "Hapus memori berdasarkan ID atau key",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "key": {"type": "string"}
                }
            }
        }
    ]

def list_tools():
    """List all available tools"""
    tools = get_base_tools()
    tools.extend(get_memory_tools())
    return {"tools": tools}

def get_tool_handlers():
    """Get tool handler mapping"""
    handlers = {
        "write_file": write_file,
        "read_file": read_file,
        "list_dir": list_dir,
        "run_shell": run_shell
    }

    if MEMORY_AVAILABLE:
        handlers.update({
            "memory_save": memory_save,
            "memory_search": memory_search,
            "memory_list": memory_list,
            "memory_delete": memory_delete
        })

    return handlers

async def call_tool(name, arguments):
    """Call a tool by name with arguments"""
    handlers = get_tool_handlers()

    if name not in handlers:
        return {"error": f"Tool {name} tidak ditemukan"}

    try:
        handler = handlers[name]
        if asyncio.iscoroutinefunction(handler):
            return await handler(arguments)
        else:
            return handler(arguments)
    except Exception as e:
        return {"error": str(e)}

def handle_tools_list(msg_id):
    """Handle tools/list request"""
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": list_tools()
    }

async def handle_tools_call(msg_id, params):
    """Handle tools/call request"""
    tool_name = params.get("name")
    tool_args = params.get("arguments", {})

    if not tool_name:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32602, "message": "Tool name required"}
        }

    result = await call_tool(tool_name, tool_args)
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "content": [{
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False)
            }]
        }
    }

@app.post("/")
async def process_message(request: Request):
    """Process a single JSON-RPC message"""
    try:
        message = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    method = message.get("method")
    params = message.get("params", {})
    msg_id = message.get("id")

    if method == "tools/list":
        response = handle_tools_list(msg_id)
    elif method == "tools/call":
        response = await handle_tools_call(msg_id, params)
    else:
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method {method} not found"}
        }
    return JSONResponse(content=response)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
