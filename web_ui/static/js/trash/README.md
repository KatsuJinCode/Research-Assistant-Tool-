# Deprecated/Archived JavaScript Files

This folder contains JavaScript files that have been deprecated or archived to prevent confusion and potential conflicts.

## Files

### property_viewer.js.deprecated
- **Date Moved**: 2025-11-24
- **Reason**: Duplicate implementation of PropertyViewer
- **Details**:
  - This file targets `#detail-panel` and uses methods like `showNodeProperties()`, `renderProperties()`
  - The active version is `property-viewer.js` (hyphen) which targets `#property-viewer-panel` and uses methods like `show()`, `hide()`, `switchTab()`
  - The HTML calls methods from property-viewer.js (hyphen version), so this underscore version was orphaned
  - Both files declaring `const PropertyViewer` caused syntax error: "Identifier 'PropertyViewer' has already been declared"
- **Can be deleted**: Yes, after confirming no issues in production

## Investigation Results: "Orphaned" Files

### agent-builder.js - ✅ KEEP (Not Orphaned)
**Status**: Active, used in separate template
**Location**: Referenced in `web_ui/templates/agent_builder.html`
**Purpose**: Visual drag-and-drop agent builder interface
**Features**:
- No-code agent creation with flow editor canvas
- Pre-built blocks (Input, Output, AI Query, Function, Transform, Condition, Loop, Parallel)
- Test runner for agent validation
- Export to Python code and YAML
- Save/load agent definitions
**Reason not in index.html**: Standalone feature with its own dedicated page

### graph-paginator.js - ⚠️ INVESTIGATE FURTHER
**Status**: Not referenced anywhere in codebase
**Purpose**: Virtual scrolling and lazy loading for large graphs (1000+ nodes)
**Features**:
- Viewport-based rendering (only render visible nodes)
- Level-of-detail (LOD) system based on zoom
- Spatial indexing with QuadTree for fast viewport queries
- Incremental loading (100 nodes at a time)
- Performance optimization for massive graphs
**Potential Actions**:
1. **Keep if planned**: May be for future large-graph optimization
2. **Integrate**: Add to graph.js if needed for performance
3. **Archive**: Move to trash if superseded by current graph rendering

## Review Process

To prevent similar issues:
1. Check for files with both hyphen and underscore versions of the same name
2. Verify which version is referenced in HTML
3. Check for orphaned files not referenced anywhere
4. Look for backup files (.bak, .backup, .old, ~)
5. Search for files with similar names using pattern matching
