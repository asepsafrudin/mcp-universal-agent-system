#!/usr/bin/env python3
"""
Research Task untuk CrewAI
Task untuk Researcher Agent untuk eksplorasi mendalam proyek MCP
"""

import sys
import os
from crewai import Task
from agents.researcher import get_researcher

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from shared.mcp_client import mcp_memory_search

def create_research_task():
    """
    Membuat task untuk Research Agent
    """
    # Get researcher agent
    researcher = get_researcher()
    
    research_task = Task(
        description="""Analyze MCP project for fullstack developer documentation:
        
        1. List /workspace structure, read mcp_server.py, init_db.sql, requirements.txt
        2. Identify available tools in tools/ folder
        3. Search memory for 'project structure' and 'MCP tools'
        
        Output JSON with: project_overview, file_structure, core_components, technology_stack, tools_analysis, database_schema, key_findings.""",
        
        expected_output="""JSON with: project_overview, file_structure, core_components, tech_stack, tools_analysis, database_schema, key_findings. Valid JSON format.""",
        
        agent=researcher,
        async_execution=False,
        
        # Context dan memory
        context=[],
        
        # Save hasil ke memory untuk agent lain
        output_file="research_results.json"
    )
    
    return research_task

def get_research_context():
    """Get context untuk task ini"""
    return {
        "task_type": "research",
        "focus_areas": [
            "project_structure",
            "core_components", 
            "technology_stack",
            "tools_analysis",
            "database_schema"
        ],
        "output_format": "json_structured"
    }

if __name__ == "__main__":
    # Test task creation
    task = create_research_task()
    print(f"✅ Research Task created")
    print(f"Agent: {task.agent.role}")
    print(f"Expected output: {task.expected_output[:100]}...")
    print(f"Context: {get_research_context()}")
