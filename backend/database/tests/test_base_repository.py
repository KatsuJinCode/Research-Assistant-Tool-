"""
Unit tests for BaseRepository.

Tests common CRUD operations, error handling, and query execution.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from backend.database.repositories.base_repository import BaseRepository


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
    return BaseRepository(client=client)


class TestBaseRepositoryInitialization:
    """Test repository initialization."""

    def test_initialization_with_client(self, mock_client):
        """Test repository accepts custom client."""
        client, _ = mock_client
        repo = BaseRepository(client=client)
        assert repo.client is client

    @patch('backend.database.repositories.base_repository.Neo4jClient')
    def test_initialization_without_client_uses_singleton(self, mock_neo4j_client):
        """Test repository uses singleton when no client provided."""
        repo = BaseRepository()
        mock_neo4j_client.assert_called_once()


class TestExecuteQuery:
    """Test query execution."""

    def test_execute_query_returns_results(self, repository, mock_client):
        """Test execute_query returns list of dictionaries."""
        _, session = mock_client

        # Mock result
        mock_record1 = Mock()
        mock_record1.data.return_value = {'id': '1', 'name': 'Test'}
        mock_record2 = Mock()
        mock_record2.data.return_value = {'id': '2', 'name': 'Test2'}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record1, mock_record2]))
        session.run.return_value = mock_result

        results = repository.execute_query("MATCH (n) RETURN n", {'limit': 10})

        assert len(results) == 2
        assert results[0] == {'id': '1', 'name': 'Test'}
        assert results[1] == {'id': '2', 'name': 'Test2'}
        session.run.assert_called_once_with("MATCH (n) RETURN n", {'limit': 10})

    def test_execute_query_with_no_parameters(self, repository, mock_client):
        """Test execute_query works without parameters."""
        _, session = mock_client
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        session.run.return_value = mock_result

        results = repository.execute_query("MATCH (n) RETURN n")

        assert results == []
        session.run.assert_called_once_with("MATCH (n) RETURN n", {})

    def test_execute_query_handles_errors(self, repository, mock_client):
        """Test execute_query raises on errors."""
        _, session = mock_client
        session.run.side_effect = Exception("Connection error")

        with pytest.raises(Exception, match="Connection error"):
            repository.execute_query("INVALID QUERY")


class TestExecuteWrite:
    """Test write query execution."""

    def test_execute_write_returns_single_value(self, repository, mock_client):
        """Test execute_write returns single result value."""
        _, session = mock_client

        mock_record = Mock()
        mock_record.__getitem__ = Mock(return_value='123')

        mock_result = Mock()
        mock_result.single.return_value = mock_record
        session.run.return_value = mock_result

        result = repository.execute_write("CREATE (n) RETURN n.id", {'id': '123'})

        assert result == '123'
        session.run.assert_called_once()

    def test_execute_write_returns_none_when_no_result(self, repository, mock_client):
        """Test execute_write returns None when no results."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = None
        session.run.return_value = mock_result

        result = repository.execute_write("CREATE (n)")

        assert result is None

    def test_execute_write_handles_errors(self, repository, mock_client):
        """Test execute_write raises on errors."""
        _, session = mock_client
        session.run.side_effect = Exception("Write failed")

        with pytest.raises(Exception, match="Write failed"):
            repository.execute_write("CREATE (n)")


class TestCreateNode:
    """Test node creation."""

    @patch('backend.database.repositories.base_repository.uuid4')
    @patch('backend.database.repositories.base_repository.datetime')
    def test_create_node_adds_id_and_timestamp(self, mock_datetime, mock_uuid, repository, mock_client):
        """Test create_node adds ID and timestamp automatically."""
        _, session = mock_client

        # Mock UUID and timestamp
        mock_uuid.return_value = '12345'
        mock_datetime.utcnow.return_value.isoformat.return_value = '2025-01-01T00:00:00'

        mock_result = Mock()
        mock_result.single.return_value = ['12345']
        session.run.return_value = mock_result

        node_id = repository.create_node('TestLabel', {'name': 'Test'})

        assert node_id == '12345'

        # Verify query called with correct properties
        call_args = session.run.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert 'CREATE (n:TestLabel $props)' in query
        assert params['props']['id'] == '12345'
        assert params['props']['created_at'] == '2025-01-01T00:00:00'
        assert params['props']['name'] == 'Test'

    def test_create_node_preserves_existing_id(self, repository, mock_client):
        """Test create_node preserves existing ID."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = ['existing-id']
        session.run.return_value = mock_result

        node_id = repository.create_node('TestLabel', {
            'id': 'existing-id',
            'name': 'Test'
        })

        assert node_id == 'existing-id'

        # Verify existing ID was used
        call_args = session.run.call_args
        params = call_args[0][1]
        assert params['props']['id'] == 'existing-id'


class TestGetNodeById:
    """Test node retrieval."""

    def test_get_node_by_id_returns_node_when_found(self, repository, mock_client):
        """Test get_node_by_id returns node properties."""
        _, session = mock_client

        mock_record = Mock()
        mock_record.data.return_value = {'n': {'id': '123', 'name': 'Test'}}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        node = repository.get_node_by_id('TestLabel', '123')

        assert node == {'id': '123', 'name': 'Test'}

    def test_get_node_by_id_returns_none_when_not_found(self, repository, mock_client):
        """Test get_node_by_id returns None when node doesn't exist."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        session.run.return_value = mock_result

        node = repository.get_node_by_id('TestLabel', '999')

        assert node is None


class TestUpdateNode:
    """Test node updates."""

    @patch('backend.database.repositories.base_repository.datetime')
    def test_update_node_adds_updated_timestamp(self, mock_datetime, repository, mock_client):
        """Test update_node adds updated_at timestamp."""
        _, session = mock_client

        mock_datetime.utcnow.return_value.isoformat.return_value = '2025-01-01T12:00:00'

        mock_result = Mock()
        mock_result.single.return_value = ['123']
        session.run.return_value = mock_result

        success = repository.update_node('TestLabel', '123', {'name': 'Updated'})

        assert success is True

        # Verify updated_at was added
        call_args = session.run.call_args
        params = call_args[0][1]
        assert params['updates']['updated_at'] == '2025-01-01T12:00:00'
        assert params['updates']['name'] == 'Updated'

    def test_update_node_returns_false_when_not_found(self, repository, mock_client):
        """Test update_node returns False when node doesn't exist."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = None
        session.run.return_value = mock_result

        success = repository.update_node('TestLabel', '999', {'name': 'Updated'})

        assert success is False


class TestDeleteNode:
    """Test node deletion."""

    def test_delete_node_returns_true_when_deleted(self, repository, mock_client):
        """Test delete_node returns True when node exists."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [1]  # 1 node deleted
        session.run.return_value = mock_result

        success = repository.delete_node('TestLabel', '123')

        assert success is True

        # Verify DETACH DELETE was used
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'DETACH DELETE' in query

    def test_delete_node_returns_false_when_not_found(self, repository, mock_client):
        """Test delete_node returns False when node doesn't exist."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [0]  # 0 nodes deleted
        session.run.return_value = mock_result

        success = repository.delete_node('TestLabel', '999')

        assert success is False


class TestFindNodes:
    """Test finding nodes with filters."""

    def test_find_nodes_with_filters(self, repository, mock_client):
        """Test find_nodes applies filters correctly."""
        _, session = mock_client

        mock_record1 = Mock()
        mock_record1.data.return_value = {'n': {'id': '1', 'status': 'active'}}
        mock_record2 = Mock()
        mock_record2.data.return_value = {'n': {'id': '2', 'status': 'active'}}

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record1, mock_record2]))
        session.run.return_value = mock_result

        nodes = repository.find_nodes('TestLabel', {'status': 'active'})

        assert len(nodes) == 2
        assert nodes[0]['status'] == 'active'

        # Verify WHERE clause was built
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'WHERE n.status = $status' in query

    def test_find_nodes_with_limit(self, repository, mock_client):
        """Test find_nodes respects limit parameter."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        session.run.return_value = mock_result

        repository.find_nodes('TestLabel', {}, limit=10)

        # Verify LIMIT was added
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'LIMIT 10' in query

    def test_find_nodes_without_limit(self, repository, mock_client):
        """Test find_nodes works without limit."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        session.run.return_value = mock_result

        repository.find_nodes('TestLabel', {})

        # Verify no LIMIT clause
        call_args = session.run.call_args
        query = call_args[0][0]
        assert 'LIMIT' not in query


class TestCreateRelationship:
    """Test relationship creation."""

    def test_create_relationship_succeeds(self, repository, mock_client):
        """Test create_relationship creates relationship."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [123]  # Relationship ID
        session.run.return_value = mock_result

        success = repository.create_relationship(
            'node-1',
            'node-2',
            'RELATES_TO',
            {'weight': 0.8}
        )

        assert success is True

        # Verify query structure
        call_args = session.run.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert 'CREATE (a)-[r:RELATES_TO $props]->(b)' in query
        assert params['from_id'] == 'node-1'
        assert params['to_id'] == 'node-2'
        assert params['props']['weight'] == 0.8

    def test_create_relationship_without_properties(self, repository, mock_client):
        """Test create_relationship works without properties."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = [123]
        session.run.return_value = mock_result

        success = repository.create_relationship('node-1', 'node-2', 'RELATES_TO')

        assert success is True

        # Verify empty properties
        call_args = session.run.call_args
        params = call_args[0][1]
        assert params['props'] == {}

    def test_create_relationship_returns_false_when_nodes_not_found(self, repository, mock_client):
        """Test create_relationship returns False when nodes don't exist."""
        _, session = mock_client

        mock_result = Mock()
        mock_result.single.return_value = None  # No relationship created
        session.run.return_value = mock_result

        success = repository.create_relationship('invalid-1', 'invalid-2', 'RELATES_TO')

        assert success is False
