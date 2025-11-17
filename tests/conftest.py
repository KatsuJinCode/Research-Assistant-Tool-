"""
Shared pytest fixtures and configuration.
"""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def sample_papers_dir(project_root):
    """Return the sample papers directory."""
    return project_root / "sample papers"


@pytest.fixture(scope="session")
def szasz_pdf_path(sample_papers_dir):
    """Return the path to the Szasz PDF."""
    return sample_papers_dir / "SHORT-The-Myth-of-Mental-Illness.pdf"


@pytest.fixture
def sample_claims():
    """Sample claims from Szasz paper for testing."""
    return [
        {
            "text": "Mental illness is not literally a 'thing' — or physical object",
            "type": "Definitional",
            "has_qualifiers": False
        },
        {
            "text": "There is no such thing as mental illness",
            "type": "Normative",
            "has_qualifiers": False
        },
        {
            "text": "Mental illness can exist only in the same sort of way in which other theoretical concepts exist",
            "type": "Theoretical",
            "has_qualifiers": True,
            "qualifiers": ["can"]
        },
        {
            "text": "Familiar theories are in the habit of posing as 'objective truths'",
            "type": "Methodological",
            "has_qualifiers": False
        },
        {
            "text": "The notion of mental illness is extremely widely used nowadays",
            "type": "Empirical",
            "has_qualifiers": False
        }
    ]


@pytest.fixture
def modal_qualifier_examples():
    """Examples of modal qualifiers for testing."""
    return {
        "can": "This can happen in practice",
        "may": "This may be correct",
        "might": "This might work",
        "could": "This could succeed",
        "would": "This would help",
        "should": "This should work",
        "must": "This must be true"
    }


@pytest.fixture
def frequency_qualifier_examples():
    """Examples of frequency qualifiers for testing."""
    return {
        "always": "This always happens",
        "never": "This never occurs",
        "often": "This often appears",
        "rarely": "This rarely manifests",
        "sometimes": "This sometimes works",
        "usually": "This usually succeeds",
        "mostly": "This mostly applies"
    }


@pytest.fixture
def quantity_qualifier_examples():
    """Examples of quantity qualifiers for testing."""
    return {
        "all": "All participants responded",
        "every": "Every study found this",
        "each": "Each case showed improvement",
        "some": "Some evidence suggests this",
        "most": "Most studies agree",
        "many": "Many researchers believe this",
        "few": "Few studies examined this",
        "several": "Several factors contribute"
    }


@pytest.fixture
def normalization_examples():
    """Examples of claim normalizations for testing."""
    return [
        {
            "original": "Mental illness can exist only in the same sort of way in which other theoretical concepts exist",
            "good_normalized": "Mental illness can only exist in the same way as other theoretical concepts",
            "bad_normalized": "Mental illness exists in the same way as other theoretical concepts",
            "should_preserve": True
        },
        {
            "original": "Mental illness is not literally a 'thing' — or physical object",
            "good_normalized": "Mental illness is not a physical object",
            "bad_normalized": "Mental illness is not physical",
            "should_preserve": True
        },
        {
            "original": "Some studies often suggest this may be true",
            "good_normalized": "Some studies often suggest this may be true",
            "bad_normalized": "Studies suggest this is true",
            "should_preserve": False
        }
    ]
