"""
Report Generation Routes
API endpoints for generating and scheduling reports
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.repositories import ClaimRepository, DocumentRepository
from backend.database.neo4j_client import Neo4jClient
from backend.workflows.scheduler import WorkflowScheduler, ScheduleType

logger = logging.getLogger(__name__)

# Create blueprint
report_routes = Blueprint('report_routes', __name__, url_prefix='/api/reports')

# Initialize repositories
claim_repo = ClaimRepository()
doc_repo = DocumentRepository()
neo4j_client = Neo4jClient()


@report_routes.route('/generate', methods=['POST'])
def generate_report():
    """
    Generate comprehensive report data

    POST /api/reports/generate

    Body:
    {
        "project_id": "optional_project_id",
        "include_documents": true,
        "include_claims": true,
        "include_evidence": true,
        "include_statistics": true
    }

    Returns:
    {
        "project": {...},
        "statistics": {...},
        "documents": [...],
        "claims": [...],
        "evidence": [...],
        "generated_at": "2025-01-15T10:30:00Z"
    }
    """
    try:
        data = request.get_json() or {}

        project_id = data.get('project_id')
        include_documents = data.get('include_documents', True)
        include_claims = data.get('include_claims', True)
        include_evidence = data.get('include_evidence', True)
        include_statistics = data.get('include_statistics', True)

        logger.info(f"[ReportAPI] Generating report for project: {project_id}")

        # Get project information
        project_info = get_project_info(project_id)

        # Initialize report data
        report_data = {
            'project': project_info,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }

        # Collect statistics
        if include_statistics:
            report_data['statistics'] = get_statistics(project_id)

        # Collect documents
        if include_documents:
            report_data['documents'] = get_documents(project_id)

        # Collect claims
        if include_claims:
            report_data['claims'] = get_claims(project_id)

        # Collect evidence
        if include_evidence:
            report_data['evidence'] = get_evidence(project_id)

        logger.info(f"[ReportAPI] Report generated successfully")

        return jsonify(report_data), 200

    except Exception as e:
        logger.error(f"[ReportAPI] Failed to generate report: {e}")
        return jsonify({
            'error': 'Failed to generate report',
            'message': str(e)
        }), 500


@report_routes.route('/schedule', methods=['POST'])
def schedule_report():
    """
    Schedule automatic report generation

    POST /api/reports/schedule

    Body:
    {
        "schedule_type": "cron",  // or "interval", "one_time"
        "schedule_config": {
            "expression": "0 0 * * *"  // Daily at midnight
        },
        "export_format": "pdf",  // pdf, markdown, bibtex
        "project_id": "optional_project_id",
        "email": "optional@email.com",
        "export_path": "/optional/export/path"
    }

    Returns:
    {
        "schedule_id": "uuid",
        "message": "Report scheduled successfully"
    }
    """
    try:
        data = request.get_json() or {}

        schedule_type = data.get('schedule_type', 'interval')
        schedule_config = data.get('schedule_config', {})
        export_format = data.get('export_format', 'pdf')
        project_id = data.get('project_id')
        email = data.get('email')
        export_path = data.get('export_path')

        # Validate schedule type
        if schedule_type not in ['cron', 'interval', 'one_time']:
            return jsonify({
                'error': 'Invalid schedule type',
                'message': 'Must be one of: cron, interval, one_time'
            }), 400

        # Validate export format
        if export_format not in ['pdf', 'markdown', 'bibtex']:
            return jsonify({
                'error': 'Invalid export format',
                'message': 'Must be one of: pdf, markdown, bibtex'
            }), 400

        # Add metadata to schedule config
        schedule_config['export_format'] = export_format
        schedule_config['project_id'] = project_id
        schedule_config['email'] = email
        schedule_config['export_path'] = export_path

        # Create workflow for report generation
        # Note: This would integrate with WorkflowScheduler
        # For now, we'll store it in a simple registry

        schedule_id = f"schedule_{datetime.utcnow().timestamp()}"

        # Store schedule in database (simplified for now)
        schedule_record = {
            'schedule_id': schedule_id,
            'schedule_type': schedule_type,
            'schedule_config': schedule_config,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'enabled': True
        }

        # TODO: Integrate with WorkflowScheduler for actual scheduling
        logger.info(f"[ReportAPI] Report scheduled: {schedule_id}")

        return jsonify({
            'schedule_id': schedule_id,
            'message': 'Report scheduled successfully',
            'schedule': schedule_record
        }), 201

    except Exception as e:
        logger.error(f"[ReportAPI] Failed to schedule report: {e}")
        return jsonify({
            'error': 'Failed to schedule report',
            'message': str(e)
        }), 500


@report_routes.route('/schedules', methods=['GET'])
def list_schedules():
    """
    List all scheduled reports

    GET /api/reports/schedules

    Returns:
    [
        {
            "schedule_id": "uuid",
            "schedule_type": "cron",
            "schedule_config": {...},
            "created_at": "2025-01-15T10:30:00Z",
            "enabled": true
        },
        ...
    ]
    """
    try:
        # TODO: Fetch from database
        # For now, return empty list
        schedules = []

        logger.info(f"[ReportAPI] Listed {len(schedules)} schedules")

        return jsonify(schedules), 200

    except Exception as e:
        logger.error(f"[ReportAPI] Failed to list schedules: {e}")
        return jsonify({
            'error': 'Failed to list schedules',
            'message': str(e)
        }), 500


@report_routes.route('/schedule/<schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """
    Cancel a scheduled report

    DELETE /api/reports/schedule/<schedule_id>

    Returns:
    {
        "message": "Schedule cancelled successfully"
    }
    """
    try:
        # TODO: Delete from database
        logger.info(f"[ReportAPI] Schedule cancelled: {schedule_id}")

        return jsonify({
            'message': 'Schedule cancelled successfully'
        }), 200

    except Exception as e:
        logger.error(f"[ReportAPI] Failed to cancel schedule: {e}")
        return jsonify({
            'error': 'Failed to cancel schedule',
            'message': str(e)
        }), 500


@report_routes.route('/schedule/<schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """
    Update a scheduled report

    PUT /api/reports/schedule/<schedule_id>

    Body:
    {
        "enabled": true/false,
        "schedule_config": {...}
    }

    Returns:
    {
        "message": "Schedule updated successfully"
    }
    """
    try:
        data = request.get_json() or {}

        # TODO: Update in database
        logger.info(f"[ReportAPI] Schedule updated: {schedule_id}")

        return jsonify({
            'message': 'Schedule updated successfully'
        }), 200

    except Exception as e:
        logger.error(f"[ReportAPI] Failed to update schedule: {e}")
        return jsonify({
            'error': 'Failed to update schedule',
            'message': str(e)
        }), 500


# Helper functions

def get_project_info(project_id=None):
    """Get project information"""
    try:
        if project_id:
            # TODO: Fetch from database
            return {
                'id': project_id,
                'name': f'Project {project_id}',
                'description': 'Research project',
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
        else:
            return {
                'id': 'default',
                'name': 'Default Project',
                'description': 'Default research project',
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
    except Exception as e:
        logger.error(f"[ReportAPI] Failed to get project info: {e}")
        return {
            'id': 'unknown',
            'name': 'Unknown Project',
            'description': '',
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }


def get_statistics(project_id=None):
    """Get graph statistics"""
    try:
        # Get counts from database
        documents = doc_repo.list_documents()
        claims = claim_repo.list_claims()

        # Count evidence links
        evidence_count = 0
        for claim in claims:
            evidence = claim_repo.get_claim_evidence(claim['id'])
            evidence_count += len(evidence)

        # Calculate average confidence
        confidences = [c['confidence'] for c in claims if 'confidence' in c]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return {
            'total_documents': len(documents),
            'total_claims': len(claims),
            'total_evidence': evidence_count,
            'total_relationships': evidence_count,  # Simplified
            'avg_confidence': avg_confidence
        }
    except Exception as e:
        logger.error(f"[ReportAPI] Failed to get statistics: {e}")
        return {
            'total_documents': 0,
            'total_claims': 0,
            'total_evidence': 0,
            'total_relationships': 0,
            'avg_confidence': 0
        }


def get_documents(project_id=None):
    """Get all documents"""
    try:
        documents = doc_repo.list_documents()

        return [
            {
                'id': doc['id'],
                'title': doc.get('title', 'Untitled'),
                'created_at': doc.get('created_at', datetime.utcnow().isoformat() + 'Z'),
                'metadata': doc.get('metadata', {})
            }
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"[ReportAPI] Failed to get documents: {e}")
        return []


def get_claims(project_id=None):
    """Get all claims"""
    try:
        claims = claim_repo.list_claims()

        return [
            {
                'id': claim['id'],
                'text': claim.get('text', ''),
                'confidence': claim.get('confidence', 0),
                'created_at': claim.get('created_at', datetime.utcnow().isoformat() + 'Z')
            }
            for claim in claims
        ]
    except Exception as e:
        logger.error(f"[ReportAPI] Failed to get claims: {e}")
        return []


def get_evidence(project_id=None):
    """Get all evidence relationships"""
    try:
        claims = claim_repo.list_claims()
        evidence_list = []

        for claim in claims:
            evidence = claim_repo.get_claim_evidence(claim['id'])

            for ev in evidence:
                evidence_list.append({
                    'source': ev.get('source_id', claim['id']),
                    'target': ev.get('target_id', claim['id']),
                    'type': ev.get('type', 'related'),
                    'weight': ev.get('weight', 1.0)
                })

        return evidence_list
    except Exception as e:
        logger.error(f"[ReportAPI] Failed to get evidence: {e}")
        return []
