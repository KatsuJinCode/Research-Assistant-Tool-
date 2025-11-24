"""
Shared State Module

This module holds references to shared application state that is used
across multiple route blueprints. It's initialized by app.py on startup.

This pattern allows blueprints to access shared resources like:
- Database connections (db, claim_repo, doc_repo)
- SocketIO instance
- Processing queue state
- Debug agent

Usage in blueprints:
    from web_ui.shared import get_db, get_socketio, get_debug_agent
"""

import logging

logger = logging.getLogger(__name__)

# Shared state holders - initialized by app.py
_db = None
_socketio = None
_debug_agent = None
_claim_repo = None
_doc_repo = None
_neo4j_client = None
_db_manager = None
_processing_queue = None
_processing_lock = None


def init_shared_state(db=None, socketio=None, debug_agent=None, claim_repo=None,
                      doc_repo=None, neo4j_client=None, db_manager=None,
                      processing_queue=None, processing_lock=None):
    """Initialize shared state. Called by app.py on startup."""
    global _db, _socketio, _debug_agent, _claim_repo, _doc_repo
    global _neo4j_client, _db_manager, _processing_queue, _processing_lock

    _db = db
    _socketio = socketio
    _debug_agent = debug_agent
    _claim_repo = claim_repo
    _doc_repo = doc_repo
    _neo4j_client = neo4j_client
    _db_manager = db_manager
    _processing_queue = processing_queue
    _processing_lock = processing_lock

    logger.info("Shared state initialized for route blueprints")


def get_db():
    """Get Neo4j database instance."""
    return _db


def get_socketio():
    """Get SocketIO instance."""
    return _socketio


def get_debug_agent():
    """Get debug agent instance."""
    return _debug_agent


def get_claim_repo():
    """Get claim repository instance."""
    return _claim_repo


def get_doc_repo():
    """Get document repository instance."""
    return _doc_repo


def get_neo4j_client():
    """Get Neo4j client instance."""
    return _neo4j_client


def get_db_manager():
    """Get database manager instance."""
    return _db_manager


def get_processing_queue():
    """Get processing queue."""
    return _processing_queue


def get_processing_lock():
    """Get processing lock."""
    return _processing_lock
