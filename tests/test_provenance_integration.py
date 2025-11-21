"""
Integration tests for complete provenance system

Tests end-to-end workflows:
- Document finder → PendingDocument → Document processor → Document + Claims
- Provenance field propagation through the entire chain
- API endpoints returning correct provenance data
- Cross-link verification of complete system
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime
from research_agent.graph_database import GraphDatabase
from research_agent.transcript_manager import TranscriptManager
from research_agent.provenance_verifier import ProvenanceVerifier


class TestProvenanceIntegration:
    """Integration tests for complete provenance system."""

    @pytest.fixture
    def temp_transcript_dir(self):
        """Create temporary directory for transcripts."""
        temp_dir = tempfile.mkdtemp(prefix='test_transcripts_')
        yield temp_dir
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def db(self):
        """Create test database instance."""
        db = GraphDatabase()
        # GraphDatabase is a NetworkX in-memory graph, no connect/close needed
        yield db
        # No cleanup needed - each test gets a fresh instance

    @pytest.fixture
    def transcript_manager(self, temp_transcript_dir):
        """Create transcript manager with temp directory."""
        return TranscriptManager(
            storage_dir=temp_transcript_dir,
            persist_to_disk=True
        )

    @pytest.fixture
    def verifier(self, db, transcript_manager):
        """Create provenance verifier."""
        return ProvenanceVerifier(db, transcript_manager)

    def test_complete_discovery_chain(self, db, transcript_manager, verifier):
        """Test complete discovery → processing chain with full provenance."""

        # Step 1: Create document_finder agent
        finder_agent_id = transcript_manager.start_agent(
            agent_type='document_finder',
            description='Finding documents about AI'
        )
        transcript_manager.log(finder_agent_id, 'info', 'Searching arXiv for AI papers')

        # Step 2: Finder creates PendingDocument
        pending_id = 'pending_ai_paper_001'
        db.create_pending_document(
            doc_id=pending_id,
            filename='ai_paper.pdf',
            file_path='/tmp/ai_paper.pdf',
            source='arxiv',
            created_by='document_finder',
            created_by_agent_id=finder_agent_id,
            metadata={'arxiv_id': '2301.12345'}
        )
        transcript_manager.log(finder_agent_id, 'success', f'Created pending document: {pending_id}')

        # Step 3: Complete finder agent
        transcript_manager.complete_agent(
            agent_id=finder_agent_id,
            result={'documents_found': 1}
        )

        # Step 4: Create document_processor agent
        processor_agent_id = transcript_manager.start_agent(
            agent_type='document_processor',
            description='Processing AI paper'
        )
        transcript_manager.log(processor_agent_id, 'info', f'Processing {pending_id}')

        # Step 5: Processor creates Document (with discovery provenance)
        doc_id = 'doc_ai_paper_001'
        db.create_document(
            doc_id=doc_id,
            title='Advances in AI',
            content='This paper discusses recent advances in artificial intelligence.',
            metadata={'processed_from': pending_id},
            created_by='document_processor',
            created_by_agent_id=processor_agent_id,
            discovered_by='document_finder',
            discovered_by_agent_id=finder_agent_id
        )
        transcript_manager.log(processor_agent_id, 'success', f'Created document: {doc_id}')

        # Step 6: Processor creates Claims from Document
        claim_ids = []
        for i in range(3):
            claim_id = f'claim_ai_{i}'
            db.create_claim(
                claim_id=claim_id,
                text=f'AI claim number {i}',
                document_id=doc_id,
                created_by='document_processor',
                created_by_agent_id=processor_agent_id
            )
            claim_ids.append(claim_id)
            transcript_manager.log(processor_agent_id, 'info', f'Extracted claim: {claim_id}')

        # Step 7: Complete processor agent
        transcript_manager.complete_agent(
            agent_id=processor_agent_id,
            result={'claims_extracted': 3}
        )

        # Verification: Check all provenance links are valid
        results = verifier.verify_all()

        assert results['status'] == 'pass', f"Verification failed: {results['issues']}"
        assert results['stats']['total_nodes_with_provenance'] == 5  # 1 pending + 1 doc + 3 claims
        assert results['stats']['total_agents_with_nodes'] == 2  # finder + processor
        assert results['stats']['total_discovery_chains'] == 1  # The Document
        assert len(results['issues']) == 0

        # Verification: Check Document has complete lineage
        doc = db.get_document(doc_id)
        assert doc['created_by'] == 'document_processor'
        assert doc['created_by_agent_id'] == processor_agent_id
        assert doc['discovered_by'] == 'document_finder'
        assert doc['discovered_by_agent_id'] == finder_agent_id

        # Verification: Check Claims have provenance
        for claim_id in claim_ids:
            claim = db.get_claim(claim_id)
            assert claim['created_by'] == 'document_processor'
            assert claim['created_by_agent_id'] == processor_agent_id

        # Verification: Check PendingDocument has provenance
        pending = db.get_pending_document(pending_id)
        assert pending['created_by'] == 'document_finder'
        assert pending['created_by_agent_id'] == finder_agent_id

        # Verification: Check transcripts exist
        finder_transcript = transcript_manager.get_transcript(finder_agent_id)
        assert finder_transcript is not None
        assert finder_transcript['status'] == 'completed'
        assert len(finder_transcript['activity_log']) >= 2

        processor_transcript = transcript_manager.get_transcript(processor_agent_id)
        assert processor_transcript is not None
        assert processor_transcript['status'] == 'completed'
        assert len(processor_transcript['activity_log']) >= 4

    def test_multiple_documents_from_one_finder(self, db, transcript_manager, verifier):
        """Test one finder creating multiple documents through different processors."""

        # Step 1: One finder finds 3 documents
        finder_agent_id = transcript_manager.start_agent(
            agent_type='document_finder',
            description='Finding multiple documents'
        )

        pending_ids = []
        for i in range(3):
            pending_id = f'pending_doc_{i}'
            db.create_pending_document(
                doc_id=pending_id,
                filename=f'doc_{i}.pdf',
                file_path=f'/tmp/doc_{i}.pdf',
                source='arxiv',
                created_by='document_finder',
                created_by_agent_id=finder_agent_id
            )
            pending_ids.append(pending_id)

        transcript_manager.complete_agent(finder_agent_id, {'documents_found': 3})

        # Step 2: Three separate processors process the documents
        doc_ids = []
        processor_agent_ids = []

        for i, pending_id in enumerate(pending_ids):
            processor_agent_id = transcript_manager.start_agent(
                agent_type='document_processor',
                description=f'Processing document {i}'
            )
            processor_agent_ids.append(processor_agent_id)

            doc_id = f'doc_{i}'
            db.create_document(
                doc_id=doc_id,
                title=f'Document {i}',
                content=f'Content for document {i}',
                created_by='document_processor',
                created_by_agent_id=processor_agent_id,
                discovered_by='document_finder',
                discovered_by_agent_id=finder_agent_id
            )
            doc_ids.append(doc_id)

            transcript_manager.complete_agent(processor_agent_id, {'success': True})

        # Verification: All documents trace back to same finder
        results = verifier.verify_all()
        assert results['status'] == 'pass'
        assert results['stats']['total_discovery_chains'] == 3

        for doc_id in doc_ids:
            doc = db.get_document(doc_id)
            assert doc['discovered_by_agent_id'] == finder_agent_id

        # Verification: Each processor created exactly 1 document
        for processor_agent_id in processor_agent_ids:
            query = """
            MATCH (d:Document)
            WHERE d.created_by_agent_id = $agent_id
            RETURN count(d) as count
            """
            result = db.execute_query(query, {'agent_id': processor_agent_id})
            assert result[0]['count'] == 1

    def test_broken_chain_detection(self, db, transcript_manager, verifier):
        """Test detection of broken provenance chains."""

        # Create document with provenance pointing to non-existent agents
        doc_id = 'broken_doc'
        db.create_document(
            doc_id=doc_id,
            title='Broken Chain Document',
            content='This document has broken provenance',
            created_by='document_processor',
            created_by_agent_id='nonexistent_processor',
            discovered_by='document_finder',
            discovered_by_agent_id='nonexistent_finder'
        )

        # Verification: Should detect both missing agents
        results = verifier.verify_all()

        assert results['status'] == 'fail'
        assert len(results['issues']) >= 2

        issue_types = [issue['type'] for issue in results['issues']]
        assert 'missing_transcript' in issue_types or 'broken_discovery_chain' in issue_types

    def test_orphaned_pending_document(self, db, transcript_manager, verifier):
        """Test detection of orphaned PendingDocument."""

        # Create PendingDocument with non-existent agent
        pending_id = 'orphaned_pending'
        db.create_pending_document(
            doc_id=pending_id,
            filename='orphaned.pdf',
            file_path='/tmp/orphaned.pdf',
            source='manual',
            created_by='document_finder',
            created_by_agent_id='ghost_agent_123'
        )

        # Verification: Should detect orphaned pending doc
        results = verifier.verify_all()

        assert results['status'] == 'fail'
        assert any(issue['type'] == 'orphaned_pending_document' for issue in results['issues'])
        orphan_issue = next(i for i in results['issues'] if i['type'] == 'orphaned_pending_document')
        assert orphan_issue['pending_id'] == pending_id
        assert orphan_issue['agent_id'] == 'ghost_agent_123'

    def test_agent_created_no_nodes_warning(self, db, transcript_manager, verifier):
        """Test warning for agent that completed but created no nodes."""

        # Create and complete processor agent without creating any nodes
        agent_id = transcript_manager.start_agent(
            agent_type='document_processor',
            description='Processor that will fail'
        )
        transcript_manager.log(agent_id, 'error', 'Failed to process document')
        transcript_manager.complete_agent(
            agent_id=agent_id,
            result={'error': 'Processing failed'}
        )

        # Verification: Should warn about no nodes created
        results = verifier.verify_all()

        assert len(results['warnings']) > 0
        assert any(w['type'] == 'agent_created_no_nodes' for w in results['warnings'])

    def test_agent_type_consistency(self, db, transcript_manager, verifier):
        """Test that agent_type in transcript matches created_by field."""

        # Create agent with type 'document_processor'
        agent_id = transcript_manager.start_agent(
            agent_type='document_processor',
            description='Processing document'
        )

        # Create document but use wrong created_by value
        doc_id = 'type_mismatch_doc'
        db.create_document(
            doc_id=doc_id,
            title='Type Mismatch Document',
            content='This has mismatched types',
            created_by='document_finder',  # Wrong! Should be document_processor
            created_by_agent_id=agent_id
        )

        transcript_manager.complete_agent(agent_id, {'success': True})

        # Verification: Should warn about type mismatch
        results = verifier.verify_all()

        assert len(results['warnings']) > 0
        assert any(w['type'] == 'agent_type_mismatch' for w in results['warnings'])

    def test_large_scale_provenance(self, db, transcript_manager, verifier):
        """Test provenance system with many agents and nodes."""

        # Create 10 finder agents
        finder_agents = []
        for i in range(10):
            finder_id = transcript_manager.start_agent(
                agent_type='document_finder',
                description=f'Finder {i}'
            )
            finder_agents.append(finder_id)

            # Each finder creates 2 pending docs
            for j in range(2):
                pending_id = f'pending_{i}_{j}'
                db.create_pending_document(
                    doc_id=pending_id,
                    filename=f'doc_{i}_{j}.pdf',
                    file_path=f'/tmp/doc_{i}_{j}.pdf',
                    source='arxiv',
                    created_by='document_finder',
                    created_by_agent_id=finder_id
                )

            transcript_manager.complete_agent(finder_id, {'documents_found': 2})

        # Create 20 processor agents (one per pending doc)
        processor_agents = []
        doc_count = 0
        for i in range(10):
            for j in range(2):
                processor_id = transcript_manager.start_agent(
                    agent_type='document_processor',
                    description=f'Processor for doc {i}_{j}'
                )
                processor_agents.append(processor_id)

                # Create document
                doc_id = f'doc_{doc_count}'
                db.create_document(
                    doc_id=doc_id,
                    title=f'Document {doc_count}',
                    content=f'Content {doc_count}',
                    created_by='document_processor',
                    created_by_agent_id=processor_id,
                    discovered_by='document_finder',
                    discovered_by_agent_id=finder_agents[i]
                )

                # Create 5 claims per document
                for k in range(5):
                    claim_id = f'claim_{doc_count}_{k}'
                    db.create_claim(
                        claim_id=claim_id,
                        text=f'Claim {k} from document {doc_count}',
                        document_id=doc_id,
                        created_by='document_processor',
                        created_by_agent_id=processor_id
                    )

                transcript_manager.complete_agent(processor_id, {'claims_extracted': 5})
                doc_count += 1

        # Verification: All provenance should be intact
        results = verifier.verify_all()

        assert results['status'] == 'pass', f"Large scale verification failed: {results['issues']}"
        assert results['stats']['total_nodes_with_provenance'] == 20 + 20 + 100  # pending + docs + claims
        assert results['stats']['total_agents_with_nodes'] == 30  # 10 finders + 20 processors
        assert results['stats']['total_discovery_chains'] == 20  # 20 documents
        assert len(results['issues']) == 0

    def test_provenance_with_failed_agents(self, db, transcript_manager, verifier):
        """Test provenance tracking when agents fail."""

        # Create finder that fails
        finder_id = transcript_manager.start_agent(
            agent_type='document_finder',
            description='Finder that will fail'
        )

        # Finder still creates pending doc before failing
        pending_id = 'pending_before_fail'
        db.create_pending_document(
            doc_id=pending_id,
            filename='before_fail.pdf',
            file_path='/tmp/before_fail.pdf',
            source='arxiv',
            created_by='document_finder',
            created_by_agent_id=finder_id
        )

        # Finder fails
        transcript_manager.fail_agent(
            agent_id=finder_id,
            error='Connection timeout'
        )

        # Verification: Provenance should still be valid even though agent failed
        results = verifier.verify_all()

        # No issues - failed agent still has valid transcript
        assert results['status'] == 'pass'

        # Check transcript shows failure
        transcript = transcript_manager.get_transcript(finder_id)
        assert transcript['status'] == 'failed'
        assert transcript['error'] == 'Connection timeout'

    def test_concurrent_agents_same_document(self, db, transcript_manager):
        """Test multiple processors working on same pending document (edge case)."""

        # Create finder and pending doc
        finder_id = transcript_manager.start_agent(
            agent_type='document_finder',
            description='Finding document'
        )

        pending_id = 'contested_pending'
        db.create_pending_document(
            doc_id=pending_id,
            filename='contested.pdf',
            file_path='/tmp/contested.pdf',
            source='arxiv',
            created_by='document_finder',
            created_by_agent_id=finder_id
        )

        transcript_manager.complete_agent(finder_id, {'success': True})

        # Two processors try to process same pending doc
        processor1_id = transcript_manager.start_agent(
            agent_type='document_processor',
            description='Processor 1'
        )

        processor2_id = transcript_manager.start_agent(
            agent_type='document_processor',
            description='Processor 2'
        )

        # Both create documents (simulating race condition)
        doc1_id = 'contested_doc_v1'
        db.create_document(
            doc1_id=doc1_id,
            title='Contested Document v1',
            content='First version',
            created_by='document_processor',
            created_by_agent_id=processor1_id,
            discovered_by='document_finder',
            discovered_by_agent_id=finder_id
        )

        doc2_id = 'contested_doc_v2'
        db.create_document(
            doc2_id=doc2_id,
            title='Contested Document v2',
            content='Second version',
            created_by='document_processor',
            created_by_agent_id=processor2_id,
            discovered_by='document_finder',
            discovered_by_agent_id=finder_id
        )

        transcript_manager.complete_agent(processor1_id, {'success': True})
        transcript_manager.complete_agent(processor2_id, {'success': True})

        # Verification: Both documents should have valid provenance
        # This is an edge case that shows provenance tracks actual creation
        doc1 = db.get_document(doc1_id)
        doc2 = db.get_document(doc2_id)

        assert doc1['created_by_agent_id'] == processor1_id
        assert doc2['created_by_agent_id'] == processor2_id
        assert doc1['discovered_by_agent_id'] == finder_id
        assert doc2['discovered_by_agent_id'] == finder_id

    def test_provenance_report_generation(self, db, transcript_manager, verifier):
        """Test human-readable provenance report generation."""

        # Create a mix of valid and invalid provenance

        # Valid: Complete chain
        finder_id = transcript_manager.start_agent(
            agent_type='document_finder',
            description='Valid finder'
        )
        db.create_pending_document(
            doc_id='valid_pending',
            filename='valid.pdf',
            file_path='/tmp/valid.pdf',
            source='arxiv',
            created_by='document_finder',
            created_by_agent_id=finder_id
        )
        transcript_manager.complete_agent(finder_id, {'success': True})

        # Invalid: Document with missing agent
        db.create_document(
            doc_id='invalid_doc',
            title='Invalid Document',
            content='Has missing agent',
            created_by='document_processor',
            created_by_agent_id='ghost_agent'
        )

        # Orphaned: Pending with missing agent
        db.create_pending_document(
            doc_id='orphaned_pending',
            filename='orphaned.pdf',
            file_path='/tmp/orphaned.pdf',
            source='manual',
            created_by='document_finder',
            created_by_agent_id='another_ghost'
        )

        # Run verification
        results = verifier.verify_all()

        # Generate report
        report = verifier.generate_report(results)

        # Verify report content
        assert 'PROVENANCE VERIFICATION REPORT' in report
        assert 'Overall Status:' in report
        assert 'Statistics:' in report
        assert 'ISSUES FOUND' in report  # Should have issues
        assert 'missing_transcript' in report or 'orphaned' in report

        # Verify report shows failure status
        assert '✗' in report or 'FAIL' in report

        print("\n" + "="*60)
        print("SAMPLE PROVENANCE REPORT:")
        print("="*60)
        print(report)
        print("="*60)
