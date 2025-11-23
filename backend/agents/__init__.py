"""
Custom Agent Framework

Provides template system, plugin manager, and testing tools for user-defined agents.
"""

from .agent_template import AgentTemplate, AgentExecutor
from .plugin_manager import PluginManager
from .agent_tester import AgentTester

__all__ = ['AgentTemplate', 'AgentExecutor', 'PluginManager', 'AgentTester']
