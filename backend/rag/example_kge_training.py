"""
Example: Training Knowledge Graph Embeddings

This example demonstrates how to:
1. Extract triples from the graph database
2. Train TransE embeddings
3. Save embeddings to disk
4. Use embeddings for similarity computation and link prediction

Run this example:
    python backend/rag/example_kge_training.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from research_agent.graph_database import GraphDatabase
from backend.rag import TripleExtractor, KGETrainer, train_embeddings_from_graph


def create_sample_graph():
    """Create a sample research graph for demonstration."""
    print("Creating sample research graph...")
    db = GraphDatabase()

    # Add research papers
    db.graph.add_node("paper_1", label="Document", title="Climate Change and Biodiversity", source_type="pdf")
    db.graph.add_node("paper_2", label="Document", title="CO2 Emissions Study", source_type="pdf")
    db.graph.add_node("paper_3", label="Document", title="Renewable Energy Report", source_type="pdf")

    # Add claims extracted from papers
    db.graph.add_node("claim_1", label="Claim", text="Climate change threatens biodiversity")
    db.graph.add_node("claim_2", label="Claim", text="Rising temperatures affect ecosystems")
    db.graph.add_node("claim_3", label="Claim", text="CO2 emissions are increasing globally")
    db.graph.add_node("claim_4", label="Claim", text="Renewable energy reduces emissions")
    db.graph.add_node("claim_5", label="Claim", text="Solar power is cost-effective")
    db.graph.add_node("claim_6", label="Claim", text="Wind energy has limitations")
    db.graph.add_node("claim_7", label="Claim", text="Biodiversity loss impacts ecosystems")
    db.graph.add_node("claim_8", label="Claim", text="Ocean acidification affects marine life")

    # Document containment relationships
    db.graph.add_edge("paper_1", "claim_1", type="CONTAINS")
    db.graph.add_edge("paper_1", "claim_2", type="CONTAINS")
    db.graph.add_edge("paper_1", "claim_7", type="CONTAINS")
    db.graph.add_edge("paper_2", "claim_3", type="CONTAINS")
    db.graph.add_edge("paper_2", "claim_8", type="CONTAINS")
    db.graph.add_edge("paper_3", "claim_4", type="CONTAINS")
    db.graph.add_edge("paper_3", "claim_5", type="CONTAINS")
    db.graph.add_edge("paper_3", "claim_6", type="CONTAINS")

    # Reasoning relationships between claims
    db.graph.add_edge("claim_1", "claim_2", type="SUPPORTS", confidence=0.9)
    db.graph.add_edge("claim_2", "claim_7", type="SUPPORTS", confidence=0.85)
    db.graph.add_edge("claim_3", "claim_8", type="SUPPORTS", confidence=0.8)
    db.graph.add_edge("claim_4", "claim_3", type="CONTRADICTS", confidence=0.7)  # Reduces emissions
    db.graph.add_edge("claim_5", "claim_4", type="SUPPORTS", confidence=0.9)
    db.graph.add_edge("claim_6", "claim_5", type="CONTRADICTS", confidence=0.6)

    # Similarity relationships
    db.graph.add_edge("claim_1", "claim_7", type="SIMILAR_TO", similarity=0.85)
    db.graph.add_edge("claim_2", "claim_8", type="SIMILAR_TO", similarity=0.75)

    print(f"Created graph with {len(db.graph.nodes)} nodes and {len(db.graph.edges)} edges")
    return db


def example_1_basic_training():
    """Example 1: Basic training workflow."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Training Workflow")
    print("="*60)

    # Create sample graph
    db = create_sample_graph()

    # Extract triples
    print("\n1. Extracting triples from graph...")
    extractor = TripleExtractor(db)
    triples = extractor.extract_from_neo4j()
    print(f"   Extracted {len(triples)} triples")

    # Show sample triples
    print("\n   Sample triples:")
    for i, (head, relation, tail) in enumerate(triples[:5], 1):
        print(f"   {i}. ({head}, {relation}, {tail})")

    # Train embeddings
    print("\n2. Training TransE embeddings...")
    trainer = KGETrainer(embedding_dim=128, model_type='TransE')
    embeddings = trainer.train_transe(
        triples,
        epochs=50,
        batch_size=32,
        validation_split=True
    )

    print(f"\n   Entity embeddings shape: {embeddings['entity_embeddings'].shape}")
    print(f"   Relation embeddings shape: {embeddings['relation_embeddings'].shape}")

    return trainer, embeddings


def example_2_save_and_load():
    """Example 2: Save and load embeddings."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Save and Load Embeddings")
    print("="*60)

    # Train embeddings
    db = create_sample_graph()
    trainer = KGETrainer(embedding_dim=128, model_type='TransE')
    extractor = TripleExtractor(db)
    triples = extractor.extract_from_neo4j()
    embeddings = trainer.train_transe(triples, epochs=20, validation_split=False)

    # Save to disk
    output_dir = "backend/rag/embeddings_example"
    print(f"\n1. Saving embeddings to {output_dir}...")
    trainer.save_embeddings(embeddings, output_dir)
    print("   Saved successfully!")

    # List saved files
    print("\n   Saved files:")
    for file in os.listdir(output_dir):
        filepath = os.path.join(output_dir, file)
        size = os.path.getsize(filepath)
        print(f"   - {file} ({size:,} bytes)")

    # Load in new trainer
    print("\n2. Loading embeddings in new trainer...")
    new_trainer = KGETrainer()
    loaded_embeddings = new_trainer.load_embeddings(output_dir)
    print(f"   Loaded {loaded_embeddings['entity_embeddings'].shape[0]} entity embeddings")
    print(f"   Loaded {loaded_embeddings['relation_embeddings'].shape[0]} relation embeddings")

    # Cleanup
    import shutil
    shutil.rmtree(output_dir)
    print("\n   (Cleaned up example directory)")


def example_3_similarity_and_prediction():
    """Example 3: Similarity computation and link prediction."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Similarity and Link Prediction")
    print("="*60)

    # Train embeddings
    db = create_sample_graph()
    trainer = KGETrainer(embedding_dim=128, model_type='TransE')
    extractor = TripleExtractor(db)
    triples = extractor.extract_from_neo4j()
    embeddings = trainer.train_transe(triples, epochs=50, validation_split=False)

    # Compute similarities
    print("\n1. Computing entity similarities...")
    similarities = [
        ("claim_1", "claim_2"),  # Should be high (SUPPORTS relationship)
        ("claim_1", "claim_7"),  # Should be high (SIMILAR_TO relationship)
        ("claim_5", "claim_6"),  # Should be lower (CONTRADICTS relationship)
        ("claim_1", "claim_4"),  # Unrelated claims
    ]

    for entity1, entity2 in similarities:
        sim = trainer.compute_similarity(entity1, entity2)
        if sim is not None:
            print(f"   {entity1} <-> {entity2}: {sim:.3f}")

    # Link prediction
    print("\n2. Predicting tail entities...")
    predictions = trainer.predict_tail("claim_1", "SUPPORTS", top_k=3)
    print(f"   Top predictions for (claim_1, SUPPORTS, ?):")
    for entity, score in predictions:
        print(f"   - {entity}: {score:.3f}")

    # Try another relation
    predictions = trainer.predict_tail("paper_1", "CONTAINS", top_k=5)
    print(f"\n   Top predictions for (paper_1, CONTAINS, ?):")
    for entity, score in predictions:
        print(f"   - {entity}: {score:.3f}")


def example_4_quick_training():
    """Example 4: Quick training using convenience function."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Quick Training with Convenience Function")
    print("="*60)

    db = create_sample_graph()

    print("\n   Training embeddings directly from graph...")
    embeddings = train_embeddings_from_graph(
        db,
        embedding_dim=128,
        model_type='TransE',
        epochs=30,
        output_dir=None  # Don't save to disk
    )

    print(f"\n   Trained embeddings:")
    print(f"   - {embeddings['entity_embeddings'].shape[0]} entities")
    print(f"   - {embeddings['relation_embeddings'].shape[0]} relations")
    print(f"   - Embedding dimension: {embeddings['entity_embeddings'].shape[1]}")


def example_5_export_to_tsv():
    """Example 5: Export triples to TSV and train."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Export to TSV and Train")
    print("="*60)

    db = create_sample_graph()
    extractor = TripleExtractor(db)

    # Export to TSV
    tsv_path = "backend/rag/triples_example.tsv"
    print(f"\n1. Exporting triples to {tsv_path}...")
    num_triples = extractor.export_to_pykeen_format(tsv_path)
    print(f"   Exported {num_triples} triples")

    # Show first few lines
    print("\n   First 5 lines:")
    with open(tsv_path, 'r') as f:
        for i, line in enumerate(f, 1):
            if i > 5:
                break
            print(f"   {i}. {line.strip()}")

    # Train from TSV
    print("\n2. Training from TSV file...")
    trainer = KGETrainer(embedding_dim=128, model_type='TransE')
    embeddings = trainer.train_from_tsv(tsv_path, epochs=20, validation_split=False)
    print(f"   Trained {embeddings['entity_embeddings'].shape[0]} entity embeddings")

    # Cleanup
    os.remove(tsv_path)
    print("\n   (Cleaned up TSV file)")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Knowledge Graph Embedding (KGE) Training Examples")
    print("="*60)

    try:
        # Run examples
        example_1_basic_training()
        example_2_save_and_load()
        example_3_similarity_and_prediction()
        example_4_quick_training()
        example_5_export_to_tsv()

        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
