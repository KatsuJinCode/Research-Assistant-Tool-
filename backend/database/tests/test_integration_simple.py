"""
Simplified integration tests focusing on verifying repository method calls.

These tests verify that the migrated code uses the correct repository methods.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock


class TestDocumentProcessorRepositoryUsage:
    """Test that document_processor.py repository instances call correct methods."""

    def test_document_processor_has_repositories(self):
        """Test that LiveDocumentProcessor has doc_repo and claim_repo attributes."""
        from web_ui.document_processor import LiveDocumentProcessor

        processor = LiveDocumentProcessor()

        # Should have repository attributes
        assert hasattr(processor, 'doc_repo')
        assert hasattr(processor, 'claim_repo')
        assert processor.doc_repo is not None
        assert processor.claim_repo is not None

    def test_document_repository_methods_exist(self):
        """Test that DocumentRepository has all required methods."""
        from backend.database.repositories import DocumentRepository

        repo = DocumentRepository()

        # Verify all migrated methods exist
        assert hasattr(repo, 'create_document')
        assert hasattr(repo, 'update_document')
        assert hasattr(repo, 'mark_document_failed')
        assert hasattr(repo, 'mark_document_complete')
        assert callable(repo.create_document)
        assert callable(repo.update_document)
        assert callable(repo.mark_document_failed)
        assert callable(repo.mark_document_complete)

    def test_claim_repository_methods_exist(self):
        """Test that ClaimRepository has all required methods."""
        from backend.database.repositories import ClaimRepository

        repo = ClaimRepository()

        # Verify all migrated methods exist
        assert hasattr(repo, 'create_claim')
        assert hasattr(repo, 'update_claim')
        assert callable(repo.create_claim)
        assert callable(repo.update_claim)


class TestAppRoutesRepositoryUsage:
    """Test that app.py routes use repositories correctly."""

    def test_app_has_repository_globals(self):
        """Test that app.py has global repository instances."""
        from web_ui import app as app_module

        # Verify repositories are initialized
        assert hasattr(app_module, 'claim_repo')
        assert hasattr(app_module, 'doc_repo')
        assert app_module.claim_repo is not None
        assert app_module.doc_repo is not None

    @patch('web_ui.app.claim_repo')
    def test_get_claim_details_route_calls_repository(self, mock_claim_repo):
        """Test that /api/claim/<claim_id> route calls get_claim_with_relationships()."""
        from web_ui.app import app

        # Setup mock
        claim_id = str(uuid4())
        mock_claim_data = {
            'id': claim_id,
            'text': 'Test claim',
            'children': [],
            'evidence': []
        }
        mock_claim_repo.get_claim_with_relationships.return_value = mock_claim_data

        # Make request
        with app.test_client() as client:
            response = client.get(f'/api/claim/{claim_id}')

        # Verify repository method was called
        mock_claim_repo.get_claim_with_relationships.assert_called_once_with(claim_id)

        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == claim_id
        assert data['text'] == 'Test claim'

    @patch('web_ui.app.claim_repo')
    def test_get_claim_details_returns_404_when_not_found(self, mock_claim_repo):
        """Test that /api/claim/<claim_id> returns 404 when claim doesn't exist."""
        from web_ui.app import app

        # Setup mock to return None
        claim_id = str(uuid4())
        mock_claim_repo.get_claim_with_relationships.return_value = None

        # Make request
        with app.test_client() as client:
            response = client.get(f'/api/claim/{claim_id}')

        # Verify response
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Claim not found'

    @patch('web_ui.app.claim_repo')
    @patch('web_ui.app.AgentTracker')
    def test_investigate_claim_route_calls_repository(self, mock_agent_tracker, mock_claim_repo):
        """Test that /api/investigate-claim route calls get_claim()."""
        from web_ui.app import app

        # Setup mocks
        claim_id = str(uuid4())
        mock_claim_data = {
            'id': claim_id,
            'text': 'Claim to investigate'
        }
        mock_claim_repo.get_claim.return_value = mock_claim_data

        # Mock agent tracker
        mock_tracker_instance = Mock()
        mock_agent_tracker.return_value = mock_tracker_instance
        mock_tracker_instance.create_research_result.return_value = Mock()
        mock_tracker_instance.create_research_result_node_in_neo4j.return_value = 'research-123'

        # Make request
        with app.test_client() as client:
            response = client.post('/api/investigate-claim', json={
                'claim_id': claim_id,
                'type': 'support'
            })

        # Verify repository method was called
        mock_claim_repo.get_claim.assert_called_once_with(claim_id)

        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'started'
        assert data['claim'] == 'Claim to investigate'

    @patch('web_ui.app.claim_repo')
    def test_investigate_claim_returns_404_when_not_found(self, mock_claim_repo):
        """Test that /api/investigate-claim returns 404 when claim doesn't exist."""
        from web_ui.app import app

        # Setup mock to return None
        claim_id = str(uuid4())
        mock_claim_repo.get_claim.return_value = None

        # Make request
        with app.test_client() as client:
            response = client.post('/api/investigate-claim', json={
                'claim_id': claim_id,
                'type': 'support'
            })

        # Verify response
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Claim not found'


class TestMigrationComplete:
    """Test that migration is complete and old code replaced."""

    def test_document_processor_uses_new_repository_pattern(self):
        """Verify document_processor.py imports and uses new repositories."""
        import inspect
        from web_ui.document_processor import LiveDocumentProcessor

        # Get source code
        source = inspect.getsource(LiveDocumentProcessor.__init__)

        # Should import from backend.database.repositories
        assert 'from backend.database.repositories import' in source
        assert 'DocumentRepository' in source
        assert 'ClaimRepository' in source

        # Should create repository instances
        assert 'self.doc_repo' in source
        assert 'self.claim_repo' in source

    def test_app_uses_new_repository_pattern(self):
        """Verify app.py imports and uses new repositories."""
        import inspect
        import web_ui.app as app_module

        # Get source code
        source = inspect.getsource(app_module)

        # Should import from backend.database.repositories
        assert 'from backend.database.repositories import' in source
        assert 'ClaimRepository' in source
        assert 'DocumentRepository' in source

        # Should create global repository instances
        assert 'claim_repo = ClaimRepository()' in source
        assert 'doc_repo = DocumentRepository()' in source

    def test_migrated_routes_use_repositories(self):
        """Verify that migrated routes use repository methods."""
        import inspect
        from web_ui import app as app_module

        # Get source for get_claim_details route
        source = inspect.getsource(app_module.get_claim_details)

        # Should call repository method, not raw Cypher query
        assert 'claim_repo.get_claim_with_relationships' in source
        assert 'MATCH (c:Claim' not in source  # No raw Cypher

        # Get source for investigate_claim route
        source = inspect.getsource(app_module.investigate_claim)

        # Should call repository method
        assert 'claim_repo.get_claim' in source


class TestRepositoryMethodSignatures:
    """Test that repository methods have correct signatures for migration."""

    def test_document_repository_create_document_signature(self):
        """Test DocumentRepository.create_document accepts migrated parameters."""
        from backend.database.repositories import DocumentRepository
        import inspect

        repo = DocumentRepository()
        sig = inspect.signature(repo.create_document)

        # Should have title, source_file, status parameters
        assert 'title' in sig.parameters
        assert 'source_file' in sig.parameters
        assert 'status' in sig.parameters

    def test_claim_repository_create_claim_signature(self):
        """Test ClaimRepository.create_claim accepts migrated parameters."""
        from backend.database.repositories import ClaimRepository
        import inspect

        repo = ClaimRepository()
        sig = inspect.signature(repo.create_claim)

        # Should have all parameters used in migration
        assert 'text' in sig.parameters
        assert 'original_text' in sig.parameters
        assert 'doc_id' in sig.parameters
        assert 'claim_type' in sig.parameters
        assert 'confidence' in sig.parameters
        assert 'status' in sig.parameters

    def test_document_repository_convenience_methods_exist(self):
        """Test that convenience methods used in migration exist."""
        from backend.database.repositories import DocumentRepository

        repo = DocumentRepository()

        # These are called in document_processor.py
        assert hasattr(repo, 'mark_document_failed')
        assert hasattr(repo, 'mark_document_complete')
        assert callable(repo.mark_document_failed)
        assert callable(repo.mark_document_complete)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
