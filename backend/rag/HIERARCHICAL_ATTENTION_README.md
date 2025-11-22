# Hierarchical Attention Mechanism for Graph RAG

**Advanced multi-level attention for tree-structured knowledge graphs**

---

## Overview

The Hierarchical Attention mechanism enables focused retrieval from tree-structured claim hierarchies by computing attention scores at multiple levels. This creates a "zoom in" effect where attention flows down the tree, focusing on the most relevant branches at each level.

### What Problem Does It Solve?

In traditional retrieval systems, all nodes are treated equally regardless of their position in the hierarchy. This can lead to:

- **Context Loss**: Evidence disconnected from its supporting claims
- **Noise**: Irrelevant sub-claims from unrelated branches
- **Poor Ranking**: High-level and low-level claims mixed together

Hierarchical Attention solves this by:

1. **Preserving Context**: Keeping claims with their supporting evidence
2. **Focused Retrieval**: Only expanding relevant branches
3. **Level-Aware Ranking**: Considering position in hierarchy

---

## Architecture

### Hierarchy Structure

```
Document (Level 0)
└── Super-Claim (Level 1) - High-level finding
    ├── Sub-Claim 1 (Level 2) - Supporting detail
    │   ├── Evidence 1 (Level 3)
    │   └── Evidence 2 (Level 3)
    └── Sub-Claim 2 (Level 2) - Supporting detail
        └── Evidence 3 (Level 3)
```

### Attention Flow

Attention cascades down the tree through multiplication:

```python
# Level 0: Document
doc_attention = similarity(query, document)

# Level 1: Super-Claims (children of document)
superclaim_attention = softmax(similarity(query, superclaim)) * doc_attention

# Level 2: Claims (children of super-claim)
claim_attention = softmax(similarity(query, claim)) * superclaim_attention

# Level 3: Evidence (children of claim)
evidence_attention = softmax(similarity(query, evidence)) * claim_attention
```

**Key Properties:**

- **Cascade Effect**: Child attention ≤ Parent attention (scores can only decrease down the tree)
- **Softmax Over Siblings**: At each level, attention is normalized across siblings
- **Temperature Control**: Sharpness of attention distribution is tunable

---

## Core Concepts

### 1. Softmax Attention

At each level, compute attention across siblings using softmax:

```python
attention_i = exp(similarity_i / temperature) / Σ exp(similarity_j / temperature)
```

**Temperature Effects:**

- `temperature = 1.0`: Normal softmax (balanced)
- `temperature < 1.0`: Sharper attention (more focused)
- `temperature > 1.0`: Softer attention (more distributed)

Example:

```python
# Sharp attention (temperature = 0.5)
# Top sibling gets 80% attention, others get 20%

# Soft attention (temperature = 2.0)
# Top sibling gets 50% attention, others get 50%
```

### 2. Branch Activation

Only expand branches that exceed the activation threshold:

```python
if attention_score >= activation_threshold:
    expand_children()
else:
    prune_branch()
```

**Threshold Guidelines:**

- `threshold = 0.0`: Expand all branches (comprehensive)
- `threshold = 0.1`: Moderate pruning (balanced)
- `threshold = 0.3`: Aggressive pruning (focused)

### 3. Cascade Multiplication

Child attention is the product of:

1. **Parent attention**: Attention inherited from parent
2. **Local attention**: Softmax score at current level

```python
child_attention = parent_attention * softmax_score
```

This ensures attention decreases down irrelevant branches.

---

## Usage

### Basic Usage

```python
from research_agent.graph_database import GraphDatabase
from backend.rag.hierarchical_attention import HierarchicalAttention

# Initialize
db = GraphDatabase()
# ... populate graph ...

attention = HierarchicalAttention(db)

# Retrieve with hierarchical attention
results = attention.retrieve_with_attention(
    query_text="How does AI affect employment?",
    top_k_docs=3,
    top_k_claims=5,
    top_k_evidence=10
)

# Display results
for node_id, score, level in results[:10]:
    node = db.get_node(node_id)
    print(f"[Level {level}] {node['text'][:50]}... (score: {score:.3f})")
```

### Advanced Configuration

```python
# Sharp attention for focused retrieval
attention = HierarchicalAttention(
    db,
    temperature=0.5,              # Sharper attention
    activation_threshold=0.3,      # Aggressive pruning
    cache_embeddings=True          # Cache for performance
)

# Soft attention for comprehensive retrieval
attention = HierarchicalAttention(
    db,
    temperature=2.0,               # Softer attention
    activation_threshold=0.05,     # Minimal pruning
    cache_embeddings=True
)
```

### Explaining Attention

```python
# Get explanation for a specific node
explanation = attention.explain_attention(
    query_text="AI in healthcare",
    node_id="claim_123"
)

print(f"Attention Path: {' -> '.join(explanation.path)}")
print(f"Scores per level: {explanation.scores_per_level}")
print(f"Final score: {explanation.final_score:.3f}")
print(f"Reason: {explanation.reason}")
```

### Attention Statistics

```python
# Get statistics about attention distribution
stats = attention.get_attention_statistics(
    query_text="machine learning",
    top_k_docs=3
)

print(f"Total nodes: {stats['total_nodes']}")
print(f"Activated nodes: {stats['activated_nodes']}")
print(f"Activation rate: {stats['activation_rate']:.1%}")

# Per-level statistics
for level, level_stats in stats['attention_by_level'].items():
    print(f"Level {level}: avg={level_stats['avg_score']:.3f}")
```

### Visualization

```python
# Generate data for d3.js visualization
vis_data = attention.visualize_attention(
    query_text="AI impact",
    root_id=doc_id,
    max_depth=3
)

# vis_data contains hierarchical tree with attention scores
# Suitable for tree visualization libraries
```

---

## API Reference

### HierarchicalAttention

```python
class HierarchicalAttention:
    def __init__(
        self,
        db: GraphDatabase,
        embedding_model: Optional[SemanticSimilarity] = None,
        temperature: float = 1.0,
        activation_threshold: float = 0.1,
        cache_embeddings: bool = True
    )
```

**Parameters:**

- `db`: GraphDatabase instance
- `embedding_model`: Optional SemanticSimilarity instance (creates default if None)
- `temperature`: Softmax temperature (< 1 = sharper, > 1 = softer)
- `activation_threshold`: Minimum score to expand branch
- `cache_embeddings`: Whether to cache embeddings for performance

### Main Methods

#### retrieve_with_attention

```python
def retrieve_with_attention(
    self,
    query_text: str,
    top_k_docs: int = 3,
    top_k_claims: int = 5,
    top_k_evidence: int = 10,
    expand_all_levels: bool = False
) -> List[Tuple[str, float, int]]
```

**Returns:** List of `(node_id, attention_score, level)` sorted by score

#### explain_attention

```python
def explain_attention(
    self,
    query_text: str,
    node_id: str,
    max_depth: int = 5
) -> Optional[AttentionPath]
```

**Returns:** `AttentionPath` with path, scores, and explanation

#### get_attention_statistics

```python
def get_attention_statistics(
    self,
    query_text: str,
    top_k_docs: int = 3
) -> Dict
```

**Returns:** Dictionary with attention statistics

#### visualize_attention

```python
def visualize_attention(
    self,
    query_text: str,
    root_id: str,
    max_depth: int = 3
) -> Dict
```

**Returns:** Tree structure with attention scores for visualization

---

## Performance Characteristics

### Time Complexity

- **Tree Building**: O(N) where N = number of nodes
- **Attention Computation**: O(N × D) where D = embedding dimension
- **Retrieval**: O(N log N) for sorting
- **With Caching**: ~5-10x speedup on repeated queries

### Space Complexity

- **Embedding Cache**: O(N × D) for cached embeddings
- **Tree Cache**: O(N) for tree structures

### Optimization Tips

1. **Enable Caching**: Set `cache_embeddings=True` for repeated queries
2. **Adjust Threshold**: Higher threshold = faster (fewer branches expanded)
3. **Limit Depth**: Set `max_depth` to avoid deep recursion
4. **Batch Queries**: Process multiple queries to amortize model loading

### Performance Results

**From tests (15-node tree):**

- First run (cold cache): ~90ms
- Second run (warm cache): ~16ms
- Speedup: 5.75x

**From tests (81-node tree):**

- Retrieval time: ~440ms
- All 81 nodes processed
- Performance: <5 seconds acceptable

---

## Examples

### Example 1: Manufacturing Jobs Query

```python
attention = HierarchicalAttention(db, temperature=0.8)

results = attention.retrieve_with_attention(
    query_text="How does automation affect factory workers?",
    top_k_docs=1,
    top_k_claims=3
)

# Results:
# 1. [Level 0] Document about AI Impact (score: 0.376)
# 2. [Level 1] SuperClaim: AI automation displaces workers (score: 0.153)
# 3. [Level 2] Claim: Factory workers replaced by robots (score: 0.057)
```

### Example 2: Healthcare Diagnosis Query

```python
attention = HierarchicalAttention(db, temperature=0.5)  # Sharp focus

results = attention.retrieve_with_attention(
    query_text="AI diagnostic accuracy in medical imaging",
    top_k_docs=1,
    top_k_claims=5
)

# Results focus on healthcare branch:
# 1. [Level 0] Document about AI Impact (score: 0.338)
# 2. [Level 1] SuperClaim: AI revolutionizes healthcare (score: 0.143)
# 3. [Level 2] Claim: AI improves diagnostic accuracy (score: 0.071)
# 4. [Level 3] Evidence: 25% accuracy improvement in radiology (score: 0.032)
```

### Example 3: Temperature Comparison

```python
# Sharp attention (focused)
sharp = HierarchicalAttention(db, temperature=0.5)
sharp_results = sharp.retrieve_with_attention("AI jobs", top_k_docs=1)
# Top result: 0.850, Second: 0.120 (large gap)

# Soft attention (distributed)
soft = HierarchicalAttention(db, temperature=2.0)
soft_results = soft.retrieve_with_attention("AI jobs", top_k_docs=1)
# Top result: 0.650, Second: 0.420 (smaller gap)
```

---

## Integration with UnifiedRetrieval

Hierarchical Attention can be integrated into the UnifiedRetrieval system:

```python
from backend.rag.unified_retrieval import UnifiedRetrieval
from backend.rag.hierarchical_attention import HierarchicalAttention

# Option 1: Use directly
attention = HierarchicalAttention(db)
results = attention.retrieve_with_attention("query")

# Option 2: Add as retrieval mode to UnifiedRetrieval
# (future enhancement)
class UnifiedRetrieval:
    def _retrieve_hierarchical(self, query_text, limit, threshold):
        attention = HierarchicalAttention(self.db)
        return attention.retrieve_with_attention(query_text, top_k_docs=3)
```

---

## Graph Database Compatibility

### Current: NetworkX

```python
# Works with NetworkX-based GraphDatabase
db = GraphDatabase()
# Uses relationships: CONTAINS, PARENT_OF, HAS_EVIDENCE
```

### Future: Neo4j

The implementation is designed for easy Neo4j migration:

```python
# Neo4j traversal (future)
def get_children_neo4j(node_id):
    query = """
    MATCH (n {id: $node_id})-[:CONTAINS|PARENT_OF|HAS_EVIDENCE]->(child)
    RETURN child.id as id, child.text as text
    """
    return session.run(query, node_id=node_id)
```

---

## Testing

Run comprehensive tests:

```bash
# Run all tests
pytest backend/rag/test_hierarchical_attention.py -v

# Run specific test
pytest backend/rag/test_hierarchical_attention.py::test_cascade_effect -v

# Run with coverage
pytest backend/rag/test_hierarchical_attention.py --cov=backend.rag.hierarchical_attention
```

Test coverage includes:

- Tree building from graph
- Embedding caching
- Attention computation
- Cascade effect verification
- Temperature effects
- Branch activation/pruning
- End-to-end retrieval
- Explainability
- Performance on large trees
- Multi-document retrieval

---

## Example Script

Run the comprehensive example:

```bash
python backend/rag/example_hierarchical_attention.py
```

This demonstrates:

1. Basic retrieval
2. Temperature effects
3. Attention explanation
4. Statistics computation
5. Branch activation
6. Performance characteristics

---

## Best Practices

### 1. Choose Appropriate Temperature

- **Focused queries** (specific topics): Use `temperature = 0.5-0.8`
- **Exploratory queries** (broad topics): Use `temperature = 1.0-2.0`
- **Default**: `temperature = 1.0`

### 2. Set Activation Threshold

- **High precision** (few but relevant): `threshold = 0.3-0.5`
- **Balanced**: `threshold = 0.1-0.3`
- **High recall** (comprehensive): `threshold = 0.0-0.1`

### 3. Enable Caching

Always enable for production:

```python
attention = HierarchicalAttention(db, cache_embeddings=True)
```

### 4. Limit Tree Depth

For very deep hierarchies:

```python
tree = attention.get_tree_structure(root_id, max_depth=4)
```

### 5. Clear Cache Periodically

When graph changes:

```python
attention.clear_cache()
```

---

## Troubleshooting

### Issue: Slow Performance

**Solution:**

- Enable embedding caching
- Reduce `max_depth`
- Increase `activation_threshold`
- Batch multiple queries

### Issue: Too Few Results

**Solution:**

- Decrease `activation_threshold`
- Increase `temperature` (softer attention)
- Increase `top_k_*` parameters

### Issue: Too Many Irrelevant Results

**Solution:**

- Increase `activation_threshold`
- Decrease `temperature` (sharper attention)
- Review query specificity

### Issue: Attention Not Cascading

**Check:**

- Verify graph relationships (CONTAINS, PARENT_OF, HAS_EVIDENCE)
- Ensure embeddings are being generated
- Check that tree is being built correctly

---

## Future Enhancements

### Planned Features

1. **Multi-Query Attention**: Support multiple queries simultaneously
2. **Attention Visualization**: Interactive d3.js tree with attention highlighting
3. **Attention Persistence**: Save/load computed attention scores
4. **Dynamic Temperature**: Auto-tune based on query specificity
5. **Learned Attention**: Train attention weights from user feedback
6. **Cross-Document Attention**: Attend across multiple documents

### Integration Points

1. **UnifiedRetrieval**: Add as retrieval mode
2. **LLM Context**: Use attention scores to select context
3. **Explanation System**: Generate natural language explanations
4. **Active Learning**: Use attention for relevance feedback

---

## References

### Attention Mechanisms

- Vaswani et al. (2017) - "Attention Is All You Need"
- Bahdanau et al. (2015) - "Neural Machine Translation by Jointly Learning to Align and Translate"

### Hierarchical Models

- Yang et al. (2016) - "Hierarchical Attention Networks for Document Classification"
- Miculicich et al. (2018) - "Document-Level Neural Machine Translation with Hierarchical Attention Networks"

### Graph RAG

- Edge et al. (2024) - "From Local to Global: A Graph RAG Approach"
- Lewis et al. (2020) - "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"

---

## License

Part of Research Assistant Tool - MIT License

---

## Contact

For questions or issues, please refer to the main project documentation.
