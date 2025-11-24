# Semantic Duplicate Detection

## Overview

Automatically detects duplicate claims across multiple documents using semantic embeddings and cosine similarity.

## Features

- **Cross-Document Detection**: Compares new claims against all existing claims from previous documents
- **Semantic Similarity**: Uses sentence-transformers to detect paraphrased duplicates (not just exact matches)
- **Three Match Quality Levels**:
  - `exact`: similarity ≥ 0.95
  - `very_high`: similarity ≥ 0.90
  - `high`: similarity ≥ 0.85 (default threshold)
- **Visual Indicators**: Orange dashed border + ≈ icon on duplicate nodes
- **Dashed Orange Links**: Connect duplicate claims to their originals
- **User Notifications**: Toast notifications inform users of detected duplicates

## Implementation

### Backend Components

1. **`SemanticDuplicateDetector`** (`web_ui/semantic_clustering.py`):
   - Initializes sentence-transformer model (all-MiniLM-L6-v2)
   - `find_duplicates()`: Compares new claims vs existing claims
   - `detect_duplicates_in_set()`: Finds duplicates within a single document
   - Returns matches with similarity scores and quality ratings

2. **Document Processor Integration** (`web_ui/document_processor.py`):
   - Runs duplicate detection at 90% progress (after all claims processed)
   - Fetches all existing claims from other documents
   - Marks duplicate claims in database with metadata
   - Emits `duplicates_found` WebSocket event

### Frontend Components

1. **Graph Visualization** (`web_ui/static/js/graph.js`):
   - `markClaimAsDuplicate()`: Adds visual indicators to duplicate nodes
   - Dashed orange border (3px offset, animated fade-in)
   - ≈ symbol in top-right corner of node
   - Creates "duplicate" type link between claims
   - Updates link colors/styles for duplicate links

2. **WebSocket Event Handler** (`web_ui/static/js/app.js`):
   - Listens for `duplicates_found` event
   - Calls `GraphRenderer.markClaimAsDuplicate()` for each match
   - Shows user notification via `UI.showNotification()`

3. **UI Notifications** (`web_ui/static/js/ui.js`):
   - `showNotification()`: Creates toast notifications
   - Auto-dismisses after 5 seconds
   - Color-coded by type (info=blue, success=green, warning=orange, error=red)

## Configuration

Default similarity threshold: **0.85** (85% semantic similarity)

Adjust threshold in `web_ui/document_processor.py`:
```python
detector = SemanticDuplicateDetector(similarity_threshold=0.85)
```

Lower threshold (e.g., 0.75) catches more paraphrases but may have false positives.
Higher threshold (e.g., 0.95) only catches near-exact duplicates.

## Testing

Comprehensive test suite in `test_duplicate_detection.py`:

```bash
python -m pytest test_duplicate_detection.py -v
```

Tests cover:
- Exact duplicate detection
- Paraphrased duplicate detection
- Non-duplicate filtering
- Empty input handling
- Within-set duplicate detection

All 6 tests pass.

## Database Schema

Duplicate claims have these additional properties:
```python
{
    'has_duplicate': True,
    'duplicate_of': '<existing_claim_id>',
    'duplicate_similarity': 0.92  # 0.0-1.0
}
```

## Usage Example

1. Upload document A containing claim: "Climate change is caused by greenhouse gases"
2. Upload document B containing claim: "Global warming is driven by greenhouse gas emissions"
3. System detects 87% similarity
4. Claim from document B is marked with orange border + ≈ icon
5. Orange dashed line connects to original claim from document A
6. User sees notification: "Found 1 duplicate claim from previous documents"

## Performance

- Model loading: ~2 seconds (first use only, cached thereafter)
- Embedding generation: ~50ms per claim
- Similarity calculation: O(n*m) where n=new claims, m=existing claims
- For 100 new claims vs 1000 existing: ~5 seconds total

## Future Enhancements

- [ ] Duplicate merging UI (combine evidence/metadata)
- [ ] Configurable threshold in UI settings
- [ ] Duplicate cluster visualization (group all similar claims)
- [ ] Show similarity score on hover
- [ ] Option to mark claims as "not duplicate" (false positive handling)
- [ ] Cross-document relationship graph view
