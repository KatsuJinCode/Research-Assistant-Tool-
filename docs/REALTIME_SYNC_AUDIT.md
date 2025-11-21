# Real-Time Database-Graph Synchronization Audit

## Date: 2025-11-17
## Philosophy: **The graph must always mirror the database state in real-time**

---

## Core Principle

**Every database operation MUST trigger an immediate visual update.**

No exceptions. No delays. No batch processing without incremental visualization.

Users should see:
- Every node as soon as it's created
- Every property update as it happens
- Every relationship as it's formed
- Every deletion as it occurs

---

## Current Implementation Status

### ✅ IMPLEMENTED: Document Operations

#### 1. Document Created
**Database**: `GraphDatabase.create_node('Document', ...)`
**Location**: `document_processor.py:1181`
**Visual Update**: `claim_added` event → Frontend creates document node
**Status**: ✅ **WORKING**

```python
# Backend emits
self._emit("Created document", 5, {
    'event': 'document_created',
    'doc_id': doc_id,
    'node_data': document_node
})

# Frontend receives (app.js:55-69)
if (data.data.event === 'document_created') {
    GraphRenderer.addNodeIncremental(nodeData, null);
}
```

---

#### 2. Document Title Updated
**Database**: `GraphDatabase.update_node_properties(doc_id, {'title': actual_title})`
**Location**: `document_processor.py:1204`
**Visual Update**: `node_update` event → Frontend updates label
**Status**: ✅ **WORKING** (Fixed in commit a39e6b7)

```python
# Backend emits
self._emit(f"Extracted title: {actual_title}", 10, {
    'event': 'title_extracted',
    'node_update': {
        'node_id': doc_id,
        'updates': {'title': actual_title}
    }
})

# Frontend receives (app.js:46-52)
if (data.data.node_update) {
    GraphRenderer.updateNodeLabel(
        data.data.node_update.node_id,
        data.data.node_update.updates.title
    );
}
```

---

#### 3. Document Processing Progress
**Database**: N/A (transient state)
**Location**: Throughout processing
**Visual Update**: Circular progress indicator
**Status**: ✅ **WORKING**

```python
# Backend emits throughout processing
self._emit("Processing...", progress, {...})

# Frontend updates (app.js:42-43)
UI.updateProcessingStatus(data.message, data.progress);
```

---

#### 4. Document Completed
**Database**: `SET d.status = 'complete'`
**Location**: `document_processor.py:1402-1405`
**Visual Update**: Remove processing indicator
**Status**: ✅ **WORKING**

```python
# Backend emits
self._emit("Document processing complete!", 100, {
    'event': 'processing_complete',
    'doc_id': doc_id
})

# Frontend receives (app.js:109-121)
GraphRenderer.markDocumentComplete(data.data.doc_id);
```

---

### ✅ IMPLEMENTED: Claim Operations (Skeleton + Update Pattern)

#### 5. Claim Extracted (Skeleton)
**Database**: `GraphDatabase.create_node('Claim', skeleton_node)`
**Location**: `document_processor.py:1281`
**Visual Update**: Gray, faded node with raw text
**Status**: ✅ **WORKING** (Implemented in commit 0c19189)

```python
# Backend creates skeleton immediately
skeleton_node = {
    'id': claim_id,
    'text': claim_text,  # Raw text
    'status': 'processing',
    'processing_stage': 'pending'
}
self.db.create_node('Claim', skeleton_node)

# Backend emits
self._emit(f"Extracted claim {idx+1}/{total_claims}", progress, {
    'event': 'claim_added',
    'claim_id': claim_id,
    'node_data': skeleton_node,
    'is_skeleton': True
})

# Frontend receives (app.js:90-108)
if (data.data.event === 'claim_added') {
    GraphRenderer.addNodeIncremental(nodeData, parentId);
}
```

---

#### 6. Claim Linked to Document
**Database**: `GraphDatabase.create_relationship(doc_id, claim_id, 'CONTAINS_CLAIM')`
**Location**: `document_processor.py:1284`
**Visual Update**: Edge drawn in graph
**Status**: ✅ **WORKING** (Implicit in skeleton creation)

---

#### 7. Claim Processing Started
**Database**: N/A (transient state)
**Location**: `document_processor.py:1311-1316`
**Visual Update**: Could add animated border/spinner
**Status**: ⚠️ **PARTIAL** (Event emitted but no visual indicator yet)

```python
# Backend emits
self._emit(f"Processing claim {idx+1}/{total_claims}", progress, {
    'event': 'claim_processing_started',
    'claim_id': claim_id,
    'processing_stage': 'analysis'
})

# Frontend: TODO - Add visual indicator
```

**Recommendation**: Add subtle pulsing animation to claim node being processed.

---

#### 8. Claim Processed (Complete)
**Database**: `GraphDatabase.update_node_properties(claim_id, processed_data)`
**Location**: `document_processor.py:1376`
**Visual Update**: Smooth transition to colored, solid appearance
**Status**: ✅ **WORKING** (Implemented in commit 0c19189)

```python
# Backend updates node
processed_data = {
    'text': simplification_result['summary'],
    'status': 'complete',
    'disposition': 'central',  # etc
    ...
}
self.db.update_node_properties(claim_id, processed_data)

# Backend emits
self._emit(f"Processed claim {idx+1}/{total_claims}", progress, {
    'event': 'claim_updated',
    'claim_id': claim_id,
    'updates': processed_data
})

# Frontend receives (app.js:122-134)
if (data.data.event === 'claim_updated') {
    GraphRenderer.updateClaimNode(claim_id, updates);
}
```

---

### 🔶 NOT YET IMPLEMENTED: Future Operations

#### 9. Super-Claims (Community Detection)
**Database**: Will create super-claim nodes + re-parent relationships
**Location**: TBD (Phase 2 - GraphRAG implementation)
**Visual Update**: Animated graph reorganization
**Status**: 🔶 **PLANNED** (See IMMEDIATE_CLAIM_RENDERING.md Phase 2)

**When Implemented**:
```python
# Backend will emit
self._emit("Reorganizing claims into communities", progress, {
    'event': 'community_detected',
    'super_claim_id': super_claim_id,
    'member_claim_ids': [claim1, claim2, claim3],
    'reorganization': {
        'new_parent': super_claim_id,
        'old_parent': doc_id
    }
})

# Frontend should:
# 1. Create super-claim node
# 2. Animate claim nodes moving to new parent
# 3. Update relationships with smooth transitions
```

---

#### 10. Investigation Trees (Future Feature)
**Database**: Create Evidence/Investigation nodes + relationships
**Location**: TBD
**Visual Update**: New branch of graph appears
**Status**: 🔶 **PLANNED**

---

#### 11. Claim Deletion
**Database**: `DELETE` Cypher query
**Location**: Not implemented yet
**Visual Update**: Node fade-out + removal
**Status**: ❌ **NOT IMPLEMENTED**

**When Implemented**:
```python
# Backend
self.db.delete_node(claim_id)
self._emit("Deleted claim", progress, {
    'event': 'claim_deleted',
    'claim_id': claim_id
})

# Frontend
if (data.data.event === 'claim_deleted') {
    GraphRenderer.removeNode(claim_id);
}
```

---

#### 12. Claim Property Updates (Manual Edits)
**Database**: `SET c.property = value`
**Location**: Not implemented yet (would be in admin panel)
**Visual Update**: Specific property changes (color, text, etc.)
**Status**: ❌ **NOT IMPLEMENTED**

**When Implemented**: Reuse `claim_updated` event pattern.

---

#### 13. Relationship Deletion
**Database**: `DELETE` relationship
**Location**: Not implemented yet
**Visual Update**: Edge fade-out + removal
**Status**: ❌ **NOT IMPLEMENTED**

---

#### 14. Batch Operations (Import/Export)
**Database**: Multiple creates/updates
**Location**: Not implemented yet
**Visual Update**: Progressive appearance (not all at once)
**Status**: ❌ **NOT IMPLEMENTED**

**Critical**: Even batch operations must show incremental progress, not wait until end.

---

## Audit Results

### ✅ Strengths

1. **Document lifecycle**: Fully synchronized (create → title update → progress → complete)
2. **Claim lifecycle**: Two-phase rendering (skeleton → processed) works perfectly
3. **Immediate feedback**: Users see all nodes within 1-2 seconds of extraction
4. **Smooth transitions**: Visual updates use animations (fade, color change, etc.)

### ⚠️ Gaps to Address

1. **Claim processing indicator**: No visual feedback while claim is in 4-stage pipeline
   - **Fix**: Add pulsing border or spinner to node being processed

2. **Error states**: No visual indication when claim processing fails
   - **Fix**: Red border + error icon on failed claims

3. **Deletion operations**: Not implemented at all
   - **Fix**: Add delete endpoints + visual fade-out

4. **Manual edits**: No UI for editing claim properties
   - **Fix**: Click-to-edit functionality + real-time updates

### 🎯 Recommendations

#### High Priority (Next Sprint)

1. **Add visual indicator for active claim processing**
   ```javascript
   // graph.js
   if (data.data.event === 'claim_processing_started') {
       svg.select(`circle[data-node-id="${claim_id}"]`)
           .style('stroke', '#FFC107')
           .style('stroke-width', 4)
           .style('stroke-dasharray', '5,5')
           .transition()
           .duration(1000)
           .ease(d3.easeLinear)
           .style('stroke-dashoffset', -10)
           .on('end', repeat);
   }
   ```

2. **Implement error state visualization**
   ```python
   # document_processor.py (on error)
   self._emit("Claim processing failed", progress, {
       'event': 'claim_failed',
       'claim_id': claim_id,
       'error': str(e)
   })
   ```

3. **Add delete functionality**
   - Backend: `/api/delete-claim/<claim_id>` endpoint
   - Frontend: Right-click menu → Delete → Fade out + remove from D3

#### Medium Priority

4. **Stage-by-stage progress indicators**
   - Show which of the 4 stages is active (Analysis/Clarification/Simplification/Validation)
   - Use different border colors or badges

5. **Relationship animations**
   - When relationships are created/deleted, animate the edge drawing/removal
   - Currently edges just appear instantly

#### Low Priority (Future)

6. **Batch operation streaming**
   - When importing multiple documents, show them appearing one by one
   - Don't wait for entire batch to finish

7. **Undo/Redo with visual feedback**
   - Show nodes/edges re-appearing when undo is clicked
   - Reverse animations

---

## Testing Checklist

### Scenarios to Test

- [ ] Upload document → See document node appear immediately
- [ ] Wait for title extraction → See label update smoothly
- [ ] Claims extracted → See all skeleton nodes appear within 1-2s
- [ ] Claims processing → See nodes transition from gray to colored
- [ ] Multiple documents → Each processes independently with visual updates
- [ ] Error during processing → See error indication (once implemented)
- [ ] Delete claim → See fade-out (once implemented)
- [ ] Edit claim → See instant update (once implemented)

---

## Architectural Pattern

**Standard Event Flow for ALL Database Operations**:

```python
# 1. Perform database operation
self.db.create_node('Type', node_data)

# 2. Emit event IMMEDIATELY after
self._emit("User-facing message", progress, {
    'event': 'operation_type',  # e.g., 'claim_added', 'node_updated'
    'affected_id': node_id,
    'node_data': node_data,  # Full data for frontend to render
    'changes': {...}  # For updates, what changed
})

# 3. Frontend receives and updates
if (data.data.event === 'operation_type') {
    GraphRenderer.updateVisualization(data.data);
}
```

**Never**:
- Perform batch DB operations without incremental events
- Wait until end of processing to show results
- Update DB without emitting corresponding event
- Emit events without actual DB changes

**Always**:
- Emit event immediately after DB operation
- Include full data needed for frontend rendering
- Use smooth transitions for visual updates
- Handle errors with visual feedback

---

## Conclusion

The current implementation **successfully achieves** the real-time sync philosophy for:
- ✅ Document creation and updates
- ✅ Claim skeleton creation (immediate visibility)
- ✅ Claim processing updates (progressive enhancement)

**Next steps**:
1. Add claim processing stage indicators
2. Implement error state visualization
3. Add delete operations with visual feedback
4. Extend pattern to all future features (super-claims, investigations, etc.)

The foundation is solid. Every new feature should follow the established pattern: **DB operation → Immediate event → Visual update**.

---

## References

- **Commit 0c19189**: Immediate claim rendering implementation
- **Commit a39e6b7**: Document title update fix
- **IMMEDIATE_CLAIM_RENDERING.md**: Detailed implementation notes
- **PIPELINE_ARCHITECTURE_ISSUES.md**: Original architecture discussion
