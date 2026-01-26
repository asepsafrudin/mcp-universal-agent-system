#!/usr/bin/env python3

import sys
import os
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from llm_config import get_llm
except ImportError:
    # Fallback if running from root
    sys.path.append(os.getcwd())
    from llm_config import get_llm

"""
Researcher Agent untuk CrewAI - ML-Enhanced Systems Analysis
Bertugas untuk eksplorasi mendalam struktur proyek MCP dengan fokus pada analisis arsitektur ML dan pemilihan library
"""

from crewai import Agent
from tools.mcp_crewai_tools import (
    MCPListDirTool,
    MCPReadFileTool,
    MCPMemorySearchTool,
    MCPSearchFilesTool,
    MCPPythonShellTool
)

def create_researcher_agent():
    """
    Membuat Researcher Agent dengan fokus pada ML Architecture Analysis
    """
    researcher = Agent(llm=get_llm(), 
        role="Senior AI Systems Researcher - ML Architecture Specialist",
        goal="Eksplorasi mendalam struktur proyek MCP dengan fokus pada analisis arsitektur ML, pemilihan library, dan identifikasi komponen kritis untuk dokumentasi teknis yang komprehensif",
        backstory="""Ahli arsitektur AI dengan 10+ tahun pengalaman dalam sistem berbasis MCP dan memory hybrid. 
        Spesialis dalam analisis struktur kode kompleks, pattern recognition, dan machine learning architecture.
        Ahli dalam evaluasi library ML dan identifikasi solusi terbaik untuk berbagai use case.
        Selalu mencari detail teknis yang relevan untuk dokumentasi yang akurat dan mendalam.
        
        Expertise:
        - Arsitektur sistem distributed dan ML pipelines
        - Pattern recognition dalam kode dan data
        - ML library evaluation dan selection (scikit-learn, pandas, TensorFlow, etc.)
        - Performance analysis dan optimization strategies
        - Documentation teknis otomatis
        - Integration analysis untuk ML components""",
        
        # Custom tools untuk Researcher
        tools=[
            # File system tools
            MCPListDirTool(),
            MCPReadFileTool(),

            # Memory tools untuk context
            MCPMemorySearchTool(),

            # Advanced analysis tools
            MCPSearchFilesTool(),

            # Shell execution untuk analysis
            MCPPythonShellTool(),
        ],
        
        verbose=True,
        allow_delegation=False,
        max_iter=3,  # Prevent infinite loops
        memory=True,  # Enable CrewAI memory
        
        # Custom configuration
        system_template="""You are a Senior AI Systems Researcher dengan expertise dalam ML Architecture Analysis. 
        Your expertise lies in deep code analysis, architectural understanding, dan ML library evaluation.
        
        Current objective: {goal}
        
        Available tools:
        - mcp_list_dir(path): List directory contents
        - mcp_read_file(path): Read file contents  
        - mcp_memory_search(query): Search previous findings
        - mcp_search_files(query, path): Search for patterns in files
        - mcp_run_python(command): Execute python commands
        
        NEW ML-Focused tools:
        - check_ml_library_versions(): Verify ML library availability and versions
        - analyze_ml_dependencies(): Identify ML dependencies in codebase
        - evaluate_ml_architecture(): Assess ML implementation quality
        
        ML Architecture Analysis Guidelines:
        1. Start with high-level structure
        2. Identify ML components dan dependencies
        3. Evaluate library choices (scikit-learn vs alternatives)
        4. Assess model training dan deployment strategies
        5. Look for performance bottlenecks dan optimization opportunities
        6. Document ML architecture patterns dan best practices
        7. Save ML-specific findings untuk other agents
        
        Provide structured analysis dengan ML architecture insights.""",
        
        human_message_template="""ML Architecture Research Request: {research_request}
        
        Please provide comprehensive analysis covering:
        1. Project structure overview dengan ML components focus
        2. Core ML components identification (models, preprocessing, evaluation)
        3. Technology stack analysis (ML libraries, frameworks, tools)
        4. ML architecture patterns dan data flow analysis
        5. Library selection rationale (why scikit-learn, pandas, etc.)
        6. Performance considerations untuk ML components
        7. Integration analysis between traditional code dan ML parts
        8. Security considerations untuk ML pipeline
        9. Scalability assessment untuk ML components
        10. Key findings dan ML-specific recommendations
        
        Focus on ML architecture decisions dan technical implementation details.""",
        
        # Output format preferences
        response_format="structured",
        max_retry_limit=2
    )
    
    return researcher

# Convenience function
def get_researcher():
    """Get the configured researcher agent"""
    return create_researcher_agent()

if __name__ == "__main__":
    # Test agent creation
    researcher = get_researcher()
    print(f"✅ ML-Enhanced Researcher Agent created: {researcher.role}")
    print(f"Goal: {researcher.goal}")
    print(f"Tools available: {len(researcher.tools)}")
    
    # Test ML library check
    try:
        import sklearn
        import pandas
        print(f"✅ ML Libraries available: scikit-learn {sklearn.__version__}, pandas {pandas.__version__}")
    except ImportError as e:
        print(f"⚠️ Some ML libraries missing: {str(e)}")
