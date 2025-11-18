"""Research Agents - Autonomous investigation system for claims verification.

This module provides a standalone research agent system that can be integrated
into applications that need autonomous background research capabilities.

Main components:
- Agents: BaseAgent, SupportAgent, ChallengeAgent, AnalysisAgent
- Interfaces: DatabaseInterface, AIInterface
- Models: Investigation, Claim, Finding, Evidence
"""

from .agents import BaseAgent, SupportAgent, ChallengeAgent, AnalysisAgent
from .interfaces import (
    DatabaseInterface,
    AIInterface,
    Investigation,
    Claim,
    Finding,
    Evidence,
    InvestigationStatus,
    InvestigationFramework,
    AgentConfig,
    AgentStatus,
)

__version__ = "0.1.0"

__all__ = [
    # Agents
    "BaseAgent",
    "SupportAgent",
    "ChallengeAgent",
    "AnalysisAgent",
    # Interfaces
    "DatabaseInterface",
    "AIInterface",
    # Models
    "Investigation",
    "Claim",
    "Finding",
    "Evidence",
    "InvestigationStatus",
    "InvestigationFramework",
    "AgentConfig",
    "AgentStatus",
]
