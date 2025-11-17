"""
Graph Enrichment Modules

Modules for enriching the knowledge graph with additional context:
- Sentence-level tracking
- Evidence integration
- Agent tracking
- Citation networks
"""

from .sentence_tracker import SentenceTracker
from .evidence_manager import EvidenceManager
from .agent_tracker import AgentTracker
from .citation_network import CitationNetwork

__all__ = [
    'SentenceTracker',
    'EvidenceManager',
    'AgentTracker',
    'CitationNetwork'
]
