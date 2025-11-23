"""
Comment System API Routes for Flask Application.

Provides REST API endpoints for managing comments on graph nodes.
Supports nested replies, markdown formatting, and full CRUD operations.
"""

import logging
from datetime import datetime
from flask import jsonify, request
from typing import Dict, Any, List, Optional
from uuid import uuid4
import re

logger = logging.getLogger(__name__)


def register_comment_routes(app, db, socketio=None):
    """
    Register comment routes with Flask app.

    Args:
        app: Flask application instance
        db: Neo4j database instance
        socketio: Optional SocketIO instance for real-time updates
    """

    @app.route('/api/comments', methods=['POST'])
    def create_comment():
        """
        Create a new comment on a node.

        Request body:
        {
            "node_id": "node_123",
            "text": "Comment text with **markdown**",
            "parent_comment_id": null  // optional, for replies
        }
        """
        try:
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400

            node_id = data.get('node_id')
            text = data.get('text', '').strip()
            parent_comment_id = data.get('parent_comment_id')

            if not node_id:
                return jsonify({'success': False, 'error': 'node_id is required'}), 400
            if not text:
                return jsonify({'success': False, 'error': 'text is required'}), 400

            # Verify node exists
            node = db.get_node(node_id)
            if not node:
                return jsonify({'success': False, 'error': 'Node not found'}), 404

            # Create comment
            comment_id = str(uuid4())
            timestamp = datetime.utcnow().isoformat()

            comment_data = {
                'id': comment_id,
                'node_id': node_id,
                'text': text,
                'created_at': timestamp,
                'updated_at': timestamp
            }

            # Create Comment node
            db.create_node('Comment', comment_data)

            # Create HAS_COMMENT relationship
            db.create_relationship(node_id, comment_id, 'HAS_COMMENT', {
                'created_at': timestamp
            })

            # If this is a reply, create REPLY_TO relationship
            if parent_comment_id:
                parent_comment = db.get_node(parent_comment_id)
                if parent_comment and parent_comment.get('label') == 'Comment':
                    db.create_relationship(comment_id, parent_comment_id, 'REPLY_TO', {
                        'created_at': timestamp
                    })
                    comment_data['parent_comment_id'] = parent_comment_id

            # Emit real-time update
            if socketio:
                socketio.emit('comment_added', {
                    'comment': comment_data,
                    'node_id': node_id
                })

            # Track activity
            _track_activity(db, socketio, 'comment_added',
                          f'Added comment on {node.get("label", "node")}',
                          node_id, node.get('label', 'Node'),
                          {'comment_id': comment_id, 'text_preview': text[:100]})

            logger.info(f"Created comment {comment_id} on node {node_id}")
            return jsonify({
                'success': True,
                'comment': comment_data
            })

        except Exception as e:
            logger.error(f"Error creating comment: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/comments/node/<node_id>', methods=['GET'])
    def get_node_comments(node_id):
        """
        Get all comments for a node, organized as a thread tree.

        Returns comments with nested replies.
        """
        try:
            # Verify node exists
            node = db.get_node(node_id)
            if not node:
                return jsonify({'success': False, 'error': 'Node not found'}), 404

            # Get all comments for this node
            comments = _get_comments_for_node(db, node_id)

            # Organize into thread tree
            comment_tree = _build_comment_tree(comments)

            return jsonify({
                'success': True,
                'comments': comment_tree,
                'count': len(comments)
            })

        except Exception as e:
            logger.error(f"Error getting comments for node {node_id}: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/comments/<comment_id>', methods=['PUT'])
    def update_comment(comment_id):
        """
        Update an existing comment.

        Request body:
        {
            "text": "Updated comment text"
        }
        """
        try:
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400

            text = data.get('text', '').strip()
            if not text:
                return jsonify({'success': False, 'error': 'text is required'}), 400

            # Get existing comment
            comment = db.get_node(comment_id)
            if not comment or comment.get('label') != 'Comment':
                return jsonify({'success': False, 'error': 'Comment not found'}), 404

            # Update comment
            timestamp = datetime.utcnow().isoformat()
            db.update_node(comment_id, {
                'text': text,
                'updated_at': timestamp
            })

            updated_comment = db.get_node(comment_id)

            # Emit real-time update
            if socketio:
                socketio.emit('comment_updated', {
                    'comment': updated_comment,
                    'node_id': comment.get('node_id')
                })

            # Track activity
            _track_activity(db, socketio, 'comment_edited',
                          f'Edited comment',
                          comment_id, 'Comment',
                          {'text_preview': text[:100]})

            logger.info(f"Updated comment {comment_id}")
            return jsonify({
                'success': True,
                'comment': updated_comment
            })

        except Exception as e:
            logger.error(f"Error updating comment {comment_id}: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/comments/<comment_id>', methods=['DELETE'])
    def delete_comment(comment_id):
        """
        Delete a comment and all its replies.
        """
        try:
            # Get comment
            comment = db.get_node(comment_id)
            if not comment or comment.get('label') != 'Comment':
                return jsonify({'success': False, 'error': 'Comment not found'}), 404

            node_id = comment.get('node_id')

            # Get all reply IDs recursively
            reply_ids = _get_all_reply_ids(db, comment_id)

            # Delete all replies first
            for reply_id in reply_ids:
                db.delete_node(reply_id)

            # Delete the comment itself
            db.delete_node(comment_id)

            # Emit real-time update
            if socketio:
                socketio.emit('comment_deleted', {
                    'comment_id': comment_id,
                    'node_id': node_id,
                    'deleted_reply_ids': reply_ids
                })

            # Track activity
            _track_activity(db, socketio, 'comment_deleted',
                          f'Deleted comment',
                          comment_id, 'Comment',
                          {'deleted_replies': len(reply_ids)})

            logger.info(f"Deleted comment {comment_id} and {len(reply_ids)} replies")
            return jsonify({
                'success': True,
                'deleted_count': 1 + len(reply_ids)
            })

        except Exception as e:
            logger.error(f"Error deleting comment {comment_id}: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/comments/search', methods=['GET'])
    def search_comments():
        """
        Search comments by text.

        Query parameters:
        - q: search query
        - node_id: optional, filter by node
        """
        try:
            query = request.args.get('q', '').strip()
            node_id = request.args.get('node_id')

            if not query:
                return jsonify({'success': False, 'error': 'Search query required'}), 400

            # Search comments
            comments = _search_comments(db, query, node_id)

            return jsonify({
                'success': True,
                'comments': comments,
                'count': len(comments)
            })

        except Exception as e:
            logger.error(f"Error searching comments: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/comments/export', methods=['GET'])
    def export_comments():
        """
        Export all comments for a node or entire graph.

        Query parameters:
        - node_id: optional, export only comments for this node
        - format: json (default) or csv
        """
        try:
            node_id = request.args.get('node_id')
            export_format = request.args.get('format', 'json')

            if node_id:
                comments = _get_comments_for_node(db, node_id)
            else:
                comments = _get_all_comments(db)

            if export_format == 'csv':
                # Convert to CSV
                import csv
                from io import StringIO

                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=['id', 'node_id', 'text', 'created_at', 'updated_at'])
                writer.writeheader()
                for comment in comments:
                    writer.writerow({
                        'id': comment['id'],
                        'node_id': comment.get('node_id', ''),
                        'text': comment['text'],
                        'created_at': comment['created_at'],
                        'updated_at': comment['updated_at']
                    })

                return output.getvalue(), 200, {
                    'Content-Type': 'text/csv',
                    'Content-Disposition': f'attachment; filename=comments_{node_id or "all"}_{datetime.utcnow().strftime("%Y%m%d")}.csv'
                }
            else:
                # Return JSON
                return jsonify({
                    'success': True,
                    'comments': comments,
                    'count': len(comments),
                    'exported_at': datetime.utcnow().isoformat()
                })

        except Exception as e:
            logger.error(f"Error exporting comments: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500


# Helper functions

def _get_comments_for_node(db, node_id: str) -> List[Dict[str, Any]]:
    """Get all comments for a specific node."""
    comments = []

    # Find all comments with HAS_COMMENT relationship
    try:
        # Get all nodes with HAS_COMMENT relationship from the target node
        result = db.graph.edges(node_id, data=True)
        for source, target, data in result:
            if data.get('type') == 'HAS_COMMENT':
                comment = db.get_node(target)
                if comment and comment.get('label') == 'Comment':
                    comments.append(comment)
    except Exception as e:
        logger.error(f"Error getting comments for node {node_id}: {e}")

    return comments


def _build_comment_tree(comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build a tree structure from flat comment list."""
    comment_map = {c['id']: {**c, 'replies': []} for c in comments}
    root_comments = []

    for comment in comments:
        comment_obj = comment_map[comment['id']]

        # Find parent if this is a reply
        parent_id = None
        # Check for REPLY_TO relationships
        # This would need to be implemented in the database layer
        # For now, assume parent_comment_id is stored in the comment properties
        parent_id = comment.get('parent_comment_id')

        if parent_id and parent_id in comment_map:
            comment_map[parent_id]['replies'].append(comment_obj)
        else:
            root_comments.append(comment_obj)

    return root_comments


def _get_all_reply_ids(db, comment_id: str) -> List[str]:
    """Recursively get all reply IDs for a comment."""
    reply_ids = []

    # Find all comments that have REPLY_TO relationship to this comment
    try:
        result = db.graph.in_edges(comment_id, data=True)
        for source, target, data in result:
            if data.get('type') == 'REPLY_TO':
                reply_ids.append(source)
                # Recursively get replies to this reply
                reply_ids.extend(_get_all_reply_ids(db, source))
    except Exception as e:
        logger.error(f"Error getting reply IDs for comment {comment_id}: {e}")

    return reply_ids


def _search_comments(db, query: str, node_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search comments by text query."""
    results = []

    # Get comments to search
    if node_id:
        comments = _get_comments_for_node(db, node_id)
    else:
        comments = _get_all_comments(db)

    # Simple text search (case-insensitive)
    query_lower = query.lower()
    for comment in comments:
        if query_lower in comment.get('text', '').lower():
            # Add context snippet
            text = comment['text']
            idx = text.lower().find(query_lower)
            start = max(0, idx - 50)
            end = min(len(text), idx + len(query) + 50)
            snippet = text[start:end]
            if start > 0:
                snippet = '...' + snippet
            if end < len(text):
                snippet = snippet + '...'

            comment['snippet'] = snippet
            results.append(comment)

    return results


def _get_all_comments(db) -> List[Dict[str, Any]]:
    """Get all comments in the database."""
    comments = []

    try:
        # Find all Comment nodes
        comments = db.find_nodes('Comment')
    except Exception as e:
        logger.error(f"Error getting all comments: {e}")

    return comments


def _track_activity(db, socketio, activity_type: str, description: str,
                   entity_id: str, entity_type: str, metadata: Dict[str, Any] = None):
    """Track activity for the activity feed."""
    try:
        # Import here to avoid circular dependency
        from web_ui.activity_routes import track_activity
        track_activity(db, socketio, activity_type, description, entity_id, entity_type, metadata)
    except Exception as e:
        logger.warning(f"Failed to track activity: {e}")
