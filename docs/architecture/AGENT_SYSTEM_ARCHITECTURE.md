# Research Verification Agent Swarm - System Architecture

## Vision

An autonomous multi-agent system that analyzes research papers, extracts claims, and uses specialized agents with different frameworks and philosophies to verify, challenge, expand, and cross-reference claims with evidence-based citations in APA format.

## Core Principles

1. **Autonomous Investigation**: Agents spawn sub-investigations recursively as new claims emerge
2. **Framework Diversity**: Different agents approach claims with distinct epistemological frameworks
3. **Evidence-Based**: All conclusions must cite sources in APA format
4. **Adversarial Verification**: Some agents support, some challenge, ensuring robust analysis
5. **Cross-Domain Discovery**: Agents actively search for relevant insights from unexpected fields
6. **Chain of Reasoning**: Each investigation creates a traceable chain of claims → evidence → counter-claims

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLI Interface Layer                         │
│  (Human commands: ingest, analyze, verify, explore, report)    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   Orchestrator Agent                            │
│  - Manages agent lifecycle and task distribution               │
│  - Coordinates investigation chains                             │
│  - Prevents infinite loops and manages resources                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
┌───────────────────▼───┐   ┌─────────▼──────────────┐
│  Document Processor   │   │  Investigation Engine  │
│  - Extract claims     │   │  - Spawn agents        │
│  - Parse structure    │   │  - Track chains        │
│  - Identify entities  │   │  - Synthesize results  │
└───────────────────┬───┘   └─────────┬──────────────┘
                    │                 │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼────────┐  ┌──────▼─────────┐
│ Claim Analyzer │  │ Agent Framework │  │ Evidence Store │
│ - Categorize   │  │ - Agent factory │  │ - Citations    │
│ - Prioritize   │  │ - Specialized   │  │ - Sources      │
│ - Link claims  │  │   agents        │  │ - Provenance   │
└────────────────┘  └────────┬────────┘  └────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
        ┌───────▼──────┐ ┌──▼────┐ ┌────▼─────────┐
        │ Support      │ │Neutral│ │ Challenge    │
        │ Agents       │ │Agents │ │ Agents       │
        │ - Confirm    │ │-Analyze│ │ - Refute     │
        │ - Strengthen │ │-Explore│ │ - Critique   │
        │ - Expand     │ │-Connect│ │ - Alternative│
        └──────────────┘ └───────┘ └──────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
            ┌───────▼──────┐  ┌──────▼────────┐
            │ Data Layer   │  │ AI Providers  │
            │ - SQLite     │  │ - OpenAI      │
            │ - File Store │  │ - Anthropic   │
            └──────────────┘  └───────────────┘
```

## Agent Types and Frameworks

### 1. Orchestrator Agent
**Role**: Master coordinator
**Responsibilities**:
- Parse user commands
- Spawn and manage specialized agents
- Prevent investigation loops
- Aggregate findings
- Generate final reports

### 2. Document Processor Agents

#### ClaimExtractorAgent
**Framework**: Structural Analysis
**Purpose**: Break down papers into discrete claims
**Output**: List of claims with metadata (type, confidence, dependencies)

#### EntityRecognizerAgent
**Framework**: Named Entity Recognition
**Purpose**: Identify key terms, concepts, people, organizations
**Output**: Entity graph for cross-referencing

### 3. Verification Agents (Support Framework)

#### SupportAgent_Empirical
**Framework**: Empirical Verification
**Philosophy**: "What evidence confirms this?"
**Tasks**:
- Find studies that support the claim
- Locate replication studies
- Check for meta-analyses
- Cite quantitative evidence (APA format)

#### SupportAgent_Theoretical
**Framework**: Theoretical Coherence
**Philosophy**: "How does this fit existing theory?"
**Tasks**:
- Find theoretical frameworks supporting the claim
- Identify foundational literature
- Map claim to established models
- Cite theoretical sources (APA format)

#### SupportAgent_CrossDomain
**Framework**: Interdisciplinary Validation
**Philosophy**: "What other fields confirm this?"
**Tasks**:
- Search related but distinct domains
- Find parallel discoveries
- Identify convergent evidence
- Cite cross-domain sources (APA format)

### 4. Challenge Agents (Adversarial Framework)

#### ChallengeAgent_Empirical
**Framework**: Empirical Falsification
**Philosophy**: "What evidence contradicts this?"
**Tasks**:
- Find contradictory studies
- Identify failed replications
- Locate null results
- Cite counter-evidence (APA format)

#### ChallengeAgent_Methodological
**Framework**: Methodological Critique
**Philosophy**: "Are the methods sound?"
**Tasks**:
- Analyze study design flaws
- Identify confounding variables
- Check statistical validity
- Cite methodological critiques (APA format)

#### ChallengeAgent_Alternative
**Framework**: Alternative Explanations
**Philosophy**: "What else could explain this?"
**Tasks**:
- Propose alternative theories
- Find competing models
- Identify rival hypotheses
- Cite alternative frameworks (APA format)

### 5. Neutral Agents (Analytical Framework)

#### AnalysisAgent_Historical
**Framework**: Historical Context
**Philosophy**: "How has understanding evolved?"
**Tasks**:
- Trace claim evolution over time
- Identify paradigm shifts
- Map historical debates
- Cite historical sources (APA format)

#### AnalysisAgent_Definitional
**Framework**: Conceptual Clarity
**Philosophy**: "What exactly does this mean?"
**Tasks**:
- Clarify ambiguous terms
- Identify operational definitions
- Resolve semantic confusion
- Cite definitional sources (APA format)

#### AnalysisAgent_Scope
**Framework**: Boundary Analysis
**Philosophy**: "Where does this apply?"
**Tasks**:
- Define scope and limitations
- Identify boundary conditions
- Map applicability
- Cite scope studies (APA format)

### 6. Discovery Agents (Exploratory Framework)

#### DiscoveryAgent_Lateral
**Framework**: Lateral Thinking
**Philosophy**: "What unexpected connections exist?"
**Tasks**:
- Search tangentially related fields
- Find analogous phenomena
- Identify metaphorical connections
- Cite surprising sources (APA format)

#### DiscoveryAgent_Emerging
**Framework**: Cutting Edge
**Philosophy**: "What's the latest research?"
**Tasks**:
- Find recent preprints
- Identify emerging trends
- Locate frontier research
- Cite newest sources (APA format)

## Data Models

### Claim Model
```python
class Claim:
    id: UUID
    source_document_id: UUID
    text: str
    claim_type: ClaimType  # empirical, theoretical, methodological, normative
    confidence: float  # 0.0-1.0
    dependencies: List[UUID]  # other claims this depends on
    entities: List[Entity]
    status: ClaimStatus  # pending, investigating, verified, challenged, uncertain
    created_at: datetime
    parent_claim_id: Optional[UUID]  # if spawned from another investigation
```

### Investigation Model
```python
class Investigation:
    id: UUID
    claim_id: UUID
    agent_id: str
    agent_framework: FrameworkType
    status: InvestigationStatus  # running, completed, failed
    findings: List[Finding]
    spawned_investigations: List[UUID]  # recursive investigations
    created_at: datetime
    completed_at: Optional[datetime]
```

### Finding Model
```python
class Finding:
    id: UUID
    investigation_id: UUID
    finding_type: FindingType  # support, challenge, neutral, expansion
    summary: str
    confidence: float
    evidence: List[Evidence]
    counter_claims: List[Claim]  # new claims generated
```

### Evidence Model
```python
class Evidence:
    id: UUID
    finding_id: UUID
    source_type: SourceType  # paper, book, dataset, expert_opinion
    citation_apa: str  # Full APA format citation
    quote: Optional[str]
    relevance_score: float
    credibility_score: float
    url: Optional[str]
    doi: Optional[str]
    accessed_date: datetime
```

### InvestigationChain Model
```python
class InvestigationChain:
    id: UUID
    root_claim_id: UUID
    chain_depth: int
    nodes: List[ChainNode]  # claims → investigations → findings → new claims
    created_at: datetime
```

## Agent Communication Protocol

### Message Types
```python
class AgentMessage:
    - SPAWN_INVESTIGATION: Request new agent
    - REPORT_FINDING: Share discovery
    - REQUEST_INFO: Query other agents
    - CLAIM_GENERATED: New claim found
    - INVESTIGATION_COMPLETE: Done
    - RESOURCE_REQUEST: Need more compute/API calls
```

### Agent State Machine
```
CREATED → INITIALIZED → INVESTIGATING → REPORTING → COMPLETED
                ↓           ↓              ↓
            FAILED ←──  BLOCKED  ←─── PAUSED
```

## Processing Pipeline

### Phase 1: Ingestion
```
1. User uploads research paper (PDF/DOC/TXT)
2. DocumentProcessorAgent extracts text
3. ClaimExtractorAgent identifies claims
4. EntityRecognizerAgent maps entities
5. Claims stored in DB with metadata
```

### Phase 2: Initial Investigation
```
1. OrchestratorAgent analyzes claims
2. Prioritizes claims by importance/controversy
3. Spawns initial agent swarm (3 Support, 3 Challenge, 2 Neutral per claim)
4. Each agent begins investigation
```

### Phase 3: Evidence Gathering
```
1. Agents search literature (via AI + APIs)
2. Extract relevant passages
3. Generate APA citations
4. Score evidence quality
5. Report findings to orchestrator
```

### Phase 4: Recursive Investigation
```
1. Agents generate counter-claims or sub-claims
2. OrchestratorAgent decides which to investigate
3. Spawns new specialized agents
4. Tracks investigation depth (max depth: configurable)
5. Continues until convergence or resource limit
```

### Phase 5: Synthesis
```
1. OrchestratorAgent aggregates all findings
2. Builds investigation chain visualization
3. Generates comprehensive report:
   - Original claims
   - Supporting evidence with citations
   - Challenging evidence with citations
   - Alternative perspectives
   - Unexplored connections
   - Confidence scores
   - Knowledge gaps
```

## CLI Commands

```bash
# Ingest a research paper
python research_agent.py ingest paper.pdf --project "Climate Science"

# Analyze and extract claims
python research_agent.py analyze-claims --doc-id 123

# Launch investigation swarm
python research_agent.py investigate --claim-id 456 --depth 3 --agent-count 8

# View investigation status
python research_agent.py status --investigation-id 789

# Generate report
python research_agent.py report --claim-id 456 --format markdown

# Explore a specific claim with custom agents
python research_agent.py explore --claim-id 456 --frameworks "empirical,theoretical,lateral"

# View investigation chain
python research_agent.py chain --claim-id 456 --visualize

# Export findings with citations
python research_agent.py export --investigation-id 789 --format "apa" --output findings.md
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Refactor current codebase for agent architecture
- [ ] Implement data models (Claim, Investigation, Finding, Evidence)
- [ ] Create SQLite schema with tables
- [ ] Build OrchestratorAgent base class
- [ ] Implement AgentMessage protocol

### Phase 2: Document Processing (Week 3)
- [ ] Build ClaimExtractorAgent
- [ ] Implement EntityRecognizerAgent
- [ ] PDF/DOC parsing pipeline
- [ ] Claim categorization logic
- [ ] Entity relationship mapping

### Phase 3: Core Agent Framework (Week 4-5)
- [ ] Create BaseAgent class
- [ ] Implement agent lifecycle management
- [ ] Build agent factory pattern
- [ ] Create SupportAgent_Empirical
- [ ] Create ChallengeAgent_Empirical
- [ ] Create AnalysisAgent_Definitional

### Phase 4: Evidence & Citations (Week 6)
- [ ] Literature search integration (Semantic Scholar API, arXiv, PubMed)
- [ ] APA citation generator
- [ ] Evidence quality scoring
- [ ] Source credibility assessment
- [ ] Citation deduplication

### Phase 5: Remaining Agents (Week 7-8)
- [ ] Implement all 9 specialized agent types
- [ ] Test each agent framework independently
- [ ] Create agent configuration system
- [ ] Build agent performance metrics

### Phase 6: Investigation Chains (Week 9)
- [ ] Recursive investigation spawning
- [ ] Chain depth limiting
- [ ] Cycle detection
- [ ] Resource management (API limits, compute)
- [ ] Investigation convergence detection

### Phase 7: Reporting & Visualization (Week 10)
- [ ] Investigation chain visualizer
- [ ] Markdown report generator
- [ ] Evidence summary builder
- [ ] Confidence score calculator
- [ ] Export to multiple formats

### Phase 8: Optimization & Testing (Week 11-12)
- [ ] Agent parallelization
- [ ] Caching strategies
- [ ] Performance profiling
- [ ] Integration tests
- [ ] End-to-end workflow tests

## Technology Stack (Updated)

### Core
- **Python 3.11+**: Async support for concurrent agents
- **SQLite**: Local database (can upgrade to PostgreSQL later)
- **Pydantic**: Data validation and models
- **asyncio**: Concurrent agent execution

### AI/ML
- **OpenAI API**: GPT-4 for complex reasoning
- **Anthropic API**: Claude for long document analysis
- **LangChain**: Agent framework and tools
- **tiktoken**: Token counting and management

### Document Processing
- **PyPDF2/pdfplumber**: PDF extraction
- **python-docx**: Word document parsing
- **spaCy**: NLP and entity recognition
- **sentence-transformers**: Semantic similarity

### Literature Search
- **Semantic Scholar API**: Academic paper search
- **arXiv API**: Preprint access
- **PubMed API**: Medical/life sciences
- **CrossRef API**: DOI resolution and citations

### CLI
- **click** or **typer**: Rich CLI framework
- **rich**: Beautiful terminal output
- **tqdm**: Progress bars for long operations

### Utilities
- **loguru**: Structured logging
- **tenacity**: Retry logic for API calls
- **httpx**: Async HTTP client

## Configuration File

```yaml
# research_agent_config.yaml

orchestrator:
  max_concurrent_agents: 10
  max_investigation_depth: 5
  resource_limits:
    max_api_calls_per_claim: 100
    max_total_tokens: 1000000
    timeout_per_agent_minutes: 30

ai_providers:
  default: anthropic
  openai:
    model: gpt-4-turbo
    api_key: ${OPENAI_API_KEY}
  anthropic:
    model: claude-3-5-sonnet-20241022
    api_key: ${ANTHROPIC_API_KEY}

agents:
  claim_extractor:
    model: anthropic
    temperature: 0.3
  support_empirical:
    model: openai
    temperature: 0.5
  challenge_empirical:
    model: openai
    temperature: 0.5
  discovery_lateral:
    model: anthropic
    temperature: 0.8

literature_search:
  semantic_scholar:
    enabled: true
    max_results: 20
  arxiv:
    enabled: true
    max_results: 10
  pubmed:
    enabled: true
    max_results: 10

citations:
  format: apa7
  include_abstract: false
  include_keywords: true

output:
  default_format: markdown
  include_confidence_scores: true
  include_investigation_chains: true
  visualization_engine: graphviz
```

## Example Workflow

```bash
# 1. Ingest a paper on climate change
$ python research_agent.py ingest climate_paper.pdf --project "Climate Analysis"
✓ Document processed: climate_paper.pdf
✓ Extracted 12 claims
✓ Identified 45 entities

# 2. View extracted claims
$ python research_agent.py list-claims --doc-id 1
Claim 1: "Global temperatures have increased 1.1°C since pre-industrial times"
  Type: Empirical | Confidence: 0.95 | Entities: [global temperature, pre-industrial]

Claim 2: "Renewable energy can meet 100% of energy needs by 2050"
  Type: Predictive | Confidence: 0.65 | Entities: [renewable energy, 2050]

# 3. Investigate a specific claim
$ python research_agent.py investigate --claim-id 2 --depth 3
⚙ Starting investigation swarm (8 agents)...
  → SupportAgent_Empirical: Searching for evidence...
  → ChallengeAgent_Methodological: Analyzing feasibility...
  → DiscoveryAgent_CrossDomain: Exploring economics literature...

[Progress bar: 3/8 agents completed]

✓ Investigation complete (Investigation ID: 789)
  - 24 findings
  - 67 citations
  - 3 counter-claims generated
  - 2 recursive investigations spawned

# 4. View results
$ python research_agent.py report --investigation-id 789
```

**Generated Report Preview:**
```markdown
# Investigation Report: Claim 2

## Original Claim
"Renewable energy can meet 100% of energy needs by 2050"

## Investigation Summary
- Duration: 15 minutes
- Agents deployed: 8
- Evidence items: 67
- Investigation depth: 3

## Supporting Evidence (Confidence: 0.72)

### Empirical Support
- Jacobson, M. Z., et al. (2017). 100% clean and renewable wind, water, and sunlight
  all-sector energy roadmaps for 139 countries of the world. *Joule*, 1(1), 108-121.
  https://doi.org/10.1016/j.joule.2017.07.005

  > "We find that the 139 countries...can transition to 100% WWS across all energy
  > sectors by 2050."

  Relevance: 0.95 | Credibility: 0.88

### Theoretical Support
- Brown, T. W., et al. (2018). Response to 'Burden of proof: A comprehensive review
  of the feasibility of 100% renewable-electricity systems'. *Renewable and
  Sustainable Energy Reviews*, 92, 834-847.

## Challenging Evidence (Confidence: 0.68)

### Methodological Challenges
- Clack, C. T., et al. (2017). Evaluation of a proposal for reliable low-cost grid
  power with 100% wind, water, and solar. *Proceedings of the National Academy of
  Sciences*, 114(26), 6722-6727. https://doi.org/10.1073/pnas.1610381114

  > "Errors in the WWS study...include inappropriate modeling assumptions,
  > insufficient grid reliability, and infeasible technology deployment."

  Relevance: 0.93 | Credibility: 0.90

## Counter-Claims Generated
1. "Grid stability requires dispatchable power beyond renewables" (Investigating...)
2. "Energy storage technology gaps prevent 100% renewable transition by 2050"

## Cross-Domain Insights
- Economics: Cost curves favor rapid deployment (Lazard, 2023)
- Materials Science: Rare earth supply chains present bottleneck (IEA, 2021)
- Policy Studies: Political feasibility varies by region (IPCC, 2022)

## Knowledge Gaps
- Long-duration energy storage (>100 hours) at scale
- Grid interconnection infrastructure requirements
- Social acceptance and behavioral change factors

## Overall Assessment
Confidence: 0.70 (Moderately Supported with Significant Caveats)

The claim is supported by multiple roadmap studies but faces substantial
methodological critiques regarding grid reliability and technology deployment
timelines. Success depends heavily on assumptions about energy storage
advancement and policy implementation.
```

## Next Steps

1. Review and approve this architecture
2. Decide on initial agent types to implement (recommend starting with 3-4)
3. Refactor existing codebase or start fresh?
4. Set up development environment with new dependencies
5. Begin Phase 1 implementation

## Questions for Clarification

1. **Scope**: Should agents search the open web or only academic databases?
2. **API Costs**: What's the budget for AI API calls per investigation?
3. **Depth**: What's the maximum investigation chain depth?
4. **Timing**: How fast should investigations complete (minutes vs hours)?
5. **Human-in-loop**: Should agents ask for approval before spawning sub-investigations?
6. **Storage**: SQLite sufficient or need PostgreSQL from the start?
7. **Output**: Primary format for reports (Markdown, PDF, web dashboard)?
