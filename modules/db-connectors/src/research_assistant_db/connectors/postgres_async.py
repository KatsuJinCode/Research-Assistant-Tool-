"""Asynchronous PostgreSQL connector implementation."""

import asyncpg
from typing import Any, Dict, List, Optional, Tuple, AsyncIterator
from contextlib import asynccontextmanager

from ..interface import AsyncDatabaseInterface, TransactionContext


class AsyncPostgreSQLTransaction(TransactionContext):
    """Async PostgreSQL transaction context."""

    def __init__(self, transaction: asyncpg.transaction.Transaction):
        """
        Initialize async transaction.

        Args:
            transaction: asyncpg transaction object
        """
        self.transaction = transaction
        self._committed = False
        self._rolled_back = False

    async def commit(self) -> None:
        """Commit the transaction."""
        if not self._rolled_back:
            await self.transaction.commit()
            self._committed = True

    async def rollback(self) -> None:
        """Rollback the transaction."""
        if not self._committed:
            await self.transaction.rollback()
            self._rolled_back = True

    # Sync versions for compatibility with TransactionContext ABC
    def commit(self) -> None:
        """Sync commit not supported - use async version."""
        raise NotImplementedError("Use async commit() instead")

    def rollback(self) -> None:
        """Sync rollback not supported - use async version."""
        raise NotImplementedError("Use async rollback() instead")


class AsyncPostgreSQLConnector(AsyncDatabaseInterface):
    """Asynchronous PostgreSQL database connector."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        min_pool_size: int = 10,
        max_pool_size: int = 20,
        **kwargs
    ):
        """
        Initialize async PostgreSQL connector.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            min_pool_size: Minimum connection pool size
            max_pool_size: Maximum connection pool size
            **kwargs: Additional asyncpg connection parameters
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.connection_params = kwargs
        self._pool: Optional[asyncpg.pool.Pool] = None

    async def connect(self) -> None:
        """Establish database connection pool."""
        if self._pool is not None:
            return

        self._pool = await asyncpg.create_pool(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            min_size=self.min_pool_size,
            max_size=self.max_pool_size,
            **self.connection_params
        )

    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def is_connected(self) -> bool:
        """Check if database pool is connected."""
        return self._pool is not None

    async def _ensure_connection(self) -> None:
        """Ensure connection pool is established."""
        if not self.is_connected():
            await self.connect()

    async def execute(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
        fetch: bool = False,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a database query.

        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch and return results

        Returns:
            Query results if fetch=True, None otherwise
        """
        await self._ensure_connection()

        async with self._pool.acquire() as connection:
            if fetch:
                rows = await connection.fetch(query, *(params or ()))
                return [dict(row) for row in rows]
            else:
                await connection.execute(query, *(params or ()))
                return None

    async def execute_many(
        self,
        query: str,
        params_list: List[Tuple[Any, ...]],
    ) -> None:
        """
        Execute a query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples
        """
        await self._ensure_connection()

        async with self._pool.acquire() as connection:
            await connection.executemany(query, params_list)

    async def fetch_one(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Single row as dict, or None if no results
        """
        await self._ensure_connection()

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, *(params or ()))
            return dict(row) if row else None

    async def fetch_all(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all rows.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of rows as dicts
        """
        await self._ensure_connection()

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, *(params or ()))
            return [dict(row) for row in rows]

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[TransactionContext]:
        """
        Create an async transaction context.

        Yields:
            TransactionContext for manual commit/rollback
        """
        await self._ensure_connection()

        async with self._pool.acquire() as connection:
            async_tx = connection.transaction()
            await async_tx.start()

            transaction = AsyncPostgreSQLTransaction(async_tx)

            try:
                yield transaction

                # Auto-commit if not manually handled
                if not transaction._committed and not transaction._rolled_back:
                    await transaction.commit()

            except Exception:
                # Auto-rollback on exception
                if not transaction._committed and not transaction._rolled_back:
                    await transaction.rollback()
                raise

    async def ping(self) -> bool:
        """
        Ping the database to check connectivity.

        Returns:
            True if connection is alive, False otherwise
        """
        try:
            await self._ensure_connection()
            async with self._pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
                return True
        except Exception:
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
