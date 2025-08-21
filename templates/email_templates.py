#!/usr/bin/env python3
"""
Email template system for loading HTML templates and filling placeholders
"""

import os
from typing import Dict, Any

class EmailTemplateLoader:
    def __init__(self):
        self.templates_dir = os.path.join(os.path.dirname(__file__), 'html')
        
    def load_template(self, template_name: str) -> str:
        """Load HTML template from file"""
        template_path = os.path.join(self.templates_dir, f"{template_name}.html")
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
            
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def fill_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Load template and fill in placeholders"""
        template = self.load_template(template_name)
        
        # Replace placeholders with actual values
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            template = template.replace(placeholder, str(value))
            
        return template

# Create global instance
template_loader = EmailTemplateLoader()
