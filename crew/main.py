#!/usr/bin/env python3
"""
Main Execution Script untuk CrewAI 3-Agent System
Mengintegrasikan Researcher, Writer, dan Checker untuk dokumentasi otomatis
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add current directory to Python path
sys.path.append(os.path.dirname(__file__))

from crewai import Crew, Process

# Import agents
from agents.researcher import get_researcher
from agents.writer import get_writer
from agents.checker import get_checker

# Import tasks
from tasks.research_task import create_research_task
from tasks.write_task import create_write_task
from tasks.check_task import create_check_task

class MCPDocumentationCrew:
    """
    CrewAI system untuk dokumentasi otomatis proyek MCP
    """
    
    def __init__(self):
        """Initialize crew dengan semua agents dan tasks"""
        print("🚀 Initializing MCP Documentation CrewAI System...")
        
        # Initialize agents
        self.researcher = get_researcher()
        self.writer = get_writer()
        self.checker = get_checker()
        
        # Initialize tasks
        self.research_task = create_research_task()
        self.write_task = create_write_task()
        self.check_task = create_check_task()
        
        print(f"✅ Agents loaded:")
        print(f"   - {self.researcher.role}")
        print(f"   - {self.writer.role}")
        print(f"   - {self.checker.role}")

        # Create crew
        self.crew = self._create_crew()
        
    def _create_crew(self):
        """Create CrewAI crew dengan agents dan tasks"""
        crew = Crew(
            agents=[self.researcher, self.writer, self.checker],
            tasks=[self.research_task, self.write_task, self.check_task],
            process=Process.sequential,
            verbose=True,  # Enable verbose logging
            memory=True,  # Enable CrewAI memory
            cache=True,
            max_rpm=2,  # Rate limiting (lowered for free tier)
            max_execution_time=600,  # 10 minutes max execution
            max_iter=2,  # Limit iterations to save tokens

            # Function calling for better tool usage
            function_calling_llm=None,  # Use default

            # Output configurations
            output_log_file="crew_execution.log"
        )
        
        return crew
    
    def run_crew(self):
        """Execute the complete crew workflow"""
        print("🚀 Starting MCP Documentation CrewAI execution...")
        print("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Kickoff crew execution
            result = self.crew.kickoff()
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            print("\n" + "=" * 60)
            print("✅ CREWAI EXECUTION COMPLETED!")
            print(f"⏱️  Total execution time: {execution_time:.2f} seconds")
            print(f"📁 Results location: output/")
            print("\n📋 Summary of deliverables:")
            
            # Check what files were created
            self._check_outputs()
            
            return result
            
        except Exception as e:
            with open("error.log", "w") as f:
                f.write(f"Crew execution failed: {str(e)}\n")
                import traceback
                traceback.print_exc(file=f)
            # print(f"\n❌ Crew execution failed: {str(e)}") # Commented out to avoid recursion error
            return None
    
    def _check_outputs(self):
        """Check what outputs were created"""
        outputs = []
        
        # Check documentation file
        doc_path = "output/mcp-documentation.md"
        if os.path.exists(doc_path):
            size = os.path.getsize(doc_path)
            outputs.append(f"📄 Documentation: {doc_path} ({size:,} bytes)")
        
        # Check QA report
        qa_path = "qa_report.md"
        if os.path.exists(qa_path):
            size = os.path.getsize(qa_path)
            outputs.append(f"📊 QA Report: {qa_path} ({size:,} bytes)")
        
        # Check research results
        research_path = "research_results.json"
        if os.path.exists(research_path):
            size = os.path.getsize(research_path)
            outputs.append(f"🔍 Research Data: {research_path} ({size:,} bytes)")
        
        # Check execution log
        log_path = "crew_execution.log"
        if os.path.exists(log_path):
            size = os.path.getsize(log_path)
            outputs.append(f"📝 Execution Log: {log_path} ({size:,} bytes)")
        
        if outputs:
            for output in outputs:
                print(f"   {output}")
        else:
            print("   ⚠️  No output files found!")
    
    def validate_setup(self):
        """Validate crew setup before execution"""
        print("🔍 Validating crew setup...")
        
        # Check agents
        if not all([self.researcher, self.writer, self.checker]):
            print("❌ Missing agents!")
            return False
        
        # Check tasks
        if not all([self.research_task, self.write_task, self.check_task]):
            print("❌ Missing tasks!")
            return False
        
        # Test MCP connection
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from shared.mcp_client import test_mcp_connection
            if test_mcp_connection():
                print("✅ MCP connection validated")
            else:
                print("⚠️  MCP connection failed - continuing anyway")
        except Exception as e:
            print(f"⚠️  MCP connection test failed: {e}")
        
        print("✅ Crew setup validation completed")
        return True

def run_crew():
    """
    Main function untuk menjalankan crew
    """
    print("🎯 CREWAI 3-AGENT MCP DOCUMENTATION SYSTEM")
    print("=" * 60)
    print("🔬 Research → ✍️ Write → ✅ Check workflow")
    print("=" * 60)
    
    # Create crew instance
    crew_system = MCPDocumentationCrew()
    
    # Validate setup
    if not crew_system.validate_setup():
        print("❌ Setup validation failed. Please check configuration.")
        return False
    
    # Run crew
    result = crew_system.run_crew()
    
    if result:
        print("\n🎉 SUCCESS! MCP Documentation CrewAI completed!")
        print("\n📁 Check the following locations for results:")
        print("   - output/mcp-documentation.md")
        print("   - qa_report.md")
        print("   - research_results.json")
        print("\n🔄 To run again: python main.py")
        return True
    else:
        print("\n❌ FAILED! Please check the error messages above.")
        return False

if __name__ == "__main__":
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the crew
    success = run_crew()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
