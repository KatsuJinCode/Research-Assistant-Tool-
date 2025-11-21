"""
Provenance Cross-Link Verifier

Ensures all provenance links are bidirectional and accessible:
- Every node → agent link is valid
- Every agent can access all its created nodes
- Discovery → processing chains are complete
- No orphaned provenance data
"""

import logging
from typing import Dict, List, Any, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class ProvenanceVerifier:
    """Verifies integrity of provenance links across the system."""

    def __init__(self, db, transcript_manager):
        """
        Initialize verifier.

        Args:
            db: Neo4j database instance
            transcript_manager: TranscriptManager instance
        """
        self.db = db
        self.transcript_manager = transcript_manager

    def verify_all(self) -> Dict[str, Any]:
        """
        Run complete provenance verification.

        Returns:
            dict with verification results and any issues found
        """
        results = {
            'status': 'pass',
            'checks': {},
            'issues': [],
            'warnings': [],
            'stats': {}
        }

        logger.info("[ProvenanceVerifier] Starting comprehensive verification...")

        # Check 1: Node → Agent Links
        node_agent_check = self._verify_node_agent_links()
        results['checks']['node_agent_links'] = node_agent_check
        if node_agent_check['issues']:
            results['status'] = 'fail'
            results['issues'].extend(node_agent_check['issues'])
        if node_agent_check['warnings']:
            results['warnings'].extend(node_agent_check['warnings'])

        # Check 2: Agent → Nodes Links
        agent_nodes_check = self._verify_agent_nodes_links()
        results['checks']['agent_nodes_links'] = agent_nodes_check
        if agent_nodes_check['issues']:
            results['status'] = 'fail'
            results['issues'].extend(agent_nodes_check['issues'])
        if agent_nodes_check['warnings']:
            results['warnings'].extend(agent_nodes_check['warnings'])

        # Check 3: Discovery → Processing Chains
        chain_check = self._verify_discovery_chains()
        results['checks']['discovery_chains'] = chain_check
        if chain_check['issues']:
            results['status'] = 'fail'
            results['issues'].extend(chain_check['issues'])
        if chain_check['warnings']:
            results['warnings'].extend(chain_check['warnings'])

        # Check 4: Orphaned Provenance Data
        orphan_check = self._check_orphaned_data()
        results['checks']['orphaned_data'] = orphan_check
        if orphan_check['issues']:
            results['status'] = 'fail'
            results['issues'].extend(orphan_check['issues'])

        # Collect stats
        results['stats'] = {
            'total_nodes_with_provenance': node_agent_check.get('total_nodes', 0),
            'total_agents_with_nodes': agent_nodes_check.get('total_agents', 0),
            'total_discovery_chains': chain_check.get('total_chains', 0),
            'total_issues': len(results['issues']),
            'total_warnings': len(results['warnings'])
        }

        logger.info(f"[ProvenanceVerifier] Verification complete: {results['status'].upper()}")
        logger.info(f"[ProvenanceVerifier] Issues: {results['stats']['total_issues']}, Warnings: {results['stats']['total_warnings']}")

        return results

    def _verify_node_agent_links(self) -> Dict[str, Any]:
        """Verify that all nodes with agent IDs have valid transcripts."""
        result = {
            'status': 'pass',
            'issues': [],
            'warnings': [],
            'total_nodes': 0
        }

        # Query all nodes with created_by_agent_id
        query = """
        MATCH (n)
        WHERE n.created_by_agent_id IS NOT NULL
        RETURN
            labels(n)[0] as node_type,
            n.id as node_id,
            n.created_by as created_by,
            n.created_by_agent_id as agent_id
        """

        try:
            nodes = self.db.execute_query(query)
            result['total_nodes'] = len(nodes)

            # Check each node's agent link
            for node in nodes:
                agent_id = node['agent_id']
                node_id = node['node_id']
                node_type = node['node_type']

                # Check if transcript exists
                transcript = self.transcript_manager.get_transcript(agent_id)

                if not transcript:
                    result['issues'].append({
                        'type': 'missing_transcript',
                        'node_id': node_id,
                        'node_type': node_type,
                        'agent_id': agent_id,
                        'message': f"{node_type} {node_id} references missing agent {agent_id}"
                    })
                    result['status'] = 'fail'
                else:
                    # Verify agent is the correct type
                    expected_type = node.get('created_by', '').replace('_', '')
                    actual_type = transcript.get('agent_type', '').replace('_', '')

                    if expected_type and actual_type and expected_type not in actual_type:
                        result['warnings'].append({
                            'type': 'agent_type_mismatch',
                            'node_id': node_id,
                            'node_type': node_type,
                            'expected': expected_type,
                            'actual': actual_type,
                            'message': f"{node_type} {node_id} created_by mismatch"
                        })

        except Exception as e:
            logger.error(f"Error verifying node→agent links: {e}")
            result['status'] = 'error'
            result['issues'].append({
                'type': 'verification_error',
                'message': str(e)
            })

        return result

    def _verify_agent_nodes_links(self) -> Dict[str, Any]:
        """Verify that all agents can access their created nodes."""
        result = {
            'status': 'pass',
            'issues': [],
            'warnings': [],
            'total_agents': 0
        }

        try:
            # Get all agents from transcript manager
            agents = self.transcript_manager.list_agents()
            result['total_agents'] = len(agents)

            for agent_summary in agents:
                agent_id = agent_summary['agent_id']

                # Query nodes created by this agent
                query = """
                MATCH (n)
                WHERE n.created_by_agent_id = $agent_id
                RETURN count(n) as node_count
                """

                nodes_result = self.db.execute_query(query, {'agent_id': agent_id})
                node_count = nodes_result[0]['node_count'] if nodes_result else 0

                # If agent has completed but created no nodes, that might be suspicious
                if agent_summary['status'] == 'completed' and node_count == 0:
                    # Check if it's a node-creating agent type
                    agent_type = agent_summary['agent_type']
                    if agent_type in ['document_processor', 'document_finder']:
                        result['warnings'].append({
                            'type': 'agent_created_no_nodes',
                            'agent_id': agent_id,
                            'agent_type': agent_type,
                            'message': f"Agent {agent_id} completed but created no nodes"
                        })

        except Exception as e:
            logger.error(f"Error verifying agent→nodes links: {e}")
            result['status'] = 'error'
            result['issues'].append({
                'type': 'verification_error',
                'message': str(e)
            })

        return result

    def _verify_discovery_chains(self) -> Dict[str, Any]:
        """Verify discovery → processing chains are complete."""
        result = {
            'status': 'pass',
            'issues': [],
            'warnings': [],
            'total_chains': 0
        }

        try:
            # Query documents with discovery provenance
            query = """
            MATCH (d:Document)
            WHERE d.discovered_by IS NOT NULL
            RETURN
                d.id as doc_id,
                d.discovered_by as discovered_by,
                d.discovered_by_agent_id as discoverer_agent_id,
                d.created_by as created_by,
                d.created_by_agent_id as processor_agent_id
            """

            docs = self.db.execute_query(query)
            result['total_chains'] = len(docs)

            for doc in docs:
                doc_id = doc['doc_id']

                # Check discoverer transcript exists
                if doc['discoverer_agent_id']:
                    discoverer_transcript = self.transcript_manager.get_transcript(doc['discoverer_agent_id'])
                    if not discoverer_transcript:
                        result['issues'].append({
                            'type': 'broken_discovery_chain',
                            'doc_id': doc_id,
                            'missing': 'discoverer_transcript',
                            'agent_id': doc['discoverer_agent_id'],
                            'message': f"Document {doc_id} references missing discoverer agent"
                        })
                        result['status'] = 'fail'

                # Check processor transcript exists
                if doc['processor_agent_id']:
                    processor_transcript = self.transcript_manager.get_transcript(doc['processor_agent_id'])
                    if not processor_transcript:
                        result['issues'].append({
                            'type': 'broken_processing_chain',
                            'doc_id': doc_id,
                            'missing': 'processor_transcript',
                            'agent_id': doc['processor_agent_id'],
                            'message': f"Document {doc_id} references missing processor agent"
                        })
                        result['status'] = 'fail'

        except Exception as e:
            logger.error(f"Error verifying discovery chains: {e}")
            result['status'] = 'error'
            result['issues'].append({
                'type': 'verification_error',
                'message': str(e)
            })

        return result

    def _check_orphaned_data(self) -> Dict[str, Any]:
        """Check for orphaned provenance data."""
        result = {
            'status': 'pass',
            'issues': []
        }

        try:
            # Find PendingDocuments that reference non-existent agents
            query = """
            MATCH (p:PendingDocument)
            WHERE p.created_by_agent_id IS NOT NULL
            RETURN
                p.id as pending_id,
                p.created_by_agent_id as agent_id,
                p.status as status
            """

            pending = self.db.execute_query(query)

            for doc in pending:
                agent_id = doc['agent_id']
                if agent_id:
                    transcript = self.transcript_manager.get_transcript(agent_id)
                    if not transcript:
                        result['issues'].append({
                            'type': 'orphaned_pending_document',
                            'pending_id': doc['pending_id'],
                            'agent_id': agent_id,
                            'status': doc['status'],
                            'message': f"PendingDocument {doc['pending_id']} references missing agent"
                        })
                        result['status'] = 'fail'

        except Exception as e:
            logger.error(f"Error checking orphaned data: {e}")
            result['status'] = 'error'
            result['issues'].append({
                'type': 'verification_error',
                'message': str(e)
            })

        return result

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable verification report."""
        lines = []
        lines.append("=" * 60)
        lines.append("PROVENANCE VERIFICATION REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Status
        status_symbol = "✓" if results['status'] == 'pass' else "✗"
        lines.append(f"Overall Status: {status_symbol} {results['status'].upper()}")
        lines.append("")

        # Stats
        lines.append("Statistics:")
        for key, value in results['stats'].items():
            lines.append(f"  • {key.replace('_', ' ').title()}: {value}")
        lines.append("")

        # Issues
        if results['issues']:
            lines.append(f"ISSUES FOUND ({len(results['issues'])}):")
            lines.append("-" * 60)
            for issue in results['issues']:
                lines.append(f"  ✗ [{issue['type']}] {issue['message']}")
                for key, value in issue.items():
                    if key not in ['type', 'message']:
                        lines.append(f"      {key}: {value}")
            lines.append("")

        # Warnings
        if results['warnings']:
            lines.append(f"WARNINGS ({len(results['warnings'])}):")
            lines.append("-" * 60)
            for warning in results['warnings']:
                lines.append(f"  ⚠ [{warning['type']}] {warning['message']}")
            lines.append("")

        # Per-check results
        lines.append("DETAILED RESULTS:")
        lines.append("-" * 60)
        for check_name, check_result in results['checks'].items():
            status = check_result.get('status', 'unknown')
            symbol = "✓" if status == 'pass' else "✗" if status == 'fail' else "?"
            lines.append(f"  {symbol} {check_name.replace('_', ' ').title()}: {status.upper()}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)
