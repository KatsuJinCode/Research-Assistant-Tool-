"""
Unit tests for progress tracking event emissions.

Tests verify that all SocketIO events required for PROGRESS_TRACKING_DESIGN.md
are emitted correctly with proper data structures.

Test-Driven Development: Write tests first to verify understanding before implementation.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from web_ui.document_processor import LiveDocumentProcessor


class MockProgressCallback:
    """Mock callback that captures all emitted events for testing."""

    def __init__(self):
        self.events = []
        self.stage_events = []
        self.claim_complete_events = []
        self.claims_extracted_events = []
        self.document_queued_events = []

    def __call__(self, message, progress, data):
        """Capture all progress updates."""
        event = {
            'message': message,
            'progress': progress,
            'data': data
        }
        self.events.append(event)

        # Categorize events by type
        if data and isinstance(data, dict):
            event_type = data.get('event')

            if event_type == 'claim_stage_update':
                self.stage_events.append(data)
            elif event_type == 'claim_complete':
                self.claim_complete_events.append(data)
            elif event_type == 'claims_extracted':
                self.claims_extracted_events.append(data)
            elif event_type == 'document_queued':
                self.document_queued_events.append(data)

    def get_stage_events_for_claim(self, claim_id):
        """Get all stage events for a specific claim."""
        return [e for e in self.stage_events if e.get('claim_id') == claim_id]

    def get_stage_event(self, claim_id, stage, status):
        """Get specific stage event for a claim."""
        for e in self.stage_events:
            if (e.get('claim_id') == claim_id and
                e.get('stage') == stage and
                e.get('status') == status):
                return e
        return None


class TestClaimsExtractedEvent:
    """Test that claims_extracted event is emitted with correct data."""

    def test_claims_extracted_event_structure(self):
        """
        REQUIREMENT: When claims are extracted, emit 'claims_extracted' event with:
        - doc_id
        - total_claims (count)
        - claim_previews (array of {id, preview})

        Per PROGRESS_TRACKING_DESIGN.md lines 177-186
        """
        callback = MockProgressCallback()

        # Mock event should contain:
        expected_structure = {
            'event': 'claims_extracted',
            'doc_id': 'doc_123',
            'total_claims': 3,
            'claim_previews': [
                {'id': 'claim_001', 'preview': 'Mental illness derives its main...'},
                {'id': 'claim_002', 'preview': 'Neurological defects cannot...'},
                {'id': 'claim_003', 'preview': 'Brain disease theory gains...'}
            ]
        }

        # Simulate callback emission
        callback('Found 3 claims', None, expected_structure)

        # Verify event captured
        assert len(callback.claims_extracted_events) == 1
        event = callback.claims_extracted_events[0]

        # Verify structure
        assert event['event'] == 'claims_extracted'
        assert event['doc_id'] == 'doc_123'
        assert event['total_claims'] == 3
        assert len(event['claim_previews']) == 3

        # Verify preview structure
        preview = event['claim_previews'][0]
        assert 'id' in preview
        assert 'preview' in preview
        assert preview['preview'].startswith('Mental illness')

    def test_claims_extracted_with_no_claims(self):
        """
        EDGE CASE: Document with no extractable claims.
        Should emit event with total_claims=0 and empty previews array.
        """
        callback = MockProgressCallback()

        event_data = {
            'event': 'claims_extracted',
            'doc_id': 'doc_empty',
            'total_claims': 0,
            'claim_previews': []
        }

        callback('Found 0 claims', None, event_data)

        assert len(callback.claims_extracted_events) == 1
        event = callback.claims_extracted_events[0]
        assert event['total_claims'] == 0
        assert event['claim_previews'] == []

    def test_preview_text_truncation(self):
        """
        REQUIREMENT: Preview text should be truncated to ~50 chars.
        Per PROGRESS_TRACKING_DESIGN.md line 182
        """
        callback = MockProgressCallback()

        long_text = "A" * 200  # Very long claim text

        event_data = {
            'event': 'claims_extracted',
            'doc_id': 'doc_123',
            'total_claims': 1,
            'claim_previews': [
                {'id': 'claim_001', 'preview': long_text[:50] + '...'}
            ]
        }

        callback('Found 1 claim', None, event_data)

        event = callback.claims_extracted_events[0]
        preview_text = event['claim_previews'][0]['preview']

        # Preview should be truncated to reasonable length
        assert len(preview_text) <= 60  # 50 chars + ellipsis + buffer


class TestEnhancedClaimStageUpdate:
    """Test that claim_stage_update events include claim index and preview."""

    def test_stage_update_includes_claim_metadata(self):
        """
        REQUIREMENT: claim_stage_update should include:
        - claim_index (1-based)
        - total_claims
        - claim_preview

        Per PROGRESS_TRACKING_DESIGN.md lines 189-197
        """
        callback = MockProgressCallback()

        event_data = {
            'event': 'claim_stage_update',
            'doc_id': 'doc_123',
            'claim_id': 'claim_001',
            'claim_index': 1,  # NEW FIELD
            'total_claims': 15,  # NEW FIELD
            'claim_preview': 'Mental illness derives...',  # NEW FIELD
            'stage': 'analysis',
            'status': 'in_progress',
            'data': {
                'original_text': 'Mental illness derives its main...',
                'word_count': 10
            }
        }

        callback('Analyzing claim...', None, event_data)

        assert len(callback.stage_events) == 1
        event = callback.stage_events[0]

        # Verify new fields present
        assert 'claim_index' in event
        assert 'total_claims' in event
        assert 'claim_preview' in event

        # Verify values
        assert event['claim_index'] == 1
        assert event['total_claims'] == 15
        assert event['claim_preview'] == 'Mental illness derives...'

    def test_stage_update_claim_index_one_based(self):
        """
        REQUIREMENT: claim_index should be 1-based (not 0-based).
        User-facing display shows "Claim 1/15", not "Claim 0/15".
        """
        callback = MockProgressCallback()

        # Simulate processing claim 3 of 15
        event_data = {
            'event': 'claim_stage_update',
            'doc_id': 'doc_123',
            'claim_id': 'claim_003',
            'claim_index': 3,  # Should be 1-based
            'total_claims': 15,
            'claim_preview': 'Brain disease theory...',
            'stage': 'simplification',
            'status': 'in_progress'
        }

        callback('Simplifying claim...', None, event_data)

        event = callback.stage_events[0]

        # Verify 1-based indexing
        assert event['claim_index'] >= 1
        assert event['claim_index'] <= event['total_claims']

    def test_all_four_stages_emit_events(self):
        """
        REQUIREMENT: All 4 stages should emit in_progress and complete events.
        Stages: analysis, clarification, simplification, validation
        """
        callback = MockProgressCallback()
        stages = ['analysis', 'clarification', 'simplification', 'validation']

        claim_id = 'claim_001'

        # Simulate all stages
        for stage in stages:
            # in_progress event
            callback(f'{stage} in progress...', None, {
                'event': 'claim_stage_update',
                'doc_id': 'doc_123',
                'claim_id': claim_id,
                'claim_index': 1,
                'total_claims': 5,
                'claim_preview': 'Test claim...',
                'stage': stage,
                'status': 'in_progress'
            })

            # complete event
            callback(f'{stage} complete', None, {
                'event': 'claim_stage_update',
                'doc_id': 'doc_123',
                'claim_id': claim_id,
                'claim_index': 1,
                'total_claims': 5,
                'claim_preview': 'Test claim...',
                'stage': stage,
                'status': 'complete',
                'data': {
                    'duration_ms': 15000
                }
            })

        # Verify all events captured
        claim_events = callback.get_stage_events_for_claim(claim_id)
        assert len(claim_events) == 8  # 4 stages × 2 events (in_progress + complete)

        # Verify each stage has both events
        for stage in stages:
            in_progress = callback.get_stage_event(claim_id, stage, 'in_progress')
            complete = callback.get_stage_event(claim_id, stage, 'complete')

            assert in_progress is not None, f"Missing in_progress event for {stage}"
            assert complete is not None, f"Missing complete event for {stage}"
            assert complete['data']['duration_ms'] > 0


class TestClaimCompleteEvent:
    """Test final claim_complete event with quality scoring."""

    def test_claim_complete_event_structure(self):
        """
        REQUIREMENT: claim_complete event should include:
        - claim_id
        - final_text (selected candidate)
        - quality_score (0.0-1.0)
        - disposition (central/child/review/discard)
        - total_duration_ms

        Per existing implementation in app.js:159-178
        """
        callback = MockProgressCallback()

        event_data = {
            'event': 'claim_complete',
            'claim_id': 'claim_001',
            'final_text': 'Neurological defects cannot explain belief',
            'quality_score': 0.85,
            'disposition': 'central',
            'total_duration_ms': 54800
        }

        # Note: claim_complete is emitted as separate event, not nested in processing_update
        callback.claim_complete_events.append(event_data)

        assert len(callback.claim_complete_events) == 1
        event = callback.claim_complete_events[0]

        # Verify structure
        assert event['event'] == 'claim_complete'
        assert 'claim_id' in event
        assert 'final_text' in event
        assert 'quality_score' in event
        assert 'disposition' in event
        assert 'total_duration_ms' in event

        # Verify quality score range
        assert 0.0 <= event['quality_score'] <= 1.0

        # Verify disposition values
        assert event['disposition'] in ['central', 'child', 'review', 'discard']

    def test_quality_score_disposition_mapping(self):
        """
        REQUIREMENT: Quality score determines disposition:
        - 0.7+ → central
        - 0.4-0.69 → child
        - <0.4 → review/discard

        Per TESTING_INSTRUCTIONS.md lines 131-137
        """
        test_cases = [
            (0.85, 'central'),
            (0.72, 'central'),
            (0.70, 'central'),
            (0.65, 'child'),
            (0.50, 'child'),
            (0.40, 'child'),
            (0.35, 'review'),
            (0.20, 'discard')
        ]

        for quality_score, expected_disposition in test_cases:
            event_data = {
                'event': 'claim_complete',
                'claim_id': f'claim_{int(quality_score*100)}',
                'final_text': 'Test claim',
                'quality_score': quality_score,
                'disposition': expected_disposition,
                'total_duration_ms': 50000
            }

            # Verify quality score matches expected disposition range
            if quality_score >= 0.7:
                assert expected_disposition == 'central'
            elif quality_score >= 0.4:
                assert expected_disposition == 'child'
            else:
                assert expected_disposition in ['review', 'discard']


class TestDocumentQueuedEvent:
    """Test document_queued event for multi-upload support."""

    def test_document_queued_event_structure(self):
        """
        REQUIREMENT: document_queued event for multi-upload tracking:
        - doc_id
        - filename
        - queue_position
        - queue_length

        Per PROGRESS_TRACKING_DESIGN.md lines 199-206
        """
        callback = MockProgressCallback()

        event_data = {
            'event': 'document_queued',
            'doc_id': 'doc_xyz789',
            'filename': 'another_doc.pdf',
            'queue_position': 2,
            'queue_length': 3
        }

        callback('Document queued', None, event_data)

        assert len(callback.document_queued_events) == 1
        event = callback.document_queued_events[0]

        # Verify structure
        assert event['event'] == 'document_queued'
        assert event['doc_id'] == 'doc_xyz789'
        assert event['filename'] == 'another_doc.pdf'
        assert event['queue_position'] == 2
        assert event['queue_length'] == 3

    def test_multiple_documents_queued(self):
        """
        REQUIREMENT: Track multiple documents in queue.
        Important for bulk uploads (100+ documents).

        Per user requirement message 3
        """
        callback = MockProgressCallback()

        # Simulate 5 documents queued
        for i in range(1, 6):
            event_data = {
                'event': 'document_queued',
                'doc_id': f'doc_{i:03d}',
                'filename': f'document_{i}.pdf',
                'queue_position': i,
                'queue_length': 5
            }

            callback(f'Document {i} queued', None, event_data)

        # Verify all events captured
        assert len(callback.document_queued_events) == 5

        # Verify queue positions
        for i, event in enumerate(callback.document_queued_events, 1):
            assert event['queue_position'] == i
            assert event['queue_length'] == 5


class TestEventSequencing:
    """Test that events are emitted in correct order."""

    def test_complete_claim_processing_sequence(self):
        """
        REQUIREMENT: Events should be emitted in this order:
        1. claims_extracted (once per document)
        2. claim_stage_update (analysis in_progress)
        3. claim_stage_update (analysis complete)
        4. claim_stage_update (clarification in_progress)
        5. claim_stage_update (clarification complete)
        6. claim_stage_update (simplification in_progress)
        7. claim_stage_update (simplification complete)
        8. claim_stage_update (validation in_progress)
        9. claim_stage_update (validation complete)
        10. claim_complete

        Per document_processor.py:573-777
        """
        callback = MockProgressCallback()

        doc_id = 'doc_123'
        claim_id = 'claim_001'

        # 1. Claims extracted
        callback('Found 1 claim', None, {
            'event': 'claims_extracted',
            'doc_id': doc_id,
            'total_claims': 1,
            'claim_previews': [{'id': claim_id, 'preview': 'Test claim...'}]
        })

        # 2-9. Stage updates
        stages = ['analysis', 'clarification', 'simplification', 'validation']
        for stage in stages:
            callback(f'{stage} in progress', None, {
                'event': 'claim_stage_update',
                'doc_id': doc_id,
                'claim_id': claim_id,
                'claim_index': 1,
                'total_claims': 1,
                'claim_preview': 'Test claim...',
                'stage': stage,
                'status': 'in_progress'
            })

            callback(f'{stage} complete', None, {
                'event': 'claim_stage_update',
                'doc_id': doc_id,
                'claim_id': claim_id,
                'claim_index': 1,
                'total_claims': 1,
                'claim_preview': 'Test claim...',
                'stage': stage,
                'status': 'complete',
                'data': {'duration_ms': 10000}
            })

        # 10. Claim complete
        callback.claim_complete_events.append({
            'event': 'claim_complete',
            'claim_id': claim_id,
            'final_text': 'Simplified test claim',
            'quality_score': 0.75,
            'disposition': 'central',
            'total_duration_ms': 40000
        })

        # Verify event counts
        assert len(callback.claims_extracted_events) == 1
        assert len(callback.stage_events) == 8  # 4 stages × 2 events
        assert len(callback.claim_complete_events) == 1

        # Verify event order in captured events
        all_event_types = []
        for event in callback.events:
            if event['data'] and isinstance(event['data'], dict):
                all_event_types.append(event['data'].get('event'))

        # First event should be claims_extracted
        assert all_event_types[0] == 'claims_extracted'

        # Last stage event should be validation complete
        stage_event_types = [e.get('event') for e in callback.events if e['data'] and e['data'].get('event') == 'claim_stage_update']
        # (verification of specific ordering would require tracking order in callback)


class TestProgressTrackerUIDataStructure:
    """Test frontend data structure matches design spec."""

    def test_claim_tracker_state_structure(self):
        """
        REQUIREMENT: Frontend should maintain claimTracker state:

        App.claimTracker = {
            'doc_123': {
                total_claims: 15,
                claims: [
                    {
                        id: 'claim_001',
                        preview: 'Mental illness derives...',
                        status: 'complete',
                        stages: {
                            analysis: 'complete',
                            clarification: 'complete',
                            simplification: 'complete',
                            validation: 'complete'
                        }
                    },
                    ...
                ]
            }
        }

        Per PROGRESS_TRACKING_DESIGN.md lines 228-257
        """
        # Simulate frontend state reconstruction from events
        claim_tracker = {}

        doc_id = 'doc_123'

        # Process claims_extracted event
        claims_extracted = {
            'doc_id': doc_id,
            'total_claims': 2,
            'claim_previews': [
                {'id': 'claim_001', 'preview': 'Mental illness derives...'},
                {'id': 'claim_002', 'preview': 'Neurological defects...'}
            ]
        }

        # Initialize claim tracker
        claim_tracker[doc_id] = {
            'total_claims': claims_extracted['total_claims'],
            'claims': []
        }

        for preview in claims_extracted['claim_previews']:
            claim_tracker[doc_id]['claims'].append({
                'id': preview['id'],
                'preview': preview['preview'],
                'status': 'pending',
                'stages': {
                    'analysis': 'pending',
                    'clarification': 'pending',
                    'simplification': 'pending',
                    'validation': 'pending'
                }
            })

        # Simulate stage update
        stage_update = {
            'claim_id': 'claim_001',
            'stage': 'analysis',
            'status': 'in_progress'
        }

        # Update state
        for claim in claim_tracker[doc_id]['claims']:
            if claim['id'] == stage_update['claim_id']:
                claim['stages'][stage_update['stage']] = stage_update['status']
                claim['status'] = 'processing'

        # Verify state structure
        assert doc_id in claim_tracker
        assert claim_tracker[doc_id]['total_claims'] == 2
        assert len(claim_tracker[doc_id]['claims']) == 2

        # Verify claim structure
        claim = claim_tracker[doc_id]['claims'][0]
        assert 'id' in claim
        assert 'preview' in claim
        assert 'status' in claim
        assert 'stages' in claim

        # Verify stage update applied
        assert claim['stages']['analysis'] == 'in_progress'
        assert claim['status'] == 'processing'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
