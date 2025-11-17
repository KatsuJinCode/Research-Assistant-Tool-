# Research Verification Agent System - Project Instructions

## 🚀 IMPORTANT: Read This First!

**Before doing ANY work in this project, read `PROJECT_INIT.md`** - it contains:
- One-command auto-install instructions (`auto_install.bat`)
- Complete dependency list
- System architecture overview
- Critical rules and testing requirements

## Auto-Install for New Agents

If dependencies are not installed, **immediately tell the user**:

```
"I need to install project dependencies first. Please run: auto_install.bat

This will automatically install:
- All Python dependencies
- Neo4j Community Edition (optional)
- Run tests to verify installation

Would you like me to explain what this does, or would you prefer to run it now?"
```

**DO NOT manually install dependencies** - Use `auto_install.bat` for consistency!

## Quick Dependency Check

At the start of any session, run:

```bash
python -c "import pytest, networkx, arxiv, PyPDF2; print('✓ Dependencies installed')"
```

If this fails, dependencies are missing. Tell user to run `auto_install.bat`.

## Critical Rules

1. **Qualifier Preservation is CRITICAL**
   - NEVER lose qualifiers (can/may/might/all/some) during processing
   - Tests will AUTO-FAIL if qualifiers are dropped
   - See: `research_agent/normalization/qualifier_extractor.py`

2. **Always Run Tests Before Committing**
   ```bash
   python run_tests.py critical
   ```
   16/17 tests must pass (PDF test may vary)

3. **Use Auto-Install System**
   - `auto_install.bat` for Windows users
   - Installs Python deps + Neo4j in one command

4. **Neo4j: No Docker Needed!**
   - Windows native installation via PowerShell
   - Automated via `install_neo4j_windows.ps1`
   - User just runs `auto_install.bat`

## Key Files

- `PROJECT_INIT.md` - **READ THIS FIRST!**
- `auto_install.bat` - One-command installer
- `VERIFICATION_COMPLETE.md` - System verification status
- `STATUS.md` - Complete technical documentation

## Testing

```bash
# Critical tests (must always pass)
python run_tests.py critical

# Quick system test
python test_extraction_simple.py

# All tests
python run_tests.py all
```

## Common User Requests

### "Install dependencies"
→ "Please run: `auto_install.bat`"

### "Set up Neo4j"
→ "Run `auto_install.bat` and answer 'y' when it asks about Neo4j"

### "Run tests"
→ `python run_tests.py critical`

### "Extract claims"
→ `python extract_and_cluster_claims.py`

## Agent Workflow

1. **Check dependencies** (run import test)
2. **If missing**: Tell user to run `auto_install.bat`
3. **If installed**: Proceed with user's request
4. **Before committing**: Run `python run_tests.py critical`

---

**This project has automated installation. Always use `auto_install.bat` instead of manual pip installs!**
