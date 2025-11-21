# Database Management Guide

## Overview

This guide explains how to manage Neo4j databases for multiple research projects,
compare them, and integrate findings across projects.

---

## Architecture Decision: One Database Per Project

**Recommendation**: Each research project gets its own Neo4j database instance.

### Benefits:
✅ **Isolation**: Different topics don't interfere
✅ **Performance**: Smaller graphs = faster queries
✅ **Management**: Easy backup/restore
✅ **Clarity**: Clear provenance per project
✅ **Flexibility**: Can merge later if needed

### Drawbacks:
❌ More setup (but auto-installer handles this)
❌ Can't query across projects directly (but we provide tools)

---

## Setup: Multiple Projects

### Method 1: Docker Containers (Recommended)

Each project runs its own Neo4j container:

```bash
# Project 1: Mental Illness Research
docker run --name neo4j-mental-illness \
    -p7474:7474 -p7687:7687 \
    -v $PWD/projects/mental-illness/neo4j-data:/data \
    --env NEO4J_AUTH=neo4j/research123 \
    -d neo4j:latest

# Project 2: Cognitive Therapy
docker run --name neo4j-cognitive-therapy \
    -p7475:7474 -p7688:7687 \
    -v $PWD/projects/cognitive-therapy/neo4j-data:/data \
    --env NEO4J_AUTH=neo4j/research123 \
    -d neo4j:latest

# Project 3: Neuroscience
docker run --name neo4j-neuroscience \
    -p7476:7474 -p7689:7687 \
    -v $PWD/projects/neuroscience/neo4j-data:/data \
    --env NEO4J_AUTH=neo4j/research123 \
    -d neo4j:latest
```

**Directory structure:**
```
projects/
├── mental-illness/
│   ├── neo4j-data/         # Database files
│   ├── papers/              # PDFs
│   ├── .env                 # NEO4J_URI=bolt://localhost:7687
│   └── config.yaml
│
├── cognitive-therapy/
│   ├── neo4j-data/
│   ├── papers/
│   ├── .env                 # NEO4J_URI=bolt://localhost:7688
│   └── config.yaml
│
└── neuroscience/
    ├── neo4j-data/
    ├── papers/
    ├── .env                 # NEO4J_URI=bolt://localhost:7689
    └── config.yaml
```

### Method 2: Named Databases (Same Instance)

Use Neo4j 4.0+ multi-database feature:

```python
# Connect to different databases in same instance
db_mental = Neo4jDatabase(database="mental_illness")
db_cognitive = Neo4jDatabase(database="cognitive_therapy")
db_neuro = Neo4jDatabase(database="neuroscience")
```

**Pros**: Easier management, one instance
**Cons**: All databases must be up/down together

---

## Working with a Project

### Start Project Database
```bash
# Start specific project
docker start neo4j-mental-illness

# Verify it's running
docker ps | grep mental-illness

# Access browser
# http://localhost:7474
```

### Switch Between Projects
```bash
# In your project directory
cd projects/mental-illness

# Load environment
source .env

# Connect
python
>>> from research_agent.neo4j_database import Neo4jDatabase
>>> db = Neo4jDatabase()  # Uses .env settings
>>> stats = db.stats()
>>> print(stats)
```

### Project Configuration File

Each project has a `.env` file:

```bash
# projects/mental-illness/.env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=research123
NEO4J_DATABASE=neo4j
PROJECT_NAME=mental-illness-research
```

---

## Comparing Projects

### 1. Export Project Graphs

```bash
# Export Project 1
cd projects/mental-illness
python -c "
from research_agent.neo4j_database import Neo4jDatabase
db = Neo4jDatabase()
# Export logic here
"

# Export Project 2
cd projects/cognitive-therapy
# Same export
```

### 2. Find Overlapping Claims

Create `compare_projects.py`:

```python
#!/usr/bin/env python3
"""
Compare claims across two research projects.
"""

from research_agent.neo4j_database import Neo4jDatabase
from typing import List, Dict, Any


def connect_to_project(project_name: str) -> Neo4jDatabase:
    """Connect to a project's database."""
    # Load project's .env file
    import os
    from dotenv import load_dotenv

    env_path = f"projects/{project_name}/.env"
    load_dotenv(env_path)

    return Neo4jDatabase()


def get_all_claims(db: Neo4jDatabase) -> List[Dict[str, Any]]:
    """Get all claims from a database."""
    return db.find_nodes('Claim')


def compute_similarity(text1: str, text2: str) -> float:
    """
    Compute similarity between two claim texts.

    Uses Jaccard similarity for now.
    In production, use embeddings.
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)


def compare_projects(project1: str, project2: str,
                    similarity_threshold: float = 0.8):
    """
    Compare two projects and find overlapping claims.

    Args:
        project1: First project name
        project2: Second project name
        similarity_threshold: Minimum similarity to report
    """
    print(f"Comparing projects: {project1} <-> {project2}")
    print(f"Similarity threshold: {similarity_threshold}")
    print()

    # Connect to both projects
    db1 = connect_to_project(project1)
    db2 = connect_to_project(project2)

    # Get all claims
    claims1 = get_all_claims(db1)
    claims2 = get_all_claims(db2)

    print(f"Project 1: {len(claims1)} claims")
    print(f"Project 2: {len(claims2)} claims")
    print()

    # Find overlaps
    overlaps = []

    for c1 in claims1:
        for c2 in claims2:
            similarity = compute_similarity(
                c1.get('text', ''),
                c2.get('text', '')
            )

            if similarity >= similarity_threshold:
                overlaps.append({
                    'project1_claim_id': c1['id'],
                    'project1_text': c1.get('text', ''),
                    'project2_claim_id': c2['id'],
                    'project2_text': c2.get('text', ''),
                    'similarity': similarity
                })

    print(f"Found {len(overlaps)} overlapping claims")
    print()

    # Display overlaps
    for i, overlap in enumerate(overlaps, 1):
        print(f"OVERLAP {i}:")
        print(f"  Similarity: {overlap['similarity']:.2f}")
        print(f"  Project 1: {overlap['project1_text'][:100]}...")
        print(f"  Project 2: {overlap['project2_text'][:100]}...")
        print()

    # Close connections
    db1.close()
    db2.close()

    return overlaps


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python compare_projects.py <project1> <project2> [threshold]")
        print()
        print("Example:")
        print("  python compare_projects.py mental-illness cognitive-therapy 0.8")
        sys.exit(1)

    project1 = sys.argv[1]
    project2 = sys.argv[2]
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8

    overlaps = compare_projects(project1, project2, threshold)
```

**Usage:**
```bash
python compare_projects.py mental-illness cognitive-therapy 0.8
```

---

## Merging Projects

### When to Merge?

Merge projects when:
- Topics converge
- Significant overlap found
- Creating meta-analysis
- Building comprehensive knowledge base

### How to Merge?

#### Option 1: Export & Import

```bash
# Export both projects to Cypher
cd projects/mental-illness
python export_project.py > mental-illness.cypher

cd projects/cognitive-therapy
python export_project.py > cognitive-therapy.cypher

# Create new merged project
docker run --name neo4j-merged \
    -p7480:7474 -p7690:7687 \
    --env NEO4J_AUTH=neo4j/research123 \
    -d neo4j:latest

# Import both
cat mental-illness.cypher cognitive-therapy.cypher | \
    cypher-shell -u neo4j -p research123
```

#### Option 2: Python Merge Script

```python
def merge_databases(source_db: Neo4jDatabase,
                   target_db: Neo4jDatabase,
                   project_label: str,
                   merge_similar: bool = True):
    """
    Merge one database into another.

    Args:
        source_db: Source database
        target_db: Target database
        project_label: Label for source nodes (provenance)
        merge_similar: Whether to merge similar claims
    """
    # Get all nodes from source
    for label in ['Document', 'Claim', 'Evidence', 'Source']:
        nodes = source_db.find_nodes(label)

        for node in nodes:
            # Check if similar node exists in target
            if merge_similar and label == 'Claim':
                similar = find_similar_in_target(target_db, node)

                if similar:
                    # Merge as variant
                    target_db.create_node('ClaimVariant', {
                        **node,
                        'project': project_label,
                        'merged_from': node['id']
                    })
                    target_db.create_relationship(
                        node['id'],
                        similar['id'],
                        'VARIANT_OF'
                    )
                    continue

            # Copy node with project label
            new_node = target_db.create_node(label, {
                **node,
                'project': project_label,
                'original_id': node['id']
            })

    print(f"✅ Merged {project_label} into target database")
```

---

## Backup & Restore

### Backup a Project

```bash
# Stop the container
docker stop neo4j-mental-illness

# Backup data directory
tar -czf mental-illness-backup-$(date +%Y%m%d).tar.gz \
    projects/mental-illness/neo4j-data

# Restart
docker start neo4j-mental-illness
```

### Restore from Backup

```bash
# Stop container
docker stop neo4j-mental-illness

# Remove old data
rm -rf projects/mental-illness/neo4j-data

# Extract backup
tar -xzf mental-illness-backup-20251117.tar.gz \
    -C projects/mental-illness/

# Restart
docker start neo4j-mental-illness
```

---

## Project Lifecycle

### 1. Create New Project
```bash
./create_project.sh neuroscience
```

This creates:
- `projects/neuroscience/` directory
- Neo4j container
- `.env` file
- Sample config

### 2. Work on Project
```bash
cd projects/neuroscience
python extract_and_cluster_claims.py
```

### 3. Archive Project
```bash
# Export to Cypher
python export_project.py > neuroscience-final.cypher

# Backup database
docker stop neo4j-neuroscience
tar -czf neuroscience-archive.tar.gz neo4j-data/

# Remove container (data is safe in archive)
docker rm neo4j-neuroscience
```

### 4. Restore Archived Project
```bash
# Extract archive
tar -xzf neuroscience-archive.tar.gz

# Start new container
docker run --name neo4j-neuroscience \
    -v $PWD/neo4j-data:/data \
    # ... rest of command

# Or import Cypher
cypher-shell -f neuroscience-final.cypher
```

---

## Cross-Project Analysis

### Shared Concepts Across Projects

```cypher
// In merged database
// Find concepts appearing in multiple projects

MATCH (c1:Claim {project: 'mental-illness'}),
      (c2:Claim {project: 'cognitive-therapy'})
WHERE c1.text CONTAINS 'depression'
  AND c2.text CONTAINS 'depression'
RETURN c1.text, c2.text
```

### Citation Networks

```cypher
// Find sources cited across multiple projects

MATCH (s:Source)<-[:REFERENCES]-(e:Evidence)-[:SUPPORTS]->(c:Claim)
WITH s, collect(DISTINCT c.project) as projects
WHERE size(projects) > 1
RETURN s.title, projects
ORDER BY size(projects) DESC
```

---

## Best Practices

### 1. Naming Conventions
- Project names: lowercase-with-hyphens
- Database names: same as project name
- Container names: `neo4j-{project-name}`

### 2. Regular Backups
```bash
# Weekly backup script
#!/bin/bash
for project in projects/*/; do
    name=$(basename $project)
    docker exec neo4j-$name neo4j-admin dump --to=/backups/$name-$(date +%Y%m%d).dump
done
```

### 3. Documentation
Each project should have:
- `README.md` - Project overview
- `papers/` - Source PDFs
- `notes.md` - Research notes
- `queries.cypher` - Useful queries

### 4. Version Control
```bash
# Commit project config (not data!)
git add projects/mental-illness/.env
git add projects/mental-illness/config.yaml
git commit -m "Add mental illness research project config"

# .gitignore Neo4j data
projects/*/neo4j-data/
```

---

## Recommended Workflow

```
1. Start
   └─> Create project
       └─> auto_install_neo4j.sh (or Docker)

2. Research
   └─> Add papers to projects/{name}/papers/
       └─> Extract claims
           └─> Investigate claims
               └─> Build knowledge graph

3. Analysis
   └─> Query within project
       └─> Export insights

4. Compare (optional)
   └─> compare_projects.py
       └─> Find overlaps
           └─> Merge if needed

5. Archive
   └─> Backup database
       └─> Export to Cypher
           └─> Document findings
```

---

## FAQ

**Q: Can I work on multiple projects simultaneously?**
A: Yes! Each has its own Docker container/port.

**Q: How much disk space per project?**
A: Depends on paper count. Estimate ~100MB per 100 papers.

**Q: Can I share projects with collaborators?**
A: Yes! Export to Cypher file and share. They can import.

**Q: What if I want everything in one database?**
A: Use project labels: `CREATE (c:Claim:ProjectA {...})`

**Q: How do I query across all projects?**
A: Use `compare_projects.py` or merge into meta-database.

---

**For more details, see HANDOFF_TO_CLI.md**
