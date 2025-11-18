# Neo4j Setup Guide

## Installation Options

### Option 1: Docker (Recommended for Development)

```bash
# Pull Neo4j image
docker pull neo4j:latest

# Run Neo4j container
docker run \
    --name research-neo4j \
    -p7474:7474 -p7687:7687 \
    -d \
    -v $PWD/neo4j/data:/data \
    -v $PWD/neo4j/logs:/logs \
    -v $PWD/neo4j/import:/var/lib/neo4j/import \
    -v $PWD/neo4j/plugins:/plugins \
    --env NEO4J_AUTH=neo4j/research123 \
    neo4j:latest

# Access Neo4j Browser
# Navigate to: http://localhost:7474
# Login: neo4j / research123
```

### Option 2: Direct Installation (Ubuntu/Debian)

```bash
# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

# Install
sudo apt-get update
sudo apt-get install neo4j

# Start service
sudo systemctl start neo4j
sudo systemctl enable neo4j

# Set initial password
sudo neo4j-admin set-initial-password research123

# Access Neo4j Browser
# Navigate to: http://localhost:7474
```

### Option 3: Neo4j Desktop (GUI Application)

1. Download from: https://neo4j.com/download/
2. Install and launch
3. Create new project: "Research Verification System"
4. Create new database: "research-claims"
5. Start database

## Python Driver Installation

```bash
pip install neo4j
```

## Configuration

Create `.env` file in project root:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=research123
NEO4J_DATABASE=neo4j
```

## Initial Schema Setup

After Neo4j is running, import the schema:

```bash
# Import from Cypher file
cat szasz_claims_graph.cypher | cypher-shell -u neo4j -p research123

# Or run Python migration script
python migrate_to_neo4j.py
```

## Verification

Test the connection:

```python
from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "research123"))

with driver.session() as session:
    result = session.run("RETURN 'Connection successful!' AS message")
    print(result.single()["message"])

driver.close()
```

## Neo4j Browser Queries

Once connected, try these queries in Neo4j Browser (http://localhost:7474):

### View all nodes
```cypher
MATCH (n) RETURN n LIMIT 25
```

### View claims and their relationships
```cypher
MATCH (d:Document)-[:CONTAINS]->(c:Claim)
RETURN d, c LIMIT 10
```

### View claim clusters
```cypher
MATCH (c1:Claim)-[s:SIMILAR_TO]-(c2:Claim)
WHERE s.score > 0.8
RETURN c1, s, c2
```

### View super-claims
```cypher
MATCH (c:Claim)-[:MERGED_INTO]->(sc:SuperClaim)
RETURN c, sc
```

### Find claims with qualifiers
```cypher
MATCH (c:Claim)-[:HAS_QUALIFIER]->(q:Qualifier)
RETURN c.text, q.type, q.text
```

## Useful Neo4j Commands

```bash
# Check status
sudo systemctl status neo4j

# View logs
sudo journalctl -u neo4j -f

# Restart
sudo systemctl restart neo4j

# Stop
sudo systemctl stop neo4j
```

## Troubleshooting

### Can't connect on port 7687
- Check firewall: `sudo ufw allow 7687`
- Check Neo4j is running: `sudo systemctl status neo4j`
- Check logs: `sudo journalctl -u neo4j`

### Password issues
- Reset password: `sudo neo4j-admin set-initial-password newpassword`
- Or disable auth (dev only): Add `dbms.security.auth_enabled=false` to neo4j.conf

### Memory issues
Edit `/etc/neo4j/neo4j.conf`:
```
dbms.memory.heap.initial_size=512m
dbms.memory.heap.max_size=2G
```

## Next Steps

After Neo4j is running:
1. Run `python migrate_to_neo4j.py` to import existing graph
2. Test with `python test_neo4j_connection.py`
3. Update `research_agent/config.py` to use Neo4j by default
4. Build investigation agents that store findings in Neo4j
