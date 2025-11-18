# Research Agents Integration Guide

This guide explains how the research agents functionality has been refactored into a standalone module and how to work with both systems.

## Overview

The research agents system has been extracted into a **standalone, reusable module** at `research-agents/`. This allows you to:

1. **Work on agents independently** without affecting document processing/graphing
2. **Develop in parallel** - changes to agents won't break other features
3. **Reuse agents** in other projects
4. **Test in isolation** - agents have their own test suite
5. **Merge cleanly** - well-defined interfaces prevent conflicts

## Architecture

```
Research-Assistant-Tool-/
├─ research-agents/                 # STANDALONE MODULE
│  ├─ src/research_agents/
│  │  ├─ agents/                   # Core agent logic
│  │  │  ├─ base_agent.py
│  │  │  ├─ support_agent.py
│  │  │  ├─ challenge_agent.py
│  │  │  └─ analysis_agent.py
│  │  └─ interfaces/               # Abstract interfaces
│  │     ├─ database_interface.py  # DB contract
│  │     ├─ ai_interface.py        # AI contract
│  │     └─ models.py              # Data models
│  ├─ tests/                       # Agent-specific tests
│  ├─ pyproject.toml               # Package config
│  └─ README.md                    # Module docs
│
├─ research_agent/                  # MAIN APPLICATION
│  ├─ adapters/                    # Connect module to app
│  │  ├─ database_adapter.py       # Implements DatabaseInterface
│  │  └─ ai_adapter.py             # Implements AIInterface
│  ├─ agents/                      # LEGACY (kept for now)
│  ├─ database.py                  # Existing DB
│  └─ utils/ai_client.py           # Existing AI client
│
└─ RESEARCH_AGENTS_INTEGRATION.md  # This file
```

## How It Works

### 1. The Standalone Module (`research-agents/`)

The `research-agents` module is **completely independent**:

- ✅ No imports from `research_agent` (main app)
- ✅ Uses abstract interfaces for DB and AI
- ✅ Can be installed as a package: `pip install -e research-agents/`
- ✅ Can be used in any Python project
- ✅ Has its own tests, docs, and versioning

**Key principle**: The module defines **what it needs** (interfaces), not **how it's implemented**.

### 2. The Adapters (`research_agent/adapters/`)

Adapters **implement** the interfaces using your existing infrastructure:

- `DatabaseAdapter`: Translates between module's `DatabaseInterface` and your PostgreSQL
- `AIAdapter`: Translates between module's `AIInterface` and your `AIClient`

**Key principle**: Adapters are the **glue code** that connects the module to your app.

### 3. Integration Flow

```
Your App Code
    ↓
Creates DatabaseAdapter(existing_db)
Creates AIAdapter(existing_ai_client)
    ↓
Passes adapters to agents
    ↓
Agents use interfaces (don't know about your DB/AI)
    ↓
Adapters translate to your actual DB/AI
```

## Working with the Modular System

### Scenario 1: Working on Document Processing/Graphing

**You can completely ignore the agents module!**

```python
# Work on document extraction, claim processing, graphing, etc.
# The agents module is separate and won't interfere

from research_agent.pdf_extractor import PDFExtractor
from research_agent.claim_extractor import ClaimExtractor
from research_agent.graph_database import GraphDatabase

# Do your work...
```

The agents will continue to work via the adapters.

### Scenario 2: Working on Research Agents

**Work directly in the `research-agents/` directory:**

```bash
cd research-agents/

# Install in development mode
pip install -e .

# Run agent-specific tests
pytest tests/

# Make changes to agents
vim src/research_agents/agents/support_agent.py
```

**Benefits:**
- Changes are isolated from main app
- Can test agents independently
- Can mock the database/AI interfaces
- Faster development cycle

### Scenario 3: Testing Integration

**Use the adapters to connect everything:**

```python
import asyncio
from research_agent.database import Database
from research_agent.utils.ai_client import AIClient
from research_agent.adapters import DatabaseAdapter, AIAdapter

# Import from standalone module
from research_agents import SupportAgent, ChallengeAgent, AgentConfig

async def main():
    # Create your existing infrastructure
    db = Database()
    await db.connect()
    ai_client = AIClient()

    # Create adapters
    db_adapter = DatabaseAdapter(db)
    ai_adapter = AIAdapter(ai_client)

    # Create agents using adapters
    config = AgentConfig(
        agent_type="support",
        poll_interval_seconds=30,
    )
    support_agent = SupportAgent(db_adapter, ai_adapter, config)
    challenge_agent = ChallengeAgent(db_adapter, ai_adapter, config)

    # Start agents
    await asyncio.gather(
        support_agent.start(),
        challenge_agent.start(),
    )

asyncio.run(main())
```

## Development Workflows

### Workflow 1: Feature Development (Agents)

**You want to add a new agent type or improve existing agents:**

1. **Work in isolation:**
   ```bash
   cd research-agents/
   ```

2. **Make changes to agents:**
   ```python
   # research-agents/src/research_agents/agents/new_agent.py
   class CitationAgent(BaseAgent):
       async def investigate(self, claim: Claim) -> Finding:
           # New agent logic...
           pass
   ```

3. **Test with mocked interfaces:**
   ```python
   # research-agents/tests/test_citation_agent.py
   from unittest.mock import AsyncMock

   class MockDatabase(DatabaseInterface):
       async def get_next_investigation(self, framework, agent_id):
           return mock_investigation

   async def test_citation_agent():
       db = MockDatabase()
       ai = MockAI()
       agent = CitationAgent(db, ai)
       # Test...
   ```

4. **When ready, integrate:**
   ```python
   # research_agent/main.py (or wherever)
   from research_agents import CitationAgent
   from research_agent.adapters import DatabaseAdapter, AIAdapter

   citation_agent = CitationAgent(db_adapter, ai_adapter)
   await citation_agent.start()
   ```

### Workflow 2: Feature Development (Main App)

**You want to improve document extraction or graphing:**

1. **Work in main app as usual:**
   ```bash
   # Work in research_agent/ directory
   vim research_agent/pdf_extractor.py
   ```

2. **Agents continue to work:**
   - Agents are already running (via orchestrator)
   - They use adapters, which use your DB
   - No code changes needed in agents

3. **If you change DB schema:**
   ```python
   # Update the adapter to match new schema
   # research_agent/adapters/database_adapter.py

   async def save_finding(self, investigation_id, finding):
       # Update SQL to match new schema
       await self.db.execute("""
           INSERT INTO findings (new_column, ...)
           VALUES ($1, ...)
       """, ...)
   ```

### Workflow 3: Parallel Development

**Two developers working simultaneously:**

**Developer A** (working on agents):
```bash
# Clone repo
git checkout -b feature/improve-support-agent

# Work in agents module
cd research-agents/
vim src/research_agents/agents/support_agent.py

# Test in isolation
pytest tests/test_support_agent.py

# Commit and push
git commit -m "Improve support agent evidence ranking"
git push
```

**Developer B** (working on document processing):
```bash
# Clone repo
git checkout -b feature/improve-pdf-extraction

# Work in main app
vim research_agent/pdf_extractor.py

# Test main app
python test_pdf_extraction.py

# Commit and push
git commit -m "Improve PDF column detection"
git push
```

**Both can merge cleanly** because they're working on separate modules!

## Interface Contracts

The interfaces define the **contract** between the module and your app. As long as the adapters implement these correctly, everything works.

### DatabaseInterface Contract

The module expects these methods to be implemented:

```python
class DatabaseInterface(ABC):
    @abstractmethod
    async def get_next_investigation(framework: str, agent_id: UUID) -> Investigation

    @abstractmethod
    async def save_finding(investigation_id: UUID, finding: Finding) -> UUID

    # ... etc (see research-agents/src/research_agents/interfaces/database_interface.py)
```

**Your job** (via adapters): Implement these using your PostgreSQL database.

### AIInterface Contract

The module expects these methods:

```python
class AIInterface(ABC):
    @abstractmethod
    async def generate(prompt: str, temperature: float, ...) -> str

    @abstractmethod
    async def generate_with_schema(prompt: str, schema: Dict) -> Dict

    # ... etc (see research-agents/src/research_agents/interfaces/ai_interface.py)
```

**Your job** (via adapters): Implement these using your AIClient (OpenAI/Anthropic).

## Migration Path

### Current State

- ✅ Standalone `research-agents/` module created
- ✅ Adapters created in `research_agent/adapters/`
- ⚠️ Old agent code still exists in `research_agent/agents/` (for backward compatibility)

### Next Steps

1. **Update orchestrator to use new module:**
   ```python
   # research_agent/investigation/orchestrator.py

   # OLD:
   from research_agent.agents.support_agent import SupportAgent

   # NEW:
   from research_agents import SupportAgent
   from research_agent.adapters import DatabaseAdapter, AIAdapter
   ```

2. **Test thoroughly:**
   ```bash
   python test_full_pipeline.py
   ```

3. **Once working, remove old agent code:**
   ```bash
   # After everything works
   rm -rf research_agent/agents/
   ```

## Benefits Summary

### ✅ Separation of Concerns
- Agents don't know about your database schema
- Document processing doesn't know about agents
- Clean boundaries

### ✅ Parallel Development
- Multiple developers can work simultaneously
- Fewer merge conflicts
- Faster iteration

### ✅ Testability
- Agents can be tested with mocked interfaces
- No need for full database setup
- Faster tests

### ✅ Reusability
- Agents module can be used in other projects
- Can be open-sourced separately
- Install via pip

### ✅ Flexibility
- Easy to swap database (PostgreSQL → SQLite → MongoDB)
- Easy to swap AI provider (OpenAI → Anthropic → Local)
- Just change the adapter

## Troubleshooting

### Issue: Import errors

```python
# Make sure research-agents is installed
cd research-agents/
pip install -e .

# Then you can import:
from research_agents import SupportAgent
```

### Issue: Interface not implemented

```
TypeError: Can't instantiate abstract class DatabaseAdapter with abstract methods get_next_investigation
```

**Solution:** Implement all methods from the interface in your adapter.

### Issue: Agents not finding work

Check that your `DatabaseAdapter.get_next_investigation()` is correctly querying your database:

```python
# Add logging
async def get_next_investigation(self, framework, agent_id):
    logger.info(f"Querying for {framework} investigations")
    row = await self.db.fetchrow(...)
    logger.info(f"Found: {row}")
    # ...
```

## Example: Complete Integration

See `examples/integrated_agent_system.py` for a complete working example of:
- Setting up adapters
- Starting agents
- Queuing investigations
- Monitoring progress

## Questions?

- **Module design**: See `research-agents/README.md`
- **Interface details**: See `research-agents/src/research_agents/interfaces/`
- **Adapter implementation**: See `research_agent/adapters/`
- **Integration examples**: See `examples/`
