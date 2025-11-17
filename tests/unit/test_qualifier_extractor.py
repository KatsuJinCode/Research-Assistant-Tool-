"""
Unit tests for QualifierExtractor - CRITICAL COMPONENT.

These tests verify the qualifier extraction and preservation system
that prevents meaning loss during claim normalization.
"""

import pytest
from research_agent.normalization.qualifier_extractor import QualifierExtractor


@pytest.fixture
def extractor():
    """Create a QualifierExtractor instance for testing."""
    return QualifierExtractor()


class TestModalQualifierExtraction:
    """Test extraction of modal qualifiers (can, may, might, etc.)."""

    @pytest.mark.critical
    def test_extract_can_modal(self, extractor):
        """Test extraction of 'can' modal qualifier."""
        text = "Mental illness can exist in theory"
        qualifiers = extractor.extract(text)

        assert len(qualifiers) == 1
        assert qualifiers[0]['type'] == 'modal'
        assert qualifiers[0]['text'] == 'can'
        assert qualifiers[0]['impact'] == 'indicates_possibility'

    @pytest.mark.critical
    def test_extract_may_modal(self, extractor):
        """Test extraction of 'may' modal qualifier."""
        text = "This hypothesis may be correct"
        qualifiers = extractor.extract(text)

        assert len(qualifiers) == 1
        assert qualifiers[0]['type'] == 'modal'
        assert qualifiers[0]['text'] == 'may'

    @pytest.mark.critical
    def test_extract_might_modal(self, extractor):
        """Test extraction of 'might' modal qualifier."""
        text = "The results might indicate correlation"
        qualifiers = extractor.extract(text)

        assert len(qualifiers) == 1
        assert qualifiers[0]['type'] == 'modal'
        assert qualifiers[0]['text'] == 'might'

    def test_extract_should_modal(self, extractor):
        """Test extraction of 'should' modal qualifier."""
        text = "This should be investigated further"
        qualifiers = extractor.extract(text)

        assert len(qualifiers) == 1
        assert qualifiers[0]['type'] == 'modal'
        assert qualifiers[0]['text'] == 'should'

    def test_extract_could_modal(self, extractor):
        """Test extraction of 'could' modal qualifier."""
        text = "This approach could yield results"
        qualifiers = extractor.extract(text)

        assert len(qualifiers) == 1
        assert qualifiers[0]['type'] == 'modal'
        assert qualifiers[0]['text'] == 'could'

    def test_modal_case_insensitive(self, extractor):
        """Test that modal extraction is case-insensitive."""
        text1 = "This Can work"
        text2 = "This CAN work"
        text3 = "This can work"

        for text in [text1, text2, text3]:
            qualifiers = extractor.extract(text)
            assert len(qualifiers) == 1
            assert qualifiers[0]['text'].lower() == 'can'


class TestFrequencyQualifierExtraction:
    """Test extraction of frequency qualifiers (always, never, often, etc.)."""

    @pytest.mark.critical
    def test_extract_always(self, extractor):
        """Test extraction of 'always' frequency qualifier."""
        text = "This pattern always appears in studies"
        qualifiers = extractor.extract(text)

        assert any(q['type'] == 'frequency' and q['text'] == 'always' for q in qualifiers)

    @pytest.mark.critical
    def test_extract_never(self, extractor):
        """Test extraction of 'never' frequency qualifier."""
        text = "This never occurs in practice"
        qualifiers = extractor.extract(text)

        assert any(q['type'] == 'frequency' and q['text'] == 'never' for q in qualifiers)

    def test_extract_often(self, extractor):
        """Test extraction of 'often' frequency qualifier."""
        text = "Researchers often find this pattern"
        qualifiers = extractor.extract(text)

        assert any(q['type'] == 'frequency' and q['text'] == 'often' for q in qualifiers)

    def test_extract_rarely(self, extractor):
        """Test extraction of 'rarely' frequency qualifier."""
        text = "This phenomenon rarely manifests"
        qualifiers = extractor.extract(text)

        assert any(q['type'] == 'frequency' and q['text'] == 'rarely' for q in qualifiers)

    def test_extract_sometimes(self, extractor):
        """Test extraction of 'sometimes' frequency qualifier."""
        text = "The effect sometimes appears"
        qualifiers = extractor.extract(text)

        assert any(q['type'] == 'frequency' and q['text'] == 'sometimes' for q in qualifiers)


class TestQuantityQualifierExtraction:
    """Test extraction of quantity qualifiers (all, some, most, etc.)."""

    @pytest.mark.critical
    def test_extract_all(self, extractor):
        """Test extraction of 'all' quantity qualifier."""
        text = "All participants showed improvement"
        qualifiers = extractor.extract(text)

        assert any(q['type'] == 'quantity' and q['text'] == 'all' for q in qualifiers)

    @pytest.mark.critical
    def test_extract_some(self, extractor):
        """Test extraction of 'some' quantity qualifier."""
        text = "Some evidence suggests correlation"
        qualifiers = extractor.extract(text)

        assert any(q['type'] == 'quantity' and q['text'] == 'some' for q in qualifiers)

    def test_extract_most(self, extractor):
        """Test extraction of 'most' quantity qualifier."""
        text = "Most studies found positive results"
        qualifiers = extractor.extract(text)

        assert any(q['type'] == 'quantity' and q['text'] == 'most' for q in qualifiers)

    def test_extract_many(self, extractor):
        """Test extraction of 'many' quantity qualifier."""
        text = "Many researchers agree"
        qualifiers = extractor.extract(text)

        assert any(q['type'] == 'quantity' and q['text'] == 'many' for q in qualifiers)

    def test_extract_few(self, extractor):
        """Test extraction of 'few' quantity qualifier."""
        text = "Few studies examined this"
        qualifiers = extractor.extract(text)

        assert any(q['type'] == 'quantity' and q['text'] == 'few' for q in qualifiers)


class TestMultipleQualifierExtraction:
    """Test extraction when multiple qualifiers are present."""

    def test_multiple_modals(self, extractor):
        """Test extraction of multiple modal qualifiers."""
        text = "This may or might not work"
        qualifiers = extractor.extract(text)

        modal_texts = [q['text'] for q in qualifiers if q['type'] == 'modal']
        assert 'may' in modal_texts
        assert 'might' in modal_texts

    def test_modal_and_frequency(self, extractor):
        """Test extraction of modal + frequency qualifiers."""
        text = "This can often lead to confusion"
        qualifiers = extractor.extract(text)

        types = [q['type'] for q in qualifiers]
        assert 'modal' in types
        assert 'frequency' in types

    def test_modal_and_quantity(self, extractor):
        """Test extraction of modal + quantity qualifiers."""
        text = "Some theories may explain this"
        qualifiers = extractor.extract(text)

        types = [q['type'] for q in qualifiers]
        assert 'modal' in types
        assert 'quantity' in types

    def test_all_three_types(self, extractor):
        """Test extraction when all three qualifier types are present."""
        text = "Some studies often suggest this might be true"
        qualifiers = extractor.extract(text)

        types = {q['type'] for q in qualifiers}
        assert 'modal' in types
        assert 'frequency' in types
        assert 'quantity' in types


class TestAbsoluteStatements:
    """Test handling of absolute statements (no qualifiers)."""

    @pytest.mark.critical
    def test_no_qualifiers(self, extractor):
        """Test that absolute statements return empty qualifier list."""
        text = "Mental illness is not a physical object"
        qualifiers = extractor.extract(text)

        assert len(qualifiers) == 0

    def test_definitive_claim(self, extractor):
        """Test definitive claim without hedging."""
        text = "There is no such thing as mental illness"
        qualifiers = extractor.extract(text)

        assert len(qualifiers) == 0


class TestQualifierPreservationVerification:
    """Test the CRITICAL qualifier preservation verification system."""

    @pytest.mark.critical
    def test_preservation_success(self, extractor):
        """Test successful qualifier preservation."""
        original = "Mental illness can exist in theory"
        normalized = "Mental illness can exist theoretically"

        result = extractor.verify_preservation(original, normalized)

        assert result['preserved'] is True
        assert len(result['missing']) == 0

    @pytest.mark.critical
    def test_preservation_failure_missing_modal(self, extractor):
        """Test detection of missing modal qualifier - AUTO-FAIL."""
        original = "Mental illness can exist in theory"
        normalized = "Mental illness exists in theory"

        result = extractor.verify_preservation(original, normalized)

        assert result['preserved'] is False
        assert 'can' in result['missing']

    @pytest.mark.critical
    def test_preservation_failure_missing_frequency(self, extractor):
        """Test detection of missing frequency qualifier - AUTO-FAIL."""
        original = "This always happens in practice"
        normalized = "This happens in practice"

        result = extractor.verify_preservation(original, normalized)

        assert result['preserved'] is False
        assert 'always' in result['missing']

    @pytest.mark.critical
    def test_preservation_failure_missing_quantity(self, extractor):
        """Test detection of missing quantity qualifier - AUTO-FAIL."""
        original = "Some studies show positive results"
        normalized = "Studies show positive results"

        result = extractor.verify_preservation(original, normalized)

        assert result['preserved'] is False
        assert 'some' in result['missing']

    def test_preservation_multiple_missing(self, extractor):
        """Test detection when multiple qualifiers are missing."""
        original = "Some studies often suggest this may be true"
        normalized = "Studies suggest this is true"

        result = extractor.verify_preservation(original, normalized)

        assert result['preserved'] is False
        assert len(result['missing']) >= 2

    def test_preservation_no_qualifiers_both(self, extractor):
        """Test preservation when neither has qualifiers."""
        original = "Mental illness is not a physical object"
        normalized = "Mental illness is not physical"

        result = extractor.verify_preservation(original, normalized)

        assert result['preserved'] is True
        assert len(result['missing']) == 0


class TestClaimStrengthAnalysis:
    """Test claim strength analysis based on qualifiers."""

    def test_strong_claim_no_qualifiers(self, extractor):
        """Test that claims without qualifiers are 'strong'."""
        text = "Mental illness is not a physical object"
        analysis = extractor.analyze_claim_strength(text)

        assert analysis['strength'] == 'strong'
        assert analysis['total_qualifiers'] == 0

    def test_neutral_claim_one_qualifier(self, extractor):
        """Test that claims with 1 qualifier are 'neutral'."""
        text = "Mental illness can exist in theory"
        analysis = extractor.analyze_claim_strength(text)

        assert analysis['strength'] == 'neutral'
        assert analysis['total_qualifiers'] == 1

    def test_weak_claim_multiple_qualifiers(self, extractor):
        """Test that claims with 2+ qualifiers are 'weak'."""
        text = "Some studies might suggest this could be true"
        analysis = extractor.analyze_claim_strength(text)

        assert analysis['strength'] == 'weak'
        assert analysis['total_qualifiers'] >= 2

    def test_analysis_includes_temporal(self, extractor):
        """Test that analysis includes temporal constraint check."""
        text = "This can happen"
        analysis = extractor.analyze_claim_strength(text)

        assert 'has_temporal_constraint' in analysis
        assert isinstance(analysis['has_temporal_constraint'], bool)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string(self, extractor):
        """Test extraction from empty string."""
        qualifiers = extractor.extract("")
        assert len(qualifiers) == 0

    def test_whitespace_only(self, extractor):
        """Test extraction from whitespace-only string."""
        qualifiers = extractor.extract("   \n  \t  ")
        assert len(qualifiers) == 0

    def test_very_long_text(self, extractor):
        """Test extraction from very long text."""
        text = "This " + "is " * 1000 + "a claim that may be true"
        qualifiers = extractor.extract(text)

        assert any(q['text'] == 'may' for q in qualifiers)

    def test_special_characters(self, extractor):
        """Test extraction with special characters."""
        text = "This can't, shouldn't, or won't work!"
        qualifiers = extractor.extract(text)

        # Should still extract modals even with punctuation
        texts = [q['text'] for q in qualifiers]
        assert any('can' in t or 'should' in t or 'won' in t for t in texts)

    def test_unicode_text(self, extractor):
        """Test extraction with unicode characters."""
        text = "This théory maÿ be çorrect"
        qualifiers = extractor.extract(text)

        assert any(q['text'] == 'may' for q in qualifiers)


class TestRealWorldClaims:
    """Test with real claims from Szasz paper."""

    @pytest.mark.critical
    def test_szasz_claim_1(self, extractor):
        """Test with actual Szasz claim - absolute statement."""
        text = "Mental illness is not literally a 'thing' — or physical object"
        qualifiers = extractor.extract(text)

        assert len(qualifiers) == 0

    @pytest.mark.critical
    def test_szasz_claim_2(self, extractor):
        """Test with actual Szasz claim - main thesis."""
        text = "There is no such thing as mental illness"
        qualifiers = extractor.extract(text)

        assert len(qualifiers) == 0

    @pytest.mark.critical
    def test_szasz_claim_3(self, extractor):
        """Test with actual Szasz claim - has modal qualifier."""
        text = "Mental illness can exist only in the same sort of way in which other theoretical concepts exist"
        qualifiers = extractor.extract(text)

        assert len(qualifiers) == 1
        assert qualifiers[0]['type'] == 'modal'
        assert qualifiers[0]['text'] == 'can'

    @pytest.mark.critical
    def test_szasz_claim_3_preservation(self, extractor):
        """Test preservation for Szasz claim 3 - CRITICAL."""
        original = "Mental illness can exist only in the same sort of way in which other theoretical concepts exist"
        good_normalized = "Mental illness can only exist in the same way as other theoretical concepts"
        bad_normalized = "Mental illness exists in the same way as other theoretical concepts"

        # Good normalization should preserve
        result_good = extractor.verify_preservation(original, good_normalized)
        assert result_good['preserved'] is True

        # Bad normalization should fail
        result_bad = extractor.verify_preservation(original, bad_normalized)
        assert result_bad['preserved'] is False
        assert 'can' in result_bad['missing']
