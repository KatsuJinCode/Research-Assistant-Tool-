"""
Agent Transcript Manager - Centralized Activity Logging
=======================================================

This module provides a centralized system for logging and retrieving
full transcripts of background agent activity.

Features:
- In-memory transcript storage with optional file persistence
- Structured logging with timestamps, levels, and metadata
- Agent lifecycle tracking (started, running, completed, failed)
- Transcript retrieval by agent ID
- JSON export for UI display
- Automatic cleanup of old transcripts

Usage:
    from research_agent.transcript_manager import get_transcript_manager

    manager = get_transcript_manager()
    agent_id = manager.create_agent('document_finder', 'Search arXiv for papers')

    manager.log(agent_id, 'info', 'Starting search...')
    manager.log(agent_id, 'success', 'Found 10 papers', {'count': 10})
    manager.complete_agent(agent_id, {'papers': [...]})

    transcript = manager.get_transcript(agent_id)
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class AgentTranscript:
    """Represents the full transcript of a single agent's execution."""

    def __init__(self, agent_id: str, agent_type: str, description: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.description = description
        self.status = 'running'  # running, completed, failed
        self.started_at = datetime.now().isoformat()
        self.completed_at: Optional[str] = None
        self.entries: List[Dict] = []
        self.result: Optional[Dict] = None
        self.error: Optional[str] = None

    def add_entry(self, level: str, message: str, data: Optional[Dict] = None):
        """Add a log entry to the transcript."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,  # info, success, warning, error
            'message': message,
            'data': data or {}
        }
        self.entries.append(entry)

    def complete(self, result: Optional[Dict] = None):
        """Mark agent as completed successfully."""
        self.status = 'completed'
        self.completed_at = datetime.now().isoformat()
        self.result = result

    def fail(self, error: str):
        """Mark agent as failed."""
        self.status = 'failed'
        self.completed_at = datetime.now().isoformat()
        self.error = error

    def to_dict(self) -> Dict:
        """Convert transcript to dictionary for JSON serialization."""
        duration = None
        if self.completed_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            duration = (end - start).total_seconds()

        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'description': self.description,
            'status': self.status,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'duration_seconds': duration,
            'entries': self.entries,
            'entry_count': len(self.entries),
            'result': self.result,
            'error': self.error
        }


class TranscriptManager:
    """
    Centralized manager for all agent transcripts.
    Thread-safe in-memory storage with optional file persistence.
    """

    def __init__(self, persist_to_disk: bool = False, storage_dir: str = "./agent_transcripts"):
        self.transcripts: Dict[str, AgentTranscript] = {}
        self.persist_to_disk = persist_to_disk
        self.storage_dir = Path(storage_dir)
        self.lock = threading.Lock()

        if self.persist_to_disk:
            self.storage_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[TranscriptManager] Initialized (persist={persist_to_disk})")

    def create_agent(self, agent_type: str, description: str, agent_id: Optional[str] = None) -> str:
        """
        Create a new agent transcript.

        Args:
            agent_type: Type of agent (e.g., 'document_finder', 'document_processor')
            description: Human-readable description of what the agent is doing
            agent_id: Optional custom agent ID (auto-generated if not provided)

        Returns:
            agent_id for referencing this transcript
        """
        with self.lock:
            if agent_id is None:
                # Generate unique agent ID
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                counter = len([t for t in self.transcripts.values() if t.agent_type == agent_type])
                agent_id = f"{agent_type}_{timestamp}_{counter}"

            transcript = AgentTranscript(agent_id, agent_type, description)
            self.transcripts[agent_id] = transcript

            logger.info(f"[TranscriptManager] Created agent: {agent_id}")
            return agent_id

    def log(self, agent_id: str, level: str, message: str, data: Optional[Dict] = None):
        """
        Add a log entry to an agent's transcript.

        Args:
            agent_id: Agent identifier
            level: Log level (info, success, warning, error)
            message: Log message
            data: Optional structured data
        """
        with self.lock:
            if agent_id not in self.transcripts:
                logger.warning(f"[TranscriptManager] Unknown agent: {agent_id}")
                return

            self.transcripts[agent_id].add_entry(level, message, data)

            # Optional: Persist to disk after each log
            if self.persist_to_disk:
                self._persist_transcript(agent_id)

    def complete_agent(self, agent_id: str, result: Optional[Dict] = None):
        """
        Mark an agent as completed successfully.

        Args:
            agent_id: Agent identifier
            result: Optional result data from the agent
        """
        with self.lock:
            if agent_id not in self.transcripts:
                logger.warning(f"[TranscriptManager] Unknown agent: {agent_id}")
                return

            self.transcripts[agent_id].complete(result)
            logger.info(f"[TranscriptManager] Agent completed: {agent_id}")

            if self.persist_to_disk:
                self._persist_transcript(agent_id)

    def fail_agent(self, agent_id: str, error: str):
        """
        Mark an agent as failed.

        Args:
            agent_id: Agent identifier
            error: Error message
        """
        with self.lock:
            if agent_id not in self.transcripts:
                logger.warning(f"[TranscriptManager] Unknown agent: {agent_id}")
                return

            self.transcripts[agent_id].fail(error)
            logger.error(f"[TranscriptManager] Agent failed: {agent_id} - {error}")

            if self.persist_to_disk:
                self._persist_transcript(agent_id)

    def get_transcript(self, agent_id: str) -> Optional[Dict]:
        """
        Get the full transcript for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Transcript dictionary or None if not found
        """
        with self.lock:
            if agent_id not in self.transcripts:
                return None
            return self.transcripts[agent_id].to_dict()

    def list_agents(self, agent_type: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """
        List all agents, optionally filtered by type and status.

        Args:
            agent_type: Optional filter by agent type
            status: Optional filter by status (running, completed, failed)

        Returns:
            List of agent summaries
        """
        with self.lock:
            agents = list(self.transcripts.values())

            if agent_type:
                agents = [a for a in agents if a.agent_type == agent_type]

            if status:
                agents = [a for a in agents if a.status == status]

            # Return summaries (not full transcripts)
            return [
                {
                    'agent_id': a.agent_id,
                    'agent_type': a.agent_type,
                    'description': a.description,
                    'status': a.status,
                    'started_at': a.started_at,
                    'completed_at': a.completed_at,
                    'entry_count': len(a.entries),
                    'has_error': a.error is not None
                }
                for a in agents
            ]

    def cleanup_old_agents(self, max_age_hours: int = 24, keep_failed: bool = True):
        """
        Remove old agent transcripts from memory.

        Args:
            max_age_hours: Remove agents older than this many hours
            keep_failed: Keep failed agents regardless of age
        """
        with self.lock:
            now = datetime.now()
            to_remove = []

            for agent_id, transcript in self.transcripts.items():
                started = datetime.fromisoformat(transcript.started_at)
                age_hours = (now - started).total_seconds() / 3600

                if age_hours > max_age_hours:
                    if keep_failed and transcript.status == 'failed':
                        continue
                    to_remove.append(agent_id)

            for agent_id in to_remove:
                del self.transcripts[agent_id]

            if to_remove:
                logger.info(f"[TranscriptManager] Cleaned up {len(to_remove)} old transcripts")

    def _persist_transcript(self, agent_id: str):
        """Save transcript to disk (private method)."""
        try:
            transcript = self.transcripts[agent_id].to_dict()
            filepath = self.storage_dir / f"{agent_id}.json"

            with open(filepath, 'w') as f:
                json.dump(transcript, f, indent=2)

        except Exception as e:
            logger.error(f"[TranscriptManager] Failed to persist transcript: {e}")


# Global instance
_transcript_manager: Optional[TranscriptManager] = None


def get_transcript_manager(persist_to_disk: bool = True) -> TranscriptManager:
    """
    Get or create the global transcript manager instance.

    Args:
        persist_to_disk: Whether to save transcripts to disk (default: True)

    Returns:
        Global TranscriptManager instance

    Note: File persistence is now enabled by default to support provenance tracking.
          All agent activity is saved for full auditability and data lineage.
    """
    global _transcript_manager
    if _transcript_manager is None:
        _transcript_manager = TranscriptManager(persist_to_disk=persist_to_disk)
    return _transcript_manager


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create manager
    manager = get_transcript_manager(persist_to_disk=True)

    # Create agent
    agent_id = manager.create_agent('test_agent', 'Testing transcript system')

    # Log some activity
    manager.log(agent_id, 'info', 'Agent started')
    manager.log(agent_id, 'info', 'Processing step 1', {'progress': 0.25})
    manager.log(agent_id, 'success', 'Step 1 completed')
    manager.log(agent_id, 'warning', 'Found minor issue', {'issue': 'timeout'})
    manager.log(agent_id, 'info', 'Processing step 2', {'progress': 0.75})
    manager.log(agent_id, 'success', 'Step 2 completed')

    # Complete agent
    manager.complete_agent(agent_id, {'total_processed': 100})

    # Retrieve transcript
    transcript = manager.get_transcript(agent_id)
    print(json.dumps(transcript, indent=2))
