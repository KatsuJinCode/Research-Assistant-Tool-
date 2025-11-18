"""Research Assistant DB - Database connectors and abstractions.

This module provides database connection interfaces and implementations
for PostgreSQL with both sync and async support.
"""

from .interface import DatabaseInterface, TransactionContext
from .connectors.postgres import PostgreSQLConnector
from .connectors.postgres_async import AsyncPostgreSQLConnector

__version__ = "0.1.0"

__all__ = [
    # Interfaces
    "DatabaseInterface",
    "TransactionContext",
    # Connectors
    "PostgreSQLConnector",
    "AsyncPostgreSQLConnector",
]
