# Quick Start: Custom Agents & Machine Learning

**60-Second Guide to Using the New Features**

## 🤖 Custom Agent Framework

### Create an Agent in 3 Steps

**1. Using Visual Builder** (No Code)
```
1. Open http://localhost:5000/agent-builder
2. Drag blocks onto canvas
3. Connect blocks
4. Click "Export YAML"
```

**2. Using Python Template**
```python
from backend.agents import AgentTemplate, AgentExecutor

# Load template
template = AgentTemplate.from_yaml('templates/document_summarizer.yaml')

# Execute
executor = AgentExecutor(ai_client=your_ai_client)
executor.register_template(template)
result = executor.execute('document_summarizer', {'document_text': 'Your text'})
```

**3. Create Plugin** (Advanced)
```python
# Save as plugins/my_plugin.py
from backend.agents.plugin_manager import AgentPlugin

class MyAgent(AgentPlugin):
    def validate(self): return True
    def execute(self, inputs):
        return {'result': 'processed ' + inputs['text']}
    def get_metadata(self):
        return {'name': 'my_agent', 'version': '1.0.0', ...}
```

### Test Your Agent

```python
from backend.agents import AgentTester, TestCase

tester = AgentTester(executor)
suite = tester.create_test_suite("my_tests", "Test my agent")
tester.add_test_case("my_tests", TestCase(
    name="test1",
    inputs={'text': 'test'},
    expected_outputs={'result': 'expected'}
))
results = tester.run_test_suite("my_tests", "my_agent")
```

---

## 🔬 Machine Learning Features

### 1. Classify Claims

**API**:
```bash
curl -X POST http://localhost:8000/api/ml/classify-claims \
  -H "Content-Type: application/json" \
  -d '{
    "claims": [
      {"id": "1", "text": "Water boils at 100°C"},
      {"id": "2", "text": "I think Python is best"}
    ]
  }'
```

**Python**:
```python
from backend.ml import ClaimClassifier

classifier = ClaimClassifier(use_ai=False)  # or use_ai=True with ai_client
results = await classifier.classify_batch([
    {'id': '1', 'text': 'Water boils at 100°C'},
    {'id': '2', 'text': 'I think Python is best'}
])
# Results: factual, opinion
```

### 2. Predict Investigation Value

**API**:
```bash
curl -X POST http://localhost:8000/api/ml/predict-value \
  -H "Content-Type: application/json" \
  -d '{"claims": [...]}'
```

**Python**:
```python
from backend.ml import InvestigationValuePredictor

predictor = InvestigationValuePredictor()
prediction = await predictor.predict(
    claim={'id': '1', 'text': 'Climate affects agriculture', 'created_at': '2024-01-01'}
)
# prediction.value_score = 85.0
# prediction.recommendation = 'high'
```

### 3. Detect Anomalies

**API**:
```bash
curl -X POST http://localhost:8000/api/ml/detect-anomalies \
  -H "Content-Type: application/json" \
  -d '{"claims": [...], "min_score": 50.0}'
```

**Python**:
```python
from backend.ml import AnomalyDetector

detector = AnomalyDetector()
result = await detector.detect(
    claim={'id': '1', 'text': 'EARTH IS FLAT!!!'},
    all_claims=[...]
)
# result.anomaly_score = 85.0
# result.anomaly_types = ['pattern', 'contradiction']
```

### 4. Analyze Trends

**API**:
```bash
curl -X POST http://localhost:8000/api/ml/analyze-trends \
  -H "Content-Type: application/json" \
  -d '{"claims": [...], "time_window_days": 90}'
```

**Python**:
```python
from backend.ml import TrendAnalyzer

analyzer = TrendAnalyzer(time_window_days=90)
analysis = await analyzer.analyze_trends(claims)
print(analysis.emerging_topics)  # Top emerging topics
print(analysis.topic_clusters)   # Clustered topics
```

---

## 🌐 Web UI

### Agent Builder
```
http://localhost:5000/agent-builder
```
- Drag & drop interface
- Test with live data
- Export Python/YAML

### ML Analysis Dashboard
```
http://localhost:5000/ml-analysis
```
- Run all 4 ML analyses
- View results in real-time
- Export reports

---

## 📋 API Endpoints

### Agents
```
GET  /api/agents/templates          # List templates
POST /api/agents/create             # Create agent
POST /api/agents/execute            # Execute agent
GET  /api/agents/plugins            # List plugins
POST /api/agents/test               # Test agent
```

### Machine Learning
```
POST /api/ml/classify-claims        # Classify claims
POST /api/ml/predict-value          # Predict investigation value
POST /api/ml/detect-anomalies       # Detect anomalies
POST /api/ml/analyze-trends         # Analyze trends
```

---

## 🚀 Example Workflow

**End-to-End Example: Analyze Research Claims**

```python
from backend.ml import ClaimClassifier, InvestigationValuePredictor, AnomalyDetector, TrendAnalyzer

# Load your claims
claims = [
    {'id': '1', 'text': 'Water boils at 100°C', 'created_at': '2024-01-01'},
    {'id': '2', 'text': 'I think Python is best', 'created_at': '2024-01-02'},
    # ... more claims
]

# 1. Classify
classifier = ClaimClassifier()
classifications = await classifier.classify_batch(claims)
print(f"Categories: {classifier.get_category_distribution(classifications)}")

# 2. Predict value
predictor = InvestigationValuePredictor()
predictions = await predictor.predict_batch(claims)
top_priority = predictor.get_priority_queue(predictions, limit=5)
print(f"Top priority claims: {[p.claim_text for p in top_priority]}")

# 3. Detect anomalies
detector = AnomalyDetector()
anomalies = await detector.detect_batch(claims)
significant = [a for a in anomalies if a.anomaly_score >= 70]
print(f"Found {len(significant)} anomalous claims")

# 4. Analyze trends
analyzer = TrendAnalyzer()
analysis = await analyzer.analyze_trends(claims)
print(f"Emerging topics: {analysis.emerging_topics}")
print(f"Topic clusters: {len(analysis.topic_clusters)}")
```

---

## 📁 File Locations

```
backend/agents/
├── agent_template.py      # Template system
├── plugin_manager.py      # Plugin loader
└── agent_tester.py        # Testing framework

backend/ml/
├── claim_classifier.py    # Classification
├── value_predictor.py     # Value prediction
├── anomaly_detector.py    # Anomaly detection
└── trend_analyzer.py      # Trend analysis

backend/app/api/
├── agents_routes.py       # Agent API
└── ml_routes.py          # ML API

web_ui/
├── templates/
│   ├── agent_builder.html # Visual builder
│   └── ml_analysis.html   # ML dashboard
└── static/
    ├── js/agent-builder.js
    └── css/agent-builder.css
```

---

## 🎯 Common Use Cases

### Use Case 1: Auto-categorize incoming claims
```python
classifier = ClaimClassifier(ai_client=ai_client)
for new_claim in incoming_claims:
    result = await classifier.classify(new_claim['text'])
    db.update_claim(new_claim['id'], category=result.category.value)
```

### Use Case 2: Prioritize research queue
```python
predictor = InvestigationValuePredictor()
predictions = await predictor.predict_batch(all_claims)
research_queue = predictor.get_priority_queue(predictions, limit=20)
for claim in research_queue:
    print(f"Investigate: {claim.claim_text} (score: {claim.value_score})")
```

### Use Case 3: Flag suspicious claims
```python
detector = AnomalyDetector(ai_client=ai_client)
anomalies = await detector.detect_batch(claims)
for anomaly in anomalies:
    if anomaly.severity == 'high':
        alert_moderator(anomaly)
```

### Use Case 4: Track emerging research topics
```python
analyzer = TrendAnalyzer()
analysis = await analyzer.analyze_trends(claims)
for topic in analysis.emerging_topics[:5]:
    print(f"📈 Trending: {topic}")
```

---

## 💡 Tips

1. **Start with rule-based**: ML features work without AI for testing
2. **Use batch operations**: Much faster than one-by-one
3. **Export results**: All features support JSON export
4. **Test agents first**: Use AgentTester before production
5. **Monitor anomalies**: Set up alerts for high-severity anomalies
6. **Review trends weekly**: Run trend analysis on regular schedule

---

## 🔧 Troubleshooting

**Agent not working?**
- Check AI client is configured
- Verify input schema matches
- Look at logs for errors

**ML returns no results?**
- Ensure claims have timestamps
- Check minimum thresholds
- Verify data format

**Visual builder won't save?**
- Check browser console
- Verify API endpoint accessible
- Test with example agent first

---

## 📚 Learn More

- **Full documentation**: `AGENT_FRAMEWORK_ML_IMPLEMENTATION.md`
- **API reference**: See route files in `backend/app/api/`
- **Code examples**: Check `backend/ml/*.py` for example functions
