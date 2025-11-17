"""
Research Paper APIs for literature discovery.

Provides unified interface to four free research paper databases:
- arXiv: Preprint server (physics, math, CS, etc.)
- CORE: Open access aggregator
- OpenAlex: Comprehensive scholarly database
- ORKG: Open Research Knowledge Graph (structured comparisons)
"""

from .arxiv_client import ArxivClient
from .core_client import CoreClient
from .openalex_client import OpenAlexClient
from .orkg_client import ORKGClient

__all__ = ['ArxivClient', 'CoreClient', 'OpenAlexClient', 'ORKGClient']
