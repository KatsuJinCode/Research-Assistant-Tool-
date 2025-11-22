# Knowledge Graph Embedding (KGE) Trainer

## Overview

The `KGETrainer` trains knowledge graph embeddings using [PyKEEN](https://pykeen.readthedocs.io/), transforming research claim graphs into dense vector representations. These embeddings enable semantic similarity computation, link prediction, and advanced Graph RAG retrieval.

## What are Knowledge Graph Embeddings?

Knowledge graph embeddings represent entities (claims, documents) and relations (SUPPORTS, CONTRADICTS) as vectors in a continuous vector space. Similar entities have similar vectors, enabling:

- **Semantic Similarity**: Find related claims based on vector cosine similarity
- **Link Prediction**: Predict missing relationships (e.g., "What does this claim support?")
- **Graph RAG Enhancement**: Use embeddings for context-aware retrieval

## Supported Models

### TransE (Translational Embeddings)
- **How it works**: Treats relations as translations: `h + r ≈ t`
- **Best for**: Hierarchical relations (CONTAINS, PARENT_OF), simple graphs
- **Speed**: Fast training, efficient inference
- **Embedding dimension**: As specified (e.g., 256)

### RotatE (Rotational Embeddings)
- **How it works**: Treats relations as rotations in complex space
- **Best for**: Complex relation patterns, symmetric and antisymmetric relations
- **Speed**: Slower than TransE, better quality
- **Embedding dimension**: 2x specified (complex numbers)

### DistMult (Bilinear Model)
- **How it works**: Bilinear product for symmetric relations
- **Best for**: Graphs with primarily symmetric relations
- **Speed**: Fast, but limited expressiveness

## Installation

```bash
pip install pykeen torch numpy
```

## Quick Start

```python
from research_agent.graph_database import GraphDatabase
from backend.rag import TripleExtractor, KGETrainer

# 1. Extract triples from graph
db = GraphDatabase()
# ... populate graph ...
extractor = TripleExtractor(db)
triples = extractor.extract_from_neo4j()

# 2. Train embeddings
trainer = KGETrainer(embedding_dim=256, model_type='TransE')
embeddings = trainer.train_transe(triples, epochs=100)

# 3. Save for later use
trainer.save_embeddings(embeddings, 'backend/rag/embeddings/')
```

## Usage Examples

### Example 1: Basic Training

```python
from backend.rag import KGETrainer

# Initialize trainer
trainer = KGETrainer(
    embedding_dim=256,      # Higher = more expressive
    model_type='TransE',    # TransE, RotatE, or DistMult
    random_seed=42          # For reproducibility
)

# Train on triples
embeddings = trainer.train_transe(
    triples,
    epochs=100,             # More epochs = better quality
    batch_size=256,         # Larger = faster but more memory
    learning_rate=0.001,    # Adam optimizer learning rate
    validation_split=True   # Split data for validation
)

print(f"Entity embeddings: {embeddings['entity_embeddings'].shape}")
print(f"Relation embeddings: {embeddings['relation_embeddings'].shape}")
```

### Example 2: Train from TSV File

```python
# Export triples to TSV
extractor.export_to_pykeen_format('triples.tsv')

# Train from TSV
trainer = KGETrainer(embedding_dim=256)
embeddings = trainer.train_from_tsv('triples.tsv', epochs=100)
```

### Example 3: Save and Load Embeddings

```python
# Save embeddings
trainer.save_embeddings(embeddings, 'backend/rag/embeddings/')

# Load in new session
new_trainer = KGETrainer()
loaded_embeddings = new_trainer.load_embeddings('backend/rag/embeddings/')
```

### Example 4: Compute Similarity

```python
# Train first
trainer.train_transe(triples, epochs=100)

# Compute cosine similarity between entities
similarity = trainer.compute_similarity('claim_123', 'claim_456')
print(f"Similarity: {similarity:.3f}")  # Range: [-1, 1]

# Higher similarity = semantically closer
```

### Example 5: Link Prediction

```python
# Predict tail entities for (head, relation, ?)
predictions = trainer.predict_tail('claim_123', 'SUPPORTS', top_k=5)

for entity_id, score in predictions:
    print(f"{entity_id}: {score:.3f}")
```

### Example 6: Quick Training

```python
from backend.rag import train_embeddings_from_graph

# Train directly from GraphDatabase
embeddings = train_embeddings_from_graph(
    db,
    embedding_dim=256,
    model_type='TransE',
    epochs=100,
    output_dir='backend/rag/embeddings/'  # Optional
)
```

## Hyperparameter Recommendations

### Graph Size: Small (< 1,000 triples)
```python
trainer = KGETrainer(embedding_dim=128, model_type='TransE')
embeddings = trainer.train_transe(triples, epochs=50, batch_size=128)
```
- **Training time**: ~10-30 seconds
- **Quality**: Good for most use cases

### Graph Size: Medium (1,000 - 10,000 triples)
```python
trainer = KGETrainer(embedding_dim=256, model_type='TransE')
embeddings = trainer.train_transe(triples, epochs=100, batch_size=256)
```
- **Training time**: ~1-5 minutes
- **Quality**: High quality embeddings

### Graph Size: Large (> 10,000 triples)
```python
trainer = KGETrainer(embedding_dim=512, model_type='RotatE')
embeddings = trainer.train_transe(triples, epochs=200, batch_size=512)
```
- **Training time**: ~10-30 minutes
- **Quality**: Very high quality, suitable for production

## Performance Optimization

### GPU Acceleration
The trainer automatically uses GPU if available (CUDA):
```python
trainer = KGETrainer(embedding_dim=256)
print(f"Using device: {trainer.device}")  # 'cuda' or 'cpu'
```

### Training Speed Tips
1. **Increase batch size**: Faster training, more memory
2. **Reduce epochs**: Trade quality for speed
3. **Disable validation**: Skip validation split for fastest training
4. **Use TransE**: Fastest model (vs RotatE)

```python
# Fast training (sacrifice some quality)
embeddings = trainer.train_transe(
    triples,
    epochs=50,              # Reduced from 100
    batch_size=512,         # Increased from 256
    validation_split=False  # Skip validation
)
```

## Output Structure

After `trainer.save_embeddings()`, you get:

```
backend/rag/embeddings/
├── entity_embeddings.npy        # (num_entities, embedding_dim)
├── relation_embeddings.npy      # (num_relations, embedding_dim)
├── entity_to_id.json            # {"claim_123": 0, "doc_789": 1, ...}
├── relation_to_id.json          # {"SUPPORTS": 0, "CONTAINS": 1, ...}
├── model_metadata.json          # Hyperparameters, statistics
└── training_history.json        # Loss, metrics over epochs
```

## Interpreting Embeddings

### Vector Similarity = Semantic Similarity
```python
# High similarity (> 0.7): Entities are semantically related
similarity = trainer.compute_similarity('claim_1', 'claim_2')
if similarity > 0.7:
    print("Claims are highly related")

# Low similarity (< 0.3): Entities are unrelated
```

### Embedding Dimensions
- **Each entity** → Vector of size `embedding_dim`
- **Each relation** → Vector of size `embedding_dim` (or 2x for RotatE)
- **Example**: With `embedding_dim=256`, claim_123 → [0.12, -0.45, 0.78, ...]

### TransE Intuition
For triple `(claim_1, SUPPORTS, claim_2)`:
```
embedding(claim_1) + embedding(SUPPORTS) ≈ embedding(claim_2)
```

The model learns to satisfy this constraint for all triples.

## Integration with Graph RAG

### Use Case 1: Semantic Search
```python
# Find similar claims
query_embedding = trainer.get_entity_embedding('claim_query')
all_embeddings = embeddings['entity_embeddings']

# Compute similarities (cosine)
similarities = cosine_similarity(query_embedding, all_embeddings)

# Get top-k similar claims
top_k_indices = np.argsort(similarities)[-10:]
```

### Use Case 2: Context Expansion
```python
# For a given claim, find supporting evidence
predictions = trainer.predict_tail('claim_123', 'SUPPORTS', top_k=5)

# Use predictions to expand retrieval context
context_claims = [entity_id for entity_id, score in predictions if score > 0.5]
```

## Validation Metrics

The trainer reports:
- **Mean Rank (MR)**: Average rank of true tail entity (lower is better)
- **Hits@10**: Percentage of correct tails in top-10 predictions (higher is better)
- **Mean Reciprocal Rank (MRR)**: Average 1/rank (higher is better)

Example output:
```
Final metrics: {'MR': 5.2, 'Hits@10': 0.85, 'MRR': 0.62}
```

## Common Issues

### Issue: "RuntimeError: CUDA out of memory"
**Solution**: Reduce batch size or embedding dimension
```python
embeddings = trainer.train_transe(triples, batch_size=128)  # Reduced
```

### Issue: "No triples extracted"
**Solution**: Check that graph has edges with `type` attribute
```python
extractor = TripleExtractor(db)
stats = extractor.get_statistics()
print(stats)  # Check total_triples
```

### Issue: "Training loss not decreasing"
**Solution**: Increase epochs or adjust learning rate
```python
embeddings = trainer.train_transe(
    triples,
    epochs=200,          # More training
    learning_rate=0.0001 # Lower learning rate
)
```

## API Reference

### `KGETrainer.__init__()`
```python
def __init__(self, embedding_dim=256, model_type='TransE', random_seed=42)
```
**Parameters:**
- `embedding_dim`: Embedding vector dimension (128, 256, 512)
- `model_type`: 'TransE', 'RotatE', or 'DistMult'
- `random_seed`: Random seed for reproducibility

### `train_transe()`
```python
def train_transe(self, triples, epochs=100, batch_size=256,
                 learning_rate=0.001, validation_split=True)
```
**Parameters:**
- `triples`: List of (head, relation, tail) tuples
- `epochs`: Training epochs (50-200 recommended)
- `batch_size`: Batch size (128-512 recommended)
- `learning_rate`: Adam optimizer learning rate
- `validation_split`: Whether to split train/val/test

**Returns:**
- Dict with 'entity_embeddings' and 'relation_embeddings'

### `save_embeddings()`
```python
def save_embeddings(self, embeddings, output_dir)
```
Saves embeddings to disk in NumPy format.

### `load_embeddings()`
```python
def load_embeddings(self, input_dir)
```
Loads embeddings from disk.

### `get_entity_embedding()`
```python
def get_entity_embedding(self, entity_id)
```
Returns embedding vector for specific entity.

### `compute_similarity()`
```python
def compute_similarity(self, entity1, entity2)
```
Returns cosine similarity [-1, 1] between two entities.

### `predict_tail()`
```python
def predict_tail(self, head, relation, top_k=5)
```
Predicts most likely tail entities for (head, relation, ?).

## Testing

Run tests:
```bash
pytest backend/rag/test_kge_trainer.py -v
```

Run examples:
```bash
python backend/rag/example_kge_training.py
```

## Further Reading

- **PyKEEN Documentation**: https://pykeen.readthedocs.io/
- **TransE Paper**: "Translating Embeddings for Modeling Multi-relational Data" (Bordes et al., 2013)
- **RotatE Paper**: "RotatE: Knowledge Graph Embedding by Relational Rotation in Complex Space" (Sun et al., 2019)
- **Knowledge Graph Embeddings**: https://arxiv.org/abs/1503.00759

## Next Steps

After training embeddings:
1. **Integrate with retrieval**: Use embeddings for semantic search
2. **Link prediction**: Predict missing relationships in graph
3. **Clustering**: Group similar claims using embeddings
4. **Visualization**: Project embeddings to 2D/3D for visualization (t-SNE, UMAP)

## License

Part of the Research Assistant Tool project.
