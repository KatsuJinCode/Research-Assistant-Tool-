"""
Pydantic models for data validation and serialization.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


class ClaimStatus(str, Enum):
    """Claim status enum."""
    EXTRACTED = "extracted"
    QUEUED = "queued"
    INVESTIGATING = "investigating"
    SUPPORTED = "supported"
    CHALLENGED = "challenged"
    VERIFIED = "verified"
    UNCERTAIN = "uncertain"
    ARCHIVED = "archived"


class FindingType(str, Enum):
    """Finding type enum."""
    SUPPORT = "support"
    CHALLENGE = "challenge"
    NEUTRAL = "neutral"
    CLARIFICATION = "clarification"


class AgentFramework(str, Enum):
    """Agent framework enum."""
    SUPPORT_EMPIRICAL = "support_empirical"
    CHALLENGE_EMPIRICAL = "challenge_empirical"
    ANALYSIS_DEFINITIONAL = "analysis_definitional"


class Document(BaseModel):
    """Document model."""
    id: Optional[UUID] = None
    title: str
    source_type: str
    file_path: Optional[str] = None
    full_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    uploaded_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class Qualifier(BaseModel):
    """Claim qualifier model."""
    qualifier_type: str  # 'modal', 'frequency', 'quantity', 'certainty', 'temporal'
    qualifier_text: str  # The actual word
    semantic_impact: str  # Description of impact

    @validator('qualifier_type')
    def validate_type(cls, v):
        valid_types = ['modal', 'frequency', 'quantity', 'certainty', 'temporal']
        if v not in valid_types:
            raise ValueError(f"qualifier_type must be one of {valid_types}")
        return v


class Claim(BaseModel):
    """Claim model."""
    id: Optional[UUID] = None
    source_document_id: Optional[UUID] = None
    parent_claim_id: Optional[UUID] = None
    original_text: str
    normalized_text: Optional[str] = None
    status: ClaimStatus = ClaimStatus.EXTRACTED
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    priority_score: int = 50
    investigation_count: int = 0
    support_count: int = 0
    challenge_count: int = 0
    neutral_count: int = 0
    created_at: Optional[datetime] = None
    last_investigated_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Related data (not in DB, populated separately)
    qualifiers: List[Qualifier] = []

    class Config:
        use_enum_values = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class Evidence(BaseModel):
    """Evidence model."""
    id: Optional[UUID] = None
    finding_id: Optional[UUID] = None
    source_category: str  # 'academic' or 'web'
    citation_apa: str
    relevant_quote: Optional[str] = None
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    credibility_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    created_at: Optional[datetime] = None

    @validator('source_category')
    def validate_category(cls, v):
        if v not in ['academic', 'web']:
            raise ValueError("source_category must be 'academic' or 'web'")
        return v

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class Finding(BaseModel):
    """Finding model."""
    id: Optional[UUID] = None
    investigation_id: Optional[UUID] = None
    claim_id: Optional[UUID] = None
    finding_type: FindingType
    summary: str
    detailed_analysis: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    created_at: Optional[datetime] = None

    # Related data
    evidence: List[Evidence] = []

    class Config:
        use_enum_values = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class Investigation(BaseModel):
    """Investigation model."""
    id: Optional[UUID] = None
    claim_id: UUID
    agent_id: Optional[UUID] = None
    agent_framework: AgentFramework
    status: str = "queued"
    priority: int = 50
    claimed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    findings_count: int = 0
    evidence_count: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        use_enum_values = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class NormalizationValidation(BaseModel):
    """Normalization validation model."""
    id: Optional[UUID] = None
    claim_id: UUID
    original_text: str
    proposed_normalized: str
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    status: str = "pending"
    user_corrected_text: Optional[str] = None
    created_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class ClaimReport(BaseModel):
    """Report for a single claim."""
    claim: Claim
    findings: List[Finding]
    overall_confidence: float
    confidence_label: str
    support_count: int
    challenge_count: int
    neutral_count: int


class AgentStatus(BaseModel):
    """Agent status information."""
    id: UUID
    framework: AgentFramework
    instance_name: str
    status: str
    investigations_completed: int
    average_duration_seconds: Optional[float] = None
    created_at: datetime
    last_active_at: Optional[datetime] = None

    class Config:
        use_enum_values = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
