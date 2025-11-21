"""
Cross-Document MECE Clustering Orchestrator

This module orchestrates the complete cross-document MECE clustering pipeline:
1. Fetch claims from multiple documents
2. Use Leiden algorithm to find natural communities
3. Generate super-claims for each community
4. Store MECE relationships in Neo4j

This replaces arbitrary similarity thresholds with mathematically optimal partitions.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import required modules
try:
    from research_agent.claim_analysis.graph_mece_clusterer import GraphMECEClusterer, check_leiden_availability
    from backend.database.repositories import ClaimRepository, DocumentRepository
    MECE_AVAILABLE = True
except ImportError as e:
    MECE_AVAILABLE = False
    logger.warning(f"MECE clustering not available: {e}")


@dataclass
class SuperClaim:
    """A super-claim generated from a community of similar claims."""
    id: str
    text: str
    description: str
    community_id: int
    member_claim_ids: List[str]
    modularity_contribution: float
    internal_density: float


class CrossDocumentMECEOrchestrator:
    """
    Orchestrates cross-document MECE clustering using Leiden algorithm.

    Workflow:
    1. Fetch all claims across documents
    2. Run Leiden community detection
    3. Generate super-claims for each community
    4. Create MECE relationships in Neo4j
    """

    def __init__(self):
        """Initialize orchestrator."""
        if not MECE_AVAILABLE:
            raise ImportError(
                "MECE clustering dependencies not available. "
                "Install: pip install leidenalg python-igraph sentence-transformers"
            )

        self.clusterer = GraphMECEClusterer(model_name='all-mpnet-base-v2')
        self.claim_repo = ClaimRepository()
        self.doc_repo = DocumentRepository()
        logger.info("Cross-document MECE orchestrator initialized")

    async def cluster_all_claims(
        self,
        similarity_threshold: float = 0.5,
        min_cluster_size: int = 2
    ) -> Dict[str, Any]:
        """
        Cluster all claims across all documents using Leiden algorithm.

        Args:
            similarity_threshold: Minimum similarity to create edge (default: 0.5)
            min_cluster_size: Minimum claims per cluster

        Returns:
            {
                'super_claims': List[SuperClaim],
                'clusters': List[GraphClusterResult],
                'metrics': Dict[str, Any],
                'stats': Dict[str, int]
            }
        """
        logger.info("Starting cross-document MECE clustering...")

        # 1. Fetch all claims from database
        logger.info("  [1/4] Fetching claims from database...")
        all_claims = await self._fetch_all_claims()

        if len(all_claims) < min_cluster_size:
            logger.warning(f"Not enough claims for clustering ({len(all_claims)} < {min_cluster_size})")
            return {
                'super_claims': [],
                'clusters': [],
                'metrics': {},
                'stats': {'total_claims': len(all_claims), 'clusters': 0}
            }

        logger.info(f"  Fetched {len(all_claims)} claims from database")

        # 2. Run Leiden clustering
        logger.info("  [2/4] Running Leiden community detection...")
        clusters, metrics = self.clusterer.cluster_claims(
            all_claims,
            similarity_threshold=similarity_threshold,
            min_cluster_size=min_cluster_size
        )

        logger.info(f"  Found {len(clusters)} communities (modularity: {metrics['modularity']:.3f})")

        # 3. Generate super-claims
        logger.info("  [3/4] Generating super-claims from communities...")
        super_claims = await self._generate_super_claims(clusters)

        logger.info(f"  Generated {len(super_claims)} super-claims")

        # 4. Store MECE relationships
        logger.info("  [4/4] Storing MECE relationships in Neo4j...")
        await self._store_mece_relationships(super_claims)

        logger.info("✓ Cross-document MECE clustering complete!")

        return {
            'super_claims': super_claims,
            'clusters': clusters,
            'metrics': metrics,
            'stats': {
                'total_claims': len(all_claims),
                'clusters': len(clusters),
                'super_claims': len(super_claims),
                'avg_cluster_size': metrics['avg_cluster_size'],
                'modularity': metrics['modularity']
            }
        }

    async def _fetch_all_claims(self) -> List[Dict[str, Any]]:
        """Fetch all claims from database."""
        # Get all documents (repositories are sync, not async)
        documents = self.doc_repo.find_all_documents()

        all_claims = []
        for doc in documents:
            # Get claims for this document
            claims = self.claim_repo.find_claims_by_document(doc['id'])

            for claim in claims:
                all_claims.append({
                    'id': claim['id'],
                    'text': claim['text'],
                    'document_id': doc['id'],
                    'document_title': doc.get('title', 'Unknown'),
                    'type': claim.get('claim_type', 'unknown'),
                    'confidence': claim.get('confidence', 0.5)
                })

        return all_claims

    async def _generate_super_claims(
        self,
        clusters: List[Any]
    ) -> List[SuperClaim]:
        """
        Generate super-claims for each community using LLM.

        For each cluster:
        1. Extract all member claims
        2. Use LLM to synthesize a super-claim
        3. Create SuperClaim object with metadata
        """
        super_claims = []

        for cluster in clusters:
            # Get all claim texts from this cluster
            claim_texts = [c['text'] for c in cluster.claims]
            claim_ids = [c['id'] for c in cluster.claims]

            # Generate super-claim text using LLM
            super_claim_text = await self._synthesize_super_claim(claim_texts)

            # Create description
            source_docs = set(c.get('document_title', 'Unknown') for c in cluster.claims)
            description = f"Community {cluster.cluster_id}: {len(claim_texts)} claims from {len(source_docs)} documents"

            super_claim = SuperClaim(
                id=f"super_claim_{cluster.cluster_id}",
                text=super_claim_text,
                description=description,
                community_id=cluster.cluster_id,
                member_claim_ids=claim_ids,
                modularity_contribution=cluster.modularity_contribution,
                internal_density=cluster.internal_density
            )

            super_claims.append(super_claim)

        return super_claims

    async def _synthesize_super_claim(
        self,
        claim_texts: List[str]
    ) -> str:
        """
        Synthesize a super-claim from a list of similar claims using LLM.

        Args:
            claim_texts: List of claim texts in this community

        Returns:
            Synthesized super-claim text
        """
        # Use the most representative claim as the super-claim
        # (For now - could be enhanced with LLM synthesis later)

        if len(claim_texts) == 1:
            return claim_texts[0]

        # Find the longest claim as it likely has the most information
        longest_claim = max(claim_texts, key=len)

        # Could enhance this with LLM synthesis:
        # prompt = f"Synthesize a single claim that captures the essence of these related claims:\n\n"
        # for i, claim in enumerate(claim_texts, 1):
        #     prompt += f"{i}. {claim}\n"
        # super_claim = await llm.generate(prompt)

        return longest_claim

    async def _store_mece_relationships(
        self,
        super_claims: List[SuperClaim]
    ) -> None:
        """
        Store MECE relationships in Neo4j.

        Creates relationships:
        - Claim -[IS_INSTANCE_OF]-> SuperClaim
        - SuperClaim -[GENERALIZES]-> Claim
        - SuperClaim -[HAS_MEMBER]-> Claim
        """
        # Note: Repository methods are not async yet, so we call them directly
        for super_claim in super_claims:
            try:
                # Get first member claim to find document
                if not super_claim.member_claim_ids:
                    continue

                first_member = self.claim_repo.get_claim(super_claim.member_claim_ids[0])
                if not first_member:
                    logger.warning(f"Could not find member claim {super_claim.member_claim_ids[0]}")
                    continue

                # Get document ID from first member's relationships
                doc_id = first_member.get('document_id', 'unknown')

                # Store super-claim as a special claim node
                super_claim_id = self.claim_repo.create_claim(
                    text=super_claim.text,
                    original_text=super_claim.text,
                    doc_id=doc_id,
                    claim_type='super_claim',
                    confidence=super_claim.internal_density,
                    status='active',
                    description=super_claim.description,
                    community_id=super_claim.community_id,
                    modularity_contribution=super_claim.modularity_contribution,
                    internal_density=super_claim.internal_density,
                    member_count=len(super_claim.member_claim_ids)
                )

                # Create relationships to member claims
                for member_id in super_claim.member_claim_ids:
                    self.claim_repo.create_relationship(
                        from_id=member_id,
                        to_id=super_claim_id,
                        relationship_type='IS_INSTANCE_OF',
                        properties={
                            'community_id': super_claim.community_id,
                            'relationship_class': 'mece'
                        }
                    )

                logger.info(f"Created super-claim {super_claim_id} with {len(super_claim.member_claim_ids)} members")

            except Exception as e:
                logger.error(f"Error storing super-claim: {e}")
                continue


def check_mece_availability() -> bool:
    """Check if MECE clustering is available."""
    return MECE_AVAILABLE and check_leiden_availability()


async def run_cross_document_clustering(
    similarity_threshold: float = 0.5,
    min_cluster_size: int = 2
) -> Dict[str, Any]:
    """
    Convenience function to run cross-document MECE clustering.

    Args:
        similarity_threshold: Minimum similarity for edge creation
        min_cluster_size: Minimum claims per cluster

    Returns:
        Clustering results with super-claims, metrics, and stats
    """
    orchestrator = CrossDocumentMECEOrchestrator()
    return await orchestrator.cluster_all_claims(
        similarity_threshold=similarity_threshold,
        min_cluster_size=min_cluster_size
    )
