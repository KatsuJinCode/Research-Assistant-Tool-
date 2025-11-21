# Quick Reference: New Features

## 🚀 Multi-Document Upload
**How to use**:
- Click upload zone OR drag multiple files
- Supports: PDF, TXT, DOCX
- Files process sequentially with progress tracking

## 🔍 Search & Filter
**Location**: Sidebar, below upload area

**Features**:
- **Search Box**: Type to search claims/documents (debounced 300ms)
- **Node Type Toggles**: Show/hide documents, claims, duplicates
- **Quality Slider**: Filter by quality score (0-100%)
- **Clear Filters**: Reset all filters
- **Focus Results**: Zoom to visible nodes

**Keyboard Shortcuts**:
- Type in search box → instant search
- Ctrl+F → focus search (browser default)

## 🔗 Duplicate Detection
**Automatic**: Runs after each document processes (90% progress)

**Visual Indicators**:
- Orange dashed border on duplicate nodes
- ≈ symbol in top-right corner
- Orange dashed lines to original claims
- Toast notification with count

**Threshold**: 85% semantic similarity (configurable in code)

## 📍 Document Positioning
**Automatic**: New documents spawn away from existing trees
- Minimum 350px separation
- 12 strategic candidate positions
- Selects position with maximum clearance

## 🎨 Visual Legend

### Node Colors:
- **Purple**: Documents
- **Blue**: Claims
- **Green**: High-quality claims (quality ≥ 0.75)
- **Orange**: Low-quality claims (quality < 0.5)
- **Orange border**: Duplicate claim

### Link Types:
- **Solid Purple**: Document → Claim
- **Solid Blue**: Claim → Sub-claim
- **Dashed Orange**: Duplicate relationship
- **Green**: Supports
- **Red**: Contradicts

### Node States:
- **Gold glow**: Newly added (fresh)
- **Pulsing**: Processing
- **"Awaiting summarization..."**: Skeleton node
- **Faded (10% opacity)**: Filtered out

## 🧪 Testing

### Run Unit Tests:
```bash
cd C:\Users\jpswi\Research-Assistant-Tool-
python -m pytest test_duplicate_detection.py test_file_types.py -v
```

**Expected**: 10/10 tests passing

### Manual Testing:
1. Upload 2-3 documents with similar content
2. Watch for duplicate detection notifications
3. Use search to find specific claims
4. Toggle filters to hide/show node types
5. Click "Focus Results" to zoom to filtered nodes

## 📊 Current Stats
**Build**: Check bottom-right of UI
**Test Coverage**: 10/10 unit tests passing
**Features**: 4 major features completed
**Known Issues**: 3 identified (see SESSION_SUMMARY.md)

## 🐛 Known Issues

### 1. Claims not appearing during live processing
**Workaround**: Refresh page after processing completes
**Status**: Under investigation

### 2. Label overlap on crowded graphs
**Workaround**: Use zoom/pan to separate nodes
**Status**: Needs screenshot for diagnosis

### 3. Color inconsistency
**Workaround**: None needed - cosmetic only
**Status**: Under review

## 📚 Documentation
- `SESSION_SUMMARY.md` - Complete session details
- `DUPLICATE_DETECTION.md` - Duplicate detection guide
- `PROJECT_ROADMAP.md` - Future features

## 🔧 Configuration

### Duplicate Detection Threshold:
**File**: `web_ui/document_processor.py` line 470
```python
detector = SemanticDuplicateDetector(similarity_threshold=0.85)
```
- Lower = more duplicates detected (more false positives)
- Higher = fewer duplicates detected (more false negatives)
- Recommended range: 0.75 - 0.90

### Document Spawn Distance:
**File**: `web_ui/static/js/graph.js` line 642
```javascript
const minDistance = 350;  // pixels
```

### Search Debounce:
**File**: `web_ui/static/js/app.js` line 417
```javascript
searchTimeout = setTimeout(() => {
    // search logic
}, 300);  // milliseconds
```

## 💻 Developer Notes

### Adding New File Types:
1. Create extractor: `research_agent/document_processing/xyz_extractor.py`
2. Update processor: `web_ui/document_processor.py` lines 1190-1215
3. Update validation: `web_ui/app.py` line 217
4. Add tests: `test_file_types.py`

### Adding New Node Types:
1. Update color map: `graph.js` `getNodeColor()` line 1005
2. Update radius calculation: `graph.js` `getNodeRadius()` line 986
3. Add filter toggle: `index.html` lines 483-495
4. Update filter logic: `graph.js` `applyFiltersToGraph()` line 1100-1109

### Adding New Link Types:
1. Update color map: `graph.js` `getLinkColor()` line 1005
2. Update width map: `graph.js` `getLinkWidth()` line 541
3. Update dash array: `graph.js` `getLinkDashArray()` line 554

## 🎯 Next Priority Features
1. Fix live claim rendering
2. Semantic search with relevance ranking
3. Manual claim editing UI
4. MECE categorization system
5. arXiv research agent

---

**Last Updated**: 2025-11-20
**Version**: See `web_ui/static/VERSION.json`
