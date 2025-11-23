# Advanced NLP Capabilities

Complete implementation of 5 advanced NLP features for the Research Assistant Tool.

## Features

### 1. Claim Contradiction Detection

**Module**: `contradiction_detector.py`

Automatically detects contradicting claims in the knowledge graph using AI analysis.

**Features**:
- Pairwise claim comparison with similarity filtering
- AI-powered contradiction analysis
- Confidence scoring (0-100%)
- Category classification (direct, implicit, semantic)
- Creates bidirectional CONTRADICTS relationships in graph
- UI indicator support for contradicting claims

**Algorithm**:
```python
For each claim pair:
  1. Check textual similarity (ignore if too dissimilar < 15%)
  2. Use AI to analyze: "Do these claims contradict?"
  3. Parse response for contradiction type and confidence
  4. If confidence > 70%, create CONTRADICTS relationship
```

**Usage**:
```python
from backend.nlp import ContradictionDetector

detector = ContradictionDetector()

# Single pair
result = await detector.detect_contradiction(claim1, claim2)
print(f"Contradiction: {result.is_contradiction}")
print(f"Type: {result.contradiction_type.value}")
print(f"Confidence: {result.confidence}%")

# Batch detection
results = await detector.detect_contradictions_batch(claims, min_confidence=70.0)
await detector.create_contradiction_relationships(graph_db, results)
```

**API Endpoint**: `POST /api/nlp/detect-contradictions`

---

### 2. Argument Mining and Structure Extraction

**Module**: `argument_miner.py`

Extracts argument structures from documents including premises, conclusions, and relationships.

**Features**:
- Identifies premises and conclusions
- Extracts support/attack relationships between arguments
- Builds argument graphs
- Classifies argument schemes (deductive, inductive, abductive, causal, analogy, authority)
- Extracts argumentation indicators (keywords like "therefore", "because")

**Node Types Created**:
- `Argument`: Main argument node
- `Premise`: Premise statements
- `Conclusion`: Conclusion statements

**Relationship Types**:
- `SUPPORTS`: Premise supports argument
- `ATTACKS`: Argument attacks another
- `REBUTS`: Rebuts the conclusion
- `UNDERCUTS`: Undercuts the inference

**Usage**:
```python
from backend.nlp import ArgumentMiner

miner = ArgumentMiner()

# Extract arguments
arguments = await miner.extract_argument_structure(text, doc_id)

# Detect relations
relations = await miner.detect_argument_relations(arguments)

# Create graph
stats = await miner.create_argument_graph(graph_db, arguments, relations)
```

**API Endpoint**: `POST /api/nlp/mine-arguments`

---

### 3. Stance Detection

**Module**: `stance_detector.py`

Determines author stance toward claims (support, oppose, neutral, unclear).

**Features**:
- Classifies stance: Support, Oppose, Neutral, Unclear
- Confidence score (0-100%)
- Extracts supporting quotes from text
- Tracks stance shifts across documents
- Visualizes stance distribution
- Adds `stance` property to claim nodes

**Usage**:
```python
from backend.nlp import StanceDetector

detector = StanceDetector()

# Single document
result = await detector.detect_stance(claim, document, context)
print(f"Stance: {result.stance.value}")
print(f"Quotes: {result.supporting_quotes}")

# Multiple documents
results = await detector.detect_stances_batch(claim, documents)
distribution = detector.get_stance_distribution(results)

# Detect shifts
shifts = await detector.detect_stance_shifts(claim, documents)
```

**API Endpoint**: `POST /api/nlp/detect-stance`

---

### 4. Automated Fact-Checking

**Module**: `fact_checker.py`

Verifies factual claims automatically using AI analysis and external knowledge.

**Features**:
- Identifies checkable claims (factual vs opinion)
- Searches external knowledge bases (simulated - can integrate real APIs)
- Compares claim with verified sources
- Generates verification report
- Assigns truthfulness score (true, mostly true, false, etc.)
- Provides fact-check badges for UI

**Truth Ratings**:
- `TRUE`: Claim is true
- `MOSTLY_TRUE`: Claim is mostly true
- `HALF_TRUE`: Claim is half true
- `MOSTLY_FALSE`: Claim is mostly false
- `FALSE`: Claim is false
- `UNVERIFIABLE`: Cannot be verified
- `NEEDS_CONTEXT`: True but needs context

**Claim Types**:
- `FACTUAL`: Verifiable fact
- `OPINION`: Subjective opinion
- `PREDICTION`: Future prediction
- `DEFINITION`: Definition claim
- `MIXED`: Mix of factual and opinion

**Usage**:
```python
from backend.nlp import FactChecker

checker = FactChecker()

# Classify claim
claim_type, is_checkable, confidence = await checker.classify_claim_type(text)

# Full fact-check
result = await checker.fact_check_claim(claim)
print(f"Truth rating: {result.truth_rating.value}")
print(f"Sources: {len(result.sources)}")
print(f"Summary: {result.verification_summary}")

# Get UI badge
badge = checker.get_fact_check_badge(result.truth_rating)
```

**API Endpoint**: `POST /api/nlp/fact-check`

**Possible Integrations**:
- Google Fact Check Tools API
- Full Fact API
- PolitiFact API
- Wikipedia API
- Academic databases (PubMed, Google Scholar)

---

### 5. Entity and Relation Extraction

**Module**: `entity_extractor.py`

Extracts named entities and relationships from text.

**Features**:
- Named Entity Recognition (Person, Organization, Location, Date, Event, Concept, Quantity, Product)
- Relationship extraction (works_for, located_in, participated_in, etc.)
- Entity linking (placeholder for knowledge base linking)
- Creates entity nodes in graph
- Links entities to claims automatically

**Entity Types**:
- `PERSON`: Named persons
- `ORGANIZATION`: Companies, institutions
- `LOCATION`: Places, countries, cities
- `DATE`: Dates and time periods
- `EVENT`: Named events
- `CONCEPT`: Key concepts and theories
- `QUANTITY`: Numbers and measurements
- `PRODUCT`: Products and technologies

**Relation Types**:
- `WORKS_FOR`: Person works for Organization
- `LOCATED_IN`: Entity located in Location
- `PARTICIPATED_IN`: Entity participated in Event
- `CAUSED_BY`: Event caused by Entity
- `PART_OF`: Entity is part of another
- `ASSOCIATED_WITH`: Generic association
- `RELATED_TO`: Generic relation

**Usage**:
```python
from backend.nlp import EntityExtractor

extractor = EntityExtractor()

# Extract entities
entities = await extractor.extract_entities(text, doc_id)

# Extract relations
relations = await extractor.extract_relations(text, entities)

# Full extraction
result = await extractor.extract_entities_and_relations(text, doc_id)

# Create graph
stats = extractor.create_entity_graph(graph_db, result)

# Get entity network
network = extractor.get_entity_network(graph_db, entity_id, max_depth=2)
```

**API Endpoint**: `POST /api/nlp/extract-entities`

---

## Installation

All NLP modules use the existing AI client adapter and work with both OpenAI and Anthropic providers.

**No additional dependencies required** - uses existing `research_agent.utils.ai_client`.

## Configuration

NLP modules automatically use the AI provider configured in `config/config.yaml`:

```yaml
ai_providers:
  default: anthropic  # or openai

  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-5-sonnet-20241022
    temperature: 0.5
    max_tokens: 4000
```

## API Integration

### Include in FastAPI App

The NLP routes are automatically included in `backend/app/main.py`:

```python
from app.api.nlp_routes import router as nlp_router
app.include_router(nlp_router)
```

### Available Endpoints

```
POST /api/nlp/detect-contradictions         # Single pair
POST /api/nlp/detect-contradictions-batch   # Batch detection
POST /api/nlp/mine-arguments                # Extract arguments
POST /api/nlp/mine-arguments-full           # Full argument analysis
POST /api/nlp/detect-stance                 # Single stance
POST /api/nlp/detect-stances-batch          # Batch stance
POST /api/nlp/fact-check                    # Single fact-check
POST /api/nlp/fact-check-batch              # Batch fact-check
POST /api/nlp/extract-entities              # Extract entities only
POST /api/nlp/extract-entities-full         # Full entity + relations
POST /api/nlp/analyze-document              # Complete analysis
GET  /api/nlp/health                        # Health check
```

### Complete Document Analysis

The main endpoint for the "🧠 NLP Analysis" button:

```javascript
POST /api/nlp/analyze-document
{
  "text": "document content...",
  "doc_id": "doc_123"
}

// Response:
{
  "success": true,
  "doc_id": "doc_123",
  "analysis": {
    "entities": {
      "count": 15,
      "types": ["person", "organization", "location"]
    },
    "relations": {
      "count": 8
    },
    "arguments": {
      "count": 3,
      "schemes": ["deductive", "inductive"]
    }
  },
  "message": "NLP analysis completed. Results added to graph."
}
```

## Graph Integration

All NLP modules create nodes and relationships in the graph:

**New Node Types**:
- `Argument`, `Premise`, `Conclusion`
- `Entity`
- `FactCheck`, `FactCheckSource`

**New Relationship Types**:
- `CONTRADICTS`
- `SUPPORTS`, `ATTACKS`, `REBUTS`, `UNDERCUTS`
- `HAS_STANCE`
- `HAS_FACT_CHECK`, `USES_SOURCE`
- `MENTIONS`, `CONTAINS_ENTITY`
- `WORKS_FOR`, `LOCATED_IN`, `PARTICIPATED_IN`, etc.

## UI Integration

### Property Viewer Enhancements

Show NLP results in claim/document property viewers:

```javascript
// Contradiction indicator
if (claim.contradicts) {
  showBadge("⚠️ Contradicts other claims", "warning");
}

// Fact-check badge
if (claim.fact_checked) {
  const badge = claim.fact_check_badge;  // From API
  showBadge(badge.label, badge.color, badge.icon);
}

// Stance indicator
if (claim.stance) {
  showStance(claim.stance, claim.stance_confidence);
}
```

### NLP Analysis Button

Add to document viewer:

```javascript
<button onClick={() => runNLPAnalysis(documentId)}>
  🧠 NLP Analysis
</button>

async function runNLPAnalysis(docId) {
  const response = await fetch('/api/nlp/analyze-document', {
    method: 'POST',
    body: JSON.stringify({
      text: documentContent,
      doc_id: docId
    })
  });

  const result = await response.json();
  showNotification(result.message);
  refreshGraph();  // Reload graph with new nodes
}
```

## Testing

Run comprehensive tests:

```bash
cd backend/nlp
pytest tests/test_nlp_integration.py -v
```

Tests cover:
- All 5 NLP features
- Graph integration
- API endpoints
- Error handling
- Edge cases

## Examples

Run the example script to see all features in action:

```bash
cd backend/nlp
python example_nlp_usage.py
```

This demonstrates:
1. Contradiction detection between claims
2. Argument extraction from text
3. Stance detection across documents
4. Automated fact-checking
5. Entity and relation extraction
6. Complete NLP analysis with graph creation

## Performance Considerations

### Batch Processing

All modules support batch processing to minimize API calls:

```python
# Instead of this:
for claim in claims:
    result = await detector.detect_contradiction(claim, other_claim)

# Do this:
results = await detector.detect_contradictions_batch(claims)
```

### Background Tasks

API endpoints use FastAPI background tasks for graph operations:

```python
@router.post("/analyze")
async def analyze(request, background_tasks: BackgroundTasks):
    # Fast analysis
    result = await analyzer.analyze(request.text)

    # Slow graph update (background)
    background_tasks.add_task(create_graph, result)

    return result  # Return immediately
```

### Caching

Consider caching results for expensive operations:

```python
# Cache fact-check results
@lru_cache(maxsize=1000)
async def fact_check_cached(claim_text: str):
    return await fact_checker.fact_check_claim(claim_text)
```

## Future Enhancements

### Possible Additions

1. **Real External APIs**:
   - Integrate actual fact-checking APIs
   - Connect to Wikipedia, Wikidata
   - Use academic databases (PubMed, arXiv)

2. **Advanced NER**:
   - Add spaCy or transformers for better entity extraction
   - Support custom entity types
   - Entity linking to knowledge bases

3. **Argument Visualization**:
   - Create argument maps
   - Toulmin diagram generation
   - Interactive argument explorer

4. **Temporal Analysis**:
   - Track claim evolution over time
   - Detect emerging contradictions
   - Stance trajectory visualization

5. **Multi-language Support**:
   - Translate claims for comparison
   - Cross-lingual entity linking
   - Multilingual fact-checking

## Architecture

```
backend/nlp/
├── __init__.py                 # Package exports
├── base_nlp.py                 # Base processor with AI client
├── contradiction_detector.py   # Feature 1
├── argument_miner.py           # Feature 2
├── stance_detector.py          # Feature 3
├── fact_checker.py             # Feature 4
├── entity_extractor.py         # Feature 5
├── example_nlp_usage.py        # Examples
├── README.md                   # This file
└── tests/
    ├── __init__.py
    └── test_nlp_integration.py # Comprehensive tests
```

## License

Part of the Research Assistant Tool project.

## Support

For issues or questions:
1. Check the example script
2. Review the tests
3. Check API documentation at `/api/docs`
