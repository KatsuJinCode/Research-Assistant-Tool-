"""Shared test fixtures for db-connectors tests."""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
import psycopg2.extras


@pytest.fixture
def db_config():
    """Sample database configuration."""
    return {
        "host": "localhost",
        "port": 5432,
        "database": "test_db",
        "user": "test_user",
        "password": "test_password",
    }


@pytest.fixture
def mock_psycopg2_connection():
    """Mock psycopg2 connection."""
    conn = Mock()
    conn.closed = False
    conn.autocommit = False

    # Mock cursor
    cursor = Mock()
    cursor.__enter__ = Mock(return_value=cursor)
    cursor.__exit__ = Mock(return_value=False)
    cursor.fetchone = Mock(return_value=None)
    cursor.fetchall = Mock(return_value=[])
    cursor.execute = Mock()
    cursor.executemany = Mock()

    conn.cursor = Mock(return_value=cursor)
    conn.commit = Mock()
    conn.rollback = Mock()
    conn.close = Mock()

    return conn


@pytest.fixture
def mock_asyncpg_pool():
    """Mock asyncpg connection pool."""
    pool = AsyncMock()

    # Mock connection
    connection = AsyncMock()
    connection.fetch = AsyncMock(return_value=[])
    connection.fetchrow = AsyncMock(return_value=None)
    connection.fetchval = AsyncMock(return_value=1)
    connection.execute = AsyncMock()
    connection.executemany = AsyncMock()

    # Mock transaction
    transaction = AsyncMock()
    transaction.start = AsyncMock()
    transaction.commit = AsyncMock()
    transaction.rollback = AsyncMock()
    connection.transaction = Mock(return_value=transaction)

    # Pool acquire returns connection
    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=connection)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    pool.close = AsyncMock()

    return pool


@pytest.fixture
def mock_create_pool_fn(mock_asyncpg_pool):
    """Fixture that returns a mock create_pool function."""
    async def mock_pool_creator(*args, **kwargs):
        return mock_asyncpg_pool
    return mock_pool_creator


@pytest.fixture
def sample_query_result():
    """Sample query result as RealDictRow."""
    # Simulate psycopg2.extras.RealDictRow
    row1 = psycopg2.extras.RealDictRow([1, "Alice", 30])
    row1._index = {"id": 0, "name": 1, "age": 2}

    row2 = psycopg2.extras.RealDictRow([2, "Bob", 25])
    row2._index = {"id": 0, "name": 1, "age": 2}

    return [row1, row2]
