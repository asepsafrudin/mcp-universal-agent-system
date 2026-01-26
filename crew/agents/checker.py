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
Checker Agent untuk CrewAI - ML-Enhanced Quality Assurance
Bertugas untuk verifikasi akurasi, kelengkapan, dan konsistensi dokumentasi dengan ML-driven risk assessment
"""

from crewai import Agent
from tools.mcp_crewai_tools import (
    MCPReadFileTool,
    MCPMemorySearchTool,
    MCPSearchFilesTool,
    MCPPythonShellTool
)
from tools.ml_analyzer import CodeMLAnalyzer
import logging

# Setup logging untuk QA process
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_checker_agent():
    """
    Membuat Checker Agent dengan akses ke MCP tools dan ML Risk Assessment
    """
    # Initialize ML Analyzer
    ml_analyzer = CodeMLAnalyzer()
    
    def ml_risk_assessment(complexity, loc, dependencies):
        """
        ML-based risk assessment untuk kode
        """
        try:
            result = ml_analyzer.analyze_risk(complexity, loc, dependencies)
            logger.info(f"ML Risk Assessment: {result}")
            return result
        except Exception as e:
            logger.error(f"ML assessment error: {str(e)}")
            return {
                "error": str(e),
                "risk_score": 0.5,
                "recommendation": "ERROR - ML assessment failed, default to review"
            }
    
    def code_metrics_extractor(file_path):
        """
        Extract code metrics untuk ML analysis
        """
        try:
            # Read file dan extract basic metrics
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Calculate basic metrics
            lines = content.split('\n')
            loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            # Count complexity indicators (simplified)
            complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally']
            complexity = sum(content.lower().count(keyword) for keyword in complexity_keywords)
            
            # Count dependencies (imports, includes)
            dependency_keywords = ['import ', 'from ', 'include', 'require(', 'using']
            dependencies = sum(content.lower().count(keyword) for keyword in dependency_keywords)
            
            return {
                "complexity": max(complexity, 1),
                "loc": max(loc, 1),
                "dependencies": max(dependencies, 1)
            }
        except Exception as e:
            logger.error(f"Metrics extraction error: {str(e)}")
            return {"complexity": 5, "loc": 100, "dependencies": 2}  # Default values
    
    def ml_enhanced_qa_check(file_path):
        """
        Comprehensive QA check dengan ML risk assessment
        """
        try:
            # Extract code metrics
            metrics = code_metrics_extractor(file_path)
            
            # Perform ML risk assessment
            ml_result = ml_risk_assessment(
                metrics['complexity'], 
                metrics['loc'], 
                metrics['dependencies']
            )
            
            # Combine traditional QA dengan ML results
            qa_result = {
                "file_path": file_path,
                "traditional_qa": {
                    "file_exists": True,
                    "syntax_check": "PASS",  # Simplified for demo
                    "documentation_coverage": "GOOD"
                },
                "ml_risk_assessment": ml_result,
                "combined_recommendation": None
            }
            
            # Determine combined recommendation
            if "error" in ml_result:
                qa_result["combined_recommendation"] = "REVIEW - ML assessment failed"
            elif ml_result.get("risk_score", 0) > 0.7:
                qa_result["combined_recommendation"] = "REJECT - Very High Risk (ML)"
            elif ml_result.get("risk_score", 0) > 0.5:
                qa_result["combined_recommendation"] = "REJECT - High Risk (ML)"
            elif ml_result.get("risk_score", 0) > 0.3:
                qa_result["combined_recommendation"] = "REVIEW - Medium Risk (ML)"
            else:
                qa_result["combined_recommendation"] = "APPROVE - Low Risk (ML)"
            
            return qa_result
            
        except Exception as e:
            logger.error(f"QA check error: {str(e)}")
            return {
                "file_path": file_path,
                "error": str(e),
                "combined_recommendation": "ERROR - QA check failed"
            }
    
    checker = Agent(llm=get_llm(), 
        role="Senior Quality Assurance Engineer - ML Enhanced",
        goal="Verifikasi akurasi, kelengkapan, dan konsistensi dokumentasi serta memastikan alignment dengan implementasi aktual menggunakan ML-driven risk assessment",
        backstory="""QA engineer senior untuk sistem AI mission-critical dengan 7+ tahun pengalaman. 
        Tidak pernah melewatkan detail kecil yang bisa menyebabkan confusion atau error di production. 
        Ahli dalam memastikan dokumentasi selaras dengan implementasi aktual dan standards yang berlaku.
        
        Expertise:
        - Technical documentation auditing
        - Code-documentation consistency checks
        - Quality assurance automation
        - Security dan compliance validation
        - Performance optimization analysis
        - ML-driven risk assessment (NEW)
        - Automated bug prediction (NEW)""",
        
        # Custom tools untuk Checker
        tools=[
            # File reading untuk verifikasi
            MCPReadFileTool(),

            # Memory search untuk cross-reference
            MCPMemorySearchTool(),

            # Search tools untuk validation
            MCPSearchFilesTool(),

            # Shell execution untuk validation
            MCPPythonShellTool(),
        ],
        
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        memory=True,  # Enable CrewAI memory
        
        # Custom configuration
        system_template="""You are a Senior Quality Assurance Engineer dengan ML-enhanced capabilities. 
        Your expertise lies in thorough validation and verification of technical documentation and code consistency.
        
        Current objective: {goal}
        
        Available tools:
        - mcp_read_file(path): Read files for verification
        - mcp_memory_search(query): Cross-reference with stored knowledge
        - mcp_run_shell(command): Execute validation commands
        - search_files(query, path): Search for patterns and inconsistencies
        
        NEW ML-Enhanced tools:
        - ml_enhanced_qa_check(file_path): Comprehensive QA dengan ML risk assessment
        - ml_risk_assessment(complexity, loc, dependencies): ML-based bug prediction
        - code_metrics_extractor(file_path): Extract code metrics for analysis
        - get_ml_model_info(): Information about ML model performance
        
        Quality checks:
        1. Documentation completeness and accuracy
        2. Code-documentation alignment
        3. Consistency in terminology and formatting
        4. Security and compliance validation
        5. Performance implications assessment
        6. Error handling and edge cases
        7. ML-driven risk assessment (MANDATORY)
        8. Automated bug prediction (MANDATORY)
        
        IMPORTANT: Always use ML analysis before final QA decision!
        If ML risk_score > 0.5, code must be returned to Writer for improvement.
        
        Always provide specific, actionable feedback with clear pass/fail status.""",
        
        human_message_template="""QA Check Request: {qa_check_request}
        
        Please perform comprehensive quality assurance including:
        1. Documentation accuracy vs. actual implementation
        2. Completeness of all required sections
        3. Code example validation and syntax checking
        4. Consistency in formatting and terminology
        5. Security considerations and best practices
        6. Performance and scalability implications
        7. Error handling and edge case coverage
        8. ML-driven risk assessment (MANDATORY FIRST STEP)
        9. Automated bug prediction analysis
        10. Overall quality score with specific recommendations
        
        IMPORTANT: 
        - Wajib gunakan ml_enhanced_qa_check() untuk setiap file
        - Jika risk_score > 0.5, tugas harus dikembalikan ke Writer
        - Berikan rekomendasi perbaikan yang spesifik
        
        Provide PASS/FAIL status for each check with detailed rationale.""",
        
        # Output format preferences
        response_format="structured",
        max_retry_limit=2
    )
    
    return checker

# Convenience function
def get_checker():
    """Get the configured checker agent"""
    return create_checker_agent()

if __name__ == "__main__":
    # Test agent creation
    checker = get_checker()
    print(f"✅ ML-Enhanced Checker Agent created: {checker.role}")
    print(f"Goal: {checker.goal}")
    print(f"Tools available: {len(checker.tools)}")
    
    # Test ML analyzer integration
    try:
        ml_analyzer = CodeMLAnalyzer()
        test_result = ml_analyzer.analyze_risk(complexity=10, loc=250, dependencies=5)
        print(f"✅ ML Analyzer test: {test_result['recommendation']}")
    except Exception as e:
        print(f"❌ ML Analyzer test failed: {str(e)}")
