# Research Verification Agent System

**AI-powered system for extracting, verifying, and analyzing claims from research papers**

---

## 🚀 Quick Start (For Users)

```bash
# 1. Clone the repository
git clone <repository-url>
cd Research-Assistant-Tool-

# 2. Start your AI agent (any of these work!)
claude        # Claude Code CLI
# or: codex   # OpenAI Codex CLI
# or: cursor  # Cursor AI
# or: aider   # Aider
# or any other AI coding assistant

# 3. That's it! Your agent will:
#    - Install all dependencies automatically
#    - Set up the database
#    - Run tests to verify everything works
#    - Ask what you'd like to do
```

**No Python knowledge required. No manual installation. Works with ANY AI coding agent!**

---

## 💡 What This System Does

### Extract Claims from Research Papers
- Reads PDF research papers
- Identifies substantive claims
- **Preserves critical qualifiers** (can/may/might/all/some)
- Organizes claims in a knowledge graph

### Verify and Investigate Claims
- Searches 4 free research APIs (arXiv, CORE, OpenAlex, ORKG)
- Finds supporting or contradicting evidence
- Builds evidence networks
- Generates citations

### Build Knowledge Graphs
- Clusters similar claims
- Identifies relationships
- Visualizes claim hierarchies
- Supports both NetworkX and Neo4j

---

## 🎯 Example Interactions

### Analyze a Research Paper
```
You: "I want to analyze this research paper"
Agent: [Extracts claims and builds graph]
Agent: "I extracted 21 claims from the paper. Here are the key findings..."
```

### Verify a Claim
```
You: "Is there evidence that mental illness is a social construct?"
Agent: [Searches research databases]
Agent: "I found 8 papers discussing this. Here's what the research shows..."
```

### Explore the Knowledge Graph
```
You: "Show me how these claims are related"
Agent: [Generates visualization]
Agent: "Here's your knowledge graph. I've clustered similar claims together..."
```

---

## 🤖 For AI Agents (Multi-Agent Support!)

**This project works with ANY AI coding assistant:**
- ✅ Claude Code CLI (reads `.claude/CLAUDE.md`)
- ✅ OpenAI Codex CLI (reads `AGENTS.md`)
- ✅ Cursor AI (reads `INSTRUCTIONS.md`)
- ✅ Aider (reads `INSTRUCTIONS.md`)
- ✅ Any other AI agent (reads `INSTRUCTIONS.md` or `README.md`)

**When you start in this directory**, you will automatically:

1. Check if system is installed (silently)
2. If not → Install everything automatically
3. Run comprehensive tests
4. Troubleshoot any issues
5. Present ready system to user

**See agent-specific instructions:**
- `.claude/CLAUDE.md` - Claude Code
- `.codex/CODEX.md` - Codex
- `AGENTS.md` - Codex (official location)
- `INSTRUCTIONS.md` - Universal fallback

**User never needs to know about:**
- Python dependencies
- Installation commands
- Test scripts
- Technical details

**You handle all orchestration. User just expresses intent.**

---

## 🏗️ System Architecture

```
Research Papers (PDF)
        ↓
   [Extraction]
        ↓
  Claims + Qualifiers
        ↓
   [Graph Database]
        ↓
  NetworkX or Neo4j
        ↓
   [Investigation]
        ↓
  Research APIs
  (arXiv, CORE, OpenAlex, ORKG)
        ↓
   [Verification]
        ↓
  Evidence Network
```

---

## 🔑 Key Features

### 1. Qualifier Preservation (Critical!)
The system **never loses** qualifiers like:
- **Modal**: can, may, might, could, would, should
- **Frequency**: always, never, often, sometimes, rarely
- **Quantity**: all, some, most, few, many, several

**Why critical**: "X can cause Y" ≠ "X causes Y" - huge semantic difference!

### 2. Intelligent Deduplication
- Finds similar claims across multiple papers
- Clusters related claims
- Creates super-claims from similar assertions
- Maintains provenance (which document, which sentence)

### 3. Free Research APIs
- **arXiv**: Preprint server (physics, math, CS, etc.)
- **CORE**: Open access aggregator
- **OpenAlex**: 250M+ scholarly papers
- **ORKG**: Structured research comparisons

All free, most require no API key!

### 4. Flexible Database
- **NetworkX**: In-memory, file-based (no setup)
- **Neo4j**: Production graph database (optional)
- System works with both!

---

## 📊 Technical Details (For Developers)

### Dependencies (Auto-Installed by Agent)
- **Python**: 3.11+
- **Core**: networkx, PyPDF2, pdfplumber, arxiv, orkg
- **Testing**: pytest, pytest-asyncio, etc.
- **Optional**: Neo4j 5.26.0 (Windows Service, no Docker)

### Project Structure
```
Research-Assistant-Tool-/
├── .claude/
│   └── CLAUDE.md           # Agent auto-setup instructions
├── research_agent/
│   ├── graph_database.py   # NetworkX implementation
│   ├── neo4j_database.py   # Neo4j implementation
│   ├── normalization/
│   │   └── qualifier_extractor.py  # CRITICAL
│   └── research_apis/
│       ├── arxiv_client.py
│       ├── core_client.py
│       ├── openalex_client.py
│       └── orkg_client.py
├── tests/                  # 60+ unit tests
├── test_full_pipeline.py   # Complete system test
└── sample papers/          # Example PDFs
```

### Testing
```bash
# Full pipeline test (run by agent automatically)
python test_full_pipeline.py

# Critical tests (must always pass)
python run_tests.py critical

# All tests
python run_tests.py all
```

---

## 🎓 Research Applications

### Systematic Literature Reviews
- Extract claims from hundreds of papers
- Identify consensus and disagreements
- Track how claims evolve over time

### Claim Verification
- Cross-reference claims across papers
- Find supporting/contradicting evidence
- Build evidence networks

### Knowledge Graph Construction
- Visualize research landscapes
- Discover hidden connections
- Identify research gaps

---

## 🔧 Advanced Features

### Investigation Agents
- **Support Agent**: Finds supporting evidence
- **Challenge Agent**: Finds contradictions
- **Analysis Agent**: Examines definitions and concepts

### Graph Queries (Neo4j)
```cypher
// Find similar claims
MATCH (c1:Claim)-[:SIMILAR_TO]-(c2:Claim)
WHERE c1.similarity_score > 0.85
RETURN c1, c2

// Claim hierarchies
MATCH (c:Claim)-[:MERGED_INTO]->(sc:SuperClaim)
RETURN sc.text, count(c) as num_claims
```

### Export Formats
- Cypher (Neo4j import)
- GraphML (Gephi, Cytoscape)
- JSON (custom analysis)

---

## 📚 Documentation

For users (via agent):
- Agent handles everything automatically
- No documentation needed!

For developers:
- `STATUS.md` - Complete system status
- `PROJECT_INIT.md` - Technical initialization guide
- `AUTO_INSTALL_COMPLETE.md` - Installation details
- `.claude/CLAUDE.md` - Agent workflow
- `tests/README.md` - Testing guide

---

## 🤝 Contributing

This system is designed for agent-orchestrated workflows. To contribute:

1. Clone repository
2. Start Claude Code or Codex
3. Let agent set everything up
4. Make changes
5. Agent runs tests automatically before commits

---

## 📜 License

[Specify license]

---

## 🙏 Acknowledgments

Built on:
- **Neo4j** - Graph database
- **NetworkX** - Python graph library
- **arXiv** - Open access preprints
- **CORE** - Open access aggregator
- **OpenAlex** - Scholarly metadata
- **ORKG** - Open Research Knowledge Graph

---

## 🎯 Status

**System**: Production Ready
**Installation**: Fully Automated
**Testing**: 60+ Unit Tests + Full Pipeline Test
**Agent Support**: Claude Code, Codex
**Platform**: Windows (with auto-install scripts)

---

**Ready to verify research claims at scale! 🚀**

**Questions?** Start your agent and ask! It knows everything about this system.
