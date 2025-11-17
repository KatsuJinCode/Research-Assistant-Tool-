# Neo4j Installation for Windows (No Docker Required!)

## Why Neo4j?

Based on your research, Neo4j provides critical features for this project:

✅ **Graph Traversal** - Navigate complex claim relationships
✅ **Pattern Matching** - Find similar claim structures using Cypher
✅ **Shortest Path** - Discover connections between claims
✅ **Community Detection** - Cluster related claims automatically
✅ **Relationship Strength** - Score claim similarities
✅ **Visual Graph Browser** - See your knowledge graph
✅ **Full-Text Search** - Find claims by content
✅ **Schema Flexibility** - Add properties without migrations

---

## Installation Options for Windows

### Option 1: Neo4j Desktop (RECOMMENDED - No Docker!)

**Best for**: Windows users who want the full Neo4j experience without Docker

#### Step 1: Download
- Go to: https://neo4j.com/download-center/#desktop
- Click "Download Neo4j Desktop"
- No account required for Community Edition

#### Step 2: Install
- Run the downloaded `.exe` file
- Follow the installer (default options are fine)
- Launch Neo4j Desktop

#### Step 3: Create Database
1. Click "New" → "Create Project"
2. Name it "Research Verification System"
3. Click "Add" → "Local DBMS"
4. Name: `research-verification`
5. Password: `research123` (IMPORTANT - code expects this)
6. Version: Latest (currently 5.x)
7. Click "Create"

#### Step 4: Start Database
1. Click the "Start" button on your database
2. Wait for it to say "Active"
3. Click "Open" → "Neo4j Browser"

#### Step 5: Configure Connection
Create `.env` file in project root:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=research123
NEO4J_DATABASE=neo4j
```

#### Step 6: Test Connection
```bash
python -c "from research_agent.neo4j_database import Neo4jDatabase; db = Neo4jDatabase(); print('✓ Connected to Neo4j!'); db.close()"
```

---

### Option 2: Docker Desktop

**Best for**: Users who already have Docker or want containerized setup

#### Step 1: Install Docker Desktop
- Download from: https://www.docker.com/products/docker-desktop
- Install and start Docker Desktop

#### Step 2: Run Auto-Install
```bash
auto_install.bat
```

When prompted "Would you like to install Neo4j via Docker?", answer `y`

OR manually:
```bash
docker run --name research-neo4j -p7474:7474 -p7687:7687 -d -v "%CD%\neo4j\data:/data" --env NEO4J_AUTH=neo4j/research123 neo4j:latest
```

---

### Option 3: Start Without Neo4j (NetworkX Only)

**Best for**: Quick start, testing, or if you don't need Neo4j features yet

The system works perfectly with NetworkX (already installed):
- No setup required
- Saves graphs to files
- Good for development
- Can migrate to Neo4j later

Just skip Neo4j installation and use the system as-is!

---

## Verifying Neo4j Installation

### 1. Check Browser Access
- Open: http://localhost:7474
- Login: `neo4j` / `research123`
- You should see the Neo4j Browser interface

### 2. Run Test Query
In Neo4j Browser, try:
```cypher
MATCH (n) RETURN n LIMIT 25;
```

(Will be empty until you migrate data)

### 3. Test Python Connection
```bash
python -c "from research_agent.neo4j_database import Neo4jDatabase; db = Neo4jDatabase(); print('Connected!'); db.close()"
```

---

## Migrating Data to Neo4j

Once Neo4j is installed and running:

### 1. Run Migration Script
```bash
python migrate_to_neo4j.py
```

This will:
- Connect to Neo4j
- Import all nodes from NetworkX graph
- Create all relationships
- Preserve all qualifiers
- Set up indexes

### 2. Verify in Browser
```cypher
// Count nodes
MATCH (n) RETURN count(n);

// View claims
MATCH (c:Claim) RETURN c LIMIT 10;

// View claim with qualifiers
MATCH (c:Claim)-[r:HAS_QUALIFIER]->(q:Qualifier)
RETURN c, r, q
LIMIT 5;
```

---

## Using Neo4j Features

### Finding Similar Claims
```cypher
MATCH (c1:Claim)-[:SIMILAR_TO]-(c2:Claim)
WHERE id(c1) < id(c2)
RETURN c1.text, c2.text, c1.similarity_score
ORDER BY c1.similarity_score DESC
LIMIT 10;
```

### Claim Hierarchies (Super Claims)
```cypher
MATCH (c:Claim)-[:MERGED_INTO]->(sc:SuperClaim)
RETURN sc.text, count(c) as num_claims
ORDER BY num_claims DESC;
```

### Claims by Qualifier Type
```cypher
MATCH (c:Claim)-[:HAS_QUALIFIER]->(q:Qualifier {type: 'modal'})
RETURN c.text, collect(q.text) as modals;
```

### Full Graph Visualization
```cypher
MATCH (n)-[r]-(m)
RETURN n, r, m
LIMIT 100;
```

---

## Troubleshooting

### "Connection refused" error
- **Neo4j Desktop**: Make sure database is started (click "Start")
- **Docker**: Check Docker Desktop is running

### "Authentication failed"
- Password must be exactly: `research123`
- Check `.env` file settings
- Neo4j Desktop: Recreate database with correct password

### "Database not found"
- Default database name is `neo4j`
- Check `.env` file: `NEO4J_DATABASE=neo4j`

### Port already in use (7474 or 7687)
- **Option A**: Stop other Neo4j instance
- **Option B**: Use different ports in Neo4j Desktop settings

---

## Neo4j Desktop vs Docker: Which to Choose?

| Feature | Neo4j Desktop | Docker |
|---------|---------------|--------|
| **Installation** | Windows installer | Requires Docker Desktop |
| **Ease of use** | Very easy | Moderate |
| **Visual tools** | Built-in | Browser only |
| **Performance** | Native | Containerized |
| **Multiple databases** | Easy to manage | Need multiple containers |
| **Recommended for** | Windows development | CI/CD, production |

**For this project on Windows: Neo4j Desktop is easier!**

---

## Next Steps After Installation

1. **Test extraction**:
   ```bash
   python test_extraction_simple.py
   ```

2. **Extract real claims**:
   ```bash
   python extract_and_cluster_claims.py
   ```

3. **Migrate to Neo4j**:
   ```bash
   python migrate_to_neo4j.py
   ```

4. **Browse graph**:
   - Open http://localhost:7474
   - Run queries in Neo4j Browser

5. **Use investigation agents**:
   ```python
   from research_agent.agents.investigation_agent import InvestigationAgent
   from research_agent.neo4j_database import Neo4jDatabase

   db = Neo4jDatabase()
   agent = InvestigationAgent(db, agent_type='support')
   ```

---

## Automated Installation (Coming Soon)

We're working on CLI download support for Neo4j Desktop. For now:

1. Download manually: https://neo4j.com/download-center/#desktop
2. Or use Docker via `auto_install.bat`
3. Or use NetworkX (no Neo4j needed!)

---

**All three options give you a working system. Neo4j adds powerful graph features when you need them!**
