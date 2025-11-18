"""Tests for database interface abstractions."""

import pytest
from research_assistant_db.interface import (
    DatabaseInterface,
    AsyncDatabaseInterface,
    TransactionContext,
)


class TestDatabaseInterface:
    """Tests for DatabaseInterface ABC."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that DatabaseInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DatabaseInterface()

    def test_abstract_methods_defined(self):
        """Test that all abstract methods are defined."""
        abstract_methods = {
            "connect",
            "disconnect",
            "is_connected",
            "execute",
            "execute_many",
            "fetch_one",
            "fetch_all",
            "transaction",
            "ping",
        }

        assert set(DatabaseInterface.__abstractmethods__) == abstract_methods


class TestAsyncDatabaseInterface:
    """Tests for AsyncDatabaseInterface ABC."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that AsyncDatabaseInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AsyncDatabaseInterface()

    def test_abstract_methods_defined(self):
        """Test that all abstract methods are defined."""
        abstract_methods = {
            "connect",
            "disconnect",
            "is_connected",
            "execute",
            "execute_many",
            "fetch_one",
            "fetch_all",
            "transaction",
            "ping",
        }

        assert set(AsyncDatabaseInterface.__abstractmethods__) == abstract_methods


class TestTransactionContext:
    """Tests for TransactionContext ABC."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that TransactionContext cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TransactionContext()

    def test_abstract_methods_defined(self):
        """Test that all abstract methods are defined."""
        abstract_methods = {"commit", "rollback"}

        assert set(TransactionContext.__abstractmethods__) == abstract_methods
