#!/usr/bin/env python3
"""
Integration tests untuk CrewAI Workflow
Testing complete workflow dari research hingga documentation
"""

import unittest
import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import MCPDocumentationCrew
from tasks.research_task import create_research_task, get_research_context
from tasks.write_task import create_write_task, get_write_context
from tasks.check_task import create_check_task, get_check_context

class TestWorkflowIntegration(unittest.TestCase):
    """Test suite untuk complete workflow integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.crew = MCPDocumentationCrew()
    
    def test_crew_creation(self):
        """Test crew creation and initialization"""
        self.assertIsNotNone(self.crew)
        self.assertIsNotNone(self.crew.researcher)
        self.assertIsNotNone(self.crew.writer)
        self.assertIsNotNone(self.crew.checker)
        self.assertIsNotNone(self.crew.research_task)
        self.assertIsNotNone(self.crew.write_task)
        self.assertIsNotNone(self.crew.check_task)
    
    def test_crew_configuration(self):
        """Test crew configuration and settings"""
        self.assertIsNotNone(self.crew.crew)
        self.assertEqual(len(self.crew.crew.agents), 3)
        self.assertEqual(len(self.crew.crew.tasks), 3)
        
        # Check agent roles
        agent_roles = [agent.role for agent in self.crew.crew.agents]
        self.assertIn("Senior AI Systems Researcher", agent_roles)
        self.assertIn("Lead Technical Documentation Writer", agent_roles)
        self.assertIn("Senior Quality Assurance Engineer", agent_roles)
    
    def test_task_creation(self):
        """Test task creation and configuration"""
        # Research task
        research_task = create_research_task()
        self.assertIsNotNone(research_task)
        self.assertEqual(research_task.agent.role, "Senior AI Systems Researcher")
        self.assertEqual(research_task.output_file, "research_results.json")
        
        # Write task
        write_task = create_write_task()
        self.assertIsNotNone(write_task)
        self.assertEqual(write_task.agent.role, "Lead Technical Documentation Writer")
        self.assertEqual(write_task.output_file, "/host/Desktop/mcp-documentation.md")
        
        # Check task
        check_task = create_check_task()
        self.assertIsNotNone(check_task)
        self.assertEqual(check_task.agent.role, "Senior Quality Assurance Engineer")
        self.assertEqual(check_task.output_file, "qa_report.md")
    
    def test_task_context(self):
        """Test task context and dependencies"""
        research_context = get_research_context()
        self.assertEqual(research_context["task_type"], "research")
        self.assertIn("project_structure", research_context["focus_areas"])
        
        write_context = get_write_context()
        self.assertEqual(write_context["task_type"], "write")
        self.assertIn("comprehensive_documentation", write_context["focus_areas"])
        
        check_context = get_check_context()
        self.assertEqual(check_context["task_type"], "quality_assurance")
        self.assertIn("documentation_completeness", check_context["focus_areas"])
    
    def test_workflow_sequence(self):
        """Test workflow sequence validation"""
        # Research task should be first
        self.assertEqual(self.crew.crew.tasks[0], self.crew.research_task)
        
        # Write task should be second
        self.assertEqual(self.crew.crew.tasks[1], self.crew.write_task)
        
        # Check task should be third
        self.assertEqual(self.crew.crew.tasks[2], self.crew.check_task)
    
    @patch('main.datetime')
    def test_crew_execution_simulation(self, mock_datetime):
        """Test crew execution with mocked datetime"""
        # Mock datetime to avoid actual time dependency
        mock_datetime.now.return_value = Mock(
            total_seconds=lambda: 120.0,
            strftime=lambda fmt: "2025-12-29 02:12:00"
        )
        
        # Mock crew kickoff to return a mock result
        with patch.object(self.crew.crew, 'kickoff') as mock_kickoff:
            mock_kickoff.return_value = {
                "status": "success",
                "results": "Mock execution completed"
            }
            
            # Test crew execution
            result = self.crew.run_crew()
            self.assertIsNotNone(result)
            mock_kickoff.assert_called_once()

class TestWorkflowPerformance(unittest.TestCase):
    """Test suite untuk workflow performance benchmarking"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.crew = MCPDocumentationCrew()
    
    def test_crew_initialization_performance(self):
        """Test crew initialization performance"""
        start_time = time.time()
        
        # Create new crew instance
        new_crew = MCPDocumentationCrew()
        
        end_time = time.time()
        initialization_time = end_time - start_time
        
        # Initialization should complete within reasonable time
        self.assertLess(initialization_time, 5.0, "Crew initialization took too long")
        print(f"Initialization time: {initialization_time:.2f} seconds")
    
    def test_task_creation_performance(self):
        """Test task creation performance"""
        # Test research task creation
        start_time = time.time()
        research_task = create_research_task()
        research_time = time.time() - start_time
        
        # Test write task creation
        start_time = time.time()
        write_task = create_write_task()
        write_time = time.time() - start_time
        
        # Test check task creation
        start_time = time.time()
        check_task = create_check_task()
        check_time = time.time() - start_time
        
        # All task creation should be fast
        self.assertLess(research_time, 1.0, "Research task creation too slow")
        self.assertLess(write_time, 1.0, "Write task creation too slow")
        self.assertLess(check_time, 1.0, "Check task creation too slow")
        
        print(f"Task creation times: Research={research_time:.3f}s, Write={write_time:.3f}s, Check={check_time:.3f}s")
    
    def test_memory_usage_estimation(self):
        """Test memory usage estimation"""
        # This is a basic test - in production you'd use memory profiling tools
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create crew and tasks
        crew = MCPDocumentationCrew()
        research_task = create_research_task()
        write_task = create_write_task()
        check_task = create_check_task()
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        # Basic memory check (should not use excessive memory)
        self.assertLess(memory_used, 500, f"Memory usage too high: {memory_used:.1f}MB")
        print(f"Memory usage: {memory_used:.1f}MB")

class TestOutputValidation(unittest.TestCase):
    """Test suite untuk output validation"""
    
    def test_research_output_format(self):
        """Test research output format validation"""
        research_task = create_research_task()
        
        # Check expected output format
        expected_sections = [
            "project_overview",
            "file_structure", 
            "core_components",
            "technology_stack",
            "tools_analysis",
            "database_schema",
            "memory_insights",
            "key_findings",
            "recommendations"
        ]
        
        # Output should be JSON structured
        self.assertIn("JSON terstruktur", research_task.expected_output)
        
        # Should include all expected sections
        for section in expected_sections:
            self.assertIn(section, research_task.expected_output)
    
    def test_write_output_format(self):
        """Test write output format validation"""
        write_task = create_write_task()
        
        # Should produce markdown documentation
        self.assertIn("Markdown", write_task.expected_output)
        
        # Should save to specific file
        self.assertEqual(write_task.output_file, "/host/Desktop/mcp-documentation.md")
        
        # Should include memory storage
        self.assertIn("memory", write_task.expected_output.lower())
    
    def test_check_output_format(self):
        """Test check output format validation"""
        check_task = create_check_task()
        
        # Should produce structured report
        self.assertIn("PASS/FAIL", check_task.expected_output)
        self.assertIn("structured", check_task.expected_output.lower())
        
        # Should save to specific file
        self.assertEqual(check_task.output_file, "qa_report.md")
    
    def test_output_file_paths(self):
        """Test output file paths"""
        # Research output
        research_task = create_research_task()
        self.assertEqual(research_task.output_file, "research_results.json")
        
        # Write output
        write_task = create_write_task()
        self.assertEqual(write_task.output_file, "/host/Desktop/mcp-documentation.md")
        
        # Check output
        check_task = create_check_task()
        self.assertEqual(check_task.output_file, "qa_report.md")

def run_workflow_tests():
    """Run all workflow integration tests"""
    print("🔄 Running Workflow Integration Tests...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestOutputValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_workflow_tests()
    sys.exit(0 if success else 1)
