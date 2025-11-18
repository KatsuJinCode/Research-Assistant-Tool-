# Research Agents

A standalone Python module for autonomous research agents that investigate claims and gather evidence.

## Overview

This module provides a decoupled, interface-based research agent system that can be integrated into any application needing autonomous background research capabilities.

### Key Features

- **Autonomous Pull-Based Architecture**: Agents continuously poll for work from a queue
- **Multiple Agent Types**: Support, Challenge, and Analysis agents for comprehensive claim investigation
- **Interface-Driven Design**: Abstract interfaces allow integration with any database or AI provider
- **Asynchronous**: Built with async/await for high concurrency
- **Type-Safe**: Full Pydantic models and type hints

## Architecture

```
┌─────────────────────────────────────────┐
│     Your Application                    │
│  ├─ Database Implementation             │
│  ├─ AI Provider Implementation          │
│  └─ Investigation Queue                 │
└─────────────────────────────────────────┘
            ▼ (via interfaces)
┌─────────────────────────────────────────┐
│     Research Agents Module              │
│  ├─ BaseAgent (pull-based processor)    │
│  ├─ SupportAgent (finds supporting)     │
│  ├─ ChallengeAgent (finds contradicting)│
│  └─ AnalysisAgent (clarifies terms)     │
└─────────────────────────────────────────┘
```

## Installation

### From source (development)

```bash
cd research-agents
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

### As a package (future)

```bash
pip install research-agents
```

## Quick Start

### 1. Implement the Interfaces

The module requires two interfaces to be implemented:

```python
from research_agents import DatabaseInterface, AIInterface

class MyDatabaseAdapter(DatabaseInterface):
    async def get_next_investigation(self, framework: str, agent_id: UUID) -> Investigation:
        # Your database logic here
        pass

    async def save_finding(self, investigation_id: UUID, finding: Finding) -> UUID:
        # Your database logic here
        pass

    # ... implement other methods

class MyAIAdapter(AIInterface):
    async def generate(self, prompt: str, temperature: float, **kwargs) -> str:
        # Your AI provider logic here (OpenAI, Anthropic, etc.)
        pass

    # ... implement other methods
```

### 2. Create and Start Agents

```python
import asyncio
from research_agents import SupportAgent, ChallengeAgent, AnalysisAgent
from research_agents import AgentConfig

# Create your adapter instances
db = MyDatabaseAdapter()
ai = MyAIAdapter()

# Configure agents
config = AgentConfig(
    agent_type="support",
    max_concurrent_investigations=5,
    poll_interval_seconds=30,
)

# Create agents
support_agent = SupportAgent(db, ai, config)
challenge_agent = ChallengeAgent(db, ai, config)
analysis_agent = AnalysisAgent(db, ai, config)

# Start agents (they will run forever, polling for work)
async def main():
    await asyncio.gather(
        support_agent.start(),
        challenge_agent.start(),
        analysis_agent.start(),
    )

asyncio.run(main())
```

### 3. Queue Investigations

Your application creates investigations in the database:

```python
# In your application code
investigation = Investigation(
    id=uuid4(),
    claim_id=claim_id,
    framework=InvestigationFramework.SUPPORT,
    status=InvestigationStatus.QUEUED,
    priority=0.8,
    created_at=datetime.utcnow(),
)

# Save to database
await db.create_investigation(investigation)

# Agents will automatically pick it up and process it
```

## Agent Types

### SupportAgent

Finds evidence that **supports** the claim.

- Searches for empirical evidence backing the claim
- Calculates positive confidence impact
- Returns 3-5 supporting sources with citations

### ChallengeAgent

Finds evidence that **challenges** the claim.

- Searches for contradicting evidence
- Looks for counter-examples and critiques
- Calculates negative confidence impact
- Returns 3-5 challenging sources with citations

### AnalysisAgent

Analyzes and **clarifies** key terms.

- Identifies ambiguous terms
- Provides definitions
- Analyzes scope and assumptions
- Minimal confidence impact (clarification only)

## Data Models

All data is modeled with Pydantic for type safety:

```python
from research_agents import (
    Claim,
    Investigation,
    Finding,
    Evidence,
    InvestigationStatus,
    InvestigationFramework,
)

# Example Claim
claim = Claim(
    id=uuid4(),
    text="Coffee consumption reduces risk of type 2 diabetes",
    confidence=0.5,
    qualifiers=["may", "moderate consumption"],
    context="Meta-analysis of cohort studies",
    created_at=datetime.utcnow(),
)

# Example Finding
finding = Finding(
    investigation_id=investigation_id,
    summary="Found 5 sources supporting this claim",
    confidence_impact=0.3,  # Increases claim confidence
    evidence_list=[evidence1, evidence2, ...],
    reasoning="Multiple large cohort studies show...",
)
```

## Interface Reference

### DatabaseInterface

Required methods:

- `get_next_investigation(framework, agent_id)` - Pull work from queue
- `claim_investigation(investigation_id, agent_id)` - Claim work
- `get_claim(claim_id)` - Load claim data
- `save_finding(investigation_id, finding)` - Save results
- `save_evidence(finding_id, evidence)` - Save evidence
- `update_investigation_status(investigation_id, status)` - Update status
- `mark_investigation_complete(investigation_id, duration)` - Complete work
- `update_claim_confidence(claim_id, confidence_delta)` - Update confidence
- `register_agent(agent_type, config)` - Register agent
- `update_agent_heartbeat(agent_id, status)` - Heartbeat
- `get_queue_status()` - Queue metrics
- `clear_stale_investigations(timeout)` - Clear stale work

### AIInterface

Required methods:

- `generate(prompt, temperature, max_tokens, response_format)` - Generate text
- `generate_with_schema(prompt, schema, temperature)` - Structured output
- `generate_batch(prompts, temperature, max_tokens)` - Batch generation
- `get_model_info()` - Model metadata

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Integration Examples

See the `examples/` directory for complete integration examples:

- PostgreSQL + OpenAI
- SQLite + Anthropic
- Custom implementations

## Roadmap

- [ ] Real research API integration (arXiv, Semantic Scholar, PubMed)
- [ ] Caching layer for evidence
- [ ] Rate limiting and backoff strategies
- [ ] Metrics and observability
- [ ] Agent orchestration tools
- [ ] Web UI for monitoring

## License

MIT

## Contributing

Contributions welcome! Please read CONTRIBUTING.md first.
