"""
Unit tests for DocumentRepository.

Tests all document-specific database operations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from backend.database.repositories.document_repository import DocumentRepository


@pytest.fixture
def mock_client():
    """Create mock Neo4jClient."""
    client = Mock()
    session = Mock()
    client.get_session.return_value.__enter__ = Mock(return_value=session)
    client.get_session.return_value.__exit__ = Mock(return_value=False)
    return client, session


@pytest.fixture
def repository(mock_client):
    """Create repository with mocked client."""
    client, _ = mock_client
    return DocumentRepository(client=client)


class TestCreateDocument:
    """Test document creation."""

    @patch('backend.database.repositories.base_repository.uuid4')
    @patch('backend.database.repositories.base_repository.datetime')
    def test_create_document_with_minimal_args(self, mock_datetime, mock_uuid, repository, mock_client):
        """Test create_document with only required arguments."""
        _, session = mock_client
        mock_uuid.return_value = 'doc-123'
        mock_datetime.utcnow.return_value.isoformat.return_value = '2025-01-01T00:00:00'

        mock_result = Mock()
        mock_result.single.return_value = ['doc-123']
        session.run.return_value = mock_result

        doc_id = repository.create_document(
            title="Test Document",
            source_file="/path/to/file.pdf"
        )

        assert doc_id == 'doc-123'

        # Verify CREATE node query was called
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'CREATE (n:Document $props)' in query

    def test_create_document_with_additional_props(self, repository, mock_client):
        """Test create_document preserves additional properties."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = ['doc-123']
        session.run.return_value = mock_result

        repository.create_document(
            title="Test",
            source_file="/file.pdf",
            author="John Doe",
            page_count=100
        )

        # Find the CREATE call
        call_args = session.run.call_args
        props = call_args[0][1]['props']
        assert props['author'] == 'John Doe'
        assert props['page_count'] == 100


class TestGetDocument:
    """Test document retrieval."""

    def test_get_document_returns_document_when_found(self, repository, mock_client):
        """Test get_document returns document properties."""
        _, session = mock_client

        mock_record = Mock()
        mock_record.data.return_value = {'n': {
            'id': 'doc-123',
            'title': 'Test Document',
            'status': 'complete'
        }}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        doc = repository.get_document('doc-123')

        assert doc['id'] == 'doc-123'
        assert doc['title'] == 'Test Document'
        assert doc['status'] == 'complete'

    def test_get_document_returns_none_when_not_found(self, repository, mock_client):
        """Test get_document returns None for non-existent document."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        session.run.return_value = mock_result

        doc = repository.get_document('nonexistent')

        assert doc is None


class TestUpdateDocument:
    """Test document updates."""

    @patch('backend.database.repositories.base_repository.datetime')
    def test_update_document_succeeds(self, mock_datetime, repository, mock_client):
        """Test update_document updates properties."""
        _, session = mock_client
        mock_datetime.utcnow.return_value.isoformat.return_value = '2025-01-01T12:00:00'

        mock_result = Mock()
        mock_result.single.return_value = ['doc-123']
        session.run.return_value = mock_result

        success = repository.update_document('doc-123', {
            'status': 'complete',
            'title': 'Updated Title'
        })

        assert success is True

    def test_update_document_returns_false_when_not_found(self, repository, mock_client):
        """Test update_document returns False for non-existent document."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = None
        session.run.return_value = mock_result

        success = repository.update_document('nonexistent', {'status': 'complete'})

        assert success is False


class TestDeleteDocument:
    """Test document deletion."""

    def test_delete_document_succeeds(self, repository, mock_client):
        """Test delete_document removes document and relationships."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [1]
        session.run.return_value = mock_result

        success = repository.delete_document('doc-123')

        assert success is True

        # Verify DETACH DELETE was used
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'DETACH DELETE' in query

    def test_delete_document_returns_false_when_not_found(self, repository, mock_client):
        """Test delete_document returns False for non-existent document."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [0]
        session.run.return_value = mock_result

        success = repository.delete_document('nonexistent')

        assert success is False


class TestFindDocumentsByStatus:
    """Test finding documents by status."""

    def test_find_documents_by_status(self, repository, mock_client):
        """Test finding documents by status filter."""
        _, session = mock_client

        mock_record = Mock()
        mock_record.data.return_value = {'n': {'id': 'doc-1', 'status': 'complete'}}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        docs = repository.find_documents_by_status('complete')

        assert len(docs) == 1
        assert docs[0]['status'] == 'complete'


class TestGetAllDocuments:
    """Test getting all documents."""

    def test_get_all_documents_returns_all_docs(self, repository, mock_client):
        """Test getting all documents."""
        _, session = mock_client

        mock_record1 = Mock()
        mock_record1.data.return_value = {'d': {'id': 'doc-1', 'title': 'Doc 1'}}
        mock_record2 = Mock()
        mock_record2.data.return_value = {'d': {'id': 'doc-2', 'title': 'Doc 2'}}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record1, mock_record2]))
        session.run.return_value = mock_result

        docs = repository.get_all_documents()

        assert len(docs) == 2
        assert docs[0]['id'] == 'doc-1'
        assert docs[1]['id'] == 'doc-2'

        # Verify ORDER BY created_at DESC
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'ORDER BY d.created_at DESC' in query

    def test_get_all_documents_with_limit(self, repository, mock_client):
        """Test getting documents with limit."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        session.run.return_value = mock_result

        repository.get_all_documents(limit=10)

        # Verify LIMIT was added
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'LIMIT 10' in query


class TestGetDocumentWithClaims:
    """Test getting document with claims."""

    def test_get_document_with_claims_returns_complete_structure(self, repository, mock_client):
        """Test getting document with all claims."""
        _, session = mock_client

        # Create claim-like objects that can be converted to dict
        class FakeClaim:
            def __init__(self, data):
                self._data = data
            def get(self, key, default=None):
                return self._data.get(key, default)
            def __iter__(self):
                return iter(self._data.items())

        claim1 = FakeClaim({'id': 'claim-1', 'text': 'Claim 1'})
        claim2 = FakeClaim({'id': 'claim-2', 'text': 'Claim 2'})
        super_claim = FakeClaim({'id': 'super-1', 'text': 'Super claim', 'claim_type': 'super_claim'})

        mock_record = Mock()
        mock_record.data.return_value = {
            'd': {'id': 'doc-123', 'title': 'Test Doc'},
            'all_claims': [claim1, claim2],
            'super_claims': [super_claim]
        }

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        doc = repository.get_document_with_claims('doc-123')

        assert doc['id'] == 'doc-123'
        assert len(doc['all_claims']) == 2
        assert len(doc['super_claims']) == 1

    def test_get_document_with_claims_returns_none_when_not_found(self, repository, mock_client):
        """Test returns None when document doesn't exist."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        session.run.return_value = mock_result

        doc = repository.get_document_with_claims('nonexistent')

        assert doc is None


class TestGetDocumentStats:
    """Test getting document statistics."""

    def test_get_document_stats_returns_counts(self, repository, mock_client):
        """Test getting document statistics."""
        _, session = mock_client

        mock_record = Mock()
        mock_record.data.return_value = {
            'd': {'id': 'doc-123', 'title': 'Test'},
            'claim_count': 5,
            'evidence_count': 10,
            'source_count': 3
        }

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        stats = repository.get_document_stats('doc-123')

        assert stats['claim_count'] == 5
        assert stats['evidence_count'] == 10
        assert stats['source_count'] == 3
        assert stats['document']['id'] == 'doc-123'

    def test_get_document_stats_returns_none_when_not_found(self, repository, mock_client):
        """Test returns None for non-existent document."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        session.run.return_value = mock_result

        stats = repository.get_document_stats('nonexistent')

        assert stats is None


class TestGetAllDocumentsWithClaimCounts:
    """Test getting all documents with claim counts."""

    def test_get_all_documents_with_claim_counts(self, repository, mock_client):
        """Test getting documents with claim counts."""
        _, session = mock_client

        mock_record1 = Mock()
        mock_record1.data.return_value = {
            'id': 'doc-1',
            'title': 'Doc 1',
            'status': 'complete',
            'created_at': '2025-01-01',
            'claim_count': 5
        }
        mock_record2 = Mock()
        mock_record2.data.return_value = {
            'id': 'doc-2',
            'title': 'Doc 2',
            'status': 'processing',
            'created_at': '2025-01-02',
            'claim_count': 3
        }

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record1, mock_record2]))
        session.run.return_value = mock_result

        docs = repository.get_all_documents_with_claim_counts()

        assert len(docs) == 2
        assert docs[0]['claim_count'] == 5
        assert docs[1]['claim_count'] == 3


class TestCountMethods:
    """Test counting methods."""

    def test_count_documents(self, repository, mock_client):
        """Test counting all documents."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [10]
        session.run.return_value = mock_result

        count = repository.count_documents()

        assert count == 10

    def test_count_documents_by_status(self, repository, mock_client):
        """Test counting documents by status."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [5]
        session.run.return_value = mock_result

        count = repository.count_documents_by_status('complete')

        assert count == 5

    def test_count_returns_zero_when_none(self, repository, mock_client):
        """Test count returns 0 when result is None."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = None
        session.run.return_value = mock_result

        count = repository.count_documents()

        assert count == 0


class TestMarkDocumentFailed:
    """Test marking document as failed."""

    @patch('backend.database.repositories.base_repository.datetime')
    def test_mark_document_failed_updates_status_and_error(self, mock_datetime, repository, mock_client):
        """Test marking document as failed."""
        _, session = mock_client
        mock_datetime.utcnow.return_value.isoformat.return_value = '2025-01-01T12:00:00'

        mock_result = Mock()
        mock_result.single.return_value = ['doc-123']
        session.run.return_value = mock_result

        success = repository.mark_document_failed('doc-123', 'Processing error')

        assert success is True

        # Verify update was called with correct values
        call_args = session.run.call_args
        params = call_args[0][1]
        assert params['updates']['status'] == 'failed'
        assert params['updates']['error'] == 'Processing error'


class TestMarkDocumentComplete:
    """Test marking document as complete."""

    @patch('backend.database.repositories.base_repository.datetime')
    def test_mark_document_complete_updates_status(self, mock_datetime, repository, mock_client):
        """Test marking document as complete."""
        _, session = mock_client
        mock_datetime.utcnow.return_value.isoformat.return_value = '2025-01-01T12:00:00'

        mock_result = Mock()
        mock_result.single.return_value = ['doc-123']
        session.run.return_value = mock_result

        success = repository.mark_document_complete('doc-123')

        assert success is True

        # Verify status was updated
        call_args = session.run.call_args
        params = call_args[0][1]
        assert params['updates']['status'] == 'complete'


class TestSearchDocumentsByTitle:
    """Test searching documents by title."""

    def test_search_documents_by_title_returns_matches(self, repository, mock_client):
        """Test searching documents by title."""
        _, session = mock_client

        mock_record = Mock()
        mock_record.data.return_value = {'d': {'id': 'doc-1', 'title': 'Test Document'}}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        docs = repository.search_documents_by_title('test', limit=20)

        assert len(docs) == 1
        assert docs[0]['title'] == 'Test Document'

        # Verify case-insensitive CONTAINS query
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'toLower(d.title) CONTAINS toLower($search_term)' in query
        assert call_args[0][1]['search_term'] == 'test'
        assert call_args[0][1]['limit'] == 20
