"""
Research Graph Web Interface

A proper web UI for navigating the research graph.
Shows top-level claims, click to expand, spawn agents, view confidence.
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from pathlib import Path
import sys
import threading
from werkzeug.utils import secure_filename
import os
import logging
import traceback
import hashlib
import subprocess
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from research_agent.neo4j_database import Neo4jDatabase
from research_agent.graph_enrichment import (
    EvidenceManager,
    AgentTracker,
    CitationNetwork
)
from web_ui.document_processor import LiveDocumentProcessor

# Repository pattern for database access
from backend.database.repositories import ClaimRepository, DocumentRepository
from backend.database.event_emitter import RepositoryEventEmitter
from backend.database.neo4j_client import Neo4jClient

app = Flask(__name__)
app.config['SECRET_KEY'] = 'research-assistant-secret-key'
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=False, engineio_logger=False)
db = Neo4jDatabase()  # Keep for backward compatibility during migration

# Document processing queue - FIFO queue to prevent interruption
import queue
import threading

processing_queue = queue.Queue()
processing_lock = threading.Lock()
is_processing = False
current_processing_filename = None  # Track currently processing file

# Register WebSocket event emitter callback for real-time updates
# CRITICAL: Wrap socketio.emit with app context for background thread safety
def emit_with_context(event, data):
    """Wrapper to ensure app context when emitting from repositories."""
    with app.app_context():
        socketio.emit(event, data)

RepositoryEventEmitter.set_emit_callback(emit_with_context)

# Initialize repositories
claim_repo = ClaimRepository()
doc_repo = DocumentRepository()

# Get Neo4j client and database manager for multi-database support
neo4j_client = Neo4jClient()
try:
    db_manager = neo4j_client.database_manager
    logger.info(f"DatabaseManager initialized. Active database: {neo4j_client.active_database}")
except Exception as e:
    logger.warning(f"DatabaseManager not available: {e}")
    db_manager = None


def process_queue_worker():
    """Background worker that processes documents from queue one at a time."""
    global is_processing, current_processing_filename

    while True:
        try:
            # Block until an item is available
            queue_item = processing_queue.get(block=True)

            if queue_item is None:  # Poison pill to stop worker
                break

            # Unpack queue item (backwards compatible: handles both old and new formats)
            if len(queue_item) == 2:
                filepath, filename = queue_item
                discovered_by, discovered_by_agent_id = None, None
            elif len(queue_item) == 4:
                filepath, filename, discovered_by, discovered_by_agent_id = queue_item
            else:
                logger.error(f"[QUEUE] Invalid queue item format: {queue_item}")
                continue

            with processing_lock:
                is_processing = True
                current_processing_filename = filename

            logger.info(f"[QUEUE] Starting processing: {filename}")

            # Create agent transcript for provenance tracking
            from research_agent.transcript_manager import get_transcript_manager
            transcript_manager = get_transcript_manager()
            agent_id = transcript_manager.create_agent(
                'document_processor',
                f'Processing document: {filename}'
            )
            transcript_manager.log(agent_id, 'info', f'Started processing: {filename}')
            if discovered_by:
                transcript_manager.log(agent_id, 'info', f'Document discovered by: {discovered_by}', {
                    'discovered_by': discovered_by,
                    'discovered_by_agent_id': discovered_by_agent_id
                })

            # Emit queue status
            with app.app_context():
                socketio.emit('queue_update', {
                    'processing': filename,
                    'queue_size': processing_queue.qsize()
                })

            try:
                def progress_callback(message, progress, data):
                    if progress is not None:
                        logger.info(f"[PROGRESS {progress:.0f}%] {message}")
                    else:
                        logger.info(f"{message}")
                    # Log to transcript
                    level = 'error' if 'error' in message.lower() or '❌' in message else \
                           'warning' if 'warning' in message.lower() or '⚠️' in message else \
                           'success' if '✓' in message or '✅' in message else 'info'
                    transcript_manager.log(agent_id, level, message, data)

                    socketio.sleep(0)
                    with app.app_context():
                        socketio.emit('processing_update', {
                            'message': message,
                            'progress': progress,
                            'data': data
                        })

                processor = LiveDocumentProcessor(
                    progress_callback=progress_callback,
                    agent_id=agent_id,
                    discovered_by=discovered_by,
                    discovered_by_agent_id=discovered_by_agent_id
                )
                doc_id = processor.process_document(filepath)

                logger.info(f"[QUEUE] Completed: {filename} -> {doc_id}")
                transcript_manager.complete_agent(agent_id, {'document_id': doc_id, 'filename': filename})

                with app.app_context():
                    socketio.emit('document_processed', {'document_id': doc_id, 'agent_id': agent_id})

            except Exception as e:
                error_msg = f"Error processing {filename}: {str(e)}"
                logger.error(f"[QUEUE] {error_msg}")
                logger.error(traceback.format_exc())
                transcript_manager.fail_agent(agent_id, error_msg)

                with app.app_context():
                    socketio.emit('processing_error', {'error': str(e), 'filename': filename, 'agent_id': agent_id})

            finally:
                processing_queue.task_done()

                # Check if queue is empty
                with processing_lock:
                    if processing_queue.empty():
                        is_processing = False
                        current_processing_filename = None

                # Emit updated queue status
                with app.app_context():
                    socketio.emit('queue_update', {
                        'processing': None,
                        'queue_size': processing_queue.qsize()
                    })

        except Exception as e:
            logger.error(f"[QUEUE WORKER] Fatal error: {e}")
            logger.error(traceback.format_exc())


# Start queue worker thread on app startup
queue_worker_thread = threading.Thread(target=process_queue_worker, daemon=True)
queue_worker_thread.start()
logger.info("[QUEUE] Worker thread started")


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/workflows')
def workflows_page():
    """Workflows management page."""
    return render_template('workflows.html')


@app.route('/api/root-claims')
def get_root_claims():
    """Get top-level (root) claims."""
    claims = claim_repo.find_root_claims()
    return jsonify(claims)


@app.route('/api/claim/<claim_id>')
def get_claim_details(claim_id):
    """Get full details for a specific claim using repository."""
    # Use repository method instead of raw Cypher query
    claim = claim_repo.get_claim_with_relationships(claim_id)

    if not claim:
        return jsonify({'error': 'Claim not found'}), 404

    return jsonify(claim)


@app.route('/api/claim/<claim_id>/override-confidence', methods=['POST'])
def override_claim_confidence(claim_id):
    """Allow user to manually override the AI-calculated confidence score."""
    data = request.json
    user_confidence = data.get('confidence')

    if user_confidence is None or not (0 <= user_confidence <= 1):
        return jsonify({'error': 'confidence must be between 0 and 1'}), 400

    # Get the claim
    claim = claim_repo.get_claim(claim_id)
    if not claim:
        return jsonify({'error': 'Claim not found'}), 404

    # Store the user override in Neo4j
    try:
        query = """
        MATCH (c:Claim {id: $claim_id})
        SET c.user_confidence_override = $user_confidence
        SET c.override_timestamp = datetime()
        RETURN c.confidence as ai_confidence, c.user_confidence_override as user_override
        """
        result = db.execute_query(query, {
            'claim_id': claim_id,
            'user_confidence': user_confidence
        })

        if result:
            return jsonify({
                'status': 'success',
                'ai_confidence': result[0]['ai_confidence'],
                'user_override': result[0]['user_override']
            })
        else:
            return jsonify({'error': 'Failed to update claim'}), 500

    except Exception as e:
        logger.error(f"Error setting confidence override: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/claim/<claim_id>/reset-confidence', methods=['POST'])
def reset_claim_confidence(claim_id):
    """Reset claim confidence to AI-calculated value (remove user override)."""
    # Get the claim
    claim = claim_repo.get_claim(claim_id)
    if not claim:
        return jsonify({'error': 'Claim not found'}), 404

    # Remove the user override from Neo4j
    try:
        query = """
        MATCH (c:Claim {id: $claim_id})
        REMOVE c.user_confidence_override
        REMOVE c.override_timestamp
        RETURN c.confidence as ai_confidence
        """
        result = db.execute_query(query, {
            'claim_id': claim_id
        })

        if result:
            return jsonify({
                'status': 'success',
                'ai_confidence': result[0]['ai_confidence']
            })
        else:
            return jsonify({'error': 'Failed to reset claim'}), 500

    except Exception as e:
        logger.error(f"Error resetting confidence override: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/claim/<claim_id>/evidence/<evidence_id>', methods=['DELETE'])
def remove_evidence(claim_id, evidence_id):
    """Remove an evidence link from a claim and recalculate confidence."""
    # Get the claim
    claim = claim_repo.get_claim(claim_id)
    if not claim:
        return jsonify({'error': 'Claim not found'}), 404

    try:
        # Delete the evidence relationship
        query = """
        MATCH (c:Claim {id: $claim_id})-[r:SUPPORTED_BY|CONTRADICTED_BY]->(e:Evidence {id: $evidence_id})
        DELETE r
        RETURN c.confidence as new_confidence
        """
        result = db.execute_query(query, {
            'claim_id': claim_id,
            'evidence_id': evidence_id
        })

        if not result:
            # Relationship might not exist
            return jsonify({'error': 'Evidence relationship not found'}), 404

        new_confidence = result[0]['new_confidence']

        # Emit real-time update via WebSocket
        with app.app_context():
            socketio.emit('evidence_removed', {
                'claim_id': claim_id,
                'evidence_id': evidence_id,
                'new_confidence': new_confidence
            })

        return jsonify({
            'status': 'success',
            'new_confidence': new_confidence,
            'message': 'Evidence removed successfully'
        })

    except Exception as e:
        logger.error(f"Error removing evidence: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/investigate-claim', methods=['POST'])
def investigate_claim():
    """Spawn an agent to investigate a claim."""
    data = request.json
    claim_id = data.get('claim_id')
    investigation_type = data.get('type', 'support')  # 'support' or 'contradict'

    if not claim_id:
        return jsonify({'error': 'claim_id required'}), 400

    # Get claim using repository
    claim = claim_repo.get_claim(claim_id)
    if not claim:
        return jsonify({'error': 'Claim not found'}), 404
    claim_text = claim['text']

    # Create agent and research result
    agent_tracker = AgentTracker()

    agent_name = f"InvestigationAgent-{investigation_type.capitalize()}"
    agent_tracker.create_agent_node_in_neo4j(
        agent_name=agent_name,
        agent_type="investigation",
        capabilities=["evidence_search", "claim_validation"],
        db=db
    )

    research_result = agent_tracker.create_research_result(
        agent_name=agent_name,
        claim_id=claim_id,
        findings=f"Investigating claim to {investigation_type}...",
        status="in_progress",
        confidence=None
    )

    result_id = agent_tracker.create_research_result_node_in_neo4j(research_result, db)

    return jsonify({
        'status': 'started',
        'research_id': result_id,
        'agent': agent_name,
        'claim': claim_text,
        'type': investigation_type
    })


@app.route('/api/agent-status')
def get_agent_status():
    """
    Get status of all active background agents.

    Returns current state of:
    - Document processing queue
    - Active document processor
    - Investigation agents (if any)
    """
    try:
        # Check document processing status
        with processing_lock:
            is_proc = is_processing

        queue_size = processing_queue.qsize()

        agents = []

        # Document processor agent
        if is_proc:
            agents.append({
                'id': 'document_processor',
                'name': 'Document Processor',
                'type': 'document',
                'status': 'processing',
                'task': 'Processing document...',
                'start_time': None  # Would need to track this globally
            })

        # Queue status
        if queue_size > 0:
            agents.append({
                'id': 'document_queue',
                'name': 'Processing Queue',
                'type': 'queue',
                'status': 'idle',
                'task': f'{queue_size} document(s) waiting',
                'queue_size': queue_size
            })

        # Future: Add investigation agents from orchestrator

        return jsonify({
            'active_agents': len(agents),
            'agents': agents,
            'is_processing': is_proc,
            'queue_size': queue_size
        })

    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/graph-stats')
def get_graph_stats():
    """Get overall graph statistics for the active project database."""
    try:
        # Use DatabaseManager to get stats from the active database
        active_db = neo4j_client.active_database
        stats = db_manager.get_database_stats(active_db)

        # Get research stats
        agent_tracker = AgentTracker()
        research_stats = agent_tracker.get_research_stats(db)

        # Get agent counts by status from transcript manager
        from research_agent.transcript_manager import get_transcript_manager
        transcript_manager = get_transcript_manager()
        all_transcripts = transcript_manager.list_all_transcripts()

        agents_active = sum(1 for t in all_transcripts if t.get('status') in ['active', 'running', 'processing'])
        agents_completed = sum(1 for t in all_transcripts if t.get('status') in ['completed', 'success', 'done'])
        agents_failed = sum(1 for t in all_transcripts if t.get('status') in ['failed', 'error'])

        # Get document counts by status
        doc_status_query = """
        MATCH (d:Document)
        RETURN d.status as status, count(*) as count
        """
        doc_status_result = db.execute_query(doc_status_query)

        documents_pending = 0
        documents_processing = 0
        documents_completed = 0

        for record in doc_status_result:
            status = record.get('status', 'unknown')
            count = record.get('count', 0)
            if status == 'pending':
                documents_pending = count
            elif status == 'processing':
                documents_processing = count
            elif status == 'completed':
                documents_completed = count

        # Get claims without evidence (orphaned claims)
        orphaned_claims_query = """
        MATCH (c:Claim)
        WHERE NOT (c)-[:HAS_EVIDENCE]->()
        RETURN count(c) as orphaned_count
        """
        orphaned_result = db.execute_query(orphaned_claims_query)
        claims_without_evidence = orphaned_result[0].get('orphaned_count', 0) if orphaned_result else 0

        return jsonify({
            'nodes': stats.get('total_nodes', 0),
            'relationships': stats.get('total_relationships', 0),
            'node_types': stats.get('label_counts', {}),

            # Document stats
            'document_count': stats.get('document_count', 0),
            'total_documents': stats.get('document_count', 0),
            'documents_pending': documents_pending,
            'documents_processing': documents_processing,
            'documents_completed': documents_completed,

            # Claim and evidence stats
            'claim_count': stats.get('claim_count', 0),
            'total_claims': stats.get('claim_count', 0),
            'evidence_count': stats.get('evidence_count', 0),
            'total_evidence': stats.get('evidence_count', 0),
            'claims_without_evidence': claims_without_evidence,

            # Agent stats
            'agents_active': agents_active,
            'agents_completed': agents_completed,
            'agents_failed': agents_failed,
            'total_agents': len(all_transcripts),

            'research': research_stats,
            'active_database': active_db
        })
    except Exception as e:
        logger.error(f"Error getting graph stats: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'nodes': 0,
            'relationships': 0,
            'node_types': {},
            'document_count': 0,
            'total_documents': 0,
            'documents_pending': 0,
            'documents_processing': 0,
            'documents_completed': 0,
            'claim_count': 0,
            'total_claims': 0,
            'evidence_count': 0,
            'total_evidence': 0,
            'agents_active': 0,
            'agents_completed': 0,
            'agents_failed': 0,
            'total_agents': 0,
            'research': {},
            'error': str(e)
        })


# ============================================================================
# SEMANTIC SIMILARITY ENDPOINTS - Stage 1 Auto-Linking
# ============================================================================

@app.route('/api/claim/<claim_id>/similar-evidence')
def find_similar_evidence(claim_id):
    """
    Find evidence nodes semantically similar to a claim.

    Query params:
        threshold: Minimum similarity score (default: 0.7)
        limit: Max number of results (default: 10)
    """
    try:
        from research_agent.semantic_similarity import get_embedding_manager

        threshold = float(request.args.get('threshold', 0.7))
        limit = int(request.args.get('limit', 10))

        embedding_manager = get_embedding_manager(db)
        similar_evidence = embedding_manager.find_similar_evidence_for_claim(
            claim_id=claim_id,
            threshold=threshold,
            limit=limit
        )

        return jsonify({
            'claim_id': claim_id,
            'threshold': threshold,
            'count': len(similar_evidence),
            'evidence': similar_evidence
        })

    except Exception as e:
        logger.error(f"Error finding similar evidence: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/embeddings/generate-all', methods=['POST'])
def generate_all_embeddings():
    """
    Generate embeddings for all claims and evidence nodes that don't have them yet.
    This is a batch operation that may take time.
    """
    try:
        from research_agent.semantic_similarity import get_embedding_manager

        embedding_manager = get_embedding_manager(db)

        # Get all claims without embeddings
        claims_query = """
        MATCH (c:Claim)
        WHERE c.embedding IS NULL
        RETURN c.id as id, c.text as text
        """
        claims = db.execute_query(claims_query)

        # Get all evidence without embeddings
        evidence_query = """
        MATCH (e:Evidence)
        WHERE e.embedding IS NULL
        RETURN e.id as id, e.text as text
        """
        evidence = db.execute_query(evidence_query)

        # Generate embeddings
        claims_processed = 0
        claims_failed = 0

        for claim in claims:
            success = embedding_manager.store_claim_embedding(claim['id'], claim['text'])
            if success:
                claims_processed += 1
            else:
                claims_failed += 1

        evidence_processed = 0
        evidence_failed = 0

        for ev in evidence:
            success = embedding_manager.store_evidence_embedding(ev['id'], ev['text'])
            if success:
                evidence_processed += 1
            else:
                evidence_failed += 1

        return jsonify({
            'success': True,
            'claims': {
                'total': len(claims),
                'processed': claims_processed,
                'failed': claims_failed
            },
            'evidence': {
                'total': len(evidence),
                'processed': evidence_processed,
                'failed': evidence_failed
            }
        })

    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/auto-link-evidence', methods=['POST'])
def auto_link_evidence():
    """
    Automatically link evidence to claims based on semantic similarity.
    Creates SUPPORTED_BY relationships with similarity metadata.

    Request body:
        threshold: Minimum similarity score (default: 0.7)
        auto_approve: If true, create links automatically. If false, create pending approvals.
    """
    try:
        from research_agent.semantic_similarity import get_embedding_manager, get_similarity_engine

        data = request.json or {}
        threshold = float(data.get('threshold', 0.7))
        auto_approve = data.get('auto_approve', False)

        # Get all claims and evidence
        claims_query = """
        MATCH (c:Claim)
        WHERE c.embedding IS NOT NULL
        RETURN c.id as id, c.text as text, c.embedding as embedding
        """
        claims = db.execute_query(claims_query)

        evidence_query = """
        MATCH (e:Evidence)
        WHERE e.embedding IS NOT NULL
        RETURN e.id as id, e.text as text, e.embedding as embedding
        """
        evidence = db.execute_query(evidence_query)

        if not claims or not evidence:
            return jsonify({
                'success': False,
                'error': 'No claims or evidence with embeddings found',
                'claims_count': len(claims) if claims else 0,
                'evidence_count': len(evidence) if evidence else 0
            })

        # Find similar pairs
        engine = get_similarity_engine()
        links_created = 0
        links_pending = 0

        for claim in claims:
            claim_id = claim['id']
            claim_embedding = engine.list_to_embedding(claim['embedding'])

            for ev in evidence:
                ev_id = ev['id']
                ev_embedding = engine.list_to_embedding(ev['embedding'])

                similarity = engine.calculate_similarity(claim_embedding, ev_embedding)

                if similarity >= threshold:
                    # Create relationship
                    if auto_approve:
                        link_query = """
                        MATCH (c:Claim {id: $claim_id})
                        MATCH (e:Evidence {id: $evidence_id})
                        MERGE (c)-[r:SUPPORTED_BY {
                            auto_linked: true,
                            semantic_similarity: $similarity,
                            link_strength: $similarity,
                            created_at: datetime()
                        }]->(e)
                        RETURN r
                        """
                        result = db.execute_query(link_query, {
                            'claim_id': claim_id,
                            'evidence_id': ev_id,
                            'similarity': similarity
                        })

                        if result:
                            links_created += 1
                    else:
                        # Create pending link for review
                        pending_query = """
                        CREATE (p:PendingLink {
                            id: $link_id,
                            claim_id: $claim_id,
                            evidence_id: $evidence_id,
                            similarity: $similarity,
                            status: 'pending_review',
                            created_at: datetime()
                        })
                        RETURN p.id as id
                        """
                        result = db.execute_query(pending_query, {
                            'link_id': f'link_{hashlib.sha256(f"{claim_id}_{ev_id}".encode()).hexdigest()[:16]}',
                            'claim_id': claim_id,
                            'evidence_id': ev_id,
                            'similarity': similarity
                        })

                        if result:
                            links_pending += 1

        # Emit update
        with app.app_context():
            socketio.emit('graph_updated', {'reason': 'auto_linking'})

        return jsonify({
            'success': True,
            'threshold': threshold,
            'auto_approve': auto_approve,
            'links_created': links_created,
            'links_pending': links_pending,
            'claims_processed': len(claims),
            'evidence_processed': len(evidence)
        })

    except Exception as e:
        logger.error(f"Error auto-linking evidence: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# ============================================================================
# RAG CONFIGURATION ENDPOINTS
# ============================================================================

@app.route('/api/rag/config', methods=['GET'])
def get_rag_config():
    """
    Get current RAG configuration including similarity thresholds.
    """
    try:
        from backend.rag import get_rag_config

        config = get_rag_config()
        thresholds = config.thresholds

        return jsonify({
            'thresholds': {
                'identical': thresholds.identical_threshold,
                'similar': thresholds.similar_threshold,
                'related': thresholds.related_threshold,
                'min_confidence': thresholds.min_confidence_for_linking
            }
        })

    except Exception as e:
        logger.error(f"Error getting RAG config: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/rag/config', methods=['PUT'])
def update_rag_config():
    """
    Update RAG configuration thresholds.

    Request body:
        {
            "identical": 0.95,  // Optional
            "similar": 0.75,    // Optional
            "related": 0.60,    // Optional
            "min_confidence": 0.70  // Optional
        }
    """
    try:
        from backend.rag import get_rag_config

        data = request.get_json()
        config = get_rag_config()

        success = config.update_thresholds(
            identical=data.get('identical'),
            similar=data.get('similar'),
            related=data.get('related'),
            min_confidence=data.get('min_confidence')
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'RAG configuration updated',
                'thresholds': {
                    'identical': config.thresholds.identical_threshold,
                    'similar': config.thresholds.similar_threshold,
                    'related': config.thresholds.related_threshold,
                    'min_confidence': config.thresholds.min_confidence_for_linking
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid threshold values'
            }), 400

    except Exception as e:
        logger.error(f"Error updating RAG config: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/rag/config/reset', methods=['POST'])
def reset_rag_config():
    """
    Reset RAG configuration to default values.
    """
    try:
        from backend.rag import get_rag_config

        config = get_rag_config()
        config.reset_to_defaults()

        return jsonify({
            'success': True,
            'message': 'RAG configuration reset to defaults',
            'thresholds': {
                'identical': config.thresholds.identical_threshold,
                'similar': config.thresholds.similar_threshold,
                'related': config.thresholds.related_threshold,
                'min_confidence': config.thresholds.min_confidence_for_linking
            }
        })

    except Exception as e:
        logger.error(f"Error resetting RAG config: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/claims/<claim_id>/similar', methods=['GET'])
def get_similar_claims(claim_id):
    """
    Get claims with SIMILAR_TO relationships for UI highlighting.

    Returns all claims that have SIMILAR_TO relationships with the specified claim.
    """
    try:
        from backend.rag import ClaimDeduplicator

        deduplicator = ClaimDeduplicator()
        similar_claims = deduplicator.get_similar_claims_for_ui(claim_id)

        return jsonify({
            'claim_id': claim_id,
            'count': len(similar_claims),
            'similar_claims': similar_claims
        })

    except Exception as e:
        logger.error(f"Error getting similar claims: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# AGENT TRANSCRIPT ENDPOINTS
@app.route('/api/agents', methods=['GET'])
def list_agents():
    """
    List all background agents with optional filtering.

    Query parameters:
        agent_type: Filter by type (document_finder, document_processor, etc.)
        status: Filter by status (running, completed, failed)
    """
    try:
        from research_agent.transcript_manager import get_transcript_manager

        transcript_manager = get_transcript_manager()

        agent_type = request.args.get('agent_type')
        status = request.args.get('status')

        agents = transcript_manager.list_agents(agent_type=agent_type, status=status)

        return jsonify({
            'agents': agents,
            'total': len(agents)
        })

    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/<agent_id>/transcript', methods=['GET'])
def get_agent_transcript(agent_id):
    """
    Get the full transcript for a specific agent.

    Path parameters:
        agent_id: The agent identifier
    """
    try:
        from research_agent.transcript_manager import get_transcript_manager

        transcript_manager = get_transcript_manager()
        transcript = transcript_manager.get_transcript(agent_id)

        if transcript is None:
            return jsonify({'error': 'Agent not found'}), 404

        return jsonify(transcript)

    except Exception as e:
        logger.error(f"Error retrieving transcript: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/<agent_id>/created-nodes', methods=['GET'])
def get_agent_created_nodes(agent_id):
    """
    Get all nodes created by a specific agent.

    Returns Documents, Claims, and any other nodes with created_by_agent_id matching agent_id.

    Path parameters:
        agent_id: The agent identifier
    """
    try:
        # Query all node types that might have been created by this agent
        query = """
        // Find all Documents created by this agent
        OPTIONAL MATCH (d:Document)
        WHERE d.created_by_agent_id = $agent_id
        WITH collect({
            type: 'Document',
            id: d.id,
            title: d.title,
            status: d.status,
            created_at: d.created_at,
            created_by: d.created_by
        }) as documents

        // Find all Claims created by this agent
        OPTIONAL MATCH (c:Claim)
        WHERE c.created_by_agent_id = $agent_id
        WITH documents, collect({
            type: 'Claim',
            id: c.id,
            text: c.text,
            status: c.status,
            created_at: c.created_at,
            created_by: c.created_by
        }) as claims

        // Find all PendingDocuments created by this agent
        OPTIONAL MATCH (p:PendingDocument)
        WHERE p.created_by_agent_id = $agent_id
        WITH documents, claims, collect({
            type: 'PendingDocument',
            id: p.id,
            filename: p.filename,
            status: p.status,
            created_at: p.created_at,
            created_by: p.created_by
        }) as pending_documents

        RETURN documents, claims, pending_documents
        """

        result = db.execute_query(query, {'agent_id': agent_id})

        if not result:
            # No results means agent exists but hasn't created any nodes yet
            return jsonify({
                'agent_id': agent_id,
                'documents': [],
                'claims': [],
                'pending_documents': [],
                'total_nodes': 0
            })

        record = result[0]
        documents = [d for d in record['documents'] if d.get('id')]
        claims = [c for c in record['claims'] if c.get('id')]
        pending_documents = [p for p in record['pending_documents'] if p.get('id')]

        return jsonify({
            'agent_id': agent_id,
            'documents': documents,
            'claims': claims,
            'pending_documents': pending_documents,
            'total_nodes': len(documents) + len(claims) + len(pending_documents),
            'counts': {
                'documents': len(documents),
                'claims': len(claims),
                'pending_documents': len(pending_documents)
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving agent created nodes: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/<agent_id>', methods=['GET'])
def get_agent_full_info(agent_id):
    """
    Get comprehensive information about an agent including:
    - Full transcript
    - Created nodes
    - Provenance (who/what created it)
    - Timestamps
    - Action log
    """
    try:
        from research_agent.transcript_manager import get_transcript_manager

        transcript_manager = get_transcript_manager()

        # Get transcript and basic info
        transcript = transcript_manager.get_transcript(agent_id)
        if transcript is None:
            return jsonify({'error': 'Agent not found'}), 404

        # Get created nodes
        nodes_query = """
        OPTIONAL MATCH (d:Document)
        WHERE d.created_by_agent_id = $agent_id
        WITH collect({
            type: 'Document',
            id: d.id,
            title: d.title,
            status: d.status,
            created_at: d.created_at
        }) as documents

        OPTIONAL MATCH (c:Claim)
        WHERE c.created_by_agent_id = $agent_id
        WITH documents, collect({
            type: 'Claim',
            id: c.id,
            text: c.text,
            status: c.status,
            created_at: c.created_at
        }) as claims

        RETURN documents, claims
        """

        nodes_result = db.execute_query(nodes_query, {'agent_id': agent_id})

        spawned_nodes = []
        if nodes_result:
            record = nodes_result[0]
            spawned_nodes.extend([d for d in record.get('documents', []) if d.get('id')])
            spawned_nodes.extend([c for c in record.get('claims', []) if c.get('id')])

        # Combine all information
        agent_info = {
            'id': agent_id,
            'name': transcript.get('agent_name', transcript.get('agent_type', 'Agent')),
            'type': transcript.get('agent_type'),
            'status': transcript.get('status'),
            'created_at': transcript.get('created_at'),
            'completed_at': transcript.get('completed_at'),
            'created_by': transcript.get('created_by'),
            'created_by_agent_id': transcript.get('created_by_agent_id'),
            'transcript': transcript.get('transcript', transcript.get('full_transcript', '')),
            'action_log': transcript.get('action_log', []),
            'spawned_nodes': spawned_nodes,
            'total_spawned': len(spawned_nodes)
        }

        return jsonify(agent_info)

    except Exception as e:
        logger.error(f"Error retrieving agent info: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/nodes/<node_id>/provenance', methods=['GET'])
def get_node_provenance(node_id):
    """
    Get complete provenance information for any node.

    Returns:
        - Node's own provenance (created_by, created_by_agent_id)
        - Discovery provenance (discovered_by, discovered_by_agent_id) if present
        - Agent transcripts (if available)
        - Full lineage chain

    Path parameters:
        node_id: The node identifier
    """
    try:
        # Query the node - search across all node types
        query = """
        // Try to find the node as any type
        OPTIONAL MATCH (n:Document {id: $node_id})
        WITH n, 'Document' as node_type
        WHERE n IS NOT NULL

        WITH n, node_type
        RETURN
            node_type,
            n.id as id,
            n.title as title,
            n.text as text,
            n.filename as filename,
            n.created_by as created_by,
            n.created_by_agent_id as created_by_agent_id,
            n.discovered_by as discovered_by,
            n.discovered_by_agent_id as discovered_by_agent_id,
            n.created_at as created_at,
            n.status as status

        UNION

        OPTIONAL MATCH (n:Claim {id: $node_id})
        WITH n, 'Claim' as node_type
        WHERE n IS NOT NULL
        RETURN
            node_type,
            n.id as id,
            null as title,
            n.text as text,
            null as filename,
            n.created_by as created_by,
            n.created_by_agent_id as created_by_agent_id,
            null as discovered_by,
            null as discovered_by_agent_id,
            n.created_at as created_at,
            n.status as status

        UNION

        OPTIONAL MATCH (n:PendingDocument {id: $node_id})
        WITH n, 'PendingDocument' as node_type
        WHERE n IS NOT NULL
        RETURN
            node_type,
            n.id as id,
            n.title as title,
            null as text,
            n.filename as filename,
            n.created_by as created_by,
            n.created_by_agent_id as created_by_agent_id,
            null as discovered_by,
            null as discovered_by_agent_id,
            n.created_at as created_at,
            n.status as status
        """

        results = db.execute_query(query, {'node_id': node_id})

        if not results:
            return jsonify({'error': 'Node not found'}), 404

        node_data = results[0]

        # Build provenance response
        provenance = {
            'node': {
                'id': node_data['id'],
                'type': node_data['node_type'],
                'title': node_data.get('title'),
                'text': node_data.get('text'),
                'filename': node_data.get('filename'),
                'status': node_data.get('status'),
                'created_at': node_data.get('created_at')
            },
            'created_by': {
                'actor': node_data.get('created_by'),
                'agent_id': node_data.get('created_by_agent_id'),
                'agent_transcript_available': False
            },
            'discovered_by': None,
            'lineage_chain': []
        }

        # Check if creator agent transcript is available
        if node_data.get('created_by_agent_id'):
            from research_agent.transcript_manager import get_transcript_manager
            transcript_manager = get_transcript_manager()
            transcript = transcript_manager.get_transcript(node_data['created_by_agent_id'])
            if transcript:
                provenance['created_by']['agent_transcript_available'] = True
                provenance['created_by']['agent_description'] = transcript.get('description')
                provenance['created_by']['agent_status'] = transcript.get('status')

        # Add discovery provenance if present
        if node_data.get('discovered_by'):
            provenance['discovered_by'] = {
                'actor': node_data['discovered_by'],
                'agent_id': node_data.get('discovered_by_agent_id'),
                'agent_transcript_available': False
            }

            if node_data.get('discovered_by_agent_id'):
                from research_agent.transcript_manager import get_transcript_manager
                transcript_manager = get_transcript_manager()
                transcript = transcript_manager.get_transcript(node_data['discovered_by_agent_id'])
                if transcript:
                    provenance['discovered_by']['agent_transcript_available'] = True
                    provenance['discovered_by']['agent_description'] = transcript.get('description')
                    provenance['discovered_by']['agent_status'] = transcript.get('status')

        # Build lineage chain (from discovery → processing → node)
        if provenance['discovered_by']:
            provenance['lineage_chain'].append({
                'step': 1,
                'action': 'discovered',
                'actor': provenance['discovered_by']['actor'],
                'agent_id': provenance['discovered_by']['agent_id']
            })

        provenance['lineage_chain'].append({
            'step': len(provenance['lineage_chain']) + 1,
            'action': 'created',
            'actor': provenance['created_by']['actor'],
            'agent_id': provenance['created_by']['agent_id']
        })

        return jsonify(provenance)

    except Exception as e:
        logger.error(f"Error retrieving node provenance: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/full-graph')
def get_full_graph():
    """Get complete hierarchical graph with arbitrary depth support, including agents."""

    try:
        # Fetch all data using repositories
        documents = doc_repo.get_all_documents_simple()
        claims = claim_repo.get_all_claims_with_children()
        doc_claims = doc_repo.get_all_document_claim_relationships()
        evidence_data = claim_repo.get_all_claim_evidence_relationships()
        semantic_links = claim_repo.get_all_semantic_relationships()
        similar_to_links = claim_repo.get_all_similar_to_relationships()  # RAG-detected similar claims

        # Fetch agent data from transcripts
        from research_agent.transcript_manager import get_transcript_manager
        transcript_manager = get_transcript_manager()
        all_transcripts = transcript_manager.list_all_transcripts()

        # Build agent info map
        agents_map = {}
        for transcript in all_transcripts:
            agent_id = transcript.get('agent_id')
            if agent_id:
                agents_map[agent_id] = {
                    'id': agent_id,
                    'type': transcript.get('agent_type', 'unknown'),
                    'status': transcript.get('status', 'unknown'),
                    'goal': transcript.get('goal', ''),
                    'created_at': transcript.get('created_at', ''),
                    'completed_at': transcript.get('completed_at', ''),
                    'created_node_ids': []  # Will populate this below
                }

        # Build sources map (URLs, files, etc.)
        sources_map = {}
        for doc in documents:
            # Extract source information from document
            source_url = doc.get('source_url') or doc.get('source_file')
            source_type = doc.get('source_type', 'file')

            if source_url:
                # Use URL/file path as source ID
                source_id = source_url
                if source_id not in sources_map:
                    # Determine source display type
                    if source_url.startswith('http'):
                        display_type = 'URL'
                        display_label = source_url.split('/')[-1] or source_url  # Get last part of URL
                    elif source_url.startswith('arxiv'):
                        display_type = 'ArXiv'
                        display_label = source_url
                    else:
                        display_type = 'File'
                        display_label = source_url.split('\\')[-1].split('/')[-1]  # Get filename

                    sources_map[source_id] = {
                        'id': source_id,
                        'url': source_url,
                        'type': display_type,
                        'label': display_label,
                        'sourced_doc_ids': []
                    }

                # Track which documents came from this source
                sources_map[source_id]['sourced_doc_ids'].append(doc['id'])

        # Build document-claim mapping
        doc_claim_map = {dc['doc_id']: dc['claim_ids'] for dc in doc_claims}

        # Build evidence mapping
        evidence_map = {ev['claim_id']: ev['evidence_list'] for ev in evidence_data}

        # Structure response
        response = []
        for doc in documents:
            doc_id = doc['id']

            # Track which agent created this document
            doc_created_by = doc.get('created_by_agent_id')
            if doc_created_by and doc_created_by in agents_map:
                agents_map[doc_created_by]['created_node_ids'].append(doc_id)

            # Get claims for this document
            doc_claim_ids = doc_claim_map.get(doc_id, [])

            # Separate super-claims and regular claims
            super_claims = []
            all_claims = []

            for claim in claims:
                if claim['id'] in doc_claim_ids:
                    # Track which agent created this claim
                    claim_created_by = claim.get('created_by_agent_id')
                    if claim_created_by and claim_created_by in agents_map:
                        agents_map[claim_created_by]['created_node_ids'].append(claim['id'])

                    claim_data = {
                        'id': claim['id'],
                        'text': claim['text'],
                        'summary': claim.get('summary'),
                        'status': claim.get('status', 'complete'),
                        'disposition': claim.get('disposition', 'child'),
                        'is_super_claim': claim['is_super_claim'],
                        'quality_score': claim.get('quality_score'),
                        'claim_type': claim.get('claim_type', 'extracted'),
                        'confidence': claim.get('confidence', 0.0),
                        'child_ids': [cid for cid in claim['child_ids'] if cid],  # Filter None
                        'created_by_agent_id': claim_created_by
                    }

                    if claim['is_super_claim']:
                        super_claims.append(claim_data)
                    all_claims.append(claim_data)

            # Get source for this document
            doc_source_url = doc.get('source_url') or doc.get('source_file')
            source_id = doc_source_url if doc_source_url else None

            response.append({
                'doc_id': doc_id,
                'doc_title': doc['title'],
                'doc_status': doc['status'],
                'created_by_agent_id': doc_created_by,
                'source_id': source_id,  # NEW - link to source node
                'super_claims': super_claims,
                'all_claims': all_claims,  # New: all claims regardless of depth
                'evidence': evidence_map,
                'semantic_links': semantic_links,  # Cross-document semantic relationships
                'similar_to_links': similar_to_links  # RAG-detected similar claims
            })

        # Add agents data to response (only agents that created nodes)
        active_agents = [agent for agent in agents_map.values() if len(agent['created_node_ids']) > 0]

        # Add sources data to response
        active_sources = list(sources_map.values())

        return jsonify({
            'documents': response,
            'agents': active_agents,
            'sources': active_sources  # NEW - data source nodes
        })

    except Exception as e:
        logger.error(f"Error in get_full_graph: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'documents': [], 'agents': [], 'sources': []}), 500


@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    """
    Handle file upload and start processing.

    User-uploaded files are auto-approved.
    Agent-uploaded files require approval.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Check if file type is supported
    allowed_extensions = {'.pdf', '.txt', '.docx'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        return jsonify({'error': f'Unsupported file type. Allowed: {", ".join(allowed_extensions)}'}), 400

    # Save file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Check if uploaded by agent or user
    source = request.form.get('source', 'user')  # 'user' or 'agent'

    if source == 'user':
        # User uploads are auto-approved - add directly to processing queue
        # No discovered_by since user manually uploaded (not agent-discovered)
        processing_queue.put((filepath, filename, None, None))
        queue_position = processing_queue.qsize()

        logger.info(f"[QUEUE] User upload added to queue: {filename} (position: {queue_position})")

        # Emit queue update
        with app.app_context():
            socketio.emit('queue_update', {
                'processing': current_processing_filename,
                'queue_size': queue_position
            })

        return jsonify({
            'status': 'queued',
            'filename': filename,
            'queue_position': queue_position,
            'auto_approved': True
        })
    else:
        # Agent uploads need approval - add to approval queue
        approval_id = f"approval_{hashlib.sha256(filename.encode()).hexdigest()[:12]}"

        # Store in Neo4j as pending document
        query = """
        CREATE (d:PendingDocument {
            id: $approval_id,
            filename: $filename,
            filepath: $filepath,
            source: $source,
            status: 'pending_approval',
            created_at: datetime()
        })
        RETURN d.id as id
        """
        result = db.execute_query(query, {
            'approval_id': approval_id,
            'filename': filename,
            'filepath': filepath,
            'source': source
        })

        logger.info(f"[APPROVAL QUEUE] Agent upload pending approval: {filename}")

        # Emit approval needed event
        with app.app_context():
            socketio.emit('approval_needed', {
                'approval_id': approval_id,
                'filename': filename,
                'source': source
            })

        return jsonify({
            'status': 'pending_approval',
            'approval_id': approval_id,
            'filename': filename,
            'auto_approved': False
        })


@app.route('/api/upload-url', methods=['POST'])
def upload_url():
    """
    Handle URL upload for processing.
    Downloads content from URL and adds to processing queue.
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400

    url = data['url'].strip()
    if not url:
        return jsonify({'error': 'URL cannot be empty'}), 400

    # TODO: Implement URL downloading and processing
    # For now, return success message indicating feature is coming
    logger.info(f"[URL UPLOAD] URL submitted: {url}")

    return jsonify({
        'status': 'not_implemented',
        'message': 'URL upload feature is not yet implemented',
        'url': url
    }), 501


@app.route('/api/pending-documents')
def get_pending_documents():
    """Get list of documents awaiting approval."""
    try:
        query = """
        MATCH (d:PendingDocument)
        WHERE d.status = 'pending_approval'
        RETURN d.id as id, d.filename as filename, d.source as source,
               d.created_at as created_at
        ORDER BY d.created_at DESC
        """
        results = db.execute_query(query)

        return jsonify({
            'pending_documents': results or [],
            'count': len(results) if results else 0
        })

    except Exception as e:
        logger.error(f"Error getting pending documents: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/approve-document/<approval_id>', methods=['POST'])
def approve_document(approval_id):
    """Approve a pending document and add to processing queue."""
    try:
        import hashlib

        # Get pending document details including provenance
        query = """
        MATCH (d:PendingDocument {id: $approval_id})
        WHERE d.status = 'pending_approval'
        RETURN d.filename as filename, d.filepath as filepath,
               d.created_by as discovered_by,
               d.created_by_agent_id as discovered_by_agent_id
        """
        result = db.execute_query(query, {'approval_id': approval_id})

        if not result:
            return jsonify({'error': 'Document not found or already processed'}), 404

        filename = result[0]['filename']
        filepath = result[0]['filepath']
        discovered_by = result[0].get('discovered_by')
        discovered_by_agent_id = result[0].get('discovered_by_agent_id')

        # Update status to approved
        update_query = """
        MATCH (d:PendingDocument {id: $approval_id})
        SET d.status = 'approved', d.approved_at = datetime()
        """
        db.execute_query(update_query, {'approval_id': approval_id})

        # Add to processing queue with provenance metadata
        processing_queue.put((filepath, filename, discovered_by, discovered_by_agent_id))
        queue_position = processing_queue.qsize()

        logger.info(f"[APPROVAL] Document approved and queued: {filename}")

        # Emit updates
        with app.app_context():
            socketio.emit('document_approved', {
                'approval_id': approval_id,
                'filename': filename
            })
            socketio.emit('queue_update', {
                'processing': current_processing_filename,
                'queue_size': queue_position
            })

        return jsonify({
            'status': 'approved',
            'filename': filename,
            'queue_position': queue_position
        })

    except Exception as e:
        logger.error(f"Error approving document: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/reject-document/<approval_id>', methods=['DELETE'])
def reject_document(approval_id):
    """Reject a pending document and remove from queue."""
    try:
        # Get document details
        query = """
        MATCH (d:PendingDocument {id: $approval_id})
        WHERE d.status = 'pending_approval'
        RETURN d.filename as filename, d.filepath as filepath
        """
        result = db.execute_query(query, {'approval_id': approval_id})

        if not result:
            return jsonify({'error': 'Document not found or already processed'}), 404

        filename = result[0]['filename']
        filepath = result[0]['filepath']

        # Delete pending document node
        delete_query = """
        MATCH (d:PendingDocument {id: $approval_id})
        DELETE d
        """
        db.execute_query(delete_query, {'approval_id': approval_id})

        # Remove file from disk
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            logger.warning(f"Could not delete file {filepath}: {e}")

        logger.info(f"[APPROVAL] Document rejected and deleted: {filename}")

        # Emit update
        with app.app_context():
            socketio.emit('document_rejected', {
                'approval_id': approval_id,
                'filename': filename
            })

        return jsonify({
            'status': 'rejected',
            'filename': filename
        })

    except Exception as e:
        logger.error(f"Error rejecting document: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/process-url', methods=['POST'])
def process_url():
    """Download and process document from URL."""
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # TODO: Implement URL download
    return jsonify({
        'status': 'not_implemented',
        'message': 'URL processing coming soon'
    })


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    print('Client connected')
    emit('connected', {'status': 'ready'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    print('Client disconnected')


# Chat message history (in-memory for now, will move to database)
chat_history = []


@socketio.on('chat_message')
def handle_chat_message(data):
    """
    Process user chat message through AI agent.

    Expected data format:
    {
        'message': str,
        'timestamp': str,
        'context': {
            'selected_nodes': list,
            'total_nodes': int,
            'total_links': int,
            'search_query': str
        }
    }
    """
    user_message = data.get('message', '').strip()
    graph_context = data.get('context', {})
    timestamp = data.get('timestamp')

    if not user_message:
        emit('chat_response', {
            'message': 'I didn\'t receive a message. Please try again.',
            'actions': [],
            'timestamp': timestamp
        })
        return

    # Store user message in history
    chat_history.append({
        'sender': 'user',
        'message': user_message,
        'timestamp': timestamp,
        'context': graph_context
    })

    logger.info(f"[CHAT] User: {user_message}")
    logger.info(f"[CHAT] Context: {graph_context}")

    # Process message and generate response
    response_data = process_chat_message(user_message, graph_context)

    # Store AI response in history
    chat_history.append({
        'sender': 'ai',
        'message': response_data['message'],
        'timestamp': response_data['timestamp'],
        'actions': response_data.get('actions', [])
    })

    logger.info(f"[CHAT] AI: {response_data['message']}")

    # Send response back to client
    emit('chat_response', response_data)


def process_chat_message(message, context):
    """
    Process chat message and determine appropriate response.

    This function will be enhanced to integrate with agent orchestration.
    For now, it provides intelligent responses based on message content.
    """
    from datetime import datetime

    message_lower = message.lower()
    response_text = ""
    actions = []

    # Command parsing (slash commands)
    if message.startswith('/'):
        return handle_chat_command(message, context)

    # Confidence adjustment via chat (EXECUTE DIRECTLY)
    if any(word in message_lower for word in ['set confidence', 'set to', 'mark as', 'confidence to']):
        # Extract confidence value
        import re
        confidence_value = None

        # Try to find percentage (e.g., "80%", "80 percent")
        percent_match = re.search(r'(\d+)\s*(?:%|percent)', message_lower)
        if percent_match:
            confidence_value = int(percent_match.group(1)) / 100.0

        # Try decimal (e.g., "0.8")
        elif re.search(r'0\.\d+', message):
            decimal_match = re.search(r'(0\.\d+)', message)
            confidence_value = float(decimal_match.group(1))

        # Try "mark as true/false"
        elif 'mark as true' in message_lower or 'set to true' in message_lower:
            confidence_value = 1.0
        elif 'mark as false' in message_lower or 'set to false' in message_lower:
            confidence_value = 0.0

        if confidence_value is not None:
            # Check if user has a claim selected
            selected_nodes = context.get('selected_nodes', [])

            if selected_nodes and len(selected_nodes) > 0:
                claim_id = selected_nodes[0]

                try:
                    # Get the claim
                    claim = claim_repo.get_claim(claim_id)
                    if not claim:
                        response_text = f"Could not find claim with ID: {claim_id}"
                    else:
                        # Store the user override in Neo4j
                        query = """
                        MATCH (c:Claim {id: $claim_id})
                        SET c.user_confidence_override = $user_confidence
                        SET c.override_timestamp = datetime()
                        RETURN c.confidence as ai_confidence, c.user_confidence_override as user_override
                        """
                        result = db.execute_query(query, {
                            'claim_id': claim_id,
                            'user_confidence': confidence_value
                        })

                        if result:
                            confidence_percent = int(confidence_value * 100)
                            response_text = (
                                f"✓ Confidence updated!\n\n"
                                f"**Claim:** {claim_id[:20]}...\n"
                                f"**New Confidence:** {confidence_percent}%\n"
                                f"**AI Original:** {int(result[0]['ai_confidence'] * 100)}%\n\n"
                                f"Your override is now active (marked with gold ✓). "
                                f"The graph has been updated."
                            )
                            actions.append({'type': 'reload_graph'})
                        else:
                            response_text = "Failed to update confidence in database"

                except Exception as e:
                    logger.error(f"Error updating confidence via chat: {e}")
                    logger.error(traceback.format_exc())
                    response_text = f"Error updating confidence: {str(e)}"
            else:
                response_text = (
                    f"To set confidence to {int(confidence_value * 100)}%, first select a claim by clicking it in the graph.\n\n"
                    f"Then you can say:\n"
                    f"• \"Set this to {int(confidence_value * 100)}%\"\n"
                    f"• \"Mark this as true\" (100%)\n"
                    f"• \"Mark this as false\" (0%)"
                )
        else:
            response_text = (
                "I couldn't find a confidence value in your message.\n\n"
                "Try:\n"
                "• \"Set to 80%\"\n"
                "• \"Mark as true\" (100%)\n"
                "• \"Mark as false\" (0%)\n"
                "• \"Set confidence to 50%\""
            )

    # Manual claim creation (with optional confidence setting)
    # More flexible pattern matching: "add a claim", "add claim", "create a claim", etc.
    elif any(phrase in message_lower for phrase in ['add a claim', 'add claim', 'create a claim', 'create claim', 'new claim', 'enter a claim', 'enter claim', 'i claim']):
        # Extract claim text if present (look for quotes or "that" constructions)
        claim_text = None
        initial_confidence = 0.5  # Default

        # Try to extract quoted text
        import re
        quotes = re.findall(r'"([^"]+)"', message)
        if quotes:
            claim_text = quotes[0]
        elif 'that ' in message_lower:
            # Try "I claim that X" or "claim that X"
            parts = message.split('that ', 1)
            if len(parts) > 1:
                # Remove any confidence specification from claim text
                claim_part = parts[1].strip()
                # Remove trailing "with confidence X%" or "at X%"
                claim_text = re.sub(r'\s+(with|at)\s+confidence\s+\d+%?.*$', '', claim_part, flags=re.IGNORECASE)
                claim_text = re.sub(r'\s+confidence\s+\d+%?.*$', '', claim_text, flags=re.IGNORECASE)

        # Extract confidence if specified (e.g., "with confidence 80%", "at 100%")
        confidence_match = re.search(r'(?:with|at)?\s*confidence\s*(?:of)?\s*(\d+)\s*%?', message_lower)
        if confidence_match:
            initial_confidence = int(confidence_match.group(1)) / 100.0
        elif 'mark as true' in message_lower or '100%' in message_lower:
            initial_confidence = 1.0
        elif 'mark as false' in message_lower or '0%' in message_lower:
            initial_confidence = 0.0

        if claim_text:
            # Create the claim (call helper function directly instead of HTTP request)
            try:
                result = _create_claim_helper(claim_text, initial_confidence)

                if result['success']:
                    confidence_note = ""
                    if initial_confidence != 0.5:
                        confidence_note = f"\n**Initial Confidence:** {int(initial_confidence * 100)}%"

                    response_text = (
                        f"✓ Claim created successfully!\n\n"
                        f"**Claim:** {result['text']}\n"
                        f"**ID:** {result['claim_id'][:16]}..."
                        f"{confidence_note}\n\n"
                        f"The claim has been added to your graph. You can now:\n"
                        f"• Find supporting evidence\n"
                        f"• Find contradicting evidence\n"
                        f"• Adjust the confidence score"
                    )
                    actions.append({'type': 'reload_graph'})
                else:
                    response_text = f"Failed to create claim: {result['error']}"
            except Exception as e:
                logger.error(f"Error creating claim via chat: {e}")
                logger.error(traceback.format_exc())
                response_text = f"Error creating claim: {str(e)}"
        else:
            response_text = (
                'To add a claim, please include it in quotes or use this format:\n\n'
                '• "Your claim here"\n'
                '• I claim that [your claim]\n'
                '• Add claim that [your claim]\n\n'
                'Example: **Add claim "Climate change is caused by human activity"**'
            )

    # Upload-related queries
    elif any(word in message_lower for word in ['upload', 'add document', 'add file', 'process document']):
        response_text = (
            "I can help you upload documents! You can:\n\n"
            "• Drag and drop files directly onto the upload zone\n"
            "• Click the upload zone to browse for files\n"
            "• Supported formats: PDF, TXT, DOCX\n\n"
            "Would you like me to highlight the upload area for you?"
        )
        actions.append({'type': 'highlight_upload'})

    # Document approval commands
    elif any(phrase in message_lower for phrase in ['pending document', 'approve document', 'reject document', 'pending approval']):
        import re

        # Show pending documents
        if any(phrase in message_lower for phrase in ['show pending', 'list pending', 'pending document', 'what pending']):
            try:
                query = """
                MATCH (d:PendingDocument)
                WHERE d.status = 'pending_approval'
                RETURN d.id as id, d.filename as filename, d.source as source,
                       d.created_at as created_at
                ORDER BY d.created_at DESC
                """
                pending_docs = db.execute_query(query)

                if pending_docs and len(pending_docs) > 0:
                    response_text = f"📋 **Pending Documents ({len(pending_docs)}):**\n\n"
                    for idx, doc in enumerate(pending_docs, 1):
                        response_text += f"{idx}. **{doc['filename']}**\n   Source: {doc['source']}\n   ID: {doc['id'][:12]}...\n\n"
                    response_text += "To approve or reject:\n• \"Approve document 1\"\n• \"Reject document 2\"\n• \"Approve all\""
                else:
                    response_text = "✓ No documents pending approval.\n\nAll documents are processed!"

            except Exception as e:
                logger.error(f"Error fetching pending documents: {e}")
                response_text = f"Error fetching pending documents: {str(e)}"

        # Approve document(s)
        elif 'approve' in message_lower:
            # Check for "approve all"
            if 'all' in message_lower:
                try:
                    query = """
                    MATCH (d:PendingDocument)
                    WHERE d.status = 'pending_approval'
                    RETURN d.id as id, d.filename as filename, d.filepath as filepath,
                           d.created_by as discovered_by,
                           d.created_by_agent_id as discovered_by_agent_id
                    """
                    pending_docs = db.execute_query(query)

                    if pending_docs and len(pending_docs) > 0:
                        approved_count = 0
                        for doc in pending_docs:
                            # Update status
                            update_query = """
                            MATCH (d:PendingDocument {id: $approval_id})
                            SET d.status = 'approved', d.approved_at = datetime()
                            """
                            db.execute_query(update_query, {'approval_id': doc['id']})

                            # Add to processing queue with provenance
                            processing_queue.put((
                                doc['filepath'],
                                doc['filename'],
                                doc.get('discovered_by'),
                                doc.get('discovered_by_agent_id')
                            ))
                            approved_count += 1

                            # Emit events
                            with app.app_context():
                                socketio.emit('document_approved', {
                                    'approval_id': doc['id'],
                                    'filename': doc['filename']
                                })

                        # Update queue status
                        queue_position = processing_queue.qsize()
                        with app.app_context():
                            socketio.emit('queue_update', {
                                'processing': None,
                                'queue_size': queue_position
                            })

                        response_text = (
                            f"✓ Approved {approved_count} document(s)!\n\n"
                            f"All pending documents have been added to the processing queue. "
                            f"Check the Background Agents panel to monitor progress."
                        )
                        actions.append({'type': 'reload_graph'})
                    else:
                        response_text = "No documents pending approval."

                except Exception as e:
                    logger.error(f"Error approving all documents: {e}")
                    logger.error(traceback.format_exc())
                    response_text = f"Error approving documents: {str(e)}"

            # Approve specific document by number or ID
            else:
                # Extract document number or ID
                number_match = re.search(r'document\s+(\d+)', message_lower)
                id_match = re.search(r'id[:\s]+([a-f0-9_]+)', message_lower)

                if number_match or id_match:
                    try:
                        # Get pending documents with provenance
                        query = """
                        MATCH (d:PendingDocument)
                        WHERE d.status = 'pending_approval'
                        RETURN d.id as id, d.filename as filename, d.filepath as filepath,
                               d.created_by as discovered_by,
                               d.created_by_agent_id as discovered_by_agent_id
                        ORDER BY d.created_at DESC
                        """
                        pending_docs = db.execute_query(query)

                        if number_match:
                            doc_number = int(number_match.group(1))
                            if doc_number > 0 and doc_number <= len(pending_docs):
                                doc = pending_docs[doc_number - 1]
                            else:
                                response_text = f"Document number {doc_number} not found. Use 'show pending' to see list."
                                doc = None
                        elif id_match:
                            doc_id = id_match.group(1)
                            doc = next((d for d in pending_docs if d['id'].startswith(doc_id)), None)
                            if not doc:
                                response_text = f"Document ID {doc_id} not found."

                        if doc:
                            # Update status
                            update_query = """
                            MATCH (d:PendingDocument {id: $approval_id})
                            SET d.status = 'approved', d.approved_at = datetime()
                            """
                            db.execute_query(update_query, {'approval_id': doc['id']})

                            # Add to processing queue with provenance
                            processing_queue.put((
                                doc['filepath'],
                                doc['filename'],
                                doc.get('discovered_by'),
                                doc.get('discovered_by_agent_id')
                            ))

                            # Emit events
                            with app.app_context():
                                socketio.emit('document_approved', {
                                    'approval_id': doc['id'],
                                    'filename': doc['filename']
                                })
                                socketio.emit('queue_update', {
                                    'processing': None,
                                    'queue_size': processing_queue.qsize()
                                })

                            response_text = (
                                f"✓ Document approved!\n\n"
                                f"**File:** {doc['filename']}\n\n"
                                f"Added to processing queue. Check Background Agents panel for progress."
                            )
                            actions.append({'type': 'reload_graph'})

                    except Exception as e:
                        logger.error(f"Error approving document: {e}")
                        logger.error(traceback.format_exc())
                        response_text = f"Error approving document: {str(e)}"
                else:
                    response_text = (
                        "Please specify which document to approve:\n\n"
                        "• \"Approve document 1\"\n"
                        "• \"Approve document ID approval_abc\"\n"
                        "• \"Approve all\"\n\n"
                        "Use 'show pending' to see the list."
                    )

        # Reject document
        elif 'reject' in message_lower:
            # Extract document number or ID
            number_match = re.search(r'document\s+(\d+)', message_lower)
            id_match = re.search(r'id[:\s]+([a-f0-9_]+)', message_lower)

            if number_match or id_match:
                try:
                    # Get pending documents
                    query = """
                    MATCH (d:PendingDocument)
                    WHERE d.status = 'pending_approval'
                    RETURN d.id as id, d.filename as filename, d.filepath as filepath
                    ORDER BY d.created_at DESC
                    """
                    pending_docs = db.execute_query(query)

                    if number_match:
                        doc_number = int(number_match.group(1))
                        if doc_number > 0 and doc_number <= len(pending_docs):
                            doc = pending_docs[doc_number - 1]
                        else:
                            response_text = f"Document number {doc_number} not found."
                            doc = None
                    elif id_match:
                        doc_id = id_match.group(1)
                        doc = next((d for d in pending_docs if d['id'].startswith(doc_id)), None)
                        if not doc:
                            response_text = f"Document ID {doc_id} not found."

                    if doc:
                        # Delete from database
                        delete_query = """
                        MATCH (d:PendingDocument {id: $approval_id})
                        DELETE d
                        """
                        db.execute_query(delete_query, {'approval_id': doc['id']})

                        # Delete file from disk
                        import os
                        if os.path.exists(doc['filepath']):
                            os.remove(doc['filepath'])

                        # Emit event
                        with app.app_context():
                            socketio.emit('document_rejected', {
                                'approval_id': doc['id'],
                                'filename': doc['filename']
                            })

                        response_text = (
                            f"✗ Document rejected!\n\n"
                            f"**File:** {doc['filename']}\n\n"
                            f"The document has been removed from the system."
                        )

                except Exception as e:
                    logger.error(f"Error rejecting document: {e}")
                    logger.error(traceback.format_exc())
                    response_text = f"Error rejecting document: {str(e)}"
            else:
                response_text = (
                    "Please specify which document to reject:\n\n"
                    "• \"Reject document 1\"\n"
                    "• \"Reject document ID approval_abc\"\n\n"
                    "Use 'show pending' to see the list."
                )

    # Claim investigation
    elif any(word in message_lower for word in ['investigate', 'research', 'find evidence', 'support', 'contradict', 'challenge']):
        # Determine investigation type
        investigation_type = 'support'
        if any(word in message_lower for word in ['contradict', 'challenge', 'against', 'opposing']):
            investigation_type = 'contradict'

        # Check if user has a claim selected
        selected_nodes = context.get('selected_nodes', [])

        if selected_nodes and len(selected_nodes) > 0:
            # Try to trigger investigation for selected claim
            claim_id = selected_nodes[0]  # Use first selected node

            try:
                # Get claim using repository
                claim = claim_repo.get_claim(claim_id)
                if not claim:
                    response_text = f"Could not find claim with ID: {claim_id}"
                else:
                    claim_text = claim['text']

                    # Create agent and research result
                    agent_tracker = AgentTracker()

                    agent_name = f"InvestigationAgent-{investigation_type.capitalize()}"
                    agent_tracker.create_agent_node_in_neo4j(
                        agent_name=agent_name,
                        agent_type="investigation",
                        capabilities=["evidence_search", "claim_validation"],
                        db=db
                    )

                    research_result = agent_tracker.create_research_result(
                        agent_name=agent_name,
                        claim_id=claim_id,
                        findings=f"Investigating claim to {investigation_type}...",
                        status="in_progress",
                        confidence=None
                    )

                    result_id = agent_tracker.create_research_result_node_in_neo4j(research_result, db)

                    response_text = (
                        f"✓ Investigation started!\n\n"
                        f"**Type:** {investigation_type.capitalize()}\n"
                        f"**Agent:** {agent_name}\n"
                        f"**Claim:** {claim_text[:100]}...\n\n"
                        f"The agent will search for {investigation_type}ing evidence. "
                        f"Results will appear in the graph when complete."
                    )
                    actions.append({'type': 'reload_graph'})

            except Exception as e:
                logger.error(f"Error starting investigation via chat: {e}")
                logger.error(traceback.format_exc())
                response_text = f"Error starting investigation: {str(e)}"

        else:
            response_text = (
                "To investigate a claim, first select it in the graph by clicking on it.\n\n"
                "Then you can ask me to:\n"
                "• \"Investigate this claim\"\n"
                "• \"Find supporting evidence\"\n"
                "• \"Find contradicting evidence\"\n\n"
                "Or use the buttons in the claim details panel."
            )

    # Auto-linking evidence commands
    elif any(phrase in message_lower for phrase in ['auto-link', 'link evidence', 'auto link', 'find related evidence', 'connect evidence']):
        try:
            from research_agent.llm_classifier import get_classifier, AutoLinkingPipeline
            from research_agent.semantic_similarity import get_similarity_engine

            # Check if user has a specific claim selected
            selected_nodes = context.get('selected_nodes', [])

            # Get user settings from context (defaults to 0.7 if not provided)
            user_settings = context.get('user_settings', {})
            similarity_threshold = user_settings.get('similarity_threshold', 0.7)
            embedding_model = user_settings.get('embedding_model', 'all-mpnet-base-v2')

            if selected_nodes and len(selected_nodes) > 0:
                # Run auto-linking for selected claim only
                claim_id = selected_nodes[0]

                # Check if it's actually a claim
                claim = claim_repo.get_claim(claim_id)
                if not claim:
                    response_text = "The selected node is not a claim. Please select a claim first."
                else:
                    response_text = "🔗 Running auto-linking pipeline for selected claim...\n\n"
                    response_text += f"**Settings:** Threshold={similarity_threshold:.2f}, Model={embedding_model}\n"
                    response_text += "**Stage 1:** Finding semantically similar evidence (embeddings)\n"
                    response_text += "**Stage 2:** Classifying relationships (LLM)\n\n"

                    classifier = get_classifier(provider="anthropic")
                    engine = get_similarity_engine(model_name=embedding_model)
                    pipeline = AutoLinkingPipeline(db, engine, classifier)

                    result = pipeline.auto_link_for_claim(
                        claim_id=claim_id,
                        semantic_threshold=similarity_threshold,
                        llm_confidence_threshold=0.7,
                        auto_approve=True
                    )

                    if 'error' in result:
                        response_text += f"❌ Error: {result['error']}"
                    else:
                        response_text += f"✓ **Found {result.get('candidates_found', 0)} similar pieces of evidence**\n\n"
                        response_text += f"**Classification Results:**\n"
                        response_text += f"• {result.get('supports', 0)} SUPPORTS\n"
                        response_text += f"• {result.get('contradicts', 0)} CONTRADICTS\n"
                        response_text += f"• {result.get('irrelevant', 0)} IRRELEVANT\n\n"
                        response_text += f"**Created {result.get('links_created', 0)} relationships** in the graph."

                        actions.append({'type': 'reload_graph'})

            else:
                # Run auto-linking for ALL claims
                response_text = "🔗 Running auto-linking for ALL claims in database...\n\n"
                response_text += f"**Settings:** Threshold={similarity_threshold:.2f}, Model={embedding_model}\n"
                response_text += "This may take a few minutes depending on the number of claims.\n\n"

                # Get all claims
                claims_query = """
                MATCH (c:Claim)
                WHERE c.embedding IS NOT NULL
                RETURN c.id as id
                """
                all_claims = db.execute_query(claims_query)

                if not all_claims:
                    response_text = "No claims with embeddings found. Upload documents first."
                else:
                    classifier = get_classifier(provider="anthropic")
                    engine = get_similarity_engine(model_name=embedding_model)
                    pipeline = AutoLinkingPipeline(db, engine, classifier)

                    total_links = 0
                    total_supports = 0
                    total_contradicts = 0

                    for claim in all_claims:
                        result = pipeline.auto_link_for_claim(
                            claim_id=claim['id'],
                            semantic_threshold=similarity_threshold,
                            llm_confidence_threshold=0.7,
                            auto_approve=True
                        )

                        if 'error' not in result:
                            total_links += result.get('links_created', 0)
                            total_supports += result.get('supports', 0)
                            total_contradicts += result.get('contradicts', 0)

                    response_text += f"✓ **Processed {len(all_claims)} claims**\n\n"
                    response_text += f"**Total Relationships Created:**\n"
                    response_text += f"• {total_supports} SUPPORTS\n"
                    response_text += f"• {total_contradicts} CONTRADICTS\n"
                    response_text += f"• {total_links} total links\n\n"
                    response_text += "Check the graph to see the new connections!"

                    actions.append({'type': 'reload_graph'})

        except Exception as e:
            logger.error(f"Error in auto-linking via chat: {e}")
            logger.error(traceback.format_exc())
            response_text = f"❌ Error during auto-linking: {str(e)}\n\nCheck the console for details."

    # Document discovery commands
    elif any(phrase in message_lower for phrase in ['search arxiv', 'find papers', 'search pubmed', 'search for papers', 'find documents', 'discover papers']):
        try:
            # Extract query from message
            query = None
            for trigger in ['search arxiv for', 'find papers about', 'search pubmed for', 'search for papers about', 'find documents about', 'discover papers about']:
                if trigger in message_lower:
                    query = message_lower.split(trigger, 1)[1].strip()
                    break

            if not query:
                # Try extracting from quoted text
                import re
                quote_match = re.search(r'["\']([^"\']+)["\']', message)
                if quote_match:
                    query = quote_match.group(1)

            if not query:
                response_text = (
                    "Please specify what to search for. Examples:\n\n"
                    "• \"Search arXiv for vaccine efficacy\"\n"
                    "• \"Find papers about 'machine learning interpretability'\"\n"
                    "• \"Search PubMed for COVID-19 treatments\""
                )
            else:
                # Determine sources from message
                sources = []
                if 'arxiv' in message_lower:
                    sources.append('arxiv')
                if 'pubmed' in message_lower:
                    sources.append('pubmed')
                if not sources:
                    sources = ['arxiv', 'pubmed']  # Default to both

                response_text = f"🔍 Starting document search...\n\n"
                response_text += f"**Query:** {query}\n"
                response_text += f"**Sources:** {', '.join(sources).upper()}\n\n"
                response_text += "The document finder agent is running in the background. "
                response_text += "Check the **Background Agents** panel to monitor progress.\n\n"
                response_text += "Found documents will be added to the approval queue automatically."

                # Start background agent
                from research_agent.document_finder_agent import DocumentFinderAgent
                from research_agent.transcript_manager import get_transcript_manager
                import threading

                # Create transcript for monitoring
                transcript_manager = get_transcript_manager()
                agent_id = transcript_manager.create_agent(
                    'document_finder',
                    f'Searching for papers: {query}'
                )

                def run_finder():
                    try:
                        transcript_manager.log(agent_id, 'info', f'Starting document search for: {query}')

                        agent = DocumentFinderAgent(
                            query=query,
                            output_dir="./uploads/discovered_papers"
                        )
                        agent.set_sources(sources)
                        agent.set_max_results(10)

                        # Set progress callback to emit WebSocket events AND log to transcript
                        def progress_callback(message, data=None):
                            # Log to transcript
                            level = 'error' if 'error' in message.lower() or '❌' in message else \
                                   'warning' if 'warning' in message.lower() or '⚠️' in message else \
                                   'success' if '✓' in message or '✅' in message else 'info'
                            transcript_manager.log(agent_id, level, message, data)

                            # Emit WebSocket event
                            with app.app_context():
                                socketio.emit('agent_progress', {
                                    'agent': 'document_finder',
                                    'agent_id': agent_id,
                                    'message': message,
                                    'data': data or {}
                                })

                        agent.set_progress_callback(progress_callback)

                        # Run search and download
                        results = agent.search_and_download()

                        # Add found papers to approval queue with provenance
                        if 'papers' in results:
                            from datetime import datetime
                            for paper in results['papers']:
                                if 'local_path' in paper:
                                    # Create PendingDocument node in Neo4j with provenance tracking
                                    approval_id = f"pending_{paper['source']}_{paper.get('arxiv_id', paper.get('pmid', 'unknown'))}"

                                    create_query = """
                                    CREATE (d:PendingDocument {
                                        id: $approval_id,
                                        filename: $filename,
                                        filepath: $filepath,
                                        title: $title,
                                        authors: $authors,
                                        source: $source,
                                        status: 'pending_approval',
                                        created_at: datetime(),
                                        created_by: 'document_finder',
                                        created_by_agent_id: $agent_id
                                    })
                                    RETURN d.id as id
                                    """

                                    db.execute_query(create_query, {
                                        'approval_id': approval_id,
                                        'filename': os.path.basename(paper['local_path']),
                                        'filepath': paper['local_path'],
                                        'title': paper['title'],
                                        'authors': ', '.join(paper.get('authors', [])[:3]),
                                        'source': paper['source'],
                                        'agent_id': agent_id
                                    })

                                    transcript_manager.log(agent_id, 'success', f"Added to approval queue: {paper['title']}", {
                                        'approval_id': approval_id,
                                        'source': paper['source']
                                    })

                        # Mark agent as completed
                        transcript_manager.complete_agent(agent_id, results)

                        # Emit completion event
                        with app.app_context():
                            socketio.emit('agent_complete', {
                                'agent': 'document_finder',
                                'agent_id': agent_id,
                                'query': query,
                                'results': results,
                                'message': f"✅ Found {results.get('downloaded', 0)} papers. Added to approval queue."
                            })

                    except Exception as e:
                        error_msg = f"Document finder agent error: {str(e)}"
                        logger.error(error_msg)
                        logger.error(traceback.format_exc())

                        # Mark agent as failed
                        transcript_manager.fail_agent(agent_id, error_msg)

                        with app.app_context():
                            socketio.emit('agent_error', {
                                'agent': 'document_finder',
                                'agent_id': agent_id,
                                'error': str(e)
                            })

                # Start in background thread
                thread = threading.Thread(target=run_finder, daemon=True)
                thread.start()

                actions.append({'type': 'highlight_element', 'selector': '#agent-monitor-panel'})

        except Exception as e:
            logger.error(f"Error starting document finder: {e}")
            logger.error(traceback.format_exc())
            response_text = f"❌ Error starting document search: {str(e)}"

    # Generate embeddings command
    elif any(phrase in message_lower for phrase in ['generate embedding', 'create embedding', 'generate embeddings']):
        try:
            from research_agent.semantic_similarity import get_embedding_manager

            # Get user settings from context
            user_settings = context.get('user_settings', {})
            embedding_model = user_settings.get('embedding_model', 'all-mpnet-base-v2')

            # Determine dimensions based on model (384 for MiniLM, 768 for others)
            dimensions = 384 if 'minilm' in embedding_model.lower() else 768

            response_text = "🔄 Generating semantic embeddings for all claims and evidence...\n\n"
            response_text += f"**Model:** {embedding_model}\n"
            response_text += f"**Dimensions:** {dimensions}\n\n"
            response_text += "This creates vectors for semantic similarity matching.\n\n"

            embedding_manager = get_embedding_manager(db, model_name=embedding_model)

            # Get nodes without embeddings
            claims_query = """
            MATCH (c:Claim)
            WHERE c.embedding IS NULL
            RETURN c.id as id, c.text as text
            """
            claims = db.execute_query(claims_query)

            evidence_query = """
            MATCH (e:Evidence)
            WHERE e.embedding IS NULL
            RETURN e.id as id, e.text as text
            """
            evidence = db.execute_query(evidence_query)

            claims_processed = 0
            claims_failed = 0
            for claim in claims:
                success = embedding_manager.store_claim_embedding(claim['id'], claim['text'])
                if success:
                    claims_processed += 1
                else:
                    claims_failed += 1

            evidence_processed = 0
            evidence_failed = 0
            for ev in evidence:
                success = embedding_manager.store_evidence_embedding(ev['id'], ev['text'])
                if success:
                    evidence_processed += 1
                else:
                    evidence_failed += 1

            response_text += f"✓ **Embeddings Generated:**\n\n"
            response_text += f"**Claims:**\n"
            response_text += f"• Processed: {claims_processed}\n"
            response_text += f"• Failed: {claims_failed}\n\n"
            response_text += f"**Evidence:**\n"
            response_text += f"• Processed: {evidence_processed}\n"
            response_text += f"• Failed: {evidence_failed}\n\n"

            if claims_failed > 0 or evidence_failed > 0:
                response_text += f"⚠️ Some embeddings failed. Check console for errors."
            else:
                response_text += f"Now you can run 'auto-link evidence' to find relationships!"

        except Exception as e:
            logger.error(f"Error generating embeddings via chat: {e}")
            logger.error(traceback.format_exc())
            response_text = f"❌ Error generating embeddings: {str(e)}\n\nCheck the console for details."

    # Graph navigation help
    elif any(word in message_lower for word in ['navigate', 'find', 'search', 'filter']):
        response_text = (
            f"Your graph currently has {context.get('total_nodes', 0)} nodes. "
            f"You can:\n\n"
            f"• Use the search bar to filter by text\n"
            f"• Toggle node type filters (Documents, Claims, Evidence)\n"
            f"• Click nodes to see details\n"
            f"• Drag nodes to rearrange\n"
            f"• Scroll to zoom in/out"
        )

    # Clustering
    elif any(word in message_lower for word in ['cluster', 'organize', 'group']):
        response_text = (
            "I can help organize your claims! Clustering happens automatically when:\n\n"
            "• You upload a new document\n"
            "• Processing completes\n\n"
            "You can also manually trigger clustering using the 'Refresh Clustering' button "
            "in the stats bar. This will group similar claims across documents."
        )

    # Confidence/quality questions
    elif any(word in message_lower for word in ['confidence', 'score', 'rating', 'quality']):
        response_text = (
            "Claim confidence scores are calculated based on:\n\n"
            "• Supporting evidence found\n"
            "• Contradicting evidence\n"
            "• Quality of sources\n\n"
            "You can override these scores manually by:\n"
            "1. Clicking on a claim\n"
            "2. Using the confidence override slider\n"
            "3. Clicking 'Apply Override'\n\n"
            "Your adjustments will be marked with a gold ✓ indicator."
        )

    # Agent status queries
    elif any(word in message_lower for word in ['agent', 'processing', 'working', 'busy', 'queue']):
        try:
            import requests
            response = requests.get('http://localhost:5000/api/agent-status', timeout=5)

            if response.ok:
                data = response.json()
                agent_count = data['active_agents']

                if agent_count == 0:
                    response_text = "No agents are currently active. The system is idle."
                else:
                    response_text = f"**Active Agents ({agent_count}):**\n\n"
                    for agent in data['agents']:
                        response_text += f"• **{agent['name']}**: {agent['task']}\n"

                    if data['queue_size'] > 0:
                        response_text += f"\n📋 {data['queue_size']} document(s) in queue"
            else:
                response_text = "Could not retrieve agent status."
        except Exception as e:
            logger.error(f"Error querying agent status: {e}")
            response_text = "Error retrieving agent status."

    # Graph statistics
    elif any(word in message_lower for word in ['how many', 'count', 'stats', 'statistics']):
        response_text = (
            f"**Current Graph Statistics:**\n\n"
            f"• Total nodes: {context.get('total_nodes', 0)}\n"
            f"• Total links: {context.get('total_links', 0)}\n"
            f"• Selected: {len(context.get('selected_nodes', []))}\n\n"
            f"Use the stats bar at the top for more detailed breakdowns."
        )

    # General help
    elif any(word in message_lower for word in ['help', 'what can you do', 'how do']):
        response_text = (
            "I'm your research assistant! Here's what I can help with:\n\n"
            "**📄 Document Processing:**\n"
            "• Upload and analyze documents (PDF, TXT, DOCX)\n"
            "• Extract claims automatically\n"
            "• Organize claims into hierarchies\n\n"
            "**🔍 Research & Investigation:**\n"
            "• Find supporting evidence for claims\n"
            "• Find contradicting evidence\n"
            "• Track research progress\n\n"
            "**📊 Graph Management:**\n"
            "• Navigate and search your knowledge graph\n"
            "• Adjust claim confidence scores\n"
            "• Remove invalid evidence\n"
            "• Cluster related claims\n\n"
            "Just ask me anything or tell me what you'd like to do!"
        )

    # Default response
    else:
        response_text = (
            f"I understand you said: \"{message}\"\n\n"
            f"I'm still learning! Currently I can help with:\n"
            f"• Uploading documents\n"
            f"• Investigating claims\n"
            f"• Navigating the graph\n"
            f"• Understanding confidence scores\n\n"
            f"Try asking 'help' for more details, or tell me specifically what you'd like to do."
        )

    return {
        'message': response_text,
        'actions': actions,
        'timestamp': datetime.now().isoformat()
    }


def handle_chat_command(command, context):
    """
    Handle slash commands like /upload, /investigate, /help.
    """
    from datetime import datetime

    parts = command.split()
    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    if cmd == '/help':
        return {
            'message': (
                "**📋 Slash Commands:**\n\n"
                "`/help` - Show this help message\n"
                "`/upload` - Highlight upload area\n"
                "`/cluster` - Trigger MECE clustering\n"
                "`/stats` - Show graph statistics\n"
                "`/clear` - Clear chat history\n\n"
                "**💬 Natural Language:**\n\n"
                "**Claims:**\n"
                "• Add claim \"Your claim here\"\n"
                "• Show me claim [partial text]\n\n"
                "**Research:**\n"
                "• Investigate this claim\n"
                "• Find supporting evidence\n"
                "• Find contradicting evidence\n\n"
                "**Monitoring:**\n"
                "• What agents are running?\n"
                "• What's in the queue?\n"
                "• Show me the stats\n\n"
                "**Navigation:**\n"
                "• Help me find [topic]\n"
                "• How do I [task]?\n\n"
                "Just talk naturally - I understand context from your graph!"
            ),
            'actions': [],
            'timestamp': datetime.now().isoformat()
        }

    elif cmd == '/upload':
        return {
            'message': "Opening upload area...",
            'actions': [{'type': 'highlight_upload'}],
            'timestamp': datetime.now().isoformat()
        }

    elif cmd == '/cluster':
        return {
            'message': "Triggering clustering... This may take a moment.",
            'actions': [{'type': 'reload_graph'}],
            'timestamp': datetime.now().isoformat()
        }

    elif cmd == '/stats':
        return {
            'message': (
                f"**Graph Statistics:**\n\n"
                f"• Nodes: {context.get('total_nodes', 0)}\n"
                f"• Links: {context.get('total_links', 0)}\n"
                f"• Selected: {len(context.get('selected_nodes', []))}"
            ),
            'actions': [],
            'timestamp': datetime.now().isoformat()
        }

    elif cmd == '/clear':
        global chat_history
        chat_history = []
        return {
            'message': "Chat history cleared! How can I help you?",
            'actions': [],
            'timestamp': datetime.now().isoformat()
        }

    else:
        return {
            'message': f"Unknown command: {cmd}\n\nType `/help` to see available commands.",
            'actions': [],
            'timestamp': datetime.now().isoformat()
        }


@app.route('/api/delete-document/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete document and only its owned claims (that would become orphaned)."""
    success = doc_repo.delete_document_with_owned_claims(doc_id)

    if success:
        return jsonify({
            'status': 'deleted',
            'message': 'Document and owned claims deleted'
        })
    else:
        return jsonify({
            'status': 'not_found',
            'message': 'Document not found'
        }), 404


@app.route('/api/clear-all', methods=['DELETE'])
def clear_all():
    """Clear all data from the database."""
    deleted_count = doc_repo.delete_all_nodes()

    return jsonify({
        'status': 'cleared',
        'message': f'All data cleared from database ({deleted_count} nodes deleted)'
    })


def _create_claim_helper(claim_text, initial_confidence=0.5):
    """
    Helper function to create a claim (shared by API and chat).

    Args:
        claim_text: The claim text
        initial_confidence: Initial confidence score (0-1)

    Returns:
        dict with 'success', 'claim_id', 'text', 'error'
    """
    if not claim_text or not claim_text.strip():
        return {'success': False, 'error': 'Claim text is required'}

    # Validate confidence
    if not (0 <= initial_confidence <= 1):
        return {'success': False, 'error': 'Confidence must be between 0 and 1'}

    try:
        # Generate unique claim ID
        claim_id = 'claim_' + hashlib.sha256(claim_text.encode()).hexdigest()[:16]

        # Create claim node in Neo4j with user-specified confidence
        query = """
        CREATE (c:Claim {
            id: $claim_id,
            text: $text,
            summary: $text,
            claim_type: 'manual',
            status: 'pending',
            disposition: 'manual',
            is_super_claim: false,
            confidence: $confidence,
            quality_score: 0.5,
            created_at: datetime()
        })
        RETURN c.id as id, c.text as text, c.confidence as confidence
        """
        result = db.execute_query(query, {
            'claim_id': claim_id,
            'text': claim_text,
            'confidence': initial_confidence
        })

        if not result:
            return {'success': False, 'error': 'Failed to create claim in database'}

        created_claim = result[0]

        # Emit real-time update
        with app.app_context():
            socketio.emit('claim_created', {
                'claim_id': created_claim['id'],
                'text': created_claim['text']
            })

        logger.info(f"[MANUAL CLAIM] Created: {claim_id}")

        return {
            'success': True,
            'claim_id': created_claim['id'],
            'text': created_claim['text']
        }

    except Exception as e:
        logger.error(f"Error creating manual claim: {e}")
        logger.error(traceback.format_exc())
        return {'success': False, 'error': str(e)}


@app.route('/api/create-manual-claim', methods=['POST'])
def create_manual_claim():
    """Create a manual claim from user input (e.g., via chat)."""
    data = request.json
    claim_text = data.get('text', '').strip()
    initial_confidence = data.get('initial_confidence', 0.5)

    result = _create_claim_helper(claim_text, initial_confidence)

    if result['success']:
        return jsonify({
            'status': 'created',
            'claim_id': result['claim_id'],
            'text': result['text'],
            'message': 'Claim created successfully'
        })
    else:
        return jsonify({'error': result['error']}), 400


@app.route('/api/run-cross-document-clustering', methods=['POST'])
def run_cross_document_clustering():
    """Run cross-document MECE clustering using Leiden algorithm."""
    try:
        from research_agent.cross_document_mece import run_cross_document_clustering
        import asyncio

        # Run the async clustering function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_cross_document_clustering())
        finally:
            loop.close()

        return jsonify({
            'status': 'success',
            'super_claims': len(result.get('super_claims', [])),
            'clusters': len(result.get('clusters', [])),
            'modularity': result.get('metrics', {}).get('modularity', 0),
            'total_claims': result.get('stats', {}).get('total_claims', 0),
            'message': f"Created {len(result.get('super_claims', []))} super-claims from {len(result.get('clusters', []))} communities"
        })

    except ImportError as e:
        logger.error(f"MECE clustering not available: {e}")
        return jsonify({
            'status': 'error',
            'message': 'MECE clustering dependencies not installed. Run: pip install leidenalg python-igraph'
        }), 500
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/assistant/chat', methods=['POST'])
def assistant_chat():
    """
    AI Assistant chat endpoint - processes user messages and returns AI responses.
    Uses the configured agent CLI (Claude Code by default).
    """
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        context = data.get('context', {})

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Build context-aware system prompt
        active_tab = context.get('activeTab', 'documents')
        selected_nodes = context.get('selectedNodes', [])

        # Build detailed selected nodes context
        selected_nodes_context = ""
        if selected_nodes:
            # Multi-node analysis mode
            if len(selected_nodes) > 1:
                selected_nodes_context = f"\n\n**Multi-Node Analysis Mode ({len(selected_nodes)} nodes selected):**\n"

                # Categorize nodes by type
                node_types = {}
                for node in selected_nodes:
                    node_data = node.get('node', {})
                    node_type = node_data.get('labels', ['Unknown'])[0] if node_data.get('labels') else 'Unknown'
                    if node_type not in node_types:
                        node_types[node_type] = []
                    node_types[node_type].append(node)

                # Summarize by type
                selected_nodes_context += "\nNode Summary:\n"
                for node_type, nodes_list in node_types.items():
                    selected_nodes_context += f"  - {len(nodes_list)} {node_type}(s)\n"

                selected_nodes_context += "\nDetailed Breakdown:\n"
                for idx, node in enumerate(selected_nodes[:5], 1):  # Limit to 5 for context size
                    node_data = node.get('node', {})
                    node_type = node_data.get('labels', ['Unknown'])[0] if node_data.get('labels') else 'Unknown'
                    node_title = node_data.get('title') or node_data.get('text', '')[:80] or node_data.get('summary', '')[:80] or 'Untitled'

                    selected_nodes_context += f"\n{idx}. {node_type}: {node_title}\n"

                    # Add relationship info for multi-node analysis
                    relationships = node.get('relationships', {})
                    if relationships:
                        rel_counts = {rel_type: len(rels) for rel_type, rels in relationships.items() if rels}
                        if rel_counts:
                            selected_nodes_context += f"   Connections: {', '.join(f'{count} {rel_type}' for rel_type, count in rel_counts.items())}\n"

                if len(selected_nodes) > 5:
                    selected_nodes_context += f"\n... and {len(selected_nodes) - 5} more nodes\n"

                selected_nodes_context += "\n**User expects comparative analysis** of these nodes - look for:\n"
                selected_nodes_context += "  - Common themes or patterns\n"
                selected_nodes_context += "  - Contradictions or inconsistencies\n"
                selected_nodes_context += "  - Knowledge gaps between nodes\n"
                selected_nodes_context += "  - Potential connections to explore\n"

            # Single node mode
            else:
                selected_nodes_context = "\n\n**Selected Node:**\n"
                node = selected_nodes[0]
                node_data = node.get('node', {})
                node_id = node_data.get('id', 'unknown')
                node_type = node_data.get('labels', ['Unknown'])[0] if node_data.get('labels') else 'Unknown'
                node_title = node_data.get('title') or node_data.get('text', '')[:100] or node_data.get('summary', '')[:100] or node_id[:8]

                selected_nodes_context += f"\n{node_type} - {node_title}\n"

                # Add key properties
                if node_type == 'Claim':
                    confidence = node_data.get('confidence', 'unknown')
                    status = node_data.get('status', 'unknown')
                    selected_nodes_context += f"  - Confidence: {confidence}\n"
                    selected_nodes_context += f"  - Status: {status}\n"

                # Add relationship counts
                relationships = node.get('relationships', {})
                if relationships:
                    rel_summary = []
                    for rel_type, rels in relationships.items():
                        if rels:
                            rel_summary.append(f"{len(rels)} {rel_type}")
                    if rel_summary:
                        selected_nodes_context += f"  - Connected to: {', '.join(rel_summary)}\n"

                # Add agent provenance
                history = node.get('history', [])
                if history:
                    created_by = next((h for h in history if h['event'] == 'Created'), None)
                    if created_by:
                        selected_nodes_context += f"  - Created by: {created_by.get('agent_type', 'unknown')} agent\n"

        system_prompt = f"""You are an AI research assistant helping users navigate and analyze their research graph database.

**Current Context:**
- Active Tab: {active_tab}
- Selected Nodes: {len(selected_nodes)} node(s) selected
- Available Actions: Search, analyze, create connections, summarize findings
{selected_nodes_context}
**Your Role:**
You help users:
1. Find and analyze documents, claims, and evidence
2. Discover connections between research items
3. Search for specific information
4. Organize and categorize research
5. Suggest next steps in their research

**Important Guidelines:**
- Be conversational and helpful
- Provide specific, actionable responses
- When suggesting data modifications (creating claims, linking evidence), acknowledge that user approval is required
- Reference the user's current context (tab, selected nodes) to give personalized suggestions
- Keep responses concise but informative
- Suggest concrete next steps based on what nodes are selected

**User's Message:**
{user_message}

Respond naturally as a helpful research assistant. Keep your response under 200 words."""

        # Invoke agent
        from .agent_config import get_agent_adapter
        adapter = get_agent_adapter()

        logger.info(f"[Assistant] Processing message: {user_message[:100]}...")

        try:
            response = adapter.invoke(system_prompt, timeout=30)

            # Try to parse JSON response if present
            try:
                import json
                # Check if response is wrapped in JSON
                if response.strip().startswith('{'):
                    response_data = json.loads(response)
                    # Extract text content if it's in a specific format
                    if 'response' in response_data:
                        response = response_data['response']
                    elif 'content' in response_data:
                        response = response_data['content']
            except (json.JSONDecodeError, KeyError):
                # Not JSON or different format, use as-is
                pass

            logger.info(f"[Assistant] Response generated ({len(response)} chars)")

            return jsonify({
                'response': response,
                'timestamp': time.time()
            })

        except subprocess.TimeoutExpired:
            logger.error("[Assistant] Agent timeout")
            return jsonify({
                'error': 'Assistant is taking too long to respond. Please try a simpler question.'
            }), 408
        except Exception as e:
            logger.error(f"[Assistant] Agent error: {e}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': f'Assistant encountered an error: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f"[Assistant] Request error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# ====================== PROJECT MANAGEMENT API ======================
# Multi-Database Architecture: Each project = separate Neo4j database

@app.route('/api/projects', methods=['GET'])
def list_projects():
    """
    List all projects with their statistics.

    Projects are stored as metadata in system database (neo4j).
    Each project has its own separate Neo4j database for complete isolation.
    """
    try:
        logger.info("[API] Fetching all projects")

        if not db_manager:
            return jsonify({'error': 'DatabaseManager not available'}), 500

        # Query project metadata from system database
        query = """
        MATCH (p:Project)
        RETURN p.id as id,
               p.name as name,
               p.description as description,
               p.color as color,
               p.database_name as database_name,
               p.is_active as is_active,
               p.created_at as created_at,
               p.updated_at as updated_at
        ORDER BY p.is_active DESC, p.created_at DESC
        """

        # Query system database for project list
        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            result = session.run(query)
            projects = []

            for record in result:
                database_name = record['database_name']

                # Get stats from the project's actual database
                try:
                    if db_manager.database_exists(database_name):
                        stats = db_manager.get_database_stats(database_name)
                        node_count = stats.get('total_nodes', 0)
                    else:
                        node_count = 0
                        logger.warning(f"Database {database_name} doesn't exist for project {record['id']}")
                except Exception as e:
                    logger.warning(f"Error getting stats for {database_name}: {e}")
                    node_count = 0

                projects.append({
                    'id': record['id'],
                    'name': record['name'],
                    'description': record['description'],
                    'color': record['color'],
                    'database_name': database_name,
                    'is_active': record['is_active'],
                    'created_at': str(record['created_at']) if record['created_at'] else None,
                    'updated_at': str(record['updated_at']) if record['updated_at'] else None,
                    'node_count': node_count
                })

        logger.info(f"[API] Found {len(projects)} projects")
        return jsonify({'projects': projects})

    except Exception as e:
        logger.error(f"[API] Error listing projects: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects', methods=['POST'])
def create_project():
    """
    Create a new project with its own isolated Neo4j database.

    Steps:
    1. Generate database name from project name
    2. Create actual Neo4j database
    3. Initialize database schema (indexes, constraints)
    4. Store project metadata in system database
    """
    try:
        data = request.json
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        color = data.get('color', '#2196F3')

        if not name:
            return jsonify({'error': 'Project name is required'}), 400

        if not db_manager:
            return jsonify({'error': 'DatabaseManager not available'}), 500

        # Generate project ID and database name
        import re
        import uuid
        project_id = re.sub(r'[^a-z0-9_-]', '_', name.lower())
        database_name = db_manager.sanitize_database_name(name)

        # Check if database name already exists
        if db_manager.database_exists(database_name):
            return jsonify({'error': f'A project with similar name already exists (database: {database_name})'}), 400

        logger.info(f"[API] Creating project: {name} (ID: {project_id}, DB: {database_name})")

        # Step 1: Create the actual Neo4j database
        success, error_message = db_manager.create_database(database_name, wait=True)
        if not success:
            detailed_error = error_message or 'Failed to create database'
            logger.error(f"[API] Database creation failed: {detailed_error}")
            return jsonify({'error': detailed_error}), 500

        logger.info(f"[API] Database created: {database_name}")

        # Step 2: Initialize database schema (indexes, constraints)
        db_manager.initialize_database_schema(database_name)
        logger.info(f"[API] Database schema initialized for {database_name}")

        # Step 3: Store project metadata in system database
        query = """
        CREATE (p:Project {
            id: $project_id,
            name: $name,
            description: $description,
            color: $color,
            database_name: $database_name,
            is_active: false,
            created_at: datetime(),
            updated_at: datetime()
        })
        RETURN p
        """

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            result = session.run(query, {
                'project_id': project_id,
                'name': name,
                'description': description,
                'color': color,
                'database_name': database_name
            })

            record = result.single()
            if record:
                project = dict(record['p'])
                project['created_at'] = str(project.get('created_at'))
                project['updated_at'] = str(project.get('updated_at'))

                logger.info(f"[API] Project metadata saved: {project_id}")
                return jsonify({
                    'success': True,
                    'project': project
                })
            else:
                # Rollback: delete the database if metadata creation failed
                logger.error("Failed to save project metadata, rolling back database creation")
                db_manager.drop_database(database_name)
                return jsonify({'error': 'Failed to create project metadata'}), 500

    except Exception as e:
        logger.error(f"[API] Error creating project: {e}")
        logger.error(traceback.format_exc())

        # Attempt cleanup on error
        try:
            if 'database_name' in locals() and db_manager:
                db_manager.drop_database(database_name)
                logger.info(f"Cleaned up failed database: {database_name}")
        except:
            pass

        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update project metadata in system database."""
    try:
        data = request.json
        logger.info(f"[API] Updating project {project_id}")

        # Build update query
        updates = []
        params = {'project_id': project_id}

        if 'name' in data:
            updates.append('p.name = $name')
            params['name'] = data['name']

        if 'description' in data:
            updates.append('p.description = $description')
            params['description'] = data['description']

        if 'color' in data:
            updates.append('p.color = $color')
            params['color'] = data['color']

        # Always update timestamp
        updates.append('p.updated_at = datetime()')

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Update metadata in system database
        query = f"""
        MATCH (p:Project {{id: $project_id}})
        SET {', '.join(updates)}
        RETURN p
        """

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            result = session.run(query, params)
            record = result.single()

            if not record:
                return jsonify({'error': 'Project not found'}), 404

            project = dict(record['p'])
            project['created_at'] = str(project.get('created_at'))
            project['updated_at'] = str(project.get('updated_at'))

        logger.info(f"[API] Project updated: {project_id}")
        return jsonify({
            'success': True,
            'project': project
        })

    except Exception as e:
        logger.error(f"[API] Error updating project: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project - drops the entire Neo4j database and removes metadata."""
    try:
        if project_id == 'default':
            return jsonify({'error': 'Cannot delete default project'}), 400

        logger.info(f"[API] Deleting project {project_id}")

        # Get project details from system database
        check_query = """
        MATCH (p:Project {id: $project_id})
        RETURN p.is_active as is_active, p.database_name as database_name, p.name as name
        """

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            result = session.run(check_query, {'project_id': project_id})
            record = result.single()

            if not record:
                return jsonify({'error': 'Project not found'}), 404

            is_active = record['is_active']
            database_name = record['database_name']
            project_name = record['name']

        # Cannot delete active project
        if is_active:
            return jsonify({
                'error': 'Cannot delete active project. Switch to another project first.'
            }), 400

        # Cannot delete system database
        if database_name in db_manager.RESERVED_NAMES:
            return jsonify({
                'error': f'Cannot delete reserved database: {database_name}'
            }), 400

        # Step 1: Drop the actual Neo4j database
        logger.info(f"[API] Dropping database: {database_name}")
        drop_success = db_manager.drop_database(database_name)

        if not drop_success:
            return jsonify({
                'error': f'Failed to drop database: {database_name}'
            }), 500

        # Step 2: Remove project metadata from system database
        delete_query = """
        MATCH (p:Project {id: $project_id})
        DELETE p
        """

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            session.run(delete_query, {'project_id': project_id})

        logger.info(f"[API] Project deleted: {project_name} (database: {database_name})")
        return jsonify({
            'success': True,
            'message': f'Project "{project_name}" and all its data have been permanently deleted'
        })

    except Exception as e:
        logger.error(f"[API] Error deleting project: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<project_id>/switch', methods=['POST'])
def switch_project(project_id):
    """Switch to a different project - changes active database."""
    try:
        logger.info(f"[API] Switching to project {project_id}")

        # Step 1: Get project details from system database
        get_query = """
        MATCH (p:Project {id: $project_id})
        RETURN p.database_name as database_name, p.name as name, p
        """

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            result = session.run(get_query, {'project_id': project_id})
            record = result.single()

            if not record:
                return jsonify({'error': 'Project not found'}), 404

            database_name = record['database_name']
            project_name = record['name']
            project_node = record['p']

        # Step 2: Verify the database exists
        if not db_manager.database_exists(database_name):
            logger.error(f"[API] Database {database_name} does not exist for project {project_id}")
            return jsonify({
                'error': f'Project database not found: {database_name}'
            }), 500

        # Step 3: Update is_active flags in system database
        update_query = """
        MATCH (p:Project)
        SET p.is_active = (p.id = $project_id)
        WITH p
        WHERE p.id = $project_id
        RETURN p
        """

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            result = session.run(update_query, {'project_id': project_id})
            record = result.single()

            project = dict(record['p'])
            project['created_at'] = str(project.get('created_at'))
            project['updated_at'] = str(project.get('updated_at'))

        # Step 4: Actually switch the active database in Neo4j client
        neo4j_client.set_active_database(database_name)
        logger.info(f"[API] Active database switched to: {database_name}")

        # Step 5: Emit project switched event for WebSocket clients
        socketio.emit('project_switched', {
            'project_id': project_id,
            'project_name': project_name,
            'database_name': database_name
        })

        logger.info(f"[API] Switched to project: {project_name} (database: {database_name})")
        return jsonify({
            'success': True,
            'project': project
        })

    except Exception as e:
        logger.error(f"[API] Error switching project: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<project_id>/stats', methods=['GET'])
def get_project_stats(project_id):
    """Get detailed statistics for a project from its database."""
    try:
        logger.info(f"[API] Fetching stats for project {project_id}")

        # Get project details from system database
        query = """
        MATCH (p:Project {id: $project_id})
        RETURN p.name as name, p.database_name as database_name
        """

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            result = session.run(query, {'project_id': project_id})
            record = result.single()

            if not record:
                return jsonify({'error': 'Project not found'}), 404

            project_name = record['name']
            database_name = record['database_name']

        # Get statistics from the project's actual database
        if db_manager.database_exists(database_name):
            stats = db_manager.get_database_stats(database_name)
        else:
            logger.warning(f"[API] Database {database_name} does not exist, returning zero stats")
            stats = {
                'total_nodes': 0,
                'total_relationships': 0,
                'document_count': 0,
                'claim_count': 0,
                'evidence_count': 0,
                'label_counts': {}
            }

        logger.info(f"[API] Stats for {project_id}: {stats}")
        return jsonify({
            'project_id': project_id,
            'name': project_name,
            'total_nodes': stats['total_nodes'],
            'total_relationships': stats['total_relationships'],
            'document_count': stats['document_count'],
            'claim_count': stats['claim_count'],
            'evidence_count': stats['evidence_count'],
            'label_counts': stats.get('label_counts', {})
        })

    except Exception as e:
        logger.error(f"[API] Error fetching project stats: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/active', methods=['GET'])
def get_active_project():
    """Get the currently active project from system database."""
    try:
        logger.info("[API] Fetching active project")

        # Query system database for active project
        query = """
        MATCH (p:Project {is_active: true})
        RETURN p
        LIMIT 1
        """

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            result = session.run(query, {})
            record = result.single()

            if not record:
                # No active project, activate default project
                logger.info("[API] No active project found, activating default")
                activate_query = """
                MATCH (p:Project {id: 'default'})
                SET p.is_active = true
                RETURN p
                """
                result = session.run(activate_query, {})
                record = result.single()

            if record:
                project = dict(record['p'])
                project['created_at'] = str(project.get('created_at'))
                project['updated_at'] = str(project.get('updated_at'))

                # Ensure Neo4j client is using the correct active database
                database_name = project.get('database_name', db_manager.SYSTEM_DATABASE)
                if neo4j_client.active_database != database_name:
                    logger.info(f"[API] Syncing active database to: {database_name}")
                    neo4j_client.set_active_database(database_name)

                return jsonify({'project': project})
            else:
                logger.error("[API] No default project found in system database")
                return jsonify({'error': 'No active project found'}), 404

    except Exception as e:
        logger.error(f"[API] Error fetching active project: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<project_id>/export', methods=['POST'])
def export_project_markdown(project_id):
    """Export project to markdown files for git-friendly version control."""
    try:
        logger.info(f"[API] Exporting project {project_id} to markdown")

        # Get project details
        query = """
        MATCH (p:Project {id: $project_id})
        RETURN p.name as name, p.database_name as database_name
        """

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            result = session.run(query, {'project_id': project_id})
            record = result.single()

            if not record:
                return jsonify({'error': 'Project not found'}), 404

            project_name = record['name']
            database_name = record['database_name']

        # Initialize export manager
        from research_agent.export_manager import get_export_manager
        export_manager = get_export_manager()

        # Create a temporary database connection for this project's database
        from research_agent.neo4j_database import Neo4jDatabase
        project_db = Neo4jDatabase()
        project_db.database = database_name

        # Perform export
        export_path = export_manager.export_project(
            db=project_db,
            project_name=project_name,
            include_metadata=True
        )

        logger.info(f"[API] Export completed: {export_path}")

        return jsonify({
            'success': True,
            'export_path': str(export_path),
            'project_name': project_name,
            'timestamp': datetime.now().isoformat(),
            'message': f'Project "{project_name}" exported successfully'
        })

    except Exception as e:
        logger.error(f"[API] Error exporting project: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# ====================== NODE DETAILS API ======================

@app.route('/api/nodes/<node_id>/full-details', methods=['GET'])
def get_node_full_details(node_id):
    """Get comprehensive node details including relationships, history, and metadata."""
    try:
        logger.info(f"[API] Fetching full details for node: {node_id}")

        # Get base node data
        query = """
        MATCH (n)
        WHERE id(n) = $node_id OR n.id = $node_id
        RETURN n, labels(n) as labels, id(n) as internal_id
        """

        result = with_app_context(
            lambda: claim_repo.execute_query(query, {'node_id': node_id})
        )

        if not result:
            return jsonify({'error': 'Node not found'}), 404

        node_data = result[0]
        node = node_data['n']
        node_labels = node_data['labels']
        internal_id = node_data['internal_id']

        # Get all properties
        node_props = dict(node)
        node_props['labels'] = node_labels
        node_props['internal_id'] = internal_id

        # Get relationships
        rel_query = """
        MATCH (n)-[r]-(m)
        WHERE id(n) = $node_id
        RETURN type(r) as rel_type,
               properties(r) as rel_props,
               startNode(r) = n as is_outgoing,
               m as related_node,
               labels(m) as related_labels,
               id(m) as related_id
        """

        relationships_result = with_app_context(
            lambda: claim_repo.execute_query(rel_query, {'node_id': internal_id})
        )

        relationships = {}
        for rel in relationships_result:
            rel_type = rel['rel_type']
            if rel_type not in relationships:
                relationships[rel_type] = []

            related = rel['related_node']
            relationships[rel_type].append({
                'type': rel_type,
                'direction': 'outgoing' if rel['is_outgoing'] else 'incoming',
                'properties': rel['rel_props'],
                'related_node': {
                    'id': rel['related_id'],
                    'internal_id': rel['related_id'],
                    'labels': rel['related_labels'],
                    'text': related.get('text', ''),
                    'title': related.get('title', ''),
                    'status': related.get('status', '')
                }
            })

        # Get history/provenance if available
        history = []
        if node_props.get('created_by_agent_id'):
            history.append({
                'timestamp': node_props.get('created_at', 'Unknown'),
                'event': 'Created',
                'agent_id': node_props.get('created_by_agent_id'),
                'agent_type': node_props.get('created_by', 'unknown')
            })

        if node_props.get('discovered_by_agent_id'):
            history.append({
                'timestamp': node_props.get('discovered_at', 'Unknown'),
                'event': 'Discovered',
                'agent_id': node_props.get('discovered_by_agent_id'),
                'agent_type': node_props.get('discovered_by', 'unknown')
            })

        # Compile full details
        full_details = {
            'node': node_props,
            'relationships': relationships,
            'history': history,
            'metadata': {
                'created_at': node_props.get('created_at'),
                'updated_at': node_props.get('updated_at'),
                'version': node_props.get('version', 1)
            }
        }

        logger.info(f"[API] Successfully fetched details for node {node_id}")
        return jsonify(full_details)

    except Exception as e:
        logger.error(f"[API] Error fetching node details: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/nodes/<node_id>/update', methods=['PUT'])
def update_node_properties(node_id):
    """Update editable node properties (confidence, investigation_value, notes)."""
    try:
        data = request.json
        logger.info(f"[API] Updating node {node_id} with data: {data}")

        # Build update query
        updates = []
        params = {'node_id': node_id}

        if 'confidence' in data:
            updates.append('n.confidence = $confidence')
            params['confidence'] = float(data['confidence'])

        if 'investigation_value' in data:
            updates.append('n.investigation_value = $investigation_value')
            params['investigation_value'] = float(data['investigation_value'])

        if 'notes' in data:
            updates.append('n.notes = $notes')
            params['notes'] = data['notes']

        # Always update timestamp
        updates.append('n.updated_at = datetime()')

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        query = f"""
        MATCH (n)
        WHERE id(n) = $node_id OR n.id = $node_id
        SET {', '.join(updates)}
        RETURN n
        """

        result = with_app_context(
            lambda: claim_repo.execute_query(query, params)
        )

        if not result:
            return jsonify({'error': 'Node not found'}), 404

        updated_node = dict(result[0]['n'])

        # Emit update event via WebSocket
        socketio.emit('node_updated', {
            'node_id': node_id,
            'properties': updated_node
        })

        logger.info(f"[API] Successfully updated node {node_id}")
        return jsonify({
            'success': True,
            'node': updated_node
        })

    except Exception as e:
        logger.error(f"[API] Error updating node: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# ============================================================================
# FRAMEWORK MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/frameworks', methods=['GET'])
def list_frameworks():
    """
    Get list of available research frameworks.

    Returns:
        JSON array of framework metadata
    """
    try:
        from backend.frameworks import FrameworkManager

        manager = FrameworkManager()
        frameworks = manager.list_available_frameworks()

        return jsonify({
            'success': True,
            'frameworks': frameworks,
            'current': manager.get_current_framework().name
        })

    except Exception as e:
        logger.error(f"Error listing frameworks: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/framework/current', methods=['GET'])
def get_current_framework():
    """
    Get details of the currently active framework.

    Returns:
        JSON object with framework configuration
    """
    try:
        from backend.frameworks import FrameworkManager

        manager = FrameworkManager()
        framework = manager.get_current_framework()

        return jsonify({
            'success': True,
            'framework': framework.to_dict()
        })

    except Exception as e:
        logger.error(f"Error getting current framework: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/framework/set', methods=['POST'])
def set_framework():
    """
    Set the active research framework.

    Request body:
        {
            "framework_name": "medical_research"
        }

    Returns:
        Success status and new framework details
    """
    try:
        from backend.frameworks import FrameworkManager

        data = request.json
        framework_name = data.get('framework_name')

        if not framework_name:
            return jsonify({'error': 'framework_name is required'}), 400

        manager = FrameworkManager()

        # Validate compatibility
        compatibility = manager.validate_framework_compatibility(framework_name)

        if not compatibility['compatible']:
            # Return warnings but allow switch
            logger.warning(f"Framework compatibility issues: {compatibility['warnings']}")

        # Set framework
        manager.set_framework(framework_name)
        framework = manager.get_current_framework()

        # Emit update via WebSocket
        with app.app_context():
            socketio.emit('framework_changed', {
                'framework_name': framework.name,
                'framework_description': framework.description
            })

        logger.info(f"Framework switched to: {framework_name}")

        return jsonify({
            'success': True,
            'framework': framework.to_dict(),
            'compatibility': compatibility
        })

    except FileNotFoundError as e:
        logger.error(f"Framework not found: {e}")
        return jsonify({'error': f'Framework not found: {str(e)}'}), 404

    except Exception as e:
        logger.error(f"Error setting framework: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/framework/<framework_name>', methods=['GET'])
def get_framework_details(framework_name):
    """
    Get detailed information about a specific framework.

    Args:
        framework_name: Name of framework to retrieve

    Returns:
        Framework configuration details
    """
    try:
        from backend.frameworks import FrameworkManager

        manager = FrameworkManager()
        details = manager.get_framework_details(framework_name)

        return jsonify({
            'success': True,
            'framework': details
        })

    except FileNotFoundError as e:
        logger.error(f"Framework not found: {e}")
        return jsonify({'error': f'Framework not found: {str(e)}'}), 404

    except Exception as e:
        logger.error(f"Error getting framework details: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/framework/upload', methods=['POST'])
def upload_custom_framework():
    """
    Upload a custom framework YAML file.

    Expects multipart/form-data with 'framework' file field.

    Returns:
        Success status and uploaded framework details
    """
    try:
        from backend.frameworks import load_framework, validate_framework
        import yaml

        # Check if file was uploaded
        if 'framework' not in request.files:
            return jsonify({'error': 'No framework file provided'}), 400

        file = request.files['framework']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith('.yaml') and not file.filename.endswith('.yml'):
            return jsonify({'error': 'File must be a YAML file (.yaml or .yml)'}), 400

        # Save to custom frameworks directory
        custom_dir = Path.cwd() / 'custom_frameworks'
        custom_dir.mkdir(exist_ok=True)

        filename = secure_filename(file.filename)
        filepath = custom_dir / filename

        file.save(filepath)
        logger.info(f"Uploaded custom framework to {filepath}")

        # Load and validate
        try:
            framework = load_framework(filepath)
            logger.info(f"Successfully validated custom framework: {framework.name}")

            return jsonify({
                'success': True,
                'framework': framework.to_dict(),
                'filename': filename,
                'message': f'Framework "{framework.name}" uploaded successfully'
            })

        except Exception as validation_error:
            # Remove invalid file
            filepath.unlink(missing_ok=True)
            logger.error(f"Invalid framework file: {validation_error}")
            return jsonify({
                'error': f'Invalid framework file: {str(validation_error)}'
            }), 400

    except Exception as e:
        logger.error(f"Error uploading framework: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/framework/validate', methods=['POST'])
def validate_framework_compatibility():
    """
    Validate if switching to a framework is compatible with current graph.

    Request body:
        {
            "framework_name": "medical_research"
        }

    Returns:
        Compatibility status and warnings
    """
    try:
        from backend.frameworks import FrameworkManager

        data = request.json
        framework_name = data.get('framework_name')

        if not framework_name:
            return jsonify({'error': 'framework_name is required'}), 400

        manager = FrameworkManager()
        compatibility = manager.validate_framework_compatibility(framework_name)

        return jsonify({
            'success': True,
            'compatibility': compatibility
        })

    except Exception as e:
        logger.error(f"Error validating framework compatibility: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# Register workflow routes
try:
    from web_ui.workflow_routes import register_workflow_routes
    register_workflow_routes(app, socketio)
    logger.info("Workflow routes registered successfully")
except Exception as e:
    logger.warning(f"Failed to register workflow routes: {e}")


if __name__ == '__main__':
    print("=" * 80)
    print("RESEARCH GRAPH WEB INTERFACE - LIVE UPDATES ENABLED".center(80))
    print("=" * 80)
    print("\nStarting web server with WebSocket support...")
    print("\nOpen your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    print("=" * 80)

    socketio.run(app, debug=True, port=5000)
