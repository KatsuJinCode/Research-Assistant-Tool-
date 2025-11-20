"""
Test semantic duplicate detection across documents
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from web_ui.semantic_clustering import SemanticDuplicateDetector, EMBEDDINGS_AVAILABLE, SKLEARN_AVAILABLE


@pytest.mark.skipif(not (EMBEDDINGS_AVAILABLE and SKLEARN_AVAILABLE),
                    reason="Sentence transformers or sklearn not available")
class TestSemanticDuplicateDetection:
    """Test duplicate claim detection"""

    def test_detector_initialization(self):
        """Test that detector initializes correctly"""
        detector = SemanticDuplicateDetector(similarity_threshold=0.85)
        assert detector.similarity_threshold == 0.85
        assert detector.model is not None

    def test_exact_duplicate_detection(self):
        """Test detection of exact duplicates"""
        detector = SemanticDuplicateDetector(similarity_threshold=0.85)

        new_claims = [
            {
                'id': 'claim-1',
                'text': 'Climate change is caused by greenhouse gas emissions',
                'summary': 'Climate change is caused by greenhouse gas emissions'
            }
        ]

        existing_claims = [
            {
                'id': 'claim-2',
                'text': 'Climate change is caused by greenhouse gas emissions',
                'summary': 'Climate change is caused by greenhouse gas emissions',
                'doc_id': 'doc-previous'
            }
        ]

        duplicates = detector.find_duplicates(new_claims, existing_claims)

        assert len(duplicates) == 1
        assert duplicates[0]['new_claim_id'] == 'claim-1'
        assert duplicates[0]['existing_claim_id'] == 'claim-2'
        assert duplicates[0]['similarity_score'] > 0.95
        assert duplicates[0]['match_quality'] == 'exact'

    def test_paraphrased_duplicate_detection(self):
        """Test detection of paraphrased duplicates"""
        # Use lower threshold to catch paraphrases
        detector = SemanticDuplicateDetector(similarity_threshold=0.75)

        new_claims = [
            {
                'id': 'claim-1',
                'text': 'Global warming is driven by the emission of greenhouse gases',
                'summary': 'Global warming is driven by the emission of greenhouse gases'
            }
        ]

        existing_claims = [
            {
                'id': 'claim-2',
                'text': 'Climate change is caused by greenhouse gas emissions',
                'summary': 'Climate change is caused by greenhouse gas emissions',
                'doc_id': 'doc-previous'
            }
        ]

        duplicates = detector.find_duplicates(new_claims, existing_claims)

        # Should detect as duplicate with lower threshold (high semantic similarity)
        assert len(duplicates) >= 1
        if len(duplicates) > 0:
            assert duplicates[0]['similarity_score'] >= 0.75
            # Verify it detected the correct pairing
            assert duplicates[0]['new_claim_id'] == 'claim-1'
            assert duplicates[0]['existing_claim_id'] == 'claim-2'

    def test_no_duplicate_detection(self):
        """Test that different claims are not marked as duplicates"""
        detector = SemanticDuplicateDetector(similarity_threshold=0.85)

        new_claims = [
            {
                'id': 'claim-1',
                'text': 'Machine learning improves medical diagnosis accuracy',
                'summary': 'Machine learning improves medical diagnosis accuracy'
            }
        ]

        existing_claims = [
            {
                'id': 'claim-2',
                'text': 'Climate change is caused by greenhouse gas emissions',
                'summary': 'Climate change is caused by greenhouse gas emissions',
                'doc_id': 'doc-previous'
            }
        ]

        duplicates = detector.find_duplicates(new_claims, existing_claims)

        assert len(duplicates) == 0

    def test_empty_input_handling(self):
        """Test handling of empty inputs"""
        detector = SemanticDuplicateDetector(similarity_threshold=0.85)

        # No new claims
        duplicates = detector.find_duplicates([], [{'id': 'claim-1', 'text': 'test', 'summary': 'test'}])
        assert len(duplicates) == 0

        # No existing claims
        duplicates = detector.find_duplicates([{'id': 'claim-1', 'text': 'test', 'summary': 'test'}], [])
        assert len(duplicates) == 0

        # Both empty
        duplicates = detector.find_duplicates([], [])
        assert len(duplicates) == 0

    def test_within_set_duplicate_detection(self):
        """Test detection of duplicates within a single set"""
        detector = SemanticDuplicateDetector(similarity_threshold=0.85)

        claims = [
            {
                'id': 'claim-1',
                'text': 'Climate change is caused by greenhouse gases',
                'summary': 'Climate change is caused by greenhouse gases'
            },
            {
                'id': 'claim-2',
                'text': 'Machine learning improves diagnosis',
                'summary': 'Machine learning improves diagnosis'
            },
            {
                'id': 'claim-3',
                'text': 'Climate change is caused by greenhouse gas emissions',
                'summary': 'Climate change is caused by greenhouse gas emissions'
            }
        ]

        duplicates = detector.detect_duplicates_in_set(claims)

        # Should find duplicate between claim-1 and claim-3
        assert len(duplicates) >= 1
        # Verify it's a tuple of (index_i, index_j, similarity)
        assert len(duplicates[0]) == 3
        # Indices should be claim-1 (0) and claim-3 (2)
        assert duplicates[0][0] == 0
        assert duplicates[0][1] == 2
        assert duplicates[0][2] >= 0.85


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
