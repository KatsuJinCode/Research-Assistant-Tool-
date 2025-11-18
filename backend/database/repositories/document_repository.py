"""
Document Repository

Handles all database operations for Document nodes.
Provides high-level methods for document CRUD, querying, and document-claim relationships.
"""

from typing import Dict, List, Any, Optional
import logging

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DocumentRepository(BaseRepository):
    """Repository for Document node operations."""

    def create_document(
        self,
        title: str,
        source_file: str,
        status: str = 'processing',
        **additional_props
    ) -> str:
        """
        Create a new document node.

        Args:
            title: Document title
            source_file: Path to source file
            status: Processing status (processing, complete, failed)
            **additional_props: Additional document properties

        Returns:
            Document ID
        """
        properties = {
            'title': title,
            'source_file': source_file,
            'status': status,
            **additional_props
        }

        doc_id = self.create_node('Document', properties)
        logger.info(f"Created document {doc_id}: {title}")
        return doc_id

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID with all properties.

        Args:
            doc_id: Document ID

        Returns:
            Document properties dict, or None if not found
        """
        return self.get_node_by_id('Document', doc_id)

    def update_document(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update document properties.

        Args:
            doc_id: Document ID
            updates: Properties to update

        Returns:
            True if updated, False if not found
        """
        return self.update_node('Document', doc_id, updates)

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document and all its relationships.

        WARNING: This will orphan claims unless cascade delete is implemented.

        Args:
            doc_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        return self.delete_node('Document', doc_id)

    def find_documents_by_status(self, status: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find documents by processing status.

        Args:
            status: Status to filter (processing, complete, failed)
            limit: Maximum results

        Returns:
            List of document dictionaries
        """
        return self.find_nodes('Document', {'status': status}, limit=limit)

    def get_all_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all documents.

        Args:
            limit: Maximum results

        Returns:
            List of document dictionaries
        """
        limit_str = f"LIMIT {limit}" if limit else ""

        query = f"""
        MATCH (d:Document)
        RETURN d
        ORDER BY d.created_at DESC
        {limit_str}
        """

        results = self.execute_query(query)
        return [r['d'] for r in results]

    def get_document_with_claims(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document with all its claims (hierarchical structure).

        Returns complete document-claim graph for visualization.

        Args:
            doc_id: Document ID

        Returns:
            Document with nested claims structure, or None if not found
        """
        query = """
        MATCH (d:Document {id: $doc_id})
        OPTIONAL MATCH (d)-[:CONTAINS_CLAIM]->(c:Claim)
        WITH d, collect(DISTINCT c) as all_claims
        OPTIONAL MATCH (d)-[:CONTAINS_CLAIM]->(super:Claim)
        WHERE super.claim_type = 'super_claim' OR super.is_super_claim = true
        RETURN d,
               all_claims,
               collect(DISTINCT super) as super_claims
        """

        results = self.execute_query(query, {'doc_id': doc_id})
        if not results:
            return None

        record = results[0]

        result = dict(record['d'])
        result['all_claims'] = [dict(c) for c in record['all_claims'] if c.get('id')]
        result['super_claims'] = [dict(c) for c in record['super_claims'] if c.get('id')]

        return result

    def get_document_stats(self, doc_id: str) -> Dict[str, Any]:
        """
        Get statistics for a document.

        Args:
            doc_id: Document ID

        Returns:
            Statistics dictionary with counts
        """
        query = """
        MATCH (d:Document {id: $doc_id})
        OPTIONAL MATCH (d)-[:CONTAINS_CLAIM]->(c:Claim)
        OPTIONAL MATCH (c)-[:SUPPORTED_BY_EVIDENCE]->(ev:Evidence)
        OPTIONAL MATCH (c)-[:EXTRACTED_FROM]->(src:Source)
        RETURN d,
               count(DISTINCT c) as claim_count,
               count(DISTINCT ev) as evidence_count,
               count(DISTINCT src) as source_count
        """

        results = self.execute_query(query, {'doc_id': doc_id})
        if not results:
            return None

        record = results[0]

        return {
            'document': dict(record['d']),
            'claim_count': record['claim_count'],
            'evidence_count': record['evidence_count'],
            'source_count': record['source_count']
        }

    def get_all_documents_with_claim_counts(self) -> List[Dict[str, Any]]:
        """
        Get all documents with their claim counts.

        Useful for document listing pages.

        Returns:
            List of documents with claim_count property
        """
        query = """
        MATCH (d:Document)
        OPTIONAL MATCH (d)-[:CONTAINS_CLAIM]->(c:Claim)
        WITH d, count(c) as claim_count
        RETURN d.id as id,
               d.title as title,
               d.status as status,
               d.created_at as created_at,
               claim_count
        ORDER BY d.created_at DESC
        """

        results = self.execute_query(query)
        return [dict(r) for r in results]

    def count_documents(self) -> int:
        """
        Count total documents.

        Returns:
            Number of documents
        """
        query = """
        MATCH (d:Document)
        RETURN count(d) as count
        """

        result = self.execute_write(query)
        return result or 0

    def count_documents_by_status(self, status: str) -> int:
        """
        Count documents by status.

        Args:
            status: Status to count

        Returns:
            Number of documents
        """
        query = """
        MATCH (d:Document {status: $status})
        RETURN count(d) as count
        """

        result = self.execute_write(query, {'status': status})
        return result or 0

    def mark_document_failed(self, doc_id: str, error: str) -> bool:
        """
        Mark document as failed with error message.

        Args:
            doc_id: Document ID
            error: Error message

        Returns:
            True if updated, False if not found
        """
        return self.update_document(doc_id, {
            'status': 'failed',
            'error': error
        })

    def mark_document_complete(self, doc_id: str) -> bool:
        """
        Mark document as complete.

        Args:
            doc_id: Document ID

        Returns:
            True if updated, False if not found
        """
        return self.update_document(doc_id, {
            'status': 'complete'
        })

    def search_documents_by_title(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search documents by title (case-insensitive contains).

        Args:
            search_term: Text to search for
            limit: Maximum results

        Returns:
            List of matching documents
        """
        query = """
        MATCH (d:Document)
        WHERE toLower(d.title) CONTAINS toLower($search_term)
        RETURN d
        ORDER BY d.created_at DESC
        LIMIT $limit
        """

        results = self.execute_query(query, {
            'search_term': search_term,
            'limit': limit
        })
        return [r['d'] for r in results]
