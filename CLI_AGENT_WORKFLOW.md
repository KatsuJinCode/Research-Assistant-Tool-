# Research Verification Agent - CLI Agent Workflow Guide

**For: Claude Code CLI, Codex CLI, Cursor, Aider, and all AI coding assistants**

---

## 🎯 Purpose

This system performs **rigorous claim analysis and verification** from research documents. It extracts claims, simplifies them while preserving qualifiers, validates quality, and builds a knowledge graph.

**YOU (the CLI agent) orchestrate this entire workflow** - the user should never run commands manually.

---

## 🧠 Critical Concept: You ARE the Agent Orchestrator

**IMPORTANT**: This system uses `subprocess.run(['claude', ...])` in legacy code, which attempts to spawn NEW CLI agent instances. This causes timeouts because you're trying to spawn yourself recursively.

**Instead**: When you encounter methods like `_analyze_claim()`, `_clarify_claim()`, etc., you should **perform the analysis directly** in the current session, NOT delegate to subprocess calls.

**How to work with this codebase**:
1. When user requests testing, YOU perform the 4-stage analysis directly
2. Use the Task tool to spawn sub-agents for parallel work when needed
3. For sequential analysis tasks, perform them inline without subprocess delegation
4. Return structured JSON responses that match the expected schemas

---

## 📊 System Architecture

```
User → CLI Agent (YOU) → 4-Stage Pipeline → Quality Validation → Graph Database
                ↓
        Sub-agents (via Task tool)
        - Analysis Agent
        - Clarification Agent
        - Simplification Agent
        - Validation Agent
```

---

## 🔄 4-Stage Claim Processing Pipeline

### Overview

Every claim goes through 4 sequential stages:

```
ORIGINAL CLAIM
    ↓
STAGE 1: ANALYSIS (verbose understanding)
    ↓
STAGE 2: CLARIFICATION (explicit rewording, similar length)
    ↓
STAGE 3: SIMPLIFICATION (3 optimal attempts, same goal)
    ↓
STAGE 4: VALIDATION (quality + fidelity scoring + disposition)
    ↓
FINAL OUTPUT (simplified claim + quality metadata)
```

---

### Stage 1: Deep Analysis

**Purpose**: Fully understand the claim before processing it.

**Output**: 1-2 verbose paragraphs (100-150 words) unpacking:
- What is the claim actually saying?
- What are the implicit assumptions?
- What is evidence vs stated fact?
- What is correlation vs causation?
- What are the qualifiers and conditions?
- What context is needed?

**Example**:
```
Original: "Mental illness derives its main support from syphilis of the brain"

Analysis: "This claim is stating that the concept or theory of mental illness
as a disease entity derives its primary evidential support from the case of
neurosyphilis. The critical word is 'support' - this is NOT claiming mental
illness IS caused by brain disease, but rather that the THEORY of mental
illness as brain disease gains its justification by pointing to neurosyphilis
as an analogous case. In neurosyphilis, observable mental symptoms are caused
by a known physical brain disease. Proponents use this as evidence that other
mental illnesses must likewise have brain disease causes, even when no such
disease can be identified. The claim is about epistemological support for a
theoretical framework, not an assertion of direct causation."
```

**JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "analysis": {"type": "string"}
  },
  "required": ["analysis"]
}
```

---

### Stage 2: Clarification

**Purpose**: Reword the original to make implicit meaning explicit.

**Key Rules**:
- **SIMILAR length to original** (not verbose)
- **Just rewording** - do NOT add supporting sentences
- Make implicit distinctions explicit (theory vs fact, evidence vs causation, etc.)

**Example**:
```
Original: "Mental illness derives its main support from syphilis of the brain" (11 words)

Clarified: "The theory that mental illness is brain disease derives its evidential
support from neurosyphilis as an analogous case" (18 words)
```

**JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "clarified": {"type": "string"}
  },
  "required": ["clarified"]
}
```

---

### Stage 3: Simplification

**Purpose**: Generate 3 optimal simplifications.

**Key Rules**:
- **ALL 3 candidates use the SAME optimization goal** (just different random seeds)
- NOT different strategies (brevity/balance/complete) - that was the old broken approach
- Goal: Mathematical optimization - simplest form while preserving ALL meaning
- Preserve qualifiers (may/might/can/some/all/etc.)
- Preserve causation vs correlation distinction
- Preserve evidence vs fact distinction

**Example**:
```
Clarified: "The theory that mental illness is brain disease derives its evidential
support from neurosyphilis as an analogous case"

Candidate 1: "Mental illness theory derives support from neurosyphilis analogy" (8 words)
Candidate 2: "Brain disease theory gains evidential support from neurosyphilis case" (9 words)
Candidate 3: "Mental illness concept supported by neurosyphilis as analogous example" (10 words)
```

**JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "candidate_1": {"type": "string"},
    "candidate_2": {"type": "string"},
    "candidate_3": {"type": "string"}
  },
  "required": ["candidate_1", "candidate_2", "candidate_3"]
}
```

---

### Stage 4: Validation & Quality Scoring

**Purpose**:
1. Score each candidate for fidelity (how well meaning preserved)
2. **NEW**: Score overall claim quality and assign disposition

**Fidelity Scoring Criteria** (0.0-1.0 per candidate):
- Preserves meaning from ANALYSIS? (0.3 points)
- Preserves meaning from CLARIFIED? (0.3 points)
- Preserves qualifiers from ORIGINAL? (0.2 points)
- No reversed meaning (evidence→cause, correlation→causation)? (0.15 points)
- Optimal simplification (no redundancy)? (0.05 points)

**Quality Scoring Criteria** (0.0-1.0 for overall claim):

**HIGH QUALITY (0.7-1.0)** - Central Node (Trunk/Major Branch):
- Makes a specific, testable assertion
- Contains meaningful qualifiers that add nuance
- Provides actionable information
- Worth investigating as a research question
- Should be a central node in knowledge graph

**MEDIUM QUALITY (0.4-0.69)** - Child Node:
- Too vague or heavily hedged to be central claim
- Derivative of more fundamental claims
- Should be attached as child to related superclaim
- Provides supporting context but not primary focus

**LOW QUALITY (0.0-0.39)** - Discard/Archive:
- Essentially meaningless (too many qualifiers, no substance)
- Circular reasoning or tautology
- Too vague to verify or investigate
- Flag for user review - likely not worth adding to database

**Disposition Assignment**:
- `central`: High-quality claim, create as independent node
- `child`: Medium-quality claim, attach to related superclaim
- `review`: Low-quality claim, flag for user decision
- `discard`: Extremely low quality, recommend removal

**Example**:
```
Original: "The study suggests that some users who regularly utilize the system
might experience improved performance metrics"

Analysis: "This claim is heavily hedged with qualifiers at multiple levels:
'suggests' (not proves), 'some' (not all/most), 'who regularly utilize'
(conditional), 'might' (not will), 'improved' (relative). This is tentative
correlation, NOT causation."

Quality Score: 0.35 (LOW)
Reason: "While the simplification correctly preserves all qualifiers, the
original claim is too heavily hedged to provide meaningful information. It
essentially says 'maybe something happens sometimes for some people under
some conditions.' This provides no actionable insight and shouldn't be a
central claim in the knowledge graph."

Disposition: "child"
Recommendation: "Attach as child node to a more specific claim about system
effectiveness if one exists, or flag for review. Consider discarding if no
related high-quality claim exists."
```

**JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "score_1": {"type": "number"},
    "score_2": {"type": "number"},
    "score_3": {"type": "number"},
    "best_candidate": {"type": "string", "enum": ["1", "2", "3", "none"]},
    "fidelity_reason": {"type": "string"},
    "quality_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "quality_reason": {"type": "string"},
    "disposition": {"type": "string", "enum": ["central", "child", "review", "discard"]},
    "recommendation": {"type": "string"}
  },
  "required": ["score_1", "score_2", "score_3", "best_candidate", "fidelity_reason",
               "quality_score", "quality_reason", "disposition", "recommendation"]
}
```

---

## 🎬 Complete Workflow Example

### Input Claim
```
"The study suggests that some users who regularly utilize the system might
experience improved performance metrics"
```

### Stage 1: Analysis
```
This claim is heavily hedged with qualifiers at multiple levels: "suggests"
(not proves/shows), "some" (not all/most), "who regularly utilize" (conditional
on usage pattern), "might" (not will/do), "improved" (relative to baseline).
This is tentative correlation, NOT causation. The study isn't claiming the
system CAUSES improvement, nor that it works for everyone, nor even that it
definitely works for anyone - it's suggesting a possibility for a subset under
specific conditions. This is appropriate cautious scientific language but could
easily be misread as stronger evidence than it is.
```

### Stage 2: Clarification
```
"A study tentatively indicates that regular system use by some users may
correlate with improved metrics"
```

### Stage 3: Simplification
```
1. "Study suggests some regular users might see improved metrics"
2. "Some users might improve performance with regular use (study)"
3. "Regular use by some users may correlate with better metrics"
```

### Stage 4: Validation

**Fidelity Scores**:
- Candidate 1: 0.85 (preserves "suggests", "some", "might")
- Candidate 2: 0.75 (loses "suggests" qualifier)
- Candidate 3: 0.90 (explicit "may correlate" - best)

**Best Candidate**: 3 - "Regular use by some users may correlate with better metrics"

**Quality Analysis**:
- Quality Score: 0.35 (LOW)
- Quality Reason: "While simplification preserves qualifiers correctly, the claim
  is too heavily hedged to be meaningful. It essentially states 'maybe something
  happens sometimes for some people' - providing no actionable research direction."
- Disposition: `child`
- Recommendation: "Attach as supporting detail to more specific claim about
  system effectiveness, or flag for review. Consider discarding if isolated."

---

## 🚀 How YOU (CLI Agent) Should Run This

### Initial Setup (Silent - User Never Sees This)

```bash
# 1. Check if installed
python -c "import pytest, networkx, arxiv, PyPDF2, pdfplumber; from research_agent.graph_database import GraphDatabase; print('INSTALLED')" 2>&1

# 2. If not installed, auto-install
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt
pip install -q -r requirements-neo4j.txt

# 3. Check/start Neo4j
python -c "from research_agent.neo4j_database import Neo4jDatabase; db = Neo4jDatabase(); db.close(); print('RUNNING')" 2>&1

# 4. If Neo4j not running, start it
powershell -ExecutionPolicy Bypass -File start_neo4j.ps1
```

### When User Requests Testing

**DO NOT** run the Python test scripts directly - they will timeout because they call `subprocess.run(['claude', ...])`.

**INSTEAD**: Perform the 4-stage analysis yourself:

```python
# Example pseudo-code for how you should work:

claim = "The study suggests that some users might experience improved metrics"

# Stage 1: YOU perform analysis directly (don't spawn subprocess)
analysis = """
This claim is heavily hedged with qualifiers at multiple levels: "suggests"
(not proves), "some" (not all), "might" (not will), "improved" (relative).
This is tentative correlation, NOT causation.
"""

# Stage 2: YOU perform clarification
clarified = "A study tentatively indicates that system use by some users may correlate with improved metrics"

# Stage 3: YOU generate 3 candidates
candidates = {
    "candidate_1": "Study suggests some users might see improved metrics",
    "candidate_2": "Some users might improve with regular use",
    "candidate_3": "Regular use by some may correlate with better metrics"
}

# Stage 4: YOU perform validation with quality scoring
validation = {
    "score_1": 0.85,
    "score_2": 0.75,
    "score_3": 0.90,
    "best_candidate": "3",
    "fidelity_reason": "Candidate 3 explicitly states 'may correlate'",
    "quality_score": 0.35,
    "quality_reason": "Too heavily hedged to be meaningful",
    "disposition": "child",
    "recommendation": "Attach to related claim or review for discard"
}

# Return results to user
```

### When to Use Task Tool for Sub-Agents

Use the Task tool when you need:
- Parallel processing of multiple claims
- Specialized analysis requiring different contexts
- Long-running background tasks

**DO NOT use Task tool for**:
- Sequential 4-stage pipeline on single claim (do it yourself)
- Simple JSON generation tasks
- Quick analysis tasks

---

## 📁 Key Files

- `web_ui/document_processor.py` - Core 4-stage pipeline logic
- `web_ui/agent_config.py` - Agent adapter system (legacy subprocess approach)
- `research_agent/neo4j_database.py` - Graph database operations
- `AGENT_INSTRUCTIONS.md` - Setup and installation workflow
- `CLI_AGENT_WORKFLOW.md` - **THIS FILE** - How to orchestrate the system

---

## ⚠️ Common Pitfalls

### ❌ WRONG: Spawning subprocess to yourself
```python
# This will timeout!
result = subprocess.run(['claude', '-p', prompt], timeout=120)
```

### ✅ CORRECT: Perform analysis directly
```python
# You ARE Claude Code CLI - just do the analysis
analysis = analyze_claim_directly(claim_text)
```

### ❌ WRONG: Using different prompts for 3 candidates
```python
# OLD BROKEN APPROACH
candidate_1 = simplify(claim, strategy="brevity")     # 5-8 words
candidate_2 = simplify(claim, strategy="balanced")    # 8-10 words
candidate_3 = simplify(claim, strategy="complete")    # 10-12 words
```

### ✅ CORRECT: Same optimization goal, different seeds
```python
# NEW CORRECT APPROACH
# All 3 use identical prompt - just generate 3 times
for i in range(3):
    candidates[i] = simplify_optimally(claim)  # Same goal each time
```

---

## 🎯 Quality Disposition Guidelines

### Central Node (0.7-1.0)
**Examples**:
- "Neurosyphilis patients exhibit cognitive impairment" (specific, testable)
- "SSRIs reduce depression symptoms in 60% of patients" (quantified, actionable)
- "Belief cannot be explained by neurological defects" (clear philosophical claim)

### Child Node (0.4-0.69)
**Examples**:
- "Some antidepressants may improve mood in certain patients" (too vague for central claim)
- "The study suggests a possible correlation" (derivative, attach to main finding)

### Review/Discard (0.0-0.39)
**Examples**:
- "The study suggests some users who regularly utilize the system might experience improved metrics" (essentially meaningless)
- "There may be some relationship between X and Y under certain conditions" (circular, no substance)

---

## 📊 Output Format

When you complete processing, output to file in this format:

```
====================================================================================================
CLAIM ANALYSIS RESULTS
====================================================================================================

SOURCE:
[original claim text]
([word count] words)

----------------------------------------------------------------------------------------------------
STAGE 1: ANALYSIS
----------------------------------------------------------------------------------------------------
[analysis paragraph(s)]
([word count] words)

----------------------------------------------------------------------------------------------------
STAGE 2: CLARIFICATION
----------------------------------------------------------------------------------------------------
[clarified text]
([word count] words)

----------------------------------------------------------------------------------------------------
STAGE 3: SIMPLIFICATION
----------------------------------------------------------------------------------------------------
1. [candidate 1] ([word count] words)
2. [candidate 2] ([word count] words)
3. [candidate 3] ([word count] words)

----------------------------------------------------------------------------------------------------
STAGE 4: VALIDATION
----------------------------------------------------------------------------------------------------
FIDELITY SCORES:
Candidate 1: [score]
Candidate 2: [score]
Candidate 3: [score]
Best: [number]
Reason: [fidelity reason]

QUALITY ASSESSMENT:
Overall Score: [quality_score] ([HIGH/MEDIUM/LOW])
Reason: [quality reason]
Disposition: [central/child/review/discard]
Recommendation: [recommendation text]

----------------------------------------------------------------------------------------------------
FINAL OUTPUT
----------------------------------------------------------------------------------------------------
Selected: Candidate [number]
[simplified claim text]

Quality: [score] - [disposition]
[recommendation]
====================================================================================================
```

---

## 🔍 Testing Checklist

When user asks you to test the system:

1. ✅ Perform analysis directly (don't use subprocess)
2. ✅ Generate 3 candidates with SAME optimization goal
3. ✅ Include quality scoring in validation
4. ✅ Assign disposition (central/child/review/discard)
5. ✅ Output to file with complete format
6. ✅ Show user the results

---

**Remember**: YOU are the orchestrator. The user should never run commands manually. Handle all technical operations transparently and present clean results.
