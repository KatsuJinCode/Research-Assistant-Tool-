"""
Unit tests for RAG configuration system.
"""

import pytest
import json
import tempfile
from pathlib import Path

from backend.rag.config import RAGThresholds, RAGConfig


class TestRAGThresholds:
    """Test RAGThresholds dataclass."""

    def test_default_thresholds(self):
        """Test default threshold values."""
        thresholds = RAGThresholds()

        assert thresholds.identical_threshold == 0.95
        assert thresholds.similar_threshold == 0.75
        assert thresholds.related_threshold == 0.60
        assert thresholds.min_confidence_for_linking == 0.70

    def test_custom_thresholds(self):
        """Test creating thresholds with custom values."""
        thresholds = RAGThresholds(
            identical_threshold=0.98,
            similar_threshold=0.80,
            related_threshold=0.65,
            min_confidence_for_linking=0.75
        )

        assert thresholds.identical_threshold == 0.98
        assert thresholds.similar_threshold == 0.80
        assert thresholds.related_threshold == 0.65
        assert thresholds.min_confidence_for_linking == 0.75

    def test_invalid_range_validation(self):
        """Test that thresholds must be between 0 and 1."""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            RAGThresholds(identical_threshold=1.5)

        with pytest.raises(ValueError, match="must be between 0 and 1"):
            RAGThresholds(similar_threshold=-0.1)

    def test_logical_ordering_validation(self):
        """Test that thresholds maintain logical ordering."""
        # similar >= identical should fail
        with pytest.raises(ValueError, match="similar_threshold must be < identical_threshold"):
            RAGThresholds(identical_threshold=0.75, similar_threshold=0.95)

        # related >= similar should fail
        with pytest.raises(ValueError, match="related_threshold must be < similar_threshold"):
            RAGThresholds(similar_threshold=0.60, related_threshold=0.75)

    def test_get_category(self):
        """Test similarity category detection."""
        thresholds = RAGThresholds()

        assert thresholds.get_category(0.97) == 'identical'
        assert thresholds.get_category(0.85) == 'similar'
        assert thresholds.get_category(0.65) == 'related'
        assert thresholds.get_category(0.50) == 'different'

    def test_should_link_existing(self):
        """Test high-similarity linking decision."""
        thresholds = RAGThresholds(identical_threshold=0.95)

        assert thresholds.should_link_existing(0.97) is True
        assert thresholds.should_link_existing(0.95) is True
        assert thresholds.should_link_existing(0.94) is False

    def test_should_create_similar_relationship(self):
        """Test medium-similarity relationship decision."""
        thresholds = RAGThresholds(identical_threshold=0.95, similar_threshold=0.75)

        assert thresholds.should_create_similar_relationship(0.85) is True
        assert thresholds.should_create_similar_relationship(0.75) is True
        assert thresholds.should_create_similar_relationship(0.95) is False  # Too high
        assert thresholds.should_create_similar_relationship(0.70) is False  # Too low

    def test_to_dict(self):
        """Test serialization to dictionary."""
        thresholds = RAGThresholds()
        data = thresholds.to_dict()

        assert isinstance(data, dict)
        assert data['identical_threshold'] == 0.95
        assert data['similar_threshold'] == 0.75
        assert data['related_threshold'] == 0.60

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'identical_threshold': 0.98,
            'similar_threshold': 0.80,
            'related_threshold': 0.65,
            'min_confidence_for_linking': 0.75
        }

        thresholds = RAGThresholds.from_dict(data)

        assert thresholds.identical_threshold == 0.98
        assert thresholds.similar_threshold == 0.80


class TestRAGConfig:
    """Test RAG configuration manager."""

    @pytest.fixture
    def temp_config_path(self):
        """Create temporary config file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / 'test_rag_config.json'

    def test_default_config(self, temp_config_path):
        """Test loading default config when file doesn't exist."""
        config = RAGConfig(config_path=temp_config_path)

        assert config.thresholds.identical_threshold == 0.95
        assert config.thresholds.similar_threshold == 0.75

    def test_save_and_load_config(self, temp_config_path):
        """Test saving and loading configuration."""
        # Create config with custom thresholds
        config = RAGConfig(config_path=temp_config_path)
        config.update_thresholds(identical=0.98, similar=0.82)

        # Save to file
        success = config.save_config()
        assert success is True
        assert temp_config_path.exists()

        # Load from file
        config2 = RAGConfig(config_path=temp_config_path)
        assert config2.thresholds.identical_threshold == 0.98
        assert config2.thresholds.similar_threshold == 0.82

    def test_update_thresholds(self, temp_config_path):
        """Test updating threshold values."""
        config = RAGConfig(config_path=temp_config_path)

        success = config.update_thresholds(
            identical=0.97,
            similar=0.80,
            related=0.65
        )

        assert success is True
        assert config.thresholds.identical_threshold == 0.97
        assert config.thresholds.similar_threshold == 0.80
        assert config.thresholds.related_threshold == 0.65

    def test_update_invalid_thresholds(self, temp_config_path):
        """Test that invalid updates are rejected."""
        config = RAGConfig(config_path=temp_config_path)

        # Try to set similar >= identical
        success = config.update_thresholds(identical=0.75, similar=0.95)

        assert success is False
        # Original values should be unchanged
        assert config.thresholds.identical_threshold == 0.95

    def test_reset_to_defaults(self, temp_config_path):
        """Test resetting configuration to defaults."""
        config = RAGConfig(config_path=temp_config_path)

        # Modify thresholds
        config.update_thresholds(identical=0.98)
        assert config.thresholds.identical_threshold == 0.98

        # Reset to defaults
        config.reset_to_defaults()
        assert config.thresholds.identical_threshold == 0.95
        assert config.thresholds.similar_threshold == 0.75

    def test_config_file_format(self, temp_config_path):
        """Test that config file is valid JSON."""
        config = RAGConfig(config_path=temp_config_path)
        config.save_config()

        # Read and parse JSON
        with open(temp_config_path, 'r') as f:
            data = json.load(f)

        assert 'thresholds' in data
        assert 'identical_threshold' in data['thresholds']
        assert data['thresholds']['identical_threshold'] == 0.95


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
