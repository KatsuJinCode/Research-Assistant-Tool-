"""
Unit tests for PDFExtractor.

Tests PDF text extraction, metadata handling, and error cases.
"""

import pytest
from pathlib import Path
from research_agent.document_processing.pdf_extractor import PDFExtractor


@pytest.fixture
def extractor():
    """Create a PDFExtractor instance for testing."""
    return PDFExtractor()


@pytest.fixture
def sample_pdf_path():
    """Path to the sample Szasz PDF."""
    return Path("sample papers/SHORT-The-Myth-of-Mental-Illness.pdf")


class TestPDFExtraction:
    """Test basic PDF extraction functionality."""

    @pytest.mark.unit
    def test_extract_returns_dict(self, extractor, sample_pdf_path):
        """Test that extract returns a dictionary."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        result = extractor.extract(sample_pdf_path)

        assert isinstance(result, dict)
        assert 'full_text' in result
        assert 'page_count' in result
        assert 'total_chars' in result

    @pytest.mark.unit
    def test_extract_full_text(self, extractor, sample_pdf_path):
        """Test that full text is extracted."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        result = extractor.extract(sample_pdf_path)

        assert isinstance(result['full_text'], str)
        assert len(result['full_text']) > 0

    @pytest.mark.unit
    @pytest.mark.critical
    def test_extract_szasz_pdf_stats(self, extractor, sample_pdf_path):
        """Test extraction of Szasz PDF produces expected statistics."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        result = extractor.extract(sample_pdf_path)

        # Expected values for SHORT-The-Myth-of-Mental-Illness.pdf
        assert result['page_count'] == 6
        assert 40000 <= result['total_chars'] <= 45000  # ~41,293 chars
        assert 'mental illness' in result['full_text'].lower()

    @pytest.mark.unit
    def test_extract_metadata(self, extractor, sample_pdf_path):
        """Test that metadata is extracted."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        result = extractor.extract(sample_pdf_path)

        assert 'metadata' in result
        assert isinstance(result['metadata'], dict)

    @pytest.mark.unit
    def test_extract_pages_info(self, extractor, sample_pdf_path):
        """Test that page information is extracted."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        result = extractor.extract(sample_pdf_path)

        assert result['page_count'] > 0
        assert isinstance(result['page_count'], int)


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    @pytest.mark.unit
    def test_nonexistent_file(self, extractor):
        """Test that nonexistent file raises appropriate error."""
        fake_path = Path("nonexistent.pdf")

        with pytest.raises((FileNotFoundError, Exception)):
            extractor.extract(fake_path)

    @pytest.mark.unit
    def test_invalid_pdf(self, extractor, tmp_path):
        """Test that invalid PDF file raises appropriate error."""
        # Create a fake PDF file
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_text("This is not a valid PDF")

        with pytest.raises(Exception):
            extractor.extract(fake_pdf)


class TestTextQuality:
    """Test quality of extracted text."""

    @pytest.mark.unit
    def test_text_contains_expected_content(self, extractor, sample_pdf_path):
        """Test that extracted text contains expected key phrases."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        result = extractor.extract(sample_pdf_path)
        text_lower = result['full_text'].lower()

        # Key phrases from Szasz paper
        expected_phrases = [
            'mental illness',
            'szasz',
            'theoretical concepts'
        ]

        for phrase in expected_phrases:
            assert phrase in text_lower, f"Expected phrase '{phrase}' not found in extracted text"

    @pytest.mark.unit
    def test_word_count_reasonable(self, extractor, sample_pdf_path):
        """Test that word count is reasonable for the document."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        result = extractor.extract(sample_pdf_path)
        words = result['full_text'].split()

        # Szasz paper should have ~17,000 words
        assert 15000 <= len(words) <= 20000

    @pytest.mark.unit
    def test_no_excessive_whitespace(self, extractor, sample_pdf_path):
        """Test that extracted text doesn't have excessive whitespace."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        result = extractor.extract(sample_pdf_path)

        # Check for excessive consecutive whitespace
        assert '    ' not in result['full_text'].replace('\n', ' ')
