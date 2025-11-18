"""
Adapters for integrating research-agents module with the main application.

These adapters implement the abstract interfaces required by the research-agents
module using the existing database and AI infrastructure.
"""

from .database_adapter import DatabaseAdapter
from .ai_adapter import AIAdapter

__all__ = ["DatabaseAdapter", "AIAdapter"]
