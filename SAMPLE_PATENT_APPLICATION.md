# SAMPLE PATENT APPLICATION

## SYSTEMS AND METHODS FOR AUTOMATED RESEARCH CLAIM EXTRACTION WITH SEMANTIC QUALIFIER PRESERVATION

---

## PATENT APPLICATION

**Application Type:** Utility Patent
**Technology Field:** Computer-Implemented Research Analysis Systems
**International Classification:** G06F 16/00 (Information Retrieval), G06N 20/00 (Machine Learning)

---

## ABSTRACT

A computer-implemented system and method for extracting, normalizing, and verifying research claims from scientific literature while preserving critical semantic qualifiers. The system employs natural language processing to identify modal, frequency, and quantitative qualifiers (e.g., "may," "can," "some," "most") that modify claim certainty, and maintains these qualifiers throughout claim extraction, deduplication, and knowledge graph construction processes. A multi-agent investigation framework automatically searches academic databases to identify supporting and contradicting evidence for extracted claims, generating confidence scores and research gap analyses. The system constructs a hierarchical knowledge graph representing relationships between documents, claims, evidence, and qualifiers, enabling semantic search and contradiction detection across large research corpora.

**Word Count:** 118 words

---

## BACKGROUND OF THE INVENTION

### Field of the Invention

[0001] This invention relates generally to computer-implemented systems for processing and analyzing research literature, and more specifically to systems that extract research claims from documents while preserving semantic qualifiers that affect claim meaning and certainty.

### Description of Related Art

[0002] Researchers conducting literature reviews face significant challenges in tracking hundreds or thousands of research claims across multiple documents. Traditional document management systems treat research papers as unstructured text files, requiring manual extraction and interpretation of individual claims.

[0003] Existing citation management tools (e.g., Zotero, Mendeley) focus on bibliographic metadata but do not extract or analyze individual claims within papers. Search engines provide keyword matching but cannot identify when claims contradict each other or when subtle qualifier words change claim meaning.

[0004] Prior art in automated claim extraction typically uses natural language processing to identify declarative statements in research papers. However, these systems suffer from critical deficiencies:

[0005] **Loss of Semantic Qualifiers:** Existing systems often normalize or remove qualifier words during text processing. For example, systems may treat "Treatment X cures disease Y" and "Treatment X may cure disease Y" as equivalent claims, when the word "may" fundamentally changes the claim's certainty and evidentiary requirements.

[0006] **Lack of Hierarchical Claim Organization:** Prior systems store claims as flat lists without capturing relationships between similar claims, parent-child conceptual hierarchies, or supporting/contradicting evidence networks.

[0007] **Manual Evidence Gathering:** Researchers must manually search for papers that support or contradict each claim, a time-consuming process that limits the scope of literature reviews.

[0008] **No Automated Contradiction Detection:** Existing systems cannot identify when different papers make contradictory claims about the same topic, requiring researchers to manually cross-reference hundreds of papers.

[0009] There remains a need for an automated system that: (1) preserves critical semantic qualifiers during claim extraction; (2) constructs hierarchical knowledge graphs showing claim relationships; (3) automatically searches for supporting and contradicting evidence; and (4) detects contradictions and research gaps across large document corpora.

---

## BRIEF SUMMARY OF THE INVENTION

[0010] The present invention provides systems and methods for automated extraction, normalization, and verification of research claims from scientific literature while preserving semantic qualifiers that affect claim meaning.

[0011] In one embodiment, a computer-implemented method comprises: receiving a research document in electronic format; extracting text from the document using optical character recognition or native text extraction; analyzing the extracted text using a natural language processing model to identify candidate claim sentences; for each candidate claim, detecting semantic qualifiers including modal verbs (can, may, might, could, should, would), frequency adverbs (always, often, sometimes, rarely, never), and quantifiers (all, most, many, some, few, none); storing each claim in a structured database with associated qualifier metadata; comparing each claim to previously stored claims using semantic similarity analysis; when similarity exceeds a threshold, creating a merged "super-claim" node while preserving all original qualifier variations; and constructing a knowledge graph with nodes representing documents, claims, super-claims, and qualifiers, and edges representing containment, similarity, and hierarchical relationships.

[0012] In another embodiment, a multi-agent investigation system comprises: a coordinator agent that receives a target claim and generates an investigation plan; a support agent that searches academic databases for papers providing supporting evidence for the claim; a challenge agent that searches for papers providing contradicting evidence; an analysis agent that calculates a confidence score based on quantity and quality of supporting versus contradicting evidence; and a report generator that produces a structured output identifying research gaps, contradiction patterns, and recommended follow-up investigations.

[0013] In a further embodiment, the system detects contradictions by: identifying pairs of claims with high semantic similarity (above a threshold such as 0.8); comparing their associated qualifiers and polarity (positive vs. negative); when claims have opposite polarity or conflicting qualifiers, flagging as a contradiction; and notifying users of the contradiction with links to source documents.

[0014] The invention provides several technical advantages: preserves semantic meaning during automated text processing; enables identification of research gaps and contradictions at scale; reduces manual effort in literature review by 50-80%; and constructs queryable knowledge graphs for complex research questions.

---

## BRIEF DESCRIPTION OF THE DRAWINGS

[0015] **FIG. 1** is a system architecture diagram showing major components including document processor, claim extractor, qualifier detector, knowledge graph builder, and multi-agent investigator.

[0016] **FIG. 2** is a flowchart illustrating the claim extraction process with qualifier preservation.

[0017] **FIG. 3** is a data structure diagram showing the hierarchical knowledge graph schema with document, claim, super-claim, and qualifier nodes.

[0018] **FIG. 4** is a flowchart illustrating the multi-agent investigation process.

[0019] **FIG. 5** is a user interface mockup showing extracted claims with highlighted qualifiers and contradiction indicators.

[0020] **FIG. 6** is a diagram showing example claim normalization with qualifier preservation: multiple source claims merging into a super-claim while retaining individual qualifiers.

---

## DETAILED DESCRIPTION OF THE INVENTION

### System Architecture

[0021] Referring to FIG. 1, the research claim verification system 100 comprises several interconnected components operating on one or more computing devices. The system includes: a document ingestion module 110, a text extraction engine 120, a claim extraction module 130 with integrated qualifier detector 135, a semantic analysis engine 140, a knowledge graph database 150, a multi-agent investigation framework 160, and a user interface layer 170.

[0022] The **document ingestion module 110** accepts research documents in multiple formats including PDF, DOCX, HTML, and plain text. For PDF documents, the module employs column detection algorithms to correctly parse multi-column academic paper layouts. The module calculates a cryptographic hash (e.g., SHA-256) of document contents to prevent duplicate ingestion.

[0023] The **text extraction engine 120** processes documents to extract plain text while preserving document structure. For PDF files, the engine uses libraries such as PyPDF2 or pdfplumber. For scanned documents, optical character recognition (OCR) may be employed. The engine segments text into paragraphs, sections, and sentences for subsequent analysis.

[0024] The **claim extraction module 130** analyzes extracted text using large language models (LLMs) such as GPT-4, Claude, or similar transformer-based architectures. The module identifies sentences or passages containing research claims—statements that assert findings, hypotheses, methods, or conclusions.

### Qualifier Detection and Preservation

[0025] The integrated **qualifier detector 135** represents a novel aspect of the invention. During claim extraction, the detector simultaneously identifies three categories of qualifiers:

[0026] **Modal Qualifiers:** Words indicating possibility, capability, permission, or obligation including: can, could, may, might, must, shall, should, would, cannot, may not. For example, in the claim "Exercise may reduce anxiety symptoms," the modal qualifier "may" indicates possibility rather than certainty.

[0027] **Frequency Qualifiers:** Words indicating how often a phenomenon occurs including: always, usually, frequently, often, sometimes, occasionally, seldom, rarely, never. For example, "Patients often respond to treatment" indicates high frequency but not universality.

[0028] **Quantitative Qualifiers:** Words indicating scope or proportion including: all, most, many, several, some, few, none; percentage expressions (e.g., "80% of patients"); and numeric ranges. For example, "Some patients experience side effects" limits the claim to a subset rather than all patients.

[0029] The detector uses dependency parsing to identify the syntactic relationship between qualifiers and the claim's main assertion. This prevents false positives where qualifier words appear in unrelated clauses. For example, in "Although some researchers disagree, the treatment is effective," the quantifier "some" modifies "researchers" not "treatment effectiveness."

[0030] Each detected qualifier is stored as structured metadata associated with the claim, including:
```
qualifier_id: UUID
qualifier_text: string
qualifier_type: enum (modal, frequency, quantitative)
position: integer (word position in claim)
scope: string (phrase modified by qualifier)
confidence: float (0.0-1.0)
```

[0031] **Preservation through processing pipeline:** A critical technical challenge addressed by this invention is maintaining qualifier associations throughout subsequent processing steps. Traditional NLP pipelines often normalize or lemmatize text, converting "may help" to "help" or "can improve" to "improve." The present invention maintains a parallel qualifier metadata structure that persists through all transformations.

### Semantic Analysis and Claim Normalization

[0032] The **semantic analysis engine 140** addresses the problem of claim deduplication while preserving semantic differences introduced by qualifiers. The engine employs the following process:

[0033] **Step 1 - Embedding Generation:** Convert each claim to a vector embedding using models such as sentence-transformers, OpenAI embeddings, or similar. In one embodiment, 384-dimensional vectors are generated using the 'all-MiniLM-L6-v2' model.

[0034] **Step 2 - Similarity Calculation:** Compute cosine similarity between claim embeddings. Claims with similarity above a threshold (e.g., 0.80) are considered semantically similar.

[0035] **Step 3 - Qualifier-Aware Grouping:** Among similar claims, the system analyzes qualifier patterns. Claims with identical qualifiers may be merged. Claims with different qualifiers are grouped but retain separate nodes. For example:
- "Exercise reduces anxiety" (no qualifier)
- "Exercise may reduce anxiety" (modal: may)
- "Exercise often reduces anxiety" (frequency: often)

These three claims are semantically similar but convey different certainty levels. The system creates a super-claim node representing the common assertion ("exercise reduces anxiety") while maintaining child nodes for each qualifier variation.

[0036] **Step 4 - Hierarchical Graph Construction:** The system creates a knowledge graph using the following node types and relationships:

**Node Types:**
- Document nodes: Represent source papers with metadata (title, authors, publication date, venue)
- Claim nodes: Individual extracted claims with full text and qualifiers
- SuperClaim nodes: Normalized claims representing groups of similar claims
- Qualifier nodes: Specific qualifier instances
- Evidence nodes: Supporting or contradicting evidence from other papers

**Edge Types:**
- CONTAINS: Document → Claim (this paper contains this claim)
- EXTRACTED_FROM: Claim → Document (inverse relationship)
- SIMILAR_TO: Claim → Claim (semantic similarity with score)
- MERGED_INTO: Claim → SuperClaim (this claim is an instance of this super-claim)
- HAS_QUALIFIER: Claim → Qualifier (this claim has this qualifier)
- SUPPORTS: Evidence → Claim (this evidence supports this claim)
- CONTRADICTS: Evidence → Claim (this evidence contradicts this claim)
- CITES: Document → Document (citation relationship)

[0037] In one embodiment, the knowledge graph is implemented using Neo4j graph database. In another embodiment, NetworkX library provides an in-memory graph for smaller datasets. The graph structure enables complex queries such as "Find all claims about treatment X that have modal qualifiers and are contradicted by at least two other papers."

### Multi-Agent Investigation Framework

[0038] Referring to FIG. 4, the **multi-agent investigation framework 160** automatically gathers evidence for target claims using a coordinated system of specialized agents. This represents a significant advancement over prior art requiring manual evidence gathering.

[0039] **Coordinator Agent:** Receives a target claim and generates an investigation plan. The plan specifies search keywords, academic databases to query, number of papers to retrieve, and investigation depth (quick/standard/thorough). The coordinator assigns tasks to specialist agents and synthesizes their results.

[0040] **Support Agent:** Searches for papers that support the target claim. The agent:
- Generates search queries using claim keywords plus synonyms
- Queries multiple academic APIs (arXiv, OpenAlex, CORE, PubMed, etc.)
- Retrieves paper abstracts or full text
- Analyzes each paper to determine if it supports the claim
- Extracts relevant passages as evidence
- Scores support strength (weak/moderate/strong)

[0041] **Challenge Agent:** Functions as an adversarial researcher, actively seeking papers that contradict the target claim. The agent:
- Generates queries including negation terms
- Searches for null results, failed replications, or contradictory findings
- Identifies methodological critiques
- Extracts passages explaining discrepancies
- Scores contradiction strength

[0042] **Analysis Agent:** Synthesizes results from support and challenge agents to generate:
- Confidence score (0.0-1.0): Proportion of supporting vs. contradicting evidence weighted by study quality
- Research gap analysis: Identifies populations, methods, or timeframes not covered by existing literature
- Contradiction patterns: Clusters contradictory findings by methodology, population, or date
- Recommendations: Suggests specific follow-up investigations needed

[0043] In one embodiment, agents operate asynchronously using a task queue system (e.g., Celery with Redis). This allows multiple investigations to run in parallel without blocking user interface operations.

[0044] **Technical advantages of multi-agent architecture:**
- Parallel processing reduces investigation time from hours to minutes
- Adversarial design (support vs. challenge) reduces confirmation bias
- Modular architecture allows adding new agent types (e.g., methodology critic agent)
- Asynchronous operation provides responsive user experience

### Contradiction Detection System

[0045] The system includes automated contradiction detection operating continuously as new claims are added:

[0046] **Step 1 - Candidate Identification:** For each newly added claim, compute semantic similarity to all existing claims. Identify candidates with similarity > 0.75 (configurable threshold).

[0047] **Step 2 - Polarity Analysis:** Analyze each candidate pair using sentiment analysis and negation detection. Identify opposing polarities such as:
- "Treatment X is effective" vs. "Treatment X is not effective"
- "Risk increases" vs. "Risk decreases"
- "Correlation found" vs. "No correlation found"

[0048] **Step 3 - Qualifier Comparison:** Even with same polarity, different qualifiers may indicate contradiction:
- "All patients respond" vs. "Some patients respond" (quantifier conflict)
- "Always occurs" vs. "Sometimes occurs" (frequency conflict)
- "Can prevent" vs. "Cannot prevent" (modal conflict)

[0049] **Step 4 - Context Validation:** Use document metadata to filter false contradictions. Papers from different domains, populations, or time periods may make different claims without true contradiction. For example:
- "Treatment works in children" vs. "Treatment doesn't work in adults" → Different populations, not true contradiction
- Historical claim (1980) vs. modern claim (2020) → May reflect scientific progress

[0050] **Step 5 - User Notification:** When contradiction detected, system generates alert including:
- Both contradicting claims with source papers
- Qualifier differences highlighted
- Metadata comparison (dates, populations, methodologies)
- Suggested resolution actions

### User Interface and Interaction

[0051] The **user interface layer 170** provides multiple modalities for interacting with the system:

[0052] **Document Upload:** Drag-and-drop or file browser upload with progress indicators. Real-time processing status updates via WebSocket connections.

[0053] **Claim Browser:** Table or card view showing extracted claims with:
- Original text with qualifiers highlighted in color
- Source document link
- Confidence scores
- Tags and categories
- Related claims (similar/supporting/contradicting)

[0054] **Knowledge Graph Visualization:** Interactive graph rendering using libraries such as D3.js or Cytoscape.js. Users can:
- Zoom and pan to explore large graphs
- Filter by node type, date range, topic, or confidence level
- Click nodes to see details in side panel
- Color-code by support level (green=supported, red=contradicted, yellow=uncertain)

[0055] **Search Interface:** Semantic search accepts natural language queries like "What evidence exists that meditation reduces anxiety?" System:
- Converts query to embedding
- Finds nearest claims in vector space
- Ranks by relevance score
- Displays results with context snippets

[0056] **Investigation Dashboard:** When user initiates claim investigation, dashboard shows:
- Real-time agent progress ("Searching arXiv... Found 47 papers")
- Intermediate results as agents complete
- Final report with evidence summary, confidence score, and recommendations

### Implementation Details

[0057] **Hardware Requirements:** The system operates on standard computing hardware. Minimum configuration: 4-core CPU, 8GB RAM, 50GB storage. Recommended configuration for production: 16-core CPU, 64GB RAM, 500GB SSD, GPU for embedding generation (e.g., NVIDIA Tesla T4).

[0058] **Software Stack:** In one embodiment, the system comprises:
- Backend: Python 3.11+ with FastAPI web framework
- Database: PostgreSQL 15+ with pgvector extension for vector similarity
- Graph Database: Neo4j Community or Enterprise edition
- Task Queue: Celery with Redis broker
- Frontend: Next.js 14+ with React 18+
- AI Services: OpenAI API (GPT-4) or Anthropic API (Claude)

[0059] **Scalability Considerations:** The architecture supports horizontal scaling:
- Multiple FastAPI workers handle concurrent requests
- Celery workers can be added to process more documents in parallel
- PostgreSQL read replicas distribute query load
- Redis cluster for high-availability task queue
- CDN for static frontend assets

[0060] **Security Features:** The system implements:
- JWT-based authentication for API access
- Role-based access control (RBAC) for multi-user environments
- API rate limiting to prevent abuse
- Input sanitization to prevent injection attacks
- HTTPS encryption for all network communication
- Regular security audits of dependencies

---

## CLAIMS

### Independent Claims

**Claim 1. A computer-implemented method for extracting and preserving research claims from documents, comprising:**

(a) receiving a research document in electronic format at a computing device having a processor and memory;

(b) extracting text content from said document using at least one of optical character recognition or native text extraction;

(c) analyzing said extracted text using a natural language processing model to identify candidate claim sentences, wherein each candidate claim sentence asserts a research finding, hypothesis, method, or conclusion;

(d) for each identified candidate claim sentence, detecting semantic qualifiers using dependency parsing, wherein said semantic qualifiers include:
    - modal qualifiers selected from the group consisting of: can, could, may, might, must, shall, should, would, and negations thereof;
    - frequency qualifiers selected from the group consisting of: always, usually, often, sometimes, rarely, never; and
    - quantitative qualifiers selected from the group consisting of: all, most, many, some, few, none, and numeric expressions;

(e) storing each claim in a structured database with associated qualifier metadata, wherein said metadata includes qualifier type, text, position, and scope;

(f) generating a vector embedding for each claim using a transformer-based language model;

(g) computing semantic similarity between claim embeddings using cosine similarity;

(h) when similarity between two claims exceeds a predetermined threshold, creating a super-claim node representing common semantic content while maintaining separate child nodes preserving original qualifier variations; and

(i) constructing a knowledge graph comprising:
    - nodes representing documents, claims, super-claims, and qualifiers; and
    - directed edges representing relationships selected from: containment, similarity, merger, and qualification relationships.

---

**Claim 2. The method of claim 1, further comprising a multi-agent investigation process for automatically gathering evidence for a target claim, said process comprising:**

(a) receiving said target claim as input to a coordinator agent;

(b) said coordinator agent generating an investigation plan specifying search parameters and assigning tasks to specialist agents;

(c) a support agent executing searches of academic databases to identify papers supporting said target claim;

(d) a challenge agent executing searches of academic databases to identify papers contradicting said target claim;

(e) an analysis agent calculating a confidence score based on quantity and quality of supporting evidence versus contradicting evidence; and

(f) generating a report identifying research gaps, contradiction patterns, and recommended follow-up investigations.

---

**Claim 3. The method of claim 1, further comprising automated contradiction detection, comprising:**

(a) for each newly added claim, computing semantic similarity to all existing claims in said knowledge graph;

(b) identifying candidate claim pairs with similarity exceeding 0.75;

(c) analyzing polarity of each candidate pair using sentiment analysis and negation detection;

(d) identifying contradictions when claims have opposite polarity or conflicting qualifier types;

(e) validating contradictions by comparing document metadata to filter false contradictions arising from different populations, time periods, or domains; and

(f) generating user notifications for validated contradictions, said notifications including both claims, source documents, and highlighted qualifier differences.

---

### Dependent Claims

**Claim 4. The method of claim 1, wherein said dependency parsing comprises:**

(a) parsing each candidate claim sentence into a syntactic tree structure;

(b) identifying qualifier words using a predefined lexicon;

(c) traversing said syntactic tree to determine which phrase or clause each qualifier word modifies; and

(d) excluding qualifiers that do not modify the main assertion of said claim.

---

**Claim 5. The method of claim 1, wherein said vector embedding is generated using a sentence-transformer model trained on scientific literature, and wherein said embedding has dimensionality between 256 and 1024 dimensions.

---

**Claim 6. The method of claim 1, wherein said predetermined threshold for similarity is adaptively adjusted based on domain specificity, wherein highly technical domains use a threshold between 0.85 and 0.95, and general domains use a threshold between 0.70 and 0.85.

---

**Claim 7. The method of claim 2, wherein said support agent and challenge agent operate asynchronously in parallel using a distributed task queue system, thereby reducing investigation time compared to sequential processing.

---

**Claim 8. The method of claim 2, wherein said analysis agent calculates said confidence score using a weighted formula:**

**Confidence = (Ws × Ns + Wq × Qs) / (Ws × Ns + Wq × Qs + Wc × Nc + Wq × Qc)**

where:
- Ns = number of supporting papers
- Nc = number of contradicting papers
- Qs = average quality score of supporting papers
- Qc = average quality score of contradicting papers
- Ws, Wc, Wq = weighting coefficients

---

**Claim 9. The method of claim 3, wherein validating contradictions comprises comparing at least one metadata field selected from the group consisting of: publication date, study population demographics, geographic location, research methodology, and subject domain classification.

---

**Claim 10. The method of claim 1, further comprising a user interface displaying extracted claims with qualifiers visually distinguished by at least one of: color highlighting, font styling, or tooltip annotations.

---

### System Claims

**Claim 11. A research claim verification system comprising:**

(a) one or more processors;

(b) memory storing instructions that, when executed by said processors, cause the system to:
    - receive research documents in electronic format;
    - extract text from said documents;
    - identify research claims using natural language processing;
    - detect and preserve semantic qualifiers for each claim;
    - generate vector embeddings for semantic similarity analysis;
    - construct a knowledge graph with nodes representing documents, claims, and qualifiers;
    - detect contradictions between claims based on semantic similarity and qualifier analysis; and
    - provide a user interface for querying and visualizing said knowledge graph.

---

**Claim 12. The system of claim 11, further comprising a multi-agent investigation module comprising:**

(a) a coordinator agent module;

(b) a support agent module configured to search academic databases for supporting evidence;

(c) a challenge agent module configured to search academic databases for contradicting evidence; and

(d) an analysis agent module configured to calculate confidence scores and generate research gap reports.

---

**Claim 13. The system of claim 11, wherein said knowledge graph is implemented using a graph database selected from the group consisting of: Neo4j, NetworkX, Apache TinkerPop, Amazon Neptune, and ArangoDB.

---

**Claim 14. The system of claim 11, further comprising a vector database for storing and querying claim embeddings, wherein said vector database supports cosine similarity search, and wherein said vector database is selected from the group consisting of: PostgreSQL with pgvector extension, Pinecone, Weaviate, Milvus, and Chroma.

---

**Claim 15. A non-transitory computer-readable storage medium storing instructions that, when executed by one or more processors, cause said processors to perform the method of any of claims 1-10.

---

## CONCLUSION

[0061] The foregoing description illustrates and describes various embodiments of the present invention. Additionally, the disclosure shows and describes preferred embodiments, but it should be understood that various alternatives, modifications, and equivalents may be used. Therefore, the foregoing description should not be construed as limiting the invention, which is defined by the appended claims.

[0062] One skilled in the art will recognize that alternative implementations may substitute different natural language models, graph databases, or embedding algorithms while retaining the core inventive concepts of qualifier preservation and multi-agent investigation.

[0063] The claims define the legal scope of patent protection. The specification provides enabling disclosure sufficient for one skilled in the art to practice the invention without undue experimentation.

---

## INVENTOR NOTES

**This sample patent application demonstrates:**

1. **Proper Structure:** Abstract, Background, Summary, Detailed Description, Claims - the standard utility patent format

2. **Technical Language:** Uses precise terminology expected in computer science patents (e.g., "transformer-based architecture," "vector embeddings," "cosine similarity")

3. **Claim Hierarchy:** Independent claims (1, 2, 3, 11) define broad inventions; dependent claims (4-10, 12-14) add specific limitations

4. **Multiple Claim Types:** Method claims (doing steps), system claims (apparatus), and storage medium claims (software)

5. **Patentable Subject Matter:** Focuses on novel technical processes (qualifier preservation, multi-agent coordination) rather than abstract ideas

**Key Patentable Aspects:**

- **Qualifier Detection & Preservation:** Novel approach to maintaining semantic qualifiers through NLP pipeline (Claims 1, 4)
- **Qualifier-Aware Deduplication:** Creating super-claims while preserving qualifier variations (Claim 1)
- **Multi-Agent Investigation:** Coordinated system with adversarial agents (Claims 2, 12)
- **Automated Contradiction Detection:** Using semantic similarity + qualifier comparison (Claims 3, 9)
- **Knowledge Graph Structure:** Specific node/edge types for research claims (Claims 1, 11, 13)

**Prosecution Strategy:**

- Independent Claim 1 is broad (may face obviousness rejections)
- Dependent Claims 4-10 provide fallback positions with more specific limitations
- System claims (11-14) cover apparatus, important for infringement suits
- Storage medium claim (15) covers software distribution

**Prior Art Considerations:**

- Existing citation managers (Zotero, Mendeley) don't extract individual claims
- LLM-based extraction tools exist but don't preserve qualifiers
- Multi-agent systems exist but not specifically for research verification
- Novelty lies in *combination* of techniques and specific application to qualifier preservation

**Estimated Patent Value:**

- Strong commercial potential: academic institutions, pharmaceutical research, legal tech
- Defensive patent: protects against competitors copying the system
- Licensing potential: could license to existing research software companies

---

**END OF SAMPLE PATENT APPLICATION**
