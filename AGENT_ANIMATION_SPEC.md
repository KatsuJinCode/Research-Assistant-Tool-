# Agent Animation & Game-Like Research Arena
**Status:** Planning
**Priority:** HIGH - Core UX Differentiator

---

## 🎮 Vision: Research as a Visual Strategy Game

Transform the research assistant from a passive graph viewer into an **active, game-like arena** where users watch agents move around, compete in debates, and collaboratively build knowledge in real-time.

---

## 🚀 Core Concepts

### 1. Agent Movement & Pathfinding
**Agents physically traverse the graph** to interact with different nodes, like units in a strategy game.

#### Movement Scenarios:

**Single-Task Agent:**
```
Spawn at center
  ↓ move to
Target Node
  ↓ process
Create Result
  ↓ fade out
Despawn
```

**Multi-Step Research Agent:**
```
🤖 Spawn near Claim
  ↓ move to (animated path)
📄 Claim Node (analyze)
  ↓ internal processing (spin/pulse on agent)
  ↓ move to
🔗 API Node (search)
  ↓ API generates temporary result nodes
📚 Search Results (appear as floating nodes)
  ↓ agent moves to each result
  ↓ pruning animation (results fade/shrink as processed)
📊 Synthesized Summary (agent creates new node)
  ↓ move back to
💡 Claim Node (attach evidence)
  ↓
✅ Complete (checkmark animation)
```

**Visual Elements:**
- **Movement**: Smooth bezier curve paths between nodes
- **Speed**: Faster for simple moves, slower for complex reasoning
- **Trail effect**: Subtle glowing trail behind agent as it moves
- **Collision avoidance**: Agents navigate around other nodes

---

### 2. Real-Time Processing Indicators

#### On Agent Node:
```
🤖 Agent Node (pulsing cyan glow)
   ├─ Progress Ring (circular, fills as task completes)
   ├─ Status Text ("Analyzing claim...", "Searching papers...", "Synthesizing...")
   └─ Sub-task Dots (3 dots showing current step: ●●○)
```

#### On Target Node (Being Modified):
```
💡 Claim Node
   ├─ Glow effect (highlights when agent is working on it)
   ├─ "Being updated by Agent-abc123" tooltip
   ├─ Shimmer animation (indicates active modification)
   └─ Real-time text updates (claim text morphs as agent refines it)
```

#### Temporary Nodes (Search Results):
```
📚 Search Result 1 (50% opacity)
📚 Search Result 2 (50% opacity)
📚 Search Result 3 (50% opacity)
   ↓ agent processes each
📚 Result 1 (fades to 20%, then disappears)
📚 Result 2 (shrinks, merges into agent)
📚 Result 3 (pruned - red X animation)
   ↓
📊 Synthesized Evidence (100% opacity, permanent)
```

**Animation Details:**
- **Pruning**: Node shrinks + fade out (500ms)
- **Merging**: Node moves toward agent + dissolves (800ms)
- **Creating**: New node grows from agent position (600ms)
- **Connecting**: Link draws from source to target (400ms)

---

### 3. Multi-Agent Debate Framework 🥊

**Game-Like Competitive Research System**

#### Architecture:

```
User: "Verify claim: 'AI will replace most jobs by 2030'"
  ↓
🎭 Moderator Agent (spawns at center)
  ├─ Spawns Pro Agent
  ├─ Spawns Con Agent
  └─ Sets up debate arena

🟢 Pro Agent (green)          🔴 Con Agent (red)
   ↓ moves to claim              ↓ moves to claim
   Analyzes                      Analyzes
   ↓ moves to API                ↓ moves to API
   Searches supporting           Searches contradicting
   ↓ creates evidence nodes      ↓ creates evidence nodes
   ↓ moves to debate center      ↓ moves to debate center

🎭 Moderator Agent
   ├─ Evaluates Pro arguments (scores: 7/10)
   ├─ Evaluates Con arguments (scores: 8/10)
   ├─ Identifies gaps in Pro argument
   ├─ Synthesizes best elements from both
   └─ Presents synthesis to user for approval

Visual Representation:
   🟢 Pro Agent ──argument──> 🎭 Moderator <──argument── 🔴 Con Agent
                                    ↓
                              📊 Synthesis Node
                                    ↓
                              👤 User Approval
```

#### Debate Phases (Animated Sequence):

**Phase 1: Setup (5s)**
- Moderator spawns at center
- Pro/Con agents spawn on opposite sides
- Claim node highlighted in gold
- Debate arena boundary fades in (circular boundary around nodes)

**Phase 2: Research (20-60s)**
- Pro agent moves to claim → API → results (green trail)
- Con agent moves to claim → API → results (red trail)
- Both agents show "Researching..." status
- Search results appear as colored nodes (green vs red)
- Real-time pruning/synthesizing animations

**Phase 3: Presentation (10s)**
- Both agents move to "debate stage" (center area)
- Agents face each other (rotate toward each other)
- Speech bubbles appear with argument summaries
- Evidence nodes pulse to indicate they're being referenced

**Phase 4: Evaluation (5s)**
- Moderator pulses (thinking animation)
- Score bars appear above each agent (filling animation)
- Winning agent glows brighter
- Losing agent dims slightly

**Phase 5: Synthesis (10s)**
- Moderator creates new synthesis node (grows from center)
- Best evidence from both sides links to synthesis
- Gaps/weaknesses highlighted in losing argument
- Synthesis presented to user (notification + highlight)

**Phase 6: User Decision**
- User approves/modifies/rejects synthesis
- If approved: Synthesis integrates into graph (permanent)
- If rejected: Debate history saved for review

---

### 4. API Nodes as Data Sources

**APIs become interactive graph nodes** that agents visit to fetch data.

```
🔗 ArXiv API Node (permanent, always visible)
   ↓ when agent queries
📚 Search Results (temporary nodes, fan out from API)
   ├─ Result 1: "Deep Learning Survey 2024"
   ├─ Result 2: "Transformers in NLP"
   └─ Result 3: "GPT-4 Analysis"

Agent processes each result:
   ├─ Result 1: ✅ Relevant (merges into synthesis)
   ├─ Result 2: ⚠️ Partially relevant (extracts key quotes)
   └─ Result 3: ❌ Irrelevant (prunes/fades out)

Final Output:
📊 Synthesized Evidence Node (attached to original claim)
```

**API Node Behavior:**
- **Idle state**: Dim, no activity
- **Queried state**: Pulses when agent sends request
- **Responding**: Search results "spawn" from API node outward
- **Complete**: Returns to idle

**Types of API Nodes:**
- 🔗 **Web Search** (Google, Bing)
- 📚 **ArXiv** (research papers)
- 📖 **Wikipedia** (general knowledge)
- 🧬 **Domain-specific APIs** (PubMed, USPTO, etc.)

---

## 🎯 Implementation Phases

### Phase 1: Agent Movement System (FOUNDATION)
**Goal:** Agents move smoothly between nodes

**Implementation:**
1. **Agent Position System**
   - Track agent x,y coordinates (separate from nodes)
   - Smooth interpolation between positions
   - Bezier curve path generation

2. **Movement Animation**
   - `moveAgentToNode(agentId, targetNodeId, duration)`
   - D3.js transition for smooth movement
   - Trail effect (SVG path with opacity gradient)

3. **WebSocket Integration**
   - Backend broadcasts agent movements
   - Frontend animates in real-time
   - Queue system for multiple movements

**Files to Modify:**
- `web_ui/static/js/graph.js` (add agent layer above nodes)
- `web_ui/app.py` (WebSocket agent movement events)
- `research_agent/agent_orchestrator.py` (broadcast agent state changes)

**Estimated Time:** 12-16 hours

---

### Phase 2: Real-Time Processing Indicators
**Goal:** Show what agents are doing at each moment

**Implementation:**
1. **Agent Status Overlay**
   - Progress ring (SVG circle with animated stroke)
   - Status text (floating above agent)
   - Sub-task indicators (dots showing progress)

2. **Node Modification Indicators**
   - Glow effect when agent is working on node
   - Shimmer/pulse animation
   - Real-time text updates (morphing text)

3. **Temporary Node System**
   - Search results as temporary nodes (50% opacity)
   - Pruning animations (fade out)
   - Merging animations (move + dissolve)

**Files to Modify:**
- `web_ui/static/js/graph.js` (add overlay system)
- `web_ui/static/css/graph.css` (animation keyframes)
- `web_ui/app.py` (WebSocket status updates)

**Estimated Time:** 10-14 hours

---

### Phase 3: Multi-Agent Debate Framework
**Goal:** Agents compete to research claims

**Implementation:**
1. **Debate Orchestrator**
   - New agent type: `DebateModeratorAgent`
   - Spawns Pro/Con research agents
   - Evaluates arguments and synthesizes

2. **Debate Arena Visualization**
   - Debate boundary (circular arena)
   - Agent positioning (Pro left, Con right, Moderator center)
   - Speech bubble system for arguments

3. **Scoring & Evaluation UI**
   - Score bars above agents
   - Argument strength visualization
   - Synthesis presentation modal

**Files to Create:**
- `research_agent/debate_moderator.py` (new agent type)
- `research_agent/debate_framework.py` (competition logic)
- `web_ui/static/js/debate_visualizer.js` (debate-specific animations)

**Files to Modify:**
- `web_ui/static/js/graph.js` (debate arena mode)
- `web_ui/app.py` (debate endpoints + WebSocket events)

**Estimated Time:** 20-24 hours

---

### Phase 4: API Nodes & Search Result Visualization
**Goal:** APIs become visible, interactive nodes

**Implementation:**
1. **API Node System**
   - Add permanent API nodes to graph (ArXiv, Wikipedia, etc.)
   - Query animation (pulse when agent sends request)
   - Response spawning (search results fan out from API)

2. **Search Result Lifecycle**
   - Spawn as temporary nodes (from API position)
   - Agent moves to each result
   - Pruning/merging animations
   - Final synthesis node creation

3. **API Configuration**
   - User can add/remove API nodes
   - Configure which APIs agents can use
   - Show API rate limits/status

**Files to Create:**
- `research_agent/api_nodes.py` (API node definitions)
- `web_ui/static/js/api_visualizer.js` (API-specific animations)

**Files to Modify:**
- `web_ui/static/js/graph.js` (add API node type)
- `research_agent/agent_orchestrator.py` (route API calls through visual system)

**Estimated Time:** 14-18 hours

---

### Phase 5: Game-Like Modes & Profiles
**Goal:** Multiple research "game modes" for different use cases

**Modes:**

1. **🥊 Debate Mode** (Default for controversial claims)
   - Pro vs Con agents compete
   - Moderator synthesizes best arguments
   - User approves final synthesis

2. **🔬 Collaborative Mode** (Default for factual research)
   - Multiple agents work together
   - Share findings in real-time
   - Consensus-building approach

3. **🏆 Tournament Mode** (For complex questions)
   - 4+ agents compete
   - Bracket-style elimination
   - Best argument wins
   - User picks final winner

4. **🎓 Tutorial Mode** (For new users)
   - Single agent with step-by-step explanations
   - Slower animations
   - Tooltips explaining each action

**Implementation:**
- Mode selection in UI (dropdown or tabs)
- Different agent orchestration strategies per mode
- Visual theme changes per mode (colors, animations)

**Files to Create:**
- `research_agent/game_modes.py` (mode definitions)
- `web_ui/static/js/mode_selector.js` (mode UI)

**Estimated Time:** 12-16 hours

---

## 🎨 Visual Design Specifications

### Color Scheme:
- **Pro Agent**: Green (#4CAF50)
- **Con Agent**: Red (#F44336)
- **Moderator Agent**: Purple (#9C27B0)
- **Neutral Agent**: Cyan (#00BCD4)
- **API Nodes**: Yellow (#FFEB3B)
- **Temporary Results**: Gray 50% opacity

### Animation Timing:
- **Movement**: 800ms ease-in-out
- **Spawn/Despawn**: 600ms fade
- **Prune**: 500ms shrink + fade
- **Merge**: 800ms move + dissolve
- **Pulse**: 1500ms loop
- **Spin**: 2000ms loop

### Agent Sizes:
- **Working Agent**: 28px radius (larger, more visible)
- **Idle Agent**: 22px radius (normal)
- **Moderator**: 32px radius (largest, authoritative)

---

## 🚀 MVP Features (Phase 1 + 2)

For initial release, focus on:
1. ✅ Agent movement between nodes
2. ✅ Progress indicators on agents
3. ✅ Status text showing current activity
4. ✅ Basic node highlighting when modified
5. ✅ WebSocket real-time updates

**Defer to later:**
- Full debate framework
- API node visualization
- Tournament mode
- Advanced pruning animations

---

## 🎮 User Experience Flow

**Example: User asks to verify a claim**

```
1. User: "Verify: AI will replace most jobs by 2030"

2. System spawns Moderator Agent (purple, center)
   Animation: Fade in + gentle pulse

3. Moderator spawns Pro Agent (green, left) and Con Agent (red, right)
   Animation: Zoom in from moderator position

4. Both agents move to claim node
   Animation: Smooth bezier paths with glowing trails

5. Agents move to ArXiv API node
   Animation: Synchronized movement, API node pulses

6. Search results spawn from API
   Animation: Fan out in semi-circle, fade in

7. Agents move between results, processing each
   Animation: Agent visits each node, progress ring fills
   - Relevant results: Glow green/red
   - Irrelevant: Fade out (pruned)

8. Agents synthesize findings
   Animation: Results shrink and merge into agent
   New evidence node grows from agent position

9. Agents move to debate center
   Animation: Face each other, speech bubbles appear

10. Moderator evaluates arguments
    Animation: Score bars fill above each agent
    Pro: 7/10, Con: 8/10 (Con wins)

11. Moderator creates synthesis
    Animation: New node grows from moderator
    Best evidence from both sides links to it

12. User approval modal appears
    User can: Approve ✅ | Modify ✏️ | Reject ❌

13. If approved: Synthesis integrates into graph
    Animation: Node solidifies, becomes permanent
    Agents fade out and despawn
```

**Total Experience Time:** ~60-90 seconds
**User sees:** Live "game" of agents competing to research their question

---

## 📊 Success Metrics

**User Engagement:**
- Time spent watching agent animations
- Number of debate sessions initiated
- User approval rate of syntheses

**Understanding:**
- Do users understand what agents are doing?
- Survey: "Did you find the visual feedback helpful?"

**Performance:**
- Animation frame rate (target: 60fps)
- WebSocket latency (target: <100ms)
- Graph remains responsive with 5+ active agents

---

## 🔧 Technical Challenges

1. **Pathfinding**: Agents must avoid colliding with other nodes
2. **Performance**: Many animations + WebSocket updates must stay smooth
3. **Synchronization**: Backend agent state must match frontend animation
4. **Conflict Resolution**: What if two agents try to modify same node?
5. **User Interruption**: What if user modifies graph while agents are working?

**Solutions:**
- Use D3.js force simulation for collision avoidance
- Throttle WebSocket updates (max 30/sec per agent)
- Lock nodes being modified (show "locked" indicator)
- Queue system for conflicting modifications
- Agents pause when user is editing, resume when done

---

## 🎛️ Modularity & Optionality

**CRITICAL REQUIREMENT**: Animation system must be **completely optional**.

### Design Principles:

1. **Backend Independence**
   - Research agents work identically with or without animations
   - WebSocket events are emitted but ignored if animations disabled
   - No backend code should depend on frontend animation system

2. **Alternative Interfaces**
   - Command-line interface (CLI) works without any visualization
   - Different frontends (mobile app, VS Code extension) can choose to implement or skip animations
   - API-only usage (programmatic access) doesn't require animation system

3. **User Control**
   - Settings toggle: "Enable Agent Animations" (default: ON)
   - Performance mode: "Disable Animations (Better Performance)" for low-end devices
   - Accessibility mode: "Simplified Visuals" for users who find animations distracting

### Implementation Architecture:

```javascript
// web_ui/static/js/settings.js
class AnimationSettings {
    constructor() {
        this.enabled = this.loadSetting('animations_enabled', true);
        this.debateMode = this.loadSetting('debate_mode_enabled', true);
        this.agentMovement = this.loadSetting('agent_movement_enabled', true);
        this.apiVisualization = this.loadSetting('api_viz_enabled', true);
    }

    toggleAnimations(enabled) {
        this.enabled = enabled;
        this.saveSetting('animations_enabled', enabled);

        if (!enabled) {
            // Disable all animation modules
            AgentAnimator.disable();
            DebateVisualizer.disable();
            APIVisualizer.disable();
        } else {
            AgentAnimator.enable();
            DebateVisualizer.enable();
            APIVisualizer.enable();
        }
    }
}

// web_ui/static/js/agent_animator.js
class AgentAnimator {
    static enabled = true;

    static moveAgent(agentId, targetNodeId) {
        if (!this.enabled) {
            // Skip animation, just update state
            return Promise.resolve();
        }

        // Perform animation
        return this.animateMovement(agentId, targetNodeId);
    }

    static disable() {
        this.enabled = false;
        // Clean up any running animations
        this.cancelAllAnimations();
    }

    static enable() {
        this.enabled = true;
    }
}
```

### Settings UI:

```
⚙️ Settings → Visualization

  Agent Animations
  ├─ ☑ Enable agent animations
  ├─ ☑ Show agent movement
  ├─ ☑ Show debate visualizations
  ├─ ☑ Show API node interactions
  └─ ☐ Performance mode (disable all animations)

  When disabled:
  - Agents still work in background
  - Results appear instantly (no animations)
  - Graph updates normally (static)
  - Lower CPU/GPU usage
```

### Fallback Behavior (Animations Disabled):

**Instead of animated agent movement:**
- Show notification: "Agent processing claim..." (text-only)
- Progress bar in notifications panel
- Graph updates instantly when complete

**Instead of debate visualization:**
- Show text summary: "Pro Agent found 5 supporting papers, Con Agent found 3 contradicting papers"
- Synthesis appears immediately without animation
- User still approves/rejects normally

**Instead of API node interactions:**
- Show log: "Querying ArXiv... Found 10 results... Processed 10 results..."
- Results added to graph instantly

### Module Structure:

```
web_ui/static/js/
├─ core/
│  ├─ graph.js (REQUIRED - basic graph rendering)
│  ├─ api.js (REQUIRED - API communication)
│  └─ websocket.js (REQUIRED - real-time updates)
│
├─ animations/ (OPTIONAL - can be completely excluded)
│  ├─ agent_animator.js
│  ├─ debate_visualizer.js
│  ├─ api_visualizer.js
│  └─ animation_settings.js
│
└─ app.js (loads animations conditionally)
```

### CLI Usage (No Animations):

```bash
# Run research agent from command line
$ python -m research_agent.cli verify-claim "AI will replace most jobs"

Starting verification...
✓ Spawned Pro Agent (agent-abc123)
✓ Spawned Con Agent (agent-def456)
✓ Spawned Moderator Agent (agent-ghi789)

Pro Agent: Searching ArXiv... [████████░░] 80%
Con Agent: Searching ArXiv... [██████████] 100%

Pro Agent found 5 supporting papers
Con Agent found 3 contradicting papers

Moderator evaluating arguments...
  Pro Agent score: 7/10
  Con Agent score: 8/10

Synthesis created: "While AI will automate many tasks, complete job
replacement unlikely due to human creativity and interpersonal skills..."

Approve synthesis? [y/N]: y
✓ Synthesis integrated into knowledge graph
```

### Performance Benefits (Animations Disabled):

- **CPU**: 60-70% reduction (no D3.js transitions)
- **GPU**: 80-90% reduction (no SVG animations)
- **Memory**: 30-40% reduction (no animation state tracking)
- **Network**: 40-50% reduction (no WebSocket movement events)

**Ideal for:**
- Low-end devices
- Server-side batch processing
- Automated testing
- Users with motion sensitivity
- Screen readers / accessibility tools

---

**Next Steps:**
1. ✅ Review and approve this spec
2. Add to roadmap and todo list
3. Start with Phase 1 (Agent Movement System)
4. Implement basic WebSocket infrastructure for real-time updates
