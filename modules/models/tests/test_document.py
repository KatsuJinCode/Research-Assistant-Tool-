"""Tests for document models."""

import pytest
from uuid import UUID
from datetime import datetime

from research_assistant_models import Document, ExtractionResult, PageInfo


class TestPageInfo:
    """Tests for PageInfo model."""

    def test_create_page_info(self):
        """Test creating a PageInfo instance."""
        page = PageInfo(
            page_number=1,
            text="Sample page text",
            char_count=100,
            word_count=20,
            has_images=True,
        )

        assert page.page_number == 1
        assert page.text == "Sample page text"
        assert page.char_count == 100
        assert page.word_count == 20
        assert page.has_images is True

    def test_page_number_validation(self):
        """Test that page_number must be >= 1."""
        with pytest.raises(ValueError):
            PageInfo(
                page_number=0,  # Invalid
                text="Test",
                char_count=10,
                word_count=2,
            )

    def test_json_serialization(self):
        """Test JSON serialization."""
        page = PageInfo(
            page_number=1, text="Test", char_count=4, word_count=1
        )

        json_data = page.model_dump_json()
        assert isinstance(json_data, str)

        # Deserialize
        page2 = PageInfo.model_validate_json(json_data)
        assert page2.page_number == page.page_number
        assert page2.text == page.text


class TestExtractionResult:
    """Tests for ExtractionResult model."""

    def test_create_extraction_result(self):
        """Test creating an ExtractionResult."""
        result = ExtractionResult(
            full_text="Complete document text",
            page_count=10,
            total_chars=5000,
            total_words=800,
            extraction_method="pdfplumber",
            quality_score=0.95,
        )

        assert result.full_text == "Complete document text"
        assert result.page_count == 10
        assert result.extraction_method == "pdfplumber"
        assert result.quality_score == 0.95

    def test_quality_score_validation(self):
        """Test quality_score must be between 0 and 1."""
        with pytest.raises(ValueError):
            ExtractionResult(
                full_text="Test",
                page_count=1,
                total_chars=4,
                total_words=1,
                quality_score=1.5,  # Invalid
            )

    def test_with_pages(self):
        """Test ExtractionResult with page information."""
        pages = [
            PageInfo(page_number=1, text="Page 1", char_count=50, word_count=10),
            PageInfo(page_number=2, text="Page 2", char_count=60, word_count=12),
        ]

        result = ExtractionResult(
            full_text="Page 1 Page 2",
            page_count=2,
            total_chars=110,
            total_words=22,
            pages=pages,
        )

        assert len(result.pages) == 2
        assert result.pages[0].page_number == 1
        assert result.pages[1].page_number == 2


class TestDocument:
    """Tests for Document model."""

    def test_create_document(self, sample_document_data):
        """Test creating a Document."""
        doc = Document(**sample_document_data)

        assert doc.title == "Test Research Paper"
        assert doc.source_type == "pdf"
        assert doc.file_path == "/path/to/test.pdf"
        assert doc.metadata["author"] == "Test Author"

    def test_document_with_extraction_result(self, sample_document_data):
        """Test Document with ExtractionResult."""
        extraction = ExtractionResult(
            full_text="Extracted text",
            page_count=5,
            total_chars=1000,
            total_words=150,
        )

        doc = Document(**sample_document_data, extraction_result=extraction)

        assert doc.extraction_result is not None
        assert doc.extraction_result.page_count == 5

    def test_json_serialization_with_uuid(self, sample_uuid, sample_document_data):
        """Test JSON serialization with UUID."""
        doc = Document(id=sample_uuid, **sample_document_data)

        json_str = doc.model_dump_json()
        assert isinstance(json_str, str)

        # UUID should be serialized as string
        doc2 = Document.model_validate_json(json_str)
        assert doc2.id == doc.id

    def test_json_serialization_with_datetime(
        self, sample_datetime, sample_document_data
    ):
        """Test JSON serialization with datetime."""
        doc = Document(uploaded_at=sample_datetime, **sample_document_data)

        json_str = doc.model_dump_json()
        doc2 = Document.model_validate_json(json_str)

        # Datetime should be preserved
        assert doc2.uploaded_at is not None
        assert doc2.uploaded_at.year == 2023
