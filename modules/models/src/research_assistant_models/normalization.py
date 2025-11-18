"""Normalization validation models."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class NormalizationValidation(BaseModel):
    """Human validation of claim normalization."""

    id: Optional[UUID] = Field(default=None, description="Unique identifier")
    claim_id: UUID = Field(..., description="Associated claim ID")
    original_text: str = Field(..., description="Original claim text")
    proposed_normalized: str = Field(..., description="AI-proposed normalized text")
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="AI confidence in normalization (0-1)",
    )
    status: str = Field(
        default="pending", description="Validation status (pending, approved, rejected)"
    )
    user_corrected_text: Optional[str] = Field(
        default=None, description="User-corrected version if rejected"
    )
    feedback: Optional[str] = Field(
        default=None, description="User feedback on normalization"
    )
    created_at: Optional[datetime] = Field(default=None, description="Creation time")
    reviewed_at: Optional[datetime] = Field(default=None, description="Review time")
    reviewed_by: Optional[str] = Field(default=None, description="Reviewer identifier")

    class Config:
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "original_text": "Studies show coffee is good for you",
                "proposed_normalized": "Some studies suggest coffee may have health benefits",
                "confidence": 0.85,
                "status": "pending",
            }
        }
