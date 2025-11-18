# Module Creation Guide

This guide provides a **template and checklist** for creating new modules in the Research Assistant Tool platform. The `models` module serves as the reference implementation.

## Overview

All modules follow the same structure and conventions to ensure consistency and maintainability.

## Quick Start

```bash
# 1. Create module structure
mkdir -p modules/your-module/src/research_assistant_your_module
mkdir -p modules/your-module/tests

# 2. Create pyproject.toml
cp modules/models/pyproject.toml modules/your-module/
# Edit name, description, dependencies

# 3. Create source files
# Add your Python files to src/research_assistant_your_module/

# 4. Create tests
# Add test files to tests/

# 5. Install and test
cd modules/your-module
pip install -e ".[dev]"
pytest

# 6. Commit
git add modules/your-module
git commit -m "feat: add your-module"
```

## Standard Module Structure

```
modules/your-module/
├── pyproject.toml           # Package configuration
├── README.md                # Module documentation
├── src/
│   └── research_assistant_your_module/
│       ├── __init__.py      # Package exports
│       ├── module1.py       # Your code
│       ├── module2.py
│       └── ...
└── tests/
    ├── conftest.py          # Shared fixtures
    ├── test_module1.py      # Tests
    ├── test_module2.py
    └── ...
```

## pyproject.toml Template

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "research-assistant-your-module"  # ← Change this
version = "0.1.0"
description = "Your module description"  # ← Change this
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Research Assistant Tool Team"}
]
keywords = ["research", "your", "keywords"]  # ← Change this
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

dependencies = [
    # Your dependencies here
    # Example: "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0",  # If you use async
    "black>=23.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/research-assistant-tool"
Repository = "https://github.com/yourusername/research-assistant-tool"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"  # If you use async
addopts = "--cov=research_assistant_your_module --cov-report=term-missing --cov-report=html"

[tool.black]
line-length = 88
target-version = ["py38", "py39", "py310", "py311"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true

[tool.ruff]
line-length = 88
target-version = "py38"
select = ["E", "F", "I", "N", "W"]

[tool.coverage.run]
source = ["src"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

## __init__.py Template

```python
"""Your Module - Brief description.

Longer description of what this module does.
"""

from .module1 import Class1, Class2
from .module2 import function1, function2

__version__ = "0.1.0"

__all__ = [
    "Class1",
    "Class2",
    "function1",
    "function2",
]
```

## README.md Template

```markdown
# Research Assistant Your Module

Brief description of what this module does.

## Installation

\`\`\`bash
cd modules/your-module
pip install -e .

# With dev dependencies
pip install -e ".[dev]"
\`\`\`

## Usage

\`\`\`python
from research_assistant_your_module import YourClass

# Example usage
obj = YourClass()
result = obj.do_something()
\`\`\`

## API Reference

### Class1

Description...

### Class2

Description...

## Development

### Running Tests

\`\`\`bash
pytest
\`\`\`

### Test Coverage

\`\`\`bash
pytest --cov
\`\`\`

### Code Formatting

\`\`\`bash
black src/ tests/
\`\`\`

## License

MIT
```

## Testing Best Practices

### 1. Use pytest fixtures (conftest.py)

```python
import pytest

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value"}

@pytest.fixture
async def async_resource():
    """Async fixture example."""
    resource = await create_resource()
    yield resource
    await resource.cleanup()
```

### 2. Organize tests by class

```python
class TestYourClass:
    """Tests for YourClass."""

    def test_initialization(self):
        """Test object creation."""
        obj = YourClass()
        assert obj is not None

    def test_method(self):
        """Test specific method."""
        obj = YourClass()
        result = obj.method()
        assert result == expected
```

### 3. Test validation

```python
def test_validation_passes(self):
    """Test that valid input passes."""
    obj = YourClass(valid_param="value")
    assert obj.valid_param == "value"

def test_validation_fails(self):
    """Test that invalid input raises error."""
    with pytest.raises(ValueError):
        YourClass(invalid_param="bad value")
```

### 4. Test async code

```python
@pytest.mark.asyncio
async def test_async_method():
    """Test async method."""
    obj = YourClass()
    result = await obj.async_method()
    assert result is not None
```

## Development Workflow

### 1. Create Module

```bash
# Use template or copy from models/
mkdir -p modules/new-module/src/research_assistant_new_module
mkdir -p modules/new-module/tests

# Copy template files
cp modules/models/pyproject.toml modules/new-module/
# Edit pyproject.toml
```

### 2. Implement Code

```python
# src/research_assistant_new_module/core.py

class YourClass:
    """Your class implementation."""

    def __init__(self, param: str):
        """Initialize."""
        self.param = param

    def method(self) -> str:
        """Your method."""
        return f"Processed: {self.param}"
```

### 3. Write Tests

```python
# tests/test_core.py

import pytest
from research_assistant_new_module import YourClass

class TestYourClass:
    def test_initialization(self):
        obj = YourClass("test")
        assert obj.param == "test"

    def test_method(self):
        obj = YourClass("test")
        result = obj.method()
        assert result == "Processed: test"
```

### 4. Install and Test

```bash
cd modules/new-module
pip install -e ".[dev]"
pytest --cov
```

### 5. Iterate

- Add more features
- Write more tests
- Aim for 80%+ coverage
- Run `black src/ tests/` for formatting
- Run `mypy src/` for type checking

### 6. Document

- Update README.md
- Add docstrings to all public functions/classes
- Add usage examples

### 7. Commit

```bash
git add modules/new-module
git commit -m "feat: add new-module with X functionality"
```

## Quality Checklist

Before considering a module "done":

- [ ] **Code Quality**
  - [ ] All functions have docstrings
  - [ ] Type hints on function signatures
  - [ ] Code formatted with `black`
  - [ ] No linting errors (`ruff check src/`)
  - [ ] Passes type checking (`mypy src/`)

- [ ] **Testing**
  - [ ] 80%+ test coverage
  - [ ] Tests pass (`pytest`)
  - [ ] Tests cover happy path and edge cases
  - [ ] Tests cover error conditions
  - [ ] Async tests if applicable

- [ ] **Documentation**
  - [ ] README.md with:
    - [ ] Overview
    - [ ] Installation instructions
    - [ ] Usage examples
    - [ ] API reference
    - [ ] Development guide
  - [ ] Docstrings on all public APIs
  - [ ] Examples in docstrings

- [ ] **Package Configuration**
  - [ ] pyproject.toml properly configured
  - [ ] Correct dependencies listed
  - [ ] Version number set
  - [ ] Package installs correctly

- [ ] **Integration**
  - [ ] Exports in `__init__.py`
  - [ ] No circular dependencies
  - [ ] Compatible with Python 3.8+

## Common Pitfalls

### ❌ Don't: Mix business logic with database access

```python
# Bad
class ClaimExtractor:
    def extract(self, text):
        claims = self._parse(text)
        # Database access mixed in
        db.execute("INSERT INTO claims ...")
        return claims
```

### ✅ Do: Separate concerns

```python
# Good
class ClaimExtractor:
    def extract(self, text) -> List[Claim]:
        """Extract claims from text (pure logic)."""
        claims = self._parse(text)
        return claims  # Let caller decide what to do with them
```

### ❌ Don't: Hardcode dependencies

```python
# Bad
class Processor:
    def __init__(self):
        self.ai = OpenAIClient()  # Hardcoded!
```

### ✅ Do: Inject dependencies

```python
# Good
class Processor:
    def __init__(self, ai_provider: AIInterface):
        self.ai = ai_provider  # Injected, can swap implementations
```

### ❌ Don't: Skip validation

```python
# Bad
def process(data):
    # Assumes data is valid
    return data["field"]
```

### ✅ Do: Validate inputs

```python
# Good
from pydantic import BaseModel

class InputData(BaseModel):
    field: str

def process(data: InputData) -> str:
    # Data is guaranteed valid
    return data.field
```

## Examples

### Example 1: Pure Library (Tier 1)

See `modules/models/` for a complete example of a Tier 1 module with:
- Zero business logic
- 99% test coverage
- 28 tests
- Comprehensive documentation

### Example 2: Service with Dependencies (Tier 2)

```python
# Future module: modules/claim-extraction/

from research_assistant_models import Claim
from research_assistant_ai import AIInterface

class ClaimExtractor:
    def __init__(self, ai: AIInterface):
        self.ai = ai  # Depends on Tier 1

    async def extract(self, text: str) -> List[Claim]:
        # Implementation...
```

## Module Tier Guidelines

### Tier 1: Core Infrastructure
- **No dependencies** on other internal modules
- **Pure libraries** - config, models, connectors
- **Example:** models, config-loader, db-connectors, ai-providers

### Tier 2: Domain Services
- **Can depend on:** Tier 1 only
- **Business logic** but no orchestration
- **Example:** document-extraction, claim-extraction, research-apis

### Tier 3: Application Services
- **Can depend on:** Tier 1 + Tier 2
- **Orchestration** and workflows
- **Example:** investigation-engine, graph-builder, reporting-engine

### Tier 4: Interface Layers
- **Can depend on:** All tiers below
- **User-facing** interfaces
- **Example:** web-api, web-ui, cli-interface, graph-ui

### Tier 5: Standalone
- **Zero dependencies** on this project
- **Publishable** to PyPI
- **Example:** research-agents

## Summary

✅ **Use the `models` module as your template**
✅ **Follow the standard structure**
✅ **Write tests first (TDD) or alongside code**
✅ **Aim for 80%+ coverage**
✅ **Document as you go**
✅ **Keep modules focused and small**
✅ **Respect tier dependencies**

**The key to successful modularization is consistency!**

---

For questions or to propose changes to this guide, open an issue or PR.
