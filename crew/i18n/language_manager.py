#!/usr/bin/env python3
"""
Internationalization (i18n) Manager untuk CrewAI Documentation System
Menyediakan multi-language support untuk semua agent outputs
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class LanguageManager:
    """
    Manager untuk multi-language support dalam CrewAI system
    """
    
    def __init__(self, default_lang: str = "en"):
        """
        Initialize Language Manager
        
        Args:
            default_lang: Default language code (en, id, es)
        """
        self.default_lang = default_lang
        self.current_lang = default_lang
        self.translations: Dict[str, Dict[str, str]] = {}
        self.translations_dir = Path(__file__).parent / "translations"
        
        # Initialize supported languages
        self.supported_languages = {
            "en": "English",
            "id": "Bahasa Indonesia", 
            "es": "Español"
        }
        
        # Load all translations
        self._load_translations()
    
    def _load_translations(self):
        """Load translation files for all supported languages"""
        for lang_code in self.supported_languages.keys():
            translation_file = self.translations_dir / f"{lang_code}.json"
            
            if translation_file.exists():
                try:
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"⚠️  Failed to load translations for {lang_code}: {e}")
                    self.translations[lang_code] = {}
            else:
                print(f"⚠️  Translation file not found: {translation_file}")
                self.translations[lang_code] = {}
    
    def set_language(self, lang_code: str) -> bool:
        """
        Set current language
        
        Args:
            lang_code: Language code (en, id, es)
            
        Returns:
            bool: True if language was set successfully
        """
        if lang_code in self.supported_languages:
            self.current_lang = lang_code
            return True
        else:
            print(f"❌ Unsupported language: {lang_code}")
            return False
    
    def get_current_language(self) -> str:
        """Get current language code"""
        return self.current_lang
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get dictionary of supported languages"""
        return self.supported_languages
    
    def translate(self, key: str, lang_code: Optional[str] = None) -> str:
        """
        Translate a key to current language
        
        Args:
            key: Translation key
            lang_code: Optional language code override
            
        Returns:
            str: Translated text or original key if translation not found
        """
        if lang_code is None:
            lang_code = self.current_lang
        
        # Get translation
        translation = self.translations.get(lang_code, {}).get(key)
        
        # Fallback to default language
        if translation is None and lang_code != self.default_lang:
            translation = self.translations.get(self.default_lang, {}).get(key)
        
        # Return translation or original key
        return translation or key
    
    def translate_agent_message(self, agent_type: str, message_type: str, 
                              variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Translate agent-specific messages
        
        Args:
            agent_type: Type of agent (researcher, writer, checker)
            message_type: Type of message (goal, instruction, etc.)
            variables: Variables to substitute in translation
            
        Returns:
            str: Translated message with variables substituted
        """
        key = f"{agent_type}.{message_type}"
        message = self.translate(key)
        
        # Substitute variables if provided
        if variables:
            try:
                message = message.format(**variables)
            except (KeyError, ValueError) as e:
                print(f"⚠️  Variable substitution failed for {key}: {e}")
        
        return message
    
    def get_documentation_sections(self) -> Dict[str, str]:
        """
        Get documentation section titles in current language
        
        Returns:
            Dict[str, str]: Dictionary of section titles
        """
        sections_key = "documentation.sections"
        sections = self.translations.get(self.current_lang, {}).get(sections_key, {})
        
        if not sections and self.current_lang != self.default_lang:
            sections = self.translations.get(self.default_lang, {}).get(sections_key, {})
        
        return sections or {
            "overview": "Overview",
            "architecture": "Architecture", 
            "installation": "Installation",
            "usage": "Usage",
            "api_reference": "API Reference",
            "troubleshooting": "Troubleshooting"
        }
    
    def get_agent_roles(self) -> Dict[str, str]:
        """
        Get agent role descriptions in current language
        
        Returns:
            Dict[str, str]: Dictionary of agent role descriptions
        """
        roles_key = "agents.roles"
        roles = self.translations.get(self.current_lang, {}).get(roles_key, {})
        
        if not roles and self.current_lang != self.default_lang:
            roles = self.translations.get(self.default_lang, {}).get(roles_key, {})
        
        return roles or {
            "researcher": "Senior AI Systems Researcher",
            "writer": "Lead Technical Documentation Writer",
            "checker": "Senior Quality Assurance Engineer"
        }
    
    def format_number(self, number: float, lang_code: Optional[str] = None) -> str:
        """
        Format numbers according to locale
        
        Args:
            number: Number to format
            lang_code: Optional language code
            
        Returns:
            str: Formatted number string
        """
        # Simple implementation - can be enhanced with proper locale libraries
        return f"{number:,.2f}"
    
    def format_date(self, date_obj, lang_code: Optional[str] = None) -> str:
        """
        Format dates according to locale
        
        Args:
            date_obj: Date object to format
            lang_code: Optional language code
            
        Returns:
            str: Formatted date string
        """
        # Simple implementation - can be enhanced with proper locale libraries
        return date_obj.strftime("%Y-%m-%d %H:%M:%S")

# Global language manager instance
language_manager = LanguageManager()

def get_language_manager() -> LanguageManager:
    """Get global language manager instance"""
    return language_manager

def set_language(lang_code: str) -> bool:
    """Set global language"""
    return language_manager.set_language(lang_code)

def t(key: str, lang_code: Optional[str] = None) -> str:
    """
    Shortcut for translate function
    
    Args:
        key: Translation key
        lang_code: Optional language code
        
    Returns:
        str: Translated text
    """
    return language_manager.translate(key, lang_code)

if __name__ == "__main__":
    # Test language manager
    lm = LanguageManager()
    
    print("🌍 Testing Language Manager:")
    print(f"Supported languages: {lm.get_supported_languages()}")
    
    # Test English
    lm.set_language("en")
    print(f"English - Researcher role: {lm.translate('agents.roles.researcher')}")
    print(f"English - Documentation: {lm.translate('documentation.title')}")
    
    # Test Indonesian
    lm.set_language("id")
    print(f"Indonesian - Researcher role: {lm.translate('agents.roles.researcher')}")
    print(f"Indonesian - Documentation: {lm.translate('documentation.title')}")
    
    # Test Spanish
    lm.set_language("es")
    print(f"Spanish - Researcher role: {lm.translate('agents.roles.researcher')}")
    print(f"Spanish - Documentation: {lm.translate('documentation.title')}")
