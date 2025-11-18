# Architecture Refactor: Claude as the AI

## Current (Wrong) Architecture

```
┌─────────┐     ┌────────────┐     ┌──────────────┐     ┌────────┐
│   PDF   │ --> │ Python     │ --> │ OpenAI/      │ --> │ Claims │
│         │     │ Extractor  │     │ Anthropic    │     │        │
└─────────┘     └────────────┘     │ API Call     │     └────────┘
                                   └──────────────┘
                                         ↑
                                   Requires API key
                                   External service
                                   Extra complexity
```

## New (Correct) Architecture

```
┌─────────┐     ┌────────────┐     ┌────────────────┐     ┌────────┐
│   PDF   │ --> │ Python     │ --> │ Claude Code    │ --> │ Claims │
│         │     │ PyPDF2     │     │ (YOU)          │     │        │
└─────────┘     └────────────┘     │ Direct         │     └────────┘
                                   │ Processing     │
                                   └────────────────┘
                                          ↑
                                   No API keys needed
                                   You're already here
                                   Simpler & faster
```

## What Changes

### REMOVE These Files/Sections:
- ❌ `research_agent/utils/ai_client.py` - External API calls
- ❌ `config/config.yaml` - API key configuration
- ❌ All `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` references
- ❌ `openai` and `anthropic` from requirements.txt

### REPLACE With:
- ✅ Direct Claude integration via function calls
- ✅ Simple Python interfaces that I execute
- ✅ No configuration needed

### Example: Claim Extraction

**OLD WAY (external API):**
```python
class ClaimExtractor:
    def __init__(self, ai_client):
        self.ai_client = ai_client  # Calls OpenAI/Anthropic

    async def extract_claims(self, text):
        prompt = "Extract claims from: " + text
        response = await self.ai_client.generate(prompt)  # ❌ External call
        return parse_json(response)
```

**NEW WAY (Claude Code):**
```python
class ClaimExtractor:
    """
    In Claude Code, this is executed by calling Claude directly.
    The user invokes: python -m research_agent extract-claims file.pdf

    Claude Code sees the prompt and responds with claims.
    No external API needed - Claude Code IS the AI.
    """

    def extract_claims(self, text):
        # Claude Code will see this prompt and respond
        print(f"""
        I am extracting claims from this text. I will identify:
        - Factual assertions
        - Theoretical claims
        - Normative statements
        - Empirical observations

        Text to analyze:
        {text[:5000]}

        Please provide claims in this format:
        [{"text": "...", "type": "...", "qualifiers": [...]}]
        """)

        # In Claude Code, I (Claude) would then respond with the claims
        # The system captures my response as the extraction result
```

## How Agents Work

### OLD WAY:
```python
# Agent spawns and makes API calls
async def investigate(claim):
    evidence = await ai_client.generate(f"Find evidence for: {claim}")
    return evidence
```

### NEW WAY:
```python
# Agent presents work to Claude, who performs it
def investigate(claim):
    print(f"""
    INVESTIGATION REQUEST
    Claim: {claim}

    I need to:
    1. Search for supporting evidence
    2. Search for contradicting evidence
    3. Assess credibility

    Claude, please investigate this claim and provide evidence.
    """)

    # Claude Code (me) responds with investigation results
    # System captures response and stores in database
```

## Database Integration

The database stays the same! It's a good design:
- ✅ PostgreSQL stores all state
- ✅ Work queue manages investigations
- ✅ Agents pull work and store results

**Only change:** Instead of agents calling external APIs, they call me (Claude Code).

## How This Works in Practice

### User runs:
```bash
python -m research_agent extract "sample papers/SHORT-The-Myth-of-Mental-Illness.pdf"
```

### System does:
1. ✅ Read PDF with PyPDF2
2. ✅ Display text to me (Claude Code)
3. ✅ Ask me to extract claims
4. ✅ I respond with claims (like I just did with the 17 claims!)
5. ✅ Store in database

### For normalization:
```bash
python -m research_agent normalize <claim_id>
```

### System does:
1. ✅ Load claim from database
2. ✅ Show me the claim
3. ✅ Ask me to normalize it while preserving qualifiers
4. ✅ I provide normalized version
5. ✅ QualifierExtractor verifies preservation (auto-fail if lost)
6. ✅ Store result

### For investigation:
```bash
python -m research_agent investigate <claim_id>
```

### System does:
1. ✅ Load claim from database
2. ✅ Show me the claim
3. ✅ Ask me to search for evidence (I can use WebSearch!)
4. ✅ I provide evidence with sources
5. ✅ Store findings in database

## Paper Discovery Workflow

**User asks:** "Find papers about cognitive behavioral therapy effectiveness"

**I (Claude) do:**
1. ✅ Use WebSearch to find relevant papers
2. ✅ Provide list of URLs and paper titles
3. ✅ User downloads PDFs to `sample papers/`
4. ✅ User runs: `git sync` (I see the new papers)
5. ✅ User runs: `python -m research_agent extract paper.pdf`
6. ✅ I extract claims from the new paper

## Benefits

1. **No API Keys Required** - You're already Claude Code
2. **Simpler Architecture** - Direct execution, no HTTP calls
3. **Better Integration** - I can use my tools (WebSearch, WebFetch)
4. **Lower Latency** - No network roundtrips
5. **Cost Effective** - No per-token API charges
6. **More Reliable** - No API rate limits or outages

## Implementation Plan

1. **Remove external API code** (30 minutes)
2. **Create Claude-direct interfaces** (1 hour)
3. **Test with Szasz paper** (30 minutes)
4. **Extract full 50+ claims** (I just do it!)
5. **Set up database** (if needed)
6. **Demonstrate full pipeline** (1 hour)

## Questions to Resolve

1. **Database**: Do you want PostgreSQL running, or should we use a simpler SQLite?
2. **Paper Access**: Should I search for papers now and give you URLs to download?
3. **CLI vs Web**: Continue in Claude Code web, or switch to CLI for longer context?

Let me know and I'll refactor the system to work this way!
