# Tab System + Dynamic Left Panel + AI Assistant Architecture

**Comprehensive Design Document for Unified Navigation System**

---

## 🎯 Overview

This document outlines the architecture for three interconnected features:
1. **Tab Navigation System** - Switch between different views/contexts
2. **Dynamic Left Panel** - Content changes based on active tab
3. **AI Assistant Panel** - Always-visible, context-aware assistant anchored to bottom

---

## 📐 Visual Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ UNIFIED HEADER                                                    │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Brand + Project Selector                                      │ │
│ ├──────────────────────────────────────────────────────────────┤ │
│ │ Stats (clickable cards) + Action Buttons                      │ │
│ ├──────────────────────────────────────────────────────────────┤ │
│ │ TAB NAVIGATION BAR                                            │ │
│ │ [📊 Graph] [📄 Docs] [📝 Claims] [🔍 Search] [🤖 Agents]     │ │
│ └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────┬──────────────────────────────────────────────┐
│ LEFT PANEL       │ MAIN GRAPH AREA                              │
│ (350px width)    │ (Flexible width)                             │
│                  │                                              │
│ ┌──────────────┐ │ ┌──────────────────────────────────────────┐ │
│ │              │ │ │                                          │ │
│ │ TAB CONTENT  │ │ │                                          │ │
│ │ (66% height) │ │ │        INTERACTIVE GRAPH                 │ │
│ │              │ │ │        VISUALIZATION                     │ │
│ │ Scrollable   │ │ │                                          │ │
│ │ Area         │ │ │        (D3.js Force Layout)              │ │
│ │              │ │ │                                          │ │
│ │ Content      │ │ │                                          │ │
│ │ changes      │ │ │                                          │ │
│ │ based on     │ │ │                                          │ │
│ │ active tab   │ │ │                                          │ │
│ │              │ │ │                                          │ │
│ ├──────────────┤ │ └──────────────────────────────────────────┘ │
│ │              │ │                                              │
│ │ AI ASSISTANT │ │  DETAIL PANEL (Overlay on demand)           │
│ │ (33% height) │ │                                              │
│ │              │ │                                              │
│ │ Always       │ │                                              │
│ │ Visible      │ │                                              │
│ │              │ │                                              │
│ └──────────────┘ │                                              │
└──────────────────┴──────────────────────────────────────────────┘
```

---

## 🔧 Component Architecture

### 1. Tab Navigation Bar

**Location**: Bottom row of unified header (new third row)

**Tabs**:
```javascript
const TABS = [
    {
        id: 'graph',
        label: 'Graph',
        icon: '📊',
        description: 'Interactive graph visualization with filters'
    },
    {
        id: 'documents',
        label: 'Documents',
        icon: '📄',
        description: 'Browse and manage all documents'
    },
    {
        id: 'claims',
        label: 'Claims',
        icon: '📝',
        description: 'Explore claims and their relationships'
    },
    {
        id: 'search',
        label: 'Search',
        icon: '🔍',
        description: 'Unified search across all content'
    },
    {
        id: 'agents',
        label: 'Agents',
        icon: '🤖',
        description: 'Monitor background agent activity'
    }
];
```

**Visual Design**:
- Horizontal tab bar with subtle background
- Active tab: brighter, underline indicator, slight lift
- Inactive tabs: muted, hover effect
- Smooth slide transition for active indicator
- Badge counts on tabs (e.g., "5 active agents")

---

### 2. Dynamic Left Panel Split System

**Two-Section Layout**:

```javascript
const PANEL_LAYOUT = {
    totalHeight: 'calc(100vh - 180px)', // Adjusted for 3-row header
    sections: {
        tabContent: {
            height: '66%', // Top 2/3
            minHeight: '300px',
            maxHeight: 'calc(100% - 200px)',
            scrollable: true
        },
        aiAssistant: {
            height: '34%', // Bottom 1/3
            minHeight: '200px',
            maxHeight: '400px',
            fixed: true,
            resizable: true // Optional: drag to resize
        }
    }
};
```

**Divider**:
- Subtle horizontal divider between sections
- Optional: Draggable to resize (with constraints)
- Visual indicator (⋮⋮⋮) when hovering
- Snap to min/max constraints

---

### 3. Tab Content Templates

#### Tab: **Graph View** (Default)
```
┌─────────────────────┐
│ 🔍 SEARCH           │
│ [Search box]        │
├─────────────────────┤
│ 🎚️ FILTERS          │
│ □ Documents         │
│ □ Claims            │
│ □ Evidence          │
│ ─────────           │
│ Status: All ▼       │
├─────────────────────┤
│ 📊 GRAPH STATS      │
│ • Nodes: 42         │
│ • Links: 89         │
│ • Clusters: 3       │
├─────────────────────┤
│ 📄 DOCUMENT LIST    │
│ ┌─────────────────┐ │
│ │ Doc 1           │ │
│ │ Doc 2           │ │
│ │ ...             │ │
│ └─────────────────┘ │
│ (Scrollable)        │
└─────────────────────┘
```

#### Tab: **Documents**
```
┌─────────────────────┐
│ 📄 DOCUMENTS        │
│                     │
│ [Search documents]  │
│                     │
│ Sort by: Date ▼     │
│ Filter: All ▼       │
├─────────────────────┤
│ ┌─────────────────┐ │
│ │ 📄 Document 1   │ │
│ │ Status: ✓       │ │
│ │ Claims: 12      │ │
│ ├─────────────────┤ │
│ │ 📄 Document 2   │ │
│ │ Status: ⏳      │ │
│ │ Claims: 0       │ │
│ └─────────────────┘ │
│                     │
│ [+ Add Document]    │
└─────────────────────┘
```

#### Tab: **Claims**
```
┌─────────────────────┐
│ 📝 CLAIMS           │
│                     │
│ [Search claims]     │
│                     │
│ Filter:             │
│ ☑ Verified          │
│ ☑ Pending           │
│ ☐ Contradicted      │
├─────────────────────┤
│ Group by:           │
│ • Document ▼        │
├─────────────────────┤
│ ┌─────────────────┐ │
│ │ 📝 Claim 1      │ │
│ │ Evidence: 3 ✓   │ │
│ ├─────────────────┤ │
│ │ 📝 Claim 2      │ │
│ │ Evidence: 0     │ │
│ └─────────────────┘ │
└─────────────────────┘
```

#### Tab: **Search**
```
┌─────────────────────┐
│ 🔍 UNIFIED SEARCH   │
│                     │
│ ┌─────────────────┐ │
│ │ [Search query]  │ │
│ │ 🔍 Search       │ │
│ └─────────────────┘ │
│                     │
│ Search in:          │
│ ☑ Documents         │
│ ☑ Claims            │
│ ☑ Transcripts       │
│                     │
│ Search type:        │
│ ● Text              │
│ ○ Semantic          │
│ ○ LLM               │
├─────────────────────┤
│ RESULTS (24):       │
│ ┌─────────────────┐ │
│ │ 📄 Match 1      │ │
│ │ 📝 Match 2      │ │
│ │ ...             │ │
│ └─────────────────┘ │
└─────────────────────┘
```

#### Tab: **Agents**
```
┌─────────────────────┐
│ 🤖 AGENT MONITOR    │
│                     │
│ Active: 2           │
│ Completed: 15       │
│ Failed: 0           │
├─────────────────────┤
│ 🟢 ACTIVE AGENTS    │
│ ┌─────────────────┐ │
│ │ 📄 Doc Processor│ │
│ │ Progress: 67%   │ │
│ │ [View Details]  │ │
│ ├─────────────────┤ │
│ │ 🔍 Doc Finder   │ │
│ │ Searching...    │ │
│ │ [View Details]  │ │
│ └─────────────────┘ │
├─────────────────────┤
│ RECENT COMPLETED    │
│ • Agent 1 (3m ago)  │
│ • Agent 2 (5m ago)  │
└─────────────────────┘
```

---

### 4. AI Assistant Panel

**Always Pinned to Bottom 1/3 of Left Panel**

```
┌─────────────────────────────────┐
│ ═══════════════════════════════ │ <- Divider (draggable)
│                                 │
│ 🤖 AI RESEARCH ASSISTANT        │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Chat Interface              │ │
│ │ (Scrollable message area)   │ │
│ │                             │ │
│ │ AI: How can I help you      │ │
│ │     navigate your research? │ │
│ │                             │ │
│ │ You: [Type message...]      │ │
│ └─────────────────────────────┘ │
│                                 │
│ QUICK ACTIONS:                  │
│ [🔗 Find Similar] [📊 Analyze]  │
│ [🔍 Search] [💡 Suggest]        │
│                                 │
│ Context: Graph View | 3 selected│
└─────────────────────────────────┘
```

**Features**:
- **Context Awareness**: Knows active tab, selected nodes, current view
- **Quick Actions**: Dynamic buttons based on context
- **Message History**: Persistent across sessions
- **Attention Drawing**: Can highlight UI elements with animations
- **Tab Control**: Can programmatically switch tabs
- **Voice Input**: Optional voice command support

**AI Capabilities**:
```javascript
const AI_CAPABILITIES = {
    // Navigation
    switchTab(tabId) {
        // "Show me the agents tab"
    },

    // Attention Drawing
    highlightElement(elementId, message) {
        // "Notice the clustering button - click it to refresh"
    },

    // Data Operations
    filterBy(type, criteria) {
        // "Show me all pending documents"
    },

    // Analysis
    analyzeClaim(claimId) {
        // "Analyze this claim's evidence strength"
    },

    // Suggestions
    suggestNextAction() {
        // "I suggest approving these 3 pending documents"
    }
};
```

---

## 💾 State Management

### Tab State
```javascript
const TabState = {
    activeTab: 'graph', // Current tab
    tabHistory: ['graph', 'documents'], // Navigation history
    tabStates: {
        // Preserve state for each tab
        graph: {
            scrollPosition: 0,
            selectedFilters: ['Document', 'Claim'],
            searchQuery: ''
        },
        documents: {
            scrollPosition: 120,
            sortBy: 'date',
            filterStatus: 'all'
        },
        // ... other tabs
    }
};
```

### AI Assistant State
```javascript
const AIState = {
    chatHistory: [],
    context: {
        activeTab: 'graph',
        selectedNodes: ['node_123', 'node_456'],
        recentActions: ['search', 'filter', 'cluster']
    },
    collapsed: false,
    height: 250 // pixels
};
```

---

## 🎨 Visual Design Specifications

### Tab Bar Styling
```css
.tab-bar {
    background: rgba(0, 0, 0, 0.15);
    padding: 8px 24px;
    display: flex;
    gap: 4px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.tab {
    padding: 10px 20px;
    border-radius: 6px 6px 0 0;
    background: rgba(255, 255, 255, 0.08);
    cursor: pointer;
    transition: all 0.3s;
    position: relative;
}

.tab.active {
    background: rgba(255, 255, 255, 0.18);
    border-bottom: 3px solid #fff;
    transform: translateY(-2px);
}

.tab:hover:not(.active) {
    background: rgba(255, 255, 255, 0.12);
}
```

### Panel Split Styling
```css
#left-panel {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 180px);
}

.panel-section-top {
    flex: 2; /* 66% */
    min-height: 300px;
    overflow-y: auto;
    padding: 20px;
}

.panel-divider {
    height: 4px;
    background: #333;
    cursor: ns-resize;
    position: relative;
}

.panel-divider::before {
    content: '⋮⋮⋮';
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    color: #666;
    font-size: 8px;
}

.panel-section-ai {
    flex: 1; /* 33% */
    min-height: 200px;
    max-height: 400px;
    background: #2a2a2a;
    border-top: 2px solid #444;
    padding: 15px;
    display: flex;
    flex-direction: column;
}
```

### AI Assistant Styling
```css
.ai-assistant {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.ai-header {
    font-size: 14px;
    font-weight: 600;
    color: #2196F3;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.ai-chat-area {
    flex: 1;
    overflow-y: auto;
    margin-bottom: 10px;
    padding: 10px;
    background: #1a1a1a;
    border-radius: 6px;
}

.ai-message {
    margin-bottom: 12px;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
}

.ai-message.ai {
    background: #2196F3;
    color: white;
    margin-left: 0;
    margin-right: 20px;
}

.ai-message.user {
    background: #444;
    color: #e0e0e0;
    margin-left: 20px;
    margin-right: 0;
}

.ai-quick-actions {
    display: flex;
    gap: 6px;
    margin-bottom: 10px;
    flex-wrap: wrap;
}

.ai-quick-action {
    background: #444;
    border: 1px solid #555;
    color: #e0e0e0;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.2s;
}

.ai-quick-action:hover {
    background: #555;
    border-color: #2196F3;
}

.ai-input-area {
    display: flex;
    gap: 8px;
}

.ai-input {
    flex: 1;
    padding: 8px;
    background: #333;
    border: 1px solid #555;
    color: #e0e0e0;
    border-radius: 4px;
    font-size: 12px;
}

.ai-send-btn {
    padding: 8px 16px;
    background: #2196F3;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
}
```

---

## 🔌 JavaScript Modules

### TabManager.js
```javascript
const TabManager = {
    activeTab: 'graph',
    tabs: {...},

    init() {
        // Initialize tab system
    },

    switchTab(tabId) {
        // Switch active tab, update UI, preserve state
    },

    updateTabContent(tabId, content) {
        // Update content for specific tab
    },

    addTabBadge(tabId, count) {
        // Add notification badge to tab
    }
};
```

### PanelManager.js
```javascript
const PanelManager = {
    currentContent: null,
    aiAssistant: null,
    dividerDragging: false,

    init() {
        // Initialize split panel system
    },

    renderTabContent(tabId) {
        // Render appropriate content for tab
    },

    setupDividerResize() {
        // Enable drag-to-resize functionality
    },

    preserveScrollPosition(tabId) {
        // Save scroll position when switching tabs
    }
};
```

### AIAssistant.js
```javascript
const AIAssistant = {
    context: {},
    chatHistory: [],

    init() {
        // Initialize AI assistant
    },

    updateContext(context) {
        // Update AI context awareness
    },

    sendMessage(message) {
        // Send message to AI, get response
    },

    highlightElement(elementId, message) {
        // Draw user attention to UI element
    },

    suggestAction(action) {
        // AI suggests next action
    },

    executeCommand(command) {
        // Execute AI command (switch tab, filter, etc.)
    }
};
```

---

## 🚀 Implementation Phases

### Phase 1: Tab Navigation Bar
1. Add third row to unified header for tabs
2. Create tab data structure and rendering
3. Implement tab switching logic
4. Add active tab visual indicators
5. Test tab navigation

### Phase 2: Dynamic Panel Split
1. Split left panel into two sections (66%/33%)
2. Create divider with drag-to-resize
3. Implement tab content templates
4. Add smooth content transitions
5. Preserve state when switching tabs

### Phase 3: AI Assistant Panel
1. Create AI assistant UI in bottom section
2. Implement chat interface
3. Add context awareness system
4. Create quick action buttons
5. Implement attention-drawing system

### Phase 4: Integration
1. Connect tabs to panel content
2. Enable AI to control tabs
3. Add keyboard shortcuts
4. Implement persistence (localStorage)
5. Mobile/responsive adaptations

### Phase 5: Polish
1. Add animations and transitions
2. Implement loading states
3. Add error handling
4. Performance optimization
5. User testing and refinement

---

## 📊 Success Metrics

**User Experience**:
- Tab switches complete in < 100ms
- Content transitions are smooth (60fps)
- AI responses within 500ms
- Zero layout shifts during navigation

**Functionality**:
- All tab content renders correctly
- State persists across tab switches
- AI assistant maintains context
- Attention-drawing system works reliably

**Performance**:
- No memory leaks during tab switching
- Smooth scrolling in all panels
- Efficient DOM updates
- Lazy loading for heavy content

---

## 🎯 Next Steps

After reviewing this plan, we should:
1. ✅ Confirm architecture decisions
2. ✅ Identify any missing requirements
3. ✅ Prioritize implementation phases
4. 🚀 Begin Phase 1: Tab Navigation Bar

This unified system will transform the Research Assistant Tool into a powerful, context-aware workspace with intelligent guidance from the AI assistant!
