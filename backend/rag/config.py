"""
RAG Configuration System

Manages user-configurable thresholds for semantic similarity and claim deduplication.
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RAGThresholds:
    """User-configurable thresholds for semantic similarity."""

    # High similarity: Link to existing claim instead of creating new
    identical_threshold: float = 0.95

    # Medium similarity: Create new claim with SIMILAR_TO relationship
    similar_threshold: float = 0.75

    # Low similarity: Show as related but don't auto-link
    related_threshold: float = 0.60

    # Minimum confidence for auto-linking claims
    min_confidence_for_linking: float = 0.70

    def __post_init__(self):
        """Validate thresholds."""
        if not (0 <= self.identical_threshold <= 1):
            raise ValueError("identical_threshold must be between 0 and 1")
        if not (0 <= self.similar_threshold <= 1):
            raise ValueError("similar_threshold must be between 0 and 1")
        if not (0 <= self.related_threshold <= 1):
            raise ValueError("related_threshold must be between 0 and 1")
        if not (0 <= self.min_confidence_for_linking <= 1):
            raise ValueError("min_confidence_for_linking must be between 0 and 1")

        # Ensure logical ordering
        if self.similar_threshold >= self.identical_threshold:
            raise ValueError("similar_threshold must be < identical_threshold")
        if self.related_threshold >= self.similar_threshold:
            raise ValueError("related_threshold must be < similar_threshold")

    def get_category(self, similarity_score: float) -> str:
        """
        Get similarity category for a score.

        Args:
            similarity_score: Similarity score (0-1)

        Returns:
            Category: 'identical', 'similar', 'related', or 'different'
        """
        if similarity_score >= self.identical_threshold:
            return 'identical'
        elif similarity_score >= self.similar_threshold:
            return 'similar'
        elif similarity_score >= self.related_threshold:
            return 'related'
        else:
            return 'different'

    def should_link_existing(self, similarity_score: float) -> bool:
        """Check if claim should link to existing instead of creating new."""
        return similarity_score >= self.identical_threshold

    def should_create_similar_relationship(self, similarity_score: float) -> bool:
        """Check if claim should have SIMILAR_TO relationship."""
        return self.similar_threshold <= similarity_score < self.identical_threshold

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'RAGThresholds':
        """Create from dictionary."""
        return cls(**data)


class RAGConfig:
    """
    Global RAG configuration manager.

    Provides access to user-configurable settings with persistence.
    """

    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / 'config' / 'rag_config.json'

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize RAG config.

        Args:
            config_path: Optional path to config file
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._thresholds = None
        self._load_config()

    def _load_config(self):
        """Load configuration from file or use defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                self._thresholds = RAGThresholds.from_dict(data.get('thresholds', {}))
                logger.info(f"Loaded RAG config from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading RAG config: {e}")
                self._thresholds = RAGThresholds()
        else:
            logger.info("No RAG config found, using defaults")
            self._thresholds = RAGThresholds()

    def save_config(self):
        """Save current configuration to file."""
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'thresholds': self._thresholds.to_dict()
            }

            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved RAG config to {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving RAG config: {e}")
            return False

    @property
    def thresholds(self) -> RAGThresholds:
        """Get current thresholds."""
        return self._thresholds

    def update_thresholds(
        self,
        identical: Optional[float] = None,
        similar: Optional[float] = None,
        related: Optional[float] = None,
        min_confidence: Optional[float] = None
    ) -> bool:
        """
        Update threshold values.

        Args:
            identical: New identical threshold (≥95% by default)
            similar: New similar threshold (75-94% by default)
            related: New related threshold (60-74% by default)
            min_confidence: Minimum confidence for auto-linking

        Returns:
            True if successful, False if validation failed
        """
        try:
            # Create new thresholds with updated values
            new_thresholds = RAGThresholds(
                identical_threshold=identical if identical is not None else self._thresholds.identical_threshold,
                similar_threshold=similar if similar is not None else self._thresholds.similar_threshold,
                related_threshold=related if related is not None else self._thresholds.related_threshold,
                min_confidence_for_linking=min_confidence if min_confidence is not None else self._thresholds.min_confidence_for_linking
            )

            # Validation happens in __post_init__
            self._thresholds = new_thresholds
            self.save_config()

            logger.info(f"Updated RAG thresholds: {new_thresholds.to_dict()}")
            return True

        except ValueError as e:
            logger.error(f"Invalid threshold values: {e}")
            return False

    def reset_to_defaults(self):
        """Reset all thresholds to default values."""
        self._thresholds = RAGThresholds()
        self.save_config()
        logger.info("Reset RAG config to defaults")


# Singleton instance
_config = None


def get_rag_config() -> RAGConfig:
    """Get or create singleton RAG config instance."""
    global _config
    if _config is None:
        _config = RAGConfig()
    return _config
