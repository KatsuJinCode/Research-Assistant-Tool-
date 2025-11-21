"""
Unit tests for ProvenanceVerifier

Tests the provenance verification system that ensures:
- All node → agent links are valid
- All agent → node links are valid
- Discovery chains are complete
- No orphaned provenance data exists
"""

import pytest
from unittest.mock import Mock, MagicMock
from research_agent.provenance_verifier import ProvenanceVerifier


class TestProvenanceVerifier:
    """Test suite for ProvenanceVerifier class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        return db

    @pytest.fixture
    def mock_transcript_manager(self):
        """Create mock transcript manager."""
        tm = Mock()
        return tm

    @pytest.fixture
    def verifier(self, mock_db, mock_transcript_manager):
        """Create ProvenanceVerifier instance."""
        return ProvenanceVerifier(mock_db, mock_transcript_manager)

    def test_init(self, verifier, mock_db, mock_transcript_manager):
        """Test verifier initialization."""
        assert verifier.db == mock_db
        assert verifier.transcript_manager == mock_transcript_manager

    def test_verify_all_success(self, verifier, mock_db, mock_transcript_manager):
        """Test complete verification with no issues."""
        # Setup mocks
        mock_db.execute_query.return_value = []
        mock_transcript_manager.list_agents.return_value = []

        results = verifier.verify_all()

        assert results['status'] == 'pass'
        assert len(results['issues']) == 0
        assert len(results['warnings']) == 0
        assert 'node_agent_links' in results['checks']
        assert 'agent_nodes_links' in results['checks']
        assert 'discovery_chains' in results['checks']
        assert 'orphaned_data' in results['checks']

    def test_verify_node_agent_links_valid(self, verifier, mock_db, mock_transcript_manager):
        """Test verification of valid node → agent links."""
        # Setup: Node with valid agent
        mock_db.execute_query.return_value = [
            {
                'node_type': 'Document',
                'node_id': 'doc_123',
                'created_by': 'document_processor',
                'agent_id': 'agent_456'
            }
        ]
        mock_transcript_manager.get_transcript.return_value = {
            'agent_id': 'agent_456',
            'agent_type': 'document_processor',
            'status': 'completed'
        }

        result = verifier._verify_node_agent_links()

        assert result['status'] == 'pass'
        assert result['total_nodes'] == 1
        assert len(result['issues']) == 0
        assert len(result['warnings']) == 0
        mock_transcript_manager.get_transcript.assert_called_once_with('agent_456')

    def test_verify_node_agent_links_missing_transcript(self, verifier, mock_db, mock_transcript_manager):
        """Test detection of node with missing agent transcript."""
        # Setup: Node with non-existent agent
        mock_db.execute_query.return_value = [
            {
                'node_type': 'Document',
                'node_id': 'doc_123',
                'created_by': 'document_processor',
                'agent_id': 'missing_agent'
            }
        ]
        mock_transcript_manager.get_transcript.return_value = None

        result = verifier._verify_node_agent_links()

        assert result['status'] == 'fail'
        assert result['total_nodes'] == 1
        assert len(result['issues']) == 1
        assert result['issues'][0]['type'] == 'missing_transcript'
        assert result['issues'][0]['agent_id'] == 'missing_agent'
        assert result['issues'][0]['node_id'] == 'doc_123'

    def test_verify_node_agent_links_type_mismatch(self, verifier, mock_db, mock_transcript_manager):
        """Test detection of agent type mismatch."""
        # Setup: Node says created_by 'document_processor' but agent is 'document_finder'
        mock_db.execute_query.return_value = [
            {
                'node_type': 'Document',
                'node_id': 'doc_123',
                'created_by': 'document_processor',
                'agent_id': 'agent_456'
            }
        ]
        mock_transcript_manager.get_transcript.return_value = {
            'agent_id': 'agent_456',
            'agent_type': 'document_finder',  # Mismatch!
            'status': 'completed'
        }

        result = verifier._verify_node_agent_links()

        assert result['status'] == 'pass'  # Not a failure, just a warning
        assert len(result['warnings']) == 1
        assert result['warnings'][0]['type'] == 'agent_type_mismatch'
        assert result['warnings'][0]['expected'] == 'documentprocessor'
        assert result['warnings'][0]['actual'] == 'documentfinder'

    def test_verify_node_agent_links_error_handling(self, verifier, mock_db):
        """Test error handling in node → agent verification."""
        # Setup: Database error
        mock_db.execute_query.side_effect = Exception("Database connection failed")

        result = verifier._verify_node_agent_links()

        assert result['status'] == 'error'
        assert len(result['issues']) == 1
        assert result['issues'][0]['type'] == 'verification_error'
        assert 'Database connection failed' in result['issues'][0]['message']

    def test_verify_agent_nodes_links_valid(self, verifier, mock_db, mock_transcript_manager):
        """Test verification of valid agent → nodes links."""
        # Setup: Agent with nodes
        mock_transcript_manager.list_agents.return_value = [
            {
                'agent_id': 'agent_123',
                'agent_type': 'document_processor',
                'status': 'completed'
            }
        ]
        mock_db.execute_query.return_value = [{'node_count': 5}]

        result = verifier._verify_agent_nodes_links()

        assert result['status'] == 'pass'
        assert result['total_agents'] == 1
        assert len(result['warnings']) == 0

    def test_verify_agent_nodes_links_no_nodes_created(self, verifier, mock_db, mock_transcript_manager):
        """Test warning for completed agent that created no nodes."""
        # Setup: Completed processor agent with 0 nodes
        mock_transcript_manager.list_agents.return_value = [
            {
                'agent_id': 'agent_123',
                'agent_type': 'document_processor',
                'status': 'completed'
            }
        ]
        mock_db.execute_query.return_value = [{'node_count': 0}]

        result = verifier._verify_agent_nodes_links()

        assert result['status'] == 'pass'
        assert len(result['warnings']) == 1
        assert result['warnings'][0]['type'] == 'agent_created_no_nodes'
        assert result['warnings'][0]['agent_type'] == 'document_processor'

    def test_verify_agent_nodes_links_finder_no_nodes(self, verifier, mock_db, mock_transcript_manager):
        """Test warning for completed finder agent that created no nodes."""
        # Setup: Completed finder agent with 0 nodes
        mock_transcript_manager.list_agents.return_value = [
            {
                'agent_id': 'agent_123',
                'agent_type': 'document_finder',
                'status': 'completed'
            }
        ]
        mock_db.execute_query.return_value = [{'node_count': 0}]

        result = verifier._verify_agent_nodes_links()

        assert result['status'] == 'pass'
        assert len(result['warnings']) == 1
        assert result['warnings'][0]['type'] == 'agent_created_no_nodes'

    def test_verify_agent_nodes_links_error_handling(self, verifier, mock_transcript_manager):
        """Test error handling in agent → nodes verification."""
        # Setup: Error listing agents
        mock_transcript_manager.list_agents.side_effect = Exception("Failed to list agents")

        result = verifier._verify_agent_nodes_links()

        assert result['status'] == 'error'
        assert len(result['issues']) == 1
        assert result['issues'][0]['type'] == 'verification_error'

    def test_verify_discovery_chains_complete(self, verifier, mock_db, mock_transcript_manager):
        """Test verification of complete discovery chains."""
        # Setup: Document with complete discovery chain
        mock_db.execute_query.return_value = [
            {
                'doc_id': 'doc_123',
                'discovered_by': 'document_finder',
                'discoverer_agent_id': 'agent_finder',
                'created_by': 'document_processor',
                'processor_agent_id': 'agent_processor'
            }
        ]
        mock_transcript_manager.get_transcript.side_effect = [
            {'agent_id': 'agent_finder', 'status': 'completed'},  # Discoverer
            {'agent_id': 'agent_processor', 'status': 'completed'}  # Processor
        ]

        result = verifier._verify_discovery_chains()

        assert result['status'] == 'pass'
        assert result['total_chains'] == 1
        assert len(result['issues']) == 0
        assert mock_transcript_manager.get_transcript.call_count == 2

    def test_verify_discovery_chains_missing_discoverer(self, verifier, mock_db, mock_transcript_manager):
        """Test detection of missing discoverer transcript."""
        # Setup: Document with missing discoverer
        mock_db.execute_query.return_value = [
            {
                'doc_id': 'doc_123',
                'discovered_by': 'document_finder',
                'discoverer_agent_id': 'missing_finder',
                'created_by': 'document_processor',
                'processor_agent_id': 'agent_processor'
            }
        ]
        mock_transcript_manager.get_transcript.side_effect = [
            None,  # Missing discoverer
            {'agent_id': 'agent_processor', 'status': 'completed'}  # Valid processor
        ]

        result = verifier._verify_discovery_chains()

        assert result['status'] == 'fail'
        assert len(result['issues']) == 1
        assert result['issues'][0]['type'] == 'broken_discovery_chain'
        assert result['issues'][0]['missing'] == 'discoverer_transcript'
        assert result['issues'][0]['agent_id'] == 'missing_finder'

    def test_verify_discovery_chains_missing_processor(self, verifier, mock_db, mock_transcript_manager):
        """Test detection of missing processor transcript."""
        # Setup: Document with missing processor
        mock_db.execute_query.return_value = [
            {
                'doc_id': 'doc_123',
                'discovered_by': 'document_finder',
                'discoverer_agent_id': 'agent_finder',
                'created_by': 'document_processor',
                'processor_agent_id': 'missing_processor'
            }
        ]
        mock_transcript_manager.get_transcript.side_effect = [
            {'agent_id': 'agent_finder', 'status': 'completed'},  # Valid discoverer
            None  # Missing processor
        ]

        result = verifier._verify_discovery_chains()

        assert result['status'] == 'fail'
        assert len(result['issues']) == 1
        assert result['issues'][0]['type'] == 'broken_processing_chain'
        assert result['issues'][0]['missing'] == 'processor_transcript'
        assert result['issues'][0]['agent_id'] == 'missing_processor'

    def test_verify_discovery_chains_error_handling(self, verifier, mock_db):
        """Test error handling in discovery chain verification."""
        # Setup: Database error
        mock_db.execute_query.side_effect = Exception("Query failed")

        result = verifier._verify_discovery_chains()

        assert result['status'] == 'error'
        assert len(result['issues']) == 1
        assert result['issues'][0]['type'] == 'verification_error'

    def test_check_orphaned_data_clean(self, verifier, mock_db, mock_transcript_manager):
        """Test orphan check with no orphaned data."""
        # Setup: Pending doc with valid agent
        mock_db.execute_query.return_value = [
            {
                'pending_id': 'pending_123',
                'agent_id': 'agent_456',
                'status': 'pending'
            }
        ]
        mock_transcript_manager.get_transcript.return_value = {
            'agent_id': 'agent_456',
            'status': 'completed'
        }

        result = verifier._check_orphaned_data()

        assert result['status'] == 'pass'
        assert len(result['issues']) == 0

    def test_check_orphaned_data_orphaned_pending(self, verifier, mock_db, mock_transcript_manager):
        """Test detection of orphaned PendingDocument."""
        # Setup: Pending doc with missing agent
        mock_db.execute_query.return_value = [
            {
                'pending_id': 'pending_123',
                'agent_id': 'missing_agent',
                'status': 'pending'
            }
        ]
        mock_transcript_manager.get_transcript.return_value = None

        result = verifier._check_orphaned_data()

        assert result['status'] == 'fail'
        assert len(result['issues']) == 1
        assert result['issues'][0]['type'] == 'orphaned_pending_document'
        assert result['issues'][0]['pending_id'] == 'pending_123'
        assert result['issues'][0]['agent_id'] == 'missing_agent'

    def test_check_orphaned_data_error_handling(self, verifier, mock_db):
        """Test error handling in orphan check."""
        # Setup: Database error
        mock_db.execute_query.side_effect = Exception("Database error")

        result = verifier._check_orphaned_data()

        assert result['status'] == 'error'
        assert len(result['issues']) == 1
        assert result['issues'][0]['type'] == 'verification_error'

    def test_generate_report_pass(self, verifier):
        """Test report generation for passing verification."""
        results = {
            'status': 'pass',
            'checks': {
                'node_agent_links': {'status': 'pass'},
                'agent_nodes_links': {'status': 'pass'},
                'discovery_chains': {'status': 'pass'},
                'orphaned_data': {'status': 'pass'}
            },
            'issues': [],
            'warnings': [],
            'stats': {
                'total_nodes_with_provenance': 10,
                'total_agents_with_nodes': 5,
                'total_discovery_chains': 3,
                'total_issues': 0,
                'total_warnings': 0
            }
        }

        report = verifier.generate_report(results)

        assert 'PROVENANCE VERIFICATION REPORT' in report
        assert '✓ PASS' in report
        assert 'total nodes with provenance' in report.lower()  # Spaces, not underscores
        assert '10' in report
        assert 'Node Agent Links: PASS' in report

    def test_generate_report_with_issues(self, verifier):
        """Test report generation with issues."""
        results = {
            'status': 'fail',
            'checks': {
                'node_agent_links': {'status': 'fail'},
                'agent_nodes_links': {'status': 'pass'}
            },
            'issues': [
                {
                    'type': 'missing_transcript',
                    'message': 'Document doc_123 references missing agent',
                    'node_id': 'doc_123',
                    'agent_id': 'missing_agent'
                }
            ],
            'warnings': [
                {
                    'type': 'agent_type_mismatch',
                    'message': 'Agent type mismatch'
                }
            ],
            'stats': {
                'total_issues': 1,
                'total_warnings': 1
            }
        }

        report = verifier.generate_report(results)

        assert 'PROVENANCE VERIFICATION REPORT' in report
        assert '✗ FAIL' in report
        assert 'ISSUES FOUND (1)' in report
        assert 'missing_transcript' in report
        assert 'doc_123' in report
        assert 'WARNINGS (1)' in report
        assert 'agent_type_mismatch' in report

    def test_generate_report_with_warnings_only(self, verifier):
        """Test report generation with warnings but no issues."""
        results = {
            'status': 'pass',
            'checks': {
                'node_agent_links': {'status': 'pass'}
            },
            'issues': [],
            'warnings': [
                {
                    'type': 'agent_created_no_nodes',
                    'message': 'Agent completed but created no nodes'
                }
            ],
            'stats': {
                'total_issues': 0,
                'total_warnings': 1
            }
        }

        report = verifier.generate_report(results)

        assert 'PROVENANCE VERIFICATION REPORT' in report
        assert '✓ PASS' in report
        assert 'WARNINGS (1)' in report
        assert 'agent_created_no_nodes' in report
        assert 'ISSUES FOUND' not in report  # No issues section

    def test_verify_all_aggregates_stats_correctly(self, verifier, mock_db, mock_transcript_manager):
        """Test that verify_all correctly aggregates stats from all checks."""
        # Setup mocks
        mock_db.execute_query.return_value = []
        mock_transcript_manager.list_agents.return_value = []

        results = verifier.verify_all()

        assert 'stats' in results
        assert 'total_nodes_with_provenance' in results['stats']
        assert 'total_agents_with_nodes' in results['stats']
        assert 'total_discovery_chains' in results['stats']
        assert 'total_issues' in results['stats']
        assert 'total_warnings' in results['stats']
        assert results['stats']['total_issues'] == len(results['issues'])
        assert results['stats']['total_warnings'] == len(results['warnings'])

    def test_verify_all_propagates_failures(self, verifier, mock_db, mock_transcript_manager):
        """Test that verify_all status becomes 'fail' if any check fails."""
        # Setup: One check will fail
        mock_db.execute_query.return_value = [
            {
                'node_type': 'Document',
                'node_id': 'doc_123',
                'created_by': 'document_processor',
                'agent_id': 'missing_agent'
            }
        ]
        mock_transcript_manager.get_transcript.return_value = None
        mock_transcript_manager.list_agents.return_value = []

        results = verifier.verify_all()

        assert results['status'] == 'fail'
        assert len(results['issues']) > 0

    def test_verify_multiple_nodes_batch(self, verifier, mock_db, mock_transcript_manager):
        """Test verification with multiple nodes in batch."""
        # Setup: Multiple nodes
        mock_db.execute_query.return_value = [
            {
                'node_type': 'Document',
                'node_id': 'doc_1',
                'created_by': 'document_processor',
                'agent_id': 'agent_1'
            },
            {
                'node_type': 'Claim',
                'node_id': 'claim_1',
                'created_by': 'document_processor',
                'agent_id': 'agent_1'
            },
            {
                'node_type': 'Document',
                'node_id': 'doc_2',
                'created_by': 'document_processor',
                'agent_id': 'agent_2'
            }
        ]
        mock_transcript_manager.get_transcript.side_effect = [
            {'agent_id': 'agent_1', 'agent_type': 'document_processor'},
            {'agent_id': 'agent_1', 'agent_type': 'document_processor'},
            None  # agent_2 missing
        ]

        result = verifier._verify_node_agent_links()

        assert result['total_nodes'] == 3
        assert len(result['issues']) == 1  # Only agent_2 is missing
        assert result['issues'][0]['node_id'] == 'doc_2'
