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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'research-assistant-secret-key'
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*")
db = Neo4jDatabase()  # Keep for backward compatibility during migration

# Document processing queue - FIFO queue to prevent interruption
import queue
import threading

processing_queue = queue.Queue()
processing_lock = threading.Lock()
is_processing = False

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


def process_queue_worker():
    """Background worker that processes documents from queue one at a time."""
    global is_processing

    while True:
        try:
            # Block until an item is available
            queue_item = processing_queue.get(block=True)

            if queue_item is None:  # Poison pill to stop worker
                break

            filepath, filename = queue_item

            with processing_lock:
                is_processing = True

            logger.info(f"[QUEUE] Starting processing: {filename}")

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
                    socketio.sleep(0)
                    with app.app_context():
                        socketio.emit('processing_update', {
                            'message': message,
                            'progress': progress,
                            'data': data
                        })

                processor = LiveDocumentProcessor(progress_callback=progress_callback)
                doc_id = processor.process_document_live(filepath)

                logger.info(f"[QUEUE] Completed: {filename} -> {doc_id}")

                with app.app_context():
                    socketio.emit('document_processed', {'document_id': doc_id})

            except Exception as e:
                logger.error(f"[QUEUE] Error processing {filename}: {e}")
                logger.error(traceback.format_exc())
                with app.app_context():
                    socketio.emit('processing_error', {'error': str(e), 'filename': filename})

            finally:
                processing_queue.task_done()

                # Check if queue is empty
                with processing_lock:
                    if processing_queue.empty():
                        is_processing = False

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
    """Get overall graph statistics."""
    stats = db.stats()

    # Get research stats
    agent_tracker = AgentTracker()
    research_stats = agent_tracker.get_research_stats(db)

    return jsonify({
        'nodes': stats['total_nodes'],
        'relationships': stats['total_relationships'],
        'node_types': stats['node_labels'],
        'research': research_stats
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


@app.route('/api/full-graph')
def get_full_graph():
    """Get complete hierarchical graph with arbitrary depth support."""

    # Fetch all data using repositories
    documents = doc_repo.get_all_documents_simple()
    claims = claim_repo.get_all_claims_with_children()
    doc_claims = doc_repo.get_all_document_claim_relationships()
    evidence_data = claim_repo.get_all_claim_evidence_relationships()
    semantic_links = claim_repo.get_all_semantic_relationships()

    # Build document-claim mapping
    doc_claim_map = {dc['doc_id']: dc['claim_ids'] for dc in doc_claims}

    # Build evidence mapping
    evidence_map = {ev['claim_id']: ev['evidence_list'] for ev in evidence_data}

    # Structure response
    response = []
    for doc in documents:
        doc_id = doc['id']

        # Get claims for this document
        doc_claim_ids = doc_claim_map.get(doc_id, [])

        # Separate super-claims and regular claims
        super_claims = []
        all_claims = []

        for claim in claims:
            if claim['id'] in doc_claim_ids:
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
                    'child_ids': [cid for cid in claim['child_ids'] if cid]  # Filter None
                }

                if claim['is_super_claim']:
                    super_claims.append(claim_data)
                all_claims.append(claim_data)

        response.append({
            'doc_id': doc_id,
            'doc_title': doc['title'],
            'doc_status': doc['status'],
            'super_claims': super_claims,
            'all_claims': all_claims,  # New: all claims regardless of depth
            'evidence': evidence_map,
            'semantic_links': semantic_links  # Cross-document semantic relationships
        })

    return jsonify(response)


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
        processing_queue.put((filepath, filename))
        queue_position = processing_queue.qsize()

        logger.info(f"[QUEUE] User upload added to queue: {filename} (position: {queue_position})")

        # Emit queue update
        with app.app_context():
            socketio.emit('queue_update', {
                'processing': None if not is_processing else 'unknown',
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

        # Get pending document details
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

        # Update status to approved
        update_query = """
        MATCH (d:PendingDocument {id: $approval_id})
        SET d.status = 'approved', d.approved_at = datetime()
        """
        db.execute_query(update_query, {'approval_id': approval_id})

        # Add to processing queue
        processing_queue.put((filepath, filename))
        queue_position = processing_queue.qsize()

        logger.info(f"[APPROVAL] Document approved and queued: {filename}")

        # Emit updates
        with app.app_context():
            socketio.emit('document_approved', {
                'approval_id': approval_id,
                'filename': filename
            })
            socketio.emit('queue_update', {
                'processing': None if not is_processing else 'unknown',
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
                    RETURN d.id as id, d.filename as filename, d.filepath as filepath
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

                            # Add to processing queue
                            processing_queue.put((doc['filepath'], doc['filename']))
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

                            # Add to processing queue
                            processing_queue.put((doc['filepath'], doc['filename']))

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


if __name__ == '__main__':
    print("=" * 80)
    print("RESEARCH GRAPH WEB INTERFACE - LIVE UPDATES ENABLED".center(80))
    print("=" * 80)
    print("\nStarting web server with WebSocket support...")
    print("\nOpen your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    print("=" * 80)

    socketio.run(app, debug=True, port=5000)
