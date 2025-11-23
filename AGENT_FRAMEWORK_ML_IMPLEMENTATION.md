# Custom Agent Framework and Machine Learning Features

**Complete Implementation Guide**

## Overview

This document describes the implementation of 8 advanced features for the Research Assistant Tool:

**PART 1: Custom Agent Framework (4 features)**
1. Agent Template System
2. Plugin System for User-Defined Agents
3. Visual Agent Builder (No-Code)
4. Agent Testing Framework

**PART 2: Machine Learning Features (4 features)**
5. Automatic Claim Classification
6. Investigation Value Prediction
7. Anomaly Detection for Claims
8. Trend Analysis for Emerging Topics

---

## PART 1: Custom Agent Framework

### 1. Agent Template System

**Location**: `C:\Users\jpswi\Research-Assistant-Tool-\backend\agents\agent_template.py`

**Features**:
- Base `AgentTemplate` class with standard interface
- Support for multiple execution types:
  - `ai_query`: AI-powered agents
  - `python_function`: Custom Python code
  - `chain`: Multi-step workflows
  - `conditional`: Conditional logic
- Input/output schema validation
- Configuration management
- YAML import/export

**Example Templates Included**:
1. **Document Summarizer**: Summarizes documents with configurable length
2. **Claim Extractor**: Extracts factual claims from text
3. **Evidence Finder**: Finds supporting/challenging evidence
4. **Contradiction Checker**: Checks if claims contradict
5. **Custom Research Agent**: Multi-step research workflow

**Usage**:
```python
from backend.agents import AgentTemplate, AgentExecutor

# Load template from YAML
template = AgentTemplate.from_yaml('templates/document_summarizer.yaml')

# Execute
executor = AgentExecutor(ai_client=your_ai_client)
executor.register_template(template)
result = executor.execute('document_summarizer', {'document_text': 'Your text here'})
```

**YAML Format**:
```yaml
name: document_summarizer
version: 1.0.0
description: Summarizes documents
inputs:
  - name: document_text
    type: string
    description: Text to summarize
outputs:
  - name: summary
    type: string
configuration:
  max_length: 500
  style: concise
  temperature: 0.3
execution:
  type: ai_query
  prompt: "Summarize: {{document_text}}"
```

---

### 2. Plugin System for User-Defined Agents

**Location**: `C:\Users\jpswi\Research-Assistant-Tool-\backend\agents\plugin_manager.py`

**Features**:
- Auto-discovery of plugins in `plugins/` directory
- Dynamic loading with error handling
- Plugin validation before execution
- Basic sandboxed execution
- Plugin metadata management

**Plugin Interface**:
```python
from backend.agents.plugin_manager import AgentPlugin

class MyCustomAgent(AgentPlugin):
    def validate(self) -> bool:
        return True

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # Your agent logic here
        return {'result': 'output'}

    def get_metadata(self) -> Dict[str, Any]:
        return {
            'name': 'my_custom_agent',
            'version': '1.0.0',
            'description': 'Does something useful',
            'author': 'Your Name',
            'inputs': [{'name': 'input1', 'type': 'string'}],
            'outputs': [{'name': 'result', 'type': 'string'}]
        }
```

**Usage**:
```python
from backend.agents import PluginManager

manager = PluginManager(plugins_dir='plugins')
manager.load_all_plugins()

# Execute plugin
result = manager.execute_plugin('my_custom_agent', {'input1': 'value'})
```

---

### 3. Visual Agent Builder

**Location**:
- `C:\Users\jpswi\Research-Assistant-Tool-\web_ui\static\js\agent-builder.js`
- `C:\Users\jpswi\Research-Assistant-Tool-\web_ui\static\css\agent-builder.css`
- `C:\Users\jpswi\Research-Assistant-Tool-\web_ui\templates\agent_builder.html`

**Features**:
- Drag-and-drop canvas interface
- Pre-built block palette:
  - **Input/Output**: Input, Output
  - **Processing**: AI Query, Function, Transform
  - **Control Flow**: Condition, Loop, Parallel
- Visual connection between blocks
- Property editor panel
- Test runner with JSON inputs
- Export to:
  - Python code (plugin format)
  - YAML template
  - JSON definition

**Access**:
Navigate to `/agent-builder` in the web UI or open `agent_builder.html` directly.

**Workflow**:
1. Drag blocks from palette to canvas
2. Connect blocks by clicking output → input points
3. Select block to edit properties
4. Test with sample inputs
5. Export as Python plugin or YAML template

---

### 4. Agent Testing Framework

**Location**: `C:\Users\jpswi\Research-Assistant-Tool-\backend\agents\agent_tester.py`

**Features**:
- Unit test generation
- Test suite management
- Performance benchmarking
- Output validation (expected values or custom functions)
- Test reports (JSON export)
- Test fixture generation

**Usage**:
```python
from backend.agents import AgentTester, TestCase, TestSuite

tester = AgentTester(agent_executor)

# Create test suite
suite = tester.create_test_suite(
    name="my_tests",
    description="Test suite for my agent"
)

# Add test cases
tester.add_test_case("my_tests", TestCase(
    name="test_basic",
    inputs={'text': 'test input'},
    expected_outputs={'summary': 'expected output'},
    description="Basic functionality test"
))

# Run tests
results = tester.run_test_suite("my_tests", "my_agent")

# Generate report
report = tester.generate_test_report("report.json")

# Benchmark
benchmark = tester.benchmark_agent("my_agent", {'text': 'test'}, iterations=100)
```

---

## PART 2: Machine Learning Features

### 5. Automatic Claim Classification

**Location**: `C:\Users\jpswi\Research-Assistant-Tool-\backend\ml\claim_classifier.py`

**Features**:
- Classifies claims into 5 categories:
  - **Factual**: Verifiable facts
  - **Opinion**: Subjective statements
  - **Hypothesis**: Scientific hypotheses
  - **Prediction**: Future predictions
  - **Definition**: Term definitions
- AI-based classification (when AI client provided)
- Rule-based fallback (pattern matching)
- Confidence scoring
- Batch classification
- Category distribution statistics

**Usage**:
```python
from backend.ml import ClaimClassifier

classifier = ClaimClassifier(ai_client=ai_client, use_ai=True)

# Classify single claim
result = await classifier.classify("Water boils at 100°C")
# result.category = ClaimCategory.FACTUAL
# result.confidence = 0.95

# Classify batch
claims = [
    {'id': '1', 'text': 'Water boils at 100°C'},
    {'id': '2', 'text': 'I think Python is best'}
]
results = await classifier.classify_batch(claims)

# Get statistics
distribution = classifier.get_category_distribution(results)
stats = classifier.get_confidence_stats(results)
```

**API Endpoint**: `POST /api/ml/classify-claims`

---

### 6. Investigation Value Prediction

**Location**: `C:\Users\jpswi\Research-Assistant-Tool-\backend\ml\value_predictor.py`

**Features**:
- Predicts investigation value (0-100 score)
- Based on 5 factors:
  - **Novelty**: How unique the claim is
  - **Evidence Gap**: Missing evidence
  - **Controversy**: Conflicting claims
  - **Recency**: How recent the topic is
  - **Impact**: Potential importance
- Weighted scoring (configurable weights)
- Priority recommendations (high/medium/low)
- Batch prediction
- Explanation generation

**Usage**:
```python
from backend.ml import InvestigationValuePredictor

predictor = InvestigationValuePredictor()

# Predict value
prediction = await predictor.predict(
    claim={'id': '1', 'text': 'Climate affects agriculture', 'created_at': '2024-01-01'},
    related_claims=[...],
    existing_evidence=[...]
)
# prediction.value_score = 85.0
# prediction.recommendation = 'high'
# prediction.factors = {'novelty': 90, 'evidence_gap': 80, ...}

# Batch prediction
predictions = await predictor.predict_batch(claims)

# Get priority queue
top_priority = predictor.get_priority_queue(predictions, limit=10)
```

**API Endpoint**: `POST /api/ml/predict-value`

---

### 7. Anomaly Detection for Claims

**Location**: `C:\Users\jpswi\Research-Assistant-Tool-\backend\ml\anomaly_detector.py`

**Features**:
- Detects 5 types of anomalies:
  - **Statistical**: Z-score outliers in metadata
  - **Semantic**: Claims distant from others
  - **Confidence**: Very high/low confidence
  - **Contradiction**: Contradicts known facts (AI-based)
  - **Pattern**: Unusual structural patterns
- Anomaly score (0-100)
- Severity levels (low/medium/high)
- Batch detection
- Detailed explanations
- Statistics and export

**Usage**:
```python
from backend.ml import AnomalyDetector

detector = AnomalyDetector(z_threshold=3.0, ai_client=ai_client)

# Detect anomalies
result = await detector.detect(
    claim={'id': '1', 'text': 'EARTH IS FLAT!!!'},
    all_claims=[...]
)
# result.anomaly_score = 85.0
# result.anomaly_types = ['pattern', 'contradiction']
# result.severity = 'high'

# Batch detection
results = await detector.detect_batch(claims)

# Get statistics
stats = detector.get_anomaly_statistics(results)
```

**API Endpoint**: `POST /api/ml/detect-anomalies`

---

### 8. Trend Analysis for Emerging Topics

**Location**: `C:\Users\jpswi\Research-Assistant-Tool-\backend\ml\trend_analyzer.py`

**Features**:
- Time-series analysis of topic frequency
- Identifies emerging vs declining topics
- Topic clustering (related topics grouped)
- Burst detection (sudden increases)
- Future trend predictions
- Visualization data generation
- Configurable time windows

**Usage**:
```python
from backend.ml import TrendAnalyzer

analyzer = TrendAnalyzer(time_window_days=90)

# Analyze trends
analysis = await analyzer.analyze_trends(
    claims=[...],
    start_date=datetime(2024, 1, 1),
    end_date=datetime.now()
)

# Results
print(analysis.emerging_topics)  # Top 10 emerging
print(analysis.declining_topics)  # Top 10 declining
print(analysis.topic_clusters)   # Clustered topics
print(analysis.predictions)      # Future predictions
print(analysis.visualization_data)  # For charts

# Get topic insights
insights = await analyzer.get_topic_insights('climate change', analysis)
```

**API Endpoint**: `POST /api/ml/analyze-trends`

---

## Backend API Routes

### Agent Framework Routes

**Base**: `/api/agents`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/templates` | List all agent templates |
| POST | `/create` | Create custom agent |
| POST | `/execute` | Execute agent with inputs |
| GET | `/plugins` | List all plugins |
| POST | `/plugins/reload` | Reload all plugins |
| POST | `/plugins/execute/{name}` | Execute plugin |
| POST | `/test` | Test agent |
| POST | `/test/suite/{suite}/{agent}` | Run test suite |
| GET | `/test/report` | Get test report |
| POST | `/upload-plugin` | Upload plugin file |

### Machine Learning Routes

**Base**: `/api/ml`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/classify-claims` | Classify claims into categories |
| POST | `/predict-value` | Predict investigation value |
| POST | `/detect-anomalies` | Detect anomalous claims |
| POST | `/analyze-trends` | Analyze topic trends |
| GET | `/analyze-trends/topic/{topic}` | Get topic insights |
| POST | `/export-results/{type}` | Export ML results |

---

## Web UI Integration

### Agent Builder UI

**URL**: `/agent-builder` or `web_ui/templates/agent_builder.html`

**Features**:
- Full visual editor
- Drag-and-drop block placement
- Canvas with grid
- Properties panel
- Test modal with JSON input
- Export options

### ML Analysis Dashboard

**URL**: `/ml-analysis` or `web_ui/templates/ml_analysis.html`

**Features**:
- 4 analysis cards (one for each ML feature)
- Real-time results display
- Statistics visualization
- Badge indicators for severity/priority
- Export functionality

---

## File Structure

```
Research-Assistant-Tool-/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── agent_template.py       # Template system
│   │   ├── plugin_manager.py       # Plugin system
│   │   └── agent_tester.py         # Testing framework
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── claim_classifier.py     # Classification
│   │   ├── value_predictor.py      # Value prediction
│   │   ├── anomaly_detector.py     # Anomaly detection
│   │   └── trend_analyzer.py       # Trend analysis
│   └── app/
│       └── api/
│           ├── agents_routes.py    # Agent API routes
│           └── ml_routes.py        # ML API routes
├── web_ui/
│   ├── static/
│   │   ├── js/
│   │   │   └── agent-builder.js   # Visual builder JS
│   │   └── css/
│   │       └── agent-builder.css  # Visual builder CSS
│   └── templates/
│       ├── agent_builder.html     # Agent builder page
│       └── ml_analysis.html       # ML analysis page
└── plugins/                       # User plugins directory
    └── (user-created plugins)
```

---

## Quick Start Examples

### Create a Custom Agent

```python
# Define agent
agent_def = {
    'name': 'my_summarizer',
    'version': '1.0.0',
    'description': 'My custom summarizer',
    'inputs': [{'name': 'text', 'type': 'string'}],
    'outputs': [{'name': 'summary', 'type': 'string'}],
    'execution': {
        'type': 'ai_query',
        'prompt': 'Summarize: {{text}}'
    },
    'configuration': {'temperature': 0.3}
}

# Create via API
response = requests.post('/api/agents/create', json={
    'agent_definition': agent_def,
    'save_as_template': True
})
```

### Run ML Analysis

```python
# Classify claims
response = requests.post('/api/ml/classify-claims', json={
    'claims': [
        {'id': '1', 'text': 'Water boils at 100°C'},
        {'id': '2', 'text': 'I think cats are cute'}
    ]
})

# Detect anomalies
response = requests.post('/api/ml/detect-anomalies', json={
    'claims': all_claims,
    'min_score': 70.0
})

# Analyze trends
response = requests.post('/api/ml/analyze-trends', json={
    'claims': all_claims,
    'time_window_days': 90
})
```

---

## Configuration

### AI Client Setup

All ML features support both AI-based and rule-based modes:

```python
# With AI (recommended)
from research_agent.utils.ai_client import AIClient

ai_client = AIClient(
    provider='anthropic',
    api_key='your-key',
    model='claude-3-5-sonnet-20241022'
)

classifier = ClaimClassifier(ai_client=ai_client, use_ai=True)

# Without AI (rule-based fallback)
classifier = ClaimClassifier(use_ai=False)
```

### Custom Weights for Value Prediction

```python
predictor = InvestigationValuePredictor(
    weights={
        'novelty': 0.30,
        'evidence_gap': 0.30,
        'controversy': 0.20,
        'recency': 0.10,
        'impact': 0.10
    }
)
```

### Anomaly Detection Thresholds

```python
detector = AnomalyDetector(
    z_threshold=3.0,           # Z-score threshold
    semantic_threshold=0.3,     # Semantic similarity threshold
    ai_client=ai_client
)
```

---

## Testing

### Agent Testing

```bash
# Run test suite
python -c "
from backend.agents import AgentTester
tester = AgentTester()
# ... create tests ...
results = tester.run_all_suites('my_agent')
print(tester.generate_test_report())
"
```

### ML Feature Testing

All ML features have example usage functions:

```python
# Test classification
import asyncio
from backend.ml.claim_classifier import example_classification
asyncio.run(example_classification())
```

---

## Performance Considerations

1. **Batch Processing**: All ML features support batch operations for efficiency
2. **Caching**: Consider caching AI responses for repeated queries
3. **Async Support**: All ML features use async for better performance
4. **Rule-based Fallback**: Graceful degradation when AI unavailable

---

## Future Enhancements

1. **Agent Framework**:
   - Visual workflow debugger
   - Agent marketplace
   - Version control for agents
   - A/B testing for agents

2. **Machine Learning**:
   - Fine-tuning on user data
   - Advanced embeddings for semantic analysis
   - Real-time streaming analysis
   - Integration with external knowledge bases

---

## Dependencies

Required Python packages:
```txt
# Existing
fastapi
pydantic
uvicorn

# New (optional, for enhanced features)
pyyaml           # For YAML template support
scikit-learn     # For advanced ML (optional)
```

---

## Troubleshooting

### Common Issues

1. **Plugin not loading**:
   - Check plugin inherits from `AgentPlugin`
   - Verify `validate()` returns True
   - Check plugin file is in `plugins/` directory

2. **ML analysis returns empty results**:
   - Ensure claims have `created_at` timestamps
   - Check minimum mentions threshold
   - Verify time window includes claim dates

3. **Visual builder blocks not connecting**:
   - Click output point first, then input point
   - Ensure blocks are compatible types

---

## Summary

All 8 features have been fully implemented:

✅ **Agent Template System**: Complete with 5 example templates
✅ **Plugin System**: Dynamic loading with validation
✅ **Visual Agent Builder**: Full drag-and-drop UI
✅ **Agent Testing Framework**: Tests, benchmarks, reports
✅ **Claim Classification**: 5 categories with confidence
✅ **Investigation Value**: 5-factor scoring system
✅ **Anomaly Detection**: 5 detection methods
✅ **Trend Analysis**: Time-series + clustering + predictions

All features include:
- Complete implementation code
- API routes
- Web UI integration
- Documentation
- Example usage

Ready for production use!
