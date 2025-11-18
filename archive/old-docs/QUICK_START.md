# Quick Start Guide - Research Verification Agent

## Run the Complete Demo

### Single Command:
```bash
python test_end_to_end_verbose.py
```

This will:
1. Extract text from the Szasz PDF (6 pages)
2. Split into 140 sentences
3. Extract 91 key claims
4. Analyze 20 claims for qualifiers
5. Build a knowledge graph in Neo4j (47 nodes, 46 relationships)
6. Show all intermediate steps and final summary

**Expected Runtime**: ~7 seconds

---

## What You'll See

### Step 1: PDF Extraction
```
Extracting text from PDF using pdfplumber...
  - Pages: 6
  - Total characters: 28,693
  - First 500 chars displayed
```

### Step 2: Sentence Segmentation
```
  - Total sentences: 140
  - Sample sentences shown
```

### Step 3: Claim Extraction
```
  - Total claims: 91
  - First 10 claims displayed
```

### Step 4: Qualifier Analysis
```
  - Claims analyzed: 20
  - Qualifier distribution:
    - quantity: 13
    - modal: 12
    - certainty: 1
  - Detailed analysis of first 5 claims
```

### Step 5: Neo4j Graph
```
  - Connection successful
  - Created 47 nodes
  - Created 46 relationships
  - Stats by type shown
```

### Step 6: Related Research
```
  - Searches arXiv (may have SSL error)
  - Would show 5 related papers
```

### Step 7: Final Summary
```
  - All statistics aggregated
  - Processing complete
```

---

## Verify Neo4j Database

### Check Database Contents:
```bash
python -c "from research_agent.neo4j_database import Neo4jDatabase; db = Neo4jDatabase(); stats = db.stats(); print('Nodes:', stats['total_nodes'], '| Relationships:', stats['total_relationships']); db.close()"
```

**Expected Output**:
```
Nodes: 47 | Relationships: 46
```

---

## View in Neo4j Browser

1. Open: http://localhost:7474
2. Login: neo4j / research123 (from .env)
3. Run query:

```cypher
MATCH (d:Document)-[:CONTAINS_CLAIM]->(c:Claim)-[:HAS_QUALIFIER]->(q:Qualifier)
RETURN d, c, q
LIMIT 25
```

You'll see:
- 1 Document node (the Szasz paper)
- 20 Claim nodes (extracted claims)
- 26 Qualifier nodes (modals, quantifiers, etc.)

---

## Sample Queries

### Find Strong Claims:
```cypher
MATCH (c:Claim {strength: 'strong'})
RETURN c.text, c.qualifier_count
```

### Find All Modals:
```cypher
MATCH (q:Qualifier {type: 'modal'})
RETURN q.text, q.impact, count(*) as uses
ORDER BY uses DESC
```

### Find Claims with Multiple Qualifiers:
```cypher
MATCH (c:Claim)-[:HAS_QUALIFIER]->(q:Qualifier)
WITH c, count(q) as qual_count
WHERE qual_count > 1
RETURN c.text, qual_count
ORDER BY qual_count DESC
```

### View Complete Document Structure:
```cypher
MATCH path = (d:Document)-[:CONTAINS_CLAIM]->(c:Claim)-[:HAS_QUALIFIER]->(q:Qualifier)
RETURN path
LIMIT 50
```

---

## Working Modules

All these modules are tested and working:

1. **PDFExtractor**
   ```python
   from research_agent.document_processing.pdf_extractor import PDFExtractor
   extractor = PDFExtractor()
   result = extractor.extract(Path("sample papers/SHORT-The-Myth-of-Mental-Illness.pdf"))
   ```

2. **QualifierExtractor**
   ```python
   from research_agent.normalization.qualifier_extractor import QualifierExtractor
   extractor = QualifierExtractor()
   qualifiers = extractor.extract("Climate change may cause severe weather events.")
   ```

3. **Neo4jDatabase**
   ```python
   from research_agent.neo4j_database import Neo4jDatabase
   db = Neo4jDatabase()
   node_id = db.create_node('Claim', {'text': 'Test claim'})
   db.close()
   ```

4. **ArxivClient**
   ```python
   from research_agent.research_apis.arxiv_client import ArxivClient
   client = ArxivClient()
   papers = client.search("machine learning", max_results=5)
   ```

---

## File Locations

**Test Script**:
```
C:\Users\jpswi\Research-Assistant-Tool-\test_end_to_end_verbose.py
```

**Sample PDF**:
```
C:\Users\jpswi\Research-Assistant-Tool-\sample papers\SHORT-The-Myth-of-Mental-Illness.pdf
```

**Results Documentation**:
```
C:\Users\jpswi\Research-Assistant-Tool-\END_TO_END_TEST_RESULTS.md
```

**Environment Config**:
```
C:\Users\jpswi\Research-Assistant-Tool-\.env
```

---

## Troubleshooting

### Neo4j Not Running:
```bash
# Check Neo4j status
neo4j status

# Start Neo4j
neo4j start

# Or use console mode
neo4j console
```

### Connection Error:
Check `.env` file has:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=research123
NEO4J_DATABASE=neo4j
```

### Module Import Error:
```bash
# Ensure you're in the project root
cd "C:\Users\jpswi\Research-Assistant-Tool-"

# Run from there
python test_end_to_end_verbose.py
```

### arXiv SSL Error:
This is expected on some systems. The test continues without it.
To fix (optional):
```bash
pip install certifi
```

---

## Success Criteria

You know it worked if you see:
- All 7 steps complete without errors
- "END-TO-END TEST COMPLETE" banner
- Database shows 47 nodes and 46 relationships
- Neo4j Browser displays the graph

---

## Next Steps

After running the test:

1. **Explore the Graph**: Open Neo4j Browser and run the sample queries
2. **Try Your Own PDF**: Modify the script to process a different paper
3. **Extend the Pipeline**: Add claim normalization or verification scoring
4. **Build UI**: Create a web interface for the knowledge graph

---

## Full Documentation

See `END_TO_END_TEST_RESULTS.md` for:
- Detailed results from each step
- Sample outputs
- Cypher query examples
- Architecture overview
- Next development phases
