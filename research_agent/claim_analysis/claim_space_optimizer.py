"""
Claim Space Optimizer - Rigorous Mathematical Approach

This module finds the optimal representation of a claim space by:
1. Analyzing semantic relationships between all claims using embeddings
2. Identifying subsumption (when one claim fully contains another)
3. Detecting redundancy (claims that convey identical information)
4. Finding hierarchical parent-child relationships
5. Computing minimal spanning set that covers entire claim space

Uses information-theoretic principles and semantic embeddings to ensure:
- No duplication
- Maximum coverage
- Minimal redundancy
- Natural hierarchy based on meaning, not just tokens
"""

import re
import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

# Semantic embedding support
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("WARNING: sentence-transformers not available. Install with: pip install sentence-transformers scikit-learn")
    print("Falling back to token-based similarity only.")


class RelationType(Enum):
    """Semantic relationship types between claims."""
    IDENTICAL = "identical"           # Same information (merge)
    SUBSUMES = "subsumes"             # A contains all info in B (B is redundant)
    SUBSUMED_BY = "subsumed_by"       # B contains all info in A (A is redundant)
    SUPPORTS = "supports"             # A provides evidence for B
    CONTRADICTS = "contradicts"       # A and B are incompatible
    REFINES = "refines"               # A is more specific version of B
    GENERALIZES = "generalizes"       # A is more general version of B
    OVERLAPS = "overlaps"             # Partial information overlap
    INDEPENDENT = "independent"       # No semantic relationship


@dataclass
class ClaimNode:
    """Represents a claim in the semantic space."""
    id: str
    text: str
    tokens: Set[str]
    length: int
    embedding: Optional[np.ndarray] = None  # Semantic embedding vector
    specificity_score: float = 0.0
    information_content: float = 0.0
    is_redundant: bool = False
    subsumed_by: Optional[str] = None
    parent_claims: List[str] = field(default_factory=list)
    child_claims: List[str] = field(default_factory=list)


class ClaimSpaceOptimizer:
    """
    Finds optimal representation of claim space using rigorous analysis.

    This is NOT a simple clustering algorithm. This performs:
    - Semantic analysis of claim relationships using embeddings
    - Information-theoretic redundancy detection
    - Hierarchical structure discovery
    - Optimal spanning set computation
    """

    def __init__(self, use_embeddings: bool = True, model_name: str = 'all-mpnet-base-v2'):
        """
        Initialize optimizer.

        Args:
            use_embeddings: Whether to use semantic embeddings (requires sentence-transformers)
            model_name: Name of sentence-transformer model to use
                        Options:
                        - 'all-MiniLM-L6-v2': Fastest, 384 dims
                        - 'all-mpnet-base-v2': Best quality, 768 dims (default)
                        - 'multi-qa-mpnet-base-dot-v1': Optimized for Q&A similarity
        """
        self.claims: Dict[str, ClaimNode] = {}
        self.relationships: Dict[Tuple[str, str], RelationType] = {}
        self.use_embeddings = use_embeddings and EMBEDDINGS_AVAILABLE
        self.embedding_model = None

        if self.use_embeddings:
            print(f"Loading semantic embedding model: {model_name}...")
            try:
                self.embedding_model = SentenceTransformer(model_name)
                print(f"  Model loaded: {model_name}")
                print(f"  Embedding dimensions: {self.embedding_model.get_sentence_embedding_dimension()}")
            except Exception as e:
                print(f"WARNING: Failed to load embedding model: {e}")
                print("Falling back to token-based similarity")
                self.use_embeddings = False

    def add_claim(self, claim_id: str, text: str):
        """Add a claim to the analysis space."""
        tokens = self._tokenize(text)

        # Generate embedding if using semantic embeddings
        embedding = None
        if self.use_embeddings and self.embedding_model:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)

        node = ClaimNode(
            id=claim_id,
            text=text,
            tokens=tokens,
            length=len(text),
            embedding=embedding
        )
        self.claims[claim_id] = node

    def _tokenize(self, text: str) -> Set[str]:
        """
        Convert text to normalized token set.

        Removes stopwords but preserves qualifiers (critical requirement).
        """
        # Lowercase and remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)

        # Split into words
        words = text.split()

        # Critical: PRESERVE qualifiers (can, may, might, all, some, etc.)
        qualifiers = {
            'can', 'may', 'might', 'could', 'should', 'must', 'will',
            'all', 'some', 'most', 'many', 'few', 'always', 'never',
            'sometimes', 'often', 'rarely', 'possibly', 'probably',
            'likely', 'unlikely', 'certain', 'uncertain'
        }

        # Remove common stopwords but NOT qualifiers
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are',
            'was', 'were', 'been', 'be', 'have', 'has', 'had',
            'do', 'does', 'did'
        } - qualifiers  # Exclude qualifiers from stopwords

        tokens = {w for w in words if w not in stopwords and len(w) > 2}

        return tokens

    def calculate_semantic_similarity(self, claim1_id: str, claim2_id: str) -> float:
        """
        Calculate semantic similarity between two claims.

        Uses semantic embeddings if available, otherwise falls back to token-based Jaccard similarity.

        Returns:
            Similarity score between 0.0 and 1.0
        """
        node1 = self.claims[claim1_id]
        node2 = self.claims[claim2_id]

        # Use semantic embeddings if available
        if self.use_embeddings and node1.embedding is not None and node2.embedding is not None:
            # Cosine similarity between embeddings
            # Reshape for sklearn: (1, n_features)
            emb1 = node1.embedding.reshape(1, -1)
            emb2 = node2.embedding.reshape(1, -1)

            similarity = cosine_similarity(emb1, emb2)[0][0]

            # Cosine similarity ranges from -1 to 1, normalize to 0 to 1
            normalized = (similarity + 1) / 2

            return normalized

        # Fall back to token-based Jaccard similarity
        tokens1 = node1.tokens
        tokens2 = node2.tokens

        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)

        return intersection / union if union > 0 else 0.0

    def detect_subsumption(self, claim1_id: str, claim2_id: str) -> Optional[RelationType]:
        """
        Detect if one claim subsumes another.

        Claim A subsumes Claim B if:
        - All information in B is contained in A
        - A may contain additional information
        - B can be safely removed without information loss

        Returns:
            SUBSUMES if claim1 subsumes claim2
            SUBSUMED_BY if claim2 subsumes claim1
            None if neither subsumes the other
        """
        node1 = self.claims[claim1_id]
        node2 = self.claims[claim2_id]

        tokens1 = node1.tokens
        tokens2 = node2.tokens

        # Check if all tokens in claim2 are in claim1
        if tokens2.issubset(tokens1):
            # claim1 subsumes claim2
            return RelationType.SUBSUMES

        # Check if all tokens in claim1 are in claim2
        if tokens1.issubset(tokens2):
            # claim2 subsumes claim1
            return RelationType.SUBSUMED_BY

        return None

    def calculate_specificity(self, claim_id: str) -> float:
        """
        Calculate how specific (vs general) a claim is.

        More specific claims:
        - Have more tokens
        - Have more rare/unique tokens
        - Have more qualifiers and constraints

        Returns:
            Specificity score (higher = more specific)
        """
        node = self.claims[claim_id]

        # Factor 1: Length (longer = more specific)
        length_score = len(node.tokens)

        # Factor 2: Rarity of tokens (rare tokens = more specific)
        # Count how many other claims share each token
        token_frequencies = defaultdict(int)
        for other_node in self.claims.values():
            for token in other_node.tokens:
                token_frequencies[token] += 1

        # Average rarity (inverse frequency)
        rarity_scores = []
        for token in node.tokens:
            freq = token_frequencies[token]
            rarity = 1.0 / freq if freq > 0 else 0.0
            rarity_scores.append(rarity)

        avg_rarity = np.mean(rarity_scores) if rarity_scores else 0.0

        # Factor 3: Number of qualifiers (more qualifiers = more specific)
        qualifiers = {
            'can', 'may', 'might', 'could', 'should', 'must', 'will',
            'all', 'some', 'most', 'many', 'few', 'always', 'never',
            'sometimes', 'often', 'rarely', 'possibly', 'probably'
        }
        qualifier_count = len(node.tokens & qualifiers)

        # Combine factors
        specificity = (
            0.4 * (length_score / 20.0) +  # Normalized by typical length
            0.4 * avg_rarity +
            0.2 * (qualifier_count / 3.0)  # Normalized by typical qualifier count
        )

        return specificity

    def calculate_information_content(self, claim_id: str) -> float:
        """
        Calculate information content (uniqueness) of a claim.

        Higher information content means the claim adds unique knowledge
        not available in other claims.

        Returns:
            Information content score
        """
        node = self.claims[claim_id]

        # Count unique tokens (tokens not in many other claims)
        unique_token_count = 0
        for token in node.tokens:
            # Count how many other claims have this token
            other_count = sum(
                1 for other_id, other_node in self.claims.items()
                if other_id != claim_id and token in other_node.tokens
            )

            # If token is rare (in < 20% of claims), count as unique
            if other_count < len(self.claims) * 0.2:
                unique_token_count += 1

        # Information content = ratio of unique tokens
        total_tokens = len(node.tokens)
        info_content = unique_token_count / total_tokens if total_tokens > 0 else 0.0

        return info_content

    def analyze_all_relationships(self):
        """
        Analyze relationships between all claim pairs.

        Determines:
        - Which claims are identical/redundant
        - Which claims subsume others
        - Which claims have parent-child relationships
        - Which claims are independent
        """
        claim_ids = list(self.claims.keys())

        for i, claim1_id in enumerate(claim_ids):
            for claim2_id in claim_ids[i+1:]:
                similarity = self.calculate_semantic_similarity(claim1_id, claim2_id)

                # Identical claims (>95% similarity)
                if similarity > 0.95:
                    self.relationships[(claim1_id, claim2_id)] = RelationType.IDENTICAL
                    # Mark second claim as redundant (keep first one)
                    self.claims[claim2_id].is_redundant = True
                    self.claims[claim2_id].subsumed_by = claim1_id
                    continue

                # Check subsumption
                subsumption = self.detect_subsumption(claim1_id, claim2_id)
                if subsumption:
                    self.relationships[(claim1_id, claim2_id)] = subsumption

                    # Mark subsumed claim as redundant
                    if subsumption == RelationType.SUBSUMES:
                        self.claims[claim2_id].is_redundant = True
                        self.claims[claim2_id].subsumed_by = claim1_id
                    elif subsumption == RelationType.SUBSUMED_BY:
                        self.claims[claim1_id].is_redundant = True
                        self.claims[claim1_id].subsumed_by = claim2_id
                    continue

                # High similarity but no subsumption = overlaps or refines
                if similarity > 0.7:
                    # Check if one is more specific (refinement)
                    spec1 = self.calculate_specificity(claim1_id)
                    spec2 = self.calculate_specificity(claim2_id)

                    if spec1 > spec2 * 1.3:  # claim1 significantly more specific
                        self.relationships[(claim1_id, claim2_id)] = RelationType.REFINES
                        # claim1 is child of claim2
                        self.claims[claim1_id].parent_claims.append(claim2_id)
                        self.claims[claim2_id].child_claims.append(claim1_id)
                    elif spec2 > spec1 * 1.3:  # claim2 significantly more specific
                        self.relationships[(claim1_id, claim2_id)] = RelationType.GENERALIZES
                        # claim2 is child of claim1
                        self.claims[claim2_id].parent_claims.append(claim1_id)
                        self.claims[claim1_id].child_claims.append(claim2_id)
                    else:
                        self.relationships[(claim1_id, claim2_id)] = RelationType.OVERLAPS
                    continue

                # Moderate similarity = supports
                if similarity > 0.3:
                    self.relationships[(claim1_id, claim2_id)] = RelationType.SUPPORTS
                    continue

                # Low similarity = independent
                self.relationships[(claim1_id, claim2_id)] = RelationType.INDEPENDENT

    def compute_optimal_spanning_set(self) -> Set[str]:
        """
        Compute minimal set of claims that span the entire claim space.

        This is the CORE optimization:
        - Remove all redundant claims (subsumed by others)
        - Keep all claims with unique information
        - Keep minimal set that maintains full coverage

        Returns:
            Set of claim IDs that form optimal representation
        """
        # Start with all claims
        candidates = set(self.claims.keys())

        # Remove redundant claims (subsumed by others)
        non_redundant = {
            claim_id for claim_id, node in self.claims.items()
            if not node.is_redundant
        }

        # From non-redundant claims, keep those with high information content
        # (claims that add unique knowledge)
        optimal_set = set()

        for claim_id in non_redundant:
            node = self.claims[claim_id]

            # Keep if:
            # 1. High information content (>30% unique tokens)
            # 2. Has child claims (is a parent node in hierarchy)
            # 3. No parent claims (is a root node)

            if (node.information_content > 0.3 or
                len(node.child_claims) > 0 or
                len(node.parent_claims) == 0):
                optimal_set.add(claim_id)

        return optimal_set

    def build_hierarchy(self) -> Dict[str, List[str]]:
        """
        Build hierarchical tree structure from optimal claim set.

        Returns:
            Dict mapping parent_claim_id -> [child_claim_ids]
        """
        hierarchy = defaultdict(list)

        for claim_id, node in self.claims.items():
            if node.is_redundant:
                continue

            for parent_id in node.parent_claims:
                if not self.claims[parent_id].is_redundant:
                    hierarchy[parent_id].append(claim_id)

        return dict(hierarchy)

    def optimize(self) -> Dict[str, any]:
        """
        Run complete optimization pipeline.

        Returns:
            Optimization results including:
            - optimal_claims: Set of claim IDs to keep
            - redundant_claims: Claims that can be removed
            - hierarchy: Parent-child relationships
            - statistics: Analysis statistics
        """
        print("\n=== CLAIM SPACE OPTIMIZATION ===\n")

        # Step 1: Calculate metrics for all claims
        print("Step 1: Analyzing claim metrics...")
        for claim_id in self.claims.keys():
            node = self.claims[claim_id]
            node.specificity_score = self.calculate_specificity(claim_id)
            node.information_content = self.calculate_information_content(claim_id)

        # Step 2: Analyze all relationships
        print("Step 2: Analyzing semantic relationships...")
        self.analyze_all_relationships()

        # Step 3: Compute optimal spanning set
        print("Step 3: Computing optimal claim set...")
        optimal_claims = self.compute_optimal_spanning_set()

        # Step 4: Build hierarchy
        print("Step 4: Building hierarchical structure...")
        hierarchy = self.build_hierarchy()

        # Step 5: Collect results
        redundant_claims = {
            claim_id for claim_id, node in self.claims.items()
            if node.is_redundant
        }

        # Statistics
        relationship_counts = defaultdict(int)
        for rel_type in self.relationships.values():
            relationship_counts[rel_type.value] += 1

        stats = {
            'total_claims': len(self.claims),
            'optimal_claims': len(optimal_claims),
            'redundant_claims': len(redundant_claims),
            'reduction_ratio': len(optimal_claims) / len(self.claims),
            'relationship_distribution': dict(relationship_counts),
            'hierarchy_depth': self._calculate_hierarchy_depth(hierarchy),
            'avg_specificity': np.mean([n.specificity_score for n in self.claims.values()]),
            'avg_information_content': np.mean([n.information_content for n in self.claims.values()])
        }

        print(f"\nOptimization complete!")
        print(f"  Original claims: {stats['total_claims']}")
        print(f"  Optimal claims: {stats['optimal_claims']}")
        print(f"  Redundant claims: {stats['redundant_claims']}")
        print(f"  Reduction: {(1 - stats['reduction_ratio']) * 100:.1f}%")

        return {
            'optimal_claims': optimal_claims,
            'redundant_claims': redundant_claims,
            'hierarchy': hierarchy,
            'statistics': stats,
            'claim_nodes': self.claims,
            'relationships': self.relationships
        }

    def _calculate_hierarchy_depth(self, hierarchy: Dict[str, List[str]]) -> int:
        """Calculate maximum depth of hierarchy tree."""
        if not hierarchy:
            return 0

        def get_depth(claim_id, visited=None):
            if visited is None:
                visited = set()
            if claim_id in visited:
                return 0
            visited.add(claim_id)

            children = hierarchy.get(claim_id, [])
            if not children:
                return 1
            return 1 + max(get_depth(child, visited) for child in children)

        # Find root nodes (claims with no parents)
        all_children = set()
        for children in hierarchy.values():
            all_children.update(children)
        roots = set(hierarchy.keys()) - all_children

        if not roots:
            return 1

        return max(get_depth(root) for root in roots)
