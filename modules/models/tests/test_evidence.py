"""Tests for evidence models."""

import pytest

from research_assistant_models import Evidence, Finding, FindingType


class TestEvidence:
    """Tests for Evidence model."""

    def test_create_evidence(self, sample_evidence_data):
        """Test creating Evidence."""
        evidence = Evidence(**sample_evidence_data)

        assert evidence.source_category == "academic"
        assert "Smith, J." in evidence.citation_apa
        assert evidence.relevance_score == 0.9
        assert evidence.credibility_score == 0.85

    def test_score_validation(self):
        """Test that scores must be between 0 and 1."""
        # Valid
        evidence = Evidence(
            source_category="academic",
            citation_apa="Test citation",
            relevance_score=0.5,
            credibility_score=0.5,
        )
        assert evidence.relevance_score == 0.5

        # Invalid relevance score
        with pytest.raises(ValueError):
            Evidence(
                source_category="academic",
                citation_apa="Test",
                relevance_score=1.5,
            )

        # Invalid credibility score
        with pytest.raises(ValueError):
            Evidence(
                source_category="academic",
                citation_apa="Test",
                credibility_score=-0.1,
            )

    def test_optional_fields(self):
        """Test that optional fields work."""
        evidence = Evidence(
            source_category="web", citation_apa="Web Citation (2023)."
        )

        assert evidence.relevant_quote is None
        assert evidence.relevance_score is None
        assert evidence.doi is None


class TestFindingType:
    """Tests for FindingType enum."""

    def test_all_finding_types(self):
        """Test all FindingType values."""
        assert FindingType.SUPPORT == "support"
        assert FindingType.CHALLENGE == "challenge"
        assert FindingType.NEUTRAL == "neutral"
        assert FindingType.CLARIFICATION == "clarification"


class TestFinding:
    """Tests for Finding model."""

    def test_create_finding(self):
        """Test creating a Finding."""
        finding = Finding(
            finding_type=FindingType.SUPPORT,
            summary="Found supporting evidence",
            detailed_analysis="Detailed analysis here",
            confidence=0.8,
        )

        assert finding.finding_type == FindingType.SUPPORT
        assert finding.summary == "Found supporting evidence"
        assert finding.confidence == 0.8

    def test_finding_with_evidence(self, sample_evidence_data):
        """Test Finding with Evidence list."""
        evidence_items = [
            Evidence(**sample_evidence_data),
            Evidence(source_category="academic", citation_apa="Another citation"),
        ]

        finding = Finding(
            finding_type=FindingType.CHALLENGE,
            summary="Found challenges",
            evidence=evidence_items,
        )

        assert len(finding.evidence) == 2
        assert finding.evidence[0].source_category == "academic"

    def test_confidence_validation(self):
        """Test confidence must be between 0 and 1."""
        with pytest.raises(ValueError):
            Finding(
                finding_type=FindingType.SUPPORT,
                summary="Test",
                confidence=2.0,
            )

    def test_json_serialization(self, sample_evidence_data):
        """Test JSON serialization."""
        finding = Finding(
            finding_type=FindingType.SUPPORT,
            summary="Test finding",
            evidence=[Evidence(**sample_evidence_data)],
        )

        json_str = finding.model_dump_json()
        finding2 = Finding.model_validate_json(json_str)

        assert finding2.finding_type == FindingType.SUPPORT
        assert len(finding2.evidence) == 1
