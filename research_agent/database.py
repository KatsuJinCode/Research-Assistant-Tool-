"""
Database connection and query management.
Uses asyncpg for PostgreSQL async operations.
"""

import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from uuid import UUID
import asyncpg


logger = logging.getLogger(__name__)


class Database:
    """
    Database connection manager for PostgreSQL.

    Uses connection pooling for efficient async operations.
    """

    def __init__(self, connection_string: str, min_size: int = 10, max_size: int = 20):
        """
        Initialize database manager.

        Args:
            connection_string: PostgreSQL connection string
            min_size: Minimum pool size
            max_size: Maximum pool size
        """
        self.connection_string = connection_string
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create connection pool."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=self.min_size,
                max_size=self.max_size
            )
            logger.info(f"Database pool created (size: {self.min_size}-{self.max_size})")

    async def disconnect(self):
        """Close connection pool."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            logger.info("Database pool closed")

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire connection from pool.

        Usage:
            async with db.acquire() as conn:
                result = await conn.fetchrow("SELECT ...")
        """
        if self.pool is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self.pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args) -> str:
        """
        Execute query (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Status message (e.g., "INSERT 0 1")
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """
        Fetch single row.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Dict of column:value, or None if no rows
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetchval(self, query: str, *args) -> Any:
        """
        Fetch single value.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single value, or None
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        Fetch multiple rows.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            List of dicts
        """
        async with self.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    # ========================================================================
    # Convenience methods for common operations
    # ========================================================================

    async def get_document(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        return await self.fetchrow(
            "SELECT * FROM documents WHERE id = $1",
            document_id
        )

    async def get_claim(self, claim_id: UUID) -> Optional[Dict[str, Any]]:
        """Get claim by ID."""
        return await self.fetchrow(
            "SELECT * FROM claims WHERE id = $1",
            claim_id
        )

    async def get_claim_qualifiers(self, claim_id: UUID) -> List[Dict[str, Any]]:
        """Get qualifiers for a claim."""
        return await self.fetch(
            "SELECT * FROM claim_qualifiers WHERE claim_id = $1",
            claim_id
        )

    async def get_findings_for_claim(self, claim_id: UUID) -> List[Dict[str, Any]]:
        """Get all findings for a claim."""
        return await self.fetch(
            """
            SELECT f.*, i.agent_framework
            FROM findings f
            JOIN investigations i ON f.investigation_id = i.id
            WHERE f.claim_id = $1
            ORDER BY f.created_at DESC
            """,
            claim_id
        )

    async def get_evidence_for_finding(self, finding_id: UUID) -> List[Dict[str, Any]]:
        """Get all evidence for a finding."""
        return await self.fetch(
            "SELECT * FROM evidence WHERE finding_id = $1 ORDER BY relevance_score DESC",
            finding_id
        )

    async def get_pending_normalizations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending normalizations for human review."""
        return await self.fetch(
            """
            SELECT nv.*, c.original_text as claim_original_text
            FROM normalization_validations nv
            JOIN claims c ON nv.claim_id = c.id
            WHERE nv.status = 'pending'
            ORDER BY nv.created_at ASC
            LIMIT $1
            """,
            limit
        )

    async def approve_normalization(self, validation_id: UUID) -> None:
        """Approve a normalization and update claim."""
        async with self.acquire() as conn:
            async with conn.transaction():
                # Get validation
                validation = await conn.fetchrow(
                    "SELECT * FROM normalization_validations WHERE id = $1",
                    validation_id
                )

                if not validation:
                    raise ValueError(f"Validation {validation_id} not found")

                # Update claim with normalized text
                await conn.execute(
                    "UPDATE claims SET normalized_text = $1 WHERE id = $2",
                    validation['proposed_normalized'],
                    validation['claim_id']
                )

                # Mark validation as approved
                await conn.execute(
                    """
                    UPDATE normalization_validations
                    SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                    """,
                    validation_id
                )

    async def edit_normalization(
        self,
        validation_id: UUID,
        corrected_text: str
    ) -> None:
        """Edit and approve a normalization with corrections."""
        async with self.acquire() as conn:
            async with conn.transaction():
                # Get validation
                validation = await conn.fetchrow(
                    "SELECT * FROM normalization_validations WHERE id = $1",
                    validation_id
                )

                if not validation:
                    raise ValueError(f"Validation {validation_id} not found")

                # Update claim with corrected text
                await conn.execute(
                    "UPDATE claims SET normalized_text = $1 WHERE id = $2",
                    corrected_text,
                    validation['claim_id']
                )

                # Mark validation as edited
                await conn.execute(
                    """
                    UPDATE normalization_validations
                    SET status = 'edited',
                        user_corrected_text = $1,
                        reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                    """,
                    corrected_text,
                    validation_id
                )

    async def get_next_investigation(self, framework: str) -> Optional[UUID]:
        """
        Get next investigation for an agent framework.

        Uses database function for atomic claim with SKIP LOCKED.

        Args:
            framework: Agent framework name

        Returns:
            Investigation ID, or None if no work available
        """
        return await self.fetchval(
            "SELECT get_next_work($1)",
            framework
        )

    async def update_claim_confidence(self, claim_id: UUID) -> float:
        """
        Calculate and update claim confidence score.

        Uses database function.

        Args:
            claim_id: Claim ID

        Returns:
            New confidence score
        """
        return await self.fetchval(
            "SELECT calculate_claim_confidence($1)",
            claim_id
        )

    async def get_investigation(self, investigation_id: UUID) -> Optional[Dict[str, Any]]:
        """Get investigation by ID."""
        return await self.fetchrow(
            "SELECT * FROM investigations WHERE id = $1",
            investigation_id
        )

    async def update_investigation_status(
        self,
        investigation_id: UUID,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Update investigation status."""
        if error_message:
            await self.execute(
                """
                UPDATE investigations
                SET status = $1, error_message = $2
                WHERE id = $3
                """,
                status, error_message, investigation_id
            )
        else:
            await self.execute(
                """
                UPDATE investigations
                SET status = $1
                WHERE id = $2
                """,
                status, investigation_id
            )

    async def mark_investigation_complete(
        self,
        investigation_id: UUID,
        duration_seconds: int
    ) -> None:
        """Mark investigation as complete."""
        await self.execute(
            """
            UPDATE investigations
            SET
                status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                duration_seconds = $1
            WHERE id = $2
            """,
            duration_seconds,
            investigation_id
        )

    async def get_claims_needing_investigation(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get claims that need investigation."""
        return await self.fetch(
            """
            SELECT *
            FROM claims
            WHERE status IN ('extracted', 'queued')
            AND (support_count = 0 OR challenge_count = 0)
            ORDER BY priority_score DESC
            LIMIT $1
            """,
            limit
        )


# Global database instance
_db_instance: Optional[Database] = None


async def init_database(connection_string: str) -> Database:
    """
    Initialize global database instance.

    Args:
        connection_string: PostgreSQL connection string

    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(connection_string)
        await _db_instance.connect()
    return _db_instance


def get_database() -> Database:
    """
    Get global database instance.

    Returns:
        Database instance

    Raises:
        RuntimeError: If database not initialized
    """
    if _db_instance is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_instance


async def close_database():
    """Close global database instance."""
    global _db_instance
    if _db_instance is not None:
        await _db_instance.disconnect()
        _db_instance = None
