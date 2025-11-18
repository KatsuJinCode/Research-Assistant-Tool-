"""
Unit tests for domain models.

Tests Claim and Document models for validation, serialization, and business logic.
"""

import pytest
from backend.database.models import Claim, Document


class TestClaimModel:
    """Test Claim domain model."""

    def test_create_claim_with_required_fields(self):
        """Test creating claim with minimal required fields."""
        claim = Claim(
            text="This is a claim",
            original_text="This is the original claim text",
            doc_id="doc-123"
        )

        assert claim.text == "This is a claim"
        assert claim.original_text == "This is the original claim text"
        assert claim.doc_id == "doc-123"
        assert claim.claim_type == 'extracted'
        assert claim.confidence == 0.0
        assert claim.status == 'processing'

    def test_create_claim_with_all_fields(self):
        """Test creating claim with all fields."""
        claim = Claim(
            text="Simplified claim",
            original_text="Original claim text",
            doc_id="doc-123",
            id="claim-456",
            claim_type="super_claim",
            confidence=0.95,
            status="complete",
            processing_stage="validated",
            disposition="central",
            summary="Claim summary",
            simplified_text="Simple text",
            normalized_text="normalized text",
            claim_category="factual",
            is_super_claim=True,
            priority_score=85,
            credibility_score=0.9,
            source_page=42,
            metadata={"custom_field": "value"}
        )

        assert claim.id == "claim-456"
        assert claim.claim_type == "super_claim"
        assert claim.confidence == 0.95
        assert claim.is_super_claim is True
        assert claim.metadata["custom_field"] == "value"

    def test_claim_validates_empty_text(self):
        """Test claim raises error for empty text."""
        with pytest.raises(ValueError, match="Claim text cannot be empty"):
            Claim(text="", original_text="original", doc_id="doc-123")

    def test_claim_validates_empty_original_text(self):
        """Test claim raises error for empty original text."""
        with pytest.raises(ValueError, match="Original text cannot be empty"):
            Claim(text="claim", original_text="", doc_id="doc-123")

    def test_claim_validates_missing_doc_id(self):
        """Test claim raises error for missing doc_id."""
        with pytest.raises(ValueError, match="Document ID is required"):
            Claim(text="claim", original_text="original", doc_id="")

    def test_claim_validates_confidence_range(self):
        """Test claim validates confidence is between 0.0 and 1.0."""
        # Too low
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Claim(text="claim", original_text="original", doc_id="doc-123", confidence=-0.1)

        # Too high
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Claim(text="claim", original_text="original", doc_id="doc-123", confidence=1.5)

    def test_claim_auto_calculates_word_count(self):
        """Test claim automatically calculates word count."""
        claim = Claim(
            text="claim",
            original_text="This is a five word sentence",
            doc_id="doc-123"
        )

        assert claim.word_count_original == 6

    def test_claim_preserves_manual_word_count(self):
        """Test claim preserves manually provided word count."""
        claim = Claim(
            text="claim",
            original_text="original",
            doc_id="doc-123",
            word_count_original=999
        )

        assert claim.word_count_original == 999

    def test_claim_to_dict_excludes_none(self):
        """Test to_dict excludes None values by default."""
        claim = Claim(
            text="claim",
            original_text="original",
            doc_id="doc-123"
        )

        data = claim.to_dict()

        assert 'text' in data
        assert 'original_text' in data
        assert 'id' not in data  # None value excluded
        assert 'summary' not in data  # None value excluded

    def test_claim_to_dict_includes_none(self):
        """Test to_dict includes None values when requested."""
        claim = Claim(
            text="claim",
            original_text="original",
            doc_id="doc-123"
        )

        data = claim.to_dict(include_none=True)

        assert 'text' in data
        assert 'id' in data
        assert data['id'] is None

    def test_claim_from_dict(self):
        """Test creating claim from dictionary."""
        data = {
            'id': 'claim-123',
            'text': 'Claim text',
            'original_text': 'Original text',
            'doc_id': 'doc-456',
            'confidence': 0.8,
            'status': 'complete'
        }

        claim = Claim.from_dict(data)

        assert claim.id == 'claim-123'
        assert claim.text == 'Claim text'
        assert claim.confidence == 0.8

    def test_claim_from_dict_with_metadata(self):
        """Test from_dict handles unknown fields as metadata."""
        data = {
            'text': 'Claim text',
            'original_text': 'Original text',
            'doc_id': 'doc-456',
            'custom_field': 'custom value',
            'another_field': 123
        }

        claim = Claim.from_dict(data)

        assert claim.metadata['custom_field'] == 'custom value'
        assert claim.metadata['another_field'] == 123

    def test_claim_is_complete(self):
        """Test is_complete status check."""
        claim = Claim(
            text="claim",
            original_text="original",
            doc_id="doc-123",
            status="complete"
        )

        assert claim.is_complete() is True
        assert claim.is_failed() is False
        assert claim.is_pending() is False

    def test_claim_is_failed(self):
        """Test is_failed status check."""
        claim = Claim(
            text="claim",
            original_text="original",
            doc_id="doc-123",
            status="failed"
        )

        assert claim.is_complete() is False
        assert claim.is_failed() is True
        assert claim.is_pending() is False

    def test_claim_is_pending(self):
        """Test is_pending status check."""
        claim_processing = Claim(
            text="claim",
            original_text="original",
            doc_id="doc-123",
            status="processing"
        )

        claim_pending = Claim(
            text="claim",
            original_text="original",
            doc_id="doc-123",
            status="pending"
        )

        assert claim_processing.is_pending() is True
        assert claim_pending.is_pending() is True

    def test_claim_repr(self):
        """Test string representation."""
        claim = Claim(
            id="claim-123",
            text="This is a long claim text that should be truncated in the repr",
            original_text="original",
            doc_id="doc-123",
            claim_type="super_claim",
            status="complete"
        )

        repr_str = repr(claim)

        assert "claim-123" in repr_str
        assert "super_claim" in repr_str
        assert "complete" in repr_str


class TestDocumentModel:
    """Test Document domain model."""

    def test_create_document_with_required_fields(self):
        """Test creating document with minimal required fields."""
        doc = Document(
            title="Test Document",
            source_file="/path/to/document.pdf"
        )

        assert doc.title == "Test Document"
        assert doc.source_file == "/path/to/document.pdf"
        assert doc.status == 'processing'

    def test_create_document_with_all_fields(self):
        """Test creating document with all fields."""
        doc = Document(
            title="Research Paper",
            source_file="/path/to/paper.pdf",
            id="doc-123",
            status="complete",
            source_type="PDF",
            file_size=1024000,
            page_count=10,
            author="John Doe",
            publication_date="2025-01-01",
            doi="10.1234/example",
            url="https://example.com/paper",
            extraction_method="pdfplumber",
            processing_time_seconds=45.5,
            metadata={"journal": "Nature"}
        )

        assert doc.id == "doc-123"
        assert doc.status == "complete"
        assert doc.file_size == 1024000
        assert doc.page_count == 10
        assert doc.metadata["journal"] == "Nature"

    def test_document_validates_empty_title(self):
        """Test document raises error for empty title."""
        with pytest.raises(ValueError, match="Document title cannot be empty"):
            Document(title="", source_file="/path/to/file.pdf")

    def test_document_validates_empty_source_file(self):
        """Test document raises error for empty source file."""
        with pytest.raises(ValueError, match="Source file path cannot be empty"):
            Document(title="Test", source_file="")

    def test_document_validates_negative_file_size(self):
        """Test document raises error for negative file size."""
        with pytest.raises(ValueError, match="File size cannot be negative"):
            Document(
                title="Test",
                source_file="/path/to/file.pdf",
                file_size=-100
            )

    def test_document_validates_negative_page_count(self):
        """Test document raises error for negative page count."""
        with pytest.raises(ValueError, match="Page count cannot be negative"):
            Document(
                title="Test",
                source_file="/path/to/file.pdf",
                page_count=-5
            )

    def test_document_validates_negative_processing_time(self):
        """Test document raises error for negative processing time."""
        with pytest.raises(ValueError, match="Processing time cannot be negative"):
            Document(
                title="Test",
                source_file="/path/to/file.pdf",
                processing_time_seconds=-10.5
            )

    def test_document_to_dict_excludes_none(self):
        """Test to_dict excludes None values by default."""
        doc = Document(
            title="Test Document",
            source_file="/path/to/file.pdf"
        )

        data = doc.to_dict()

        assert 'title' in data
        assert 'source_file' in data
        assert 'id' not in data  # None value excluded
        assert 'author' not in data  # None value excluded

    def test_document_to_dict_includes_none(self):
        """Test to_dict includes None values when requested."""
        doc = Document(
            title="Test Document",
            source_file="/path/to/file.pdf"
        )

        data = doc.to_dict(include_none=True)

        assert 'title' in data
        assert 'id' in data
        assert data['id'] is None

    def test_document_from_dict(self):
        """Test creating document from dictionary."""
        data = {
            'id': 'doc-123',
            'title': 'Test Document',
            'source_file': '/path/to/file.pdf',
            'status': 'complete',
            'page_count': 10
        }

        doc = Document.from_dict(data)

        assert doc.id == 'doc-123'
        assert doc.title == 'Test Document'
        assert doc.page_count == 10

    def test_document_from_dict_with_metadata(self):
        """Test from_dict handles unknown fields as metadata."""
        data = {
            'title': 'Test Document',
            'source_file': '/path/to/file.pdf',
            'custom_field': 'custom value',
            'another_field': 456
        }

        doc = Document.from_dict(data)

        assert doc.metadata['custom_field'] == 'custom value'
        assert doc.metadata['another_field'] == 456

    def test_document_is_complete(self):
        """Test is_complete status check."""
        doc = Document(
            title="Test",
            source_file="/path/to/file.pdf",
            status="complete"
        )

        assert doc.is_complete() is True
        assert doc.is_failed() is False
        assert doc.is_processing() is False

    def test_document_is_failed(self):
        """Test is_failed status check."""
        doc = Document(
            title="Test",
            source_file="/path/to/file.pdf",
            status="failed"
        )

        assert doc.is_complete() is False
        assert doc.is_failed() is True
        assert doc.is_processing() is False

    def test_document_is_processing(self):
        """Test is_processing status check."""
        doc_processing = Document(
            title="Test",
            source_file="/path/to/file.pdf",
            status="processing"
        )

        doc_queued = Document(
            title="Test",
            source_file="/path/to/file.pdf",
            status="queued"
        )

        assert doc_processing.is_processing() is True
        assert doc_queued.is_processing() is True

    def test_document_mark_failed(self):
        """Test marking document as failed."""
        doc = Document(
            title="Test",
            source_file="/path/to/file.pdf",
            status="processing"
        )

        doc.mark_failed("Extraction error")

        assert doc.status == "failed"
        assert doc.error == "Extraction error"

    def test_document_mark_complete(self):
        """Test marking document as complete."""
        doc = Document(
            title="Test",
            source_file="/path/to/file.pdf",
            status="processing",
            error="Previous error"
        )

        doc.mark_complete()

        assert doc.status == "complete"
        assert doc.error is None

    def test_document_repr(self):
        """Test string representation."""
        doc = Document(
            id="doc-123",
            title="This is a very long document title that should be truncated",
            source_file="/path/to/document.pdf",
            status="complete"
        )

        repr_str = repr(doc)

        assert "doc-123" in repr_str
        assert "complete" in repr_str
        assert "/path/to/document.pdf" in repr_str
