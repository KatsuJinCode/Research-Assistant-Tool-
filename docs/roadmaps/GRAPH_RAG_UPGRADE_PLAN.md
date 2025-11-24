# Graph RAG Architecture Upgrade Plan
**Status:** Planning
**Priority:** HIGH - Core Intelligence Layer

---

## 🔍 Current Architecture Analysis

### What We Have ✅

1. **Graph Database**: Neo4j with rich relationship types
   - SUPPORTS, CONTRADICTS, SIMILAR_TO, HAS_EVIDENCE
   - Hierarchical structure (super-claims → sub-claims)
   - Document → Claims → Evidence chains

2. **Basic Embeddings**: Sentence-Transformers
   - Model: `all-MiniLM-L6-v2` (384 dimensions)
   - Simple cosine similarity
   - Thresholds: Identical (0.95), Similar (0.85), Related (0.70)

3. **Semantic Clustering**: Basic similarity-based grouping
   - DBSCAN clustering
   - Manual threshold tuning

### What We're Missing ❌

1. **No Graph Neural Networks (GNNs)**
   - Not encoding graph structure into embeddings
   - Missing relationship-aware embeddings

2. **No Knowledge Graph Embeddings (KGE)**
   - Not using TransE, RotatE, or similar methods
   - Edge types not represented in embedding space

3. **No Hierarchical Attention**
   - Flat retrieval (all claims treated equally)
   - Not exploiting tree structure for efficient search

4. **No Structure-Aware Retrieval**
   - Can't follow paths like: Claim → SUPPORTS → Evidence → CITES → Paper
   - Missing multi-hop reasoning capability

5. **No Tree-Structured Encoding**
   - Hierarchical claim structure not propagated in embeddings
   - Parent-child relationships ignored during retrieval

---

## 🎯 Proposed Upgrades

### **Tier 1: Foundation (Immediate Impact)**

#### 1.1 Knowledge Graph Embeddings (KGE) Layer
**Implementation:** Add TransE/RotatE embeddings for structured retrieval

**What It Does:**
- Learns vector representations for **both nodes AND edges**
- Example: `embedding(Claim_A) + embedding(SUPPORTS) ≈ embedding(Evidence_B)`
- Enables path-based queries: "Find evidence that supports this claim"

**Libraries:**
- PyKEEN (PyTorch Knowledge Graph Embedding library)
- DGL-KE (Deep Graph Library for KGE)
- AmpliGraph

**Architecture:**
```
Neo4j Graph → Extract triples → Train KGE model → Store embeddings

Triple format:
(Claim_A, SUPPORTS, Claim_B)
(Claim_X, HAS_EVIDENCE, Evidence_Y)
(Doc_1, CONTAINS, Claim_Z)
```

**Retrieval Example:**
```python
# Old way (text similarity only):
similar_claims = find_by_text_similarity(query_embedding)

# New way (structure-aware):
related_claims = find_by_path_similarity(
    query_embedding,
    path_types=['SUPPORTS', 'HAS_EVIDENCE'],
    max_hops=2
)
```

**Time Estimate:** 16-20 hours
**Impact:** 40-60% better retrieval precision

---

#### 1.2 Hierarchical Attention for Claim Trees
**Implementation:** Multi-level attention mechanism

**What It Does:**
- **Level 1 Attention**: Choose relevant document/super-claim branches
- **Level 2 Attention**: Focus on specific sub-claims within chosen branch
- **Level 3 Attention**: Extract precise evidence/quotes

**Architecture:**
```
Query →
  ├─ Attend to Super-Claims (select top-k branches)
  │   ├─ Super-Claim A (score: 0.9) ✓
  │   ├─ Super-Claim B (score: 0.7) ✓
  │   └─ Super-Claim C (score: 0.3) ✗
  │
  └─ For each selected branch:
      ├─ Attend to Sub-Claims (within branch)
      │   ├─ Sub-Claim A1 (score: 0.95) ✓
      │   └─ Sub-Claim A2 (score: 0.4) ✗
      │
      └─ Extract evidence from selected sub-claims
```

**Benefits:**
- **Efficiency**: Only process 10-20% of graph instead of 100%
- **Precision**: Focus on relevant branches first
- **Explainability**: Show which branches were activated

**Libraries:**
- Hugging Face Transformers (attention mechanisms)
- Custom attention layer in PyTorch

**Time Estimate:** 20-24 hours
**Impact:** 3-5x faster retrieval, better precision

---

### **Tier 2: Advanced (Power Features)**

#### 2.1 Graph Neural Networks (GNNs)
**Implementation:** R-GNN for relationship-aware node embeddings

**What It Does:**
- Propagates information through graph structure
- Learns: "Claims connected by SUPPORTS are more similar than claims connected by CONTRADICTS"
- Generates context-aware embeddings (claim embedding changes based on neighbors)

**Architecture:**
```
Message Passing:
Claim_A receives messages from:
  ├─ Parent claim (via CONTAINS)
  ├─ Supporting evidence (via HAS_EVIDENCE)
  ├─ Related claims (via SIMILAR_TO)
  └─ Contradicting claims (via CONTRADICTS)

Aggregation:
embedding(Claim_A) = f(
    self_embedding,
    messages_from_neighbors,
    edge_types
)
```

**Libraries:**
- PyTorch Geometric (PyG) - most popular
- Deep Graph Library (DGL)
- Spektral (TensorFlow-based)

**Models to Consider:**
- **R-GCN** (Relational Graph Convolutional Network) - handles different edge types
- **GAT** (Graph Attention Networks) - learns importance of neighbors
- **GraphSAGE** - efficient for large graphs

**Time Estimate:** 24-32 hours
**Impact:** State-of-the-art retrieval, relational reasoning

---

#### 2.2 Sparse Attention / Localized Retrieval
**Implementation:** Graph-constrained attention patterns

**What It Does:**
- Instead of attending to ALL claims, only attend to:
  - Direct neighbors in graph (1-hop)
  - Claims within same document
  - Claims in path to root (ancestors)

**Efficiency Gains:**
```
Full attention: O(N²) where N = all claims
Sparse attention: O(N × k) where k = avg neighbors (~5-10)

Example: 10,000 claims
  Full: 100,000,000 comparisons
  Sparse: 50,000 - 100,000 comparisons
  Speedup: 1000-2000x faster
```

**Implementation:**
```python
def sparse_retrieval(query_embedding, graph):
    # Step 1: Find top-k seed claims (coarse search)
    seed_claims = find_k_nearest_neighbors(query_embedding, k=10)

    # Step 2: Expand to neighbors in graph (fine search)
    candidate_claims = set()
    for seed in seed_claims:
        candidate_claims.update(graph.get_neighbors(
            seed,
            edge_types=['SUPPORTS', 'HAS_EVIDENCE'],
            max_depth=2
        ))

    # Step 3: Rank candidates using full attention
    ranked = rank_by_relevance(query_embedding, candidate_claims)
    return ranked
```

**Time Estimate:** 12-16 hours
**Impact:** Massive speedup for large graphs (1000x+)

---

#### 2.3 Tree-Structured LSTMs
**Implementation:** TreeLSTM for hierarchical claim encoding

**What It Does:**
- Encodes entire claim tree as single vector
- Information flows both bottom-up (child → parent) and top-down (parent → child)
- Learns: "Parent claim is summary of children"

**Architecture:**
```
Document: "AI will transform healthcare"
  ├─ Super-Claim 1: "AI improves diagnosis"
  │   ├─ Sub-Claim 1a: "CNN accuracy > 95% on X-rays"
  │   └─ Sub-Claim 1b: "Reduces false negatives by 30%"
  └─ Super-Claim 2: "AI reduces costs"
      └─ Sub-Claim 2a: "Automation saves $100k/year"

TreeLSTM encodes:
- Bottom-up: Sub-claim embeddings → Super-claim embeddings
- Top-down: Document context → influences sub-claim interpretation
```

**Use Case:**
- Query: "How does AI improve medical imaging?"
- TreeLSTM: Activates Super-Claim 1 branch, retrieves 1a and 1b
- Result: Focused, hierarchically-coherent answer

**Libraries:**
- DGL (Deep Graph Library) has TreeLSTM implementation
- PyTorch Geometric

**Time Estimate:** 16-20 hours
**Impact:** Better hierarchical reasoning, coherent multi-claim answers

---

## 🏗️ Proposed Architecture (After Upgrades)

### Layered Embedding System:

```
Level 1: Text Embeddings (CURRENT)
  ├─ Sentence-Transformers (all-MiniLM-L6-v2)
  └─ 384-dim vectors for raw text

Level 2: Knowledge Graph Embeddings (NEW - Tier 1)
  ├─ TransE/RotatE
  ├─ Learns (node, relation, node) triples
  └─ 256-dim vectors for structured relationships

Level 3: Graph Neural Network Embeddings (NEW - Tier 2)
  ├─ R-GCN or GAT
  ├─ Context-aware embeddings (same claim, different context)
  └─ 512-dim vectors with neighborhood information

Level 4: Hierarchical Tree Embeddings (NEW - Tier 2)
  ├─ TreeLSTM
  ├─ Encodes entire claim subtrees
  └─ 256-dim vectors for hierarchical coherence
```

### Hybrid Retrieval Pipeline:

```
Query: "Find evidence that AI improves medical diagnosis"

Step 1: Coarse Search (Text Embeddings)
  ├─ Find top-50 semantically similar claims
  └─ Fast approximate search (FAISS/Annoy)

Step 2: Structural Filtering (KGE)
  ├─ Filter to claims with HAS_EVIDENCE relationships
  ├─ Follow SUPPORTS paths
  └─ Prune to top-20 candidates

Step 3: Graph-Aware Ranking (GNN)
  ├─ Re-rank using neighborhood context
  ├─ Boost claims with strong supporting evidence
  └─ Top-10 results

Step 4: Hierarchical Coherence (TreeLSTM)
  ├─ Ensure selected claims form coherent tree
  ├─ Include parent/child claims for context
  └─ Final top-5 results with full context
```

---

## 📊 Expected Performance Improvements

### Retrieval Quality:
| Metric | Current | Tier 1 | Tier 2 |
|--------|---------|--------|--------|
| Precision@5 | 60% | 80% | 90% |
| Recall@5 | 50% | 70% | 85% |
| Path-based queries | N/A | 75% | 90% |
| Multi-hop reasoning | N/A | N/A | 80% |

### Efficiency:
| Operation | Current | Tier 1 | Tier 2 |
|-----------|---------|--------|--------|
| Search 1000 claims | 200ms | 100ms | 10ms |
| Search 10,000 claims | 2000ms | 500ms | 50ms |
| Multi-hop query | N/A | 300ms | 80ms |

---

## 🛠️ Implementation Plan

### Phase 1: KGE Foundation (Tier 1.1)
**Time:** 16-20 hours
**Deliverables:**
1. Extract graph triples from Neo4j
2. Train TransE embeddings
3. Store embeddings in graph (new property: `kge_embedding`)
4. Implement path-based retrieval
5. Benchmarking vs. current system

**Files to Create:**
- `backend/rag/knowledge_graph_embeddings.py`
- `backend/rag/triple_extractor.py`
- `backend/rag/kge_retrieval.py`

**Dependencies:**
```bash
pip install pykeen torch
```

---

### Phase 2: Hierarchical Attention (Tier 1.2)
**Time:** 20-24 hours
**Deliverables:**
1. Multi-level attention mechanism
2. Branch activation system
3. Explainable retrieval (show which branches activated)
4. Integration with existing retrieval API

**Files to Create:**
- `backend/rag/hierarchical_attention.py`
- `backend/rag/tree_navigator.py`

**Dependencies:**
```bash
pip install transformers torch
```

---

### Phase 3: GNN Layer (Tier 2.1)
**Time:** 24-32 hours
**Deliverables:**
1. R-GCN model for claim graph
2. Training pipeline (update embeddings as graph grows)
3. Context-aware similarity search
4. Neighborhood-aware ranking

**Files to Create:**
- `backend/rag/graph_neural_network.py`
- `backend/rag/gnn_trainer.py`
- `backend/rag/graph_loader.py`

**Dependencies:**
```bash
pip install torch-geometric dgl
```

---

### Phase 4: Tree-Structured Encoding (Tier 2.3)
**Time:** 16-20 hours
**Deliverables:**
1. TreeLSTM for claim hierarchies
2. Coherent multi-claim retrieval
3. Parent-child context propagation

**Files to Create:**
- `backend/rag/tree_lstm.py`
- `backend/rag/hierarchical_encoder.py`

---

### Phase 5: Sparse Retrieval Optimization (Tier 2.2)
**Time:** 12-16 hours
**Deliverables:**
1. Graph-constrained attention
2. Two-stage retrieval (coarse + fine)
3. Performance benchmarking

**Files to Create:**
- `backend/rag/sparse_retrieval.py`
- `backend/rag/graph_constrained_search.py`

---

## 🎯 Recommended Prioritization

### **MVP (Minimum Viable Product):**
Start with **Phase 1 (KGE)** + **Phase 2 (Hierarchical Attention)**

**Why:**
- Biggest impact for least effort
- Leverages existing graph structure
- No complex training pipelines yet
- **Total Time:** 36-44 hours (~1 week full-time)
- **Expected Improvement:** 40-60% better retrieval

### **Full Power:**
Add **Phase 3 (GNN)** after MVP proves value

**Why:**
- Requires more infrastructure (training pipeline, model management)
- Harder to explain/debug
- But gives state-of-the-art results
- **Additional Time:** 24-32 hours
- **Expected Improvement:** 80-90% precision

### **Optional Enhancements:**
Phases 4 & 5 are optimizations

**When to add:**
- Phase 4 (TreeLSTM): When hierarchical reasoning becomes critical
- Phase 5 (Sparse): When graph has >10,000 claims (performance issue)

---

## 🧪 Evaluation Strategy

### Datasets:
1. **Synthetic Test Set**: Hand-labeled claim relationships
   - 100 queries with ground-truth answers
   - Tests: duplicate detection, SUPPORTS path finding, contradiction detection

2. **Real-World Benchmark**: ArXiv papers on AI safety
   - Extract claims from 50 papers
   - Query set: 25 research questions
   - Measure: Precision@k, Recall@k, NDCG

### Metrics:
- **Precision@5**: % of top-5 results that are relevant
- **Recall@5**: % of relevant items found in top-5
- **Path Accuracy**: % of correctly identified SUPPORTS/CONTRADICTS paths
- **Latency**: Query response time
- **Explainability**: Can we show why results were chosen?

---

## 🔄 Integration with Existing System

### Backward Compatibility:
```python
# backend/rag/unified_retrieval.py
class UnifiedRetrieval:
    def __init__(self, mode='hybrid'):
        """
        mode options:
        - 'basic': Current sentence-transformers only
        - 'kge': Add knowledge graph embeddings
        - 'hybrid': KGE + Hierarchical Attention
        - 'advanced': Full GNN + TreeLSTM stack
        """
        self.mode = mode
        self.text_retriever = SemanticSimilarity()  # Current system

        if mode in ['kge', 'hybrid', 'advanced']:
            self.kge_retriever = KGERetrieval()

        if mode in ['hybrid', 'advanced']:
            self.hierarchical_attention = HierarchicalAttention()

        if mode == 'advanced':
            self.gnn_retriever = GNNRetrieval()
            self.tree_encoder = TreeLSTM()

    def retrieve(self, query, top_k=5):
        if self.mode == 'basic':
            return self.text_retriever.find_similar(query, top_k)

        elif self.mode == 'kge':
            # Two-stage: text + structure
            candidates = self.text_retriever.find_similar(query, top_k * 5)
            return self.kge_retriever.rerank(query, candidates, top_k)

        # ... etc
```

### Settings UI:
```
⚙️ Settings → Advanced Retrieval

  Retrieval Mode:
  ○ Basic (Fastest, current system)
  ○ Structure-Aware (KGE, recommended)
  ● Hierarchical (KGE + Attention, best quality)
  ○ Advanced (GNN, experimental)

  Performance Impact:
  - Basic: 100ms per query
  - Structure-Aware: 150ms per query
  - Hierarchical: 200ms per query
  - Advanced: 300ms per query
```

---

## 📚 Research Papers to Reference

1. **TransE**: "Translating Embeddings for Modeling Multi-relational Data" (Bordes et al., 2013)
2. **RotatE**: "RotatE: Knowledge Graph Embedding by Relational Rotation" (Sun et al., 2019)
3. **R-GCN**: "Modeling Relational Data with Graph Convolutional Networks" (Schlichtkrull et al., 2017)
4. **TreeLSTM**: "Improved Semantic Representations From Tree-Structured LSTM Networks" (Tai et al., 2015)
5. **Hierarchical Attention**: "Hierarchical Attention Networks for Document Classification" (Yang et al., 2016)
6. **Structured RAG**: "Reasoning on Graphs: Faithful and Interpretable Large Language Model Reasoning" (Luo et al., 2023)

---

## ✅ Next Steps

1. **Review & Approve**: User confirms upgrade plan
2. **Start with MVP**: Phase 1 (KGE) + Phase 2 (Hierarchical Attention)
3. **Benchmark**: Compare against current system
4. **Iterate**: Add Tier 2 features if MVP shows clear improvement
5. **Production Deploy**: Make hybrid system default

---

**Total Estimated Time:**
- MVP (Tier 1): 36-44 hours (~1 week)
- Full System (Tier 1 + 2): 88-112 hours (~2.5-3 weeks)

**Expected ROI:**
- 2-3x better retrieval quality
- Enables multi-hop reasoning
- Foundation for future AI capabilities
