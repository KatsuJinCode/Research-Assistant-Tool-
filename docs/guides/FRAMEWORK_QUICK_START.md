# Framework System - Quick Start Guide

## What is the Framework System?

The Framework YAML System allows you to customize the Research Assistant for different research domains (medical, legal, scientific, etc.) by defining:

- **Entity Types**: What kinds of things exist in your domain (e.g., Disease, Treatment, Drug)
- **Relationship Types**: How things relate to each other (e.g., TREATS, CAUSES, CONTRAINDICATES)
- **Domain-Specific Prompts**: How the AI should analyze text in your domain
- **Evaluation Criteria**: How to judge the quality of claims and evidence

## Quick Start: Using a Built-in Framework

### Via Web UI (Easiest)

1. Open the Research Assistant: `http://localhost:5000`
2. Click the **Settings** (⚙️) button in the top navigation
3. Under "Research Framework", select your domain:
   - **General Research** - Default, works for any domain
   - **Medical Research** - Clinical trials, treatments, evidence-based medicine
   - **Legal Research** - Case law, statutes, precedents
   - **Scientific Research** - Hypotheses, experiments, reproducibility
4. Click **Save Settings**
5. Done! The assistant now uses your selected framework

### Via Python API

```python
from backend.frameworks import FrameworkManager

# Get the framework manager
manager = FrameworkManager()

# Switch to medical research framework
manager.set_framework('medical_research')

# Get current framework
framework = manager.get_current_framework()

print(f"Using: {framework.name}")
print(f"Entity types: {framework.entity_types}")
```

## What's Included?

### General Research Framework
- **Best for**: Literature reviews, cross-domain research
- **Entity Types**: Claim, Evidence, Document, Author, Concept, Finding, etc.
- **Use when**: You need flexibility or are working across multiple domains

### Medical Research Framework
- **Best for**: Clinical research, systematic reviews, drug safety
- **Entity Types**: Disease, Treatment, Drug, Clinical_Trial, Patient_Population, etc.
- **Relationships**: TREATS, CAUSES, CONTRAINDICATES, TESTED_ON
- **Special Features**:
  - GRADE criteria for evidence evaluation
  - PICO-structured claim extraction
  - Level I-V evidence hierarchy
  - Source preferences: PubMed, Cochrane Library

### Legal Research Framework
- **Best for**: Case law research, statutory analysis, legal memoranda
- **Entity Types**: Case, Statute, Legal_Principle, Jurisdiction, Precedent, etc.
- **Relationships**: CITES, OVERRULES, DISTINGUISHES, APPLIES, INTERPRETS
- **Special Features**:
  - Binding vs. persuasive authority tracking
  - Jurisdictional hierarchy
  - Bluebook citation format
  - Source preferences: Westlaw, LexisNexis

### Scientific Research Framework
- **Best for**: Hypothesis testing, meta-analysis, replication studies
- **Entity Types**: Hypothesis, Experiment, Finding, Theory, Dataset, Protocol, etc.
- **Relationships**: REPLICATES, VALIDATES, FALSIFIES, SUPPORTS, REFUTES
- **Special Features**:
  - Pre-registration tracking
  - Reproducibility assessment
  - Open science principles
  - Source preferences: PubMed, arXiv, bioRxiv

## Creating a Custom Framework

### Method 1: Extend an Existing Framework (Easiest)

Create a YAML file in the project root or anywhere:

```yaml
# psychology_research.yaml
name: psychology_research
description: Framework for psychological research
version: 1.0.0
extends: scientific_research  # Inherit from scientific framework

# Add your custom entity types
entity_types:
  - Behavior
  - Cognitive_Process
  - Intervention
  - Participant_Group
  - Psychological_Measure

# Add your custom relationship types
relationship_types:
  - INFLUENCES
  - CORRELATES_WITH
  - MODERATES
  - MEDIATES
  - PREDICTS

# Optionally customize prompts
prompts:
  extraction: |
    Extract psychological claims focusing on:
    - Behavioral observations
    - Cognitive processes
    - Intervention effects

    Text: {text}
```

Then upload via Settings → Upload Custom, or:

```python
from backend.frameworks import load_framework

# Load and use your custom framework
framework = load_framework('/path/to/psychology_research.yaml')
```

### Method 2: Programmatic Creation

```python
from backend.frameworks import FrameworkManager

manager = FrameworkManager()

# Create custom framework
custom = manager.create_custom_framework(
    name='psychology_research',
    base_framework='scientific_research',
    custom_settings={
        'entity_types': [
            'Behavior',
            'Cognitive_Process',
            'Intervention'
        ],
        'relationship_types': [
            'INFLUENCES',
            'MODERATES',
            'MEDIATES'
        ]
    }
)

# Framework is automatically saved and ready to use
manager.set_framework('psychology_research')
```

### Method 3: Start from Scratch

Copy one of the built-in templates from `backend/frameworks/templates/` and modify it.

## Common Tasks

### View Framework Details

**Via Web UI:**
Settings → Select framework → Click "View Details"

**Via Python:**
```python
manager = FrameworkManager()
details = manager.get_framework_details('medical_research')
print(f"Entity types: {details['entity_types']}")
print(f"Relationships: {details['relationship_types']}")
```

### Check Compatibility

Before switching frameworks with existing data:

```python
manager = FrameworkManager()
result = manager.validate_framework_compatibility('medical_research')

if result['compatible']:
    print("Safe to switch!")
    manager.set_framework('medical_research')
else:
    print("Warnings:", result['warnings'])
    # Decide whether to proceed
```

### List All Frameworks

```python
manager = FrameworkManager()
frameworks = manager.list_available_frameworks()

for fw in frameworks:
    print(f"{fw['name']}: {fw['description']}")
```

## API Endpoints

If you're building on top of the Research Assistant:

- `GET /api/frameworks` - List all frameworks
- `GET /api/framework/current` - Get current framework
- `POST /api/framework/set` - Switch framework
- `GET /api/framework/{name}` - Get framework details
- `POST /api/framework/upload` - Upload custom framework
- `POST /api/framework/validate` - Check compatibility

## Best Practices

1. **Start with a built-in framework** - They're production-ready
2. **Extend rather than create from scratch** - Use `extends` to inherit
3. **Keep entity types focused** - 10-30 types is ideal
4. **Name consistently** - Entity types in PascalCase, relationships in UPPER_SNAKE_CASE
5. **Test compatibility** - Check before switching on production data

## Troubleshooting

### "Framework file not found"
- Check the framework name (no .yaml extension when using manager)
- Ensure file is in `backend/frameworks/templates/` or `custom_frameworks/`

### "Framework validation failed"
- Check YAML syntax (use a YAML validator)
- Ensure required fields are present (name, entity_types, relationship_types)
- Check version format (must be X.Y.Z)

### "Compatibility warnings"
- Your graph contains entity/relationship types not in the new framework
- Either: add those types to the framework, or accept the warning

## Next Steps

1. Try the built-in frameworks via Settings
2. Create a custom framework for your domain
3. Read the full documentation: `backend/frameworks/README.md`
4. Explore example frameworks in `backend/frameworks/templates/`

## Support

- Full documentation: `backend/frameworks/README.md`
- Implementation details: `FRAMEWORK_SYSTEM_IMPLEMENTATION.md`
- Example frameworks: `backend/frameworks/templates/`
