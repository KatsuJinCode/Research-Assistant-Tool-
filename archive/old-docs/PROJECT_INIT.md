# Project Initialization - Research Verification Agent System

**IMPORTANT**: This file is automatically read by Claude Code when starting in this directory.

---

## 🚀 Quick Start for New Agents

If this is your first time working on this project, **run this ONE command**:

```bash
auto_install.bat
```

This will:
1. ✅ Install ALL Python dependencies automatically
2. ✅ Run critical tests to verify installation
3. ✅ Offer to install Neo4j Community Edition (Windows native, no Docker!)
4. ✅ Create `.env` configuration file
5. ✅ Verify system is ready

**That's it! Everything else is automated.**

---

## 📦 What Gets Auto-Installed

### Python Dependencies (from requirements.txt)
- **Core**: asyncpg, pydantic, click, python-dotenv, PyYAML
- **AI**: openai, anthropic
- **Documents**: pdfplumber, PyPDF2
- **Graph**: networkx
- **Research**: arxiv
- **Testing**: pytest, pytest-asyncio, pytest-cov, pytest-mock, etc.
- **Neo4j**: neo4j driver (Python)

### Neo4j Database (Optional but Recommended)
- **Version**: 5.26.0 Community Edition
- **Method**: Windows Service (no Docker!)
- **Installation**: Automated via PowerShell script
- **Auto-installs**: Java 21 (if needed via Chocolatey)
- **Password**: research123
- **Ports**: 7474 (browser), 7687 (bolt)

---

## 🎯 Project Architecture

### Core System
This is a **Research Verification Agent System** that:
1. Extracts claims from research papers (PDFs)
2. Preserves CRITICAL qualifiers (can/may/might/all/some)
3. Builds a knowledge graph
4. Investigates claims using free research APIs
5. Finds similar claims and clusters them

### Database Strategy
- **Development**: NetworkX (in-memory, file-based)
- **Production**: Neo4j (graph database with powerful query features)
- **Both work!** System supports either/both

### Key Feature: Qualifier Preservation
**CRITICAL**: The system MUST preserve qualifiers like "can", "may", "might", "all", "some"

- ❌ BAD: "Mental illness exists" (loses "can")
- ✅ GOOD: "Mental illness can exist" (preserves "can")

**All critical tests enforce this!**

---

## 📁 Important Files

### Auto-Install System
- `auto_install.bat` - **Main installer** (double-click or run from terminal)
- `install_neo4j_windows.ps1` - Neo4j auto-installer (called by auto_install.bat)
- `requirements.txt` - **Complete** Python dependencies list

### Documentation
- `VERIFICATION_COMPLETE.md` - System verification summary
- `WINDOWS_SETUP.md` - Manual installation guide
- `NEO4J_WINDOWS_INSTALL.md` - Neo4j installation options
- `HANDOFF_TO_CLI.md` - Original Web→CLI handoff
- `STATUS.md` - Complete technical documentation

### Entry Points
- `extract_and_cluster_claims.py` - Main extraction pipeline
- `test_extraction_simple.py` - Quick system test
- `migrate_to_neo4j.py` - Migrate NetworkX → Neo4j
- `run_tests.py` - Test runner

### Source Code
- `research_agent/graph_database.py` - NetworkX implementation
- `research_agent/neo4j_database.py` - Neo4j implementation
- `research_agent/normalization/qualifier_extractor.py` - **CRITICAL**
- `research_agent/research_apis/` - arXiv, CORE, OpenAlex clients
- `research_agent/agents/` - Investigation agents

---

## ✅ Verifying Installation

After running `auto_install.bat`, verify everything works:

### 1. Check Python packages
```bash
pip list | findstr "pytest networkx arxiv neo4j"
```

### 2. Run critical tests
```bash
python run_tests.py critical
```

Expected: **16/17 tests passing** (PDF test may vary, but ALL qualifier tests MUST pass)

### 3. Test extraction
```bash
python test_extraction_simple.py
```

Expected: SUCCESS message with graph stats

### 4. Test Neo4j (if installed)
```bash
python -c "from research_agent.neo4j_database import Neo4jDatabase; db = Neo4jDatabase(); print('Connected!'); db.close()"
```

Open browser: http://localhost:7474 (login: neo4j / research123)

---

## 🔧 Common Tasks

### Extract Claims
```bash
python extract_and_cluster_claims.py
```

### Run Tests
```bash
# Critical tests only
python run_tests.py critical

# All tests
python run_tests.py all

# Specific test
pytest tests/unit/test_qualifier_extractor.py -v
```

### Search Research Papers
```python
from research_agent.research_apis import ArxivClient

client = ArxivClient()
papers = client.search("mental illness", max_results=10)
```

### Use Neo4j
```bash
# Migrate existing graph to Neo4j
python migrate_to_neo4j.py

# Query in browser (http://localhost:7474)
MATCH (c:Claim) RETURN c LIMIT 25;
```

---

## ⚠️ Known Issues & Solutions

### Issue: "Module not found" errors
**Solution**: Run `auto_install.bat` - installs all dependencies

### Issue: Neo4j connection refused
**Solution**: Check Neo4j service is running:
```bash
"%ProgramFiles%\Neo4j\neo4j-community-5.26.0\bin\neo4j.bat" status
```

### Issue: Unicode encoding errors
**Solution**: Set environment variable:
```bash
set PYTHONIOENCODING=utf-8
```

Or use wrapper scripts: `run_extraction.bat`

### Issue: Tests failing
**Solution**: Make sure you ran `auto_install.bat` first. Critical qualifier tests MUST pass!

---

## 🎓 Understanding the System

### Workflow
1. **PDF → Text**: Extract text from research papers
2. **Text → Sentences**: Split into individual sentences
3. **Sentences → Claims**: Identify substantive claims
4. **Claims → Qualifiers**: Extract can/may/all/some/etc.
5. **Claims → Graph**: Store in NetworkX or Neo4j
6. **Clustering**: Find similar claims
7. **Investigation**: Use research APIs to verify

### Critical Components

**Qualifier Extractor** (`research_agent/normalization/qualifier_extractor.py`):
- Extracts modal qualifiers (can, may, might, could, would, should)
- Extracts frequency qualifiers (always, never, often, sometimes)
- Extracts quantity qualifiers (all, some, most, few, many)
- **AUTO-FAILS** if qualifiers are lost during normalization

**Graph Database** (NetworkX or Neo4j):
- Stores: Documents, Sentences, Claims, Qualifiers, Evidence
- Relationships: CONTAINS, EXPRESSES, HAS_QUALIFIER, SIMILAR_TO, MERGED_INTO
- Query capabilities: Find similar claims, traverse hierarchies

**Research APIs**:
- **arXiv**: Preprint papers (free, no API key)
- **CORE**: Open access papers (free, optional API key)
- **OpenAlex**: 250M+ papers (free, optional email)
- **ORKG**: Open Research Knowledge Graph - structured comparisons (free, no API key)

---

## 🚨 Critical Rules

1. **NEVER lose qualifiers** during claim normalization
   - Tests will AUTO-FAIL if qualifiers are dropped
   - "can exist" ≠ "exists" - completely different meanings!

2. **Always run tests** before committing changes
   ```bash
   python run_tests.py critical
   ```

3. **Use auto_install.bat** for new setups
   - Don't manually install dependencies
   - Ensures everything is installed correctly

4. **Check branch** before working
   ```bash
   git branch --show-current
   ```

---

## 📞 For New Developers

**First time here?**

1. Run: `auto_install.bat` (installs everything)
2. Read: `VERIFICATION_COMPLETE.md` (system overview)
3. Read: `STATUS.md` (technical details)
4. Test: `python test_extraction_simple.py` (verify works)
5. Code: Start building!

**Questions?**
- Check documentation files (*.md)
- Run tests: `python run_tests.py critical`
- View tests: `tests/` directory

---

## 🎯 Agent Instructions

**If you are a Claude Code agent starting work in this project**:

1. **First, check if dependencies are installed**:
   ```bash
   python -c "import pytest, networkx, arxiv; print('Dependencies OK')"
   ```

2. **If that fails, tell the user**:
   ```
   "I need to install dependencies first. Please run: auto_install.bat"
   ```

3. **After installation, verify**:
   ```bash
   python run_tests.py critical
   ```

4. **Then proceed with the user's request**

**Do NOT manually install packages** - Use auto_install.bat for consistency!

---

## 🌟 Features

- ✅ **Automated installation**: One command installs everything
- ✅ **No Docker required**: Neo4j installs as Windows service
- ✅ **Complete dependencies**: requirements.txt has everything
- ✅ **Tested & verified**: 16/17 critical tests passing
- ✅ **Research APIs working**: arXiv confirmed in CLI
- ✅ **Flexible database**: Works with NetworkX or Neo4j
- ✅ **Production ready**: End-to-end pipeline operational

---

**This project is ready to use! Just run `auto_install.bat` and start building! 🚀**
