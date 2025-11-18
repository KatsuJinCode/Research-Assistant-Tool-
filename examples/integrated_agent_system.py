"""
Example: Integrated Agent System

Demonstrates how to use the standalone research-agents module
with your existing database and AI infrastructure via adapters.
"""

import asyncio
import logging
import sys
import os

# Add paths for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../research-agents/src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from research_agent.database import Database
from research_agent.utils.ai_client import AIClient
from research_agent.adapters import DatabaseAdapter, AIAdapter

# Import from standalone module
from research_agents import (
    SupportAgent,
    ChallengeAgent,
    AnalysisAgent,
    AgentConfig,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Main function demonstrating integrated agent system.
    """
    logger.info("Starting integrated agent system...")

    # 1. Initialize existing infrastructure
    logger.info("Connecting to database...")
    db = Database()
    await db.connect()

    logger.info("Initializing AI client...")
    ai_client = AIClient()

    # 2. Create adapters
    logger.info("Creating adapters...")
    db_adapter = DatabaseAdapter(db)
    ai_adapter = AIAdapter(ai_client)

    # 3. Configure agents
    support_config = AgentConfig(
        agent_type="support",
        max_concurrent_investigations=5,
        poll_interval_seconds=30,
        timeout_minutes=30,
    )

    challenge_config = AgentConfig(
        agent_type="challenge",
        max_concurrent_investigations=5,
        poll_interval_seconds=30,
        timeout_minutes=30,
    )

    analysis_config = AgentConfig(
        agent_type="analysis",
        max_concurrent_investigations=3,
        poll_interval_seconds=30,
        timeout_minutes=30,
    )

    # 4. Create agents using adapters
    logger.info("Creating agents...")
    support_agent = SupportAgent(db_adapter, ai_adapter, support_config)
    challenge_agent = ChallengeAgent(db_adapter, ai_adapter, challenge_config)
    analysis_agent = AnalysisAgent(db_adapter, ai_adapter, analysis_config)

    # 5. Start agents (they will run forever, polling for work)
    logger.info("Starting agents...")
    logger.info("Agents will now continuously poll for investigations from the queue")
    logger.info("Press Ctrl+C to stop")

    try:
        await asyncio.gather(
            support_agent.start(),
            challenge_agent.start(),
            analysis_agent.start(),
        )
    except KeyboardInterrupt:
        logger.info("Stopping agents...")
        await support_agent.stop()
        await challenge_agent.stop()
        await analysis_agent.stop()
        logger.info("Agents stopped")
    finally:
        await db.close()
        logger.info("Database connection closed")


async def demo_queue_status():
    """
    Demo: Check queue status using adapters.
    """
    db = Database()
    await db.connect()
    db_adapter = DatabaseAdapter(db)

    status = await db_adapter.get_queue_status()
    logger.info(f"Queue Status: {status}")

    await db.close()


async def demo_clear_stale():
    """
    Demo: Clear stale investigations.
    """
    db = Database()
    await db.connect()
    db_adapter = DatabaseAdapter(db)

    count = await db_adapter.clear_stale_investigations(timeout_minutes=30)
    logger.info(f"Cleared {count} stale investigations")

    await db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Integrated Agent System")
    parser.add_argument(
        "--mode",
        choices=["run", "status", "clear-stale"],
        default="run",
        help="Mode to run: run agents, check status, or clear stale investigations",
    )

    args = parser.parse_args()

    if args.mode == "run":
        asyncio.run(main())
    elif args.mode == "status":
        asyncio.run(demo_queue_status())
    elif args.mode == "clear-stale":
        asyncio.run(demo_clear_stale())
