"""Research Assistant Models - Shared Pydantic models for type-safe data structures.

This module provides all domain models used across the Research Assistant Tool platform.
"""

from .document import Document, ExtractionResult, PageInfo
from .claim import Claim, Qualifier, ClaimStatus
from .evidence import Evidence, Finding, FindingType
from .investigation import Investigation, InvestigationStatus, AgentFramework
from .agent import AgentStatus, AgentConfig
from .report import ClaimReport, InvestigationReport
from .normalization import NormalizationValidation

__version__ = "0.1.0"

__all__ = [
    # Document models
    "Document",
    "ExtractionResult",
    "PageInfo",
    # Claim models
    "Claim",
    "Qualifier",
    "ClaimStatus",
    # Evidence models
    "Evidence",
    "Finding",
    "FindingType",
    # Investigation models
    "Investigation",
    "InvestigationStatus",
    "AgentFramework",
    # Agent models
    "AgentStatus",
    "AgentConfig",
    # Report models
    "ClaimReport",
    "InvestigationReport",
    # Normalization
    "NormalizationValidation",
]
