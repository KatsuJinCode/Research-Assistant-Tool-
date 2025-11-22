"""
Example Usage of Hierarchical Attention Mechanism

Demonstrates:
1. Building a hierarchical knowledge graph
2. Computing attention scores at multiple levels
3. Retrieving relevant claims with hierarchical attention
4. Explaining attention paths
5. Visualizing attention distribution
6. Performance characteristics

Run with:
    python backend/rag/example_hierarchical_attention.py
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from research_agent.graph_database import GraphDatabase
from backend.rag.hierarchical_attention import HierarchicalAttention
from backend.rag.semantic_similarity import SemanticSimilarity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_knowledge_graph():
    """
    Create a sample hierarchical knowledge graph about AI impact.

    Structure:
        Document: "AI Impact on Society"
        ├── SuperClaim: "AI affects employment"
        │   ├── Claim: "Automation displaces workers"
        │   │   ├── Evidence: "Manufacturing jobs reduced by 30%"
        │   │   └── Evidence: "5M jobs lost globally"
        │   └── Claim: "AI creates new jobs"
        │       └── Evidence: "ML engineer demand up 500%"
        └── SuperClaim: "AI improves healthcare"
            ├── Claim: "AI aids diagnosis"
            │   └── Evidence: "25% accuracy improvement"
            └── Claim: "AI accelerates drug discovery"
                └── Evidence: "Discovery time reduced by 50%"
    """
    db = GraphDatabase()

    # Create document
    doc_id = db.create_node('Document', {
        'title': 'Artificial Intelligence: Transforming Society and Industry',
        'text': 'This comprehensive study examines the multifaceted impact of artificial intelligence on employment, healthcare, and societal structures.',
        'author': 'Research Institute for AI Studies',
        'year': 2024
    })

    # --- Employment Branch ---

    # SuperClaim 1: Employment
    sc_employment = db.create_node('SuperClaim', {
        'text': 'Artificial intelligence has significant and complex effects on employment, both displacing existing jobs and creating new opportunities.',
        'confidence': 0.95
    })
    db.create_relationship(doc_id, sc_employment, 'CONTAINS')

    # Claim 1.1: Job displacement
    claim_displacement = db.create_node('Claim', {
        'text': 'Automation and AI-powered robotics are displacing workers in manufacturing and routine-task sectors.',
        'confidence': 0.90
    })
    db.create_relationship(sc_employment, claim_displacement, 'PARENT_OF')

    # Evidence 1.1.1
    evidence_manufacturing = db.create_node('Evidence', {
        'text': 'A 2020 study by the International Labor Organization found a 30% reduction in manufacturing employment due to automation between 2015 and 2020.',
        'source': 'ILO Report 2020',
        'confidence': 0.85
    })
    db.create_relationship(claim_displacement, evidence_manufacturing, 'HAS_EVIDENCE')

    # Evidence 1.1.2
    evidence_global_jobs = db.create_node('Evidence', {
        'text': 'Approximately 5 million jobs globally have been eliminated due to AI and robotic automation in the past decade.',
        'source': 'World Economic Forum 2023',
        'confidence': 0.80
    })
    db.create_relationship(claim_displacement, evidence_global_jobs, 'HAS_EVIDENCE')

    # Claim 1.2: Job creation
    claim_creation = db.create_node('Claim', {
        'text': 'AI is creating new high-skilled job opportunities in technology, data science, and machine learning engineering.',
        'confidence': 0.92
    })
    db.create_relationship(sc_employment, claim_creation, 'PARENT_OF')

    # Evidence 1.2.1
    evidence_ml_jobs = db.create_node('Evidence', {
        'text': 'Demand for machine learning engineers has increased by 500% since 2015, making it the fastest-growing job category according to LinkedIn.',
        'source': 'LinkedIn Jobs Report 2023',
        'confidence': 0.88
    })
    db.create_relationship(claim_creation, evidence_ml_jobs, 'HAS_EVIDENCE')

    # Evidence 1.2.2
    evidence_data_science = db.create_node('Evidence', {
        'text': 'Data scientist positions have grown by 650% in the past 5 years, with median salaries exceeding $120,000.',
        'source': 'Glassdoor Economic Research 2024',
        'confidence': 0.87
    })
    db.create_relationship(claim_creation, evidence_data_science, 'HAS_EVIDENCE')

    # --- Healthcare Branch ---

    # SuperClaim 2: Healthcare
    sc_healthcare = db.create_node('SuperClaim', {
        'text': 'AI technologies are revolutionizing healthcare through improved diagnostics and accelerated drug discovery.',
        'confidence': 0.93
    })
    db.create_relationship(doc_id, sc_healthcare, 'CONTAINS')

    # Claim 2.1: Diagnostic improvement
    claim_diagnosis = db.create_node('Claim', {
        'text': 'AI-powered diagnostic systems achieve higher accuracy rates than human physicians in certain medical imaging tasks.',
        'confidence': 0.89
    })
    db.create_relationship(sc_healthcare, claim_diagnosis, 'PARENT_OF')

    # Evidence 2.1.1
    evidence_radiology = db.create_node('Evidence', {
        'text': 'Deep learning models demonstrate 25% improvement in diagnostic accuracy for radiology, particularly in detecting early-stage cancers.',
        'source': 'Nature Medicine 2023',
        'confidence': 0.91
    })
    db.create_relationship(claim_diagnosis, evidence_radiology, 'HAS_EVIDENCE')

    # Evidence 2.1.2
    evidence_pathology = db.create_node('Evidence', {
        'text': 'AI systems can analyze pathology slides 1000x faster than human pathologists with comparable accuracy.',
        'source': 'Journal of Medical AI 2024',
        'confidence': 0.86
    })
    db.create_relationship(claim_diagnosis, evidence_pathology, 'HAS_EVIDENCE')

    # Claim 2.2: Drug discovery
    claim_drugs = db.create_node('Claim', {
        'text': 'Machine learning algorithms are dramatically accelerating the drug discovery and development process.',
        'confidence': 0.88
    })
    db.create_relationship(sc_healthcare, claim_drugs, 'PARENT_OF')

    # Evidence 2.2.1
    evidence_discovery_time = db.create_node('Evidence', {
        'text': 'AI-driven drug discovery platforms have reduced the time to identify viable drug candidates by 50%, from 4-5 years to 2-2.5 years.',
        'source': 'Pharmaceutical Research Journal 2023',
        'confidence': 0.84
    })
    db.create_relationship(claim_drugs, evidence_discovery_time, 'HAS_EVIDENCE')

    # Evidence 2.2.2
    evidence_molecule_design = db.create_node('Evidence', {
        'text': 'DeepMind\'s AlphaFold has predicted structures for over 200 million proteins, vastly expanding potential drug targets.',
        'source': 'Science 2023',
        'confidence': 0.95
    })
    db.create_relationship(claim_drugs, evidence_molecule_design, 'HAS_EVIDENCE')

    logger.info(f"Created knowledge graph with {db.stats()['total_nodes']} nodes and {db.stats()['total_relationships']} relationships")

    return db, doc_id


def demonstrate_basic_retrieval(db, doc_id):
    """Demonstrate basic hierarchical attention retrieval."""
    print("\n" + "="*80)
    print("1. BASIC HIERARCHICAL ATTENTION RETRIEVAL")
    print("="*80)

    attention = HierarchicalAttention(db, temperature=1.0)

    # Query about employment
    query = "How does AI and automation affect manufacturing jobs?"
    print(f"\nQuery: '{query}'")

    results = attention.retrieve_with_attention(
        query_text=query,
        top_k_docs=1,
        top_k_claims=5,
        top_k_evidence=5
    )

    print(f"\nTop {min(10, len(results))} results:")
    print("-" * 80)

    for i, (node_id, score, level) in enumerate(results[:10], 1):
        node = db.get_node(node_id)
        text = node.get('text', node.get('title', ''))[:100]
        label = node.get('label', 'Unknown')

        print(f"{i}. [Level {level}] [{label}] {text}...")
        print(f"   Attention Score: {score:.4f}")
        print()


def demonstrate_temperature_effects(db, doc_id):
    """Demonstrate how temperature affects attention distribution."""
    print("\n" + "="*80)
    print("2. TEMPERATURE EFFECTS ON ATTENTION")
    print("="*80)

    query = "AI in healthcare and medical diagnosis"
    print(f"\nQuery: '{query}'")

    # Sharp attention (temperature = 0.5)
    print("\n--- Sharp Attention (temperature = 0.5) ---")
    sharp_attention = HierarchicalAttention(db, temperature=0.5)
    sharp_results = sharp_attention.retrieve_with_attention(query, top_k_docs=1, top_k_claims=3)

    for i, (node_id, score, level) in enumerate(sharp_results[:5], 1):
        node = db.get_node(node_id)
        print(f"{i}. {node.get('label', 'Node')[:15]:15s} Score: {score:.4f}")

    # Soft attention (temperature = 2.0)
    print("\n--- Soft Attention (temperature = 2.0) ---")
    soft_attention = HierarchicalAttention(db, temperature=2.0)
    soft_results = soft_attention.retrieve_with_attention(query, top_k_docs=1, top_k_claims=3)

    for i, (node_id, score, level) in enumerate(soft_results[:5], 1):
        node = db.get_node(node_id)
        print(f"{i}. {node.get('label', 'Node')[:15]:15s} Score: {score:.4f}")

    print("\nObservation: Sharp attention (low temperature) creates more focused scores,")
    print("while soft attention (high temperature) distributes attention more evenly.")


def demonstrate_attention_explanation(db, doc_id):
    """Demonstrate attention path explanation."""
    print("\n" + "="*80)
    print("3. ATTENTION PATH EXPLANATION")
    print("="*80)

    attention = HierarchicalAttention(db)

    query = "machine learning job opportunities"
    print(f"\nQuery: '{query}'")

    # Find a relevant claim
    results = attention.retrieve_with_attention(query, top_k_docs=1, top_k_claims=3)

    if results:
        target_node_id = results[0][0]
        target_node = db.get_node(target_node_id)

        print(f"\nExplaining attention for: {target_node.get('text', '')[:80]}...")
        print("-" * 80)

        explanation = attention.explain_attention(query, target_node_id)

        if explanation:
            print(f"\nAttention Path (root -> target):")
            for i, node_id in enumerate(explanation.path):
                node = db.get_node(node_id)
                level_score = explanation.scores_per_level[i]
                label = node.get('label', 'Unknown')

                indent = "  " * i
                print(f"{indent}{'+-' if i > 0 else ''} [{label}] {node.get('text', node.get('title', ''))[:60]}...")
                print(f"{indent}   Attention: {level_score:.4f}")

            print(f"\nFinal Score: {explanation.final_score:.4f}")
            print(f"Activated: {explanation.activated}")
            print(f"Reason: {explanation.reason}")


def demonstrate_attention_statistics(db, doc_id):
    """Demonstrate attention distribution statistics."""
    print("\n" + "="*80)
    print("4. ATTENTION DISTRIBUTION STATISTICS")
    print("="*80)

    attention = HierarchicalAttention(db, activation_threshold=0.2)

    query = "artificial intelligence impact on society"
    print(f"\nQuery: '{query}'")

    stats = attention.get_attention_statistics(query, top_k_docs=1)

    print("\nOverall Statistics:")
    print("-" * 80)
    print(f"Total Nodes:       {stats['total_nodes']}")
    print(f"Activated Nodes:   {stats['activated_nodes']}")
    print(f"Activation Rate:   {stats['activation_rate']:.2%}")
    print(f"Avg Attention:     {stats['avg_attention']:.4f}")
    print(f"Max Attention:     {stats['max_attention']:.4f}")
    print(f"Min Attention:     {stats['min_attention']:.4f}")
    print(f"Std Deviation:     {stats['std_attention']:.4f}")

    print("\nAttention by Level:")
    print("-" * 80)
    for level, level_stats in sorted(stats['attention_by_level'].items()):
        level_names = {0: 'Document', 1: 'SuperClaim', 2: 'Claim', 3: 'Evidence'}
        level_name = level_names.get(level, f'Level {level}')

        print(f"{level_name:15s} | Count: {level_stats['count']:2d} | "
              f"Avg: {level_stats['avg_score']:.4f} | "
              f"Max: {level_stats['max_score']:.4f} | "
              f"Min: {level_stats['min_score']:.4f}")


def demonstrate_branch_activation(db, doc_id):
    """Demonstrate branch activation and pruning."""
    print("\n" + "="*80)
    print("5. BRANCH ACTIVATION AND PRUNING")
    print("="*80)

    # High threshold (aggressive pruning)
    print("\n--- High Activation Threshold (0.4) - Aggressive Pruning ---")
    high_threshold = HierarchicalAttention(db, activation_threshold=0.4, temperature=0.8)

    query = "drug discovery and pharmaceutical research"
    print(f"\nQuery: '{query}'")

    results_high = high_threshold.retrieve_with_attention(query, top_k_docs=1)
    print(f"Nodes retrieved: {len(results_high)}")

    for i, (node_id, score, level) in enumerate(results_high[:5], 1):
        node = db.get_node(node_id)
        print(f"{i}. [{node.get('label', 'N'):12s}] Score: {score:.4f} - {node.get('text', '')[:50]}...")

    # Low threshold (minimal pruning)
    print("\n--- Low Activation Threshold (0.05) - Minimal Pruning ---")
    low_threshold = HierarchicalAttention(db, activation_threshold=0.05, temperature=0.8)

    results_low = low_threshold.retrieve_with_attention(query, top_k_docs=1)
    print(f"Nodes retrieved: {len(results_low)}")

    for i, (node_id, score, level) in enumerate(results_low[:5], 1):
        node = db.get_node(node_id)
        print(f"{i}. [{node.get('label', 'N'):12s}] Score: {score:.4f} - {node.get('text', '')[:50]}...")

    print(f"\nWith high threshold: {len(results_high)} nodes (focused)")
    print(f"With low threshold:  {len(results_low)} nodes (comprehensive)")


def demonstrate_performance(db, doc_id):
    """Demonstrate performance characteristics."""
    print("\n" + "="*80)
    print("6. PERFORMANCE CHARACTERISTICS")
    print("="*80)

    import time

    attention = HierarchicalAttention(db, cache_embeddings=True)

    query = "AI impact analysis"

    # First run (cold cache)
    print("\nFirst run (cold cache):")
    start = time.time()
    results1 = attention.retrieve_with_attention(query, top_k_docs=1)
    time1 = time.time() - start
    print(f"  Time: {time1:.3f} seconds")
    print(f"  Results: {len(results1)} nodes")
    print(f"  Cache size: {len(attention._embedding_cache)} embeddings")

    # Second run (warm cache)
    print("\nSecond run (warm cache):")
    start = time.time()
    results2 = attention.retrieve_with_attention(query, top_k_docs=1)
    time2 = time.time() - start
    print(f"  Time: {time2:.3f} seconds")
    print(f"  Results: {len(results2)} nodes")
    print(f"  Speedup: {time1/time2:.2f}x")


def main():
    """Run all demonstrations."""
    print("="*80)
    print("HIERARCHICAL ATTENTION MECHANISM - DEMONSTRATION")
    print("="*80)

    # Create sample graph
    print("\nCreating sample knowledge graph...")
    db, doc_id = create_sample_knowledge_graph()

    # Run demonstrations
    demonstrate_basic_retrieval(db, doc_id)
    demonstrate_temperature_effects(db, doc_id)
    demonstrate_attention_explanation(db, doc_id)
    demonstrate_attention_statistics(db, doc_id)
    demonstrate_branch_activation(db, doc_id)
    demonstrate_performance(db, doc_id)

    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()
