# UI Enhancement Roadmap

**Last Updated:** November 21, 2025

---

## 🎯 High-Priority Enhancements

### 1. Graph Filters Relocation
**Status:** Proposed
**Priority:** Medium

**Problem:**
Graph filters currently live in the Documents tab, which doesn't make logical sense.

**Proposed Solutions:**
- **Option A:** Move to Projects tab (group by project context)
- **Option B:** Move to Search tab (filters as search refinement)
- **Option C:** Create new "Display" or "View" tab specifically for visualization controls

**Implementation:**
1. Decide on final location (requires user decision)
2. Update tab_manager.js to move filter UI
3. Ensure filter state persists across tab switches
4. Update visual hierarchy

---

### 2. Advanced Context-Aware AI Suggestions
**Status:** Proposed
**Priority:** High

**Vision:**
Transform AI assistant from tab-aware to **fully workflow-aware**, understanding:
- What tab the user is on
- What nodes are selected
- What the user is trying to accomplish
- Where they are in their research journey

**Key Features:**

#### A. Node Selection Context
- **Auto-add to context**: When user selects a node, automatically add it to AI context
- **Visual feedback**: Show "📄 Document: [Title] added to context" in AI panel
- **Full node knowledge**: AI receives:
  - Node properties (title, text, status, confidence)
  - Source document
  - Creating agent + full agent history
  - All connected nodes (claims, evidence, contradictions)
  - Relationships (SUPPORTS, CONTRADICTS, SIMILAR_TO)
  - Timestamps and provenance

#### B. Smart Suggestions Based on Selection

**Selected Node Types:**

1. **Orphaned Claim** (no evidence):
   ```
   💡 This claim has no supporting evidence. Would you like me to:
   • Search for supporting evidence
   • Spawn an evidence research agent
   • Find similar claims for cross-referencing
   ```

2. **New Claim** (just created):
   ```
   🔍 I see you just created a new claim. Next steps:
   • Search for supporting/contradicting evidence
   • Extract sub-claims for deeper analysis
   • Link to related existing claims
   ```

3. **Document** (selected):
   ```
   📄 This document has been processed. I can help you:
   • Summarize key claims
   • Find similar documents
   • Identify research gaps
   • Generate follow-up questions
   ```

4. **Evidence Node** (selected):
   ```
   🎯 Analyzing this evidence. I can:
   • Assess strength and relevance
   • Find supporting/contradicting evidence
   • Check source credibility
   ```

5. **Multiple Nodes** (multi-select):
   ```
   🔗 You've selected 3 claims. I can:
   • Find connections between them
   • Identify contradictions
   • Generate comparative analysis
   • Merge if duplicates
   ```

#### C. Onboarding & Empty States

**No Selection + App Just Opened:**
```
👋 Welcome! What would you like to do?
• Start a new research project
• Upload your first document
• Take a tour of the features
• Resume where you left off
```

**No Selection + Existing Project:**
```
📊 Your project "AI Safety Research" has:
• 12 documents, 45 claims, 8 pending investigations

Would you like me to:
• Catch you up on recent findings
• Show claims needing evidence
• Suggest next research steps
```

**Empty Database:**
```
🆕 Let's get started! I can help you:
• Upload a research paper
• Create a manual claim
• Import data from another source
• Explain how the system works
```

#### D. Workflow-Aware Suggestions

**Scenario Detection:**

1. **Many pending documents** → "I see you have 5 pending documents. Want me to process them all?"
2. **Unlinked claims** → "You have 8 claims without evidence. Shall I research them?"
3. **Agent failures** → "2 agents failed. Let me investigate what went wrong."
4. **High confidence claim** → "This claim is well-supported! Consider it publication-ready?"
5. **Contradicting claims** → "I found contradictions between Claims A and B. Investigate?"

**Implementation Plan:**

**Phase 1: Node Selection Context** (6-8 hours)
1. Add event listeners for node selection in graph
2. Dispatch `nodeSelected` event with full node data
3. Update AIAssistant.addSelectedNode() to fetch full node details
4. Display context badge: "📄 [Node] selected"
5. Send full node context with AI queries

**Phase 2: Smart Suggestion Engine** (10-12 hours)
1. Create `generateSmartSuggestions(context)` function
2. Analyze selection type (orphaned, new, multiple, etc.)
3. Query node relationships and properties
4. Generate contextual action suggestions
5. Update suggestions in real-time on selection change

**Phase 3: Workflow Detection** (8-10 hours)
1. Track user actions (uploads, selections, searches)
2. Detect patterns (many pending, failures, contradictions)
3. Generate workflow-specific suggestions
4. Implement onboarding flows for new users

**Phase 4: Multi-Node Analysis** (6-8 hours)
1. Support multi-select in graph
2. Analyze relationships between selected nodes
3. Generate comparative analysis suggestions
4. Enable bulk operations

---

## 📊 Current Status Summary

### ✅ Completed
- Context-aware suggestions per tab
- Help (?) button for AI assistant
- Browser-style tabs with centered header
- Agent info cards with full transcript/provenance
- Switchable agent filters (Active/Completed/Failed)

### 🚧 In Progress
- (Ready for next tasks)

### 📋 Pending
- Graph filters relocation (needs user decision)
- Framework YAML System
- Workflow Engine
- **Advanced Graph RAG Upgrades** (NEW - see GRAPH_RAG_UPGRADE_PLAN.md)
  - Tier 1 MVP: KGE + Hierarchical Attention (36-44h, 2-3x better retrieval)
  - Tier 2 Advanced: GNN + TreeLSTM + Sparse Retrieval (64-68h, state-of-the-art)
- **Game-Like Agent Animation System** (NEW - 5 phases, see AGENT_ANIMATION_SPEC.md)
  - Phase 1: Agent Movement System (12-16h)
  - Phase 2: Real-Time Processing Indicators (10-14h)
  - Phase 3: Multi-Agent Debate Framework (20-24h)
  - Phase 4: API Nodes & Search Visualization (14-18h)
  - Phase 5: Game Modes & Profiles (12-16h)
- Agent Graph Visualization - Phase 3: Enhanced info cards
- Agent Graph Visualization - Phase 4: Auto follow-up system

---

## 💡 Additional Ideas

### Real-Time Collaboration Hints
- Show when another user is viewing the same node
- Collaborative annotations and comments
- Shared research sessions

### AI Assistant Personalities
- Let user choose assistant tone (formal, casual, academic)
- Customizable prompt templates
- Domain-specific knowledge bases

### Visual Enhancements
- Node importance sizing (more evidence = bigger node)
- Confidence color gradients
- Animated graph transitions
- Minimap for large graphs

---

## 🗳️ Decisions Needed

1. **Graph Filters Location**: Projects, Search, or new Display tab?
2. **Node Selection UI**: Click vs. right-click vs. keyboard shortcuts?
3. **AI Suggestion Frequency**: Every selection or throttled?
4. **Context Persistence**: Remember selections across sessions?

---

**Next Actions:**
1. User decides on graph filter location
2. Implement Phase 1 of Advanced Context-Aware AI
3. Continue with remaining todo items
