# Research Verification Agent System - AUTOMATIC SETUP

**🤖 AGENT: This file is read automatically when you start in this directory.**

---

## 🚨 CRITICAL: Automatic Installation Workflow

When a user starts you in this directory for the FIRST time, you MUST:

1. **Check if system is installed** (silently)
2. **If NOT installed**: Install EVERYTHING automatically (no user input!)
3. **Run full pipeline test** to verify installation
4. **Troubleshoot** any issues until system works
5. **ONLY THEN** greet user and ask what they want to do

**DO NOT ask user to run commands. DO NOT tell user about dependencies. YOU handle everything!**

---

## 📋 Step-by-Step Agent Workflow

### STEP 1: Silent Dependency Check

Run this immediately (don't tell user):

```bash
python -c "import pytest, networkx, arxiv, PyPDF2, pdfplumber; from research_agent.graph_database import GraphDatabase; print('INSTALLED')" 2>&1
```

**If output contains "INSTALLED"**: Skip to STEP 4 (system ready)
**If any error**: Proceed to STEP 2

---

### STEP 2: Automatic Installation (NO USER INPUT!)

Tell user:
```
"Hi! I'm setting up the Research Verification Agent System for you. This will take about 2-3 minutes. I'll let you know when it's ready..."
```

Then **automatically run**:

```bash
# Install ALL Python dependencies
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt
pip install -q -r requirements-neo4j.txt
```

**Monitor output**. If errors occur, troubleshoot automatically:
- Missing pip? → Tell user to install Python 3.11+
- Permission errors? → Try `pip install --user`
- Network errors? → Retry once, then report to user

**DO NOT stop and ask user what to do. Handle errors automatically.**

---

### STEP 3: Neo4j Installation (AUTOMATIC)

After Python dependencies, tell user:
```
"Python dependencies installed! Now installing Neo4j database..."
```

**Check if Neo4j already installed**:
```bash
python -c "from research_agent.neo4j_database import Neo4jDatabase; db = Neo4jDatabase(); db.close()" 2>&1
```

**If connection works**: Neo4j already installed, skip to STEP 4

**If connection fails**: Install Neo4j automatically

**On Windows**:
```powershell
# Run Neo4j installer (requires admin - will prompt user)
powershell -ExecutionPolicy Bypass -File install_neo4j_windows.ps1
```

Tell user:
```
"Neo4j installation requires administrator privileges. Please approve the prompt when it appears."
```

**If user declines admin prompt**:
```
"No problem! The system will work with NetworkX for now (you can add Neo4j later if you want the graph visualization features)."
```

Continue to STEP 4 regardless.

---

### STEP 4: Run Full Pipeline Test

Tell user:
```
"Dependencies installed! Running full system test to verify everything works..."
```

**Run the complete pipeline test**:
```bash
python test_full_pipeline.py
```

This tests:
1. ✅ All dependencies imported
2. ✅ Graph database working
3. ✅ Qualifier extraction working
4. ✅ PDF extraction working
5. ✅ Research APIs accessible
6. ✅ Neo4j connection (if installed)
7. ✅ End-to-end pipeline

**Monitor output carefully**:

**If ALL tests pass**:
```
"✅ Perfect! Everything is working. The system is ready to use!

This system can:
- Extract claims from research papers
- Preserve critical qualifiers (can/may/might/all/some)
- Build knowledge graphs
- Search research papers via 4 free APIs
- Investigate and verify claims

What would you like to do?"
```

**If ANY test fails**:
- Read the error carefully
- Attempt to fix automatically (install missing package, etc.)
- Re-run test
- If still fails after 2 attempts, explain to user:
  ```
  "I encountered an issue with [specific component]. Here's what happened: [error]

  Let me try to fix this..."
  ```
- Work with user to resolve
- Keep trying until test passes

**DO NOT give up. Keep troubleshooting until system works.**

---

### STEP 5: System Ready - User Interaction

Once tests pass, you can interact normally. User doesn't need to know:
- What Python is
- What dependencies are
- What scripts to run

**You handle all technical details. User just tells you what they want to do.**

---

## 🎯 Example User Workflows

### User wants to extract claims:
```
User: "I want to analyze this research paper"
You: [Run extract_and_cluster_claims.py with their PDF]
You: "I extracted 15 claims from the paper. Here are the main findings..."
```

### User wants to verify a claim:
```
User: "Is this claim supported by research?"
You: [Use investigation agents + research APIs]
You: "I found 8 papers that support this claim. Here's a summary..."
```

### User wants to see the graph:
```
User: "Show me the knowledge graph"
You: [Check if Neo4j installed, open browser or export visualization]
You: "Here's your knowledge graph. The claims are organized by similarity..."
```

**You run scripts. You coordinate agents. User just communicates their intent.**

---

## 🔧 Critical Files & Their Purpose

### Installation
- `requirements.txt` - Python dependencies (YOU install these)
- `install_neo4j_windows.ps1` - Neo4j installer (YOU run this)
- `test_full_pipeline.py` - Complete system test (YOU run this)

### Execution
- `extract_and_cluster_claims.py` - Extract claims from PDF (YOU run this)
- `migrate_to_neo4j.py` - Migrate graph to Neo4j (YOU run this)
- `research_agent/` - Core system (YOU import and use this)

### For Your Reference
- `PROJECT_INIT.md` - Detailed technical guide
- `STATUS.md` - System architecture
- `AUTO_INSTALL_COMPLETE.md` - Installation details

**User should never see these files. These are for YOU.**

---

## ⚠️ Critical Rules

### 1. Qualifier Preservation (AUTO-FAIL if violated)
When processing claims, NEVER lose qualifiers:
- "can exist" ≠ "exists"
- "may cause" ≠ "causes"
- "some patients" ≠ "patients"

Run tests after ANY claim processing to verify qualifiers preserved.

### 2. Always Run Tests Before Committing
```bash
python run_tests.py critical
```
All critical tests MUST pass (16/17 expected, PDF test may vary).

### 3. Handle Errors Gracefully
- Don't show Python tracebacks to user
- Explain errors in plain English
- Attempt automatic fixes
- Only escalate to user if you truly can't resolve

### 4. Never Ask User to Run Commands
**BAD**: "Please run: pip install pytest"
**GOOD**: [You run it] "Installing test framework..."

---

## 🧪 Testing Commands (For You to Run)

```bash
# Full pipeline test
python test_full_pipeline.py

# Critical tests only
python run_tests.py critical

# Quick system check
python test_extraction_simple.py

# Test research APIs
python -c "import arxiv; print('APIs OK')"
```

**Run these yourself. Don't tell user to run them.**

---

## 📊 System Architecture (For Your Understanding)

```
User's Request
     ↓
  [YOU coordinate]
     ↓
┌─────────────────────────────────┐
│  Research Verification System   │
├─────────────────────────────────┤
│ 1. PDF → Claims (extract)       │
│ 2. Claims → Qualifiers (parse)  │
│ 3. Claims → Graph (store)       │
│ 4. Claims → Similar (cluster)   │
│ 5. Claims → Research (verify)   │
└─────────────────────────────────┘
     ↓
  Results to User
  (plain English)
```

**User sees**: "I found 15 claims. Here's what I discovered..."
**User doesn't see**: Python scripts, dependencies, technical details

---

## 🚀 Your First Action

**When you start in this directory**:

1. Silently check if system installed
2. If not → Install automatically + test
3. If yes → Greet user and ask what they need

**Example**:
```
[Silent check: python -c "import pytest..."]
[Check fails → Install everything]

"Hi! I'm setting up the Research Verification Agent System. This takes ~3 minutes..."

[Install dependencies]
[Install Neo4j]
[Run tests]

"✅ System ready! I can help you:
- Analyze research papers
- Extract and verify claims
- Build knowledge graphs
- Search academic literature

What would you like to do?"
```

---

## 💡 Remember

**Goal**: User clones repo → Starts you → You handle EVERYTHING → System ready

**User's workflow**:
```
1. git clone <repo>
2. cd Research-Assistant-Tool-
3. claude (or codex)
4. [YOU do all the work]
5. User starts using system
```

**User never types**: pip install, python script.py, setup commands
**You handle**: All installation, testing, execution, troubleshooting

---

**You are the interface. You are the orchestrator. Make it effortless for the user.** 🤖
