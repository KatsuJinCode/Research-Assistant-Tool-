"""Report models."""

from typing import List
from pydantic import BaseModel, Field

from .claim import Claim
from .evidence import Finding


class ClaimReport(BaseModel):
    """Comprehensive report for a single claim."""

    claim: Claim = Field(..., description="The claim being reported on")
    findings: List[Finding] = Field(
        default_factory=list, description="All investigation findings"
    )
    overall_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence score (0-1)"
    )
    confidence_label: str = Field(
        ..., description="Human-readable confidence (High, Medium, Low, etc.)"
    )
    support_count: int = Field(default=0, ge=0, description="Supporting findings count")
    challenge_count: int = Field(
        default=0, ge=0, description="Challenging findings count"
    )
    neutral_count: int = Field(default=0, ge=0, description="Neutral findings count")
    clarification_count: int = Field(
        default=0, ge=0, description="Clarification findings count"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "overall_confidence": 0.75,
                "confidence_label": "High",
                "support_count": 5,
                "challenge_count": 2,
                "neutral_count": 1,
            }
        }


class InvestigationReport(BaseModel):
    """Report for a set of investigations."""

    total_claims: int = Field(default=0, ge=0, description="Total claims investigated")
    total_investigations: int = Field(
        default=0, ge=0, description="Total investigations run"
    )
    total_evidence: int = Field(
        default=0, ge=0, description="Total evidence items collected"
    )
    avg_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Average confidence across all claims"
    )
    claims_by_status: dict = Field(
        default_factory=dict, description="Claims grouped by status"
    )
    findings_by_type: dict = Field(
        default_factory=dict, description="Findings grouped by type"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_claims": 50,
                "total_investigations": 150,
                "total_evidence": 450,
                "avg_confidence": 0.68,
            }
        }
