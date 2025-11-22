# Graph RAG Architecture for Intelligent Agents

## Overview

This document describes the Graph RAG (Retrieval-Augmented Generation) system that enhances agent intelligence by providing graph context during claim extraction, analysis, and normalization.

---

## Goals

### Primary Objectives

1. **Better Claim Normalization**
   - Query existing similar claims before creating new ones
   - Reduce duplicates through semantic similarity
   - Improve consistency across claims

2. **Context-Aware Extraction**
   - Agents can reference related works already in the graph
   - Cross-reference claims during extraction
   - Maintain relationships to cited sources

3. **Intelligent Deduplication**
   - Semantic similarity scoring (not just exact text match)
   - Merge similar claims while preserving provenance
   - Suggest consolidation to user

4. **Enhanced Analysis**
   - Use graph context to identify contradictions
   - Find supporting/opposing evidence
   - Detect claim evolution over time

---

## Architecture Components

### 1. RAG Context Builder

**Purpose:** Retrieve relevant graph context for agent prompts

**Location:** `backend/rag/graph_context_builder.py`

```python
class GraphContextBuilder:
    """Build context from knowledge graph for RAG prompts."""

    def get_similar_claims(self, claim_text: str, limit: int = 5) -> List[Claim]:
        """Find existing similar claims using semantic search."""

    def get_document_context(self, document_id: str) -> Dict:
        """Get all claims/evidence from a document."""

    def get_claim_relationships(self, claim_id: str) -> Dict:
        """Get all relationships for a claim (supports, contradicts, etc.)."""

    def build_extraction_context(self, document: Document) -> str:
        """Build context string for claim extraction prompt."""
```

**Key Features:**
- Semantic search using embeddings
- Graph traversal for relationships
- Context formatting for LLM prompts

### 2. Semantic Similarity Engine

**Purpose:** Calculate similarity between claims for deduplication

**Location:** `backend/rag/semantic_similarity.py`

```python
class SemanticSimilarity:
    """Calculate semantic similarity between claims."""

    def __init__(self):
        # Use sentence-transformers for embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""

    def find_duplicates(self, claim_text: str, threshold: float = 0.85) -> List[Claim]:
        """Find potential duplicate claims above similarity threshold."""

    def cluster_similar_claims(self, claims: List[Claim]) -> List[List[Claim]]:
        """Group similar claims into clusters."""
```

**Similarity Thresholds:**
- `>= 0.95`: Almost identical (auto-merge candidate)
- `0.85 - 0.94`: Very similar (suggest merge to user)
- `0.70 - 0.84`: Related (show as related claims)
- `< 0.70`: Different claims

### 3. RAG-Enhanced Agent Prompts

**Purpose:** Inject graph context into agent system prompts

**Location:** `backend/agents/rag_prompts.py`

```python
class RAGPromptBuilder:
    """Build RAG-enhanced prompts for agents."""

    def build_claim_extraction_prompt(
        self,
        document: Document,
        existing_claims: List[Claim],
        related_documents: List[Document]
    ) -> str:
        """Build prompt with graph context for claim extraction."""

    def build_normalization_prompt(
        self,
        raw_claim: str,
        similar_claims: List[Claim]
    ) -> str:
        """Build prompt to normalize claim using similar existing claims."""
```

**Prompt Template Example:**
```
You are extracting claims from a research document.

EXISTING RELATED CLAIMS IN GRAPH:
1. [Claim ID: claim_123] "Machine learning models require large datasets"
   - Confidence: 0.85
   - Evidence count: 3

2. [Claim ID: claim_456] "Deep learning needs substantial training data"
   - Confidence: 0.90
   - Evidence count: 5

TASK:
Extract claims from the new document. If a claim is similar to existing claims above:
- Use consistent language
- Reference the existing claim ID
- Indicate if it supports, contradicts, or refines the existing claim

NEW DOCUMENT EXCERPT:
[document text here]
```

### 4. Claim Deduplication System

**Purpose:** Automatically detect and handle duplicate claims

**Location:** `backend/rag/claim_deduplicator.py`

```python
class ClaimDeduplicator:
    """Detect and handle duplicate claims in the graph."""

    def detect_duplicates(self, project_id: str) -> List[ClaimCluster]:
        """Find all duplicate claim clusters in project."""

    def merge_claims(
        self,
        primary_claim_id: str,
        duplicate_claim_ids: List[str]
    ) -> Claim:
        """Merge duplicate claims, preserving all provenance."""

    def suggest_merges(self, threshold: float = 0.85) -> List[MergeSuggestion]:
        """Suggest claim merges to user for review."""
```

**Merge Strategy:**
- Primary claim = highest confidence or earliest created
- Merge all evidence relationships
- Preserve provenance from all sources
- Mark merged claims with `merged_into` property

---

## Data Flow

### Claim Extraction with RAG

```
1. User uploads PDF document
   ↓
2. Document chunked and analyzed
   ↓
3. RAG Context Builder queries graph:
   - Find similar documents
   - Get existing claims from similar documents
   - Calculate semantic similarity
   ↓
4. Build enhanced extraction prompt:
   PROMPT = base_prompt + graph_context + document_text
   ↓
5. Agent extracts claims with awareness of existing claims:
   - Uses consistent language
   - References similar claims
   - Indicates relationships (supports/contradicts)
   ↓
6. Before creating new claim:
   - Check semantic similarity with existing claims
   - If >0.95 similar → Link instead of create
   - If 0.85-0.94 → Create but suggest merge to user
   - If <0.85 → Create as new claim
   ↓
7. Store claim with metadata:
   - similar_to: [claim_ids]
   - similarity_scores: {claim_id: score}
   - extraction_context: "RAG-enhanced"
```

### Deduplication Workflow

```
1. Background job runs periodically (daily)
   ↓
2. Scan all claims in project
   ↓
3. Calculate pairwise semantic similarity
   ↓
4. Group claims into clusters (threshold: 0.85)
   ↓
5. For each cluster:
   - If auto-merge threshold (>0.95): Merge automatically
   - If review threshold (0.85-0.94): Notify user
   ↓
6. User reviews merge suggestions:
   - Accept: Merge claims
   - Reject: Mark as "reviewed, not duplicates"
   - Edit: Manually adjust normalization
```

---

## Implementation Plan

### Phase 1: Core RAG Infrastructure (Week 1)

**Tasks:**
1. ✅ Create GraphContextBuilder class
2. ✅ Implement semantic similarity engine
3. ✅ Add sentence-transformers dependency
4. ✅ Create claim embedding storage (Neo4j vector index)
5. ✅ Write unit tests for RAG components

**Deliverables:**
- `backend/rag/graph_context_builder.py`
- `backend/rag/semantic_similarity.py`
- Tests with mock data

### Phase 2: Agent Integration (Week 2)

**Tasks:**
1. ✅ Update claim extraction agent prompts
2. ✅ Add RAG context to agent system prompts
3. ✅ Implement pre-extraction similarity check
4. ✅ Add claim relationship detection
5. ✅ Test with real documents

**Deliverables:**
- Enhanced agent prompts
- RAG-aware claim extraction
- Integration tests

### Phase 3: Deduplication System (Week 3)

**Tasks:**
1. ✅ Create ClaimDeduplicator class
2. ✅ Implement merge algorithm
3. ✅ Add background deduplication job
4. ✅ Create UI for merge suggestions
5. ✅ Add user merge review interface

**Deliverables:**
- Automatic deduplication
- User review UI
- Merge history tracking

### Phase 4: Advanced Features (Week 4+)

**Tasks:**
1. ⏳ Cross-project claim search
2. ⏳ Claim evolution tracking
3. ⏳ Contradiction detection using RAG
4. ⏳ Evidence strength analysis
5. ⏳ Citation network visualization

---

## Technical Details

### Embedding Model

**Model:** `sentence-transformers/all-MiniLM-L6-v2`

**Why This Model:**
- Fast inference (100+ sentences/sec)
- Good semantic understanding
- Small model size (~90MB)
- Pre-trained on diverse text

**Alternative:** `all-mpnet-base-v2` (slower but more accurate)

### Neo4j Vector Index

```cypher
// Create vector index for claims
CREATE VECTOR INDEX claim_embeddings
FOR (c:Claim)
ON c.embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
}
```

**Query Similar Claims:**
```cypher
CALL db.index.vector.queryNodes(
  'claim_embeddings',
  5,  // top 5 results
  $embedding
)
YIELD node, score
RETURN node.text, score
ORDER BY score DESC
```

### Caching Strategy

**Embedding Cache:**
- Cache claim embeddings in Neo4j (avoid recalculation)
- Invalidate cache on claim text update
- Background job to pre-compute embeddings

**Context Cache:**
- Cache graph context for 1 hour (Redis/in-memory)
- Invalidate on graph updates
- Per-document cache key

---

## Performance Considerations

### Embedding Generation

**Batch Processing:**
- Process claims in batches of 100
- Parallel embedding generation
- Estimated: 1000 claims in ~10 seconds

### Similarity Search

**Neo4j Vector Index:**
- Sub-millisecond query time
- Scales to millions of claims
- Approximate nearest neighbor (ANN)

### Memory Usage

**Embedding Storage:**
- 384 dimensions × 4 bytes = ~1.5KB per claim
- 10,000 claims = ~15MB
- Acceptable overhead

---

## Example Usage

### Extracting Claims with RAG

```python
from backend.rag.graph_context_builder import GraphContextBuilder
from backend.agents.claim_extractor import ClaimExtractor

# Initialize RAG components
context_builder = GraphContextBuilder(project_id="project_ml")
extractor = ClaimExtractor()

# Get document
document = document_repo.get_by_id("doc_123")

# Build RAG context
similar_claims = context_builder.get_similar_claims_for_document(document)
context = context_builder.build_extraction_context(document, similar_claims)

# Extract claims with context
claims = extractor.extract_claims(
    document=document,
    rag_context=context,
    use_rag=True
)

# Claims will now reference similar existing claims
for claim in claims:
    if claim.similar_to:
        print(f"Similar to existing claim: {claim.similar_to}")
        print(f"Similarity: {claim.similarity_score}")
```

### Finding Duplicates

```python
from backend.rag.claim_deduplicator import ClaimDeduplicator

deduplicator = ClaimDeduplicator(project_id="project_ml")

# Find all duplicate clusters
clusters = deduplicator.detect_duplicates(threshold=0.85)

# Review suggestions
for cluster in clusters:
    print(f"Cluster of {len(cluster.claims)} similar claims:")
    for claim in cluster.claims:
        print(f"  - {claim.text[:50]}... (confidence: {claim.confidence})")

    # Auto-merge if very similar
    if cluster.max_similarity > 0.95:
        merged = deduplicator.merge_claims(cluster.claims)
        print(f"Auto-merged into: {merged.id}")
```

---

## Success Metrics

### Quality Metrics

1. **Deduplication Rate**
   - Target: Reduce duplicates by 80%
   - Measure: % of claims with similarity >0.85

2. **Normalization Consistency**
   - Target: 90% of similar claims use consistent language
   - Measure: Human review of claim clusters

3. **False Positive Rate**
   - Target: <5% of auto-merges are incorrect
   - Measure: User rejection rate of merge suggestions

### Performance Metrics

1. **Extraction Speed**
   - Target: <5% slowdown with RAG enabled
   - Measure: Time to extract claims from 100-page document

2. **Similarity Search Speed**
   - Target: <100ms for top-5 similar claims
   - Measure: Neo4j vector index query time

---

## Future Enhancements

### Phase 5+ (Long-term)

1. **Active Learning**
   - User feedback improves similarity thresholds
   - Learn which merges are accepted/rejected
   - Adaptive confidence scoring

2. **Multi-Project RAG**
   - Search across all user's projects
   - Cross-reference claims from different domains
   - Suggest related research from other projects

3. **Claim Evolution Tracking**
   - Track how claims evolve over time
   - Visualize claim refinement history
   - Identify consensus building

4. **Citation Network Analysis**
   - Build citation graph from document references
   - Identify influential papers
   - Suggest missing citations

---

## Dependencies

### Python Packages

```
sentence-transformers>=2.2.0
numpy>=1.24.0
scikit-learn>=1.3.0
torch>=2.0.0  # For sentence-transformers
```

### Neo4j Requirements

- Neo4j 5.0+ (for vector index support)
- APOC plugin (for graph algorithms)

---

**Document Status:** Design Complete ✅
**Implementation Status:** Ready to Begin
**Next Step:** Implement GraphContextBuilder class
