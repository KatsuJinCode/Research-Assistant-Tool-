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

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research_agent.neo4j_database import Neo4jDatabase
from research_agent.graph_enrichment import (
    EvidenceManager,
    AgentTracker,
    CitationNetwork
)
from web_ui.document_processor import LiveDocumentProcessor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'research-assistant-secret-key'
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*")
db = Neo4jDatabase()


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
    """Get full details for a specific claim."""
    query = """
    MATCH (c:Claim {id: $claim_id})

    // Get child claims
    OPTIONAL MATCH (c)-[:PARENT_OF]->(child:Claim)

    // Get supporting claims
    OPTIONAL MATCH (c)<-[:SUPPORTS]-(supporter:Claim)

    // Get evidence
    OPTIONAL MATCH (c)<-[r_ev:SUPPORTS|CONTRADICTS]-(e:Evidence)

    // Get source locations
    OPTIONAL MATCH (c)-[:EXTRACTED_FROM]->(s:Sentence)-[:IN_DOCUMENT]->(d:Document)

    // Get research results
    OPTIONAL MATCH (res:ResearchResult)-[:INVESTIGATES]->(c)
    OPTIONAL MATCH (res)-[:PERFORMED_BY]->(a:Agent)

    RETURN c.id as id,
           c.text as text,
           c.summary as summary,
           c.specificity_score as specificity,
           c.strength as strength,
           c.compression_ratio as compression_ratio,
           c.qualifiers_preserved as qualifiers_preserved,
           collect(DISTINCT {id: child.id, text: child.text, summary: child.summary, specificity: child.specificity_score}) as children,
           collect(DISTINCT {id: supporter.id, text: supporter.text, summary: supporter.summary}) as supporters,
           collect(DISTINCT {
               title: e.title,
               type: type(r_ev),
               strength: r_ev.strength,
               url: e.url
           }) as evidence,
           collect(DISTINCT {
               page: s.page,
               line: s.start_line,
               sentence: s.text,
               document: d.title
           }) as sources,
           collect(DISTINCT {
               agent: a.name,
               findings: res.findings,
               confidence: res.confidence,
               status: res.status
           }) as research
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query, claim_id=claim_id)
        record = result.single()

        if not record:
            return jsonify({'error': 'Claim not found'}), 404

        claim = dict(record)

        # Clean up None values
        claim['children'] = [c for c in claim['children'] if c.get('id')]
        claim['supporters'] = [s for s in claim['supporters'] if s.get('id')]
        claim['evidence'] = [e for e in claim['evidence'] if e.get('title')]
        claim['sources'] = [s for s in claim['sources'] if s.get('page')]
        claim['research'] = [r for r in claim['research'] if r.get('agent')]

        return jsonify(claim)


@app.route('/api/investigate-claim', methods=['POST'])
def investigate_claim():
    """Spawn an agent to investigate a claim."""
    data = request.json
    claim_id = data.get('claim_id')
    investigation_type = data.get('type', 'support')  # 'support' or 'contradict'

    if not claim_id:
        return jsonify({'error': 'claim_id required'}), 400

    # Get claim
    query = "MATCH (c:Claim {id: $claim_id}) RETURN c.text as text"
    with db.driver.session(database=db.database) as session:
        result = session.run(query, claim_id=claim_id)
        record = result.single()
        if not record:
            return jsonify({'error': 'Claim not found'}), 404
        claim_text = record['text']

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
    """Get complete hierarchical graph: Documents -> Root Claims -> Sub-claims -> Evidence."""
    query = """
    // Get Documents
    MATCH (d:Document)

    // Get root claims (no parent)
    OPTIONAL MATCH (d)-[:CONTAINS_CLAIM]->(root:Claim)
    WHERE root.is_optimal = true AND NOT ()-[:PARENT_OF]->(root)

    // Get child claims
    OPTIONAL MATCH (root)-[:PARENT_OF]->(child:Claim)

    // Get evidence
    OPTIONAL MATCH (root)<-[r_ev:SUPPORTS|CONTRADICTS]-(e:Evidence)
    OPTIONAL MATCH (child)<-[r_ev_child:SUPPORTS|CONTRADICTS]-(e_child:Evidence)

    RETURN
        d.id as doc_id,
        d.title as doc_title,
        collect(DISTINCT {
            id: root.id,
            text: root.text,
            summary: root.summary,
            normalized: root.normalized,
            specificity: root.specificity_score
        }) as root_claims,
        collect(DISTINCT {
            id: child.id,
            parent_id: root.id,
            text: child.text,
            summary: child.summary,
            normalized: child.normalized,
            specificity: child.specificity_score
        }) as child_claims,
        collect(DISTINCT {
            id: e.id,
            claim_id: root.id,
            title: e.title,
            type: type(r_ev),
            url: e.url
        }) as evidence
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query)
        records = [dict(record) for record in result]

    # Clean up None values
    for record in records:
        record['root_claims'] = [c for c in record['root_claims'] if c.get('id')]
        record['child_claims'] = [c for c in record['child_claims'] if c.get('id')]
        record['evidence'] = [e for e in record['evidence'] if e.get('id')]

    return jsonify(records)


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

    # Start processing in background thread
    def process_with_updates(filepath):
        def progress_callback(message, progress, data):
            # Emit to all connected clients
            socketio.emit('processing_update', {
                'message': message,
                'progress': progress,
                'data': data
            })

        processor = LiveDocumentProcessor(progress_callback)
        processor.process_document(filepath)

    thread = threading.Thread(target=process_with_updates, args=(filepath,))
    thread.start()

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
    """Delete document and all its associated claims."""
    query = """
    // Find document and all connected claims
    MATCH (d:Document {id: $doc_id})
    OPTIONAL MATCH (d)-[:CONTAINS_CLAIM]->(c:Claim)

    // Delete all relationships and nodes
    DETACH DELETE d, c

    RETURN count(d) as deleted_docs, count(c) as deleted_claims
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query, doc_id=doc_id)
        record = result.single()

    return jsonify({
        'status': 'deleted',
        'deleted_documents': record['deleted_docs'],
        'deleted_claims': record['deleted_claims']
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
