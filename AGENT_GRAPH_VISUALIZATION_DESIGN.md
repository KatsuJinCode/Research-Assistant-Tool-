# Agent Graph Visualization Design

**Date:** November 21, 2025
**Status:** Proposed - Not Yet Implemented
**Priority:** High (after current UI compaction tasks complete)

---

## Vision

Transform the graph view from a static database visualization into a **live, transparent view of the entire research process** - showing not just the data, but the agents working on it, the sources they're querying, and the workflows they're executing.

---

## Core Principle

**Radical Transparency**: If our app exists in a space of getting information from various sources (documents, online resources) and processing it into databases, **let's visualize that whole process for the user** - not just the database at the end, but the entire ingress of data, the processing, the agent workflows, and the decision-making.

---

## Key Features

### 1. Agents as Graph Nodes

**Current:** Agents only visible in Agents tab as a list

**Proposed:** Agents appear as visual nodes in the graph view
- Visual: Robot emoji 🤖 or similar icon
- Node type: `Agent`
- Real-time appearance: When agent is spawned, node appears in graph
- Real-time movement: Agent node visually moves between nodes it's processing
- Node properties visible on hover/click

**Why:** Users should see agents working in the same view as their data

---

### 2. Visual Processing Feedback

**Proposed:** Nodes change appearance as agents work on them
- **Processing animation**: Node border pulses or glows
- **Progress indicator**: Node fills with color as processing completes
- **Agent connection**: Visual line from agent node to current target
- **State colors**:
  - Gray: Not processed
  - Yellow: Queued
  - Blue (pulsing): Currently processing
  - Green: Completed
  - Red: Error

**Example:**
```
[Document Node] ←─ 🤖 [Agent: ClaimExtractor]
   ████░░░░░░ 40% processed
```

---

### 3. Data Source Nodes

**Proposed:** Add nodes representing external data sources
- **Node types:** `DataSource`
- **Visual:** Different icons per source type
  - 📚 arXiv (orange)
  - 🎓 CORE (blue)
  - 🔬 OpenAlex (purple)
  - 🧪 ORKG (green)
  - 🌐 Internet (gray, default hidden/deactivated)

**Agent Workflow Visualization:**
1. Agent analyzes local data (document/claim node)
2. Agent determines what to search for
3. Agent visually moves to DataSource node
4. Search query fires (visible as animation)
5. Results appear as temporary nodes connected to DataSource
6. Agent analyzes each result
7. Agent extracts/creates claims
8. Agent returns to original node
9. New claims appear connected to document

**Example Flow:**
```
[Document: "AI Safety Paper"]
    ↓ (agent analyzes)
[Agent 🤖] → "Need to verify claim about transformer models"
    ↓ (moves to source)
[DataSource: arXiv 📚]
    ↓ (searches)
[5 Search Results] (temporary nodes)
    ↓ (agent analyzes)
[New Claim: "Transformers scale with O(n²) complexity"]
    ↓ (linked back)
[Document: "AI Safety Paper"]
```

---

### 4. Transparent Background Processing

**Current Problem:** Agents work in background, users don't see what's happening until it's done

**Proposed Solution:** All agent activity visible in graph view
- See agents spawn in real-time
- Watch them navigate between nodes
- Observe decision points
- View search queries as they happen
- Monitor result processing
- Track claim extraction/creation

**Benefits:**
- User understands what's happening
- Can intervene if agent goes off-track
- Builds trust in system
- Educational - shows research process
- Debugging - immediately see if something breaks

---

### 5. Agent Info Cards

**Proposed:** Click/select an agent node to see full details panel

**Info Card Contents:**

#### Metadata
- **Agent ID**: Unique identifier
- **Type**: ClaimExtractor, EvidenceResearcher, etc.
- **Status**: Active, Completed, Failed, Paused
- **Created**: Timestamp
- **Created By**: User, AutoAgent, ParentAgentID
- **Lifetime**: Duration since spawn

#### Prompt & Configuration
- **Creation Prompt**: Full prompt that spawned this agent
- **Decision Framework**: Rules/logic the agent follows
- **Philosophy Documents**: Reference docs agent uses
- **Parameters**:
  - Temperature
  - Model
  - Max tokens
  - Search depth
  - Confidence threshold
  - etc.

#### Workflow
- **Todo List**: Full checklist of tasks agent will complete
  - ✅ Extract claims from document
  - ✅ Identify key assertions
  - 🔄 Search for supporting evidence (in progress)
  - ⏳ Verify contradicting claims
  - ⏳ Update confidence scores
- **Current Task**: What agent is doing right now
- **Progress**: % complete

#### History
- **Action Log**: Chronological list of everything agent has done
  - "Analyzed document 'AI Safety Paper'"
  - "Extracted 12 claims"
  - "Identified claim needing verification: [link to claim]"
  - "Searched arXiv for 'transformer attention mechanisms'"
  - "Found 5 relevant papers"
  - "Analyzed paper 'Attention is All You Need'"
  - "Created supporting evidence link"
- **Cross-linked**: Click any action to jump to relevant node

#### Results
- **Nodes Created**: Claims, Evidence, Documents
- **Relationships Created**: SUPPORTS, CONTRADICTS, SIMILAR_TO
- **Confidence Updates**: What confidence scores changed
- **Errors**: Any failures or retries

---

### 6. Automatic Follow-up Agent System

**Future Feature:** Agent that analyzes graph and proposes research follow-ups

**Workflow:**
1. **Agent spawns**: "Research Proposal Agent 🤖"
2. **Moves through graph**: Visits each claim node
3. **Analyzes each claim**:
   - Strength: Well-supported? Needs more evidence?
   - Weaknesses: Contradictions? Gaps in logic?
   - Structure: Vague? Over-specific? Missing qualifiers?
   - Context: Related to other claims? Part of larger pattern?
4. **Proposes follow-ups**:
   - "CHALLENGE: Find contradicting evidence"
   - "CLARIFY: This claim is vague, needs more specificity"
   - "SUPPORT: Strong claim but low confidence, find more evidence"
   - "RESTATE: Qualifiers may be lost, verify original text"
   - "BRANCH: This implies X, should investigate"
   - "CONNECT: Similar to claim [ID], may be duplicate"
5. **Spawns proposed agents**: Each proposal includes:
   - Agent type to spawn
   - Specific task/prompt
   - Expected outcome
   - Priority/importance
6. **User approval**: User sees proposals and can:
   - ✅ Approve (spawn agent)
   - ✏️ Refine (modify prompt/parameters)
   - ❌ Reject (dismiss proposal)
7. **Moves to next node**: Continuous background analysis

**Visual:**
```
[Claim Node]
    ↓
[Research Proposal Agent 🤖] analyzes
    ↓
[3 Proposed Follow-ups]
    • CHALLENGE: Find contradicting evidence ✅ Approved
    • CLARIFY: Restate with more precision ❌ Rejected
    • SUPPORT: Find 2 more sources ⏳ Pending
```

---

## Implementation Plan

### Phase 1: Agent Nodes & Basic Visualization
**Estimated: 8-12 hours**

1. **Data Model Updates** (2 hours)
   - Add `Agent` node type to Neo4j
   - Store agent state (status, current_target, progress)
   - Create relationships: PROCESSING, CREATED_BY, SPAWNED

2. **Graph Visualization** (4 hours)
   - Add agent nodes to D3.js/vis.js rendering
   - Implement node icons (🤖 for agents)
   - Add visual connection lines (agent → target)
   - Implement node state colors (processing, complete, error)

3. **Real-time Updates** (3 hours)
   - WebSocket events for agent state changes
   - Agent spawn/complete notifications
   - Progress updates
   - Current target updates

4. **Basic Agent Info Card** (2 hours)
   - Panel appears on agent node click
   - Display metadata, status, current task
   - Show basic action log

---

### Phase 2: Data Source Nodes & Workflow Visualization
**Estimated: 10-15 hours**

1. **Data Source Nodes** (3 hours)
   - Add `DataSource` node type
   - Create nodes for arXiv, CORE, OpenAlex, ORKG
   - Add icons and colors
   - Default hide Internet source (inactive)

2. **Agent Movement Animation** (5 hours)
   - Visual path from agent to target
   - Animated transitions as agent moves
   - Search query visualization (pulse from agent to source)
   - Result nodes appear connected to source
   - Agent analyzes results animation

3. **Processing Animations** (4 hours)
   - Node border pulse during processing
   - Progress fill animation
   - Color transitions on state change
   - Connection line animations

4. **Temporary Nodes** (2 hours)
   - Search results as temporary nodes
   - Auto-remove when agent finishes analyzing
   - Visual distinction (dashed border?)
   - Fade out animation

---

### Phase 3: Enhanced Agent Info Cards
**Estimated: 6-8 hours**

1. **Full Metadata Panel** (2 hours)
   - Creation prompt display
   - Decision framework
   - Philosophy documents
   - All parameters

2. **Interactive Todo List** (2 hours)
   - Full workflow checklist
   - Real-time status updates
   - Progress bar per task

3. **Complete Action History** (3 hours)
   - Chronological log
   - Cross-linking to nodes
   - Click action → jump to node
   - Filter/search history

---

### Phase 4: Auto Follow-up Agent System
**Estimated: 15-20 hours**

1. **Research Proposal Agent** (8 hours)
   - Agent that analyzes claim nodes
   - Generates follow-up proposals
   - Stores proposals in database
   - Moves through graph systematically

2. **Proposal UI** (5 hours)
   - Display proposals on claim nodes
   - Approve/refine/reject interface
   - Spawn proposed agents on approval
   - Track proposal status

3. **Proposal Logic** (5 hours)
   - Strength/weakness analysis
   - Gap detection
   - Connection finding
   - Priority scoring

---

## Technical Requirements

### Database Schema Updates

```cypher
// Agent node
CREATE (a:Agent {
    id: "agent_abc123",
    type: "ClaimExtractor",
    status: "active",
    created_at: datetime(),
    created_by: "user",
    created_by_agent_id: null,
    current_target_id: "doc_xyz",
    progress: 0.4,

    // Configuration
    prompt: "Extract all claims from this document...",
    decision_framework: "Use MECE principles...",
    philosophy_docs: ["qualifier_preservation.md"],
    parameters: {
        model: "claude-3-sonnet",
        temperature: 0.7,
        max_tokens: 4096
    },

    // Workflow
    todo_list: [
        {task: "Extract claims", status: "completed"},
        {task: "Search for evidence", status: "in_progress"},
        {task: "Update confidence", status: "pending"}
    ],

    // Results
    nodes_created: 12,
    relationships_created: 8,
    errors: 0
})

// Data source node
CREATE (ds:DataSource {
    id: "arxiv",
    name: "arXiv",
    icon: "📚",
    color: "#FF6B35",
    active: true,
    api_endpoint: "http://export.arxiv.org/api/query"
})

// Research proposal
CREATE (rp:ResearchProposal {
    id: "proposal_123",
    claim_id: "claim_xyz",
    type: "CHALLENGE",
    description: "Find contradicting evidence",
    proposed_agent_type: "EvidenceResearcher",
    proposed_prompt: "Search for evidence that contradicts...",
    priority: 0.8,
    status: "pending"
})
```

### WebSocket Events

```javascript
// Agent lifecycle
socket.on('agent_spawned', {agent_id, type, created_by})
socket.on('agent_status', {agent_id, status, progress})
socket.on('agent_target', {agent_id, target_id})
socket.on('agent_completed', {agent_id, results})

// Processing
socket.on('node_processing', {node_id, agent_id, progress})
socket.on('node_complete', {node_id, agent_id})

// Search
socket.on('search_started', {agent_id, source_id, query})
socket.on('search_results', {agent_id, source_id, results})

// Proposals
socket.on('proposal_created', {proposal_id, claim_id, type})
socket.on('proposal_approved', {proposal_id, agent_id_spawned})
```

---

## Benefits

### For Users
- **Understanding**: See exactly what system is doing
- **Trust**: Transparency builds confidence
- **Control**: Can intervene if needed
- **Education**: Learn research methodology
- **Debugging**: Immediately spot issues

### For System
- **Accountability**: All agent actions logged and visible
- **Provenance**: Clear chain from source → agent → claim
- **Quality**: Users can spot and correct errors
- **Feedback**: User interactions improve future agents

---

## Open Questions

1. **Performance**: Will animating many agents slow down graph?
   - Solution: Limit concurrent agent visualizations
   - Solution: Virtualization (only render visible area)

2. **Graph Clutter**: Too many agent nodes?
   - Solution: Filter toggle to show/hide agents
   - Solution: Collapse completed agents
   - Solution: Agent layer (can hide entire layer)

3. **Data Source Placement**: Where do source nodes go in layout?
   - Solution: Fixed positions (sidebar?)
   - Solution: Force-directed with strong repulsion
   - Solution: Separate "sources" panel area

4. **Temporary Node Cleanup**: When to remove search result nodes?
   - Solution: Remove when agent finishes analyzing
   - Solution: Fade out after 30 seconds
   - Solution: User toggle to keep visible

---

## Comparison to Traditional Approaches

### Traditional Agent Systems
- Agents in separate tab/window
- Text-based logs
- No spatial relationship to data
- Asynchronous, disconnected

### Our Proposed System
- ✅ Agents in same view as data
- ✅ Visual, spatial representation
- ✅ Real-time movement and connections
- ✅ Integrated, holistic view

---

## Next Steps

1. **Immediate** (This session):
   - ✅ Document vision (this file)
   - Add to todo list

2. **Short-term** (After current UI tasks):
   - Implement Phase 1 (Agent Nodes & Basic Viz)
   - Test with single agent
   - Gather feedback

3. **Medium-term** (Next sprint):
   - Implement Phase 2 (Data Sources & Workflow)
   - Implement Phase 3 (Enhanced Info Cards)

4. **Long-term** (Future):
   - Implement Phase 4 (Auto Follow-up System)
   - Polish animations
   - Performance optimization

---

## Conclusion

This is a **fundamental shift** from "showing users the database" to "showing users the entire research process". It aligns perfectly with our transparency principle and transforms the graph view into a **living, breathing visualization of knowledge work**.

Rather than hiding agents in a separate tab, we make them **first-class citizens** in the graph - visible, trackable, and understandable. Users don't just see what data exists, they see **how it got there** and **what's being done with it**.

This is the kind of interface that makes AI research assistance **trustworthy, educational, and genuinely useful**.
