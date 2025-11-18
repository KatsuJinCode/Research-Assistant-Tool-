"""Tests for async PostgreSQL connector."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from research_assistant_db.connectors.postgres_async import (
    AsyncPostgreSQLConnector,
    AsyncPostgreSQLTransaction,
)


class TestAsyncPostgreSQLTransaction:
    """Tests for AsyncPostgreSQLTransaction."""

    @pytest.mark.asyncio
    async def test_async_commit(self):
        """Test committing an async transaction."""
        mock_tx = AsyncMock()
        transaction = AsyncPostgreSQLTransaction(mock_tx)

        await transaction.commit()

        mock_tx.commit.assert_called_once()
        assert transaction._committed is True

    @pytest.mark.asyncio
    async def test_async_rollback(self):
        """Test rolling back an async transaction."""
        mock_tx = AsyncMock()
        transaction = AsyncPostgreSQLTransaction(mock_tx)

        await transaction.rollback()

        mock_tx.rollback.assert_called_once()
        assert transaction._rolled_back is True

    @pytest.mark.asyncio
    async def test_commit_after_rollback_does_nothing(self):
        """Test that commit after rollback does nothing."""
        mock_tx = AsyncMock()
        transaction = AsyncPostgreSQLTransaction(mock_tx)

        await transaction.rollback()
        await transaction.commit()

        # Only rollback should be called
        mock_tx.rollback.assert_called_once()
        mock_tx.commit.assert_not_called()

    def test_sync_commit_raises(self):
        """Test that sync commit raises NotImplementedError."""
        mock_tx = AsyncMock()
        transaction = AsyncPostgreSQLTransaction(mock_tx)

        with pytest.raises(NotImplementedError, match="Use async commit"):
            transaction.commit()

    def test_sync_rollback_raises(self):
        """Test that sync rollback raises NotImplementedError."""
        mock_tx = AsyncMock()
        transaction = AsyncPostgreSQLTransaction(mock_tx)

        with pytest.raises(NotImplementedError, match="Use async rollback"):
            transaction.rollback()


class TestAsyncPostgreSQLConnector:
    """Tests for AsyncPostgreSQLConnector."""

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_connect(self, mock_create_pool, db_config, mock_create_pool_fn):
        """Test establishing database connection pool."""
        mock_create_pool.side_effect = mock_create_pool_fn

        connector = AsyncPostgreSQLConnector(**db_config)
        await connector.connect()

        mock_create_pool.assert_called_once()
        assert connector.is_connected() is True

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_connect_already_connected(self, mock_create_pool, db_config, mock_create_pool_fn):
        """Test that connect() does nothing if already connected."""
        mock_create_pool.side_effect = mock_create_pool_fn

        connector = AsyncPostgreSQLConnector(**db_config)
        await connector.connect()
        await connector.connect()  # Second connect

        # Should only connect once
        mock_create_pool.assert_called_once()

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_disconnect(self, mock_create_pool, db_config, mock_create_pool_fn):
        """Test closing database connection pool."""
        mock_create_pool.side_effect = mock_create_pool_fn

        connector = AsyncPostgreSQLConnector(**db_config)
        await connector.connect()
        await connector.disconnect()

        pool = await mock_create_pool_fn()
        pool.close.assert_called_once()
        assert connector._pool is None

    def test_is_connected_when_not_connected(self, db_config):
        """Test is_connected() when not connected."""
        connector = AsyncPostgreSQLConnector(**db_config)
        assert connector.is_connected() is False

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_execute_with_fetch(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test executing query with fetch=True."""
        mock_connection = AsyncMock()
        mock_connection.fetch = AsyncMock(return_value=[
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ])

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)
        result = await connector.execute("SELECT * FROM users", fetch=True)

        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_execute_without_fetch(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test executing query with fetch=False."""
        mock_connection = AsyncMock()
        mock_connection.execute = AsyncMock()

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)
        result = await connector.execute("INSERT INTO users (name) VALUES ('Alice')")

        assert result is None
        mock_connection.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_execute_with_params(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test executing query with parameters."""
        mock_connection = AsyncMock()
        mock_connection.execute = AsyncMock()

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)
        await connector.execute("SELECT * FROM users WHERE id = $1", params=(1,))

        mock_connection.execute.assert_called_with("SELECT * FROM users WHERE id = $1", 1)

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_execute_many(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test executing query with multiple parameter sets."""
        mock_connection = AsyncMock()
        mock_connection.executemany = AsyncMock()

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)
        params_list = [(1, "Alice"), (2, "Bob")]
        await connector.execute_many("INSERT INTO users (id, name) VALUES ($1, $2)", params_list)

        mock_connection.executemany.assert_called_once()

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_fetch_one(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test fetching a single row."""
        mock_connection = AsyncMock()
        mock_connection.fetchrow = AsyncMock(return_value={"id": 1, "name": "Alice"})

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)
        result = await connector.fetch_one("SELECT * FROM users WHERE id = 1")

        assert result == {"id": 1, "name": "Alice"}

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_fetch_one_no_results(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test fetch_one when no results."""
        mock_connection = AsyncMock()
        mock_connection.fetchrow = AsyncMock(return_value=None)

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)
        result = await connector.fetch_one("SELECT * FROM users WHERE id = 999")

        assert result is None

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_fetch_all(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test fetching all rows."""
        mock_connection = AsyncMock()
        mock_connection.fetch = AsyncMock(return_value=[
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ])

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)
        result = await connector.fetch_all("SELECT * FROM users")

        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_transaction_commit(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test async transaction with manual commit."""
        mock_connection = AsyncMock()
        mock_tx = AsyncMock()
        mock_tx.start = AsyncMock()
        mock_tx.commit = AsyncMock()
        mock_connection.transaction = Mock(return_value=mock_tx)
        mock_connection.execute = AsyncMock()

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)

        async with connector.transaction() as tx:
            await connector.execute("INSERT INTO users (name) VALUES ('Alice')")
            await tx.commit()

        mock_tx.commit.assert_called()

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_transaction_rollback(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test async transaction with manual rollback."""
        mock_connection = AsyncMock()
        mock_tx = AsyncMock()
        mock_tx.start = AsyncMock()
        mock_tx.rollback = AsyncMock()
        mock_connection.transaction = Mock(return_value=mock_tx)
        mock_connection.execute = AsyncMock()

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)

        async with connector.transaction() as tx:
            await connector.execute("INSERT INTO users (name) VALUES ('Alice')")
            await tx.rollback()

        mock_tx.rollback.assert_called()

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_transaction_auto_commit(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test async transaction with automatic commit."""
        mock_connection = AsyncMock()
        mock_tx = AsyncMock()
        mock_tx.start = AsyncMock()
        mock_tx.commit = AsyncMock()
        mock_connection.transaction = Mock(return_value=mock_tx)
        mock_connection.execute = AsyncMock()

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)

        async with connector.transaction():
            await connector.execute("INSERT INTO users (name) VALUES ('Alice')")

        # Should auto-commit
        mock_tx.commit.assert_called()

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_transaction_auto_rollback_on_exception(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test async transaction with automatic rollback on exception."""
        mock_connection = AsyncMock()
        mock_tx = AsyncMock()
        mock_tx.start = AsyncMock()
        mock_tx.rollback = AsyncMock()
        mock_connection.transaction = Mock(return_value=mock_tx)
        mock_connection.execute = AsyncMock(side_effect=Exception("DB error"))

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)

        with pytest.raises(Exception, match="DB error"):
            async with connector.transaction():
                await connector.execute("INSERT INTO users (name) VALUES ('Alice')")

        # Should auto-rollback
        mock_tx.rollback.assert_called()

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_ping_success(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test successful ping."""
        mock_connection = AsyncMock()
        mock_connection.fetchval = AsyncMock(return_value=1)

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)
        result = await connector.ping()

        assert result is True
        mock_connection.fetchval.assert_called_with("SELECT 1")

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_ping_failure(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test failed ping."""
        mock_connection = AsyncMock()
        mock_connection.fetchval = AsyncMock(side_effect=Exception("Connection lost"))

        mock_asyncpg_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(**db_config)
        result = await connector.ping()

        assert result is False

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_context_manager(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test using connector as async context manager."""
        mock_create_pool.return_value = mock_asyncpg_pool

        async with AsyncPostgreSQLConnector(**db_config) as connector:
            assert connector.is_connected() is True

        mock_asyncpg_pool.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("research_assistant_db.connectors.postgres_async.asyncpg.create_pool")
    async def test_pool_size_configuration(self, mock_create_pool, db_config, mock_asyncpg_pool):
        """Test that pool size is configured correctly."""
        mock_create_pool.return_value = mock_asyncpg_pool

        connector = AsyncPostgreSQLConnector(
            **db_config,
            min_pool_size=5,
            max_pool_size=15
        )
        await connector.connect()

        # Check that create_pool was called with correct pool sizes
        call_args = mock_create_pool.call_args
        assert call_args.kwargs["min_size"] == 5
        assert call_args.kwargs["max_size"] == 15
