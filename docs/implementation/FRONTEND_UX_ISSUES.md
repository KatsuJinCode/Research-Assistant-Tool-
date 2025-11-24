# Frontend UX Issues - To Fix During Modularization

## Date: 2025-11-17
## Status: DOCUMENTED - Fix in Phase 6 (Frontend Modularization)

---

## Problem Summary

The info card (claim detail panel) has multiple UX issues that need fixing:

### 1. Slow to Appear
**Problem**: Info card takes too long to pop up when selecting a node
**Likely Cause**: Fetching `/api/claim/<id>` on every click instead of using cached graph data
**Fix**: Use data already loaded in graph, only fetch for additional details if needed

### 2. Title Same as Summary
**Problem**: Title field shows exact same text as summary field
**Expected Behavior**:
- **Title**: Original extracted claim text (full, unmodified)
- **Summary**: AI-simplified version (shorter, clearer)

**Current Data Available**:
- `claim.text`: Original full text
- `claim.summary`: Simplified text

**Fix**:
```javascript
document.getElementById('node-title').textContent = claim.text;      // Original
document.getElementById('node-summary').textContent = claim.summary; // Simplified
```

### 3. All Metrics Show 50%
**Problem**: Quality and confidence always show 50% regardless of actual values
**Root Cause**: Hardcoded defaults in HTML:
```html
<div class="confidence-fill" id="confidence-bar-fill" style="width: 50%;"></div>
<div class="confidence-fill" id="investigation-bar-fill" style="width: 50%;"></div>
```

**Available Data**:
- `claim.quality_score`: Actual quality score (0.0-1.0)
- `claim.confidence`: Actual confidence score (0.0-1.0)

**Fix**: Use real data from claim object instead of defaults

### 4. No Full Original Text
**Problem**: Info card doesn't show the original extracted claim text
**Expected**: Always display full original text for reference
**Available**: `claim.text` contains original extraction

**Fix**: Add "Original Text" section to info card displaying `claim.text`

###5. No Timestamps
**Problem**: No indication of when claim was created/processed
**Expected**: Show creation time and last update time
**Missing Data**: Need to add `created_at` and `updated_at` timestamps to claim nodes

**Backend Fix Needed**:
```python
# In document_processor.py when creating claims
claim_data = {
    'id': claim_id,
    'text': text,
    'created_at': datetime.now().isoformat(),
    'updated_at': datetime.now().isoformat(),
    ...
}
```

**Frontend Display**:
```html
<div class="detail-subtitle">Timeline</div>
<div class="detail-item">
    <small>Created: <span id="claim-created"></span></small><br>
    <small>Last Updated: <span id="claim-updated"></span></small>
</div>
```

### 6. Evidence Buttons Do Nothing
**Problem**: "Find Supporting Evidence" and "Find Contradicting Evidence" buttons have no effect
**Current Implementation**: Calls `investigateClaim()` which exists but doesn't work
**Expected**: Should spawn research agent to find evidence

**Function Exists**: `index.html` lines 540-543 call `investigateClaim('support')` or `investigateClaim('contradict')`

**Investigation Needed**:
- Does `/api/investigate-claim` endpoint work?
- Are agents actually spawned?
- Is there any feedback to user?

**Fix Options**:
1. If not implemented: Remove buttons or disable with "Coming Soon"
2. If implemented but broken: Fix agent spawning
3. If working but no feedback: Add status indicators

---

## Recommended Fix Order (Phase 6: Frontend Modularization)

### Step 1: Create ClaimInfoPanel Component
```javascript
// web_ui/static/js/components/ClaimInfoPanel.js
class ClaimInfoPanel {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentClaim = null;
    }

    show(claimData) {
        this.currentClaim = claimData;
        this.render();
    }

    render() {
        // Populate all fields with real data
        this.setTitle(this.currentClaim.text);           // Original text
        this.setSummary(this.currentClaim.summary);       // Simplified
        this.setQuality(this.currentClaim.quality_score);
        this.setConfidence(this.currentClaim.confidence);
        this.setTimestamps(this.currentClaim.created_at, this.currentClaim.updated_at);
        this.setOriginalText(this.currentClaim.text);
    }

    setTitle(text) {
        document.getElementById('node-title').textContent = text;
    }

    setSummary(text) {
        document.getElementById('node-summary').textContent = text || 'No summary available';
    }

    setQuality(score) {
        const percentage = ((score || 0) * 100).toFixed(0);
        document.getElementById('detail-quality').textContent = percentage + '%';
        document.getElementById('quality-bar-fill').style.width = percentage + '%';
    }

    setConfidence(score) {
        const percentage = ((score || 0) * 100).toFixed(0);
        document.getElementById('detail-confidence').textContent = percentage + '%';
        document.getElementById('confidence-bar-fill').style.width = percentage + '%';
    }

    setTimestamps(created, updated) {
        document.getElementById('claim-created').textContent =
            created ? new Date(created).toLocaleString() : 'Unknown';
        document.getElementById('claim-updated').textContent =
            updated ? new Date(updated).toLocaleString() : 'Unknown';
    }

    setOriginalText(text) {
        document.getElementById('original-text').textContent = text;
    }
}
```

### Step 2: Update HTML Template
Add missing sections to `index.html`:
```html
<!-- Original Text Section (after summary) -->
<div class="detail-section">
    <div class="detail-subtitle">📝 Original Extracted Text</div>
    <div class="detail-item">
        <p id="original-text" style="font-style: italic; color: #ccc;"></p>
    </div>
</div>

<!-- Timeline Section (after confidence) -->
<div class="detail-section">
    <div class="detail-subtitle">🕒 Timeline</div>
    <div class="detail-item">
        <small>Created: <span id="claim-created">-</span></small><br>
        <small>Last Updated: <span id="claim-updated">-</span></small>
    </div>
</div>
```

### Step 3: Fix Evidence Buttons
Either implement properly or remove:
```html
<!-- Option 1: Disable until implemented -->
<button class="btn btn-success" disabled title="Coming soon">
    ✓ Find Supporting Evidence
</button>

<!-- Option 2: Implement properly -->
<button class="btn btn-success" onclick="investigateClaim('support')">
    ✓ Find Supporting Evidence
</button>
<!-- Add status indicator -->
<div id="investigation-status" style="display:none;">
    <small>🔄 Agent searching...</small>
</div>
```

### Step 4: Add Timestamps to Backend
Update `document_processor.py` claim creation:
```python
from datetime import datetime

claim_data = {
    'id': claim_id,
    'text': text,
    'summary': summary,
    'created_at': datetime.now().isoformat(),
    'updated_at': datetime.now().isoformat(),
    'status': 'processing',
    'disposition': 'child',
    ...
}
```

Update claim updates to refresh `updated_at`:
```python
db.update_node_properties(claim_id, {
    'summary': summary,
    'disposition': disposition,
    'updated_at': datetime.now().isoformat(),
    ...
})
```

---

## Testing Plan

After fixes:
1. Click a claim node → info card appears instantly (< 200ms)
2. Title shows full original text
3. Summary shows simplified version (different from title)
4. Quality and confidence show real percentages (not always 50%)
5. Original text section displays full extraction
6. Timestamps show creation and last update times
7. Evidence buttons either work or are disabled/removed

---

## References

- User feedback: "Why does the info card take so long to pop up"
- User feedback: "Why is its title always exactly the same as its summary"
- User feedback: "Why do all the metrics have 50%"
- User feedback: "Why is there no full original text"
- User feedback: "Why no timestamp"
- User feedback: "What do the find evidence buttons do they don't seem to have any effect"

---

## Priority: HIGH

These UX issues make the interface confusing and less useful. Fix during Phase 6 (Frontend Modularization) when creating the `ClaimInfoPanel` component.
