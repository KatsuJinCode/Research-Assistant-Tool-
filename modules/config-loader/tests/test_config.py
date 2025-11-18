"""Tests for configuration models."""

import pytest
from research_assistant_config import (
    Config,
    DatabaseConfig,
    AIProviderConfig,
    AgentTypeConfig,
    ConfidenceThresholds,
    NormalizationConfig,
    LoggingConfig,
    SystemConfig,
)


class TestDatabaseConfig:
    """Tests for DatabaseConfig model."""

    def test_create_database_config(self, sample_database_config):
        """Test creating DatabaseConfig."""
        config = DatabaseConfig(**sample_database_config)

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.name == "research_db"
        assert config.user == "research_user"

    def test_connection_string(self, sample_database_config):
        """Test PostgreSQL connection string generation."""
        config = DatabaseConfig(**sample_database_config)

        expected = "postgresql://research_user:test_password@localhost:5432/research_db"
        assert config.connection_string == expected

    def test_async_connection_string(self, sample_database_config):
        """Test async PostgreSQL connection string generation."""
        config = DatabaseConfig(**sample_database_config)

        expected = "postgresql+asyncpg://research_user:test_password@localhost:5432/research_db"
        assert config.connection_string_async == expected

    def test_port_validation(self, sample_database_config):
        """Test port number validation."""
        # Valid port
        config = DatabaseConfig(**sample_database_config)
        assert config.port == 5432

        # Invalid port - too high
        with pytest.raises(ValueError):
            DatabaseConfig(**{**sample_database_config, "port": 70000})

        # Invalid port - zero
        with pytest.raises(ValueError):
            DatabaseConfig(**{**sample_database_config, "port": 0})

    def test_immutability(self, sample_database_config):
        """Test that DatabaseConfig is frozen/immutable."""
        config = DatabaseConfig(**sample_database_config)

        with pytest.raises(Exception):  # Pydantic raises ValidationError
            config.host = "newhost"


class TestAIProviderConfig:
    """Tests for AIProviderConfig model."""

    def test_create_ai_provider_config(self, sample_ai_provider_config):
        """Test creating AIProviderConfig."""
        config = AIProviderConfig(**sample_ai_provider_config)

        assert config.api_key == "sk-test-key-1234567890"
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 4000

    def test_api_key_validation(self, sample_ai_provider_config):
        """Test API key cannot be empty."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            AIProviderConfig(**{**sample_ai_provider_config, "api_key": ""})

        with pytest.raises(ValueError, match="API key cannot be empty"):
            AIProviderConfig(**{**sample_ai_provider_config, "api_key": "   "})

    def test_temperature_validation(self, sample_ai_provider_config):
        """Test temperature must be in valid range."""
        # Valid temperatures
        config = AIProviderConfig(**{**sample_ai_provider_config, "temperature": 0.0})
        assert config.temperature == 0.0

        config = AIProviderConfig(**{**sample_ai_provider_config, "temperature": 2.0})
        assert config.temperature == 2.0

        # Invalid - too high
        with pytest.raises(ValueError):
            AIProviderConfig(**{**sample_ai_provider_config, "temperature": 3.0})

        # Invalid - negative
        with pytest.raises(ValueError):
            AIProviderConfig(**{**sample_ai_provider_config, "temperature": -0.1})

    def test_max_tokens_validation(self, sample_ai_provider_config):
        """Test max_tokens validation."""
        # Valid
        config = AIProviderConfig(**{**sample_ai_provider_config, "max_tokens": 128000})
        assert config.max_tokens == 128000

        # Invalid - zero
        with pytest.raises(ValueError):
            AIProviderConfig(**{**sample_ai_provider_config, "max_tokens": 0})


class TestAgentTypeConfig:
    """Tests for AgentTypeConfig model."""

    def test_create_agent_config(self, sample_agent_config):
        """Test creating AgentTypeConfig."""
        config = AgentTypeConfig(**sample_agent_config)

        assert config.count == 3
        assert config.enabled is True
        assert config.description == "Test agent for citation extraction"

    def test_count_validation(self, sample_agent_config):
        """Test agent count validation."""
        # Valid counts
        config = AgentTypeConfig(**{**sample_agent_config, "count": 0})
        assert config.count == 0

        config = AgentTypeConfig(**{**sample_agent_config, "count": 100})
        assert config.count == 100

        # Invalid - too high
        with pytest.raises(ValueError):
            AgentTypeConfig(**{**sample_agent_config, "count": 101})

        # Invalid - negative
        with pytest.raises(ValueError):
            AgentTypeConfig(**{**sample_agent_config, "count": -1})


class TestConfidenceThresholds:
    """Tests for ConfidenceThresholds model."""

    def test_create_confidence_thresholds(self, sample_confidence_config):
        """Test creating ConfidenceThresholds."""
        config = ConfidenceThresholds(**sample_confidence_config)

        assert config.high == 0.9
        assert config.medium == 0.7
        assert config.low == 0.5
        assert config.low_confidence_additional_agents == 5

    def test_threshold_ordering(self):
        """Test that thresholds must be in order: low < medium < high."""
        # Valid ordering
        config = ConfidenceThresholds(high=0.9, medium=0.7, low=0.5)
        assert config.low < config.medium < config.high

        # Invalid - medium >= high
        with pytest.raises(ValueError, match="medium threshold must be < high"):
            ConfidenceThresholds(high=0.7, medium=0.9, low=0.5)

        # Invalid - low >= medium
        with pytest.raises(ValueError, match="low threshold must be < medium"):
            ConfidenceThresholds(high=0.9, medium=0.7, low=0.8)

    def test_threshold_ranges(self):
        """Test thresholds must be 0-1."""
        with pytest.raises(ValueError):
            ConfidenceThresholds(high=1.5, medium=0.7, low=0.5)

        with pytest.raises(ValueError):
            ConfidenceThresholds(high=0.9, medium=-0.1, low=0.5)


class TestNormalizationConfig:
    """Tests for NormalizationConfig model."""

    def test_create_normalization_config(self, sample_normalization_config):
        """Test creating NormalizationConfig."""
        config = NormalizationConfig(**sample_normalization_config)

        assert config.require_human_validation is True
        assert config.min_confidence_for_auto_approve == 0.95
        assert config.max_candidates == 4
        assert config.auto_fail_if_qualifiers_lost is True

    def test_defaults(self):
        """Test default values."""
        config = NormalizationConfig()

        assert config.require_human_validation is True
        assert config.min_confidence_for_auto_approve == 0.95
        assert config.max_candidates == 4

    def test_validation(self):
        """Test validation of min_confidence_for_auto_approve."""
        with pytest.raises(ValueError):
            NormalizationConfig(min_confidence_for_auto_approve=1.5)


class TestLoggingConfig:
    """Tests for LoggingConfig model."""

    def test_create_logging_config(self, sample_logging_config):
        """Test creating LoggingConfig."""
        config = LoggingConfig(**sample_logging_config)

        assert config.level == "INFO"
        assert config.file == "logs/test.log"
        assert config.max_bytes == 10485760

    def test_level_validation(self):
        """Test logging level validation."""
        # Valid levels (case insensitive)
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = LoggingConfig(level=level)
            assert config.level == level.upper()

            config = LoggingConfig(level=level.lower())
            assert config.level == level.upper()

        # Invalid level
        with pytest.raises(ValueError, match="level must be one of"):
            LoggingConfig(level="INVALID")


class TestSystemConfig:
    """Tests for SystemConfig model."""

    def test_create_system_config(self, sample_system_config):
        """Test creating SystemConfig."""
        config = SystemConfig(**sample_system_config)

        assert config.agent_poll_interval_seconds == 30
        assert config.investigation_timeout_seconds == 300
        assert config.max_concurrent_investigations == 10

    def test_interval_validation(self):
        """Test interval validation."""
        # Valid
        config = SystemConfig(agent_poll_interval_seconds=1)
        assert config.agent_poll_interval_seconds == 1

        # Invalid - too small
        with pytest.raises(ValueError):
            SystemConfig(agent_poll_interval_seconds=0)

        # Invalid - too large
        with pytest.raises(ValueError):
            SystemConfig(agent_poll_interval_seconds=3601)


class TestConfig:
    """Tests for main Config class."""

    def test_create_config(
        self,
        sample_database_config,
        sample_ai_provider_config,
        sample_agent_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test creating main Config."""
        config = Config(
            database=DatabaseConfig(**sample_database_config),
            ai_providers={
                "openai": AIProviderConfig(**sample_ai_provider_config),
            },
            agents={
                "test_agent": AgentTypeConfig(**sample_agent_config),
            },
            confidence=ConfidenceThresholds(**sample_confidence_config),
            normalization=NormalizationConfig(**sample_normalization_config),
            logging=LoggingConfig(**sample_logging_config),
            system=SystemConfig(**sample_system_config),
            default_provider="openai",
        )

        assert config.database.host == "localhost"
        assert config.default_provider == "openai"
        assert "openai" in config.ai_providers

    def test_default_provider_validation(
        self,
        sample_database_config,
        sample_ai_provider_config,
        sample_agent_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test default_provider must exist in ai_providers."""
        # Valid - provider exists
        config = Config(
            database=DatabaseConfig(**sample_database_config),
            ai_providers={
                "openai": AIProviderConfig(**sample_ai_provider_config),
            },
            agents={
                "test_agent": AgentTypeConfig(**sample_agent_config),
            },
            confidence=ConfidenceThresholds(**sample_confidence_config),
            normalization=NormalizationConfig(**sample_normalization_config),
            logging=LoggingConfig(**sample_logging_config),
            system=SystemConfig(**sample_system_config),
            default_provider="openai",
        )
        assert config.default_provider == "openai"

        # Invalid - provider doesn't exist
        with pytest.raises(ValueError, match="default_provider.*not found"):
            Config(
                database=DatabaseConfig(**sample_database_config),
                ai_providers={
                    "openai": AIProviderConfig(**sample_ai_provider_config),
                },
                agents={
                    "test_agent": AgentTypeConfig(**sample_agent_config),
                },
                confidence=ConfidenceThresholds(**sample_confidence_config),
                normalization=NormalizationConfig(**sample_normalization_config),
                logging=LoggingConfig(**sample_logging_config),
                system=SystemConfig(**sample_system_config),
                default_provider="nonexistent",
            )

    def test_get_active_agents(
        self,
        sample_database_config,
        sample_ai_provider_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test getting only active agents."""
        config = Config(
            database=DatabaseConfig(**sample_database_config),
            ai_providers={
                "openai": AIProviderConfig(**sample_ai_provider_config),
            },
            agents={
                "active1": AgentTypeConfig(count=3, enabled=True),
                "active2": AgentTypeConfig(count=2, enabled=True),
                "disabled": AgentTypeConfig(count=0, enabled=False),
            },
            confidence=ConfidenceThresholds(**sample_confidence_config),
            normalization=NormalizationConfig(**sample_normalization_config),
            logging=LoggingConfig(**sample_logging_config),
            system=SystemConfig(**sample_system_config),
            default_provider="openai",
        )

        active = config.get_active_agents()
        assert len(active) == 2
        assert "active1" in active
        assert "active2" in active
        assert "disabled" not in active

    def test_get_ai_provider(
        self,
        sample_database_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test getting AI provider configuration."""
        config = Config(
            database=DatabaseConfig(**sample_database_config),
            ai_providers={
                "openai": AIProviderConfig(
                    api_key="sk-openai", model="gpt-4", temperature=0.7, max_tokens=4000
                ),
                "anthropic": AIProviderConfig(
                    api_key="sk-ant", model="claude-3-5-sonnet", temperature=0.5, max_tokens=8000
                ),
            },
            agents={
                "test": AgentTypeConfig(count=1, enabled=True),
            },
            confidence=ConfidenceThresholds(**sample_confidence_config),
            normalization=NormalizationConfig(**sample_normalization_config),
            logging=LoggingConfig(**sample_logging_config),
            system=SystemConfig(**sample_system_config),
            default_provider="anthropic",
        )

        # Get default provider
        provider = config.get_ai_provider()
        assert provider.model == "claude-3-5-sonnet"

        # Get specific provider
        provider = config.get_ai_provider("openai")
        assert provider.model == "gpt-4"

        # Get nonexistent provider
        with pytest.raises(ValueError, match="Provider.*not configured"):
            config.get_ai_provider("nonexistent")

    def test_extra_fields_forbidden(
        self,
        sample_database_config,
        sample_ai_provider_config,
        sample_agent_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValueError):
            Config(
                database=DatabaseConfig(**sample_database_config),
                ai_providers={
                    "openai": AIProviderConfig(**sample_ai_provider_config),
                },
                agents={
                    "test_agent": AgentTypeConfig(**sample_agent_config),
                },
                confidence=ConfidenceThresholds(**sample_confidence_config),
                normalization=NormalizationConfig(**sample_normalization_config),
                logging=LoggingConfig(**sample_logging_config),
                system=SystemConfig(**sample_system_config),
                default_provider="openai",
                extra_field="not allowed",  # Should fail
            )
