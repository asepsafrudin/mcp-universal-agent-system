#!/usr/bin/env python3
"""
Advanced Template Engine untuk CrewAI Documentation System
Menyediakan dynamic content generation dan customizable templates
"""

import json
import os
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateError
from datetime import datetime

class TemplateEngine:
    """
    Advanced Template Engine dengan support untuk dynamic content generation
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize Template Engine
        
        Args:
            templates_dir: Directory untuk template files
        """
        self.templates_dir = Path(templates_dir) if templates_dir else Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=True
        )
        
        # Register custom filters
        self._register_filters()
        
        # Template configurations
        self.template_configs = {
            "documentation": {
                "name": "Documentation Template",
                "description": "Comprehensive technical documentation template",
                "sections": ["overview", "architecture", "installation", "usage", "api", "troubleshooting"]
            },
            "api_reference": {
                "name": "API Reference Template", 
                "description": "API documentation template with examples",
                "sections": ["endpoints", "examples", "authentication", "errors"]
            },
            "quick_start": {
                "name": "Quick Start Guide",
                "description": "Getting started guide template",
                "sections": ["introduction", "setup", "first_steps", "next_steps"]
            }
        }
    
    def _register_filters(self):
        """Register custom Jinja2 filters"""
        
        def format_date(value, format_str="%Y-%m-%d"):
            """Format date filter"""
            if isinstance(value, datetime):
                return value.strftime(format_str)
            return value
        
        def highlight_code(code, language="python"):
            """Syntax highlighting filter"""
            return f"```{language}\n{code}\n```"
        
        def safe_truncate(text, length=100):
            """Safe text truncation"""
            if len(text) <= length:
                return text
            return text[:length] + "..."
        
        def format_number(number, decimal_places=2):
            """Number formatting filter"""
            return f"{number:,.{decimal_places}f}"
        
        # Register filters
        self.jinja_env.filters['format_date'] = format_date
        self.jinja_env.filters['highlight_code'] = highlight_code
        self.jinja_env.filters['safe_truncate'] = safe_truncate
        self.jinja_env.filters['format_number'] = format_number
    
    def get_template_config(self, template_name: str) -> Dict[str, Any]:
        """Get template configuration"""
        return self.template_configs.get(template_name, {})
    
    def list_available_templates(self) -> List[str]:
        """List all available template names"""
        return list(self.template_configs.keys())
    
    def load_template(self, template_name: str) -> str:
        """
        Load template content
        
        Args:
            template_name: Name of the template
            
        Returns:
            str: Template content
        """
        template_file = self.templates_dir / f"{template_name}.md"
        
        if not template_file.exists():
            raise FileNotFoundError(f"Template {template_name} not found")
        
        with open(template_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def render_template(self, template_name: str, data: Dict[str, Any], 
                       custom_filters: Optional[Dict] = None) -> str:
        """
        Render template with data
        
        Args:
            template_name: Name of the template
            data: Data to render in template
            custom_filters: Additional custom filters
            
        Returns:
            str: Rendered content
        """
        try:
            # Load template
            template = self.jinja_env.get_template(f"{template_name}.md")
            
            # Add custom filters if provided
            if custom_filters:
                self.jinja_env.filters.update(custom_filters)
            
            # Add default context
            context = {
                'generated_at': datetime.now(),
                'generated_date': datetime.now().strftime("%Y-%m-%d"),
                'generated_time': datetime.now().strftime("%H:%M:%S"),
                'language': 'en',
                'version': '1.0.0',
                **data
            }
            
            # Render template
            rendered = template.render(**context)
            
            # Clean up any custom filters added temporarily
            if custom_filters:
                for filter_name in custom_filters.keys():
                    if filter_name in self.jinja_env.filters:
                        del self.jinja_env.filters[filter_name]
            
            return rendered
            
        except TemplateError as e:
            raise TemplateError(f"Template rendering failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Template processing failed: {str(e)}")
    
    def create_custom_template(self, template_name: str, content: str) -> bool:
        """
        Create custom template
        
        Args:
            template_name: Name for the template
            content: Template content
            
        Returns:
            bool: Success status
        """
        try:
            template_file = self.templates_dir / f"{template_name}.md"
            
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Add to template configs
            self.template_configs[template_name] = {
                "name": template_name.replace('_', ' ').title(),
                "description": "Custom template",
                "sections": []
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create template: {e}")
            return False
    
    def validate_template(self, template_name: str) -> Dict[str, Any]:
        """
        Validate template syntax and structure
        
        Args:
            template_name: Name of the template
            
        Returns:
            Dict: Validation results
        """
        results = {
            "template_name": template_name,
            "exists": False,
            "syntax_valid": False,
            "sections_found": [],
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check if template exists
            template_file = self.templates_dir / f"{template_name}.md"
            results["exists"] = template_file.exists()
            
            if not results["exists"]:
                results["errors"].append("Template file not found")
                return results
            
            # Load and validate syntax
            content = self.load_template(template_name)
            
            # Basic syntax checks
            if not content.strip():
                results["warnings"].append("Template is empty")
            
            # Find sections (headers)
            headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
            results["sections_found"] = headers
            
            # Check for required variables
            variables = re.findall(r'\{\{([^}]+)\}\}', content)
            results["variables_found"] = list(set(variables))
            
            # Try to render with minimal data
            try:
                self.render_template(template_name, {"test": "data"})
                results["syntax_valid"] = True
            except TemplateError as e:
                results["errors"].append(f"Template syntax error: {str(e)}")
            
        except Exception as e:
            results["errors"].append(f"Validation failed: {str(e)}")
        
        return results
    
    def generate_from_data(self, template_name: str, data: Dict[str, Any], 
                          output_file: Optional[str] = None) -> str:
        """
        Generate content from data using template
        
        Args:
            template_name: Template to use
            data: Data for generation
            output_file: Optional output file path
            
        Returns:
            str: Generated content
        """
        # Validate template first
        validation = self.validate_template(template_name)
        if validation["errors"]:
            raise ValueError(f"Template validation failed: {validation['errors']}")
        
        # Render content
        content = self.render_template(template_name, data)
        
        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return content
    
    def get_template_variables(self, template_name: str) -> List[str]:
        """
        Extract variables used in template
        
        Args:
            template_name: Name of the template
            
        Returns:
            List[str]: List of variable names
        """
        try:
            content = self.load_template(template_name)
            variables = re.findall(r'\{\{\s*([^}]+?)\s*\}\}', content)
            return list(set(variables))
        except Exception:
            return []
    
    def list_templates_with_details(self) -> Dict[str, Dict[str, Any]]:
        """List all templates with their details"""
        details = {}
        
        for template_name in self.list_available_templates():
            config = self.get_template_config(template_name)
            variables = self.get_template_variables(template_name)
            
            details[template_name] = {
                **config,
                "variables": variables,
                "exists": (self.templates_dir / f"{template_name}.md").exists()
            }
        
        return details

# Global template engine instance
template_engine = TemplateEngine()

def get_template_engine() -> TemplateEngine:
    """Get global template engine instance"""
    return template_engine

def render_template(template_name: str, data: Dict[str, Any]) -> str:
    """Render template with data"""
    return template_engine.render_template(template_name, data)

def create_template_from_content(template_name: str, content: str) -> bool:
    """Create new template from content"""
    return template_engine.create_custom_template(template_name, content)

if __name__ == "__main__":
    # Test template engine
    engine = TemplateEngine()
    
    print("🎨 Testing Template Engine...")
    print(f"Available templates: {engine.list_available_templates()}")
    
    # Test template validation
    # validation = engine.validate_template("documentation")
    # print(f"Template validation: {validation}")
    
    # Test variable extraction
    # variables = engine.get_template_variables("documentation")
    # print(f"Template variables: {variables}")
