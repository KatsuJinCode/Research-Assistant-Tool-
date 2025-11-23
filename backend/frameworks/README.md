# Research Framework YAML System

A comprehensive framework system for domain customization in the Research Assistant Tool. This system allows users to define custom research frameworks via YAML files, tailoring entity types, relationship types, prompts, and evaluation criteria to specific research domains.

## Overview

The Framework YAML System enables the Research Assistant to adapt to different research domains:

- **Medical Research**: Clinical trials, treatments, evidence-based medicine
- **Legal Research**: Case law, statutes, precedents, jurisdictional analysis
- **Scientific Research**: Hypotheses, experiments, reproducibility, peer review
- **General Research**: Flexible framework for cross-domain research

## Architecture

```
backend/frameworks/
├── __init__.py                    # Package exports
├── framework_loader.py            # Core loader & schema (Framework dataclass)
├── framework_manager.py           # Runtime management & caching
└── templates/                     # Built-in framework templates
    ├── general_research.yaml      # Default framework
    ├── medical_research.yaml      # Medical/clinical research
    ├── legal_research.yaml        # Legal/case law research
    └── scientific_research.yaml   # Scientific methodology focus
```

## Quick Start

### Using a Framework

```python
from backend.frameworks import FrameworkManager

# Get the singleton manager
manager = FrameworkManager()

# Switch to medical research framework
manager.set_framework('medical_research')

# Get current framework
framework = manager.get_current_framework()

print(f"Framework: {framework.name}")
print(f"Entity Types: {framework.entity_types}")
print(f"Relationship Types: {framework.relationship_types}")
```

### Via Web UI

1. Click **Settings** button in the top navigation
2. Select desired framework from the **Research Framework** dropdown
3. Click **View Details** to see entity types and relationships
4. Click **Save Settings** to apply the framework

## Framework Schema

A framework YAML file contains the following sections:

### Basic Information

```yaml
name: medical_research              # Unique framework identifier
description: Framework for medical and clinical research
version: 1.0.0                      # Semantic versioning
extends: general_research           # Optional: inherit from base framework
```

### Entity Types

Domain-specific entity types for the knowledge graph:

```yaml
entity_types:
  - Disease
  - Treatment
  - Drug
  - Clinical_Trial
  - Patient_Population
  - Biomarker
  # ... more entity types
```

### Relationship Types

Domain-specific relationship types between entities:

```yaml
relationship_types:
  - TREATS
  - CAUSES
  - CONTRAINDICATES
  - TESTED_ON
  - INTERACTS_WITH
  # ... more relationship types
```

### Prompts

Domain-specific prompts for extraction, analysis, and evaluation:

```yaml
prompts:
  extraction: |
    Extract medical claims from the following clinical text...

  analysis: |
    Analyze this medical claim using evidence-based medicine principles...

  evaluation: |
    Evaluate this medical evidence using GRADE criteria...

  claim_simplification: |
    Simplify this medical claim into PICO components...

  evidence_assessment: |
    Assess medical evidence strength for this claim...
```

### Evaluation Criteria

Domain-specific quality metrics:

```yaml
evaluation_criteria:
  evidence_levels:
    - Level_I_Systematic_Review
    - Level_II_RCT
    - Level_III_Controlled_Trial
    # ... more levels

  quality_metrics:
    - randomization
    - blinding
    - sample_size
    - p_value
    # ... more metrics

  authority_indicators:
    - FDA_approved
    - published_in_tier1_journal
    # ... more indicators

  minimum_confidence: 0.7  # Threshold for claim acceptance
```

### Claim Structure

How claims are structured in this domain:

```yaml
claim_structure:
  components:
    - population      # Who
    - intervention    # What
    - comparison      # Compared to what
    - outcome         # Result

  required_fields:
    - text
    - source
    - evidence_level

  optional_fields:
    - p_value
    - sample_size
    - adverse_events
```

### Evidence Requirements

What counts as evidence:

```yaml
evidence_requirements:
  source_types:
    - randomized_controlled_trial
    - systematic_review
    - meta_analysis

  minimum_sources: 2           # Require multiple sources
  preferred_date_range: last_5_years
  peer_review_required: true   # Strict peer review
```

### Source Preferences

Preferred databases and journals:

```yaml
source_preferences:
  databases:
    - PubMed
    - Cochrane_Library
    - ClinicalTrials.gov

  journals:
    - New_England_Journal_of_Medicine
    - The_Lancet
    - JAMA

  publication_types:
    - randomized_controlled_trial
    - systematic_review

  authority_sources:
    - FDA
    - WHO
    - NIH
```

## Creating a Custom Framework

### Option 1: Via Web UI

1. Click **Settings** → **Upload Custom**
2. Select your `.yaml` file
3. Framework is validated and added to the system
4. Select it from the dropdown

### Option 2: Via Python API

```python
from backend.frameworks import FrameworkManager

manager = FrameworkManager()

# Create custom framework extending base framework
custom = manager.create_custom_framework(
    name='psychology_research',
    base_framework='scientific_research',
    custom_settings={
        'entity_types': [
            'Behavior',
            'Cognitive_Process',
            'Intervention',
            'Participant_Group'
        ],
        'relationship_types': [
            'INFLUENCES',
            'CORRELATES_WITH',
            'MODERATES',
            'MEDIATES'
        ]
    }
)

# Framework is automatically saved to custom_frameworks/psychology_research.yaml
manager.set_framework('psychology_research')
```

### Option 3: Manual YAML Creation

Create a YAML file in `custom_frameworks/`:

```yaml
name: psychology_research
description: Framework for psychological research
version: 1.0.0
extends: scientific_research

entity_types:
  - Behavior
  - Cognitive_Process
  - Intervention
  - Participant_Group
  - Psychological_Measure

relationship_types:
  - INFLUENCES
  - CORRELATES_WITH
  - MODERATES
  - MEDIATES
  - PREDICTS

# ... rest of framework configuration
```

## Framework Inheritance

Frameworks can inherit from base frameworks using the `extends` field:

```yaml
name: clinical_psychology
description: Clinical psychology research
version: 1.0.0
extends: psychology_research  # Inherits from custom framework

# Additional entity types (merged with parent)
entity_types:
  - Clinical_Disorder
  - Treatment_Protocol
  - Clinical_Outcome

# These are added to psychology_research entity types
```

**Inheritance Rules:**

- Child entity types are **merged** with parent (no duplicates)
- Child relationship types are **merged** with parent
- Child prompts **override** parent prompts (if specified)
- Child evaluation criteria are **merged** with parent
- Child metadata **overrides** parent metadata

## API Endpoints

### GET /api/frameworks

List all available frameworks:

```bash
curl http://localhost:5000/api/frameworks
```

Response:
```json
{
  "success": true,
  "frameworks": [
    {
      "name": "general_research",
      "description": "General-purpose research framework",
      "version": "1.0.0",
      "type": "built-in"
    },
    {
      "name": "medical_research",
      "description": "Medical and clinical research",
      "version": "1.0.0",
      "type": "built-in"
    }
  ],
  "current": "general_research"
}
```

### GET /api/framework/current

Get current active framework:

```bash
curl http://localhost:5000/api/framework/current
```

### POST /api/framework/set

Switch active framework:

```bash
curl -X POST http://localhost:5000/api/framework/set \
  -H "Content-Type: application/json" \
  -d '{"framework_name": "medical_research"}'
```

### GET /api/framework/{name}

Get framework details:

```bash
curl http://localhost:5000/api/framework/medical_research
```

### POST /api/framework/upload

Upload custom framework YAML:

```bash
curl -X POST http://localhost:5000/api/framework/upload \
  -F "framework=@custom_framework.yaml"
```

### POST /api/framework/validate

Validate framework compatibility:

```bash
curl -X POST http://localhost:5000/api/framework/validate \
  -H "Content-Type: application/json" \
  -d '{"framework_name": "medical_research"}'
```

Response:
```json
{
  "success": true,
  "compatibility": {
    "compatible": true,
    "warnings": [],
    "unsupported_entities": [],
    "unsupported_relationships": []
  }
}
```

## Integration Points

### Triple Extractor

The framework system integrates with the knowledge graph triple extractor:

```python
from research_agent.graph_database import GraphDatabase
from backend.rag.triple_extractor import TripleExtractor

db = GraphDatabase()

# Triple extractor automatically uses current framework
extractor = TripleExtractor(db, use_framework=True)

# Only extracts triples matching framework's relationship types
triples = extractor.extract_from_neo4j()

# Semantic triples filtered by framework
semantic = extractor.get_semantic_triples()
```

### Agent System

Agents can access the current framework for domain-specific prompts:

```python
from backend.frameworks import get_framework_manager

manager = get_framework_manager()
framework = manager.get_current_framework()

# Use framework-specific extraction prompt
extraction_prompt = framework.prompts.extraction.format(text=document_text)

# Use framework-specific evaluation criteria
min_confidence = framework.evaluation_criteria.minimum_confidence
```

## Design Decisions

### 1. YAML Format

**Why YAML?**
- Human-readable and easy to edit
- Supports multi-line strings (important for prompts)
- Hierarchical structure matches framework schema
- Widely adopted in configuration files

### 2. Singleton Manager

**Why Singleton?**
- Ensures single source of truth for active framework
- Thread-safe framework switching
- Efficient caching of loaded frameworks
- Consistent framework state across the application

### 3. Framework Inheritance

**Why Inheritance?**
- Avoid duplication (DRY principle)
- Easy specialization of existing frameworks
- Gradual customization (start from base, add specifics)
- Maintain compatibility with base framework

### 4. Backward Compatibility

**Design Goal:**
- `general_research.yaml` = current default behavior
- Existing code works without any changes
- Framework system is opt-in (can disable with `use_framework=False`)

## Validation

Framework validation checks:

1. **Required fields**: `name`, `entity_types`, `relationship_types`
2. **Version format**: Semantic versioning (X.Y.Z)
3. **Confidence threshold**: Between 0.0 and 1.0
4. **Minimum sources**: At least 1
5. **No duplicates**: Entity and relationship types are unique

Example validation error:

```
ValueError: Framework validation failed:
  - Framework must define at least one entity_type
  - minimum_confidence must be between 0.0 and 1.0, got 1.5
  - Duplicate entity types: {'Claim'}
```

## Best Practices

### 1. Naming Conventions

- **Frameworks**: `snake_case` (e.g., `medical_research`)
- **Entity Types**: `PascalCase` (e.g., `Clinical_Trial`)
- **Relationship Types**: `UPPER_SNAKE_CASE` (e.g., `TESTED_ON`)

### 2. Framework Design

- Start from an existing framework (`extends: general_research`)
- Define 10-30 entity types (too few = not specific, too many = overwhelming)
- Define 10-20 relationship types (focus on key semantic relationships)
- Write clear, domain-specific prompts with examples
- Set appropriate confidence thresholds (higher for critical domains like medical/legal)

### 3. Prompt Engineering

- Use PICO format for medical research
- Use IRAC format for legal research
- Use hypothesis-method-result for scientific research
- Include specific examples in prompts
- Reference domain standards (GRADE, Bluebook, etc.)

### 4. Compatibility Checking

Always validate compatibility before switching frameworks in production:

```python
manager = FrameworkManager()
result = manager.validate_framework_compatibility('medical_research')

if result['compatible']:
    manager.set_framework('medical_research')
else:
    print("Warnings:", result['warnings'])
    # Decide whether to proceed
```

## Examples

See the built-in frameworks for complete examples:

- `templates/general_research.yaml` - Default framework
- `templates/medical_research.yaml` - Medical/clinical research
- `templates/legal_research.yaml` - Legal research
- `templates/scientific_research.yaml` - Scientific methodology

## Troubleshooting

### Framework Not Loading

**Error**: `FileNotFoundError: Framework file not found`

**Solution**: Check framework name and ensure file exists in `backend/frameworks/templates/` or `custom_frameworks/`

### Validation Errors

**Error**: `ValueError: Framework validation failed`

**Solution**: Review validation messages and fix YAML schema errors

### Compatibility Warnings

**Warning**: Entity types not supported by framework

**Solution**: Either switch to a compatible framework or modify the framework to include those entity types

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'backend.frameworks'`

**Solution**: Ensure you're running from the project root directory

## Future Enhancements

Potential improvements for future versions:

1. **Framework Templates**: Pre-built templates for more domains (business, engineering, etc.)
2. **Dynamic Prompts**: Prompt templates with variable substitution
3. **Framework Versioning**: Support multiple versions of the same framework
4. **Framework Marketplace**: Share custom frameworks with the community
5. **Auto-Detection**: Automatically suggest framework based on document content
6. **Hybrid Frameworks**: Combine multiple frameworks for interdisciplinary research

## License

Part of the Research Assistant Tool. See main project LICENSE.
