"""Abstract database interface for research agents."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime

from .models import Investigation, Claim, Finding, Evidence, InvestigationStatus


class DatabaseInterface(ABC):
    """Abstract interface for database operations required by research agents.

    This interface defines all database operations that agents need to perform.
    Concrete implementations can use PostgreSQL, SQLite, or any other database.
    """

    # Investigation Queue Operations

    @abstractmethod
    async def get_next_investigation(
        self, framework: str, agent_id: Optional[UUID] = None
    ) -> Optional[Investigation]:
        """Get the next available investigation from the queue.

        Args:
            framework: The investigation framework (e.g., 'support', 'challenge', 'analysis')
            agent_id: Optional agent ID to claim the investigation

        Returns:
            Investigation object if available, None otherwise
        """
        pass

    @abstractmethod
    async def claim_investigation(
        self, investigation_id: UUID, agent_id: UUID
    ) -> bool:
        """Claim an investigation for processing by an agent.

        Args:
            investigation_id: ID of the investigation to claim
            agent_id: ID of the agent claiming the investigation

        Returns:
            True if successfully claimed, False otherwise
        """
        pass

    @abstractmethod
    async def update_investigation_status(
        self,
        investigation_id: UUID,
        status: InvestigationStatus,
        error: Optional[str] = None,
    ) -> None:
        """Update the status of an investigation.

        Args:
            investigation_id: ID of the investigation
            status: New status
            error: Optional error message if status is failed
        """
        pass

    @abstractmethod
    async def mark_investigation_complete(
        self, investigation_id: UUID, duration_seconds: float
    ) -> None:
        """Mark an investigation as completed.

        Args:
            investigation_id: ID of the investigation
            duration_seconds: How long the investigation took
        """
        pass

    # Claim Operations

    @abstractmethod
    async def get_claim(self, claim_id: UUID) -> Optional[Claim]:
        """Get a claim by ID.

        Args:
            claim_id: ID of the claim

        Returns:
            Claim object if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_claim_confidence(
        self, claim_id: UUID, confidence_delta: float
    ) -> None:
        """Update a claim's confidence score based on new evidence.

        Args:
            claim_id: ID of the claim
            confidence_delta: Amount to adjust confidence (-1.0 to 1.0)
        """
        pass

    # Finding and Evidence Operations

    @abstractmethod
    async def save_finding(
        self, investigation_id: UUID, finding: Finding
    ) -> UUID:
        """Save a finding from an investigation.

        Args:
            investigation_id: ID of the investigation
            finding: Finding object to save

        Returns:
            ID of the saved finding
        """
        pass

    @abstractmethod
    async def save_evidence(
        self, finding_id: UUID, evidence: Evidence
    ) -> UUID:
        """Save evidence associated with a finding.

        Args:
            finding_id: ID of the finding
            evidence: Evidence object to save

        Returns:
            ID of the saved evidence
        """
        pass

    # Agent Registration and Tracking

    @abstractmethod
    async def register_agent(
        self,
        agent_type: str,
        agent_config: Dict,
    ) -> UUID:
        """Register a new agent instance.

        Args:
            agent_type: Type of agent (e.g., 'support', 'challenge')
            agent_config: Configuration dictionary

        Returns:
            ID of the registered agent
        """
        pass

    @abstractmethod
    async def update_agent_heartbeat(
        self, agent_id: UUID, status: Dict
    ) -> None:
        """Update agent heartbeat to show it's alive.

        Args:
            agent_id: ID of the agent
            status: Status dictionary with metrics
        """
        pass

    # Queue Management

    @abstractmethod
    async def get_queue_status(self) -> Dict:
        """Get current queue status and metrics.

        Returns:
            Dictionary with queue statistics
        """
        pass

    @abstractmethod
    async def clear_stale_investigations(
        self, timeout_minutes: int = 30
    ) -> int:
        """Clear investigations that have been claimed but not completed.

        Args:
            timeout_minutes: How long before an investigation is considered stale

        Returns:
            Number of investigations cleared
        """
        pass
