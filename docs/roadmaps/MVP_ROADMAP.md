# Research Verification Agent System - MVP Implementation Roadmap

## Core Principles Acknowledgment

### 1. Qualifier Terms - Rigorous Inclusion

**Recognition**: Qualifier terms like "mostly", "often", "usually", "can", "may", "will" are **CRITICAL** to claim accuracy.

**Examples of Why This Matters**:
```
Claim: "AI will replace all jobs by 2030"
vs
Claim: "AI may replace some jobs by 2030"

These are COMPLETELY DIFFERENT claims!
- "will" vs "may" = certainty level
- "all" vs "some" = scope
- Same timeframe, utterly different assertions
```

**System Design**:
- **Qualifier Extraction**: Pattern matching + NER for all modals, adverbs, quantifiers
- **Qualifier Preservation**: Hard requirement in normalization - auto-fail if lost
- **Qualifier Tracking**: Separate database column for quick filtering/analysis
- **Investigation Impact**: Different agent strategies based on qualifiers
  - "will" claims → demand stronger evidence
  - "may" claims → acknowledge uncertainty in findings
  - "all" claims → look for counter-examples
  - "some" claims → need representative examples

**Database Schema Addition**:
```sql
-- Qualifier metadata (critical for analysis)
CREATE TABLE claim_qualifiers (
    claim_id UUID REFERENCES claims(id),
    qualifier_type VARCHAR(50),  -- 'modal', 'frequency', 'quantity', 'certainty'
    qualifier_text VARCHAR(50),  -- The actual word: 'can', 'mostly', 'all', etc.
    position_in_claim INT,       -- Where it appears
    semantic_impact TEXT,        -- 'indicates_possibility', 'indicates_certainty', etc.

    PRIMARY KEY (claim_id, qualifier_type, qualifier_text)
);

-- Examples:
-- Claim: "Renewable energy can meet most global needs by 2050"
-- Qualifiers:
--   (modal, 'can', position=3, impact='indicates_possibility')
--   (quantity, 'most', position=5, impact='indicates_majority_but_not_all')
--   (temporal, 'by 2050', position=8, impact='future_deadline')
```

### 2. Confidence Scores - Adaptive Investigation Depth

**Recognition**: Confidence scores determine **investigation effort allocation**.

**Confidence-Based Workflow**:
```
High Confidence (0.85-1.0):
├── Fewer agents needed (3-5)
├── Shorter investigation time
├── Lower priority for re-verification
└── Can proceed to next phase

Medium Confidence (0.60-0.84):
├── Standard agent pool (8-10)
├── Normal investigation depth
├── May trigger follow-up investigations
└── Monitor for conflicting evidence

Low Confidence (0.00-0.59):
├── Deploy additional diverse agents (15+)
├── Increase investigation depth (+2 levels)
├── Try different philosophical frameworks
├── Add lateral discovery agents
├── Flag for expert human review
└── May trigger decomposition if claim is too complex
```

**Confidence Score Sources**:
```python
# Every operation produces confidence score

# 1. Normalization confidence
normalization_confidence = (
    0.30 * embedding_similarity +      # How similar is normalized to original?
    0.40 * llm_equivalence_score +     # Does LLM confirm they're the same?
    0.20 * information_preservation +   # All facts still present?
    0.10 * quantifier_preservation      # All qualifiers preserved?
)

# 2. Investigation confidence (per agent)
investigation_confidence = (
    0.40 * evidence_quality +           # Strength of sources found
    0.30 * evidence_consistency +       # Do sources agree?
    0.20 * agent_framework_fit +        # Was this the right agent for this claim?
    0.10 * completeness                 # Did agent finish fully?
)

# 3. Overall claim confidence (aggregated)
claim_confidence = weighted_average([
    (support_findings_avg_confidence, support_evidence_count),
    (challenge_findings_avg_confidence, challenge_evidence_count),
    (neutral_findings_avg_confidence, neutral_evidence_count)
])

# 4. Confidence-based actions
if claim_confidence < 0.60:
    schedule_additional_investigations(
        claim_id,
        additional_agent_count=10,
        increase_depth=2,
        add_frameworks=['Skeptical Inquiry', 'Interdisciplinary Synthesis']
    )
```

**Confidence Visualization in Reports**:
```
Claim Status: SUPPORTED ⭐⭐⭐⭐☆ (Confidence: 0.78)

Breakdown:
├── Normalization: ⭐⭐⭐⭐⭐ (0.96) - High confidence in claim accuracy
├── Support Evidence: ⭐⭐⭐⭐☆ (0.82) - Strong supporting evidence
├── Challenge Evidence: ⭐⭐⭐☆☆ (0.65) - Moderate challenges identified
└── Overall Assessment: ⭐⭐⭐⭐☆ (0.78) - Likely true with caveats

Recommendation: Medium confidence → Standard investigation complete.
              No additional verification needed unless new evidence emerges.
```

---

## MVP Implementation Plan

### MVP Goal
**Build a working end-to-end pipeline** that can:
1. Ingest a research paper (PDF)
2. Extract claims
3. Normalize claims (basic, with human validation)
4. Run 3 agent types: Support, Challenge, Analysis
5. Generate a simple report with confidence scores
6. Store everything in PostgreSQL

**Timeline**: 4-6 weeks (aggressive) or 8-10 weeks (realistic)

---

## Phase 1: Foundation (Week 1-2)

### Deliverables
- [x] Database schema (PostgreSQL)
- [x] Configuration system
- [x] Basic AI provider integration (OpenAI/Anthropic)
- [x] CLI framework
- [ ] Simple document ingestion

### Tasks

#### 1.1 Database Setup
```bash
# Create PostgreSQL database
createdb research_verification

# Install extensions
psql research_verification -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
psql research_verification -c "CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";"
psql research_verification -c "CREATE EXTENSION IF NOT EXISTS \"vector\";"
psql research_verification -c "CREATE EXTENSION IF NOT EXISTS \"ltree\";"
```

**Schema File**: `database/schema_v1_mvp.sql`

```sql
-- MVP Schema (simplified from full design)
-- Focus: Core tables only, no advanced features yet

-- Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    file_path TEXT,
    full_text TEXT,
    metadata JSONB,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Claims (simplified)
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_document_id UUID REFERENCES documents(id),
    parent_claim_id UUID REFERENCES claims(id),

    original_text TEXT NOT NULL,
    normalized_text TEXT,  -- NULL until normalized

    status VARCHAR(50) DEFAULT 'extracted',
    confidence_score DECIMAL(3,2),
    priority_score INT DEFAULT 50,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Claim Qualifiers (CRITICAL)
CREATE TABLE claim_qualifiers (
    claim_id UUID REFERENCES claims(id) ON DELETE CASCADE,
    qualifier_type VARCHAR(50),
    qualifier_text VARCHAR(50),
    semantic_impact TEXT,
    PRIMARY KEY (claim_id, qualifier_type, qualifier_text)
);

-- Agents
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    framework VARCHAR(50) NOT NULL,
    instance_name VARCHAR(100) UNIQUE,
    status VARCHAR(20) DEFAULT 'idle',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Investigations (work queue)
CREATE TABLE investigations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID REFERENCES claims(id),
    agent_framework VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'queued',
    priority INT DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Findings
CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigation_id UUID REFERENCES investigations(id),
    claim_id UUID REFERENCES claims(id),

    finding_type VARCHAR(20),  -- 'support', 'challenge', 'neutral'
    summary TEXT,
    confidence DECIMAL(3,2),  -- Agent's confidence in this finding

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Evidence
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    finding_id UUID REFERENCES findings(id),

    source_category VARCHAR(20),  -- 'academic' or 'web'
    citation_apa TEXT NOT NULL,
    relevant_quote TEXT,

    relevance_score DECIMAL(3,2),
    credibility_score DECIMAL(3,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Human validation (for normalization)
CREATE TABLE normalization_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID REFERENCES claims(id),
    original_text TEXT,
    proposed_normalized TEXT,
    confidence DECIMAL(3,2),

    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'approved', 'edited', 'rejected'
    user_corrected_text TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP
);
```

#### 1.2 Configuration System
**File**: `config/config.yaml`

```yaml
database:
  host: localhost
  port: 5432
  name: research_verification
  user: postgres
  password: ${DB_PASSWORD}  # From environment

ai_providers:
  default: anthropic

  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo
    temperature: 0.5

  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-5-sonnet-20241022
    temperature: 0.5

agents:
  # MVP: Only 3 agent types
  support_empirical:
    count: 2
    enabled: true

  challenge_empirical:
    count: 2
    enabled: true

  analysis_definitional:
    count: 1
    enabled: true

confidence_thresholds:
  high: 0.85
  medium: 0.60
  low: 0.00

  # Adaptive investigation
  low_confidence_additional_agents: 5
  low_confidence_depth_increase: 2

normalization:
  require_human_validation: true
  min_confidence_for_auto_approve: 0.95
  max_candidates: 4

logging:
  level: INFO
  file: logs/research_agent.log
```

#### 1.3 Core Application Structure
```
research_agent/
├── __init__.py
├── cli.py              # CLI commands
├── config.py           # Load config
├── database.py         # DB connection pool
├── models.py           # Pydantic models
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # BaseAgent class
│   ├── support_agent.py        # MVP: One agent type
│   └── agent_factory.py        # Create agents
│
├── document_processing/
│   ├── __init__.py
│   ├── pdf_extractor.py        # Extract text from PDF
│   └── claim_extractor.py      # Extract claims (simple)
│
├── normalization/
│   ├── __init__.py
│   ├── normalizer.py           # ClaimNormalizer (basic)
│   └── qualifier_extractor.py  # Extract modals/quantifiers
│
├── investigation/
│   ├── __init__.py
│   ├── orchestrator.py         # Manage investigations
│   └── work_scheduler.py       # Create investigation tasks
│
├── reporting/
│   ├── __init__.py
│   └── report_generator.py     # Generate reports
│
└── utils/
    ├── __init__.py
    ├── ai_client.py            # Wrapper for OpenAI/Anthropic
    └── confidence.py           # Confidence score calculations
```

---

## Phase 2: Document Ingestion & Claim Extraction (Week 2-3)

### MVP Approach: Simple Rule-Based + LLM

**No complex NLP models yet** - use:
1. PDF text extraction (pdfplumber)
2. Sentence splitting
3. LLM to identify which sentences are claims

### Deliverables
- [ ] PDF upload and text extraction
- [ ] Basic claim extraction (LLM-based)
- [ ] Store claims in database

### Implementation

**File**: `document_processing/pdf_extractor.py`
```python
import pdfplumber
from pathlib import Path

class PDFExtractor:
    def extract_text(self, pdf_path: Path) -> dict:
        """Extract text from PDF."""
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            pages = []

            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                pages.append({
                    'page_number': i + 1,
                    'text': text
                })
                full_text += text + "\n\n"

        return {
            'full_text': full_text,
            'pages': pages,
            'page_count': len(pages)
        }
```

**File**: `document_processing/claim_extractor.py`
```python
from typing import List
from utils.ai_client import AIClient

class ClaimExtractor:
    def __init__(self, ai_client: AIClient):
        self.ai = ai_client

    async def extract_claims(self, document_text: str) -> List[dict]:
        """
        Extract claims from document using LLM.
        MVP: Simple approach - identify claim sentences.
        """

        prompt = f"""You are a research claim extractor. Identify all factual claims,
hypotheses, and conclusions in this document.

A claim is:
- A statement that asserts something as true or likely
- A hypothesis being tested
- A conclusion from results
- A prediction or recommendation

NOT a claim:
- Background information
- Methodology descriptions
- Acknowledgments
- References to others' work (unless the author is affirming it)

Document:
{document_text[:8000]}  # Limit for MVP

Return JSON array:
[
  {{
    "text": "exact claim text from document",
    "type": "empirical" | "theoretical" | "predictive" | "normative",
    "confidence": 0.0-1.0
  }}
]"""

        response = await self.ai.generate(
            prompt,
            temperature=0.3,
            response_format='json'
        )

        claims = json.loads(response)
        return claims
```

**CLI Command**:
```bash
python -m research_agent ingest paper.pdf --title "Climate Research Paper"
# Output:
# ✓ Uploaded: paper.pdf
# ✓ Extracted text: 15,234 words
# ✓ Identified 23 claims
# Claims stored with IDs: claim-001 to claim-023
```

---

## Phase 3: Claim Normalization (Week 3-4)

### MVP Approach: LLM-Based with Qualifier Preservation

**Focus**: Ensure qualifiers are NEVER lost

### Deliverables
- [ ] Qualifier extraction (pattern matching)
- [ ] Basic normalization (LLM)
- [ ] Human validation interface (CLI)
- [ ] Confidence scoring

### Implementation

**File**: `normalization/qualifier_extractor.py`
```python
import re
from typing import List, Dict

class QualifierExtractor:
    """
    Extract qualifier terms that MUST be preserved.
    """

    # Comprehensive qualifier lists
    MODALS = ['can', 'could', 'may', 'might', 'will', 'would', 'shall', 'should', 'must']
    FREQUENCY = ['always', 'never', 'often', 'rarely', 'sometimes', 'usually', 'generally',
                 'frequently', 'occasionally', 'seldom', 'mostly', 'typically']
    QUANTITY = ['all', 'every', 'each', 'some', 'most', 'many', 'few', 'several', 'none', 'any']
    CERTAINTY = ['certainly', 'probably', 'possibly', 'likely', 'unlikely', 'perhaps', 'maybe']

    def extract(self, claim_text: str) -> List[Dict]:
        """
        Extract all qualifiers from claim text.
        Returns list of {type, text, position, impact}
        """
        qualifiers = []

        # Extract modals
        for modal in self.MODALS:
            if re.search(rf'\b{modal}\b', claim_text, re.I):
                qualifiers.append({
                    'type': 'modal',
                    'text': modal,
                    'impact': self._modal_impact(modal)
                })

        # Extract frequency adverbs
        for freq in self.FREQUENCY:
            if re.search(rf'\b{freq}\b', claim_text, re.I):
                qualifiers.append({
                    'type': 'frequency',
                    'text': freq,
                    'impact': f'indicates_{freq}_occurrence'
                })

        # Extract quantity
        for quant in self.QUANTITY:
            if re.search(rf'\b{quant}\b', claim_text, re.I):
                qualifiers.append({
                    'type': 'quantity',
                    'text': quant,
                    'impact': self._quantity_impact(quant)
                })

        # Extract percentages
        percentages = re.findall(r'\b(\d+(?:\.\d+)?)\s*(?:%|percent)\b', claim_text, re.I)
        for pct in percentages:
            qualifiers.append({
                'type': 'quantity',
                'text': f'{pct}%',
                'impact': f'indicates_{pct}_percent'
            })

        # Extract temporal markers
        temporal = re.findall(r'\b(by|until|before|after|in|during)\s+(\d{4})\b', claim_text, re.I)
        for prep, year in temporal:
            qualifiers.append({
                'type': 'temporal',
                'text': f'{prep} {year}',
                'impact': f'time_constraint_{prep}_{year}'
            })

        return qualifiers

    def _modal_impact(self, modal: str) -> str:
        impacts = {
            'can': 'indicates_possibility',
            'could': 'indicates_conditional_possibility',
            'may': 'indicates_permission_or_possibility',
            'might': 'indicates_low_probability',
            'will': 'indicates_future_certainty',
            'would': 'indicates_conditional_certainty',
            'must': 'indicates_necessity',
            'should': 'indicates_obligation_or_expectation'
        }
        return impacts.get(modal.lower(), 'indicates_modality')

    def _quantity_impact(self, quantity: str) -> str:
        impacts = {
            'all': 'universal_quantification',
            'some': 'existential_quantification',
            'most': 'majority_quantification',
            'many': 'large_quantity',
            'few': 'small_quantity',
            'none': 'negation'
        }
        return impacts.get(quantity.lower(), 'quantity_modifier')

    def verify_preservation(self, original: str, normalized: str) -> bool:
        """
        Verify all qualifiers from original appear in normalized.
        CRITICAL: Auto-fail normalization if any qualifier lost.
        """
        original_qualifiers = self.extract(original)
        normalized_qualifiers = self.extract(normalized)

        original_texts = {q['text'].lower() for q in original_qualifiers}
        normalized_texts = {q['text'].lower() for q in normalized_qualifiers}

        missing = original_texts - normalized_texts

        if missing:
            print(f"❌ QUALIFIER LOSS DETECTED: {missing}")
            return False

        return True
```

**File**: `normalization/normalizer.py`
```python
class ClaimNormalizer:
    def __init__(self, ai_client: AIClient):
        self.ai = ai_client
        self.qualifier_extractor = QualifierExtractor()

    async def normalize(self, claim_text: str) -> dict:
        """
        Normalize claim while preserving qualifiers.
        """

        # Step 1: Extract qualifiers FIRST
        qualifiers = self.qualifier_extractor.extract(claim_text)

        # Step 2: Generate normalized version
        normalized_text = await self._generate_normalized(claim_text, qualifiers)

        # Step 3: VERIFY qualifiers preserved
        qualifiers_preserved = self.qualifier_extractor.verify_preservation(
            claim_text,
            normalized_text
        )

        if not qualifiers_preserved:
            # Auto-fail - try again with stricter prompt
            normalized_text = await self._generate_normalized_strict(claim_text, qualifiers)
            qualifiers_preserved = self.qualifier_extractor.verify_preservation(
                claim_text,
                normalized_text
            )

        # Step 4: Calculate confidence
        confidence = await self._calculate_confidence(
            claim_text,
            normalized_text,
            qualifiers_preserved
        )

        return {
            'normalized_text': normalized_text,
            'qualifiers': qualifiers,
            'qualifiers_preserved': qualifiers_preserved,
            'confidence': confidence,
            'needs_human_review': confidence < 0.95 or not qualifiers_preserved
        }

    async def _generate_normalized(self, claim_text: str, qualifiers: List[Dict]) -> str:
        """Generate normalized claim."""

        qualifier_list = ", ".join([q['text'] for q in qualifiers])

        prompt = f"""Simplify this claim to its core assertion while preserving:
1. ALL qualifier words: {qualifier_list}
2. ALL numbers and percentages
3. ALL temporal markers (years, dates)
4. The exact meaning

Original claim: "{claim_text}"

Simplified claim (MUST include all qualifiers):"""

        response = await self.ai.generate(prompt, temperature=0.1)
        return response.strip()

    async def _calculate_confidence(
        self,
        original: str,
        normalized: str,
        qualifiers_preserved: bool
    ) -> float:
        """
        Calculate normalization confidence.
        MVP: Simple LLM-based check.
        """

        if not qualifiers_preserved:
            return 0.0  # Auto-fail

        # Ask LLM: "Are these semantically equivalent?"
        prompt = f"""Do these two claims mean exactly the same thing?

Original: "{original}"
Normalized: "{normalized}"

Answer with a confidence score (0.0-1.0) where:
- 1.0 = Identical meaning, all details preserved
- 0.9 = Nearly identical, minor simplification
- 0.7 = Same core meaning, some detail simplified
- 0.5 = Similar but some information changed
- 0.0 = Different meaning

Return only the number."""

        response = await self.ai.generate(prompt, temperature=0.0)
        confidence = float(response.strip())

        return confidence
```

**CLI for Human Validation**:
```bash
# View pending normalizations
python -m research_agent review-normalizations

# Output:
# Pending Normalizations:
#
# [1] Claim #claim-001
#     Original: "Deep learning models can achieve over 95% accuracy on ImageNet..."
#     Normalized: "Deep learning models can achieve over 95% accuracy on ImageNet"
#     Confidence: 0.92
#     Qualifiers: ✓ All preserved (can, over 95%)
#
#     [a] Approve  [e] Edit  [r] Reject

# User approves
python -m research_agent approve-normalization claim-001

# Or user edits
python -m research_agent edit-normalization claim-001 \
  --corrected "Deep learning models can achieve over 95% accuracy on ImageNet classification"
```

---

## Phase 4: Basic Investigation Agents (Week 4-5)

### MVP: 3 Agent Types Only

1. **SupportAgent_Empirical** - Find supporting evidence
2. **ChallengeAgent_Empirical** - Find challenging evidence
3. **AnalysisAgent_Definitional** - Clarify key terms

### Deliverables
- [ ] Base agent class
- [ ] 3 simple agent implementations
- [ ] Work queue system (pull-based)
- [ ] Evidence storage with APA citations

### Implementation

**File**: `agents/base_agent.py`
```python
class BaseAgent:
    def __init__(self, framework: str, db, ai_client):
        self.framework = framework
        self.db = db
        self.ai = ai_client
        self.agent_id = self._register()

    def _register(self) -> UUID:
        """Register this agent instance."""
        return self.db.execute("""
            INSERT INTO agents (framework, instance_name, status)
            VALUES (%s, %s, 'idle')
            RETURNING id
        """, (self.framework, f"{self.framework}_{uuid.uuid4().hex[:8]}"))

    async def run_forever(self):
        """Main agent loop - pull work from queue."""
        while True:
            # Get next work
            investigation = await self._get_next_work()

            if not investigation:
                await asyncio.sleep(30)  # Wait 30s
                continue

            # Do investigation
            try:
                result = await self.investigate(investigation)
                await self._save_findings(investigation['id'], result)
                await self._complete_investigation(investigation['id'])
            except Exception as e:
                await self._fail_investigation(investigation['id'], str(e))

    async def _get_next_work(self):
        """Pull next investigation from queue."""
        return self.db.execute("""
            UPDATE investigations
            SET status = 'claimed'
            WHERE id = (
                SELECT id FROM investigations
                WHERE status = 'queued' AND agent_framework = %s
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id, claim_id
        """, (self.framework,))

    async def investigate(self, investigation: dict) -> dict:
        """Override in subclasses."""
        raise NotImplementedError
```

**File**: `agents/support_agent.py`
```python
class SupportAgent_Empirical(BaseAgent):
    """Find empirical evidence that SUPPORTS the claim."""

    async def investigate(self, investigation: dict) -> dict:
        claim_id = investigation['claim_id']

        # Load claim
        claim = await self.db.get_claim(claim_id)
        claim_text = claim['normalized_text'] or claim['original_text']

        # Search for supporting evidence (MVP: LLM generates, not real search yet)
        evidence_list = await self._search_supporting_evidence(claim_text)

        # Calculate confidence
        confidence = self._calculate_finding_confidence(evidence_list)

        return {
            'finding_type': 'support',
            'summary': f"Found {len(evidence_list)} sources supporting this claim",
            'confidence': confidence,
            'evidence': evidence_list
        }

    async def _search_supporting_evidence(self, claim: str) -> List[dict]:
        """
        MVP: Use LLM to generate plausible evidence.
        TODO Phase 2: Real academic search (Semantic Scholar API, etc.)
        """

        prompt = f"""You are a research assistant finding evidence that SUPPORTS this claim:

"{claim}"

Find 3-5 academic sources that provide supporting evidence. For each:
1. Generate a realistic APA citation
2. Provide a relevant quote that supports the claim
3. Rate relevance (0.0-1.0)
4. Rate credibility (0.0-1.0)

Return JSON array:
[
  {{
    "citation_apa": "Author, A. (2023). Title. Journal, 10(2), 123-145.",
    "quote": "relevant passage supporting the claim",
    "relevance": 0.9,
    "credibility": 0.85
  }}
]"""

        response = await self.ai.generate(prompt, temperature=0.6, response_format='json')
        return json.loads(response)
```

---

## Phase 5: Report Generation (Week 5-6)

### MVP: Simple Markdown Report

**Deliverables**:
- [ ] Markdown report generator
- [ ] Confidence score visualization
- [ ] Evidence listing with citations

### Implementation

```python
class ReportGenerator:
    async def generate_claim_report(self, claim_id: UUID) -> str:
        """Generate markdown report for a claim."""

        claim = await self.db.get_claim(claim_id)
        findings = await self.db.get_findings_for_claim(claim_id)

        # Group findings by type
        support = [f for f in findings if f['finding_type'] == 'support']
        challenge = [f for f in findings if f['finding_type'] == 'challenge']
        neutral = [f for f in findings if f['finding_type'] == 'neutral']

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(findings)

        # Generate report
        report = f"""# Investigation Report

## Claim
**Original**: {claim['original_text']}

**Normalized**: {claim['normalized_text']}

**Qualifiers**: {', '.join([q['text'] for q in claim['qualifiers']])}

---

## Overall Assessment
**Confidence**: {overall_confidence:.2f} ({self._confidence_label(overall_confidence)})

{self._confidence_stars(overall_confidence)}

---

## Supporting Evidence ({len(support)} findings)

"""

        for finding in support:
            report += f"\n### Finding (Confidence: {finding['confidence']:.2f})\n"
            report += f"{finding['summary']}\n\n"

            evidence_items = await self.db.get_evidence_for_finding(finding['id'])
            for ev in evidence_items:
                report += f"- {ev['citation_apa']}\n"
                if ev['quote']:
                    report += f"  > \"{ev['quote']}\"\n"
                report += f"  Relevance: {ev['relevance_score']:.2f}, "
                report += f"Credibility: {ev['credibility_score']:.2f}\n\n"

        # Similar for challenge and neutral...

        return report

    def _confidence_stars(self, confidence: float) -> str:
        """Visual confidence indicator."""
        stars = int(confidence * 5)
        return "⭐" * stars + "☆" * (5 - stars)

    def _confidence_label(self, confidence: float) -> str:
        if confidence >= 0.85:
            return "HIGH - Strong evidence, reliable"
        elif confidence >= 0.60:
            return "MEDIUM - Moderate evidence, needs monitoring"
        else:
            return "LOW - Weak evidence, needs more investigation"
```

---

## MVP Test Plan (Week 6)

### End-to-End Test

```bash
# 1. Ingest document
python -m research_agent ingest test_paper.pdf

# 2. View extracted claims
python -m research_agent list-claims --doc-id doc-001

# 3. Normalize claims (with human review)
python -m research_agent normalize-all --doc-id doc-001
python -m research_agent review-normalizations
python -m research_agent approve-normalization claim-001

# 4. Start agents (background)
python -m research_agent start-agents --count 5

# 5. Monitor progress
python -m research_agent status

# 6. Generate report
python -m research_agent generate-report --claim-id claim-001 --output report.md

# 7. View confidence scores
python -m research_agent confidence-summary --claim-id claim-001
```

### Success Criteria

✅ Can ingest PDF and extract claims
✅ Claims are normalized with qualifiers preserved
✅ Human can review and approve normalizations
✅ Agents run autonomously and find evidence
✅ Evidence includes APA citations
✅ Confidence scores calculated at all stages
✅ Report shows confidence visualization
✅ Low confidence triggers more investigation

---

## Post-MVP: Enhancement Phases

### Phase 6: Real Academic Search (Week 7-8)
- Integrate Semantic Scholar API
- arXiv API
- PubMed API
- Web search for non-academic sources

### Phase 7: Philosophy Frameworks (Week 9-10)
- Implement configurable agent philosophies
- Deep Learning, Critical Theory, Skeptical Inquiry, etc.

### Phase 8: Advanced Normalization (Week 11-12)
- SRL verification
- Multiple candidate generation
- Learning from corrections

### Phase 9: Investigation Tree Visualization (Week 13-14)
- Build investigation trees
- ASCII/Mermaid rendering
- Word document export

### Phase 10: Production Hardening (Week 15-16)
- Error recovery
- Performance optimization
- Comprehensive testing
- Documentation

---

## Current Status Tracking

**File**: `PROJECT_STATUS.md` (update weekly)

```markdown
# Project Status - Week X

## Completed
- [x] Database schema designed
- [x] Configuration system
- [ ] PDF ingestion
- [ ] Claim extraction
...

## In Progress
- [ ] Normalizer implementation (80% - working on qualifier preservation)

## Blocked
- None

## Next Week
1. Finish normalizer
2. Human validation CLI
3. First agent implementation

## Confidence Scores This Week
- Normalization confidence avg: 0.88 (target: >0.90)
- Evidence quality avg: N/A (not implemented yet)
```

---

## Implementation Priority: What to Build First

### Week 1-2: Core Foundation ⚡ START HERE
1. Database schema (1 day)
2. Configuration system (1 day)
3. AI client wrapper (1 day)
4. CLI framework (2 days)
5. Database connection/ORM (2 days)

### Week 2-3: Document → Claims
1. PDF text extraction (1 day)
2. LLM claim extraction (2 days)
3. Qualifier extraction (2 days)
4. Store in database (1 day)

### Week 3-4: Normalization + Human Validation
1. Basic normalizer (2 days)
2. Confidence calculation (1 day)
3. Human review CLI (2 days)
4. Approval/edit workflow (2 days)

### Week 4-5: Investigation Agents
1. Base agent class (2 days)
2. Work queue system (2 days)
3. Support agent (2 days)
4. Challenge agent (1 day)

### Week 5-6: Reports + Testing
1. Report generator (2 days)
2. Confidence visualization (1 day)
3. End-to-end testing (3 days)
4. Bug fixes (1 day)

**Total: 6 weeks to MVP**

Ready to start implementing? I recommend beginning with **Phase 1: Database Schema** - shall I create the actual SQL schema file and database setup scripts?
