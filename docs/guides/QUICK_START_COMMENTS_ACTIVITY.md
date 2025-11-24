# Quick Start: Comments and Activity Feed

## Using the Commenting System

### Add a Comment
1. Click any node in the graph
2. Property Viewer opens on the right
3. Click the **Comments** tab
4. Type your comment in the text area (Markdown supported!)
5. Click **Add Comment**

### Reply to a Comment
1. Click the 💬 **Reply** button on any comment
2. Your reply will be nested under the parent comment

### Edit a Comment
1. Click the ✏️ **Edit** button
2. Text appears in the editor
3. Make changes
4. Click **Update Comment**

### Delete a Comment
1. Click the 🗑️ **Delete** button
2. Confirm deletion
3. Comment and all replies are removed

### Markdown Formatting
```markdown
**Bold text**
*Italic text*
`Inline code`
[Link](https://example.com)
```

### Search Comments
1. Open Comments tab
2. Use search bar
3. Results show matching comments with context

### Export Comments
```javascript
CommentSystem.exportComments('json')  // or 'csv'
```

## Using the Activity Feed

### Open Activity Feed
- Click the 📋 button in the top-right header
- Sidebar slides in from the right

### View Activities
- Activities grouped by date:
  - Today
  - Yesterday
  - This Week
  - This Month
  - Older

### Filter Activities
1. Click 🔍 **Filter** button
2. Select activity type (e.g., "Document Uploaded")
3. Select time range (e.g., "Last 24 Hours")
4. Click **Apply**

### View Statistics
1. Click 📊 **Stats** button
2. Dashboard shows:
   - Total activities
   - Activities by type (chart)
   - Activity timeline (last 7 days)
   - Most active entities

### Navigate to Entity
- Click any activity item
- Jumps to the related node in the graph
- Opens Property Viewer with details

### Export Activity Log
1. Click 💾 **Export** button
2. Choose CSV or JSON
3. File downloads automatically

## Activity Types You'll See

| Icon | Type | Description |
|------|------|-------------|
| 📄 | Document Uploaded | File uploaded to system |
| ✅ | Document Processed | Processing completed |
| 💡 | Claim Created | New claim extracted |
| ✏️ | Claim Edited | Claim modified |
| 💬 | Comment Added | New comment posted |
| 🔍 | Search Performed | Search executed |
| 📊 | Report Generated | Report created |
| 🤖 | Agent Spawned | AI agent started |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+/` | Toggle markdown preview (in comment editor) |
| `Esc` | Close Property Viewer (and Comments) |
| `Ctrl+K` | Focus comment search |

## API Quick Reference

### Comments
```bash
# Get comments for a node
GET /api/comments/node/{node_id}

# Add comment
POST /api/comments
Body: {"node_id": "...", "text": "...", "parent_comment_id": null}

# Update comment
PUT /api/comments/{comment_id}
Body: {"text": "..."}

# Delete comment
DELETE /api/comments/{comment_id}

# Search
GET /api/comments/search?q=keyword&node_id={node_id}

# Export
GET /api/comments/export?node_id={node_id}&format=json
```

### Activity
```bash
# Get activity feed
GET /api/activity?limit=50&offset=0&type=document_uploaded

# Get stats
GET /api/activity/stats

# Get activity for entity
GET /api/activity/entity/{entity_id}

# Export
GET /api/activity/export?format=json
```

## Tips and Tricks

### Comments
- Use `**bold**` for emphasis on important points
- Use backticks for `technical terms` or `code`
- Reply to create discussion threads
- Search helps find old comments quickly

### Activity Feed
- Keep it open while working to see real-time updates
- Use filters to focus on specific activity types
- Export logs for auditing or reporting
- Click activities to quickly navigate the graph

## Troubleshooting

**Comments not loading?**
- Refresh the page
- Check browser console for errors
- Verify you're connected to the server

**Activity feed not updating?**
- Check WebSocket connection (green dot in header)
- Wait 30 seconds (fallback polling)
- Refresh the page

**Markdown not rendering?**
- Check syntax (preview button helps)
- Use proper markdown format
- Refresh if needed

## Examples

### Good Comment Example
```markdown
This claim is **strongly supported** by the evidence in Figure 3.

However, note that:
- Sample size is small (n=42)
- Confidence interval is wide

See also: [Related Study](https://example.com)
```

### Activity Feed Use Cases

**Audit Trail:**
1. Open Activity Feed
2. Filter by "Last 7 Days"
3. Export as CSV
4. Review all actions taken

**Track Document Processing:**
1. Upload document
2. See "Document Uploaded" activity
3. Wait for processing
4. See "Document Processed" activity
5. Click to view processed document

**Follow Investigation:**
1. Filter by "Agent Spawned" and "Agent Completed"
2. See entire agent workflow
3. Click to see agent transcripts

## Need More Help?

- Full Documentation: `COMMENTING_AND_ACTIVITY_SYSTEM.md`
- Project Docs: `CLAUDE.md`
- Issues: Create a GitHub issue
