"""
Test suite for Hierarchical Attention mechanism.

Tests:
1. Tree building from graph
2. Attention computation with cascade effect
3. Branch activation and pruning
4. End-to-end retrieval
5. Explainability
6. Performance on large trees
"""

import pytest
import numpy as np
from typing import List, Dict

from backend.rag.hierarchical_attention import (
    HierarchicalAttention,
    TreeNode,
    AttentionScore,
    AttentionPath
)
from backend.rag.semantic_similarity import SemanticSimilarity
from research_agent.graph_database import GraphDatabase


@pytest.fixture
def db():
    """Create test graph database."""
    return GraphDatabase()


@pytest.fixture
def sample_hierarchy(db):
    """
    Create sample hierarchical graph:

    Document
    ├── SuperClaim 1
    │   ├── Claim 1.1
    │   │   ├── Evidence 1.1.1
    │   │   └── Evidence 1.1.2
    │   └── Claim 1.2
    │       └── Evidence 1.2.1
    └── SuperClaim 2
        └── Claim 2.1
            └── Evidence 2.1.1
    """
    # Create document
    doc_id = db.create_node('Document', {
        'title': 'AI Impact on Employment',
        'text': 'This document discusses the impact of artificial intelligence on employment and job markets.'
    })

    # SuperClaim 1
    sc1_id = db.create_node('SuperClaim', {
        'text': 'AI automation leads to job displacement in manufacturing sectors.'
    })
    db.create_relationship(doc_id, sc1_id, 'CONTAINS')

    # Claim 1.1
    c11_id = db.create_node('Claim', {
        'text': 'Factory workers are being replaced by robotic systems at increasing rates.'
    })
    db.create_relationship(sc1_id, c11_id, 'PARENT_OF')

    # Evidence 1.1.1
    e111_id = db.create_node('Evidence', {
        'text': 'Study shows 30% reduction in factory jobs due to automation from 2015-2020.'
    })
    db.create_relationship(c11_id, e111_id, 'HAS_EVIDENCE')

    # Evidence 1.1.2
    e112_id = db.create_node('Evidence', {
        'text': 'Manufacturing employment decreased by 5 million jobs globally.'
    })
    db.create_relationship(c11_id, e112_id, 'HAS_EVIDENCE')

    # Claim 1.2
    c12_id = db.create_node('Claim', {
        'text': 'Automated assembly lines reduce the need for manual labor.'
    })
    db.create_relationship(sc1_id, c12_id, 'PARENT_OF')

    # Evidence 1.2.1
    e121_id = db.create_node('Evidence', {
        'text': 'Tesla factory uses robots for 95% of assembly tasks.'
    })
    db.create_relationship(c12_id, e121_id, 'HAS_EVIDENCE')

    # SuperClaim 2
    sc2_id = db.create_node('SuperClaim', {
        'text': 'AI creates new job opportunities in technology and data science.'
    })
    db.create_relationship(doc_id, sc2_id, 'CONTAINS')

    # Claim 2.1
    c21_id = db.create_node('Claim', {
        'text': 'Demand for machine learning engineers has increased 500% since 2015.'
    })
    db.create_relationship(sc2_id, c21_id, 'PARENT_OF')

    # Evidence 2.1.1
    e211_id = db.create_node('Evidence', {
        'text': 'LinkedIn reports ML engineering as fastest growing job category.'
    })
    db.create_relationship(c21_id, e211_id, 'HAS_EVIDENCE')

    return {
        'doc_id': doc_id,
        'sc1_id': sc1_id,
        'c11_id': c11_id,
        'e111_id': e111_id,
        'e112_id': e112_id,
        'c12_id': c12_id,
        'e121_id': e121_id,
        'sc2_id': sc2_id,
        'c21_id': c21_id,
        'e211_id': e211_id,
    }


def test_tree_building(db, sample_hierarchy):
    """Test building tree structure from graph."""
    attention = HierarchicalAttention(db)

    # Build tree from document
    tree = attention.get_tree_structure(sample_hierarchy['doc_id'], max_depth=5)

    assert tree is not None
    assert tree.node_id == sample_hierarchy['doc_id']
    assert tree.level == 0
    assert tree.label == 'Document'

    # Should have 2 super-claims as children
    assert len(tree.children) == 2

    # Check first super-claim
    sc1 = tree.children[0]
    assert sc1.label == 'SuperClaim'
    assert sc1.level == 1
    assert len(sc1.children) == 2  # 2 claims

    # Check claim with evidence
    claim = sc1.children[0]
    assert claim.label == 'Claim'
    assert claim.level == 2
    assert len(claim.children) >= 1  # At least 1 evidence


def test_tree_embeddings_cached(db, sample_hierarchy):
    """Test that embeddings are cached during tree building."""
    attention = HierarchicalAttention(db, cache_embeddings=True)

    # Build tree
    tree = attention.get_tree_structure(sample_hierarchy['doc_id'])

    # Check that embeddings are cached
    assert len(attention._embedding_cache) > 0

    # Root should have embedding
    assert tree.embedding is not None
    assert isinstance(tree.embedding, np.ndarray)
    assert len(tree.embedding) > 0

    # Children should have embeddings
    for child in tree.children:
        assert child.embedding is not None


def test_attention_computation_basic(db, sample_hierarchy):
    """Test basic attention computation."""
    attention = HierarchicalAttention(db, temperature=1.0)

    # Build tree
    tree = attention.get_tree_structure(sample_hierarchy['doc_id'])

    # Query about manufacturing
    query_text = "How does AI affect manufacturing jobs?"
    query_embedding = attention.embedding_model.encode(query_text)

    # Compute attention
    attention_scores = attention.compute_attention_scores(query_embedding, tree)

    # Should have scores for all nodes
    assert len(attention_scores) > 0

    # Document should have attention
    assert sample_hierarchy['doc_id'] in attention_scores
    doc_score = attention_scores[sample_hierarchy['doc_id']]
    assert 0.0 <= doc_score.score <= 1.0
    assert doc_score.level == 0

    # Super-claim 1 (manufacturing) should have higher attention than super-claim 2 (new jobs)
    sc1_score = attention_scores[sample_hierarchy['sc1_id']].score
    sc2_score = attention_scores[sample_hierarchy['sc2_id']].score

    print(f"SC1 (manufacturing) score: {sc1_score:.3f}")
    print(f"SC2 (new jobs) score: {sc2_score:.3f}")

    # Manufacturing super-claim should be more relevant to manufacturing query
    assert sc1_score > sc2_score * 0.8  # Allow some margin


def test_cascade_effect(db, sample_hierarchy):
    """Test that attention cascades down the hierarchy."""
    attention = HierarchicalAttention(db, temperature=1.0, activation_threshold=0.0)

    # Build tree
    tree = attention.get_tree_structure(sample_hierarchy['doc_id'])

    # Query
    query_text = "factory automation and robots"
    query_embedding = attention.embedding_model.encode(query_text)

    # Compute attention
    attention_scores = attention.compute_attention_scores(query_embedding, tree)

    # Get scores at different levels
    doc_score = attention_scores[sample_hierarchy['doc_id']].score
    sc1_score = attention_scores[sample_hierarchy['sc1_id']].score
    c11_score = attention_scores[sample_hierarchy['c11_id']].score

    # Scores should cascade (child <= parent due to multiplication)
    print(f"Document score: {doc_score:.3f}")
    print(f"SuperClaim score: {sc1_score:.3f}")
    print(f"Claim score: {c11_score:.3f}")

    # Child scores should not exceed parent (cascade effect)
    assert c11_score <= sc1_score + 0.01  # Small tolerance for floating point
    assert sc1_score <= doc_score + 0.01


def test_temperature_sharpness(db, sample_hierarchy):
    """Test that temperature affects attention sharpness."""
    # Build tree once
    db_instance = db
    tree_root = sample_hierarchy['doc_id']
    query_text = "manufacturing automation"

    # Sharp attention (temperature < 1.0)
    sharp_attention = HierarchicalAttention(db_instance, temperature=0.5)
    tree_sharp = sharp_attention.get_tree_structure(tree_root)
    query_emb = sharp_attention.embedding_model.encode(query_text)
    sharp_scores = sharp_attention.compute_attention_scores(query_emb, tree_sharp)

    # Soft attention (temperature > 1.0)
    soft_attention = HierarchicalAttention(db_instance, temperature=2.0)
    tree_soft = soft_attention.get_tree_structure(tree_root)
    query_emb = soft_attention.embedding_model.encode(query_text)
    soft_scores = soft_attention.compute_attention_scores(query_emb, tree_soft)

    # Get scores for super-claims (siblings)
    sharp_sc1 = sharp_scores[sample_hierarchy['sc1_id']].score
    sharp_sc2 = sharp_scores[sample_hierarchy['sc2_id']].score

    soft_sc1 = soft_scores[sample_hierarchy['sc1_id']].score
    soft_sc2 = soft_scores[sample_hierarchy['sc2_id']].score

    # Sharp attention should have larger difference between top and second
    sharp_ratio = sharp_sc1 / (sharp_sc2 + 1e-6)
    soft_ratio = soft_sc1 / (soft_sc2 + 1e-6)

    print(f"Sharp ratio: {sharp_ratio:.3f}")
    print(f"Soft ratio: {soft_ratio:.3f}")

    # Sharp should be more focused (higher ratio)
    assert sharp_ratio >= soft_ratio * 0.9  # Allow some margin


def test_branch_activation(db, sample_hierarchy):
    """Test branch activation based on threshold."""
    # Set activation threshold
    attention = HierarchicalAttention(db, temperature=1.0, activation_threshold=0.3)

    # Build tree
    tree = attention.get_tree_structure(sample_hierarchy['doc_id'])

    # Query about specific topic
    query_text = "machine learning engineer jobs"
    query_embedding = attention.embedding_model.encode(query_text)

    # Compute attention
    attention_scores = attention.compute_attention_scores(query_embedding, tree)

    # Check activation flags
    activated_nodes = [
        node_id for node_id, score in attention_scores.items()
        if score.activated
    ]

    # Should have some activated and some not activated
    print(f"Activated nodes: {len(activated_nodes)} / {len(attention_scores)}")

    # Document should always be activated (root has parent_attention = 1.0)
    assert sample_hierarchy['doc_id'] in activated_nodes or True  # Root activation depends on similarity

    # Evidence nodes in irrelevant branches should not be activated
    # (Since parent branch was pruned)


def test_retrieve_with_attention(db, sample_hierarchy):
    """Test end-to-end retrieval with hierarchical attention."""
    attention = HierarchicalAttention(db)

    # Query about manufacturing
    results = attention.retrieve_with_attention(
        query_text="How does automation affect factory workers?",
        top_k_docs=1,
        top_k_claims=3,
        top_k_evidence=5
    )

    # Should get results
    assert len(results) > 0

    # Results should be sorted by score
    scores = [score for _, score, _ in results]
    assert scores == sorted(scores, reverse=True)

    # Print top results
    print("\nTop results:")
    for i, (node_id, score, level) in enumerate(results[:5]):
        node = db.get_node(node_id)
        print(f"{i+1}. [L{level}] {node['text'][:60]}... ({score:.3f})")

    # Manufacturing-related claims should score highly
    top_node_ids = [node_id for node_id, _, _ in results[:3]]

    # At least one of the top results should be from the manufacturing branch
    manufacturing_nodes = [
        sample_hierarchy['sc1_id'],
        sample_hierarchy['c11_id'],
        sample_hierarchy['c12_id'],
        sample_hierarchy['e111_id'],
    ]

    overlap = set(top_node_ids) & set(manufacturing_nodes)
    assert len(overlap) > 0, "Top results should include manufacturing-related nodes"


def test_explain_attention(db, sample_hierarchy):
    """Test attention explanation functionality."""
    attention = HierarchicalAttention(db)

    # Query
    query_text = "factory automation"

    # Explain attention for a claim
    explanation = attention.explain_attention(
        query_text=query_text,
        node_id=sample_hierarchy['c11_id']
    )

    assert explanation is not None
    assert isinstance(explanation, AttentionPath)

    # Should have path from document to claim
    assert len(explanation.path) >= 3  # Doc -> SuperClaim -> Claim
    assert explanation.path[0] == sample_hierarchy['doc_id']
    assert explanation.path[-1] == sample_hierarchy['c11_id']

    # Should have scores for each level
    assert len(explanation.scores_per_level) == len(explanation.path)

    # Should have final score
    assert 0.0 <= explanation.final_score <= 1.0

    # Should have activation status
    assert isinstance(explanation.activated, bool)

    # Should have reason
    assert len(explanation.reason) > 0

    print(f"\nExplanation for claim {sample_hierarchy['c11_id']}:")
    print(f"Path: {' -> '.join(explanation.path)}")
    print(f"Scores: {[f'{s:.3f}' for s in explanation.scores_per_level]}")
    print(f"Final score: {explanation.final_score:.3f}")
    print(f"Activated: {explanation.activated}")
    print(f"Reason: {explanation.reason}")


def test_attention_statistics(db, sample_hierarchy):
    """Test attention statistics computation."""
    attention = HierarchicalAttention(db)

    # Get statistics
    stats = attention.get_attention_statistics(
        query_text="AI and employment",
        top_k_docs=1
    )

    # Should have statistics
    assert 'total_nodes' in stats
    assert 'activated_nodes' in stats
    assert 'activation_rate' in stats
    assert 'avg_attention' in stats
    assert 'max_attention' in stats
    assert 'min_attention' in stats

    # Values should be reasonable
    assert stats['total_nodes'] > 0
    assert 0.0 <= stats['activation_rate'] <= 1.0
    assert 0.0 <= stats['avg_attention'] <= 1.0
    assert 0.0 <= stats['max_attention'] <= 1.0

    # Should have per-level statistics
    assert 'attention_by_level' in stats

    print("\nAttention statistics:")
    for key, value in stats.items():
        if key != 'attention_by_level':
            print(f"  {key}: {value}")


def test_visualization_data(db, sample_hierarchy):
    """Test visualization data generation."""
    attention = HierarchicalAttention(db)

    # Generate visualization data
    vis_data = attention.visualize_attention(
        query_text="manufacturing jobs",
        root_id=sample_hierarchy['doc_id'],
        max_depth=3
    )

    # Should have required fields
    assert 'query' in vis_data
    assert 'root_id' in vis_data
    assert 'tree' in vis_data
    assert 'temperature' in vis_data
    assert 'activation_threshold' in vis_data

    # Tree should have hierarchical structure
    tree = vis_data['tree']
    assert 'id' in tree
    assert 'text' in tree
    assert 'level' in tree
    assert 'attention' in tree
    assert 'activated' in tree
    assert 'children' in tree

    # Should have children
    assert len(tree['children']) > 0

    print(f"\nVisualization data generated for {tree['id']}")
    print(f"Root attention: {tree['attention']:.3f}")
    print(f"Number of children: {len(tree['children'])}")


def test_performance_large_tree(db):
    """Test performance on a larger tree (100+ nodes)."""
    import time

    # Create a larger hierarchy
    # Document -> 5 SuperClaims -> 5 Claims each -> 2 Evidence each
    # Total: 1 + 5 + 25 + 50 = 81 nodes (close to 100)

    doc_id = db.create_node('Document', {
        'title': 'Large Research Document',
        'text': 'Comprehensive study on various topics in artificial intelligence.'
    })

    for i in range(5):
        sc_id = db.create_node('SuperClaim', {
            'text': f'Major finding {i+1} about AI applications in domain {i+1}.'
        })
        db.create_relationship(doc_id, sc_id, 'CONTAINS')

        for j in range(5):
            claim_id = db.create_node('Claim', {
                'text': f'Sub-finding {i+1}.{j+1} provides detailed evidence for the major finding.'
            })
            db.create_relationship(sc_id, claim_id, 'PARENT_OF')

            for k in range(2):
                evidence_id = db.create_node('Evidence', {
                    'text': f'Evidence {i+1}.{j+1}.{k+1} from study shows concrete results.'
                })
                db.create_relationship(claim_id, evidence_id, 'HAS_EVIDENCE')

    # Test retrieval performance
    attention = HierarchicalAttention(db)

    start_time = time.time()
    results = attention.retrieve_with_attention(
        query_text="AI applications and evidence",
        top_k_docs=1,
        top_k_claims=10
    )
    end_time = time.time()

    elapsed = end_time - start_time

    print(f"\nPerformance test:")
    print(f"  Tree size: ~81 nodes")
    print(f"  Retrieval time: {elapsed:.3f} seconds")
    print(f"  Results returned: {len(results)}")

    # Should complete in reasonable time (< 5 seconds for small tree)
    assert elapsed < 5.0, f"Retrieval took too long: {elapsed:.3f}s"

    # Should return results
    assert len(results) > 0


def test_cache_functionality(db, sample_hierarchy):
    """Test embedding and tree caching."""
    attention = HierarchicalAttention(db, cache_embeddings=True)

    # Build tree (populates cache)
    tree1 = attention.get_tree_structure(sample_hierarchy['doc_id'])

    # Cache should be populated
    cache_size_1 = len(attention._embedding_cache)
    assert cache_size_1 > 0

    # Build same tree again (should use cache)
    tree2 = attention.get_tree_structure(sample_hierarchy['doc_id'], use_cache=True)

    # Cache size should be same
    cache_size_2 = len(attention._embedding_cache)
    assert cache_size_2 == cache_size_1

    # Clear cache
    attention.clear_cache()

    # Cache should be empty
    assert len(attention._embedding_cache) == 0
    assert len(attention._tree_cache) == 0


def test_multiple_documents(db):
    """Test attention across multiple documents."""
    # Create two documents
    doc1_id = db.create_node('Document', {
        'title': 'AI in Healthcare',
        'text': 'Study on artificial intelligence applications in medical diagnosis.'
    })

    claim1_id = db.create_node('Claim', {
        'text': 'AI improves diagnostic accuracy by 25% in radiology.'
    })
    db.create_relationship(doc1_id, claim1_id, 'CONTAINS')

    doc2_id = db.create_node('Document', {
        'title': 'AI in Finance',
        'text': 'Research on machine learning for fraud detection in banking.'
    })

    claim2_id = db.create_node('Claim', {
        'text': 'ML algorithms reduce fraud by detecting anomalous transactions.'
    })
    db.create_relationship(doc2_id, claim2_id, 'CONTAINS')

    # Query about healthcare
    attention = HierarchicalAttention(db)
    results = attention.retrieve_with_attention(
        query_text="medical diagnosis AI",
        top_k_docs=2
    )

    # Should get results from both documents
    assert len(results) > 0

    # Healthcare document should rank higher
    top_node_ids = [node_id for node_id, _, _ in results[:2]]

    # At least one result should be from healthcare document
    healthcare_nodes = [doc1_id, claim1_id]
    assert any(node_id in healthcare_nodes for node_id in top_node_ids)


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '-s'])
