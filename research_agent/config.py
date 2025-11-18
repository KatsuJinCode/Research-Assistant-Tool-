"""
Configuration loader for Research Verification Agent System.
Loads config from YAML and substitutes environment variables.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict
import yaml
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class AIProviderConfig:
    """AI provider configuration."""
    api_key: str
    model: str
    temperature: float
    max_tokens: int


@dataclass
class AgentTypeConfig:
    """Agent type configuration."""
    count: int
    enabled: bool
    description: str


@dataclass
class ConfidenceThresholds:
    """Confidence threshold configuration."""
    high: float
    medium: float
    low: float
    low_confidence_additional_agents: int
    low_confidence_depth_increase: int


@dataclass
class NormalizationConfig:
    """Normalization configuration."""
    require_human_validation: bool
    min_confidence_for_auto_approve: float
    max_candidates: int
    auto_fail_if_qualifiers_lost: bool


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str
    file: str
    format: str
    max_bytes: int
    backup_count: int


@dataclass
class SystemConfig:
    """System configuration."""
    agent_poll_interval_seconds: int
    investigation_timeout_seconds: int
    expansion_scheduler_interval_hours: int
    discovery_scheduler_interval_hours: int
    max_concurrent_investigations: int
    max_api_calls_per_minute: int


class Config:
    """Main configuration class."""

    def __init__(self, config_path: str = None):
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config.yaml. Defaults to config/config.yaml
        """
        if config_path is None:
            # Default to config/config.yaml in project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self._raw_config = self._load_yaml()
        self._substitute_env_vars()

        # Parse into dataclasses
        self.database = self._parse_database()
        self.ai_providers = self._parse_ai_providers()
        self.agents = self._parse_agents()
        self.confidence = self._parse_confidence()
        self.normalization = self._parse_normalization()
        self.logging = self._parse_logging()
        self.system = self._parse_system()

    def _load_yaml(self) -> Dict[str, Any]:
        """Load YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _substitute_env_vars(self):
        """Recursively substitute ${VAR} with environment variables."""
        def substitute(obj):
            if isinstance(obj, dict):
                return {k: substitute(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [substitute(item) for item in obj]
            elif isinstance(obj, str):
                # Find all ${VAR} patterns
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, obj)
                for var_name in matches:
                    env_value = os.getenv(var_name, '')
                    if not env_value:
                        # Try without prefix (e.g., if user set OPENAI_API_KEY directly)
                        env_value = os.getenv(var_name, '')
                    obj = obj.replace(f'${{{var_name}}}', env_value)
                return obj
            else:
                return obj

        self._raw_config = substitute(self._raw_config)

    def _parse_database(self) -> DatabaseConfig:
        """Parse database configuration."""
        db = self._raw_config['database']
        return DatabaseConfig(
            host=db['host'],
            port=db['port'],
            name=db['name'],
            user=db['user'],
            password=db['password']
        )

    def _parse_ai_providers(self) -> Dict[str, AIProviderConfig]:
        """Parse AI provider configurations."""
        providers = {}
        provider_configs = self._raw_config['ai_providers']
        default = provider_configs.get('default', 'anthropic')

        for name in ['openai', 'anthropic']:
            if name in provider_configs:
                config = provider_configs[name]
                providers[name] = AIProviderConfig(
                    api_key=config['api_key'],
                    model=config['model'],
                    temperature=config['temperature'],
                    max_tokens=config['max_tokens']
                )

        # Set default provider
        self.default_provider = default
        return providers

    def _parse_agents(self) -> Dict[str, AgentTypeConfig]:
        """Parse agent configurations."""
        agents = {}
        agent_configs = self._raw_config['agents']

        for name, config in agent_configs.items():
            agents[name] = AgentTypeConfig(
                count=config['count'],
                enabled=config['enabled'],
                description=config.get('description', '')
            )

        return agents

    def _parse_confidence(self) -> ConfidenceThresholds:
        """Parse confidence threshold configuration."""
        conf = self._raw_config['confidence_thresholds']
        return ConfidenceThresholds(
            high=conf['high'],
            medium=conf['medium'],
            low=conf['low'],
            low_confidence_additional_agents=conf['low_confidence_additional_agents'],
            low_confidence_depth_increase=conf['low_confidence_depth_increase']
        )

    def _parse_normalization(self) -> NormalizationConfig:
        """Parse normalization configuration."""
        norm = self._raw_config['normalization']
        return NormalizationConfig(
            require_human_validation=norm['require_human_validation'],
            min_confidence_for_auto_approve=norm['min_confidence_for_auto_approve'],
            max_candidates=norm['max_candidates'],
            auto_fail_if_qualifiers_lost=norm['auto_fail_if_qualifiers_lost']
        )

    def _parse_logging(self) -> LoggingConfig:
        """Parse logging configuration."""
        log = self._raw_config['logging']
        return LoggingConfig(
            level=log['level'],
            file=log['file'],
            format=log['format'],
            max_bytes=log['max_bytes'],
            backup_count=log['backup_count']
        )

    def _parse_system(self) -> SystemConfig:
        """Parse system configuration."""
        sys = self._raw_config['system']
        return SystemConfig(
            agent_poll_interval_seconds=sys['agent_poll_interval_seconds'],
            investigation_timeout_seconds=sys['investigation_timeout_seconds'],
            expansion_scheduler_interval_hours=sys['expansion_scheduler_interval_hours'],
            discovery_scheduler_interval_hours=sys['discovery_scheduler_interval_hours'],
            max_concurrent_investigations=sys['max_concurrent_investigations'],
            max_api_calls_per_minute=sys['max_api_calls_per_minute']
        )

    def get_active_agents(self) -> Dict[str, AgentTypeConfig]:
        """Get only enabled agents."""
        return {name: config for name, config in self.agents.items() if config.enabled}


# Global config instance
_config_instance = None


def load_config(config_path: str = None) -> Config:
    """
    Load configuration (singleton pattern).

    Args:
        config_path: Optional path to config file

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None or config_path is not None:
        _config_instance = Config(config_path)
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
