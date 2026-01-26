#!/usr/bin/env python3
"""
Check Task untuk CrewAI
Task untuk Checker Agent untuk verifikasi dan quality assurance
"""

from crewai import Task
from agents.checker import get_checker

def create_check_task():
    """
    Membuat task untuk Checker Agent
    """
    # Get checker agent
    checker = get_checker()
    
    check_task = Task(
        description="""QA check on documentation:
        
        1. Verify all sections present, code examples valid
        2. Cross-check tools mentioned vs actual tools in /workspace/tools
        3. Check file paths accuracy
        4. Provide QA report with PASS/FAIL, quality score (1-10), critical issues, recommendations
        
        Save to qa_report.md""",
        
        expected_output="""QA report with: PASS/FAIL status, findings, quality score (1-10), critical issues, recommendations. Structured format.""",
        
        agent=checker,
        async_execution=False,

        # Save laporan ke file
        output_file="qa_report.md"
    )
    
    return check_task

def get_check_context():
    """Get context untuk task ini"""
    return {
        "task_type": "quality_assurance",
        "focus_areas": [
            "documentation_completeness",
            "code_alignment", 
            "technical_accuracy",
            "quality_standards"
        ],
        "output_format": "structured_report",
        "target_file": "qa_report.md"
    }

if __name__ == "__main__":
    # Test task creation
    task = create_check_task()
    print(f"✅ Check Task created")
    print(f"Agent: {task.agent.role}")
    print(f"Expected output: {task.expected_output[:100]}...")
    print(f"Context: {get_check_context()}")
    print(f"Output file: {task.output_file}")
