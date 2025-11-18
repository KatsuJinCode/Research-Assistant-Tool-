# Research Assistant Config Loader

Unified configuration management for the Research Assistant Tool platform with environment variable substitution, validation, and type safety using Pydantic.

## Features

- **YAML Configuration** - Load config from YAML files with `${VAR}` substitution
- **Environment Variables** - Load config entirely from env vars with `RESEARCH_ASSISTANT_` prefix
- **Type Safety** - All configs are Pydantic models with automatic validation
- **Immutable** - Frozen config objects prevent accidental modification
- **Validation** - Comprehensive validation with helpful error messages
- **Singleton Pattern** - Global config instance management

## Installation

```bash
cd modules/config-loader
pip install -e .

# With dev dependencies
pip install -e ".[dev]"
```

## Usage

### Basic Usage

```python
from research_assistant_config import load_config, get_config

# Load configuration from YAML file
config = load_config("config/config.yaml")

# Access configuration
print(config.database.host)
print(config.default_provider)

# Get active agents
active_agents = config.get_active_agents()

# Get AI provider config
provider = config.get_ai_provider("openai")
print(provider.api_key, provider.model)

# Get singleton instance later
config = get_config()
```

### YAML Configuration

Create a `config.yaml` file:

```yaml
database:
  host: localhost
  port: 5432
  name: research_db
  user: research_user
  password: ${DB_PASSWORD}  # Environment variable substitution

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
    description: Extracts citations from academic papers
  claim_extractor:
    count: 2
    enabled: true
    description: Extracts verifiable claims

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
  file: logs/app.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  max_bytes: 10485760
  backup_count: 5

system:
  agent_poll_interval_seconds: 30
  investigation_timeout_seconds: 300
  expansion_scheduler_interval_hours: 1
  discovery_scheduler_interval_hours: 6
  max_concurrent_investigations: 10
  max_api_calls_per_minute: 60
```

Then load it:

```python
from research_assistant_config import YAMLConfigLoader

loader = YAMLConfigLoader("config/config.yaml")
config = loader.load()
```

### Environment Variables

Load configuration entirely from environment variables:

```bash
export RESEARCH_ASSISTANT_DATABASE__HOST=localhost
export RESEARCH_ASSISTANT_DATABASE__PORT=5432
export RESEARCH_ASSISTANT_DATABASE__NAME=research_db
export RESEARCH_ASSISTANT_DATABASE__USER=research_user
export RESEARCH_ASSISTANT_DATABASE__PASSWORD=secret

export RESEARCH_ASSISTANT_AI_PROVIDERS__OPENAI__API_KEY=sk-...
export RESEARCH_ASSISTANT_AI_PROVIDERS__OPENAI__MODEL=gpt-4
export RESEARCH_ASSISTANT_AI_PROVIDERS__OPENAI__TEMPERATURE=0.7
export RESEARCH_ASSISTANT_AI_PROVIDERS__OPENAI__MAX_TOKENS=4000

export RESEARCH_ASSISTANT_AGENTS__CITATION_EXTRACTOR__COUNT=3
export RESEARCH_ASSISTANT_AGENTS__CITATION_EXTRACTOR__ENABLED=true

export RESEARCH_ASSISTANT_CONFIDENCE_THRESHOLDS__HIGH=0.9
export RESEARCH_ASSISTANT_CONFIDENCE_THRESHOLDS__MEDIUM=0.7
export RESEARCH_ASSISTANT_CONFIDENCE_THRESHOLDS__LOW=0.5

export RESEARCH_ASSISTANT_DEFAULT_PROVIDER=openai
```

Then load:

```python
from research_assistant_config import EnvConfigLoader

loader = EnvConfigLoader()
config = loader.load()
```

### Configuration Validation

```python
from research_assistant_config import validate_config, ValidationError

try:
    validate_config(config)
    print("✓ Configuration is valid")
except ValidationError as e:
    print(f"✗ Configuration validation failed:")
    for error in e.errors:
        print(f"  - {error}")
```

## API Reference

### Config

Main configuration class containing all settings.

**Properties:**
- `database: DatabaseConfig` - Database connection settings
- `ai_providers: Dict[str, AIProviderConfig]` - AI provider configurations
- `agents: Dict[str, AgentTypeConfig]` - Agent type configurations
- `confidence: ConfidenceThresholds` - Confidence threshold settings
- `normalization: NormalizationConfig` - Normalization settings
- `logging: LoggingConfig` - Logging configuration
- `system: SystemConfig` - System-wide settings
- `default_provider: str` - Default AI provider name

**Methods:**
- `get_active_agents() -> Dict[str, AgentTypeConfig]` - Get only enabled agents
- `get_ai_provider(provider_name: Optional[str] = None) -> AIProviderConfig` - Get AI provider config

### DatabaseConfig

Database connection configuration.

**Fields:**
- `host: str` - Database host
- `port: int` - Database port (1-65535)
- `name: str` - Database name
- `user: str` - Database user
- `password: str` - Database password

**Properties:**
- `connection_string: str` - PostgreSQL connection string
- `connection_string_async: str` - Async PostgreSQL connection string (asyncpg)

### AIProviderConfig

AI provider configuration.

**Fields:**
- `api_key: str` - API key (cannot be empty)
- `model: str` - Model identifier
- `temperature: float` - Sampling temperature (0.0-2.0, default: 0.7)
- `max_tokens: int` - Maximum tokens (1-128000, default: 4000)

### AgentTypeConfig

Agent type configuration.

**Fields:**
- `count: int` - Number of agent instances (0-100)
- `enabled: bool` - Whether agent type is enabled (default: True)
- `description: str` - Agent type description (default: "")

### ConfidenceThresholds

Confidence threshold configuration.

**Fields:**
- `high: float` - High confidence threshold (0.0-1.0)
- `medium: float` - Medium confidence threshold (0.0-1.0, must be < high)
- `low: float` - Low confidence threshold (0.0-1.0, must be < medium)
- `low_confidence_additional_agents: int` - Additional agents for low confidence (default: 5)
- `low_confidence_depth_increase: int` - Depth increase for low confidence (default: 2)

### NormalizationConfig

Normalization configuration.

**Fields:**
- `require_human_validation: bool` - Require human validation (default: True)
- `min_confidence_for_auto_approve: float` - Min confidence for auto-approval (0.0-1.0, default: 0.95)
- `max_candidates: int` - Max normalization candidates (1-20, default: 4)
- `auto_fail_if_qualifiers_lost: bool` - Auto-fail if qualifiers lost (default: True)

### LoggingConfig

Logging configuration.

**Fields:**
- `level: str` - Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `file: str` - Log file path (default: "logs/app.log")
- `format: str` - Log format string
- `max_bytes: int` - Max log file size in bytes (default: 10485760)
- `backup_count: int` - Number of backup log files (0-100, default: 5)

### SystemConfig

System-wide configuration.

**Fields:**
- `agent_poll_interval_seconds: int` - Agent polling interval (1-3600, default: 30)
- `investigation_timeout_seconds: int` - Investigation timeout (10-7200, default: 300)
- `expansion_scheduler_interval_hours: int` - Expansion scheduler interval (1-168, default: 1)
- `discovery_scheduler_interval_hours: int` - Discovery scheduler interval (1-168, default: 6)
- `max_concurrent_investigations: int` - Max concurrent investigations (1-1000, default: 10)
- `max_api_calls_per_minute: int` - Max API calls per minute (1-10000, default: 60)

### YAMLConfigLoader

Load configuration from YAML file with environment variable substitution.

```python
loader = YAMLConfigLoader("config/config.yaml", load_env=True)
config = loader.load()
```

**Parameters:**
- `config_path: str` - Path to YAML config file
- `load_env: bool` - Whether to load `.env` file (default: True)

**Methods:**
- `load() -> Config` - Load and parse configuration

### EnvConfigLoader

Load configuration entirely from environment variables.

```python
loader = EnvConfigLoader()
config = loader.load()
```

**Methods:**
- `load() -> Config` - Load configuration from environment variables

### Functions

**`load_config(config_path: Optional[str] = None) -> Config`**

Load configuration from YAML file and set as global singleton.

**`get_config() -> Config`**

Get current global configuration instance.

**`validate_config(config: Config) -> None`**

Validate configuration for common issues. Raises `ValidationError` if invalid.

### Exceptions

**`ValidationError(message: str, errors: Optional[List[str]] = None)`**

Configuration validation error with list of specific errors.

## Development

### Running Tests

```bash
pytest
```

### Test Coverage

```bash
pytest --cov
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Configuration Best Practices

1. **Use Environment Variables for Secrets**
   ```yaml
   api_key: ${OPENAI_API_KEY}  # ✓ Good
   api_key: sk-actual-key       # ✗ Bad - hardcoded secret
   ```

2. **Validate Early**
   ```python
   config = load_config("config.yaml")
   validate_config(config)  # Catch issues immediately
   ```

3. **Use Singleton Pattern**
   ```python
   # Load once at startup
   config = load_config()

   # Use throughout application
   config = get_config()
   ```

4. **Separate Dev/Prod Configs**
   ```bash
   # Development
   load_config("config/dev.yaml")

   # Production
   load_config("config/prod.yaml")
   ```

5. **Don't Modify Config at Runtime**
   ```python
   # Config objects are frozen/immutable
   config.database.host = "new"  # ✗ Raises error
   ```

## Examples

### Example 1: Simple Application

```python
from research_assistant_config import load_config, get_config

# Startup: load configuration
config = load_config("config/config.yaml")

# Use throughout app
def connect_database():
    config = get_config()
    conn_str = config.database.connection_string
    # ... connect to database

def get_ai_client():
    config = get_config()
    provider = config.get_ai_provider()
    return AIClient(provider.api_key, provider.model)
```

### Example 2: Environment-Specific Configuration

```python
import os
from research_assistant_config import load_config

# Load config based on environment
env = os.getenv("ENVIRONMENT", "development")
config_file = f"config/{env}.yaml"
config = load_config(config_file)
```

### Example 3: Custom Validation

```python
from research_assistant_config import load_config, validate_config, ValidationError

config = load_config("config.yaml")

try:
    validate_config(config)

    # Additional custom validation
    if config.system.max_concurrent_investigations > 50:
        print("⚠ Warning: High concurrent investigation limit")

except ValidationError as e:
    print(f"Configuration errors:")
    for error in e.errors:
        print(f"  - {error}")
    exit(1)
```

## License

MIT
