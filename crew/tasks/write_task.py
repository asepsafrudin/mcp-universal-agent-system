#!/usr/bin/env python3
"""
Write Task untuk CrewAI
Task untuk Writer Agent untuk membuat dokumentasi teknis
"""

from crewai import Task
from agents.writer import get_writer

def create_write_task():
    """
    Membuat task untuk Writer Agent
    """
    # Get writer agent
    writer = get_writer()
    
    write_task = Task(
        description="""Create technical documentation for fullstack developers based on research:
        
        1. Write Markdown doc with: Executive Summary, Architecture, Components, Tools Reference, API Docs, Setup Guide
        2. Include code examples for each MCP tool
        3. Save to output/mcp-documentation.md
        4. Save summary to PostgreSQL memory (key: 'mcp-docs-v1')
        
        Use clear formatting, syntax highlighting, practical examples.""",
        
        expected_output="""Markdown doc with: summary, architecture, tools reference, API docs, setup guide, examples. Saved to output/mcp-documentation.md and PostgreSQL.""",
        
        agent=writer,
        async_execution=False,

        # Output file
        output_file="output/mcp-documentation.md"
    )
    
    return write_task

def get_write_context():
    """Get context untuk task ini"""
    return {
        "task_type": "write",
        "focus_areas": [
            "comprehensive_documentation",
            "code_examples",
            "user_guide",
            "api_reference"
        ],
        "output_format": "markdown",
        "target_file": "output/mcp-documentation.md",
        "memory_key": "mcp-docs-v1"
    }

if __name__ == "__main__":
    # Test task creation
    task = create_write_task()
    print(f"✅ Write Task created")
    print(f"Agent: {task.agent.role}")
    print(f"Expected output: {task.expected_output[:100]}...")
    print(f"Context: {get_write_context()}")
    print(f"Output file: {task.output_file}")
