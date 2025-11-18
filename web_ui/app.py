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

# Register WebSocket event emitter callback for real-time updates
RepositoryEventEmitter.set_emit_callback(socketio.emit)

# Initialize repositories
claim_repo = ClaimRepository()
doc_repo = DocumentRepository()


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/root-claims')
def get_root_claims():
    """Get top-level (root) claims."""
    query = """
    MATCH (c:Claim)
    WHERE c.is_optimal = true AND NOT ()-[:PARENT_OF]->(c)
    RETURN c.id as id,
           c.text as text,
           c.summary as summary,
           c.specificity_score as specificity,
           c.information_content as uniqueness,
           c.compression_ratio as compression_ratio,
           c.qualifiers_preserved as qualifiers_preserved
    ORDER BY c.specificity_score ASC
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query)
        claims = [dict(record) for record in result]

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

    # Get all documents
    doc_query = """
    MATCH (d:Document)
    RETURN d.id as id, d.title as title, d.status as status
    """

    # Get all claims with their relationships (supports arbitrary depth)
    # Note: Using PARENT_OF for hierarchical relationships (matches actual schema)
    claims_query = """
    MATCH (c:Claim)
    OPTIONAL MATCH (c)-[r:PARENT_OF]->(child:Claim)
    RETURN
        c.id as id,
        c.text as text,
        c.summary as summary,
        c.status as status,
        c.disposition as disposition,
        c.quality_score as quality_score,
        c.claim_type as claim_type,
        c.confidence as confidence,
        coalesce(c.is_super_claim, false) as is_super_claim,
        collect(child.id) as child_ids
    """

    # Get document-claim relationships
    doc_claim_query = """
    MATCH (d:Document)-[:CONTAINS_CLAIM]->(c:Claim)
    RETURN d.id as doc_id, collect(c.id) as claim_ids
    """

    # Get evidence relationships
    evidence_query = """
    MATCH (c:Claim)<-[r:SUPPORTS|CONTRADICTS]-(e:Evidence)
    RETURN
        c.id as claim_id,
        collect({
            id: e.id,
            title: e.title,
            type: type(r),
            url: e.url
        }) as evidence_list
    """

    with db.driver.session(database=db.database) as session:
        # Fetch all data
        documents = [dict(r) for r in session.run(doc_query)]
        claims = [dict(r) for r in session.run(claims_query)]
        doc_claims = [dict(r) for r in session.run(doc_claim_query)]
        evidence_data = [dict(r) for r in session.run(evidence_query)]

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
            'evidence': evidence_map
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

    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Only PDF files supported'}), 400

    # Save file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Start processing in background task (must use socketio.start_background_task for eventlet compatibility)
    def process_with_updates(filepath):
        try:
            def progress_callback(message, progress, data):
                # Handle progress being None (for stage events that don't have overall progress)
                if progress is not None:
                    logger.info(f"[PROGRESS {progress:.0f}%] {message}")
                else:
                    logger.info(f"{message}")
                socketio.sleep(0)  # Yield to eventlet event loop before emitting
                socketio.emit('processing_update', {
                    'message': message,
                    'progress': progress,
                    'data': data
                })
                socketio.sleep(0)  # Yield again after emitting to allow event delivery
                if progress is not None:
                    logger.debug(f"Emitted processing_update: {progress:.0f}%")
                else:
                    logger.debug(f"Emitted processing_update: {message}")

            logger.info(f"Starting background processing for: {filepath}")
            processor = LiveDocumentProcessor(progress_callback)
            doc_id = processor.process_document(filepath)
            logger.info(f"Background processing completed: {doc_id}")

            # Emit completion
            socketio.emit('document_processed', {'document_id': doc_id})

        except Exception as e:
            logger.error(f"BACKGROUND THREAD ERROR: {e}")
            logger.error(traceback.format_exc())
            socketio.emit('processing_error', {'error': str(e)})

    # CRITICAL: Use socketio.start_background_task() instead of threading.Thread()
    # This ensures the task runs in the eventlet greenthread context where Socket.IO events work
    socketio.start_background_task(process_with_updates, filepath)

    return jsonify({
        'status': 'processing_started',
        'filename': filename
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
    query = """
    // Find document
    MATCH (d:Document {id: $doc_id})

    // Find all claims ONLY connected to this document
    OPTIONAL MATCH (d)-[:CONTAINS_CLAIM]->(root:Claim)
    OPTIONAL MATCH (root)-[:PARENT_OF*]->(child:Claim)

    // Collect all claims to delete
    WITH d, collect(DISTINCT root) + collect(DISTINCT child) as all_claims

    // Delete only the claims and document (DETACH handles relationships)
    FOREACH (claim IN all_claims | DETACH DELETE claim)
    DETACH DELETE d

    RETURN 1 as deleted
    """

    with db.driver.session(database=db.database) as session:
        session.run(query, doc_id=doc_id)

    return jsonify({
        'status': 'deleted',
        'message': 'Document and owned claims deleted'
    })


@app.route('/api/clear-all', methods=['DELETE'])
def clear_all():
    """Clear all data from the database."""
    query = """
    MATCH (n)
    DETACH DELETE n
    """

    with db.driver.session(database=db.database) as session:
        session.run(query)

    return jsonify({
        'status': 'cleared',
        'message': 'All data cleared from database'
    })


if __name__ == '__main__':
    print("=" * 80)
    print("RESEARCH GRAPH WEB INTERFACE - LIVE UPDATES ENABLED".center(80))
    print("=" * 80)
    print("\nStarting web server with WebSocket support...")
    print("\nOpen your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    print("=" * 80)

    socketio.run(app, debug=True, port=5000)
