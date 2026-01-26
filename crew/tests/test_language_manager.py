#!/usr/bin/env python3
"""
Unit tests untuk Language Manager
Testing multi-language support dan translation functionality
"""

import unittest
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from i18n.language_manager import LanguageManager

class TestLanguageManager(unittest.TestCase):
    """Test suite untuk Language Manager"""
    
    def setUp(self):
        """Set up test environment"""
        self.lm = LanguageManager()
    
    def test_initialization(self):
        """Test language manager initialization"""
        self.assertIn("en", self.lm.supported_languages)
        self.assertIn("id", self.lm.supported_languages)
        self.assertIn("es", self.lm.supported_languages)
        self.assertEqual(self.lm.current_lang, "en")
    
    def test_set_language(self):
        """Test language setting functionality"""
        # Test valid language
        result = self.lm.set_language("id")
        self.assertTrue(result)
        self.assertEqual(self.lm.current_lang, "id")
        
        # Test invalid language
        result = self.lm.set_language("invalid")
        self.assertFalse(result)
        self.assertEqual(self.lm.current_lang, "id")  # Should remain unchanged
    
    def test_translation_english(self):
        """Test English translations"""
        self.lm.set_language("en")
        
        # Test basic translations
        welcome = self.lm.translate("common.welcome")
        self.assertEqual(welcome, "Welcome to MCP Documentation System")
        
        researcher_role = self.lm.translate("agents.roles.researcher")
        self.assertEqual(researcher_role, "Senior AI Systems Researcher")
    
    def test_translation_indonesian(self):
        """Test Indonesian translations"""
        self.lm.set_language("id")
        
        # Test Indonesian translations
        welcome = self.lm.translate("common.welcome")
        self.assertEqual(welcome, "Selamat Datang di Sistem Dokumentasi MCP")
        
        researcher_role = self.lm.translate("agents.roles.researcher")
        self.assertEqual(researcher_role, "Peneliti Sistem AI Senior")
    
    def test_translation_spanish(self):
        """Test Spanish translations"""
        self.lm.set_language("es")
        
        # Test Spanish translations
        welcome = self.lm.translate("common.welcome")
        self.assertEqual(welcome, "Bienvenido al Sistema de Documentación MCP")
        
        researcher_role = self.lm.translate("agents.roles.researcher")
        self.assertEqual(researcher_role, "Investigador Senior de Sistemas IA")
    
    def test_agent_message_translation(self):
        """Test agent-specific message translation"""
        self.lm.set_language("id")
        
        # Test researcher goal translation
        goal = self.lm.translate_agent_message("researcher", "goal")
        self.assertIn("eksplorasi mendalam", goal)
        
        # Test writer goal translation
        goal = self.lm.translate_agent_message("writer", "goal")
        self.assertIn("dokumentasi teknis", goal)
    
    def test_documentation_sections(self):
        """Test documentation section translations"""
        # Test English sections
        self.lm.set_language("en")
        sections = self.lm.get_documentation_sections()
        self.assertEqual(sections["overview"], "Overview")
        self.assertEqual(sections["architecture"], "Architecture")
        
        # Test Indonesian sections
        self.lm.set_language("id")
        sections = self.lm.get_documentation_sections()
        self.assertEqual(sections["overview"], "Ikhtisar")
        self.assertEqual(sections["architecture"], "Ikhtisar Arsitektur")
    
    def test_agent_roles_translation(self):
        """Test agent roles translation"""
        # Test English roles
        self.lm.set_language("en")
        roles = self.lm.get_agent_roles()
        self.assertEqual(roles["researcher"], "Senior AI Systems Researcher")
        self.assertEqual(roles["writer"], "Lead Technical Documentation Writer")
        
        # Test Indonesian roles
        self.lm.set_language("id")
        roles = self.lm.get_agent_roles()
        self.assertEqual(roles["researcher"], "Peneliti Sistem AI Senior")
        self.assertEqual(roles["writer"], "Penulis Dokumentasi Teknis Utama")
    
    def test_fallback_to_default_language(self):
        """Test fallback to default language when translation missing"""
        # Set to Spanish
        self.lm.set_language("es")
        
        # Request a translation that doesn't exist in Spanish
        non_existent = self.lm.translate("non.existent.key")
        
        # Should fallback to English (default)
        self.assertEqual(non_existent, "non.existent.key")  # Returns key if no fallback
    
    def test_format_number(self):
        """Test number formatting"""
        number = 1234.56
        formatted = self.lm.format_number(number)
        self.assertEqual(formatted, "1,234.56")
    
    def test_supported_languages(self):
        """Test supported languages retrieval"""
        supported = self.lm.get_supported_languages()
        
        expected = {
            "en": "English",
            "id": "Bahasa Indonesia", 
            "es": "Español"
        }
        
        self.assertEqual(supported, expected)

class TestGlobalLanguageManager(unittest.TestCase):
    """Test global language manager instance"""
    
    def test_global_instance(self):
        """Test global language manager instance"""
        from i18n.language_manager import language_manager, get_language_manager, set_language, t
        
        # Test global instance
        self.assertIsInstance(language_manager, LanguageManager)
        
        # Test get function
        global_lm = get_language_manager()
        self.assertIsInstance(global_lm, LanguageManager)
        
        # Test set function
        result = set_language("id")
        self.assertTrue(result)
        self.assertEqual(language_manager.current_lang, "id")
        
        # Test translate shortcut
        result = t("common.welcome")
        self.assertIn("Selamat Datang", result)

def run_tests():
    """Run all language manager tests"""
    print("🌍 Running Language Manager Tests...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestLanguageManager))
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalLanguageManager))
    
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
