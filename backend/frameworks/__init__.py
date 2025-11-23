"""
Framework System for Domain Customization

This package provides a YAML-based framework system for customizing the research
assistant to different domains (medical, legal, scientific, etc.).

Example usage:
    >>> from backend.frameworks import FrameworkManager
    >>> manager = FrameworkManager()
    >>> manager.set_framework('medical_research')
    >>> framework = manager.get_current_framework()
    >>> print(framework.entity_types)
    ['Disease', 'Treatment', 'Drug', ...]
"""

from backend.frameworks.framework_loader import Framework, load_framework, validate_framework
from backend.frameworks.framework_manager import FrameworkManager

__all__ = [
    'Framework',
    'load_framework',
    'validate_framework',
    'FrameworkManager',
]
