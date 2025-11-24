# Advanced Visualization Features - User Guide

## Overview

The Research Assistant Tool graph visualization now includes comprehensive advanced visualization options with 6 major feature sets:

1. **Multiple Layout Algorithms** (5 options)
2. **Node Clustering** (4 methods)
3. **Heatmap Coloring** (6 color schemes)
4. **Timeline Animation** (time-based graph evolution)
5. **Export Options** (PNG, SVG, PDF, JSON)
6. **Visual Enhancements** (cluster boundaries, legends)

---

## 1. Layout Algorithms

Access via: **Visualization Controls Panel → Layout**

### Available Layouts:

#### Force-Directed (Default)
- **Description**: Physics-based layout with dynamic node positioning
- **Best for**: General-purpose visualization, exploring connections
- **Features**:
  - Automatic spacing based on link types
  - Dynamic distance (170-200px based on relationship)
  - Collision detection prevents overlap

#### Hierarchical Tree
- **Description**: Top-down tree structure from root nodes
- **Best for**: Document hierarchies, claim structures
- **Features**:
  - Automatically identifies root nodes (documents, sources)
  - Multi-tree layout for multiple documents
  - Clear parent-child relationships

#### Circular
- **Description**: Nodes arranged in a circle
- **Best for**: Highlighting overall graph structure
- **Features**:
  - Equal spacing around perimeter
  - Clear visualization of cross-document links
  - Good for small-to-medium graphs (< 50 nodes)

#### Grid
- **Description**: Nodes arranged in a regular grid
- **Best for**: Systematic comparison, equal weighting
- **Features**:
  - Auto-calculated grid dimensions
  - No overlap guarantee
  - Clean, organized appearance

#### Radial (by Type)
- **Description**: Concentric circles grouped by node type
- **Best for**: Exploring type-based relationships
- **Features**:
  - Documents in center, claims in outer rings
  - Agent nodes in separate ring
  - Type-based color coding maintained

---

## 2. Node Clustering

Access via: **Visualization Controls Panel → Clustering**

### Clustering Methods:

#### No Clustering (Default)
- Disables all clustering
- Shows original graph structure

#### By Similarity
- **Algorithm**: K-means clustering on text embeddings
- **k**: Auto-calculated (min 2, max 5, typically √n/10)
- **Features**:
  - Groups semantically similar nodes
  - Pseudo-embeddings from text content
  - Up to 50 iterations for convergence
- **Use cases**: Finding research themes, identifying duplicate claims

#### By Type
- **Description**: Groups by node type (document, claim, evidence, agent, source)
- **Features**:
  - Simple categorical clustering
  - Preserves type distinctions
- **Use cases**: Separating different entity types

#### By Confidence
- **Description**: Groups by confidence score ranges
- **Ranges**:
  - Low (0-30%)
  - Medium (30-60%)
  - High (60-100%)
- **Use cases**: Quality assessment, filtering low-confidence claims

### Cluster Boundaries
- Toggle: **Show Boundaries** checkbox
- **Visualization**: Convex hull around each cluster
- **Styling**:
  - Semi-transparent fill (15% opacity)
  - Dashed stroke (5,5 pattern)
  - 30px padding from nodes
  - Color-coded by cluster ID

---

## 3. Heatmap Color Schemes

Access via: **Visualization Controls Panel → Color Scheme**

### Available Schemes:

#### By Type (Default)
- **Description**: Standard type-based colors
- **Colors**:
  - Documents: Green
  - Super Claims: Blue
  - Sub Claims: Purple
  - Evidence: Orange
  - Agents: Cyan
  - Sources: Yellow

#### Confidence Heatmap
- **Scale**: Red (low) → Yellow → Green (high)
- **Domain**: 0-100%
- **Algorithm**: D3 interpolateRdYlGn
- **Use cases**: Quality assessment, identifying uncertain claims

#### Quality Score
- **Scale**: Plasma color scheme (dark purple → bright yellow)
- **Domain**: 0-100%
- **Source**: `quality_score` field from node data
- **Use cases**: Research prioritization, quality filtering

#### Investigation Value
- **Scale**: Viridis color scheme (dark blue → bright yellow)
- **Domain**: 0-100%
- **Source**: `investigation_value` field
- **Use cases**: Research prioritization, gap identification

#### Recency
- **Scale**: Cool color scheme (blue → cyan)
- **Domain**: 0 (old) → 1 (recent)
- **Calculation**: Age relative to 1 year maximum
- **Use cases**: Tracking new research, temporal analysis

#### Connections
- **Scale**: Warm color scheme (dark red → bright yellow)
- **Domain**: 0-20 connections
- **Calculation**: Count of incoming + outgoing links
- **Use cases**: Finding hub nodes, network centrality

### Legend
- Toggle: **Show Legend** checkbox
- **Display**: Bottom-right corner
- **Elements**:
  - Scheme name
  - Gradient bar (10-step interpolation)
  - Min/Max labels (contextual)

---

## 4. Timeline Animation

Access via: **Visualization Controls Panel → Timeline → Enable Timeline**

### Features:

#### Playback Controls
- **Play/Pause**: Toggle animation
- **Reset**: Return to beginning
- **Seek**: Drag slider to any timestamp

#### Speed Control
- **Options**: 0.5x, 1x, 2x, 5x, 10x
- **Default**: 1x (10 seconds for full timeline)
- **Algorithm**: Frame-based interpolation

#### Visualization
- **Nodes**: Fade in when created (opacity 0.05 → 1.0)
- **Links**: Show only when both endpoints visible
- **Timestamp**: Live date/time display

#### Timeline Calculation
- **Source**: `created_at` field from node data
- **Fallback**: Current time if missing
- **Range**: Minimum to maximum timestamp across all nodes

### Use Cases:
- Research evolution analysis
- Document processing tracking
- Agent activity replay
- Temporal pattern discovery

---

## 5. Export Options

Access via: **Visualization Controls Panel → Export**

### Export Formats:

#### PNG (Raster Image)
- **Resolution**: Canvas size (typically 1920×1080)
- **Background**: Dark (#1a1a1a) matching UI
- **Quality**: High (lossless PNG)
- **Use cases**: Presentations, reports, social media

#### SVG (Vector Graphics)
- **Format**: Scalable vector with inline styles
- **Compatibility**: All modern browsers/editors
- **Benefits**:
  - Infinite scaling without quality loss
  - Editable in Inkscape, Adobe Illustrator
  - Small file size
- **Use cases**: Publications, posters, web embedding

#### PDF (Document)
- **Orientation**: Auto (landscape if width > height)
- **Size**: Matches canvas dimensions
- **Dependency**: jsPDF library (loaded via CDN)
- **Fallback**: PNG export if jsPDF unavailable
- **Use cases**: Reports, documentation, archival

#### JSON (Data Export)
- **Contents**:
  - All nodes with full data
  - All links with types and metadata
  - Export timestamp
  - Node/link counts
- **Format**: Pretty-printed (2-space indentation)
- **Use cases**: Data backup, external analysis, migration

### Export Process:
1. Click export button
2. Graph rendered to canvas (SVG → Canvas → Image)
3. Download automatically triggers
4. Notification confirms success

---

## 6. Visualization Controls Panel

### Location
- **Position**: Top-right corner of graph area
- **z-index**: 100 (above graph, below modals)

### Collapsible Design
- **Toggle**: Click "−" button in header
- **Collapsed state**: Shows only header
- **Icon change**: "−" → "+" when collapsed

### Responsive Behavior
- **Desktop**: Full 280px width
- **Tablet/Mobile**: Reduced to 240px
- **Max height**: 70vh with scroll

### Styling
- **Theme**: Dark (#2a2a2a) matching main UI
- **Header**: Blue gradient matching app theme
- **Sections**: Separated by horizontal dividers
- **Buttons**: Consistent blue (#2196F3) accent

---

## Technical Implementation

### File Structure
```
web_ui/static/js/
├── layout-manager.js      (332 lines - 5 layout algorithms)
├── clustering.js          (418 lines - k-means, convex hull)
├── heatmap-colorizer.js   (264 lines - 6 color schemes)
├── timeline-player.js     (252 lines - animation engine)
└── export-manager.js      (264 lines - 4 export formats)

web_ui/templates/
└── index.html             (Updated - controls panel, CSS, scripts)
```

### Dependencies
- **D3.js v7**: Core visualization library
- **jsPDF** (optional): PDF export functionality
- **Browser APIs**: Canvas, Blob, FileReader

### Performance Considerations
- **Large Graphs** (>100 nodes): Consider hierarchical or grid layout
- **Clustering**: O(n×k×iterations) complexity, typically < 100ms
- **Timeline**: Frame-based animation, ~60fps target
- **Export**: Canvas rendering may take 1-3 seconds for large graphs

### Browser Compatibility
- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Features**: ES6+, Canvas API, D3.js v7
- **Export**: Download attribute support required

---

## Usage Examples

### Example 1: Finding Research Themes
1. Select **Clustering → By Similarity**
2. Enable **Show Boundaries**
3. Select **Color Scheme → Investigation Value**
4. Observe clusters of related research topics

### Example 2: Quality Assessment
1. Select **Color Scheme → Confidence Heatmap**
2. Enable **Show Legend**
3. Filter low-confidence nodes visually (red)
4. Export as PNG for team review

### Example 3: Temporal Analysis
1. Click **Enable Timeline**
2. Set speed to **2x**
3. Click **Play** to watch graph evolution
4. Pause at key points to analyze

### Example 4: Presentation Export
1. Select **Layout → Hierarchical**
2. Choose **Color Scheme → By Type**
3. Export as **SVG** for scaling
4. Import into presentation software

### Example 5: Network Analysis
1. Select **Color Scheme → Connections**
2. Enable **Show Legend**
3. Identify hub nodes (bright yellow)
4. Select **Layout → Radial** for clarity

---

## Keyboard Shortcuts

- **Ctrl+Click**: Multi-select nodes (comparison mode)
- **Shift+Drag**: Box selection (coming soon)
- **Space**: Pause/play timeline (when active)
- **R**: Reset timeline to start
- **Esc**: Close visualization controls

---

## Troubleshooting

### Issue: Layout doesn't change
- **Solution**: Ensure graph has loaded (nodes visible)
- **Check**: Console for errors
- **Try**: Refresh page and retry

### Issue: Clustering shows no boundaries
- **Solution**: Enable "Show Boundaries" checkbox
- **Check**: Minimum 3 nodes per cluster required
- **Note**: Single-node clusters have no hull

### Issue: Export fails
- **PNG/SVG**: Check browser console for errors
- **PDF**: Verify jsPDF loaded (check Network tab)
- **Fallback**: Use PNG export instead

### Issue: Timeline not playing
- **Solution**: Verify nodes have `created_at` timestamps
- **Check**: Console logs for timestamp parsing errors
- **Fallback**: Nodes without timestamps shown at start

### Issue: Colors don't update
- **Solution**: Verify nodes have required data fields
- **Check**: confidence, quality_score, investigation_value
- **Fallback**: Default type-based coloring used

---

## API Reference

### LayoutManager
```javascript
// Switch layout
LayoutManager.setLayout('hierarchical');

// Available layouts
LayoutManager.layouts = {
  force, hierarchical, circular, grid, radial
};
```

### NodeClusterer
```javascript
// Apply clustering
await NodeClusterer.clusterBySimilarity(nodes, 'embedding');

// Show cluster boundaries
ClusterVisualizer.showClusters(nodes);
```

### HeatmapColorizer
```javascript
// Apply color scheme
HeatmapColorizer.applyHeatmap(nodes, 'confidence');

// Show legend
HeatmapColorizer.showLegend('confidence');
```

### TimelinePlayer
```javascript
// Initialize and play
TimelinePlayer.init(nodes, links);
TimelinePlayer.play();

// Control playback
TimelinePlayer.setSpeed(2.0);
TimelinePlayer.seekTo(timestamp);
```

### ExportManager
```javascript
// Export in various formats
await ExportManager.exportAsPNG();
await ExportManager.exportAsSVG();
await ExportManager.exportAsPDF();
ExportManager.exportAsJSON();
```

---

## Future Enhancements

### Planned Features
- [ ] **Custom color schemes**: User-defined gradients
- [ ] **Layout persistence**: Save/load layout preferences
- [ ] **Advanced clustering**: DBSCAN, hierarchical clustering
- [ ] **Animation recording**: Export timeline as GIF/video
- [ ] **3D visualization**: WebGL-based 3D graph
- [ ] **Collaborative highlighting**: Multi-user selection sync
- [ ] **Layout presets**: Save custom layout configurations
- [ ] **Filter integration**: Combine with search/filter system

### Community Requests
- Interactive cluster editing
- Custom node shapes
- Edge bundling for cleaner layouts
- Minimap overview for large graphs
- Zoom-to-fit controls

---

## Credits

**Implemented**: November 2025
**Author**: Claude Code AI Assistant
**Framework**: D3.js v7, Research Assistant Tool
**Lines of Code**: ~1,530 (visualization modules only)

---

## Support

For issues, feature requests, or questions:
- Check console logs for error messages
- Verify browser compatibility
- Ensure all JavaScript files loaded correctly
- Review this guide's Troubleshooting section

**Happy Visualizing!** 🎨📊✨
