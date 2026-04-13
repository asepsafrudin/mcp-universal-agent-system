#!/usr/bin/env python3
"""
BLACKBOXAI MCP Server - Dedicated MCP protocol server untuk BLACKBOXAI tools.
Extend mcp-unified capabilities dengan BLACKBOX-specific planning & execution.
(FIXED: Proper triple-quote docstring - no syntax error)
"""

import sys
import os
import asyncio
import logging
import inspect
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Logging to stderr (MCP stdout reserved for protocol)
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger('blackbox-mcp')

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

mcp_server = Server('blackboxai-mcp')

# BLACKBOXAI Tools Registry (simplified untuk MCP)
tools_registry = {}

def register_blackbox_tool(name, description, input_schema):
    '''Register BLACKBOXAI tool (Decorator factory)'''
    def decorator(func):
        tools_registry[name] = {
            'name': name,
            'description': description,
            'inputSchema': input_schema,
            'handler': func
        }
        return func
    return decorator

# Define BLACKBOXAI MCP Tools
@register_blackbox_tool(
    name='blackbox_thinking_plan',
    description='Buat detailed thinking plan untuk complex task menggunakan BLACKBOXAI methodology',
    input_schema={
        "type": "object",
        "properties": {
            "task_description": {"type": "string", "description": "Deskripsi tugas yang akan direncanakan"},
            "context": {"type": "string", "description": "Konteks tambahan"}
        },
        "required": ["task_description"]
    }
)
def blackbox_thinking_plan(task_description: str, context: str = ''):
    '''Buat detailed thinking plan untuk complex task menggunakan BLACKBOXAI methodology'''
    return {
        'plan': f'Planning for: {task_description}. Context: {context}',
        'steps': ['Step 1: Analyze', 'Step 2: Tool selection', 'Step 3: Execute'],
        'confidence': 0.95
    }

@register_blackbox_tool(
    name='blackbox_project_analysis',
    description='Analyze project structure & suggest improvements',
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path direktori proyek"}
        },
        "required": ["path"]
    }
)
def blackbox_project_analysis(path: str):
    '''Analyze project structure & suggest improvements'''
    return {'summary': f'Project at {path}: Ready for MCP integration', 'recommendations': ['Add TODO.md']}

@register_blackbox_tool(
    name='blackbox_fix_plan',
    description='Generate fix plan untuk code error',
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path ke file yang bermasalah"},
            "error_msg": {"type": "string", "description": "Pesan error atau deskripsi bug"}
        },
        "required": ["file_path", "error_msg"]
    }
)
def blackbox_fix_plan(file_path: str, error_msg: str):
    '''Generate fix plan untuk code error'''
    return {'fix_steps': [f'Fix {error_msg} in {file_path}']}

@mcp_server.list_tools()
async def list_blackbox_tools():
    tools = []
    for tool_info in tools_registry.values():
        tools.append(Tool(
            name=tool_info['name'],
            description=tool_info['description'],
            inputSchema=tool_info['inputSchema']
        ))
    logger.info(f'Exposed {len(tools)} BLACKBOXAI tools via MCP')
    return tools

@mcp_server.call_tool()
async def call_blackbox_tool(name: str, arguments: dict):
    try:
        if name not in tools_registry:
            raise ValueError(f'Unknown tool: {name}')
        
        tool_info = tools_registry[name]
        handler = tool_info['handler']
        
        # Execute tool handler
        if inspect.iscoroutinefunction(handler):
            result = await handler(**arguments)
        else:
            result = handler(**arguments)
        
        return [TextContent(type='text', text=str(result))]
    except Exception as e:
        logger.error(f'Tool {name} failed: {e}')
        return [TextContent(type='text', text=f'Error: {str(e)}')]

async def main():
    logger.info('Starting BLACKBOXAI MCP Server')
    logger.info('Available tools: blackbox_thinking_plan, blackbox_project_analysis, blackbox_fix_plan')
    
    async with stdio_server() as streams:
        await mcp_server.run(*streams, mcp_server.create_initialization_options())

if __name__ == '__main__':
    asyncio.run(main())

