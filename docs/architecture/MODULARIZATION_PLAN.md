# Project Modularization Plan

## Date: 2025-11-17
## Status: PLANNING
## Goal: Refactor monolithic codebase into modular, testable, maintainable architecture

---

## Why Modularize?

### Current Pain Points
- **document_processor.py**: 1400+ lines doing extraction, agents, database, WebSocket, orchestration
- **graph.js**: Mixed concerns (API, rendering, layout, interactions)
- **app.py**: Routes mixed with business logic
- **Hard to test**: No clear boundaries between layers
- **Hard to extend**: GraphRAG implementation will make it worse

### Benefits of Modularization
- ✅ **Testability**: Each module can be unit tested independently
- ✅ **Maintainability**: Clear responsibility boundaries
- ✅ **Extensibility**: Easy to add GraphRAG, new agents, new features
- ✅ **Parallel Development**: Work on frontend/backend/agents independently
- ✅ **Debugging**: Easier to isolate issues to specific modules
- ✅ **Reusability**: Agents, repositories can be reused across features

---

## Target Architecture

```
Research-Assistant-Tool/
├── backend/
│   ├── api/                          # Flask API layer (HTTP endpoints)
│   ├── services/                     # Business logic layer
│   ├── agents/                       # AI agent layer
│   ├── database/                     # Data access layer
│   └── events/                       # Event system
│
├── frontend/
│   ├── api/                          # API client layer
│   ├── components/                   # UI components
│   ├── state/                        # State management
│   └── utils/                        # Utilities
│
└── shared/
    ├── constants/                    # Shared constants
    └── schemas/                      # Data schemas
```

---

## Migration Phases

### Phase 1: Database Layer (Repositories)
**Duration**: 1-2 sessions
**Risk**: Medium (touches all database access)
**Prerequisite**: None

#### Files to Create
```
backend/database/
├── __init__.py
├── neo4j_client.py                  # Singleton Neo4j connection
├── repositories/
│   ├── __init__.py
│   ├── base_repository.py           # Abstract base class
│   ├── document_repository.py
│   ├── claim_repository.py
│   └── graph_repository.py          # For GraphRAG queries
└── models/
    ├── __init__.py
    ├── document.py                   # Document domain model
    ├── claim.py                      # Claim domain model
    └── relationship.py               # Relationship types
```

#### Migration Steps

1. **Create `neo4j_client.py`**
   - Move Neo4j connection logic from `research_agent/neo4j_database.py`
   - Singleton pattern for driver management
   - Environment variable configuration

2. **Create `ClaimRepository`**
   - Extract all Cypher queries from:
     - `document_processor.py` (claim CRUD)
     - `app.py` (claim queries in routes)
   - Methods:
     - `create_claim(claim_data) -> str`
     - `update_claim(claim_id, updates) -> None`
     - `get_claim(claim_id) -> Dict`
     - `find_claims_by_document(doc_id) -> List[Dict]`
     - `find_similar_claims(claim_id, min_score) -> List[Dict]`
     - `get_claim_cluster(claim_id) -> List[str]`

3. **Create `DocumentRepository`**
   - Extract document queries from `app.py` and `document_processor.py`
   - Methods:
     - `create_document(doc_data) -> str`
     - `update_document(doc_id, updates) -> None`
     - `get_document(doc_id) -> Dict`
     - `get_all_documents() -> List[Dict]`
     - `link_claim_to_document(doc_id, claim_id, order) -> None`

4. **Create `GraphRepository`**
   - For GraphRAG queries (prepare for future)
   - Methods:
     - `get_full_graph() -> Dict`
     - `get_document_subgraph(doc_id) -> Dict`
     - `get_statistics() -> Dict`

5. **Update Consumers**
   - `document_processor.py`: Replace `self.db.create_node()` with `claim_repo.create_claim()`
   - `app.py`: Replace inline Cypher with repository calls

#### Success Criteria
- [ ] All database access goes through repositories
- [ ] No Cypher queries in `document_processor.py` or `app.py`
- [ ] Tests pass
- [ ] GraphRAG repository ready for Phase 4

---

### Phase 2: Services Layer (Business Logic)
**Duration**: 2-3 sessions
**Risk**: High (major refactor of document_processor.py)
**Prerequisite**: Phase 1 complete

#### Files to Create
```
backend/services/
├── __init__.py
├── document_service.py               # Document processing orchestration
├── claim_service.py                  # Claim processing orchestration
├── graphrag_service.py               # GraphRAG algorithms (FUTURE)
└── research_service.py               # Investigation coordination
```

#### Migration Steps

1. **Create `DocumentService`**
   - Extract from `document_processor.py`:
     - Document upload handling
     - Title extraction coordination
     - Overall orchestration
   - Dependencies: `DocumentRepository`, `ClaimService`, `EventEmitter`
   - Methods:
     - `process_document(file_path, emit_callback) -> str`
     - `extract_title(doc_id, text) -> str`
     - `update_document_status(doc_id, status) -> None`

2. **Create `ClaimService`**
   - Extract from `document_processor.py`:
     - Claim extraction orchestration
     - 4-stage pipeline orchestration
     - Skeleton creation logic
   - Dependencies: `ClaimRepository`, `ExtractionAgents`, `ProcessingAgents`, `EventEmitter`
   - Methods:
     - `extract_claims(doc_id, text, emit_callback) -> List[str]`
     - `create_skeleton_claims(doc_id, raw_claims, emit_callback) -> List[str]`
     - `process_claim(claim_id, text, emit_callback) -> Dict`
     - `run_4stage_pipeline(claim_text) -> Dict`

3. **Create `GraphRAGService`** (Future)
   - Placeholder for GraphRAG implementation
   - Dependencies: `GraphRepository`, `ClaimRepository`, `EventEmitter`
   - Methods:
     - `detect_communities(doc_id) -> List[List[str]]`
     - `create_super_claims(community_ids) -> List[str]`
     - `reorganize_graph(doc_id) -> None`

4. **Update `document_processor.py`**
   - Becomes thin wrapper around `DocumentService`
   - OR: Delete and use `DocumentService` directly in routes

5. **Update Routes in `app.py`**
   - Replace `processor.process_document()` with `document_service.process_document()`

#### Success Criteria
- [ ] Business logic separated from routes
- [ ] Services can be tested independently
- [ ] `document_processor.py` < 200 lines OR deleted
- [ ] Clear orchestration layer

---

### Phase 3: Agents Layer (AI Processing)
**Duration**: 1-2 sessions
**Risk**: Low (already somewhat modular)
**Prerequisite**: Phase 2 complete

#### Files to Create
```
backend/agents/
├── __init__.py
├── base_agent.py                     # Abstract base class
├── extraction/
│   ├── __init__.py
│   ├── claim_extractor.py            # Claims from text
│   └── title_extractor.py            # Document title
├── processing/
│   ├── __init__.py
│   ├── claim_analyzer.py             # Stage 1: Analysis
│   ├── claim_clarifier.py            # Stage 2: Clarification
│   ├── claim_simplifier.py           # Stage 3: Simplification
│   └── claim_validator.py            # Stage 4: Validation
└── research/
    ├── __init__.py
    ├── arxiv_agent.py
    └── semantic_scholar_agent.py
```

#### Migration Steps

1. **Create `BaseAgent`**
   - Abstract class with common functionality
   - CLI invocation wrapper
   - Error handling
   - Timing/metrics

2. **Extract Extraction Agents**
   - Move from `document_processor.py`:
     - `_extract_title_with_agent()` → `TitleExtractor`
     - `_extract_flat_claims_with_agent()` → `ClaimExtractor`

3. **Extract Processing Agents**
   - Move from `document_processor.py`:
     - `_simplify_claim_with_agent()` → Split into 4 agents
     - Each agent handles one stage of pipeline
     - Return structured output

4. **Update `ClaimService`**
   - Use new agent classes instead of inline methods
   - Cleaner orchestration

#### Success Criteria
- [ ] All agents in `backend/agents/`
- [ ] Each agent is independently testable
- [ ] Common functionality in `BaseAgent`
- [ ] `document_processor.py` has no CLI invocations

---

### Phase 4: Events Layer (Decoupling)
**Duration**: 1 session
**Risk**: Low (additive change)
**Prerequisite**: Phase 2 complete

#### Files to Create
```
backend/events/
├── __init__.py
├── event_emitter.py                  # Centralized event emission
├── event_types.py                    # Event type constants
└── event_handlers.py                 # Event subscribers (if needed)
```

#### Migration Steps

1. **Create `EventEmitter`**
   - Centralize WebSocket emission
   - Replace all `self._emit()` calls in services
   - Support multiple transports (WebSocket, logging, metrics)

2. **Create `EventTypes`**
   - Constants for all event types:
     - `DOCUMENT_CREATED`
     - `CLAIM_ADDED`
     - `CLAIM_UPDATED`
     - `PROCESSING_COMPLETE`
     - etc.

3. **Update Services**
   - Inject `EventEmitter` into services
   - Replace inline `socketio.emit()` with `events.emit()`

4. **Benefits**
   - Services no longer depend on Flask-SocketIO
   - Can add logging, metrics, webhooks easily
   - Easier testing (mock event emitter)

#### Success Criteria
- [ ] All events go through `EventEmitter`
- [ ] No `socketio.emit()` in services
- [ ] Event types are constants
- [ ] Can swap event transport

---

### Phase 5: API Layer (Routes)
**Duration**: 1 session
**Risk**: Low (mostly organizational)
**Prerequisite**: Phase 2 complete

#### Files to Create
```
backend/api/
├── __init__.py
├── routes/
│   ├── __init__.py
│   ├── documents.py                  # Document upload/retrieval
│   ├── claims.py                     # Claim operations
│   ├── graph.py                      # Graph queries
│   └── research.py                   # Investigation endpoints
└── middleware/
    ├── __init__.py
    ├── auth.py                       # Future authentication
    └── websocket.py                  # WebSocket setup
```

#### Migration Steps

1. **Split `app.py` by Domain**
   - Move routes to domain-specific files
   - Keep `app.py` as main entry point with Blueprint registration

2. **Create Route Modules**
   - `documents.py`: `/api/upload-document`, `/api/graph`
   - `claims.py`: `/api/claim/<id>`
   - `graph.py`: `/api/graph`, `/api/stats`
   - `research.py`: `/api/investigate-claim`

3. **Inject Dependencies**
   - Services, repositories passed to routes
   - No tight coupling

#### Success Criteria
- [ ] `app.py` < 100 lines (just setup)
- [ ] Routes grouped by domain
- [ ] Blueprints registered
- [ ] Services injected

---

### Phase 6: Frontend Modularization
**Duration**: 2 sessions
**Risk**: Medium (D3 is complex)
**Prerequisite**: None (can do in parallel)

#### Files to Create
```
frontend/
├── api/
│   ├── api_client.js                 # Centralized fetch() wrapper
│   └── websocket_client.js           # WebSocket management
├── components/
│   ├── graph/
│   │   ├── graph_renderer.js         # D3 rendering
│   │   ├── graph_layout.js           # Force simulation
│   │   ├── graph_interactions.js     # Click/drag handling
│   │   └── graph_updates.js          # Real-time update logic
│   ├── upload/
│   │   ├── upload_widget.js
│   │   └── file_validator.js
│   └── sidebar/
│       ├── claim_details.js
│       └── stats_panel.js
├── state/
│   ├── graph_state.js                # Current graph data
│   └── ui_state.js                   # UI state (selected node, etc.)
└── utils/
    ├── formatting.js
    ├── validation.js
    └── constants.js
```

#### Migration Steps

1. **Split `graph.js`**
   - `graph_renderer.js`: D3 SVG creation, node/link rendering
   - `graph_layout.js`: Force simulation, physics
   - `graph_interactions.js`: Click, drag, zoom handlers
   - `graph_updates.js`: Incremental updates, smooth transitions

2. **Create `api_client.js`**
   - Centralize all `fetch()` calls from `api.js`
   - Error handling, retries
   - Base URL configuration

3. **Create `websocket_client.js`**
   - Move WebSocket logic from `app.js`
   - Event subscription
   - Reconnection logic

4. **Update `app.js`**
   - Becomes thin orchestrator
   - Wires components together
   - < 200 lines

#### Success Criteria
- [ ] `graph.js` split into 4 files
- [ ] API calls centralized
- [ ] WebSocket handling separated
- [ ] Components are reusable

---

## Migration Order (Recommended)

### Week 1: Foundation
1. **Phase 1**: Database Layer (repositories)
   - Critical foundation for all other phases
   - Low risk, high value

### Week 2: Core Refactor
2. **Phase 2**: Services Layer
   - Major refactor, needs careful testing
3. **Phase 4**: Events Layer
   - Quick win, decouples services

### Week 3: Organization
4. **Phase 5**: API Layer
   - Organizational cleanup
5. **Phase 3**: Agents Layer
   - Clean up after services refactor

### Week 4: Frontend
6. **Phase 6**: Frontend Modularization
   - Can do earlier if working on frontend features

---

## Testing Strategy

### After Each Phase
- [ ] All existing tests pass
- [ ] No regressions in functionality
- [ ] Upload document → Extract claims → Process → Display WORKS

### New Tests to Add
- **Phase 1**: Repository unit tests
  - Mock Neo4j driver
  - Test CRUD operations
- **Phase 2**: Service unit tests
  - Mock repositories
  - Test orchestration logic
- **Phase 3**: Agent unit tests
  - Mock CLI invocations
  - Test structured output parsing
- **Phase 6**: Frontend component tests
  - Mock API calls
  - Test D3 rendering

---

## Risk Mitigation

### High-Risk Changes
1. **Phase 2 (Services)**: Major refactor of `document_processor.py`
   - **Mitigation**: Branch-based development, frequent commits
   - **Rollback**: Keep old `document_processor.py` until services proven

2. **Phase 6 (Frontend)**: Splitting `graph.js` might break rendering
   - **Mitigation**: Copy-paste approach, test each split
   - **Rollback**: Keep backup of working `graph.js`

### Dependencies
- Neo4j must stay running
- AI agent CLIs must work
- WebSocket connections must stay stable

---

## GraphRAG Readiness

### After Phase 1 (Repositories)
- ✅ `GraphRepository` ready for community detection queries
- ✅ `ClaimRepository` ready for similarity queries

### After Phase 2 (Services)
- ✅ `GraphRAGService` can be implemented
- ✅ Real-time events already work

### After Phase 3 (Agents)
- ✅ Super-claim generation agent can be added
- ✅ Follows established pattern

### GraphRAG Implementation (Phase 7)
```python
# backend/services/graphrag_service.py
class GraphRAGService:
    def detect_communities(self, doc_id):
        # 1. Get all claims for document
        claims = self.claim_repo.find_claims_by_document(doc_id)

        # 2. Build similarity graph
        similarity_graph = self._build_similarity_graph(claims)

        # 3. Run Leiden algorithm
        communities = self._leiden_clustering(similarity_graph)

        # 4. Emit progress
        self.events.emit('community_detected', {...})

        return communities

    def create_super_claims(self, community_ids):
        # 1. For each community
        for community in community_ids:
            # 2. Generate super-claim with agent
            super_claim_text = self.super_claim_agent.generate(community)

            # 3. Create in database
            super_claim_id = self.claim_repo.create_claim({
                'text': super_claim_text,
                'is_super_claim': True,
                ...
            })

            # 4. Re-parent child claims
            for claim_id in community:
                self.graph_repo.create_relationship(
                    super_claim_id, claim_id, 'HAS_SUB_CLAIM'
                )

            # 5. Emit real-time update
            self.events.emit('super_claim_created', {
                'super_claim_id': super_claim_id,
                'member_ids': community
            })
```

**Frontend already handles this!** The event system we built supports graph reorganization.

---

## File Deletion Candidates

After modularization, these files can be **deprecated**:
- ❌ `research_agent/graph_database.py` (replaced by repositories)
- ❌ `web_ui/document_processor.py` (replaced by services)
- ⚠️ `research_agent/neo4j_database.py` (move to `backend/database/neo4j_client.py`)

Keep for now:
- ✅ `web_ui/app.py` (becomes entry point)
- ✅ `web_ui/static/js/graph.js` (gets split, not deleted)
- ✅ `web_ui/static/js/app.js` (becomes orchestrator)

---

## Success Metrics

### Code Quality
- **Line count**: `document_processor.py` goes from 1400 → 200 (or deleted)
- **Testability**: 80%+ code coverage on services
- **Modularity**: Each file < 300 lines

### Functionality
- **Zero regressions**: Upload → Process → Display still works
- **Real-time updates**: Still working after refactor
- **Performance**: No degradation

### Developer Experience
- **New feature time**: 50% reduction (e.g., adding new agent type)
- **Bug isolation**: Can pinpoint issues to specific module
- **Onboarding**: New developer can understand one module at a time

---

## Next Steps

### Immediate (Next Session)
1. Read this plan
2. Commit current working state to Git
3. Create feature branch: `feature/modularization-phase1`
4. Start Phase 1: Create `backend/database/` structure

### Before Starting
- [ ] Commit all current changes
- [ ] Tag current version: `v0.1-pre-modularization`
- [ ] Create migration branch
- [ ] Back up Neo4j database

---

## References

- **Current Architecture**: Documented in code
- **Real-Time Sync Philosophy**: `docs/REALTIME_SYNC_AUDIT.md`
- **Schema Documentation**: `docs/FRONTEND_VISUAL_UPDATE_ISSUES.md`
- **GraphRAG Vision**: Microsoft GraphRAG paper
