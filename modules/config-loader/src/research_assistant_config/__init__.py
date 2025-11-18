"""Research Assistant Config - Configuration management with validation.

This module provides unified configuration loading with environment variable
substitution, validation, and type safety using Pydantic.
"""

from .config import (
    Config,
    DatabaseConfig,
    AIProviderConfig,
    AgentTypeConfig,
    ConfidenceThresholds,
    NormalizationConfig,
    LoggingConfig,
    SystemConfig,
    load_config,
    get_config,
)
from .loader import YAMLConfigLoader, EnvConfigLoader
from .validator import validate_config

__version__ = "0.1.0"

__all__ = [
    # Main config
    "Config",
    # Config sections
    "DatabaseConfig",
    "AIProviderConfig",
    "AgentTypeConfig",
    "ConfidenceThresholds",
    "NormalizationConfig",
    "LoggingConfig",
    "SystemConfig",
    # Loading functions
    "load_config",
    "get_config",
    # Loaders
    "YAMLConfigLoader",
    "EnvConfigLoader",
    # Validation
    "validate_config",
]
