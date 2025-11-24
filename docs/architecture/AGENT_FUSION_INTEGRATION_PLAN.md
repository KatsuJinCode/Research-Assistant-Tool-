# Agent-Fusion Integration Plan

## Date: 2025-11-17
## Status: PLANNING
## Goal: Install and integrate Agent-Fusion for semantic code search and multi-agent orchestration

---

## What is Agent-Fusion?

Agent-Fusion is a **local semantic search engine** that gives AI agents instant access to code, documentation (Markdown, Word, PDF).

**Two Main Components:**
1. **Context Engine**: Automatically indexes and searches configured folders (code, docs, PDFs)
2. **Task Manager**: Optionally coordinates multiple AI assistants, routing tasks, enabling voting, tracking via web dashboard

**Key Features:**
- Semantic understanding (not just keyword matching)
- Finds "authentication logic" even when described as "login," "credentials," or "token validation"
- MCP (Model Context Protocol) compatible
- Works with Claude Code, Codex CLI, Gemini, Amazon Q

---

## Why Agent-Fusion for This Project?

### Current State
- Neo4j graph database with claims, documents, evidence
- Python backend processing PDFs and extracting claims
- Flask web UI for visualization
- Planning modularization (6 phases)

### Benefits of Agent-Fusion
1. **Semantic Code Search**: AI agents can find relevant code without copy-pasting
2. **Multi-Agent Coordination**: Task Manager can orchestrate research agents
3. **Document Indexing**: Automatically indexes uploaded PDFs for context
4. **Integration Ready**: MCP protocol works with Claude Code (what we're using now)

### Use Cases
1. **Development**: "Find where we extract claims from PDFs" → Agent-Fusion finds relevant code
2. **Research Agents**: Coordinate multiple agents investigating claims
3. **Document Context**: Give agents instant access to uploaded research papers
4. **Modularization**: During refactoring, agents can find all usages of a function

---

## System Requirements

### Required
- **Java 21 or higher** (Download: https://adoptium.net/)
- **Python 3.11+** (already installed)
- **Claude Code** (already installed)

### Check Current System
```bash
java -version
```

If not installed or version < 21, install Java 21 from Adoptium.

---

## Installation Plan

### Phase 1: Install Agent-Fusion (5-10 minutes)

#### Step 1.1: Check Java Version
```bash
java -version
```

Expected output: `openjdk version "21.x.x"` or higher

If not installed:
1. Download Java 21 from https://adoptium.net/
2. Install for Windows
3. Verify: `java -version`

#### Step 1.2: Download Agent-Fusion
1. Visit: https://github.com/krokozyab/Agent-Fusion/releases
2. Download `release.zip` (latest version)
3. Extract to: `C:\Users\jpswi\Agent-Fusion\`

**Extracted files:**
```
C:\Users\jpswi\Agent-Fusion\
├── orchestrator-0.1.0-all.jar       # Main application (JAR file)
├── fusionagent.toml                 # Mac/Linux config
├── fusionagent_win.toml             # Windows config (use this)
├── start.bat                        # Windows startup script
├── start.sh                         # Mac/Linux startup
└── orchestrator-mcp-proxy.bat       # MCP proxy for Windows
```

#### Step 1.3: Configure Agent-Fusion for Research Project

Edit `fusionagent_win.toml`:

```toml
# Watch paths - directories to monitor and index
watch_paths = [
  "C:\\Users\\jpswi\\Research-Assistant-Tool-\\research_agent",
  "C:\\Users\\jpswi\\Research-Assistant-Tool-\\web_ui",
  "C:\\Users\\jpswi\\Research-Assistant-Tool-\\docs",
  "C:\\Users\\jpswi\\Research-Assistant-Tool-\\web_ui\\uploads"  # Uploaded PDFs
]

[context]
deployment = "STANDALONE"  # Run as standalone service

[context.indexing]
# File types to index (code, docs, PDFs)
allowed_extensions = [
  ".py",    # Python source
  ".js",    # JavaScript
  ".html",  # Templates
  ".md",    # Documentation
  ".pdf",   # Research papers
  ".json",  # Config files
  ".toml"   # Config files
]

max_file_size_bytes_to_watch = 5242880     # 5MB for watching
max_file_size_bytes_to_index = 209715200   # 200MB for indexing

[context.watcher]
# File watcher settings
debounce_ms = 500                   # Wait 500ms before reindexing
deletion_sweep_interval_seconds = 60

# Ignore patterns (don't index these)
[ignore]
patterns = [
  "**/__pycache__/**",
  "**/.git/**",
  "**/node_modules/**",
  "**/.pytest_cache/**",
  "**/venv/**",
  "**/*.pyc"
]

[context.providers]
# Enable all search methods
full_text = { enabled = true }
semantic = { enabled = true }
hybrid = { enabled = true }
```

#### Step 1.4: Start Agent-Fusion

**Windows:**
```bash
cd C:\Users\jpswi\Agent-Fusion
start.bat
```

Or: Double-click `start.bat` in Windows Explorer

**What Happens:**
1. Service starts on http://127.0.0.1:3000
2. Indexes files from watch_paths
3. Opens admin homepage in browser
4. Ready for MCP connection

**Verify:**
- Browser opens to admin panel
- Console shows "Indexing complete" or similar
- Service is running on port 3000

---

### Phase 2: Integrate with Claude Code (5 minutes)

#### Step 2.1: Add MCP Server to Claude Code

```bash
claude mcp add --transport http orchestrator http://127.0.0.1:3000/mcp
```

#### Step 2.2: Verify Connection

```bash
claude mcp list
```

Expected output: Should show `orchestrator` with URL `http://127.0.0.1:3000/mcp`

#### Step 2.3: Test Search Functionality

In Claude Code session:
```
Please use query_context to find where we extract claims from PDFs
```

Claude Code will now use Agent-Fusion to search your codebase semantically.

---

### Phase 3: Configure for Research Project (10 minutes)

#### Step 3.1: Add Agent Definitions

Edit `fusionagent_win.toml` to add research agent types:

```toml
[agents.research_extractor]
name = "Research Claim Extractor"
type = "claude"
model = "claude-sonnet-4"
capabilities = ["pdf_extraction", "claim_analysis"]

[agents.evidence_finder]
name = "Evidence Finder"
type = "claude"
model = "claude-sonnet-4"
capabilities = ["web_search", "citation_finding"]

[agents.fact_checker]
name = "Fact Checker"
type = "claude"
model = "claude-sonnet-4"
capabilities = ["verification", "contradiction_detection"]
```

#### Step 3.2: Test Multi-Agent Coordination

In Claude Code:
```
Please coordinate with the research agents to:
1. Extract claims from uploaded PDF
2. Find supporting evidence
3. Verify facts

Use the task manager to orchestrate this workflow.
```

#### Step 3.3: Verify PDF Indexing

Upload a test PDF to `web_ui/uploads/` and verify Agent-Fusion indexes it:

1. Upload PDF via web UI
2. Check Agent-Fusion admin panel → "Indexed Files"
3. Verify PDF appears in indexed documents
4. Test search: "Find information about [topic in PDF]"

---

## Integration with Existing System

### Option 1: Standalone (Recommended for Testing)
- Agent-Fusion runs independently
- Claude Code uses it via MCP
- No code changes needed
- Easy to test and evaluate

### Option 2: Embedded (Future Integration)
- Integrate Agent-Fusion into Flask app
- Call Agent-Fusion API from Python backend
- Enables programmatic access to search
- More complex, better for production

**Recommendation**: Start with **Option 1 (Standalone)** to evaluate, then move to **Option 2 (Embedded)** during modularization Phase 3 (Agents Layer).

---

## Usage Patterns

### For Development
```
# Finding code
"use query_context to find where we create claim nodes in Neo4j"
"use query_context to find all WebSocket event handlers"

# Understanding architecture
"use query_context to understand how claims are processed"
"use query_context to find the real-time update logic"
```

### For Research Agents
```
# Coordinating agents
"Use the task manager to coordinate research agents to investigate this claim"

# Finding evidence
"use query_context to find supporting evidence for this claim in our uploaded PDFs"
```

### For Modularization
```
# During refactoring
"use query_context to find all places where document_processor is imported"
"use query_context to find all Cypher queries that need to move to repositories"
```

---

## Testing Plan

### Test 1: Basic Search
1. Start Agent-Fusion
2. In Claude Code: "use query_context to find claim extraction logic"
3. Verify it finds `document_processor.py` and relevant functions

### Test 2: PDF Indexing
1. Upload a PDF via web UI
2. Wait 1 minute for indexing
3. In Claude Code: "use query_context to find information about [topic in PDF]"
4. Verify it searches PDF content

### Test 3: Multi-Agent (Optional)
1. Configure agent definitions in TOML
2. Ask Claude Code to coordinate multiple agents
3. Verify task routing works

---

## Troubleshooting

### Issue: Java not found
**Solution**: Install Java 21 from https://adoptium.net/

### Issue: Port 3000 already in use
**Solution**:
- Check what's using port 3000: `netstat -ano | findstr :3000`
- Kill process or change Agent-Fusion port in config

### Issue: Files not being indexed
**Solution**:
- Check `watch_paths` in config matches actual directories
- Check file extensions are in `allowed_extensions`
- Check file size is under `max_file_size_bytes_to_index`

### Issue: "agentId is required" error
**Solution**: Ensure agent name in TOML matches agent referenced in prompts

### Issue: Search returns no results
**Solution**:
- Verify indexing completed (check admin panel)
- Try more general search terms
- Check logs in Agent-Fusion console

---

## Next Steps After Installation

### Immediate (Testing)
1. Install and start Agent-Fusion
2. Connect to Claude Code via MCP
3. Test basic code search
4. Test PDF indexing with uploaded documents

### Short-term (Evaluation)
1. Use during development to find code
2. Test multi-agent coordination
3. Evaluate usefulness for modularization
4. Document benefits and issues

### Long-term (Integration)
1. **Phase 3 (Agents Layer)** during modularization:
   - Create `research_agent/orchestrator.py`
   - Integrate Agent-Fusion API calls
   - Use Task Manager for multi-agent workflows

2. **After Modularization**:
   - Embedded deployment mode
   - Programmatic access from Python backend
   - Custom agent definitions for research tasks

---

## Cost/Benefit Analysis

### Costs
- **Time**: 20-30 minutes setup
- **Resources**: ~200MB JAR file, Java runtime
- **Maintenance**: Keep Agent-Fusion running alongside Flask

### Benefits
- **Development Speed**: Instant code search without grepping
- **Multi-Agent**: Built-in orchestration for research agents
- **PDF Context**: Automatic indexing of research papers
- **Modularization**: Easier refactoring with semantic search
- **Future**: Foundation for advanced agent coordination

**Recommendation**: **Worth installing** - Low cost, high potential benefit, especially for modularization and future multi-agent features.

---

## Files to Create

After installation, document the setup:

### 1. `start_agent_fusion.bat` (Convenience script)
```batch
@echo off
echo Starting Agent-Fusion...
cd C:\Users\jpswi\Agent-Fusion
start.bat
```

### 2. `.gitignore` updates
```
# Agent-Fusion
Agent-Fusion/
*.db  # Agent-Fusion database
```

### 3. `docs/AGENT_FUSION_USAGE.md` (Usage guide)
Create after testing with actual usage examples.

---

## References

- Agent-Fusion GitHub: https://github.com/krokozyab/Agent-Fusion
- Installation Guide: https://github.com/krokozyab/Agent-Fusion/blob/main/docs/INSTALL.md
- MCP Protocol: https://spec.modelcontextprotocol.io/
- Claude Code MCP Docs: https://code.claude.com/docs/en/mcp
