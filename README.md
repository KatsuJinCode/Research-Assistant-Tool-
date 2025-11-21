# Research Verification Agent System

**AI-powered system for extracting, verifying, and analyzing claims from research papers with interactive web UI**

---

## 🚀 Quick Start (For Users)

```bash
# 1. Clone the repository
git clone <repository-url>
cd Research-Assistant-Tool-

# 2. Start the web interface
cd web_ui
python app.py

# 3. Open your browser
http://localhost:5000

# 4. Start exploring!
#    - Upload PDF research papers
#    - Extract and visualize claims
#    - Ask the AI assistant questions
#    - Track provenance for all data
```

**Or use with ANY AI coding assistant:**
```bash
claude        # Claude Code CLI
# or: codex   # OpenAI Codex CLI
# or: cursor  # Cursor AI
# or: aider   # Aider
```

---

## 💡 What This System Does

### 🌐 Interactive Web Interface
- **Real-time graph visualization** with D3.js force-directed layout
- **Tab-based navigation** (Documents, Search, Agents, Projects)
- **Draggable panel system** for customizable layout
- **AI chat assistant** powered by Claude Code
- **WebSocket live updates** for real-time collaboration
- **Context-aware interface** that adapts to your workflow

### 📄 Extract Claims from Research Papers
- Reads PDF research papers
- Identifies substantive claims using LLM extraction
- **Preserves critical qualifiers** (can/may/might/all/some)
- Organizes claims in a knowledge graph
- **Tracks provenance** for every claim and document

### 🔍 Verify and Investigate Claims
- Searches 4 free research APIs (arXiv, CORE, OpenAlex, ORKG)
- **Semantic similarity matching** for evidence discovery
- **LLM-based classification** (support/contradict)
- **Automatic evidence linking** after processing
- Builds evidence networks with confidence scores

### 🤖 AI Agent System
- **Document Processor Agent**: Extracts claims and evidence
- **Document Finder Agent**: Multi-source document discovery
- **Background Agents**: Asynchronous processing with live status
- **Agent Transcript Logging**: Full activity capture with provenance
- **AI Chat Assistant**: Context-aware conversational interface

### 🔗 Build Knowledge Graphs
- Clusters similar claims using semantic embeddings
- Identifies relationships and evidence links
- Visualizes claim hierarchies with interactive graph
- Supports both NetworkX and Neo4j databases

### 🎯 Provenance Tracking
- **Full lineage**: Every node tracks creating agent and discovery chain
- **Verification system**: Cross-link validation ensures data integrity
- **Audit trail**: Complete history of all agent activities
- **Trust scores**: Track confidence and investigation value

---

## 🎨 Web Interface Features

### Tab Navigation System
- **Documents Tab**: Browse all documents, claims, and evidence
- **Search Tab**: Text search, semantic search, LLM-powered search
- **Agents Tab**: Monitor active/completed/failed background agents
- **Projects Tab**: Organize research into separate workspaces

### Draggable Panels
- **Resize left panel**: Drag horizontal divider (250-600px)
- **Resize AI assistant**: Drag vertical divider (150-500px)
- **Panel sizes persist** across sessions via localStorage

### AI Chat Assistant
- **Context-aware**: Knows active tab and selected nodes
- **Natural language**: Ask questions conversationally
- **Quick actions**: Find Similar, Analyze, Suggest buttons
- **Approval system**: Confirms before modifying data
- **Real-time responses**: Powered by Claude Code CLI

### Real-Time Updates
- **WebSocket integration**: Live graph updates
- **Agent monitoring**: Real-time status of background tasks
- **Event notifications**: Toast messages for important events
- **Progress tracking**: Visual indicators for long operations

### User Settings
- **Similarity threshold**: Configurable (0.5-0.9) for evidence matching
- **Embedding model**: 6 choices from fast to multilingual
  - ⚡ MiniLM-L6 (fastest, 384-dim)
  - ⚖️ MiniLM-L12 (balanced, 384-dim)
  - ✨ MPNet (recommended, 768-dim)
  - 🔬 DistilRoBERTa (premium, 768-dim)
  - 🌍 Multilingual MPNet (50+ languages, 768-dim)
  - 🎯 MS MARCO (search-optimized, 768-dim)

---

## 🎯 Example Interactions

### Analyze a Research Paper
```
1. Click "Upload Documents" button
2. Select PDF file
3. System extracts claims automatically
4. View results in interactive graph
5. Click nodes to see details
```

### Ask the AI Assistant
```
You: "Find documents about machine learning"
AI: "I found 3 documents related to machine learning. Would you like me to filter the graph?"

You: "What claims are most important to investigate?"
AI: "Based on investigation scores, these 5 claims need attention..."

You: "Show me evidence supporting this claim"
AI: "Here are 4 pieces of evidence with confidence scores..."
```

### Track Provenance
```
1. Select any node in the graph
2. View "Created by" agent information
3. Click agent ID to see full transcript
4. See complete lineage chain
5. Verify data integrity
```

---

## 🤖 For AI Agents (Multi-Agent Support!)

**This project works with ANY AI coding assistant:**
- ✅ Claude Code CLI (reads `.claude/CLAUDE.md`)
- ✅ OpenAI Codex CLI (reads `AGENTS.md`)
- ✅ Cursor AI (reads `INSTRUCTIONS.md`)
- ✅ Aider (reads `INSTRUCTIONS.md`)
- ✅ Any other AI agent (reads `INSTRUCTIONS.md` or `README.md`)

**Agent Configuration** (`web_ui/agent_config.py`):
- Supports multiple CLI adapters
- Easy to add custom adapters
- Environment variable or config file selection
- Defaults to Claude Code

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web UI (Flask + SocketIO)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Tab Navigation  │  AI Assistant  │  Graph Viz (D3)  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Repository Pattern (Backend/Database)           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Claim Repo  │  Document Repo  │  Event Emitter     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Neo4j Graph Database                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Documents  →  Claims  →  Evidence  +  Provenance    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Agent System                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Doc Processor  │  Doc Finder  │  AI Assistant       │   │
│  │  Transcript Logs  │  Provenance  │  CLI Adapters     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              External APIs & Services                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  arXiv  │  CORE  │  OpenAlex  │  ORKG  │  LLMs      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Features

### 1. Qualifier Preservation (Critical!)
The system **never loses** qualifiers like:
- **Modal**: can, may, might, could, would, should
- **Frequency**: always, never, often, sometimes, rarely
- **Quantity**: all, some, most, few, many, several

**Why critical**: "X can cause Y" ≠ "X causes Y" - huge semantic difference!

### 2. Complete Provenance Tracking
Every node in the graph tracks:
- **created_by**: Agent type (document_processor, document_finder)
- **created_by_agent_id**: Unique agent instance ID
- **discovered_by**: Optional discoverer agent type
- **discovered_by_agent_id**: Optional discoverer instance ID
- **Full transcript**: Complete agent activity log with timestamps

Verification system ensures:
- All provenance links are valid
- No orphaned nodes without agent transcripts
- Cross-references work in both directions

### 3. Semantic Evidence Matching
- **Embedding-based similarity**: Uses sentence-transformers
- **Configurable threshold**: User controls precision/recall trade-off
- **Multiple models**: From fast (MiniLM) to premium (DistilRoBERTa)
- **Automatic linking**: Evidence matched after document processing
- **LLM classification**: Support/contradict/neutral determination

### 4. Agent Transcript System
Complete activity logging:
- **Agent lifecycle**: created → active → completed/failed
- **Timestamped events**: Every action logged with microsecond precision
- **Structured data**: JSON-based with rich metadata
- **File persistence**: Transcripts saved to disk by default
- **API access**: Query transcripts and agent-created nodes

### 5. Free Research APIs
- **arXiv**: Preprint server (physics, math, CS, etc.)
- **CORE**: Open access aggregator
- **OpenAlex**: 250M+ scholarly papers
- **ORKG**: Structured research comparisons

All free, most require no API key!

### 6. Flexible Database
- **NetworkX**: In-memory, file-based (no setup)
- **Neo4j**: Production graph database (current default)
- System works with both!

---

## 📊 Technical Details (For Developers)

### Dependencies (Auto-Installed by Agent)
- **Python**: 3.11+
- **Backend**: Flask, Flask-SocketIO, eventlet
- **Database**: neo4j-driver, networkx
- **AI/ML**: sentence-transformers, anthropic
- **PDF Processing**: PyPDF2, pdfplumber
- **Research APIs**: arxiv, orkg
- **Testing**: pytest, pytest-asyncio
- **Optional**: Neo4j 5.26.0 (Windows Service)

### Project Structure
```
Research-Assistant-Tool-/
├── .claude/
│   └── CLAUDE.md                    # Agent auto-setup
├── backend/
│   └── database/
│       ├── repositories/            # Repository pattern
│       │   ├── claim_repository.py
│       │   └── document_repository.py
│       ├── event_emitter.py         # WebSocket events
│       └── neo4j_client.py          # Database connection
├── research_agent/
│   ├── graph_database.py            # NetworkX
│   ├── neo4j_database.py            # Neo4j
│   ├── transcript_manager.py        # NEW: Agent logging
│   ├── provenance_verifier.py       # NEW: Verification
│   ├── normalization/
│   │   └── qualifier_extractor.py   # CRITICAL
│   └── research_apis/
│       ├── arxiv_client.py
│       ├── core_client.py
│       ├── openalex_client.py
│       └── orkg_client.py
├── web_ui/
│   ├── app.py                       # Flask application
│   ├── agent_config.py              # NEW: Multi-CLI support
│   ├── document_processor.py        # Agent orchestration
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   │       ├── tab_manager.js       # NEW: Tab navigation
│   │       ├── panel_manager.js     # NEW: Draggable panels
│   │       ├── ai_assistant.js      # NEW: Chat interface
│   │       └── header_manager.js    # NEW: Unified header
│   └── templates/
│       └── index.html               # Main UI
├── docs/
│   └── TAB_SYSTEM_ARCHITECTURE.md   # NEW: UI architecture
├── tests/                           # 60+ unit tests
│   ├── test_provenance_unit.py      # NEW: Provenance tests
│   └── test_provenance_simple_integration.py  # NEW
├── test_full_pipeline.py            # Complete system test
└── sample papers/                   # Example PDFs
```

### API Endpoints

**Core Endpoints:**
- `GET /api/graph` - Get full graph data
- `POST /api/upload-document` - Upload PDF
- `POST /api/process-document` - Extract claims
- `GET /api/documents` - List all documents
- `GET /api/claims` - List all claims

**Provenance Endpoints:**
- `GET /api/nodes/<id>/provenance` - Get node provenance
- `GET /api/agents/<id>/transcript` - Get agent transcript
- `GET /api/agents/<id>/created-nodes` - Get agent's nodes

**Assistant Endpoint:**
- `POST /api/assistant/chat` - AI chat assistant

**Settings Endpoints:**
- `POST /api/update-confidence` - Update claim confidence
- `POST /api/create-manual-claim` - Create claim via chat

### Testing
```bash
# Full pipeline test (run by agent automatically)
python test_full_pipeline.py

# Critical tests (must always pass)
python run_tests.py critical

# Provenance tests (23 tests)
pytest tests/test_provenance_unit.py -v
pytest tests/test_provenance_simple_integration.py -v

# All tests
python run_tests.py all
```

---

## 🎓 Research Applications

### Systematic Literature Reviews
- Extract claims from hundreds of papers
- Identify consensus and disagreements
- Track how claims evolve over time
- Visualize research landscape interactively

### Claim Verification
- Cross-reference claims across papers
- Find supporting/contradicting evidence
- Build evidence networks with semantic matching
- Track confidence and investigation scores

### Knowledge Graph Construction
- Visualize research landscapes
- Discover hidden connections via graph traversal
- Identify research gaps through missing links
- Export to standard formats (Cypher, GraphML, JSON)

### Research Transparency
- Complete provenance tracking
- Audit trail for all data
- Reproducible workflows
- Trust verification system

---

## 🔧 Advanced Features

### Investigation Agents
- **Support Agent**: Finds supporting evidence
- **Challenge Agent**: Finds contradictions
- **Analysis Agent**: Examines definitions and concepts
- **All logged**: Full transcripts with provenance

### Graph Queries (Neo4j)
```cypher
// Find similar claims
MATCH (c1:Claim)-[:SIMILAR_TO]-(c2:Claim)
WHERE c1.similarity_score > 0.85
RETURN c1, c2

// Claim hierarchies with provenance
MATCH (c:Claim)-[:MERGED_INTO]->(sc:SuperClaim)
RETURN sc.text, sc.created_by_agent_id, count(c) as num_claims

// Get agent's created nodes
MATCH (n)
WHERE n.created_by_agent_id = $agent_id
RETURN n

// Verify provenance chain
MATCH (d:Document)<-[:DISCOVERED]-(c:Claim)
WHERE d.discovered_by_agent_id = c.created_by_agent_id
RETURN d, c
```

### Export Formats
- Cypher (Neo4j import)
- GraphML (Gephi, Cytoscape)
- JSON (custom analysis)
- Agent Transcripts (JSON logs)

---

## 📚 Documentation

### For Users
- Interactive web UI at `http://localhost:5000`
- AI assistant for help and guidance
- Contextual tooltips throughout UI

### For Developers
- `STATUS.md` - Complete system status
- `PROJECT_INIT.md` - Technical initialization guide
- `docs/TAB_SYSTEM_ARCHITECTURE.md` - UI architecture
- `.claude/CLAUDE.md` - Agent workflow
- `tests/README.md` - Testing guide
- `AGENT_INSTRUCTIONS.md` - Agent setup guide

---

## 🤝 Contributing

This system is designed for agent-orchestrated workflows. To contribute:

1. Clone repository
2. Start Claude Code or Codex
3. Let agent set everything up
4. Make changes
5. Agent runs tests automatically before commits

**Key areas for contribution:**
- Additional research API integrations
- Enhanced semantic matching algorithms
- More visualization options
- Additional agent types
- Performance optimizations

---

## 📜 License

[Specify license]

---

## 🙏 Acknowledgments

Built on:
- **Neo4j** - Graph database
- **NetworkX** - Python graph library
- **Flask + SocketIO** - Web framework with real-time updates
- **D3.js** - Interactive graph visualization
- **Sentence-Transformers** - Semantic embeddings
- **Claude Code** - AI assistant backend
- **arXiv** - Open access preprints
- **CORE** - Open access aggregator
- **OpenAlex** - Scholarly metadata
- **ORKG** - Open Research Knowledge Graph

---

## 🎯 Current Status

**System**: ✅ Production Ready
**Web UI**: ✅ Fully Functional with Tab Navigation + AI Assistant
**Provenance**: ✅ Complete with Verification System
**Testing**: ✅ 60+ Unit Tests + 23 Provenance Tests
**Agent Support**: ✅ Claude Code, OpenAI, Gemini, Custom
**Platform**: ✅ Windows (with auto-install scripts)
**Database**: ✅ Neo4j (default) + NetworkX (fallback)

### Recent Major Features (2025)
- ✨ Interactive web UI with real-time updates
- 🎨 Tab navigation system with draggable panels
- 🤖 AI chat assistant powered by Claude Code
- 🔗 Complete provenance tracking with verification
- 🧠 Semantic evidence matching with configurable models
- 📝 Agent transcript logging with file persistence
- ⚙️ User-configurable settings UI
- 🔍 Document finder agent with multi-source support

---

**Ready to verify research claims at scale with full transparency! 🚀**

**Questions?**
- Start the web UI: `cd web_ui && python app.py`
- Ask the AI assistant in the bottom-left panel
- Or start your AI agent and ask - it knows everything!
