"""Tests for configuration loaders."""

import os
import pytest
from pathlib import Path

from research_assistant_config import (
    YAMLConfigLoader,
    EnvConfigLoader,
    Config,
)


class TestYAMLConfigLoader:
    """Tests for YAMLConfigLoader."""

    def test_load_yaml_config(self, temp_config_file, set_env_vars):
        """Test loading configuration from YAML file."""
        loader = YAMLConfigLoader(str(temp_config_file), load_env=False)
        config = loader.load()

        assert isinstance(config, Config)
        assert config.database.host == "localhost"
        assert config.database.port == 5432
        assert config.database.name == "research_db"

    def test_env_var_substitution(self, temp_config_file, set_env_vars):
        """Test ${VAR} substitution in YAML."""
        loader = YAMLConfigLoader(str(temp_config_file), load_env=False)
        config = loader.load()

        # Password should be substituted from ${DB_PASSWORD}
        assert config.database.password == "test_password"

        # API keys should be substituted
        assert config.ai_providers["openai"].api_key == "sk-test-openai-123"
        assert config.ai_providers["anthropic"].api_key == "sk-ant-test-anthropic-456"

    def test_file_not_found(self, tmp_path):
        """Test error when config file doesn't exist."""
        loader = YAMLConfigLoader(str(tmp_path / "nonexistent.yaml"))

        with pytest.raises(FileNotFoundError, match="Config file not found"):
            loader.load()

    def test_missing_env_var(self, tmp_path, monkeypatch):
        """Test behavior when environment variable is missing."""
        # Remove environment variable
        monkeypatch.delenv("DB_PASSWORD", raising=False)

        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            """
database:
  host: localhost
  port: 5432
  name: test_db
  user: user
  password: ${DB_PASSWORD}

ai_providers:
  default: openai
  openai:
    api_key: sk-test
    model: gpt-4
    temperature: 0.7
    max_tokens: 4000

agents:
  test:
    count: 1
    enabled: true

confidence_thresholds:
  high: 0.9
  medium: 0.7
  low: 0.5

normalization: {}

logging:
  level: INFO

system:
  agent_poll_interval_seconds: 30
"""
        )

        loader = YAMLConfigLoader(str(config_file), load_env=False)
        config = loader.load()

        # Should keep original ${DB_PASSWORD} string if var not found
        assert config.database.password == "${DB_PASSWORD}"

    def test_ai_providers_default_extraction(self, tmp_path, monkeypatch):
        """Test that 'default' is extracted from ai_providers correctly."""
        monkeypatch.setenv("API_KEY", "sk-test-123")

        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            """
database:
  host: localhost
  port: 5432
  name: test_db
  user: user
  password: pass

ai_providers:
  default: openai
  openai:
    api_key: ${API_KEY}
    model: gpt-4
    temperature: 0.7
    max_tokens: 4000

agents:
  test:
    count: 1
    enabled: true

confidence_thresholds:
  high: 0.9
  medium: 0.7
  low: 0.5

normalization: {}

logging:
  level: INFO

system:
  agent_poll_interval_seconds: 30
"""
        )

        loader = YAMLConfigLoader(str(config_file), load_env=False)
        config = loader.load()

        assert config.default_provider == "openai"
        # default should not appear in ai_providers dict
        assert "default" not in config.ai_providers

    def test_nested_env_var_substitution(self, tmp_path, monkeypatch):
        """Test environment variable substitution in nested structures."""
        monkeypatch.setenv("DB_HOST", "db.example.com")
        monkeypatch.setenv("DB_PORT", "5433")
        monkeypatch.setenv("API_KEY", "sk-nested-test")

        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            """
database:
  host: ${DB_HOST}
  port: 5433
  name: test_db
  user: user
  password: pass

ai_providers:
  default: openai
  openai:
    api_key: ${API_KEY}
    model: gpt-4
    temperature: 0.7
    max_tokens: 4000

agents:
  test:
    count: 1
    enabled: true

confidence_thresholds:
  high: 0.9
  medium: 0.7
  low: 0.5

normalization: {}

logging:
  level: INFO

system:
  agent_poll_interval_seconds: 30
"""
        )

        loader = YAMLConfigLoader(str(config_file), load_env=False)
        config = loader.load()

        assert config.database.host == "db.example.com"
        assert config.database.port == 5433
        assert config.ai_providers["openai"].api_key == "sk-nested-test"


class TestEnvConfigLoader:
    """Tests for EnvConfigLoader."""

    def test_load_from_env(self, monkeypatch):
        """Test loading configuration entirely from environment variables."""
        # Set all required environment variables
        monkeypatch.setenv("RESEARCH_ASSISTANT_DATABASE__HOST", "envhost")
        monkeypatch.setenv("RESEARCH_ASSISTANT_DATABASE__PORT", "5432")
        monkeypatch.setenv("RESEARCH_ASSISTANT_DATABASE__NAME", "envdb")
        monkeypatch.setenv("RESEARCH_ASSISTANT_DATABASE__USER", "envuser")
        monkeypatch.setenv("RESEARCH_ASSISTANT_DATABASE__PASSWORD", "envpass")

        monkeypatch.setenv(
            "RESEARCH_ASSISTANT_AI_PROVIDERS__OPENAI__API_KEY", "sk-env-test"
        )
        monkeypatch.setenv("RESEARCH_ASSISTANT_AI_PROVIDERS__OPENAI__MODEL", "gpt-4")
        monkeypatch.setenv(
            "RESEARCH_ASSISTANT_AI_PROVIDERS__OPENAI__TEMPERATURE", "0.8"
        )
        monkeypatch.setenv(
            "RESEARCH_ASSISTANT_AI_PROVIDERS__OPENAI__MAX_TOKENS", "5000"
        )

        monkeypatch.setenv("RESEARCH_ASSISTANT_AGENTS__TEST__COUNT", "3")
        monkeypatch.setenv("RESEARCH_ASSISTANT_AGENTS__TEST__ENABLED", "true")

        monkeypatch.setenv("RESEARCH_ASSISTANT_CONFIDENCE_THRESHOLDS__HIGH", "0.9")
        monkeypatch.setenv("RESEARCH_ASSISTANT_CONFIDENCE_THRESHOLDS__MEDIUM", "0.7")
        monkeypatch.setenv("RESEARCH_ASSISTANT_CONFIDENCE_THRESHOLDS__LOW", "0.5")

        monkeypatch.setenv("RESEARCH_ASSISTANT_LOGGING__LEVEL", "DEBUG")

        monkeypatch.setenv(
            "RESEARCH_ASSISTANT_SYSTEM__AGENT_POLL_INTERVAL_SECONDS", "60"
        )

        monkeypatch.setenv("RESEARCH_ASSISTANT_DEFAULT_PROVIDER", "openai")

        loader = EnvConfigLoader()
        config = loader.load()

        assert config.database.host == "envhost"
        assert config.database.port == 5432  # Converted to int
        assert config.ai_providers["openai"].api_key == "sk-env-test"
        assert config.ai_providers["openai"].temperature == 0.8  # Converted to float
        assert config.ai_providers["openai"].max_tokens == 5000  # Converted to int
        assert config.agents["test"].count == 3  # Converted to int
        assert config.agents["test"].enabled is True  # Converted to bool
        assert config.logging.level == "DEBUG"
        assert config.system.agent_poll_interval_seconds == 60

    def test_value_type_conversion(self, monkeypatch):
        """Test automatic type conversion for env vars."""
        loader = EnvConfigLoader()

        # Test boolean conversion
        assert loader._convert_value("true") is True
        assert loader._convert_value("True") is True
        assert loader._convert_value("yes") is True
        assert loader._convert_value("1") is True
        assert loader._convert_value("false") is False
        assert loader._convert_value("False") is False
        assert loader._convert_value("no") is False
        assert loader._convert_value("0") is False

        # Test integer conversion
        assert loader._convert_value("42") == 42
        assert loader._convert_value("5432") == 5432

        # Test float conversion
        assert loader._convert_value("0.7") == 0.7
        assert loader._convert_value("3.14159") == 3.14159

        # Test string (no conversion)
        assert loader._convert_value("hello") == "hello"
        assert loader._convert_value("gpt-4") == "gpt-4"

    def test_prefix_filtering(self, monkeypatch):
        """Test that only RESEARCH_ASSISTANT_ prefixed vars are used."""
        monkeypatch.setenv("RESEARCH_ASSISTANT_DATABASE__HOST", "localhost")
        monkeypatch.setenv("OTHER_VAR", "should be ignored")
        monkeypatch.setenv("DATABASE__HOST", "should be ignored")

        loader = EnvConfigLoader()
        config_dict = loader._build_config_dict()

        assert "database" in config_dict
        assert config_dict["database"]["host"] == "localhost"
        # Other vars should not appear
        assert "other_var" not in config_dict
        assert "OTHER_VAR" not in config_dict
