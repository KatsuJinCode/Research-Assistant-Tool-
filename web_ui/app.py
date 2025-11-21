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
    """Handle file upload and start processing."""
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

    # Add to processing queue instead of starting immediately
    processing_queue.put((filepath, filename))
    queue_position = processing_queue.qsize()

    logger.info(f"[QUEUE] Added to queue: {filename} (position: {queue_position})")

    # Emit queue update
    with app.app_context():
        socketio.emit('queue_update', {
            'processing': None if not is_processing else 'unknown',
            'queue_size': queue_position
        })

    return jsonify({
        'status': 'queued',
        'filename': filename,
        'queue_position': queue_position
    })


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
