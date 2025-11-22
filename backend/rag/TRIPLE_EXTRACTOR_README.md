# Knowledge Graph Triple Extractor

Foundation for implementing advanced Graph RAG with knowledge graph embeddings (TransE, RotatE, etc.).

## Overview

The `TripleExtractor` converts the NetworkX-based research claim graph into (head, relation, tail) triples suitable for training PyKEEN embeddings. This enables:

- **Semantic similarity in embedding space**: Find similar claims using learned vector representations
- **Link prediction**: Predict missing relationships (e.g., "Does Claim A support Claim B?")
- **Claim clustering**: Group claims based on learned embeddings
- **Graph-enhanced RAG**: Use embeddings for better context retrieval

## Quick Start

```python
from research_agent.graph_database import GraphDatabase
from backend.rag import TripleExtractor

# Initialize
db = GraphDatabase()
extractor = TripleExtractor(db)

# Extract all triples
triples = extractor.extract_from_neo4j()
# Returns: [('claim_123', 'SUPPORTS', 'claim_456'), ...]

# Export for PyKEEN training
extractor.export_to_pykeen_format('triples.tsv')
```

## Features

### 1. Basic Extraction

Extract all triples from the graph:

```python
triples = extractor.extract_from_neo4j()
# Returns: List[Tuple[str, str, str]]
# Format: (head_entity, relation, tail_entity)
```

### 2. Filtered Extraction

Extract specific relationship types:

```python
# Semantic relationships only (reasoning)
semantic = extractor.get_semantic_triples()
# Returns: SUPPORTS, CONTRADICTS, SIMILAR_TO relationships

# Hierarchical relationships only (structure)
hierarchical = extractor.get_hierarchical_triples()
# Returns: PARENT_OF, CONTAINS, MERGED_INTO relationships

# Custom filter
custom = extractor.extract_by_relation_type(['SUPPORTS', 'CONTRADICTS'])
```

### 3. Statistics

Get insights about your graph:

```python
stats = extractor.get_statistics()

# Returns:
{
    'total_triples': 1523,
    'unique_entities': 342,
    'unique_relations': 7,
    'relation_counts': {
        'SUPPORTS': 345,
        'CONTRADICTS': 123,
        'SIMILAR_TO': 234,
        ...
    },
    'node_label_counts': {
        'Claim': 200,
        'Document': 25,
        'SuperClaim': 45,
        ...
    },
    'avg_triples_per_relation': 217.57,
    'avg_degree': 8.91
}
```

### 4. PyKEEN Export

Export triples in PyKEEN-compatible TSV format:

```python
# Export all triples
count = extractor.export_to_pykeen_format('triples.tsv')

# Export filtered triples
count = extractor.export_to_pykeen_format(
    'semantic_triples.tsv',
    relation_filter=['SUPPORTS', 'CONTRADICTS']
)
```

Output format:
```
claim_123    SUPPORTS      claim_456
claim_456    CONTRADICTS   claim_789
doc_001      CONTAINS      claim_123
```

### 5. Entity Type Mapping

Get entity types for typed embeddings:

```python
entity_types = extractor.get_entity_types()
# Returns: {'claim_123': 'Claim', 'doc_001': 'Document', ...}
```

## Graph Schema

### Node Types

| Type | Description |
|------|-------------|
| `Document` | Research papers |
| `Claim` | Individual claims from papers |
| `SuperClaim` | Normalized merged claims |
| `Qualifier` | Modal/frequency/quantity qualifiers |
| `Evidence` | Supporting/contradicting evidence |
| `Source` | External sources |

### Relationship Types

| Relation | Type | Description |
|----------|------|-------------|
| `SUPPORTS` | Semantic | Claim A supports Claim B |
| `CONTRADICTS` | Semantic | Claim A contradicts Claim B |
| `SIMILAR_TO` | Semantic | Claims are semantically similar |
| `PARENT_OF` | Hierarchical | Parent-child claim relationship |
| `CONTAINS` | Hierarchical | Document contains claim |
| `MERGED_INTO` | Hierarchical | Claim merged into SuperClaim |
| `HAS_QUALIFIER` | Metadata | Claim has qualifier |
| `SOURCED_FROM` | Metadata | Source attribution |

**Note**: `CREATED` (agent provenance) is excluded from extraction as it doesn't add semantic value.

## Usage with PyKEEN

### Step 1: Export Triples

```python
from research_agent.graph_database import GraphDatabase
from backend.rag import TripleExtractor

db = GraphDatabase()
# ... populate graph ...

extractor = TripleExtractor(db)
extractor.export_to_pykeen_format('research_triples.tsv')
```

### Step 2: Train Embeddings

```python
from pykeen.triples import TriplesFactory
from pykeen.pipeline import pipeline

# Load triples
triples = TriplesFactory.from_path('research_triples.tsv')

# Train TransE embeddings
result = pipeline(
    training=triples,
    model='TransE',
    epochs=100,
    embedding_dim=128,
)

# Save model
result.save_to_directory('embeddings/')
```

### Step 3: Use for Graph RAG

```python
# Get embeddings for a claim
model = result.model
claim_embedding = model.entity_embeddings(entity_id_to_idx['claim_123'])

# Find similar claims (cosine similarity in embedding space)
similarities = cosine_similarity(claim_embedding, all_embeddings)

# Predict missing links
score = model.predict_hrt(
    head='claim_123',
    relation='SUPPORTS',
    tail='claim_456'
)
```

## Advanced Features

### Caching

Triples are cached after first extraction. Invalidate when graph changes:

```python
# Extract triples (cached)
triples1 = extractor.extract_from_neo4j()

# Modify graph
db.create_relationship(claim_a, claim_b, 'SUPPORTS')

# Invalidate cache
extractor.invalidate_cache()

# Re-extract with changes
triples2 = extractor.extract_from_neo4j()
```

### Filtering Invalid Triples

The extractor automatically filters:
- Triples where head or tail node doesn't exist
- Relationships with `None` or empty relation type
- Metadata relationships (e.g., `CREATED`)

### Custom Relation Exclusion

Modify `EXCLUDED_RELATIONS` to customize:

```python
TripleExtractor.EXCLUDED_RELATIONS.add('MY_METADATA_RELATION')
```

## Performance Considerations

### Graph Size

| Nodes | Edges | Extraction Time |
|-------|-------|-----------------|
| 100 | 500 | <0.1s |
| 1,000 | 5,000 | ~0.5s |
| 10,000 | 50,000 | ~5s |

**Note**: First extraction is slower, subsequent calls use cache.

### Memory Usage

- **Triples storage**: ~100 bytes per triple
- **10,000 triples**: ~1 MB
- **100,000 triples**: ~10 MB

For very large graphs (>1M triples), consider batch processing.

## Examples

See `backend/rag/example_triple_extraction.py` for complete examples:

```bash
python backend/rag/example_triple_extraction.py
```

## Testing

Run the test suite:

```bash
python backend/rag/test_triple_extractor.py
```

Tests cover:
- Basic triple extraction
- Relation type filtering
- Statistics generation
- Semantic vs hierarchical extraction
- PyKEEN TSV export
- Entity type mapping
- Cache invalidation

## Integration with Existing RAG Module

The `TripleExtractor` integrates seamlessly with existing RAG components:

```python
from backend.rag import (
    TripleExtractor,
    SemanticSimilarity,
    GraphContextBuilder,
    ClaimDeduplicator
)

# Combine triple extraction with semantic similarity
extractor = TripleExtractor(db)
similarity = SemanticSimilarity()

# Export semantic triples for embedding training
semantic_triples = extractor.get_semantic_triples()
extractor.export_to_pykeen_format('semantic.tsv',
                                  relation_filter=['SUPPORTS', 'CONTRADICTS'])

# Use embeddings to enhance similarity matching
# (after training with PyKEEN)
```

## Design Decisions

### Why String-based IDs?

PyKEEN expects string entity IDs. The extractor converts all node IDs to strings, ensuring compatibility with various graph backends (NetworkX, Neo4j, etc.).

### Why Cache Triples?

Triple extraction iterates over all edges. For large graphs, this can be expensive. Caching ensures fast repeated access during embedding training iterations.

### Why Exclude Metadata Relations?

Relationships like `CREATED` (agent provenance) don't encode semantic knowledge useful for embeddings. They're excluded to reduce noise and improve embedding quality.

### Why Separate Semantic/Hierarchical?

Different relationship types serve different purposes:
- **Semantic**: Capture reasoning (use for link prediction)
- **Hierarchical**: Capture structure (use for entity classification)

Separating them allows specialized embedding strategies.

## Future Enhancements

Potential improvements:

1. **Weighted triples**: Include relationship properties (e.g., confidence scores)
2. **Temporal triples**: Add timestamps for temporal KG embeddings
3. **Batch export**: Memory-efficient export for very large graphs
4. **Neo4j optimization**: Direct Cypher query for faster extraction
5. **Triple validation**: Detect inconsistencies (e.g., cycles in PARENT_OF)

## References

- [PyKEEN Documentation](https://pykeen.readthedocs.io/)
- [TransE Paper](https://papers.nips.cc/paper/2013/hash/1cecc7a77928ca8133fa24680a88d2f9-Abstract.html)
- [RotatE Paper](https://arxiv.org/abs/1902.10197)
- [Knowledge Graph Embeddings Tutorial](https://towardsdatascience.com/knowledge-graph-embeddings-101-2cc1ca5db44f)

## License

Part of the Research Assistant Tool project.
