"""
Claim Repository

Handles all database operations for Claim nodes.
Provides high-level methods for claim CRUD, querying, and relationships.
"""

from typing import Dict, List, Any, Optional
import logging

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ClaimRepository(BaseRepository):
    """Repository for Claim node operations."""

    def create_claim(
        self,
        text: str,
        original_text: str,
        doc_id: str,
        claim_type: str = 'extracted',
        confidence: float = 0.0,
        status: str = 'processing',
        created_by: str = 'user',
        created_by_agent_id: str = None,
        **additional_props
    ) -> str:
        """
        Create a new claim node with provenance tracking.

        Args:
            text: Claim text (display text, may be simplified)
            original_text: Original extracted text
            doc_id: Parent document ID
            claim_type: Type of claim (extracted, super_claim, etc.)
            confidence: Confidence score (0.0-1.0)
            status: Processing status
            created_by: Who/what created this claim (user, document_processor, auto_linker)
            created_by_agent_id: Agent transcript ID if created by agent (for provenance tracking)
            **additional_props: Additional claim properties

        Returns:
            Claim ID
        """
        from datetime import datetime

        properties = {
            'text': text,
            'original_text': original_text,
            'claim_type': claim_type,
            'confidence': confidence,
            'status': status,
            'processing_stage': 'pending',
            'word_count_original': len(original_text.split()),
            # Provenance tracking
            'created_by': created_by,
            'created_by_agent_id': created_by_agent_id,
            'created_at': datetime.now().isoformat(),
            **additional_props
        }

        claim_id = self.create_node('Claim', properties)

        # Create relationship to document
        self.create_relationship(doc_id, claim_id, 'CONTAINS_CLAIM')

        logger.info(f"Created claim {claim_id} for document {doc_id}")
        return claim_id

    def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """
        Get claim by ID with all properties.

        Args:
            claim_id: Claim ID

        Returns:
            Claim properties dict, or None if not found
        """
        return self.get_node_by_id('Claim', claim_id)

    def update_claim(self, claim_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update claim properties.

        Args:
            claim_id: Claim ID
            updates: Properties to update

        Returns:
            True if updated, False if not found
        """
        return self.update_node('Claim', claim_id, updates)

    def delete_claim(self, claim_id: str) -> bool:
        """
        Delete claim and all its relationships.

        Args:
            claim_id: Claim ID

        Returns:
            True if deleted, False if not found
        """
        return self.delete_node('Claim', claim_id)

    def find_claims_by_document(self, doc_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find all claims for a document.

        Args:
            doc_id: Document ID
            limit: Maximum results

        Returns:
            List of claim dictionaries
        """
        limit_str = f"LIMIT {limit}" if limit else ""

        query = f"""
        MATCH (d:Document {{id: $doc_id}})-[:CONTAINS_CLAIM]->(c:Claim)
        RETURN c
        ORDER BY c.created_at
        {limit_str}
        """

        results = self.execute_query(query, {'doc_id': doc_id})
        return [r['c'] for r in results]

    def find_claims_by_status(self, status: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find claims by processing status.

        Args:
            status: Status to filter (processing, complete, failed, etc.)
            limit: Maximum results

        Returns:
            List of claim dictionaries
        """
        return self.find_nodes('Claim', {'status': status}, limit=limit)

    def find_claims_by_disposition(self, disposition: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find claims by disposition (central, child, review, discard).

        Args:
            disposition: Disposition category
            limit: Maximum results

        Returns:
            List of claim dictionaries
        """
        return self.find_nodes('Claim', {'disposition': disposition}, limit=limit)

    def get_claim_with_relationships(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """
        Get claim with all related nodes (children, evidence, research).

        Args:
            claim_id: Claim ID

        Returns:
            Claim with relationships, or None if not found
        """
        query = """
        MATCH (c:Claim {id: $claim_id})
        OPTIONAL MATCH (c)-[:SUPPORTS]->(child:Claim)
        OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(supporter:Claim)
        OPTIONAL MATCH (c)-[:SUPPORTED_BY_EVIDENCE]->(ev:Evidence)
        OPTIONAL MATCH (c)-[:EXTRACTED_FROM]->(src:Source)
        OPTIONAL MATCH (res:ResearchResult)-[:INVESTIGATES]->(c)
        OPTIONAL MATCH (res)-[:PERFORMED_BY]->(a:Agent)
        RETURN c,
               collect(DISTINCT {id: child.id, text: child.text, summary: child.summary}) as children,
               collect(DISTINCT {id: supporter.id, text: supporter.text, summary: supporter.summary}) as supporters,
               collect(DISTINCT {title: ev.title, url: ev.url, credibility: ev.credibility_score}) as evidence,
               collect(DISTINCT {page: src.page, text: src.text}) as sources,
               collect(DISTINCT {
                   agent: a.name,
                   findings: res.findings,
                   confidence: res.confidence,
                   status: res.status
               }) as research
        """

        results = self.execute_query(query, {'claim_id': claim_id})
        if not results:
            return None

        record = results[0]

        # Clean up None values
        result = dict(record['c'])
        result['children'] = [c for c in record['children'] if c.get('id')]
        result['supporters'] = [s for s in record['supporters'] if s.get('id')]
        result['evidence'] = [e for e in record['evidence'] if e.get('title')]
        result['sources'] = [s for s in record['sources'] if s.get('page')]
        result['research'] = [r for r in record['research'] if r.get('agent')]

        return result

    def create_claim_relationship(
        self,
        from_claim_id: str,
        to_claim_id: str,
        relationship_type: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """
        Create relationship between claims.

        Args:
            from_claim_id: Source claim ID
            to_claim_id: Target claim ID
            relationship_type: SUPPORTS, CONTRADICTS, SIMILAR_TO, etc.
            properties: Relationship properties

        Returns:
            True if created
        """
        return self.create_relationship(
            from_claim_id,
            to_claim_id,
            relationship_type,
            properties
        )

    def find_similar_claims(
        self,
        claim_id: str,
        min_similarity: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar claims using SIMILAR_TO relationships.

        Args:
            claim_id: Claim ID
            min_similarity: Minimum similarity score
            limit: Maximum results

        Returns:
            List of similar claims with similarity scores
        """
        query = """
        MATCH (c:Claim {id: $claim_id})-[r:SIMILAR_TO]-(similar:Claim)
        WHERE r.similarity >= $min_similarity
        RETURN similar, r.similarity as similarity
        ORDER BY r.similarity DESC
        LIMIT $limit
        """

        results = self.execute_query(query, {
            'claim_id': claim_id,
            'min_similarity': min_similarity,
            'limit': limit
        })

        return [
            {**r['similar'], 'similarity': r['similarity']}
            for r in results
        ]

    def get_claim_cluster(self, claim_id: str) -> List[str]:
        """
        Get all claims in the same cluster (connected via SIMILAR_TO).

        Args:
            claim_id: Claim ID

        Returns:
            List of claim IDs in cluster
        """
        query = """
        MATCH (c:Claim {id: $claim_id})
        MATCH (c)-[:SIMILAR_TO*]-(cluster:Claim)
        RETURN DISTINCT cluster.id as id
        """

        results = self.execute_query(query, {'claim_id': claim_id})
        return [r['id'] for r in results]

    def get_super_claims(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Get all super-claims (top-level claims) for a document.

        Args:
            doc_id: Document ID

        Returns:
            List of super-claim dictionaries
        """
        query = """
        MATCH (d:Document {id: $doc_id})-[:CONTAINS_CLAIM]->(c:Claim)
        WHERE c.claim_type = 'super_claim' OR c.is_super_claim = true
        RETURN c
        ORDER BY c.created_at
        """

        results = self.execute_query(query, {'doc_id': doc_id})
        return [r['c'] for r in results]

    def get_claim_hierarchy(self, claim_id: str, max_depth: int = 5) -> Dict[str, Any]:
        """
        Get complete claim hierarchy (parents and children).

        Args:
            claim_id: Root claim ID
            max_depth: Maximum depth to traverse

        Returns:
            Nested claim structure
        """
        query = f"""
        MATCH path = (c:Claim {{id: $claim_id}})-[:SUPPORTS*0..{max_depth}]->(child:Claim)
        WITH c, collect(DISTINCT child) as children
        RETURN c, children
        """

        results = self.execute_query(query, {'claim_id': claim_id})
        if not results:
            return None

        record = results[0]
        result = dict(record['c'])
        result['children'] = [dict(child) for child in record['children'] if child.get('id')]

        return result

    def count_claims_by_document(self, doc_id: str) -> int:
        """
        Count claims for a document.

        Args:
            doc_id: Document ID

        Returns:
            Number of claims
        """
        query = """
        MATCH (d:Document {id: $doc_id})-[:CONTAINS_CLAIM]->(c:Claim)
        RETURN count(c) as count
        """

        result = self.execute_write(query, {'doc_id': doc_id})
        return result or 0

    def count_claims_by_status(self, status: str) -> int:
        """
        Count claims by status.

        Args:
            status: Status to count

        Returns:
            Number of claims
        """
        query = """
        MATCH (c:Claim {status: $status})
        RETURN count(c) as count
        """

        result = self.execute_write(query, {'status': status})
        return result or 0

    def find_root_claims(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find root claims (optimal claims without parents).

        Args:
            limit: Maximum number of claims to return

        Returns:
            List of root claims with metadata
        """
        query = """
        MATCH (c:Claim)
        WHERE c.is_optimal = true AND NOT ()-[:PARENT_OF]->(c)
        RETURN c.id as id,
               c.text as text,
               c.summary as summary,
               c.specificity_score as specificity,
               c.information_content as uniqueness,
               c.compression_ratio as compression_ratio,
               c.qualifiers_preserved as qualifiers_preserved
        ORDER BY c.specificity_score ASC
        """

        if limit:
            query += f" LIMIT {limit}"

        return self.execute_query(query)

    def get_all_claims_with_children(self) -> List[Dict[str, Any]]:
        """
        Get all claims with their child IDs.

        Returns:
            List of claims with child_ids array
        """
        query = """
        MATCH (c:Claim)
        OPTIONAL MATCH (c)-[r:PARENT_OF]->(child:Claim)
        RETURN
            c.id as id,
            c.text as text,
            c.summary as summary,
            c.status as status,
            c.disposition as disposition,
            c.quality_score as quality_score,
            c.claim_type as claim_type,
            c.confidence as confidence,
            coalesce(c.is_super_claim, false) as is_super_claim,
            collect(child.id) as child_ids
        """

        return self.execute_query(query)

    def get_document_claim_ids(self, doc_id: str) -> List[str]:
        """
        Get all claim IDs for a document.

        Args:
            doc_id: Document ID

        Returns:
            List of claim IDs
        """
        query = """
        MATCH (d:Document {id: $doc_id})-[:CONTAINS_CLAIM]->(c:Claim)
        RETURN collect(c.id) as claim_ids
        """

        results = self.execute_query(query, {'doc_id': doc_id})
        return results[0].get('claim_ids', []) if results else []

    def get_claim_evidence(self, claim_id: str) -> List[Dict[str, Any]]:
        """
        Get evidence supporting or contradicting a claim.

        Args:
            claim_id: Claim ID

        Returns:
            List of evidence with relationship type
        """
        query = """
        MATCH (c:Claim {id: $claim_id})<-[r:SUPPORTS|CONTRADICTS]-(e:Evidence)
        RETURN
            e.id as id,
            e.title as title,
            type(r) as relationship_type,
            e.url as url
        """

        return self.execute_query(query, {'claim_id': claim_id})

    def get_all_claim_evidence_relationships(self) -> List[Dict[str, Any]]:
        """
        Get all claim-evidence relationships.

        Returns:
            List of {claim_id, evidence_list} mappings
        """
        query = """
        MATCH (c:Claim)<-[r:SUPPORTS|CONTRADICTS]-(e:Evidence)
        RETURN
            c.id as claim_id,
            collect({
                id: e.id,
                title: e.title,
                type: type(r),
                url: e.url
            }) as evidence_list
        """

        return self.execute_query(query)

    def create_semantic_relationship(
        self,
        claim1_id: str,
        claim2_id: str,
        similarity_score: float,
        relationship_type: str = 'SEMANTICALLY_SIMILAR'
    ) -> bool:
        """
        Create a semantic similarity relationship between two claims.

        Creates bidirectional link for cross-document visualization.

        Args:
            claim1_id: First claim ID
            claim2_id: Second claim ID
            similarity_score: Semantic similarity score (0.0-1.0)
            relationship_type: Type of semantic relationship

        Returns:
            True if created successfully
        """
        query = """
        MATCH (c1:Claim {id: $claim1_id})
        MATCH (c2:Claim {id: $claim2_id})
        MERGE (c1)-[r:SEMANTICALLY_SIMILAR]->(c2)
        SET r.similarity_score = $similarity_score,
            r.created_at = datetime()
        RETURN r
        """

        params = {
            'claim1_id': claim1_id,
            'claim2_id': claim2_id,
            'similarity_score': similarity_score
        }

        result = self.execute_query(query, params)
        return len(result) > 0

    def get_all_semantic_relationships(self) -> List[Dict[str, Any]]:
        """
        Get all semantic similarity relationships between claims.

        Returns:
            List of {source_id, target_id, similarity_score} relationships
        """
        query = """
        MATCH (c1:Claim)-[r:SEMANTICALLY_SIMILAR]->(c2:Claim)
        RETURN
            c1.id as source_id,
            c2.id as target_id,
            r.similarity_score as similarity_score
        """

        return self.execute_query(query)
