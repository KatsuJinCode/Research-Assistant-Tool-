# Evidence Auto-Linking Strategy
## Critical System Component - Research & Design

**Status**: Research Phase
**Priority**: CRITICAL - Make or Break Feature
**Last Updated**: 2025-01-20

---

## Problem Statement

When documents are processed and evidence is extracted, we need to automatically link evidence to relevant claims with high accuracy. This determines whether:
- Claims get properly supported/contradicted
- Confidence scores are meaningful
- The entire research system provides value

**Simple text matching is NOT sufficient.**

---

## Proposed Multi-Stage Pipeline

### Stage 1: Semantic Embedding Similarity
**Purpose**: Find potentially related claim-evidence pairs

**Approach**:
- Generate embeddings for all claims and evidence using sentence transformers
- Model: `all-mpnet-base-v2` or `all-MiniLM-L6-v2`
- Compute cosine similarity between claim embeddings and evidence embeddings
- Threshold: Consider pairs with similarity > 0.7 as candidates

**Libraries**:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-mpnet-base-v2')
```

**Advantages**:
- Captures semantic meaning beyond keywords
- Fast computation with vector databases
- Works across different phrasings

**Limitations**:
- Doesn't determine support vs contradiction
- Can match topically related but irrelevant content
- Requires threshold tuning

---

### Stage 2: LLM-Based Classification
**Purpose**: Determine relationship type (SUPPORTS / CONTRADICTS / IRRELEVANT)

**Approach**:
For each candidate pair from Stage 1, use LLM to classify:

```
Claim: "Climate change is caused by human activity"
Evidence: "CO2 levels have increased 40% since industrial revolution"

Classification: SUPPORTS | CONTRADICTS | IRRELEVANT
Confidence: 0.0 - 1.0
Reasoning: [brief explanation]
```

**LLM Prompt Template**:
```
You are an evidence classifier for a research analysis system.

CLAIM: {claim_text}
EVIDENCE: {evidence_text}

Determine if the evidence:
1. SUPPORTS the claim
2. CONTRADICTS the claim
3. Is IRRELEVANT to the claim

Respond in JSON:
{
  "relationship": "SUPPORTS|CONTRADICTS|IRRELEVANT",
  "confidence": 0.85,
  "reasoning": "Brief explanation"
}
```

**Advantages**:
- Understands nuanced relationships
- Can explain reasoning (for user review)
- Handles complex logical relationships

**Limitations**:
- Slower than embedding similarity
- Costs per API call
- May hallucinate relationships

---

### Stage 3: Confidence Scoring
**Purpose**: Weight the strength of evidence-claim links

**Factors to Consider**:
1. **Semantic Similarity Score** (from Stage 1)
2. **LLM Classification Confidence** (from Stage 2)
3. **Evidence Quality Score**:
   - Source credibility (journal tier, peer review status)
   - Citation count
   - Publication date (more recent = higher weight)
4. **Claim Specificity**:
   - Broad claims need more evidence
   - Specific claims can be strongly affected by single evidence

**Combined Score Formula**:
```python
link_strength = (
    semantic_similarity * 0.3 +
    llm_confidence * 0.4 +
    evidence_quality * 0.2 +
    claim_specificity_factor * 0.1
)
```

---

## Alternative Approaches to Research

### Option A: Fine-Tuned NLI Model
Use Natural Language Inference models specifically trained for claim-evidence pairs:
- `microsoft/deberta-v3-large-nli`
- `facebook/bart-large-mnli`

**Pros**: Fast, designed for this task
**Cons**: May need domain-specific fine-tuning

### Option B: Hybrid Ensemble
Combine multiple approaches and vote:
- Embedding similarity
- NLI model
- LLM classification
- Keyword overlap

**Pros**: More robust
**Cons**: Complex, slower

### Option C: Graph-Based Propagation
After initial linking, propagate evidence through claim hierarchies:
- Evidence supporting child claim → weak support for parent
- Contradiction at child level → flag parent for review

**Pros**: Leverages graph structure
**Cons**: Errors can propagate

---

## Implementation Considerations

### Performance
- **Batch Processing**: Process evidence linking in batches
- **Caching**: Store embeddings in Neo4j as node properties
- **Async**: Run LLM calls concurrently with rate limiting

### User Control
- **Review Mode**: Show proposed links before applying
- **Manual Override**: Users can add/remove links
- **Confidence Threshold**: User-configurable minimum link strength

### Continuous Improvement
- **User Feedback Loop**: Track when users remove auto-links
- **A/B Testing**: Test different threshold values
- **Metrics Dashboard**: Show linking accuracy over time

---

## Database Schema for Evidence Links

```cypher
// Store link metadata on relationship
(Claim)-[r:SUPPORTED_BY {
    auto_linked: true,
    semantic_similarity: 0.85,
    llm_confidence: 0.92,
    evidence_quality: 0.78,
    link_strength: 0.87,
    created_at: datetime(),
    reasoning: "Evidence directly demonstrates mechanism"
}]->(Evidence)
```

---

## Research Questions to Resolve

1. **Which embedding model performs best for scientific claims?**
   - Test: `all-mpnet-base-v2`, `all-MiniLM-L6-v2`, `sentence-t5-base`
   - Metric: Manual evaluation on 100 claim-evidence pairs

2. **What's the optimal similarity threshold?**
   - Test: 0.6, 0.7, 0.8, 0.9
   - Metric: Precision/Recall on validated dataset

3. **Should we use NLI models or LLM prompting?**
   - Compare: DeBERTa-NLI vs GPT-4 vs Claude
   - Metric: Accuracy, cost, speed

4. **How to handle contradictory evidence?**
   - Equal weight?
   - Prioritize higher quality?
   - Flag for user review?

---

## Next Steps

1. **Prototype Stage 1**: Implement embedding similarity in isolation
2. **Collect Test Data**: 50 manual claim-evidence pairs with labels
3. **Benchmark Models**: Compare embedding models and NLI approaches
4. **Tune Thresholds**: Find optimal similarity cutoffs
5. **Implement Stage 2**: Add LLM classification
6. **User Testing**: Beta test with real research workflows
7. **Iterate**: Refine based on accuracy metrics

---

## External Resources to Consult

- **Papers**:
  - "Fact Extraction and VERification" (FEVER) dataset methodology
  - "Natural Language Inference" (NLI) model benchmarks
  - SciFact dataset for scientific claim verification

- **Tools**:
  - Sentence Transformers documentation
  - FAISS for vector similarity search
  - LangChain for LLM orchestration

- **Communities**:
  - r/MachineLearning - NLI model recommendations
  - Hugging Face forums - Model selection guidance
  - Research ML Slack - Scientific NLP best practices

---

## Risk Assessment

**High Risk**: Using only embeddings → Many false positives
**Medium Risk**: Over-reliance on LLM → Hallucinations, cost
**Low Risk**: Hybrid approach with user review → Safer, scalable

**Recommendation**: Start with hybrid (embeddings + LLM), iterate based on accuracy.
