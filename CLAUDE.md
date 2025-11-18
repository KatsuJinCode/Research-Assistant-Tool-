# CLAUDE.md

This file provides guidance to AI coding assistants when working with code in this repository.

**Compatible with**: Claude Code CLI, Codex CLI, Cursor, GitHub Copilot, and other AI development tools.

## Project Overview

Research Assistant Tool: An intelligent AI-powered research assistant for gathering, analyzing, and synthesizing information from documents. Currently in **CLI version** (v0.1) with web version planned.

**Dual-provider AI support**: OpenAI (ChatGPT) and Anthropic (Claude) models.

## Architecture

### Current Implementation (CLI)
- **Core**: Python 3.7+ CLI application with SQLite database
- **Main entry point**: `cli_assistant_enhanced.py` (uses `ai_helper.py` for AI features)
- **Wrapper scripts**: `research.sh` (macOS/Linux), `research.bat` (Windows)
- **Database**: SQLite at `./data/research.db` with tables: projects, documents, notes
- **AI providers**:
  - OpenAI: GPT-3.5-turbo, GPT-4-turbo, GPT-4o
  - Anthropic: Claude 3.5 Sonnet (default), Claude 3 Opus, Claude 3 Haiku
- **Configuration**: `.research_config` file in project root

### Future Implementation (Web)
- **Backend**: FastAPI + PostgreSQL (planned, skeleton exists in `backend/`)
- **Frontend**: Next.js 14 + TypeScript + Tailwind (planned, skeleton exists in `frontend/`)
- **See**: PROJECT_PLAN.md for detailed roadmap

## Key Components

### CLI Application (`cli_assistant.py` & `cli_assistant_enhanced.py`)
- `SimpleResearchAssistant` class: Core document/project management with SQLite
- Database schema: projects, documents (with content_hash for deduplication), notes
- Document support: .txt, .md files (PDF planned)
- Search: Full-text SQLite LIKE queries with snippet extraction

### AI Helper (`ai_helper.py`)
- `AIHelper` class: Multi-provider AI abstraction layer
- Provider switching: Reads `DEFAULT_PROVIDER` from `.research_config`
- Methods: `summarize()`, `answer_question()`, `extract_key_points()`, `suggest_tags()`
- Graceful degradation: Falls back to simple algorithms when no API key configured

### Setup System
- Interactive setup: `setup.sh` (Linux/macOS), `setup.bat` (Windows)
- Auto-installs dependencies: `openai` and `anthropic` Python packages
- Guides user through API key configuration and model selection
- Creates `.research_config` with chosen provider and credentials

## Common Development Commands

### Setup and Configuration
```bash
# Interactive setup (recommended - configures API keys)
./setup.sh              # Linux/macOS
setup.bat               # Windows

# Manual dependency install
pip install openai anthropic
```

### Running the CLI
```bash
# Using wrapper scripts (auto-checks dependencies)
./research.sh <command> [args]     # Linux/macOS
research.bat <command> [args]      # Windows

# Direct Python execution
python3 cli_assistant_enhanced.py <command> [args]
```

### Available CLI Commands
```bash
# Project management
create-project <name> --description "text"
list-projects
summary <project_id>

# Document operations
add-document <project_id> <file_path>
view <doc_id>
search <query> [--project <id>]

# AI features (require API key)
summarize <doc_id>
ask <doc_id> "question"
keypoints <doc_id> [--num 10]
auto-tag <doc_id>
```

### Backend Development (Future/Planned)
```bash
# Backend (FastAPI)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (Next.js)
cd frontend
npm install
npm run dev
```

### Testing
```bash
# Run demo with sample documents
./demo.sh

# Backend tests (when implemented)
cd backend
pytest
```

## Important Implementation Details

### Multi-Provider AI System
- **Configuration file**: `.research_config` stores API keys and model preferences
- **Provider selection**: `DEFAULT_PROVIDER` can be "openai" or "anthropic"
- **Model fallback**: If API call fails, falls back to simple non-AI algorithms
- **Key validation**: Setup scripts validate API key format (`sk-` for OpenAI, `sk-ant-` for Anthropic)

### Document Processing
- **Deduplication**: Uses SHA256 `content_hash` to prevent duplicate documents
- **Metadata storage**: JSON field stores source file info (path, type, size)
- **Content extraction**: Currently reads .txt/.md as UTF-8, tries text mode for unknown types
- **Chunking**: Not yet implemented (planned for web version with embeddings)

### Database Schema
```sql
-- Projects: Top-level organization
projects: id, name, description, created_at

-- Documents: Stored content with deduplication
documents: id, project_id, title, content, content_hash (UNIQUE),
           file_path, metadata (JSON), created_at

-- Notes: User annotations
notes: id, document_id, content, tags (JSON), created_at
```

### Search Implementation
- **Current**: Simple SQLite `LIKE '%query%'` with context snippets (±100 chars)
- **Planned**: Vector embeddings with pgvector for semantic search (Phase 3 in PROJECT_PLAN.md)

## Configuration Files

### `.research_config` Format
```bash
# Example with both providers
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-3.5-turbo"
ANTHROPIC_API_KEY="sk-ant-..."
ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
DEFAULT_PROVIDER="anthropic"
```

### Environment Variables (Web Version)
- Backend uses `.env` file with `pydantic-settings`
- See `backend/app/core/config.py` for available settings
- Key settings: `DATABASE_URL`, `OPENAI_API_KEY`, `CORS_ORIGINS`

## Cross-Platform Support

### Windows-Specific
- **Batch files**: `setup.bat`, `research.bat` provide equivalent functionality to .sh scripts
- **Path handling**: Python code uses `pathlib.Path` for cross-platform paths
- **Line endings**: Git configured for CRLF on Windows (see recent commits)

### Common Gotchas
- **Python command**: Scripts use `python3` on Unix, `python` on Windows
- **Script execution**: Unix scripts need `chmod +x`, Windows uses `.bat` directly
- **Database location**: Always `./data/research.db` relative to project root

## Development Workflow

### Phase Status
- **Phase 0 (CLI)**: ✅ Complete and working
- **Phase 1-8 (Web)**: 📋 Planned (see PROJECT_PLAN.md for detailed phases)

### Code Quality Standards
- Type hints for function signatures
- Docstrings for classes and public methods
- Error handling with try/except and graceful degradation
- User-friendly messages (✓, ⚠, ❌ prefixes for status)

### Git Workflow
- Main branch: `claude/init-project-planning-014JiiquZLEGyHPcCMzRT85Z`
- Recent focus: Multi-provider AI support, Windows compatibility, setup automation
- Conventional commits preferred

## Testing Strategy

### Current Testing
- Manual testing via `demo.sh` with sample documents in `sample_documents/`
- Sample docs: `ai_research.txt`, `climate_change.txt`

### Planned Testing (Web Version)
- Backend: pytest, pytest-asyncio (requirements-dev.txt)
- Frontend: Playwright for E2E tests (package.json)
- Target coverage: >80%

## External Dependencies

### Python Packages (CLI)
- **Required**: None (core features work without external deps)
- **AI features**: `openai>=1.0.0`, `anthropic>=0.21.0`
- Installed automatically by setup scripts

### Python Packages (Backend - Planned)
- See `backend/requirements.txt` for complete list
- Key: FastAPI, SQLAlchemy 2.0, LangChain, sentence-transformers

### Node Packages (Frontend - Planned)
- See `frontend/package.json`
- Key: Next.js 14, React Query, Zustand, Tailwind CSS

## Documentation Resources

- **QUICKSTART.md**: 60-second getting started guide
- **MULTI_PROVIDER_GUIDE.md**: Detailed AI provider configuration
- **CLI_README.md**: Complete CLI command reference
- **USAGE_EXAMPLES.md**: Real-world usage workflows
- **PROJECT_PLAN.md**: Full 8-phase development roadmap with architecture
- **ROADMAP.md**: High-level timeline and milestones

## Current Limitations

- **File formats**: Only .txt and .md currently supported (PDF planned)
- **Search**: Basic text matching only (semantic search planned)
- **Collaboration**: Single-user only (multi-user planned for web version)
- **Storage**: Local SQLite only (PostgreSQL planned for web version)
- **Performance**: No caching, rate limiting, or optimization (planned for web version)
