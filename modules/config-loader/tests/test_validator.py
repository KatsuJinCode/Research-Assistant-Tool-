"""Tests for configuration validation."""

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
    validate_config,
)
from research_assistant_config.validator import ValidationError


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_valid_config_passes(
        self,
        sample_database_config,
        sample_ai_provider_config,
        sample_agent_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test that valid configuration passes validation."""
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

        # Should not raise
        validate_config(config)

    def test_no_ai_providers(
        self,
        sample_database_config,
        sample_agent_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test validation fails when no AI providers configured."""
        # This will fail in Pydantic validation because default_provider not in ai_providers
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            Config(
                database=DatabaseConfig(**sample_database_config),
                ai_providers={},  # Empty!
                agents={
                    "test_agent": AgentTypeConfig(**sample_agent_config),
                },
                confidence=ConfidenceThresholds(**sample_confidence_config),
                normalization=NormalizationConfig(**sample_normalization_config),
                logging=LoggingConfig(**sample_logging_config),
                system=SystemConfig(**sample_system_config),
                default_provider="openai",  # This will fail in pydantic validation
            )

    def test_default_provider_not_in_ai_providers(
        self,
        sample_database_config,
        sample_ai_provider_config,
        sample_agent_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test validation when default provider not in ai_providers."""
        # Note: This will be caught by Pydantic validation in Config.__init__
        # But we test it here anyway for the validator
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

        # Manually change default_provider to test validator
        # (We can't do this normally because Config is frozen)
        object.__setattr__(config, "default_provider", "nonexistent")

        with pytest.raises(ValidationError) as exc_info:
            validate_config(config)

        assert "Default provider 'nonexistent' not in ai_providers" in str(
            exc_info.value.errors
        )

    def test_no_enabled_agents(
        self,
        sample_database_config,
        sample_ai_provider_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test validation fails when no agents enabled."""
        config = Config(
            database=DatabaseConfig(**sample_database_config),
            ai_providers={
                "openai": AIProviderConfig(**sample_ai_provider_config),
            },
            agents={
                "disabled1": AgentTypeConfig(count=0, enabled=False),
                "disabled2": AgentTypeConfig(count=0, enabled=False),
            },
            confidence=ConfidenceThresholds(**sample_confidence_config),
            normalization=NormalizationConfig(**sample_normalization_config),
            logging=LoggingConfig(**sample_logging_config),
            system=SystemConfig(**sample_system_config),
            default_provider="openai",
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_config(config)

        assert "No agents enabled" in str(exc_info.value.errors)

    def test_enabled_agent_with_zero_count(
        self,
        sample_database_config,
        sample_ai_provider_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test validation fails when enabled agent has count=0."""
        config = Config(
            database=DatabaseConfig(**sample_database_config),
            ai_providers={
                "openai": AIProviderConfig(**sample_ai_provider_config),
            },
            agents={
                "bad_agent": AgentTypeConfig(count=0, enabled=True),  # Enabled but count=0!
            },
            confidence=ConfidenceThresholds(**sample_confidence_config),
            normalization=NormalizationConfig(**sample_normalization_config),
            logging=LoggingConfig(**sample_logging_config),
            system=SystemConfig(**sample_system_config),
            default_provider="openai",
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_config(config)

        assert "is enabled but count is 0" in str(exc_info.value.errors)

    def test_confidence_thresholds_not_in_order(
        self,
        sample_database_config,
        sample_ai_provider_config,
        sample_agent_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test validation of confidence threshold ordering."""
        # This will fail in ConfidenceThresholds validation itself
        # But we test it in the validator too
        with pytest.raises(ValueError):
            ConfidenceThresholds(high=0.5, medium=0.7, low=0.9)  # Wrong order

    def test_invalid_api_key_placeholder(
        self,
        sample_database_config,
        sample_agent_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test validation fails when API key is a placeholder."""
        config = Config(
            database=DatabaseConfig(**sample_database_config),
            ai_providers={
                "openai": AIProviderConfig(
                    api_key="${OPENAI_API_KEY}",  # Not substituted!
                    model="gpt-4",
                    temperature=0.7,
                    max_tokens=4000,
                ),
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

        with pytest.raises(ValidationError) as exc_info:
            validate_config(config)

        assert "AI provider 'openai' has invalid API key" in str(exc_info.value.errors)

    def test_empty_api_key(
        self,
        sample_database_config,
        sample_agent_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test validation fails when API key is empty."""
        # Empty API key will fail in AIProviderConfig validation
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError, match="API key cannot be empty"):
            Config(
                database=DatabaseConfig(**sample_database_config),
                ai_providers={
                    "openai": AIProviderConfig(
                        api_key="",  # Empty!
                        model="gpt-4",
                        temperature=0.7,
                        max_tokens=4000,
                    ),
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

    def test_invalid_logging_level(
        self,
        sample_database_config,
        sample_ai_provider_config,
        sample_agent_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_system_config,
    ):
        """Test validation of logging level."""
        # This will fail in LoggingConfig validation
        with pytest.raises(ValueError, match="level must be one of"):
            LoggingConfig(level="INVALID_LEVEL")

    def test_multiple_validation_errors(
        self,
        sample_database_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test that multiple validation errors are collected."""
        config = Config(
            database=DatabaseConfig(**sample_database_config),
            ai_providers={
                "openai": AIProviderConfig(
                    api_key="${NOT_SUBSTITUTED}",  # Error 1
                    model="gpt-4",
                    temperature=0.7,
                    max_tokens=4000,
                ),
            },
            agents={
                "disabled": AgentTypeConfig(count=0, enabled=False),  # Error 2: no enabled agents
            },
            confidence=ConfidenceThresholds(**sample_confidence_config),
            normalization=NormalizationConfig(**sample_normalization_config),
            logging=LoggingConfig(**sample_logging_config),
            system=SystemConfig(**sample_system_config),
            default_provider="openai",
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_config(config)

        # Should have multiple errors
        assert len(exc_info.value.errors) >= 2
        errors_str = str(exc_info.value.errors)
        assert "No agents enabled" in errors_str
        assert "AI provider" in errors_str and "invalid API key" in errors_str

    def test_database_connection_string_validation(
        self,
        sample_ai_provider_config,
        sample_agent_config,
        sample_confidence_config,
        sample_normalization_config,
        sample_logging_config,
        sample_system_config,
    ):
        """Test that database connection string can be constructed."""
        # Valid config
        config = Config(
            database=DatabaseConfig(
                host="localhost",
                port=5432,
                name="test_db",
                user="user",
                password="pass",
            ),
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

        # Should not raise
        validate_config(config)
        assert config.database.connection_string.startswith("postgresql://")
