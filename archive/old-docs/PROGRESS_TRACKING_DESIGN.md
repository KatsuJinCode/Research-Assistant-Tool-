# Progress Tracking UI Design

## Problem Statement

Users need comprehensive visibility into document processing progress, especially when:
- Multiple documents are queued for processing
- Each document has multiple claims being processed
- Each claim goes through 4 stages (analysis, clarification, simplification, validation)
- Processing can take 40-60 seconds per claim

**Current Issues**:
1. Live graph updates show nodes without proper linkages (requires refresh)
2. No visibility into how many claims will be processed
3. No per-claim progress tracking
4. No document queue visibility
5. No activity log to understand what's happening

## Proposed Solution

### 1. Document Queue Panel (Top Priority)

**Location**: Right sidebar, collapsible

**Features**:
- Shows queued documents with status: `queued`, `processing`, `complete`, `error`
- For processing documents: shows current claim being processed (e.g., "Claim 3/15")
- Queue position indicator (e.g., "2 documents ahead")
- Allow clicking to expand/collapse details

**Visual**:
```
┌─ Document Queue ─────────────────────┐
│ 📄 research_paper.pdf                │
│    ● Processing (Claim 3/15)          │
│    Progress: ██████░░░░░░ 20%        │
│                                       │
│ 📄 another_doc.pdf                   │
│    ⏳ Queued (2nd in line)            │
│                                       │
│ 📄 completed_doc.pdf                 │
│    ✓ Complete (12 claims processed)  │
└───────────────────────────────────────┘
```

### 2. Claim Progress Tracker (High Priority)

**Location**: Right sidebar, below document queue

**Features**:
- Appears when document processing starts
- Shows ALL claims that will be processed (extracted count)
- Each claim is a checkbox item that gets checked off when complete
- Shows current stage for each in-progress claim
- Color-coded by status: pending (gray), processing (blue), complete (green), error (red)

**Visual**:
```
┌─ research_paper.pdf ─────────────────┐
│ Extracting claims... Found 15        │
│                                       │
│ ✓ Claim 1: "Mental illness derives..." │
│ ✓ Claim 2: "Neurological defects..."  │
│ ⟳ Claim 3: "The concept of illness..." │
│   ├─ ✓ Analysis                        │
│   ├─ ✓ Clarification                   │
│   ├─ ⟳ Simplification (in progress)    │
│   └─ ⏳ Validation                      │
│ ☐ Claim 4: "Is there such a thing..." │
│ ☐ Claim 5: "Many people today take..." │
│ ... (10 more)                          │
└────────────────────────────────────────┘
```

### 3. Terminal-Style Activity Log (Medium Priority)

**Location**: Bottom panel, collapsible, max height with scroll

**Features**:
- Real-time log of all processing steps
- Timestamped entries
- Color-coded by event type (info, success, warning, error)
- Auto-scrolls to bottom
- Searchable/filterable
- Can be minimized to save space

**Visual**:
```
┌─ Activity Log ───────────────────────────────────────────┐
│ [16:30:15] ℹ️ Document uploaded: research_paper.pdf      │
│ [16:30:16] ℹ️ Extracting text from PDF... (78 pages)     │
│ [16:30:22] ✓ Text extraction complete                    │
│ [16:30:22] ℹ️ Extracting claims...                       │
│ [16:30:35] ✓ Found 15 claims                             │
│ [16:30:35] ℹ️ Starting claim processing (claim_001)      │
│ [16:30:36] ℹ️ Stage 1/4: Analysis...                     │
│ [16:30:51] ✓ Analysis complete (15.2s)                   │
│ [16:30:51] ℹ️ Stage 2/4: Clarification...                │
│ [16:31:04] ✓ Clarification complete (13.4s)              │
│ [16:31:04] ℹ️ Stage 3/4: Simplification...               │
│ [16:31:19] ✓ Simplification complete (14.9s)             │
│ [16:31:19] ℹ️ Stage 4/4: Validation...                   │
│ [16:31:30] ✓ Validation complete (11.2s)                 │
│ [16:31:30] ✓ Claim complete: "Mental illness derives..." │
│ [16:31:30] ℹ️ Starting claim processing (claim_002)      │
│ ... (auto-scroll to bottom)                              │
└──────────────────────────────────────────────────────────┘
```

### 4. Enhanced Progress Bar (Low Priority)

**Location**: Top of main area, below header

**Features**:
- Shows overall document processing progress
- Displays: "Processing claim 3 of 15 (20%)"
- Shows current stage within claim
- Smooth animated transitions

**Visual**:
```
┌──────────────────────────────────────────────────────────┐
│ Processing research_paper.pdf                            │
│ Claim 3/15 - Simplification (Stage 3/4)                 │
│ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 20%      │
└──────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Backend Events (1-2 hours)
- [ ] Add event: `claims_extracted` with count
- [ ] Modify existing events to include:
  - `claim_index` (1-based)
  - `total_claims`
  - `claim_text_preview` (first 50 chars)
- [ ] Add event: `document_queued` for multi-upload support
- [ ] Add document queue management in backend

### Phase 2: Document Queue UI (1 hour)
- [ ] Create queue panel HTML/CSS
- [ ] Add SocketIO handlers for queue events
- [ ] Implement queue rendering logic
- [ ] Add expand/collapse functionality

### Phase 3: Claim Progress Tracker (2 hours)
- [ ] Create claim tracker HTML/CSS with checkboxes
- [ ] Add stage indicators (4 dots/icons per claim)
- [ ] Implement real-time claim state updates
- [ ] Add checkbox animation on completion
- [ ] Color-code by status

### Phase 4: Activity Log (1 hour)
- [ ] Create log panel HTML/CSS
- [ ] Add log entry creation function
- [ ] Implement auto-scroll
- [ ] Add timestamp formatting
- [ ] Color-code by log level
- [ ] Add minimize/maximize toggle

### Phase 5: Enhanced Progress Bar (30 mins)
- [ ] Update existing progress bar
- [ ] Add claim counter display
- [ ] Add stage indicator

### Phase 6: Integration & Testing (1 hour)
- [ ] Wire all components together
- [ ] Test with single document
- [ ] Test with multiple documents
- [ ] Test error handling
- [ ] Verify UI responsiveness

## Data Structure

### Backend Events

```python
# When claims extracted
socketio.emit('claims_extracted', {
    'doc_id': 'abc123',
    'total_claims': 15,
    'claim_previews': [
        {'id': 'claim_001', 'preview': 'Mental illness derives its main...'},
        {'id': 'claim_002', 'preview': 'Neurological defects cannot...'},
        # ... all claims
    ]
})

# When processing claim
socketio.emit('claim_stage_update', {
    'doc_id': 'abc123',
    'claim_id': 'claim_001',
    'claim_index': 1,  # NEW
    'total_claims': 15,  # NEW
    'claim_preview': 'Mental illness derives...',  # NEW
    'stage': 'analysis',
    'status': 'in_progress'
})

# When document queued (for multi-upload)
socketio.emit('document_queued', {
    'doc_id': 'xyz789',
    'filename': 'another_doc.pdf',
    'queue_position': 2,
    'queue_length': 3
})
```

### Frontend State

```javascript
App.documentQueue = [
    {
        id: 'abc123',
        filename: 'research_paper.pdf',
        status: 'processing',
        current_claim: 3,
        total_claims': 15,
        progress: 20
    },
    {
        id: 'xyz789',
        filename: 'another_doc.pdf',
        status: 'queued',
        queue_position: 2
    }
];

App.claimTracker = {
    'abc123': {
        total_claims: 15,
        claims: [
            {
                id: 'claim_001',
                preview: 'Mental illness derives...',
                status: 'complete',
                stages: {
                    analysis: 'complete',
                    clarification: 'complete',
                    simplification: 'complete',
                    validation: 'complete'
                }
            },
            {
                id: 'claim_002',
                preview: 'Neurological defects...',
                status: 'processing',
                stages: {
                    analysis: 'complete',
                    clarification: 'complete',
                    simplification: 'in_progress',
                    validation: 'pending'
                }
            }
            // ... more claims
        ]
    }
};

App.activityLog = [
    { timestamp: 1700000000, level: 'info', message: 'Document uploaded: research_paper.pdf' },
    { timestamp: 1700000001, level: 'success', message: 'Text extraction complete' },
    // ... more entries
];
```

## CSS Styling Notes

- Use monospace font for activity log (terminal feel)
- Use smooth transitions for progress bars
- Use subtle animations for checkboxes
- Make panels collapsible with smooth slide animation
- Use consistent color scheme:
  - Info: #2196F3 (blue)
  - Success: #4CAF50 (green)
  - Warning: #FF9800 (orange)
  - Error: #F44336 (red)
  - Pending: #757575 (gray)

## Mobile Responsiveness

- Stack panels vertically on small screens
- Make activity log full-width on mobile
- Reduce claim preview text length on mobile
- Hide queue panel by default on mobile (show button to expand)

## Accessibility

- Use proper ARIA labels
- Ensure keyboard navigation works
- Provide screen reader announcements for progress updates
- Use sufficient color contrast
- Support high contrast mode
