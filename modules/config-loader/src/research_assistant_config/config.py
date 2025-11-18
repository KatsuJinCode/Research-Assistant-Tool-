"""Configuration models and main Config class."""

from typing import Dict, Optional
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DatabaseConfig(BaseModel):
    """Database configuration."""

    model_config = ConfigDict(frozen=True)

    host: str = Field(..., description="Database host")
    port: int = Field(..., ge=1, le=65535, description="Database port")
    name: str = Field(..., description="Database name")
    user: str = Field(..., description="Database user")
    password: str = Field(..., description="Database password")

    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def connection_string_async(self) -> str:
        """Get async PostgreSQL connection string."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class AIProviderConfig(BaseModel):
    """AI provider configuration."""

    model_config = ConfigDict(frozen=True)

    api_key: str = Field(..., description="API key for provider")
    model: str = Field(..., description="Model identifier")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int = Field(default=4000, ge=1, le=128000, description="Max tokens")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key is not empty."""
        if not v or v.strip() == "":
            raise ValueError("API key cannot be empty")
        return v


class AgentTypeConfig(BaseModel):
    """Agent type configuration."""

    model_config = ConfigDict(frozen=True)

    count: int = Field(..., ge=0, le=100, description="Number of agent instances")
    enabled: bool = Field(default=True, description="Whether agent type is enabled")
    description: str = Field(default="", description="Agent type description")


class ConfidenceThresholds(BaseModel):
    """Confidence threshold configuration."""

    model_config = ConfigDict(frozen=True)

    high: float = Field(..., ge=0.0, le=1.0, description="High confidence threshold")
    medium: float = Field(..., ge=0.0, le=1.0, description="Medium confidence threshold")
    low: float = Field(..., ge=0.0, le=1.0, description="Low confidence threshold")
    low_confidence_additional_agents: int = Field(
        default=5, ge=0, description="Additional agents for low confidence"
    )
    low_confidence_depth_increase: int = Field(
        default=2, ge=0, description="Depth increase for low confidence"
    )

    @field_validator("medium")
    @classmethod
    def validate_medium(cls, v: float, info) -> float:
        """Validate medium < high."""
        if "high" in info.data and v >= info.data["high"]:
            raise ValueError("medium threshold must be < high threshold")
        return v

    @field_validator("low")
    @classmethod
    def validate_low(cls, v: float, info) -> float:
        """Validate low < medium."""
        if "medium" in info.data and v >= info.data["medium"]:
            raise ValueError("low threshold must be < medium threshold")
        return v


class NormalizationConfig(BaseModel):
    """Normalization configuration."""

    model_config = ConfigDict(frozen=True)

    require_human_validation: bool = Field(
        default=True, description="Require human validation"
    )
    min_confidence_for_auto_approve: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Min confidence for auto-approval"
    )
    max_candidates: int = Field(
        default=4, ge=1, le=20, description="Max normalization candidates"
    )
    auto_fail_if_qualifiers_lost: bool = Field(
        default=True, description="Auto-fail if qualifiers lost"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    model_config = ConfigDict(frozen=True)

    level: str = Field(default="INFO", description="Logging level")
    file: str = Field(default="logs/app.log", description="Log file path")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
    )
    max_bytes: int = Field(
        default=10485760, ge=1024, description="Max log file size in bytes"
    )
    backup_count: int = Field(default=5, ge=0, le=100, description="Number of backups")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"level must be one of {valid_levels}")
        return v_upper


class SystemConfig(BaseModel):
    """System configuration."""

    model_config = ConfigDict(frozen=True)

    agent_poll_interval_seconds: int = Field(
        default=30, ge=1, le=3600, description="Agent polling interval"
    )
    investigation_timeout_seconds: int = Field(
        default=300, ge=10, le=7200, description="Investigation timeout"
    )
    expansion_scheduler_interval_hours: int = Field(
        default=1, ge=1, le=168, description="Expansion scheduler interval"
    )
    discovery_scheduler_interval_hours: int = Field(
        default=6, ge=1, le=168, description="Discovery scheduler interval"
    )
    max_concurrent_investigations: int = Field(
        default=10, ge=1, le=1000, description="Max concurrent investigations"
    )
    max_api_calls_per_minute: int = Field(
        default=60, ge=1, le=10000, description="Max API calls per minute"
    )


class Config(BaseModel):
    """Main configuration class."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    database: DatabaseConfig
    ai_providers: Dict[str, AIProviderConfig]
    agents: Dict[str, AgentTypeConfig]
    confidence: ConfidenceThresholds
    normalization: NormalizationConfig
    logging: LoggingConfig
    system: SystemConfig
    default_provider: str = Field(default="anthropic", description="Default AI provider")

    @field_validator("default_provider")
    @classmethod
    def validate_default_provider(cls, v: str, info) -> str:
        """Validate default provider exists in ai_providers."""
        if "ai_providers" in info.data and v not in info.data["ai_providers"]:
            raise ValueError(
                f"default_provider '{v}' not found in ai_providers. "
                f"Available: {list(info.data['ai_providers'].keys())}"
            )
        return v

    def get_active_agents(self) -> Dict[str, AgentTypeConfig]:
        """Get only enabled agents."""
        return {name: config for name, config in self.agents.items() if config.enabled}

    def get_ai_provider(self, provider_name: Optional[str] = None) -> AIProviderConfig:
        """
        Get AI provider configuration.

        Args:
            provider_name: Provider name, or None for default

        Returns:
            AIProviderConfig
        """
        name = provider_name or self.default_provider
        if name not in self.ai_providers:
            raise ValueError(f"Provider '{name}' not configured")
        return self.ai_providers[name]


# Global config instance (singleton pattern)
_config_instance: Optional[Config] = None


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file (defaults to config/config.yaml)

    Returns:
        Config instance
    """
    global _config_instance

    from .loader import YAMLConfigLoader

    if config_path is None:
        # Try to find config.yaml in standard locations
        possible_paths = [
            Path("config/config.yaml"),
            Path("../config/config.yaml"),
            Path.cwd() / "config" / "config.yaml",
        ]
        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break

    if config_path is None:
        raise FileNotFoundError(
            "Config file not found. Tried: " + ", ".join(str(p) for p in possible_paths)
        )

    loader = YAMLConfigLoader(config_path)
    _config_instance = loader.load()
    return _config_instance


def get_config() -> Config:
    """
    Get current configuration instance.

    Returns:
        Config instance

    Raises:
        RuntimeError: If config hasn't been loaded yet
    """
    if _config_instance is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return _config_instance
