# Research Verification Agent System - Universal Agent Instructions

**🤖 SINGLE SOURCE OF TRUTH - All agent-specific files reference this master document**

**For: Claude Code, Codex CLI, Cursor, Aider, and all AI coding assistants**

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

### Step 1: Silent Check
```bash
python -c "import pytest, networkx, arxiv, PyPDF2, pdfplumber; from research_agent.graph_database import GraphDatabase; print('INSTALLED')" 2>&1
```

- If "INSTALLED" appears → Skip to Step 4
- If error → Continue to Step 2

### Step 2: Install Python Dependencies
```bash
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt
pip install -q -r requirements-neo4j.txt
```

Tell user: *"Setting up the Research Verification Agent System (2-3 minutes)..."*

### Step 3: Install Neo4j (Optional but Recommended)
```bash
# Check if Neo4j already working
python -c "from research_agent.neo4j_database import Neo4jDatabase; db = Neo4jDatabase(); db.close()" 2>&1
```

If fails (not installed):
```powershell
# On Windows
powershell -ExecutionPolicy Bypass -File install_neo4j_windows.ps1
```

Note: Requires admin privileges. If user declines, system works with NetworkX instead.

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
