# Web UI JavaScript Modules

This directory contains the modular JavaScript code for the Research Graph Interface. The code has been separated into focused modules for better maintainability.

## File Structure

```
web_ui/static/js/
├── README.md           # This file - documentation for the JS modules
├── api.js              # Backend API communication
├── graph.js            # D3.js graph visualization
├── ui.js               # User interface interactions
└── app.js              # Main application coordinator
```

## Module Responsibilities

### api.js (75 lines)
**Purpose**: Centralized backend communication layer

**Contains**:
- `fetchGraph()` - Retrieve full graph data (documents → super-claims → sub-claims → evidence)
- `fetchStats()` - Get database statistics (document/claim/evidence counts)
- `fetchClaim(claimId)` - Get detailed information about a specific claim
- `uploadDocument(file)` - Upload and process a new PDF document
- `clearAll()` - Clear all data from the database
- `investigateClaim(claimId, investigationType)` - Launch an agent to investigate a claim

**When to edit**: When adding new API endpoints or modifying backend communication

---

### graph.js (262 lines)
**Purpose**: D3.js force-directed graph rendering and visualization

**Contains**:
- `buildUnifiedGraph(graphData)` - Constructs node/link structure from API data
- `renderGraph(nodes, links)` - Creates and renders D3.js force-directed graph
- `updateGraphSmooth(graphData)` - Smoothly updates graph with new data (no flicker)
- `updateGraphVisuals()` - Refreshes visual elements when data changes
- `getNodeColor(type)` - Returns color for node types (document/super/sub/evidence)
- `getNodeRadius(type)` - Returns size for node types
- `getLinkColor(type)` - Returns color for relationship types
- Drag handlers: `dragStarted`, `dragged`, `dragEnded`

**Current node types**:
- `document` - Green (#4CAF50), radius 25px
- `super` - Blue (#2196F3), radius 20px
- `sub` - Purple (#9C27B0), radius 15px
- `evidence` - Orange (#FF9800), radius 12px

**Current link types**:
- `contains` - Document → Super-claim (gray #888)
- `has_sub` - Super-claim → Sub-claim (dark gray #666)
- `supports` - Claim/Evidence → Claim (green #4CAF50)
- `contradicts` - Evidence → Claim (red #F44336)

**When to edit**:
- Adding new graph visualization features
- Changing node/link appearance
- Implementing new graph layouts or physics
- Adding label overlap detection (TODO)
- Implementing arbitrary depth support (TODO)

---

### ui.js (145 lines)
**Purpose**: User interface interactions and modal dialogs

**Contains**:
- `showClaimDetails(claimId)` - Display claim information in modal
- `closeClaimModal()` - Hide the claim details modal
- `updateStats(stats)` - Update the statistics display (doc/claim/evidence counts)
- `updateProcessingStatus(message, progress)` - Update progress bar and status text
- `showUploadModal()` - Display file upload dialog
- `hideUploadModal()` - Hide file upload dialog
- `handleFileUpload(file)` - Process file upload and show progress
- `confirmClearAll()` - Confirm and execute database clear operation

**Global exports**:
- `window.showClaimDetails` - Made globally accessible for graph click handlers

**When to edit**:
- Adding new modals or dialogs
- Changing how user interactions work
- Adding new dashboard panels (TODO)
- Implementing spider/radar charts (TODO)

---

### app.js (135 lines)
**Purpose**: Main application coordinator and initialization

**Contains**:
- `init()` - Initialize the application on page load
- `initializeSocket()` - Setup WebSocket connection for real-time updates
- `loadGraph()` - Load and render graph data
- `loadStats()` - Load and display statistics
- `setupEventListeners()` - Wire up UI event handlers
- `setupDragAndDrop()` - Enable drag-and-drop file upload (not currently called)

**WebSocket events handled**:
- `connect` - Log connection success
- `processing_update` - Update progress bar during document processing
- `claim_added` - Reload graph when new claim is added
- `document_processed` - Reload graph and stats when processing completes

**When to edit**:
- Adding new initialization steps
- Adding new WebSocket event handlers
- Changing application startup behavior
- Adding new global event listeners

---

## Load Order

The modules are loaded in this specific order in `index.html`:

```html
<script src="{{ url_for('static', filename='js/api.js') }}"></script>
<script src="{{ url_for('static', filename='js/graph.js') }}"></script>
<script src="{{ url_for('static', filename='js/ui.js') }}"></script>
<script src="{{ url_for('static', filename='js/app.js') }}"></script>
```

**Why this order?**
1. **api.js** first - No dependencies, provides functions used by others
2. **graph.js** second - Uses API module for data fetching
3. **ui.js** third - Uses API module, graph.js calls its functions
4. **app.js** last - Coordinates all other modules, calls their init functions

## Coding Conventions

### Module Pattern
All modules use the object literal pattern:
```javascript
const ModuleName = {
    method1() { ... },
    method2() { ... }
};
```

### Async/Await
All API calls use async/await for clean error handling:
```javascript
async someFunction() {
    try {
        const data = await API.fetchSomething();
        // ... use data
    } catch (error) {
        console.error('Failed:', error);
    }
}
```

### Error Handling
- Log errors to console with `console.error()`
- Show user-friendly messages via `alert()` or UI updates
- Never expose stack traces to users

### Graph Updates
- Use `updateGraphSmooth()` for real-time updates (no flicker)
- Use `renderGraph()` only for complete redraws
- Store current graph data in `GraphRenderer.currentGraphData`

## Common Tasks

### Adding a New API Endpoint

1. **Add to api.js**:
```javascript
async newEndpoint(param) {
    const response = await fetch(`/api/new-endpoint/${param}`);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return await response.json();
}
```

2. **Use it in other modules**:
```javascript
const data = await API.newEndpoint('value');
```

### Adding a New Node Type

1. **Update getNodeColor() in graph.js**:
```javascript
getNodeColor(type) {
    const colors = {
        'document': '#4CAF50',
        'super': '#2196F3',
        'sub': '#9C27B0',
        'evidence': '#FF9800',
        'newtype': '#YOUR_COLOR'  // Add here
    };
    return colors[type] || '#999';
}
```

2. **Update getNodeRadius() similarly**
3. **Ensure buildUnifiedGraph() creates nodes with the new type**

### Adding a New Modal

1. **Add HTML structure to index.html**
2. **Add show/hide functions to ui.js**:
```javascript
showNewModal() {
    document.getElementById('new-modal').style.display = 'flex';
},
hideNewModal() {
    document.getElementById('new-modal').style.display = 'none';
}
```

3. **Wire up event listeners in app.js**:
```javascript
document.getElementById('new-btn').addEventListener('click', () => {
    UI.showNewModal();
});
```

## Known TODOs

### High Priority
- [ ] **Label overlap detection** - Text labels currently overlap, making them unreadable
- [ ] **Arbitrary depth support** - Currently hardcoded to 2 levels (super → sub)
- [ ] **Dynamic connection lengths** - Currently fixed at 150px

### Medium Priority
- [ ] **Rich visual encoding** - Use color/size/border to encode data attributes
- [ ] **Different connection styles** - Vary line thickness/style by relationship type
- [ ] **Spider/radar charts** - Per-node metrics visualization

### Low Priority
- [ ] **Document node click handler** - Currently just logs to console
- [ ] **Evidence node click handler** - Currently just logs to console
- [ ] **Drag-and-drop upload** - setupDragAndDrop() exists but not called

## Debugging Tips

### Graph Not Updating
1. Check browser console for API errors
2. Verify WebSocket connection: Look for "✓ WebSocket connected"
3. Check if `loadGraph()` is being called
4. Inspect `GraphRenderer.currentGraphData` in console

### Click Events Not Working
1. Check if event listeners are set up in `app.js`
2. Verify the DOM element exists with correct ID
3. Check browser console for JavaScript errors
4. Use `event.stopPropagation()` to prevent bubbling

### WebSocket Issues
1. Check if Flask server is running
2. Verify Socket.IO client library is loaded
3. Check browser network tab for socket connections
4. Look for "Client connected" in server logs

## Performance Notes

- **Graph rendering**: D3.js force simulation can be CPU-intensive for large graphs (>200 nodes)
- **Smooth updates**: `updateGraphSmooth()` reuses existing nodes to prevent flicker
- **Progress bar**: Never goes backwards (see ui.js:82-88)
- **Real-time updates**: WebSocket provides instant feedback during processing

## Related Files

- `../templates/index.html` - HTML structure and CSS styles
- `../../app.py` - Flask backend API endpoints
- `../../document_processor.py` - Backend document processing logic
- `../../../research_agent/graph_database.py` - Neo4j database operations
