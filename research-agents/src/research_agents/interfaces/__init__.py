"""Interfaces for research agents module.

This module defines abstract interfaces that decouple the research agents
from specific implementations of database, AI providers, and other dependencies.
"""

from .database_interface import DatabaseInterface
from .ai_interface import AIInterface
from .models import (
    Investigation,
    Claim,
    Finding,
    Evidence,
    InvestigationStatus,
    InvestigationFramework,
)

__all__ = [
    "DatabaseInterface",
    "AIInterface",
    "Investigation",
    "Claim",
    "Finding",
    "Evidence",
    "InvestigationStatus",
    "InvestigationFramework",
]
