"""Configuration loaders for different sources (YAML, environment variables)."""

import os
import re
from pathlib import Path
from typing import Any, Dict
import yaml
from dotenv import load_dotenv

from .config import (
    Config,
    DatabaseConfig,
    AIProviderConfig,
    AgentTypeConfig,
    ConfidenceThresholds,
    NormalizationConfig,
    LoggingConfig,
    SystemConfig,
)


class YAMLConfigLoader:
    """Load configuration from YAML file with environment variable substitution."""

    def __init__(self, config_path: str, load_env: bool = True):
        """
        Initialize YAML config loader.

        Args:
            config_path: Path to YAML config file
            load_env: Whether to load .env file
        """
        self.config_path = Path(config_path)
        if load_env:
            # Load .env file if it exists
            env_path = self.config_path.parent.parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)

    def load(self) -> Config:
        """
        Load configuration from YAML file.

        Returns:
            Config instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        # Load YAML
        with open(self.config_path, "r") as f:
            raw_config = yaml.safe_load(f)

        # Substitute environment variables
        config_with_env = self._substitute_env_vars(raw_config)

        # Parse into Pydantic models
        return self._parse_config(config_with_env)

    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        Recursively substitute ${VAR} with environment variables.

        Args:
            obj: Object to process (dict, list, str, etc.)

        Returns:
            Processed object with substitutions
        """
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # Find all ${VAR} or $VAR patterns
            pattern = r'\$\{([^}]+)\}|\$([A-Z_][A-Z0-9_]*)'

            def replace_var(match):
                var_name = match.group(1) or match.group(2)
                env_value = os.getenv(var_name)
                if env_value is None:
                    # Keep original if not found (will fail validation if required)
                    return match.group(0)
                return env_value

            return re.sub(pattern, replace_var, obj)
        else:
            return obj

    def _parse_config(self, raw_config: Dict[str, Any]) -> Config:
        """
        Parse raw config dict into Config object.

        Args:
            raw_config: Raw configuration dictionary

        Returns:
            Config instance
        """
        # Parse database
        database = DatabaseConfig(**raw_config["database"])

        # Parse AI providers
        ai_providers_raw = raw_config["ai_providers"]
        # Check for default in two places: inside ai_providers or at top level
        if "default" in ai_providers_raw:
            default_provider = ai_providers_raw.pop("default")
        else:
            default_provider = raw_config.get("default_provider", "anthropic")
        ai_providers = {
            name: AIProviderConfig(**config)
            for name, config in ai_providers_raw.items()
        }

        # Parse agents
        agents = {
            name: AgentTypeConfig(**config)
            for name, config in raw_config["agents"].items()
        }

        # Parse confidence thresholds
        confidence = ConfidenceThresholds(**raw_config["confidence_thresholds"])

        # Parse normalization (use defaults if not provided)
        normalization = NormalizationConfig(**raw_config.get("normalization", {}))

        # Parse logging (use defaults if not provided)
        logging_config = LoggingConfig(**raw_config.get("logging", {}))

        # Parse system (use defaults if not provided)
        system = SystemConfig(**raw_config.get("system", {}))

        # Create main config
        return Config(
            database=database,
            ai_providers=ai_providers,
            agents=agents,
            confidence=confidence,
            normalization=normalization,
            logging=logging_config,
            system=system,
            default_provider=default_provider,
        )


class EnvConfigLoader:
    """Load configuration entirely from environment variables."""

    PREFIX = "RESEARCH_ASSISTANT_"

    def load(self) -> Config:
        """
        Load configuration from environment variables.

        Environment variables should be prefixed with RESEARCH_ASSISTANT_
        and use double underscores for nesting:

        Examples:
            RESEARCH_ASSISTANT_DATABASE__HOST=localhost
            RESEARCH_ASSISTANT_DATABASE__PORT=5432
            RESEARCH_ASSISTANT_AI_PROVIDERS__OPENAI__API_KEY=sk-...

        Returns:
            Config instance
        """
        # Build nested dict from environment variables
        config_dict = self._build_config_dict()

        # Create YAMLConfigLoader with the dict (skip env var substitution)
        loader = YAMLConfigLoader.__new__(YAMLConfigLoader)
        return loader._parse_config(config_dict)

    def _build_config_dict(self) -> Dict[str, Any]:
        """Build nested config dictionary from environment variables."""
        config: Dict[str, Any] = {}

        for key, value in os.environ.items():
            if not key.startswith(self.PREFIX):
                continue

            # Remove prefix and split by __
            parts = key[len(self.PREFIX):].lower().split("__")

            # Navigate/create nested structure
            current = config
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Set value (try to convert types)
            final_key = parts[-1]
            current[final_key] = self._convert_value(value)

        return config

    def _convert_value(self, value: str) -> Any:
        """
        Convert string value to appropriate type.

        Args:
            value: String value from environment

        Returns:
            Converted value
        """
        # Boolean
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # String (default)
        return value
