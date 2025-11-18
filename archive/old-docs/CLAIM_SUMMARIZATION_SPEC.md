# Claim Summarization Specification

**Version:** 1.0
**Last Updated:** 2025-01-17
**Owner:** Research Assistant Tool - Claude Code CLI

---

## Purpose

This document defines the SINGLE AUTHORITATIVE specification for how research claims should be summarized for display in the web UI graph visualization.

## Core Principle

**Maximize simplicity while PRESERVING qualifiers**

Qualifiers change the meaning of claims. A claim that says "might improve performance" is fundamentally different from "improves performance". Our summarization MUST preserve these distinctions.

---

## Critical Qualifiers (NEVER Remove)

### Modal Verbs (Uncertainty)
- may, might, can, could
- should, would
- must, shall

### Quantifiers (Scope)
- all, some, few, many, most
- every, each
- several, multiple

### Hedging Language
- suggests, indicates, appears
- likely, possibly, probably
- tend to, seem to

---

## Summarization Process

### Input
Full research claim text (typically 20-100 words)

### Output
Two versions:

1. **simplified** (5-12 words)
   - Ultra-concise core assertion
   - MUST include key qualifiers
   - Used as node labels in graph

2. **normalized** (15-25 words)
   - Medium-length version
   - More complete but still simplified
   - Used in tooltips/detail views

### Method
- Powered by Claude Code CLI (AI sub-agent)
- NO hard-coded word limits beyond ranges above
- NO rule-based extraction that loses qualifiers
- Intelligent simplification that understands meaning

---

## What to Remove

### Safe to Remove:
- Redundant phrases ("in other words", "that is to say")
- Verbose constructions ("it should be noted that", "one could argue that")
- Unnecessary elaboration and examples
- Repetitive content

### NEVER Remove:
- Qualifiers (see list above)
- Core subject-verb-object
- Uncertainty markers
- Scope limiters

---

## Examples

### Example 1: Empirical Finding
**Original:**
"The longitudinal study conducted over 24 months suggests that some users who regularly utilize the system might experience improved performance metrics in comparison to the control group."

**simplified:**
"Some users might experience improved performance"

**normalized:**
"Study suggests some regular users might experience improved performance metrics"

**Preserved Qualifiers:** "suggests", "some", "might"

---

### Example 2: Methodological Claim
**Original:**
"It is important to note that researchers should employ randomized controlled trials when investigating causal relationships, as this methodology can help eliminate confounding variables."

**simplified:**
"Researchers should use RCTs for causal studies"

**normalized:**
"Randomized controlled trials should be used to investigate causal relationships"

**Preserved Qualifiers:** "should", "can help"

---

### Example 3: Interpretive Claim
**Original:**
"The findings appear to indicate that all participants in the experimental condition demonstrated statistically significant improvements, which could suggest a robust treatment effect."

**simplified:**
"All participants showed significant improvement"

**normalized:**
"Findings suggest all experimental participants showed significant improvements"

**Preserved Qualifiers:** "appear", "all", "could suggest"

---

## Implementation

### Single Source of Truth
- File: `web_ui/document_processor.py`
- Method: `_simplify_claim_with_agent()`
- Agent: Claude Code CLI sub-agent

### Usage
```python
# Correct usage:
summary_result = self._simplify_claim_with_agent(claim_text)
claim_node = {
    'summary': summary_result['simplified'],
    'normalized': summary_result['normalized']
}

# NEVER use these (broken implementations):
# - IntelligentSummarizer  (stub with TODO)
# - ClaimSimplifierAgent   (rule-based, loses qualifiers)
# - ClaimSummarizer        (hard-coded patterns)
```

### Deprecated Code
The following modules are DEPRECATED and should NOT be used:
- `research_agent/claim_analysis/intelligent_summarizer.py`
- `research_agent/claim_analysis/claim_simplifier_agent.py`
- `research_agent/claim_analysis/claim_summarizer.py`

These were previous attempts that either:
1. Used hard-coded word limits
2. Applied rule-based extraction that deleted qualifiers
3. Were stubs with TODO comments

---

## Quality Checks

Before accepting a summary, verify:

1. **Qualifier Preservation**: Count qualifiers in original vs. summary
   - Missing qualifiers = FAILED

2. **Length Constraints**:
   - simplified: 5-12 words
   - normalized: 15-25 words
   - Outside range by >3 words = WARNING (not fatal)

3. **Meaning Preservation**:
   - Summary accurately reflects original claim
   - No information added that wasn't in original
   - No meaning reversed (e.g., "might not" → "does")

4. **Grammatical Correctness**:
   - Complete sentences
   - Proper subject-verb agreement
   - No orphaned qualifiers ("might improved" ✗)

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Hard-coded word limits
```python
# WRONG - loses qualifiers to hit arbitrary limit
summary = ' '.join(claim.split()[:5])
```

### ❌ Mistake 2: Treating qualifiers as "filler words"
```python
# WRONG - "may", "some", "might" are NOT filler!
filler = {'may', 'might', 'some', 'can', ...}
words = [w for w in words if w not in filler]
```

### ❌ Mistake 3: Multiple competing implementations
```python
# WRONG - creates confusion about which to use
from summarizer_v1 import summarize
from summarizer_v2 import simplify
from summarizer_final import process
```

### ✅ Correct: Single AI-powered method
```python
# RIGHT - one method, AI-powered, qualifier-aware
summary = self._simplify_claim_with_agent(claim_text)
```

---

## Testing

### Unit Test Requirements
1. Test with claims containing each qualifier type
2. Verify qualifiers appear in output
3. Test length constraints (should warn, not fail)
4. Test edge cases (very short claims, very long claims)

### Example Test Cases
```python
def test_preserves_modal_qualifiers():
    claim = "The system might improve efficiency"
    result = processor._simplify_claim_with_agent(claim)
    assert "might" in result['simplified'].lower()

def test_preserves_quantifiers():
    claim = "Some users experienced improved outcomes"
    result = processor._simplify_claim_with_agent(claim)
    assert "some" in result['simplified'].lower()
```

---

## Changelog

### v1.0 (2025-01-17)
- Initial specification
- Consolidated 3 broken implementations into single AI-powered method
- Emphasized qualifier preservation as primary requirement
- Defined clear examples and anti-patterns

---

## References

- Implementation: `web_ui/document_processor.py:_simplify_claim_with_agent()`
- Incident Report: `WEBSOCKET_INCIDENT_REPORT.md` (lesson on testing before committing)
- User Requirement: "maximally simplifying each claim while preserving qualifiers"
