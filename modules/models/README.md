# Research Assistant Models

Shared Pydantic models for the Research Assistant Tool platform.

## Overview

This module provides **type-safe, validated data models** used across all Research Assistant Tool components. By centralizing models in one package, we ensure:

- ✅ **Consistency** - Same models everywhere
- ✅ **Type Safety** - Full Pydantic validation
- ✅ **DRY Principle** - Single source of truth
- ✅ **Easy Updates** - Change once, use everywhere

## Installation

### From source (development)

```bash
cd modules/models
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

### As a package (future)

```bash
pip install research-assistant-models
```

## Models

### Core Domain Models

#### Document
Represents a source document (PDF, DOCX, TXT, URL).

```python
from research_assistant_models import Document

doc = Document(
    title="Research Paper Title",
    source_type="pdf",
    file_path="/path/to/paper.pdf",
    full_text="Extracted text content...",
    metadata={"author": "Smith et al.", "year": 2023}
)
```

#### Claim
Represents an extracted claim from a document.

```python
from research_assistant_models import Claim, ClaimStatus

claim = Claim(
    original_text="Coffee consumption reduces risk of type 2 diabetes",
    normalized_text="Coffee consumption may reduce risk of type 2 diabetes",
    status=ClaimStatus.EXTRACTED,
    confidence_score=0.5,
    qualifiers=[
        Qualifier(
            qualifier_type="modal",
            qualifier_text="may",
            semantic_impact="Indicates possibility, not certainty"
        )
    ]
)
```

#### Evidence
Represents evidence supporting or challenging a claim.

```python
from research_assistant_models import Evidence

evidence = Evidence(
    source_category="academic",
    citation_apa="Author, A. (2023). Paper Title. Journal, 10(2), 123-145.",
    relevant_quote="Our meta-analysis found a 30% reduction in risk...",
    relevance_score=0.9,
    credibility_score=0.85
)
```

#### Finding
Represents an investigation finding (supports/challenges/neutral/clarification).

```python
from research_assistant_models import Finding, FindingType

finding = Finding(
    finding_type=FindingType.SUPPORT,
    summary="Found 5 sources supporting this claim",
    detailed_analysis="Multiple large cohort studies show...",
    confidence=0.8,
    evidence=[evidence1, evidence2, evidence3]
)
```

#### Investigation
Represents an investigation task for an agent.

```python
from research_assistant_models import Investigation, AgentFramework

investigation = Investigation(
    claim_id=claim_id,
    agent_framework=AgentFramework.SUPPORT_EMPIRICAL,
    status="queued",
    priority=50
)
```

### Enums

#### ClaimStatus
```python
class ClaimStatus(str, Enum):
    EXTRACTED = "extracted"
    QUEUED = "queued"
    INVESTIGATING = "investigating"
    SUPPORTED = "supported"
    CHALLENGED = "challenged"
    VERIFIED = "verified"
    UNCERTAIN = "uncertain"
    ARCHIVED = "archived"
```

#### FindingType
```python
class FindingType(str, Enum):
    SUPPORT = "support"
    CHALLENGE = "challenge"
    NEUTRAL = "neutral"
    CLARIFICATION = "clarification"
```

#### AgentFramework
```python
class AgentFramework(str, Enum):
    SUPPORT_EMPIRICAL = "support_empirical"
    CHALLENGE_EMPIRICAL = "challenge_empirical"
    ANALYSIS_DEFINITIONAL = "analysis_definitional"
```

## Features

### Automatic Validation

All models use Pydantic for automatic validation:

```python
# This will raise ValidationError
claim = Claim(
    original_text="Test claim",
    confidence_score=1.5  # ❌ Must be between 0.0 and 1.0
)

# This works
claim = Claim(
    original_text="Test claim",
    confidence_score=0.8  # ✅ Valid
)
```

### JSON Serialization

All models can be serialized to/from JSON:

```python
# To JSON
claim_json = claim.model_dump_json()

# From JSON
claim = Claim.model_validate_json(claim_json)

# To dict
claim_dict = claim.model_dump()
```

### Custom Validators

Some models have custom validators:

```python
# Qualifier type must be one of predefined types
qualifier = Qualifier(
    qualifier_type="modal",  # ✅ Valid
    qualifier_text="may",
    semantic_impact="..."
)

qualifier = Qualifier(
    qualifier_type="invalid",  # ❌ ValidationError
    qualifier_text="may",
    semantic_impact="..."
)
```

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

### Linting

```bash
ruff check src/
```

## Design Principles

1. **Immutability when possible** - Use frozen models for value objects
2. **Validation at boundaries** - Validate all inputs
3. **Optional by default for DB fields** - IDs, timestamps are Optional
4. **Required for business logic** - Core fields are required
5. **JSON-compatible** - All models can serialize to JSON

## Versioning

This module follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

Current version: **0.1.0** (Alpha)

## Migration from Old Code

### Before (scattered models)

```python
# In research_agent/models.py
from research_agent.models import Claim

# In web_ui/models.py
claim_dict = {"text": "...", "confidence": 0.8}

# In research-agents/
from research_agents.interfaces.models import Claim
```

### After (centralized)

```python
# Everywhere
from research_assistant_models import Claim
```

## Contributing

See the main project CONTRIBUTING.md for guidelines.

When adding new models:
1. Add model to appropriate file in `src/research_assistant_models/`
2. Export from `__init__.py`
3. Add tests in `tests/`
4. Update this README
5. Bump version in `pyproject.toml`

## License

MIT

## Questions?

Open an issue in the main Research Assistant Tool repository.
