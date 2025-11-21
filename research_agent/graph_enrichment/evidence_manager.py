"""
Evidence Integration System

Manages external evidence (research papers, articles, studies) that support or contradict claims.
"""

import logging
from typing import Dict, List, Any, Optional
from uuid import uuid4
from datetime import datetime

logger = logging.getLogger(__name__)


class EvidenceManager:
    """Manage evidence nodes and their relationships to claims."""

    def __init__(self):
        """Initialize evidence manager."""
        pass

    def create_evidence(
        self,
        title: str,
        source_type: str,
        url: Optional[str] = None,
        authors: Optional[List[str]] = None,
        publication_date: Optional[str] = None,
        abstract: Optional[str] = None,
        doi: Optional[str] = None,
        arxiv_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create an evidence record.

        Args:
            title: Evidence title
            source_type: Type (research_paper, article, study, book, etc.)
            url: URL to evidence
            authors: List of author names
            publication_date: Publication date
            abstract: Abstract/summary
            doi: DOI identifier
            arxiv_id: arXiv identifier
            metadata: Additional metadata

        Returns:
            Evidence dict
        """
        evidence = {
            'id': str(uuid4()),
            'title': title,
            'source_type': source_type,
            'url': url,
            'authors': authors or [],
            'publication_date': publication_date,
            'abstract': abstract,
            'doi': doi,
            'arxiv_id': arxiv_id,
            'metadata': metadata or {},
            'added_at': datetime.utcnow().isoformat()
        }

        logger.info(f"Created evidence: {title}")
        return evidence

    def link_evidence_to_claim(
        self,
        evidence_id: str,
        claim_id: str,
        relationship_type: str,
        strength: float,
        notes: Optional[str] = None,
        db = None
    ) -> str:
        """
        Link evidence to a claim.

        Args:
            evidence_id: Evidence UUID
            claim_id: Claim UUID
            relationship_type: SUPPORTS, CONTRADICTS, or RELATES_TO
            strength: Relationship strength 0.0-1.0
            notes: Optional notes about the relationship
            db: Neo4jDatabase instance

        Returns:
            Relationship ID
        """
        if relationship_type not in ['SUPPORTS', 'CONTRADICTS', 'RELATES_TO']:
            raise ValueError(
                f"Invalid relationship type: {relationship_type}. "
                "Must be SUPPORTS, CONTRADICTS, or RELATES_TO"
            )

        if not (0.0 <= strength <= 1.0):
            raise ValueError(f"Strength must be 0.0-1.0, got {strength}")

        properties = {
            'strength': strength,
            'notes': notes,
            'created_at': datetime.utcnow().isoformat()
        }

        if db:
            rel_id = db.create_relationship(
                evidence_id,
                claim_id,
                relationship_type,
                properties
            )
            logger.info(
                f"Linked evidence to claim: {relationship_type} "
                f"(strength: {strength:.2f})"
            )
            return rel_id

        return None

    def create_evidence_node_in_neo4j(
        self,
        evidence: Dict[str, Any],
        db
    ) -> str:
        """
        Create Evidence node in Neo4j.

        Args:
            evidence: Evidence dict
            db: Neo4jDatabase instance

        Returns:
            Evidence node ID
        """
        # Create Evidence node
        node_id = db.create_node('Evidence', {
            'id': evidence['id'],
            'title': evidence['title'],
            'source_type': evidence['source_type'],
            'url': evidence.get('url'),
            'authors': ', '.join(evidence.get('authors', [])),
            'publication_date': evidence.get('publication_date'),
            'abstract': evidence.get('abstract'),
            'doi': evidence.get('doi'),
            'arxiv_id': evidence.get('arxiv_id'),
            'added_at': evidence['added_at']
        })

        logger.info(f"Created Evidence node: {evidence['title']}")
        return node_id

    def find_supporting_evidence(
        self,
        claim_id: str,
        db,
        min_strength: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Find all evidence supporting a claim.

        Args:
            claim_id: Claim UUID
            db: Neo4jDatabase instance
            min_strength: Minimum strength threshold

        Returns:
            List of evidence dicts with relationship info
        """
        query = """
        MATCH (e:Evidence)-[r:SUPPORTS]->(c:Claim {id: $claim_id})
        WHERE r.strength >= $min_strength
        RETURN e, r
        ORDER BY r.strength DESC
        """

        with db.driver.session(database=db.database) as session:
            result = session.run(query, claim_id=claim_id, min_strength=min_strength)

            evidence_list = []
            for record in result:
                evidence_node = dict(record['e'])
                relationship = dict(record['r'])

                evidence_list.append({
                    **evidence_node,
                    'support_strength': relationship.get('strength'),
                    'notes': relationship.get('notes')
                })

            return evidence_list

    def find_contradicting_evidence(
        self,
        claim_id: str,
        db,
        min_strength: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Find all evidence contradicting a claim.

        Args:
            claim_id: Claim UUID
            db: Neo4jDatabase instance
            min_strength: Minimum strength threshold

        Returns:
            List of evidence dicts with relationship info
        """
        query = """
        MATCH (e:Evidence)-[r:CONTRADICTS]->(c:Claim {id: $claim_id})
        WHERE r.strength >= $min_strength
        RETURN e, r
        ORDER BY r.strength DESC
        """

        with db.driver.session(database=db.database) as session:
            result = session.run(query, claim_id=claim_id, min_strength=min_strength)

            evidence_list = []
            for record in result:
                evidence_node = dict(record['e'])
                relationship = dict(record['r'])

                evidence_list.append({
                    **evidence_node,
                    'contradiction_strength': relationship.get('strength'),
                    'notes': relationship.get('notes')
                })

            return evidence_list

    def get_evidence_balance(
        self,
        claim_id: str,
        db
    ) -> Dict[str, Any]:
        """
        Get balance of supporting vs contradicting evidence for a claim.

        Args:
            claim_id: Claim UUID
            db: Neo4jDatabase instance

        Returns:
            Dict with evidence balance metrics
        """
        supporting = self.find_supporting_evidence(claim_id, db)
        contradicting = self.find_contradicting_evidence(claim_id, db)

        support_strength_sum = sum(e.get('support_strength', 0) for e in supporting)
        contra_strength_sum = sum(e.get('contradiction_strength', 0) for e in contradicting)

        total_strength = support_strength_sum + contra_strength_sum

        return {
            'supporting_count': len(supporting),
            'contradicting_count': len(contradicting),
            'support_strength': support_strength_sum,
            'contradiction_strength': contra_strength_sum,
            'balance_ratio': (
                support_strength_sum / total_strength
                if total_strength > 0 else 0.5
            ),
            'verdict': self._get_verdict(
                len(supporting),
                len(contradicting),
                support_strength_sum,
                contra_strength_sum
            )
        }

    def _get_verdict(
        self,
        support_count: int,
        contra_count: int,
        support_strength: float,
        contra_strength: float
    ) -> str:
        """Determine verdict based on evidence balance."""
        if support_count == 0 and contra_count == 0:
            return "No evidence"

        if support_strength > contra_strength * 2:
            return "Strongly supported"
        elif support_strength > contra_strength:
            return "Supported"
        elif contra_strength > support_strength * 2:
            return "Strongly contradicted"
        elif contra_strength > support_strength:
            return "Contradicted"
        else:
            return "Mixed evidence"
