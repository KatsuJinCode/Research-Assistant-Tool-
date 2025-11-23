"""
Advanced NLP capabilities for Research Assistant Tool.

Modules:
- contradiction_detector: Detect contradicting claims
- argument_miner: Extract argument structures
- stance_detector: Determine author stance
- fact_checker: Verify factual claims
- entity_extractor: Extract entities and relations
"""

from .contradiction_detector import ContradictionDetector
from .argument_miner import ArgumentMiner
from .stance_detector import StanceDetector
from .fact_checker import FactChecker
from .entity_extractor import EntityExtractor

__all__ = [
    'ContradictionDetector',
    'ArgumentMiner',
    'StanceDetector',
    'FactChecker',
    'EntityExtractor',
]
