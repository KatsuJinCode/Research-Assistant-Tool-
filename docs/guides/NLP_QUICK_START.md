# Advanced NLP Quick Start Guide

## Overview

All 5 advanced NLP features are now implemented and ready to use:

1. ✅ **Claim Contradiction Detection** - Automatically detect contradicting claims
2. ✅ **Argument Mining** - Extract argument structures (premises, conclusions)
3. ✅ **Stance Detection** - Determine author stance (support/oppose/neutral)
4. ✅ **Automated Fact-Checking** - Verify factual claims with truth ratings
5. ✅ **Entity Extraction** - Extract named entities and their relationships

## Quick Usage

### Option 1: API Endpoints (Recommended)

Start the FastAPI server:

```bash
cd backend
uvicorn app.main:app --reload
```

Access documentation at: `http://localhost:8000/api/docs`

**Main Endpoint - Complete Analysis**:

```bash
POST http://localhost:8000/api/nlp/analyze-document
Content-Type: application/json

{
  "text": "Your document text here...",
  "doc_id": "doc_123"
}
```

This runs ALL NLP features on the document and adds results to the graph.

**Individual Feature Endpoints**:

```bash
# Contradiction Detection
POST /api/nlp/detect-contradictions
POST /api/nlp/detect-contradictions-batch

# Argument Mining
POST /api/nlp/mine-arguments
POST /api/nlp/mine-arguments-full

# Stance Detection
POST /api/nlp/detect-stance
POST /api/nlp/detect-stances-batch

# Fact-Checking
POST /api/nlp/fact-check
POST /api/nlp/fact-check-batch

# Entity Extraction
POST /api/nlp/extract-entities
POST /api/nlp/extract-entities-full

# Health Check
GET /api/nlp/health
```

### Option 2: Python Direct Usage

```python
import asyncio
from backend.nlp import (
    ContradictionDetector,
    ArgumentMiner,
    StanceDetector,
    FactChecker,
    EntityExtractor
)

async def main():
    # 1. Detect contradictions
    detector = ContradictionDetector()
    result = await detector.detect_contradiction(claim1, claim2)
    print(f"Contradiction: {result.is_contradiction}")

    # 2. Mine arguments
    miner = ArgumentMiner()
    arguments = await miner.extract_argument_structure(text)
    print(f"Found {len(arguments)} arguments")

    # 3. Detect stance
    stance_detector = StanceDetector()
    stance = await stance_detector.detect_stance(claim, document)
    print(f"Stance: {stance.stance.value}")

    # 4. Fact-check
    checker = FactChecker()
    fact_check = await checker.fact_check_claim(claim)
    print(f"Truth rating: {fact_check.truth_rating.value}")

    # 5. Extract entities
    extractor = EntityExtractor()
    entities = await extractor.extract_entities(text)
    print(f"Found {len(entities)} entities")

asyncio.run(main())
```

### Option 3: Run Examples

```bash
cd backend/nlp
python example_nlp_usage.py
```

This demonstrates all 5 features with realistic examples.

## UI Integration

### Add "🧠 NLP Analysis" Button

In your document viewer component:

```javascript
// React/Next.js example
const analyzeDocument = async (docId) => {
  const response = await fetch('/api/nlp/analyze-document', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: documentContent,
      doc_id: docId
    })
  });

  const result = await response.json();

  if (result.success) {
    // Show results
    showNotification(`Analysis complete! Found:
      - ${result.analysis.entities.count} entities
      - ${result.analysis.arguments.count} arguments
    `);

    // Refresh graph to show new nodes
    refreshGraph();
  }
};

// Button
<button onClick={() => analyzeDocument(doc.id)}>
  🧠 NLP Analysis
</button>
```

### Show NLP Results in Property Viewer

```javascript
// Contradiction indicator
{claim.contradictions?.length > 0 && (
  <Badge color="warning">
    ⚠️ Contradicts {claim.contradictions.length} claims
  </Badge>
)}

// Fact-check badge
{claim.fact_checked && (
  <Badge color={claim.fact_check_badge.color}>
    {claim.fact_check_badge.label}
  </Badge>
)}

// Stance indicator
{claim.stance && (
  <StanceIndicator
    stance={claim.stance}
    confidence={claim.stance_confidence}
  />
)}

// Entities mentioned
{claim.entities?.length > 0 && (
  <EntityList entities={claim.entities} />
)}
```

## Testing

Run comprehensive tests:

```bash
cd backend/nlp
pytest tests/test_nlp_integration.py -v -s
```

Or run specific test classes:

```bash
pytest tests/test_nlp_integration.py::TestContradictionDetector -v
pytest tests/test_nlp_integration.py::TestArgumentMiner -v
pytest tests/test_nlp_integration.py::TestStanceDetector -v
pytest tests/test_nlp_integration.py::TestFactChecker -v
pytest tests/test_nlp_integration.py::TestEntityExtractor -v
```

## Configuration

NLP modules use the existing AI client from `config/config.yaml`:

```yaml
ai_providers:
  default: anthropic  # or openai

  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-5-sonnet-20241022
    temperature: 0.5
    max_tokens: 4000
```

**No additional configuration needed!**

## Graph Database Integration

All features create nodes and relationships in the graph:

**New Node Types**:
- `Argument`, `Premise`, `Conclusion`
- `Entity`
- `FactCheck`, `FactCheckSource`

**New Relationship Types**:
- `CONTRADICTS` - Links contradicting claims
- `SUPPORTS`, `ATTACKS` - Argument relations
- `HAS_STANCE` - Document → Claim stance
- `HAS_FACT_CHECK` - Claim → FactCheck
- `MENTIONS` - Claim → Entity
- `WORKS_FOR`, `LOCATED_IN` - Entity relations

### Query Examples

```python
from research_agent.graph_database import GraphDatabase

graph = GraphDatabase()

# Get contradictions for a claim
contradictions = detector.get_contradictions_for_claim(
    graph, claim_id, min_confidence=70.0
)

# Get entity network
network = extractor.get_entity_network(
    graph, entity_id, max_depth=2
)

# Get all fact-checked claims
fact_checked = graph.find_nodes('Claim', {'fact_checked': True})
```

## File Structure

```
backend/nlp/
├── __init__.py                    # Exports all modules
├── base_nlp.py                    # Base class with AI client
├── contradiction_detector.py      # Feature 1 ✅
├── argument_miner.py              # Feature 2 ✅
├── stance_detector.py             # Feature 3 ✅
├── fact_checker.py                # Feature 4 ✅
├── entity_extractor.py            # Feature 5 ✅
├── example_nlp_usage.py           # Complete examples
├── README.md                      # Full documentation
└── tests/
    ├── __init__.py
    └── test_nlp_integration.py    # Comprehensive tests

backend/app/api/
└── nlp_routes.py                  # FastAPI endpoints ✅

backend/app/
└── main.py                        # Updated with NLP routes ✅
```

## API Response Examples

### Contradiction Detection

```json
{
  "success": true,
  "result": {
    "is_contradiction": true,
    "contradiction_type": "semantic",
    "confidence": 85.5,
    "explanation": "These claims present opposing views on...",
    "keywords": ["climate", "human", "natural"]
  }
}
```

### Argument Mining

```json
{
  "success": true,
  "count": 2,
  "arguments": [
    {
      "id": "arg_1",
      "scheme": "deductive",
      "confidence": 90.0,
      "premises": [
        {
          "text": "All models require data",
          "confidence": 95.0
        }
      ],
      "conclusion": {
        "text": "AI models need training data",
        "confidence": 90.0
      },
      "indicators": ["because", "therefore"]
    }
  ]
}
```

### Fact-Checking

```json
{
  "success": true,
  "result": {
    "claim_type": "factual",
    "is_checkable": true,
    "truth_rating": "mostly_true",
    "confidence": 82.0,
    "verification_summary": "The claim is largely supported by...",
    "sources": [
      {
        "name": "Wikipedia",
        "credibility": 85.0,
        "text": "According to the article..."
      }
    ],
    "badge": {
      "label": "MOSTLY TRUE",
      "color": "light-green",
      "icon": "check"
    }
  }
}
```

## Common Use Cases

### 1. Document Upload Pipeline

```python
async def process_uploaded_document(doc_id, text):
    # Run complete NLP analysis
    response = await client.post('/api/nlp/analyze-document', {
        'text': text,
        'doc_id': doc_id
    })

    # Results automatically added to graph
    return response.json()
```

### 2. Claim Verification

```python
async def verify_claim(claim):
    # Fact-check
    fact_check = await client.post('/api/nlp/fact-check', {
        'claim': claim
    })

    # Check for contradictions
    contradictions = await client.post('/api/nlp/detect-contradictions-batch', {
        'claims': [claim] + existing_claims
    })

    return {
        'fact_check': fact_check.json(),
        'contradictions': contradictions.json()
    }
```

### 3. Research Exploration

```python
async def explore_topic(document):
    # Extract entities
    entities = await client.post('/api/nlp/extract-entities-full', {
        'text': document.content,
        'doc_id': document.id
    })

    # Mine arguments
    arguments = await client.post('/api/nlp/mine-arguments-full', {
        'text': document.content,
        'doc_id': document.id
    })

    # Build knowledge graph
    return {
        'entities': entities.json(),
        'arguments': arguments.json()
    }
```

## Troubleshooting

### Issue: AI client initialization fails

**Solution**: Check that `config/config.yaml` has valid API keys:

```bash
# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
# or
export OPENAI_API_KEY="sk-..."
```

### Issue: Import errors

**Solution**: Ensure project root is in Python path:

```python
from pathlib import Path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

### Issue: Tests fail with timeout

**Solution**: Increase test timeout or use mock AI responses:

```python
@pytest.mark.timeout(60)  # 60 second timeout
async def test_slow_operation():
    ...
```

## Performance Tips

1. **Use Batch Operations**: Always prefer batch endpoints for multiple items
2. **Background Tasks**: API uses background tasks for graph updates
3. **Caching**: Consider caching results for expensive operations
4. **Similarity Filtering**: Contradiction detector skips dissimilar claim pairs
5. **Chunking**: Long texts are automatically chunked for processing

## Next Steps

1. ✅ All 5 features implemented
2. ✅ FastAPI endpoints created
3. ✅ Graph integration complete
4. ✅ Comprehensive tests added
5. ✅ Documentation written

**Ready to use!** Try the example script or start the API server.

## Support

- **Full Documentation**: `backend/nlp/README.md`
- **Examples**: `backend/nlp/example_nlp_usage.py`
- **Tests**: `backend/nlp/tests/test_nlp_integration.py`
- **API Docs**: `http://localhost:8000/api/docs` (when server is running)
