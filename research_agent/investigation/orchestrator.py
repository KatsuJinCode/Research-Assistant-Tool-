"""
Investigation orchestrator - manages agent pools and scheduling.
"""

import asyncio
import logging
from typing import List, Dict, Any
from research_agent.database import Database
from research_agent.utils.ai_client import AIClient
from research_agent.agents.support_agent import SupportAgent
from research_agent.agents.challenge_agent import ChallengeAgent
from research_agent.agents.analysis_agent import AnalysisAgent
from research_agent.investigation.work_scheduler import WorkScheduler
from research_agent.config import Config


logger = logging.getLogger(__name__)


class InvestigationOrchestrator:
    """
    Manage pool of autonomous agents and background schedulers.

    Agents run indefinitely, pulling work from queue.
    """

    def __init__(self, config: Config, db: Database, ai_client: AIClient):
        """
        Initialize orchestrator.

        Args:
            config: Configuration
            db: Database instance
            ai_client: AI client instance
        """
        self.config = config
        self.db = db
        self.ai = ai_client
        self.scheduler = WorkScheduler(db)

        self.agents: List = []
        self.running = False

    async def start_agent_pool(self):
        """
        Start configured number of each agent type.

        They run autonomously forever.
        """
        logger.info("Starting agent pool...")

        tasks = []

        # Get active agent configurations
        active_agents = self.config.get_active_agents()

        # Start support agents
        if 'support_empirical' in active_agents:
            count = active_agents['support_empirical'].count
            for i in range(count):
                agent = SupportAgent(
                    self.db,
                    self.ai,
                    poll_interval=self.config.system.agent_poll_interval_seconds
                )
                self.agents.append(agent)
                tasks.append(asyncio.create_task(agent.start()))

                logger.info(f"Started Support Agent {i+1}/{count}")

        # Start challenge agents
        if 'challenge_empirical' in active_agents:
            count = active_agents['challenge_empirical'].count
            for i in range(count):
                agent = ChallengeAgent(
                    self.db,
                    self.ai,
                    poll_interval=self.config.system.agent_poll_interval_seconds
                )
                self.agents.append(agent)
                tasks.append(asyncio.create_task(agent.start()))
                logger.info(f"Started Challenge Agent {i+1}/{count}")

        # Start analysis agents
        if 'analysis_definitional' in active_agents:
            count = active_agents['analysis_definitional'].count
            for i in range(count):
                agent = AnalysisAgent(
                    self.db,
                    self.ai,
                    poll_interval=self.config.system.agent_poll_interval_seconds
                )
                self.agents.append(agent)
                tasks.append(asyncio.create_task(agent.start()))
                logger.info(f"Started Analysis Agent {i+1}/{count}")

        logger.info(f"Started {len(self.agents)} agents")

        # Start background schedulers
        tasks.append(asyncio.create_task(self._run_expansion_scheduler()))

        self.running = True

        # Wait for all tasks
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Orchestrator shutting down...")
            await self.stop()

    async def stop(self):
        """Stop all agents and schedulers."""
        logger.info("Stopping orchestrator...")
        self.running = False

        for agent in self.agents:
            await agent.stop()

        logger.info("Orchestrator stopped")

    async def _run_expansion_scheduler(self):
        """
        Run every hour to schedule expansion work.

        Finds claims needing more investigation.
        """
        interval = self.config.system.expansion_scheduler_interval_hours * 3600

        logger.info(
            f"Expansion scheduler started "
            f"(interval: {self.config.system.expansion_scheduler_interval_hours}h)"
        )

        while self.running:
            try:
                await asyncio.sleep(interval)

                if not self.running:
                    break

                logger.info("Running expansion scheduler...")
                count = await self.scheduler.schedule_expansion_investigations()
                logger.info(f"Expansion scheduler completed: {count} investigations scheduled")

            except Exception as e:
                logger.error(f"Error in expansion scheduler: {e}", exc_info=True)
                await asyncio.sleep(60)  # Back off on error

    async def get_status(self) -> Dict[str, Any]:
        """
        Get orchestrator status.

        Returns:
            Status dict
        """
        # Get agent statuses
        agent_statuses = []
        for agent in self.agents:
            status = await agent.get_status()
            agent_statuses.append(status)

        # Get queue status
        queue_status = await self.scheduler.get_queue_status()

        # Get claim statistics
        total_claims = await self.db.fetchval("SELECT COUNT(*) FROM claims")
        verified_claims = await self.db.fetchval(
            "SELECT COUNT(*) FROM claims WHERE status = 'verified'"
        )

        return {
            'running': self.running,
            'total_agents': len(self.agents),
            'agents': agent_statuses,
            'queue': queue_status,
            'claims': {
                'total': total_claims,
                'verified': verified_claims
            }
        }
