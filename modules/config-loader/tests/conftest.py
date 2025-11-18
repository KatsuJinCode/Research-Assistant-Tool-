"""Shared test fixtures for config-loader tests."""

import os
import pytest
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def sample_database_config():
    """Sample database configuration."""
    return {
        "host": "localhost",
        "port": 5432,
        "name": "research_db",
        "user": "research_user",
        "password": "test_password",
    }


@pytest.fixture
def sample_ai_provider_config():
    """Sample AI provider configuration."""
    return {
        "api_key": "sk-test-key-1234567890",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 4000,
    }


@pytest.fixture
def sample_agent_config():
    """Sample agent type configuration."""
    return {
        "count": 3,
        "enabled": True,
        "description": "Test agent for citation extraction",
    }


@pytest.fixture
def sample_confidence_config():
    """Sample confidence thresholds configuration."""
    return {
        "high": 0.9,
        "medium": 0.7,
        "low": 0.5,
        "low_confidence_additional_agents": 5,
        "low_confidence_depth_increase": 2,
    }


@pytest.fixture
def sample_normalization_config():
    """Sample normalization configuration."""
    return {
        "require_human_validation": True,
        "min_confidence_for_auto_approve": 0.95,
        "max_candidates": 4,
        "auto_fail_if_qualifiers_lost": True,
    }


@pytest.fixture
def sample_logging_config():
    """Sample logging configuration."""
    return {
        "level": "INFO",
        "file": "logs/test.log",
        "format": "%(asctime)s - %(message)s",
        "max_bytes": 10485760,
        "backup_count": 5,
    }


@pytest.fixture
def sample_system_config():
    """Sample system configuration."""
    return {
        "agent_poll_interval_seconds": 30,
        "investigation_timeout_seconds": 300,
        "expansion_scheduler_interval_hours": 1,
        "discovery_scheduler_interval_hours": 6,
        "max_concurrent_investigations": 10,
        "max_api_calls_per_minute": 60,
    }


@pytest.fixture
def sample_full_config_dict(
    sample_database_config,
    sample_ai_provider_config,
    sample_agent_config,
    sample_confidence_config,
    sample_normalization_config,
    sample_logging_config,
    sample_system_config,
):
    """Complete configuration dictionary."""
    return {
        "database": sample_database_config,
        "ai_providers": {
            "openai": sample_ai_provider_config,
            "anthropic": {
                "api_key": "sk-ant-test-key-1234567890",
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.5,
                "max_tokens": 8000,
            },
        },
        "agents": {
            "citation_extractor": sample_agent_config,
            "claim_extractor": {
                "count": 2,
                "enabled": True,
                "description": "Extracts claims",
            },
            "disabled_agent": {
                "count": 0,
                "enabled": False,
                "description": "Disabled for testing",
            },
        },
        "confidence_thresholds": sample_confidence_config,
        "normalization": sample_normalization_config,
        "logging": sample_logging_config,
        "system": sample_system_config,
    }


@pytest.fixture
def sample_yaml_content(sample_full_config_dict):
    """Sample YAML configuration content."""
    return """
database:
  host: localhost
  port: 5432
  name: research_db
  user: research_user
  password: ${DB_PASSWORD}

ai_providers:
  default: anthropic
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4
    temperature: 0.7
    max_tokens: 4000
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-5-sonnet-20241022
    temperature: 0.5
    max_tokens: 8000

agents:
  citation_extractor:
    count: 3
    enabled: true
    description: Test agent for citation extraction
  claim_extractor:
    count: 2
    enabled: true
    description: Extracts claims

confidence_thresholds:
  high: 0.9
  medium: 0.7
  low: 0.5
  low_confidence_additional_agents: 5
  low_confidence_depth_increase: 2

normalization:
  require_human_validation: true
  min_confidence_for_auto_approve: 0.95
  max_candidates: 4
  auto_fail_if_qualifiers_lost: true

logging:
  level: INFO
  file: logs/test.log
  format: "%(asctime)s - %(message)s"
  max_bytes: 10485760
  backup_count: 5

system:
  agent_poll_interval_seconds: 30
  investigation_timeout_seconds: 300
  expansion_scheduler_interval_hours: 1
  discovery_scheduler_interval_hours: 6
  max_concurrent_investigations: 10
  max_api_calls_per_minute: 60
"""


@pytest.fixture
def temp_config_file(tmp_path, sample_yaml_content):
    """Create temporary YAML config file."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(sample_yaml_content)
    return config_file


@pytest.fixture
def set_env_vars(monkeypatch):
    """Set environment variables for testing."""
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-123")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-anthropic-456")
    return {
        "DB_PASSWORD": "test_password",
        "OPENAI_API_KEY": "sk-test-openai-123",
        "ANTHROPIC_API_KEY": "sk-ant-test-anthropic-456",
    }
