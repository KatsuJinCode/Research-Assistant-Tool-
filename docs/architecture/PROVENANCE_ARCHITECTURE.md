# Provenance Architecture - Design Principles

## Core Principles

### 1. Data Preservation
**"Rarely throw away data unless it's bad data"**

- Save full agent transcripts (not just summaries)
- Persist all intermediate thinking/processing steps
- Store downloaded files and created documents
- Keep logs of all transformations
- User can delete, but system never auto-deletes

### 2. Provenance Tracking
**"Every node should know its provenance"**

Every node (Claim, Evidence, Document) tracks:
```cypher
Node {
  id: string,
  created_by: string,        // "user" | "document_processor" | "document_finder" | "auto_linker"
  created_by_agent_id: string,  // Link to agent transcript if created by agent
  created_at: timestamp,
  source_document_id: string,   // If extracted from document
  confidence_source: string     // "user_override" | "llm_calculation" | "manual_entry"
}
```

### 3. Bidirectional Linking
**"Everything should be linked so everything we keep is accessible"**

#### Node → Agent:
- Node details panel shows "Created by: [Agent Name]" (clickable)
- Clicking opens agent transcript at creation moment
- Shows context: what agent was doing when it created this node

#### Agent → Nodes:
- Agent monitor shows "Created Nodes: [count]"
- Expandable list of all nodes created by this agent
- Each node is clickable → jumps to node in graph
- Selecting agent highlights all its nodes in graph (yellow glow)

### 4. File Persistence
**"Full transcript of everything it did should be stored in files"**

Directory structure:
```
./agent_transcripts/
  document_finder_20250121_103015_0/
    transcript.json          # Full structured log
    metadata.json            # Agent type, status, duration
    files/
      arxiv_1234.pdf         # Downloaded papers
      arxiv_5678.pdf

  document_processor_20250121_103530_0/
    transcript.json
    metadata.json
    extracted_claims.json    # Intermediate data
    llm_responses.json       # Raw LLM outputs
    files/
      original_document.pdf
```

### 5. Cross-Link Verification
**"Check that everything is accessible via every other thing it links to"**

Verification tests:
- ✓ Every node with `created_by_agent_id` → agent exists in transcript manager
- ✓ Every agent's `created_nodes` list → nodes exist in graph
- ✓ Every document → claims exist
- ✓ Every claim → evidence exists
- ✓ Every semantic link → both nodes exist
- ✓ All file paths are valid and accessible

### 6. Visual Navigation
**"Jump between different connections in our app"**

Navigation paths:
```
Node Card → "Created by Agent X" → Agent Transcript
Agent Card → "Created Nodes (5)" → Expand list → Click node → Graph focuses on node
Graph → Select node → See provenance in sidebar
Agent Monitor → Click agent → Highlight all nodes in graph (yellow outline)
Document → "Processed by Agent Y" → Agent Transcript → "Created Claims (12)" → Claim list
```

---

## Implementation Checklist

### Phase 1: Data Model Updates
- [ ] Add provenance fields to Claim/Evidence/Document nodes
- [ ] Update neo4j_database.py to store provenance
- [ ] Modify claim_repository.py and document_repository.py
- [ ] Add agent_id parameter to all creation methods

### Phase 2: Transcript Manager Enhancements
- [ ] Enable file persistence by default
- [ ] Create directory structure for each agent
- [ ] Save intermediate data files
- [ ] Store metadata.json with agent info

### Phase 3: Agent Integration
- [ ] Update document_processor to log provenance
- [ ] Update document_finder to log provenance
- [ ] Update auto_linker to log provenance
- [ ] Pass agent_id to all node creation calls

### Phase 4: Backend API
- [ ] Add GET /api/nodes/<node_id>/provenance
- [ ] Add GET /api/agents/<agent_id>/created-nodes
- [ ] Add POST /api/agents/<agent_id>/highlight-nodes
- [ ] Add GET /api/verify-cross-links

### Phase 5: Frontend UI
- [ ] Add "Created by" section to node detail cards
- [ ] Make agent name clickable → opens transcript modal
- [ ] Add "Created Nodes" expandable section to agent cards
- [ ] Implement node highlighting when agent selected
- [ ] Add visual breadcrumb trail for navigation

### Phase 6: Cross-Link Verification
- [ ] Write verification function
- [ ] Run on startup
- [ ] Log warnings for broken links
- [ ] Add "Verify Links" button in UI

### Phase 7: Testing
- [ ] Unit tests for provenance tracking
- [ ] Integration tests for node ↔ agent links
- [ ] E2E tests for navigation flows
- [ ] Test transcript file persistence

---

## Example Flow

### User uploads document → Full provenance chain:

1. **Document Created**
   ```json
   {
     "id": "doc_123",
     "created_by": "user",
     "created_by_agent_id": null,
     "created_at": "2025-01-21T10:30:00Z"
   }
   ```

2. **Document Processor Agent Starts**
   ```json
   {
     "agent_id": "document_processor_20250121_103015_0",
     "agent_type": "document_processor",
     "description": "Processing: research_paper.pdf",
     "started_at": "2025-01-21T10:30:15Z"
   }
   ```

3. **Claims Extracted**
   ```json
   {
     "id": "claim_456",
     "text": "Vaccines reduce infection rates by 90%",
     "created_by": "document_processor",
     "created_by_agent_id": "document_processor_20250121_103015_0",
     "source_document_id": "doc_123",
     "created_at": "2025-01-21T10:30:45Z"
   }
   ```

4. **User Views Claim**
   - Card shows: "Created by: Document Processor (2025-01-21 10:30)"
   - Click → Opens agent transcript
   - Transcript highlights entry at 10:30:45: "Extracted claim: Vaccines reduce..."

5. **User Views Agent**
   - Agent card shows: "Created Nodes: 15 claims, 42 evidence"
   - Expand → List of all nodes (clickable)
   - Graph highlights all 57 nodes with yellow outline

---

## Future Enhancements

- **Provenance Graphs**: Visualize full lineage chain
- **Undo/Redo**: Use provenance to implement undo
- **Audit Logs**: Export provenance for compliance
- **Agent Collaboration**: Track multi-agent workflows
- **Version Control**: Track node modifications over time
