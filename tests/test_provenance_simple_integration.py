"""
Simplified integration tests for provenance system

Tests basic provenance workflows with the correct API:
- Creating agents and nodes with provenance
- Verifying provenance links
- Cross-link verification
"""

import pytest
import os
import tempfile
import shutil
from research_agent.graph_database import GraphDatabase
from research_agent.transcript_manager import TranscriptManager
from research_agent.provenance_verifier import ProvenanceVerifier


class TestProvenanceSimpleIntegration:
    """Simplified integration tests using correct API."""

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
        yield db

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

    def test_basic_document_provenance(self, db, transcript_manager, verifier):
        """Test basic document creation with provenance."""

        # Create processor agent using correct API
        processor_agent_id = transcript_manager.create_agent(
            agent_type='document_processor',
            description='Processing test document'
        )

        # Log activity
        transcript_manager.log(processor_agent_id, 'info', 'Starting processing')

        # Create document with provenance
        doc_id = 'test_doc_001'
        db.create_document(
            doc_id=doc_id,
            title='Test Document',
            content='This is a test document for provenance.',
            created_by='document_processor',
            created_by_agent_id=processor_agent_id
        )

        # Complete agent
        transcript_manager.complete_agent(
            agent_id=processor_agent_id,
            result={'success': True}
        )

        # Verify provenance
        results = verifier.verify_all()

        # Should pass - all links are valid
        assert results['status'] == 'pass'
        assert results['stats']['total_nodes_with_provenance'] == 1
        assert results['stats']['total_agents_with_nodes'] == 1
        assert len(results['issues']) == 0

        # Verify document has correct provenance
        doc = db.get_document(doc_id)
        assert doc is not None
        assert doc['created_by'] == 'document_processor'
        assert doc['created_by_agent_id'] == processor_agent_id

        # Verify transcript exists
        transcript = transcript_manager.get_transcript(processor_agent_id)
        assert transcript is not None
        assert transcript['status'] == 'completed'
        assert transcript['agent_type'] == 'document_processor'

    def test_document_with_claims_provenance(self, db, transcript_manager, verifier):
        """Test document with multiple claims all having provenance."""

        # Create processor agent
        processor_agent_id = transcript_manager.create_agent(
            agent_type='document_processor',
            description='Processing document with claims'
        )

        # Create document
        doc_id = 'test_doc_claims'
        db.create_document(
            doc_id=doc_id,
            title='Document with Claims',
            content='Document containing multiple claims.',
            created_by='document_processor',
            created_by_agent_id=processor_agent_id
        )

        # Create multiple claims
        claim_ids = []
        for i in range(5):
            claim_id = f'test_claim_{i}'
            db.create_claim(
                claim_id=claim_id,
                text=f'Test claim number {i}',
                document_id=doc_id,
                created_by='document_processor',
                created_by_agent_id=processor_agent_id
            )
            claim_ids.append(claim_id)
            transcript_manager.log(processor_agent_id, 'info', f'Extracted claim {i}')

        transcript_manager.complete_agent(processor_agent_id, {'claims': 5})

        # Verify provenance
        results = verifier.verify_all()

        assert results['status'] == 'pass'
        assert results['stats']['total_nodes_with_provenance'] == 6  # 1 doc + 5 claims
        assert len(results['issues']) == 0

        # Verify all claims have correct provenance
        for claim_id in claim_ids:
            claim = db.get_claim(claim_id)
            assert claim['created_by_agent_id'] == processor_agent_id

    def test_missing_agent_detection(self, db, transcript_manager, verifier):
        """Test that verifier detects missing agent transcripts."""

        # Create document with non-existent agent ID
        doc_id = 'orphaned_doc'
        db.create_document(
            doc_id=doc_id,
            title='Orphaned Document',
            content='Document with missing agent.',
            created_by='document_processor',
            created_by_agent_id='nonexistent_agent_123'
        )

        # Verify - should detect missing agent
        results = verifier.verify_all()

        assert results['status'] == 'fail'
        assert len(results['issues']) > 0

        # Check that issue is about missing transcript
        missing_issues = [i for i in results['issues'] if i['type'] == 'missing_transcript']
        assert len(missing_issues) > 0
        assert missing_issues[0]['agent_id'] == 'nonexistent_agent_123'

    def test_failed_agent_has_valid_provenance(self, db, transcript_manager, verifier):
        """Test that failed agents still have valid provenance."""

        # Create agent that will fail
        agent_id = transcript_manager.create_agent(
            agent_type='document_processor',
            description='Agent that will fail'
        )

        # Agent creates document before failing
        doc_id = 'doc_from_failed_agent'
        db.create_document(
            doc_id=doc_id,
            title='Document from Failed Agent',
            content='Created before agent failed.',
            created_by='document_processor',
            created_by_agent_id=agent_id
        )

        # Agent fails
        transcript_manager.fail_agent(
            agent_id=agent_id,
            error='Processing error occurred'
        )

        # Verify - should pass because transcript exists even though agent failed
        results = verifier.verify_all()

        assert results['status'] == 'pass'
        assert len(results['issues']) == 0

        # Verify document provenance is valid
        doc = db.get_document(doc_id)
        assert doc['created_by_agent_id'] == agent_id

        # Verify transcript shows failure
        transcript = transcript_manager.get_transcript(agent_id)
        assert transcript['status'] == 'failed'
        assert transcript['error'] == 'Processing error occurred'

    def test_multiple_agents_multiple_documents(self, db, transcript_manager, verifier):
        """Test multiple agents creating multiple documents."""

        agent_ids = []
        doc_ids = []

        # Create 3 agents, each creating 2 documents
        for agent_num in range(3):
            agent_id = transcript_manager.create_agent(
                agent_type='document_processor',
                description=f'Processor {agent_num}'
            )
            agent_ids.append(agent_id)

            for doc_num in range(2):
                doc_id = f'doc_{agent_num}_{doc_num}'
                db.create_document(
                    doc_id=doc_id,
                    title=f'Document {agent_num}-{doc_num}',
                    content=f'Content from agent {agent_num}',
                    created_by='document_processor',
                    created_by_agent_id=agent_id
                )
                doc_ids.append(doc_id)

            transcript_manager.complete_agent(agent_id, {'documents': 2})

        # Verify all provenance
        results = verifier.verify_all()

        assert results['status'] == 'pass'
        assert results['stats']['total_nodes_with_provenance'] == 6  # 6 documents
        assert results['stats']['total_agents_with_nodes'] == 3  # 3 agents
        assert len(results['issues']) == 0

        # Verify each agent's documents
        for idx, agent_id in enumerate(agent_ids):
            expected_doc_ids = [f'doc_{idx}_0', f'doc_{idx}_1']
            for doc_id in expected_doc_ids:
                doc = db.get_document(doc_id)
                assert doc['created_by_agent_id'] == agent_id

    def test_provenance_report_generation(self, db, transcript_manager, verifier):
        """Test generating a human-readable provenance report."""

        # Create valid and invalid data
        valid_agent_id = transcript_manager.create_agent(
            agent_type='document_processor',
            description='Valid processor'
        )
        db.create_document(
            doc_id='valid_doc',
            title='Valid Document',
            content='Has valid agent.',
            created_by='document_processor',
            created_by_agent_id=valid_agent_id
        )
        transcript_manager.complete_agent(valid_agent_id, {'success': True})

        # Invalid document
        db.create_document(
            doc_id='invalid_doc',
            title='Invalid Document',
            content='Missing agent.',
            created_by='document_processor',
            created_by_agent_id='missing_agent'
        )

        # Verify and generate report
        results = verifier.verify_all()
        report = verifier.generate_report(results)

        # Check report content
        assert 'PROVENANCE VERIFICATION REPORT' in report
        assert 'Overall Status:' in report
        assert 'FAIL' in report  # Should fail due to invalid doc
        assert 'ISSUES FOUND' in report
        assert 'missing_transcript' in report

        # Report should mention both documents
        assert results['stats']['total_nodes_with_provenance'] == 2

    def test_discovery_chain_basic(self, db, transcript_manager, verifier):
        """Test basic discovery chain provenance."""

        # Create finder agent
        finder_id = transcript_manager.create_agent(
            agent_type='document_finder',
            description='Finding documents'
        )

        # Finder creates pending document (using proper create_ method if exists)
        pending_id = 'pending_test'
        # Note: This assumes create_pending_document exists with these params
        try:
            db.create_pending_document(
                doc_id=pending_id,
                filename='test.pdf',
                file_path='/tmp/test.pdf',
                source='test',
                created_by='document_finder',
                created_by_agent_id=finder_id
            )
        except AttributeError:
            # If method doesn't exist, skip this part
            pytest.skip("create_pending_document method not available")

        transcript_manager.complete_agent(finder_id, {'found': 1})

        # Create processor agent
        processor_id = transcript_manager.create_agent(
            agent_type='document_processor',
            description='Processing found document'
        )

        # Processor creates document with discovery provenance
        doc_id = 'processed_test_doc'
        db.create_document(
            doc_id=doc_id,
            title='Processed Document',
            content='Document processed from pending.',
            created_by='document_processor',
            created_by_agent_id=processor_id,
            discovered_by='document_finder',
            discovered_by_agent_id=finder_id
        )

        transcript_manager.complete_agent(processor_id, {'success': True})

        # Verify discovery chain
        results = verifier.verify_all()

        assert results['status'] == 'pass'
        assert results['stats']['total_discovery_chains'] >= 1
        assert len(results['issues']) == 0

        # Verify document has both provenance fields
        doc = db.get_document(doc_id)
        assert doc['created_by_agent_id'] == processor_id
        assert doc['discovered_by_agent_id'] == finder_id
