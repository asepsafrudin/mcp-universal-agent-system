#!/usr/bin/env python3
"""
MCP Tools untuk CrewAI - BaseTool Compatible Format
Wrapper untuk mengintegrasikan MCP tools dengan CrewAI agents
"""

import sys
import os
from typing import Any, Type
from crewai.tools import BaseTool

# Add parent directory to path for shared imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
sys.path.insert(0, project_root)

from shared.mcp_client import (
    mcp_list_dir,
    mcp_read_file,
    mcp_memory_search,
    call_mcp_tool
)

# BaseTool implementations untuk MCP functions

class MCPListDirTool(BaseTool):
    """Tool untuk list directory via MCP"""
    name: str = "mcp_list_dir"
    description: str = "List contents of a directory using MCP server. Useful for exploring project structure and finding files."

    def _run(self, path: str = "/workspace") -> str:
        """Execute MCP list_dir tool"""
        # Handle dict input from LLM
        if isinstance(path, dict):
            path = path.get("path", "/workspace")
        try:
            result = mcp_list_dir(path)
            if result.get("status") == "success":
                data = result.get("data", {})
                directories = data.get("directories", [])
                files = data.get("files", [])
                return f"Path: {path}\nDirectories: {directories}\nFiles: {files}"
            else:
                return f"Error: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Exception: {str(e)}"

class MCPReadFileTool(BaseTool):
    """Tool untuk read file via MCP"""
    name: str = "mcp_read_file"
    description: str = "Read contents of a file using MCP server. Essential for analyzing code, documentation, and configuration files."

    def _run(self, path: str) -> str:
        """Execute MCP read_file tool"""
        # Handle dict input from LLM
        if isinstance(path, dict):
            path = path.get("path", "")
        if not path:
            return "Error: path parameter is required"
        try:
            result = mcp_read_file(path)
            if result.get("status") == "success":
                data = result.get("data", "")
                return str(data)
            else:
                return f"Error: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Exception: {str(e)}"

class MCPMemorySearchTool(BaseTool):
    """Tool untuk search memory via MCP"""
    name: str = "mcp_memory_search"
    description: str = "Search through stored memory and previous findings using MCP server. Useful for retrieving context and past analysis."

    def _run(self, query: str) -> str:
        """Execute MCP memory_search tool"""
        # Handle dict input from LLM
        if isinstance(query, dict):
            query = query.get("query", "")
        if not query:
            return "Error: query parameter is required"
        try:
            result = mcp_memory_search(query)
            if result.get("status") == "success":
                data = result.get("data", "")
                return str(data)
            else:
                return f"Error: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Exception: {str(e)}"

class MCPSearchFilesTool(BaseTool):
    """Tool untuk search files via MCP"""
    name: str = "mcp_search_files"
    description: str = "Search for patterns across files in the project using MCP server. Ideal for finding specific code patterns, functions, or text."

    def _run(self, query: str, path: str = "/workspace") -> str:
        """Execute MCP search_files tool"""
        # Handle dict input from LLM
        if isinstance(query, dict):
            path = query.get("path", "/workspace")
            query = query.get("query", "")
        if not query:
            return "Error: query parameter is required"
        try:
            result = call_mcp_tool("search_files", {"query": query, "path": path})
            if result.get("status") == "success":
                data = result.get("data", "")
                return str(data)
            else:
                return f"Error: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Exception: {str(e)}"

class MCPPythonShellTool(BaseTool):
    """Tool untuk run Python commands via MCP"""
    name: str = "mcp_run_python"
    description: str = "Execute Python commands and scripts using MCP server. Useful for running analysis scripts, checking imports, and testing code."

    def _run(self, command: str) -> str:
        """Execute MCP run_shell tool with python"""
        # Handle dict input from LLM
        if isinstance(command, dict):
            command = command.get("command", "")
        if not command:
            return "Error: command parameter is required"
        try:
            result = call_mcp_tool("run_shell", {"command": f"python3 -c '{command}'"})
            if result.get("status") == "success":
                data = result.get("data", "")
                return str(data)
            else:
                return f"Error: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Exception: {str(e)}"

class MCPMemorySaveTool(BaseTool):
    """Tool untuk save to memory via MCP"""
    name: str = "mcp_memory_save"
    description: str = "Save information to persistent memory using MCP server. Essential for storing analysis results and context for future use."

    def _run(self, key: str, content: str) -> str:
        """Execute MCP memory_save tool"""
        # Handle dict input from LLM
        if isinstance(key, dict):
            content = key.get("content", "")
            key = key.get("key", "")
        if not key or not content:
            return "Error: both key and content parameters are required"
        try:
            from shared.mcp_client import mcp_memory_save
            result = mcp_memory_save(key, content)
            if result.get("status") == "success":
                return f"Successfully saved to memory with key: {key}"
            else:
                return f"Error: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Exception: {str(e)}"

class MCPWriteFileTool(BaseTool):
    """Tool untuk write file via MCP"""
    name: str = "mcp_write_file"
    description: str = "Write or create files using MCP server. Useful for generating documentation, configuration files, and code."

    def _run(self, path: str, content: str) -> str:
        """Execute MCP write_file tool"""
        # Handle dict input from LLM
        if isinstance(path, dict):
            content = path.get("content", "")
            path = path.get("path", "")
        if not path or not content:
            return "Error: both path and content parameters are required"
        try:
            from shared.mcp_client import mcp_write_file
            result = mcp_write_file(path, content)
            if result.get("status") == "success":
                return f"Successfully wrote to file: {path}"
            else:
                return f"Error: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Exception: {str(e)}"

# Convenience functions untuk get tools
def get_mcp_tools():
    """Get all MCP tools as BaseTool instances"""
    return [
        MCPListDirTool(),
        MCPReadFileTool(),
        MCPMemorySearchTool(),
        MCPSearchFilesTool(),
        MCPPythonShellTool(),
        MCPMemorySaveTool(),
        MCPWriteFileTool(),
    ]

def get_researcher_tools():
    """Get tools specifically untuk Researcher agent"""
    return [
        MCPListDirTool(),
        MCPReadFileTool(),
        MCPMemorySearchTool(),
        MCPSearchFilesTool(),
        MCPPythonShellTool(),
    ]

def get_writer_tools():
    """Get tools specifically untuk Writer agent"""
    return [
        MCPReadFileTool(),
        MCPMemorySearchTool(),
        MCPMemorySaveTool(),
        MCPWriteFileTool(),
        MCPSearchFilesTool(),
    ]

def get_checker_tools():
    """Get tools specifically untuk Checker agent"""
    return [
        MCPReadFileTool(),
        MCPMemorySearchTool(),
        MCPSearchFilesTool(),
        MCPPythonShellTool(),
    ]

# Test function
def test_mcp_crewai_tools():
    """Test MCP CrewAI tools"""
    print("🧪 Testing MCP CrewAI Tools...")

    tools = get_mcp_tools()
    print(f"✅ Created {len(tools)} MCP tools for CrewAI")

    for tool in tools:
        print(f"   - {tool.name}: {tool.description[:50]}...")

    # Test basic functionality
    list_tool = MCPListDirTool()
    result = list_tool._run("/workspace")
    if "Error" not in result:
        print("✅ MCPListDirTool test PASSED")
    else:
        print(f"❌ MCPListDirTool test FAILED: {result}")

    print("🎉 MCP CrewAI Tools ready!")

if __name__ == "__main__":
    test_mcp_crewai_tools()
