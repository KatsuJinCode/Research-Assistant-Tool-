"""
Unit tests for ClaimRepository.

Tests all claim-specific database operations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from backend.database.repositories.claim_repository import ClaimRepository


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
    return ClaimRepository(client=client)


class TestCreateClaim:
    """Test claim creation."""

    @patch('backend.database.repositories.base_repository.uuid4')
    @patch('backend.database.repositories.base_repository.datetime')
    def test_create_claim_with_minimal_args(self, mock_datetime, mock_uuid, repository, mock_client):
        """Test create_claim with only required arguments."""
        _, session = mock_client
        mock_uuid.return_value = 'claim-123'
        mock_datetime.utcnow.return_value.isoformat.return_value = '2025-01-01T00:00:00'

        # Mock node creation
        mock_result = Mock()
        mock_result.single.return_value = ['claim-123']
        session.run.return_value = mock_result

        claim_id = repository.create_claim(
            text="Test claim",
            original_text="Original test claim",
            doc_id="doc-123"
        )

        assert claim_id == 'claim-123'

        # Verify CREATE node query was called
        calls = [call[0][0] for call in session.run.call_args_list]
        assert any('CREATE (n:Claim $props)' in call for call in calls)

        # Verify CONTAINS_CLAIM relationship was created
        assert any('CONTAINS_CLAIM' in call for call in calls)

    def test_create_claim_with_additional_props(self, repository, mock_client):
        """Test create_claim preserves additional properties."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = ['claim-123']
        session.run.return_value = mock_result

        repository.create_claim(
            text="Test",
            original_text="Original",
            doc_id="doc-123",
            quality_score=0.9,
            disposition="central"
        )

        # Find the CREATE call
        create_call = None
        for call in session.run.call_args_list:
            if 'CREATE (n:Claim $props)' in call[0][0]:
                create_call = call
                break

        assert create_call is not None
        props = create_call[0][1]['props']
        assert props['quality_score'] == 0.9
        assert props['disposition'] == 'central'


class TestGetClaim:
    """Test claim retrieval."""

    def test_get_claim_returns_claim_when_found(self, repository, mock_client):
        """Test get_claim returns claim properties."""
        _, session = mock_client

        mock_record = Mock()
        mock_record.data.return_value = {'n': {
            'id': 'claim-123',
            'text': 'Test claim',
            'status': 'complete'
        }}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        claim = repository.get_claim('claim-123')

        assert claim['id'] == 'claim-123'
        assert claim['text'] == 'Test claim'
        assert claim['status'] == 'complete'

    def test_get_claim_returns_none_when_not_found(self, repository, mock_client):
        """Test get_claim returns None for non-existent claim."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        session.run.return_value = mock_result

        claim = repository.get_claim('nonexistent')

        assert claim is None


class TestUpdateClaim:
    """Test claim updates."""

    @patch('backend.database.repositories.base_repository.datetime')
    def test_update_claim_succeeds(self, mock_datetime, repository, mock_client):
        """Test update_claim updates properties."""
        _, session = mock_client
        mock_datetime.utcnow.return_value.isoformat.return_value = '2025-01-01T12:00:00'

        mock_result = Mock()
        mock_result.single.return_value = ['claim-123']
        session.run.return_value = mock_result

        success = repository.update_claim('claim-123', {
            'status': 'complete',
            'summary': 'Updated summary'
        })

        assert success is True

    def test_update_claim_returns_false_when_not_found(self, repository, mock_client):
        """Test update_claim returns False for non-existent claim."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = None
        session.run.return_value = mock_result

        success = repository.update_claim('nonexistent', {'status': 'complete'})

        assert success is False


class TestDeleteClaim:
    """Test claim deletion."""

    def test_delete_claim_succeeds(self, repository, mock_client):
        """Test delete_claim removes claim and relationships."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [1]
        session.run.return_value = mock_result

        success = repository.delete_claim('claim-123')

        assert success is True

        # Verify DETACH DELETE was used
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'DETACH DELETE' in query

    def test_delete_claim_returns_false_when_not_found(self, repository, mock_client):
        """Test delete_claim returns False for non-existent claim."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [0]
        session.run.return_value = mock_result

        success = repository.delete_claim('nonexistent')

        assert success is False


class TestFindClaimsByDocument:
    """Test finding claims by document."""

    def test_find_claims_by_document_returns_all_claims(self, repository, mock_client):
        """Test finding all claims for a document."""
        _, session = mock_client

        mock_record1 = Mock()
        mock_record1.data.return_value = {'c': {'id': 'claim-1', 'text': 'Claim 1'}}
        mock_record2 = Mock()
        mock_record2.data.return_value = {'c': {'id': 'claim-2', 'text': 'Claim 2'}}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record1, mock_record2]))
        session.run.return_value = mock_result

        claims = repository.find_claims_by_document('doc-123')

        assert len(claims) == 2
        assert claims[0]['id'] == 'claim-1'
        assert claims[1]['id'] == 'claim-2'

        # Verify query structure
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'CONTAINS_CLAIM' in query
        assert call_args[0][1]['doc_id'] == 'doc-123'

    def test_find_claims_by_document_with_limit(self, repository, mock_client):
        """Test finding claims with limit."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        session.run.return_value = mock_result

        repository.find_claims_by_document('doc-123', limit=10)

        # Verify LIMIT was added
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'LIMIT 10' in query


class TestFindClaimsByStatus:
    """Test finding claims by status."""

    def test_find_claims_by_status(self, repository, mock_client):
        """Test finding claims by status filter."""
        _, session = mock_client

        mock_record = Mock()
        mock_record.data.return_value = {'n': {'id': 'claim-1', 'status': 'complete'}}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        claims = repository.find_claims_by_status('complete')

        assert len(claims) == 1
        assert claims[0]['status'] == 'complete'


class TestFindClaimsByDisposition:
    """Test finding claims by disposition."""

    def test_find_claims_by_disposition(self, repository, mock_client):
        """Test finding claims by disposition filter."""
        _, session = mock_client

        mock_record = Mock()
        mock_record.data.return_value = {'n': {'id': 'claim-1', 'disposition': 'central'}}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        claims = repository.find_claims_by_disposition('central')

        assert len(claims) == 1
        assert claims[0]['disposition'] == 'central'


class TestGetClaimWithRelationships:
    """Test getting claim with all relationships."""

    def test_get_claim_with_relationships_returns_complete_data(self, repository, mock_client):
        """Test getting claim with children, evidence, and research."""
        _, session = mock_client

        mock_record = Mock()
        mock_record.data.return_value = {
            'c': {'id': 'claim-123', 'text': 'Main claim'},
            'children': [
                {'id': 'child-1', 'text': 'Child claim 1', 'summary': 'Summary 1'},
                {'id': 'child-2', 'text': 'Child claim 2', 'summary': 'Summary 2'}
            ],
            'supporters': [{'id': 'support-1', 'text': 'Supporting claim', 'summary': 'Summary'}],
            'evidence': [{'title': 'Evidence 1', 'url': 'http://example.com', 'credibility': 0.9}],
            'sources': [{'page': 1, 'text': 'Source text'}],
            'research': [{'agent': 'Agent1', 'findings': 'Findings', 'confidence': 0.8, 'status': 'complete'}]
        }

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        claim = repository.get_claim_with_relationships('claim-123')

        assert claim['id'] == 'claim-123'
        assert len(claim['children']) == 2
        assert len(claim['supporters']) == 1
        assert len(claim['evidence']) == 1
        assert len(claim['sources']) == 1
        assert len(claim['research']) == 1

    def test_get_claim_with_relationships_filters_none_values(self, repository, mock_client):
        """Test that None values are filtered from relationships."""
        _, session = mock_client

        mock_record = Mock()
        mock_record.data.return_value = {
            'c': {'id': 'claim-123', 'text': 'Main claim'},
            'children': [{'id': 'child-1', 'text': 'Valid'}, {'id': None}],  # One invalid
            'supporters': [{'id': None}],  # All invalid
            'evidence': [{'title': 'Valid', 'url': 'url'}, {'title': None}],  # One invalid
            'sources': [{'page': None}],  # All invalid
            'research': [{'agent': None}]  # All invalid
        }

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        claim = repository.get_claim_with_relationships('claim-123')

        assert len(claim['children']) == 1  # Filtered one None
        assert len(claim['supporters']) == 0  # Filtered all
        assert len(claim['evidence']) == 1  # Filtered one None
        assert len(claim['sources']) == 0  # Filtered all
        assert len(claim['research']) == 0  # Filtered all

    def test_get_claim_with_relationships_returns_none_when_not_found(self, repository, mock_client):
        """Test returns None when claim doesn't exist."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        session.run.return_value = mock_result

        claim = repository.get_claim_with_relationships('nonexistent')

        assert claim is None


class TestCreateClaimRelationship:
    """Test creating relationships between claims."""

    def test_create_claim_relationship_succeeds(self, repository, mock_client):
        """Test creating relationship between claims."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [123]
        session.run.return_value = mock_result

        success = repository.create_claim_relationship(
            'claim-1',
            'claim-2',
            'SUPPORTS',
            {'confidence': 0.9}
        )

        assert success is True

        # Verify relationship creation
        call_args = session.run.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert 'SUPPORTS' in query
        assert params['from_id'] == 'claim-1'
        assert params['to_id'] == 'claim-2'
        assert params['props']['confidence'] == 0.9


class TestFindSimilarClaims:
    """Test finding similar claims."""

    def test_find_similar_claims_returns_sorted_results(self, repository, mock_client):
        """Test finding similar claims sorted by similarity."""
        _, session = mock_client

        mock_record1 = Mock()
        mock_record1.data.return_value = {
            'similar': {'id': 'claim-2', 'text': 'Similar claim 2'},
            'similarity': 0.95
        }
        mock_record2 = Mock()
        mock_record2.data.return_value = {
            'similar': {'id': 'claim-3', 'text': 'Similar claim 3'},
            'similarity': 0.85
        }

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record1, mock_record2]))
        session.run.return_value = mock_result

        similar = repository.find_similar_claims('claim-1', min_similarity=0.7, limit=10)

        assert len(similar) == 2
        assert similar[0]['id'] == 'claim-2'
        assert similar[0]['similarity'] == 0.95
        assert similar[1]['similarity'] == 0.85

        # Verify query parameters
        call_args = session.run.call_args
        params = call_args[0][1]
        assert params['min_similarity'] == 0.7
        assert params['limit'] == 10


class TestGetClaimCluster:
    """Test getting claim clusters."""

    def test_get_claim_cluster_returns_all_cluster_members(self, repository, mock_client):
        """Test getting all claims in cluster."""
        _, session = mock_client

        mock_record1 = Mock()
        mock_record1.data.return_value = {'id': 'claim-2'}
        mock_record2 = Mock()
        mock_record2.data.return_value = {'id': 'claim-3'}
        mock_record3 = Mock()
        mock_record3.data.return_value = {'id': 'claim-4'}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record1, mock_record2, mock_record3]))
        session.run.return_value = mock_result

        cluster = repository.get_claim_cluster('claim-1')

        assert len(cluster) == 3
        assert 'claim-2' in cluster
        assert 'claim-3' in cluster
        assert 'claim-4' in cluster

        # Verify query uses SIMILAR_TO relationship
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'SIMILAR_TO' in query


class TestGetSuperClaims:
    """Test getting super-claims."""

    def test_get_super_claims_returns_only_super_claims(self, repository, mock_client):
        """Test getting super-claims for document."""
        _, session = mock_client

        mock_record1 = Mock()
        mock_record1.data.return_value = {'c': {'id': 'super-1', 'claim_type': 'super_claim'}}
        mock_record2 = Mock()
        mock_record2.data.return_value = {'c': {'id': 'super-2', 'is_super_claim': True}}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record1, mock_record2]))
        session.run.return_value = mock_result

        super_claims = repository.get_super_claims('doc-123')

        assert len(super_claims) == 2
        assert super_claims[0]['id'] == 'super-1'
        assert super_claims[1]['id'] == 'super-2'


class TestGetClaimHierarchy:
    """Test getting claim hierarchy."""

    def test_get_claim_hierarchy_returns_nested_structure(self, repository, mock_client):
        """Test getting claim with children hierarchy."""
        _, session = mock_client

        mock_record = Mock()
        mock_record.data.return_value = {
            'c': {'id': 'parent', 'text': 'Parent claim'},
            'children': [
                {'id': 'child-1', 'text': 'Child 1'},
                {'id': 'child-2', 'text': 'Child 2'}
            ]
        }

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        hierarchy = repository.get_claim_hierarchy('parent', max_depth=3)

        assert hierarchy['id'] == 'parent'
        assert len(hierarchy['children']) == 2
        assert hierarchy['children'][0]['id'] == 'child-1'

        # Verify max_depth was used in query
        call_args = session.run.call_args
        query = call_args[0][0]
        assert '*0..3' in query


class TestCountMethods:
    """Test counting methods."""

    def test_count_claims_by_document(self, repository, mock_client):
        """Test counting claims for document."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [5]
        session.run.return_value = mock_result

        count = repository.count_claims_by_document('doc-123')

        assert count == 5

    def test_count_claims_by_status(self, repository, mock_client):
        """Test counting claims by status."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [3]
        session.run.return_value = mock_result

        count = repository.count_claims_by_status('complete')

        assert count == 3

    def test_count_returns_zero_when_none(self, repository, mock_client):
        """Test count returns 0 when result is None."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = None
        session.run.return_value = mock_result

        count = repository.count_claims_by_document('empty-doc')

        assert count == 0
