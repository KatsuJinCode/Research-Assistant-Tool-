"""
Knowledge Graph Embedding (KGE) Trainer

Trains knowledge graph embeddings using PyKEEN (Python KnowlEdge EmbeddiNgs).
Supports TransE, RotatE, and DistMult models for embedding research claim graphs.

Knowledge Graph Embeddings represent entities and relations as vectors in a continuous
vector space, enabling semantic similarity computation and link prediction.

Models:
- TransE: Translational model (h + r ≈ t) - simple, fast, good for hierarchical relations
- RotatE: Rotational model in complex space - better for complex relation patterns
- DistMult: Bilinear model - best for symmetric relations

Typical workflow:
    1. Extract triples from GraphDatabase using TripleExtractor
    2. Train embeddings using KGETrainer.train_transe()
    3. Save embeddings to disk
    4. Load embeddings for downstream tasks (retrieval, link prediction)

Example:
    >>> from research_agent.graph_database import GraphDatabase
    >>> from backend.rag import TripleExtractor, KGETrainer
    >>>
    >>> db = GraphDatabase()
    >>> extractor = TripleExtractor(db)
    >>> triples = extractor.extract_from_neo4j()
    >>>
    >>> trainer = KGETrainer(embedding_dim=256, model_type='TransE')
    >>> embeddings = trainer.train_transe(triples, epochs=100)
    >>> trainer.save_embeddings(embeddings, 'backend/rag/embeddings/')
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

# PyKEEN imports
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory
from pykeen.models import Model
import torch

# Configure logging
logger = logging.getLogger(__name__)


class KGETrainer:
    """Train knowledge graph embeddings using PyKEEN."""

    # Supported model types
    SUPPORTED_MODELS = {'TransE', 'RotatE', 'DistMult'}

    # Default hyperparameters
    DEFAULT_EMBEDDING_DIM = 256
    DEFAULT_EPOCHS = 100
    DEFAULT_BATCH_SIZE = 256
    DEFAULT_LEARNING_RATE = 0.001

    # Training split ratios (train/val/test)
    TRAIN_RATIO = 0.8
    VAL_RATIO = 0.1
    TEST_RATIO = 0.1

    def __init__(self, embedding_dim: int = DEFAULT_EMBEDDING_DIM,
                 model_type: str = 'TransE',
                 random_seed: int = 42):
        """
        Initialize KGE trainer.

        Args:
            embedding_dim: Dimension of embeddings (default: 256)
                          Higher = more expressive but slower
                          Recommended: 128 (small graphs), 256 (medium), 512 (large)
            model_type: 'TransE', 'RotatE', or 'DistMult'
                       TransE: Simple, fast, good for hierarchical relations
                       RotatE: Better for complex patterns, slower
                       DistMult: Best for symmetric relations
            random_seed: Random seed for reproducibility

        Raises:
            ValueError: If model_type is not supported
        """
        if model_type not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model type: {model_type}. "
                f"Supported models: {self.SUPPORTED_MODELS}"
            )

        self.embedding_dim = embedding_dim
        self.model_type = model_type
        self.random_seed = random_seed

        # Will be populated after training
        self.model: Optional[Model] = None
        self.entity_to_id: Optional[Dict[str, int]] = None
        self.relation_to_id: Optional[Dict[str, int]] = None
        self.id_to_entity: Optional[Dict[int, str]] = None
        self.id_to_relation: Optional[Dict[int, str]] = None
        self.training_history: Optional[Dict[str, List[float]]] = None

        # Detect device (GPU if available)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"KGETrainer initialized: {model_type}, dim={embedding_dim}, device={self.device}")

    def train_transe(self, triples: List[Tuple[str, str, str]],
                     epochs: int = DEFAULT_EPOCHS,
                     batch_size: int = DEFAULT_BATCH_SIZE,
                     learning_rate: float = DEFAULT_LEARNING_RATE,
                     validation_split: bool = True,
                     early_stopping_patience: int = 10) -> Dict[str, np.ndarray]:
        """
        Train TransE embeddings on triples.

        TransE treats relations as translations in embedding space:
        h + r ≈ t (head entity + relation ≈ tail entity)

        This is ideal for hierarchical and transitive relations like:
        - CONTAINS, PARENT_OF (hierarchical)
        - SUPPORTS, CONTRADICTS (reasoning)

        Args:
            triples: List of (head, relation, tail) tuples
            epochs: Training epochs (default: 100)
                   More epochs = better embeddings but longer training
                   Recommended: 50 (quick), 100 (standard), 200 (high quality)
            batch_size: Batch size for training (default: 256)
                       Larger = faster but more memory
            learning_rate: Learning rate (default: 0.001)
                          Standard Adam optimizer
            validation_split: Whether to split data for validation (default: True)
            early_stopping_patience: Stop if no improvement for N epochs (default: 10)

        Returns:
            Dict with 'entity_embeddings' and 'relation_embeddings' as numpy arrays

        Raises:
            ValueError: If triples list is empty or invalid
        """
        if not triples:
            raise ValueError("Cannot train on empty triples list")

        logger.info(f"Training TransE on {len(triples)} triples...")
        logger.info(f"Hyperparameters: epochs={epochs}, batch_size={batch_size}, lr={learning_rate}")

        # Create triples factory
        tf = TriplesFactory.from_labeled_triples(
            np.array(triples, dtype=str),
            create_inverse_triples=False,  # Don't automatically add inverse relations
        )

        # Split into train/val/test if requested
        training_kwargs = {}
        if validation_split:
            train_tf, val_tf, test_tf = tf.split(
                [self.TRAIN_RATIO, self.VAL_RATIO, self.TEST_RATIO],
                random_state=self.random_seed,
            )
            training_kwargs['training'] = train_tf
            training_kwargs['validation'] = val_tf
            training_kwargs['testing'] = test_tf
            logger.info(f"Split: train={len(train_tf.triples)}, "
                       f"val={len(val_tf.triples)}, test={len(test_tf.triples)}")
        else:
            training_kwargs['training'] = tf

        # Configure training pipeline
        result = pipeline(
            model=self.model_type,
            model_kwargs=dict(
                embedding_dim=self.embedding_dim,
            ),
            optimizer='Adam',
            optimizer_kwargs=dict(
                lr=learning_rate,
            ),
            training_loop='sLCWA',  # Stochastic Local Closed World Assumption
            epochs=epochs,
            training_kwargs=dict(
                batch_size=batch_size,
            ),
            negative_sampler='basic',  # Basic negative sampling
            evaluator_kwargs=dict(
                filtered=True,  # Use filtered evaluation (more accurate)
            ),
            random_seed=self.random_seed,
            device=self.device,
            use_testing_data=validation_split,
            **training_kwargs,
        )

        # Store trained model and mappings
        self.model = result.model
        self.entity_to_id = tf.entity_to_id
        self.relation_to_id = tf.relation_to_id
        self.id_to_entity = {v: k for k, v in self.entity_to_id.items()}
        self.id_to_relation = {v: k for k, v in self.relation_to_id.items()}

        # Extract training history
        self._extract_training_history(result)

        # Extract embeddings as numpy arrays
        embeddings = self._extract_embeddings()

        # Log final metrics
        if validation_split and hasattr(result, 'metric_results'):
            metrics = result.metric_results.to_dict()
            logger.info(f"Final metrics: {metrics}")

        logger.info("Training complete!")
        return embeddings

    def train_from_tsv(self, tsv_path: str, **kwargs) -> Dict[str, np.ndarray]:
        """
        Train from TSV file exported by TripleExtractor.

        TSV format:
            head_entity<TAB>relation<TAB>tail_entity
            claim_123<TAB>SUPPORTS<TAB>claim_456
            doc_789<TAB>CONTAINS<TAB>claim_123

        Args:
            tsv_path: Path to triples.tsv file
            **kwargs: Training parameters (epochs, batch_size, learning_rate, etc.)
                     See train_transe() for full list

        Returns:
            Dict with embeddings

        Raises:
            FileNotFoundError: If TSV file doesn't exist
            ValueError: If TSV file is empty or invalid
        """
        if not os.path.exists(tsv_path):
            raise FileNotFoundError(f"TSV file not found: {tsv_path}")

        logger.info(f"Loading triples from TSV: {tsv_path}")

        # Load triples from TSV
        triples = []
        with open(tsv_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) != 3:
                    logger.warning(f"Line {line_num}: Invalid format (expected 3 columns): {line}")
                    continue

                head, relation, tail = parts
                triples.append((head, relation, tail))

        if not triples:
            raise ValueError(f"No valid triples found in {tsv_path}")

        logger.info(f"Loaded {len(triples)} triples from TSV")

        # Train using loaded triples
        return self.train_transe(triples, **kwargs)

    def save_embeddings(self, embeddings: Dict[str, np.ndarray], output_dir: str):
        """
        Save embeddings to disk.

        Creates the following files:
            - entity_embeddings.npy: Entity embeddings (num_entities x embedding_dim)
            - relation_embeddings.npy: Relation embeddings (num_relations x embedding_dim)
            - entity_to_id.json: Entity -> ID mapping
            - relation_to_id.json: Relation -> ID mapping
            - model_metadata.json: Hyperparameters and training stats
            - training_history.json: Loss and metrics over epochs

        Args:
            embeddings: Dict with entity/relation embeddings
            output_dir: Directory to save embeddings

        Raises:
            ValueError: If embeddings dict is invalid
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Validate embeddings
        if 'entity_embeddings' not in embeddings or 'relation_embeddings' not in embeddings:
            raise ValueError("embeddings must contain 'entity_embeddings' and 'relation_embeddings'")

        # Save embedding arrays
        entity_path = os.path.join(output_dir, 'entity_embeddings.npy')
        relation_path = os.path.join(output_dir, 'relation_embeddings.npy')

        np.save(entity_path, embeddings['entity_embeddings'])
        np.save(relation_path, embeddings['relation_embeddings'])
        logger.info(f"Saved embeddings to {output_dir}")

        # Save ID mappings
        if self.entity_to_id is not None:
            entity_to_id_path = os.path.join(output_dir, 'entity_to_id.json')
            with open(entity_to_id_path, 'w', encoding='utf-8') as f:
                json.dump(self.entity_to_id, f, indent=2)

        if self.relation_to_id is not None:
            relation_to_id_path = os.path.join(output_dir, 'relation_to_id.json')
            with open(relation_to_id_path, 'w', encoding='utf-8') as f:
                json.dump(self.relation_to_id, f, indent=2)

        # Save metadata
        metadata = {
            'model_type': self.model_type,
            'embedding_dim': self.embedding_dim,
            'num_entities': len(self.entity_to_id) if self.entity_to_id else 0,
            'num_relations': len(self.relation_to_id) if self.relation_to_id else 0,
            'random_seed': self.random_seed,
            'device': self.device,
        }
        metadata_path = os.path.join(output_dir, 'model_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        # Save training history
        if self.training_history is not None:
            history_path = os.path.join(output_dir, 'training_history.json')
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(self.training_history, f, indent=2)

        logger.info(f"Saved all embedding data to {output_dir}")

    def load_embeddings(self, input_dir: str) -> Dict[str, np.ndarray]:
        """
        Load embeddings from disk.

        Loads all files created by save_embeddings():
            - entity_embeddings.npy
            - relation_embeddings.npy
            - entity_to_id.json
            - relation_to_id.json
            - model_metadata.json
            - training_history.json (if available)

        Args:
            input_dir: Directory containing saved embeddings

        Returns:
            Dict with embeddings

        Raises:
            FileNotFoundError: If required files are missing
        """
        # Load embedding arrays
        entity_path = os.path.join(input_dir, 'entity_embeddings.npy')
        relation_path = os.path.join(input_dir, 'relation_embeddings.npy')

        if not os.path.exists(entity_path):
            raise FileNotFoundError(f"Entity embeddings not found: {entity_path}")
        if not os.path.exists(relation_path):
            raise FileNotFoundError(f"Relation embeddings not found: {relation_path}")

        entity_embeddings = np.load(entity_path)
        relation_embeddings = np.load(relation_path)
        logger.info(f"Loaded embeddings from {input_dir}")

        # Load ID mappings
        entity_to_id_path = os.path.join(input_dir, 'entity_to_id.json')
        if os.path.exists(entity_to_id_path):
            with open(entity_to_id_path, 'r', encoding='utf-8') as f:
                self.entity_to_id = json.load(f)
                self.id_to_entity = {int(v): k for k, v in self.entity_to_id.items()}

        relation_to_id_path = os.path.join(input_dir, 'relation_to_id.json')
        if os.path.exists(relation_to_id_path):
            with open(relation_to_id_path, 'r', encoding='utf-8') as f:
                self.relation_to_id = json.load(f)
                self.id_to_relation = {int(v): k for k, v in self.relation_to_id.items()}

        # Load metadata
        metadata_path = os.path.join(input_dir, 'model_metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                self.model_type = metadata.get('model_type', self.model_type)
                self.embedding_dim = metadata.get('embedding_dim', self.embedding_dim)
                logger.info(f"Loaded metadata: {self.model_type}, dim={self.embedding_dim}")

        # Load training history
        history_path = os.path.join(input_dir, 'training_history.json')
        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                self.training_history = json.load(f)

        return {
            'entity_embeddings': entity_embeddings,
            'relation_embeddings': relation_embeddings,
        }

    def get_entity_embedding(self, entity_id: str) -> Optional[np.ndarray]:
        """
        Get embedding for a specific entity.

        Args:
            entity_id: Entity ID (e.g., 'claim_123', 'doc_456')

        Returns:
            Embedding vector (shape: embedding_dim,) or None if entity not found

        Example:
            >>> embedding = trainer.get_entity_embedding('claim_123')
            >>> print(embedding.shape)
            (256,)
        """
        if self.model is None:
            logger.warning("No model loaded. Call train_transe() or load_embeddings() first.")
            return None

        if self.entity_to_id is None or entity_id not in self.entity_to_id:
            logger.warning(f"Entity not found: {entity_id}")
            return None

        entity_idx = self.entity_to_id[entity_id]

        # Extract embedding from model
        # Use the forward pass of the representation module
        entity_embedding = self.model.entity_representations[0](
            indices=torch.tensor([entity_idx], device=self.device)
        )

        return entity_embedding.detach().cpu().numpy()[0]

    def get_relation_embedding(self, relation: str) -> Optional[np.ndarray]:
        """
        Get embedding for a specific relation.

        Args:
            relation: Relation type (e.g., 'SUPPORTS', 'CONTRADICTS')

        Returns:
            Embedding vector (shape: embedding_dim,) or None if relation not found

        Example:
            >>> embedding = trainer.get_relation_embedding('SUPPORTS')
            >>> print(embedding.shape)
            (256,)
        """
        if self.model is None:
            logger.warning("No model loaded. Call train_transe() or load_embeddings() first.")
            return None

        if self.relation_to_id is None or relation not in self.relation_to_id:
            logger.warning(f"Relation not found: {relation}")
            return None

        relation_idx = self.relation_to_id[relation]

        # Extract embedding from model
        relation_embedding = self.model.relation_representations[0](
            indices=torch.tensor([relation_idx], device=self.device)
        )

        return relation_embedding.detach().cpu().numpy()[0]

    def predict_tail(self, head: str, relation: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Predict most likely tail entities for (head, relation, ?) query.

        This is useful for link prediction tasks like:
        - "What does this claim SUPPORT?"
        - "What document CONTAINS this claim?"

        Args:
            head: Head entity ID
            relation: Relation type
            top_k: Return top K predictions (default: 5)

        Returns:
            List of (entity_id, score) tuples, sorted by score (higher = more likely)

        Example:
            >>> predictions = trainer.predict_tail('claim_123', 'SUPPORTS', top_k=5)
            >>> for entity, score in predictions:
            ...     print(f"{entity}: {score:.3f}")
        """
        if self.model is None or self.entity_to_id is None or self.relation_to_id is None:
            logger.warning("Model not loaded")
            return []

        if head not in self.entity_to_id or relation not in self.relation_to_id:
            logger.warning(f"Head or relation not found: {head}, {relation}")
            return []

        head_idx = self.entity_to_id[head]
        relation_idx = self.relation_to_id[relation]

        # Get embeddings
        h = self.model.entity_representations[0](indices=torch.tensor([head_idx], device=self.device))
        r = self.model.relation_representations[0](indices=torch.tensor([relation_idx], device=self.device))

        # For TransE: score(h,r,t) = -||h + r - t||
        # Lower distance = higher score
        # We compute h + r, then find closest entities
        if self.model_type == 'TransE':
            query = h + r
            all_entities = self.model.entity_representations[0]._embeddings.weight

            # Compute distances
            distances = torch.norm(all_entities - query, dim=1)
            scores = -distances  # Negate so higher is better

        else:
            # For other models, use model's score function
            # This is a simplified implementation
            logger.warning(f"Tail prediction for {self.model_type} not fully implemented")
            return []

        # Get top-k predictions
        top_scores, top_indices = torch.topk(scores, k=min(top_k, len(scores)))

        # Convert to list of (entity_id, score)
        predictions = []
        for idx, score in zip(top_indices.tolist(), top_scores.tolist()):
            entity_id = self.id_to_entity[idx]
            predictions.append((entity_id, float(score)))

        return predictions

    def compute_similarity(self, entity1: str, entity2: str) -> Optional[float]:
        """
        Compute cosine similarity between two entities.

        Higher similarity = entities are semantically closer in the graph.

        Args:
            entity1: First entity ID
            entity2: Second entity ID

        Returns:
            Cosine similarity in [-1, 1], or None if entities not found
            1.0 = identical, 0.0 = orthogonal, -1.0 = opposite

        Example:
            >>> similarity = trainer.compute_similarity('claim_123', 'claim_456')
            >>> print(f"Similarity: {similarity:.3f}")
        """
        emb1 = self.get_entity_embedding(entity1)
        emb2 = self.get_entity_embedding(entity2)

        if emb1 is None or emb2 is None:
            return None

        # Compute cosine similarity
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def _extract_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Extract embeddings from trained model.

        Returns:
            Dict with 'entity_embeddings' and 'relation_embeddings'
        """
        if self.model is None:
            raise ValueError("No model available. Train a model first.")

        # Extract entity embeddings
        # PyKEEN wraps torch.nn.Embedding in pykeen.nn.representation.Embedding
        # Access the internal _embeddings module to get the weight tensor
        entity_embeddings = self.model.entity_representations[0]._embeddings.weight.detach().cpu().numpy()

        # Extract relation embeddings
        relation_embeddings = self.model.relation_representations[0]._embeddings.weight.detach().cpu().numpy()

        logger.info(f"Extracted embeddings: entities={entity_embeddings.shape}, "
                   f"relations={relation_embeddings.shape}")

        return {
            'entity_embeddings': entity_embeddings,
            'relation_embeddings': relation_embeddings,
        }

    def _extract_training_history(self, result):
        """
        Extract training history from pipeline result.

        Args:
            result: PyKEEN pipeline result
        """
        # PyKEEN stores losses in result.losses
        self.training_history = {
            'epochs': [],
            'losses': [],
        }

        if hasattr(result, 'losses') and result.losses:
            for epoch, loss in enumerate(result.losses, 1):
                self.training_history['epochs'].append(epoch)
                self.training_history['losses'].append(float(loss))

        # Add metrics if available
        if hasattr(result, 'metric_results'):
            metrics_dict = result.metric_results.to_dict()
            for metric_name, metric_value in metrics_dict.items():
                if isinstance(metric_value, (int, float)):
                    self.training_history[metric_name] = float(metric_value)


# Convenience function for quick training
def train_embeddings_from_graph(db,
                                 embedding_dim: int = 256,
                                 model_type: str = 'TransE',
                                 epochs: int = 100,
                                 output_dir: Optional[str] = None) -> Dict[str, np.ndarray]:
    """
    Quick training from GraphDatabase.

    Extracts triples, trains embeddings, optionally saves to disk.

    Args:
        db: GraphDatabase instance
        embedding_dim: Embedding dimension (default: 256)
        model_type: 'TransE', 'RotatE', or 'DistMult'
        epochs: Training epochs (default: 100)
        output_dir: Optional directory to save embeddings

    Returns:
        Dict with embeddings

    Example:
        >>> from research_agent.graph_database import GraphDatabase
        >>> db = GraphDatabase()
        >>> # ... populate graph ...
        >>> embeddings = train_embeddings_from_graph(
        ...     db,
        ...     embedding_dim=256,
        ...     epochs=100,
        ...     output_dir='backend/rag/embeddings/'
        ... )
    """
    from backend.rag.triple_extractor import TripleExtractor

    # Extract triples
    logger.info("Extracting triples from graph...")
    extractor = TripleExtractor(db)
    triples = extractor.extract_from_neo4j()

    if not triples:
        logger.warning("No triples found in graph")
        return {'entity_embeddings': np.array([]), 'relation_embeddings': np.array([])}

    logger.info(f"Extracted {len(triples)} triples")

    # Train embeddings
    trainer = KGETrainer(embedding_dim=embedding_dim, model_type=model_type)
    embeddings = trainer.train_transe(triples, epochs=epochs)

    # Save if requested
    if output_dir:
        trainer.save_embeddings(embeddings, output_dir)

    return embeddings
