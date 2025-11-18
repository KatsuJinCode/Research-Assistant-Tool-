"""
Database adapter for research-agents module.

Implements the DatabaseInterface using the existing PostgreSQL database.
"""

import logging
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime, timedelta

from research_agent.database import Database

# Import from the standalone research-agents module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../research-agents/src'))

from research_agents import (
    DatabaseInterface,
    Investigation,
    Claim,
    Finding,
    Evidence,
    InvestigationStatus,
    InvestigationFramework,
)


logger = logging.getLogger(__name__)


class DatabaseAdapter(DatabaseInterface):
    """
    Adapter that implements DatabaseInterface using the existing PostgreSQL database.

    This allows the research-agents module to work with the existing database schema.
    """

    def __init__(self, db: Database):
        """
        Initialize adapter.

        Args:
            db: Existing Database instance
        """
        self.db = db

    async def get_next_investigation(
        self, framework: str, agent_id: Optional[UUID] = None
    ) -> Optional[Investigation]:
        """Get the next available investigation from the queue."""
        row = await self.db.fetchrow(
            """
            SELECT i.*, c.original_text, c.normalized_text, c.confidence_score
            FROM investigations i
            JOIN claims c ON i.claim_id = c.id
            WHERE i.framework = $1
              AND i.status = 'queued'
            ORDER BY i.priority DESC, i.created_at ASC
            LIMIT 1
            """,
            framework,
        )

        if not row:
            return None

        # Convert to Investigation object with embedded Claim
        claim = Claim(
            id=row["claim_id"],
            text=row["normalized_text"] or row["original_text"],
            confidence=float(row["confidence_score"]),
            created_at=row["created_at"],
        )

        investigation = Investigation(
            id=row["id"],
            claim_id=row["claim_id"],
            framework=InvestigationFramework(row["framework"]),
            status=InvestigationStatus(row["status"]),
            priority=float(row["priority"]),
            assigned_agent_id=row.get("assigned_agent_id"),
            created_at=row["created_at"],
            claimed_at=row.get("claimed_at"),
            completed_at=row.get("completed_at"),
            error=row.get("error_message"),
            claim=claim,
        )

        return investigation

    async def claim_investigation(
        self, investigation_id: UUID, agent_id: UUID
    ) -> bool:
        """Claim an investigation for processing by an agent."""
        result = await self.db.execute(
            """
            UPDATE investigations
            SET status = 'claimed',
                assigned_agent_id = $2,
                claimed_at = CURRENT_TIMESTAMP
            WHERE id = $1
              AND status = 'queued'
            """,
            investigation_id,
            agent_id,
        )

        # Check if any row was updated
        return result == "UPDATE 1"

    async def update_investigation_status(
        self,
        investigation_id: UUID,
        status: InvestigationStatus,
        error: Optional[str] = None,
    ) -> None:
        """Update the status of an investigation."""
        if error:
            await self.db.execute(
                """
                UPDATE investigations
                SET status = $2, error_message = $3
                WHERE id = $1
                """,
                investigation_id,
                status.value,
                error,
            )
        else:
            await self.db.execute(
                """
                UPDATE investigations
                SET status = $2
                WHERE id = $1
                """,
                investigation_id,
                status.value,
            )

    async def mark_investigation_complete(
        self, investigation_id: UUID, duration_seconds: float
    ) -> None:
        """Mark an investigation as completed."""
        await self.db.execute(
            """
            UPDATE investigations
            SET status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                duration_seconds = $2
            WHERE id = $1
            """,
            investigation_id,
            int(duration_seconds),
        )

    async def get_claim(self, claim_id: UUID) -> Optional[Claim]:
        """Get a claim by ID."""
        row = await self.db.fetchrow(
            """
            SELECT id, original_text, normalized_text, confidence_score,
                   qualifiers, created_at
            FROM claims
            WHERE id = $1
            """,
            claim_id,
        )

        if not row:
            return None

        return Claim(
            id=row["id"],
            text=row["normalized_text"] or row["original_text"],
            confidence=float(row["confidence_score"]),
            qualifiers=row.get("qualifiers"),
            created_at=row["created_at"],
        )

    async def update_claim_confidence(
        self, claim_id: UUID, confidence_delta: float
    ) -> None:
        """Update a claim's confidence score based on new evidence."""
        # Get current confidence
        current = await self.db.fetchval(
            "SELECT confidence_score FROM claims WHERE id = $1",
            claim_id,
        )

        if current is None:
            logger.error(f"Claim {claim_id} not found")
            return

        # Calculate new confidence (clamp to 0.0-1.0)
        new_confidence = max(0.0, min(1.0, current + confidence_delta))

        # Update
        await self.db.execute(
            """
            UPDATE claims
            SET confidence_score = $2,
                last_updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            """,
            claim_id,
            new_confidence,
        )

        logger.info(
            f"Updated claim {claim_id} confidence: {current:.2f} -> {new_confidence:.2f}"
        )

    async def save_finding(
        self, investigation_id: UUID, finding: Finding
    ) -> UUID:
        """Save a finding from an investigation."""
        # Map finding to database schema
        finding_type_map = {
            InvestigationFramework.SUPPORT: "support",
            InvestigationFramework.CHALLENGE: "challenge",
            InvestigationFramework.ANALYSIS: "clarification",
        }

        # Get investigation to determine type
        inv = await self.db.fetchrow(
            "SELECT framework, claim_id FROM investigations WHERE id = $1",
            investigation_id,
        )

        if not inv:
            raise ValueError(f"Investigation {investigation_id} not found")

        finding_type = finding_type_map.get(
            InvestigationFramework(inv["framework"]), "neutral"
        )

        # Calculate confidence from confidence_impact
        confidence = abs(finding.confidence_impact)

        finding_id = await self.db.fetchval(
            """
            INSERT INTO findings (
                investigation_id,
                claim_id,
                finding_type,
                summary,
                detailed_analysis,
                confidence
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            investigation_id,
            inv["claim_id"],
            finding_type,
            finding.summary,
            finding.reasoning,
            confidence,
        )

        return finding_id

    async def save_evidence(
        self, finding_id: UUID, evidence: Evidence
    ) -> UUID:
        """Save evidence associated with a finding."""
        evidence_id = await self.db.fetchval(
            """
            INSERT INTO evidence (
                finding_id,
                source_category,
                citation_apa,
                relevant_quote,
                relevance_score,
                credibility_score
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            finding_id,
            "academic",  # Default category
            evidence.source,
            evidence.quote,
            evidence.relevance_score,
            evidence.relevance_score,  # Use relevance as credibility for now
        )

        return evidence_id

    async def register_agent(
        self,
        agent_type: str,
        agent_config: Dict,
    ) -> UUID:
        """Register a new agent instance."""
        agent_id = await self.db.fetchval(
            """
            INSERT INTO agents (framework, instance_name, status)
            VALUES ($1, $2, 'idle')
            RETURNING id
            """,
            agent_type,
            f"{agent_type}_{agent_config.get('agent_type', 'unknown')}",
        )

        return agent_id

    async def update_agent_heartbeat(
        self, agent_id: UUID, status: Dict
    ) -> None:
        """Update agent heartbeat to show it's alive."""
        await self.db.execute(
            """
            UPDATE agents
            SET status = $2,
                last_active_at = CURRENT_TIMESTAMP,
                metrics = $3
            WHERE id = $1
            """,
            agent_id,
            status.get("status", "idle"),
            status,  # Store full status as JSONB
        )

    async def get_queue_status(self) -> Dict:
        """Get current queue status and metrics."""
        stats = await self.db.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE status = 'queued') as queued,
                COUNT(*) FILTER (WHERE status = 'claimed') as claimed,
                COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'failed') as failed
            FROM investigations
            """
        )

        return dict(stats) if stats else {}

    async def clear_stale_investigations(
        self, timeout_minutes: int = 30
    ) -> int:
        """Clear investigations that have been claimed but not completed."""
        cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)

        result = await self.db.execute(
            """
            UPDATE investigations
            SET status = 'queued',
                assigned_agent_id = NULL,
                claimed_at = NULL,
                error_message = 'Timeout - reset to queue'
            WHERE status IN ('claimed', 'in_progress')
              AND claimed_at < $1
            """,
            cutoff,
        )

        # Parse "UPDATE N" to get count
        count = int(result.split()[-1]) if result else 0
        return count
