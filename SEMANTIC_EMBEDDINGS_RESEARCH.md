# Semantic Embeddings Research Summary

## Overview

Semantic embeddings convert text into dense vector representations that capture meaning, enabling mathematical comparison of semantic similarity.

---

## Top Models for Our Use Case (2025)

### 1. **SBERT (Sentence-BERT)** ✅ RECOMMENDED FOR US
- **Status**: Open-source, no API costs
- **Dimensions**: 768
- **Speed**: 40,000+ sentence pairs/sec on GPU
- **Best for**: Semantic similarity, clustering, lightweight deployment
- **Why good for us**:
  - Fast inference (works on CPU)
  - No API costs
  - Proven for claim similarity tasks
  - Pre-trained models available on HuggingFace

### 2. **OpenAI text-embedding-3-large**
- **Status**: Commercial API ($0.13 per 1M tokens)
- **Dimensions**: 256/1024/3072 (configurable)
- **Best for**: Production systems with budget
- **Why NOT for us**: API costs, requires internet

### 3. **NVIDIA NV-Embed** (Latest 2025)
- **Status**: Open-source, built on Llama-3.1-8B
- **MTEB Score**: 69.32 (current SOTA)
- **Best for**: Multilingual, high-accuracy requirements
- **Why NOT for us**: 8B parameters = heavy, slow on CPU

### 4. **gte-Qwen3**
- **Status**: Open-source
- **Sizes**: 0.6B, 4B, 8B parameters
- **Best for**: Multilingual support
- **Why maybe for us**: 0.6B version could work if SBERT insufficient

### 5. **Google Gemma 3** (300M)
- **Status**: Open-source
- **Dimensions**: 300M parameters
- **Best for**: Mobile/edge deployment, 100+ languages
- **Why maybe for us**: Lightweight, good for limited hardware

---

## MTEB Leaderboard

**Massive Text Embedding Benchmark** - Standard for comparing embedding models

- **URL**: https://huggingface.co/spaces/mteb/leaderboard
- **Tasks**: 56 total (retrieval, classification, clustering, STS, etc.)
- **Key Task for Us**: Semantic Textual Similarity (STS)
  - Measures how similar two sentences are
  - Uses cosine similarity on embeddings
  - Compared with ground truth via Spearman correlation

---

## Semantic Embedding in Claude Code Ecosystem

### claude-context Project (Zilliz)
**GitHub**: https://github.com/zilliztech/claude-context

**What it does**:
- Code search MCP for Claude Code
- Makes entire codebase the context for coding agents
- Hybrid search: BM25 + dense vector embeddings

**Embedding approach**:
- Uses `nomic-embed-text:v1.5` (768-dim)
- Intelligent code chunking via AST (Abstract Syntax Trees)
- Supports OpenAI, VoyageAI embedding providers
- Can use local Milvus vector database

**Key insight**: They use vector databases (Milvus) for storage and retrieval, not just in-memory comparison

---

## Technical Comparison

| Model | Params | Dims | Speed | Cost | Multilingual | Best Use |
|-------|--------|------|-------|------|--------------|----------|
| SBERT | 110M | 768 | Fast | Free | No | Semantic similarity |
| OpenAI ada-002 | ? | 1536 | API | $$ | Yes | Production RAG |
| OpenAI 3-large | ? | 3072 | API | $$ | Yes | High-accuracy RAG |
| NV-Embed | 8B | ? | Slow | Free | Yes | SOTA accuracy |
| gte-Qwen3 | 0.6-8B | ? | Med | Free | Yes | Multilingual |
| Gemma 3 | 300M | ? | Fast | Free | Yes | Edge deployment |

---

## Recommendation for Our Project

**Use SBERT (sentence-transformers)** because:

1. ✅ **No API costs** - runs locally, unlimited usage
2. ✅ **Fast enough** - works on CPU, good for 20-100 claims
3. ✅ **Proven for similarity tasks** - designed specifically for STS
4. ✅ **Easy integration** - pip install sentence-transformers
5. ✅ **Pre-trained models** - 15,000+ models on HuggingFace
6. ✅ **768 dimensions** - good balance of accuracy and speed

**Specific model to use**:
- `all-MiniLM-L6-v2` - Fastest, 384 dims, good for our use case
- `all-mpnet-base-v2` - More accurate, 768 dims, best quality
- `multi-qa-mpnet-base-dot-v1` - Optimized for question-answer similarity

---

## Implementation Strategy

### Phase 1: Basic Semantic Similarity (NOW)
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-mpnet-base-v2')

# Encode claims to embeddings
embeddings = model.encode(claim_texts)

# Calculate cosine similarity
from sklearn.metrics.pairwise import cosine_similarity
similarity_matrix = cosine_similarity(embeddings)
```

### Phase 2: Advanced Relationships
- Subsumption detection (claim A contains claim B)
- Parent-child hierarchies (general → specific)
- Support relationships (claim A supports claim B)

### Phase 3: Evidence Integration
- Embed research papers from arXiv
- Find papers that support/contradict each claim
- Build evidence graph in Neo4j

### Phase 4: Vector Database (FUTURE)
If we scale to 1000s of claims:
- Add Milvus or Qdrant for vector storage
- Enable fast similarity search
- Support incremental updates

---

## Alternative: Hybrid Approach

Could combine multiple methods:
1. **Token-based** (current) - for exact subsumption
2. **Semantic embeddings** (SBERT) - for similarity and relationships
3. **LLM-based** (Claude API) - for complex reasoning about relationships

Each has strengths:
- Token-based: Fast, deterministic, finds exact duplicates
- SBERT: Captures meaning, finds similar concepts
- LLM: Understands context, nuance, logical relationships

---

## Next Steps

1. ✅ Install sentence-transformers (DONE)
2. ⏭️ Update ClaimSpaceOptimizer to use SBERT embeddings
3. ⏭️ Test on our 20 Szasz claims
4. ⏭️ Build parent-child hierarchy based on semantic similarity
5. ⏭️ Integrate with Neo4j for visualization
6. ⏭️ Add evidence linking (arXiv papers)

---

**Reference Links**:
- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
- Sentence-Transformers Docs: https://www.sbert.net/
- Claude Context (Zilliz): https://github.com/zilliztech/claude-context
- SBERT Models: https://huggingface.co/sentence-transformers
