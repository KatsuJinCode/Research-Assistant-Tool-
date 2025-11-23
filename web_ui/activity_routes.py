"""
Activity Feed API Routes for Flask Application.

Provides REST API endpoints for tracking and viewing user activity history.
Tracks all important actions: document uploads, node edits, comments, searches, etc.
"""

import logging
from datetime import datetime, timedelta
from flask import jsonify, request
from typing import Dict, Any, List, Optional
from uuid import uuid4
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

# Global activity tracking (in-memory for local/single-user)
# For production, this would be stored in Neo4j or a separate time-series DB
activity_log: List[Dict[str, Any]] = []
MAX_ACTIVITY_LOG_SIZE = 10000  # Keep last 10k activities


def register_activity_routes(app, db, socketio=None):
    """
    Register activity routes with Flask app.

    Args:
        app: Flask application instance
        db: Neo4j database instance
        socketio: Optional SocketIO instance for real-time updates
    """

    @app.route('/api/activity', methods=['GET'])
    def get_activity_feed():
        """
        Get activity feed with filtering and pagination.

        Query parameters:
        - limit: number of activities to return (default 50)
        - offset: pagination offset (default 0)
        - type: filter by activity type
        - entity_id: filter by entity
        - since: ISO timestamp, only return activities after this time
        """
        try:
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            activity_type = request.args.get('type')
            entity_id = request.args.get('entity_id')
            since = request.args.get('since')

            # Filter activities
            filtered = activity_log.copy()

            if activity_type:
                filtered = [a for a in filtered if a['type'] == activity_type]

            if entity_id:
                filtered = [a for a in filtered if a['entity_id'] == entity_id]

            if since:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                filtered = [a for a in filtered if datetime.fromisoformat(a['created_at'].replace('Z', '+00:00')) > since_dt]

            # Sort by created_at descending (most recent first)
            filtered.sort(key=lambda x: x['created_at'], reverse=True)

            # Paginate
            paginated = filtered[offset:offset + limit]

            # Group by date for UI display
            grouped = _group_activities_by_date(paginated)

            return jsonify({
                'success': True,
                'activities': paginated,
                'grouped': grouped,
                'total': len(filtered),
                'limit': limit,
                'offset': offset
            })

        except Exception as e:
            logger.error(f"Error getting activity feed: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/activity/stats', methods=['GET'])
    def get_activity_stats():
        """
        Get activity statistics for dashboard.

        Returns:
        - Total activities
        - Activities by type
        - Activities by day (last 7 days)
        - Most active entities
        """
        try:
            # Calculate stats
            stats = {
                'total': len(activity_log),
                'by_type': defaultdict(int),
                'by_day': defaultdict(int),
                'most_active_entities': [],
                'recent_activity': []
            }

            # Count by type
            for activity in activity_log:
                stats['by_type'][activity['type']] += 1

            # Count by day (last 7 days)
            today = datetime.utcnow().date()
            for i in range(7):
                day = today - timedelta(days=i)
                day_str = day.isoformat()
                stats['by_day'][day_str] = 0

            for activity in activity_log:
                created_date = datetime.fromisoformat(activity['created_at'].replace('Z', '+00:00')).date()
                if created_date >= today - timedelta(days=6):
                    stats['by_day'][created_date.isoformat()] += 1

            # Most active entities
            entity_counts = defaultdict(int)
            for activity in activity_log:
                key = (activity['entity_id'], activity['entity_type'])
                entity_counts[key] += 1

            most_active = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            stats['most_active_entities'] = [
                {
                    'entity_id': entity_id,
                    'entity_type': entity_type,
                    'activity_count': count
                }
                for (entity_id, entity_type), count in most_active
            ]

            # Recent activity (last hour)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            stats['recent_activity'] = [
                a for a in activity_log
                if datetime.fromisoformat(a['created_at'].replace('Z', '+00:00')) > one_hour_ago
            ]

            # Convert defaultdicts to regular dicts
            stats['by_type'] = dict(stats['by_type'])
            stats['by_day'] = dict(stats['by_day'])

            return jsonify({
                'success': True,
                'stats': stats
            })

        except Exception as e:
            logger.error(f"Error getting activity stats: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/activity/export', methods=['GET'])
    def export_activity():
        """
        Export activity log.

        Query parameters:
        - format: json (default) or csv
        - since: ISO timestamp, only export activities after this time
        """
        try:
            export_format = request.args.get('format', 'json')
            since = request.args.get('since')

            # Filter activities
            filtered = activity_log.copy()

            if since:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                filtered = [a for a in filtered if datetime.fromisoformat(a['created_at'].replace('Z', '+00:00')) > since_dt]

            # Sort by created_at ascending for export
            filtered.sort(key=lambda x: x['created_at'])

            if export_format == 'csv':
                # Convert to CSV
                import csv
                from io import StringIO

                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=[
                    'id', 'type', 'description', 'entity_id', 'entity_type', 'created_at'
                ])
                writer.writeheader()
                for activity in filtered:
                    writer.writerow({
                        'id': activity['id'],
                        'type': activity['type'],
                        'description': activity['description'],
                        'entity_id': activity['entity_id'],
                        'entity_type': activity['entity_type'],
                        'created_at': activity['created_at']
                    })

                return output.getvalue(), 200, {
                    'Content-Type': 'text/csv',
                    'Content-Disposition': f'attachment; filename=activity_log_{datetime.utcnow().strftime("%Y%m%d")}.csv'
                }
            else:
                # Return JSON
                return jsonify({
                    'success': True,
                    'activities': filtered,
                    'count': len(filtered),
                    'exported_at': datetime.utcnow().isoformat()
                })

        except Exception as e:
            logger.error(f"Error exporting activity: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/activity/<activity_id>', methods=['GET'])
    def get_activity_detail(activity_id):
        """Get detailed information about a specific activity."""
        try:
            activity = next((a for a in activity_log if a['id'] == activity_id), None)

            if not activity:
                return jsonify({'success': False, 'error': 'Activity not found'}), 404

            # Enrich with entity data if available
            if activity['entity_id']:
                entity = db.get_node(activity['entity_id'])
                if entity:
                    activity['entity_data'] = entity

            return jsonify({
                'success': True,
                'activity': activity
            })

        except Exception as e:
            logger.error(f"Error getting activity {activity_id}: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/activity/entity/<entity_id>', methods=['GET'])
    def get_entity_activity(entity_id):
        """Get all activities for a specific entity."""
        try:
            entity_activities = [a for a in activity_log if a['entity_id'] == entity_id]
            entity_activities.sort(key=lambda x: x['created_at'], reverse=True)

            return jsonify({
                'success': True,
                'activities': entity_activities,
                'count': len(entity_activities)
            })

        except Exception as e:
            logger.error(f"Error getting entity activity for {entity_id}: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500


# Helper functions

def _group_activities_by_date(activities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group activities by date categories (Today, Yesterday, This Week, etc.)."""
    grouped = {
        'Today': [],
        'Yesterday': [],
        'This Week': [],
        'This Month': [],
        'Older': []
    }

    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    for activity in activities:
        created_date = datetime.fromisoformat(activity['created_at'].replace('Z', '+00:00')).date()

        if created_date == today:
            grouped['Today'].append(activity)
        elif created_date == yesterday:
            grouped['Yesterday'].append(activity)
        elif created_date > week_ago:
            grouped['This Week'].append(activity)
        elif created_date > month_ago:
            grouped['This Month'].append(activity)
        else:
            grouped['Older'].append(activity)

    # Remove empty groups
    return {k: v for k, v in grouped.items() if v}


# Activity tracking function (called from other routes)

def track_activity(db, socketio, activity_type: str, description: str,
                  entity_id: str, entity_type: str, metadata: Dict[str, Any] = None):
    """
    Track an activity in the activity log.

    Args:
        db: Database instance
        socketio: SocketIO instance for real-time updates
        activity_type: Type of activity (document_uploaded, claim_created, etc.)
        description: Human-readable description
        entity_id: ID of the entity involved
        entity_type: Type of entity (document, claim, etc.)
        metadata: Optional additional metadata
    """
    global activity_log

    try:
        activity = {
            'id': str(uuid4()),
            'type': activity_type,
            'description': description,
            'entity_id': entity_id,
            'entity_type': entity_type,
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }

        # Add to log
        activity_log.append(activity)

        # Trim if too large
        if len(activity_log) > MAX_ACTIVITY_LOG_SIZE:
            activity_log = activity_log[-MAX_ACTIVITY_LOG_SIZE:]

        # Emit real-time update
        if socketio:
            socketio.emit('activity_added', activity)

        logger.info(f"Activity tracked: {activity_type} - {description}")

    except Exception as e:
        logger.error(f"Error tracking activity: {e}", exc_info=True)


# Activity type constants for consistency
class ActivityType:
    """Activity type constants."""
    DOCUMENT_UPLOADED = 'document_uploaded'
    DOCUMENT_PROCESSED = 'document_processed'
    CLAIM_CREATED = 'claim_created'
    CLAIM_EDITED = 'claim_edited'
    CLAIM_DELETED = 'claim_deleted'
    NODE_EDITED = 'node_edited'
    COMMENT_ADDED = 'comment_added'
    COMMENT_EDITED = 'comment_edited'
    COMMENT_DELETED = 'comment_deleted'
    PROJECT_CREATED = 'project_created'
    PROJECT_SWITCHED = 'project_switched'
    SEARCH_PERFORMED = 'search_performed'
    REPORT_GENERATED = 'report_generated'
    ANALYSIS_RUN = 'analysis_run'
    WORKFLOW_STARTED = 'workflow_started'
    WORKFLOW_COMPLETED = 'workflow_completed'
    AGENT_SPAWNED = 'agent_spawned'
    AGENT_COMPLETED = 'agent_completed'


# Activity icons for UI display
ACTIVITY_ICONS = {
    ActivityType.DOCUMENT_UPLOADED: '📄',
    ActivityType.DOCUMENT_PROCESSED: '✅',
    ActivityType.CLAIM_CREATED: '💡',
    ActivityType.CLAIM_EDITED: '✏️',
    ActivityType.CLAIM_DELETED: '🗑️',
    ActivityType.NODE_EDITED: '✏️',
    ActivityType.COMMENT_ADDED: '💬',
    ActivityType.COMMENT_EDITED: '✏️',
    ActivityType.COMMENT_DELETED: '🗑️',
    ActivityType.PROJECT_CREATED: '📁',
    ActivityType.PROJECT_SWITCHED: '🔄',
    ActivityType.SEARCH_PERFORMED: '🔍',
    ActivityType.REPORT_GENERATED: '📊',
    ActivityType.ANALYSIS_RUN: '🔬',
    ActivityType.WORKFLOW_STARTED: '⚙️',
    ActivityType.WORKFLOW_COMPLETED: '✓',
    ActivityType.AGENT_SPAWNED: '🤖',
    ActivityType.AGENT_COMPLETED: '✓'
}


def get_activity_icon(activity_type: str) -> str:
    """Get icon for activity type."""
    return ACTIVITY_ICONS.get(activity_type, '•')
