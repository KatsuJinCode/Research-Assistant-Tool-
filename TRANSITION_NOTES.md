# Transition Notes: From Arbitrary Thresholds to MECE Graph Architecture

## What Changed and Why

### 1. Chunk Size: 7K → 400K characters (57x increase!)

**Problem**: Was only using ~1.5 pages of a 200K token context window
**Fix**: Now using ~100 pages per chunk
**Impact**: 300-page document goes from 100+ chunks to 3-6 chunks

**Evidence**:
- Claude Sonnet 4.5: 200K tokens
- 1 token ≈ 4 characters
- 200K × 4 = 800K characters (theoretical max)
- Use 400K for document (leaves 400K for prompt + response + safety)

**Actual Math**:
- 400,000 chars ÷ 4,000 chars/page = 100 pages per chunk
- 600-page document ÷ 100 pages = 6 chunks (not 200!)

### 2. Extraction Directive: Added MECE Requirements

**Before**:
```
Extract 10-20 claims. Preserve qualifiers.
```

**After**:
```
CRITICAL MECE Requirements:

1. MUTUALLY EXCLUSIVE: Each claim = ONE distinct idea
   - No overlap between claims
   - Extract parent claim AND child claims separately

2. COMPREHENSIVELY EXHAUSTIVE: Extract EVERY substantive claim
   - Don't skip "obvious" claims
   - Include ALL claim types (factual, methodological, causal, interpretive)

Extract 20-50 claims for comprehensive coverage.
```

**Why**: LLM needs explicit instruction to avoid:
- Skipping "minor" claims
- Merging related claims
- Missing edge cases

### 3. Semantic Linking: Thresholds → Graph Communities (Next Phase)

**Current (Temporary)**:
- 70% threshold for "related"
- 85% threshold for "duplicate"
- ❌ **This is wrong and needs to be replaced**

**Correct Approach** (to be implemented):

```python
# WRONG: Arbitrary thresholds
if similarity > 0.85:
    mark_as_duplicate()
elif similarity > 0.70:
    mark_as_related()

# CORRECT: Graph-based clustering
embeddings = embed_all_claims()
G = build_similarity_graph(embeddings, min_sim=0.5)
communities = leiden_algorithm(G)  # Discovers natural clusters

for community in communities:
    super_claim = generate_super_claim(community.claims)
    for claim in community.claims:
        create_relationship(claim, "IS_INSTANCE_OF", super_claim)
```

**Why Graph-Based is Better**:
1. **No Manual Tuning**: Algorithm finds optimal partition
2. **Mathematically Principled**: Maximizes modularity (intra-cluster similarity, inter-cluster dissimilarity)
3. **Hierarchical**: Naturally reveals parent-child structure
4. **Scalable**: Works for 10 documents or 10,000 documents

## Implementation Roadmap

### Phase 1: Foundation (DONE ✅)
- [x] Increase chunk size to 400K chars
- [x] Add MECE directive to extraction prompt
- [x] Document architecture in MECE_ARCHITECTURE.md

### Phase 2: Graph Infrastructure (NEXT)
- [ ] Install graph libraries: `pip install leidenalg python-igraph scikit-learn`
- [ ] Create `research_agent/mece_clustering.py`
- [ ] Implement embedding pipeline (reuse existing sentence-transformers)
- [ ] Implement similarity graph builder
- [ ] Integrate Leiden community detection

### Phase 3: Super-Claim Generation
- [ ] Design super-claim generation prompt
- [ ] Add LLM-based super-claim synthesis
- [ ] Create MECE relationship types in Neo4j:
  - `IS_INSTANCE_OF` (specific example of general claim)
  - `GENERALIZES` (broader framing)
  - `CONTRASTS_WITH` (alternative perspective)
  - `REFINES` (adds nuance/detail)

### Phase 4: UI Integration
- [ ] Add "MECE View" toggle button
- [ ] Visualize super-claims as larger nodes
- [ ] Color-code relationship types
- [ ] Add cluster quality metrics display
- [ ] Show modularity scores

### Phase 5: Validation & Testing
- [ ] Validate MECE properties:
  - Mutual exclusivity: Inter-cluster similarity < 0.6
  - Comprehensiveness: Coverage > 95%
- [ ] Test with multiple related documents
- [ ] Compare against manual clustering (ground truth)

## Migration Path

**Current State**:
- Using temporary 70%/85% thresholds
- Works but not optimal

**Transition**:
1. Keep current system running
2. Implement graph clustering in parallel
3. A/B test both approaches
4. Switch to graph clustering when validated
5. Remove threshold-based code

**Backward Compatibility**:
- Old claims still work
- New MECE relationships added incrementally
- Can run MECE clustering on existing database

## Performance Expectations

### Before (7K chunks):
- 300-page document: ~120 chunks
- Processing time: ~10 minutes (120 agent calls)
- Claim extraction: Incomplete (missed content beyond 8K chars)

### After (400K chunks):
- 300-page document: ~4 chunks
- Processing time: ~2 minutes (4 agent calls)
- Claim extraction: Complete (all 300 pages analyzed)

### Graph Clustering (when implemented):
- 1,000 claims: ~2 seconds (embedding + clustering)
- 10,000 claims: ~20 seconds
- Real-time updates: Not needed (run periodically)

## Key Insights

1. **Context is King**: Using full 200K context dramatically improves extraction quality
2. **Explicit MECE Directive**: LLM needs to be told to be comprehensive
3. **Graph > Thresholds**: Let the data reveal its own structure
4. **Overlap is Good**: 50K char overlap ensures no claims fall through cracks
5. **Quality over Speed**: Taking 30 seconds per chunk to do it right beats rushing with tiny fragments

## Next Immediate Action

Run a test with a large document to validate:
1. Chunks are actually 400K chars (not 7K)
2. Extraction includes MECE directive
3. More claims are extracted per chunk
4. Overlap prevents boundary issues

Then proceed to Phase 2: Graph clustering implementation.
