"""Claim-related models."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ClaimStatus(str, Enum):
    """Status of a claim in the investigation lifecycle."""

    EXTRACTED = "extracted"  # Newly extracted from document
    QUEUED = "queued"  # Queued for investigation
    INVESTIGATING = "investigating"  # Currently being investigated
    SUPPORTED = "supported"  # Has supporting evidence
    CHALLENGED = "challenged"  # Has challenging evidence
    VERIFIED = "verified"  # High confidence, well-investigated
    UNCERTAIN = "uncertain"  # Conflicting or insufficient evidence
    ARCHIVED = "archived"  # No longer active


class Qualifier(BaseModel):
    """Semantic qualifier that modifies claim meaning (may, might, all, some, etc.)."""

    qualifier_type: str = Field(
        ...,
        description="Type of qualifier (modal, frequency, quantity, certainty, temporal)",
    )
    qualifier_text: str = Field(..., description="The actual qualifier word(s)")
    semantic_impact: str = Field(
        ..., description="How this qualifier affects claim interpretation"
    )
    position: Optional[int] = Field(
        default=None, description="Character position in original text"
    )

    @field_validator("qualifier_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate qualifier type."""
        valid_types = ["modal", "frequency", "quantity", "certainty", "temporal"]
        if v not in valid_types:
            raise ValueError(f"qualifier_type must be one of {valid_types}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "qualifier_type": "modal",
                "qualifier_text": "may",
                "semantic_impact": "Indicates possibility, not certainty",
                "position": 25,
            }
        }


class Claim(BaseModel):
    """Factual claim extracted from a document."""

    id: Optional[UUID] = Field(default=None, description="Unique identifier")
    source_document_id: Optional[UUID] = Field(
        default=None, description="Source document ID"
    )
    parent_claim_id: Optional[UUID] = Field(
        default=None, description="Parent claim if this is a sub-claim"
    )
    original_text: str = Field(..., description="Original extracted text")
    normalized_text: Optional[str] = Field(
        default=None, description="Normalized version preserving qualifiers"
    )
    status: ClaimStatus = Field(
        default=ClaimStatus.EXTRACTED, description="Current status"
    )
    confidence_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Confidence score (0-1)"
    )
    priority_score: int = Field(
        default=50, ge=0, le=100, description="Investigation priority (0-100)"
    )
    investigation_count: int = Field(
        default=0, ge=0, description="Number of completed investigations"
    )
    support_count: int = Field(default=0, ge=0, description="Supporting findings count")
    challenge_count: int = Field(
        default=0, ge=0, description="Challenging findings count"
    )
    neutral_count: int = Field(default=0, ge=0, description="Neutral findings count")
    created_at: Optional[datetime] = Field(default=None, description="Creation time")
    last_investigated_at: Optional[datetime] = Field(
        default=None, description="Last investigation time"
    )
    updated_at: Optional[datetime] = Field(default=None, description="Last update time")

    # Related data (populated separately, not stored directly)
    qualifiers: List[Qualifier] = Field(
        default_factory=list, description="Extracted qualifiers"
    )

    class Config:
        use_enum_values = True
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "original_text": "Coffee consumption reduces risk of type 2 diabetes",
                "normalized_text": "Coffee consumption may reduce risk of type 2 diabetes",
                "status": "extracted",
                "confidence_score": 0.5,
                "priority_score": 75,
            }
        }
