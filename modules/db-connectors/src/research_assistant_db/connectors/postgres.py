"""Synchronous PostgreSQL connector implementation."""

import psycopg2
import psycopg2.extras
from typing import Any, Dict, List, Optional, Tuple, Iterator
from contextlib import contextmanager

from ..interface import DatabaseInterface, TransactionContext


class PostgreSQLTransaction(TransactionContext):
    """PostgreSQL transaction context."""

    def __init__(self, connection):
        """
        Initialize transaction.

        Args:
            connection: psycopg2 connection object
        """
        self.connection = connection
        self._committed = False
        self._rolled_back = False

    def commit(self) -> None:
        """Commit the transaction."""
        if not self._rolled_back:
            self.connection.commit()
            self._committed = True

    def rollback(self) -> None:
        """Rollback the transaction."""
        if not self._committed:
            self.connection.rollback()
            self._rolled_back = True


class PostgreSQLConnector(DatabaseInterface):
    """Synchronous PostgreSQL database connector."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        **kwargs
    ):
        """
        Initialize PostgreSQL connector.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            **kwargs: Additional psycopg2 connection parameters
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection_params = kwargs
        self._connection: Optional[psycopg2.extensions.connection] = None

    def connect(self) -> None:
        """Establish database connection."""
        if self._connection is not None and not self._connection.closed:
            return

        self._connection = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            cursor_factory=psycopg2.extras.RealDictCursor,
            **self.connection_params
        )
        self._connection.autocommit = False

    def disconnect(self) -> None:
        """Close database connection."""
        if self._connection is not None and not self._connection.closed:
            self._connection.close()
            self._connection = None

    def is_connected(self) -> bool:
        """Check if database is connected."""
        return (
            self._connection is not None
            and not self._connection.closed
        )

    def _ensure_connection(self) -> None:
        """Ensure connection is established."""
        if not self.is_connected():
            self.connect()

    def execute(
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
        self._ensure_connection()

        with self._connection.cursor() as cursor:
            cursor.execute(query, params)

            if fetch:
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

            self._connection.commit()
            return None

    def execute_many(
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
        self._ensure_connection()

        with self._connection.cursor() as cursor:
            cursor.executemany(query, params_list)
            self._connection.commit()

    def fetch_one(
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
        self._ensure_connection()

        with self._connection.cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetch_all(
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
        self._ensure_connection()

        with self._connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @contextmanager
    def transaction(self) -> Iterator[TransactionContext]:
        """
        Create a transaction context.

        Yields:
            TransactionContext for manual commit/rollback
        """
        self._ensure_connection()

        # Save current autocommit state
        old_autocommit = self._connection.autocommit
        self._connection.autocommit = False

        transaction = PostgreSQLTransaction(self._connection)

        try:
            yield transaction

            # Auto-commit if not manually handled
            if not transaction._committed and not transaction._rolled_back:
                transaction.commit()

        except Exception:
            # Auto-rollback on exception
            if not transaction._committed and not transaction._rolled_back:
                transaction.rollback()
            raise

        finally:
            # Restore autocommit state
            self._connection.autocommit = old_autocommit

    def ping(self) -> bool:
        """
        Ping the database to check connectivity.

        Returns:
            True if connection is alive, False otherwise
        """
        try:
            self._ensure_connection()
            with self._connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
