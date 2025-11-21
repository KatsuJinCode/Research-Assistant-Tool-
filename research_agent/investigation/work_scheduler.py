"""
Work scheduler for investigations.

Creates investigation tasks and adds them to the work queue.
Does NOT spawn agents - agents pull work themselves.
"""

import logging
from typing import List, Dict, Any
from uuid import UUID
from research_agent.database import Database
from research_agent.models import AgentFramework


logger = logging.getLogger(__name__)


class WorkScheduler:
    """
    Create investigation tasks and add them to work queue.

    Agents discover these tasks and pull them from the queue.
    """

    def __init__(self, db: Database):
        """
        Initialize work scheduler.

        Args:
            db: Database instance
        """
        self.db = db

    async def schedule_initial_investigations(self, claim_id: UUID) -> int:
        """
        Schedule initial investigations for a new claim.

        Creates investigation records that agents will discover.

        Args:
            claim_id: Claim ID

        Returns:
            Number of investigations scheduled
        """
        # MVP: Schedule 3 agent types
        frameworks_to_apply = [
            AgentFramework.SUPPORT_EMPIRICAL.value,
            AgentFramework.CHALLENGE_EMPIRICAL.value,
            AgentFramework.ANALYSIS_DEFINITIONAL.value
        ]

        count = 0
        for framework in frameworks_to_apply:
            await self.db.execute(
                """
                INSERT INTO investigations (
                    claim_id,
                    agent_framework,
                    status,
                    priority
                ) VALUES ($1, $2, 'queued', $3)
                """,
                claim_id,
                framework,
                await self._calculate_priority(claim_id)
            )
            count += 1

        logger.info(f"Scheduled {count} investigations for claim {claim_id}")
        return count

    async def schedule_expansion_investigations(self) -> int:
        """
        Find claims that need more investigation.

        Called periodically by background scheduler.

        Returns:
            Number of investigations scheduled
        """
        # Find underinvestigated claims
        underinvestigated = await self.db.fetch(
            """
            SELECT id FROM claims
            WHERE status IN ('extracted', 'queued')
            AND (support_count = 0 OR challenge_count = 0)
            ORDER BY priority_score DESC
            LIMIT 100
            """,
        )

        count = 0
        for claim in underinvestigated:
            count += await self._schedule_missing_investigations(claim['id'])

        logger.info(f"Scheduled {count} expansion investigations")
        return count

    async def _schedule_missing_investigations(self, claim_id: UUID) -> int:
        """
        Schedule missing investigation types for a claim.

        Args:
            claim_id: Claim ID

        Returns:
            Number of investigations scheduled
        """
        claim = await self.db.get_claim(claim_id)
        if not claim:
            return 0

        count = 0

        # Schedule support if missing
        if claim['support_count'] == 0:
            await self.db.execute(
                """
                INSERT INTO investigations (
                    claim_id, agent_framework, status, priority
                ) VALUES ($1, $2, 'queued', $3)
                """,
                claim_id,
                AgentFramework.SUPPORT_EMPIRICAL.value,
                await self._calculate_priority(claim_id)
            )
            count += 1

        # Schedule challenge if missing
        if claim['challenge_count'] == 0:
            await self.db.execute(
                """
                INSERT INTO investigations (
                    claim_id, agent_framework, status, priority
                ) VALUES ($1, $2, 'queued', $3)
                """,
                claim_id,
                AgentFramework.CHALLENGE_EMPIRICAL.value,
                await self._calculate_priority(claim_id)
            )
            count += 1

        # Schedule analysis if needed
        if claim['neutral_count'] == 0:
            await self.db.execute(
                """
                INSERT INTO investigations (
                    claim_id, agent_framework, status, priority
                ) VALUES ($1, $2, 'queued', $3)
                """,
                claim_id,
                AgentFramework.ANALYSIS_DEFINITIONAL.value,
                await self._calculate_priority(claim_id)
            )
            count += 1

        return count

    async def _calculate_priority(self, claim_id: UUID) -> int:
        """
        Calculate investigation priority for a claim.

        Args:
            claim_id: Claim ID

        Returns:
            Priority score (higher = more urgent)
        """
        claim = await self.db.get_claim(claim_id)
        if not claim:
            return 50  # Default priority

        # Use claim's priority score
        return claim['priority_score']

    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current work queue status.

        Returns:
            Status dict with queue statistics
        """
        # Count by status
        queued = await self.db.fetchval(
            "SELECT COUNT(*) FROM investigations WHERE status = 'queued'"
        )

        in_progress = await self.db.fetchval(
            "SELECT COUNT(*) FROM investigations WHERE status IN ('claimed', 'in_progress')"
        )

        completed = await self.db.fetchval(
            "SELECT COUNT(*) FROM investigations WHERE status = 'completed'"
        )

        failed = await self.db.fetchval(
            "SELECT COUNT(*) FROM investigations WHERE status = 'failed'"
        )

        # Count by framework
        by_framework = await self.db.fetch(
            """
            SELECT agent_framework, COUNT(*) as count
            FROM investigations
            WHERE status = 'queued'
            GROUP BY agent_framework
            ORDER BY count DESC
            """
        )

        return {
            'total_queued': queued,
            'in_progress': in_progress,
            'completed': completed,
            'failed': failed,
            'by_framework': {row['agent_framework']: row['count'] for row in by_framework}
        }

    async def clear_stale_investigations(self, timeout_minutes: int = 30) -> int:
        """
        Mark stale in-progress investigations as failed.

        Args:
            timeout_minutes: Timeout in minutes

        Returns:
            Number of investigations marked as failed
        """
        result = await self.db.execute(
            """
            UPDATE investigations
            SET
                status = 'timeout',
                error_message = 'Investigation timeout'
            WHERE status = 'in_progress'
            AND started_at < NOW() - INTERVAL '%s minutes'
            RETURNING id
            """,
            timeout_minutes
        )

        count = len(result) if result else 0
        if count > 0:
            logger.warning(f"Marked {count} stale investigations as timeout")

        return count
