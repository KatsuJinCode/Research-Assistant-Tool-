"""
Web UI Route Blueprints

This package contains Flask blueprints that were extracted from the main app.py
to improve maintainability and code organization.

Each blueprint handles a specific domain:
- debug_routes: Debugging agent controls (extracted)
- claim_routes: Claim CRUD, overrides, evidence management (planned)
- document_routes: Document upload, processing, deletion (planned)
- graph_routes: Graph visualization, stats, full graph data (planned)
- agent_routes: Agent status, transcripts, tracking (planned)
- search_routes: Quick search, semantic search (planned)
- project_routes: Project CRUD, switching, export (planned)
- framework_routes: Framework management (planned)
"""

from .debug_routes import debug_bp

__all__ = ['debug_bp']
