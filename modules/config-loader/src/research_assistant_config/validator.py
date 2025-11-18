"""Configuration validation utilities."""

from typing import List, Optional
from .config import Config


class ValidationError(Exception):
    """Configuration validation error."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []


def validate_config(config: Config) -> None:
    """
    Validate configuration for common issues.

    Args:
        config: Config to validate

    Raises:
        ValidationError: If configuration is invalid
    """
    errors = []

    # Validate at least one AI provider is configured
    if not config.ai_providers:
        errors.append("No AI providers configured")

    # Validate default provider exists
    if config.default_provider not in config.ai_providers:
        errors.append(
            f"Default provider '{config.default_provider}' not in ai_providers"
        )

    # Validate at least one enabled agent
    active_agents = config.get_active_agents()
    if not active_agents:
        errors.append("No agents enabled - at least one agent must be enabled")

    # Validate agent counts
    for name, agent_config in config.agents.items():
        if agent_config.enabled and agent_config.count == 0:
            errors.append(f"Agent '{name}' is enabled but count is 0")

    # Validate confidence thresholds are in order
    if not (config.confidence.low < config.confidence.medium < config.confidence.high):
        errors.append(
            f"Confidence thresholds not in order: "
            f"low={config.confidence.low}, "
            f"medium={config.confidence.medium}, "
            f"high={config.confidence.high}"
        )

    # Validate database connection string can be constructed
    try:
        _ = config.database.connection_string
    except Exception as e:
        errors.append(f"Invalid database configuration: {e}")

    # Validate AI provider API keys are not placeholders
    for name, provider in config.ai_providers.items():
        if provider.api_key.startswith("${") or provider.api_key == "":
            errors.append(
                f"AI provider '{name}' has invalid API key (env var not substituted)"
            )

    # Validate logging level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.logging.level.upper() not in valid_levels:
        errors.append(f"Invalid logging level: {config.logging.level}")

    if errors:
        raise ValidationError(
            f"Configuration validation failed with {len(errors)} error(s)", errors=errors
        )
