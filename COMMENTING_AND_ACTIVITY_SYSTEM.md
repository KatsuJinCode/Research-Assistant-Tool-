# Commenting System and Activity Feed

## Overview

This document describes the comprehensive commenting system and activity feed implementation for the Research Assistant Tool. These features enhance collaboration and provide visibility into system activities for the local/single-user version.

## Features Implemented

### 1. Commenting System

#### Core Features
- **Add comments to any node** (documents, claims, evidence)
- **Rich text support** with Markdown formatting
- **Nested reply threads** for discussions
- **Edit and delete** your own comments
- **Search within comments** for quick navigation
- **Export comments** with reports (CSV/JSON)

#### Database Schema (Neo4j)

```cypher
# Comment Node
(:Comment {
  id: 'comment_uuid',
  node_id: 'node_123',
  text: 'Comment text with **markdown**',
  created_at: timestamp(),
  updated_at: timestamp()
})

# Relationships
(Node)-[:HAS_COMMENT]->(Comment)
(Comment)-[:REPLY_TO]->(ParentComment)
```

#### UI Components

**Location**: Property Viewer → Comments Tab

Features:
- Markdown editor with live preview
- Nested comment threads with indentation
- Reply, edit, and delete buttons on each comment
- Comment count badge on tab
- Search functionality
- Export to CSV/JSON

#### Backend API Endpoints

```
POST   /api/comments              # Create comment
GET    /api/comments/node/<id>    # Get comments for node
PUT    /api/comments/<id>         # Update comment
DELETE /api/comments/<id>         # Delete comment (and replies)
GET    /api/comments/search       # Search comments
GET    /api/comments/export       # Export comments
```

#### Usage Examples

**Add a Comment:**
```javascript
// Via API
fetch('/api/comments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        node_id: 'node_123',
        text: 'This is a great claim! **Bold** and *italic* text supported.',
        parent_comment_id: null  // or ID for replies
    })
})

// Via UI
1. Click on any node in the graph
2. Open Property Viewer
3. Click "Comments" tab
4. Type your comment (Markdown supported)
5. Click "Add Comment"
```

**Reply to a Comment:**
```javascript
// Click the reply button (💬) on any comment
// The textarea will focus with "Replying to..." indicator
```

**Search Comments:**
```javascript
CommentSystem.searchComments('keyword')
// Results show matching comments with context snippets
```

### 2. Activity Feed

#### Core Features
- **Timeline of all actions** in the system
- **Real-time updates** via WebSocket
- **Filter by type, date range, entity**
- **Activity statistics dashboard**
- **Export activity log** (CSV/JSON)
- **Navigate to entities** by clicking activities

#### Activity Types Tracked

```javascript
// Document Operations
DOCUMENT_UPLOADED       - File uploaded to system
DOCUMENT_PROCESSED      - Document processing completed

// Claim Operations
CLAIM_CREATED          - New claim extracted
CLAIM_EDITED          - Claim properties modified
CLAIM_DELETED         - Claim removed

// Node Operations
NODE_EDITED           - Node properties updated

// Comment Operations
COMMENT_ADDED         - New comment posted
COMMENT_EDITED        - Comment modified
COMMENT_DELETED       - Comment removed

// System Operations
PROJECT_CREATED       - New project created
PROJECT_SWITCHED      - Active project changed
SEARCH_PERFORMED      - Search query executed
REPORT_GENERATED      - Report created
ANALYSIS_RUN          - Analysis workflow completed
WORKFLOW_STARTED      - Workflow execution started
WORKFLOW_COMPLETED    - Workflow execution finished
AGENT_SPAWNED         - AI agent initiated
AGENT_COMPLETED       - AI agent finished task
```

#### Database Storage

Activities are stored in-memory (last 10,000 activities) for the local/single-user version. For production deployment, consider using:
- Neo4j for activity nodes
- Time-series database (e.g., InfluxDB)
- PostgreSQL with partitioning

```python
activity = {
    'id': 'uuid',
    'type': 'document_uploaded',
    'description': 'Uploaded document: example.pdf',
    'entity_id': 'doc_123',
    'entity_type': 'document',
    'metadata': {'filename': 'example.pdf'},
    'created_at': '2025-01-15T10:30:00Z'
}
```

#### UI Components

**Location**: Right sidebar (toggle button in header)

Features:
- Collapsible sidebar with activities
- Grouped by date (Today, Yesterday, This Week, etc.)
- Filter by activity type and date range
- Statistics dashboard with charts
- Click to navigate to related entities
- Export functionality

#### Backend API Endpoints

```
GET    /api/activity               # Get activity feed
GET    /api/activity/stats         # Get activity statistics
GET    /api/activity/export        # Export activity log
GET    /api/activity/<id>          # Get activity details
GET    /api/activity/entity/<id>   # Get activities for entity
```

#### Usage Examples

**View Activity Feed:**
```javascript
// Click the 📋 button in the header
// Sidebar slides in from the right
```

**Filter Activities:**
```javascript
// Click the 🔍 filter button
// Select activity type and date range
// Click "Apply"
```

**View Statistics:**
```javascript
// Click the 📊 stats button
// Shows:
// - Total activities
// - Activities by type (bar chart)
// - Activity timeline (last 7 days)
// - Most active entities
```

**Export Activity Log:**
```javascript
// Click the 💾 export button
// Choose CSV or JSON format
// Downloads file with all activities
```

## Integration Points

### 1. Property Viewer Integration

The commenting system is fully integrated into the Property Viewer as a new tab:

```javascript
// Load comments when Comments tab is opened
PropertyViewer.switchTab('comments')
// → CommentSystem.loadComments(nodeId)
```

### 2. WebSocket Real-Time Updates

Both systems use WebSocket for real-time synchronization:

```javascript
// Comment updates
socket.on('comment_added', (data) => { /* refresh comments */ })
socket.on('comment_updated', (data) => { /* refresh comments */ })
socket.on('comment_deleted', (data) => { /* refresh comments */ })

// Activity updates
socket.on('activity_added', (activity) => { /* add to feed */ })
```

### 3. Activity Tracking in Existing Events

Activity tracking is automatically called for key events:

```python
# Document upload
track_activity(db, socketio, ActivityType.DOCUMENT_UPLOADED,
              f'Uploaded document: {filename}',
              filename, 'document',
              {'filename': filename})

# Document processing complete
track_activity(db, socketio, ActivityType.DOCUMENT_PROCESSED,
              f'Processed document: {filename}',
              doc_id, 'document',
              {'filename': filename})
```

## File Structure

### Backend Files

```
web_ui/
├── comment_routes.py          # Comment API endpoints
├── activity_routes.py         # Activity feed API endpoints
└── app.py                     # Route registration
```

### Frontend Files

```
web_ui/static/js/
├── comment-system.js          # Comment UI and logic
├── activity-feed.js           # Activity feed UI and logic
└── property-viewer.js         # Updated with Comments tab
```

### Template Updates

```
web_ui/templates/
└── index.html                 # Added Comments tab and styles
```

## Markdown Support

The comment system supports standard Markdown syntax:

```markdown
**Bold text**
*Italic text*
`Code`
[Link text](https://example.com)
Line breaks are preserved
```

Rendering is done client-side with a simple markdown parser. For production, consider using a library like `marked.js` or `markdown-it`.

## Security Considerations

For the single-user local version:
- No authentication required
- All users can edit/delete any comment
- Activity log is visible to all

For multi-user production deployment:
- Add user authentication
- Implement permission checks
- Add user attribution to comments and activities
- Implement rate limiting

## Performance Considerations

### Comment System
- Comments are loaded on-demand when Comments tab is opened
- Nested replies use recursive tree structure
- Consider pagination for nodes with >100 comments

### Activity Feed
- In-memory storage limited to 10,000 activities
- Automatic trimming when limit exceeded
- Polling fallback every 30 seconds if WebSocket fails
- Consider database storage for production

## Testing

### Manual Testing Checklist

**Comments:**
- [ ] Add comment to a node
- [ ] View comments in Comments tab
- [ ] Reply to a comment
- [ ] Edit a comment
- [ ] Delete a comment
- [ ] Search comments
- [ ] Export comments (CSV and JSON)
- [ ] Verify Markdown rendering
- [ ] Verify real-time updates

**Activity Feed:**
- [ ] Open activity feed sidebar
- [ ] View grouped activities (Today, Yesterday, etc.)
- [ ] Filter by activity type
- [ ] Filter by date range
- [ ] View statistics dashboard
- [ ] Export activity log (CSV and JSON)
- [ ] Click activity to navigate to entity
- [ ] Verify real-time updates

**Integration:**
- [ ] Upload document → verify activity logged
- [ ] Process document → verify activity logged
- [ ] Add comment → verify activity logged
- [ ] Edit node → verify activity logged (if implemented)
- [ ] Run analysis → verify activity logged (if implemented)

## API Examples

### Comment API

**Create Comment:**
```bash
curl -X POST http://localhost:5001/api/comments \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node_123",
    "text": "This is a **great** claim!",
    "parent_comment_id": null
  }'
```

**Get Comments for Node:**
```bash
curl http://localhost:5001/api/comments/node/node_123
```

**Update Comment:**
```bash
curl -X PUT http://localhost:5001/api/comments/comment_456 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Updated comment text"
  }'
```

**Delete Comment:**
```bash
curl -X DELETE http://localhost:5001/api/comments/comment_456
```

**Search Comments:**
```bash
curl "http://localhost:5001/api/comments/search?q=keyword&node_id=node_123"
```

**Export Comments:**
```bash
# JSON
curl "http://localhost:5001/api/comments/export?node_id=node_123&format=json"

# CSV
curl "http://localhost:5001/api/comments/export?node_id=node_123&format=csv"
```

### Activity API

**Get Activity Feed:**
```bash
curl "http://localhost:5001/api/activity?limit=50&offset=0"
```

**Get Activity Statistics:**
```bash
curl http://localhost:5001/api/activity/stats
```

**Get Activity for Entity:**
```bash
curl http://localhost:5001/api/activity/entity/doc_123
```

**Export Activity Log:**
```bash
# JSON
curl "http://localhost:5001/api/activity/export?format=json"

# CSV
curl "http://localhost:5001/api/activity/export?format=csv"
```

## Future Enhancements

### Comments
- [ ] @mentions for notifying users (multi-user version)
- [ ] Emoji reactions (👍 👎 ❤️)
- [ ] Comment notifications
- [ ] Comment moderation
- [ ] Rich text editor (WYSIWYG)
- [ ] File attachments
- [ ] Comment threading depth limit UI

### Activity Feed
- [ ] Persistent storage (database)
- [ ] Activity notifications
- [ ] Activity filtering by user (multi-user)
- [ ] Activity undo functionality
- [ ] Activity replay feature
- [ ] Integration with external logging systems
- [ ] Performance metrics in activity feed

## Troubleshooting

### Comments Not Loading

**Problem**: Comments tab shows loading indefinitely

**Solutions:**
1. Check browser console for errors
2. Verify `/api/comments/node/<id>` endpoint returns 200
3. Check Neo4j connection
4. Verify comment routes are registered in `app.py`

### Activity Feed Not Updating

**Problem**: New activities don't appear in feed

**Solutions:**
1. Check WebSocket connection (should see "✓ WebSocket connected" in console)
2. Verify `activity_added` event is being emitted
3. Check if polling fallback is working (30s interval)
4. Clear browser cache and reload

### Markdown Not Rendering

**Problem**: Markdown appears as plain text

**Solutions:**
1. Verify `CommentSystem.renderMarkdown()` is being called
2. Check for JavaScript errors in console
3. For production, integrate a proper markdown library

## Migration to Production

When deploying to production with multiple users:

1. **Add User Authentication**
   - Store user ID with comments and activities
   - Implement permission checks (can only edit own comments)

2. **Database Storage**
   - Store comments in Neo4j with user relationships
   - Store activities in time-series database or PostgreSQL

3. **Performance Optimization**
   - Implement comment pagination
   - Add caching for frequently accessed comments
   - Use background jobs for activity logging

4. **Security**
   - Sanitize markdown input to prevent XSS
   - Rate limit comment creation
   - Implement CSRF protection

5. **Features**
   - Add user profiles to comments
   - Implement comment notifications
   - Add activity digest emails

## Conclusion

The commenting system and activity feed provide essential collaboration and visibility features for the Research Assistant Tool. The implementation is designed for single-user local deployment but can be easily extended for multi-user production environments.

For questions or issues, please refer to the main project documentation or create an issue in the repository.
