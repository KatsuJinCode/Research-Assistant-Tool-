# Project Management System - User Guide

## Overview

The Research Assistant Tool includes a comprehensive Project Management System that allows users to create, manage, and switch between multiple research projects with complete data isolation.

## Architecture

### Two Implementation Modes

The system supports two modes depending on your Neo4j edition:

#### 1. **Multi-Database Mode (Neo4j Enterprise/Desktop)**
- Each project gets its own separate Neo4j database
- Complete physical isolation between projects
- Databases named with pattern: `project_<sanitized_name>`
- Project metadata stored in system database (`neo4j`)

#### 2. **Single-Database Mode (Neo4j Community)**
- All projects share one database (`neo4j`)
- Logical isolation using `project_id` property on all nodes
- All queries automatically filter by active project
- More cost-effective for most users

**The system automatically detects your Neo4j edition and uses the appropriate mode.**

## Features

### ✅ Core Functionality

- **Create Projects**: Name, description, color for visual identification
- **Switch Projects**: Instantly switch between research contexts
- **Delete Projects**: Remove projects and all associated data
- **Update Projects**: Change name, description, or color
- **Project Statistics**: View node counts, document counts, etc.
- **Export Projects**: Export project data to JSON/Markdown
- **Visual Indicators**: Color-coded project identification in UI

### ✅ Data Isolation

- **Complete isolation**: Nodes from one project never appear in another
- **Automatic filtering**: All graph queries filter by active project
- **Document uploads**: New documents automatically assigned to active project
- **Search isolation**: Search results filtered by project (with cross-project option)

### ✅ Session Management

- **Active project**: One project active per session
- **WebSocket sync**: Project switches broadcast to all connected clients
- **Persistent state**: Active project stored in database

## User Interface

### Project Selector

Located in the header bar:

```
┌─────────────────────────────────────┐
│ Current Project: Default Project ▼  │
└─────────────────────────────────────┘
```

Click to open the Project Management Modal.

### Project Management Modal

#### Tabs:

1. **Projects List**
   - Grid of all projects
   - Each card shows:
     - Name and description
     - Color indicator (left border)
     - Node count
     - Active badge
     - Actions: Switch, Edit, Delete

2. **Create New Project**
   - Name (required)
   - Description (optional)
   - Color picker (visual identification)

3. **Project Statistics**
   - Total nodes
   - Document count
   - Claim count
   - Evidence count
   - Relationship count

## API Endpoints

### List All Projects
```http
GET /api/projects
```

**Response:**
```json
{
  "projects": [
    {
      "id": "default",
      "name": "Default Project",
      "description": "Default research project",
      "color": "#2196F3",
      "database_name": "neo4j",
      "is_active": true,
      "created_at": "2025-01-15T10:30:00",
      "updated_at": "2025-01-15T10:30:00",
      "node_count": 150
    }
  ]
}
```

### Get Active Project
```http
GET /api/projects/active
```

**Response:**
```json
{
  "project": {
    "id": "default",
    "name": "Default Project",
    "is_active": true,
    ...
  }
}
```

### Create Project
```http
POST /api/projects
Content-Type: application/json

{
  "name": "AI Research 2025",
  "description": "Comprehensive AI research project",
  "color": "#FF5722"
}
```

**Response:**
```json
{
  "success": true,
  "project": {
    "id": "ai_research_2025",
    "name": "AI Research 2025",
    ...
  }
}
```

### Update Project
```http
PUT /api/projects/<project_id>
Content-Type: application/json

{
  "description": "Updated description",
  "color": "#00BCD4"
}
```

### Switch Project
```http
POST /api/projects/<project_id>/switch
```

**Response:**
```json
{
  "success": true,
  "project": {
    "id": "ai_research_2025",
    "name": "AI Research 2025"
  }
}
```

**Side Effects:**
- Updates `is_active` flag in database
- Changes active database in Neo4j client
- Emits `project_switched` WebSocket event
- Reloads graph visualization

### Delete Project
```http
DELETE /api/projects/<project_id>
```

**Restrictions:**
- Cannot delete active project (switch first)
- Cannot delete default project if it contains nodes
- Requires confirmation in UI

**Response:**
```json
{
  "success": true,
  "message": "Project 'AI Research 2025' and all its data have been permanently deleted"
}
```

### Get Project Statistics
```http
GET /api/projects/<project_id>/stats
```

**Response:**
```json
{
  "project_id": "ai_research_2025",
  "name": "AI Research 2025",
  "total_nodes": 234,
  "total_relationships": 456,
  "document_count": 12,
  "claim_count": 180,
  "evidence_count": 42,
  "label_counts": {
    "Document": 12,
    "Claim": 180,
    "Evidence": 42
  }
}
```

### Export Project
```http
POST /api/projects/<project_id>/export
```

Exports project data to markdown files for version control.

## Database Schema

### Project Node (System Database)

```cypher
(:Project {
  id: string,              // Unique identifier
  name: string,            // Display name
  description: string,     // Optional description
  color: string,           // Hex color code
  database_name: string,   // Neo4j database name
  is_active: boolean,      // Currently active flag
  created_at: datetime,
  updated_at: datetime
})
```

### Node Properties (All Types)

All nodes in the system have a `project_id` property:

```cypher
(:Claim {
  id: string,
  text: string,
  project_id: string,      // Links to Project.id
  ...
})

(:Document {
  id: string,
  title: string,
  project_id: string,      // Links to Project.id
  ...
})
```

### Indexes

```cypher
CREATE INDEX project_id_index FOR (n:Claim) ON (n.project_id)
CREATE INDEX document_project_index FOR (n:Document) ON (n.project_id)
```

## Migration

### First-Time Setup

Run the migration to add project support to existing data:

```bash
python backend/database/migrations/add_project_support.py
```

**What it does:**
1. Creates default Project node
2. Adds `project_id` property to all existing nodes
3. Creates indexes for efficient querying
4. Verifies migration success

### Rollback (Testing Only)

```bash
python backend/database/migrations/add_project_support.py --rollback
```

**Warning:** This removes all project data!

## Usage Examples

### Example 1: Research Workflow

```
1. Create project "Climate Change 2025"
2. Upload documents to that project
3. Review claims and evidence
4. Create project "AI Safety 2025"
5. Upload different documents
6. Switch between projects to compare findings
```

### Example 2: Collaboration

```
1. Team A works on "Medical Research" project
2. Team B works on "Drug Discovery" project
3. Both teams use same Research Assistant instance
4. Complete data isolation ensures no cross-contamination
5. Admin can switch between projects to review all work
```

### Example 3: Versioning

```
1. Create "Literature Review v1" project
2. Upload initial documents
3. Export project to git repository
4. Create "Literature Review v2" project
5. Import v1 data and continue work
6. Compare versions by switching projects
```

## Best Practices

### 1. **Naming Conventions**

- Use descriptive names: "AI Ethics Literature Review 2025"
- Include dates/versions: "Climate Study v2"
- Use colors consistently: Green for completed, Blue for active, Red for review needed

### 2. **Project Organization**

- One project per research topic
- Split large topics into sub-projects
- Use default project for quick tests/demos

### 3. **Data Management**

- Regularly export projects for backup
- Delete completed/obsolete projects
- Monitor node counts to avoid oversized projects

### 4. **Performance**

- Keep projects under 10,000 nodes for optimal performance
- Use cross-project search sparingly
- Switch projects only when needed (triggers graph reload)

## Troubleshooting

### Issue: "Multi-database not available"

**Cause:** You're using Neo4j Community Edition

**Solution:** This is expected. The system automatically uses single-database mode with `project_id` filtering. All features work identically.

**Upgrade Option:** Install Neo4j Desktop or Enterprise for multi-database support.

### Issue: Can't delete default project

**Cause:** Default project contains nodes

**Solution:**
1. Create a new project
2. Switch to it
3. Delete default project (will be empty after switch)

### Issue: Wrong project data showing

**Cause:** Active project not synced

**Solution:**
1. Reload the page
2. Check active project in header
3. Re-switch to desired project

### Issue: Project not appearing after creation

**Cause:** Database creation failed (Enterprise only)

**Solution:**
1. Check Neo4j logs
2. Verify database name doesn't conflict
3. Ensure Neo4j has sufficient resources

## WebSocket Events

### `project_switched`

Emitted when active project changes:

```javascript
socket.on('project_switched', (data) => {
  console.log('Switched to:', data.project_name);
  // Reload graph, update UI, etc.
});
```

**Payload:**
```json
{
  "project_id": "ai_research_2025",
  "project_name": "AI Research 2025",
  "database_name": "project_ai_research_2025"
}
```

## JavaScript API

### ProjectManager Module

```javascript
// Initialize
await ProjectManager.init();

// Open project modal
ProjectManager.openProjectModal();

// Create project
await ProjectManager.createProject();

// Switch project
await ProjectManager.switchProject('project_id');

// Delete project
await ProjectManager.deleteProject('project_id', 'Project Name');

// Get current project
const currentProject = ProjectManager.currentProject;
```

## Technical Details

### Multi-Database Support Detection

```python
from backend.database.database_manager import DatabaseManager

manager = DatabaseManager(driver)

# Try to create database
success, error = manager.create_database("test_db")

if not success and "does not support multiple databases" in error:
    # Use single-database mode with project_id filtering
    mode = "single-database"
else:
    # Use multi-database mode
    mode = "multi-database"
```

### Query Filtering (Single-Database Mode)

All queries automatically include `project_id` filter:

```cypher
# Without filtering (old)
MATCH (c:Claim)
RETURN c

# With project filtering (new)
MATCH (c:Claim {project_id: $active_project_id})
RETURN c
```

### Database Naming (Multi-Database Mode)

```python
# Sanitization rules
name = "AI Research 2025!"
# ↓
sanitized = "project_ai_research_2025"

# Rules:
# - Lowercase only
# - Alphanumeric + underscore
# - Max 63 characters
# - Prefix with "project_"
```

## Files Reference

### Backend
- `backend/database/neo4j_client.py` - Neo4j client singleton
- `backend/database/database_manager.py` - Multi-database operations
- `backend/database/migrations/add_project_support.py` - Migration script

### Frontend
- `web_ui/static/js/project_manager.js` - UI logic
- `web_ui/templates/index.html` - Project modal UI

### API
- `web_ui/app.py` - Project API endpoints (lines 3122-3647)

### Testing
- `test_project_management.py` - Comprehensive test suite

## Support

For issues or questions:
1. Check this guide
2. Review test output: `python test_project_management.py`
3. Check Neo4j logs
4. Verify migration completed: See "Migration Verification" section
5. Review browser console for JavaScript errors

---

**Version:** 1.0.0
**Last Updated:** 2025-01-15
**Compatible With:** Neo4j Community (4.4+), Neo4j Enterprise (4.4+), Neo4j Desktop
