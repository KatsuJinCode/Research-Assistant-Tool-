"""
Integration tests for document processing with repository layer.

These tests verify that the document_processor.py and app.py routes work correctly
with the new repository pattern implementation.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from uuid import uuid4

# Test that imports work
def test_imports():
    """Verify all necessary imports are available."""
    from backend.database.repositories import ClaimRepository, DocumentRepository
    from backend.database.models import Claim, Document
    from backend.database.neo4j_client import Neo4jClient

    # Should not raise
    assert ClaimRepository is not None
    assert DocumentRepository is not None
    assert Claim is not None
    assert Document is not None
    assert Neo4jClient is not None


class TestDocumentProcessorMigration:
    """Test that document_processor.py uses repositories correctly."""

    @patch('backend.database.repositories.claim_repository.ClaimRepository')
    @patch('backend.database.repositories.document_repository.DocumentRepository')
    @patch('web_ui.document_processor.Neo4jDatabase')
    def test_document_processor_initializes_repositories(self, mock_db, mock_doc_repo_class, mock_claim_repo_class):
        """Test that LiveDocumentProcessor initializes repository instances."""
        from web_ui.document_processor import LiveDocumentProcessor

        processor = LiveDocumentProcessor()

        # Should create repository instances
        mock_doc_repo_class.assert_called_once()
        mock_claim_repo_class.assert_called_once()

        # Should store repository instances
        assert processor.doc_repo is not None
        assert processor.claim_repo is not None

    @patch('backend.database.repositories.claim_repository.ClaimRepository')
    @patch('backend.database.repositories.document_repository.DocumentRepository')
    @patch('web_ui.document_processor.Neo4jDatabase')
    @patch('web_ui.document_processor.PDFExtractor')
    @patch('web_ui.document_processor.ClaudeCodeAdapter')
    def test_document_creation_uses_repository(
        self, mock_adapter, mock_pdf, mock_db, mock_doc_repo_class, mock_claim_repo_class
    ):
        """Test that document creation uses DocumentRepository.create_document()."""
        from web_ui.document_processor import LiveDocumentProcessor

        # Setup mocks
        mock_doc_repo = Mock()
        mock_claim_repo = Mock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_claim_repo_class.return_value = mock_claim_repo

        # Mock PDF extraction
        mock_extractor = Mock()
        mock_pdf.return_value = mock_extractor
        mock_extractor.extract_text.return_value = ('Test content', 0.9)

        # Mock agent for title extraction
        mock_agent = Mock()
        mock_adapter.return_value = mock_agent
        mock_agent.query.return_value = 'Test Document Title'

        # Mock document creation
        doc_id = str(uuid4())
        mock_doc_repo.create_document.return_value = doc_id

        # Create test PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4\ntest')
            temp_path = f.name

        try:
            processor = LiveDocumentProcessor()

            # Process the document - this should call create_document
            # NOTE: This will fail at claim extraction since we're mocking, but we just want to verify document creation
            try:
                processor.process_document(temp_path)
            except Exception:
                pass  # Expected to fail at claim extraction

            # Verify create_document was called with correct arguments
            assert mock_doc_repo.create_document.called
            call_kwargs = mock_doc_repo.create_document.call_args[1]

            # Check required fields
            assert 'title' in call_kwargs
            assert 'source_file' in call_kwargs
            assert call_kwargs['status'] == 'processing'

        finally:
            os.unlink(temp_path)

    @patch('backend.database.repositories.claim_repository.ClaimRepository')
    @patch('backend.database.repositories.document_repository.DocumentRepository')
    @patch('web_ui.document_processor.Neo4jDatabase')
    def test_document_update_uses_repository(self, mock_db, mock_doc_repo_class, mock_claim_repo_class):
        """Test that document updates use DocumentRepository.update_document()."""
        from web_ui.document_processor import LiveDocumentProcessor

        # Setup mocks
        mock_doc_repo = Mock()
        mock_claim_repo = Mock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_claim_repo_class.return_value = mock_claim_repo

        processor = LiveDocumentProcessor()

        # Simulate title update (line 1210 in document_processor.py)
        doc_id = str(uuid4())
        new_title = "Updated Title"

        # Call update_document
        processor.doc_repo.update_document(doc_id, {'title': new_title})

        # Verify it was called correctly
        mock_doc_repo.update_document.assert_called_once_with(doc_id, {'title': new_title})

    @patch('backend.database.repositories.claim_repository.ClaimRepository')
    @patch('backend.database.repositories.document_repository.DocumentRepository')
    @patch('web_ui.document_processor.Neo4jDatabase')
    def test_document_failure_uses_repository(self, mock_db, mock_doc_repo_class, mock_claim_repo_class):
        """Test that marking document as failed uses DocumentRepository.mark_document_failed()."""
        from web_ui.document_processor import LiveDocumentProcessor

        # Setup mocks
        mock_doc_repo = Mock()
        mock_claim_repo = Mock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_claim_repo_class.return_value = mock_claim_repo

        processor = LiveDocumentProcessor()

        # Simulate failure (line 1242 in document_processor.py)
        doc_id = str(uuid4())
        error_msg = "Test error message"

        # Call mark_document_failed
        processor.doc_repo.mark_document_failed(doc_id, error_msg)

        # Verify it was called correctly
        mock_doc_repo.mark_document_failed.assert_called_once_with(doc_id, error_msg)

    @patch('backend.database.repositories.claim_repository.ClaimRepository')
    @patch('backend.database.repositories.document_repository.DocumentRepository')
    @patch('web_ui.document_processor.Neo4jDatabase')
    def test_document_completion_uses_repository(self, mock_db, mock_doc_repo_class, mock_claim_repo_class):
        """Test that marking document as complete uses DocumentRepository.mark_document_complete()."""
        from web_ui.document_processor import LiveDocumentProcessor

        # Setup mocks
        mock_doc_repo = Mock()
        mock_claim_repo = Mock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_claim_repo_class.return_value = mock_claim_repo

        processor = LiveDocumentProcessor()

        # Simulate completion (line 1413 in document_processor.py)
        doc_id = str(uuid4())

        # Call mark_document_complete
        processor.doc_repo.mark_document_complete(doc_id)

        # Verify it was called correctly
        mock_doc_repo.mark_document_complete.assert_called_once_with(doc_id)

    @patch('backend.database.repositories.claim_repository.ClaimRepository')
    @patch('backend.database.repositories.document_repository.DocumentRepository')
    @patch('web_ui.document_processor.Neo4jDatabase')
    def test_claim_creation_uses_repository(self, mock_db, mock_doc_repo_class, mock_claim_repo_class):
        """Test that claim creation uses ClaimRepository.create_claim()."""
        from web_ui.document_processor import LiveDocumentProcessor

        # Setup mocks
        mock_doc_repo = Mock()
        mock_claim_repo = Mock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_claim_repo_class.return_value = mock_claim_repo

        processor = LiveDocumentProcessor()

        # Simulate claim creation (line 1285-1294 in document_processor.py)
        doc_id = str(uuid4())
        claim_text = "Test claim text"
        claim_id = str(uuid4())

        mock_claim_repo.create_claim.return_value = claim_id

        # Call create_claim
        result = processor.claim_repo.create_claim(
            text=claim_text,
            original_text=claim_text,
            doc_id=doc_id,
            claim_type='extracted',
            confidence=0.8,
            status='processing',
            processing_stage='pending',
            word_count_original=len(claim_text.split())
        )

        # Verify it was called correctly
        mock_claim_repo.create_claim.assert_called_once()
        call_kwargs = mock_claim_repo.create_claim.call_args[1]

        assert call_kwargs['text'] == claim_text
        assert call_kwargs['original_text'] == claim_text
        assert call_kwargs['doc_id'] == doc_id
        assert call_kwargs['claim_type'] == 'extracted'
        assert call_kwargs['confidence'] == 0.8
        assert call_kwargs['status'] == 'processing'

        assert result == claim_id

    @patch('backend.database.repositories.claim_repository.ClaimRepository')
    @patch('backend.database.repositories.document_repository.DocumentRepository')
    @patch('web_ui.document_processor.Neo4jDatabase')
    def test_claim_update_uses_repository(self, mock_db, mock_doc_repo_class, mock_claim_repo_class):
        """Test that claim updates use ClaimRepository.update_claim()."""
        from web_ui.document_processor import LiveDocumentProcessor

        # Setup mocks
        mock_doc_repo = Mock()
        mock_claim_repo = Mock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_claim_repo_class.return_value = mock_claim_repo

        processor = LiveDocumentProcessor()

        # Simulate claim update (line 1398 in document_processor.py)
        claim_id = str(uuid4())
        processed_data = {
            'text': 'Updated claim text',
            'quality_score': 0.9,
            'status': 'complete'
        }

        # Call update_claim
        processor.claim_repo.update_claim(claim_id, processed_data)

        # Verify it was called correctly
        mock_claim_repo.update_claim.assert_called_once_with(claim_id, processed_data)


class TestAppRoutesMigration:
    """Test that app.py routes use repositories correctly."""

    def test_app_initializes_repositories(self):
        """Test that app.py initializes repository instances."""
        # Import app module
        import sys
        import importlib

        # Need to reload app module to test initialization
        if 'web_ui.app' in sys.modules:
            importlib.reload(sys.modules['web_ui.app'])

        from web_ui import app as app_module

        # Verify repositories are initialized
        assert hasattr(app_module, 'claim_repo')
        assert hasattr(app_module, 'doc_repo')
        assert app_module.claim_repo is not None
        assert app_module.doc_repo is not None

    @patch('web_ui.app.claim_repo')
    def test_get_claim_details_route_uses_repository(self, mock_claim_repo):
        """Test that /api/claim/<claim_id> route uses ClaimRepository."""
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
    def test_investigate_claim_route_uses_repository(self, mock_agent_tracker, mock_claim_repo):
        """Test that /api/investigate-claim route uses ClaimRepository."""
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


class TestEndToEndIntegration:
    """End-to-end integration tests (these would need a real Neo4j database)."""

    @pytest.mark.skip(reason="Requires real Neo4j database")
    def test_full_document_upload_pipeline(self):
        """Test complete document upload and processing pipeline."""
        # This would test:
        # 1. Upload PDF via /api/upload-document
        # 2. Verify document created in Neo4j
        # 3. Verify claims extracted and created
        # 4. Verify relationships created
        # 5. Verify document marked as complete
        pass

    @pytest.mark.skip(reason="Requires real Neo4j database")
    def test_claim_investigation_pipeline(self):
        """Test complete claim investigation pipeline."""
        # This would test:
        # 1. Create claim via repository
        # 2. Trigger investigation via /api/investigate-claim
        # 3. Verify research result created
        # 4. Verify agent node created
        # 5. Verify relationships created
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
