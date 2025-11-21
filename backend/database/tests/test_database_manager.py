"""
Unit tests for DatabaseManager - Neo4j Multi-Database Management
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch
from backend.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class TestDatabaseManager:
    """Test DatabaseManager database lifecycle operations."""

    @pytest.fixture
    def mock_driver(self):
        """Create a mock Neo4j driver."""
        driver = Mock()
        return driver

    @pytest.fixture
    def db_manager(self, mock_driver):
        """Create a DatabaseManager instance with mock driver."""
        return DatabaseManager(mock_driver)

    def test_initialization(self, db_manager):
        """Test DatabaseManager initialization."""
        assert db_manager.driver is not None
        assert db_manager.active_database == DatabaseManager.SYSTEM_DATABASE
        assert db_manager.active_database == "neo4j"

    def test_set_active_database(self, db_manager):
        """Test setting active database."""
        db_manager.set_active_database("project_test")
        assert db_manager.active_database == "project_test"

    def test_sanitize_database_name_basic(self):
        """Test basic database name sanitization."""
        result = DatabaseManager.sanitize_database_name("My Project")
        assert result == "project_my_project"

    def test_sanitize_database_name_special_chars(self):
        """Test sanitizing names with special characters."""
        result = DatabaseManager.sanitize_database_name("Test@#$%Project!")
        assert result == "project_test_project"

    def test_sanitize_database_name_consecutive_underscores(self):
        """Test removing consecutive underscores."""
        result = DatabaseManager.sanitize_database_name("Test___Project")
        assert result == "project_test_project"

    def test_sanitize_database_name_leading_number(self):
        """Test handling names that start with numbers."""
        result = DatabaseManager.sanitize_database_name("123 Project")
        assert result == "project__123_project"

    def test_sanitize_database_name_max_length(self):
        """Test truncating long names."""
        long_name = "a" * 100
        result = DatabaseManager.sanitize_database_name(long_name)
        assert len(result) <= 63

    def test_sanitize_database_name_lowercase(self):
        """Test converting to lowercase."""
        result = DatabaseManager.sanitize_database_name("MyProject")
        assert result == "project_myproject"
        assert result.islower()

    def test_get_session_default_database(self, db_manager, mock_driver):
        """Test getting session with default (active) database."""
        mock_session = Mock()
        mock_driver.session.return_value = mock_session

        db_manager.set_active_database("project_test")
        session = db_manager.get_session()

        mock_driver.session.assert_called_once_with(database="project_test")

    def test_get_session_specific_database(self, db_manager, mock_driver):
        """Test getting session with specific database override."""
        mock_session = Mock()
        mock_driver.session.return_value = mock_session

        db_manager.set_active_database("project_test")
        session = db_manager.get_session(database="project_other")

        mock_driver.session.assert_called_once_with(database="project_other")

    def test_list_databases(self, db_manager, mock_driver):
        """Test listing all databases."""
        # Mock session with context manager support
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=False)
        mock_driver.session.return_value = mock_context

        # Mock result - create proper mock records
        mock_records = [
            Mock(get=lambda k, d=None: {
                'name': 'neo4j',
                'type': 'system',
                'default': True,
                'currentStatus': 'online',
                'requestedStatus': 'online'
            }.get(k, d)),
            Mock(get=lambda k, d=None: {
                'name': 'project_test',
                'type': 'standard',
                'default': False,
                'currentStatus': 'online',
                'requestedStatus': 'online'
            }.get(k, d))
        ]

        mock_result = MagicMock()
        mock_result.__iter__.return_value = iter(mock_records)
        mock_session.run.return_value = mock_result

        databases = db_manager.list_databases()

        assert len(databases) == 2
        assert databases[0]['name'] == 'neo4j'
        assert databases[1]['name'] == 'project_test'

    def test_database_exists_true(self, db_manager):
        """Test checking if database exists (positive case)."""
        with patch.object(db_manager, 'list_databases') as mock_list:
            mock_list.return_value = [
                {'name': 'neo4j'},
                {'name': 'project_test'}
            ]

            assert db_manager.database_exists('project_test') is True

    def test_database_exists_false(self, db_manager):
        """Test checking if database exists (negative case)."""
        with patch.object(db_manager, 'list_databases') as mock_list:
            mock_list.return_value = [
                {'name': 'neo4j'}
            ]

            assert db_manager.database_exists('project_test') is False

    def test_create_database_success(self, db_manager, mock_driver):
        """Test creating a new database successfully."""
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=False)
        mock_driver.session.return_value = mock_context

        with patch.object(db_manager, 'database_exists', return_value=False):
            result = db_manager.create_database('project_test')

            assert result is True
            mock_session.run.assert_called_once()
            call_args = mock_session.run.call_args[0][0]
            assert 'CREATE DATABASE' in call_args
            assert 'project_test' in call_args
            assert 'WAIT' in call_args

    def test_create_database_already_exists(self, db_manager):
        """Test creating a database that already exists."""
        with patch.object(db_manager, 'database_exists', return_value=True):
            result = db_manager.create_database('project_test')
            assert result is True  # Returns True if already exists

    def test_create_database_no_wait(self, db_manager, mock_driver):
        """Test creating database without WAIT option."""
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=False)
        mock_driver.session.return_value = mock_context

        with patch.object(db_manager, 'database_exists', return_value=False):
            result = db_manager.create_database('project_test', wait=False)

            call_args = mock_session.run.call_args[0][0]
            assert 'WAIT' not in call_args

    def test_drop_database_success(self, db_manager, mock_driver):
        """Test dropping a database successfully."""
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=False)
        mock_driver.session.return_value = mock_context

        with patch.object(db_manager, 'database_exists', return_value=True):
            result = db_manager.drop_database('project_test')

            assert result is True
            mock_session.run.assert_called_once()
            call_args = mock_session.run.call_args[0][0]
            assert 'DROP DATABASE' in call_args
            assert 'project_test' in call_args

    def test_drop_database_reserved_name(self, db_manager):
        """Test that reserved databases cannot be dropped."""
        result = db_manager.drop_database('neo4j')
        assert result is False

        result = db_manager.drop_database('system')
        assert result is False

    def test_drop_database_not_exists(self, db_manager):
        """Test dropping a database that doesn't exist."""
        with patch.object(db_manager, 'database_exists', return_value=False):
            result = db_manager.drop_database('project_test')
            assert result is True  # Returns True if doesn't exist

    def test_initialize_database_schema(self, db_manager, mock_driver):
        """Test initializing database schema with indexes."""
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=False)
        mock_driver.session.return_value = mock_context

        result = db_manager.initialize_database_schema('project_test')

        assert result is True
        # Should create multiple indexes
        assert mock_session.run.call_count >= 5  # At least 5 indexes

        # Check that index queries were executed
        calls = [call[0][0] for call in mock_session.run.call_args_list]
        assert any('claim_id_index' in call for call in calls)
        assert any('document_id_index' in call for call in calls)
        assert any('evidence_id_index' in call for call in calls)

    def test_get_database_stats(self, db_manager, mock_driver):
        """Test getting database statistics."""
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=False)
        mock_driver.session.return_value = mock_context

        # Mock node count result
        mock_node_records = [
            {'label': 'Document', 'count': 5},
            {'label': 'Claim', 'count': 10},
            {'label': 'Evidence', 'count': 3}
        ]
        mock_node_result = MagicMock()
        mock_node_result.__iter__.return_value = iter([
            Mock(__getitem__=lambda self, k, r=rec: r[k]) for rec in mock_node_records
        ])

        # Mock relationship count result
        mock_rel_result = MagicMock()
        mock_rel_record = Mock()
        mock_rel_record.__getitem__ = lambda self, key: 8
        mock_rel_result.single.return_value = mock_rel_record

        mock_session.run.side_effect = [mock_node_result, mock_rel_result]

        stats = db_manager.get_database_stats('project_test')

        assert stats['total_nodes'] == 18
        assert stats['total_relationships'] == 8
        assert stats['document_count'] == 5
        assert stats['claim_count'] == 10
        assert stats['evidence_count'] == 3

    def test_get_database_stats_empty_database(self, db_manager, mock_driver):
        """Test getting stats for empty database."""
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=False)
        mock_driver.session.return_value = mock_context

        # Mock empty results
        mock_node_result = MagicMock()
        mock_node_result.__iter__.return_value = iter([])

        mock_rel_result = MagicMock()
        mock_rel_record = Mock()
        mock_rel_record.__getitem__ = lambda self, key: 0
        mock_rel_result.single.return_value = mock_rel_record

        mock_session.run.side_effect = [mock_node_result, mock_rel_result]

        stats = db_manager.get_database_stats('project_test')

        assert stats['total_nodes'] == 0
        assert stats['total_relationships'] == 0
        assert stats['document_count'] == 0
        assert stats['claim_count'] == 0
        assert stats['evidence_count'] == 0


class TestDatabaseManagerIntegration:
    """Integration tests that require actual Neo4j instance."""

    @pytest.fixture
    def real_db_manager(self):
        """Create DatabaseManager with real Neo4j connection."""
        try:
            from backend.database.neo4j_client import Neo4jClient
            client = Neo4jClient()
            return client.database_manager
        except Exception as e:
            pytest.skip(f"Neo4j not available: {e}")

    @pytest.mark.integration
    def test_create_and_drop_database_real(self, real_db_manager):
        """Test creating and dropping a real database."""
        test_db_name = "project_integration_test"

        try:
            # Create database
            result = real_db_manager.create_database(test_db_name, wait=True)
            assert result is True

            # Verify it exists
            assert real_db_manager.database_exists(test_db_name) is True

            # Drop database
            result = real_db_manager.drop_database(test_db_name)
            assert result is True

            # Verify it's gone
            assert real_db_manager.database_exists(test_db_name) is False

        finally:
            # Cleanup in case test failed
            real_db_manager.drop_database(test_db_name)

    @pytest.mark.integration
    def test_initialize_schema_real(self, real_db_manager):
        """Test initializing schema on real database."""
        test_db_name = "project_schema_test"

        try:
            # Create database
            real_db_manager.create_database(test_db_name, wait=True)

            # Initialize schema
            result = real_db_manager.initialize_database_schema(test_db_name)
            assert result is True

            # Get stats (should be empty but have indexes)
            stats = real_db_manager.get_database_stats(test_db_name)
            assert stats['total_nodes'] == 0
            assert stats['total_relationships'] == 0

        finally:
            real_db_manager.drop_database(test_db_name)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
