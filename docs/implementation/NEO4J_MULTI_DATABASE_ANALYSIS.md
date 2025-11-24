# Neo4j Multi-Database Architecture Analysis

## Quick Decision: ✅ Use Neo4j Built-in Multi-Database Feature

---

## Pros of Built-in Multi-Database

### 1. **Native Support**
- Available in Neo4j 4.0+ (both Community and Enterprise)
- Well-tested, documented, and supported by Neo4j
- Part of core architecture - not a hack or workaround

### 2. **Complete Isolation**
- Each database is 100% separate - no data leakage possible
- Different schemas, indexes, constraints per database
- No risk of accidental cross-project queries
- Security: projects cannot access each other's data

### 3. **Performance**
- Smaller databases = faster queries
- No filtering overhead (no WHERE project_id clauses)
- Better memory locality
- Queries only scan relevant data

### 4. **Database Management**
- Individual backup/restore per project
- Can delete entire project database cleanly
- Easy to export/import specific projects
- Clear disk usage per project

### 5. **Scalability**
- Can run different projects on different Neo4j instances later
- Distributed architecture possible
- No single-database bottleneck

### 6. **Simplicity**
- One project = one database (easy mental model)
- No need for project_id on every node
- Cleaner Cypher queries
- Less code complexity

---

## Cons of Built-in Multi-Database

### 1. **Version Requirements**
- Requires Neo4j 4.0+ (released April 2020)
- User's current version: 5.26.0 ✅ (fully supported)
- Not a concern for this project

### 2. **Memory Overhead**
- Each database has some memory overhead
- Minimal for our use case (estimated ~10-50MB per project)
- Only active database fully loaded in memory

### 3. **Cross-Database Queries**
- Cannot query across databases in single Cypher query
- Need application-level logic for cross-project features
- Mitigated: User wants isolation now, cross-project later

### 4. **Management Complexity**
- Application must manage database lifecycle
- Need to handle CREATE/DROP DATABASE operations
- Mitigated: Encapsulate in DatabaseManager class

---

## Alternative: Separate Files Approach

### Why NOT Recommended:

**Multiple Neo4j Instances:**
- Each project = separate Neo4j server instance
- Requires different ports (7687, 7688, 7689...)
- High memory overhead (each instance ~200MB+)
- Complex process management
- User would need multiple Neo4j services running

**File-Based Switching:**
- Stop Neo4j, swap data files, restart Neo4j
- Extremely slow (30+ seconds per switch)
- High risk of data corruption
- Poor user experience
- Not viable for active development

**Verdict:** Not practical for this use case

---

## Implementation Plan

### 1. Neo4j Multi-Database Commands

```cypher
-- List all databases
SHOW DATABASES;

-- Create new database
CREATE DATABASE project_123;

-- Switch to database (in session)
-- driver.session(database="project_123")

-- Drop database
DROP DATABASE project_123 IF EXISTS;

-- Get database info
SHOW DATABASE project_123;
```

### 2. Python Driver Usage

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# Create session with specific database
with driver.session(database="project_123") as session:
    result = session.run("MATCH (n) RETURN count(n)")

# Switch databases by creating new session
with driver.session(database="project_456") as session:
    result = session.run("MATCH (n) RETURN count(n)")
```

### 3. Application Architecture

```
Application Layer
    ├── DatabaseManager
    │   ├── create_database(project_id)
    │   ├── drop_database(project_id)
    │   ├── list_databases()
    │   └── get_active_database()
    │
    ├── Neo4jClient (updated)
    │   ├── get_session(database_name)  # NEW
    │   └── active_database = "neo4j"   # NEW
    │
    └── Repositories (updated)
        ├── Use client.get_session(active_database)
        └── No more project_id filtering
```

### 4. Project Workflow

**Create Project:**
1. User creates project "Machine Learning Research"
2. Generate database name: `project_ml_research`
3. Execute: `CREATE DATABASE project_ml_research`
4. Store project metadata in system database
5. Switch active database to new project

**Switch Project:**
1. User clicks "Switch" on project
2. Update active_database in application state
3. All subsequent queries use new database
4. Frontend reloads graph (empty for new projects)

**Delete Project:**
1. Confirm with user (irreversible)
2. Execute: `DROP DATABASE project_ml_research`
3. Remove project from system database
4. Switch to default project

---

## Technical Considerations

### Database Naming
- Format: `project_{sanitized_name}` or `proj_{uuid}`
- Sanitize: lowercase, alphanumeric + underscore only
- Max length: 63 characters (Neo4j limit)
- Reserved: `neo4j`, `system` (Neo4j system databases)

### System Database
- Use default `neo4j` database for project metadata
- Stores: project list, active project, user preferences
- Small overhead, always available

### Transactions
- Each database has independent transactions
- No cross-database transactions (not needed)
- Standard ACID guarantees per database

### Indexes
- Created per database
- Need to recreate indexes when creating new project
- Can template initial indexes

---

## Migration Strategy

### From Current Implementation:

**Current (Wrong):**
- Single database with project_id on all nodes
- 45 nodes with project_id = 'default'

**Migration:**
1. Keep `neo4j` database as default project
2. Remove project_id properties (optional, doesn't hurt)
3. Future projects create new databases
4. No data loss - existing work preserved

**Rollback project_id migration:**
```cypher
// Optional: Remove project_id properties
MATCH (n)
WHERE n.project_id IS NOT NULL
REMOVE n.project_id
RETURN count(n);

// Drop Project nodes
MATCH (p:Project)
DELETE p;
```

---

## Conclusion

✅ **Use Neo4j Multi-Database Feature**

**Benefits:**
- Native, well-supported feature
- Complete isolation (user's requirement)
- Better performance
- Simpler architecture
- Future-proof for scaling

**Drawbacks:**
- Minimal (version requirement already met)
- Easy to manage with DatabaseManager class

**Recommendation:** Proceed with implementation immediately

---

## Next Steps

1. ✅ Create DatabaseManager class
2. ✅ Update neo4j_client.py with database parameter
3. ✅ Modify all repositories to use active database
4. ✅ Update Project API endpoints for database lifecycle
5. ✅ Test with 2-3 separate databases
6. ✅ Update documentation

**Estimated Time:** 2-3 hours for complete implementation
