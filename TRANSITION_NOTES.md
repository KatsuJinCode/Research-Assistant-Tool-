# Transition Notes for Continuing in Claude Code Web Interface

## Current State Summary

### ✅ What We've Completed

1. **Full System Architecture** - `REVISED_ARCHITECTURE.md`
   - Pull-based agent work queue system
   - PostgreSQL database design with hybrid hierarchical storage
   - 11 specialized agent types with different frameworks
   - Dual-source evidence system (academic + web)
   - Investigation chains and claim relationships

2. **Philosophy Framework System** - `AGENT_PHILOSOPHY_AND_NORMALIZATION.md`
   - Configurable agent cognition (8 pre-built frameworks)
   - ClaimNormalizer agent design
   - Presupposition and context tracking
   - Investigation tree visualization
   - Word document export system

3. **ClaimNormalizer Research** - `CLAIM_NORMALIZER_RESEARCH.md`
   - Academic research on argument mining, Toulmin model, SRL
   - 6-layer context preservation system
   - Multi-stage normalization pipeline
   - Human-in-the-loop validation
   - Learning system from user corrections
   - Hybrid database structure for recursive claims

4. **MVP Roadmap** - `MVP_ROADMAP.md`
   - **CRITICAL ACKNOWLEDGMENTS**:
     - Qualifier terms (can/will/mostly/often) must be preserved
     - Confidence scores drive adaptive investigation depth
   - 6-week implementation plan
   - Phase-by-phase deliverables
   - Test success criteria

5. **Compatibility Documentation** - `AI_CODING_ASSISTANT_COMPATIBILITY.md`
   - Confirmed: Works with Claude Code CLI, Codex CLI, Cursor, etc.
   - CLAUDE.md is universal guide

6. **Updated CLAUDE.md**
   - Compatible with all AI coding assistants
   - Project overview and architecture
   - Common commands and development workflow

## 🎯 Where We Are Now

**Phase**: Ready to begin **Phase 1: Foundation Implementation**

**Next Immediate Tasks**:
1. Create database schema file (`database/schema_v1_mvp.sql`)
2. Create database setup script (`database/setup.sh`)
3. Create configuration template (`config/config.yaml`)
4. Set up Python project structure

**Current Todo List Status**:
- [x] Document qualifier and confidence score systems
- [x] Create MVP implementation roadmap
- [ ] **IN PROGRESS**: Implement Phase 1: Core database schema
- [ ] Implement Phase 2: Basic claim extraction
- [ ] Implement Phase 3: Simple normalization
- [ ] Implement Phase 4: Basic investigation agents
- [ ] Test MVP end-to-end pipeline

## 📋 What to Tell Claude Code Web Interface

When you continue, provide this context:

```
We're building a Research Verification Agent System - an autonomous multi-agent
system that analyzes research papers, extracts claims, and uses specialized agents
to verify/challenge/expand claims with evidence.

CRITICAL DESIGN PRINCIPLES:
1. Qualifier terms (can/will/mostly/often/all/some) MUST be preserved - auto-fail if lost
2. Confidence scores at every stage - low confidence triggers more investigation
3. Pull-based work queue - agents discover work, don't spawn recursively
4. Human-in-the-loop for claim normalization
5. PostgreSQL with hybrid hierarchical structure

CURRENT PHASE: Phase 1 - Foundation (Week 1-2)
We need to implement:
1. PostgreSQL database schema (see MVP_ROADMAP.md Phase 1)
2. Configuration system
3. AI client wrapper (OpenAI + Anthropic)
4. CLI framework
5. Database connection

FILES TO READ FIRST:
- MVP_ROADMAP.md (implementation plan)
- REVISED_ARCHITECTURE.md (full system design)
- CLAIM_NORMALIZER_RESEARCH.md (normalization details)

START WITH: Create database/schema_v1_mvp.sql based on the MVP schema in MVP_ROADMAP.md
```

## 📁 Files You'll Need to Reference

### Core Architecture Documents
1. **REVISED_ARCHITECTURE.md** - Full system architecture
2. **AGENT_PHILOSOPHY_AND_NORMALIZATION.md** - ClaimNormalizer + philosophy frameworks
3. **CLAIM_NORMALIZER_RESEARCH.md** - Research-backed normalization design
4. **MVP_ROADMAP.md** - 6-week implementation plan with code examples

### Configuration & Compatibility
5. **AI_CODING_ASSISTANT_COMPATIBILITY.md** - Tool compatibility
6. **CLAUDE.md** - Universal AI assistant guide

### Original Planning (For Reference)
7. **AGENT_SYSTEM_ARCHITECTURE.md** - Original recursive design (superseded by REVISED)
8. **PROJECT_PLAN.md** - Original web app plan (now CLI-focused)

## 🔑 Key Decisions Made

### Technology Stack (MVP)
- **Database**: PostgreSQL (not SQLite) - chosen for complex queries, concurrency
- **AI Providers**: OpenAI + Anthropic (multi-provider support)
- **Interface**: CLI first (not web) - faster to build
- **Language**: Python 3.11+
- **PDF Processing**: pdfplumber
- **Academic Search**: Semantic Scholar, arXiv, PubMed (Phase 6)

### Architecture Patterns
- **Agent System**: Pull-based work queue (NOT recursive spawning)
- **Claim Hierarchy**: Hybrid (adjacency list + materialized path + ltree + closure table)
- **Normalization**: Human-in-the-loop with learning system
- **Investigation**: Autonomous background agents with configurable philosophies

### MVP Scope (What's IN)
✅ PDF ingestion
✅ Claim extraction (LLM-based)
✅ Qualifier preservation (CRITICAL)
✅ Human-validated normalization
✅ 3 agent types (Support, Challenge, Analysis)
✅ Evidence with APA citations
✅ Confidence scoring
✅ Markdown reports

### MVP Scope (What's OUT - Post-MVP)
❌ Real academic API search (Phase 6)
❌ Philosophy frameworks (Phase 7)
❌ Advanced normalization with SRL (Phase 8)
❌ Tree visualization (Phase 9)
❌ Word document export (Phase 9)

## 🚀 Recommended First Actions

### Option A: Continue Implementation
```bash
# Tell Claude Code:
"Let's continue implementing Phase 1.
Create database/schema_v1_mvp.sql with the MVP schema from MVP_ROADMAP.md.
Focus on: documents, claims, claim_qualifiers, agents, investigations, findings, evidence."
```

### Option B: Review & Refine
```bash
# Tell Claude Code:
"Review the MVP_ROADMAP.md and suggest any improvements before we start coding.
Are there any edge cases we haven't considered for qualifier preservation?"
```

### Option C: Quick Prototype
```bash
# Tell Claude Code:
"Let's build a quick proof-of-concept for the qualifier extraction system.
Create normalization/qualifier_extractor.py with the regex patterns for
modals, frequency adverbs, and quantifiers."
```

## ⚠️ Important Reminders for Claude Code

1. **Qualifier Preservation is CRITICAL**
   - Test case: "AI can improve most tasks" → normalized MUST keep "can" and "most"
   - Auto-fail any normalization that loses qualifiers

2. **Confidence Thresholds Matter**
   - <0.60 = Low → trigger more agents
   - 0.60-0.84 = Medium → standard investigation
   - 0.85-1.0 = High → can proceed

3. **Human-in-the-Loop is Required**
   - Never auto-approve normalizations without user review
   - User feedback teaches the system

4. **Database is PostgreSQL, Not SQLite**
   - We need pgvector, ltree extensions
   - Concurrent agent access is important

## 📊 Project Statistics

- **Total Architecture Docs**: 6 major documents
- **Lines of Design Work**: ~8,000 lines
- **Database Tables Designed**: 25+ (full system), 8 (MVP)
- **Agent Types Designed**: 11 (full), 3 (MVP)
- **Implementation Phases**: 10 phases total, 5 phases for MVP
- **Estimated MVP Timeline**: 6 weeks
- **Lines of Code to Write (MVP)**: ~3,000-4,000 estimated

## ✅ Ready to Transition

**Yes, we're ready!** All architecture decisions are documented. The MVP roadmap is clear with specific deliverables and code examples.

When you continue in Claude Code web interface, it will have access to all the markdown files we created, and can start implementing based on the detailed plans in MVP_ROADMAP.md.

## 🎯 Immediate Next Step

```python
# First file to create:
"database/schema_v1_mvp.sql"

# Contents: The simplified MVP schema from MVP_ROADMAP.md Phase 1
# Tables: documents, claims, claim_qualifiers, agents, investigations,
#         findings, evidence, normalization_validations
```

Good luck with the implementation! The foundation is solid. 🚀
