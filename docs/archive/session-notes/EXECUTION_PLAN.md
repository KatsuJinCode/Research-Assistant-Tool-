# Execution Plan: Phase A - Intelligence Foundation (RAG MVP)
**Approved Strategy:** Option 1 - Balanced Approach
**Current Phase:** A - RAG MVP (36-44 hours)
**Goal:** 2-3x better retrieval using KGE + Hierarchical Attention

---

## 🎯 Phase A Breakdown

### Tier 1.1: Knowledge Graph Embeddings (KGE)
**Time:** 16-20 hours
**Deliverables:**
1. Triple extraction from Neo4j
2. TransE training pipeline
3. Embedding storage in graph
4. Path-based retrieval API

### Tier 1.2: Hierarchical Attention
**Time:** 20-24 hours
**Deliverables:**
1. Multi-level attention mechanism
2. Branch activation system
3. Tree navigator for efficient traversal
4. Explainable retrieval (show activated branches)

---

## 🤖 Sub-Agent Delegation Strategy

### Task 1: Triple Extractor (SUB-AGENT ✓)
**Why Sub-Agent:** Isolated, well-defined task with clear inputs/outputs
**Agent Type:** general-purpose
**Context Needed:**
- Neo4j schema (relationship types: SUPPORTS, CONTRADICTS, HAS_EVIDENCE, etc.)
- Current graph structure (Document → Claims → Evidence)
- Triple format requirements for PyKEEN

**Deliverable:** `backend/rag/triple_extractor.py`
**Interface:**
```python
class TripleExtractor:
    def extract_from_neo4j(self, db) -> List[Tuple[str, str, str]]:
        """Extract (head, relation, tail) triples"""
        pass
```

**Estimated Time:** 2-3 hours (sub-agent working in parallel)

---

### Task 2: KGE Training Pipeline (SUB-AGENT ✓)
**Why Sub-Agent:** Complex ML task, isolated from main codebase
**Agent Type:** general-purpose
**Context Needed:**
- PyKEEN library documentation
- Triple format from Task 1
- Embedding dimension requirements (256-dim)
- Training hyperparameters

**Deliverable:** `backend/rag/kge_trainer.py`
**Interface:**
```python
class KGETrainer:
    def train_transe(self, triples, epochs=100) -> Dict[str, np.ndarray]:
        """Train TransE and return node/relation embeddings"""
        pass
```

**Estimated Time:** 4-6 hours (sub-agent working in parallel)

---

### Task 3: Hierarchical Attention (SUB-AGENT ✓)
**Why Sub-Agent:** Complex ML implementation, self-contained
**Agent Type:** general-purpose
**Context Needed:**
- Attention mechanism theory (hierarchical attention papers)
- Graph structure (tree hierarchy)
- PyTorch implementation patterns

**Deliverable:** `backend/rag/hierarchical_attention.py`
**Interface:**
```python
class HierarchicalAttention:
    def compute_attention_scores(
        self,
        query_embedding: np.ndarray,
        tree_structure: Dict,
        level: int
    ) -> Dict[str, float]:
        """Compute attention scores at specific tree level"""
        pass
```

**Estimated Time:** 6-8 hours (sub-agent working in parallel)

---

### Task 4: Integration & Storage (I HANDLE)
**Why Me:** Requires full system context, touches existing code
**What I'll Do:**
- Store embeddings in Neo4j (add properties to nodes)
- Create unified retrieval API
- Integrate with existing SemanticSimilarity class
- Ensure backward compatibility

**Deliverable:** `backend/rag/unified_retrieval.py`
**Estimated Time:** 4-6 hours (while sub-agents work)

---

### Task 5: Path-Based Retrieval (I HANDLE)
**Why Me:** Requires understanding of both KGE and Neo4j
**What I'll Do:**
- Implement path queries (e.g., find SUPPORTS chains)
- Vector arithmetic for relation embeddings
- Multi-hop reasoning

**Deliverable:** `backend/rag/kge_retrieval.py`
**Estimated Time:** 3-4 hours

---

### Task 6: Tree Navigator (SUB-AGENT or ME)
**Decision:** Start as sub-agent, I'll refine if needed
**What It Does:**
- Efficient tree traversal
- Branch pruning based on attention scores
- Lazy loading of sub-trees

**Deliverable:** `backend/rag/tree_navigator.py`
**Estimated Time:** 3-4 hours

---

### Task 7: Benchmarking & Testing (I HANDLE)
**Why Me:** Requires full system understanding
**What I'll Do:**
- Create test dataset (synthetic + real queries)
- Benchmark: Current vs KGE vs Hierarchical vs Full
- Measure: Precision@k, Recall@k, latency
- Document results

**Deliverable:** `backend/rag/benchmark.py` + results report
**Estimated Time:** 4-6 hours

---

### Task 8: Settings & UI Integration (I HANDLE)
**Why Me:** Frontend integration
**What I'll Do:**
- Add retrieval mode selector to settings
- Update API endpoints
- Add explainability UI (show activated branches)

**Estimated Time:** 3-4 hours

---

## 📋 Execution Sequence

### **Sprint 1: Foundation (Parallel Work)**
**Duration:** 6-8 hours

**Sub-Agent 1:** Triple Extractor
- Context: Graph schema documentation
- Start immediately
- Output: Working triple extraction

**Sub-Agent 2:** KGE Training Pipeline (starts after Task 1)
- Context: PyKEEN docs + triples from Task 1
- Output: Training code + embeddings

**Me (Parallel):**
- Design overall architecture
- Set up integration scaffolding
- Prepare Neo4j schema updates
- Write integration tests

**Status Check:** Review sub-agent outputs, provide feedback

---

### **Sprint 2: Hierarchical Components (Parallel Work)**
**Duration:** 8-10 hours

**Sub-Agent 3:** Hierarchical Attention
- Context: Attention theory + graph structure
- Output: Attention mechanism implementation

**Sub-Agent 4 (Optional):** Tree Navigator
- Context: Tree structure + attention scores
- Output: Efficient tree traversal

**Me (Parallel):**
- Integrate KGE embeddings into Neo4j
- Implement path-based retrieval
- Build unified retrieval API
- Test KGE retrieval accuracy

**Status Check:** Review sub-agent outputs, integrate into system

---

### **Sprint 3: Integration & Polish**
**Duration:** 6-8 hours

**Me:**
- Integrate all components
- End-to-end testing
- Benchmarking against current system
- Bug fixes & optimization
- Settings UI
- Documentation

**Deliverables:**
- Working KGE + Hierarchical Attention system
- Benchmark results
- Updated API
- User-facing settings

---

### **Sprint 4: Validation & Handoff**
**Duration:** 4-6 hours

**Me:**
- Run comprehensive test suite
- Performance profiling
- Documentation
- Demo preparation
- Commit all changes

**User Review:**
- Show benchmark results
- Demo new retrieval capabilities
- Get feedback

---

## 🎛️ Context Management Strategy

### For Sub-Agents:
**Provide:**
- Specific file references (not entire files)
- Interface requirements (input/output specs)
- Example usage
- Relevant documentation links

**Don't Provide:**
- Full codebase dumps
- Unrelated system details
- My internal thought process

### For Me:
**Track:**
- Sub-agent progress (check outputs regularly)
- Integration points between components
- Overall system state
- Todo list updates

**Delegate When:**
- Task is isolated (clear boundaries)
- Task is well-defined (clear success criteria)
- Task doesn't require full system context
- Sub-agent can work in parallel

**Keep When:**
- Task touches multiple system components
- Task requires architectural decisions
- Task needs full context understanding
- Integration/testing work

---

## 📊 Progress Tracking

### Todos will be updated as:
```
[in_progress] RAG MVP Sprint 1: Foundation (Sub-agents: Triple + KGE)
[in_progress] RAG MVP Sprint 1: Integration scaffolding (Me)
[pending] RAG MVP Sprint 2: Hierarchical Attention
[pending] RAG MVP Sprint 3: Integration & Testing
[pending] RAG MVP Sprint 4: Validation
```

### Success Criteria:
- [ ] KGE embeddings stored in Neo4j
- [ ] Path-based queries working (e.g., find SUPPORTS chains)
- [ ] Hierarchical attention activates correct branches
- [ ] Retrieval 2x better than current system (measured)
- [ ] Backward compatible (basic mode still works)
- [ ] Settings UI allows mode selection
- [ ] Documentation complete

---

## 🚀 Next: Phase B (After Phase A Success)

### Animation Phase 1-2 (22-30 hours)
**Will delegate:**
- Agent position tracking system (isolated)
- D3.js animation library integration (visual)
- WebSocket event system (well-defined)

**I'll handle:**
- Architecture & coordination
- Backend WebSocket server
- Frontend integration
- User experience testing

---

## 🎯 Starting Now

**Immediate Actions:**
1. Update todo list with Sprint 1 tasks
2. Launch Sub-Agent 1 (Triple Extractor)
3. Begin integration scaffolding work
4. Monitor sub-agent progress
5. Prepare for Sub-Agent 2 (KGE Trainer)

**Expected Completion:**
- Sprint 1: 6-8 hours
- Sprint 2: 8-10 hours
- Sprint 3: 6-8 hours
- Sprint 4: 4-6 hours
**Total: 24-32 hours** (faster than estimate due to parallelization)

---

**Let's begin! 🚀**
