"""
Base agent class for autonomous investigation.

Agents pull work from the database queue and process investigations.
This refactored version uses abstract interfaces instead of direct database access.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime

from ..interfaces import (
    DatabaseInterface,
    AIInterface,
    Investigation,
    Claim,
    Finding,
    Evidence,
    InvestigationFramework,
    InvestigationStatus,
    AgentConfig,
)


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

    This refactored version is decoupled from specific database and AI implementations.
    """

    def __init__(
        self,
        framework: InvestigationFramework,
        db: DatabaseInterface,
        ai: AIInterface,
        config: Optional[AgentConfig] = None,
    ):
        """
        Initialize agent.

        Args:
            framework: Agent framework type
            db: Database interface implementation
            ai: AI interface implementation
            config: Optional agent configuration
        """
        self.framework = framework
        self.db = db
        self.ai = ai
        self.config = config or AgentConfig(agent_type=framework.value)

        self.agent_id: Optional[UUID] = None
        self.instance_name: str = ""
        self.running = False
        self.start_time: Optional[datetime] = None

        # Metrics
        self.investigations_completed = 0
        self.investigations_failed = 0
        self.total_duration_seconds = 0.0

    async def start(self):
        """Start the agent (register and begin work loop)."""
        await self.register()
        self.start_time = datetime.utcnow()
        logger.info(f"Agent {self.instance_name} started")
        await self.run_forever()

    async def stop(self):
        """Stop the agent."""
        self.running = False
        logger.info(f"Agent {self.instance_name} stopping")

    async def register(self):
        """Register this agent instance in the database."""
        self.instance_name = f"{self.framework.value}_{uuid4().hex[:8]}"

        self.agent_id = await self.db.register_agent(
            agent_type=self.framework.value,
            agent_config=self.config.dict(),
        )

        logger.info(f"Agent registered: {self.instance_name} (ID: {self.agent_id})")

    async def run_forever(self):
        """Main agent loop - continuously pull and process work."""
        self.running = True

        while self.running:
            try:
                # 1. Get next available work from queue
                investigation = await self._get_next_work()

                if investigation is None:
                    # No work available, update heartbeat and sleep
                    await self._update_heartbeat("idle")
                    await asyncio.sleep(self.config.poll_interval_seconds)
                    continue

                # 2. Update heartbeat
                await self._update_heartbeat("working", investigation.id)

                # 3. Process investigation
                start_time = time.time()
                success = await self._process_investigation(investigation)
                duration = time.time() - start_time

                # 4. Update metrics
                if success:
                    self.investigations_completed += 1
                else:
                    self.investigations_failed += 1
                self.total_duration_seconds += duration

                # 5. Update heartbeat back to idle
                await self._update_heartbeat("idle")

            except Exception as e:
                logger.error(f"Error in agent loop: {e}", exc_info=True)
                self.investigations_failed += 1
                await self._update_heartbeat("error")
                await asyncio.sleep(60)  # Back off on error

    async def _get_next_work(self) -> Optional[Investigation]:
        """
        Pull next investigation from work queue.

        Returns:
            Investigation object, or None if no work available
        """
        investigation = await self.db.get_next_investigation(
            framework=self.framework.value,
            agent_id=self.agent_id,
        )

        if investigation:
            # Claim the investigation
            claimed = await self.db.claim_investigation(
                investigation.id, self.agent_id
            )
            if claimed:
                return investigation
            else:
                logger.warning(
                    f"Failed to claim investigation {investigation.id}, "
                    "another agent may have taken it"
                )
                return None

        return None

    async def _process_investigation(self, investigation: Investigation) -> bool:
        """
        Process an investigation.

        Args:
            investigation: Investigation to process

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load claim if not already loaded
            if investigation.claim is None:
                claim = await self.db.get_claim(investigation.claim_id)
                if not claim:
                    logger.error(f"Claim {investigation.claim_id} not found")
                    await self.db.update_investigation_status(
                        investigation.id,
                        InvestigationStatus.FAILED,
                        error="Claim not found",
                    )
                    return False
                investigation.claim = claim

            # Update status to in_progress
            await self.db.update_investigation_status(
                investigation.id, InvestigationStatus.IN_PROGRESS
            )

            logger.info(
                f"Agent {self.instance_name} processing investigation "
                f"{investigation.id} for claim: {investigation.claim.text[:100]}..."
            )

            # Do the investigation (subclass implements this)
            finding = await self.investigate(investigation.claim)

            # Save findings
            await self._save_finding(investigation.id, finding)

            # Mark investigation complete
            start = investigation.claimed_at or investigation.created_at
            duration = (datetime.utcnow() - start).total_seconds()
            await self.db.mark_investigation_complete(investigation.id, duration)

            # Update claim confidence based on finding
            await self.db.update_claim_confidence(
                investigation.claim_id, finding.confidence_impact
            )

            logger.info(f"Investigation {investigation.id} completed in {duration:.1f}s")
            return True

        except Exception as e:
            logger.error(
                f"Error processing investigation {investigation.id}: {e}",
                exc_info=True,
            )
            await self.db.update_investigation_status(
                investigation.id, InvestigationStatus.FAILED, error=str(e)
            )
            return False

    async def investigate(self, claim: Claim) -> Finding:
        """
        Perform investigation on a claim.

        Subclasses MUST override this method.

        Args:
            claim: Claim to investigate

        Returns:
            Finding object with results
        """
        raise NotImplementedError("Subclasses must implement investigate()")

    async def _save_finding(self, investigation_id: UUID, finding: Finding):
        """
        Save investigation finding to database.

        Args:
            investigation_id: Investigation ID
            finding: Finding to save
        """
        # Ensure investigation_id is set
        finding.investigation_id = investigation_id

        # Save the finding
        finding_id = await self.db.save_finding(investigation_id, finding)

        # Save evidence
        for evidence in finding.evidence_list:
            await self.db.save_evidence(finding_id, evidence)

        logger.info(
            f"Saved finding {finding_id} with {len(finding.evidence_list)} evidence items"
        )

    async def _update_heartbeat(
        self,
        status: str,
        current_investigation_id: Optional[UUID] = None,
    ):
        """Update agent heartbeat to show it's alive."""
        if not self.agent_id:
            return

        uptime = 0.0
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()

        status_dict = {
            "status": status,
            "investigations_completed": self.investigations_completed,
            "investigations_failed": self.investigations_failed,
            "current_investigation_id": str(current_investigation_id)
            if current_investigation_id
            else None,
            "uptime_seconds": uptime,
        }

        await self.db.update_agent_heartbeat(self.agent_id, status_dict)

    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()

        avg_duration = None
        if self.investigations_completed > 0:
            avg_duration = self.total_duration_seconds / self.investigations_completed

        return {
            "id": str(self.agent_id) if self.agent_id else None,
            "framework": self.framework.value,
            "instance_name": self.instance_name,
            "running": self.running,
            "investigations_completed": self.investigations_completed,
            "investigations_failed": self.investigations_failed,
            "average_duration_seconds": avg_duration,
            "uptime_seconds": uptime,
        }
