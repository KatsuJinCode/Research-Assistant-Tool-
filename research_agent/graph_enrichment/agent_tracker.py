"""
Agent Tracking System

Tracks which agents investigated which claims, what they found, and when.
Enables visualization of research progress and agent activity.
"""

import logging
from typing import Dict, List, Any, Optional
from uuid import uuid4
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentTracker:
    """Track agent research activities."""

    def __init__(self):
        """Initialize agent tracker."""
        pass

    def create_research_result(
        self,
        agent_name: str,
        claim_id: str,
        findings: str,
        status: str,
        confidence: Optional[float] = None,
        sources_found: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a research result record.

        Args:
            agent_name: Name of the agent
            claim_id: Claim being investigated
            findings: What the agent found
            status: completed, in_progress, failed, etc.
            confidence: Agent's confidence in findings (0.0-1.0)
            sources_found: List of source URLs/IDs found
            metadata: Additional metadata

        Returns:
            Research result dict
        """
        result = {
            'id': str(uuid4()),
            'agent_name': agent_name,
            'claim_id': claim_id,
            'findings': findings,
            'status': status,
            'confidence': confidence,
            'sources_found': sources_found or [],
            'metadata': metadata or {},
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': datetime.utcnow().isoformat() if status == 'completed' else None
        }

        logger.info(f"Created research result for agent: {agent_name}")
        return result

    def create_agent_node_in_neo4j(
        self,
        agent_name: str,
        agent_type: str,
        capabilities: Optional[List[str]] = None,
        db = None
    ) -> str:
        """
        Create or update Agent node in Neo4j.

        Args:
            agent_name: Agent name
            agent_type: Type of agent (research, validation, synthesis, etc.)
            capabilities: List of agent capabilities
            db: Neo4jDatabase instance

        Returns:
            Agent node ID
        """
        if not db:
            return None

        # Check if agent already exists
        existing = db.find_nodes('Agent', {'name': agent_name})

        if existing:
            logger.info(f"Agent already exists: {agent_name}")
            return existing[0]['id']

        # Create new agent
        agent_id = str(uuid4())
        node_id = db.create_node('Agent', {
            'id': agent_id,
            'name': agent_name,
            'type': agent_type,
            'capabilities': ', '.join(capabilities) if capabilities else '',
            'created_at': datetime.utcnow().isoformat()
        })

        logger.info(f"Created Agent node: {agent_name}")
        return node_id

    def create_research_result_node_in_neo4j(
        self,
        result: Dict[str, Any],
        db
    ) -> str:
        """
        Create ResearchResult node in Neo4j.

        Args:
            result: Research result dict
            db: Neo4jDatabase instance

        Returns:
            ResearchResult node ID
        """
        # Create ResearchResult node
        node_id = db.create_node('ResearchResult', {
            'id': result['id'],
            'agent_name': result['agent_name'],
            'findings': result['findings'],
            'status': result['status'],
            'confidence': result.get('confidence'),
            'sources_found_count': len(result.get('sources_found', [])),
            'started_at': result['started_at'],
            'completed_at': result.get('completed_at')
        })

        # Link to Agent
        agent_nodes = db.find_nodes('Agent', {'name': result['agent_name']})
        if agent_nodes:
            db.create_relationship(
                node_id,
                agent_nodes[0]['id'],
                'PERFORMED_BY'
            )

        # Link to Claim
        db.create_relationship(
            node_id,
            result['claim_id'],
            'INVESTIGATES',
            {
                'status': result['status'],
                'confidence': result.get('confidence')
            }
        )

        logger.info(f"Created ResearchResult node for {result['agent_name']}")
        return node_id

    def link_result_to_evidence(
        self,
        result_id: str,
        evidence_id: str,
        db
    ) -> str:
        """
        Link research result to evidence it found.

        Args:
            result_id: ResearchResult UUID
            evidence_id: Evidence UUID
            db: Neo4jDatabase instance

        Returns:
            Relationship ID
        """
        rel_id = db.create_relationship(
            result_id,
            evidence_id,
            'FOUND_EVIDENCE',
            {'timestamp': datetime.utcnow().isoformat()}
        )

        logger.info("Linked research result to evidence")
        return rel_id

    def get_claim_research_history(
        self,
        claim_id: str,
        db
    ) -> List[Dict[str, Any]]:
        """
        Get research history for a claim.

        Args:
            claim_id: Claim UUID
            db: Neo4jDatabase instance

        Returns:
            List of research results
        """
        query = """
        MATCH (r:ResearchResult)-[:INVESTIGATES]->(c:Claim {id: $claim_id})
        OPTIONAL MATCH (r)-[:PERFORMED_BY]->(a:Agent)
        OPTIONAL MATCH (r)-[:FOUND_EVIDENCE]->(e:Evidence)
        RETURN r, a, collect(e) as evidence
        ORDER BY r.started_at DESC
        """

        with db.driver.session(database=db.database) as session:
            result = session.run(query, claim_id=claim_id)

            history = []
            for record in result:
                result_node = dict(record['r'])
                agent_node = dict(record['a']) if record['a'] else None
                evidence_nodes = [dict(e) for e in record['evidence'] if e]

                history.append({
                    **result_node,
                    'agent': agent_node,
                    'evidence_found': evidence_nodes
                })

            return history

    def get_agent_activity(
        self,
        agent_name: str,
        db,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent activity for an agent.

        Args:
            agent_name: Agent name
            db: Neo4jDatabase instance
            limit: Max results to return

        Returns:
            List of research results
        """
        query = """
        MATCH (r:ResearchResult {agent_name: $agent_name})-[:INVESTIGATES]->(c:Claim)
        RETURN r, c
        ORDER BY r.started_at DESC
        LIMIT $limit
        """

        with db.driver.session(database=db.database) as session:
            result = session.run(query, agent_name=agent_name, limit=limit)

            activity = []
            for record in result:
                result_node = dict(record['r'])
                claim_node = dict(record['c'])

                activity.append({
                    **result_node,
                    'claim': claim_node
                })

            return activity

    def get_research_stats(self, db) -> Dict[str, Any]:
        """
        Get overall research statistics.

        Args:
            db: Neo4jDatabase instance

        Returns:
            Stats dict
        """
        query = """
        MATCH (r:ResearchResult)
        OPTIONAL MATCH (r)-[:PERFORMED_BY]->(a:Agent)
        RETURN
            count(DISTINCT r) as total_research_results,
            count(DISTINCT a) as active_agents,
            count(DISTINCT CASE WHEN r.status = 'completed' THEN r END) as completed,
            count(DISTINCT CASE WHEN r.status = 'in_progress' THEN r END) as in_progress,
            count(DISTINCT CASE WHEN r.status = 'failed' THEN r END) as failed,
            avg(r.confidence) as avg_confidence
        """

        with db.driver.session(database=db.database) as session:
            result = session.run(query)
            record = result.single()

            if record:
                return {
                    'total_research_results': record['total_research_results'],
                    'active_agents': record['active_agents'],
                    'completed': record['completed'],
                    'in_progress': record['in_progress'],
                    'failed': record['failed'],
                    'avg_confidence': record['avg_confidence']
                }

            return {
                'total_research_results': 0,
                'active_agents': 0,
                'completed': 0,
                'in_progress': 0,
                'failed': 0,
                'avg_confidence': None
            }
