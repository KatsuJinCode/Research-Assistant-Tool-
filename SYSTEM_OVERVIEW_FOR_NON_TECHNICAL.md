# Research Assistant Tool - Complete System Guide
**A comprehensive overview for technical users new to modern data engineering**

---

## What This System Does (The Big Picture)

Think of this tool as a **smart research librarian** that helps scholars organize and verify claims from academic papers. Instead of manually reading hundreds of papers and tracking which studies support or contradict each other, this system automates that process.

**The Core Problem It Solves:**
- Researchers claim "Treatment X helps 80% of patients"
- But did they say "helps" or "may help"? That one word matters.
- What other papers support or contradict this claim?
- How do you track hundreds of such claims across dozens of papers?

**This system extracts claims, preserves critical qualifiers (can/may/might/some), and builds a network showing how claims relate to each other.**

---

## System Architecture: Two Versions

### Version 1: Command-Line (CLI) - Currently Working
*Think: 1980s-style terminal commands, like MS-DOS or Unix shells*

### Version 2: Web Application - Planned for Future
*Think: Modern websites like Gmail or Google Docs*

We'll explain both, so you understand where we're headed.

---

## Part 1: What Users Can Do (Features & Interactions)

### A. Adding Content to the System

#### **1. Adding Documents (Research Papers)**

**CLI Version (Current):**
```bash
# User types this command in terminal:
./research.sh add-document 123 "paper.pdf"

# System responds:
✓ Extracted 2,847 words from 12 pages
✓ Found 34 research claims
✓ Saved as document #456
```

**Web Version (Planned):**
- User drags PDF file into browser window
- System shows progress bar: "Extracting text... Analyzing claims..."
- User sees document appear in their project library
- Can click to view extracted claims immediately

**What happens behind the scenes:**
1. System reads the PDF file (like opening a Word document)
2. Extracts all text, handling two-column layouts, footnotes, tables
3. Calculates a "fingerprint" (SHA256 hash) to prevent duplicates
4. Stores full text in database (SQLite now, PostgreSQL later)

---

#### **2. Adding Claims Manually**

Sometimes users want to add their own observations:

**CLI Version:**
```bash
./research.sh add-claim --text "Patients may respond to therapy" \
                        --type "empirical" \
                        --source "Clinical observation"
```

**Web Version (Planned):**
- Click "New Claim" button
- Type claim in text box
- System automatically detects qualifiers: highlights "may"
- Choose category: Empirical / Theoretical / Methodological
- Add tags: depression, therapy, clinical
- Save → claim appears in knowledge graph

**Important Feature - Qualifier Preservation:**
The system treats these VERY differently:
- "Therapy **works** for patients" (definitive)
- "Therapy **may work** for **some** patients" (qualified)

It highlights and tracks words like: can, may, might, could, some, many, all, most, few

---

#### **3. Telling Agents to Do Research**

This is where it gets interesting. The system has AI "agents" (think: automated research assistants) that can investigate claims.

**CLI Version:**
```bash
# Tell agent to investigate claim #789
./research.sh investigate 789 --depth thorough

# System spawns multiple agents:
[Investigation Agent] Searching arXiv for related papers...
[Support Agent]       Found 12 supporting studies
[Challenge Agent]     Found 3 contradicting studies
[Analysis Agent]      Calculating confidence score...

# Result:
✓ Investigation complete
  - 12 supporting papers
  - 3 challenging papers
  - Confidence: 68% (moderate support)
  - Report saved to: investigation_789.md
```

**Web Version (Planned):**
- Right-click any claim → "Investigate this claim"
- See live updates as agents work:
  - 🔍 Searching academic databases...
  - 📚 Found 47 candidate papers
  - 📥 Downloading 12 most relevant...
  - 🧠 Analyzing evidence...
- Results appear in sidebar with color-coded support levels
- Click any cited paper to view full text

**The Agent System (Simplified Explanation):**

Think of it like a team of specialized assistants:

1. **Investigation Agent** - The coordinator who assigns work
2. **Support Agent** - Looks for papers that agree with the claim
3. **Challenge Agent** - Looks for papers that disagree (devil's advocate)
4. **Analysis Agent** - Weighs all evidence and calculates confidence

They work in parallel (simultaneously), like having 4 people at 4 different library terminals instead of 1 person doing everything sequentially.

---

### B. Searching & Exploring

#### **Search Capabilities**

**Current (CLI - Basic text matching):**
```bash
./research.sh search "cognitive therapy depression"

Results:
1. [Doc #123] ...found that cognitive therapy reduces depression...
2. [Doc #456] ...cognitive therapy may help some patients with depression...
3. [Doc #789] ...no significant effect of cognitive therapy on depression...
```

**Planned (Web - Semantic search):**

Instead of just matching words, it understands meaning:
- Search: "talk therapy for sadness"
- Finds: "cognitive behavioral therapy for depression"
- Why? System knows: talk therapy ≈ CBT, sadness ≈ depression

**Technical detail (simplified):**
- System converts text to numbers (vectors) representing meaning
- 200 dimensions capture concepts like: therapy-type, condition, effectiveness
- Finds "nearby" claims in this mathematical space
- Like: "latitude/longitude" but with 200 coordinates instead of 2

---

### C. Viewing the Knowledge Graph

**What's a Knowledge Graph?**
Think of it like a mind map or org chart, but for research claims.

```
┌─────────────────┐
│  Document #123  │
│  "Smith 2020"   │
└────────┬────────┘
         │ CONTAINS
         ▼
┌─────────────────────────────┐
│  Claim #456                 │
│  "Therapy may help patients"│
└──────┬──────────────┬───────┘
       │              │
       │ SIMILAR_TO   │ HAS_QUALIFIER
       ▼              ▼
┌──────────┐    ┌──────────┐
│ Claim    │    │ "may"    │
│ #789     │    │ (modal)  │
└──────────┘    └──────────┘
```

**CLI Version:**
```bash
./research.sh show-graph --doc 123
# Opens visualization in browser (HTML file)
```

**Web Version (Planned):**
- Interactive graph view (zoom, drag, click)
- Filter by: document, date, topic, confidence level
- Color-coding: green=supported, red=contradicted, yellow=uncertain
- Click any node → see full details in side panel

---

## Part 2: How the Backend Works

### The Technology Stack (Explained Simply)

#### **Current CLI Stack:**

1. **Python** - Programming language (like BASIC or FORTRAN, but modern)
2. **SQLite** - Database (like a single-file Microsoft Access database)
3. **NetworkX** - Graph library (draws the knowledge network)
4. **OpenAI/Anthropic APIs** - AI services (sends text, gets analysis back)

**Analogy:** Like using command-line tools to process text files and store results in a database file, but with AI doing the reading comprehension.

---

#### **Planned Web Stack:**

**Frontend (What user sees in browser):**
- **Next.js** - Modern web framework (like building a website, but interactive like an app)
- **TypeScript** - JavaScript with type checking (prevents bugs)
- **Tailwind CSS** - Styling system (makes it look professional)

**Backend (Server processing):**
- **FastAPI** - Web server (receives requests from browser, sends responses)
- **PostgreSQL** - Industrial-strength database (like Oracle, but free)
- **Redis** - Ultra-fast cache (keeps frequent data in memory for speed)
- **Celery** - Task queue (handles long-running jobs without making user wait)

**Analogy:**
- Frontend = Bank teller window (what customer sees)
- Backend = Bank vault and processing systems (where real work happens)
- Database = Filing cabinets with all records
- Redis = Teller's cash drawer (quick access to common requests)
- Celery = Back office workers processing loans overnight

---

### How Data Flows Through the System

#### **Example: User Uploads a PDF**

**Step 1: Upload & Initial Processing**
```
User's computer → Upload PDF (5 MB) → Server
                                        ↓
                                  FastAPI receives file
                                        ↓
                                  Saves to disk/cloud storage
                                        ↓
                                  Creates database entry:
                                  - ID: doc_12345
                                  - Title: "Smith_2020.pdf"
                                  - Status: "processing"
                                        ↓
                                  Returns to user: "Upload successful!"
```

**Step 2: Background Processing (User can keep working)**
```
Celery Task Queue picks up job:
  ↓
[Task 1] Extract text from PDF
  - Uses PyPDF2 library
  - Detects columns, tables, headers
  - Output: 12,847 words of plain text
  ↓
[Task 2] Send to AI for claim extraction
  - Breaks text into chunks (AI has token limits)
  - Sends to OpenAI/Anthropic API
  - Receives structured JSON with claims
  - Output: 67 claims
  ↓
[Task 3] Analyze each claim
  - Extract qualifiers (may, might, can)
  - Categorize type (empirical/theoretical)
  - Calculate readability score
  ↓
[Task 4] Build graph relationships
  - Compare to existing claims (similarity)
  - Create nodes and edges
  - Store in NetworkX/Neo4j
  ↓
[Task 5] Generate embeddings for search
  - Convert claims to 384-dimensional vectors
  - Store in pgvector (PostgreSQL extension)
  ↓
Update database: Status = "complete"
Send notification to user (WebSocket)
```

**Step 3: User Sees Results**
```
Browser receives WebSocket message
  ↓
"Document processed! 67 claims extracted"
  ↓
Graph view automatically updates with new nodes
```

---

### Database Schema (How Data is Organized)

Think of this like a filing system with related folders:

**Projects Table** (Top-level organization)
```
projects
├─ id: 1
├─ name: "Depression Research Review"
├─ created: 2024-01-15
└─ user_id: 42
```

**Documents Table** (Papers in each project)
```
documents
├─ id: 456
├─ project_id: 1  ← Links to project above
├─ title: "Smith et al 2020"
├─ file_path: "/storage/pdfs/smith2020.pdf"
├─ full_text: "In this study we found..."
├─ content_hash: "a3f2b8c1..." ← Prevents duplicates
└─ metadata: {"pages": 12, "authors": ["Smith", "Jones"]}
```

**Claims Table** (Extracted statements)
```
claims
├─ id: 789
├─ document_id: 456  ← Links to document above
├─ original_text: "Therapy may reduce symptoms"
├─ normalized_text: "therapy reduces symptoms"
├─ claim_type: "empirical"
├─ confidence: 0.72
└─ qualifiers: ["may"]  ← JSON array
```

**Relationships Table** (How claims connect)
```
claim_relationships
├─ id: 999
├─ claim1_id: 789
├─ claim2_id: 812
├─ relationship_type: "SIMILAR_TO"
├─ similarity_score: 0.85
└─ evidence: "Both discuss CBT for depression"
```

**Accounting Analogy:**
- Projects = Client accounts
- Documents = Individual invoices/receipts
- Claims = Line items on invoices
- Relationships = Cross-references between entries

---

### How the System Guides Follow-Up Research

**1. Automatic Suggestions**

When user views a claim, system suggests:
- "3 related claims found in other documents"
- "2 papers cited this study - investigate?"
- "Confidence low (45%) - needs more evidence"

**2. Gap Detection**

System identifies knowledge gaps:
```
Claim: "Exercise reduces anxiety"
Status: Uncertain (52% confidence)

Gaps identified:
- No studies on long-term effects (>1 year)
- All studies used college students (bias)
- No replication studies found

Suggested actions:
→ Search for: "exercise anxiety longitudinal"
→ Filter for: diverse demographics
→ Check: replication studies
```

**3. Citation Network Analysis**

Builds a network of who cites whom:
```
Smith 2020 ───cites───→ Jones 2018 ───cites───→ Lee 2015
     │                       ↑
     └────────cites──────────┘

Insight: "Circular citation pattern detected -
          may indicate bias or limited evidence base"
```

**4. Contradiction Detection**

Flags conflicting claims:
```
⚠ Contradiction Detected:

Claim A (Smith 2020): "Treatment X is effective"
Claim B (Jones 2021): "Treatment X shows no benefit"

User actions:
→ Investigate both studies
→ Check methodology differences
→ Look for reconciling meta-analysis
```

---

## Part 3: Key Technical Concepts (Simplified)

### Asynchronous Processing

**Old way (synchronous):**
```
User clicks "Process PDF"
  → Wait 2 minutes while processing...
  → Can't do anything else...
  → Finally, results appear
```

**New way (asynchronous):**
```
User clicks "Process PDF"
  → "Processing started!" (instant response)
  → User keeps working on other tasks
  → Notification pops up when done: "PDF ready!"
```

**How it works:**
- Main program (FastAPI) receives request
- Adds job to queue (Celery)
- Returns immediately to user
- Worker process handles job in background
- Sends notification via WebSocket when complete

**Accounting analogy:** Like dropping tax documents in accountant's inbox vs. waiting at their desk while they process everything.

---

### Vector Embeddings (Semantic Search)

**Problem:** Computer doesn't understand that "car" and "automobile" mean the same thing.

**Solution:** Convert words to numbers that capture meaning.

**Example:**
```
"car"        → [0.2, 0.8, 0.1, 0.9, ...]  (384 numbers)
"automobile" → [0.3, 0.8, 0.1, 0.9, ...]  (very similar numbers!)
"banana"     → [0.9, 0.1, 0.8, 0.2, ...]  (very different numbers)
```

**Finding similar claims:**
```
Query: "depression treatment"
Vector: [0.4, 0.7, 0.2, ...]

Compare to all stored claim vectors:
Claim 1: [0.5, 0.7, 0.3, ...] → Distance: 0.12 (very close!)
Claim 2: [0.1, 0.9, 0.8, ...] → Distance: 0.89 (far away)

Return closest matches first.
```

**Accounting analogy:** Like organizing receipts by category codes instead of exact vendor names - you can find all "office supplies" even if they're from different stores.

---

### API Integration (How AI Services Work)

**The system doesn't run AI locally - it calls external services:**

```
Your Server                OpenAI's Server
    ↓                           ↑
    Sends text ─────────────────┘
    + API key
    + Model name ("gpt-4")

    ↓
    Waits for response...

    ↓                           ↑
    Receives JSON ──────────────┘
    with extracted claims
```

**Cost model:**
- Charged per 1,000 tokens (≈750 words)
- GPT-4: ~$0.03 per 1,000 tokens
- Typical paper (5,000 words) ≈ $0.20 to process

**Rate limiting:**
- OpenAI limits: 10,000 requests/minute
- System queues requests to stay under limit
- Caches results to avoid re-processing

---

### Graph Database Concepts

**Relational Database (traditional):**
```
Table: Claims
ID | Text           | Doc_ID
1  | "Therapy works"| 123
2  | "CBT effective"| 124

To find relationships: JOIN queries (slow for complex connections)
```

**Graph Database (modern):**
```
(Claim1:Text) ─[SIMILAR_TO:0.9]─→ (Claim2:Text)
      │                                  │
      └─[FROM]─→ (Doc:Paper) ←─[FROM]───┘
```

**Advantages:**
- Find "all claims similar to Claim1" → instant traversal
- Find "papers citing papers that cite Smith" → 2 hops
- Traditional SQL: requires complex recursive queries

**Accounting analogy:**
- Relational DB = Spreadsheet with lookup formulas
- Graph DB = Mind map with direct connections drawn

---

## Part 4: User Workflows (Putting It All Together)

### Workflow 1: Literature Review

**Goal:** Survey all research on "exercise and mental health"

**Steps:**
1. Create project: "Exercise Mental Health Review"
2. Upload 20 PDFs from PubMed download
3. System processes overnight (async)
4. Morning: Review extracted claims (487 total)
5. Click "Normalize claims" → system groups into 93 unique claims
6. View graph: see clusters (anxiety, depression, ADHD subtopics)
7. Export to Markdown report for manuscript

---

### Workflow 2: Claim Verification

**Goal:** Verify claim from news article

**Steps:**
1. Add claim manually: "Meditation cures anxiety"
2. Click "Investigate"
3. Agents search academic databases
4. Results:
   - 34 studies found
   - 18 show "reduces" (not "cures")
   - Qualifier issue: claim overstates evidence
5. System suggests revision: "Meditation may reduce anxiety"
6. Generate report with citations for fact-check article

---

### Workflow 3: Ongoing Research Monitoring

**Goal:** Track new papers in your field

**Steps:**
1. Set up saved search: "cognitive behavioral therapy 2024"
2. System runs arXiv query weekly (cron job)
3. New papers auto-processed
4. Email digest: "5 new claims added this week"
5. Review in web interface, add to relevant projects
6. System flags: "New claim contradicts Claim #456 from 2020"
7. Investigate discrepancy

---

## Summary: Why This Architecture?

**Modularity:**
- Each component does one job well
- Can swap PostgreSQL for MySQL if needed
- Can switch from OpenAI to Anthropic Claude
- Frontend and backend completely separate

**Scalability:**
- Current: 1 user, 100 papers (CLI)
- Future: 1,000 users, 100,000 papers (web)
- Add more workers to queue (horizontal scaling)
- Add database replicas for reads

**Maintainability:**
- Type hints catch bugs before runtime
- Automated tests verify each component
- Clear separation of concerns
- Documented APIs for future developers

**Cost-Effectiveness:**
- SQLite free (current)
- PostgreSQL free (future)
- Only cost: AI API calls (pay per use)
- Can self-host everything (no vendor lock-in)

---

## Next Steps for Your Father to Review

**Questions to consider:**
1. Is the manual claim entry workflow intuitive?
2. Should the system auto-suggest tags, or require manual tagging?
3. How much detail in reports - summary or full citations?
4. Export formats needed: PDF, Word, LaTeX, BibTeX?
5. Multi-user: sharing projects, or single-user focused?

**Technical decisions:**
1. Self-hosted (runs on your server) vs cloud (runs on AWS)?
2. Which AI provider: OpenAI (faster) or Anthropic (better reasoning)?
3. Graph visualization: simple diagrams or interactive 3D?
4. Mobile app eventually, or web-only?

---

**End of document** - 5 pages covering features, backend processing, data flow, and key concepts accessible to users with command-line experience but limited modern web development background.
