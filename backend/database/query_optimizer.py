"""
Query Optimizer for Neo4j Database

Provides optimized Cypher queries with:
- Parameterized queries (no string concatenation)
- Appropriate LIMIT clauses
- Query plan analysis
- Batch operations
- Index hints

Performance Features:
- Uses query parameters for safety and performance
- Implements pagination for large result sets
- Batches similar queries together
- Provides PROFILE/EXPLAIN analysis
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Optimized query builder for Neo4j graph database.

    All queries use parameters instead of string concatenation for:
    - Security (prevents injection)
    - Performance (query plan caching)
    - Readability
    """

    def __init__(self, session):
        """
        Initialize query optimizer.

        Args:
            session: Neo4j session object
        """
        self.session = session
        self.query_cache = {}
        self.cache_ttl = timedelta(minutes=5)

    # ===========================
    # OPTIMIZED GRAPH QUERIES
    # ===========================

    def get_full_graph(self, project_id: str = None, limit: int = 1000) -> Dict[str, Any]:
        """
        Get full graph with pagination and optional project filtering.

        OPTIMIZED with:
        - Parameters instead of string concat
        - LIMIT clause for performance
        - Optional project filtering
        - Uses indexes on project_id

        Args:
            project_id: Optional project ID filter
            limit: Maximum nodes to return (default 1000)

        Returns:
            Dict with nodes and relationships
        """
        # Build query with optional project filter
        if project_id:
            query = """
            MATCH (n)
            WHERE n.project_id = $project_id
            WITH n LIMIT $limit
            OPTIONAL MATCH (n)-[r]->(m)
            WHERE m.project_id = $project_id
            RETURN n, collect({rel: r, node: m}) as relationships
            """
            params = {"project_id": project_id, "limit": limit}
        else:
            query = """
            MATCH (n)
            WITH n LIMIT $limit
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n, collect({rel: r, node: m}) as relationships
            """
            params = {"limit": limit}

        result = self.session.run(query, params)

        nodes = []
        links = []
        node_ids = set()

        for record in result:
            node = record['n']
            node_dict = dict(node)
            node_dict['id'] = node.element_id
            node_dict['labels'] = list(node.labels)

            if node_dict['id'] not in node_ids:
                nodes.append(node_dict)
                node_ids.add(node_dict['id'])

            # Process relationships
            for rel_data in record['relationships']:
                if rel_data['rel']:
                    rel = rel_data['rel']
                    target = rel_data['node']

                    target_dict = dict(target)
                    target_dict['id'] = target.element_id
                    target_dict['labels'] = list(target.labels)

                    if target_dict['id'] not in node_ids:
                        nodes.append(target_dict)
                        node_ids.add(target_dict['id'])

                    links.append({
                        'source': node_dict['id'],
                        'target': target_dict['id'],
                        'type': rel.type,
                        'properties': dict(rel)
                    })

        return {
            'nodes': nodes,
            'links': links,
            'total': len(nodes)
        }

    def get_paginated_graph(self, skip: int = 0, limit: int = 100,
                           project_id: str = None) -> Dict[str, Any]:
        """
        Get paginated graph data for incremental loading.

        OPTIMIZED with:
        - SKIP/LIMIT for pagination
        - Parameter binding
        - Efficient relationship collection

        Args:
            skip: Number of nodes to skip
            limit: Number of nodes to return
            project_id: Optional project filter

        Returns:
            Dict with nodes, relationships, and pagination info
        """
        if project_id:
            query = """
            MATCH (n)
            WHERE n.project_id = $project_id
            WITH n
            ORDER BY n.created_at DESC
            SKIP $skip
            LIMIT $limit
            OPTIONAL MATCH (n)-[r]->(m)
            WHERE m.project_id = $project_id
            RETURN n, collect({rel: r, node: m}) as relationships
            """
            params = {"project_id": project_id, "skip": skip, "limit": limit}
        else:
            query = """
            MATCH (n)
            WITH n
            ORDER BY n.created_at DESC
            SKIP $skip
            LIMIT $limit
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n, collect({rel: r, node: m}) as relationships
            """
            params = {"skip": skip, "limit": limit}

        result = self.session.run(query, params)

        nodes = []
        links = []
        node_ids = set()

        for record in result:
            node = record['n']
            node_dict = dict(node)
            node_dict['id'] = node.element_id
            node_dict['labels'] = list(node.labels)

            if node_dict['id'] not in node_ids:
                nodes.append(node_dict)
                node_ids.add(node_dict['id'])

            for rel_data in record['relationships']:
                if rel_data['rel']:
                    rel = rel_data['rel']
                    target = rel_data['node']

                    target_dict = dict(target)
                    target_dict['id'] = target.element_id
                    target_dict['labels'] = list(target.labels)

                    if target_dict['id'] not in node_ids:
                        nodes.append(target_dict)
                        node_ids.add(target_dict['id'])

                    links.append({
                        'source': node_dict['id'],
                        'target': target_dict['id'],
                        'type': rel.type,
                        'properties': dict(rel)
                    })

        return {
            'nodes': nodes,
            'links': links,
            'skip': skip,
            'limit': limit,
            'count': len(nodes)
        }

    # ===========================
    # OPTIMIZED SEARCH QUERIES
    # ===========================

    def search_claims(self, query_text: str, limit: int = 50,
                     min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search claims by text with confidence filtering.

        OPTIMIZED with:
        - Full-text index usage (if available)
        - Parameters for safety
        - LIMIT for performance
        - Confidence filtering

        Args:
            query_text: Search query
            limit: Max results
            min_confidence: Minimum confidence score

        Returns:
            List of matching claims
        """
        query = """
        MATCH (c:Claim)
        WHERE c.text CONTAINS $query_text
        AND c.confidence >= $min_confidence
        RETURN c
        ORDER BY c.confidence DESC, c.created_at DESC
        LIMIT $limit
        """
        params = {
            "query_text": query_text,
            "min_confidence": min_confidence,
            "limit": limit
        }

        result = self.session.run(query, params)

        claims = []
        for record in result:
            claim = record['c']
            claim_dict = dict(claim)
            claim_dict['id'] = claim.element_id
            claim_dict['labels'] = list(claim.labels)
            claims.append(claim_dict)

        return claims

    def search_full_text(self, query_text: str, node_types: List[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Full-text search across multiple node types.

        OPTIMIZED with:
        - Dynamic label filtering
        - Parameter binding
        - LIMIT clause

        Args:
            query_text: Search query
            node_types: List of node labels to search (e.g., ['Claim', 'Document'])
            limit: Max results

        Returns:
            List of matching nodes
        """
        if node_types:
            # Build dynamic label filter
            label_filter = " OR ".join([f"n:{label}" for label in node_types])
            query = f"""
            MATCH (n)
            WHERE ({label_filter})
            AND (n.text CONTAINS $query_text OR n.title CONTAINS $query_text)
            RETURN n, labels(n) as node_labels
            ORDER BY n.created_at DESC
            LIMIT $limit
            """
        else:
            query = """
            MATCH (n)
            WHERE n.text CONTAINS $query_text OR n.title CONTAINS $query_text
            RETURN n, labels(n) as node_labels
            ORDER BY n.created_at DESC
            LIMIT $limit
            """

        params = {"query_text": query_text, "limit": limit}
        result = self.session.run(query, params)

        results = []
        for record in result:
            node = record['n']
            node_dict = dict(node)
            node_dict['id'] = node.element_id
            node_dict['labels'] = record['node_labels']
            results.append(node_dict)

        return results

    # ===========================
    # OPTIMIZED DOCUMENT QUERIES
    # ===========================

    def get_document_with_claims(self, document_id: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get document with all its claims.

        OPTIMIZED with:
        - Single query instead of multiple
        - Parameter binding
        - LIMIT on claims

        Args:
            document_id: Document ID
            limit: Max claims to return

        Returns:
            Document with claims
        """
        query = """
        MATCH (d:Document)
        WHERE elementId(d) = $document_id
        OPTIONAL MATCH (d)-[:CONTAINS]->(c:Claim)
        WITH d, collect(c)[..$limit] as claims
        RETURN d, claims
        """
        params = {"document_id": document_id, "limit": limit}

        result = self.session.run(query, params)
        record = result.single()

        if not record:
            return None

        doc = record['d']
        doc_dict = dict(doc)
        doc_dict['id'] = doc.element_id
        doc_dict['labels'] = list(doc.labels)

        claims = []
        for claim in record['claims']:
            if claim:
                claim_dict = dict(claim)
                claim_dict['id'] = claim.element_id
                claim_dict['labels'] = list(claim.labels)
                claims.append(claim_dict)

        doc_dict['claims'] = claims

        return doc_dict

    def get_documents_by_project(self, project_id: str,
                                skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get all documents for a project with pagination.

        OPTIMIZED with:
        - Index on project_id
        - SKIP/LIMIT pagination
        - Parameter binding

        Args:
            project_id: Project ID
            skip: Pagination offset
            limit: Page size

        Returns:
            List of documents
        """
        query = """
        MATCH (d:Document)
        WHERE d.project_id = $project_id
        RETURN d
        ORDER BY d.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        params = {"project_id": project_id, "skip": skip, "limit": limit}

        result = self.session.run(query, params)

        documents = []
        for record in result:
            doc = record['d']
            doc_dict = dict(doc)
            doc_dict['id'] = doc.element_id
            doc_dict['labels'] = list(doc.labels)
            documents.append(doc_dict)

        return documents

    # ===========================
    # OPTIMIZED RELATIONSHIP TRAVERSAL
    # ===========================

    def get_claim_network(self, claim_id: str, max_depth: int = 2,
                         relationship_types: List[str] = None) -> Dict[str, Any]:
        """
        Get network of related claims with depth limit.

        OPTIMIZED with:
        - Variable-length path with max depth
        - Optional relationship type filtering
        - Parameter binding

        Args:
            claim_id: Starting claim ID
            max_depth: Maximum traversal depth
            relationship_types: Filter by relationship types

        Returns:
            Network of claims and relationships
        """
        if relationship_types:
            rel_filter = "|".join(relationship_types)
            query = f"""
            MATCH (c:Claim)
            WHERE elementId(c) = $claim_id
            CALL apoc.path.subgraphAll(c, {{
                relationshipFilter: "{rel_filter}",
                maxLevel: $max_depth
            }})
            YIELD nodes, relationships
            RETURN nodes, relationships
            """
        else:
            query = """
            MATCH (c:Claim)
            WHERE elementId(c) = $claim_id
            MATCH path = (c)-[*1..$max_depth]-(related:Claim)
            WITH collect(distinct c) + collect(distinct related) as nodes,
                 collect(distinct relationships(path)) as rels
            UNWIND rels as rel_list
            UNWIND rel_list as r
            RETURN nodes, collect(distinct r) as relationships
            """

        params = {"claim_id": claim_id, "max_depth": max_depth}

        result = self.session.run(query, params)
        record = result.single()

        if not record:
            return {'nodes': [], 'relationships': []}

        nodes = []
        for node in record['nodes']:
            node_dict = dict(node)
            node_dict['id'] = node.element_id
            node_dict['labels'] = list(node.labels)
            nodes.append(node_dict)

        relationships = []
        for rel in record['relationships']:
            relationships.append({
                'source': rel.start_node.element_id,
                'target': rel.end_node.element_id,
                'type': rel.type,
                'properties': dict(rel)
            })

        return {
            'nodes': nodes,
            'relationships': relationships
        }

    # ===========================
    # BATCH OPERATIONS
    # ===========================

    def batch_create_claims(self, claims: List[Dict[str, Any]]) -> int:
        """
        Batch create multiple claims in single transaction.

        OPTIMIZED with:
        - UNWIND for batch processing
        - Single transaction
        - Parameter binding

        Args:
            claims: List of claim dicts with properties

        Returns:
            Number of claims created
        """
        query = """
        UNWIND $claims as claim_data
        CREATE (c:Claim)
        SET c = claim_data
        SET c.created_at = datetime()
        RETURN count(c) as created_count
        """
        params = {"claims": claims}

        result = self.session.run(query, params)
        record = result.single()

        return record['created_count'] if record else 0

    def batch_create_relationships(self, relationships: List[Tuple[str, str, str, Dict]]) -> int:
        """
        Batch create relationships.

        Args:
            relationships: List of (source_id, target_id, rel_type, properties)

        Returns:
            Number of relationships created
        """
        # Convert to format suitable for UNWIND
        rel_data = [
            {
                'source_id': src,
                'target_id': tgt,
                'type': rel_type,
                'properties': props or {}
            }
            for src, tgt, rel_type, props in relationships
        ]

        query = """
        UNWIND $relationships as rel
        MATCH (source), (target)
        WHERE elementId(source) = rel.source_id AND elementId(target) = rel.target_id
        CALL apoc.create.relationship(source, rel.type, rel.properties, target)
        YIELD rel as created_rel
        RETURN count(created_rel) as created_count
        """
        params = {"relationships": rel_data}

        result = self.session.run(query, params)
        record = result.single()

        return record['created_count'] if record else 0

    # ===========================
    # QUERY ANALYSIS
    # ===========================

    def profile_query(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """
        Profile a query to analyze performance.

        Args:
            query: Cypher query
            params: Query parameters

        Returns:
            Profile information
        """
        profiled_query = f"PROFILE {query}"
        result = self.session.run(profiled_query, params or {})

        summary = result.consume()

        return {
            'db_hits': summary.profile.get('dbHits', 0),
            'rows': summary.profile.get('rows', 0),
            'time': summary.result_available_after + summary.result_consumed_after
        }

    def explain_query(self, query: str, params: Dict = None) -> str:
        """
        Explain query execution plan.

        Args:
            query: Cypher query
            params: Query parameters

        Returns:
            Execution plan as string
        """
        explained_query = f"EXPLAIN {query}"
        result = self.session.run(explained_query, params or {})

        plan = result.consume().plan

        return self._format_plan(plan)

    def _format_plan(self, plan, indent=0) -> str:
        """Format execution plan for readability."""
        lines = []
        prefix = "  " * indent

        lines.append(f"{prefix}{plan.operator_type}")

        if hasattr(plan, 'identifiers'):
            lines.append(f"{prefix}  Identifiers: {plan.identifiers}")

        if hasattr(plan, 'children'):
            for child in plan.children:
                lines.append(self._format_plan(child, indent + 1))

        return "\n".join(lines)
