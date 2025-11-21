# Testing Framework

Comprehensive test suite for the Research Verification Agent System.

## Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
python run_tests.py all

# Run only critical tests
python run_tests.py critical

# Run tests with coverage
python run_tests.py coverage
```

## Test Organization

```
tests/
├── unit/                    # Unit tests (fast, no external dependencies)
│   ├── test_qualifier_extractor.py  # CRITICAL: Qualifier preservation
│   └── test_pdf_extractor.py        # PDF text extraction
├── integration/             # Integration tests (may use DB/APIs)
└── fixtures/                # Shared test data
```

## Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (DB/API required)
- `@pytest.mark.critical` - Critical path tests (MUST always pass)
- `@pytest.mark.slow` - Slow tests (>1 second)
- `@pytest.mark.requires_api` - Requires API keys
- `@pytest.mark.requires_db` - Requires database connection

## Running Tests

### Using the Test Runner

```bash
# All tests
python run_tests.py all

# Unit tests only
python run_tests.py unit

# Integration tests only
python run_tests.py integration

# Critical tests only (must always pass)
python run_tests.py critical

# Fast tests (exclude slow)
python run_tests.py fast

# Specific component tests
python run_tests.py qualifier   # Qualifier extractor (CRITICAL)
python run_tests.py pdf         # PDF extractor

# Coverage report
python run_tests.py coverage    # Generates htmlcov/index.html
```

### Using pytest directly

```bash
# All tests
pytest

# Specific file
pytest tests/unit/test_qualifier_extractor.py

# Specific test
pytest tests/unit/test_qualifier_extractor.py::TestModalQualifierExtraction::test_extract_can_modal

# With markers
pytest -m critical           # Only critical tests
pytest -m "unit and not slow"  # Fast unit tests
pytest -m "not requires_api" # Tests that don't need API keys

# Verbose output
pytest -v

# Show test coverage
pytest --cov=research_agent --cov-report=term-missing

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

## Test Coverage Goals

| Component | Target Coverage | Critical Tests |
|-----------|----------------|----------------|
| Qualifier Extractor | 100% | ✅ Yes (60+ tests) |
| PDF Extractor | 90% | ✅ Yes (15+ tests) |
| Claim Extractor | 85% | Planned |
| Normalizer | 90% | Planned |
| Agents | 80% | Planned |
| Database | 85% | Planned |
| Overall | 85% | - |

## Critical Test Coverage

### Qualifier Extractor (MOST CRITICAL)

The qualifier extractor has the most comprehensive test coverage because it's the foundation of the system. Losing qualifiers changes claim meaning catastrophically.

**60+ tests covering**:
- ✅ All modal qualifiers (can, may, might, could, would, should, must)
- ✅ All frequency qualifiers (always, never, often, rarely, sometimes, usually)
- ✅ All quantity qualifiers (all, some, most, many, few, several)
- ✅ Multiple qualifiers in same claim
- ✅ Qualifier preservation verification (AUTO-FAIL detection)
- ✅ Claim strength analysis
- ✅ Edge cases (empty, whitespace, unicode, special chars)
- ✅ Real-world claims from Szasz paper

**Critical test examples**:
```python
# Must detect modal loss (AUTO-FAIL)
original = "Mental illness can exist in theory"
bad = "Mental illness exists in theory"
assert verify_preservation(original, bad)['preserved'] == False

# Must preserve all qualifiers
original = "Some studies often suggest this may be true"
bad = "Studies suggest this is true"
assert len(verify_preservation(original, bad)['missing']) >= 2
```

## Continuous Integration

### Pre-commit Checks

Before committing code, run:

```bash
# Critical tests must pass
python run_tests.py critical

# All unit tests should pass
python run_tests.py unit

# Check coverage
python run_tests.py coverage
```

### CI Pipeline (Planned)

```yaml
# .github/workflows/tests.yml
- Run critical tests (must pass)
- Run all unit tests (must pass)
- Run integration tests (can be flaky)
- Generate coverage report
- Fail if coverage < 80%
```

## Writing New Tests

### Test Structure

```python
import pytest
from research_agent.your_module import YourClass


@pytest.fixture
def your_fixture():
    """Create test instance."""
    return YourClass()


class TestYourFeature:
    """Test a specific feature."""

    @pytest.mark.unit
    @pytest.mark.critical  # If critical path
    def test_basic_case(self, your_fixture):
        """Test the basic case."""
        result = your_fixture.method()
        assert result == expected
```

### Critical Test Guidelines

Mark tests as `@pytest.mark.critical` if they test:
1. Qualifier preservation (any aspect)
2. Core claim extraction logic
3. Database integrity constraints
4. Evidence credibility scoring
5. Confidence calculation accuracy

### Test Naming

- File: `test_<module>.py`
- Class: `Test<Feature>` (e.g., `TestModalQualifierExtraction`)
- Function: `test_<what_it_tests>` (e.g., `test_extract_can_modal`)

### Assertions

Be specific with assertions:

```python
# ✅ Good - specific
assert len(qualifiers) == 1
assert qualifiers[0]['type'] == 'modal'
assert qualifiers[0]['text'] == 'can'

# ❌ Bad - vague
assert qualifiers
assert qualifiers[0]
```

## Debugging Failed Tests

```bash
# Run with full stack traces
pytest --tb=long

# Drop into debugger on failure
pytest --pdb

# Print output even for passing tests
pytest -s

# Show locals in traceback
pytest --showlocals
```

## Performance Testing

```bash
# Show slowest tests
pytest --durations=10

# Profile test execution
pytest --profile
```

## Test Data

### Sample Documents

- `sample papers/SHORT-The-Myth-of-Mental-Illness.pdf` - 6 pages, ~17k words
- Used for integration tests and demonstrations

### Fixtures

Shared fixtures are defined in `tests/conftest.py`:
- `sample_claims` - 5 claims from Szasz paper
- `modal_qualifier_examples` - Examples of all modals
- `frequency_qualifier_examples` - Examples of all frequency qualifiers
- `quantity_qualifier_examples` - Examples of all quantity qualifiers

## Code Coverage Reports

After running `python run_tests.py coverage`:

1. **Terminal report** - Shows line-by-line coverage
2. **HTML report** - Open `htmlcov/index.html` in browser

Coverage reports show:
- Lines executed vs. missed
- Branch coverage
- Files with low coverage

## Next Steps

### Planned Test Additions

1. **Claim Extractor Tests**
   - AI prompt validation
   - Claim type classification
   - Confidence scoring

2. **Normalizer Tests**
   - AI-generated normalizations
   - Human-in-the-loop workflow
   - Learning from corrections

3. **Agent Tests**
   - Work queue polling
   - Investigation execution
   - Finding generation

4. **Database Tests**
   - Schema integrity
   - Trigger functionality
   - Concurrent access

5. **Integration Tests**
   - Full pipeline (PDF → Report)
   - Multi-agent coordination
   - Database + AI integration

### Test Coverage Targets

- Phase 1 (Current): 60+ tests, core components
- Phase 2: 150+ tests, all components
- Phase 3: 300+ tests, full integration
- Target: 85%+ overall coverage

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
