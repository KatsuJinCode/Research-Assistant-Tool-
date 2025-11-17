# Live Updates Implementation Plan

## Overview

Implement real-time visualization of the 4-stage claim processing pipeline in the frontend, showing users exactly what's happening as agents analyze, clarify, simplify, and validate each claim.

---

## Backend Changes (web_ui/document_processor.py)

### Current Event Flow
```python
socketio.emit('progress', {
    'doc_id': doc_id,
    'message': 'Processing...',
    'progress': 50
})
```

### New Event Structure

Each stage should emit detailed progress events:

```python
# Stage 1: Analysis Starting
socketio.emit('claim_stage_update', {
    'doc_id': doc_id,
    'claim_id': claim_id,
    'stage': 'analysis',
    'status': 'in_progress',
    'message': 'Analyzing claim for deep understanding...',
    'data': {
        'original_text': claim_text,
        'word_count': len(claim_text.split())
    }
})

# Stage 1: Analysis Complete
socketio.emit('claim_stage_update', {
    'doc_id': doc_id,
    'claim_id': claim_id,
    'stage': 'analysis',
    'status': 'complete',
    'message': 'Analysis complete',
    'data': {
        'analysis': analysis_text,
        'word_count': len(analysis_text.split()),
        'duration_ms': 15234
    }
})

# Stage 2: Clarification
socketio.emit('claim_stage_update', {
    'doc_id': doc_id,
    'claim_id': claim_id,
    'stage': 'clarification',
    'status': 'in_progress'|'complete',
    'data': {
        'clarified': clarified_text,
        'duration_ms': 13421
    }
})

# Stage 3: Simplification
socketio.emit('claim_stage_update', {
    'doc_id': doc_id,
    'claim_id': claim_id,
    'stage': 'simplification',
    'status': 'in_progress'|'complete',
    'data': {
        'candidate_1': "text",
        'candidate_2': "text",
        'candidate_3': "text",
        'duration_ms': 14892
    }
})

# Stage 4: Validation
socketio.emit('claim_stage_update', {
    'doc_id': doc_id,
    'claim_id': claim_id,
    'stage': 'validation',
    'status': 'complete',
    'data': {
        'fidelity_scores': [0.82, 0.89, 0.78],
        'best_candidate': 2,
        'fidelity_reason': "...",
        'quality_score': 0.85,
        'quality_reason': "...",
        'disposition': 'central',
        'recommendation': "...",
        'duration_ms': 11234
    }
})

# Final: Claim Complete
socketio.emit('claim_complete', {
    'doc_id': doc_id,
    'claim_id': claim_id,
    'final_text': selected_candidate,
    'quality_score': 0.85,
    'disposition': 'central',
    'total_duration_ms': 54783
})
```

---

## Frontend Changes (web_ui/templates/index.html)

### Visual Elements

1. **Processing Status Panel**
   - Show current stage for each claim
   - Progress bar for each stage
   - Real-time stage transitions

2. **Claim Node Enhancement**
   ```
   ┌─────────────────────────────────────────┐
   │  Claim Node                       [0.85]│  ← Quality score badge
   │  "Neurological defects cannot..."       │
   │                                          │
   │  ● Analysis    ● Clarification          │  ← Stage indicators
   │  ● Simplified  ● Validated              │
   │                                          │
   │  Status: CENTRAL                        │  ← Disposition
   └─────────────────────────────────────────┘
   ```

3. **Stage Visualization**
   - Each stage shows as icon/indicator
   - Animated transitions between stages
   - Color coding:
     - Gray: Not started
     - Blue pulsing: In progress
     - Green: Complete
     - Red: Failed

4. **Expandable Details**
   ```
   Click claim → Show modal/panel with:

   ┌─────────────────────────────────────────────┐
   │  Claim Processing Details                   │
   ├─────────────────────────────────────────────┤
   │                                              │
   │  Original (15 words):                        │
   │  "A person's belief cannot be explained..."  │
   │                                              │
   │  ✓ Analysis (123 words) - 15.2s             │
   │    This claim makes a negative epistemic... │
   │    [Show Full]                               │
   │                                              │
   │  ✓ Clarification (11 words) - 13.4s         │
   │    Belief cannot be reduced to or fully...  │
   │                                              │
   │  ✓ Simplification - 14.9s                   │
   │    1. [0.75] Beliefs cannot be explained... │
   │    2. [0.70] Belief transcends neurological│
   │    3. [0.80] Neurological defects cannot..  │ ← Selected
   │                                              │
   │  ✓ Validation - 11.2s                       │
   │    Quality: 0.85 (HIGH)                     │
   │    Disposition: CENTRAL                     │
   │    Reason: Specific philosophical claim...  │
   │                                              │
   │  Total: 54.8s                               │
   └─────────────────────────────────────────────┘
   ```

---

## Implementation Steps

### Phase 1: Backend Event Emission

1. Modify `_analyze_claim()` to emit start/end events
2. Modify `_clarify_claim()` to emit start/end events
3. Modify `_simplify_claim_candidates()` to emit start/end events
4. Modify `_validate_final()` to emit start/end events
5. Emit final `claim_complete` event

### Phase 2: Frontend SocketIO Handlers

```javascript
socket.on('claim_stage_update', (data) => {
    updateClaimStage(data.claim_id, data.stage, data.status, data.data);
});

socket.on('claim_complete', (data) => {
    finalizeClaimNode(data.claim_id, data);
    updateGraph();
});
```

### Phase 3: UI Components

1. **Stage Indicator Component**
   - Shows 4 dots/icons for 4 stages
   - Updates color based on status
   - Animates transitions

2. **Quality Badge Component**
   - Shows score (0.0-1.0)
   - Color coded: Green (≥0.7), Yellow (0.4-0.69), Red (<0.4)
   - Shows disposition text

3. **Details Modal/Panel**
   - Expandable section showing all stages
   - Formatted text display
   - Timing information

### Phase 4: Graph Updates

1. **Node Creation Timeline**
   - Create node immediately when claim extracted (gray/pending)
   - Update node as stages complete (color transitions)
   - Final state shows quality and disposition

2. **Visual Progression**
   ```
   [Gray placeholder]
     ↓ Analysis starts
   [Blue pulsing - analyzing]
     ↓ Analysis complete
   [Light blue - clarifying]
     ↓ Clarification complete
   [Blue - simplifying]
     ↓ Simplification complete
   [Blue - validating]
     ↓ Validation complete
   [Green/Yellow/Red based on quality score]
   ```

---

## Technical Details

### SocketIO Events

| Event Name | Direction | Purpose |
|------------|-----------|---------|
| `claim_stage_update` | Server → Client | Update stage progress |
| `claim_complete` | Server → Client | Claim fully processed |
| `processing_stats` | Server → Client | Overall stats (optional) |

### Data Flow

```
User uploads document
  ↓
Flask processes file
  ↓
Extract claims
  ↓
For each claim:
  ├─ Create placeholder node → emit to frontend
  ├─ Stage 1: Analysis
  │    ├─ emit(stage='analysis', status='in_progress')
  │    ├─ perform analysis
  │    └─ emit(stage='analysis', status='complete', data={...})
  ├─ Stage 2: Clarification
  │    ├─ emit(stage='clarification', status='in_progress')
  │    ├─ perform clarification
  │    └─ emit(stage='clarification', status='complete', data={...})
  ├─ Stage 3: Simplification
  │    ├─ emit(stage='simplification', status='in_progress')
  │    ├─ generate candidates
  │    └─ emit(stage='simplification', status='complete', data={...})
  ├─ Stage 4: Validation
  │    ├─ emit(stage='validation', status='in_progress')
  │    ├─ validate candidates
  │    └─ emit(stage='validation', status='complete', data={...})
  └─ emit('claim_complete', data={final result})
```

---

## Example Output

### During Processing

```
Document: szasz_claims.txt [Processing]

Claim 1: [●●●○] "Neurological defects cannot..."
         Stage 3/4 - Simplifying
         Quality: Pending

Claim 2: [●○○○] "The study suggests that some..."
         Stage 1/4 - Analyzing
         Quality: Pending

Claim 3: [●●●●] "Brain disease theory gains..."
         Complete - 0.80 HIGH (CENTRAL)
```

### After Processing

```
Document: szasz_claims.txt [Complete]

Claim 1: [●●●●] "Neurological defects cannot explain belief"
         Complete - 0.85 HIGH (CENTRAL)
         Click for details

Claim 2: [●●●●] "Regular use by some may correlate..."
         Complete - 0.35 LOW (REVIEW)
         Click for details

Claim 3: [●●●●] "Brain disease theory gains evidential support..."
         Complete - 0.80 HIGH (CENTRAL)
         Click for details
```

---

## Files to Modify

1. `web_ui/document_processor.py` - Add event emissions
2. `web_ui/templates/index.html` - Add UI components
3. `web_ui/static/js/main.js` - Add SocketIO handlers (if exists)
4. `web_ui/static/css/style.css` - Add styling (if exists)

---

## Success Criteria

- [x] User sees claims appear immediately when extracted
- [x] User sees stage-by-stage progress for each claim
- [x] User sees quality scores and dispositions
- [x] User can click claim to see full details
- [x] Graph updates in real-time without refresh
- [x] Processing times displayed for each stage
- [x] Visual distinction between high/medium/low quality claims

---

## Next Steps

1. Read current index.html to understand existing structure
2. Implement backend event emissions
3. Update frontend SocketIO handlers
4. Add UI components for stage visualization
5. Test end-to-end with sample document
