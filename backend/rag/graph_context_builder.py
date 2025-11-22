"""
Graph Context Builder for RAG

Retrieves relevant context from the knowledge graph to enhance agent prompts.
Provides similar claims, document context, and relationship information.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from backend.database.neo4j_client import Neo4jClient
from backend.rag.semantic_similarity import SemanticSimilarity, SimilarityResult

logger = logging.getLogger(__name__)


@dataclass
class ClaimContext:
    """Context for a claim from the graph."""
    claim_id: str
    text: str
    confidence: float
    evidence_count: int
    document_title: Optional[str] = None
    created_by: Optional[str] = None


@dataclass
class DocumentContext:
    """Context for a document from the graph."""
    document_id: str
    title: str
    claim_count: int
    evidence_count: int
    status: str


class GraphContextBuilder:
    """
    Build RAG context from the knowledge graph.

    Retrieves relevant claims, documents, and relationships to provide
    context for agent operations like claim extraction and normalization.
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize graph context builder.

        Args:
            project_id: Optional project ID to scope queries
        """
        self.project_id = project_id
        self.neo4j_client = Neo4jClient()
        self.similarity_engine = SemanticSimilarity()

    def get_similar_claims(
        self,
        claim_text: str,
        limit: int = 5,
        threshold: float = 0.70
    ) -> List[SimilarityResult]:
        """
        Find existing similar claims using semantic search.

        Args:
            claim_text: Text of the claim to find similar claims for
            limit: Maximum number of results
            threshold: Minimum similarity threshold

        Returns:
            List of SimilarityResult objects
        """
        # Query all claims from the active database
        query = """
        MATCH (c:Claim)
        RETURN c.id as id, c.text as text, c.confidence as confidence
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

            # Use semantic similarity to find similar claims
            similar = self.similarity_engine.find_similar(
                query_text=claim_text,
                candidates=claims,
                threshold=threshold,
                limit=limit
            )

            return similar

        except Exception as e:
            logger.error(f"Error finding similar claims: {e}")
            return []

    def get_claim_details(self, claim_id: str) -> Optional[ClaimContext]:
        """
        Get detailed context for a specific claim.

        Args:
            claim_id: ID of the claim

        Returns:
            ClaimContext object or None if not found
        """
        query = """
        MATCH (c:Claim {id: $claim_id})
        OPTIONAL MATCH (c)<-[:EXTRACTED]-(d:Document)
        OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(e:Evidence)
        RETURN c.id as id,
               c.text as text,
               c.confidence as confidence,
               c.created_by as created_by,
               d.title as document_title,
               count(DISTINCT e) as evidence_count
        """

        try:
            with self.neo4j_client.get_session() as session:
                result = session.run(query, {'claim_id': claim_id})
                record = result.single()

                if not record:
                    return None

                return ClaimContext(
                    claim_id=record['id'],
                    text=record['text'],
                    confidence=record.get('confidence', 0.5),
                    evidence_count=record['evidence_count'],
                    document_title=record.get('document_title'),
                    created_by=record.get('created_by')
                )

        except Exception as e:
            logger.error(f"Error getting claim details: {e}")
            return None

    def get_document_context(self, document_id: str) -> Optional[DocumentContext]:
        """
        Get context for a document including claims and evidence.

        Args:
            document_id: ID of the document

        Returns:
            DocumentContext object or None if not found
        """
        query = """
        MATCH (d:Document {id: $document_id})
        OPTIONAL MATCH (d)-[:EXTRACTED]->(c:Claim)
        OPTIONAL MATCH (d)-[:CONTAINS]->(e:Evidence)
        RETURN d.id as id,
               d.title as title,
               d.status as status,
               count(DISTINCT c) as claim_count,
               count(DISTINCT e) as evidence_count
        """

        try:
            with self.neo4j_client.get_session() as session:
                result = session.run(query, {'document_id': document_id})
                record = result.single()

                if not record:
                    return None

                return DocumentContext(
                    document_id=record['id'],
                    title=record['title'],
                    claim_count=record['claim_count'],
                    evidence_count=record['evidence_count'],
                    status=record.get('status', 'unknown')
                )

        except Exception as e:
            logger.error(f"Error getting document context: {e}")
            return None

    def get_claims_from_document(self, document_id: str) -> List[ClaimContext]:
        """
        Get all claims extracted from a specific document.

        Args:
            document_id: ID of the document

        Returns:
            List of ClaimContext objects
        """
        query = """
        MATCH (d:Document {id: $document_id})-[:EXTRACTED]->(c:Claim)
        OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(e:Evidence)
        RETURN c.id as id,
               c.text as text,
               c.confidence as confidence,
               c.created_by as created_by,
               count(DISTINCT e) as evidence_count
        ORDER BY c.created_at DESC
        """

        try:
            with self.neo4j_client.get_session() as session:
                result = session.run(query, {'document_id': document_id})

                claims = []
                for record in result:
                    claims.append(ClaimContext(
                        claim_id=record['id'],
                        text=record['text'],
                        confidence=record.get('confidence', 0.5),
                        evidence_count=record['evidence_count'],
                        created_by=record.get('created_by')
                    ))

                return claims

        except Exception as e:
            logger.error(f"Error getting claims from document: {e}")
            return []

    def get_claim_relationships(self, claim_id: str) -> Dict[str, List[str]]:
        """
        Get all relationships for a claim (supports, contradicts, etc.).

        Args:
            claim_id: ID of the claim

        Returns:
            Dictionary mapping relationship types to lists of related claim IDs
        """
        query = """
        MATCH (c:Claim {id: $claim_id})
        OPTIONAL MATCH (c)-[r:SUPPORTS]->(supported:Claim)
        OPTIONAL MATCH (c)-[r2:CONTRADICTS]->(contradicted:Claim)
        OPTIONAL MATCH (c)-[r3:REFINES]->(refined:Claim)
        RETURN collect(DISTINCT supported.id) as supports,
               collect(DISTINCT contradicted.id) as contradicts,
               collect(DISTINCT refined.id) as refines
        """

        try:
            with self.neo4j_client.get_session() as session:
                result = session.run(query, {'claim_id': claim_id})
                record = result.single()

                if not record:
                    return {}

                relationships = {}
                if record['supports']:
                    relationships['supports'] = [id for id in record['supports'] if id]
                if record['contradicts']:
                    relationships['contradicts'] = [id for id in record['contradicts'] if id]
                if record['refines']:
                    relationships['refines'] = [id for id in record['refines'] if id]

                return relationships

        except Exception as e:
            logger.error(f"Error getting claim relationships: {e}")
            return {}

    def build_extraction_context(
        self,
        document_title: str,
        similar_claims_limit: int = 5
    ) -> str:
        """
        Build RAG context string for claim extraction.

        Args:
            document_title: Title of document being processed
            similar_claims_limit: Number of similar claims to include

        Returns:
            Formatted context string for agent prompt
        """
        context_parts = []

        # Add header
        context_parts.append("=== EXISTING CLAIMS IN KNOWLEDGE GRAPH ===\n")

        # Get all claims (limit to recent ones for performance)
        query = """
        MATCH (c:Claim)
        OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(e:Evidence)
        RETURN c.id as id,
               c.text as text,
               c.confidence as confidence,
               count(DISTINCT e) as evidence_count
        ORDER BY c.created_at DESC
        LIMIT 100
        """

        try:
            with self.neo4j_client.get_session() as session:
                result = session.run(query)

                claims = []
                for record in result:
                    claims.append({
                        'id': record['id'],
                        'text': record['text'],
                        'confidence': record.get('confidence', 0.5),
                        'evidence_count': record['evidence_count']
                    })

                if claims:
                    context_parts.append(f"Found {len(claims)} existing claims in the graph.\n")
                    context_parts.append("Top claims (most recent):\n")

                    for i, claim in enumerate(claims[:similar_claims_limit], 1):
                        context_parts.append(
                            f"\n{i}. [ID: {claim['id']}] \"{claim['text']}\"\n"
                            f"   - Confidence: {claim['confidence']:.2f}\n"
                            f"   - Evidence count: {claim['evidence_count']}\n"
                        )
                else:
                    context_parts.append("No existing claims found in the graph.\n")

        except Exception as e:
            logger.error(f"Error building extraction context: {e}")
            context_parts.append("Error retrieving existing claims.\n")

        context_parts.append("\n=== GUIDELINES ===\n")
        context_parts.append(
            "When extracting claims from the new document:\n"
            "1. Check if similar claims already exist above\n"
            "2. If a claim is very similar to an existing one:\n"
            "   - Use consistent language and terminology\n"
            "   - Reference the existing claim ID in your response\n"
            "   - Indicate the relationship (supports/contradicts/refines)\n"
            "3. If the claim is genuinely new, extract it as a new claim\n"
            "4. Maintain high standards for claim quality and precision\n"
        )

        return ''.join(context_parts)

    def build_normalization_context(
        self,
        raw_claim: str,
        similar_threshold: float = 0.85
    ) -> Tuple[str, List[SimilarityResult]]:
        """
        Build context for claim normalization.

        Args:
            raw_claim: Raw claim text to normalize
            similar_threshold: Similarity threshold for finding similar claims

        Returns:
            Tuple of (context_string, list_of_similar_claims)
        """
        # Find similar existing claims
        similar_claims = self.get_similar_claims(
            claim_text=raw_claim,
            limit=5,
            threshold=similar_threshold
        )

        if not similar_claims:
            return "No similar existing claims found.", []

        # Build context string
        context_parts = []
        context_parts.append("=== SIMILAR EXISTING CLAIMS ===\n")

        for i, similar in enumerate(similar_claims, 1):
            # Get full details
            details = self.get_claim_details(similar.claim_id)

            context_parts.append(
                f"\n{i}. [Similarity: {similar.similarity_score:.2f}] \"{similar.claim_text}\"\n"
            )

            if details:
                context_parts.append(f"   - ID: {details.claim_id}\n")
                context_parts.append(f"   - Confidence: {details.confidence:.2f}\n")
                context_parts.append(f"   - Evidence count: {details.evidence_count}\n")
                if details.document_title:
                    context_parts.append(f"   - Source: {details.document_title}\n")

        context_parts.append("\n=== NORMALIZATION GUIDELINES ===\n")
        context_parts.append(
            "Normalize the raw claim by:\n"
            "1. Using consistent terminology from similar claims above\n"
            "2. Maintaining the original meaning and nuance\n"
            "3. Following the language style of existing claims\n"
            "4. Indicating if this refines/supports/contradicts existing claims\n"
        )

        return ''.join(context_parts), similar_claims

    def get_project_statistics(self) -> Dict[str, int]:
        """
        Get statistics for the current project.

        Returns:
            Dictionary with counts of documents, claims, evidence
        """
        query = """
        MATCH (d:Document)
        OPTIONAL MATCH (c:Claim)
        OPTIONAL MATCH (e:Evidence)
        RETURN count(DISTINCT d) as document_count,
               count(DISTINCT c) as claim_count,
               count(DISTINCT e) as evidence_count
        """

        try:
            with self.neo4j_client.get_session() as session:
                result = session.run(query)
                record = result.single()

                return {
                    'document_count': record['document_count'],
                    'claim_count': record['claim_count'],
                    'evidence_count': record['evidence_count']
                }

        except Exception as e:
            logger.error(f"Error getting project statistics: {e}")
            return {
                'document_count': 0,
                'claim_count': 0,
                'evidence_count': 0
            }
