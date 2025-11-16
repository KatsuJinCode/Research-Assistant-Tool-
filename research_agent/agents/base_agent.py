"""
Base agent class for autonomous investigation.

Agents pull work from the database queue and process investigations.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from research_agent.database import Database
from research_agent.utils.ai_client import AIClient
from research_agent.models import AgentFramework


logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Base class for all investigation agents.

    Implements pull-based work queue pattern:
    1. Pull next investigation from database
    2. Process investigation
    3. Save findings
    4. Mark complete
    5. Repeat
    """

    def __init__(
        self,
        framework: AgentFramework,
        db: Database,
        ai_client: AIClient,
        poll_interval: int = 30
    ):
        """
        Initialize agent.

        Args:
            framework: Agent framework type
            db: Database instance
            ai_client: AI client instance
            poll_interval: Seconds to wait between polls
        """
        self.framework = framework
        self.db = db
        self.ai = ai_client
        self.poll_interval = poll_interval

        self.agent_id: Optional[UUID] = None
        self.instance_name: str = ""
        self.running = False

        # Metrics
        self.investigations_completed = 0
        self.total_duration_seconds = 0

    async def start(self):
        """Start the agent (register and begin work loop)."""
        await self.register()
        logger.info(f"Agent {self.instance_name} started")
        await self.run_forever()

    async def stop(self):
        """Stop the agent."""
        self.running = False
        logger.info(f"Agent {self.instance_name} stopping")

    async def register(self):
        """Register this agent instance in the database."""
        self.instance_name = f"{self.framework.value}_{uuid4().hex[:8]}"

        self.agent_id = await self.db.fetchval(
            """
            INSERT INTO agents (framework, instance_name, status)
            VALUES ($1, $2, 'idle')
            RETURNING id
            """,
            self.framework.value,
            self.instance_name
        )

        logger.info(f"Agent registered: {self.instance_name} (ID: {self.agent_id})")

    async def run_forever(self):
        """Main agent loop - continuously pull and process work."""
        self.running = True

        while self.running:
            try:
                # 1. Get next available work from queue
                investigation_id = await self._get_next_work()

                if investigation_id is None:
                    # No work available, sleep and retry
                    await asyncio.sleep(self.poll_interval)
                    continue

                # 2. Update agent status
                await self._update_status('working')

                # 3. Process investigation
                start_time = time.time()
                await self._process_investigation(investigation_id)
                duration = int(time.time() - start_time)

                # 4. Update metrics
                self.investigations_completed += 1
                self.total_duration_seconds += duration

                # 5. Update agent status back to idle
                await self._update_status('idle')

            except Exception as e:
                logger.error(f"Error in agent loop: {e}", exc_info=True)
                await self._update_status('idle', error=str(e))
                await asyncio.sleep(60)  # Back off on error

    async def _get_next_work(self) -> Optional[UUID]:
        """
        Pull next investigation from work queue.

        Returns:
            Investigation ID, or None if no work available
        """
        return await self.db.get_next_investigation(self.framework.value)

    async def _process_investigation(self, investigation_id: UUID):
        """
        Process an investigation.

        Args:
            investigation_id: Investigation to process
        """
        try:
            # Load investigation and claim
            investigation = await self.db.get_investigation(investigation_id)
            if not investigation:
                logger.error(f"Investigation {investigation_id} not found")
                return

            claim = await self.db.get_claim(investigation['claim_id'])
            if not claim:
                logger.error(f"Claim {investigation['claim_id']} not found")
                return

            # Update status
            await self.db.update_investigation_status(investigation_id, 'in_progress')

            logger.info(
                f"Agent {self.instance_name} processing investigation "
                f"{investigation_id} for claim: {claim['original_text'][:100]}..."
            )

            # Do the investigation (subclass implements this)
            result = await self.investigate(claim)

            # Save findings
            await self._save_findings(investigation_id, claim['id'], result)

            # Mark investigation complete
            duration = int(time.time() - investigation['claimed_at'].timestamp())
            await self.db.mark_investigation_complete(investigation_id, duration)

            # Update claim confidence
            await self.db.update_claim_confidence(claim['id'])

            logger.info(
                f"Investigation {investigation_id} completed in {duration}s"
            )

        except Exception as e:
            logger.error(
                f"Error processing investigation {investigation_id}: {e}",
                exc_info=True
            )
            await self.db.update_investigation_status(
                investigation_id,
                'failed',
                error_message=str(e)
            )

    async def investigate(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform investigation on a claim.

        Subclasses MUST override this method.

        Args:
            claim: Claim dict from database

        Returns:
            Dict with:
                - finding_type: 'support', 'challenge', 'neutral', 'clarification'
                - summary: Brief summary of findings
                - detailed_analysis: Detailed analysis
                - confidence: Confidence in findings (0.0-1.0)
                - evidence: List of evidence dicts
        """
        raise NotImplementedError("Subclasses must implement investigate()")

    async def _save_findings(
        self,
        investigation_id: UUID,
        claim_id: UUID,
        result: Dict[str, Any]
    ):
        """
        Save investigation findings to database.

        Args:
            investigation_id: Investigation ID
            claim_id: Claim ID
            result: Investigation result dict
        """
        # Insert finding
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
            claim_id,
            result['finding_type'],
            result['summary'],
            result.get('detailed_analysis'),
            result.get('confidence')
        )

        # Insert evidence
        evidence_list = result.get('evidence', [])
        for evidence in evidence_list:
            await self.db.execute(
                """
                INSERT INTO evidence (
                    finding_id,
                    source_category,
                    citation_apa,
                    relevant_quote,
                    relevance_score,
                    credibility_score
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                finding_id,
                evidence.get('source_category', 'web'),
                evidence['citation_apa'],
                evidence.get('relevant_quote'),
                evidence.get('relevance_score', 0.8),
                evidence.get('credibility_score', 0.7)
            )

        logger.info(
            f"Saved finding {finding_id} with {len(evidence_list)} evidence items"
        )

    async def _update_status(self, status: str, error: Optional[str] = None):
        """Update agent status in database."""
        if error:
            await self.db.execute(
                """
                UPDATE agents
                SET status = $1, last_active_at = CURRENT_TIMESTAMP, last_error = $2
                WHERE id = $3
                """,
                status, error, self.agent_id
            )
        else:
            await self.db.execute(
                """
                UPDATE agents
                SET status = $1, last_active_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                status, self.agent_id
            )

    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        agent_data = await self.db.fetchrow(
            "SELECT * FROM agents WHERE id = $1",
            self.agent_id
        )

        return {
            'id': self.agent_id,
            'framework': self.framework.value,
            'instance_name': self.instance_name,
            'status': agent_data['status'],
            'investigations_completed': self.investigations_completed,
            'average_duration_seconds': (
                self.total_duration_seconds / self.investigations_completed
                if self.investigations_completed > 0 else None
            ),
            'running': self.running
        }
