"""Tests for claim models."""

import pytest

from research_assistant_models import Claim, Qualifier, ClaimStatus


class TestQualifier:
    """Tests for Qualifier model."""

    def test_create_qualifier(self):
        """Test creating a Qualifier."""
        qualifier = Qualifier(
            qualifier_type="modal",
            qualifier_text="may",
            semantic_impact="Indicates possibility",
        )

        assert qualifier.qualifier_type == "modal"
        assert qualifier.qualifier_text == "may"
        assert qualifier.semantic_impact == "Indicates possibility"

    def test_invalid_qualifier_type(self):
        """Test that invalid qualifier_type raises error."""
        with pytest.raises(ValueError, match="qualifier_type must be one of"):
            Qualifier(
                qualifier_type="invalid_type",
                qualifier_text="may",
                semantic_impact="Test",
            )

    def test_valid_qualifier_types(self):
        """Test all valid qualifier types."""
        valid_types = ["modal", "frequency", "quantity", "certainty", "temporal"]

        for qtype in valid_types:
            qualifier = Qualifier(
                qualifier_type=qtype, qualifier_text="test", semantic_impact="test"
            )
            assert qualifier.qualifier_type == qtype


class TestClaimStatus:
    """Tests for ClaimStatus enum."""

    def test_all_statuses(self):
        """Test all ClaimStatus values."""
        assert ClaimStatus.EXTRACTED == "extracted"
        assert ClaimStatus.QUEUED == "queued"
        assert ClaimStatus.INVESTIGATING == "investigating"
        assert ClaimStatus.SUPPORTED == "supported"
        assert ClaimStatus.CHALLENGED == "challenged"
        assert ClaimStatus.VERIFIED == "verified"
        assert ClaimStatus.UNCERTAIN == "uncertain"
        assert ClaimStatus.ARCHIVED == "archived"


class TestClaim:
    """Tests for Claim model."""

    def test_create_claim(self, sample_claim_data):
        """Test creating a Claim."""
        claim = Claim(**sample_claim_data)

        assert claim.original_text == "Coffee consumption reduces risk of type 2 diabetes"
        assert claim.confidence_score == 0.75
        assert claim.status == ClaimStatus.EXTRACTED

    def test_claim_defaults(self):
        """Test default values."""
        claim = Claim(original_text="Test claim")

        assert claim.status == ClaimStatus.EXTRACTED
        assert claim.priority_score == 50
        assert claim.investigation_count == 0
        assert claim.support_count == 0
        assert claim.challenge_count == 0

    def test_confidence_score_validation(self):
        """Test confidence_score must be between 0 and 1."""
        # Valid
        claim = Claim(original_text="Test", confidence_score=0.5)
        assert claim.confidence_score == 0.5

        # Invalid - too high
        with pytest.raises(ValueError):
            Claim(original_text="Test", confidence_score=1.5)

        # Invalid - negative
        with pytest.raises(ValueError):
            Claim(original_text="Test", confidence_score=-0.1)

    def test_claim_with_qualifiers(self):
        """Test Claim with qualifiers."""
        qualifiers = [
            Qualifier(
                qualifier_type="modal",
                qualifier_text="may",
                semantic_impact="Possibility",
            ),
            Qualifier(
                qualifier_type="frequency",
                qualifier_text="sometimes",
                semantic_impact="Occasional",
            ),
        ]

        claim = Claim(original_text="Test claim", qualifiers=qualifiers)

        assert len(claim.qualifiers) == 2
        assert claim.qualifiers[0].qualifier_type == "modal"
        assert claim.qualifiers[1].qualifier_type == "frequency"

    def test_json_serialization(self, sample_claim_data):
        """Test JSON serialization."""
        claim = Claim(**sample_claim_data)

        json_str = claim.model_dump_json()
        assert isinstance(json_str, str)

        claim2 = Claim.model_validate_json(json_str)
        assert claim2.original_text == claim.original_text
        assert claim2.confidence_score == claim.confidence_score

    def test_enum_serialization(self):
        """Test that enum values are serialized correctly."""
        claim = Claim(original_text="Test", status=ClaimStatus.VERIFIED)

        data = claim.model_dump()
        # With use_enum_values = True, should be string not enum
        assert data["status"] == "verified"
        assert isinstance(data["status"], str)
