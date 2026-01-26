#!/usr/bin/env python3
import asyncio
import json
import sys
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Tambahkan path root agar bisa import shared dan engine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.planning import PlanningEngine
from engine.scheduler import ExecutionScheduler

app = FastAPI()
planner = PlanningEngine()
scheduler = ExecutionScheduler()

@app.get("/health")
async def health_check():
    return {"status": "ok", "components": ["planner", "scheduler", "agents"]}

@app.post("/")
async def mcp_interface(request: Request):
    """Interface utama MCP JSON-RPC 2.0"""
    try:
        message = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    method = message.get("method")
    params = message.get("params", {})
    msg_id = message.get("id")

    if method == "tools/list":
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "execute_task",
                        "description": "Berikan tugas tingkat tinggi yang akan didekomposisi dan dieksekusi secara otonom.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "task_content": {"type": "string"}
                            },
                            "required": ["task_content"]
                        }
                    }
                ]
            }
        })
    
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if tool_name == "execute_task":
            task_content = tool_args.get("task_content")
            if not task_content:
                return JSONResponse(content={"error": "task_content required"})
            
            # Meluncurkan Workflow Sub-Agent
            print(f"🚀 Memproses tugas baru: {task_content}")
            
            # 1. Dekomposisi
            plan = await planner.decompose(task_content)
            
            # 2. Eksekusi
            result = await scheduler.run(plan)
            
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False)
                    }]
                }
            })

    return JSONResponse(content={
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": "Method not found"}
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) # Port 8001 agar tidak konflik dengan mcp-memory
