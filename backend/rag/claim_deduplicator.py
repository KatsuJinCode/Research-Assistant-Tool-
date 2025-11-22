"""
Claim Deduplicator

Implements intelligent claim deduplication and linking based on semantic similarity.

Handles three scenarios:
1. High similarity (≥95%): Link existing claim to new document (no new node)
2. Medium similarity (75-95%): Create new claim with SIMILAR_TO relationship
3. Low similarity (<75%): Create independent new claim
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from backend.database.neo4j_client import Neo4jClient
from backend.rag.semantic_similarity import SemanticSimilarity, SimilarityResult
from backend.rag.config import get_rag_config

logger = logging.getLogger(__name__)


@dataclass
class ClaimDeduplicationResult:
    """Result of claim deduplication check."""
    action: str  # 'link_existing', 'create_with_similar', or 'create_new'
    existing_claim_id: Optional[str] = None
    existing_claim_text: Optional[str] = None
    similarity_score: Optional[float] = None
    similar_claims: Optional[List[SimilarityResult]] = None


class ClaimDeduplicator:
    """
    Intelligent claim deduplication using semantic similarity.

    Prevents duplicate claims by:
    - Linking high-similarity claims to existing nodes
    - Creating SIMILAR_TO relationships for medium-similarity claims
    - Creating independent nodes for genuinely new claims
    """

    def __init__(self):
        """Initialize claim deduplicator."""
        self.neo4j_client = Neo4jClient()
        self.similarity_engine = SemanticSimilarity()
        self.config = get_rag_config()

    def check_claim_duplication(
        self,
        claim_text: str,
        document_id: str,
        min_confidence: Optional[float] = None
    ) -> ClaimDeduplicationResult:
        """
        Check if a claim should be deduplicated.

        Args:
            claim_text: Text of the new claim
            document_id: ID of the document being processed
            min_confidence: Minimum confidence threshold for linking

        Returns:
            ClaimDeduplicationResult with recommended action
        """
        # Get all existing claims from active database
        existing_claims = self._get_existing_claims()

        if not existing_claims:
            return ClaimDeduplicationResult(action='create_new')

        # Find similar claims
        thresholds = self.config.thresholds
        similar_claims = self.similarity_engine.find_similar(
            query_text=claim_text,
            candidates=existing_claims,
            threshold=thresholds.related_threshold,  # Get all related claims
            limit=10
        )

        if not similar_claims:
            return ClaimDeduplicationResult(action='create_new')

        # Get the most similar claim
        top_match = similar_claims[0]

        # Check confidence threshold if specified
        min_conf = min_confidence or thresholds.min_confidence_for_linking
        if top_match.confidence and top_match.confidence < min_conf:
            logger.info(
                f"Top match has low confidence ({top_match.confidence:.2f}), "
                f"creating new claim"
            )
            return ClaimDeduplicationResult(action='create_new')

        # Determine action based on similarity score
        if thresholds.should_link_existing(top_match.similarity_score):
            # High similarity: Link to existing claim
            logger.info(
                f"High similarity ({top_match.similarity_score:.2f}) - "
                f"will link to existing claim: {top_match.claim_id}"
            )
            return ClaimDeduplicationResult(
                action='link_existing',
                existing_claim_id=top_match.claim_id,
                existing_claim_text=top_match.claim_text,
                similarity_score=top_match.similarity_score
            )

        elif thresholds.should_create_similar_relationship(top_match.similarity_score):
            # Medium similarity: Create new claim with SIMILAR_TO relationships
            logger.info(
                f"Medium similarity ({top_match.similarity_score:.2f}) - "
                f"will create new claim with SIMILAR_TO relationship"
            )
            # Filter for claims in the similar range
            similar_in_range = [
                sc for sc in similar_claims
                if thresholds.should_create_similar_relationship(sc.similarity_score)
            ]
            return ClaimDeduplicationResult(
                action='create_with_similar',
                similar_claims=similar_in_range
            )

        else:
            # Low similarity: Create independent claim
            logger.info(
                f"Low similarity ({top_match.similarity_score:.2f}) - "
                f"creating independent claim"
            )
            return ClaimDeduplicationResult(action='create_new')

    def link_claim_to_document(
        self,
        claim_id: str,
        document_id: str,
        quote: str,
        page_number: Optional[int] = None,
        confidence: Optional[float] = None
    ) -> bool:
        """
        Link an existing claim to a new document.

        This is used for high-similarity matches where we don't create a new
        claim node, but instead connect the existing claim to the new document.

        Args:
            claim_id: ID of the existing claim to link
            document_id: ID of the new document
            quote: Quote from the new document supporting this claim
            page_number: Optional page number in the document
            confidence: Optional confidence score for this extraction

        Returns:
            True if successful, False otherwise
        """
        query = """
        MATCH (c:Claim {id: $claim_id})
        MATCH (d:Document {id: $document_id})

        // Create EXTRACTED relationship from document to claim
        MERGE (d)-[r:EXTRACTED]->(c)
        SET r.quote = $quote,
            r.page_number = $page_number,
            r.confidence = $confidence,
            r.linked_at = datetime()

        // Create Evidence node for this quote
        CREATE (e:Evidence {
            id: randomUUID(),
            text: $quote,
            page_number: $page_number,
            created_at: datetime()
        })

        // Link evidence to document and claim
        CREATE (d)-[:CONTAINS]->(e)
        CREATE (c)-[:SUPPORTED_BY]->(e)

        RETURN c.id as claim_id, e.id as evidence_id
        """

        try:
            with self.neo4j_client.get_session() as session:
                result = session.run(
                    query,
                    {
                        'claim_id': claim_id,
                        'document_id': document_id,
                        'quote': quote,
                        'page_number': page_number,
                        'confidence': confidence
                    }
                )
                record = result.single()

                if record:
                    logger.info(
                        f"Linked existing claim {claim_id} to document {document_id}, "
                        f"created evidence {record['evidence_id']}"
                    )
                    return True
                else:
                    logger.error("Failed to link claim to document")
                    return False

        except Exception as e:
            logger.error(f"Error linking claim to document: {e}")
            return False

    def create_claim_with_similar_relationships(
        self,
        claim_text: str,
        document_id: str,
        similar_claims: List[SimilarityResult],
        quote: str,
        page_number: Optional[int] = None,
        confidence: Optional[float] = None,
        created_by: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a new claim and establish SIMILAR_TO relationships.

        This is used for medium-similarity matches where we create a distinct
        claim node but link it to similar existing claims.

        Args:
            claim_text: Text of the new claim
            document_id: ID of the document
            similar_claims: List of similar existing claims
            quote: Quote from document
            page_number: Optional page number
            confidence: Optional confidence score
            created_by: Optional agent/user who created this

        Returns:
            ID of the created claim, or None if failed
        """
        import uuid

        claim_id = str(uuid.uuid4())

        query = """
        MATCH (d:Document {id: $document_id})

        // Create new claim node
        CREATE (c:Claim {
            id: $claim_id,
            text: $claim_text,
            confidence: $confidence,
            created_by: $created_by,
            created_at: datetime()
        })

        // Link to document
        CREATE (d)-[r:EXTRACTED]->(c)
        SET r.quote = $quote,
            r.page_number = $page_number,
            r.confidence = $confidence

        // Create evidence
        CREATE (e:Evidence {
            id: randomUUID(),
            text: $quote,
            page_number: $page_number,
            created_at: datetime()
        })
        CREATE (d)-[:CONTAINS]->(e)
        CREATE (c)-[:SUPPORTED_BY]->(e)

        RETURN c.id as claim_id, e.id as evidence_id
        """

        try:
            # Create the new claim
            with self.neo4j_client.get_session() as session:
                result = session.run(
                    query,
                    {
                        'claim_id': claim_id,
                        'document_id': document_id,
                        'claim_text': claim_text,
                        'quote': quote,
                        'page_number': page_number,
                        'confidence': confidence,
                        'created_by': created_by
                    }
                )
                record = result.single()

                if not record:
                    logger.error("Failed to create claim")
                    return None

            # Create SIMILAR_TO relationships
            for similar_claim in similar_claims:
                self._create_similar_relationship(
                    claim_id,
                    similar_claim.claim_id,
                    similar_claim.similarity_score
                )

            logger.info(
                f"Created claim {claim_id} with {len(similar_claims)} "
                f"SIMILAR_TO relationships"
            )
            return claim_id

        except Exception as e:
            logger.error(f"Error creating claim with similar relationships: {e}")
            return None

    def _create_similar_relationship(
        self,
        claim_id1: str,
        claim_id2: str,
        similarity_score: float
    ) -> bool:
        """
        Create bidirectional SIMILAR_TO relationship between claims.

        Args:
            claim_id1: First claim ID
            claim_id2: Second claim ID
            similarity_score: Similarity score (0-1)

        Returns:
            True if successful
        """
        query = """
        MATCH (c1:Claim {id: $claim_id1})
        MATCH (c2:Claim {id: $claim_id2})

        // Create bidirectional SIMILAR_TO relationships
        MERGE (c1)-[r1:SIMILAR_TO]->(c2)
        SET r1.similarity_score = $similarity_score,
            r1.created_at = datetime()

        MERGE (c2)-[r2:SIMILAR_TO]->(c1)
        SET r2.similarity_score = $similarity_score,
            r2.created_at = datetime()

        RETURN c1.id, c2.id
        """

        try:
            with self.neo4j_client.get_session() as session:
                result = session.run(
                    query,
                    {
                        'claim_id1': claim_id1,
                        'claim_id2': claim_id2,
                        'similarity_score': similarity_score
                    }
                )
                record = result.single()
                return record is not None

        except Exception as e:
            logger.error(f"Error creating SIMILAR_TO relationship: {e}")
            return False

    def _get_existing_claims(self) -> List[Dict]:
        """
        Get all existing claims from active database.

        Returns:
            List of claim dicts with 'id', 'text', 'confidence'
        """
        query = """
        MATCH (c:Claim)
        RETURN c.id as id,
               c.text as text,
               c.confidence as confidence
        LIMIT 1000
        """

        try:
            with self.neo4j_client.get_session() as session:
                result = session.run(query)
                claims = [
                    {
                        'id': record['id'],
                        'text': record['text'],
                        'confidence': record.get('confidence', 0.5)
                    }
                    for record in result
                ]
                return claims

        except Exception as e:
            logger.error(f"Error getting existing claims: {e}")
            return []

    def get_similar_claims_for_ui(self, claim_id: str) -> List[Dict]:
        """
        Get all claims with SIMILAR_TO relationships for UI highlighting.

        Args:
            claim_id: ID of the claim

        Returns:
            List of similar claim dicts with similarity scores
        """
        query = """
        MATCH (c:Claim {id: $claim_id})-[r:SIMILAR_TO]->(similar:Claim)
        RETURN similar.id as id,
               similar.text as text,
               similar.confidence as confidence,
               r.similarity_score as similarity_score
        ORDER BY r.similarity_score DESC
        """

        try:
            with self.neo4j_client.get_session() as session:
                result = session.run(query, {'claim_id': claim_id})
                similar_claims = [
                    {
                        'id': record['id'],
                        'text': record['text'],
                        'confidence': record.get('confidence', 0.5),
                        'similarity_score': record['similarity_score']
                    }
                    for record in result
                ]
                return similar_claims

        except Exception as e:
            logger.error(f"Error getting similar claims for UI: {e}")
            return []
