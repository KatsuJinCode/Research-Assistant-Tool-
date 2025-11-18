"""Tests for PostgreSQL connector."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import psycopg2

from research_assistant_db.connectors.postgres import (
    PostgreSQLConnector,
    PostgreSQLTransaction,
)


class TestPostgreSQLTransaction:
    """Tests for PostgreSQLTransaction."""

    def test_commit(self):
        """Test committing a transaction."""
        mock_conn = Mock()
        transaction = PostgreSQLTransaction(mock_conn)

        transaction.commit()

        mock_conn.commit.assert_called_once()
        assert transaction._committed is True

    def test_rollback(self):
        """Test rolling back a transaction."""
        mock_conn = Mock()
        transaction = PostgreSQLTransaction(mock_conn)

        transaction.rollback()

        mock_conn.rollback.assert_called_once()
        assert transaction._rolled_back is True

    def test_commit_after_rollback_does_nothing(self):
        """Test that commit after rollback does nothing."""
        mock_conn = Mock()
        transaction = PostgreSQLTransaction(mock_conn)

        transaction.rollback()
        transaction.commit()

        # Only rollback should be called
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    def test_rollback_after_commit_does_nothing(self):
        """Test that rollback after commit does nothing."""
        mock_conn = Mock()
        transaction = PostgreSQLTransaction(mock_conn)

        transaction.commit()
        transaction.rollback()

        # Only commit should be called
        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()


class TestPostgreSQLConnector:
    """Tests for PostgreSQLConnector."""

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_connect(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test establishing database connection."""
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)
        connector.connect()

        mock_connect.assert_called_once()
        assert connector.is_connected() is True

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_connect_already_connected(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test that connect() does nothing if already connected."""
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)
        connector.connect()
        connector.connect()  # Second connect

        # Should only connect once
        mock_connect.assert_called_once()

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_disconnect(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test closing database connection."""
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)
        connector.connect()
        connector.disconnect()

        mock_psycopg2_connection.close.assert_called_once()
        assert connector._connection is None

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_is_connected_when_not_connected(self, mock_connect, db_config):
        """Test is_connected() when not connected."""
        connector = PostgreSQLConnector(**db_config)
        assert connector.is_connected() is False

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_execute_with_fetch(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test executing query with fetch=True."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_cursor.fetchall = Mock(return_value=[
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ])

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)
        result = connector.execute("SELECT * FROM users", fetch=True)

        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        mock_cursor.execute.assert_called_once()

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_execute_without_fetch(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test executing query with fetch=False."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)
        result = connector.execute("INSERT INTO users (name) VALUES ('Alice')")

        assert result is None
        mock_cursor.execute.assert_called_once()
        mock_psycopg2_connection.commit.assert_called_once()

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_execute_with_params(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test executing query with parameters."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_cursor.fetchall = Mock(return_value=[])  # Add fetchall return value

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)
        connector.execute("SELECT * FROM users WHERE id = %s", params=(1,), fetch=True)

        mock_cursor.execute.assert_called_with("SELECT * FROM users WHERE id = %s", (1,))

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_execute_many(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test executing query with multiple parameter sets."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)
        params_list = [(1, "Alice"), (2, "Bob")]
        connector.execute_many("INSERT INTO users (id, name) VALUES (%s, %s)", params_list)

        mock_cursor.executemany.assert_called_once()
        mock_psycopg2_connection.commit.assert_called_once()

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_fetch_one(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test fetching a single row."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_cursor.fetchone = Mock(return_value={"id": 1, "name": "Alice"})

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)
        result = connector.fetch_one("SELECT * FROM users WHERE id = 1")

        assert result == {"id": 1, "name": "Alice"}
        mock_cursor.execute.assert_called_once()

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_fetch_one_no_results(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test fetch_one when no results."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_cursor.fetchone = Mock(return_value=None)

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)
        result = connector.fetch_one("SELECT * FROM users WHERE id = 999")

        assert result is None

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_fetch_all(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test fetching all rows."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_cursor.fetchall = Mock(return_value=[
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ])

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)
        result = connector.fetch_all("SELECT * FROM users")

        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_transaction_commit(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test transaction with manual commit."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)

        with connector.transaction() as tx:
            connector.execute("INSERT INTO users (name) VALUES ('Alice')")
            tx.commit()

        mock_psycopg2_connection.commit.assert_called()

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_transaction_rollback(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test transaction with manual rollback."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)

        with connector.transaction() as tx:
            connector.execute("INSERT INTO users (name) VALUES ('Alice')")
            tx.rollback()

        mock_psycopg2_connection.rollback.assert_called()

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_transaction_auto_commit(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test transaction with automatic commit."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)

        with connector.transaction():
            connector.execute("INSERT INTO users (name) VALUES ('Alice')")

        # Should auto-commit
        mock_psycopg2_connection.commit.assert_called()

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_transaction_auto_rollback_on_exception(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test transaction with automatic rollback on exception."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_cursor.execute = Mock(side_effect=Exception("DB error"))

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)

        with pytest.raises(Exception, match="DB error"):
            with connector.transaction():
                connector.execute("INSERT INTO users (name) VALUES ('Alice')")

        # Should auto-rollback
        mock_psycopg2_connection.rollback.assert_called()

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_ping_success(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test successful ping."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)
        result = connector.ping()

        assert result is True
        mock_cursor.execute.assert_called_with("SELECT 1")

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_ping_failure(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test failed ping."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_cursor.execute = Mock(side_effect=Exception("Connection lost"))

        mock_psycopg2_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_psycopg2_connection

        connector = PostgreSQLConnector(**db_config)
        result = connector.ping()

        assert result is False

    @patch("research_assistant_db.connectors.postgres.psycopg2.connect")
    def test_context_manager(self, mock_connect, db_config, mock_psycopg2_connection):
        """Test using connector as context manager."""
        mock_connect.return_value = mock_psycopg2_connection

        with PostgreSQLConnector(**db_config) as connector:
            assert connector.is_connected() is True

        mock_psycopg2_connection.close.assert_called_once()
