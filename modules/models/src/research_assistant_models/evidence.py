"""Evidence and finding models."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class FindingType(str, Enum):
    """Type of investigation finding."""

    SUPPORT = "support"  # Evidence supports the claim
    CHALLENGE = "challenge"  # Evidence challenges/contradicts the claim
    NEUTRAL = "neutral"  # Evidence is neutral or inconclusive
    CLARIFICATION = "clarification"  # Definitional/conceptual clarification


class Evidence(BaseModel):
    """Evidence item (citation, quote, relevance, credibility)."""

    id: Optional[UUID] = Field(default=None, description="Unique identifier")
    finding_id: Optional[UUID] = Field(default=None, description="Associated finding ID")
    source_category: str = Field(
        ..., description="Category of source (academic, web, etc.)"
    )
    citation_apa: str = Field(..., description="Citation in APA format")
    doi: Optional[str] = Field(default=None, description="DOI if available")
    url: Optional[str] = Field(default=None, description="URL to source")
    relevant_quote: Optional[str] = Field(
        default=None, description="Relevant quoted passage"
    )
    relevance_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="How relevant to claim (0-1)"
    )
    credibility_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Source credibility (0-1)"
    )
    publication_year: Optional[int] = Field(
        default=None, description="Year of publication"
    )
    methodology: Optional[str] = Field(
        default=None, description="Research methodology used"
    )
    sample_size: Optional[str] = Field(default=None, description="Sample size if study")
    created_at: Optional[datetime] = Field(default=None, description="Creation time")

    @field_validator("source_category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate source category."""
        valid_categories = ["academic", "web", "book", "preprint", "dataset", "other"]
        if v not in valid_categories:
            # Allow but warn
            pass
        return v

    class Config:
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "source_category": "academic",
                "citation_apa": "Author, A. (2023). Paper Title. Journal, 10(2), 123-145.",
                "doi": "10.1234/example",
                "relevant_quote": "Our meta-analysis found a 30% reduction...",
                "relevance_score": 0.9,
                "credibility_score": 0.85,
                "publication_year": 2023,
            }
        }


class Finding(BaseModel):
    """Investigation finding (summary, analysis, evidence)."""

    id: Optional[UUID] = Field(default=None, description="Unique identifier")
    investigation_id: Optional[UUID] = Field(
        default=None, description="Investigation ID"
    )
    claim_id: Optional[UUID] = Field(default=None, description="Claim ID")
    finding_type: FindingType = Field(..., description="Type of finding")
    summary: str = Field(..., description="Brief summary of findings")
    detailed_analysis: Optional[str] = Field(
        default=None, description="Detailed analysis text"
    )
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Confidence in finding (0-1)"
    )
    created_at: Optional[datetime] = Field(default=None, description="Creation time")

    # Related data (populated separately)
    evidence: List[Evidence] = Field(
        default_factory=list, description="Supporting evidence items"
    )

    class Config:
        use_enum_values = True
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "finding_type": "support",
                "summary": "Found 5 sources supporting this claim",
                "detailed_analysis": "Multiple large cohort studies show...",
                "confidence": 0.8,
            }
        }
