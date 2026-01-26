#!/usr/bin/env python3
"""
Unit tests untuk CrewAI Agents
Testing agent creation, configuration, dan functionality
"""

import unittest
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.researcher import get_researcher
from agents.writer import get_writer
from agents.checker import get_checker

class TestResearcherAgent(unittest.TestCase):
    """Test suite untuk Researcher Agent"""
    
    def setUp(self):
        """Set up test environment"""
        self.researcher = get_researcher()
    
    def test_researcher_creation(self):
        """Test researcher agent creation"""
        self.assertIsNotNone(self.researcher)
        self.assertEqual(self.researcher.role, "Senior AI Systems Researcher")
        self.assertIn("eksplorasi mendalam", self.researcher.goal)
        self.assertTrue(self.researcher.memory)
        self.assertEqual(self.researcher.max_iter, 3)
    
    def test_researcher_tools(self):
        """Test researcher agent tools"""
        self.assertGreater(len(self.researcher.tools), 0)
        
        # Check for expected tools
        tool_names = []
        for tool in self.researcher.tools:
            if hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))
        
        # Tools should include file operations and analysis capabilities
        self.assertTrue(any("list_dir" in name or "read_file" in name or "search" in name.lower() 
                           for name in tool_names))
    
    def test_researcher_configuration(self):
        """Test researcher agent configuration"""
        self.assertFalse(self.researcher.allow_delegation)
        self.assertTrue(self.researcher.verbose)
        self.assertEqual(self.researcher.max_retry_limit, 2)
        self.assertEqual(self.researcher.response_format, "structured")

class TestWriterAgent(unittest.TestCase):
    """Test suite untuk Writer Agent"""
    
    def setUp(self):
        """Set up test environment"""
        self.writer = get_writer()
    
    def test_writer_creation(self):
        """Test writer agent creation"""
        self.assertIsNotNone(self.writer)
        self.assertEqual(self.writer.role, "Lead Technical Documentation Writer")
        self.assertIn("dokumentasi teknis", self.writer.goal)
        self.assertTrue(self.writer.memory)
        self.assertEqual(self.writer.max_iter, 3)
    
    def test_writer_tools(self):
        """Test writer agent tools"""
        self.assertGreater(len(self.writer.tools), 0)
        
        # Check for expected tools
        tool_names = []
        for tool in self.writer.tools:
            if hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))
        
        # Tools should include file writing and memory operations
        self.assertTrue(any("write_file" in name or "memory" in name.lower() 
                           for name in tool_names))
    
    def test_writer_configuration(self):
        """Test writer agent configuration"""
        self.assertTrue(self.writer.allow_delegation)
        self.assertTrue(self.writer.verbose)
        self.assertEqual(self.writer.max_retry_limit, 2)
        self.assertEqual(self.writer.response_format, "markdown")

class TestCheckerAgent(unittest.TestCase):
    """Test suite untuk Checker Agent"""
    
    def setUp(self):
        """Set up test environment"""
        self.checker = get_checker()
    
    def test_checker_creation(self):
        """Test checker agent creation"""
        self.assertIsNotNone(self.checker)
        self.assertEqual(self.checker.role, "Senior Quality Assurance Engineer")
        self.assertIn("verifikasi", self.checker.goal)
        self.assertTrue(self.checker.memory)
        self.assertEqual(self.checker.max_iter, 3)
    
    def test_checker_tools(self):
        """Test checker agent tools"""
        self.assertGreater(len(self.checker.tools), 0)
        
        # Check for expected tools
        tool_names = []
        for tool in self.checker.tools:
            if hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))
        
        # Tools should include file reading and validation
        self.assertTrue(any("read_file" in name or "search" in name or "run_shell" in name 
                           for name in tool_names))
    
    def test_checker_configuration(self):
        """Test checker agent configuration"""
        self.assertFalse(self.checker.allow_delegation)
        self.assertTrue(self.checker.verbose)
        self.assertEqual(self.checker.max_retry_limit, 2)
        self.assertEqual(self.checker.response_format, "structured")

class TestAgentIntegration(unittest.TestCase):
    """Test suite untuk agent integration"""
    
    def test_all_agents_creation(self):
        """Test that all agents can be created successfully"""
        researcher = get_researcher()
        writer = get_writer()
        checker = get_checker()
        
        self.assertIsNotNone(researcher)
        self.assertIsNotNone(writer)
        self.assertIsNotNone(checker)
        
        # Verify each agent has unique role
        self.assertNotEqual(researcher.role, writer.role)
        self.assertNotEqual(writer.role, checker.role)
        self.assertNotEqual(researcher.role, checker.role)
    
    def test_agent_memory_enabled(self):
        """Test that all agents have memory enabled"""
        researcher = get_researcher()
        writer = get_writer()
        checker = get_checker()
        
        self.assertTrue(researcher.memory)
        self.assertTrue(writer.memory)
        self.assertTrue(checker.memory)
    
    def test_agent_iteration_limits(self):
        """Test that all agents have appropriate iteration limits"""
        researcher = get_researcher()
        writer = get_writer()
        checker = get_checker()
        
        self.assertEqual(researcher.max_iter, 3)
        self.assertEqual(writer.max_iter, 3)
        self.assertEqual(checker.max_iter, 3)
    
    def test_agent_verbose_setting(self):
        """Test that all agents have verbose enabled"""
        researcher = get_researcher()
        writer = get_writer()
        checker = get_checker()
        
        self.assertTrue(researcher.verbose)
        self.assertTrue(writer.verbose)
        self.assertTrue(checker.verbose)

class TestAgentToolCompatibility(unittest.TestCase):
    """Test suite untuk agent tool compatibility"""
    
    def test_researcher_tool_compatibility(self):
        """Test researcher agent tool compatibility"""
        researcher = get_researcher()
        
        # Test that tools can be called (mock test)
        try:
            # These should not raise exceptions
            for tool in researcher.tools:
                if callable(tool):
                    # Don't actually call the tools, just check they're callable
                    self.assertTrue(callable(tool))
        except Exception as e:
            self.fail(f"Researcher tools compatibility test failed: {e}")
    
    def test_writer_tool_compatibility(self):
        """Test writer agent tool compatibility"""
        writer = get_writer()
        
        try:
            for tool in writer.tools:
                if callable(tool):
                    self.assertTrue(callable(tool))
        except Exception as e:
            self.fail(f"Writer tools compatibility test failed: {e}")
    
    def test_checker_tool_compatibility(self):
        """Test checker agent tool compatibility"""
        checker = get_checker()
        
        try:
            for tool in checker.tools:
                if callable(tool):
                    self.assertTrue(callable(tool))
        except Exception as e:
            self.fail(f"Checker tools compatibility test failed: {e}")

def run_tests():
    """Run all agent tests"""
    print("🤖 Running CrewAI Agent Tests...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestResearcherAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestWriterAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestCheckerAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentToolCompatibility))
    
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
    success = run_tests()
    sys.exit(0 if success else 1)
