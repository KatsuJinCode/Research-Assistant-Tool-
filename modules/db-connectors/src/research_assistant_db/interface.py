"""Database interface abstractions."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, AsyncIterator, Iterator
from contextlib import contextmanager, asynccontextmanager


class TransactionContext(ABC):
    """Abstract transaction context manager."""

    @abstractmethod
    def commit(self) -> None:
        """Commit the transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the transaction."""
        pass


class DatabaseInterface(ABC):
    """Abstract database interface."""

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if database is connected."""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    @contextmanager
    def transaction(self) -> Iterator[TransactionContext]:
        """
        Create a transaction context.

        Yields:
            TransactionContext for manual commit/rollback
        """
        pass

    @abstractmethod
    def ping(self) -> bool:
        """
        Ping the database to check connectivity.

        Returns:
            True if connection is alive, False otherwise
        """
        pass


class AsyncDatabaseInterface(ABC):
    """Abstract async database interface."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if database is connected."""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[TransactionContext]:
        """
        Create an async transaction context.

        Yields:
            TransactionContext for manual commit/rollback
        """
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """
        Ping the database to check connectivity.

        Returns:
            True if connection is alive, False otherwise
        """
        pass
