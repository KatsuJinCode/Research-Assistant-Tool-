"""Pytest configuration and shared fixtures for model tests."""

import pytest
from datetime import datetime
from uuid import uuid4


@pytest.fixture
def sample_uuid():
    """Generate a sample UUID for testing."""
    return uuid4()


@pytest.fixture
def sample_datetime():
    """Generate a sample datetime for testing."""
    return datetime(2023, 11, 18, 12, 0, 0)


@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "title": "Test Research Paper",
        "source_type": "pdf",
        "file_path": "/path/to/test.pdf",
        "metadata": {"author": "Test Author", "year": 2023},
    }


@pytest.fixture
def sample_claim_data():
    """Sample claim data for testing."""
    return {
        "original_text": "Coffee consumption reduces risk of type 2 diabetes",
        "normalized_text": "Coffee consumption may reduce risk of type 2 diabetes",
        "confidence_score": 0.75,
        "priority_score": 80,
    }


@pytest.fixture
def sample_evidence_data():
    """Sample evidence data for testing."""
    return {
        "source_category": "academic",
        "citation_apa": "Smith, J. (2023). Coffee and Health. Journal of Medicine, 10(2), 45-60.",
        "relevant_quote": "Our study found a 30% reduction in diabetes risk.",
        "relevance_score": 0.9,
        "credibility_score": 0.85,
        "publication_year": 2023,
    }
