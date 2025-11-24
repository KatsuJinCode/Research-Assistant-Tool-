# Pipeline Architecture Issues & Proposed Solutions

## Date: 2025-11-17
## Status: Needs Discussion & Implementation

---

## Issues Identified

### 1. Document Title Update Not Reflected in Graph
**Status**: FIXED (Commit b455907)
- Backend extracted title but didn't update frontend
- Solution: Added `node_update` event emission + frontend handler

### 2. Pipeline Order is Wrong

**Current Pipeline**:
```
1. Extract text
2. Extract claims (as hierarchical categories)
3. Semantic embedding clustering ← TOO EARLY
4. Process each claim (analyze → clarify → simplify → validate)
5. Add to graph
```

**Problems**:
- We're doing semantic clustering on RAW, unprocessed claims
- We should analyze/clarify claims FIRST, then cluster based on PROCESSED versions
- According to GraphRAG plan, we should use community detection, not upfront clustering

**Correct Pipeline (per GraphRAG Plan)**:
```
1. Extract text
2. Extract raw claims
3. Process EACH claim immediately:
   - Analyze
   - Clarify
   - Simplify
   - Validate
   - ADD TO GRAPH IMMEDIATELY ← Real-time visualization
4. LATER (separate phase): Community detection for categorization
5. LATER: Adjust graph layout based on communities
```

### 3. No Real-Time Graph Population

**Current Behavior**:
- Extract ALL claims
- Cluster ALL claims
- Process ALL claims
- THEN add to graph

**Desired Behavior**:
- Extract claim → Process claim → ADD TO GRAPH immediately
- User sees graph populate in real-time as claims are processed
- Later, claims can be re-organized into communities

---

## Proposed Solution

### Phase 1: Immediate Fixes (Get Frontend Working)

**Goal**: Make graph populate in real-time, 1-to-1 with database

**Changes Needed**:

1. **Remove Premature Clustering** (document_processor.py:1217-1220)
   - Don't call `_extract_and_cluster_claims()`
   - Just call simpler `_extract_claims()` that returns flat list

2. **Process & Add Claims Immediately** (document_processor.py:1300-1390)
   - Loop through claims
   - For each claim:
     - Process with 4-stage pipeline
     - Create node in Neo4j
     - Emit `claim_added` event ← Frontend adds to graph IMMEDIATELY
     - Don't wait for siblings

3. **Keep Super-Claims Simple For Now**
   - Can add super-claim nodes later during community detection
   - For MVP, just add flat claims connected to document

### Phase 2: GraphRAG Community Detection (Later)

**Reference**: GRAPH_RAG_IMPLEMENTATION_PLAN.md Phase 0-2

**Process**:
1. After ALL claims are processed and in graph
2. Run community detection algorithm (Louvain/Leiden)
3. Create super-claim nodes for each community
4. Re-parent claims under appropriate super-claims
5. Emit graph reorganization events ← Frontend animates re-layout

---

## Code Changes Needed

### Change 1: Simplify Claim Extraction (Remove Clustering)

**File**: `web_ui/document_processor.py`

**Before** (lines 1216-1220):
```python
try:
    hierarchical_result, clustering_metrics = self._extract_and_cluster_claims(text)
    categories = hierarchical_result.get('categories', [])
```

**After**:
```python
try:
    # Extract flat list of claims (no clustering yet)
    claims_list = self._extract_claims_flat(text)  # NEW METHOD
```

### Change 2: Process & Add Claims Immediately

**Before** (lines 1248-1390):
```python
# Iterate through categories first
for cat_idx, category in enumerate(categories):
    # Create super-claim
    super_claim_id = str(uuid4())
    # ... create super claim node ...

    # THEN process sub-claims
    for sub_idx, claim_data in enumerate(sub_claims):
        # Process claim
        simplification_result = self._simplify_claim_with_agent(...)
        # Create node
        # Emit event
```

**After**:
```python
# Process each claim immediately
for idx, claim_text in enumerate(claims_list):
    claim_id = str(uuid4())

    # Process claim (4 stages)
    simplification_result = self._simplify_claim_with_agent(
        claim_text,
        claim_id=claim_id,
        doc_id=doc_id,
        claim_index=idx + 1,
        total_claims=len(claims_list)
    )

    # Create node in Neo4j
    claim_node = {
        'id': claim_id,
        'text': simplification_result['summary'],
        'summary': simplification_result['summary'],
        # ... all other fields ...
    }
    self.db.create_node('Claim', claim_node)

    # Link directly to document (no super-claim yet)
    self.db.create_relationship(doc_id, claim_id, 'CONTAINS_CLAIM')

    # Emit IMMEDIATELY so frontend adds to graph
    self._emit(f"Added claim {idx+1}/{len(claims_list)}", progress, {
        'event': 'claim_added',
        'doc_id': doc_id,
        'claim_id': claim_id,
        'node_data': claim_node,  # Frontend needs this to render
        'parent_id': doc_id  # Link to document, not super-claim
    })

    # Small sleep to prevent UI freezing
    socketio.sleep(0)  # Yield to event loop
```

### Change 3: New Method for Flat Extraction

**Add to document_processor.py**:
```python
def _extract_claims_flat(self, text: str) -> List[str]:
    """
    Extract claims as flat list (no clustering/hierarchy).
    Clustering happens later via community detection.
    """
    schema = {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["claims"]
    }

    prompt = f"""Extract all factual claims from this text.
Return a flat list of claims (no categories or hierarchy).

TEXT:
{text}

Return JSON with 'claims' array of claim strings."""

    result = self._invoke_agent_with_structured_output(prompt, schema, "extract-claims")
    return result['claims']
```

---

## Benefits of This Approach

1. **Real-Time Visualization**: Users see claims appear immediately as processed
2. **1-to-1 Database Sync**: Graph always reflects database state exactly
3. **Follows GraphRAG Plan**: Community detection happens separately, as designed
4. **Better UX**: No long wait for entire batch to process before seeing anything
5. **Easier Debugging**: Can see exactly which claim is being processed
6. **Incremental Progress**: Each claim completion is visible progress

---

## Migration Path

### MVP (This Week)
- Implement flat extraction + immediate rendering
- Get real-time graph population working
- Skip super-claims entirely for now

### Phase 1 (Next Week)
- Add community detection as separate backend task
- Run AFTER all claims processed
- Emit reorganization events to frontend

### Phase 2 (Future)
- Full GraphRAG implementation per GRAPH_RAG_IMPLEMENTATION_PLAN.md
- Arbitrary depth hierarchies
- Multi-document analysis
- Investigation trees

---

## Questions for Discussion

1. **Should we keep ANY hierarchy for MVP?**
   - Option A: Flat claims → Document only
   - Option B: Keep categories but make them "tags" not parents

2. **When to run community detection?**
   - Option A: Automatically after each document
   - Option B: On-demand via "Organize Claims" button
   - Option C: Background task that updates periodically

3. **How to handle graph re-organization?**
   - Animate claims moving to new positions?
   - Or just refresh entire graph?

---

## Next Steps

1. Discuss pipeline architecture (this document)
2. Decide on MVP scope
3. Implement flat extraction + immediate rendering
4. Test real-time graph population
5. Commit and merge

---

## References

- **GRAPH_RAG_IMPLEMENTATION_PLAN.md** - Full GraphRAG architecture plan
- **PROGRESS_TRACKING_STATUS.md** - Frontend progress tracking implementation
- **Commit b455907** - Document title update fix
- **Commit 96f9f55** - Summary field bug fix
