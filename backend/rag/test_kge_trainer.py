"""
Tests for Knowledge Graph Embedding (KGE) Trainer

Tests cover:
1. Small graph training with TransE
2. TSV import and training
3. Embedding save/load
4. Entity/relation lookup
5. Link prediction
6. Similarity computation
7. Model comparison (TransE vs RotatE)
"""

import os
import tempfile
import shutil
import pytest
import numpy as np
from pathlib import Path

from backend.rag.kge_trainer import KGETrainer, train_embeddings_from_graph
from research_agent.graph_database import GraphDatabase


class TestKGETrainer:
    """Test suite for KGETrainer."""

    @pytest.fixture
    def sample_triples(self):
        """Create sample triples for testing."""
        return [
            # Claim relationships
            ("claim_1", "SUPPORTS", "claim_2"),
            ("claim_2", "SUPPORTS", "claim_3"),
            ("claim_1", "CONTRADICTS", "claim_4"),
            ("claim_4", "CONTRADICTS", "claim_5"),

            # Document containment
            ("doc_1", "CONTAINS", "claim_1"),
            ("doc_1", "CONTAINS", "claim_2"),
            ("doc_2", "CONTAINS", "claim_3"),
            ("doc_2", "CONTAINS", "claim_4"),

            # Hierarchical relationships
            ("claim_1", "PARENT_OF", "claim_6"),
            ("claim_2", "PARENT_OF", "claim_7"),

            # Similarity
            ("claim_1", "SIMILAR_TO", "claim_8"),
            ("claim_3", "SIMILAR_TO", "claim_9"),

            # More complex patterns
            ("claim_6", "SUPPORTS", "claim_7"),
            ("claim_7", "SUPPORTS", "claim_8"),
            ("claim_8", "CONTRADICTS", "claim_9"),
        ]

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    def test_trainer_initialization(self):
        """Test KGETrainer initialization."""
        # Default initialization
        trainer = KGETrainer()
        assert trainer.embedding_dim == 256
        assert trainer.model_type == 'TransE'
        assert trainer.device in ['cpu', 'cuda']

        # Custom initialization
        trainer = KGETrainer(embedding_dim=128, model_type='RotatE')
        assert trainer.embedding_dim == 128
        assert trainer.model_type == 'RotatE'

        # Invalid model type
        with pytest.raises(ValueError):
            KGETrainer(model_type='InvalidModel')

    def test_small_graph_training(self, sample_triples):
        """Test training on small graph."""
        trainer = KGETrainer(embedding_dim=64, model_type='TransE')

        # Train with few epochs for speed
        embeddings = trainer.train_transe(
            sample_triples,
            epochs=10,  # Quick test
            batch_size=32,
            validation_split=True
        )

        # Check embeddings shape
        assert 'entity_embeddings' in embeddings
        assert 'relation_embeddings' in embeddings

        entity_emb = embeddings['entity_embeddings']
        relation_emb = embeddings['relation_embeddings']

        assert entity_emb.shape[1] == 64  # embedding_dim
        assert relation_emb.shape[1] == 64

        # Check we have entities and relations
        assert entity_emb.shape[0] > 0
        assert relation_emb.shape[0] > 0

        # Check embeddings are not all zeros
        assert np.abs(entity_emb).sum() > 0
        assert np.abs(relation_emb).sum() > 0

        print(f"Trained on {len(sample_triples)} triples")
        print(f"Entity embeddings shape: {entity_emb.shape}")
        print(f"Relation embeddings shape: {relation_emb.shape}")

    def test_tsv_import(self, sample_triples, temp_dir):
        """Test training from TSV file."""
        # Create TSV file
        tsv_path = os.path.join(temp_dir, 'triples.tsv')
        with open(tsv_path, 'w', encoding='utf-8') as f:
            for head, relation, tail in sample_triples:
                f.write(f"{head}\t{relation}\t{tail}\n")

        # Train from TSV
        trainer = KGETrainer(embedding_dim=64, model_type='TransE')
        embeddings = trainer.train_from_tsv(
            tsv_path,
            epochs=10,
            batch_size=32
        )

        # Verify embeddings
        assert 'entity_embeddings' in embeddings
        assert 'relation_embeddings' in embeddings
        assert embeddings['entity_embeddings'].shape[0] > 0

        print(f"Successfully loaded and trained from TSV: {tsv_path}")

    def test_embedding_save_load(self, sample_triples, temp_dir):
        """Test saving and loading embeddings."""
        # Train embeddings
        trainer = KGETrainer(embedding_dim=64, model_type='TransE')
        embeddings = trainer.train_transe(
            sample_triples,
            epochs=10,
            batch_size=32
        )

        # Save embeddings
        output_dir = os.path.join(temp_dir, 'embeddings')
        trainer.save_embeddings(embeddings, output_dir)

        # Check files were created
        assert os.path.exists(os.path.join(output_dir, 'entity_embeddings.npy'))
        assert os.path.exists(os.path.join(output_dir, 'relation_embeddings.npy'))
        assert os.path.exists(os.path.join(output_dir, 'entity_to_id.json'))
        assert os.path.exists(os.path.join(output_dir, 'relation_to_id.json'))
        assert os.path.exists(os.path.join(output_dir, 'model_metadata.json'))

        # Load embeddings in new trainer
        new_trainer = KGETrainer()
        loaded_embeddings = new_trainer.load_embeddings(output_dir)

        # Verify consistency
        assert loaded_embeddings['entity_embeddings'].shape == embeddings['entity_embeddings'].shape
        assert loaded_embeddings['relation_embeddings'].shape == embeddings['relation_embeddings'].shape

        # Check arrays are identical
        np.testing.assert_array_almost_equal(
            loaded_embeddings['entity_embeddings'],
            embeddings['entity_embeddings']
        )
        np.testing.assert_array_almost_equal(
            loaded_embeddings['relation_embeddings'],
            embeddings['relation_embeddings']
        )

        print("Save/load successful - embeddings match!")

    def test_entity_lookup(self, sample_triples):
        """Test getting embedding for specific entity."""
        trainer = KGETrainer(embedding_dim=64, model_type='TransE')
        trainer.train_transe(sample_triples, epochs=10, batch_size=32)

        # Get embedding for known entity
        emb = trainer.get_entity_embedding('claim_1')
        assert emb is not None
        assert emb.shape == (64,)
        assert np.abs(emb).sum() > 0

        # Try unknown entity
        emb = trainer.get_entity_embedding('unknown_entity')
        assert emb is None

        print("Entity lookup working correctly")

    def test_relation_lookup(self, sample_triples):
        """Test getting embedding for specific relation."""
        trainer = KGETrainer(embedding_dim=64, model_type='TransE')
        trainer.train_transe(sample_triples, epochs=10, batch_size=32)

        # Get embedding for known relation
        emb = trainer.get_relation_embedding('SUPPORTS')
        assert emb is not None
        assert emb.shape == (64,)
        assert np.abs(emb).sum() > 0

        # Try unknown relation
        emb = trainer.get_relation_embedding('UNKNOWN_RELATION')
        assert emb is None

        print("Relation lookup working correctly")

    def test_similarity_computation(self, sample_triples):
        """Test computing similarity between entities."""
        trainer = KGETrainer(embedding_dim=64, model_type='TransE')
        trainer.train_transe(sample_triples, epochs=10, batch_size=32)

        # Compute similarity between two entities
        sim = trainer.compute_similarity('claim_1', 'claim_2')
        assert sim is not None
        assert -1.0 <= sim <= 1.0

        print(f"Similarity(claim_1, claim_2) = {sim:.3f}")

        # Self-similarity should be close to 1.0
        self_sim = trainer.compute_similarity('claim_1', 'claim_1')
        assert self_sim is not None
        assert self_sim > 0.99  # Very close to 1.0

        print(f"Self-similarity(claim_1, claim_1) = {self_sim:.3f}")

        # Unknown entity
        sim_unknown = trainer.compute_similarity('claim_1', 'unknown')
        assert sim_unknown is None

        print("Similarity computation working correctly")

    def test_tail_prediction(self, sample_triples):
        """Test predicting tail entities (link prediction)."""
        trainer = KGETrainer(embedding_dim=64, model_type='TransE')
        trainer.train_transe(sample_triples, epochs=10, batch_size=32)

        # Predict tail for (claim_1, SUPPORTS, ?)
        predictions = trainer.predict_tail('claim_1', 'SUPPORTS', top_k=3)

        assert len(predictions) > 0
        assert len(predictions) <= 3

        # Check format
        for entity_id, score in predictions:
            assert isinstance(entity_id, str)
            assert isinstance(score, float)

        print(f"Top predictions for (claim_1, SUPPORTS, ?):")
        for entity_id, score in predictions:
            print(f"  {entity_id}: {score:.3f}")

    def test_empty_triples(self):
        """Test handling of empty triples."""
        trainer = KGETrainer(embedding_dim=64)

        with pytest.raises(ValueError, match="empty"):
            trainer.train_transe([])

    def test_invalid_tsv(self, temp_dir):
        """Test handling of invalid TSV files."""
        trainer = KGETrainer()

        # Non-existent file
        with pytest.raises(FileNotFoundError):
            trainer.train_from_tsv('nonexistent.tsv')

        # Empty file
        empty_tsv = os.path.join(temp_dir, 'empty.tsv')
        with open(empty_tsv, 'w') as f:
            f.write('')

        with pytest.raises(ValueError, match="No valid triples"):
            trainer.train_from_tsv(empty_tsv)

    def test_training_history(self, sample_triples):
        """Test that training history is recorded."""
        trainer = KGETrainer(embedding_dim=64, model_type='TransE')
        trainer.train_transe(sample_triples, epochs=10, batch_size=32)

        # Check training history exists
        assert trainer.training_history is not None
        assert 'epochs' in trainer.training_history
        assert 'losses' in trainer.training_history

        # Check we have loss values
        assert len(trainer.training_history['losses']) > 0

        print(f"Training history recorded: {len(trainer.training_history['losses'])} epochs")

    def test_model_comparison(self, sample_triples):
        """Compare TransE vs RotatE training."""
        # Train TransE
        trainer_transe = KGETrainer(embedding_dim=64, model_type='TransE')
        embeddings_transe = trainer_transe.train_transe(
            sample_triples,
            epochs=10,
            batch_size=32
        )

        # Train RotatE (uses complex embeddings, so actual dimension is 2x)
        trainer_rotate = KGETrainer(embedding_dim=64, model_type='RotatE')
        embeddings_rotate = trainer_rotate.train_transe(  # Same method works for all models
            sample_triples,
            epochs=10,
            batch_size=32
        )

        # Both should produce embeddings (but RotatE will be 2x dimension due to complex space)
        assert embeddings_transe['entity_embeddings'].shape[0] == embeddings_rotate['entity_embeddings'].shape[0]

        # TransE: (num_entities, embedding_dim)
        # RotatE: (num_entities, 2*embedding_dim) - complex embeddings
        print(f"TransE shape: {embeddings_transe['entity_embeddings'].shape}")
        print(f"RotatE shape: {embeddings_rotate['entity_embeddings'].shape}")

        assert embeddings_transe['entity_embeddings'].shape[1] == 64
        assert embeddings_rotate['entity_embeddings'].shape[1] == 128  # 2x for complex

        print("Model comparison successful!")


class TestGraphDatabaseIntegration:
    """Test integration with GraphDatabase."""

    @pytest.fixture
    def populated_db(self):
        """Create and populate a GraphDatabase for testing."""
        db = GraphDatabase()

        # Add nodes directly to the graph
        db.graph.add_node("claim_1", label="Claim", text="Climate change is real")
        db.graph.add_node("claim_2", label="Claim", text="Global warming affects ecosystems")
        db.graph.add_node("claim_3", label="Claim", text="CO2 levels are rising")
        db.graph.add_node("claim_4", label="Claim", text="Climate change is a hoax")
        db.graph.add_node("doc_1", label="Document", title="Research Paper")
        db.graph.add_node("doc_2", label="Document", title="Scientific Report")

        # Add edges with type attribute
        db.graph.add_edge("claim_1", "claim_2", type="SUPPORTS", confidence=0.9)
        db.graph.add_edge("claim_2", "claim_3", type="SUPPORTS", confidence=0.85)
        db.graph.add_edge("claim_1", "claim_4", type="CONTRADICTS", confidence=0.95)
        db.graph.add_edge("doc_1", "claim_1", type="CONTAINS")
        db.graph.add_edge("doc_1", "claim_2", type="CONTAINS")
        db.graph.add_edge("doc_2", "claim_3", type="CONTAINS")

        return db

    def test_train_from_graph(self, populated_db, tmp_path):
        """Test training embeddings from GraphDatabase."""
        output_dir = str(tmp_path / 'embeddings')

        embeddings = train_embeddings_from_graph(
            populated_db,
            embedding_dim=64,
            model_type='TransE',
            epochs=10,
            output_dir=output_dir
        )

        # Check embeddings were created
        assert 'entity_embeddings' in embeddings
        assert 'relation_embeddings' in embeddings
        assert embeddings['entity_embeddings'].shape[0] > 0

        # Check files were saved
        assert os.path.exists(os.path.join(output_dir, 'entity_embeddings.npy'))
        assert os.path.exists(os.path.join(output_dir, 'relation_embeddings.npy'))

        print(f"Successfully trained embeddings from GraphDatabase")
        print(f"Entities: {embeddings['entity_embeddings'].shape[0]}")
        print(f"Relations: {embeddings['relation_embeddings'].shape[0]}")


def run_performance_test():
    """
    Performance test for different graph sizes.

    This is not a pytest test - run separately to measure performance.
    """
    print("\n" + "="*60)
    print("KGE Trainer Performance Test")
    print("="*60)

    from backend.rag.triple_extractor import TripleExtractor
    import time

    # Test different graph sizes
    graph_sizes = [50, 100, 500, 1000]

    for size in graph_sizes:
        print(f"\nTesting with {size} triples...")

        # Generate synthetic triples
        triples = []
        for i in range(size):
            head = f"entity_{i}"
            tail = f"entity_{(i+1) % size}"
            relation = ['SUPPORTS', 'CONTRADICTS', 'SIMILAR_TO'][i % 3]
            triples.append((head, relation, tail))

        # Train
        trainer = KGETrainer(embedding_dim=128, model_type='TransE')
        start_time = time.time()

        embeddings = trainer.train_transe(
            triples,
            epochs=50,
            batch_size=128,
            validation_split=False  # Skip validation for speed
        )

        elapsed = time.time() - start_time

        print(f"  Training time: {elapsed:.2f}s")
        print(f"  Entities: {embeddings['entity_embeddings'].shape[0]}")
        print(f"  Relations: {embeddings['relation_embeddings'].shape[0]}")
        print(f"  Time per triple: {elapsed/size*1000:.2f}ms")


if __name__ == '__main__':
    # Run pytest
    pytest.main([__file__, '-v', '-s'])

    # Optionally run performance test
    # run_performance_test()
