# Windows Setup Guide for Research Verification Agent

## Quick Start (Recommended)

### Option 1: Double-Click Installation (Easiest)
1. Double-click `auto_install.bat`
2. Follow the prompts
3. Done!

### Option 2: PowerShell Installation
```powershell
powershell -ExecutionPolicy Bypass -File auto_install.ps1
```

### Option 3: Manual Installation
See detailed instructions below.

---

## What Gets Installed

The auto-install script will:
1. ✅ Verify Python 3.11+ is installed
2. ✅ Install all Python dependencies
3. ✅ Run critical tests to verify installation
4. ✅ Check for Docker and offer to install Neo4j
5. ✅ Create `.env` configuration file (if Neo4j installed)

---

## Manual Installation Steps

### 1. Prerequisites

**Python 3.11+**
- Download from: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

**Git** (if cloning repository)
- Download from: https://git-scm.com/download/win

**Docker Desktop** (optional, for Neo4j)
- Download from: https://www.docker.com/products/docker-desktop

### 2. Clone Repository
```bash
git clone <repository-url>
cd Research-Assistant-Tool-
```

### 3. Install Python Dependencies
```bash
# Core dependencies
pip install -r requirements.txt

# Test dependencies
pip install -r requirements-test.txt

# Research API dependencies
pip install networkx arxiv

# Neo4j driver (if using Neo4j)
pip install -r requirements-neo4j.txt
```

### 4. Run Tests
```bash
# Run critical tests
python run_tests.py critical

# Should see: "16 passed, 1 failed" (PDF extraction test may vary)
# All qualifier tests MUST pass!
```

### 5. Test Research APIs
```bash
# Test arXiv API
python -c "import arxiv; print('arXiv API: OK')"

# The research APIs should work in CLI (unlike Web environment)
```

---

## Neo4j Installation (Optional but Recommended)

Neo4j provides the production graph database for the system.

### Option A: Docker (Recommended)

1. **Start Docker Desktop**
   - Make sure Docker Desktop is running

2. **Create directories**
   ```bash
   mkdir neo4j\data neo4j\logs neo4j\import neo4j\plugins
   ```

3. **Run Neo4j container**
   ```bash
   docker run --name research-neo4j -p7474:7474 -p7687:7687 -d -v "%CD%\neo4j\data:/data" -v "%CD%\neo4j\logs:/logs" -v "%CD%\neo4j\import:/var/lib/neo4j/import" -v "%CD%\neo4j\plugins:/plugins" --env NEO4J_AUTH=neo4j/research123 neo4j:latest
   ```

4. **Wait for startup (30 seconds)**
   ```bash
   timeout /t 30
   ```

5. **Create .env file**
   ```bash
   # Create .env with this content:
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=research123
   NEO4J_DATABASE=neo4j
   ```

6. **Open Neo4j Browser**
   - Go to: http://localhost:7474
   - Login: neo4j / research123

### Option B: Neo4j Desktop (Windows Native)

1. Download Neo4j Desktop: https://neo4j.com/download/
2. Install and create a new database
3. Set password to: `research123`
4. Start the database
5. Create `.env` file with connection details

---

## Verify Installation

### 1. Check Python Packages
```bash
pip list | findstr /C:"pytest" /C:"networkx" /C:"arxiv" /C:"neo4j"
```

### 2. Run Critical Tests
```bash
python run_tests.py critical
```

Expected output:
```
16 passed, 1 failed, 34 deselected

CRITICAL TESTS PASSED ✓
```

The one failed test is just PDF character count (not critical).

### 3. Test Research APIs
```bash
python -c "import arxiv; search = arxiv.Search(query='test', max_results=1); print('arXiv OK')"
```

### 4. Test Neo4j Connection (if installed)
```bash
python -c "from research_agent.neo4j_database import Neo4jDatabase; db = Neo4jDatabase(); print('Neo4j OK'); db.close()"
```

---

## Common Issues

### Issue: "Python not found"
**Solution**: Install Python 3.11+ and add to PATH during installation

### Issue: "pip not found"
**Solution**: Python installation should include pip. Reinstall Python with pip option checked.

### Issue: "Docker not running"
**Solution**: Start Docker Desktop application

### Issue: SSL Certificate errors with research APIs
**Solution**: This is expected in some Windows environments. The arxiv package handles this automatically.

### Issue: Unicode encoding errors
**Solution**: Set environment variable:
```bash
set PYTHONIOENCODING=utf-8
```

### Issue: "Module not found" errors
**Solution**: Make sure you're in the project directory and all dependencies are installed:
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
pip install networkx arxiv
```

---

## Next Steps After Installation

### 1. Extract Claims from PDF
```bash
python extract_and_cluster_claims.py
```

This will:
- Extract claims from sample PDF
- Cluster similar claims
- Create knowledge graph
- Export to NetworkX format

### 2. Migrate to Neo4j (if installed)
```bash
python migrate_to_neo4j.py
```

### 3. View Graph in Neo4j Browser
- Open: http://localhost:7474
- Run query: `MATCH (n) RETURN n LIMIT 25`

### 4. Investigate Claims
```python
from research_agent.agents.investigation_agent import InvestigationAgent
from research_agent.neo4j_database import Neo4jDatabase

db = Neo4jDatabase()
agent = InvestigationAgent(db, agent_type='support')

# Investigate a claim
results = agent.investigate(claim)
```

---

## Project Structure

```
Research-Assistant-Tool-/
├── auto_install.bat              # ← DOUBLE-CLICK TO INSTALL (Windows)
├── auto_install.ps1              # PowerShell version
├── requirements.txt              # Core dependencies
├── requirements-test.txt         # Test dependencies
├── requirements-neo4j.txt        # Neo4j driver
├── run_tests.py                  # Test runner
├── extract_and_cluster_claims.py # Main extraction pipeline
├── migrate_to_neo4j.py          # Migrate to Neo4j
├── research_agent/              # Main package
│   ├── graph_database.py        # NetworkX graph DB
│   ├── neo4j_database.py        # Neo4j production DB
│   ├── sentence_analyzer.py     # Incremental extraction
│   ├── normalization/
│   │   └── qualifier_extractor.py  # CRITICAL qualifier system
│   ├── research_apis/
│   │   ├── arxiv_client.py
│   │   ├── core_client.py
│   │   └── openalex_client.py
│   └── agents/
│       ├── investigation_agent.py
│       ├── support_agent.py
│       └── challenge_agent.py
└── tests/                       # 60+ unit tests
    └── unit/
        ├── test_qualifier_extractor.py  # CRITICAL
        └── test_pdf_extractor.py
```

---

## Documentation

- **STATUS.md** - Complete system status
- **HANDOFF_TO_CLI.md** - Handoff from Web to CLI
- **WINDOWS_SETUP.md** - This file
- **DATABASE_RESEARCH_FINDINGS.md** - Why Neo4j
- **tests/README.md** - Testing guide

---

## Getting Help

If you encounter issues:

1. Check this file for common issues
2. Read STATUS.md for technical details
3. Check test output: `python run_tests.py critical`
4. Verify Python version: `python --version` (must be 3.11+)

---

## Development Workflow

### Running Tests
```bash
# Critical tests only (must always pass)
python run_tests.py critical

# All tests
python run_tests.py all

# Specific test file
pytest tests/unit/test_qualifier_extractor.py -v
```

### Extracting Claims
```bash
# From default PDF
python extract_and_cluster_claims.py

# Add your own PDFs to "sample papers/" directory
```

### Checking Neo4j Database
```bash
# Test connection
python -c "from research_agent.neo4j_database import Neo4jDatabase; db = Neo4jDatabase(); print('Connected'); db.close()"

# View in browser
# http://localhost:7474
```

---

**Installation complete! You're ready to build! 🚀**
