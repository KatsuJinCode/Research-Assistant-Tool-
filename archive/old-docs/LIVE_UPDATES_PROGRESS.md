# Live Updates Implementation Progress

## ✅ COMPLETED - Backend Event Emissions

### Changes Made to `web_ui/document_processor.py`

1. **Added `import time`** for timing measurements
2. **Completely rewrote `_simplify_claim_with_agent()`** to implement full 4-stage pipeline:
   - **Stage 1: Analysis** - Deep understanding of claim
   - **Stage 2: Clarification** - Make implicit meaning explicit
   - **Stage 3: Simplification** - Generate 3 optimal candidates
   - **Stage 4: Validation** - Fidelity + Quality scoring

3. **Real-Time Event Emissions**:
   - Emits `claim_stage_update` with `status='in_progress'` at start of each stage
   - Emits `claim_stage_update` with `status='complete'` + data at end of each stage
   - Emits `claim_complete` with final results
   - All events include `doc_id` and `claim_id` for tracking

4. **Timing Data**: Each stage records duration in milliseconds:
   - `duration_analysis_ms`
   - `duration_clarification_ms`
   - `duration_simplification_ms`
   - `duration_validation_ms`
   - `duration_total_ms`

5. **Updated Method Signature**:
   ```python
   def _simplify_claim_with_agent(self, claim_text: str, claim_id: str = None, doc_id: str = None, max_retries: int = 2)
   ```
   Added `doc_id` parameter to enable event tracking.

6. **Updated Call Site** (line 1268-1272):
   ```python
   simplification_result = self._simplify_claim_with_agent(
       claim_data['text'],
       claim_id=claim_id,
       doc_id=doc_id
   )
   ```

## ✅ COMPLETED - Neo4j Schema Updated

### Enhanced Claim Node Structure

Updated claim nodes to store **complete processing history** (lines 1274-1322):

```python
claim_node = {
    'id': claim_id,

    # Display text (what user sees in graph)
    'text': simplification_result['summary'],

    # Complete processing chain (for details view)
    'original_text': claim_data['text'],
    'analysis': simplification_result['analysis'],
    'clarified': simplification_result['clarified'],

    # All 3 candidates
    'candidate_1': simplification_result['candidate_1'],
    'candidate_2': simplification_result['candidate_2'],
    'candidate_3': simplification_result['candidate_3'],

    # Fidelity scores
    'score_1': simplification_result['score_1'],
    'score_2': simplification_result['score_2'],
    'score_3': simplification_result['score_3'],
    'fidelity_reason': simplification_result['fidelity_reason'],
    'selected_candidate': simplification_result['selected_candidate'],

    # Quality assessment
    'quality_score': simplification_result['quality_score'],
    'quality_reason': simplification_result['quality_reason'],
    'disposition': simplification_result['disposition'],
    'recommendation': simplification_result['recommendation'],

    # Timing data (milliseconds)
    'duration_analysis_ms': ...,
    'duration_clarification_ms': ...,
    'duration_simplification_ms': ...,
    'duration_validation_ms': ...,
    'duration_total_ms': ...,

    # Processing status
    'processing_stage': ...,

    # Word counts
    'word_count_original': ...,
    'word_count_final': ...,

    # Metadata
    'parent_super_claim': ...,
    'claim_type': ...,
    'confidence': ...,
    'is_optimal': ...
}
```

## 🔄 IN PROGRESS - Frontend SocketIO Handlers

### Existing Structure

Frontend uses modular JavaScript architecture:
- `web_ui/static/js/app.js` - Main application, socket handlers
- `web_ui/static/js/graph.js` - Graph rendering (D3.js)
- `web_ui/static/js/ui.js` - UI updates
- `web_ui/static/js/api.js` - API calls

### Existing Socket Handlers (in app.js)

Already implemented:
- `processing_update` - General progress updates
  - `document_created` - Document node added
  - `super_claim_added` - Category/super-claim added
  - `claim_added` - Sub-claim added
  - `processing_complete` - Document finished

### NEXT STEPS - Add New Event Handlers

Need to add to `app.js` in the `initializeSocket()` method:

```javascript
// Track claim processing states
this.claimStates = {};

this.socket.on('claim_stage_update', (data) => {
    const { claim_id, stage, status, data: stageData } = data;

    // Initialize claim state if needed
    if (!this.claimStates[claim_id]) {
        this.claimStates[claim_id] = {
            stages: {
                analysis: { status: 'pending' },
                clarification: { status: 'pending' },
                simplification: { status: 'pending' },
                validation: { status: 'pending' }
            },
            allData: {}
        };
    }

    // Update stage status
    this.claimStates[claim_id].stages[stage] = { status, ...stageData };
    this.claimStates[claim_id].allData[stage] = stageData;

    // Update UI visualization
    UI.updateClaimStageVisualization(claim_id, stage, status, stageData);
});

this.socket.on('claim_complete', (data) => {
    const { claim_id, final_text, quality_score, disposition, total_duration_ms } = data;

    // Finalize claim visualization
    UI.finalizeClaimNode(claim_id, {
        text: final_text,
        qualityScore: quality_score,
        disposition: disposition,
        totalDuration: total_duration_ms,
        ...this.claimStates[claim_id]
    });
});
```

## 📋 TODO - UI Components

### 1. Stage Visualization Indicators

Add to claim nodes in graph:

```html
<div class="claim-stages">
    <div class="stage analysis" data-status="complete">
        <div class="stage-icon">📊</div>
    </div>
    <div class="stage clarification" data-status="in_progress">
        <div class="stage-icon pulsing">✏️</div>
    </div>
    <div class="stage simplification" data-status="pending">
        <div class="stage-icon">🔍</div>
    </div>
    <div class="stage validation" data-status="pending">
        <div class="stage-icon">✓</div>
    </div>
</div>
```

### 2. Quality Badge

```html
<div class="quality-badge" data-quality="high">
    <span class="score">0.85</span>
    <span class="disposition">CENTRAL</span>
</div>
```

Quality levels:
- **HIGH** (0.7-1.0): Green badge, "CENTRAL" disposition
- **MEDIUM** (0.4-0.69): Orange badge, "CHILD" disposition
- **LOW** (0.0-0.39): Red badge, "REVIEW" or "DISCARD" disposition

### 3. Expandable Details Panel

Click on claim → show modal/sidebar with:
- Original text (word count)
- Analysis (word count, duration)
- Clarified text (word count, duration)
- All 3 candidates with fidelity scores
- Selected candidate highlighted
- Quality assessment with reason
- Disposition and recommendation
- Total processing time

### 4. CSS Styling Needed

```css
/* Stage indicators */
.claim-stages {
    display: flex;
    gap: 10px;
}

.stage[data-status="pending"] {
    opacity: 0.3;
}

.stage[data-status="in_progress"] {
    background: #e3f2fd;
    border: 2px solid #2196f3;
}

.stage[data-status="complete"] {
    background: #e8f5e9;
    border: 2px solid #4caf50;
}

.stage-icon.pulsing {
    animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Quality badges */
.quality-badge[data-quality="high"] {
    background: #4caf50;
    color: white;
}

.quality-badge[data-quality="medium"] {
    background: #ff9800;
    color: white;
}

.quality-badge[data-quality="low"] {
    background: #f44336;
    color: white;
}
```

## 📊 Event Flow Example

### User Uploads Document

1. **Backend**: Flask receives file → `LiveDocumentProcessor.process_document()`
2. **Backend**: Extracts claims, creates categories
3. **For each claim**:

   **Stage 1: Analysis (15.2s)**
   ```javascript
   // Emitted: claim_stage_update
   {
       doc_id: "abc123",
       claim_id: "claim_001",
       stage: "analysis",
       status: "in_progress",
       data: { original_text: "...", word_count: 15 }
   }

   // Emitted: claim_stage_update
   {
       stage: "analysis",
       status: "complete",
       data: { analysis: "...", word_count: 123, duration_ms: 15234 }
   }
   ```

   **Stage 2: Clarification (13.4s)**
   ```javascript
   // in_progress → complete
   ```

   **Stage 3: Simplification (14.9s)**
   ```javascript
   // in_progress → complete
   {
       data: {
           candidate_1: "...",
           candidate_2: "...",
           candidate_3: "...",
           duration_ms: 14892
       }
   }
   ```

   **Stage 4: Validation (11.2s)**
   ```javascript
   // in_progress → complete
   {
       data: {
           fidelity_scores: { score_1: 0.75, score_2: 0.70, score_3: 0.80 },
           best_candidate: 3,
           fidelity_reason: "...",
           quality_score: 0.85,
           quality_reason: "...",
           disposition: "central",
           recommendation: "...",
           duration_ms: 11234
       }
   }
   ```

   **Final: Completion**
   ```javascript
   // Emitted: claim_complete
   {
       doc_id: "abc123",
       claim_id: "claim_001",
       final_text: "Neurological defects cannot explain belief",
       quality_score: 0.85,
       disposition: "central",
       total_duration_ms: 54783
   }
   ```

4. **Frontend**: Updates graph node with final text, quality badge, stage indicators

## 🎯 Implementation Priorities

1. ✅ **Backend event emissions** - DONE
2. ✅ **Neo4j schema updates** - DONE
3. 🔄 **Frontend socket handlers** - IN PROGRESS
4. ⏳ **UI components** - PENDING
5. ⏳ **CSS styling** - PENDING
6. ⏳ **End-to-end testing** - PENDING

## 🧪 Testing Plan

1. Start Neo4j: `powershell -ExecutionPolicy Bypass -File start_neo4j.ps1`
2. Start Flask backend: `cd web_ui && python app.py`
3. Open browser: `http://localhost:5000`
4. Upload test document
5. Watch console for event emissions
6. Verify graph updates in real-time
7. Click claim node → verify details panel shows all processing data

## 📝 Key Design Decisions

1. **Complete Data Preservation**: Every claim node stores entire processing history
2. **Real-Time Events**: SocketIO events for each stage transition
3. **Timing Transparency**: All durations recorded for user visibility
4. **Quality Scoring**: 0.7+ = central, 0.4-0.69 = child, <0.4 = review/discard
5. **Label vs Details**: Graph shows simplified text as label, details panel shows everything
