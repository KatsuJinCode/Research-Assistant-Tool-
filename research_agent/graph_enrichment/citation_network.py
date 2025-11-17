"""
Citation Network System

Tracks how claims cite each other and how they're cited in documents.
Builds a network of claim references.
"""

import logging
from typing import Dict, List, Any, Optional
from uuid import uuid4
from datetime import datetime

logger = logging.getLogger(__name__)


class CitationNetwork:
    """Manage citation relationships between claims."""

    def __init__(self):
        """Initialize citation network."""
        pass

    def create_citation(
        self,
        citing_claim_id: str,
        cited_claim_id: str,
        citation_type: str,
        context: Optional[str] = None,
        db = None
    ) -> str:
        """
        Create a citation relationship between claims.

        Args:
            citing_claim_id: Claim that cites
            cited_claim_id: Claim being cited
            citation_type: Type (supports, contradicts, extends, mentions)
            context: Context of citation
            db: Neo4jDatabase instance

        Returns:
            Relationship ID
        """
        if citation_type not in ['supports', 'contradicts', 'extends', 'mentions']:
            raise ValueError(
                f"Invalid citation type: {citation_type}. "
                "Must be supports, contradicts, extends, or mentions"
            )

        properties = {
            'citation_type': citation_type,
            'context': context,
            'created_at': datetime.utcnow().isoformat()
        }

        if db:
            rel_id = db.create_relationship(
                citing_claim_id,
                cited_claim_id,
                'CITES',
                properties
            )
            logger.info(f"Created citation: {citation_type}")
            return rel_id

        return None

    def create_document_citation(
        self,
        claim_id: str,
        document_id: str,
        page: int,
        line_number: Optional[int] = None,
        quote: Optional[str] = None,
        db = None
    ) -> str:
        """
        Track where a claim is cited in a document.

        Args:
            claim_id: Claim UUID
            document_id: Document UUID
            page: Page number
            line_number: Line number (optional)
            quote: Exact quote from document
            db: Neo4jDatabase instance

        Returns:
            Relationship ID
        """
        properties = {
            'page': page,
            'line_number': line_number,
            'quote': quote,
            'cited_at': datetime.utcnow().isoformat()
        }

        if db:
            rel_id = db.create_relationship(
                claim_id,
                document_id,
                'CITED_IN',
                properties
            )
            logger.info(f"Linked claim to document citation (page {page})")
            return rel_id

        return None

    def find_citing_claims(
        self,
        claim_id: str,
        db,
        citation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all claims that cite this claim.

        Args:
            claim_id: Claim UUID
            db: Neo4jDatabase instance
            citation_type: Filter by citation type (optional)

        Returns:
            List of citing claims with citation info
        """
        if citation_type:
            query = """
            MATCH (citing:Claim)-[r:CITES {citation_type: $citation_type}]->(cited:Claim {id: $claim_id})
            RETURN citing, r
            ORDER BY r.created_at DESC
            """
            params = {'claim_id': claim_id, 'citation_type': citation_type}
        else:
            query = """
            MATCH (citing:Claim)-[r:CITES]->(cited:Claim {id: $claim_id})
            RETURN citing, r
            ORDER BY r.created_at DESC
            """
            params = {'claim_id': claim_id}

        with db.driver.session(database=db.database) as session:
            result = session.run(query, **params)

            citations = []
            for record in result:
                citing_node = dict(record['citing'])
                relationship = dict(record['r'])

                citations.append({
                    **citing_node,
                    'citation_type': relationship.get('citation_type'),
                    'context': relationship.get('context'),
                    'created_at': relationship.get('created_at')
                })

            return citations

    def find_cited_claims(
        self,
        claim_id: str,
        db,
        citation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all claims cited by this claim.

        Args:
            claim_id: Claim UUID
            db: Neo4jDatabase instance
            citation_type: Filter by citation type (optional)

        Returns:
            List of cited claims with citation info
        """
        if citation_type:
            query = """
            MATCH (citing:Claim {id: $claim_id})-[r:CITES {citation_type: $citation_type}]->(cited:Claim)
            RETURN cited, r
            ORDER BY r.created_at DESC
            """
            params = {'claim_id': claim_id, 'citation_type': citation_type}
        else:
            query = """
            MATCH (citing:Claim {id: $claim_id})-[r:CITES]->(cited:Claim)
            RETURN cited, r
            ORDER BY r.created_at DESC
            """
            params = {'claim_id': claim_id}

        with db.driver.session(database=db.database) as session:
            result = session.run(query, **params)

            citations = []
            for record in result:
                cited_node = dict(record['cited'])
                relationship = dict(record['r'])

                citations.append({
                    **cited_node,
                    'citation_type': relationship.get('citation_type'),
                    'context': relationship.get('context'),
                    'created_at': relationship.get('created_at')
                })

            return citations

    def get_citation_metrics(
        self,
        claim_id: str,
        db
    ) -> Dict[str, Any]:
        """
        Get citation metrics for a claim.

        Args:
            claim_id: Claim UUID
            db: Neo4jDatabase instance

        Returns:
            Citation metrics
        """
        query = """
        MATCH (c:Claim {id: $claim_id})
        OPTIONAL MATCH (citing:Claim)-[r_in:CITES]->(c)
        OPTIONAL MATCH (c)-[r_out:CITES]->(cited:Claim)
        RETURN
            count(DISTINCT citing) as times_cited,
            count(DISTINCT cited) as claims_cited,
            count(DISTINCT CASE WHEN r_in.citation_type = 'supports' THEN citing END) as cited_as_support,
            count(DISTINCT CASE WHEN r_in.citation_type = 'contradicts' THEN citing END) as cited_as_contradiction,
            count(DISTINCT CASE WHEN r_out.citation_type = 'supports' THEN cited END) as cites_as_support,
            count(DISTINCT CASE WHEN r_out.citation_type = 'contradicts' THEN cited END) as cites_as_contradiction
        """

        with db.driver.session(database=db.database) as session:
            result = session.run(query, claim_id=claim_id)
            record = result.single()

            if record:
                return {
                    'times_cited': record['times_cited'],
                    'claims_cited': record['claims_cited'],
                    'cited_as_support': record['cited_as_support'],
                    'cited_as_contradiction': record['cited_as_contradiction'],
                    'cites_as_support': record['cites_as_support'],
                    'cites_as_contradiction': record['cites_as_contradiction'],
                    'citation_impact': record['times_cited']  # Simple impact score
                }

            return {
                'times_cited': 0,
                'claims_cited': 0,
                'cited_as_support': 0,
                'cited_as_contradiction': 0,
                'cites_as_support': 0,
                'cites_as_contradiction': 0,
                'citation_impact': 0
            }

    def find_citation_chain(
        self,
        claim_id: str,
        db,
        max_depth: int = 5
    ) -> List[List[str]]:
        """
        Find citation chains starting from a claim.

        Args:
            claim_id: Starting claim UUID
            db: Neo4jDatabase instance
            max_depth: Maximum chain depth

        Returns:
            List of citation chains (each chain is list of claim IDs)
        """
        query = """
        MATCH path = (start:Claim {id: $claim_id})-[:CITES*1..{max_depth}]->(end:Claim)
        RETURN [node in nodes(path) | node.id] as chain
        ORDER BY length(path) DESC
        LIMIT 100
        """.format(max_depth=max_depth)

        with db.driver.session(database=db.database) as session:
            result = session.run(query, claim_id=claim_id)

            chains = []
            for record in result:
                chains.append(record['chain'])

            return chains

    def detect_circular_citations(
        self,
        db
    ) -> List[List[str]]:
        """
        Detect circular citation patterns.

        Args:
            db: Neo4jDatabase instance

        Returns:
            List of circular citation loops
        """
        query = """
        MATCH path = (c:Claim)-[:CITES*2..10]->(c)
        RETURN [node in nodes(path) | node.id] as loop
        LIMIT 50
        """

        with db.driver.session(database=db.database) as session:
            result = session.run(query)

            loops = []
            for record in result:
                loops.append(record['loop'])

            logger.info(f"Found {len(loops)} circular citation patterns")
            return loops
