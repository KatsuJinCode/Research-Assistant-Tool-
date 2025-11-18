# Research Assistant Tool: Complete Modularization Plan

**Status:** Planning Phase
**Goal:** Transform monolithic codebase into independent, parallel-developable modules
**Strategy:** Fork current project, refactor into modules, enable parallel agent development

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Architecture Problems](#current-architecture-problems)
3. [Target Modular Architecture](#target-modular-architecture)
4. [Module Specifications](#module-specifications)
5. [Dependency Graph](#dependency-graph)
6. [Migration Strategy](#migration-strategy)
7. [Parallel Development Plan](#parallel-development-plan)
8. [Testing Strategy](#testing-strategy)

---

## Executive Summary

### Current State
- **~50 Python files**, ~10,000 lines of code
- **3 separate applications** with no code sharing
- **Duplicate implementations** (AI clients, agents, config)
- **4 different databases** (SQLite, PostgreSQL, Neo4j, NetworkX)
- **Tightly coupled** business logic, data access, and presentation

### Target State
- **17 independent modules** organized in 5 tiers
- **Each module** is a standalone Python package
- **Clear interfaces** between modules
- **Parallel development** - different agents work on different modules
- **Independent deployment** - modules can be updated separately

### Benefits
✅ **Parallel Development** - 5+ agents working simultaneously
✅ **Independent Testing** - Test modules in isolation
✅ **Reusability** - Use modules in other projects
✅ **Clear Ownership** - Each module has clear responsibilities
✅ **Easier Onboarding** - New devs understand one module at a time
✅ **Microservices Ready** - Can deploy as separate services if needed

---

## Current Architecture Problems

### Problem 1: Three Separate Applications

```
┌────────────────────────────────┐
│  Legacy CLI (cli_assistant.py) │  ← SQLite, own AI helper
└────────────────────────────────┘

┌────────────────────────────────┐
│  Research Agent (research_agent/)│ ← PostgreSQL, asyncpg
└────────────────────────────────┘

┌────────────────────────────────┐
│  Graph UI (web_ui/)            │  ← Neo4j, Flask+Socket.IO
└────────────────────────────────┘

NO SHARED CODE, NO INTEGRATION, DUPLICATE FEATURES
```

### Problem 2: Duplicate Implementations

| Functionality | Implementation 1 | Implementation 2 |
|---------------|------------------|------------------|
| **AI Client** | `ai_helper.py` | `utils/ai_client.py` |
| **Agents** | `research_agent/agents/` | `research-agents/` |
| **Config** | `config.yaml` | `.research_config` |
| **Models** | `research_agent/models.py` | `research-agents/.../models.py` |

### Problem 3: Tight Coupling

**Example: web_ui/app.py (Flask routes)**
```python
@app.route('/api/upload', methods=['POST'])
def upload_document():
    # Business logic directly in route
    extractor = PDFExtractor()  # Direct instantiation
    graph_db = Neo4jDatabase()  # Direct instantiation
    claims = await claim_extractor.extract(...)  # No service layer
    # ...
```

**Should be:**
```python
@app.route('/api/upload', methods=['POST'])
def upload_document():
    # Thin controller
    result = await document_service.process_upload(file)
    return jsonify(result)
```

### Problem 4: Database Fragmentation

```
SQLite (legacy) ───┐
                   │
PostgreSQL (main) ─┤  All store similar data
                   │  No migration path
Neo4j (graph) ─────┤
                   │
NetworkX (memory) ─┘
```

---

## Target Modular Architecture

### Module Organization: 5 Tiers

```
┌─────────────────────────────────────────────────────────────┐
│ TIER 5: Standalone Modules (Publishable to PyPI)           │
├─────────────────────────────────────────────────────────────┤
│  17. research-agents   (Investigation agents)               │
└─────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────┐
│ TIER 4: Interface Layers (User-facing)                      │
├─────────────────────────────────────────────────────────────┤
│  13. web-api           (FastAPI REST API)                   │
│  14. web-ui            (Next.js frontend)                   │
│  15. cli-interface     (Click-based CLI)                    │
│  16. graph-ui          (Interactive graph viewer)           │
└─────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────┐
│ TIER 3: Application Services (Business orchestration)       │
├─────────────────────────────────────────────────────────────┤
│  10. investigation-engine (Agent orchestration)             │
│  11. graph-builder        (Graph construction)              │
│  12. reporting-engine     (Report generation)               │
└─────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────┐
│ TIER 2: Domain Services (Business logic)                    │
├─────────────────────────────────────────────────────────────┤
│  5. document-extraction   (PDF/DOCX text extraction)        │
│  6. claim-extraction      (Extract claims from text)        │
│  7. qualifier-detection   (Semantic qualifier analysis)     │
│  8. semantic-clustering   (Embedding and clustering)        │
│  9. research-apis         (Academic search APIs)            │
└─────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────┐
│ TIER 1: Core Infrastructure (Pure libraries)                │
├─────────────────────────────────────────────────────────────┤
│  1. config-loader         (Configuration management)        │
│  2. models                (Pydantic domain models)          │
│  3. db-connectors         (Database connection pools)       │
│  4. ai-providers          (AI client abstraction)           │
└─────────────────────────────────────────────────────────────┘
```

### Module Independence Rules

**TIER 1 (Core):** No dependencies on any other modules
**TIER 2 (Domain):** Can depend on TIER 1 only
**TIER 3 (Application):** Can depend on TIER 1 + TIER 2
**TIER 4 (Interface):** Can depend on all tiers below
**TIER 5 (Standalone):** Zero dependencies on this project

---

## Module Specifications

### TIER 1: Core Infrastructure

#### Module 1: `config-loader`
**Package:** `research_assistant_config`
**Responsibility:** Load, validate, and provide application configuration

**Structure:**
```
config-loader/
├── pyproject.toml
├── src/research_assistant_config/
│   ├── __init__.py
│   ├── loader.py              # Load from YAML/JSON/ENV
│   ├── validator.py           # Pydantic-based validation
│   ├── schema.py              # Config schema definition
│   └── environments/
│       ├── development.py
│       ├── production.py
│       └── testing.py
└── tests/
```

**Interface:**
```python
from research_assistant_config import Config, load_config

config = load_config(env="production")
# Access: config.database.url, config.ai_providers.openai.api_key
```

**External Dependencies:** `pydantic`, `PyYAML`, `python-dotenv`

---

#### Module 2: `models`
**Package:** `research_assistant_models`
**Responsibility:** Shared Pydantic models and enums

**Structure:**
```
models/
├── pyproject.toml
├── src/research_assistant_models/
│   ├── __init__.py
│   ├── document.py           # Document, Page, ExtractionResult
│   ├── claim.py              # Claim, Qualifier, Confidence
│   ├── evidence.py           # Evidence, Finding, Citation
│   ├── investigation.py      # Investigation, AgentStatus
│   ├── graph.py              # GraphNode, GraphEdge
│   └── enums.py              # All enums
└── tests/
```

**Interface:**
```python
from research_assistant_models import Claim, Evidence, Investigation
from research_assistant_models.enums import ClaimStatus, FindingType

claim = Claim(text="...", confidence=0.8, status=ClaimStatus.PENDING)
```

**External Dependencies:** `pydantic`

**Key Design:** This consolidates ALL models from:
- `research_agent/models.py`
- `research-agents/.../models.py`
- Any duplicates in `web_ui/`

---

#### Module 3: `db-connectors`
**Package:** `research_assistant_db`
**Responsibility:** Database connection management and query execution

**Structure:**
```
db-connectors/
├── pyproject.toml
├── src/research_assistant_db/
│   ├── __init__.py
│   ├── base.py               # Abstract DatabaseInterface
│   ├── postgresql.py         # PostgreSQL with asyncpg
│   ├── neo4j.py              # Neo4j with official driver
│   ├── sqlite.py             # SQLite (for dev/testing)
│   ├── connection_pool.py   # Connection pooling
│   └── transaction.py        # Transaction management
└── tests/
```

**Interface:**
```python
from research_assistant_db import PostgreSQLDatabase, Neo4jDatabase

# PostgreSQL for relational data
pg_db = PostgreSQLDatabase(config.database.postgresql)
await pg_db.connect()
result = await pg_db.fetchrow("SELECT * FROM claims WHERE id = $1", claim_id)

# Neo4j for graph operations
neo4j_db = Neo4jDatabase(config.database.neo4j)
await neo4j_db.execute_cypher("CREATE (n:Claim {text: $text})", text=claim_text)
```

**External Dependencies:** `asyncpg`, `neo4j`, `sqlalchemy` (optional)

---

#### Module 4: `ai-providers`
**Package:** `research_assistant_ai`
**Responsibility:** Unified AI provider abstraction

**Structure:**
```
ai-providers/
├── pyproject.toml
├── src/research_assistant_ai/
│   ├── __init__.py
│   ├── base.py               # Abstract AIInterface
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   ├── local_provider.py     # For local models
│   ├── retry.py              # Retry logic
│   ├── rate_limiter.py       # Rate limiting
│   └── cache.py              # Response caching
└── tests/
```

**Interface:**
```python
from research_assistant_ai import OpenAIProvider, AnthropicProvider

ai = OpenAIProvider(api_key=config.ai_providers.openai.api_key)
response = await ai.generate("Extract claims from: ...", temperature=0.7)
```

**External Dependencies:** `openai`, `anthropic`

**Consolidates:** `ai_helper.py`, `utils/ai_client.py`, `adapters/ai_adapter.py`

---

### TIER 2: Domain Services

#### Module 5: `document-extraction`
**Package:** `research_assistant_extraction`
**Responsibility:** Extract text from PDF, DOCX, TXT files

**Structure:**
```
document-extraction/
├── pyproject.toml
├── src/research_assistant_extraction/
│   ├── __init__.py
│   ├── base_extractor.py     # Abstract interface
│   ├── pdf_extractor.py
│   ├── docx_extractor.py
│   ├── txt_extractor.py
│   ├── column_detector.py
│   └── postprocessor.py
└── tests/
```

**Interface:**
```python
from research_assistant_extraction import PDFExtractor
from research_assistant_models import Document

extractor = PDFExtractor()
result = await extractor.extract(file_path)
# Returns: ExtractionResult(full_text, page_count, metadata, pages)
```

**External Dependencies:** `pdfplumber`, `PyPDF2`, `python-docx`
**Internal Dependencies:** `research_assistant_models`

**Consolidates:** `document_processing/` directory

---

#### Module 6: `claim-extraction`
**Package:** `research_assistant_claims`
**Responsibility:** Extract claims from document text using AI

**Structure:**
```
claim-extraction/
├── pyproject.toml
├── src/research_assistant_claims/
│   ├── __init__.py
│   ├── extractor.py          # Main ClaimExtractor
│   ├── prompts.py            # Claim extraction prompts
│   ├── validator.py          # Validate extracted claims
│   └── batch_processor.py    # Process large docs in batches
└── tests/
```

**Interface:**
```python
from research_assistant_claims import ClaimExtractor

extractor = ClaimExtractor(ai_provider=ai)
claims = await extractor.extract_claims(text)
# Returns: List[Claim]
```

**External Dependencies:** None (uses AI abstraction)
**Internal Dependencies:** `research_assistant_models`, `research_assistant_ai`

**Consolidates:** `document_processing/claim_extractor.py`

---

#### Module 7: `qualifier-detection`
**Package:** `research_assistant_qualifiers`
**Responsibility:** Extract and preserve semantic qualifiers (may, might, all, some)

**Structure:**
```
qualifier-detection/
├── pyproject.toml
├── src/research_assistant_qualifiers/
│   ├── __init__.py
│   ├── extractor.py          # Extract qualifiers from text
│   ├── normalizer.py         # Normalize claims preserving qualifiers
│   ├── validator.py          # Validate preservation
│   └── categories.py         # Qualifier categories
└── tests/
```

**Interface:**
```python
from research_assistant_qualifiers import QualifierExtractor, ClaimNormalizer

extractor = QualifierExtractor()
qualifiers = extractor.extract("Some studies suggest climate change may accelerate")
# Returns: [Qualifier(text="some", category="QUANTITY"), Qualifier(text="may", ...)]

normalizer = ClaimNormalizer(ai_provider=ai)
result = await normalizer.normalize("Some studies suggest...")
# Returns: NormalizationResult(normalized_text, qualifiers_preserved, confidence)
```

**External Dependencies:** None
**Internal Dependencies:** `research_assistant_models`, `research_assistant_ai`

**Consolidates:** `normalization/` directory

---

#### Module 8: `semantic-clustering`
**Package:** `research_assistant_clustering`
**Responsibility:** Cluster claims by semantic similarity, build hierarchies

**Structure:**
```
semantic-clustering/
├── pyproject.toml
├── src/research_assistant_clustering/
│   ├── __init__.py
│   ├── embedder.py           # Generate embeddings
│   ├── clusterer.py          # Clustering algorithms (DBSCAN, HDBSCAN)
│   ├── hierarchy_builder.py  # Build claim hierarchies
│   ├── similarity.py         # Similarity metrics
│   └── cache.py              # Cache embeddings
└── tests/
```

**Interface:**
```python
from research_assistant_clustering import ClaimClusterer

clusterer = ClaimClusterer(embedding_model="sentence-transformers/...")
clusters = await clusterer.cluster_claims(claims, eps=0.3, min_samples=2)
# Returns: List[ClaimCluster]

hierarchy = await clusterer.build_hierarchy(claims)
# Returns: ClaimHierarchy (tree structure)
```

**External Dependencies:** `sentence-transformers`, `scikit-learn`, `numpy`
**Internal Dependencies:** `research_assistant_models`

**Consolidates:** `claim_analysis/`, `sentence_analyzer.py`

---

#### Module 9: `research-apis`
**Package:** `research_assistant_research`
**Responsibility:** Search academic papers via multiple APIs

**Structure:**
```
research-apis/
├── pyproject.toml
├── src/research_assistant_research/
│   ├── __init__.py
│   ├── base_api.py           # Abstract ResearchAPIInterface
│   ├── arxiv_api.py
│   ├── semantic_scholar_api.py
│   ├── pubmed_api.py
│   ├── crossref_api.py
│   ├── openalex_api.py
│   ├── aggregator.py         # Search across multiple APIs
│   └── citation_formatter.py # Format citations (APA, MLA, etc.)
└── tests/
```

**Interface:**
```python
from research_assistant_research import ArxivAPI, ResearchAggregator

api = ArxivAPI()
papers = await api.search("machine learning", max_results=10)
# Returns: List[Paper]

# Or use aggregator for multi-source search
aggregator = ResearchAggregator(apis=[arxiv, semantic_scholar, pubmed])
all_papers = await aggregator.search("climate change", max_results=20)
```

**External Dependencies:** `arxiv`, `requests`, `orkg`
**Internal Dependencies:** `research_assistant_models`

**Consolidates:** `research_apis/` directory

---

### TIER 3: Application Services

#### Module 10: `investigation-engine`
**Package:** `research_assistant_investigation`
**Responsibility:** Orchestrate multi-agent investigation system

**Structure:**
```
investigation-engine/
├── pyproject.toml
├── src/research_assistant_investigation/
│   ├── __init__.py
│   ├── orchestrator.py       # Agent lifecycle management
│   ├── work_scheduler.py     # Investigation queue management
│   ├── priority_calculator.py # Calculate investigation priority
│   └── monitor.py            # Agent monitoring
└── tests/
```

**Interface:**
```python
from research_assistant_investigation import InvestigationOrchestrator
from research_agents import SupportAgent, ChallengeAgent

orchestrator = InvestigationOrchestrator(db=db, ai=ai)
await orchestrator.start_agent_pool(agent_configs=[
    {"type": "support", "count": 3},
    {"type": "challenge", "count": 3},
])

status = await orchestrator.get_status()
# Returns: AgentPoolStatus(active_agents, queue_length, ...)
```

**External Dependencies:** None
**Internal Dependencies:**
- `research-agents` (standalone module)
- `research_assistant_models`
- `research_assistant_db`
- `research_assistant_ai`

**Consolidates:** `investigation/` directory

---

#### Module 11: `graph-builder`
**Package:** `research_assistant_graph`
**Responsibility:** Build and enrich knowledge graph in Neo4j

**Structure:**
```
graph-builder/
├── pyproject.toml
├── src/research_assistant_graph/
│   ├── __init__.py
│   ├── builder.py            # Build graph from claims/evidence
│   ├── enrichment/
│   │   ├── evidence_manager.py
│   │   ├── citation_network.py
│   │   ├── sentence_tracker.py
│   │   └── agent_tracker.py
│   ├── queries.py            # Common Cypher queries
│   └── visualizer.py         # Graph visualization helpers
└── tests/
```

**Interface:**
```python
from research_assistant_graph import GraphBuilder

builder = GraphBuilder(neo4j_db=neo4j)
await builder.create_claim_node(claim)
await builder.link_evidence_to_claim(evidence_id, claim_id, relationship_type="SUPPORTS")

graph_data = await builder.get_subgraph(claim_id, depth=2)
# Returns: GraphData (nodes, edges for visualization)
```

**External Dependencies:** None
**Internal Dependencies:**
- `research_assistant_db` (Neo4j)
- `research_assistant_models`

**Consolidates:** `graph_enrichment/`, `graph_database.py`

---

#### Module 12: `reporting-engine`
**Package:** `research_assistant_reporting`
**Responsibility:** Generate reports from investigation results

**Structure:**
```
reporting-engine/
├── pyproject.toml
├── src/research_assistant_reporting/
│   ├── __init__.py
│   ├── generator.py          # Main report generator
│   ├── templates/
│   │   ├── claim_report.jinja2
│   │   ├── investigation_report.jinja2
│   │   └── document_report.jinja2
│   ├── formatters/
│   │   ├── markdown.py
│   │   ├── html.py
│   │   └── pdf.py
│   └── analyzers/
│       └── confidence_analyzer.py
└── tests/
```

**Interface:**
```python
from research_assistant_reporting import ReportGenerator

generator = ReportGenerator(db=db)
report = await generator.generate_claim_report(
    claim_id=claim_id,
    format="markdown"
)
# Returns: str (formatted report)
```

**External Dependencies:** `jinja2`, `markdown`, `pdfkit` (optional)
**Internal Dependencies:** `research_assistant_models`, `research_assistant_db`

**Consolidates:** `reporting/` directory

---

### TIER 4: Interface Layers

#### Module 13: `web-api`
**Package:** `research_assistant_api`
**Responsibility:** REST API for all operations (FastAPI)

**Structure:**
```
web-api/
├── pyproject.toml
├── src/research_assistant_api/
│   ├── __init__.py
│   ├── main.py               # FastAPI app
│   ├── routes/
│   │   ├── documents.py
│   │   ├── claims.py
│   │   ├── investigations.py
│   │   ├── reports.py
│   │   └── graph.py
│   ├── middleware/
│   │   ├── auth.py
│   │   ├── cors.py
│   │   └── logging.py
│   ├── schemas/              # API request/response schemas
│   └── dependencies.py       # FastAPI dependencies
└── tests/
```

**API Endpoints:**
```
POST   /api/v1/documents/upload
GET    /api/v1/documents/{doc_id}
DELETE /api/v1/documents/{doc_id}

GET    /api/v1/claims
POST   /api/v1/claims/{claim_id}/investigate
GET    /api/v1/claims/{claim_id}/report

GET    /api/v1/graph/root-claims
GET    /api/v1/graph/subgraph/{claim_id}

GET    /api/v1/investigations/status
POST   /api/v1/investigations/schedule
```

**External Dependencies:** `fastapi`, `uvicorn`, `pydantic`
**Internal Dependencies:** ALL application service modules

**Consolidates:** `backend/` skeleton, replaces Flask routes in `web_ui/app.py`

---

#### Module 14: `web-ui`
**Package:** `research-assistant-frontend`
**Responsibility:** Next.js web interface

**Structure:**
```
web-ui/
├── package.json
├── src/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   ├── documents/
│   │   ├── claims/
│   │   ├── graph/
│   │   └── reports/
│   ├── components/
│   │   ├── DocumentUpload.tsx
│   │   ├── ClaimList.tsx
│   │   ├── GraphVisualization.tsx
│   │   └── InvestigationStatus.tsx
│   ├── lib/
│   │   └── api-client.ts
│   └── hooks/
└── tests/
```

**External Dependencies:** `next`, `react`, `tailwind`, `d3` (for graphs)
**API Client:** Calls `web-api` REST endpoints

**Consolidates:** `frontend/` skeleton + graph visualization from `web_ui/`

---

#### Module 15: `cli-interface`
**Package:** `research-assistant-cli`
**Responsibility:** Command-line interface using Click

**Structure:**
```
cli-interface/
├── pyproject.toml
├── src/research_assistant_cli/
│   ├── __init__.py
│   ├── main.py               # Click app
│   ├── commands/
│   │   ├── documents.py      # ingest, list, view
│   │   ├── claims.py         # extract, normalize, investigate
│   │   ├── agents.py         # start, stop, status
│   │   └── reports.py        # generate, export
│   └── utils/
│       └── progress.py       # Progress bars
└── tests/
```

**Commands:**
```bash
research-assistant ingest <file> --title "Document Title"
research-assistant claims extract <doc_id>
research-assistant claims investigate <claim_id>
research-assistant agents start --support 3 --challenge 3
research-assistant agents status
research-assistant report generate <claim_id> -o report.md
```

**External Dependencies:** `click`, `rich` (for pretty output)
**Internal Dependencies:** ALL application service modules OR calls `web-api`

**Consolidates:** `research_agent/cli.py`, `cli_assistant_enhanced.py`

---

#### Module 16: `graph-ui`
**Package:** `research_assistant_graph_ui`
**Responsibility:** Interactive graph visualization (Flask + Socket.IO)

**Structure:**
```
graph-ui/
├── pyproject.toml
├── src/research_assistant_graph_ui/
│   ├── __init__.py
│   ├── app.py                # Flask + Socket.IO app
│   ├── routes.py
│   ├── socketio_handlers.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── js/
│       │   ├── graph-renderer.js
│       │   └── websocket-client.js
│       └── css/
└── tests/
```

**Features:**
- Real-time graph updates via WebSocket
- Interactive D3.js visualization
- Claim/evidence exploration

**External Dependencies:** `flask`, `flask-socketio`
**Internal Dependencies:** `research_assistant_graph`, `research_assistant_models`

**Consolidates:** `web_ui/` directory

---

### TIER 5: Standalone Modules

#### Module 17: `research-agents`
**Already created!** ✅

**Status:** Completed in previous refactoring
**Location:** `/research-agents/`
**Package:** `research-agents`

**Interface:**
```python
from research_agents import SupportAgent, ChallengeAgent, AnalysisAgent
from research_agents import DatabaseInterface, AIInterface

# Implement interfaces
db_adapter = MyDatabaseAdapter()
ai_adapter = MyAIAdapter()

# Create agents
support = SupportAgent(db_adapter, ai_adapter)
await support.start()
```

---

## Dependency Graph

### Visual Dependency Graph

```
┌──────────────────────────────────────────────────────────────────┐
│                     TIER 5: Standalone Modules                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  research-agents (completely independent)                  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ uses via adapters
┌──────────────────────────────────────────────────────────────────┐
│                    TIER 4: Interface Layers                      │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  web-api  │  │  web-ui   │  │    cli    │  │ graph-ui  │    │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘    │
│        └────────────────┴──────────────┴──────────────┘          │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────┴─────────────────────────────────────┐
│                  TIER 3: Application Services                    │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │investigation-    │  │graph-builder │  │reporting-    │       │
│  │   engine         │  │              │  │   engine     │       │
│  └─────────┬────────┘  └──────┬───────┘  └──────┬───────┘       │
│            └───────────────────┴──────────────────┘              │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────┴─────────────────────────────────────┐
│                    TIER 2: Domain Services                       │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │ document- │  │   claim-  │  │qualifier- │  │ semantic- │    │
│  │extraction │  │extraction │  │ detection │  │clustering │    │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘    │
│        │              │              │              │            │
│  ┌─────┴──────────────┴──────────────┴──────────────┴──────┐    │
│  │              research-apis                              │    │
│  └───────────────────────────────┬─────────────────────────┘    │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────────────────┴─────────────────────────────────┐
│                   TIER 1: Core Infrastructure                    │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  config-  │  │  models   │  │    db-    │  │    ai-    │    │
│  │  loader   │  │           │  │connectors │  │ providers │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
│                                                                  │
│  NO INTERNAL DEPENDENCIES - Pure libraries                      │
└──────────────────────────────────────────────────────────────────┘
```

### Dependency Matrix

| Module | Depends On (Internal) | External Deps |
|--------|----------------------|---------------|
| **config-loader** | None | pydantic, PyYAML |
| **models** | None | pydantic |
| **db-connectors** | models | asyncpg, neo4j |
| **ai-providers** | models | openai, anthropic |
| **document-extraction** | models | pdfplumber, PyPDF2 |
| **claim-extraction** | models, ai-providers | None |
| **qualifier-detection** | models, ai-providers | None |
| **semantic-clustering** | models | sentence-transformers, scikit-learn |
| **research-apis** | models | arxiv, requests |
| **investigation-engine** | models, db-connectors, ai-providers, research-agents | None |
| **graph-builder** | models, db-connectors | None |
| **reporting-engine** | models, db-connectors | jinja2 |
| **web-api** | ALL Tier 3 modules | fastapi, uvicorn |
| **web-ui** | web-api (REST only) | next, react, tailwind |
| **cli-interface** | ALL Tier 3 modules OR web-api | click, rich |
| **graph-ui** | graph-builder, models | flask, flask-socketio |
| **research-agents** | None (uses interfaces) | pydantic |

---

## Migration Strategy

### Phase 1: Foundation (Week 1-2)

**Goal:** Create core infrastructure modules

**Tasks:**
1. Create `models` module
   - Extract all Pydantic models from codebase
   - Consolidate duplicates
   - Add comprehensive validation

2. Create `config-loader` module
   - Unified configuration schema
   - Environment-specific configs
   - Validation

3. Create `db-connectors` module
   - PostgreSQL connector with connection pooling
   - Neo4j connector
   - Abstract interface

4. Create `ai-providers` module
   - Consolidate `ai_helper.py` and `utils/ai_client.py`
   - Add retry logic and rate limiting
   - Response caching

**Success Criteria:**
- [ ] All 4 Tier 1 modules created
- [ ] Published to private PyPI or installed via `pip install -e`
- [ ] Basic tests for each module (50%+ coverage)
- [ ] Other code can import: `from research_assistant_models import Claim`

---

### Phase 2: Domain Services (Week 3-4)

**Goal:** Extract business logic into domain services

**Tasks:**
1. Create `document-extraction` module
   - Move `document_processing/` code
   - Use `models` module

2. Create `claim-extraction` module
   - Move `claim_extractor.py`
   - Use `ai-providers` abstraction

3. Create `qualifier-detection` module
   - Move `normalization/` code

4. Create `semantic-clustering` module
   - Consolidate `claim_analysis/` and `sentence_analyzer.py`

5. Create `research-apis` module
   - Move `research_apis/` code
   - Add aggregator

**Success Criteria:**
- [ ] All 5 Tier 2 modules created
- [ ] Each module can be used standalone
- [ ] Integration tests with real data
- [ ] Documentation with examples

---

### Phase 3: Application Services (Week 5-6)

**Goal:** Build orchestration layer

**Tasks:**
1. Create `investigation-engine` module
   - Move `investigation/` code
   - Integrate with `research-agents` module
   - Use adapters to connect to db/ai

2. Create `graph-builder` module
   - Move `graph_enrichment/` and `graph_database.py`
   - Clean Cypher query interface

3. Create `reporting-engine` module
   - Move `reporting/` code
   - Add templates

**Success Criteria:**
- [ ] All 3 Tier 3 modules created
- [ ] End-to-end test: Upload PDF → Extract claims → Investigate → Report
- [ ] Can be used via Python API (no CLI yet)

---

### Phase 4: Interface Layers (Week 7-8)

**Goal:** Build user-facing interfaces

**Tasks:**
1. Create `web-api` module
   - Implement FastAPI REST API
   - Replace Flask routes from `web_ui/app.py`
   - Add authentication

2. Create `cli-interface` module
   - Consolidate all CLI code
   - Rich progress bars
   - Calls application services OR web-api

3. Create `graph-ui` module
   - Extract graph visualization from `web_ui/`
   - Socket.IO for real-time updates

4. Create `web-ui` module
   - Next.js frontend
   - Calls `web-api`

**Success Criteria:**
- [ ] API fully functional and documented (OpenAPI/Swagger)
- [ ] CLI can perform all operations
- [ ] Graph UI interactive and real-time
- [ ] Web UI basic functionality working

---

### Phase 5: Testing & Polish (Week 9-10)

**Goal:** Comprehensive testing and documentation

**Tasks:**
1. Write tests for all modules (80%+ coverage)
2. Integration test suite for full pipeline
3. Performance testing and optimization
4. Documentation for each module
5. Migration guide from old to new architecture
6. Deployment guides (Docker, Kubernetes)

**Success Criteria:**
- [ ] 80%+ test coverage across all modules
- [ ] Full documentation site (MkDocs or Sphinx)
- [ ] Performance benchmarks documented
- [ ] Docker Compose for local development
- [ ] CI/CD pipeline running

---

### Phase 6: Deprecation & Cleanup (Week 11-12)

**Goal:** Remove old monolithic code

**Tasks:**
1. Mark old code as deprecated
2. Migrate any remaining functionality
3. Remove `cli_assistant.py` (migrate to new CLI)
4. Remove `web_ui/app.py` (migrate to new web-api + graph-ui)
5. Remove duplicate agent code (`research_agent/agents/`)
6. Clean up root directory scripts

**Success Criteria:**
- [ ] All functionality available via new modules
- [ ] Old code removed or archived
- [ ] No duplicate implementations
- [ ] Clean repository structure

---

## Parallel Development Plan

### How Multiple Agents Work Simultaneously

#### Agent Assignment Strategy

```
┌─────────────────────┬──────────────────┬──────────────────────┐
│ Agent ID            │ Module           │ Primary Tasks        │
├─────────────────────┼──────────────────┼──────────────────────┤
│ Agent-Infrastructure│ Tier 1 modules   │ Core infrastructure  │
│ Agent-Documents     │ Module 5         │ Document extraction  │
│ Agent-Claims        │ Modules 6, 7     │ Claim processing     │
│ Agent-Research      │ Modules 9, 11    │ Research APIs, agents│
│ Agent-Graph         │ Module 11        │ Graph operations     │
│ Agent-Frontend      │ Modules 14, 16   │ UI development       │
│ Agent-API           │ Module 13        │ REST API             │
│ Agent-Testing       │ All modules      │ Write tests          │
└─────────────────────┴──────────────────┴──────────────────────┘
```

### Development Workflow

1. **Day 1: Setup**
   - Create module directory structure
   - Each agent creates their module skeleton
   - Define interfaces first

2. **Day 2-5: Implementation**
   - Agents work in parallel on their modules
   - Use mocks for dependencies not yet implemented
   - Daily sync: 15-min standup on what's blocking

3. **Day 6-7: Integration**
   - Replace mocks with real implementations
   - Integration testing
   - Fix interface mismatches

4. **Day 8-10: Polish**
   - Testing
   - Documentation
   - Performance optimization

### Communication Between Agents

**Shared Documents:**
- `INTERFACES.md` - Interface contracts (updated by all)
- `CHANGELOG.md` - What changed in each module
- `BLOCKERS.md` - Current blockers and dependencies

**Daily Sync:**
- What did you complete?
- What are you working on today?
- What's blocking you?

**Interface Changes:**
- Post in `#interface-changes` channel
- Update `INTERFACES.md`
- Notify dependent agents

### Git Workflow for Parallel Development

```
main (protected)
 │
 ├── module/tier1-models (Agent-Infrastructure)
 ├── module/tier1-config (Agent-Infrastructure)
 ├── module/tier1-db (Agent-Infrastructure)
 ├── module/tier1-ai (Agent-Infrastructure)
 │
 ├── module/tier2-extraction (Agent-Documents)
 ├── module/tier2-claims (Agent-Claims)
 ├── module/tier2-qualifiers (Agent-Claims)
 ├── module/tier2-clustering (Agent-Claims)
 ├── module/tier2-research-apis (Agent-Research)
 │
 ├── module/tier3-investigation (Agent-Research)
 ├── module/tier3-graph (Agent-Graph)
 ├── module/tier3-reporting (Agent-Testing)
 │
 ├── module/tier4-web-api (Agent-API)
 ├── module/tier4-web-ui (Agent-Frontend)
 ├── module/tier4-cli (Agent-API)
 └── module/tier4-graph-ui (Agent-Frontend)
```

**Branch Naming:**
- `module/<module-name>` for main module work
- `module/<module-name>/feature/<feature>` for specific features
- `integration/<milestone>` for integration work

**Merge Strategy:**
- Tier 1 modules merge first (no dependencies)
- Tier 2 modules merge once Tier 1 is stable
- etc.

---

## Testing Strategy

### Module-Level Testing

Each module must have:

1. **Unit Tests** (70%+ coverage)
   ```python
   # tests/test_claim_extractor.py
   @pytest.mark.asyncio
   async def test_extract_claims_from_text():
       extractor = ClaimExtractor(ai=MockAI())
       claims = await extractor.extract_claims("Sample text...")
       assert len(claims) > 0
       assert claims[0].text is not None
   ```

2. **Integration Tests**
   ```python
   # tests/integration/test_full_pipeline.py
   async def test_pdf_to_claims_pipeline():
       # Uses real modules, mocked external services
       extractor = PDFExtractor()
       claim_extractor = ClaimExtractor(ai=MockAI())

       doc = await extractor.extract("sample.pdf")
       claims = await claim_extractor.extract_claims(doc.full_text)

       assert len(claims) > 0
   ```

3. **Contract Tests** (for interfaces)
   ```python
   # tests/contracts/test_ai_provider_contract.py
   def test_openai_implements_ai_interface():
       from research_assistant_ai import OpenAIProvider, AIInterface
       assert issubclass(OpenAIProvider, AIInterface)

       # Check all methods implemented
       for method in ['generate', 'generate_with_schema', ...]:
           assert hasattr(OpenAIProvider, method)
   ```

### System-Level Testing

1. **End-to-End Tests**
   - Upload PDF → Extract claims → Investigate → Generate report
   - Uses all modules together
   - Run against real database (test instance)

2. **Performance Tests**
   - Benchmark each module
   - Load testing for API
   - Stress testing for agent pool

3. **Smoke Tests**
   - Quick sanity checks
   - Run before merging PRs
   - ~5 minutes total

### CI/CD Pipeline

```yaml
# .github/workflows/test-modules.yml
name: Test All Modules

on: [push, pull_request]

jobs:
  test-tier1:
    # Test all Tier 1 modules in parallel
    strategy:
      matrix:
        module: [config-loader, models, db-connectors, ai-providers]
    steps:
      - name: Test ${{ matrix.module }}
        run: |
          cd ${{ matrix.module }}
          pytest tests/ --cov

  test-tier2:
    needs: test-tier1
    # Test Tier 2 after Tier 1 passes
    ...

  integration:
    needs: [test-tier1, test-tier2, test-tier3]
    # Full integration tests
    ...
```

---

## Success Metrics

### Technical Metrics

- [ ] **17 modules** created and published
- [ ] **80%+ test coverage** across all modules
- [ ] **<100ms p95 latency** for API endpoints
- [ ] **Zero duplicate code** (consolidated)
- [ ] **All dependencies explicitly declared** in pyproject.toml

### Developer Experience Metrics

- [ ] **New dev onboarding <1 day** (understand one module quickly)
- [ ] **Parallel PRs without conflicts** (5+ simultaneous)
- [ ] **Module update doesn't break others** (interface stability)
- [ ] **CI pipeline <10 minutes** for full test suite

### Deployment Metrics

- [ ] **Independent deployment** of any module
- [ ] **Rollback single module** without affecting others
- [ ] **Docker image per module** (<500MB each)
- [ ] **Kubernetes-ready** with Helm charts

---

## Rollout Plan

### Week 1-2: Foundation
- Create Tier 1 modules
- Setup CI/CD
- Document interfaces

### Week 3-4: Domain Services
- Create Tier 2 modules
- Write domain tests
- Integration with Tier 1

### Week 5-6: Application Services
- Create Tier 3 modules
- End-to-end testing
- Performance benchmarks

### Week 7-8: Interfaces
- Create Tier 4 modules
- User acceptance testing
- Documentation

### Week 9-10: Testing & Polish
- Comprehensive testing
- Performance optimization
- Documentation site

### Week 11-12: Migration
- Deprecate old code
- Final cleanup
- Launch new architecture

---

## Questions & Next Steps

### Immediate Questions

1. **Separate repositories vs monorepo?**
   - Option A: Separate repo per module (better for publishing)
   - Option B: Monorepo with workspaces (easier development)

2. **Private PyPI vs local install?**
   - Option A: Private PyPI server (production-like)
   - Option B: `pip install -e` for development

3. **Database migration?**
   - Migrate legacy SQLite to PostgreSQL?
   - Or maintain both?

### Next Steps

1. **Create branch:** `git checkout -b modularization-refactor`
2. **Start with Tier 1:** Begin with `models` module
3. **Setup module template:** Create standard structure
4. **Assign agents:** Distribute modules to parallel agents
5. **Daily standups:** Track progress and blockers

---

**Ready to begin modularization?**

Let's start by creating the first module (`models`) as a template that others can follow!
