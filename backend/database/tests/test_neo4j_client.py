"""
Unit tests for Neo4jClient singleton.

Tests connection management, singleton behavior, and error handling.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from backend.database.neo4j_client import Neo4jClient


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton before each test."""
    Neo4jClient.reset_instance()
    yield
    Neo4jClient.reset_instance()


@pytest.fixture
def mock_driver():
    """Create mock Neo4j driver."""
    driver = Mock()
    driver.verify_connectivity = Mock()
    driver.session = Mock()
    driver.close = Mock()
    return driver


class TestNeo4jClientSingleton:
    """Test singleton pattern behavior."""

    @patch('backend.database.neo4j_client.GraphDatabase')
    def test_singleton_creates_only_one_instance(self, mock_graph_db, mock_driver):
        """Test that multiple calls return same instance."""
        mock_graph_db.driver.return_value = mock_driver

        client1 = Neo4jClient()
        client2 = Neo4jClient()

        assert client1 is client2
        # Driver should only be created once
        assert mock_graph_db.driver.call_count == 1

    @patch('backend.database.neo4j_client.GraphDatabase')
    def test_singleton_reset_allows_new_instance(self, mock_graph_db, mock_driver):
        """Test that reset allows creating fresh instance."""
        mock_graph_db.driver.return_value = mock_driver

        client1 = Neo4jClient()
        Neo4jClient.reset_instance()
        client2 = Neo4jClient()

        # Should be different instances after reset
        assert client1 is not client2
        # Driver should be created twice (once per instance)
        assert mock_graph_db.driver.call_count == 2


class TestNeo4jClientInitialization:
    """Test client initialization and configuration."""

    @patch('backend.database.neo4j_client.GraphDatabase')
    @patch.dict(os.environ, {
        'NEO4J_URI': 'bolt://test:7687',
        'NEO4J_USER': 'testuser',
        'NEO4J_PASSWORD': 'testpass',
        'NEO4J_DATABASE': 'testdb'
    })
    def test_initialization_uses_environment_variables(self, mock_graph_db, mock_driver):
        """Test that initialization reads from environment."""
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient()

        assert client.uri == 'bolt://test:7687'
        assert client.user == 'testuser'
        assert client.password == 'testpass'
        assert client.database == 'testdb'

        mock_graph_db.driver.assert_called_once_with(
            'bolt://test:7687',
            auth=('testuser', 'testpass')
        )

    @patch('backend.database.neo4j_client.GraphDatabase')
    def test_initialization_uses_defaults_when_env_not_set(self, mock_graph_db, mock_driver):
        """Test that initialization uses defaults when env vars missing."""
        mock_graph_db.driver.return_value = mock_driver

        with patch.dict(os.environ, {}, clear=True):
            client = Neo4jClient()

        assert client.uri == 'bolt://localhost:7687'
        assert client.user == 'neo4j'
        assert client.password == 'neo4j'
        assert client.database == 'neo4j'

    @patch('backend.database.neo4j_client.GraphDatabase')
    def test_initialization_verifies_connectivity(self, mock_graph_db, mock_driver):
        """Test that initialization verifies database connectivity."""
        mock_graph_db.driver.return_value = mock_driver

        Neo4jClient()

        mock_driver.verify_connectivity.assert_called_once()

    @patch('backend.database.neo4j_client.GraphDatabase')
    def test_initialization_raises_on_connection_failure(self, mock_graph_db, mock_driver):
        """Test that connection failures are raised."""
        mock_driver.verify_connectivity.side_effect = Exception("Connection failed")
        mock_graph_db.driver.return_value = mock_driver

        with pytest.raises(Exception, match="Connection failed"):
            Neo4jClient()

    def test_initialization_raises_when_neo4j_not_installed(self):
        """Test that missing neo4j package raises clear error."""
        with patch('backend.database.neo4j_client.GraphDatabase', side_effect=ImportError):
            with pytest.raises(ImportError, match="Neo4j driver not installed"):
                Neo4jClient()


class TestNeo4jClientMethods:
    """Test client methods and properties."""

    @patch('backend.database.neo4j_client.GraphDatabase')
    def test_driver_property_returns_driver(self, mock_graph_db, mock_driver):
        """Test driver property returns initialized driver."""
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient()

        assert client.driver is mock_driver

    @patch('backend.database.neo4j_client.GraphDatabase')
    def test_get_session_creates_session_with_correct_database(self, mock_graph_db, mock_driver):
        """Test get_session creates session with configured database."""
        mock_session = Mock()
        mock_driver.session.return_value = mock_session
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient()
        session = client.get_session()

        mock_driver.session.assert_called_once_with(database='neo4j')
        assert session is mock_session

    @patch('backend.database.neo4j_client.GraphDatabase')
    def test_get_session_passes_additional_kwargs(self, mock_graph_db, mock_driver):
        """Test get_session passes through additional parameters."""
        mock_session = Mock()
        mock_driver.session.return_value = mock_session
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient()
        session = client.get_session(default_access_mode='READ')

        mock_driver.session.assert_called_once_with(
            database='neo4j',
            default_access_mode='READ'
        )

    @patch('backend.database.neo4j_client.GraphDatabase')
    def test_close_closes_driver(self, mock_graph_db, mock_driver):
        """Test close method closes the driver."""
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient()
        client.close()

        mock_driver.close.assert_called_once()
        assert client._driver is None

    @patch('backend.database.neo4j_client.GraphDatabase')
    def test_context_manager_does_not_close_connection(self, mock_graph_db, mock_driver):
        """Test context manager preserves connection (singleton pattern)."""
        mock_graph_db.driver.return_value = mock_driver

        with Neo4jClient() as client:
            pass

        # Should NOT close (singleton stays alive)
        mock_driver.close.assert_not_called()
        assert client._driver is mock_driver


class TestNeo4jClientErrorHandling:
    """Test error handling and edge cases."""

    def test_driver_property_raises_when_not_initialized(self):
        """Test accessing driver before initialization raises error."""
        # Manually create instance without initialization
        client = object.__new__(Neo4jClient)
        client._driver = None

        with pytest.raises(RuntimeError, match="Neo4j driver not initialized"):
            _ = client.driver

    @patch('backend.database.neo4j_client.GraphDatabase')
    def test_double_close_is_safe(self, mock_graph_db, mock_driver):
        """Test calling close multiple times doesn't error."""
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient()
        client.close()
        client.close()  # Should not raise

        # Close should only be called once
        assert mock_driver.close.call_count == 1
