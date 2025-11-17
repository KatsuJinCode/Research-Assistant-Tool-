"""
Research Paper APIs for literature discovery.

Provides unified interface to three free research paper databases:
- arXiv: Preprint server (physics, math, CS, etc.)
- CORE: Open access aggregator
- OpenAlex: Comprehensive scholarly database
"""

from .arxiv_client import ArxivClient
from .core_client import CoreClient
from .openalex_client import OpenAlexClient

__all__ = ['ArxivClient', 'CoreClient', 'OpenAlexClient']
