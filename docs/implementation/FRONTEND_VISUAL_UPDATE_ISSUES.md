# Frontend Visual Update Issues - Root Cause Analysis

## Date: 2025-11-17
## Status: ROOT CAUSE IDENTIFIED

---

## Problem Summary

After successfully processing all claims through the 4-stage pipeline:
1. **Backend**: All claims processed successfully ✓
2. **Database**: All claims stored correctly with proper relationships ✓
3. **Events**: All WebSocket events emitted correctly ✓
4. **Frontend During Processing**: Claims appear but don't connect or update ✗
5. **Frontend After Refresh**: Claims disappear completely ✗

---

## Root Cause: Schema Mismatch

The `/api/graph` endpoint (`get_full_graph()` in app.py:208-308) expects the **OLD schema** but we're creating claims with the **NEW schema**.

### OLD Schema (Expected by get_full_graph):
```python
# app.py:221-232
{
    'id': str,
    'text': str,
    'summary': str,
    'normalized': str,              # ← WE DON'T HAVE THIS
    'specificity': float,            # ← WE DON'T HAVE THIS (we have specificity_score)
    'is_super_claim': bool,          # ← WE DON'T SET THIS
    'category_description': str,     # ← WE DON'T HAVE THIS
    'quality_score': float,
    'claim_type': str,
    'confidence': float,
    'child_ids': List[str]
}
```

### NEW Schema (What We're Creating):
```python
# document_processor.py:1361-1376
{
    'id': str,
    'text': str,                     # Updated with summary after processing
    'summary': str,
    'status': str,                   # ← NEW: 'processing' or 'complete'
    'processing_stage': str,         # ← NEW: 'pending', 'analysis', etc.
    'disposition': str,              # ← NEW: 'central', 'child', 'review', 'discard'
    'quality_score': float,
    'recommendation': str,           # ← NEW
    'analysis': str,                 # ← NEW
    'clarified': str,                # ← NEW
    'candidate_1': str,              # ← NEW
    'score_1': float,                # ← NEW
    # ...many more NEW fields
    'confidence': float,
    'claim_type': str
}
```

---

## Database Diagnostic Results

```
1. Documents: 1 document (status='complete') ✓
2. Claims: 4 claims with:
   - status='complete' ✓
   - disposition='central' or 'child' ✓
   - summary=<simplified text> ✓
3. CONTAINS_CLAIM relationships: 4 relationships ✓
```

**The database is correct!** Claims ARE stored with all processed data.

---

## Why Claims Disappear on Refresh

1. Page loads → calls `/api/graph`
2. `get_full_graph()` queries claims with:
   ```cypher
   MATCH (c:Claim)
   RETURN c.normalized as normalized, ...
   ```
3. Our claims don't have `normalized` field → returns `None`
4. Frontend receives claims with `normalized: null`
5. Frontend's `updateGraphSmooth()` (graph.js) likely filters or fails on these

---

## Why Claims Don't Update During Processing

Two separate issues:

###Issue 1: Missing `disposition` in get_full_graph
The query doesn't select `disposition`, so even if claims load, they won't have the color info.

### Issue 2: Frontend event handling
Even though `claim_updated` events ARE being emitted, the frontend's `updateClaimNode()` (graph.js:766-823) tries to update nodes that may not exist yet or may not have proper `data-node-id` attributes.

---

## Fixes Needed

### Fix 1: Update get_full_graph() Query (app.py:218-233)

**Current**:
```python
claims_query = """
MATCH (c:Claim)
OPTIONAL MATCH (c)-[r:HAS_SUB_CLAIM]->(child:Claim)
RETURN
    c.id as id,
    c.text as text,
    c.summary as summary,
    c.normalized as normalized,           # ← REMOVE (doesn't exist)
    c.specificity_score as specificity,   # ← RENAME (we don't have this)
    c.is_super_claim as is_super_claim,   # ← ADD DEFAULT (we don't set this)
    c.category_description as category_description,  # ← REMOVE (doesn't exist)
    c.quality_score as quality_score,
    c.claim_type as claim_type,
    c.confidence as confidence,
    collect(child.id) as child_ids
"""
```

**Fixed**:
```python
claims_query = """
MATCH (c:Claim)
OPTIONAL MATCH (c)-[r:HAS_SUB_CLAIM]->(child:Claim)
RETURN
    c.id as id,
    c.text as text,
    c.summary as summary,
    c.status as status,                   # ← ADD (for processing state)
    c.disposition as disposition,         # ← ADD (for color)
    c.quality_score as quality_score,
    c.claim_type as claim_type,
    c.confidence as confidence,
    coalesce(c.is_super_claim, false) as is_super_claim,  # ← DEFAULT to false
    collect(child.id) as child_ids
"""
```

### Fix 2: Update Claim Data Building (app.py:281-293)

**Current**:
```python
claim_data = {
    'id': claim['id'],
    'text': claim['text'],
    'summary': claim['summary'],
    'normalized': claim['normalized'],        # ← REMOVE
    'specificity': claim['specificity'],      # ← REMOVE
    'is_super_claim': claim['is_super_claim'],
    'category_description': claim['category_description'],  # ← REMOVE
    'quality_score': claim['quality_score'],
    'claim_type': claim['claim_type'],
    'confidence': claim['confidence'],
    'child_ids': [cid for cid in claim['child_ids'] if cid]
}
```

**Fixed**:
```python
claim_data = {
    'id': claim['id'],
    'text': claim['text'],
    'summary': claim['summary'],
    'status': claim.get('status', 'complete'),        # ← ADD
    'disposition': claim.get('disposition', 'child'), # ← ADD
    'quality_score': claim.get('quality_score'),
    'claim_type': claim.get('claim_type', 'extracted'),
    'confidence': claim.get('confidence', 0.0),
    'is_super_claim': claim['is_super_claim'],
    'child_ids': [cid for cid in claim['child_ids'] if cid]
}
```

### Fix 3: Update Frontend Graph Rendering (graph.js)

The frontend needs to handle the new `disposition` and `status` fields when building initial graph.

**In `updateGraphSmooth()` (around line 350-450)**:
- Map `disposition` to colors (central=green, child=blue, review=orange, discard=red)
- Use `status` to determine opacity (processing=0.6, complete=1.0)

---

## Testing Plan

1. Apply fixes to app.py
2. Restart Flask server
3. Refresh page → verify claims appear
4. Upload new document → verify real-time updates work
5. Check browser console for errors

---

## Files to Modify

1. **web_ui/app.py** (lines 218-233, 281-293)
   - Update claims_query to select correct fields
   - Update claim_data building to use correct fields

2. **web_ui/static/js/graph.js** (updateGraphSmooth method)
   - Add disposition → color mapping
   - Add status → opacity handling

---

## References

- **REALTIME_SYNC_AUDIT.md** - Real-time sync philosophy
- **IMMEDIATE_CLAIM_RENDERING.md** - Two-phase rendering implementation
- **web_ui/document_processor.py:1260-1390** - Claim creation with NEW schema
- **Diagnostic output** - Confirmed claims exist with correct data
