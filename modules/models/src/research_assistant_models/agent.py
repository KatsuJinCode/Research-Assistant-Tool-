"""Agent configuration and status models."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from .investigation import AgentFramework


class AgentConfig(BaseModel):
    """Configuration for an agent instance."""

    agent_type: str = Field(..., description="Type of agent (support, challenge, etc.)")
    max_concurrent_investigations: int = Field(
        default=5, ge=1, le=100, description="Max concurrent investigations"
    )
    poll_interval_seconds: int = Field(
        default=30, ge=1, le=3600, description="Polling interval in seconds"
    )
    timeout_minutes: int = Field(
        default=30, ge=1, le=1440, description="Investigation timeout in minutes"
    )
    custom_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Custom agent-specific settings"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "agent_type": "support",
                "max_concurrent_investigations": 5,
                "poll_interval_seconds": 30,
                "timeout_minutes": 30,
            }
        }


class AgentStatus(BaseModel):
    """Runtime status of an agent instance."""

    id: UUID = Field(..., description="Agent instance ID")
    framework: AgentFramework = Field(..., description="Agent framework")
    instance_name: str = Field(..., description="Instance name")
    status: str = Field(
        ..., description="Current status (idle, working, stopped, error)"
    )
    investigations_completed: int = Field(
        default=0, ge=0, description="Total investigations completed"
    )
    investigations_failed: int = Field(
        default=0, ge=0, description="Total investigations failed"
    )
    average_duration_seconds: Optional[float] = Field(
        default=None, ge=0, description="Average investigation duration"
    )
    current_investigation_id: Optional[UUID] = Field(
        default=None, description="Currently processing investigation"
    )
    created_at: datetime = Field(..., description="Agent creation time")
    last_active_at: Optional[datetime] = Field(
        default=None, description="Last activity time"
    )
    uptime_seconds: float = Field(default=0.0, ge=0, description="Total uptime")

    class Config:
        use_enum_values = True
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "framework": "support_empirical",
                "instance_name": "support_agent_1",
                "status": "working",
                "investigations_completed": 42,
                "average_duration_seconds": 125.5,
            }
        }
