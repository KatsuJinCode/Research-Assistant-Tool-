# Codex CLI - Agent Instructions

**📄 This file references the master instructions to prevent sync issues.**

**Official Codex location** - See [AGENT_INSTRUCTIONS.md](./AGENT_INSTRUCTIONS.md) for complete workflow

---

## ⚡ Quick Reference for Codex

See **[AGENT_INSTRUCTIONS.md](./AGENT_INSTRUCTIONS.md)** for complete, up-to-date instructions.

---

## 🚀 TL;DR

1. **Silently check** if system installed
2. **If not**: Auto-install everything
3. **Run** `python test_full_pipeline.py`
4. **Troubleshoot** until working
5. **Then** interact with user

**User should NEVER run commands - you handle everything!**

---

## 📋 Essential Commands

### Check Installation
```bash
python -c "import pytest, networkx, arxiv, PyPDF2, pdfplumber; from research_agent.graph_database import GraphDatabase; print('INSTALLED')" 2>&1
```

### Install Dependencies
```bash
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt
pip install -q -r requirements-neo4j.txt
```

### Install Neo4j (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File install_neo4j_windows.ps1
```

### Run Tests
```bash
python test_full_pipeline.py
```

---

## ⚠️ Critical Rules

1. **Qualifier Preservation** - NEVER lose can/may/might/all/some
2. **No User Commands** - You run everything
3. **Test Before Commit** - `python run_tests.py critical`
4. **Handle Errors Gracefully** - Plain English, no tracebacks

---

**For complete workflow, see**: [AGENT_INSTRUCTIONS.md](./AGENT_INSTRUCTIONS.md)
