# MECE Knowledge Graph Architecture

## Core Problem
Currently using arbitrary similarity thresholds (70% for "related", 85% for "duplicate") which is:
- **Non-semantic**: Arbitrary percentages don't reflect actual logical relationships
- **Non-MECE**: No guarantee claims are Mutually Exclusive, Comprehensively Exhaustive
- **Fragile**: Thresholds need manual tuning per domain

## Correct Approach: Graph-Based MECE Clustering

### Phase 1: Full Context Extraction (200K tokens = ~600 pages)

**Current (WRONG)**:
- CHUNK_SIZE = 7,000 characters (~1.5 pages)
- Only sees tiny fragments of document

**Correct**:
- **Claude Sonnet 4.5**: 200K tokens = ~150K words = ~600K characters
- **Actual usable**: ~400K-500K characters for document + prompt overhead
- **Chunk size**: 400K characters (~100 pages) per extraction pass
- **For 600-page document**: 6 passes maximum, not 100+ tiny chunks

**Token Math**:
- 1 token ≈ 4 characters (English text)
- 200K tokens = 800K characters (theoretical max)
- Leave ~200K-300K for prompt, response, safety margin
- **Use: 500K characters per chunk**

### Phase 2: MECE Directive in Extraction Prompt

The extraction agent must be instructed to find **structurally complete** claims:

```
Your task: Extract ALL research claims from this document section.

CRITICAL MECE Requirements:
1. MUTUALLY EXCLUSIVE: Each claim should represent ONE distinct idea
   - No overlap in scope between claims
   - If two claims seem related, extract their common parent claim AND specific child claims

2. COMPREHENSIVELY EXHAUSTIVE: Extract EVERY substantive claim
   - Don't skip "obvious" or "minor" claims
   - Include methodological, theoretical, empirical, and interpretive claims
   - Preserve the document's logical structure

3. HIERARCHICAL: Identify natural parent-child relationships
   - Super-claim: "Machine learning improves medical diagnosis"
   - Sub-claims:
     * "CNNs achieve 95% accuracy on X-ray classification"
     * "Transformers outperform RNNs on clinical notes"

Output 20-50 claims per section. Preserve ALL substantive content.
```

### Phase 3: Semantic Embedding + Graph Community Detection

**Stop using arbitrary similarity thresholds!**

Instead:

1. **Embed all claims** across all documents into vector space
2. **Build similarity graph** where edges = cosine similarity > 0.5 (low threshold)
3. **Use graph algorithms** to find natural clusters:
   - **Louvain method**: Discovers community structure
   - **Leiden algorithm**: Improved resolution, faster
   - **Hierarchical clustering**: Natural tree structure

4. **MECE emerges from graph structure**:
   - Clusters become **super-claims** (high internal similarity)
   - Claims within cluster become **sub-claims** (variations, specifics)
   - Cross-document links appear naturally (same cluster = related)

### Phase 4: Super-Claim Generation via LLM

For each discovered cluster:

```
You have a cluster of semantically similar claims from multiple documents:

Claim 1 (Doc A): "CNNs achieve 95% accuracy on chest X-rays"
Claim 2 (Doc B): "Deep learning models excel at medical image classification"
Claim 3 (Doc C): "Neural networks outperform traditional methods on radiological diagnosis"

Generate:
1. SUPER-CLAIM: One sentence capturing the shared essence
   → "Deep learning significantly improves medical image diagnosis"

2. MECE RELATIONSHIPS:
   - Claim 1: INSTANCE_OF (specific instantiation)
   - Claim 2: GENERALIZATION (broader statement)
   - Claim 3: COMPARISON (contrasts with alternatives)

3. UNIQUE ASPECTS: What each claim adds beyond overlap
   - Claim 1: Specific accuracy metric (95%), specific modality (chest X-ray)
   - Claim 2: General applicability claim
   - Claim 3: Comparative framing against baselines
```

## Proposed Implementation

### 1. Document Processor Updates

**File**: `web_ui/document_processor.py`

```python
class LiveDocumentProcessor:
    # Context window config (tokens)
    CLAUDE_SONNET_CONTEXT = 200_000  # tokens
    CHARS_PER_TOKEN = 4  # conservative estimate
    MAX_CHARS = 500_000  # 125K tokens for document, rest for prompt/response

    def _extract_flat_claims_with_agent(self, text: str):
        """Extract claims using FULL context window."""

        # Most documents fit in one pass!
        if len(text) <= self.MAX_CHARS:
            return self._extract_claims_single_pass(text)

        # Large documents: 3-6 chunks (not 100!)
        chunks = self._intelligent_chunking(
            text,
            chunk_size=400_000,  # ~100 pages
            overlap=50_000  # ~10 pages overlap
        )

        all_claims = []
        for chunk in chunks:
            claims = self._extract_claims_single_pass(chunk)
            all_claims.extend(claims)

        # Lightweight deduplication (exact matches only)
        return self._deduplicate_exact(all_claims)
```

### 2. MECE Clustering Engine

**New File**: `research_agent/mece_clustering.py`

```python
class MECEClusterEngine:
    """
    Discovers natural MECE structure using graph community detection.
    NO arbitrary thresholds - structure emerges from data.
    """

    def discover_structure(self, claims: List[Claim]) -> MECEGraph:
        # 1. Embed all claims
        embeddings = self.embed_claims(claims)

        # 2. Build similarity graph (edges = similarity > 0.5)
        G = self.build_similarity_graph(embeddings)

        # 3. Detect communities (Leiden algorithm)
        communities = self.detect_communities(G)

        # 4. For each community, generate super-claim
        mece_structure = []
        for community in communities:
            super_claim = self.generate_super_claim(community.claims)
            mece_structure.append({
                'super_claim': super_claim,
                'sub_claims': community.claims,
                'coherence': community.modularity_score
            })

        return MECEGraph(mece_structure)

    def detect_communities(self, G):
        """Use Leiden algorithm for community detection."""
        import leidenalg
        import igraph as ig

        # Convert to igraph
        ig_graph = ig.Graph()
        ig_graph.add_vertices(len(G.nodes))
        ig_graph.add_edges(list(G.edges))

        # Leiden algorithm (better than Louvain)
        partition = leidenalg.find_partition(
            ig_graph,
            leidenalg.ModularityVertexPartition
        )

        return partition
```

### 3. Integration Flow

```
1. Upload Document
   ↓
2. Extract text (PDF/DOCX/TXT)
   ↓
3. Chunk into 400K-500K character sections (3-6 chunks for most papers)
   ↓
4. Extract claims from each chunk with MECE directive
   → "Extract ALL claims, make them mutually exclusive, be comprehensive"
   ↓
5. Deduplicate exact matches across chunks
   ↓
6. ADD TO GLOBAL CLAIM POOL (all documents together)
   ↓
7. When user requests MECE view OR periodically:
   ↓
8. Run MECE clustering on ENTIRE claim pool:
   - Embed all claims
   - Build similarity graph
   - Detect communities (Leiden algorithm)
   - Generate super-claims for each community
   ↓
9. Create MECE relationships in Neo4j:
   - Claim → IS_INSTANCE_OF → SuperClaim
   - Claim → GENERALIZES → SuperClaim
   - Claim → CONTRASTS_WITH → Claim (different communities)
   ↓
10. Visualize MECE structure
```

## Why This Works

1. **No arbitrary thresholds**: Graph structure emerges naturally
2. **True MECE**: Communities are mathematically optimal partitions
3. **Cross-document**: All claims in same embedding space
4. **Scalable**: Works for 10 documents or 1,000 documents
5. **Explainable**: Modularity scores show cluster quality

## Next Steps

1. Update chunk size to 400K-500K characters
2. Add MECE directive to extraction prompt
3. Implement graph-based clustering (Leiden algorithm)
4. Add super-claim generation step
5. Create MECE relationship types in Neo4j
6. Add "MECE View" toggle in UI

## Libraries Needed

```bash
pip install leidenalg python-igraph scikit-learn
```

## Validation

After clustering, validate MECE properties:

```python
def validate_mece(clusters):
    # Mutual Exclusivity: Low inter-cluster similarity
    for i, c1 in enumerate(clusters):
        for c2 in clusters[i+1:]:
            similarity = cosine_sim(c1.centroid, c2.centroid)
            assert similarity < 0.6, "Clusters overlap!"

    # Comprehensiveness: High coverage of original claims
    assigned_claims = sum(len(c.claims) for c in clusters)
    assert assigned_claims >= 0.95 * total_claims, "Missing claims!"
```
