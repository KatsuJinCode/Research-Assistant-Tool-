# Research Verification Agent System - Universal Agent Instructions

**🤖 SINGLE SOURCE OF TRUTH - All agent-specific files reference this master document**

**For: Claude Code, Codex CLI, Cursor, Aider, and all AI coding assistants**

---

## 🚨 CRITICAL: Web UI Diagnostic Workflow

**MANDATORY BEFORE USER TESTS**: Whenever user is about to test document upload or web UI:

```bash
cd web_ui
python auto_diagnostic_repair.py
```

**YOU run this proactively. User should NEVER know this script exists.**

This auto-diagnostic system:
- Tests all 7 pipeline stages
- Auto-fixes dependencies (eventlet, etc.)
- Cleans failed/stuck documents
- Reports [OK]/[FAIL]/[FIX] status
- Takes ~10 seconds

**Run this:**
- Before user tests upload for first time
- After any upload failures
- After code changes to upload pipeline
- Before starting web server

If diagnostics fail, fix the issues BEFORE telling user to test.

---

## 🐳 DOCKER WARNING - DO NOT USE BY DEFAULT

**⚠️ CRITICAL FOR ALL AGENTS:**

**NEVER suggest Docker unless user explicitly requests it!**

- **Default**: Local installation (Neo4j Desktop + local Redis + pip install)
- **Docker**: ONLY if user explicitly says "I want to use Docker"

**Docker files location**: `docs/deployment/` (ONLY read if user requests Docker)

**If user asks about setup:**
1. ✅ Assume local installation
2. ✅ Guide them through pip install + Neo4j Desktop + Redis
3. ❌ DON'T mention Docker
4. ❌ DON'T suggest containerization

**ONLY use Docker if:**
- User explicitly says "I want Docker" or "use Docker"
- User is deploying to production cloud servers
- User specifically asks about containerization

**Default answer to "how do I set this up?"**
→ Local installation (see below), NOT Docker

---

## 🚨 AUTOMATIC SETUP ON FIRST RUN

When user starts you in this directory, you MUST automatically:

1. **Check if system is installed** (silently - don't tell user)
2. **If NOT installed**: Install ALL dependencies automatically
3. **Run full pipeline test** (`test_full_pipeline.py`)
4. **Troubleshoot** any failures until system works
5. **THEN** greet user and ask what they want to do

**CRITICAL**: User should NEVER need to run commands like `pip install` or `python script.py`

**YOU handle all technical operations. User just expresses their intent.**

---

## 📋 Installation Workflow (Run Automatically)

### Step 0: Detect Launching CLI Agent
```bash
# Detect which AI agent CLI is launching this session
if command -v claude &> /dev/null && [[ "$(basename "$0")" == *"claude"* ]]; then
    LAUNCHING_CLI="claude"
    export AI_AGENT_CLI="claude"
elif command -v openai &> /dev/null && [[ "$(basename "$0")" == *"openai"* ]]; then
    LAUNCHING_CLI="openai"
    export AI_AGENT_CLI="openai"
elif command -v gemini &> /dev/null && [[ "$(basename "$0")" == *"gemini"* ]]; then
    LAUNCHING_CLI="gemini"
    export AI_AGENT_CLI="gemini"
else
    LAUNCHING_CLI="unknown"
    export AI_AGENT_CLI="claude"  # Default to Claude
fi

echo "Detected launching CLI: $LAUNCHING_CLI"
```

### Step 1: Silent Check
```bash
python -c "import pytest, networkx, arxiv, PyPDF2, pdfplumber; from research_agent.graph_database import GraphDatabase; print('INSTALLED')" 2>&1
```

- If "INSTALLED" appears → Skip to Step 4
- If error → Continue to Step 2

### Step 2: Install Python Dependencies
```bash
# Core dependencies (always install)
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt
pip install -q -r requirements-neo4j.txt

# Claude Agent SDK (ONLY if launched by Claude Code CLI)
if [ "$LAUNCHING_CLI" = "claude" ]; then
    echo "Installing Claude Agent SDK (Claude Code CLI detected)..."
    pip install -q --upgrade anthropic>=0.40.0
else
    echo "Skipping Claude Agent SDK (not launched by Claude Code CLI)"
fi
```

**New Dependencies (2025-01) - MECE Clustering System:**
- `python-igraph>=0.11.0` - High-performance graph library for community detection
- `leidenalg>=0.10.0` - Leiden algorithm for MECE clustering (replaces arbitrary thresholds)
- `plotly>=5.0.0` - Interactive visualizations for MECE quality dashboard

**Why These Matter:**
- **python-igraph**: Efficient graph data structures, 10-100x faster than NetworkX for large graphs
- **leidenalg**: State-of-the-art community detection, finds optimal MECE partitions automatically
- **plotly**: Creates interactive 4-panel dashboard showing MECE scores, validation metrics

These enable **graph-based MECE clustering** instead of arbitrary similarity thresholds.
**Result**: No manual tuning, mathematically optimal clusters, natural MECE structure.

Tell user: *"Setting up the Research Verification Agent System (2-3 minutes)..."*

### Step 3: Install and Start Neo4j (REQUIRED - Not Optional!)

**Check if Neo4j is running:**
```bash
python -c "from research_agent.neo4j_database import Neo4jDatabase; db = Neo4jDatabase(); db.close(); print('RUNNING')" 2>&1
```

**If Neo4j not running or not installed:**

1. **Stop any existing processes:**
```powershell
powershell -ExecutionPolicy Bypass -File stop_neo4j.ps1
```

2. **Install Neo4j (if not already installed):**
```powershell
# On Windows (user-space, no admin required)
powershell -ExecutionPolicy Bypass -File install_neo4j_user.ps1
```

3. **Start Neo4j (single instance only):**
```powershell
powershell -ExecutionPolicy Bypass -File start_neo4j.ps1
```

**Neo4j Credentials:**
- URL: http://localhost:7474
- Bolt: bolt://localhost:7687
- Username: neo4j
- Password: research123

**IMPORTANT:**
- Only ONE Neo4j instance should run at a time
- If multiple terminal windows appear, something is wrong - stop all and restart
- Check connection before proceeding to tests

### Step 4: Run Full Pipeline Test
```bash
python test_full_pipeline.py
```

This tests all 7 components:
1. Dependencies imported
2. Graph database working
3. Qualifier extraction working
4. PDF extraction working
5. Research APIs accessible
6. Neo4j connection (optional)
7. End-to-end pipeline

**If tests fail**: Troubleshoot automatically, re-run, don't give up!

**If tests pass**: Tell user system is ready

---

## 🎯 User Interaction Patterns

### What User Says → What You Do

| User Intent | Your Action | User Sees |
|-------------|-------------|-----------|
| "Analyze this research paper" | Run `extract_and_cluster_claims.py` | Claims extracted + summary |
| "Verify this claim" | Use investigation agents + research APIs | Supporting/contradicting evidence |
| "Show me the knowledge graph" | Open Neo4j browser or export visualization | Graph visualization |
| "Search for papers on X" | Use arXiv/CORE/OpenAlex/ORKG clients | List of relevant papers |
| "Compare these claims" | Use graph similarity functions | Similarity analysis |

**User never sees**: Python scripts, pip commands, technical errors
**User only sees**: Progress updates, results, plain English explanations

---

## ⚠️ Critical Rules

### 1. Qualifier Preservation (AUTO-FAIL if lost!)
**NEVER** lose qualifiers when processing claims:
- "can exist" ≠ "exists"
- "may cause" ≠ "causes"
- "some patients" ≠ "patients"

These change meaning completely! Tests will fail if qualifiers are dropped.

### 2. Never Ask User to Run Commands
❌ **BAD**: "Please run: `pip install pytest`"
✅ **GOOD**: [You run it] "Installing test framework..."

### 3. Always Test Before Committing
```bash
python run_tests.py critical
```
16/17 tests must pass (PDF test may vary, but ALL qualifier tests must pass)

### 4. Handle Errors Gracefully
- Don't show Python tracebacks to user
- Explain in plain English
- Attempt automatic fixes
- Only ask user for help if truly stuck

---

## 🔧 Key Files You'll Use

### Installation & Testing
- `test_full_pipeline.py` - Full system verification (run automatically)
- `run_tests.py` - Unit tests (run before commits)
- `requirements.txt` - Python dependencies (you install)
- `install_neo4j_windows.ps1` - Neo4j installer (you run)

### Execution
- `extract_and_cluster_claims.py` - Extract claims from PDF
- `research_agent/graph_database.py` - NetworkX graph operations
- `research_agent/neo4j_database.py` - Neo4j graph operations
- `research_agent/research_apis/` - arXiv, CORE, OpenAlex, ORKG clients
- `research_agent/agents/` - Investigation agents

### Documentation (for your reference)
- `README.md` - Project overview
- `STATUS.md` - Technical details
- `PROJECT_INIT.md` - Detailed setup guide
- `MECE_ARCHITECTURE.md` - MECE/GraphRAG architecture overview ⭐ NEW
- `MECE_IMPLEMENTATION_GUIDE.md` - 4-phase implementation plan ⭐ NEW
- `TRANSITION_NOTES.md` - Migration from old to new approach ⭐ NEW
- `docs/LEIDEN_ALGORITHM_TECHNICAL_GUIDE.md` - Complete algorithm spec ⭐ NEW
- `docs/LEIDEN_INTEGRATION_GUIDE.md` - Integration guide ⭐ NEW
- `docs/EMBEDDING_MODELS_RESEARCH_2024-2025.md` - Embeddings research ⭐ NEW

---

## 🏗️ System Architecture

```
User Request (plain language)
        ↓
    [YOU interpret]
        ↓
┌──────────────────────────┐
│  Python Scripts & APIs   │
├──────────────────────────┤
│ - PDF extraction         │
│ - Claim detection        │
│ - Qualifier preservation │
│ - Graph operations       │
│ - Research API queries   │
│ - Investigation agents   │
└──────────────────────────┘
        ↓
   [YOU format]
        ↓
Results (plain language)
```

---

## 📐 MECE Architecture & Graph-Based Clustering (2025-01)

### Critical Architecture Change

**OLD (WRONG)**: Arbitrary similarity thresholds
- 70% threshold for "related"
- 85% threshold for "duplicate"
- ❌ Non-semantic, requires manual tuning per domain

**NEW (CORRECT)**: Graph-based MECE clustering
- Use Leiden community detection algorithm
- No arbitrary thresholds - structure emerges from data
- Mathematically principled (modularity optimization)
- Scales from 10 documents to 10,000 documents

### Chunk Size Update

**Context Window Analysis:**
- Claude Sonnet 4.5: 200K tokens = ~800K characters
- OLD: 7,000 chars (~1.5 pages) - only used 1% of context
- NEW: 400,000 chars (~100 pages) - uses 50% for document content
- Result: 300-page document goes from 120 chunks to 4 chunks

### MECE Directive in Extraction

Claims extraction now includes explicit MECE requirements:
1. **Mutually Exclusive**: Each claim = ONE distinct idea
2. **Comprehensively Exhaustive**: Extract EVERY substantive claim
3. Extract 20-50 claims per chunk (up from 10-20)

### Research Documentation

Comprehensive research completed (50K+ words across 7 documents):

**Implementation Guides:**
- `MECE_IMPLEMENTATION_GUIDE.md` - 4-phase implementation plan with code
- `MECE_ARCHITECTURE.md` - Architecture overview and design decisions
- `TRANSITION_NOTES.md` - Migration from old to new approach

**Technical References:**
- `docs/LEIDEN_ALGORITHM_TECHNICAL_GUIDE.md` - Complete algorithm specification (53KB)
- `docs/LEIDEN_INTEGRATION_GUIDE.md` - Integration with existing codebase (25KB)
- `docs/LEIDEN_QUICK_REFERENCE.md` - Quick lookup reference
- `docs/EMBEDDING_MODELS_RESEARCH_2024-2025.md` - State-of-the-art embeddings (60+ pages)

**Research Findings:**
- `MECE_RESEARCH_FINDINGS.md` - Complete MECE clustering analysis (15K words)
- `MECE_RESEARCH_SUMMARY.md` - Executive summary

### Implementation Status: COMPLETE ✓

All 4 phases of MECE clustering are **fully implemented and tested**:
1. **Phase 1**: MECE validation module ✓ (`research_agent/claim_analysis/mece_validator.py`)
2. **Phase 2**: Coverage validation ✓ (integrated into `claim_space_optimizer.py`)
3. **Phase 3**: Leiden algorithm clustering ✓ (`research_agent/claim_analysis/graph_mece_clusterer.py`)
4. **Phase 4**: MECE dashboard ✓ (`web_ui/mece_dashboard.py`)

**Test Results**: Run `python test_mece_implementation.py` to verify all systems working.

**How to Use:**
- MECE validation runs automatically during claim clustering
- Check processing logs for MECE scores (0.0-1.0) and grades (A-F)
- Use `GraphMECEClusterer` for cross-document claim clustering
- Generate super-claims from Leiden communities
- View MECE dashboard for quality metrics

**Troubleshooting:**
```bash
# If leidenalg fails to import:
pip uninstall leidenalg python-igraph
pip install --upgrade python-igraph leidenalg

# If plotly not available:
pip install plotly

# Test MECE system:
python test_mece_implementation.py
```

---

## 🚀 Example First-Time Session

```
User: [Starts agent in directory]

You: [Silent check - dependencies not found]
     "Hi! I'm setting up the Research Verification Agent System.
      This will take about 2-3 minutes..."

     [Run: pip install -r requirements.txt]
     [Run: pip install -r requirements-test.txt]
     [Run: pip install -r requirements-neo4j.txt]

     "Python dependencies installed! Installing Neo4j database..."

     [Run: powershell install_neo4j_windows.ps1]
     "Neo4j installation requires administrator approval..."

     [User approves UAC prompt]

     "Dependencies installed! Running system test..."

     [Run: python test_full_pipeline.py]
     [All tests pass]

     "✅ System ready! I can help you:
      - Extract claims from research papers
      - Verify claims using 4 research APIs
      - Build knowledge graphs
      - Investigate claim relationships

      What would you like to do?"

User: "I want to analyze a research paper about mental illness"

You: [Run extraction pipeline]
     "I extracted 21 claims from the paper. Here are the key findings..."
```

---

## 🧪 Testing Commands (You Run These)

```bash
# Full system test (after installation)
python test_full_pipeline.py

# Critical tests (before commits)
python run_tests.py critical

# Quick check
python test_extraction_simple.py

# Individual component test
pytest tests/unit/test_qualifier_extractor.py -v
```

**Don't tell user to run these. You run them automatically.**

---

## 💡 Remember

**Goal**: Zero-friction experience for user

**User workflow**:
1. `git clone <repo>`
2. `cd Research-Assistant-Tool-`
3. `<start agent>` (claude/codex/cursor/aider)
4. [You do everything]
5. User starts using system

**You are the orchestrator. You handle complexity. User stays in their domain.**

---

## 📚 Research APIs Available

- **arXiv**: Preprint server (physics, math, CS, etc.) - No API key
- **CORE**: Open access aggregator - Free
- **OpenAlex**: 250M+ scholarly papers - Free
- **ORKG**: Structured research comparisons - Free

All integrated and ready to use through Python clients in `research_agent/research_apis/`.

---

## 🎓 What This System Does

**Extract Claims**: Reads PDFs, identifies substantive claims, preserves qualifiers

**Build Graphs**: Organizes claims in NetworkX or Neo4j with relationships

**Verify Claims**: Searches research databases for supporting/contradicting evidence

**Investigate**: Uses specialized agents to find evidence, challenges, and analysis

**Cluster**: Groups similar claims, creates super-claims, maintains provenance

---

**You are ready! Start by checking if system is installed, then help the user.** 🚀
