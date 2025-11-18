"""Data models for research agents module."""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class InvestigationStatus(str, Enum):
    """Status of an investigation."""

    QUEUED = "queued"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class InvestigationFramework(str, Enum):
    """Framework for conducting investigations."""

    SUPPORT = "support"
    CHALLENGE = "challenge"
    ANALYSIS = "analysis"
    GENERAL = "general"


class Claim(BaseModel):
    """A claim extracted from a document."""

    id: UUID
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    qualifiers: Optional[List[str]] = None
    context: Optional[str] = None
    document_id: Optional[UUID] = None
    created_at: datetime


class Investigation(BaseModel):
    """An investigation task for an agent."""

    id: UUID
    claim_id: UUID
    framework: InvestigationFramework
    status: InvestigationStatus
    priority: float = Field(ge=0.0, le=1.0)
    assigned_agent_id: Optional[UUID] = None
    created_at: datetime
    claimed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    # Related data (populated by joins)
    claim: Optional[Claim] = None


class Evidence(BaseModel):
    """Evidence supporting or challenging a claim."""

    id: Optional[UUID] = None
    source: str  # Citation in APA format
    quote: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    supports_claim: bool
    methodology: Optional[str] = None
    sample_size: Optional[str] = None
    publication_year: Optional[int] = None
    created_at: Optional[datetime] = None


class Finding(BaseModel):
    """A finding from an investigation."""

    id: Optional[UUID] = None
    investigation_id: UUID
    summary: str
    confidence_impact: float = Field(ge=-1.0, le=1.0)
    evidence_list: List[Evidence] = Field(default_factory=list)
    reasoning: Optional[str] = None
    created_at: Optional[datetime] = None


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    agent_type: str
    max_concurrent_investigations: int = 5
    poll_interval_seconds: int = 30
    timeout_minutes: int = 30
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class AgentStatus(BaseModel):
    """Status of an agent."""

    agent_id: UUID
    agent_type: str
    status: str  # "active", "idle", "stopped", "error"
    investigations_completed: int = 0
    investigations_failed: int = 0
    current_investigation_id: Optional[UUID] = None
    last_heartbeat: datetime
    uptime_seconds: float = 0.0
