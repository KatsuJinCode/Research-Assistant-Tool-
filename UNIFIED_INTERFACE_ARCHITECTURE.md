# Unified Interface Architecture
**Research Assistant Tool - Web Portal Integration Plan**

---

## Problem Statement

The application currently exists in two disconnected parts:
1. **Web UI** - Visualization and graph navigation
2. **Command-line** - Agent orchestration, document processing, research

**Critical Missing Features:**
- No user control over claim validation (can't adjust confidence, challenge research)
- No way to trigger research agents from UI
- No visibility into background agent activity
- No unified interface for AI-assisted interaction

---

## Architectural Vision

### Core Principle: AI-First Interface
Instead of building manual controls for every operation, provide a **chat interface** that leverages the existing agent system. Users describe intent in natural language, AI handles execution.

### Architecture Components

```
┌─────────────────────────────────────────────────────┐
│                   WEB PORTAL UI                      │
├──────────────────┬──────────────────┬───────────────┤
│   Graph View     │   Chat Panel     │  Agent Monitor│
│   (existing)     │   (NEW)          │  (NEW)        │
│                  │                  │               │
│  - Nodes/Links   │  - AI Assistant  │  - Active     │
│  - Detail Panel  │  - Commands      │    Agents     │
│  - Search/Filter │  - History       │  - Progress   │
│                  │  - Context-aware │  - Controls   │
└──────────────────┴──────────────────┴───────────────┘
           │                │                │
           └────────────────┴────────────────┘
                         │
                    WebSocket
                         │
           ┌─────────────┴──────────────┐
           │    BACKEND SERVICES         │
           ├─────────────────────────────┤
           │  - Flask App                │
           │  - Agent Orchestrator       │
           │  - Neo4j Database           │
           │  - Research Agents          │
           │  - Document Processors      │
           └─────────────────────────────┘
```

---

## Feature Breakdown by Priority

### **PHASE 1: User Control Over Claims** (Critical)
**Goal:** Give users power to validate/invalidate claims and evidence

#### 1.1 Claim Detail Panel Enhancements
**Location:** `web_ui/templates/index.html` - detail panel section

**Features:**
- **Confidence Override Slider**
  - Current confidence displayed
  - User can adjust (0-100%)
  - Visual indicator when manually overridden (gold border?)
  - Store in database: `claim.user_confidence_override`

- **Research Trigger Buttons**
  ```html
  <button onclick="investigateClaim('support')">
    🔍 Find Supporting Evidence
  </button>
  <button onclick="investigateClaim('contradict')">
    ❌ Find Contradicting Evidence
  </button>
  ```

- **Evidence Management**
  - List all evidence links for claim
  - Each evidence has "Remove" button
  - Confirmation dialog: "This will permanently remove this evidence link"
  - Updates claim confidence after removal

**API Endpoints:**
```python
@app.route('/api/claim/<claim_id>/override-confidence', methods=['POST'])
def override_confidence(claim_id):
    # Store user override
    # Re-render graph with updated confidence
    pass

@app.route('/api/claim/<claim_id>/evidence/<evidence_id>', methods=['DELETE'])
def remove_evidence(claim_id, evidence_id):
    # Delete evidence relationship
    # Recalculate claim confidence
    pass
```

#### 1.2 Database Schema Updates
**File:** `backend/database/repositories/claim_repository.py`

**New Properties:**
```python
claim = {
    'confidence': 0.85,  # AI-calculated
    'user_confidence_override': None,  # User manual override
    'effective_confidence': 0.85,  # Final value (override if set, else calculated)
    'manual_adjustments': {
        'confidence_override': {'value': 0.95, 'timestamp': '...'},
        'evidence_removed': ['evidence_id_1', 'evidence_id_2']
    }
}
```

**Repository Methods:**
```python
def set_user_confidence_override(claim_id, confidence_value, user_id=None):
    """Set manual confidence override for a claim."""
    pass

def remove_evidence_link(claim_id, evidence_id):
    """Remove evidence relationship and recalculate confidence."""
    pass

def get_effective_confidence(claim_id):
    """Get final confidence value (user override or calculated)."""
    pass
```

---

### **PHASE 2: Chat Interface** (High Priority)
**Goal:** Unified AI assistant for all operations

#### 2.1 Chat UI Panel
**Location:** `web_ui/templates/index.html`

**Design Options:**
1. **Bottom-right expandable** (like customer support chat)
2. **Right sidebar** (collapsible, takes up ~300px)
3. **Bottom bar** (full width, slides up)

**Recommended:** Bottom-right expandable (familiar UX pattern)

**HTML Structure:**
```html
<div id="chat-panel" class="collapsed">
    <div class="chat-header" onclick="toggleChat()">
        <span>💬 AI Assistant</span>
        <span id="chat-toggle">▼</span>
    </div>
    <div class="chat-body">
        <div id="chat-messages"></div>
        <div class="chat-input-area">
            <input type="text" id="chat-input" placeholder="Ask me anything...">
            <button id="chat-send">Send</button>
        </div>
    </div>
</div>
```

**CSS:**
```css
#chat-panel {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 400px;
    background: #2a2a2a;
    border: 2px solid #2196F3;
    border-radius: 12px;
    z-index: 2000;
}

#chat-panel.collapsed .chat-body {
    display: none;
}

#chat-panel.expanded .chat-body {
    height: 500px;
    display: flex;
    flex-direction: column;
}
```

#### 2.2 Chat Backend
**File:** `web_ui/app.py`

**WebSocket Events:**
```python
@socketio.on('chat_message')
def handle_chat_message(data):
    """Process user chat message through AI agent."""
    user_message = data['message']

    # Get current graph state as context
    graph_context = get_graph_context()

    # Send to AI agent with graph context
    agent_response = process_chat_with_agent(user_message, graph_context)

    # Emit response back to client
    emit('chat_response', {
        'message': agent_response['text'],
        'actions': agent_response.get('actions', []),  # e.g., [{'type': 'highlight_upload'}]
        'timestamp': datetime.now().isoformat()
    })
```

**Chat Agent Integration:**
```python
def process_chat_with_agent(user_message, graph_context):
    """
    Route user message through existing agent orchestration system.

    The agent can:
    - Answer questions about claims/documents
    - Trigger research investigations
    - Guide user to upload documents
    - Explain graph relationships
    - Execute commands (/upload, /investigate, etc.)
    """
    from research_agent.agent_orchestrator import ChatOrchestrator

    orchestrator = ChatOrchestrator(graph_context)
    return orchestrator.process_message(user_message)
```

#### 2.3 Chat Commands
**Slash Commands:**
- `/upload` - Highlight upload zone, explain supported formats
- `/investigate <claim_text>` - Find claim in graph, trigger research
- `/delete <claim_id>` - Delete claim node
- `/confidence <claim_id> <value>` - Override claim confidence
- `/help` - Show available commands
- `/agents` - Show active background agents

#### 2.4 Context-Aware Responses
The chat agent should have access to:
- **Current graph state**: All claims, documents, relationships
- **Selected nodes**: What user is currently viewing
- **Recent actions**: Upload history, recent investigations
- **User preferences**: Stored in session or database

**Example Interactions:**
```
User: "What claims do I have about climate change?"
AI: "You have 3 claims related to climate change:
     1. Global temperatures rising (confidence: 92%)
     2. Sea levels increasing (confidence: 87%)
     3. Arctic ice melting (confidence: 78%)
     Would you like to investigate any of these further?"

User: "Investigate claim 2"
AI: "Starting research investigation for 'Sea levels increasing'...
     Spawning agents to find supporting and contradicting evidence.
     I'll notify you when results are ready."

User: "I don't think claim 3 is accurate"
AI: "I understand. Would you like to:
     1. Lower its confidence score manually
     2. Trigger research to find contradicting evidence
     3. Delete the claim entirely"
```

---

### **PHASE 3: Background Agent Monitoring** (High Priority)
**Goal:** Visibility into all background agent activity

#### 3.1 Agent Monitor Panel
**Location:** Top-right of graph area (or collapsible sidebar)

**Display:**
```
┌─────────────────────────────────────┐
│  🤖 Active Agents (3)               │
├─────────────────────────────────────┤
│  📄 Document Processor              │
│     Processing: paper_2024.pdf      │
│     Progress: 67% (Claims Extraction)│
│     [Pause] [Cancel]                │
│                                     │
│  🔍 Research Agent #1               │
│     Investigating: Climate claims   │
│     Status: Searching arXiv...      │
│     [View] [Cancel]                 │
│                                     │
│  🔗 MECE Clustering                 │
│     Analyzing 47 claims...          │
│     Progress: 23%                   │
│     [Cancel]                        │
└─────────────────────────────────────┘
```

**Implementation:**
```javascript
// Poll for agent status every 2 seconds
setInterval(() => {
    fetch('/api/agents/status')
        .then(r => r.json())
        .then(agents => updateAgentMonitor(agents));
}, 2000);

function updateAgentMonitor(agents) {
    const container = document.getElementById('agent-monitor');
    container.innerHTML = agents.map(agent => `
        <div class="agent-card">
            <div class="agent-type">${agent.icon} ${agent.type}</div>
            <div class="agent-task">${agent.task}</div>
            <div class="agent-progress">
                <div class="progress-bar" style="width: ${agent.progress}%"></div>
            </div>
            <div class="agent-controls">
                <button onclick="pauseAgent('${agent.id}')">Pause</button>
                <button onclick="cancelAgent('${agent.id}')">Cancel</button>
            </div>
        </div>
    `).join('');
}
```

#### 3.2 Agent Status API
**File:** `web_ui/app.py`

```python
# Global agent registry
active_agents = {}

class AgentHandle:
    def __init__(self, agent_id, agent_type, task_description):
        self.id = agent_id
        self.type = agent_type
        self.task = task_description
        self.progress = 0
        self.status = 'running'
        self.started_at = datetime.now()
        self.thread = None  # Reference to background thread

    def update_progress(self, progress):
        self.progress = progress
        socketio.emit('agent_progress_update', {
            'agent_id': self.id,
            'progress': progress
        })

@app.route('/api/agents/status')
def get_agent_status():
    """Get status of all active background agents."""
    return jsonify([{
        'id': agent.id,
        'type': agent.type,
        'task': agent.task,
        'progress': agent.progress,
        'status': agent.status,
        'icon': get_agent_icon(agent.type),
        'started_at': agent.started_at.isoformat()
    } for agent in active_agents.values()])

@app.route('/api/agents/<agent_id>/pause', methods=['POST'])
def pause_agent(agent_id):
    """Pause a running agent."""
    # Implementation depends on how agents are structured
    pass

@app.route('/api/agents/<agent_id>/cancel', methods=['POST'])
def cancel_agent(agent_id):
    """Cancel and remove an agent."""
    if agent_id in active_agents:
        agent = active_agents[agent_id]
        agent.status = 'cancelled'
        # Stop background thread if applicable
        del active_agents[agent_id]
    return jsonify({'status': 'cancelled'})
```

#### 3.3 Integration with Document Processor
**File:** `web_ui/document_processor.py`

**Register agent on start:**
```python
def process_document_live(self, filepath):
    # Create agent handle
    agent_id = f"doc_proc_{generate_id()}"
    agent = AgentHandle(
        agent_id=agent_id,
        agent_type='document_processor',
        task_description=f'Processing: {os.path.basename(filepath)}'
    )
    active_agents[agent_id] = agent

    try:
        # Existing processing logic...
        # Update progress as we go
        agent.update_progress(10)  # Text extraction
        agent.update_progress(30)  # Claims extraction
        agent.update_progress(70)  # Summarization
        agent.update_progress(100) # Complete
    finally:
        # Remove from active agents when done
        if agent_id in active_agents:
            del active_agents[agent_id]
```

---

### **PHASE 4: Advanced Features** (Medium Priority)

#### 4.1 Startup Welcome Flow
**On page load:**
```javascript
socket.on('connected', () => {
    // Send welcome message
    addChatMessage('ai', 'Welcome! I\'m your research assistant. Do you have any claims you\'d like to investigate right away?');
});
```

#### 4.2 Chat-Initiated Document Upload
**AI can guide user:**
```
User: "I want to add a research paper"
AI: "Great! You can upload documents by clicking here [highlights upload zone].
     I support PDF, TXT, and DOCX formats.
     Or you can paste an arXiv URL and I'll download it for you."
```

**Implementation:**
```javascript
socket.on('chat_response', (data) => {
    if (data.actions) {
        data.actions.forEach(action => {
            if (action.type === 'highlight_upload') {
                highlightElement('#upload-zone');
            }
        });
    }
});

function highlightElement(selector) {
    const element = document.querySelector(selector);
    element.classList.add('highlighted');
    element.scrollIntoView({ behavior: 'smooth' });
    setTimeout(() => element.classList.remove('highlighted'), 3000);
}
```

#### 4.3 Manual Claim Entry via Chat
```
User: "Add a claim: The Earth is round"
AI: "I've created a new claim node: 'The Earth is round'
     Would you like me to:
     1. Find supporting evidence
     2. Connect it to an existing document
     3. Set an initial confidence score"
```

**API:**
```python
@app.route('/api/claims/create-manual', methods=['POST'])
def create_manual_claim():
    """Create a claim node from user text input."""
    data = request.json
    claim_text = data['text']

    # Create claim node
    claim_id = claim_repo.create_claim({
        'text': claim_text,
        'source': 'user_manual_entry',
        'confidence': 0.5,  # Default for manual claims
        'claim_type': 'manual'
    })

    # Emit to graph for live update
    socketio.emit('new_claim_added', {
        'claim_id': claim_id,
        'text': claim_text
    })

    return jsonify({'claim_id': claim_id})
```

---

## Implementation Order

### Week 1: Foundation
1. ✅ UI refinements (COMPLETED)
2. Add claim confidence override UI
3. Add evidence removal controls
4. Database schema updates for user overrides

### Week 2: Chat Interface
5. Build chat panel UI
6. Create WebSocket chat endpoint
7. Integrate with agent orchestration
8. Implement basic chat commands

### Week 3: Background Monitoring
9. Build agent monitor panel
10. Create agent status API
11. Integrate with document processor
12. Add agent control (pause/cancel)

### Week 4: Advanced Features
13. Implement research trigger buttons
14. Add chat-initiated uploads
15. Add manual claim entry
16. Implement startup welcome flow

### Week 5: Polish & Testing
17. Visual indicators for manual overrides
18. Chat history persistence
19. Agent status real-time updates
20. End-to-end testing

---

## Database Schema Changes

### Claims Table Updates
```python
# New fields in claim nodes
{
    'user_confidence_override': float | None,
    'effective_confidence': float,  # Calculated property
    'manual_adjustments': {
        'confidence': {
            'value': float,
            'timestamp': str,
            'user_id': str
        },
        'evidence_removed': [str],  # List of removed evidence IDs
        'notes': str  # User notes about why they adjusted
    },
    'source': str,  # 'ai_extracted' | 'user_manual_entry'
}
```

### Chat History Table (Optional)
```python
# For persistent chat history
{
    'message_id': str,
    'session_id': str,
    'timestamp': datetime,
    'sender': str,  # 'user' | 'ai'
    'message': str,
    'context': {
        'selected_claim_ids': [str],
        'current_document_id': str
    },
    'actions_taken': [str]  # e.g., ['spawned_agent', 'updated_confidence']
}
```

---

## Technical Considerations

### WebSocket vs HTTP Polling
- Use **WebSocket** for:
  - Chat messages (real-time bidirectional)
  - Agent status updates
  - Graph updates

- Use **HTTP** for:
  - Initial page load
  - One-time actions (delete, update confidence)
  - Agent status endpoint (with polling fallback)

### Agent Orchestration Reuse
The existing document processing pipeline can be reused for chat:
```python
# Current: Document upload → Agent processes → Graph update
# New:     Chat command → Agent processes → Graph update
#          Same backend, different trigger
```

### State Management
- **Graph state**: Already in Neo4j (single source of truth)
- **Chat state**: In-memory session + optional persistence
- **Agent state**: In-memory registry (active_agents dict)
- **User preferences**: Session cookies or Neo4j user nodes

---

## Testing Strategy

### Unit Tests
- Claim confidence override logic
- Evidence removal and recalculation
- Chat command parsing
- Agent status tracking

### Integration Tests
- WebSocket chat flow
- Agent spawning from chat
- Real-time graph updates
- Background agent monitoring

### User Testing
- Manual claim validation workflow
- Chat-based interactions
- Agent monitoring usability
- Overall unified experience

---

## Future Enhancements (Post-MVP)

1. **Multi-user Support**
   - User accounts and authentication
   - Per-user confidence overrides
   - Collaborative research

2. **Advanced Research Agents**
   - Custom agent types (web search, code analysis, etc.)
   - Agent templates and presets
   - Scheduled/recurring research

3. **Knowledge Graph Export**
   - Export with user adjustments
   - Import from external sources
   - Graph versioning and history

4. **AI Agent Improvements**
   - Multi-turn conversations with memory
   - Proactive suggestions ("I noticed claim X has low confidence, should I investigate?")
   - Natural language query interface ("Show me all claims from 2024 papers")

---

## Success Metrics

- ✅ Users can override any AI-generated confidence score
- ✅ Users can remove invalid evidence links
- ✅ Users can trigger research from UI
- ✅ Chat interface handles 80%+ of common operations
- ✅ Background agents visible and controllable
- ✅ No more switching between web UI and command line
