"""
Event emitter for repository operations.

Emits WebSocket events when database operations occur, enabling real-time UI updates.
"""

from typing import Optional, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


class RepositoryEventEmitter:
    """
    Singleton event emitter for repository operations.

    Repositories call this to emit events that the UI can listen to via WebSocket.
    """

    _instance: Optional['RepositoryEventEmitter'] = None
    _emit_callback: Optional[Callable] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def set_emit_callback(cls, callback: Callable):
        """
        Set the WebSocket emit callback (called from Flask app).

        Args:
            callback: Function that emits WebSocket events (e.g., socketio.emit)
        """
        instance = cls()
        instance._emit_callback = callback
        logger.info("RepositoryEventEmitter: WebSocket callback registered")

    def emit_node_created(self, label: str, node_id: str, properties: Dict[str, Any]):
        """
        Emit event when a node is created.

        Args:
            label: Node label (Document, Claim, etc.)
            node_id: Node ID
            properties: Node properties
        """
        if self._emit_callback:
            try:
                # CRITICAL: Emit might be called from background thread, so callback
                # must handle app context (Flask-SocketIO requires it)
                self._emit_callback('node_created', {
                    'label': label,
                    'id': node_id,
                    'properties': properties
                })
                logger.info(f"Emitted node_created: {label} {node_id}")
            except Exception as e:
                logger.error(f"Failed to emit node_created: {e}")

    def emit_node_updated(self, label: str, node_id: str, properties: Dict[str, Any]):
        """
        Emit event when a node is updated.

        Args:
            label: Node label
            node_id: Node ID
            properties: Updated properties
        """
        if self._emit_callback:
            try:
                self._emit_callback('node_updated', {
                    'label': label,
                    'id': node_id,
                    'properties': properties
                })
                logger.debug(f"Emitted node_updated: {label} {node_id}")
            except Exception as e:
                logger.error(f"Failed to emit node_updated: {e}")

    def emit_relationship_created(
        self,
        from_id: str,
        to_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Emit event when a relationship is created.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            relationship_type: Relationship type
            properties: Relationship properties
        """
        if self._emit_callback:
            try:
                self._emit_callback('relationship_created', {
                    'from_id': from_id,
                    'to_id': to_id,
                    'type': relationship_type,
                    'properties': properties or {}
                })
                logger.debug(f"Emitted relationship_created: {from_id} -{relationship_type}-> {to_id}")
            except Exception as e:
                logger.error(f"Failed to emit relationship_created: {e}")

    def emit_document_status_changed(self, doc_id: str, status: str, error: Optional[str] = None):
        """
        Emit event when document status changes.

        Args:
            doc_id: Document ID
            status: New status
            error: Error message if status is 'failed'
        """
        if self._emit_callback:
            try:
                self._emit_callback('document_status_changed', {
                    'doc_id': doc_id,
                    'status': status,
                    'error': error
                })
                logger.debug(f"Emitted document_status_changed: {doc_id} -> {status}")
            except Exception as e:
                logger.error(f"Failed to emit document_status_changed: {e}")

    def emit_claim_status_changed(self, claim_id: str, status: str, properties: Optional[Dict[str, Any]] = None):
        """
        Emit event when claim status changes.

        Args:
            claim_id: Claim ID
            status: New status
            properties: Additional properties to include
        """
        if self._emit_callback:
            try:
                self._emit_callback('claim_status_changed', {
                    'claim_id': claim_id,
                    'status': status,
                    **(properties or {})
                })
                logger.debug(f"Emitted claim_status_changed: {claim_id} -> {status}")
            except Exception as e:
                logger.error(f"Failed to emit claim_status_changed: {e}")


# Global singleton instance
event_emitter = RepositoryEventEmitter()
