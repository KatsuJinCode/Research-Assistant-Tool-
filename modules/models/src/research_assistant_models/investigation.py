"""Investigation and agent framework models."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class InvestigationStatus(str, Enum):
    """Status of an investigation task."""

    QUEUED = "queued"  # In queue, not yet claimed
    CLAIMED = "claimed"  # Claimed by agent
    IN_PROGRESS = "in_progress"  # Agent actively working
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Failed with error


class AgentFramework(str, Enum):
    """Investigation framework/approach."""

    SUPPORT_EMPIRICAL = "support_empirical"  # Find empirical support
    CHALLENGE_EMPIRICAL = "challenge_empirical"  # Find empirical challenges
    ANALYSIS_DEFINITIONAL = "analysis_definitional"  # Definitional analysis


class Investigation(BaseModel):
    """Investigation task for an agent."""

    id: Optional[UUID] = Field(default=None, description="Unique identifier")
    claim_id: UUID = Field(..., description="Claim being investigated")
    agent_id: Optional[UUID] = Field(default=None, description="Assigned agent ID")
    agent_framework: AgentFramework = Field(..., description="Investigation framework")
    status: InvestigationStatus = Field(
        default=InvestigationStatus.QUEUED, description="Current status"
    )
    priority: int = Field(
        default=50, ge=0, le=100, description="Priority (0-100, higher = more urgent)"
    )
    claimed_at: Optional[datetime] = Field(default=None, description="Claim time")
    started_at: Optional[datetime] = Field(default=None, description="Start time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    duration_seconds: Optional[int] = Field(
        default=None, ge=0, description="Duration in seconds"
    )
    findings_count: int = Field(default=0, ge=0, description="Number of findings")
    evidence_count: int = Field(default=0, ge=0, description="Number of evidence items")
    error_message: Optional[str] = Field(default=None, description="Error if failed")
    retry_count: int = Field(default=0, ge=0, description="Number of retries")
    created_at: Optional[datetime] = Field(default=None, description="Creation time")

    class Config:
        use_enum_values = True
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "claim_id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_framework": "support_empirical",
                "status": "queued",
                "priority": 75,
            }
        }
